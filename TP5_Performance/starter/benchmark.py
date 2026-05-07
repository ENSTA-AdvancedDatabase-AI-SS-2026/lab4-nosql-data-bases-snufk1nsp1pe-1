"""
TP5 - Benchmark Comparatif NoSQL
Mesurer les performances de Redis, MongoDB, Cassandra, Neo4j
"""
import time
import statistics
import json
from typing import Callable, List, Tuple
import redis
from pymongo import MongoClient
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, BatchType
from neo4j import GraphDatabase

# ─── Utilitaires de mesure ────────────────────────────────────────────────────

def measure_latency(fn: Callable, iterations: int = 1000) -> dict:
    """
    Exécuter fn iterations fois et retourner les statistiques
    """
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        latencies.append((time.perf_counter() - start) * 1000)  # en ms
    
    latencies.sort()
    return {
        "mean_ms": statistics.mean(latencies),
        "p50_ms": latencies[int(0.50 * len(latencies))],
        "p95_ms": latencies[int(0.95 * len(latencies))],
        "p99_ms": latencies[int(0.99 * len(latencies))],
        "max_ms": max(latencies),
        "throughput_rps": 1000 / statistics.mean(latencies)
    }


def print_results(name: str, results: dict):
    print(f"\n{'='*50}")
    print(f" {name}")
    print(f"{'='*50}")
    for k, v in results.items():
        print(f"  {k:20s}: {v:.2f}")


# ─── Ex1 : Benchmark Écriture ─────────────────────────────────────────────────

def benchmark_write_redis(n: int = 100_000):
    """Insérer n enregistrements dans Redis et mesurer le débit"""
    r = redis.Redis(host='localhost', port=6379)
    r.flushdb()
    start = time.perf_counter()
    pipe = r.pipeline(transaction=False)
    for i in range(n):
        pipe.set(f"bench:key:{i}", json.dumps({"id": i, "value": f"v{i}", "ts": time.time()}))
        if (i + 1) % 1000 == 0:
            pipe.execute()
    pipe.execute()
    elapsed = time.perf_counter() - start
    print_results("Redis Write", {"seconds": elapsed, "throughput_rps": n / elapsed})


def benchmark_write_mongodb(n: int = 100_000):
    """Insérer n documents dans MongoDB et mesurer le débit"""
    client = MongoClient("mongodb://admin:admin123@localhost:27017/")
    db = client["benchmark"]
    col = db["items"]
    col.drop()
    docs = [{"_id": i, "value": f"v{i}", "ts": time.time()} for i in range(n)]
    start = time.perf_counter()
    col.insert_many(docs, ordered=False)
    elapsed = time.perf_counter() - start
    print_results("MongoDB Write", {"seconds": elapsed, "throughput_rps": n / elapsed})


