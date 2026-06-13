import json

import pytest

from qsm import QSM, State, StateContext


class FileIOContext:
    def __init__(self, name: str, events: list[str] | None = None):
        self.name = name
        self.events = events or []


class FileIOStartState(State):
    def __init__(self, next_state: str, label: str):
        self.next_state = next_state
        self.label = label

    def execute(self, ctx: StateContext):
        ctx.context.events.append(self.label)
        ctx.queue.append(self.next_state)


class FileIOFinishState(State):
    def execute(self, ctx: StateContext):
        ctx.context.events.append(f"finished:{ctx.context.name}")


def test_from_json_text_builds_qsm_from_json_string() -> None:
    machine = QSM.from_json_text(json.dumps(_config()))

    assert isinstance(machine, QSM)
    assert machine.initial_state == "start"
    assert machine.current_state == "start"
    assert machine.queue.maxsize == 5
    assert isinstance(machine.context, FileIOContext)
    assert machine.context.name == "World"
    assert set(machine.state_map) == {"start", "finish"}
    assert isinstance(machine.state_map["start"], FileIOStartState)
    assert isinstance(machine.state_map["finish"], FileIOFinishState)


def test_from_json_builds_qsm_from_mapping() -> None:
    machine = QSM.from_json(_config())

    assert isinstance(machine, QSM)
    assert machine.initial_state == "start"
    assert machine.current_state == "start"
    assert machine.queue.maxsize == 5
    assert isinstance(machine.context, FileIOContext)
    assert isinstance(machine.state_map["start"], FileIOStartState)
    assert isinstance(machine.state_map["finish"], FileIOFinishState)


def test_from_json_text_constructs_state_kwargs() -> None:
    machine = QSM.from_json_text(json.dumps(_config()))

    start = machine.state_map["start"]

    assert isinstance(start, FileIOStartState)
    assert start.next_state == "finish"
    assert start.label == "started"


def test_from_json_text_configured_machine_can_loop() -> None:
    machine = QSM.from_json_text(json.dumps(_config()))

    machine.loop()

    assert machine.context.events == ["started", "finished:World"]
    assert machine.current_state == "finish"


def test_from_json_injects_runtime_kwargs_into_models() -> None:
    config = _config()
    events = ["existing"]
    config["initial_context"]["kwargs"]["name"] = "$name"
    config["initial_context"]["kwargs"]["events"] = "$events"
    config["states"]["start"]["kwargs"]["label"] = "$label"

    machine = QSM.from_json(
        config,
        name="Injected",
        events=events,
        label="runtime-label",
    )

    assert machine.context.name == "Injected"
    assert machine.context.events is events
    start = machine.state_map["start"]
    assert isinstance(start, FileIOStartState)
    assert start.next_state == "finish"
    assert start.label == "runtime-label"


def test_from_json_text_injects_runtime_kwargs_into_models() -> None:
    config = _config()
    events = ["existing"]
    config["initial_context"]["kwargs"]["name"] = "$name"
    config["initial_context"]["kwargs"]["events"] = "$events"
    config["states"]["start"]["kwargs"]["label"] = "$label"

    machine = QSM.from_json_text(
        json.dumps(config),
        name="Injected",
        events=events,
        label="runtime-label",
    )

    assert machine.context.name == "Injected"
    assert machine.context.events is events
    start = machine.state_map["start"]
    assert isinstance(start, FileIOStartState)
    assert start.next_state == "finish"
    assert start.label == "runtime-label"


def test_from_json_text_raises_for_malformed_json() -> None:
    with pytest.raises(ValueError):
        QSM.from_json_text("{not json")


def test_from_json_text_raises_for_bad_import_path() -> None:
    config = _config()
    config["states"]["start"]["model"] = "tests.test_fileio.DoesNotExist"

    with pytest.raises((AttributeError, ValueError)):
        QSM.from_json_text(json.dumps(config))


def _config() -> dict:
    return {
        "initial_state": "start",
        "initial_context": {
            "model": _model_path(FileIOContext),
            "kwargs": {
                "name": "World",
            },
        },
        "max_queue_size": 5,
        "states": {
            "start": {
                "model": _model_path(FileIOStartState),
                "kwargs": {
                    "next_state": "finish",
                    "label": "started",
                },
            },
            "finish": {
                "model": _model_path(FileIOFinishState),
                "kwargs": {},
            },
        },
    }


def _model_path(model: type) -> str:
    return f"{model.__module__}.{model.__qualname__}"
