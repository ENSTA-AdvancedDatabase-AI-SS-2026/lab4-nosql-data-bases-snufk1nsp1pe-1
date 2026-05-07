# RAPPORT TP1 - Redis

## 1) Performance cache (hit vs miss)
- Les appels `CACHE MISS` sont nettement plus lents (accès DB simulé).
- Les appels `CACHE HIT` sont quasi immédiats (lecture Redis).
- Le taux de hit augmente après réchauffement du cache.

## 2) Choix de modélisation
- `Hash` pour les produits et paniers (`product:*`, `cart:*`).
- `List` pour l'historique de navigation avec limite (`LPUSH` + `LTRIM`).
- `Set` pour catégories et intersections (`SINTER`).
- `Sorted Set` pour classement ventes temps réel.

## 3) Réponses aux questions
- **Redémarrage Redis**: perte des données en mémoire sans persistance AOF/RDB.
- **Cohérence cache/DB**: invalider la clé après update DB et utiliser des TTL.
- **TTL trop court**: provoque trop de misses et surcharge la base source.
