import random


NORMAL = "NORMAL"
SMOKE = "SMOKE"
FIRE = "FIRE"

SMOKE_THRESHOLD = 45.0
SMOKE_RESET_THRESHOLD = 35.0
FIRE_THRESHOLD = 55.0
FIRE_RESET_THRESHOLD = 45.0


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


class Zone:
    def __init__(self, name):
        self.name = name
        self.base_temp = 22.0
        self.base_smoke = 8.0
        self.temp = self.base_temp
        self.smoke = self.base_smoke
        self.sprinklers_on = False
        self.ventilation_on = False
        self.state = NORMAL

    def evaluate_state(self):
        if self.temp >= FIRE_THRESHOLD:
            return FIRE
        if self.smoke >= SMOKE_THRESHOLD:
            return SMOKE
        if self.temp < FIRE_RESET_THRESHOLD and self.smoke < SMOKE_RESET_THRESHOLD:
            return NORMAL
        return self.state

    def apply_auto_actuation(self):
        if self.state == FIRE:
            self.sprinklers_on = True
            self.ventilation_on = True
        elif self.state == SMOKE:
            self.sprinklers_on = False
            self.ventilation_on = True
        else:
            self.sprinklers_on = False
            self.ventilation_on = False

    def step(self, auto_recovery, auto_control):
        self.state = self.evaluate_state()
        if auto_control:
            self.apply_auto_actuation()

        temp_delta = 0.0
        smoke_delta = 0.0

        if self.state == FIRE:
            temp_delta += random.uniform(1.1, 2.0)
            smoke_delta += random.uniform(1.8, 3.1)
        elif self.state == SMOKE:
            temp_delta += random.uniform(0.0, 0.5)
            smoke_delta += random.uniform(1.0, 1.9)
        else:
            temp_delta += (self.base_temp - self.temp) * 0.18 + random.uniform(-0.2, 0.2)
            smoke_delta += (self.base_smoke - self.smoke) * 0.25 + random.uniform(-0.3, 0.3)

        if auto_recovery and self.ventilation_on:
            smoke_delta -= random.uniform(1.3, 2.2)
            temp_delta -= random.uniform(0.0, 0.2)

        if auto_recovery and self.sprinklers_on:
            temp_delta -= random.uniform(2.8, 3.8)
            smoke_delta -= random.uniform(0.7, 1.4)

        self.temp = clamp(self.temp + temp_delta, 0.0, 120.0)
        self.smoke = clamp(self.smoke + smoke_delta, 0.0, 200.0)
        self.state = self.evaluate_state()

        if auto_control:
            self.apply_auto_actuation()

    def normalize_readings(self):
        self.temp = self.base_temp
        self.smoke = self.base_smoke

    def trigger_fire(self):
        self.temp = max(self.temp, FIRE_THRESHOLD + 10.0)
        self.smoke = max(self.smoke, SMOKE_THRESHOLD + 15.0)
        self.state = self.evaluate_state()

    def trigger_smoke(self):
        self.smoke = max(self.smoke, SMOKE_THRESHOLD + 12.0)
        self.state = self.evaluate_state()

    def clear_events(self):
        self.normalize_readings()
        self.sprinklers_on = False
        self.ventilation_on = False
        self.state = self.evaluate_state()


class FireAlarmSim:
    def __init__(self, zone_count=15, zone_name_factory=None):
        if zone_name_factory is None:
            zone_name_factory = lambda i: f"Zone {i + 1}"
        self.zones = [Zone(zone_name_factory(i)) for i in range(zone_count)]
        self.tick_count = 0
        self.auto_scenarios = False
        self.auto_recovery = True
        self.auto_control = False
        self.last_auto_event = None

    def tick(self):
        self.tick_count += 1
        self.last_auto_event = None
        if self.auto_scenarios:
            self.maybe_trigger_random_event()
        for zone in self.zones:
            zone.step(self.auto_recovery, self.auto_control)

    def maybe_trigger_random_event(self):
        if random.random() >= 0.01:
            return
        zone = random.choice(self.zones)
        event = random.choice(["fire", "smoke"])
        if event == "fire":
            zone.trigger_fire()
        else:
            zone.trigger_smoke()
        self.last_auto_event = (event, zone)

    def system_state(self):
        states = [zone.state for zone in self.zones]
        if FIRE in states:
            return FIRE
        if SMOKE in states:
            return SMOKE
        return NORMAL
