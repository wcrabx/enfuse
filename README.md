# WindowStore

Time-windowed record storage with automatic eviction and thread safety.

## Install

```bash
pip install sortedcontainers
```

## Usage

```python
from window_store import WindowStore
import time

store = WindowStore(window_seconds=60)

# Upsert records with timestamp
now = time.time()
store.upsert("user1", now - 30, {"event": "login"})
store.upsert("user1", now - 10, {"event": "view"})
store.upsert("user1", now, {"event": "purchase"})

# Query records within window at a specific timestamp
results = store.query("user1", now)
# Returns: [{"event": "login"}, {"event": "view"}, {"event": "purchase"}]

# Query at different timestamp (e.g., 10 seconds ago)
results = store.query("user1", now - 10)
# Returns records within [now-10-60, now-10] window
```

## API

### `WindowStore(window_seconds=60)`

Create store with time window size in seconds.

### `upsert(key, timestamp, record)`

Add or update record at given timestamp. Records older than `window_seconds` from now are rejected and automatically evicted. Thread-safe.

### `query(key, at_timestamp)`

Return list of records for key within window at `at_timestamp`. Window is `[at_timestamp - window_seconds, at_timestamp]` inclusive.

Returns empty list if key not found.

## Features

- **Time windowing**: Only keeps records within configurable window
- **Sorted storage**: Records ordered by timestamp for efficient queries
- **Automatic eviction**: Old records removed on upsert to prevent unbounded growth
- **Thread safe**: Concurrent reads/writes protected by reentrant lock
- **Flexible timestamps**: Query at any past or future timestamp

## Examples

Run demos:

```bash
python demo_window_store.py
python demo_threading.py
```

## Testing

```bash
pytest test_window_store.py -v
```

100% code coverage. 22 tests covering initialization, upsert, query, eviction, boundaries, concurrency, and edge cases.

## Design

Records are stored in `SortedList` keyed by timestamp for O(log n) insertion and efficient prefix-skipping during queries. Eviction uses a cutoff timestamp approach—records older than `time.time() - window_seconds` are removed.

Thread safety via reentrant lock (`threading.RLock`) on upsert, query, and evict operations.
