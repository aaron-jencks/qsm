import pytest

from qsm.exceptions import NoSuchHandlerException, NoSuchStateException
from qsm.qsm import QSM
from qsm.states import State, StateContent, StateContext


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


def test_state_uses_default_handler_when_content_is_none() -> None:
    state = State()

    def handler(ctx: StateContext) -> StateContent:
        return StateContent(type="result", payload=ctx.content)

    state.default_handler = handler

    assert state.execute(ctx=_ctx(content=None)) == StateContent(
        type="result",
        payload=None,
    )


def test_state_uses_only_registered_handler_when_no_default_exists() -> None:
    state = State()

    def handler(ctx: StateContext) -> StateContent:
        return StateContent(type="result", payload="ok")

    state.handlers["only"] = handler

    assert state.execute(ctx=_ctx(content=None)) == StateContent(
        type="result",
        payload="ok",
    )


def test_state_raises_when_no_content_and_multiple_handlers_without_default() -> None:
    state = State()
    state.handlers["a"] = lambda ctx: None
    state.handlers["b"] = lambda ctx: None

    with pytest.raises(NoSuchHandlerException):
        state.execute(ctx=_ctx(content=None))


def test_state_dispatches_by_content_type() -> None:
    state = State()
    state.handlers["event"] = lambda ctx: StateContent(
        type="result",
        payload=ctx.content.payload if ctx.content is not None else None,
    )

    result = state.execute(_ctx(StateContent(type="event", payload="hello")))

    assert result == StateContent(type="result", payload="hello")


def test_execute_current_state_returns_handler_result() -> None:
    machine = QSM(initial_state="ready")
    state = State()
    state.default_handler = lambda ctx: StateContent(type="done", payload=True)
    machine.state_map["ready"] = state

    assert machine.execute_current_state() == StateContent(
        type="done",
        payload=True,
    )


def _ctx(content: StateContent | None) -> StateContext:
    return StateContext(queue=None, content=content)
