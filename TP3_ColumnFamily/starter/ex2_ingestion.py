"""
TP3 - Exercice 2 : Ingestion de données IoT
Use Case : SmartGrid DZ - 10 000 capteurs, 5 minutes de mesures
"""
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, BatchType
import uuid
import random
from datetime import datetime, timedelta
import time

# Configuration
CASSANDRA_HOST = 'localhost'
KEYSPACE = 'smartgrid'
NB_CAPTEURS = 10000
MINUTES_HISTORIQUE = 5

WILAYAS = ["Alger", "Oran", "Constantine", "Annaba", "Blida"]
COMMUNES = {
    "Alger": ["Bab Ezzouar", "Hydra", "El Harrach", "Dar El Beida"],
    "Oran": ["Bir El Djir", "Es Senia", "Arzew"],
    "Constantine": ["El Khroub", "Ain Smara", "Hamma Bouziane"],
    "Annaba": ["El Bouni", "El Hadjar", "Seraidi"],
    "Blida": ["Bougara", "Boufarik", "Larbaa"],
}

def connect():
    """Connexion au cluster Cassandra"""
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect(KEYSPACE)
    return session, cluster


def generate_mesure(capteur_id, wilaya, commune, timestamp):
    """Générer une mesure réaliste pour un capteur"""
    tension_base = 220  # Volts (réseau algérien)
    
    return {
        "capteur_id": capteur_id,
        "date_jour": timestamp.date(),
        "timestamp": timestamp,
        "wilaya": wilaya,
        "commune": commune,
        # Variation normale ± 10V
        "tension_v": round(tension_base + random.gauss(0, 5), 2),
        "courant_a": round(random.uniform(0.5, 15.0), 2),
        "puissance_kw": round(random.uniform(0.1, 3.3), 3),
        "frequence_hz": round(50 + random.gauss(0, 0.1), 2),
        "temperature": round(random.uniform(20, 65), 1),
        # 5% de chance d'alerte
        "alerte": random.random() < 0.05,
    }


def insert_single(session, mesure):
    """
    Insérer une seule mesure dans mesures_par_capteur
    Utiliser une prepared statement
    """
    stmt = session.prepare("""
        INSERT INTO mesures_par_capteur (
            capteur_id, date_jour, timestamp, wilaya, commune,
            tension_v, courant_a, puissance_kw, frequence_hz,
            temperature, alerte, code_alerte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        USING TTL 7776000
    """)
    code_alerte = None
    if mesure["alerte"]:
        if mesure["tension_v"] < 200:
            code_alerte = "SOUS_TENSION"
        elif mesure["tension_v"] > 240:
            code_alerte = "SUR_TENSION"
        else:
            code_alerte = "ANOMALIE_RESEAU"

    session.execute(stmt, (
        mesure["capteur_id"], mesure["date_jour"], mesure["timestamp"],
        mesure["wilaya"], mesure["commune"], mesure["tension_v"],
        mesure["courant_a"], mesure["puissance_kw"], mesure["frequence_hz"],
        mesure["temperature"], mesure["alerte"], code_alerte
    ))


def insert_batch(session, mesures: list):
    """
    Insérer un batch de mesures de manière efficace
    Utiliser UNLOGGED BATCH pour les séries temporelles
    Faire des batches de max 50 items (bonne pratique Cassandra)
    """
    stmt_mesure = session.prepare("""
        INSERT INTO mesures_par_capteur (
            capteur_id, date_jour, timestamp, wilaya, commune,
            tension_v, courant_a, puissance_kw, frequence_hz,
            temperature, alerte, code_alerte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        USING TTL 7776000
    """)
    stmt_alerte = session.prepare("""
        INSERT INTO alertes_par_wilaya (
            wilaya, date_jour, timestamp, capteur_id, code_alerte,
            description, gravite, resolue
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        USING TTL 31536000
    """)

    batch_size = 50
    for i in range(0, len(mesures), batch_size):
        batch = BatchStatement(batch_type=BatchType.UNLOGGED)
        chunk = mesures[i:i + batch_size]
        for mesure in chunk:
            code_alerte = None
            if mesure["alerte"]:
                if mesure["tension_v"] < 200:
                    code_alerte = "SOUS_TENSION"
                elif mesure["tension_v"] > 240:
                    code_alerte = "SUR_TENSION"
                else:
                    code_alerte = "ANOMALIE_RESEAU"

            batch.add(stmt_mesure, (
                mesure["capteur_id"], mesure["date_jour"], mesure["timestamp"],
                mesure["wilaya"], mesure["commune"], mesure["tension_v"],
                mesure["courant_a"], mesure["puissance_kw"], mesure["frequence_hz"],
                mesure["temperature"], mesure["alerte"], code_alerte
            ))

            if mesure["alerte"]:
                description = f"Alerte {code_alerte} capteur {mesure['capteur_id']}"
                gravite = 3 if code_alerte in ("SOUS_TENSION", "SUR_TENSION") else 2
                batch.add(stmt_alerte, (
                    mesure["wilaya"], mesure["date_jour"], mesure["timestamp"],
                    mesure["capteur_id"], code_alerte, description, gravite, False
                ))
        session.execute(batch)


def run_ingestion(session):
    """
    Générer et insérer NB_CAPTEURS × MINUTES_HISTORIQUE mesures
    1. Générer les capteurs (ID aléatoires + assignation wilaya/commune)
    2. Pour chaque minute des MINUTES_HISTORIQUE dernières minutes
       → Insérer les mesures de tous les capteurs
    3. Mesurer et afficher :
       - Nombre total d'insertions
       - Durée totale
       - Débit (mesures/seconde)
    """
    print(f"Démarrage ingestion : {NB_CAPTEURS} capteurs × {MINUTES_HISTORIQUE} min")
    start = time.time()
    
    capteurs = []
    for _ in range(NB_CAPTEURS):
        wilaya = random.choice(WILAYAS)
        commune = random.choice(COMMUNES[wilaya])
        capteurs.append((uuid.uuid4(), wilaya, commune))

    now = datetime.utcnow().replace(second=0, microsecond=0)
    for minute_offset in range(MINUTES_HISTORIQUE):
        timestamp = now - timedelta(minutes=minute_offset)
        mesures = [
            generate_mesure(capteur_id, wilaya, commune, timestamp)
            for capteur_id, wilaya, commune in capteurs
        ]
        insert_batch(session, mesures)
        print(f"  Minute {minute_offset + 1}/{MINUTES_HISTORIQUE} insérée ({len(mesures):,} mesures)")
    
    elapsed = time.time() - start
    total = NB_CAPTEURS * MINUTES_HISTORIQUE
    print(f"\n✅ {total:,} mesures insérées en {elapsed:.1f}s")
    print(f"   Débit : {total/elapsed:,.0f} mesures/seconde")


if __name__ == "__main__":
    session, cluster = connect()
    run_ingestion(session)
    cluster.shutdown()
