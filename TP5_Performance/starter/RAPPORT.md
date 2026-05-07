# RAPPORT TP5 - Benchmark NoSQL

## 1) Débit écriture / lecture
- Le script `benchmark.py` mesure latence et throughput pour Redis, MongoDB, Cassandra.
- Les métriques clés: `p50`, `p95`, `p99`, `throughput_rps`.

## 2) Charge concurrente
- `benchmark_concurrent` lance des clients simultanés et calcule la dégradation.
- Les résultats permettent d'identifier la saturation par technologie.

## 3) Tableau de décision (synthèse)
- **Redis**: excellent cache et lookup clé-valeur.
- **MongoDB**: très bon compromis document + agrégations.
- **Cassandra**: ingestion massive et séries temporelles à grande échelle.
- **Neo4j**: meilleur pour traversées graphe, recommandations et chemins.
