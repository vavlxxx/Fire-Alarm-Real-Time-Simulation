import random

NORMAL = "NORMAL"
SMOKE = "SMOKE"
FIRE = "FIRE"

MAX_TEMP = 120.0
MAX_SMOKE = 200.0

SMOKE_THRESHOLD = 50.0
SMOKE_RESET_THRESHOLD = 30.0
FIRE_THRESHOLD = 54.0
FIRE_RESET_THRESHOLD = 40.0


class Zone:
    def __init__(self, name):
        self.name = name
        self.base_temp = 22.0
        self.base_smoke = 8.0

        self.temp = self.base_temp
        self.smoke = self.base_smoke

        self.temp_velocity = 0.0
        self.smoke_velocity = 0.0

        self.fire_intensity = 0.0
        self.fuel = 1.0

        self.sprinklers_on = False
        self.ventilation_on = False
        self.state = NORMAL

        self.fire_time = 0.0
        self.smolder = 0.0
        self.smoke_sensor = self.base_smoke
        self.temp_sensor = self.base_temp

    def evaluate_state(self, auto_recovery):
        if self.temp >= FIRE_THRESHOLD:
            return FIRE
        
        if self.state == NORMAL and self.smoke >= SMOKE_THRESHOLD:
            return SMOKE
            
        if self.state == SMOKE and self.temp >= FIRE_THRESHOLD:
            return FIRE

        if auto_recovery:
            if self.state == FIRE:
                if self.temp < FIRE_RESET_THRESHOLD:
                    if self.smoke >= SMOKE_RESET_THRESHOLD:
                        return SMOKE
                    else:
                        return NORMAL
                else:
                    return FIRE
                    
            if self.state == SMOKE:
                if self.smoke < SMOKE_RESET_THRESHOLD:
                    return NORMAL
                else:
                    return SMOKE
                    
        return self.state

    def apply_auto_actuation(self):
        if self.state == FIRE:
            self.sprinklers_on = True
            self.ventilation_on = True
        elif self.state == SMOKE:
            self.ventilation_on = True
            self.sprinklers_on = False
        else:
            self.sprinklers_on = False
            self.ventilation_on = False

    def step(self, auto_recovery, auto_control):
        dt = 1.0

        self.state = self.evaluate_state(auto_recovery)
        if auto_control:
            self.apply_auto_actuation()

        burning = self.fire_intensity > 0.001

        t_grow = 90.0
        if burning and self.fuel > 0.0:
            self.fire_time += dt * random.uniform(0.5, 1.5)
            target_I = min(1.0, (self.fire_time / t_grow) ** 2)
            target_I += random.uniform(-0.05, 0.1)
        else:
            target_I = 0.0

        if burning and not self.sprinklers_on:
            target_I = max(target_I, self.fire_intensity)

        if self.sprinklers_on:
            target_I = 0.0
            self.fire_intensity -= 0.05 * dt
            self.fire_time = max(0.0, self.fire_time - 5.0 * dt)

        tau_fire = random.uniform(5.0, 15.0)
        self.fire_intensity += (target_I - self.fire_intensity) * (dt / tau_fire)
        self.fire_intensity = max(0.0, min(1.5, self.fire_intensity))

        burn_rate = 0.0025
        self.fuel = max(0.0, self.fuel - burn_rate * self.fire_intensity * dt)
        if self.fuel == 0.0:
            self.fire_time = 0.0

        self.smolder *= 0.985

        temp_rise_max = 85.0
        temp_target = self.base_temp + temp_rise_max * self.fire_intensity

        if self.ventilation_on:
            temp_target -= 8.0

        if self.sprinklers_on:
            temp_target -= 18.0

        tau_temp = random.uniform(15.0, 30.0)
        self.temp += (temp_target - self.temp) * (dt / tau_temp)

        self.temp_velocity += random.uniform(-0.35, 0.35)
        self.temp_velocity *= 0.65
        self.temp += self.temp_velocity * dt + random.uniform(-0.1, 0.1)

        self.temp = max(self.base_temp - 2.0, min(MAX_TEMP, self.temp))

        smoke_gen_fire = random.uniform(2.5, 4.0) * self.fire_intensity
        smoke_gen_smolder = random.uniform(1.2, 2.5) * self.smolder
        smoke_gen = smoke_gen_fire + smoke_gen_smolder

        k_decay = 0.012

        k_vent = 0.0
        if self.ventilation_on:
            k_vent = 0.15
            self.smolder *= 0.9

        if self.sprinklers_on:
            k_decay += 0.05

        self.smoke += smoke_gen * dt
        self.smoke -= (k_decay + k_vent) * self.smoke * dt

        self.smoke_velocity += random.uniform(-0.6, 0.6)
        self.smoke_velocity *= 0.65
        self.smoke += self.smoke_velocity * dt + random.uniform(-0.2, 0.2)

        self.smoke = max(0.0, min(MAX_SMOKE, self.smoke))

        tau_sensor_temp = 6.0
        tau_sensor_smoke = 8.0
        self.temp_sensor += (self.temp - self.temp_sensor) * (dt / tau_sensor_temp)
        self.smoke_sensor += (self.smoke - self.smoke_sensor) * (dt / tau_sensor_smoke)

        self.state = self.evaluate_state(auto_recovery)
        if auto_control:
            self.apply_auto_actuation()

    def trigger_fire(self):

        self.fire_time = max(self.fire_time, 60.0)
        self.fire_intensity = max(self.fire_intensity, 0.8)
        self.fuel = 1.0

    def trigger_smoke(self):

        self.smolder = max(self.smolder, 4.0)

    def clear_events(self):
        self.temp = self.base_temp
        self.smoke = self.base_smoke
        self.fire_intensity = 0.0
        self.fuel = 1.0
        self.temp_velocity = 0.0
        self.smoke_velocity = 0.0
        self.sprinklers_on = False
        self.ventilation_on = False
        self.state = NORMAL


class FireAlarmSim:
    def __init__(self, zone_count=5, zone_name_factory=None):
        if zone_name_factory is None:
            zone_name_factory = lambda i: f"Zone {i + 1}"  # noqa

        self.zones = [Zone(zone_name_factory(i)) for i in range(zone_count)]

        self.auto_scenarios = False
        self.auto_recovery = True
        self.auto_control = False

        self.tick_count = 0
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
