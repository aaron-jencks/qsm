from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from queue import Queue
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class StateContext:
    queue: Queue
    context: Any


class State(ABC):
    @abstractmethod
    def execute(self, ctx: StateContext):
        pass
