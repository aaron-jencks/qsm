from queue import Full, Queue
from time import monotonic
from typing import Optional


class StringDequeQueue(Queue[str]):
    def put(self, *items: str, block: bool = True, timeout: Optional[float] = None) -> None:
        self.append(*items, block=block, timeout=timeout)

    def append(self, *items: str, block: bool = True, timeout: Optional[float] = None) -> None:
        for item in items:
            self._put_string(item, left=False, block=block, timeout=timeout)

    def prepend(self, *items: str, block: bool = True, timeout: Optional[float] = None) -> None:
        for item in items:
            self._put_string(item, left=True, block=block, timeout=timeout)

    def append_nowait(self, *items: str) -> None:
        self.append(*items, block=False)

    def prepend_nowait(self, *items: str) -> None:
        self.prepend(*items, block=False)

    def _put_string(self, item: str, left: bool, block: bool, timeout: Optional[float]) -> None:
        if not isinstance(item, str):
            raise TypeError("StringDequeQueue only accepts strings")
        if timeout is not None and timeout < 0:
            raise ValueError("'timeout' must be either 0 or non-negative")

        with self.not_full:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() >= self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() >= self.maxsize:
                        self.not_full.wait()
                else:
                    endtime = monotonic() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = endtime - monotonic()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)

            if left:
                self.queue.appendleft(item)
            else:
                self.queue.append(item)

            self.unfinished_tasks += 1
            self.not_empty.notify()
