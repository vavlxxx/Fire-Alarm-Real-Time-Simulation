import random

from simulation import FIRE, NORMAL, SMOKE, FireAlarmSim, Zone


def test_state_transitions_smoke_fire_hysteresis():
    zone = Zone("Z")

    zone.temp = 22.0
    zone.smoke = 46.0
    assert zone.evaluate_state() == SMOKE

    zone.state = SMOKE
    zone.smoke = 40.0
    assert zone.evaluate_state() == SMOKE

    zone.smoke = 34.0
    zone.temp = 22.0
    assert zone.evaluate_state() == NORMAL

    zone.state = SMOKE
    zone.temp = 56.0
    zone.smoke = 50.0
    assert zone.evaluate_state() == FIRE

    zone.state = FIRE
    zone.temp = 50.0
    zone.smoke = 40.0
    assert zone.evaluate_state() == FIRE

    zone.temp = 44.0
    zone.smoke = 34.0
    assert zone.evaluate_state() == NORMAL


def test_fire_priority_over_smoke():
    zone = Zone("Z")
    zone.temp = 60.0
    zone.smoke = 80.0
    assert zone.evaluate_state() == FIRE


def test_auto_actuation_enabled_flag():
    sim = FireAlarmSim(zone_count=1)
    zone = sim.zones[0]

    sim.auto_recovery = False
    sim.auto_control = False
    zone.trigger_smoke()
    sim.tick()
    assert zone.ventilation_on is False

    sim.auto_control = True
    zone.trigger_smoke()
    sim.tick()
    assert zone.ventilation_on is True


def test_ventilation_reduces_smoke():
    zone_no_vent = Zone("A")
    zone_no_vent.temp = 24.0
    zone_no_vent.smoke = 65.0

    zone_with_vent = Zone("B")
    zone_with_vent.temp = 24.0
    zone_with_vent.smoke = 65.0
    zone_with_vent.ventilation_on = True

    random.seed(123)
    zone_no_vent.step(auto_recovery=True, auto_control=False)

    random.seed(123)
    zone_with_vent.step(auto_recovery=True, auto_control=False)

    assert zone_with_vent.smoke < zone_no_vent.smoke


def test_sprinklers_reduce_temp_and_clear_fire():
    zone_no_sprinklers = Zone("A")
    zone_no_sprinklers.temp = 75.0
    zone_no_sprinklers.smoke = 70.0

    zone_with_sprinklers = Zone("B")
    zone_with_sprinklers.temp = 75.0
    zone_with_sprinklers.smoke = 70.0
    zone_with_sprinklers.sprinklers_on = True

    random.seed(77)
    zone_no_sprinklers.step(auto_recovery=True, auto_control=False)

    random.seed(77)
    zone_with_sprinklers.step(auto_recovery=True, auto_control=False)

    assert zone_with_sprinklers.temp < zone_no_sprinklers.temp
    assert zone_with_sprinklers.smoke <= zone_no_sprinklers.smoke

    zone = Zone("C")
    zone.temp = 90.0
    zone.smoke = 90.0
    zone.sprinklers_on = True
    zone.ventilation_on = True
    zone.state = FIRE

    random.seed(11)
    for _ in range(80):
        zone.sprinklers_on = True
        zone.ventilation_on = True
        zone.step(auto_recovery=True, auto_control=False)

    assert zone.state != FIRE
