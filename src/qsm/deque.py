from queue import Full, Queue
from time import monotonic
from typing import Optional


class StringDequeQueue(Queue[str]):
    """Thread-safe string queue that supports appending to either end.

    This queue follows the synchronization behavior of ``queue.Queue`` while
    adding prepend operations backed by the underlying deque.
    """

    def put(self, *items: str, block: bool = True, timeout: Optional[float] = None) -> None:
        """Append one or more strings using the standard ``Queue.put`` name."""
        self.append(*items, block=block, timeout=timeout)

    def append(self, *items: str, block: bool = True, timeout: Optional[float] = None) -> None:
        """Add one or more strings to the back of the queue."""
        for item in items:
            self._put_string(item, left=False, block=block, timeout=timeout)

    def prepend(self, *items: str, block: bool = True, timeout: Optional[float] = None) -> None:
        """Add one or more strings to the front of the queue."""
        for item in items:
            self._put_string(item, left=True, block=block, timeout=timeout)

    def append_nowait(self, *items: str) -> None:
        """Add one or more strings to the back without blocking."""
        self.append(*items, block=False)

    def prepend_nowait(self, *items: str) -> None:
        """Add one or more strings to the front without blocking."""
        self.prepend(*items, block=False)

    def flush(self) -> int:
        """Remove all queued strings and count them as completed.

        Returns:
            The number of queued items removed.
        """
        with self.mutex:
            removed = self._qsize()
            if removed == 0:
                return 0

            self.queue.clear()
            self.unfinished_tasks -= removed
            if self.unfinished_tasks == 0:
                self.all_tasks_done.notify_all()
            self.not_full.notify_all()
            return removed

    def _put_string(self, item: str, left: bool, block: bool, timeout: Optional[float]) -> None:
        """Add a single string while holding the queue's producer lock."""
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
