-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 001_initial
-- Première tranche : import_anomalies, séquences, listes de référence,
-- clients, catalogue.
--
-- Référence : modèle de données SQLite V3.9 — §2 (conventions), §4.1 à §4.5,
-- §4.17 (précisions de DDL), §8 (TR-90, TR-95), §9 (index), §17.1.
-- Invariants : INV-04, INV-05, INV-06, INV-10, INV-11, INV-14, INV-20, INV-21,
-- INV-22, INV-27, INV-49, INV-130, INV-136, INV-165, INV-166.
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 1 posé par le runner APRÈS succès ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini.
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA.
--
-- Aucune ligne n'est insérée : les listes de référence (catégories de
-- prestations, catégories de dépenses D-18) et le catalogue par défaut sont
-- livrés par le jeu de données d'installation (D-14, modèle §10.1), pas par la
-- migration de schéma.
--
-- Conventions : toutes les tables sont STRICT (§1) ; TS = TEXT
-- 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé par GLOB ; D = 'YYYY-MM-DD' (date
-- réelle) ; DL = décimal à précision libre (§2.3).
-- =====================================================================


-- ---------------------------------------------------------------------
-- import_anomalies (§4.1) — créée en premier
-- Anomalies déclarées par import-v6.json : 'a_verifier' (objet importé à
-- contrôler) ou 'non_importe' (donnée non représentable, conservée).
-- type_entite : texte non vide, sans CHECK IN (exception à la règle des liens
-- polymorphes, modèle §2.1 et §4.17 point 7) ; valeurs définies par le contrat
-- import-v6.json (point P-04). Pas de FK : lien polymorphe, contrôlé par CK-09.
-- Jamais supprimée ; seuls statut et traite_at évoluent, une fois (TR-90).
-- ---------------------------------------------------------------------
CREATE TABLE import_anomalies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type_entite TEXT    NOT NULL CHECK (type_entite <> ''),
    entite_id   INTEGER,
    ref_source  TEXT    NOT NULL CHECK (ref_source <> ''),
    categorie   TEXT    NOT NULL CHECK (categorie IN ('a_verifier', 'non_importe')),
    motif       TEXT    NOT NULL CHECK (motif <> ''),
    donnees     TEXT    CHECK (donnees IS NULL OR json_valid(donnees)),
    statut      TEXT    NOT NULL DEFAULT 'a_traiter' CHECK (statut IN ('a_traiter', 'traite')),
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    traite_at   TEXT,

    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (traite_at IS NULL OR traite_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK ((statut = 'a_traiter') = (traite_at IS NULL)),
    -- a_verifier => objet V6 concerné renseigné
    CHECK (categorie <> 'a_verifier' OR entite_id IS NOT NULL),
    -- non_importe => aucun objet V6, donnée conservée
    CHECK (categorie <> 'non_importe' OR (entite_id IS NULL AND donnees IS NOT NULL))
) STRICT;


-- ---------------------------------------------------------------------
-- numerotation_sequences (§4.2, §6) [INV-20 à INV-22]
-- Une séquence par (type_objet, annee) ; annee sur 2 chiffres, 0 pour CLI/FOU.
-- Situation et solde partagent FAC ; ACP et AVO sont séparés.
-- dernier_numero ne diminue jamais (TR-95) ; plafond 99 999 (documents),
-- 9 999 (CLI/FOU). Attribution, dans la transaction de création du document :
--   INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero)
--   VALUES (?, ?, 1)
--   ON CONFLICT (type_objet, annee)
--   DO UPDATE SET dernier_numero = dernier_numero + 1,
--                 updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
--   RETURNING dernier_numero;
-- Au plafond, le CHECK refuse l'écriture ; le service la traduit en erreur
-- métier explicite.
-- ---------------------------------------------------------------------
CREATE TABLE numerotation_sequences (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    type_objet     TEXT    NOT NULL
                   CHECK (type_objet IN ('CLI', 'FOU', 'DEV', 'BCD', 'ACP', 'FAC', 'AVO', 'PVR', 'DEP')),
    annee          INTEGER NOT NULL DEFAULT 0 CHECK (annee BETWEEN 0 AND 99),
    dernier_numero INTEGER NOT NULL DEFAULT 0,
    derniere_date  TEXT,
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (type_objet, annee),
    CHECK ((type_objet IN ('CLI', 'FOU')) = (annee = 0)),
    CHECK (dernier_numero BETWEEN 0 AND CASE WHEN type_objet IN ('CLI', 'FOU') THEN 9999 ELSE 99999 END),
    CHECK (derniere_date IS NULL OR
           (derniere_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(derniere_date) = derniere_date)),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- Référentiels de listes (§4.3) — modifiables par l'utilisateur
-- Contenu initial : jeu de données d'installation (catégories de dépenses :
-- décision D-18), pas cette migration.
-- ---------------------------------------------------------------------
CREATE TABLE categories_prestations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    NOT NULL UNIQUE CHECK (code <> ''),
    libelle    TEXT    NOT NULL CHECK (libelle <> ''),
    actif      INTEGER NOT NULL CHECK (actif IN (0, 1)),
    ordre      INTEGER,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

CREATE TABLE categories_depenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    NOT NULL UNIQUE CHECK (code <> ''),
    libelle    TEXT    NOT NULL CHECK (libelle <> ''),
    actif      INTEGER NOT NULL CHECK (actif IN (0, 1)),
    ordre      INTEGER,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- clients (§4.4) — BLOC-IMP+ (§2.4)
