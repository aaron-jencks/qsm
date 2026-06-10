from dataclasses import dataclass
import logging
from queue import Queue
from typing import Any, Callable, Dict, Optional

from .exceptions import NoSuchHandlerException


logger = logging.getLogger(__name__)


@dataclass
class StateContent:
    type: str
    payload: Any


@dataclass
class StateContext:
    queue: Queue
    content: Optional[StateContent]


PayloadHandler = Callable[[StateContext], Optional[StateContent]]


class State:
    def __init__(self):
        self.default_handler: Optional[PayloadHandler] = None
        self.handlers: Dict[str, PayloadHandler] = {}

    def _execute_handler(self, name: str, context: StateContext) -> Optional[StateContent]:
        if name not in self.handlers:
            raise NoSuchHandlerException(name)
        logger.debug(f"Executing handler for {name}")
        return self.handlers[name](context)

    def execute(self, ctx: StateContext) -> Optional[StateContent]:
        if ctx.content is None:
            if self.default_handler is None:
                if len(self.handlers) != 1:
                    raise NoSuchHandlerException("No default handler found")
                else:
                    return self._execute_handler(list(self.handlers.keys())[0], ctx)
            return self.default_handler(ctx)
        return self._execute_handler(ctx.content.type, ctx)
