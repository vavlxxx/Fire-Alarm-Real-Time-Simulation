import random


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


class Zone:
    def __init__(self, name):
        self.name = name
        self.base_temp = 22.0
        self.base_smoke = 8.0
        self.base_co = 4.0
        self.temp = self.base_temp
        self.smoke = self.base_smoke
        self.co = self.base_co
        self.fire_active = False
        self.smoke_active = False
        self.fault_active = False
        self.manual_call = False
        self.sprinklers_on = False
        self.ventilation_on = True
        self.status = "NORMAL"

    def step(self, auto_recovery):
        if self.fault_active:
            self.temp = clamp(self.temp + random.uniform(-0.3, 0.3), 0, 120)
            self.smoke = clamp(self.smoke + random.uniform(-0.6, 0.6), 0, 200)
            self.co = clamp(self.co + random.uniform(-0.3, 0.3), 0, 120)
        elif self.fire_active:
            temp_rise = 1.6
            smoke_rise = 2.2
            co_rise = 1.1
            if auto_recovery and self.sprinklers_on:
                temp_rise *= 0.35
                smoke_rise *= 0.4
                co_rise *= 0.6
                self.temp -= 0.4
                self.smoke -= 0.6
            if auto_recovery and self.ventilation_on:
                smoke_rise *= 0.85
            self.temp = clamp(self.temp + temp_rise + random.uniform(-0.2, 0.4), 0, 120)
            self.smoke = clamp(self.smoke + smoke_rise + random.uniform(-0.3, 0.5), 0, 200)
            self.co = clamp(self.co + co_rise + random.uniform(-0.2, 0.3), 0, 120)
            if auto_recovery and self.sprinklers_on and self.temp < 35 and self.smoke < 20:
                self.fire_active = False
        elif self.smoke_active:
            smoke_rise = 1.4
            if auto_recovery and self.ventilation_on:
                smoke_rise *= 0.5
                self.smoke -= 0.4
            self.temp = clamp(self.temp + 0.2 + random.uniform(-0.2, 0.3), 0, 120)
            self.smoke = clamp(self.smoke + smoke_rise + random.uniform(-0.3, 0.5), 0, 200)
            self.co = clamp(self.co + 0.5 + random.uniform(-0.2, 0.3), 0, 120)
            if auto_recovery and self.ventilation_on and self.smoke < 20:
                self.smoke_active = False
        else:
            self.temp = self.temp + (self.base_temp - self.temp) * 0.15 + random.uniform(-0.2, 0.2)
            self.smoke = self.smoke + (self.base_smoke - self.smoke) * 0.2 + random.uniform(-0.3, 0.3)
            self.co = self.co + (self.base_co - self.co) * 0.2 + random.uniform(-0.2, 0.2)
            self.temp = clamp(self.temp, 0, 120)
            self.smoke = clamp(self.smoke, 0, 200)
            self.co = clamp(self.co, 0, 120)

        self.status = self.evaluate_status()

    def evaluate_status(self):
        if self.fault_active:
            return "FAULT"
        if self.manual_call:
            return "ALARM"
        if self.fire_active or self.smoke_active:
            return "ALARM"
        if self.temp >= 65 or self.smoke >= 60 or self.co >= 55:
            return "ALARM"
        return "NORMAL"

    def normalize_readings(self):
        self.temp = self.base_temp
        self.smoke = self.base_smoke
        self.co = self.base_co

    def clear_events(self, clear_fault, normalize=False):
        self.fire_active = False
        self.smoke_active = False
        self.manual_call = False
        if clear_fault:
            self.fault_active = False
        if normalize:
            self.normalize_readings()
        self.status = self.evaluate_status()


class FireAlarmSim:
    def __init__(self, zone_count=15, zone_name_factory=None):
        if zone_name_factory is None:
            zone_name_factory = lambda i: f"Zone {i + 1}"
        self.zones = [Zone(zone_name_factory(i)) for i in range(zone_count)]
        self.tick_count = 0
        self.auto_scenarios = False
        self.auto_recovery = True
        self.last_auto_event = None

    def tick(self):
        self.tick_count += 1
        self.last_auto_event = None
        if self.auto_scenarios:
            self.maybe_trigger_random_event()
        for zone in self.zones:
            zone.step(self.auto_recovery)

    def maybe_trigger_random_event(self):
        if random.random() < 0.01:
            candidates = [
                zone
                for zone in self.zones
                if not (zone.fire_active or zone.smoke_active or zone.fault_active)
            ]
            if not candidates:
                return
            zone = random.choice(candidates)
            event = random.choice(["fire", "smoke", "fault"])
            if event == "fire":
                zone.fire_active = True
            elif event == "smoke":
                zone.smoke_active = True
            else:
                zone.fault_active = True
            self.last_auto_event = (event, zone)

    def system_state(self):
        statuses = [zone.status for zone in self.zones]
        if "ALARM" in statuses:
            return "ALARM"
        if "FAULT" in statuses:
            return "FAULT"
        return "NORMAL"
