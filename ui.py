import ctypes
import datetime
import json
import tkinter as tk
from collections import deque
from fractions import Fraction
from pathlib import Path
from tkinter import ttk

import strings_ru as strings
from charts import LineChart
from simulation import FireAlarmSim


class FireAlarmApp:
    def __init__(self, root):
        self.root = root
        self.tick_interval_ms = 1000
        self.blink_interval_ms = 500
        self.spinner = ["|", "/", "-", "\\"]
        self.spinner_index = 0

        self.bg = "#f4f1ea"
        self.panel_bg = "#fbfaf6"
        self.text_color = "#2f2f2f"
        self.subtext_color = "#5f5f5f"
        self.accent = "#1565c0"
        self.good = "#2e7d32"
        self.alarm = "#c62828"
        self.fault = "#6d4c41"
        self.grid_color = "#ddd6cc"
        self.border = "#d0c8bc"
        self.idle_zone_outline = "#a9a094"

        self.pending_logs = []

        self.assets_dir = Path(__file__).resolve().parent / "assets"
        self.images_dir = self.assets_dir / "images"
        self.sounds_dir = self.assets_dir / "sounds"

        self.zone_layout = []
        self.zone_layout_by_id = {}
        self.zone_hit_polygons = {}
        self.map_missing_zone_logged = set()
        self.layout_metadata = self.read_layout_metadata()

        zone_count = self.derive_zone_count(self.layout_metadata)
        self.sim = FireAlarmSim(zone_count=zone_count, zone_name_factory=strings.zone_name)

        self.history_len = 60
        self.temp_history = [deque(maxlen=self.history_len) for _ in self.sim.zones]
        self.smoke_history = [deque(maxlen=self.history_len) for _ in self.sim.zones]
        self.last_zone_status = [zone.status for zone in self.sim.zones]

        self.sound_silenced = False
        self.alarm_acknowledged = False
        self.help_window = None

        self.selected_zone_var = tk.StringVar(value=self.sim.zones[0].name)
        self.last_selected_zone_index = 0
        self.auto_scenarios_var = tk.BooleanVar(value=self.sim.auto_scenarios)
        self.auto_recovery_var = tk.BooleanVar(value=self.sim.auto_recovery)
        self.sprinkler_var = tk.BooleanVar(value=False)
        self.vent_var = tk.BooleanVar(value=True)

        self.map_original_image = None
        self.map_image = None
        self.map_scale_key = (1, 1)
        self.map_image_cache = {}
        self.map_image_pos = (0, 0)
        self.map_image_size = (1, 1)
        self.map_render_scale = 1.0
        self.map_zoom = 1.0
        self.map_min_zoom = 0.8
        self.map_max_zoom = 6.0
        self.map_pan_x = 0.0
        self.map_pan_y = 0.0
        self.map_pan_active = False
        self.map_pan_last = None
        self.blink_visible = True

        self.context_zone_id = None
        self.context_sprinkler_var = tk.BooleanVar(value=False)
        self.context_vent_var = tk.BooleanVar(value=True)

        self.winmm = ctypes.windll.winmm if hasattr(ctypes, "windll") else None
        self.alarm_alias = "alarm_loop"
        self.beep_alias = "zone_beep"
        self.alarm_audio_active = False
        self.sound_error_logged = False
        self.alarm_sound_path = self.find_sound_path("alam.mp3", "alarm.mp3")
        self.beep_sound_path = self.find_sound_path("beep.mp3")

        self.build_ui()
        self.flush_pending_logs()
        self.update_histories()
        self.update_histories()
        self.update_ui()
        self.root.after(self.tick_interval_ms, self.update_loop)
        self.root.after(self.blink_interval_ms, self.blink_loop)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        self.root.title(strings.t("app_title"))
        self.root.configure(bg=self.bg)
        self.root.geometry("1580x980")
        self.root.minsize(1260, 820)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24, background=self.panel_bg)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TNotebook.Tab", font=("Segoe UI", 9))
        style.map("Treeview", background=[("selected", "#d8e6f8")])

        header = tk.Frame(self.root, bg=self.bg)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header.columnconfigure(0, weight=1)

        self.title_label = tk.Label(
            header,
            text=strings.t("header_title"),
            font=("Segoe UI", 16, "bold"),
            bg=self.bg,
            fg=self.text_color,
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.system_state_label = tk.Label(
            header,
            text=strings.t("system_state", state=strings.status_label("NORMAL")),
            font=("Segoe UI", 11, "bold"),
            bg=self.bg,
            fg=self.good,
        )
        self.system_state_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        right_header = tk.Frame(header, bg=self.bg)
        right_header.grid(row=0, column=1, rowspan=2, sticky="e")
        self.clock_label = tk.Label(
            right_header,
            text="00:00:00",
            font=("Segoe UI", 12),
            bg=self.bg,
            fg=self.text_color,
        )
        self.clock_label.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.spinner_label = tk.Label(
            right_header,
            text=self.spinner[0],
            font=("Segoe UI", 12, "bold"),
            bg=self.bg,
            fg=self.accent,
        )
        self.spinner_label.grid(row=0, column=0, sticky="e")
        self.cycle_label = tk.Label(
            right_header,
            text=strings.t("cycle", count=0),
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.subtext_color,
        )
        self.cycle_label.grid(row=1, column=0, columnspan=2, sticky="e")
        help_button = ttk.Button(right_header, text=strings.t("help_button"), command=self.show_help)
        help_button.grid(row=2, column=0, columnspan=2, sticky="e", pady=(6, 0))

        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))

        main_tab = tk.Frame(self.main_notebook, bg=self.bg)
        data_tab = tk.Frame(self.main_notebook, bg=self.panel_bg)

        self.main_notebook.add(main_tab, text=strings.t("tab_main"))
        self.main_notebook.add(data_tab, text=strings.t("tab_data"))

        main_tab.columnconfigure(0, weight=1)
        main_tab.rowconfigure(0, weight=7)
        main_tab.rowconfigure(1, weight=3)

        top_frame = tk.Frame(main_tab, bg=self.bg)
        self.top_frame = top_frame
        top_frame.grid(row=0, column=0, sticky="nsew")
        top_frame.columnconfigure(0, weight=7)
        top_frame.columnconfigure(1, weight=3)
        top_frame.rowconfigure(0, weight=1)
        top_frame.bind("<Configure>", self.on_top_frame_configure)

        self.build_map_panel(top_frame)
        self.build_chart_panel(top_frame)
        self.build_control_panel(main_tab)

        self.build_data_tab(data_tab)

    def build_map_panel(self, parent):
        map_panel = tk.Frame(parent, bg=self.panel_bg, bd=1, relief="solid")
        map_panel.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=6)
        map_panel.columnconfigure(0, weight=1)
        map_panel.rowconfigure(1, weight=1)

        label = tk.Label(
            map_panel,
            text=strings.t("zone_map"),
            font=("Segoe UI", 11, "bold"),
            bg=self.panel_bg,
            fg=self.text_color,
        )
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        self.map_canvas = tk.Canvas(map_panel, bg="#ffffff", highlightthickness=0)
        self.map_canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))
        self.map_canvas.bind("<Configure>", self.on_map_canvas_configure)
        self.map_canvas.bind("<Button-1>", self.on_map_left_click)
        self.map_canvas.bind("<Button-3>", self.on_map_right_click)
        self.map_canvas.bind("<MouseWheel>", self.on_map_mouse_wheel)
        self.map_canvas.bind("<Button-4>", self.on_map_wheel_up)
        self.map_canvas.bind("<Button-5>", self.on_map_wheel_down)
        self.map_canvas.bind("<ButtonPress-2>", self.on_map_pan_start)
        self.map_canvas.bind("<B2-Motion>", self.on_map_pan_move)
        self.map_canvas.bind("<ButtonRelease-2>", self.on_map_pan_end)
        self.map_canvas.bind("<Shift-ButtonPress-1>", self.on_map_pan_start)
        self.map_canvas.bind("<Shift-B1-Motion>", self.on_map_pan_move)
        self.map_canvas.bind("<Shift-ButtonRelease-1>", self.on_map_pan_end)

        legend_frame = tk.Frame(map_panel, bg=self.panel_bg)
        legend_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        legend_title = tk.Label(
            legend_frame,
            text=strings.t("map_legend"),
            font=("Segoe UI", 9, "bold"),
            bg=self.panel_bg,
            fg=self.subtext_color,
        )
        legend_title.pack(side="left")

        legend_items = [
            (self.good, strings.t("legend_normal")),
            (self.alarm, strings.t("legend_alarm")),
            (self.fault, strings.t("legend_fault")),
        ]
        for color, text in legend_items:
            swatch = tk.Canvas(legend_frame, width=14, height=14, bg=self.panel_bg, highlightthickness=0)
            swatch.pack(side="left", padx=(10, 4))
            swatch.create_rectangle(1, 1, 13, 13, outline="#4e4e4e", fill=color)
            tk.Label(
                legend_frame,
                text=text,
                font=("Segoe UI", 8),
                bg=self.panel_bg,
                fg=self.text_color,
            ).pack(side="left")

        self.load_zone_layout()

    def build_chart_panel(self, parent):
        chart_panel = tk.Frame(parent, bg=self.panel_bg, bd=1, relief="solid")
        chart_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=6)
        chart_panel.columnconfigure(0, weight=1)
        chart_panel.rowconfigure(1, weight=1)
        chart_panel.rowconfigure(2, weight=1)

        top_row = tk.Frame(chart_panel, bg=self.panel_bg)
        top_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        top_row.columnconfigure(1, weight=1)

        label = tk.Label(
            top_row,
            text=strings.t("charts_title"),
            font=("Segoe UI", 11, "bold"),
            bg=self.panel_bg,
            fg=self.text_color,
        )
        label.grid(row=0, column=0, sticky="w")

        zone_label = tk.Label(
            top_row,
            text=strings.t("zone_view"),
            font=("Segoe UI", 9),
            bg=self.panel_bg,
            fg=self.subtext_color,
        )
        zone_label.grid(row=0, column=1, sticky="e")

        zone_selector = ttk.Combobox(
            top_row,
            textvariable=self.selected_zone_var,
            values=[z.name for z in self.sim.zones],
            width=14,
            state="readonly",
        )
        zone_selector.grid(row=0, column=2, sticky="e", padx=(6, 0))
        zone_selector.bind("<<ComboboxSelected>>", self.on_zone_change)

        self.temp_chart = LineChart(
            chart_panel,
            title=strings.t("temp_chart"),
            y_label=strings.t("axis_temp"),
            y_min=0,
            y_max=120,
            line_color="#f57c00",
            bg=self.panel_bg,
            text_color=self.text_color,
            grid_color=self.grid_color,
            width=420,
            height=220,
            max_points=self.history_len,
            x_label=strings.t("axis_time"),
        )
        self.temp_chart.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 8))

        self.smoke_chart = LineChart(
            chart_panel,
            title=strings.t("smoke_chart"),
            y_label=strings.t("axis_smoke"),
            y_min=0,
            y_max=200,
            line_color="#1565c0",
            bg=self.panel_bg,
            text_color=self.text_color,
            grid_color=self.grid_color,
            width=420,
            height=220,
            max_points=self.history_len,
            x_label=strings.t("axis_time"),
        )
        self.smoke_chart.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def build_control_panel(self, parent):
        control_panel = tk.Frame(parent, bg=self.panel_bg, bd=1, relief="solid")
        control_panel.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 6))
        control_panel.columnconfigure(0, weight=2)
        control_panel.columnconfigure(1, weight=1)
        control_panel.columnconfigure(2, weight=2)
        control_panel.columnconfigure(3, weight=1)

        top_row = tk.Frame(control_panel, bg=self.panel_bg)
        top_row.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(8, 4))

        label = tk.Label(
            top_row,
            text=strings.t("controls_title"),
            font=("Segoe UI", 11, "bold"),
            bg=self.panel_bg,
            fg=self.text_color,
        )
        label.pack(side="left")

        selector_label = tk.Label(
            top_row,
            text=strings.t("selected_zone"),
            font=("Segoe UI", 9),
            bg=self.panel_bg,
            fg=self.subtext_color,
        )
        selector_label.pack(side="left", padx=(20, 6))

        zone_selector = ttk.Combobox(
            top_row,
            textvariable=self.selected_zone_var,
            values=[z.name for z in self.sim.zones],
            width=14,
            state="readonly",
        )
        zone_selector.pack(side="left")
        zone_selector.bind("<<ComboboxSelected>>", self.on_zone_change)

        scenario_frame = tk.LabelFrame(
            control_panel,
            text=strings.t("scenario_triggers"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        scenario_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 6), pady=(4, 10))
        scenario_frame.columnconfigure(0, weight=1)
        scenario_frame.columnconfigure(1, weight=1)

        ttk.Button(scenario_frame, text=strings.t("button_fire"), command=self.trigger_fire).grid(
            row=0, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_smoke"), command=self.trigger_smoke).grid(
            row=0, column=1, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_clear_events"), command=self.clear_events).grid(
            row=1, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_fault"), command=self.trigger_fault).grid(
            row=1, column=1, sticky="ew", padx=6, pady=4
        )

        auto_frame = tk.LabelFrame(
            control_panel,
            text=strings.t("automation"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        auto_frame.grid(row=1, column=1, sticky="nsew", padx=6, pady=(4, 10))
        auto_frame.columnconfigure(0, weight=1)

        ttk.Checkbutton(
            auto_frame,
            text=strings.t("check_auto_scenarios"),
            variable=self.auto_scenarios_var,
            command=self.toggle_auto,
        ).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Checkbutton(
            auto_frame,
            text=strings.t("check_auto_recovery"),
            variable=self.auto_recovery_var,
            command=self.toggle_auto,
        ).grid(row=1, column=0, sticky="w", padx=6, pady=6)

        actuator_frame = tk.LabelFrame(
            control_panel,
            text=strings.t("actuators"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        actuator_frame.grid(row=1, column=2, sticky="nsew", padx=6, pady=(4, 10))
        actuator_frame.columnconfigure(0, weight=1)

        ttk.Checkbutton(
            actuator_frame,
            text=strings.t("check_sprinklers"),
            variable=self.sprinkler_var,
            command=self.toggle_actuators,
        ).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(
            actuator_frame,
            text=strings.t("check_ventilation"),
            variable=self.vent_var,
            command=self.toggle_actuators,
        ).grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Button(actuator_frame, text=strings.t("button_ack"), command=self.acknowledge_alarm).grid(
            row=2, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(actuator_frame, text=strings.t("button_silence"), command=self.silence_sounders).grid(
            row=3, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(actuator_frame, text=strings.t("button_reset"), command=self.reset_system).grid(
            row=4, column=0, sticky="ew", padx=6, pady=4
        )

        info_frame = tk.LabelFrame(
            control_panel,
            text=strings.t("system_indicators"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        info_frame.grid(row=1, column=3, sticky="nsew", padx=(6, 10), pady=(4, 10))
        info_frame.columnconfigure(0, weight=1)

        self.info_label = tk.Label(
            info_frame,
            text=strings.t("info_summary", alarms=0, faults=0),
            font=("Segoe UI", 9),
            bg=self.panel_bg,
            fg=self.text_color,
            justify="left",
        )
        self.info_label.grid(row=0, column=0, sticky="w", padx=6, pady=(6, 2))

        self.sounder_label = tk.Label(
            info_frame,
            text=strings.t("sounders", state=strings.sounder_label("IDLE")),
            font=("Segoe UI", 9),
            bg=self.panel_bg,
            fg=self.subtext_color,
        )
        self.sounder_label.grid(row=1, column=0, sticky="w", padx=6, pady=(0, 6))

    def build_data_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(1, weight=2)

        table_group = tk.LabelFrame(
            parent,
            text=strings.t("tab_table"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        table_group.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))
        self.build_table_tab(table_group)

        log_group = tk.LabelFrame(
            parent,
            text=strings.t("tab_log"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        log_group.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        self.build_log_tab(log_group)

    def build_table_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        table_frame = tk.Frame(parent, bg=self.panel_bg)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = (
            "zone",
            "temp",
            "smoke",
            "co",
            "status",
            "fire",
            "manual",
            "fault",
            "sprinkler",
            "vent",
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        self.tree.heading("zone", text=strings.t("col_zone"))
        self.tree.heading("temp", text=strings.t("col_temp"))
        self.tree.heading("smoke", text=strings.t("col_smoke"))
        self.tree.heading("co", text=strings.t("col_co"))
        self.tree.heading("status", text=strings.t("col_status"))
        self.tree.heading("fire", text=strings.t("col_fire"))
        self.tree.heading("manual", text=strings.t("col_manual_call"))
        self.tree.heading("fault", text=strings.t("col_fault_flag"))
        self.tree.heading("sprinkler", text=strings.t("col_sprinkler"))
        self.tree.heading("vent", text=strings.t("col_vent"))

        self.tree.column("zone", width=100, anchor="w")
        self.tree.column("temp", width=90, anchor="e")
        self.tree.column("smoke", width=95, anchor="e")
        self.tree.column("co", width=90, anchor="e")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("fire", width=80, anchor="center")
        self.tree.column("manual", width=80, anchor="center")
        self.tree.column("fault", width=110, anchor="center")
        self.tree.column("sprinkler", width=110, anchor="center")
        self.tree.column("vent", width=110, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.tag_configure("NORMAL", background="#e8f5e9")
        self.tree.tag_configure("ALARM", background="#ffebee")
        self.tree.tag_configure("FAULT", background="#efebe9")

        self.tree_items = []
        for zone in self.sim.zones:
            item_id = self.tree.insert("", "end", values=(zone.name, "", "", "", "", "", "", "", "", ""))
            self.tree_items.append(item_id)

    def build_log_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            parent,
            wrap="word",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg=self.text_color,
            bd=1,
            relief="solid",
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.log_text.configure(state="disabled")

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=8)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def flush_pending_logs(self):
        if not hasattr(self, "log_text"):
            return
        for message in self.pending_logs:
            self.log(message)
        self.pending_logs.clear()

    def queue_log(self, message):
        if hasattr(self, "log_text"):
            self.log(message)
        else:
            self.pending_logs.append(message)

    def read_layout_metadata(self):
        fallback = self.default_zone_layout()
        layout_path = self.assets_dir / "zones_layout.json"
        if not layout_path.exists():
            return fallback
        try:
            with layout_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as error:
            self.queue_log(strings.t("log_layout_error", error=str(error)))
            return fallback

    def derive_zone_count(self, layout_data):
        zones = self.parse_zones(layout_data.get("zones", []))
        if zones:
            return max(zone["id"] for zone in zones)
        return 15

    def find_sound_path(self, *names):
        for name in names:
            for folder in (self.sounds_dir, self.assets_dir):
                candidate = folder / name
                if candidate.exists():
                    return candidate
        return None

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

        for folder in (self.images_dir, self.assets_dir):
            png_files = sorted(folder.glob("*.png"))
            if png_files:
                return png_files[0]

        raise FileNotFoundError("Map image not found.")

    def load_zone_layout(self):
        fallback_layout = self.default_zone_layout()
        layout_data = self.layout_metadata if self.layout_metadata else fallback_layout

        image_name = layout_data.get("image") or fallback_layout["image"]
        image_path = self.resolve_image_path(image_name)

        try:
            self.map_original_image = tk.PhotoImage(file=str(image_path))
        except tk.TclError as error:
            raise RuntimeError(f"Unable to load map image: {image_path}") from error

        parsed_zones = self.parse_zones(layout_data.get("zones", []))
        if not parsed_zones:
            parsed_zones = self.parse_zones(fallback_layout["zones"])

        self.zone_layout = sorted(parsed_zones, key=lambda zone: zone["id"])
        self.zone_layout_by_id = {zone["id"]: zone for zone in self.zone_layout}
        self.map_missing_zone_logged.clear()
        self.map_scale_key = (1, 1)
        self.map_image_cache = {}
        self.map_image = None
        self.map_zoom = 1.0
        self.map_pan_x = 0.0
        self.map_pan_y = 0.0
        self.map_render_scale = 1.0

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

            label_point = None
            label_raw = raw.get("label")
            if isinstance(label_raw, (list, tuple)) and len(label_raw) == 2:
                try:
                    label_point = (
                        min(1.0, max(0.0, float(label_raw[0]))),
                        min(1.0, max(0.0, float(label_raw[1]))),
                    )
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
        return zones

    def default_zone_layout(self):
        return {
            "image": "images/Одноэтажный комплекс Одуванчик.png",
            "zones": [
                {"id": 1, "name": "Зона 1", "polygons": [[[0.045, 0.077], [0.170, 0.077], [0.170, 0.406], [0.045, 0.406]]], "label": [0.107, 0.242]},
                {"id": 2, "name": "Зона 2", "polygons": [[[0.170, 0.077], [0.285, 0.077], [0.285, 0.406], [0.170, 0.406]]], "label": [0.227, 0.242]},
                {"id": 3, "name": "Зона 3", "polygons": [[[0.285, 0.077], [0.515, 0.077], [0.515, 0.406], [0.285, 0.406]]], "label": [0.400, 0.242]},
                {"id": 4, "name": "Зона 4", "polygons": [[[0.515, 0.077], [0.598, 0.077], [0.598, 0.406], [0.515, 0.406]]], "label": [0.556, 0.242]},
                {"id": 5, "name": "Зона 5", "polygons": [[[0.598, 0.077], [0.760, 0.077], [0.760, 0.406], [0.598, 0.406]]], "label": [0.679, 0.242]},
                {"id": 6, "name": "Зона 6", "polygons": [[[0.760, 0.077], [0.972, 0.077], [0.972, 0.406], [0.760, 0.406]]], "label": [0.866, 0.242]},
                {"id": 7, "name": "Зона 7", "polygons": [[[0.045, 0.539], [0.140, 0.539], [0.140, 0.925], [0.045, 0.925]]], "label": [0.093, 0.731]},
                {"id": 8, "name": "Зона 8", "polygons": [[[0.140, 0.539], [0.255, 0.539], [0.255, 0.925], [0.140, 0.925]]], "label": [0.197, 0.731]},
                {"id": 9, "name": "Зона 9", "polygons": [[[0.255, 0.539], [0.360, 0.539], [0.360, 0.925], [0.255, 0.925]]], "label": [0.308, 0.731]},
                {"id": 10, "name": "Зона 10", "polygons": [[[0.360, 0.539], [0.430, 0.539], [0.430, 0.925], [0.360, 0.925]]], "label": [0.395, 0.731]},
                {"id": 11, "name": "Зона 11", "polygons": [[[0.430, 0.539], [0.545, 0.539], [0.545, 0.925], [0.430, 0.925]]], "label": [0.488, 0.731]},
                {"id": 12, "name": "Зона 12", "polygons": [[[0.545, 0.539], [0.675, 0.539], [0.675, 0.925], [0.545, 0.925]]], "label": [0.610, 0.731]},
                {"id": 13, "name": "Зона 13", "polygons": [[[0.675, 0.539], [0.890, 0.539], [0.890, 0.925], [0.675, 0.925]]], "label": [0.782, 0.731]},
                {"id": 14, "name": "Зона 14", "polygons": [[[0.890, 0.539], [0.972, 0.539], [0.972, 0.925], [0.890, 0.925]]], "label": [0.931, 0.731]},
                {"id": 15, "name": "Зона 15", "polygons": [[[0.045, 0.406], [0.972, 0.406], [0.972, 0.539], [0.045, 0.539]]], "label": [0.510, 0.472]},
            ],
        }

    def update_loop(self):
        self.sim.tick()
        self.update_histories()
        self.update_ui()
        self.root.after(self.tick_interval_ms, self.update_loop)

    def blink_loop(self):
        self.blink_visible = not self.blink_visible
        self.redraw_map()
        self.root.after(self.blink_interval_ms, self.blink_loop)

    def update_histories(self):
        for idx, zone in enumerate(self.sim.zones):
            self.temp_history[idx].append(zone.temp)
            self.smoke_history[idx].append(zone.smoke)

    def update_ui(self):
        now = datetime.datetime.now()
        self.clock_label.configure(text=now.strftime("%H:%M:%S"))
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner)
        self.spinner_label.configure(text=self.spinner[self.spinner_index])
        self.cycle_label.configure(text=strings.t("cycle", count=self.sim.tick_count))

        state = self.sim.system_state()
        state_color = self.status_color(state)
        self.system_state_label.configure(
            text=strings.t("system_state", state=strings.status_label(state)),
            fg=state_color,
        )

        alarm_count = sum(1 for z in self.sim.zones if z.status == "ALARM")
        fault_count = sum(1 for z in self.sim.zones if z.status == "FAULT")
        self.info_label.configure(text=strings.t("info_summary", alarms=alarm_count, faults=fault_count))

        if alarm_count == 0 and fault_count == 0:
            self.alarm_acknowledged = False
            self.sound_silenced = False

        sounder_state = "IDLE"
        if alarm_count > 0:
            sounder_state = "SILENCED" if self.sound_silenced else "ACTIVE"
        self.sounder_label.configure(text=strings.t("sounders", state=strings.sounder_label(sounder_state)))

        self.update_alarm_sound(alarm_count > 0 and not self.sound_silenced)
        self.update_header_alarm_blink(alarm_count > 0, state_color)

        self.update_table()
        self.update_charts()
        self.sync_zone_controls()
        self.redraw_map()

        if self.sim.last_auto_event:
            event_type, zone = self.sim.last_auto_event
            self.log(strings.auto_event_message(event_type, zone.name))

    def update_header_alarm_blink(self, alarm_active, state_color):
        if alarm_active and self.blink_visible:
            self.title_label.configure(fg=self.alarm)
            self.clock_label.configure(fg=self.alarm)
            self.spinner_label.configure(fg=self.alarm)
            self.cycle_label.configure(fg=self.alarm)
            self.system_state_label.configure(fg=self.alarm)
            return

        self.title_label.configure(fg=self.text_color)
        self.clock_label.configure(fg=self.text_color)
        self.spinner_label.configure(fg=self.accent)
        self.cycle_label.configure(fg=self.subtext_color)
        self.system_state_label.configure(fg=state_color)

    def update_alarm_sound(self, should_play):
        if should_play:
            self.play_alarm_loop()
        else:
            self.stop_alarm_loop()

    def update_table(self):
        for idx, (zone, item_id) in enumerate(zip(self.sim.zones, self.tree_items)):
            self.tree.item(
                item_id,
                values=(
                    zone.name,
                    f"{zone.temp:5.1f}",
                    f"{zone.smoke:5.0f}",
                    f"{zone.co:5.0f}",
                    strings.status_label(zone.status),
                    strings.on_off(zone.fire_active),
                    strings.on_off(zone.manual_call),
                    strings.on_off(zone.fault_active),
                    strings.on_off(zone.sprinklers_on),
                    strings.on_off(zone.ventilation_on),
                ),
                tags=(zone.status,),
            )

            if zone.status != self.last_zone_status[idx]:
                self.log(strings.log_status_change(zone.name, zone.status))
                self.last_zone_status[idx] = zone.status

    def update_charts(self):
        idx = self.get_selected_zone_index()
        self.temp_chart.draw(self.temp_history[idx])
        self.smoke_chart.draw(self.smoke_history[idx])

    def sync_zone_controls(self):
        zone = self.get_selected_zone()
        self.sprinkler_var.set(zone.sprinklers_on)
        self.vent_var.set(zone.ventilation_on)
        self.auto_scenarios_var.set(self.sim.auto_scenarios)
        self.auto_recovery_var.set(self.sim.auto_recovery)

    def status_color(self, status):
        if status == "ALARM":
            return self.alarm
        if status == "FAULT":
            return self.fault
        return self.good

    def get_selected_zone_index(self):
        name = self.selected_zone_var.get()
        for idx, zone in enumerate(self.sim.zones):
            if zone.name == name:
                return idx
        return 0

    def get_selected_zone(self):
        return self.sim.zones[self.get_selected_zone_index()]

    def get_zone_by_id(self, zone_id):
        if 1 <= zone_id <= len(self.sim.zones):
            return self.sim.zones[zone_id - 1]
        return None

    def select_zone_by_id(self, zone_id, play_sound=True):
        zone = self.get_zone_by_id(zone_id)
        if zone is None:
            return

        new_idx = zone_id - 1
        changed = new_idx != self.last_selected_zone_index
        self.selected_zone_var.set(zone.name)
        self.last_selected_zone_index = new_idx

        if changed and play_sound:
            self.play_beep_sound()

        self.sync_zone_controls()
        self.update_charts()
        self.redraw_map()

    def on_zone_change(self, _event):
        new_idx = self.get_selected_zone_index()
        if new_idx != self.last_selected_zone_index:
            self.last_selected_zone_index = new_idx
            self.play_beep_sound()
        self.sync_zone_controls()
        self.update_charts()
        self.redraw_map()

    def on_top_frame_configure(self, event):
        if event.width <= 0:
            return
        map_target = int(event.width * 0.70)
        chart_target = max(220, event.width - map_target)
        self.top_frame.grid_columnconfigure(0, minsize=map_target)
        self.top_frame.grid_columnconfigure(1, minsize=chart_target)

    def on_map_canvas_configure(self, _event):
        self.redraw_map()

    def redraw_map(self):
        if not hasattr(self, "map_canvas"):
            return

        canvas_width = self.map_canvas.winfo_width()
        canvas_height = self.map_canvas.winfo_height()
        if canvas_width < 120 or canvas_height < 120:
            return

        self.map_canvas.delete("all")
        if self.map_original_image is None:
            self.map_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="Карта недоступна",
                fill=self.subtext_color,
                font=("Segoe UI", 10),
            )
            return

        if not self.update_map_image_scale(canvas_width, canvas_height):
            return

        image_width = self.map_image.width()
        image_height = self.map_image.height()
        base_x0 = (canvas_width - image_width) / 2
        base_y0 = (canvas_height - image_height) / 2
        x0 = base_x0 + self.map_pan_x
        y0 = base_y0 + self.map_pan_y
        x0, y0 = self.clamp_map_position(canvas_width, canvas_height, image_width, image_height, x0, y0)
        self.map_pan_x = x0 - base_x0
        self.map_pan_y = y0 - base_y0
        self.map_image_pos = (x0, y0)
        self.map_image_size = (image_width, image_height)

        self.map_canvas.create_image(x0, y0, image=self.map_image, anchor="nw")
        self.zone_hit_polygons = {}

        selected_zone_id = self.get_selected_zone_index() + 1
        for zone_id, zone in enumerate(self.sim.zones, start=1):
            layout_zone = self.zone_layout_by_id.get(zone_id)
            if not layout_zone:
                if zone_id not in self.map_missing_zone_logged:
                    self.queue_log(strings.t("log_zone_not_found", zone=zone.name))
                    self.map_missing_zone_logged.add(zone_id)
                continue

            pixel_polygons = []
            show_alert = zone.status in ("ALARM", "FAULT") and self.blink_visible
            zone_color = self.status_color(zone.status)
            fill = zone_color if show_alert else ""
            outline = zone_color if show_alert else self.idle_zone_outline
            width = 2 if show_alert else 1
            if zone_id == selected_zone_id:
                outline = self.accent
                width = 3

            for polygon in layout_zone["polygons"]:
                pixel_points = [self.normalized_to_canvas(x, y) for x, y in polygon]
                pixel_polygons.append(pixel_points)
                flat = [coord for point in pixel_points for coord in point]
                kwargs = {"fill": fill, "outline": outline, "width": width}
                if fill:
                    kwargs["stipple"] = "gray50"
                self.map_canvas.create_polygon(flat, **kwargs)

            self.zone_hit_polygons[zone_id] = pixel_polygons
            self.draw_zone_label(layout_zone, zone_id, zone.status, show_alert, zone_id == selected_zone_id)

    def draw_zone_label(self, layout_zone, zone_id, status, show_alert, selected):
        label = layout_zone.get("label")
        if not label:
            label = self.polygon_center(layout_zone["polygons"][0])
        x, y = self.normalized_to_canvas(label[0], label[1])

        label_text = f"{zone_id} {strings.status_short_label(status)}"
        if selected:
            bg_color = self.accent
            fg_color = "#ffffff"
        elif show_alert:
            bg_color = self.status_color(status)
            fg_color = "#ffffff"
        else:
            bg_color = "#ffffff"
            fg_color = self.text_color

        text_id = self.map_canvas.create_text(
            x,
            y,
            text=label_text,
            fill=fg_color,
            font=("Segoe UI", 8, "bold"),
        )
        x1, y1, x2, y2 = self.map_canvas.bbox(text_id)
        rect_id = self.map_canvas.create_rectangle(
            x1 - 3,
            y1 - 1,
            x2 + 3,
            y2 + 1,
            fill=bg_color,
            outline=self.border,
            width=1,
        )
        self.map_canvas.tag_raise(text_id, rect_id)

    def polygon_center(self, polygon):
        sum_x = sum(point[0] for point in polygon)
        sum_y = sum(point[1] for point in polygon)
        count = max(1, len(polygon))
        return sum_x / count, sum_y / count

    def update_map_image_scale(self, canvas_width, canvas_height):
        available_width = canvas_width - 12
        available_height = canvas_height - 12
        if available_width < 120 or available_height < 120:
            return False

        original_width = self.map_original_image.width()
        original_height = self.map_original_image.height()
        if original_width <= 0 or original_height <= 0:
            return False

        fit_scale = min(available_width / original_width, available_height / original_height)
        scale = fit_scale * self.map_zoom
        scale = max(0.05, min(4.0, scale))
        scale_fraction = Fraction(scale).limit_denominator(20)
        scale_key = (scale_fraction.numerator, scale_fraction.denominator)

        if scale_key not in self.map_image_cache:
            self.map_image_cache[scale_key] = self.map_original_image.zoom(
                scale_fraction.numerator, scale_fraction.numerator
            ).subsample(scale_fraction.denominator, scale_fraction.denominator)

        if self.map_image is None or scale_key != self.map_scale_key:
            self.map_scale_key = scale_key
            self.map_image = self.map_image_cache[scale_key]
            self.map_render_scale = self.map_image.width() / original_width

        return True

    def clamp_map_position(self, canvas_width, canvas_height, image_width, image_height, x0, y0):
        if image_width <= canvas_width:
            x0 = (canvas_width - image_width) / 2
        else:
            x0 = min(0, max(canvas_width - image_width, x0))

        if image_height <= canvas_height:
            y0 = (canvas_height - image_height) / 2
        else:
            y0 = min(0, max(canvas_height - image_height, y0))

        return x0, y0

    def normalized_to_canvas(self, nx, ny):
        x0, y0 = self.map_image_pos
        width, height = self.map_image_size
        return x0 + nx * width, y0 + ny * height

    def on_map_mouse_wheel(self, event):
        direction = 1 if event.delta > 0 else -1
        self.apply_map_zoom(event.x, event.y, direction)

    def on_map_wheel_up(self, event):
        self.apply_map_zoom(event.x, event.y, 1)

    def on_map_wheel_down(self, event):
        self.apply_map_zoom(event.x, event.y, -1)

    def apply_map_zoom(self, cursor_x, cursor_y, direction):
        if self.map_original_image is None:
            return

        canvas_width = self.map_canvas.winfo_width()
        canvas_height = self.map_canvas.winfo_height()
        if canvas_width < 120 or canvas_height < 120:
            return
        if self.map_render_scale <= 0:
            self.redraw_map()
            if self.map_render_scale <= 0:
                return

        factor = 1.15 if direction > 0 else 1 / 1.15
        old_zoom = self.map_zoom
        new_zoom = max(self.map_min_zoom, min(self.map_max_zoom, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-6:
            return

        old_x0, old_y0 = self.map_image_pos
        world_x = (cursor_x - old_x0) / self.map_render_scale
        world_y = (cursor_y - old_y0) / self.map_render_scale

        self.map_zoom = new_zoom
        if not self.update_map_image_scale(canvas_width, canvas_height):
            return

        image_width = self.map_image.width()
        image_height = self.map_image.height()
        new_x0 = cursor_x - world_x * self.map_render_scale
        new_y0 = cursor_y - world_y * self.map_render_scale
        base_x0 = (canvas_width - image_width) / 2
        base_y0 = (canvas_height - image_height) / 2
        self.map_pan_x = new_x0 - base_x0
        self.map_pan_y = new_y0 - base_y0

        self.redraw_map()

    def on_map_pan_start(self, event):
        self.map_pan_active = True
        self.map_pan_last = (event.x, event.y)

    def on_map_pan_move(self, event):
        if not self.map_pan_active or self.map_pan_last is None:
            return
        dx = event.x - self.map_pan_last[0]
        dy = event.y - self.map_pan_last[1]
        self.map_pan_x += dx
        self.map_pan_y += dy
        self.map_pan_last = (event.x, event.y)
        self.redraw_map()

    def on_map_pan_end(self, _event):
        self.map_pan_active = False
        self.map_pan_last = None

    def on_map_left_click(self, event):
        # Shift + LMB reserved for map panning.
        if event.state & 0x0001:
            return
        zone_id = self.find_zone_at_point(event.x, event.y)
        if zone_id:
            self.select_zone_by_id(zone_id, play_sound=True)

    def on_map_right_click(self, event):
        zone_id = self.find_zone_at_point(event.x, event.y)
        if not zone_id:
            return
        self.select_zone_by_id(zone_id, play_sound=True)
        self.show_zone_context_menu(event.x_root, event.y_root, zone_id)

    def find_zone_at_point(self, x, y):
        for zone_id, polygons in self.zone_hit_polygons.items():
            for polygon in polygons:
                if self.point_in_polygon(x, y, polygon):
                    return zone_id
        return None

    def point_in_polygon(self, x, y, polygon):
        inside = False
        point_count = len(polygon)
        j = point_count - 1
        for i in range(point_count):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersects = (yi > y) != (yj > y)
            if intersects:
                slope_x = (xj - xi) * (y - yi) / ((yj - yi) + 1e-12) + xi
                if x < slope_x:
                    inside = not inside
            j = i
        return inside

    def show_zone_context_menu(self, x_root, y_root, zone_id):
        zone = self.get_zone_by_id(zone_id)
        if zone is None:
            return

        self.context_zone_id = zone_id
        self.context_sprinkler_var.set(zone.sprinklers_on)
        self.context_vent_var.set(zone.ventilation_on)

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=strings.t("menu_zone_header", zone=zone.name), state="disabled")
        menu.add_separator()
        menu.add_command(label=strings.t("menu_fire"), command=lambda zid=zone_id: self.trigger_fire(zid))
        menu.add_command(label=strings.t("menu_smoke"), command=lambda zid=zone_id: self.trigger_smoke(zid))
        menu.add_command(label=strings.t("menu_manual_call"), command=lambda zid=zone_id: self.trigger_manual_call(zid))
        menu.add_command(label=strings.t("menu_fault"), command=lambda zid=zone_id: self.trigger_fault(zid))
        menu.add_separator()
        menu.add_command(label=strings.t("menu_clear_events"), command=lambda zid=zone_id: self.clear_events(zid))
        menu.add_command(label=strings.t("menu_clear_fault"), command=lambda zid=zone_id: self.clear_fault(zid))
        menu.add_separator()
        menu.add_checkbutton(
            label=strings.t("menu_sprinklers"),
            variable=self.context_sprinkler_var,
            command=lambda zid=zone_id: self.apply_zone_actuators(
                zid, sprinklers=self.context_sprinkler_var.get(), log_change=True
            ),
        )
        menu.add_checkbutton(
            label=strings.t("menu_ventilation"),
            variable=self.context_vent_var,
            command=lambda zid=zone_id: self.apply_zone_actuators(
                zid, vent=self.context_vent_var.get(), log_change=True
            ),
        )

        try:
            menu.tk_popup(x_root, y_root)
        finally:
            menu.grab_release()

    def resolve_zone(self, zone_id=None):
        if zone_id is not None:
            zone = self.get_zone_by_id(zone_id)
            if zone is not None:
                return zone
        return self.get_selected_zone()

    def trigger_fire(self, zone_id=None):
        zone = self.resolve_zone(zone_id)
        zone.fire_active = True
        zone.status = zone.evaluate_status()
        self.log(strings.t("log_manual_fire", zone=zone.name))
        self.update_ui()

    def trigger_smoke(self, zone_id=None):
        zone = self.resolve_zone(zone_id)
        zone.smoke_active = True
        zone.status = zone.evaluate_status()
        self.log(strings.t("log_manual_smoke", zone=zone.name))
        self.update_ui()

    def trigger_manual_call(self, zone_id=None):
        zone = self.resolve_zone(zone_id)
        zone.manual_call = True
        zone.status = zone.evaluate_status()
        self.log(strings.t("log_manual_call", zone=zone.name))
        self.update_ui()

    def trigger_fault(self, zone_id=None):
        zone = self.resolve_zone(zone_id)
        zone.fault_active = True
        zone.status = zone.evaluate_status()
        self.log(strings.t("log_manual_fault", zone=zone.name))
        self.update_ui()

    def clear_events(self, zone_id=None):
        zone = self.resolve_zone(zone_id)
        zone.clear_events(clear_fault=False, normalize=True)
        self.log(strings.t("log_clear_events", zone=zone.name))
        self.update_ui()

    def clear_fault(self, zone_id=None):
        zone = self.resolve_zone(zone_id)
        zone.clear_events(clear_fault=True, normalize=True)
        self.log(strings.t("log_clear_fault", zone=zone.name))
        self.update_ui()

    def toggle_auto(self):
        self.sim.auto_scenarios = self.auto_scenarios_var.get()
        self.sim.auto_recovery = self.auto_recovery_var.get()
        self.log(
            strings.t(
                "log_automation",
                auto_scenarios=strings.on_off(self.sim.auto_scenarios),
                auto_recovery=strings.on_off(self.sim.auto_recovery),
            )
        )

    def apply_zone_actuators(self, zone_id, sprinklers=None, vent=None, log_change=True):
        zone = self.get_zone_by_id(zone_id)
        if zone is None:
            return

        if sprinklers is not None:
            zone.sprinklers_on = bool(sprinklers)
        if vent is not None:
            zone.ventilation_on = bool(vent)

        if zone_id == self.get_selected_zone_index() + 1:
            self.sprinkler_var.set(zone.sprinklers_on)
            self.vent_var.set(zone.ventilation_on)

        if log_change:
            self.log(
                strings.t(
                    "log_actuators",
                    zone=zone.name,
                    sprinklers=strings.on_off(zone.sprinklers_on),
                    vent=strings.on_off(zone.ventilation_on),
                )
            )
        self.redraw_map()

    def toggle_actuators(self):
        zone_id = self.get_selected_zone_index() + 1
        self.apply_zone_actuators(
            zone_id,
            sprinklers=self.sprinkler_var.get(),
            vent=self.vent_var.get(),
            log_change=True,
        )

    def acknowledge_alarm(self):
        self.alarm_acknowledged = True
        self.log(strings.t("log_ack"))

    def silence_sounders(self):
        self.sound_silenced = not self.sound_silenced
        if self.sound_silenced:
            self.log(strings.t("log_silence_on"))
        else:
            self.log(strings.t("log_silence_off"))
        self.update_ui()

    def reset_system(self):
        for zone in self.sim.zones:
            zone.clear_events(clear_fault=True, normalize=True)
            zone.sprinklers_on = False
            zone.ventilation_on = True
        self.sound_silenced = False
        self.alarm_acknowledged = False
        self.log(strings.t("log_reset_done"))
        self.update_ui()

    def show_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.focus_set()
            return

        help_window = tk.Toplevel(self.root)
        help_window.title(strings.t("help_title"))
        help_window.configure(bg=self.panel_bg)
        help_window.geometry("560x420")
        help_window.resizable(False, False)

        text = tk.Text(
            help_window,
            wrap="word",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg=self.text_color,
            bd=1,
            relief="solid",
        )
        text.insert("1.0", strings.t("help_text"))
        text.configure(state="disabled")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        close_button = ttk.Button(help_window, text=strings.t("help_close"), command=help_window.destroy)
        close_button.pack(pady=(0, 10))

        self.help_window = help_window

    def mci_send(self, command):
        if self.winmm is None:
            return False
        buffer = ctypes.create_unicode_buffer(512)
        error_code = self.winmm.mciSendStringW(command, buffer, 511, 0)
        if error_code != 0 and not self.sound_error_logged:
            err_buffer = ctypes.create_unicode_buffer(256)
            self.winmm.mciGetErrorStringW(error_code, err_buffer, 255)
            message = err_buffer.value or str(error_code)
            self.queue_log(strings.t("log_sound_error", error=message))
            self.sound_error_logged = True
        return error_code == 0

    def mci_open_alias(self, alias, path):
        safe_path = str(path).replace('"', "")
        self.mci_send(f"stop {alias}")
        self.mci_send(f"close {alias}")
        return self.mci_send(f'open "{safe_path}" type mpegvideo alias {alias}')

    def play_alarm_loop(self):
        if self.alarm_audio_active or self.alarm_sound_path is None:
            return
        if self.mci_open_alias(self.alarm_alias, self.alarm_sound_path):
            if self.mci_send(f"play {self.alarm_alias} repeat"):
                self.alarm_audio_active = True

    def stop_alarm_loop(self):
        if not self.alarm_audio_active:
            return
        self.mci_send(f"stop {self.alarm_alias}")
        self.mci_send(f"close {self.alarm_alias}")
        self.alarm_audio_active = False

    def play_beep_sound(self):
        if self.beep_sound_path is None:
            return
        if self.mci_open_alias(self.beep_alias, self.beep_sound_path):
            self.mci_send(f"play {self.beep_alias} from 0")

    def on_close(self):
        self.stop_alarm_loop()
        self.mci_send(f"stop {self.beep_alias}")
        self.mci_send(f"close {self.beep_alias}")
        self.root.destroy()

    def log(self, message):
        if not hasattr(self, "log_text"):
            self.pending_logs.append(message)
            return

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"{timestamp}  {message}\\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
