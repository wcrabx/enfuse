from collections import defaultdict
from typing import Any
from sortedcontainers import SortedList  # pip install sortedcontainers
import time
import threading


class WindowStore:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        # KEY -> SortedList of (timestamp, record)
        self.store: defaultdict[Any, SortedList] = defaultdict(
            lambda: SortedList(key=lambda x: x[0])
        )
        self._lock = threading.RLock()

    @property
    def _cutoff(self) -> float:
        return time.time() - self.window_seconds

    def upsert(self, key: Any, timestamp: float, record: Any) -> None:
        with self._lock:
            if timestamp >= self._cutoff:
                self.store[key].add((timestamp, record))
            self._evict(key)

    def query(self, key: Any, at_timestamp: float) -> list[Any]:
        with self._lock:
            lo = at_timestamp - self.window_seconds
            records = self.store[key]
            result = []
            for ts, r in records:
                if ts < lo:
                    continue
                if ts > at_timestamp:
                    break
                result.append(r)
            return result

    def _evict(self, key: Any) -> None:
        with self._lock:
            cutoff = self._cutoff
            records = self.store[key]
            while records and records[0][0] < cutoff:  # type: ignore[operator]
                records.pop(0)
