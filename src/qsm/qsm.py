from queue import Empty
from typing import Any, Dict, Optional

from .deque import StringDequeQueue
from .exceptions import NoSuchStateException
from .states import State, StateContext


class QSM:
    """Queued state machine.

    A ``QSM`` stores pending state names in a queue, resolves each name through
    ``state_map``, and executes states until no pending states remain.
    """

    def __init__(self, initial_context: Any = None, initial_state: str = "initial_state", max_queue_size: Optional[int] = None):
        """Create a queued state machine.

        Args:
            initial_context: Shared workflow data passed to every state.
            initial_state: State name used when ``loop`` is called without an
                explicit initial state.
            max_queue_size: Optional maximum number of queued states.
        """
        self.queue = StringDequeQueue(maxsize=max_queue_size) if max_queue_size is not None else StringDequeQueue()
        self.state_map: Dict[str, State] = {}
        self.initial_state = initial_state
        self.current_state: str = initial_state
        self.context = initial_context

    def get_next_state(self) -> Optional[str]:
        """Dequeues the next state name and makes it current.

        Returns ``None`` when no state is queued.
        """
        try:
            self.current_state = self.queue.get_nowait()
            return self.current_state
        except Empty:
            return None

    def execute_state(self, name: str):
        """Execute a registered state by name.

        Raises:
            NoSuchStateException: If ``name`` is not registered in
                ``state_map``.
        """
        if name not in self.state_map:
            raise NoSuchStateException(name)
        ctx = StateContext(
            queue=self.queue,
            context=self.context,
        )
        self.state_map[name].execute(ctx)

    def execute_current_state(self):
        """Execute the state named by ``current_state``."""
        self.execute_state(self.current_state)

    def loop(self, flush: bool = True):
        """Run queued states until the queue is empty.

        If ``flush`` is True, the loop will flush the current queue and enqueue self.initial_state
        """
        if flush:
            self.queue.flush()
            self.queue.append(self.initial_state)
        while not self.queue.empty():
            state = self.get_next_state()
            if state is not None:
                self.execute_current_state()
