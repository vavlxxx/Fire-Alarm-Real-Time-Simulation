import datetime
import json
from collections import deque
from pathlib import Path

from PyQt6.QtCore import QPointF, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF, QTextCursor
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import strings_ru as strings
from charts import ZoneChartsWidget
from simulation import FIRE, NORMAL, SMOKE, FireAlarmSim


class MapGraphicsView(QGraphicsView):
    zone_left_clicked = pyqtSignal(int)
    zone_right_clicked = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QColor("#ffffff"))

        self.map_item = None
        self.zone_items = {}
        self.zone_label_items = {}

        self.min_zoom = 0.25
        self.max_zoom = 8.0
        self.zoom_level = 1.0
        self._has_user_interacted = False

        self._left_press_pos = None
        self._last_pan_pos = None
        self._panning = False

    def set_layout(self, pixmap, zones):
        self._scene.clear()
        self.zone_items = {}
        self.zone_label_items = {}

        self.map_item = self._scene.addPixmap(pixmap)
        self.map_item.setZValue(0)

        width = pixmap.width()
        height = pixmap.height()

        for zone in zones:
            zone_id = zone["id"]
            polygons = zone.get("polygons", [])
            if not polygons:
                continue

            for polygon in polygons:
                points = QPolygonF([QPointF(x * width, y * height) for x, y in polygon])
                item = QGraphicsPolygonItem()
                item.setPolygon(points)
                item.setData(0, zone_id)
                item.setZValue(10)
                self._scene.addItem(item)
                self.zone_items.setdefault(zone_id, []).append(item)

            label_point = zone.get("label")
            if not label_point:
                label_point = self._polygon_center(polygons[0])
            lx = label_point[0] * width
            ly = label_point[1] * height

            rect_item = QGraphicsRectItem()
            rect_item.setZValue(19)
            self._scene.addItem(rect_item)

            text_item = QGraphicsSimpleTextItem()
            text_item.setZValue(20)
            self._scene.addItem(text_item)

            self.zone_label_items[zone_id] = (rect_item, text_item, QPointF(lx, ly))

        self._scene.setSceneRect(self.map_item.boundingRect())
        self.reset_to_fit()

    def reset_to_fit(self):
        if self.map_item is None:
            return
        self.zoom_level = 1.0
        self._has_user_interacted = False
        self.fitInView(self.map_item, Qt.AspectRatioMode.KeepAspectRatio)

    def _polygon_center(self, polygon):
        sx = 0.0
        sy = 0.0
        for x, y in polygon:
            sx += x
            sy += y
        count = max(1, len(polygon))
        return sx / count, sy / count

    def zone_at_view_pos(self, pos):
        item = self.itemAt(pos)
        while item is not None:
            zone_id = item.data(0)
            if zone_id is not None:
                try:
                    return int(zone_id)
                except (TypeError, ValueError):
                    return None
            item = item.parentItem()
        return None

    def wheelEvent(self, event):
        if self.map_item is None:
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = 1.15 if delta > 0 else 1 / 1.15
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom_level * factor))
        if abs(new_zoom - self.zoom_level) < 1e-6:
            return

        factor_to_apply = new_zoom / self.zoom_level
        self.zoom_level = new_zoom
        self._has_user_interacted = True
        self.scale(factor_to_apply, factor_to_apply)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._left_press_pos = event.pos()
            self._last_pan_pos = event.pos()
            self._panning = False
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            zone_id = self.zone_at_view_pos(event.pos())
            if zone_id is not None:
                self.zone_right_clicked.emit(zone_id, event.globalPosition().toPoint())
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._left_press_pos is None:
            super().mouseMoveEvent(event)
            return

        if not self._panning and (event.pos() - self._left_press_pos).manhattanLength() > 6:
            self._panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        if self._panning and self._last_pan_pos is not None:
            delta = event.pos() - self._last_pan_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._last_pan_pos = event.pos()
            self._has_user_interacted = True
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._left_press_pos is not None:
            moved = (event.pos() - self._left_press_pos).manhattanLength()
            if not self._panning and moved <= 6:
                zone_id = self.zone_at_view_pos(event.pos())
                if zone_id is not None:
                    self.zone_left_clicked.emit(zone_id)

            self._left_press_pos = None
            self._last_pan_pos = None
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._has_user_interacted:
            self.reset_to_fit()

    def update_styles(self, states_by_id, selected_zone_id, blink_visible, colors):
        idle_outline = QColor("#a9a094")
        accent = QColor("#1565c0")

        for zone_id, items in self.zone_items.items():
            state = states_by_id.get(zone_id, NORMAL)
            color = QColor(colors[state])
            is_alert = state in (SMOKE, FIRE) and blink_visible

            fill_color = QColor(color)
            fill_color.setAlpha(85 if is_alert else 0)
            outline_color = accent if zone_id == selected_zone_id else (color if is_alert else idle_outline)
            width = 3 if zone_id == selected_zone_id else (2 if is_alert else 1)

            pen = QPen(outline_color, width)
            for item in items:
                item.setPen(pen)
                item.setBrush(fill_color)

            label_data = self.zone_label_items.get(zone_id)
            if label_data is None:
                continue

            rect_item, text_item, anchor = label_data
            text_item.setText(f"{zone_id} {strings.state_short_label(state)}")

            if zone_id == selected_zone_id:
                text_color = QColor("#ffffff")
                label_bg = accent
            elif is_alert:
                text_color = QColor("#ffffff")
                label_bg = color
            else:
                text_color = QColor("#202020")
                label_bg = QColor("#ffffff")

            text_item.setBrush(text_color)
            rect_item.setBrush(label_bg)
            rect_item.setPen(QPen(QColor("#d0c8bc"), 1))

            text_rect = text_item.boundingRect()
            tx = anchor.x() - text_rect.width() / 2
            ty = anchor.y() - text_rect.height() / 2
            text_item.setPos(tx, ty)
            rect_item.setRect(tx - 4, ty - 2, text_rect.width() + 8, text_rect.height() + 4)


class FireAlarmWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tick_interval_ms = 1000
        self.blink_interval_ms = 500
        self.history_len = 60

        self.colors = {
            NORMAL: "#2e7d32",
            SMOKE: "#f57c00",
            FIRE: "#c62828",
        }

        self.assets_dir = Path(__file__).resolve().parent / "assets"
        self.images_dir = self.assets_dir / "images"
        self.sounds_dir = self.assets_dir / "sounds"

        self.pending_logs = []
        self.map_missing_zone_logged = set()

        self.layout_metadata = self.read_layout_metadata()
        zone_count = self.derive_zone_count(self.layout_metadata)
        self.sim = FireAlarmSim(zone_count=zone_count, zone_name_factory=strings.zone_name)

        self.zone_layout = []
        self.zone_layout_by_id = {}

        self.selected_zone_index = 0
        self.blink_visible = True
        self._syncing_controls = False

        self.temp_history = [deque(maxlen=self.history_len) for _ in self.sim.zones]
        self.smoke_history = [deque(maxlen=self.history_len) for _ in self.sim.zones]
        self.last_zone_states = [zone.state for zone in self.sim.zones]
        self.last_zone_actuators = [(zone.sprinklers_on, zone.ventilation_on) for zone in self.sim.zones]

        self.log_lines = deque(maxlen=5000)
        self.beep_player = None
        self.beep_audio = None
        self.alarm_player = None
        self.alarm_audio = None
        self.init_audio()

        self.build_ui()
        self.load_zone_layout()
        self.update_histories()
        self.update_histories()
        self.flush_pending_logs()
        self.update_ui()

        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(self.tick_interval_ms)
        self.tick_timer.timeout.connect(self.update_loop)
        self.tick_timer.start()

        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(self.blink_interval_ms)
        self.blink_timer.timeout.connect(self.blink_loop)
        self.blink_timer.start()

    def build_ui(self):
        self.setWindowTitle(strings.t("app_title"))
        self.resize(1580, 980)
        self.setMinimumSize(1260, 820)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        left_header = QVBoxLayout()
        self.title_label = QLabel(strings.t("header_title"))
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #2f2f2f;")

        self.system_state_label = QLabel(strings.t("system_state", state=strings.state_label(NORMAL)))
        self.system_state_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #2e7d32;")

        left_header.addWidget(self.title_label)
        left_header.addWidget(self.system_state_label)
        header_layout.addLayout(left_header)
        header_layout.addStretch(1)

        right_header = QVBoxLayout()

        self.clock_label = QLabel("00:00:00")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.clock_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #2f2f2f;")

        self.cycle_label = QLabel(strings.t("cycle", count=0))
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.cycle_label.setStyleSheet("font-size: 12px; color: #5f5f5f;")

        help_button = QPushButton(strings.t("help_button"))
        help_button.clicked.connect(self.show_help)

        right_header.addWidget(self.clock_label)
        right_header.addWidget(self.cycle_label)
        right_header.addWidget(help_button, alignment=Qt.AlignmentFlag.AlignRight)

        header_layout.addLayout(right_header)
        main_layout.addWidget(header)

        self.main_tabs = QTabWidget()
        main_layout.addWidget(self.main_tabs)

        main_tab = QWidget()
        data_tab = QWidget()
        self.main_tabs.addTab(main_tab, strings.t("tab_main"))
        self.main_tabs.addTab(data_tab, strings.t("tab_data"))

        self.build_main_tab(main_tab)
        self.build_data_tab(data_tab)

    def build_main_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

        map_group = QGroupBox(strings.t("zone_map"))
        map_layout = QVBoxLayout(map_group)

        self.map_view = MapGraphicsView()
        self.map_view.zone_left_clicked.connect(self.on_map_zone_selected)
        self.map_view.zone_right_clicked.connect(self.on_map_zone_context)
        map_layout.addWidget(self.map_view)

        legend = QHBoxLayout()
        legend.addWidget(QLabel(strings.t("map_legend")))
        legend.addWidget(self.make_legend_label(strings.t("legend_normal"), self.colors[NORMAL]))
        legend.addWidget(self.make_legend_label(strings.t("legend_smoke"), self.colors[SMOKE]))
        legend.addWidget(self.make_legend_label(strings.t("legend_fire"), self.colors[FIRE]))
        legend.addStretch(1)
        map_layout.addLayout(legend)

        right_splitter = QSplitter(Qt.Orientation.Vertical)

        control_group = QGroupBox(strings.t("controls_title"))
        control_layout = QVBoxLayout(control_group)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel(strings.t("selected_zone")))
        self.zone_selector = QComboBox()
        self.zone_selector.addItems([zone.name for zone in self.sim.zones])
        self.zone_selector.currentIndexChanged.connect(self.on_zone_selector_changed)
        selector_row.addWidget(self.zone_selector)
        selector_row.addStretch(1)
        control_layout.addLayout(selector_row)

        scenario_group = QGroupBox(strings.t("scenario_triggers"))
        scenario_layout = QHBoxLayout(scenario_group)
        self.fire_button = QPushButton(strings.t("button_fire"))
        self.fire_button.clicked.connect(lambda _checked=False: self.trigger_fire())
        self.smoke_button = QPushButton(strings.t("button_smoke"))
        self.smoke_button.clicked.connect(lambda _checked=False: self.trigger_smoke())
        self.clear_zone_button = QPushButton(strings.t("button_clear_events"))
        self.clear_zone_button.clicked.connect(lambda _checked=False: self.clear_zone())
        scenario_layout.addWidget(self.fire_button)
        scenario_layout.addWidget(self.smoke_button)
        scenario_layout.addWidget(self.clear_zone_button)
        control_layout.addWidget(scenario_group)

        automation_group = QGroupBox(strings.t("automation"))
        automation_layout = QVBoxLayout(automation_group)

        self.auto_scenarios_check = QCheckBox(strings.t("check_auto_scenarios"))
        self.auto_scenarios_check.stateChanged.connect(self.toggle_auto)

        self.auto_recovery_check = QCheckBox(strings.t("check_auto_recovery"))
        self.auto_recovery_check.setChecked(True)
        self.auto_recovery_check.stateChanged.connect(self.toggle_auto)

        self.auto_control_check = QCheckBox(strings.t("check_auto_control"))
        self.auto_control_check.stateChanged.connect(self.toggle_auto)

        automation_layout.addWidget(self.auto_scenarios_check)
        automation_layout.addWidget(self.auto_recovery_check)
        automation_layout.addWidget(self.auto_control_check)
        control_layout.addWidget(automation_group)

        actuators_group = QGroupBox(strings.t("actuators"))
        actuators_layout = QVBoxLayout(actuators_group)

        self.sprinkler_check = QCheckBox(strings.t("check_sprinklers"))
        self.sprinkler_check.stateChanged.connect(self.toggle_actuators)

        self.vent_check = QCheckBox(strings.t("check_ventilation"))
        self.vent_check.stateChanged.connect(self.toggle_actuators)

        self.reset_button = QPushButton(strings.t("button_reset"))
        self.reset_button.clicked.connect(self.reset_system)

        actuators_layout.addWidget(self.sprinkler_check)
        actuators_layout.addWidget(self.vent_check)
        actuators_layout.addWidget(self.reset_button)
        control_layout.addWidget(actuators_group)

        indicators_group = QGroupBox(strings.t("system_indicators"))
        indicators_layout = QVBoxLayout(indicators_group)
        self.info_label = QLabel(strings.t("info_summary", smoke=0, fire=0))
        indicators_layout.addWidget(self.info_label)
        control_layout.addWidget(indicators_group)

        control_layout.addStretch(1)

        log_group = QGroupBox(strings.t("event_log"))
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        right_splitter.addWidget(control_group)
        right_splitter.addWidget(log_group)
        right_splitter.setSizes([620, 260])

        main_splitter.addWidget(map_group)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([1050, 480])

    def build_data_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        table_group = QGroupBox(strings.t("tab_table"))
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget(len(self.sim.zones), 6)
        self.table.setHorizontalHeaderLabels(
            [
                strings.t("col_zone"),
                strings.t("col_temp"),
                strings.t("col_smoke"),
                strings.t("col_state"),
                strings.t("col_sprinkler"),
                strings.t("col_vent"),
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self.on_table_zone_selected)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.table)

        chart_group = QGroupBox(strings.t("charts_title"))
        chart_layout = QVBoxLayout(chart_group)
        self.charts = ZoneChartsWidget()
        chart_layout.addWidget(self.charts)

        splitter.addWidget(table_group)
        splitter.addWidget(chart_group)
        splitter.setSizes([470, 320])

    def make_legend_label(self, text, color_hex):
        label = QLabel(f"  {text}  ")
        label.setStyleSheet(
            f"background: {color_hex}; color: #ffffff; border: 1px solid #9a9a9a; border-radius: 3px; padding: 2px 6px;"
        )
        return label

    def read_layout_metadata(self):
        fallback = self.default_zone_layout()
        layout_path = self.assets_dir / "zones_layout.json"
        if not layout_path.exists():
            return fallback
        try:
            with layout_path.open("r", encoding="utf-8-sig") as file:
                return json.load(file)
        except Exception as error:
            self.queue_log(strings.t("log_layout_error", error=str(error)))
            return fallback

    def derive_zone_count(self, layout_data):
        zones = self.parse_zones(layout_data.get("zones", []))
        if zones:
            return max(zone["id"] for zone in zones)
        return 15

    def resolve_image_path(self, image_name):
        image_ref = Path(image_name)
        candidates = []
        if image_ref.is_absolute():
            candidates.append(image_ref)
        else:
            candidates.append(self.assets_dir / image_ref)
            candidates.append(self.images_dir / image_ref)

        for candidate in candidates:
            if candidate.exists():
                return candidate

        png_files = sorted(self.images_dir.glob("*.png"))
        if png_files:
            return png_files[0]
        raise FileNotFoundError("Map image not found")

    def resolve_sound_path(self, *names):
        for name in names:
            candidate = self.sounds_dir / name
            if candidate.exists():
                return candidate
        return None

    def init_audio(self):
        try:
            beep_path = self.resolve_sound_path("beep.mp3")
            if beep_path is not None:
                self.beep_player = QMediaPlayer(self)
                self.beep_audio = QAudioOutput(self)
                self.beep_audio.setVolume(0.35)
                self.beep_player.setAudioOutput(self.beep_audio)
                self.beep_player.setSource(QUrl.fromLocalFile(str(beep_path)))

            alarm_path = self.resolve_sound_path("alarm.mp3")
            if alarm_path is not None:
                self.alarm_player = QMediaPlayer(self)
                self.alarm_audio = QAudioOutput(self)
                self.alarm_audio.setVolume(0.55)
                self.alarm_player.setAudioOutput(self.alarm_audio)
                self.alarm_player.setSource(QUrl.fromLocalFile(str(alarm_path)))
                self.alarm_player.setLoops(QMediaPlayer.Loops.Infinite)
        except Exception as error:
            self.queue_log(f"Ошибка инициализации звука: {error}")

    def play_beep_sound(self):
        if self.beep_player is None:
            return
        self.beep_player.stop()
        self.beep_player.play()

    def update_alarm_sound(self, alarm_active):
        if self.alarm_player is None:
            return
        state = self.alarm_player.playbackState()
        if alarm_active:
            if state != QMediaPlayer.PlaybackState.PlayingState:
                self.alarm_player.play()
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self.alarm_player.stop()

    def parse_zones(self, raw_zones):
        zones = []
        for raw in raw_zones:
            try:
                zone_id = int(raw.get("id"))
            except (TypeError, ValueError):
                continue

            polygons = []
            for raw_polygon in raw.get("polygons", []):
                polygon = []
                for point in raw_polygon:
                    if not isinstance(point, (list, tuple)) or len(point) != 2:
                        continue
                    try:
                        x = float(point[0])
                        y = float(point[1])
                    except (TypeError, ValueError):
                        continue
                    polygon.append((min(1.0, max(0.0, x)), min(1.0, max(0.0, y))))
                if len(polygon) >= 3:
                    polygons.append(polygon)

            if not polygons:
                continue

            label = raw.get("label")
            label_point = None
            if isinstance(label, (list, tuple)) and len(label) == 2:
                try:
                    label_point = (float(label[0]), float(label[1]))
                except (TypeError, ValueError):
                    label_point = None

            zones.append(
                {
                    "id": zone_id,
                    "name": raw.get("name") or strings.zone_name(zone_id - 1),
                    "polygons": polygons,
                    "label": label_point,
                }
            )

        zones.sort(key=lambda item: item["id"])
        return zones

    def default_zone_layout(self):
        return {
            "image": "images/Одноэтажный комплекс Одуванчик.png",
            "zones": [
                {"id": 1, "name": "Зона 1", "polygons": [[[0.0446, 0.0787], [0.2285, 0.0787], [0.2285, 0.4595], [0.0446, 0.4595]]], "label": [0.1366, 0.2691]},
                {"id": 2, "name": "Зона 2", "polygons": [[[0.2285, 0.0787], [0.3218, 0.0787], [0.3218, 0.4595], [0.2285, 0.4595]]], "label": [0.2752, 0.2691]},
                {"id": 3, "name": "Зона 3", "polygons": [[[0.3218, 0.0787], [0.4145, 0.0787], [0.4145, 0.4595], [0.3218, 0.4595]]], "label": [0.3682, 0.2691]},
                {"id": 4, "name": "Зона 4", "polygons": [[[0.4145, 0.0787], [0.5997, 0.0787], [0.5997, 0.4595], [0.4145, 0.4595]]], "label": [0.5071, 0.2691]},
                {"id": 5, "name": "Зона 5", "polygons": [[[0.5997, 0.0787], [0.7863, 0.0787], [0.7863, 0.4595], [0.5997, 0.4595]]], "label": [0.6930, 0.2691]},
                {"id": 6, "name": "Зона 6", "polygons": [[[0.7863, 0.0787], [0.9682, 0.0787], [0.9682, 0.4595], [0.7863, 0.4595]]], "label": [0.8773, 0.2691]},
                {"id": 7, "name": "Зона 7", "polygons": [[[0.0446, 0.5861], [0.1400, 0.5861], [0.1400, 0.9567], [0.0446, 0.9567]]], "label": [0.0923, 0.7714]},
                {"id": 8, "name": "Зона 8", "polygons": [[[0.1400, 0.5861], [0.2285, 0.5861], [0.2285, 0.9567], [0.1400, 0.9567]]], "label": [0.1842, 0.7714]},
                {"id": 9, "name": "Зона 9", "polygons": [[[0.2285, 0.5861], [0.3218, 0.5861], [0.3218, 0.9567], [0.2285, 0.9567]]], "label": [0.2752, 0.7714]},
                {"id": 10, "name": "Зона 10", "polygons": [[[0.3218, 0.5861], [0.4145, 0.5861], [0.4145, 0.9567], [0.3218, 0.9567]]], "label": [0.3682, 0.7714]},
                {"id": 11, "name": "Зона 11", "polygons": [[[0.4145, 0.5861], [0.5071, 0.5861], [0.5071, 0.9567], [0.4145, 0.9567]]], "label": [0.4608, 0.7714]},
                {"id": 12, "name": "Зона 12", "polygons": [[[0.5071, 0.5861], [0.5997, 0.5861], [0.5997, 0.9567], [0.5071, 0.9567]]], "label": [0.5534, 0.7714]},
                {"id": 13, "name": "Зона 13", "polygons": [[[0.5997, 0.5861], [0.7863, 0.5861], [0.7863, 0.9567], [0.5997, 0.9567]]], "label": [0.6930, 0.7714]},
                {"id": 14, "name": "Зона 14", "polygons": [[[0.7863, 0.5861], [0.9682, 0.5861], [0.9682, 0.9567], [0.7863, 0.9567]]], "label": [0.8773, 0.7714]},
                {"id": 15, "name": "Зона 15", "polygons": [[[0.0446, 0.4595], [0.9682, 0.4595], [0.9682, 0.5861], [0.0446, 0.5861]]], "label": [0.5064, 0.5228]},
            ],
        }

    def load_zone_layout(self):
        fallback = self.default_zone_layout()
        layout_data = self.layout_metadata if self.layout_metadata else fallback

        image_name = layout_data.get("image") or fallback["image"]
        image_path = self.resolve_image_path(image_name)
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            raise RuntimeError(f"Unable to load map image: {image_path}")

        parsed_zones = self.parse_zones(layout_data.get("zones", []))
        if not parsed_zones:
            parsed_zones = self.parse_zones(fallback["zones"])

        self.zone_layout = parsed_zones
        self.zone_layout_by_id = {zone["id"]: zone for zone in self.zone_layout}
        self.map_missing_zone_logged.clear()

        self.map_view.set_layout(pixmap, self.zone_layout)

    def update_loop(self):
        self.sim.tick()
        self.update_histories()
        self.update_ui()

    def blink_loop(self):
        self.blink_visible = not self.blink_visible
        self.update_map()

    def update_histories(self):
        for idx, zone in enumerate(self.sim.zones):
            self.temp_history[idx].append(zone.temp)
            self.smoke_history[idx].append(zone.smoke)

    def update_ui(self):
        now = datetime.datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S"))
        self.cycle_label.setText(strings.t("cycle", count=self.sim.tick_count))

        system_state = self.sim.system_state()
        self.system_state_label.setText(strings.t("system_state", state=strings.state_label(system_state)))
        self.system_state_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {self.colors[system_state]};")

        smoke_count = sum(1 for zone in self.sim.zones if zone.state == SMOKE)
        fire_count = sum(1 for zone in self.sim.zones if zone.state == FIRE)
        self.info_label.setText(strings.t("info_summary", smoke=smoke_count, fire=fire_count))
        self.update_alarm_sound(smoke_count > 0 or fire_count > 0)

        for idx, zone in enumerate(self.sim.zones):
            if zone.state != self.last_zone_states[idx]:
                self.log(strings.log_state_change(zone.name, zone.state))
                self.last_zone_states[idx] = zone.state

            previous = self.last_zone_actuators[idx]
            current = (zone.sprinklers_on, zone.ventilation_on)
            if current != previous:
                if self.sim.auto_control:
                    self.log(
                        strings.t(
                            "log_actuators_auto",
                            zone=zone.name,
                            sprinklers=strings.on_off(zone.sprinklers_on),
                            vent=strings.on_off(zone.ventilation_on),
                        )
                    )
                self.last_zone_actuators[idx] = current

        if self.sim.last_auto_event:
            event_type, zone = self.sim.last_auto_event
            self.log(strings.auto_event_message(event_type, zone.name))

        self.update_table()
        self.sync_zone_controls()
        self.update_charts()
        self.update_map()

    def update_table(self):
        for row, zone in enumerate(self.sim.zones):
            values = [
                zone.name,
                f"{zone.temp:5.1f}",
                f"{zone.smoke:5.0f}",
                strings.state_label(zone.state),
                strings.on_off(zone.sprinklers_on),
                strings.on_off(zone.ventilation_on),
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col > 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            row_color = QColor("#e8f5e9")
            if zone.state == SMOKE:
                row_color = QColor("#fff4e5")
            elif zone.state == FIRE:
                row_color = QColor("#ffebee")

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is not None:
                    item.setBackground(row_color)

    def update_charts(self):
        idx = self.selected_zone_index
        self.charts.set_data(self.temp_history[idx], self.smoke_history[idx])

    def update_map(self):
        states_by_id = {}
        for zone_id, zone in enumerate(self.sim.zones, start=1):
            states_by_id[zone_id] = zone.state
            if zone_id not in self.zone_layout_by_id and zone_id not in self.map_missing_zone_logged:
                self.queue_log(strings.t("log_zone_not_found", zone=zone.name))
                self.map_missing_zone_logged.add(zone_id)

        self.map_view.update_styles(
            states_by_id=states_by_id,
            selected_zone_id=self.selected_zone_index + 1,
            blink_visible=self.blink_visible,
            colors=self.colors,
        )

    def sync_zone_controls(self):
        self._syncing_controls = True
        zone = self.get_selected_zone()

        self.zone_selector.setCurrentIndex(self.selected_zone_index)
        self.auto_scenarios_check.setChecked(self.sim.auto_scenarios)
        self.auto_recovery_check.setChecked(self.sim.auto_recovery)
        self.auto_control_check.setChecked(self.sim.auto_control)

        self.sprinkler_check.setChecked(zone.sprinklers_on)
        self.vent_check.setChecked(zone.ventilation_on)

        if self.table.currentRow() != self.selected_zone_index:
            self.table.selectRow(self.selected_zone_index)

        self._syncing_controls = False

    def on_zone_selector_changed(self, index):
        if index < 0:
            return
        self.set_selected_zone(index)

    def on_table_zone_selected(self, row, _column):
        self.set_selected_zone(row)

    def on_map_zone_selected(self, zone_id):
        self.set_selected_zone(zone_id - 1, play_sound=True)

    def on_map_zone_context(self, zone_id, global_pos):
        zone = self.get_zone_by_id(zone_id)
        if zone is None:
            return
        self.set_selected_zone(zone_id - 1, play_sound=True)

        menu = QMenu(self)
        title_action = menu.addAction(strings.t("menu_zone_header", zone=zone.name))
        title_action.setEnabled(False)
        menu.addSeparator()

        fire_action = menu.addAction(strings.t("menu_fire"))
        smoke_action = menu.addAction(strings.t("menu_smoke"))
        clear_action = menu.addAction(strings.t("menu_clear_events"))
        menu.addSeparator()

        sprinklers_action = menu.addAction(strings.t("menu_sprinklers"))
        sprinklers_action.setCheckable(True)
        sprinklers_action.setChecked(zone.sprinklers_on)

        vent_action = menu.addAction(strings.t("menu_ventilation"))
        vent_action.setCheckable(True)
        vent_action.setChecked(zone.ventilation_on)

        chosen = menu.exec(global_pos)
        if chosen is None:
            return

        if chosen == fire_action:
            self.trigger_fire(zone_id)
        elif chosen == smoke_action:
            self.trigger_smoke(zone_id)
        elif chosen == clear_action:
            self.clear_zone(zone_id)
        elif chosen == sprinklers_action:
            self.apply_zone_actuators(zone_id, sprinklers=sprinklers_action.isChecked(), log_change=True)
        elif chosen == vent_action:
            self.apply_zone_actuators(zone_id, vent=vent_action.isChecked(), log_change=True)

    def set_selected_zone(self, index, play_sound=False):
        index = max(0, min(len(self.sim.zones) - 1, index))
        changed = index != self.selected_zone_index
        self.selected_zone_index = index
        if changed and play_sound:
            self.play_beep_sound()
        self.sync_zone_controls()
        self.update_charts()
        self.update_map()

    def get_selected_zone(self):
        return self.sim.zones[self.selected_zone_index]

    def get_zone_by_id(self, zone_id):
        if 1 <= zone_id <= len(self.sim.zones):
            return self.sim.zones[zone_id - 1]
        return None

    def resolve_zone_id(self, zone_id=None):
        if isinstance(zone_id, bool):
            return self.selected_zone_index + 1
        if zone_id is not None:
            return zone_id
        return self.selected_zone_index + 1

    def trigger_fire(self, zone_id=None):
        zid = self.resolve_zone_id(zone_id)
        zone = self.get_zone_by_id(zid)
        if zone is None:
            return
        zone.trigger_fire()
        self.log(strings.t("log_manual_fire", zone=zone.name))
        self.update_ui()

    def trigger_smoke(self, zone_id=None):
        zid = self.resolve_zone_id(zone_id)
        zone = self.get_zone_by_id(zid)
        if zone is None:
            return
        zone.trigger_smoke()
        self.log(strings.t("log_manual_smoke", zone=zone.name))
        self.update_ui()

    def clear_zone(self, zone_id=None):
        zid = self.resolve_zone_id(zone_id)
        zone = self.get_zone_by_id(zid)
        if zone is None:
            return
        zone.clear_events()
        self.log(strings.t("log_clear_events", zone=zone.name))
        self.last_zone_actuators[zid - 1] = (zone.sprinklers_on, zone.ventilation_on)
        self.update_ui()

    def reset_system(self):
        for idx, zone in enumerate(self.sim.zones):
            zone.clear_events()
            self.last_zone_states[idx] = zone.state
            self.last_zone_actuators[idx] = (zone.sprinklers_on, zone.ventilation_on)

        self.log(strings.t("log_reset_done"))
        self.update_ui()

    def toggle_auto(self):
        if self._syncing_controls:
            return

        self.sim.auto_scenarios = self.auto_scenarios_check.isChecked()
        self.sim.auto_recovery = self.auto_recovery_check.isChecked()
        self.sim.auto_control = self.auto_control_check.isChecked()

        self.log(
            strings.t(
                "log_automation",
                auto_scenarios=strings.on_off(self.sim.auto_scenarios),
                auto_recovery=strings.on_off(self.sim.auto_recovery),
                auto_control=strings.on_off(self.sim.auto_control),
            )
        )

    def toggle_actuators(self):
        if self._syncing_controls:
            return
        zid = self.selected_zone_index + 1
        self.apply_zone_actuators(
            zid,
            sprinklers=self.sprinkler_check.isChecked(),
            vent=self.vent_check.isChecked(),
            log_change=True,
        )

    def apply_zone_actuators(self, zone_id, sprinklers=None, vent=None, log_change=True):
        zone = self.get_zone_by_id(zone_id)
        if zone is None:
            return

        if sprinklers is not None:
            zone.sprinklers_on = bool(sprinklers)
        if vent is not None:
            zone.ventilation_on = bool(vent)

        self.last_zone_actuators[zone_id - 1] = (zone.sprinklers_on, zone.ventilation_on)

        if log_change:
            self.log(
                strings.t(
                    "log_actuators_manual",
                    zone=zone.name,
                    sprinklers=strings.on_off(zone.sprinklers_on),
                    vent=strings.on_off(zone.ventilation_on),
                )
            )

        self.update_ui()

    def show_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(strings.t("help_title"))
        dialog.resize(700, 500)

        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(strings.t("help_text"))
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(strings.t("help_close"))
        layout.addWidget(buttons)

        dialog.exec()

    def queue_log(self, message):
        if hasattr(self, "log_text"):
            self.log(message)
        else:
            self.pending_logs.append(message)

    def flush_pending_logs(self):
        for message in self.pending_logs:
            self.log(message)
        self.pending_logs.clear()

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"{timestamp}  {message}")

        self.log_text.setPlainText("\n".join(self.log_lines))
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def closeEvent(self, event):
        self.tick_timer.stop()
        self.blink_timer.stop()
        if self.alarm_player is not None:
            self.alarm_player.stop()
        if self.beep_player is not None:
            self.beep_player.stop()
        super().closeEvent(event)
