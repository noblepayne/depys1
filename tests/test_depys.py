import datetime
import time

import anyio
import pytest

import depys


def _start_sync(state, config):
    time_to_sleep = config["time_to_sleep"]
    time.sleep(time_to_sleep)
    return {"slept": time_to_sleep, "stopped": False}


def _stop_sync(component):
    component["stopped"] = True


async def _start_async(state, config):
    time_to_sleep = config["time_to_sleep"]
    await anyio.sleep(time_to_sleep)
    return {"slept": time_to_sleep, "stopped": False}


async def _stop_async(component):
    component["stopped"] = True


_simple_config = {
    "sync": {"start": _start_sync, "stop": _stop_sync, "config": {"time_to_sleep": 2}},
    "async": {
        "start": _start_async,
        "stop": _stop_async,
        "config": {"time_to_sleep": 3},
    },
}


@pytest.fixture
def config():
    return _simple_config


def _start_component(config, state, comp_key):
    start = datetime.datetime.now()
    depys.start_component(config, state, comp_key)
    stop = datetime.datetime.now()
    return stop - start


@pytest.mark.parametrize("comp_key", ("sync", "async"))
def test_start_component(config, comp_key):
    state = {}
    expected_time_to_sleep = config[comp_key]["config"]["time_to_sleep"]
    td = _start_component(config, state, comp_key)

    assert td >= datetime.timedelta(seconds=expected_time_to_sleep)
    assert comp_key in state
    assert state[comp_key]["slept"] == expected_time_to_sleep
    assert state[comp_key]["stopped"] == False


@pytest.mark.parametrize("comp_key", ("sync", "async"))
def test_stop_component(config, comp_key):
    state = {}
    # Start.
    _start_component(config, state, comp_key)
    assert comp_key in state
    # Stop.
    _, component = depys.stop_component(config, state, comp_key)
    assert comp_key not in state
    assert component["stopped"] == True


def _start_systems(config, state, state2):
    start = datetime.datetime.now()
    # Start manually.
    for component in config:
        depys.start_component(config, state, component)
    # Start with helper.
    depys.start_system(config, state2)
    stop = datetime.datetime.now()
    return stop - start


def _expected_time_to_sleep(config):
    to_sleep = 0
    for _, conf in config.items():
        to_sleep += conf["config"]["time_to_sleep"]
    return datetime.timedelta(seconds=to_sleep)


def test_start_system(config):
    state = {}
    state2 = {}
    td = _start_systems(config, state, state2)
    assert td >= _expected_time_to_sleep(config)
    assert state == state2


def test_stop_system(config):
    state = {}
    depys.start_system(config, state)
    assert state != {}
    old_state = state.copy()  # N.B. not deep copy.
    depys.stop_system(config, state)
    assert state != old_state
    assert state == {}
    for comp_key, comp in state.items():
        assert comp["stopped"] == True
