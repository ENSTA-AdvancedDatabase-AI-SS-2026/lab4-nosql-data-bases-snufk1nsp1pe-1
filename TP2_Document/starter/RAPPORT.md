# RAPPORT TP2 - MongoDB

## 1) Embedding vs Referencing
- `patients` contient les `consultations` en **embedding** (accès fréquent en lecture dossier).
- `analyses` est en collection séparée (**referencing**) pour maîtriser le volume et faciliter l'archivage TTL.

## 2) Explain avant/après index
- Index créés: wilaya+antécédents, date consultation, text diagnostic, patient/date sur analyses.
- Attendu après indexation: baisse de `totalDocsExamined` et de `executionTimeMillis`.
- Requêtes ciblées sont servies avec moins de scan global.

## 3) Pipeline complexe expliqué
- `$unwind` pour dérouler les consultations/médicaments.
- `$group` pour agréger (diagnostic, spécialité, médecin, etc.).
- `$addFields` pour calculs dérivés (âge, taux de re-consultation).
- `$sort` + `$limit` pour extraire les top résultats.
