import pyqtgraph as pg
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from simulation import FIRE_THRESHOLD, SMOKE_THRESHOLD


class ZoneChartsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        left_group = QGroupBox("Температура")
        right_group = QGroupBox("Дымность")
        left_layout = QVBoxLayout(left_group)
        right_layout = QVBoxLayout(right_group)
        left_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.temp_plot = pg.PlotWidget()
        self.smoke_plot = pg.PlotWidget()

        self._configure_plot(
            self.temp_plot, "Температура", "Время, с", "Температура, °C"
        )
        self._configure_plot(self.smoke_plot, "Дымность", "Время, с", "CO2, ppm")

        self.temp_curve = self.temp_plot.plot(pen=pg.mkPen("#f57c00", width=2))
        self.smoke_curve = self.smoke_plot.plot(pen=pg.mkPen("#1565c0", width=2))

        temp_line = pg.InfiniteLine(
            angle=0, movable=False, 
            pen=pg.mkPen("r", width=2, style=Qt.PenStyle.DashLine),
            label="Порог: {value:.1f} °C",
            labelOpts={'position': 0.85, 'color': 'r', 'movable': True, 'fill': (255, 255, 255, 180)}
        )
        temp_line.setPos(FIRE_THRESHOLD)
        self.temp_plot.addItem(temp_line)

        smoke_line = pg.InfiniteLine(
            angle=0, movable=False, 
            pen=pg.mkPen("r", width=2, style=Qt.PenStyle.DashLine),
            label="Порог: {value:.1f} ppm",
            labelOpts={'position': 0.85, 'color': 'r', 'movable': True, 'fill': (255, 255, 255, 180)}
        )
        smoke_line.setPos(SMOKE_THRESHOLD)
        self.smoke_plot.addItem(smoke_line)

        left_layout.addWidget(self.temp_plot)
        right_layout.addWidget(self.smoke_plot)

        layout.addWidget(left_group, 1)
        layout.addWidget(right_group, 1)

    def _configure_plot(self, plot, title, x_label, y_label):
        plot.setBackground("#ffffff")
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.setTitle(title)
        plot.setLabel("bottom", x_label)
        plot.setLabel("left", y_label)
        plot.setMenuEnabled(False)
        plot.setMouseEnabled(x=True, y=False)

    def set_data(self, temp_values, smoke_values):
        temp_x = list(range(len(temp_values)))
        smoke_x = list(range(len(smoke_values)))
        self.temp_curve.setData(temp_x, list(temp_values))
        self.smoke_curve.setData(smoke_x, list(smoke_values))
