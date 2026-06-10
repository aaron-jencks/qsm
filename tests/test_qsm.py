import pytest

from qsm import QSM, State, StateContext
from qsm.exceptions import NoSuchStateException


class RecordingState(State):
    def __init__(self, name: str, calls: list[str]):
        self.name = name
        self.calls = calls

    def execute(self, ctx: StateContext):
        self.calls.append(self.name)


def test_get_next_state_returns_none_when_queue_is_empty() -> None:
    machine = QSM()

    assert machine.get_next_state() is None


def test_get_next_state_updates_current_state() -> None:
    machine = QSM()
    machine.queue.append("next")

    assert machine.get_next_state() == "next"
    assert machine.current_state == "next"


def test_execute_state_raises_for_unknown_state() -> None:
    machine = QSM()

    with pytest.raises(NoSuchStateException):
        machine.execute_state("missing")


def test_execute_state_passes_queue_and_context_to_state() -> None:
    seen: dict[str, object] = {}

    class ContextState(State):
        def execute(self, ctx: StateContext):
            seen["queue"] = ctx.queue
            seen["context"] = ctx.context

    context = {"name": "world"}
    machine = QSM(initial_context=context)
    machine.state_map["context"] = ContextState()

    machine.execute_state("context")
    assert seen["queue"] is machine.queue
    assert seen["context"] is context


def test_execute_current_state_returns_state_result() -> None:
    calls: list[str] = []
    machine = QSM(initial_state="ready")
    machine.state_map["ready"] = RecordingState("ready", calls)

    machine.execute_current_state()
    assert calls == ["ready"]


def test_loop_executes_queued_states_in_order() -> None:
    class InitialState(State):
        def execute(self, ctx: StateContext) -> None:
            ctx.queue.append("first", "second")

    calls: list[str] = []
    machine = QSM()
    machine.state_map["initial_state"] = InitialState()
    machine.state_map["first"] = RecordingState("first", calls)
    machine.state_map["second"] = RecordingState("second", calls)

    machine.loop()

    assert calls == ["first", "second"]
    assert machine.current_state == "second"


def test_state_can_append_more_states_during_execution() -> None:
    calls: list[str] = []

    class AppendState(State):
        def execute(self, ctx: StateContext) -> None:
            calls.append("append")
            ctx.queue.append("next")

    machine = QSM(initial_state="append")
    machine.state_map["append"] = AppendState()
    machine.state_map["next"] = RecordingState("next", calls)

    machine.loop()

    assert calls == ["append", "next"]


def test_state_can_prepend_more_states_during_execution_wo_flush() -> None:
    calls: list[str] = []

    class PrependState(State):
        def execute(self, ctx: StateContext) -> None:
            calls.append("prepend")
            ctx.queue.prepend("urgent")

    machine = QSM()
    machine.state_map["prepend"] = PrependState()
    machine.state_map["later"] = RecordingState("later", calls)
    machine.state_map["urgent"] = RecordingState("urgent", calls)

    machine.queue.append("prepend", "later")
    machine.loop(flush=False)

    assert calls == ["prepend", "urgent", "later"]


def test_states_share_mutable_context() -> None:
    class IncrementState(State):
        def execute(self, ctx: StateContext) -> None:
            ctx.context["count"] += 1

    class IncrementInitialState(State):
        def execute(self, ctx: StateContext) -> None:
            ctx.context["count"] = 0
            ctx.queue.append("increment", "increment")

    context = {"count": 0}
    machine = QSM(initial_context=context)
    machine.state_map["initial_state"] = IncrementInitialState()
    machine.state_map["increment"] = IncrementState()

    machine.loop()

    assert context == {"count": 2}