def benchmark_write_cassandra(n: int = 100_000):
    """Insérer n rows dans Cassandra et mesurer le débit"""
    cluster = Cluster(["localhost"])
    session = cluster.connect()
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS benchmark
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
    """)
    session.set_keyspace("benchmark")
    session.execute("""
        CREATE TABLE IF NOT EXISTS kv_items (
            id INT PRIMARY KEY,
            value TEXT,
            ts DOUBLE
        )
    """)
    session.execute("TRUNCATE kv_items")
    stmt = session.prepare("INSERT INTO kv_items (id, value, ts) VALUES (?, ?, ?)")
    start = time.perf_counter()
    batch = BatchType
    del batch  # keep imports unchanged without warnings in simple starter
    for i in range(0, n, 100):
        b = BatchStatement(batch_type=BatchType.UNLOGGED)
        for j in range(i, min(i + 100, n)):
            b.add(stmt, (j, f"v{j}", time.time()))
        session.execute(b)
    elapsed = time.perf_counter() - start
    print_results("Cassandra Write", {"seconds": elapsed, "throughput_rps": n / elapsed})
    cluster.shutdown()


# ─── Ex2 : Benchmark Lecture ─────────────────────────────────────────────────

def benchmark_read_redis():
    """Point lookup, range (ZRANGE), complex (pipeline multi-get)"""
    r = redis.Redis(host='localhost', port=6379)
    r.flushdb()
    for i in range(10_000):
        r.set(f"bench:key:{i}", i)
        r.zadd("bench:zset", {f"member:{i}": i})

    point = measure_latency(lambda: r.get("bench:key:5000"), iterations=1000)
    range_q = measure_latency(lambda: r.zrange("bench:zset", 100, 300), iterations=1000)
    complex_q = measure_latency(
        lambda: (lambda p: (p.mget([f"bench:key:{k}" for k in range(1000, 1050)]), p.execute()))(r.pipeline()),
        iterations=300
    )
    print_results("Redis Read Point", point)
    print_results("Redis Read Range", range_q)
    print_results("Redis Read Complex", complex_q)


def benchmark_read_mongodb():
    """find_one, find avec range, aggregate pipeline"""
    client = MongoClient("mongodb://admin:admin123@localhost:27017/")
    db = client["benchmark"]
    col = db["items"]
    if col.count_documents({}) < 10_000:
        col.drop()
        col.insert_many([{"_id": i, "bucket": i % 100, "value": i, "ts": i} for i in range(10_000)], ordered=False)
    col.create_index("ts")
    col.create_index("bucket")

    point = measure_latency(lambda: col.find_one({"_id": 5000}), iterations=1000)
    range_q = measure_latency(lambda: list(col.find({"ts": {"$gte": 2000, "$lte": 2300}})), iterations=400)
    complex_q = measure_latency(
        lambda: list(col.aggregate([
            {"$match": {"ts": {"$gte": 0}}},
            {"$group": {"_id": "$bucket", "avg": {"$avg": "$value"}}}
        ])),
        iterations=200
    )
    print_results("MongoDB Read Point", point)
    print_results("MongoDB Read Range", range_q)
    print_results("MongoDB Read Complex", complex_q)


# ─── Ex3 : Charge concurrente ─────────────────────────────────────────────────

def benchmark_concurrent(db_fn: Callable, n_clients: int = 50, requests_per_client: int = 200):
    """
    Lancer n_clients threads simultanés
    Chaque thread effectue requests_per_client requêtes
    Mesurer les latences globales et la dégradation vs single client
    """
    import threading
    latencies = []
    lock = threading.Lock()

    def worker():
        local = []
        for _ in range(requests_per_client):
            start = time.perf_counter()
            db_fn()
            local.append((time.perf_counter() - start) * 1000)
        with lock:
            latencies.extend(local)

    start = time.perf_counter()
    threads = [threading.Thread(target=worker) for _ in range(n_clients)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start

    if not latencies:
        return {}
    latencies.sort()
    return {
        "total_requests": n_clients * requests_per_client,
        "total_seconds": elapsed,
        "throughput_rps": (n_clients * requests_per_client) / elapsed,
        "p50_ms": latencies[int(0.50 * len(latencies))],
        "p95_ms": latencies[int(0.95 * len(latencies))],
        "p99_ms": latencies[int(0.99 * len(latencies))],
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Benchmark NoSQL - Comparatif des 4 technologies")
    print("="*60)
    
    N = 10_000  # Réduire pour les tests, 100_000 pour la production
    
    print(f"\n📝 Benchmark Écriture ({N:,} enregistrements)")
    benchmark_write_redis(N)
    benchmark_write_mongodb(N)
    benchmark_write_cassandra(N)
    
    print(f"\n📖 Benchmark Lecture (1,000 requêtes)")
    benchmark_read_redis()
    benchmark_read_mongodb()
    
    print(f"\n⚡ Test Charge Concurrente (50 clients)")
    # benchmark_concurrent(...)
    
    print("\n✅ Benchmark terminé ! Consultez RAPPORT.md pour l'analyse.")
