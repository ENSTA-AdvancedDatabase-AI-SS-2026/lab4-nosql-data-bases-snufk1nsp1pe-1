// TP4 - Exercice 1 : Création du graphe UniConnect DZ
// Effacer la base pour partir propre
MATCH (n) DETACH DELETE n;

// ─── 1.1 : Contraintes d'unicité ─────────────────────────────────────────────
CREATE CONSTRAINT etudiant_id IF NOT EXISTS FOR (e:Etudiant) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT cours_code IF NOT EXISTS FOR (c:Cours) REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT competence_nom IF NOT EXISTS FOR (c:Competence) REQUIRE c.nom IS UNIQUE;

// ─── 1.2 : Créer les compétences ──────────────────────────────────────────────
UNWIND [
  {nom: "Python", categorie: "Programmation"},
  {nom: "Java", categorie: "Programmation"},
  {nom: "SQL", categorie: "Bases de Données"},
  {nom: "NoSQL", categorie: "Bases de Données"},
  {nom: "Machine Learning", categorie: "IA"},
  {nom: "Deep Learning", categorie: "IA"},
  {nom: "React", categorie: "Web"},
  {nom: "Docker", categorie: "DevOps"},
  {nom: "Linux", categorie: "Systèmes"},
  {nom: "Réseaux", categorie: "Infrastructure"}
] AS comp
MERGE (:Competence {nom: comp.nom, categorie: comp.categorie});

// ─── 1.3 : Créer les cours ────────────────────────────────────────────────────
UNWIND [
  {code: "INFO401", intitule: "Bases de Données Avancées", credits: 6, dept: "Informatique"},
  {code: "INFO402", intitule: "Intelligence Artificielle", credits: 6, dept: "Informatique"},
  {code: "INFO403", intitule: "Développement Web", credits: 4, dept: "Informatique"},
  {code: "INFO404", intitule: "Systèmes Distribués", credits: 5, dept: "Informatique"},
  {code: "INFO405", intitule: "Cloud Computing", credits: 4, dept: "Informatique"}
] AS cours
MERGE (:Cours {code: cours.code, intitule: cours.intitule, 
               credits: cours.credits, departement: cours.dept});

// ─── 1.4 : Créer les étudiants ────────────────────────────────────────────────
WITH [
  "Ahmed","Fatima","Yasmina","Mohamed","Imane","Samir","Nadia","Amine","Sofia","Nour",
  "Karim","Lina","Riad","Amina","Walid","Meriem","Yacine","Ikram","Hocine","Chaima"
] AS prenoms,
["Bensalem","Ouali","Mansouri","Khellaf","Benali","Rezig","Hamdi","Ait Ali","Bouzid","Meziane"] AS noms,
["USTHB","UMBB","USTO","UMC","UBMA"] AS unis,
["Informatique","Mathématiques","Electronique","Telecoms","GL"] AS filieres,
["Alger","Boumerdes","Oran","Constantine","Annaba"] AS villes
UNWIND range(1, 50) AS i
MERGE (e:Etudiant {id: "E" + right("00" + toString(i), 3)})
SET e.prenom = prenoms[(i - 1) % size(prenoms)],
    e.nom = noms[(i - 1) % size(noms)],
    e.universite = unis[(i - 1) % size(unis)],
    e.filiere = filieres[(i - 1) % size(filieres)],
    e.annee = 1 + (i % 5),
    e.ville = villes[(i - 1) % size(villes)];

// ─── 1.5 : Créer les relations ────────────────────────────────────────────────
// CONNAIT : chaîne + liens aléatoires pour garantir la connexité
MATCH (e:Etudiant)
WITH e ORDER BY e.id
WITH collect(e) AS etudiants
UNWIND range(0, size(etudiants) - 2) AS i
WITH etudiants[i] AS a, etudiants[i + 1] AS b
MERGE (a)-[:CONNAIT {depuis: 2022 + (i % 4), contexte: "Université"}]->(b)
MERGE (b)-[:CONNAIT {depuis: 2022 + (i % 4), contexte: "Université"}]->(a);

MATCH (a:Etudiant), (b:Etudiant)
WHERE a.id < b.id AND rand() < 0.05
MERGE (a)-[:CONNAIT {depuis: 2021 + toInteger(rand() * 5), contexte: "Club"}]->(b);

// SUIT : chaque étudiant suit 2-3 cours
MATCH (e:Etudiant), (c:Cours)
WITH e, c WHERE rand() < 0.55
MERGE (e)-[:SUIT {semestre: "S" + toString(1 + toInteger(rand() * 6)), note: 10 + toInteger(rand() * 10)}]->(c);

// MAITRISE : 2-4 compétences par étudiant
MATCH (e:Etudiant), (comp:Competence)
WITH e, comp WHERE rand() < 0.35
MERGE (e)-[:MAITRISE {niveau: ["Débutant","Intermédiaire","Avancé"][toInteger(rand() * 3)]}]->(comp);

// Cours -> compétences requises
MATCH (c:Cours {code: "INFO401"}), (comp:Competence {nom: "SQL"})
MERGE (c)-[:REQUIERT]->(comp);
MATCH (c:Cours {code: "INFO401"}), (comp:Competence {nom: "NoSQL"})
MERGE (c)-[:REQUIERT]->(comp);
MATCH (c:Cours {code: "INFO402"}), (comp:Competence {nom: "Python"})
MERGE (c)-[:REQUIERT]->(comp);
MATCH (c:Cours {code: "INFO402"}), (comp:Competence {nom: "Machine Learning"})
MERGE (c)-[:REQUIERT]->(comp);
MATCH (c:Cours {code: "INFO403"}), (comp:Competence {nom: "React"})
MERGE (c)-[:REQUIERT]->(comp);
MATCH (c:Cours {code: "INFO404"}), (comp:Competence {nom: "Linux"})
MERGE (c)-[:REQUIERT]->(comp);

// Vérification
MATCH (n) RETURN labels(n)[0] AS type, count(n) AS total ORDER BY total DESC;
MATCH ()-[r]->() RETURN type(r) AS relation, count(r) AS total ORDER BY total DESC;
