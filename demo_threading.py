#!/usr/bin/env python
"""Demo of WindowStore with concurrent threading."""

import threading
import time
from window_store import WindowStore


def demo_concurrent_writes():
    print("=== Concurrent Writes ===")
    store = WindowStore(window_seconds=5)
    base_time = time.time()
    results = []

    def writer(thread_id):
        for i in range(10):
            ts = base_time + i * 0.1
            store.upsert("events", ts, f"thread{thread_id}_msg{i}")
            results.append(f"thread{thread_id} wrote msg{i}")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final = store.query("events", base_time + 1)
    print(f"Wrote: {len(results)} messages from 3 threads")
    print(f"Stored: {len(final)} records in window")
    print()


def demo_concurrent_read_write():
    print("=== Concurrent Read/Write ===")
    store = WindowStore(window_seconds=10)
    base_time = time.time()
    read_count = [0]
    write_count = [0]

    def writer():
        for i in range(50):
            store.upsert("stream", base_time + i * 0.01, f"data{i}")
            write_count[0] += 1
            time.sleep(0.001)

    def reader():
        for i in range(50):
            store.query("stream", base_time + i * 0.01)
            read_count[0] += 1
            time.sleep(0.001)

    threads = [
        threading.Thread(target=writer),
        threading.Thread(target=writer),
        threading.Thread(target=reader),
        threading.Thread(target=reader),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Writes: {write_count[0]}, Reads: {read_count[0]}")
    print(f"Final store size: {len(store.query('stream', base_time + 1))}")
    print()


def demo_multiple_keys():
    print("=== Multiple Keys Concurrent ===")
    store = WindowStore(window_seconds=5)
    base_time = time.time()

    def user_activity(user_id):
        for i in range(20):
            ts = base_time + i * 0.05
            store.upsert(f"user{user_id}", ts, {"action": f"action{i}"})

    threads = [threading.Thread(target=user_activity, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for user_id in range(5):
        count = len(store.query(f"user{user_id}", base_time + 1))
        print(f"user{user_id}: {count} events")
    print()


def demo_stress():
    print("=== Stress Test ===")
    store = WindowStore(window_seconds=10)
    base_time = time.time()
    ops = [0]
    lock = threading.Lock()

    def stress_worker(thread_id):
        for i in range(100):
            if i % 3 == 0:
                store.upsert("key1", base_time + i * 0.001, f"t{thread_id}_w{i}")
            else:
                store.query("key1", base_time + i * 0.001)
            with lock:
                ops[0] += 1

    start = time.time()
    threads = [threading.Thread(target=stress_worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start

    print(f"1000 mixed ops in {elapsed:.2f}s ({ops[0]/elapsed:.0f} ops/sec)")
    print()


if __name__ == "__main__":
    demo_concurrent_writes()
    demo_concurrent_read_write()
    demo_multiple_keys()
    demo_stress()
