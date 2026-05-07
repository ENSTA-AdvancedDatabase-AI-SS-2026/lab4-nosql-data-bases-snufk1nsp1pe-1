/**
 * TP2 - Exercice 3 : Pipelines d'Agrégation
 * Use Case : Statistiques médicales HealthCare DZ
 */

use("medical_db");

// ─── 3.1 : Distribution des diagnostics par wilaya ────────────────────────────
print("=== 3.1 : Top diagnostics par wilaya ===");

const diagParWilaya = db.patients.aggregate([
  { $unwind: "$consultations" },
  {
    $group: {
      _id: { wilaya: "$adresse.wilaya", diagnostic: "$consultations.diagnostic" },
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 20 }
]).toArray();

// printjson(diagParWilaya);

// ─── 3.2 : Médicament le plus prescrit par spécialité ─────────────────────────
print("\n=== 3.2 : Top médicaments par spécialité ===");

const medsParSpecialite = db.patients.aggregate([
  { $unwind: "$consultations" },
  { $unwind: "$consultations.medicaments" },
  {
    $group: {
      _id: {
        specialite: "$consultations.medecin.specialite",
        medicament: "$consultations.medicaments.nom"
      },
      total: { $sum: 1 }
    }
  },
  { $sort: { "_id.specialite": 1, total: -1 } },
  {
    $group: {
      _id: "$_id.specialite",
      medicament: { $first: "$_id.medicament" },
      total: { $first: "$total" }
    }
  }
]).toArray();

// ─── 3.3 : Évolution mensuelle des consultations ──────────────────────────────
print("\n=== 3.3 : Consultations par mois (12 derniers mois) ===");

const evolutionMensuelle = db.patients.aggregate([
  { $unwind: "$consultations" },
  { $match: {
    "consultations.date": {
      $gte: new Date(new Date().setFullYear(new Date().getFullYear() - 1))
    }
  }},
  {
    $group: {
      _id: {
        annee: { $year: "$consultations.date" },
        mois: { $month: "$consultations.date" }
      },
      total: { $sum: 1 }
    }
  },
  { $sort: { "_id.annee": 1, "_id.mois": 1 } },
  {
    $project: {
      _id: 0,
      periode: {
        $concat: [
          { $toString: "$_id.annee" },
          "-",
          {
            $cond: [
              { $lt: ["$_id.mois", 10] },
              { $concat: ["0", { $toString: "$_id.mois" }] },
              { $toString: "$_id.mois" }
            ]
          }
        ]
      },
      total: 1
    }
  }
]).toArray();

// ─── 3.4 : Patients à risque multiple ────────────────────────────────────────
print("\n=== 3.4 : Profil patients à risque élevé ===");

const patientsRisque = db.patients.aggregate([
  {
    $match: {
      antecedents: { $all: ["Diabète type 2", "HTA"] },
      dateNaissance: { $lte: new Date(new Date().setFullYear(new Date().getFullYear() - 60)) }
    }
  },
  {
    $addFields: {
      age: {
        $dateDiff: { startDate: "$dateNaissance", endDate: "$$NOW", unit: "year" }
      },
      nb_consultations: { $size: "$consultations" }
    }
  },
  {
    $group: {
      _id: null,
      total_patients_risque: { $sum: 1 },
      age_moyen: { $avg: "$age" },
      consultations_moyennes: { $avg: "$nb_consultations" }
    }
  }
]).toArray();

// ─── 3.5 : Rapport médecins ───────────────────────────────────────────────────
print("\n=== 3.5 : Top 5 médecins & taux de ré-consultation ===");

const rapportMedecins = db.patients.aggregate([
  { $unwind: "$consultations" },
  {
    $group: {
      _id: "$consultations.medecin.nom",
      total_consultations: { $sum: 1 },
      patients_uniques: { $addToSet: "$_id" }
    }
  },
  {
    $addFields: {
      nb_patients_uniques: { $size: "$patients_uniques" },
      taux_reconsultation: {
        $multiply: [
          {
            $divide: [
              { $subtract: ["$total_consultations", { $size: "$patients_uniques" }] },
              { $size: "$patients_uniques" }
            ]
          },
          100
        ]
      }
    }
  },
  { $sort: { total_consultations: -1 } },
  { $limit: 5 }
]).toArray();

printjson(rapportMedecins);
