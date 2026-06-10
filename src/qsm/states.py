from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Any

from .deque import StringDequeQueue

logger = logging.getLogger(__name__)


@dataclass
class StateContext:
    """Execution context passed into each state.

    Attributes:
        queue: Queue used to schedule additional state names.
        context: Shared workflow data owned by the ``QSM`` instance.
    """

    queue: StringDequeQueue
    context: Any


class State(ABC):
    """Base class for queued state machine states."""

    @abstractmethod
    def execute(self, ctx: StateContext):
        """Run this state with the provided context."""
        pass
