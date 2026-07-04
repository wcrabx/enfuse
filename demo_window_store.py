#!/usr/bin/env python
"""Demo script exercising WindowStore functionality."""

import time
from window_store import WindowStore


def demo_basic():
    print("=== Basic Usage ===")
    store = WindowStore(window_seconds=10)
    now = time.time()

    store.upsert("user1", now - 5, {"event": "login", "ip": "192.168.1.1"})
    store.upsert("user1", now - 2, {"event": "view_page", "page": "home"})
    store.upsert("user1", now, {"event": "purchase", "amount": 99.99})

    results = store.query("user1", now)
    print(f"Events for user1 in window: {results}")
    print()


def demo_time_windowing():
    print("=== Time Windowing ===")
    store = WindowStore(window_seconds=5)
    now = time.time()

    for i in range(10):
        timestamp = now - 10 + i
        store.upsert("metrics", timestamp, {"value": i * 10})

    results = store.query("metrics", now)
    print(f"Metrics within 5-second window: {results}")
    print()


def demo_multiple_users():
    print("=== Multiple Users ===")
    store = WindowStore(window_seconds=30)
    base_time = time.time()

    for user_id in range(1, 4):
        for offset in [0, 5, 10]:
            store.upsert(f"user{user_id}", base_time + offset, f"user{user_id}_event_{offset}")

    for user_id in range(1, 4):
        results = store.query(f"user{user_id}", base_time + 10)
        print(f"user{user_id}: {results}")
    print()


def demo_eviction():
    print("=== Automatic Eviction ===")
    store = WindowStore(window_seconds=5)
    old_time = time.time() - 20
    now = time.time()

    store.upsert("events", old_time, "very_old")
    store.upsert("events", now - 3, "recent")
    store.upsert("events", now, "current")

    print(f"Before eviction: {len(store.store['events'])} records")
    store._evict("events")
    print(f"After eviction: {len(store.store['events'])} records")
    print(f"Remaining: {store.query('events', now)}")
    print()


def demo_streaming_scenario():
    print("=== Streaming Scenario ===")
    store = WindowStore(window_seconds=2)

    print("Simulating 6 seconds of events...")
    for second in range(6):
        timestamp = time.time() + second
        store.upsert("stream", timestamp, f"event_at_{second}s")

        current_time = time.time() + second
        in_window = store.query("stream", current_time)
        print(f"  At {second}s: {len(in_window)} events in window - {in_window}")


if __name__ == "__main__":
    demo_basic()
    demo_time_windowing()
    demo_multiple_users()
    demo_eviction()
    demo_streaming_scenario()
