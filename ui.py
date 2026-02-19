
import datetime
import tkinter as tk
from collections import deque
from tkinter import ttk

import strings_ru as strings
from charts import LineChart
from simulation import FireAlarmSim


class FireAlarmApp:
    def __init__(self, root):
        self.root = root
        self.sim = FireAlarmSim(zone_name_factory=strings.zone_name)
        self.tick_interval_ms = 1000
        self.spinner = ["|", "/", "-", "\\"]
        self.spinner_index = 0

        self.bg = "#f4f1ea"
        self.panel_bg = "#fbfaf6"
        self.text_color = "#2f2f2f"
        self.subtext_color = "#5f5f5f"
        self.accent = "#1565c0"
        self.good = "#2e7d32"
        self.warn = "#f9a825"
        self.alarm = "#c62828"
        self.fault = "#6d4c41"
        self.grid_color = "#ddd6cc"
        self.border = "#d0c8bc"

        self.history_len = 60
        self.temp_history = [deque(maxlen=self.history_len) for _ in self.sim.zones]
        self.smoke_history = [deque(maxlen=self.history_len) for _ in self.sim.zones]
        self.last_zone_status = [zone.status for zone in self.sim.zones]

        self.sound_silenced = False
        self.alarm_acknowledged = False
        self.help_window = None

        self.selected_zone_var = tk.StringVar(value=self.sim.zones[0].name)
        self.auto_scenarios_var = tk.BooleanVar(value=True)
        self.auto_recovery_var = tk.BooleanVar(value=True)
        self.sprinkler_var = tk.BooleanVar(value=False)
        self.vent_var = tk.BooleanVar(value=True)

        self.build_ui()
        self.update_histories()
        self.update_histories()
        self.update_ui()
        self.root.after(self.tick_interval_ms, self.update_loop)

    def build_ui(self):
        self.root.title(strings.t("app_title"))
        self.root.configure(bg=self.bg)
        self.root.geometry("1240x780")
        self.root.minsize(1080, 700)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24, background=self.panel_bg)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#d8e6f8")])

        header = tk.Frame(self.root, bg=self.bg)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header.columnconfigure(0, weight=1)

        title = tk.Label(
            header,
            text=strings.t("header_title"),
            font=("Segoe UI", 16, "bold"),
            bg=self.bg,
            fg=self.text_color,
        )
        title.grid(row=0, column=0, sticky="w")

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
            right_header, text="00:00:00", font=("Segoe UI", 12), bg=self.bg, fg=self.text_color
        )
        self.clock_label.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.spinner_label = tk.Label(
            right_header, text=self.spinner[0], font=("Segoe UI", 12, "bold"), bg=self.bg, fg=self.accent
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

        main = tk.Frame(self.root, bg=self.bg)
        main.grid(row=1, column=0, sticky="nsew")
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=1)
        main.rowconfigure(0, weight=1)

        self.build_zone_panel(main)
        self.build_chart_panel(main)
        self.build_control_panel(main)
        self.build_log_panel()

    def build_zone_panel(self, parent):
        zone_panel = tk.Frame(parent, bg=self.panel_bg, bd=1, relief="solid")
        zone_panel.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
        zone_panel.columnconfigure(0, weight=1)
        zone_panel.rowconfigure(2, weight=1)

        label = tk.Label(
            zone_panel,
            text=strings.t("zone_overview"),
            font=("Segoe UI", 11, "bold"),
            bg=self.panel_bg,
            fg=self.text_color,
        )
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        cards_frame = tk.Frame(zone_panel, bg=self.panel_bg)
        cards_frame.grid(row=1, column=0, sticky="ew", padx=8)
        for col in range(2):
            cards_frame.columnconfigure(col, weight=1)

        self.zone_cards = []
        for i, zone in enumerate(self.sim.zones):
            card = tk.Frame(cards_frame, bg=self.panel_bg, highlightbackground=self.border, highlightthickness=1)
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)
            indicator = tk.Frame(card, width=8, bg=self.good)
            indicator.pack(side="left", fill="y")
            content = tk.Frame(card, bg=self.panel_bg)
            content.pack(side="left", fill="both", expand=True, padx=6, pady=4)
            name_label = tk.Label(
                content, text=zone.name, font=("Segoe UI", 9, "bold"), bg=self.panel_bg, fg=self.text_color
            )
            name_label.pack(anchor="w")
            status_label = tk.Label(
                content,
                text=strings.status_label("NORMAL"),
                font=("Segoe UI", 9),
                bg=self.panel_bg,
                fg=self.good,
            )
            status_label.pack(anchor="w")
            reading_label = tk.Label(
                content,
                text=strings.reading_text(zone.temp, zone.smoke),
                font=("Segoe UI", 8),
                bg=self.panel_bg,
                fg=self.subtext_color,
            )
            reading_label.pack(anchor="w")
            self.zone_cards.append(
                {
                    "indicator": indicator,
                    "status": status_label,
                    "reading": reading_label,
                }
            )

        table_label = tk.Label(
            zone_panel,
            text=strings.t("live_table"),
            font=("Segoe UI", 10, "bold"),
            bg=self.panel_bg,
            fg=self.text_color,
        )
        table_label.grid(row=2, column=0, sticky="w", padx=10, pady=(8, 4))

        table_frame = tk.Frame(zone_panel, bg=self.panel_bg)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("zone", "temp", "smoke", "co", "status", "sprinkler", "vent")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
        self.tree.heading("zone", text=strings.t("col_zone"))
        self.tree.heading("temp", text=strings.t("col_temp"))
        self.tree.heading("smoke", text=strings.t("col_smoke"))
        self.tree.heading("co", text=strings.t("col_co"))
        self.tree.heading("status", text=strings.t("col_status"))
        self.tree.heading("sprinkler", text=strings.t("col_sprinkler"))
        self.tree.heading("vent", text=strings.t("col_vent"))
        self.tree.column("zone", width=90, anchor="w")
        self.tree.column("temp", width=80, anchor="e")
        self.tree.column("smoke", width=90, anchor="e")
        self.tree.column("co", width=80, anchor="e")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("sprinkler", width=70, anchor="center")
        self.tree.column("vent", width=70, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.tag_configure("NORMAL", background="#e8f5e9")
        self.tree.tag_configure("PREALARM", background="#fff8e1")
        self.tree.tag_configure("ALARM", background="#ffebee")
        self.tree.tag_configure("FAULT", background="#efebe9")

        self.tree_items = []
        for zone in self.sim.zones:
            item_id = self.tree.insert("", "end", values=(zone.name, "", "", "", "", "", ""))
            self.tree_items.append(item_id)

    def build_chart_panel(self, parent):
        chart_panel = tk.Frame(parent, bg=self.panel_bg, bd=1, relief="solid")
        chart_panel.grid(row=0, column=1, sticky="nsew", padx=8, pady=6)
        chart_panel.columnconfigure(0, weight=1)

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
            width=12,
            state="readonly",
        )
        zone_selector.grid(row=0, column=2, sticky="e", padx=(6, 0))
        zone_selector.bind("<<ComboboxSelected>>", self.on_zone_change)

        self.temp_chart = LineChart(
            chart_panel,
            title=strings.t("temp_chart"),
            y_label=strings.UNIT_C,
            y_min=0,
            y_max=120,
            line_color="#f57c00",
            bg=self.panel_bg,
            text_color=self.text_color,
            grid_color=self.grid_color,
            max_points=self.history_len,
            x_label=strings.t("time_axis"),
        )
        self.temp_chart.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 8))

        self.smoke_chart = LineChart(
            chart_panel,
            title=strings.t("smoke_chart"),
            y_label=strings.UNIT_PPM,
            y_min=0,
            y_max=200,
            line_color="#1565c0",
            bg=self.panel_bg,
            text_color=self.text_color,
            grid_color=self.grid_color,
            max_points=self.history_len,
            x_label=strings.t("time_axis"),
        )
        self.smoke_chart.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def build_control_panel(self, parent):
        control_panel = tk.Frame(parent, bg=self.panel_bg, bd=1, relief="solid")
        control_panel.grid(row=0, column=2, sticky="nsew", padx=8, pady=6)
        control_panel.columnconfigure(0, weight=1)

        label = tk.Label(
            control_panel,
            text=strings.t("controls_title"),
            font=("Segoe UI", 11, "bold"),
            bg=self.panel_bg,
            fg=self.text_color,
        )
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        selector_frame = tk.Frame(control_panel, bg=self.panel_bg)
        selector_frame.grid(row=1, column=0, sticky="ew", padx=10)
        selector_label = tk.Label(
            selector_frame,
            text=strings.t("selected_zone"),
            font=("Segoe UI", 9),
            bg=self.panel_bg,
            fg=self.subtext_color,
        )
        selector_label.pack(side="left")
        zone_selector = ttk.Combobox(
            selector_frame,
            textvariable=self.selected_zone_var,
            values=[z.name for z in self.sim.zones],
            width=12,
            state="readonly",
        )
        zone_selector.pack(side="left", padx=(6, 0))
        zone_selector.bind("<<ComboboxSelected>>", self.on_zone_change)

        scenario_frame = tk.LabelFrame(
            control_panel,
            text=strings.t("scenario_triggers"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        scenario_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 4))
        scenario_frame.columnconfigure(0, weight=1)

        ttk.Button(scenario_frame, text=strings.t("button_fire"), command=self.trigger_fire).grid(
            row=0, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_smoke"), command=self.trigger_smoke).grid(
            row=1, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_manual_call"), command=self.trigger_manual_call).grid(
            row=2, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_fault"), command=self.trigger_fault).grid(
            row=3, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_clear_events"), command=self.clear_events).grid(
            row=4, column=0, sticky="ew", padx=6, pady=4
        )
        ttk.Button(scenario_frame, text=strings.t("button_clear_fault"), command=self.clear_fault).grid(
            row=5, column=0, sticky="ew", padx=6, pady=4
        )

        auto_frame = tk.LabelFrame(
            control_panel,
            text=strings.t("automation"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        auto_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 4))
        auto_frame.columnconfigure(0, weight=1)
        ttk.Checkbutton(
            auto_frame,
            text=strings.t("check_auto_scenarios"),
            variable=self.auto_scenarios_var,
            command=self.toggle_auto,
        ).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(
            auto_frame,
            text=strings.t("check_auto_recovery"),
            variable=self.auto_recovery_var,
            command=self.toggle_auto,
        ).grid(row=1, column=0, sticky="w", padx=6, pady=4)

        actuator_frame = tk.LabelFrame(
            control_panel,
            text=strings.t("actuators"),
            bg=self.panel_bg,
            fg=self.text_color,
            font=("Segoe UI", 9, "bold"),
            labelanchor="n",
        )
        actuator_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(6, 4))
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
        info_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=(6, 10))
        info_frame.columnconfigure(0, weight=1)

        self.info_label = tk.Label(
            info_frame,
            text=strings.t("info_summary", alarms=0, faults=0, prealarms=0),
            font=("Segoe UI", 9),
            bg=self.panel_bg,
            fg=self.text_color,
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

    def build_log_panel(self):
        log_frame = tk.Frame(self.root, bg=self.panel_bg, bd=1, relief="solid")
        log_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)

        log_label = tk.Label(
            log_frame,
            text=strings.t("event_log"),
            font=("Segoe UI", 10, "bold"),
            bg=self.panel_bg,
            fg=self.text_color,
        )
        log_label.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))

        text_frame = tk.Frame(log_frame, bg=self.panel_bg)
        text_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        text_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            text_frame,
            height=7,
            wrap="word",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg=self.text_color,
            bd=1,
            relief="solid",
        )
        self.log_text.grid(row=0, column=0, sticky="ew")
        self.log_text.configure(state="disabled")

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def update_loop(self):
        self.sim.tick()
        self.update_histories()
        self.update_ui()
        self.root.after(self.tick_interval_ms, self.update_loop)

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
        prealarm_count = sum(1 for z in self.sim.zones if z.status == "PREALARM")
        self.info_label.configure(
            text=strings.t("info_summary", alarms=alarm_count, faults=fault_count, prealarms=prealarm_count)
        )

        if alarm_count == 0 and fault_count == 0:
            self.alarm_acknowledged = False
            self.sound_silenced = False

        sounder_state = "IDLE"
        if alarm_count > 0:
            sounder_state = "SILENCED" if self.sound_silenced else "ACTIVE"
        self.sounder_label.configure(
            text=strings.t("sounders", state=strings.sounder_label(sounder_state))
        )

        self.update_zone_cards()
        self.update_table()
        self.update_charts()
        self.sync_zone_controls()

        if self.sim.last_auto_event:
            event_type, zone = self.sim.last_auto_event
            self.log(strings.auto_event_message(event_type, zone.name))

    def update_zone_cards(self):
        for zone, card in zip(self.sim.zones, self.zone_cards):
            color = self.status_color(zone.status)
            card["indicator"].configure(bg=color)
            card["status"].configure(text=strings.status_label(zone.status), fg=color)
            card["reading"].configure(text=strings.reading_text(zone.temp, zone.smoke))

    def update_table(self):
        for zone, item_id in zip(self.sim.zones, self.tree_items):
            self.tree.item(
                item_id,
                values=(
                    zone.name,
                    f"{zone.temp:5.1f}",
                    f"{zone.smoke:5.0f}",
                    f"{zone.co:5.0f}",
                    strings.status_label(zone.status),
                    strings.on_off(zone.sprinklers_on),
                    strings.on_off(zone.ventilation_on),
                ),
                tags=(zone.status,),
            )

            idx = self.sim.zones.index(zone)
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
        if status == "PREALARM":
            return self.warn
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

    def on_zone_change(self, _event):
        self.sync_zone_controls()

    def trigger_fire(self):
        zone = self.get_selected_zone()
        zone.fire_active = True
        self.log(strings.t("log_manual_fire", zone=zone.name))

    def trigger_smoke(self):
        zone = self.get_selected_zone()
        zone.smoke_active = True
        self.log(strings.t("log_manual_smoke", zone=zone.name))

    def trigger_manual_call(self):
        zone = self.get_selected_zone()
        zone.manual_call = True
        self.log(strings.t("log_manual_call", zone=zone.name))

    def trigger_fault(self):
        zone = self.get_selected_zone()
        zone.fault_active = True
        self.log(strings.t("log_manual_fault", zone=zone.name))

    def clear_events(self):
        zone = self.get_selected_zone()
        zone.clear_events(clear_fault=False)
        self.log(strings.t("log_clear_events", zone=zone.name))

    def clear_fault(self):
        zone = self.get_selected_zone()
        zone.clear_events(clear_fault=True)
        self.log(strings.t("log_clear_fault", zone=zone.name))

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

    def toggle_actuators(self):
        zone = self.get_selected_zone()
        zone.sprinklers_on = self.sprinkler_var.get()
        zone.ventilation_on = self.vent_var.get()
        self.log(
            strings.t(
                "log_actuators",
                zone=zone.name,
                sprinklers=strings.on_off(zone.sprinklers_on),
                vent=strings.on_off(zone.ventilation_on),
            )
        )

    def acknowledge_alarm(self):
        self.alarm_acknowledged = True
        self.log(strings.t("log_ack"))

    def silence_sounders(self):
        if self.sound_silenced:
            self.sound_silenced = False
            self.log(strings.t("log_silence_off"))
        else:
            self.sound_silenced = True
            self.log(strings.t("log_silence_on"))

    def reset_system(self):
        if any(zone.status in ("ALARM", "PREALARM") for zone in self.sim.zones):
            self.log(strings.t("log_reset_blocked"))
            return
        for zone in self.sim.zones:
            zone.clear_events(clear_fault=True)
            zone.sprinklers_on = False
            zone.ventilation_on = True
        self.sound_silenced = False
        self.alarm_acknowledged = False
        self.log(strings.t("log_reset_done"))

    def show_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.focus_set()
            return

        help_window = tk.Toplevel(self.root)
        help_window.title(strings.t("help_title"))
        help_window.configure(bg=self.panel_bg)
        help_window.geometry("520x360")
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

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"{timestamp}  {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

