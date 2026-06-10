import threading
import time
from queue import Full

import pytest

from qsm.deque import StringDequeQueue


def test_append_gets_items_in_fifo_order() -> None:
    queue = StringDequeQueue()

    queue.append("a")
    queue.append("b")
    queue.append("c")

    assert queue.get_nowait() == "a"
    assert queue.get_nowait() == "b"
    assert queue.get_nowait() == "c"


def test_prepend_gets_items_before_existing_items() -> None:
    queue = StringDequeQueue()

    queue.append("b")
    queue.prepend("a")
    queue.append("c")

    assert queue.get_nowait() == "a"
    assert queue.get_nowait() == "b"
    assert queue.get_nowait() == "c"


def test_prepend_nowait_respects_maxsize() -> None:
    queue = StringDequeQueue(maxsize=1)

    queue.append_nowait("a")

    with pytest.raises(Full):
        queue.prepend_nowait("b")


def test_append_rejects_non_strings() -> None:
    queue = StringDequeQueue()

    with pytest.raises(TypeError):
        queue.append(123)  # type: ignore[arg-type]


def test_prepend_rejects_non_strings() -> None:
    queue = StringDequeQueue()

    with pytest.raises(TypeError):
        queue.prepend(object())  # type: ignore[arg-type]


def test_negative_timeout_raises_value_error() -> None:
    queue = StringDequeQueue(maxsize=1)
    queue.append("a")

    with pytest.raises(ValueError):
        queue.append("b", timeout=-1)


def test_append_timeout_raises_full_when_queue_stays_full() -> None:
    queue = StringDequeQueue(maxsize=1)
    queue.append("a")

    with pytest.raises(Full):
        queue.append("b", timeout=0.01)


def test_blocking_append_waits_until_space_is_available() -> None:
    queue = StringDequeQueue(maxsize=1)
    queue.append("a")

    def consume_later() -> None:
        time.sleep(0.01)
        assert queue.get() == "a"

    thread = threading.Thread(target=consume_later)
    thread.start()

    queue.append("b", timeout=1)

    thread.join(timeout=1)
    assert not thread.is_alive()
    assert queue.get_nowait() == "b"


def test_task_done_and_join_work_for_prepended_items() -> None:
    queue = StringDequeQueue()

    queue.prepend("a")

    assert queue.get_nowait() == "a"
    queue.task_done()

    join_thread = threading.Thread(target=queue.join)
    join_thread.start()
    join_thread.join(timeout=1)

    assert not join_thread.is_alive()
