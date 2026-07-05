import time
import threading
from window_store import WindowStore


def test_init_default_window():
    store = WindowStore()
    assert store.window_seconds == 60


def test_init_custom_window():
    store = WindowStore(window_seconds=30)
    assert store.window_seconds == 30


def test_upsert_single_record():
    store = WindowStore()
    now = time.time()
    store.upsert("key1", now, {"data": "record1"})
    assert "key1" in store.store
    assert len(store.store["key1"]) == 1


def test_upsert_multiple_records_same_key():
    store = WindowStore()
    now = time.time()
    store.upsert("key1", now, {"data": "record1"})
    store.upsert("key1", now + 1, {"data": "record2"})
    store.upsert("key1", now + 2, {"data": "record3"})
    assert len(store.store["key1"]) == 3


def test_upsert_multiple_keys():
    store = WindowStore()
    now = time.time()
    store.upsert("key1", now, "rec1")
    store.upsert("key2", now, "rec2")
    store.upsert("key3", now, "rec3")
    assert len(store.store) == 3


def test_upsert_records_sorted_by_timestamp():
    store = WindowStore()
    now = time.time()
    store.upsert("key1", now + 10, "rec10")
    store.upsert("key1", now, "rec0")
    store.upsert("key1", now + 5, "rec5")
    times = [ts for ts, _ in store.store["key1"]]
    assert times == sorted(times)


def test_query_all_records_in_window():
    store = WindowStore(window_seconds=10)
    now = time.time()
    store.upsert("key1", now - 5, "rec1")
    store.upsert("key1", now, "rec2")
    store.upsert("key1", now + 5, "rec3")
    results = store.query("key1", now + 5)
    assert len(results) == 3
    assert "rec1" in results
    assert "rec2" in results
    assert "rec3" in results


def test_query_excludes_records_before_window():
    store = WindowStore(window_seconds=10)
    now = time.time()
    store.upsert("key1", now - 15, "too_old")
    store.upsert("key1", now - 5, "in_window")
    store.upsert("key1", now, "in_window2")
    results = store.query("key1", now)
    assert len(results) == 2
    assert "too_old" not in results
    assert "in_window" in results


def test_query_excludes_records_after_query_time():
    store = WindowStore(window_seconds=10)
    now = time.time()
    store.upsert("key1", now - 5, "before")
    store.upsert("key1", now, "at")
    store.upsert("key1", now + 5, "after")
    results = store.query("key1", now)
    assert len(results) == 2
    assert "before" in results
    assert "at" in results
    assert "after" not in results


def test_query_empty_key():
    store = WindowStore()
    now = time.time()
    results = store.query("nonexistent", now)
    assert results == []


def test_query_window_boundary_inclusive():
    store = WindowStore(window_seconds=10)
    now = time.time()
    store.upsert("key1", now - 9, "at_lower_bound")
    store.upsert("key1", now, "at_upper_bound")
    results = store.query("key1", now)
    assert len(results) == 2
    assert "at_lower_bound" in results
    assert "at_upper_bound" in results


def test_evict_removes_old_records():
    store = WindowStore(window_seconds=10)
    old_time = time.time() - 30
    recent_time = time.time()
    store.upsert("key1", old_time, "old")
    store.upsert("key1", recent_time, "recent")
    store._evict("key1")
    assert len(store.store["key1"]) == 1
    assert store.store["key1"][0][1] == "recent"


def test_evict_keeps_recent_records():
    store = WindowStore(window_seconds=10)
    now = time.time()
    store.upsert("key1", now - 5, "rec1")
    store.upsert("key1", now, "rec2")
    store.upsert("key1", now + 5, "rec3")
    store._evict("key1")
    assert len(store.store["key1"]) == 3


def test_evict_called_on_upsert():
    store = WindowStore(window_seconds=10)
    old_time = time.time() - 30
    store.upsert("key1", old_time, "old")
    store.upsert("key1", time.time(), "recent")
    assert len(store.store["key1"]) == 1


def test_evict_empty_list():
    store = WindowStore()
    store._evict("nonexistent")
    assert "nonexistent" not in store.store or len(store.store["nonexistent"]) == 0


def test_complex_scenario():
    store = WindowStore(window_seconds=20)
    base_time = time.time()

    store.upsert("user1", base_time - 30, {"old": 1})
    store.upsert("user1", base_time - 10, {"recent": 2})
    store.upsert("user1", base_time, {"current": 3})
    store.upsert("user1", base_time + 10, {"future": 4})

    store.upsert("user2", base_time - 5, {"data": "a"})
    store.upsert("user2", base_time + 15, {"data": "b"})

    user1_results = store.query("user1", base_time + 10)
    assert len(user1_results) == 3
    assert {"old": 1} not in user1_results
    assert {"recent": 2} in user1_results
    assert {"current": 3} in user1_results
    assert {"future": 4} in user1_results

    user2_results = store.query("user2", base_time + 15)
    assert len(user2_results) == 2
    assert {"data": "a"} in user2_results
    assert {"data": "b"} in user2_results


def test_many_records_performance():
    store = WindowStore()
    now = time.time()
    for i in range(1000):
        store.upsert("key1", now + i * 0.001, f"record{i}")
    results = store.query("key1", now + 0.5)
    assert len(results) > 0
    assert len(store.store["key1"]) == 1000


def test_different_record_types():
    store = WindowStore()
    now = time.time()
    store.upsert("k1", now, "string")
    store.upsert("k2", now, 42)
    store.upsert("k3", now, {"dict": "value"})
    store.upsert("k4", now, [1, 2, 3])
    store.upsert("k5", now, None)

    assert store.query("k1", now) == ["string"]
    assert store.query("k2", now) == [42]
    assert store.query("k3", now) == [{"dict": "value"}]
    assert store.query("k4", now) == [[1, 2, 3]]
    assert store.query("k5", now) == [None]


def test_upsert_rejects_too_old():
    store = WindowStore(window_seconds=10)
    now = time.time()
    old_time = now - 25

    store.upsert("key1", old_time, "too_old")
    store.upsert("key1", now, "current")

    assert len(store.store["key1"]) == 1
    assert store.query("key1", now) == ["current"]


def test_evict_pops_expired():
    store = WindowStore(window_seconds=10)
    now = time.time()
    cutoff = now - 10

    store.store["key1"].add((cutoff - 5, "expired"))
    store.store["key1"].add((cutoff + 5, "valid"))

    store._evict("key1")
    assert len(store.store["key1"]) == 1
    assert store.store["key1"][0][1] == "valid"


def test_query_skips_records_before_window():
    store = WindowStore(window_seconds=10)
    now = time.time()

    store.store["key1"].add((now - 15, "before_window"))
    store.store["key1"].add((now - 5, "in_window"))
    store.store["key1"].add((now, "at_end"))

    results = store.query("key1", now)
    assert len(results) == 2
    assert "before_window" not in results
    assert "in_window" in results
    assert "at_end" in results


def test_thread_safety():
    store = WindowStore(window_seconds=10)
    now = time.time()

    def upsert_many():
        for i in range(100):
            store.upsert("key1", now + i * 0.01, f"record{i}")

    def query_many():
        for i in range(100):
            store.query("key1", now + i * 0.01)

    threads = [
        threading.Thread(target=upsert_many),
        threading.Thread(target=upsert_many),
        threading.Thread(target=query_many),
        threading.Thread(target=query_many),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(store.query("key1", now + 1)) > 0
