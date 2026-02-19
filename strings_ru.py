UNIT_C = "C"
UNIT_PPM = "ppm"
UNIT_CO = "CO"

TRANSLIT = [
    ("Shch", "\u0429"),
    ("shch", "\u0449"),
    ("Yo", "\u0401"),
    ("yo", "\u0451"),
    ("Zh", "\u0416"),
    ("zh", "\u0436"),
    ("Kh", "\u0425"),
    ("kh", "\u0445"),
    ("Ts", "\u0426"),
    ("ts", "\u0446"),
    ("Ch", "\u0427"),
    ("ch", "\u0447"),
    ("Sh", "\u0428"),
    ("sh", "\u0448"),
    ("Yu", "\u042e"),
    ("yu", "\u044e"),
    ("Ya", "\u042f"),
    ("ya", "\u044f"),
    ("Eh", "\u042d"),
    ("eh", "\u044d"),
    ("A", "\u0410"),
    ("a", "\u0430"),
    ("B", "\u0411"),
    ("b", "\u0431"),
    ("V", "\u0412"),
    ("v", "\u0432"),
    ("G", "\u0413"),
    ("g", "\u0433"),
    ("D", "\u0414"),
    ("d", "\u0434"),
    ("E", "\u0415"),
    ("e", "\u0435"),
    ("Z", "\u0417"),
    ("z", "\u0437"),
    ("I", "\u0418"),
    ("i", "\u0438"),
    ("J", "\u0419"),
    ("j", "\u0439"),
    ("K", "\u041a"),
    ("k", "\u043a"),
    ("L", "\u041b"),
    ("l", "\u043b"),
    ("M", "\u041c"),
    ("m", "\u043c"),
    ("N", "\u041d"),
    ("n", "\u043d"),
    ("O", "\u041e"),
    ("o", "\u043e"),
    ("P", "\u041f"),
    ("p", "\u043f"),
    ("R", "\u0420"),
    ("r", "\u0440"),
    ("S", "\u0421"),
    ("s", "\u0441"),
    ("T", "\u0422"),
    ("t", "\u0442"),
    ("U", "\u0423"),
    ("u", "\u0443"),
    ("F", "\u0424"),
    ("f", "\u0444"),
    ("H", "\u0425"),
    ("h", "\u0445"),
    ("Y", "\u042b"),
    ("y", "\u044b"),
    ("'", "\u044c"),
]

RAW_TEXT = {
    "app_title": "Sistema pozharnoj signalizatsii - imitatsiya",
    "header_title": "Sistema pozharnoj signalizatsii",
    "system_state": "Sistema: {state}",
    "cycle": "Tsikl: {count}",
    "zone_overview": "Obzor zon",
    "live_table": "Tablica datchikov",
    "charts_title": "Grafiki",
    "zone_view": "Zona:",
    "controls_title": "Upravlenie",
    "selected_zone": "Vybrannaya zona:",
    "scenario_triggers": "Stsenarii",
    "automation": "Avtomatizatsiya",
    "actuators": "Privody",
    "system_indicators": "Sostoyanie sistemy",
    "event_log": "Zhurnal sobytij",
    "temp_chart": "Temperatura",
    "smoke_chart": "Dymnost'",
    "time_axis": "Vremya (s)",
    "info_summary": "Trevogi: {alarms}  Neispravnosti: {faults}  Predtrevogi: {prealarms}",
    "sounders": "Opoveshchateli: {state}",
    "on": "VKL",
    "off": "VYK",
    "button_fire": "Smodelirovat' pozhar",
    "button_smoke": "Smodelirovat' zadymlenie",
    "button_manual_call": "Ruchnoj izveshchatel'",
    "button_fault": "Smodelirovat' neispravnost'",
    "button_clear_events": "Sbrosit' sobytiya",
    "button_clear_fault": "Sbrosit' neispravnost'",
    "button_ack": "Kvitirovat' trevogu",
    "button_silence": "Otklyuchit' opoveshchateli",
    "button_reset": "Sbros sistemy",
    "check_auto_scenarios": "Avtostsenarii",
    "check_auto_recovery": "Avtovosstanovlenie",
    "check_sprinklers": "Sprinklery vklyucheny",
    "check_ventilation": "Dymoudalenie vklyucheno",
    "col_zone": "Zona",
    "col_temp": "Temp., {c_unit}",
    "col_smoke": "Dym, {ppm}",
    "col_co": "{co}, {ppm}",
    "col_status": "Status",
    "col_sprinkler": "Sprinklery",
    "col_vent": "Dymoudal.",
    "log_automation": "Avtomatizatsiya: avtostsenarii={auto_scenarios}, avtovosstanovlenie={auto_recovery}",
    "log_actuators": "Privody dlya {zone}: sprinklery={sprinklers}, dymoudalenie={vent}",
    "log_ack": "Trevoga kvitirovana operatorom",
    "log_silence_on": "Opoveshchateli otklyucheny operatorom",
    "log_silence_off": "Opoveshchateli snova vklyucheny",
    "log_reset_blocked": "Sbros nevozmozhen: est' aktivnye trevogi ili predtrevogi",
    "log_reset_done": "Sbros sistemy vypolnen",
    "log_clear_events": "Sobytiya sbrosheny dlya {zone}",
    "log_clear_fault": "Neispravnost' sbroshena dlya {zone}",
    "log_manual_fire": "Ruchnoe sobytie: pozhar v {zone}",
    "log_manual_smoke": "Ruchnoe sobytie: zadymlenie v {zone}",
    "log_manual_call": "Ruchnoj izveshchatel' srabotal v {zone}",
    "log_manual_fault": "Ruchnoe sobytie: neispravnost' datchika v {zone}",
    "log_status_change": "{zone}: status izmenen na {status}",
    "reading": "Temp. {temp:4.1f} {c_unit} | Dym {smoke:4.0f} {ppm}",
    "zone_name": "Zona {index}",
    "help_title": "Spravka",
    "help_button": "Spravka",
    "help_text": "Mini spravka po rabote:\n\n"
    "1) Vyberite zonu v spiske.\n"
    "2) V razdele Stsenarii smodelirujte pozhar, zadymlenie, neispravnost' ili ruchnoj izveshchatel'.\n"
    "3) V razdele Privody vklyuchite sprinklery i dymoudalenie dlya stabilizatsii.\n"
    "4) Kvitirovat' trevogu i Otklyuchit' opoveshchateli - dejstviya operatora.\n"
    "5) Sbros sistemy dostupen tol'ko pri otsutstvii trevog i predtrevog.\n\n"
    "Avtomatika:\n"
    "- Avtostsenarii generirujut sluchajnye sobytiya.\n"
    "- Avtovosstanovlenie pomogaet snizit' pokazateli pri vklyuchennyh privodah.",
    "help_close": "Zakryt'",
}

