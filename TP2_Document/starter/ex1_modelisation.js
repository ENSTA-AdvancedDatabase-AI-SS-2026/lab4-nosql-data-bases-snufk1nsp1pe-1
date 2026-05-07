/**
 * TP2 - Exercice 1 : Modélisation MongoDB
 * Use Case : HealthCare DZ - Dossiers Médicaux
 */

// Se connecter à la base médicale
use("medical_db");

// ─── 1.1 : Créer la collection avec validation ────────────────────────────────
// Validation de schéma JSON
db.createCollection("patients", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["cin", "nom", "prenom", "dateNaissance", "sexe", "adresse", "consultations"],
      properties: {
        cin: { bsonType: "string", minLength: 12, maxLength: 12 },
        nom: { bsonType: "string" },
        prenom: { bsonType: "string" },
        dateNaissance: { bsonType: "date" },
        sexe: { enum: ["M", "F"] },
        adresse: {
          bsonType: "object",
          required: ["wilaya", "commune"],
          properties: {
            wilaya: { bsonType: "string" },
            commune: { bsonType: "string" }
          }
        },
        antecedents: { bsonType: "array", items: { bsonType: "string" } },
        allergies: { bsonType: "array", items: { bsonType: "string" } },
        consultations: {
          bsonType: "array",
          minItems: 2,
          items: {
            bsonType: "object",
            required: ["id", "date", "medecin", "diagnostic", "tension"],
            properties: {
              id: { bsonType: "binData" },
              date: { bsonType: "date" },
              diagnostic: { bsonType: "string" },
              notes: { bsonType: "string" }
            }
          }
        }
      }
    }
  }
});

// ─── 1.2 : Insérer des patients avec données algériennes ──────────────────────
// Insertion d'au moins 20 patients avec :
// - Prénoms et noms algériens variés
// - Wilayas différentes (Alger, Oran, Constantine, Annaba, Blida...)
// - Pathologies courantes (Diabète, HTA, Asthme, etc.)
// - Au moins 2-5 consultations par patient
// - Dates réalistes sur les 2 dernières années

const prenoms = ["Ahmed", "Fatima", "Yasmine", "Mohamed", "Imane", "Nadia", "Samir", "Amine", "Sofia", "Nour"];
const noms = ["Bensalem", "Ouali", "Mansouri", "Khellaf", "Benali", "Rezig", "Hamdi", "Ait Ali", "Bouzid", "Meziane"];
const wilayas = ["Alger", "Oran", "Constantine", "Annaba", "Blida"];
const communes = {
  Alger: ["Bab Ezzouar", "Hydra", "El Harrach"],
  Oran: ["Bir El Djir", "Es Senia", "Arzew"],
  Constantine: ["El Khroub", "Ain Smara", "Hamma Bouziane"],
  Annaba: ["El Bouni", "El Hadjar", "Seraidi"],
  Blida: ["Bougara", "Boufarik", "Larbaa"]
};
const diagnostics = ["Hypertension artérielle", "Diabète type 2", "Asthme", "Anémie", "Dyslipidémie"];
const specialites = ["Cardiologie", "Endocrinologie", "Médecine interne", "Pneumologie"];

const patients = Array.from({ length: 20 }).map((_, i) => {
  const wilaya = wilayas[i % wilayas.length];
  const age = 25 + (i * 2);
  const consultations = Array.from({ length: 2 + (i % 4) }).map((__, c) => ({
    id: UUID(),
    date: new Date(new Date().setMonth(new Date().getMonth() - (c + i % 8))),
    medecin: { nom: `Dr. ${noms[(i + c) % noms.length]}`, specialite: specialites[(i + c) % specialites.length] },
    diagnostic: diagnostics[(i + c) % diagnostics.length],
    tension: { systolique: 120 + ((i + c) % 35), diastolique: 75 + ((i + c) % 20) },
    medicaments: [{ nom: "Amlodipine", dosage: "5mg", duree: "30 jours" }],
    notes: "Suivi régulier recommandé"
  }));

  return {
    cin: `${198000000000 + i}`.slice(0, 12),
    nom: noms[i % noms.length],
    prenom: prenoms[i % prenoms.length],
    dateNaissance: new Date(new Date().setFullYear(new Date().getFullYear() - age)),
    sexe: i % 2 === 0 ? "M" : "F",
    adresse: { wilaya, commune: communes[wilaya][i % communes[wilaya].length] },
    groupeSanguin: ["O+", "A+", "B+", "AB+", "O-"][i % 5],
    antecedents: i % 3 === 0 ? ["Diabète type 2", "HTA"] : [diagnostics[i % diagnostics.length]],
    allergies: i % 4 === 0 ? ["Pénicilline"] : [],
    consultations
  };
});

db.patients.deleteMany({});
db.patients.insertMany(patients);

// ─── 1.3 : Collection analyses (référencée) ───────────────────────────────────
// Créer des analyses pour les patients insérés
// Types : "Glycémie", "NFS", "Lipidogramme", "Créatinine", "ECG"

const analyses = [
  // Génération simple d'analyses référencées
];
db.analyses.deleteMany({});
db.patients.find({}, { _id: 1 }).forEach((p, idx) => {
  analyses.push(
    {
      patient_id: p._id,
      date: new Date(new Date().setDate(new Date().getDate() - (idx + 5))),
      type: "Glycémie",
      resultats: { glycemie_g_l: 0.8 + (idx % 8) * 0.1 },
      laboratoire: "Labo Central Alger",
      valide: true
    },
    {
      patient_id: p._id,
      date: new Date(new Date().setDate(new Date().getDate() - (idx + 20))),
      type: "NFS",
      resultats: { hemoglobine: 12 + (idx % 3), leucocytes: 5000 + idx * 50 },
      laboratoire: "Labo Oran",
      valide: true
    }
  );
});
db.analyses.insertMany(analyses);

print("✅ Modélisation terminée. Patients insérés:", db.patients.countDocuments());
print("✅ Analyses insérées:", db.analyses.countDocuments());
