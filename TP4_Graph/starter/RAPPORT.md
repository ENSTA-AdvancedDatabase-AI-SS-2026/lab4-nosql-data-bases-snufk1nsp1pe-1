# RAPPORT TP4 - Neo4j

## 1) Schéma graphe
- Nœuds: `Etudiant`, `Cours`, `Competence`.
- Relations: `CONNAIT`, `SUIT`, `MAITRISE`, `REQUIERT`.
- Contraintes d'unicité appliquées sur `Etudiant.id`, `Cours.code`, `Competence.nom`.

## 2) Communautés détectées
- Louvain segmente le réseau en groupes fortement connectés.
- Les communautés suivent en pratique l'université/filière et les cours partagés.
- Les étudiants "ponts" relient des groupes autrement séparés.

## 3) SQL vs Cypher
- Requêtes de voisinage et plus court chemin sont plus naturelles en Cypher.
- En SQL, la même logique demande plusieurs JOINs récursifs complexes.
- Pour réseau social/recommandation, le graphe est plus lisible et scalable fonctionnellement.