STATUS_LABELS_RAW = {
    "NORMAL": "Norma",
    "PREALARM": "Predtrevoga",
    "ALARM": "Trevoga",
    "FAULT": "Neispravnost'",
}

SOUNDER_LABELS_RAW = {
    "IDLE": "Ozhidanie",
    "ACTIVE": "Aktivny",
    "SILENCED": "Otklyucheny",
}

AUTO_EVENT_TEMPLATES_RAW = {
    "fire": "Avtosobytie: pozhar v {zone}",
    "smoke": "Avtosobytie: zadymlenie v {zone}",
    "fault": "Avtosobytie: neispravnost' datchika v {zone}",
}

DEFAULT_FORMATS = {
    "c_unit": UNIT_C,
    "ppm": UNIT_PPM,
    "co": UNIT_CO,
}


def to_ru(text):
    parts = []
    buffer = []
    in_brace = False
    for ch in text:
        if ch == "{":
            if buffer:
                parts.append(_translit("".join(buffer)))
                buffer = []
            in_brace = True
            parts.append(ch)
            continue
        if ch == "}" and in_brace:
            in_brace = False
            parts.append(ch)
            continue
        if in_brace:
            parts.append(ch)
        else:
            buffer.append(ch)
    if buffer:
        parts.append(_translit("".join(buffer)))
    return "".join(parts)


def _translit(text):
    for src, dst in TRANSLIT:
        text = text.replace(src, dst)
    return text


TEXT = {key: to_ru(value) for key, value in RAW_TEXT.items()}
STATUS_LABELS = {key: to_ru(value) for key, value in STATUS_LABELS_RAW.items()}
SOUNDER_LABELS = {key: to_ru(value) for key, value in SOUNDER_LABELS_RAW.items()}
AUTO_EVENT_TEMPLATES = {key: to_ru(value) for key, value in AUTO_EVENT_TEMPLATES_RAW.items()}


def t(key, **kwargs):
    params = DEFAULT_FORMATS.copy()
    params.update(kwargs)
    return TEXT[key].format(**params)


def zone_name(index):
    return t("zone_name", index=index + 1)


def status_label(status):
    return STATUS_LABELS.get(status, status)


def sounder_label(state):
    return SOUNDER_LABELS.get(state, state)


def on_off(value):
    return t("on") if value else t("off")


def reading_text(temp, smoke):
    return t("reading", temp=temp, smoke=smoke)


def auto_event_message(event_type, zone):
    template = AUTO_EVENT_TEMPLATES.get(event_type, to_ru("Avtosobytie: sobytie v {zone}"))
    return template.format(zone=zone)


def log_status_change(zone, status):
    return t("log_status_change", zone=zone, status=status_label(status))
