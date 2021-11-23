import anyio
import asyncio


def start_component(config: dict, state: dict, component: str):
    assert component not in state  # TODO: IDEMPOTENT, RESTARTS?
    assert component in config
    component_config = config.get(component)
    assert "start" in component_config
    component_constructor_config = component_config.get("config", {})
    start_fn = component_config.get("start")
    try:
        if asyncio.iscoroutinefunction(start_fn):
            new_component = anyio.run(start_fn, state, component_constructor_config)
        else:
            new_component = start_fn(state=state, config=component_constructor_config)
        # TODO: check new component?
        state[component] = new_component
    except Exception as e:
        raise IOError(f"Exception raised starting {component}.")
    else:
        return (state, new_component)


def stop_component(config: dict, state: dict, component: str):
    assert component in config
    component_config = config.get(component)
    assert "stop" in component_config
    stop_fn = component_config.get("stop")

    assert component in state
    existing_component = state.get(component)
    try:
        if asyncio.iscoroutinefunction(stop_fn):
            anyio.run(stop_fn, existing_component)
        else:
            stop_fn(existing_component)
        state.pop(component)
    except Exception as e:
        raise IOError(f"Exception raised stoping {component}")
    else:
        return (state, existing_component)


def start_system(config: dict, state: dict):
    for component in config:
        start_component(config, state, component)


def stop_system(config: dict, state: dict):
    for component in reversed(config):
        if component in state:
            stop_component(config, state, component)
