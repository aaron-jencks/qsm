from queue import Empty
from typing import Any, Dict, Optional

from .deque import StringDequeQueue
from .exceptions import NoSuchStateException
from .states import State, StateContext


class QSM:
    def __init__(self, initial_context: Any = None, initial_state: str = "initial_state", max_queue_size: Optional[int] = None):
        self.queue = StringDequeQueue(maxsize=max_queue_size) if max_queue_size is not None else StringDequeQueue()
        self.state_map: Dict[str, State] = {}
        self.current_state: str = initial_state
        self.context = initial_context

    def get_next_state(self) -> Optional[str]:
        try:
            self.current_state = self.queue.get_nowait()
            return self.current_state
        except Empty:
            return None

    def execute_state(self, name: str):
        if name not in self.state_map:
            raise NoSuchStateException(name)
        ctx = StateContext(
            queue=self.queue,
            context=self.context,
        )
        return self.state_map[name].execute(ctx)

    def execute_current_state(self):
        return self.execute_state(self.current_state)

    def loop(self):
        while not self.queue.empty():
            state = self.get_next_state()
            if state is not None:
                self.execute_current_state()
