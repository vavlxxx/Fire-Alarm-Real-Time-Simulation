UNIT_C = "°C"
UNIT_PPM = "ppm"

TEXT = {
    "app_title": "Система пожарной сигнализации - имитация СРВ",
    "header_title": "Система пожарной сигнализации",
    "system_state": "Система: {state}",
    "cycle": "Цикл: {count}",
    "tab_main": "Главный экран",
    "tab_data": "Данные",
    "zone_map": "План помещения",
    "map_legend": "Легенда статусов",
    "legend_normal": "Норма",
    "legend_smoke": "Избыточный дым",
    "legend_fire": "Избыточная температура (пожар)",
    "controls_title": "Управление",
    "selected_zone": "Выбранная зона:",
    "scenario_triggers": "Сценарии",
    "automation": "Автоматизация",
    "actuators": "Приводы",
    "system_indicators": "Состояние системы",
    "event_log": "Журнал событий",
    "charts_title": "Графики выбранной зоны",
    "button_fire": "Смоделировать пожар",
    "button_smoke": "Смоделировать задымление",
    "button_clear_events": "Сброс зоны",
    "button_reset": "Сброс системы",
    "check_auto_scenarios": "Автосценарии",
    "check_auto_recovery": "Автовосстановление",
    "check_auto_control": "Автовключение приводов",
    "check_sprinklers": "Спринклеры включены",
    "check_ventilation": "Дымоудаление включено",
    "info_summary": "Задымления: {smoke}  Пожары: {fire}",
    "tab_table": "Таблица зон",
    "col_zone": "Зона",
    "col_temp": "Температура, {c_unit}",
    "col_smoke": "Дым, {ppm}",
    "col_state": "Состояние",
    "col_sprinkler": "Спринклеры",
    "col_vent": "Дымоудаление",
    "on": "ВКЛ",
    "off": "ВЫКЛ",
    "help_title": "Справка",
    "help_button": "Справка",
    "help_close": "Закрыть",
    "help_text": (
        "Краткое руководство по работе:\n\n"
        "1) На вкладке 'Главный экран' слева отображается интерактивная карта зон.\n"
        "2) Масштабирование выполняется колесом мыши, панорамирование - перетаскиванием ЛКМ.\n"
        "3) ЛКМ по зоне выбирает ее; ПКМ открывает контекстное меню действий и приводов.\n"
        "4) Справа сверху расположено управление: сценарии, автоматика и ручные приводы.\n"
        "5) Справа снизу расположен журнал событий системы.\n"
        "6) На вкладке 'Данные' доступна таблица зон и графики температуры/дыма.\n"
        "7) Клик по строке таблицы переключает активную зону и обновляет графики.\n\n"
        "Состояния зон:\n"
        "- Норма\n"
        "- Избыточный дым\n"
        "- Избыточная температура (пожар)\n\n"
        "Автоматизация:\n"
        "- При активном флаге автоматики и состоянии 'Избыточный дым' автоматически включается дымоудаление.\n"
        "- При активном флаге автоматики и состоянии 'Пожар' автоматически включаются спринклеры и дымоудаление.\n"
        "- После возврата к 'Норме' приводы автоматически отключаются.\n\n"
        "Автор программы: Нефедов Владимир Владимирович, студент группы ИВТ-432Б."
    ),
    "menu_zone_header": "Действия: {zone}",
    "menu_fire": "Пожар",
    "menu_smoke": "Задымление",
    "menu_clear_events": "Сброс зоны",
    "menu_sprinklers": "Спринклеры",
    "menu_ventilation": "Дымоудаление",
    "log_automation": "Автоматизация: автосценарии={auto_scenarios}, автовосстановление={auto_recovery}, автоприводы={auto_control}",
    "log_actuators_manual": "Приводы для {zone} (ручное): спринклеры={sprinklers}, дымоудаление={vent}",
    "log_actuators_auto": "Приводы для {zone} (авто): спринклеры={sprinklers}, дымоудаление={vent}",
    "log_reset_done": "Сброс системы выполнен",
    "log_clear_events": "События сброшены для {zone}",
    "log_manual_fire": "Ручное событие: пожар в {zone}",
    "log_manual_smoke": "Ручное событие: задымление в {zone}",
    "log_status_change": "{zone}: состояние изменено на {state}",
    "log_layout_error": "Ошибка загрузки разметки зон: {error}",
    "log_zone_not_found": "Предостережение: разметка не найдена для {zone}",
}

STATE_LABELS = {
    "NORMAL": "Норма",
    "SMOKE": "Избыточный дым",
    "FIRE": "Избыточная температура (пожар)",
}

STATE_SHORT_LABELS = {
    "NORMAL": "НОРМА",
    "SMOKE": "ДЫМ",
    "FIRE": "ПОЖАР",
}

AUTO_EVENT_TEMPLATES = {
    "fire": "Автособытие: пожар в {zone}",
    "smoke": "Автособытие: задымление в {zone}",
}

DEFAULT_FORMATS = {
    "c_unit": UNIT_C,
    "ppm": UNIT_PPM,
}


def t(key, **kwargs):
    params = DEFAULT_FORMATS.copy()
    params.update(kwargs)
    return TEXT[key].format(**params)


def zone_name(index):
    return f"Зона {index + 1}"


def state_label(state):
    return STATE_LABELS.get(state, state)


def state_short_label(state):
    return STATE_SHORT_LABELS.get(state, state)


def on_off(value):
    return t("on") if value else t("off")


def auto_event_message(event_type, zone):
    template = AUTO_EVENT_TEMPLATES.get(event_type, "Автособытие: событие в {zone}")
    return template.format(zone=zone)


def log_state_change(zone, state):
    return t("log_status_change", zone=zone, state=state_label(state))
