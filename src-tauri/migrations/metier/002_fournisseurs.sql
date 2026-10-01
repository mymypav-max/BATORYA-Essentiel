-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 002_fournisseurs
-- Deuxième tranche : fournisseurs.
--
-- Référence : modèle de données SQLite V3.10 — §2 (conventions), §4.4
-- (fournisseurs), §6 (numérotation FOU), §9 (index), §10.3 (bloc refusé),
-- §17.1. Invariants : INV-04, INV-05, INV-06, INV-10, INV-20, INV-21, INV-22,
-- INV-25, INV-100. Décisions : D-01, D-23.
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 2 posé par le runner APRÈS succès ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini.
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA.
--
-- Aucune ligne n'est insérée. Le code est attribué par le service dans la
-- transaction de création, via la séquence FOU (numerotation_sequences,
-- annee = 0, plafond 9 999 — migration 001 ; high-water dans machine.db).
--
-- Conventions : table STRICT (§1) ; TS = TEXT 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC)
-- contrôlé par GLOB.
-- =====================================================================


-- ---------------------------------------------------------------------
-- fournisseurs (§4.4)
-- Entité indépendante référencée par identifiant (INV-100) ; aucune FK
-- sortante. Le contrôle de suppression d'un fournisseur ayant un historique
-- est la FK RESTRICT de depenses.fournisseur_id (INV-05, INV-06), créée par la
-- tranche des dépenses : un fournisseur ayant un historique est archivé.
-- statut : 'actif' ou 'archive', sans valeur par défaut (le service le fournit).
-- Un fournisseur 'archive' reste consultable mais n'est pas sélectionnable
-- pour une nouvelle dépense (règle de service, tranche des dépenses).
-- code : FOU-0001, sans exception d'origine (INV-20) ; séquence FOU, annee = 0.
-- Pas de BLOC-IMP : le bloc 'fournisseurs' est refusé par import-v6.json
-- (modèle §10.3, D-01, D-23). Aucun autre champ que ceux du modèle.
-- ---------------------------------------------------------------------
CREATE TABLE fournisseurs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    NOT NULL UNIQUE CHECK (code GLOB 'FOU-[0-9][0-9][0-9][0-9]'),
    nom        TEXT    NOT NULL CHECK (nom <> ''),
    adresse    TEXT,
    cpville    TEXT,
    tel        TEXT,
    email      TEXT,
    notes      TEXT,
    statut     TEXT    NOT NULL CHECK (statut IN ('actif', 'archive')),
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9)
-- =====================================================================
CREATE INDEX idx_fournisseurs_statut ON fournisseurs (statut);
