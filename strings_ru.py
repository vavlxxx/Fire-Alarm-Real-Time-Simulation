UNIT_C = "°C"
UNIT_PPM = "ppm"
UNIT_CO = "CO"

TEXT = {
    "app_title": "Система пожарной сигнализации - имитация",
    "header_title": "Система пожарной сигнализации",
    "system_state": "Система: {state}",
    "cycle": "Цикл: {count}",
    "zone_map": "План помещения",
    "zone_overview": "Обзор зон",
    "map_legend": "Легенда статусов",
    "legend_normal": "Норма",
    "legend_alarm": "Тревога",
    "legend_fault": "Неисправность",
    "live_table": "Таблица датчиков",
    "tab_main": "Главный экран",
    "tab_data": "Данные",
    "tab_table": "Таблица",
    "tab_log": "Журнал",
    "charts_title": "Графики",
    "zone_view": "Зона:",
    "axis_time": "Время, с",
    "axis_temp": "Температура, °C",
    "axis_smoke": "Дымность, ppm",
    "controls_title": "Управление",
    "selected_zone": "Выбранная зона:",
    "scenario_triggers": "Сценарии",
    "automation": "Автоматизация",
    "actuators": "Приводы",
    "system_indicators": "Состояние системы",
    "event_log": "Журнал событий",
    "temp_chart": "Температура",
    "smoke_chart": "Дымность",
    "time_axis": "Время (с)",
    "info_summary": "Тревоги: {alarms}  Неисправности: {faults}",
    "sounders": "Оповещатели: {state}",
    "on": "ВКЛ",
    "off": "ВЫКЛ",
    "button_fire": "Смоделировать пожар",
    "button_smoke": "Смоделировать задымление",
    "button_manual_call": "Ручной извещатель",
    "button_fault": "Смоделировать неисправность",
    "button_clear_events": "Сбросить события",
    "button_clear_fault": "Сбросить неисправность",
    "button_ack": "Квитировать тревогу",
    "button_silence": "Отключить оповещатели",
    "button_reset": "Сброс системы",
    "check_auto_scenarios": "Автосценарии",
    "check_auto_recovery": "Автовосстановление",
    "check_sprinklers": "Спринклеры включены",
    "check_ventilation": "Дымоудаление включено",
    "col_zone": "Зона",
    "col_temp": "Темп., {c_unit}",
    "col_smoke": "Дым, {ppm}",
    "col_co": "{co}, {ppm}",
    "col_status": "Статус",
    "col_fire": "Пожар",
    "col_manual_call": "Ручной",
    "col_fault_flag": "Неиспр. датч.",
    "col_sprinkler": "Спринклеры",
    "col_vent": "Дымоудал.",
    "log_automation": "Автоматизация: автосценарии={auto_scenarios}, автовосстановление={auto_recovery}",
    "log_actuators": "Приводы для {zone}: спринклеры={sprinklers}, дымоудаление={vent}",
    "log_ack": "Тревога квитирована оператором",
    "log_silence_on": "Оповещатели отключены оператором",
    "log_silence_off": "Оповещатели снова включены",
    "log_reset_blocked": "Сброс невозможен: есть активные тревоги",
    "log_reset_done": "Сброс системы выполнен",
    "log_clear_events": "События сброшены для {zone}",
    "log_clear_fault": "Неисправность сброшена для {zone}",
    "log_manual_fire": "Ручное событие: пожар в {zone}",
    "log_manual_smoke": "Ручное событие: задымление в {zone}",
    "log_manual_call": "Ручной извещатель сработал в {zone}",
    "log_manual_fault": "Ручное событие: неисправность датчика в {zone}",
    "log_status_change": "{zone}: статус изменен на {status}",
    "reading": "Темп. {temp:4.1f} {c_unit} | Дым {smoke:4.0f} {ppm}",
    "zone_name": "Зона {index}",
    "help_title": "Справка",
    "help_button": "Справка",
    "help_text": "Мини-справка по работе:\n\n"
    "1) На вкладке \"Главный экран\" слева показана карта зон.\n"
    "2) Левая кнопка мыши по зоне - выбор, правая - меню действий зоны.\n"
    "3) Колесом мыши масштабируйте карту, средняя кнопка или Shift+ЛКМ - перемещение карты.\n"
    "4) Внизу экрана используйте быстрые кнопки и приводы.\n"
    "5) На вкладке \"Данные\" доступны таблица зон и журнал событий.\n\n"
    "Сигнализация:\n"
    "- При тревоге включается циклический звук и мигают надписи вверху.\n"
    "- При смене зоны воспроизводится короткий сигнал.\n"
    "- Сброс зоны/системы нормализует показания и устраняет активную тревогу.",
    "help_close": "Закрыть",
    "menu_zone_header": "Действия: {zone}",
    "menu_fire": "Пожар",
    "menu_smoke": "Задымление",
    "menu_manual_call": "Ручной извещатель",
    "menu_fault": "Неисправность",
    "menu_clear_events": "Сбросить события",
    "menu_clear_fault": "Сбросить неисправность",
    "menu_sprinklers": "Спринклеры",
    "menu_ventilation": "Дымоудаление",
    "log_zone_not_found": "Предостережение: разметка не найдена для {zone}",
    "log_layout_error": "Ошибка загрузки разметки зон: {error}",
    "log_sound_error": "Ошибка звука: {error}",
}

STATUS_LABELS = {
    "NORMAL": "Норма",
    "ALARM": "Тревога",
    "FAULT": "Неисправность",
}

STATUS_SHORT_LABELS = {
    "NORMAL": "НОРМА",
    "ALARM": "ТРЕВОГА",
    "FAULT": "НЕИСПР.",
}

SOUNDER_LABELS = {
    "IDLE": "Ожидание",
    "ACTIVE": "Активны",
    "SILENCED": "Отключены",
}

AUTO_EVENT_TEMPLATES = {
    "fire": "Автособытие: пожар в {zone}",
    "smoke": "Автособытие: задымление в {zone}",
    "fault": "Автособытие: неисправность датчика в {zone}",
}

DEFAULT_FORMATS = {
    "c_unit": UNIT_C,
    "ppm": UNIT_PPM,
    "co": UNIT_CO,
}


def t(key, **kwargs):
    params = DEFAULT_FORMATS.copy()
    params.update(kwargs)
    return TEXT[key].format(**params)


def zone_name(index):
    return t("zone_name", index=index + 1)


def status_label(status):
    return STATUS_LABELS.get(status, status)


def status_short_label(status):
    return STATUS_SHORT_LABELS.get(status, status)


def sounder_label(state):
    return SOUNDER_LABELS.get(state, state)


def on_off(value):
    return t("on") if value else t("off")


def reading_text(temp, smoke):
    return t("reading", temp=temp, smoke=smoke)


def auto_event_message(event_type, zone):
    template = AUTO_EVENT_TEMPLATES.get(event_type, "Автособытие: событие в {zone}")
    return template.format(zone=zone)


def log_status_change(zone, status):
    return t("log_status_change", zone=zone, status=status_label(status))
