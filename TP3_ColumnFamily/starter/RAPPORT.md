# RAPPORT TP3 - Cassandra

## 1) Justification des Partition Keys
- `mesures_par_capteur`: `((capteur_id, date_jour), timestamp)` pour répartir la charge et éviter les hot partitions longues.
- `alertes_par_wilaya`: `((wilaya, date_jour), timestamp, capteur_id)` optimisé pour requête "alertes d'une wilaya sur un jour".
- `agregats_horaires`: `((wilaya, date_jour), date_heure)` pour dashboard journalier par wilaya.

## 2) Pourquoi éviter ALLOW FILTERING
- Peut déclencher des scans larges et coûteux.
- Latence imprévisible en production.
- Solution: créer une table dédiée par pattern de requête.

## 3) TWCS vs STCS vs LCS
- **TWCS**: idéal pour séries temporelles + TTL (tables de mesures).
- **STCS**: charge d'écriture générale, moins bon pour lecture ciblée.
- **LCS**: bonnes lectures mais coût d'écriture plus élevé.
