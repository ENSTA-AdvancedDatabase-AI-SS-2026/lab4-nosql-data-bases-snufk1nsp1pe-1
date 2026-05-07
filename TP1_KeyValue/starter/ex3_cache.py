"""
TP1 - Exercice 3 : Pattern Cache-Aside avec TTL
Use Case : Cache des pages produits ShopFast
"""
import redis
import json
import time
from typing import Optional

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def slow_db_get_product(product_id: int) -> Optional[dict]:
    """Simule une requête PostgreSQL lente (2 secondes)"""
    time.sleep(2)
    products = {
        1: {"id": 1, "name": "Samsung Galaxy A54", "price": 65000, "stock": 15},
        2: {"id": 2, "name": "Laptop HP 15-inch", "price": 120000, "stock": 8},
        3: {"id": 3, "name": "Casque JBL Bluetooth", "price": 12000, "stock": 50},
        4: {"id": 4, "name": "Clavier Mécanique", "price": 8000, "stock": 30},
    }
    return products.get(product_id)


def get_product_cached(r, product_id: int, ttl: int = 600) -> Optional[dict]:
    """
    Pattern Cache-Aside :
    1. Chercher dans Redis (clé: "product_cache:{product_id}")
    2. Si MISS → chercher dans slow_db → stocker dans Redis avec TTL
    3. Retourner le produit
    4. Afficher si c'est un HIT ou MISS avec la latence
    """
    start = time.time()
    
    # TODO: Implémenter le pattern Cache-Aside
    # Utiliser json.dumps/json.loads pour sérialiser
    key = f"product_cache:{product_id}"
    cached = r.get(key)
    cache_hit = cached is not None

    if cache_hit:
        product = json.loads(cached)
    else:
        product = slow_db_get_product(product_id)
        if product is not None:
            r.setex(key, ttl, json.dumps(product))
    
    elapsed = time.time() - start
    # TODO: Afficher "CACHE HIT (Xms)" ou "CACHE MISS (Xms)"
    state = "CACHE HIT" if cache_hit else "CACHE MISS"
    print(f"{state} ({elapsed * 1000:.1f}ms)")
    return product


def invalidate_product_cache(r, product_id: int):
    """Supprimer le cache d'un produit (après mise à jour en DB)"""
    # TODO
    r.delete(f"product_cache:{product_id}")


def benchmark_cache(r, product_id: int, iterations: int = 20):
    """
    Effectuer 'iterations' appels à get_product_cached
    Afficher :
    - Temps moyen cache HIT
    - Temps moyen cache MISS
    - Taux de cache hit (%)
    """
    # TODO
    hits = 0
    misses = 0
    hit_latencies = []
    miss_latencies = []
    key = f"product_cache:{product_id}"

    for i in range(iterations):
        if i % 5 == 0:
            r.delete(key)

        start = time.time()
        was_cached = r.exists(key) == 1
        get_product_cached(r, product_id)
        latency_ms = (time.time() - start) * 1000

        if was_cached:
            hits += 1
            hit_latencies.append(latency_ms)
        else:
            misses += 1
            miss_latencies.append(latency_ms)

    hit_rate = (hits / iterations * 100) if iterations else 0.0
    avg_hit = (sum(hit_latencies) / len(hit_latencies)) if hit_latencies else 0.0
    avg_miss = (sum(miss_latencies) / len(miss_latencies)) if miss_latencies else 0.0

    print(f"Temps moyen cache HIT  : {avg_hit:.1f}ms")
    print(f"Temps moyen cache MISS : {avg_miss:.1f}ms")
    print(f"Taux de cache hit      : {hit_rate:.1f}%")


if __name__ == "__main__":
    r.flushdb()
    
    print("=== Test Cache-Aside ===")
    print("\nPremier appel (MISS attendu):")
    get_product_cached(r, 1)
    
    print("\nDeuxième appel (HIT attendu):")
    get_product_cached(r, 1)
    
    print("\n=== Benchmark ===")
    benchmark_cache(r, 1, iterations=10)