-- code : CLI-0001, sans exception d'origine (D-01, INV-20, INV-27) ; l'ancien
-- code d'un client importé va dans legacy_numero (seulement s'il diffère).
-- statut 'a_rattacher' réservé aux clients importés (INV-49 : le rattachement
-- réaffecte client_id, tracé, via les tables et triggers des tranches
-- suivantes). Un client ayant un historique est archivé, jamais supprimé
-- (INV-06 : FK RESTRICT des documents, tranches suivantes).
-- ---------------------------------------------------------------------
CREATE TABLE clients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT    NOT NULL UNIQUE CHECK (code GLOB 'CLI-[0-9][0-9][0-9][0-9]'),
    nom           TEXT    NOT NULL CHECK (nom <> ''),
    prenom        TEXT,
    adresse       TEXT,
    cpville       TEXT,
    tel           TEXT,
    email         TEXT,
    notes         TEXT,
    statut        TEXT    NOT NULL DEFAULT 'actif' CHECK (statut IN ('actif', 'archive', 'a_rattacher')),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP+
    origine       TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id     TEXT,
    legacy_data   TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),
    legacy_numero TEXT,

    CHECK (statut <> 'a_rattacher' OR origine = 'import'),
    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL AND legacy_numero IS NULL)),
    CHECK (legacy_numero IS NULL OR legacy_numero <> code),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- prestations (§4.5) — BLOC-IMP
-- Désactivée, jamais supprimée si utilisée (INV-06). Une modification du
-- catalogue ne modifie jamais un document existant (INV-37, snapshots des
-- tranches suivantes). ELE-008 absente du catalogue par défaut (INV-166).
-- prix_unitaire_ht : famille DL (précision libre, sans zéro de fin, >= 0).
-- ---------------------------------------------------------------------
CREATE TABLE prestations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    reference        TEXT    NOT NULL UNIQUE CHECK (reference <> ''),
    designation      TEXT    NOT NULL CHECK (designation <> ''),
    description      TEXT,
    categorie_id     INTEGER NOT NULL REFERENCES categories_prestations (id) ON DELETE RESTRICT,
    unite            TEXT    NOT NULL CHECK (unite IN ('u', 'ens', 'ml', 'm2', 'm3')),
    type_prestation  TEXT    NOT NULL CHECK (type_prestation IN ('fourniture', 'pose', 'fourniture_pose')),
    prix_unitaire_ht TEXT    NOT NULL
                     CHECK (prix_unitaire_ht <> ''
                        AND prix_unitaire_ht NOT GLOB '*[^0-9.]*'
                        AND prix_unitaire_ht NOT GLOB '*.*.*'
                        AND prix_unitaire_ht NOT GLOB '.*'
                        AND prix_unitaire_ht NOT GLOB '*.'
                        AND prix_unitaire_ht NOT GLOB '*.*0'
                        AND prix_unitaire_ht NOT GLOB '0[0-9]*'),
    actif            INTEGER NOT NULL CHECK (actif IN (0, 1)),
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP
    origine          TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id        TEXT,
    legacy_data      TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),

    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- prestation_garanties (§4.5)
-- Types de garantie PAR DÉFAUT d'une prestation (un ou plusieurs) ; jamais
-- source historique : les garanties sont copiées en snapshot sur les lignes
-- de devis puis de BC. La durée dérive du type (pas de colonne durée).
-- CASCADE : seule FK en CASCADE de cette tranche (INV-05). L'index de
-- UNIQUE (prestation_id, garantie_type) couvre la FK.
-- ---------------------------------------------------------------------
CREATE TABLE prestation_garanties (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    prestation_id INTEGER NOT NULL REFERENCES prestations (id) ON DELETE CASCADE,
    garantie_type TEXT    NOT NULL CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale')),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (prestation_id, garantie_type),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK, plus les index de recherche de la tranche
-- =====================================================================
CREATE INDEX idx_clients_statut                  ON clients (statut);
CREATE INDEX idx_prestations_categorie_id        ON prestations (categorie_id);
CREATE INDEX idx_prestations_actif               ON prestations (actif);
CREATE INDEX idx_import_anomalies_categorie_statut ON import_anomalies (categorie, statut);


-- =====================================================================
-- Triggers (§8)
-- =====================================================================

-- TR-90 [INV-130] : import_anomalies n'est jamais supprimée.
CREATE TRIGGER tr_90_import_anomalies_no_delete
BEFORE DELETE ON import_anomalies
BEGIN
    SELECT RAISE(ABORT, 'INV-130: import_anomalies ne se supprime jamais');
END;

-- TR-90 [INV-130] : seule transition permise a_traiter -> traite, une fois ;
-- statut et traite_at sont les seules colonnes modifiables.
CREATE TRIGGER tr_90_import_anomalies_update
BEFORE UPDATE ON import_anomalies
WHEN OLD.statut <> 'a_traiter'
  OR NEW.statut <> 'traite'
  OR NEW.id          IS NOT OLD.id
  OR NEW.type_entite IS NOT OLD.type_entite
  OR NEW.entite_id   IS NOT OLD.entite_id
  OR NEW.ref_source  IS NOT OLD.ref_source
  OR NEW.categorie   IS NOT OLD.categorie
  OR NEW.motif       IS NOT OLD.motif
  OR NEW.donnees     IS NOT OLD.donnees
  OR NEW.created_at  IS NOT OLD.created_at
BEGIN
    SELECT RAISE(ABORT, 'INV-130: import_anomalies, seule la transition a_traiter -> traite est permise (statut, traite_at)');
END;

-- TR-95 [INV-22] : dernier_numero ne diminue jamais.
CREATE TRIGGER tr_95_numerotation_sequences_no_decrease
BEFORE UPDATE OF dernier_numero ON numerotation_sequences
WHEN NEW.dernier_numero < OLD.dernier_numero
BEGIN
    SELECT RAISE(ABORT, 'INV-22: numerotation_sequences.dernier_numero ne diminue jamais');
END;
