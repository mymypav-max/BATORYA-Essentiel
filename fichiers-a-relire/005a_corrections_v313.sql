-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration corrective 005a_corrections_v313
-- Corrective M-A (rang 6) : applique les corrections V3.13 qui concernent
-- clients, fournisseurs et devis. Ce n'est PAS une tranche métier : elle ne
-- consomme aucun numéro de tranche (conventions techniques §5, V-2).
--
-- Référence : modèle de données SQLite V3.13 — §2.5, §4.4, §4.6, §4.19
-- (lignes 1 à 9 et 21), §7, §8 (TR-01, TR-10, TR-11, TR-14, TR-18, TR-97,
-- TR-98, TR-100), §9, §17.1 (ligne 005a) ; conventions techniques §5
-- (chaîne ordonnée, « Transaction et user_version », protocole de
-- reconstruction de table) ; rapport de compatibilité 001–004 avant 005
-- (G-1, G-2, G-3). Propositions techniques : PT-2, PT-3, PT-4, PT-5, PT-17,
-- PT-21. Invariants : INV-04, INV-06, INV-23, INV-31, INV-34, INV-36, INV-175,
-- INV-180, INV-181, INV-182, INV-183, INV-196.
--
-- Périmètre arbitré (2026-10-04) :
--   * périmètre complet de la ligne 005a du §17.1 ;
--   * l'année du numéro d'un devis V6 reste celle de date_creation (PT-2 :
--     aucune nouvelle colonne de date de numérotation) ;
--   * PT-8 (sort de frozen_at), PT-7 (devis_origine_id) et PT-17 (sort de
--     date_refus / motif_refus à la réouverture) restent ouverts : frozen_at,
--     TR-14 et leurs CHECK sont conservés tels quels, devis_origine_id n'est
--     pas créé, date_refus et motif_refus sont conservés à la réouverture.
--
-- Contenu :
--   1. clients reconstruit sans statut ni index de statut (protocole §5 ; PT-3) ;
--   2. fournisseurs.statut retiré par DROP INDEX puis DROP COLUMN, sans
--      reconstruction de fournisseurs (PT-3) ;
--   3. gardes TR-97 : clients et fournisseurs ne se suppriment jamais, code
--      immuable (PT-4) ;
--   4. devis reconstruit : statut 'brouillon', numero nullable, révisions
--      (PT-2, PT-21) ;
--   5. TR-01 devis adapté (numero attribué une fois), TR-10 réécrit (PT-2,
--      PT-17, PT-21), TR-11 réécrit en liste blanche (PT-2, PT-5, PT-21),
--      TR-98 (seul un brouillon se supprime ; la cascade des lignes ne joue
--      donc que pour un brouillon, PT-5) ;
--   6. table devis_revisions (append-only) et TR-100 (PT-21) ;
--   7. objets de 003 et 004 dont la reconstruction impose le retrait puis la
--      recréation (conventions §5, étape 4) : tr_14_devis_frozen_at
--      (identique) ; tr_18_devis_statut_avec_bc et tr_17_bons_commande_insert
--      (004 : logique actuelle, identique, G-2) ; tr_12_bons_commande_gele et
--      tr_12_bons_commande_annule (004 : sans la clause du client
--      'a_rattacher', G-1). Leur adaptation de fond (bc_devis, PT-6, PT-16)
--      appartient à M-B (005b).
--   Objets de 004 vérifiés et laissés tels quels (G-3) : tr_01_bons_commande_
--   numero_immuable, tr_14_bons_commande_frozen_at, tr_19_bons_commande_no_
--   delete ne référencent ni clients ni devis ; tr_12_bons_commande_modifiable
--   non plus. Le retrait de leur dépendance n'est donc pas nécessaire.
--
-- Interprétations retenues pour les points que le modèle laisse à valider
-- (chacune est testée ; à confirmer ou corriger avant 005b) :
--   * date_creation d'un devis reste immuable, brouillon compris (TR-01 de 003
--     inchangé) ; seul numero passe de NULL à une valeur une fois (finalisation) ;
--   * devis 'accepte' et 'refuse' : seuls statut, date_acceptation, date_refus,
--     motif_refus, cancelled_at, motif_annulation, frozen_at (NULL -> valeur,
--     TR-14) et updated_at se modifient ; 'refuse' ne peut que redevenir
--     'en_attente' ; 'annule' est terminal (seul updated_at se modifie) ;
--   * contenu d'un devis 'en_attente' (snapshots et leurs versions, objet,
--     notes, date_validite, remise, acompte, total_ht) : modifiable seulement
--     si revision_en_cours = 1 ;
--   * transitions de revision / revision_en_cours : démarrage (0 -> 1),
--     abandon (1 -> 0, revision inchangé), validation (1 -> 0, revision passe
--     à COALESCE(revision, 0) + 1 et le snapshot de ce numéro existe déjà) ;
--   * sortie de 'brouillon' : le snapshot de la version initiale
--     (devis_revisions.revision IS NULL) existe déjà ; l'INSERT d'une révision
--     numérotée exige un devis 'en_attente' avec revision_en_cours = 1 et le
--     numéro consécutif ; l'INSERT de la version initiale n'est soumis qu'à
--     l'index unique partiel (une seule par devis) ;
--   * les devis déjà présents ne reçoivent AUCUN snapshot : la migration ne
--     crée aucune donnée (le contrôle CK-15 les signalera).
--
-- Exécution par le runner de migrations (côté Rust) — protocole de
-- reconstruction, conventions §5 :
--   * hors transaction : PRAGMA foreign_keys = OFF, puis relecture (= 0) ;
--   * une seule transaction pour ce fichier (BEGIN IMMEDIATE) ;
--   * ce fichier = étapes 4 à 11 ; puis, dans la transaction :
--     PRAGMA foreign_key_check (résultat vide), PRAGMA integrity_check,
--     PRAGMA user_version = 6 (rang de 005a), COMMIT ; échec = ROLLBACK intégral ;
--   * hors transaction : PRAGMA foreign_keys = ON, puis relecture (= 1) ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--     foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--     recursive_triggers=ON (D-39).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA d'écriture. Il refuse toutefois
-- de s'exécuter si foreign_keys est actif (un DROP TABLE avec foreign_keys=ON
-- supprimerait en silence les lignes liées en CASCADE) ou si user_version n'est pas
-- 5 (gardes ci-dessous, en lecture seule).
-- Aucune ligne n'est créée : les seules écritures sont la copie technique des
-- lignes existantes (ids conservés) et la conservation de sqlite_sequence.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Gardes d'exécution (lecture seule, aucune trace) :
--   * foreign_keys doit valoir 0 (étapes 1 et 2 du protocole) ;
--   * user_version doit valoir 5 : 005a est le rang 6 et ne s'applique qu'à une
--     base arrêtée à 005 (chaîne 005 -> 005a, jamais 004 -> 005a ; une base déjà
--     au rang 6 ou plus ne la rejoue pas).
-- Tables temporaires supprimées aussitôt ; échec = erreur de CHECK, donc ROLLBACK.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE garde_005a_foreign_keys_off (
    foreign_keys INTEGER NOT NULL
        CONSTRAINT "005a exige PRAGMA foreign_keys = OFF (protocole de reconstruction)" CHECK (foreign_keys = 0)
);
INSERT INTO garde_005a_foreign_keys_off (foreign_keys) SELECT foreign_keys FROM pragma_foreign_keys;
DROP TABLE garde_005a_foreign_keys_off;

CREATE TEMP TABLE garde_005a_user_version (
    user_version INTEGER NOT NULL
        CONSTRAINT "005a exige user_version = 5 (chaine 005 -> 005a)" CHECK (user_version = 5)
);
INSERT INTO garde_005a_user_version (user_version) SELECT user_version FROM pragma_user_version;
DROP TABLE garde_005a_user_version;


-- =====================================================================
-- Étape 4 — retrait des triggers qui référencent clients ou devis (ou qui sont
-- posés sur devis), y compris ceux d'autres tables.
-- =====================================================================
-- 003 : devis
DROP TRIGGER tr_01_devis_numero_immuable;
DROP TRIGGER tr_10_devis_modifiable;
DROP TRIGGER tr_10_devis_refuse_annule;
DROP TRIGGER tr_10_devis_gele;
DROP TRIGGER tr_14_devis_frozen_at;
-- 003 : lignes et garanties de lignes (lisent devis)
DROP TRIGGER tr_11_devis_lignes_insert;
DROP TRIGGER tr_11_devis_lignes_update;
DROP TRIGGER tr_11_devis_lignes_delete;
DROP TRIGGER tr_11_devis_ligne_garanties_insert;
DROP TRIGGER tr_11_devis_ligne_garanties_update;
DROP TRIGGER tr_11_devis_ligne_garanties_delete;
-- 004 : posés sur devis ou sur bons_commande, lisent devis ou clients
DROP TRIGGER tr_18_devis_statut_avec_bc;
DROP TRIGGER tr_17_bons_commande_insert;
DROP TRIGGER tr_12_bons_commande_gele;
DROP TRIGGER tr_12_bons_commande_annule;


-- =====================================================================
-- clients (§4.4) — reconstruction sans statut (PT-3)
-- Retirés : colonne statut, CHECK statut <> 'a_rattacher' OR origine = 'import',
-- idx_clients_statut. Tout le reste est repris à l'identique de 001.
-- =====================================================================
CREATE TABLE clients_new (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT    NOT NULL UNIQUE CHECK (code GLOB 'CLI-[0-9][0-9][0-9][0-9]'),
    nom           TEXT    NOT NULL CHECK (nom <> ''),
    prenom        TEXT,
    adresse       TEXT,
    cpville       TEXT,
    tel           TEXT,
    email         TEXT,
    notes         TEXT,
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP+
    origine       TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id     TEXT,
    legacy_data   TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),
    legacy_numero TEXT,

    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL AND legacy_numero IS NULL)),
    CHECK (legacy_numero IS NULL OR legacy_numero <> code),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

INSERT INTO clients_new (id, code, nom, prenom, adresse, cpville, tel, email, notes,
                         created_at, updated_at, origine, legacy_id, legacy_data, legacy_numero)
SELECT id, code, nom, prenom, adresse, cpville, tel, email, notes,
       created_at, updated_at, origine, legacy_id, legacy_data, legacy_numero
  FROM clients
 ORDER BY id;

-- sqlite_sequence : la nouvelle valeur est >= à l'ancienne (INV-04, étape 7)
UPDATE sqlite_sequence
   SET seq = max(seq, COALESCE((SELECT seq FROM sqlite_sequence WHERE name = 'clients'), 0))
 WHERE name = 'clients_new';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'clients_new', seq FROM sqlite_sequence
 WHERE name = 'clients'
   AND NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = 'clients_new');

DROP TABLE clients;
ALTER TABLE clients_new RENAME TO clients;


-- =====================================================================
-- fournisseurs (§4.4) — retrait de statut, SANS reconstruction (PT-3)
-- Ordre imposé : l'index d'abord, puis la colonne.
-- =====================================================================
DROP INDEX idx_fournisseurs_statut;
ALTER TABLE fournisseurs DROP COLUMN statut;


-- =====================================================================
-- devis (§4.6) — reconstruction (PT-2, PT-21)
-- Changements par rapport à 003 :
--   * statut accepte 'brouillon' ; numero devient nullable (NULL <=> brouillon) ;
--   * revision (NULL = version initiale, sinon >= 1) et revision_en_cours (0/1) ;
--   * format du numéro V6 conditionné par numero NOT NULL ; son année reste
--     celle de date_creation.
-- Inchangés : frozen_at et ses CHECK (PT-8 ouvert), date_refus / motif_refus et
-- CHECK statut = 'refuse' => date_refus (PT-17 ouvert), toutes les familles
-- décimales, BLOC-SNAP, BLOC-IMP. Aucune colonne devis_origine_id (PT-7 ouvert).
-- =====================================================================
CREATE TABLE devis_new (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                      TEXT    UNIQUE CHECK (numero IS NULL OR numero <> ''),
    client_id                   INTEGER NOT NULL REFERENCES clients (id) ON DELETE RESTRICT,
    -- BLOC-SNAP
    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot)),
    client_snapshot_version     INTEGER NOT NULL,
    entreprise_snapshot         TEXT    NOT NULL CHECK (json_valid(entreprise_snapshot)),
    entreprise_snapshot_version INTEGER NOT NULL,
    chantier_snapshot           TEXT    NOT NULL CHECK (json_valid(chantier_snapshot)),
    chantier_snapshot_version   INTEGER NOT NULL,
    date_creation               TEXT    NOT NULL CHECK (date_creation GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_creation) IS date_creation),
    date_validite               TEXT    CHECK (date_validite IS NULL OR
                              (date_validite GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_validite) IS date_validite)),
    date_acceptation            TEXT    CHECK (date_acceptation IS NULL OR
                              (date_acceptation GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_acceptation) IS date_acceptation)),
    date_refus                  TEXT    CHECK (date_refus IS NULL OR
                              (date_refus GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_refus) IS date_refus)),
    objet                       TEXT,
    notes                       TEXT,
    statut                      TEXT    NOT NULL CHECK (statut IN ('brouillon', 'en_attente', 'accepte', 'refuse', 'annule')),
    revision                    INTEGER CHECK (revision IS NULL OR revision >= 1),
    revision_en_cours           INTEGER NOT NULL DEFAULT 0 CHECK (revision_en_cours IN (0, 1)),
    remise_type                 TEXT    NOT NULL DEFAULT 'aucune' CHECK (remise_type IN ('aucune', 'pourcentage', 'montant')),
    remise_valeur               TEXT,
    acompte_type                TEXT    NOT NULL DEFAULT 'aucun' CHECK (acompte_type IN ('aucun', 'pourcentage', 'montant')),
    acompte_valeur              TEXT,
    total_ht                    TEXT    NOT NULL
                                CHECK (total_ht GLOB '[0-9]*.[0-9][0-9]'
                                       AND total_ht NOT GLOB '*[^0-9.]*'
                                       AND total_ht NOT GLOB '*.*.*'
                                       AND total_ht NOT GLOB '0[0-9]*'),
    frozen_at                   TEXT,
    cancelled_at                TEXT,
    motif_refus                 TEXT,
    motif_annulation            TEXT,
    created_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP
    origine                     TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id                   TEXT,
    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),

    -- brouillon <=> pas de numéro (PT-2) ; un brouillon n'a ni révision ni phase de révision (PT-21)
    CHECK ((statut = 'brouillon') = (numero IS NULL)),
    CHECK (statut <> 'brouillon' OR (revision IS NULL AND revision_en_cours = 0)),
    CHECK (revision_en_cours = 0 OR statut = 'en_attente'),
    -- numéro V6 : format et année cohérente avec date_creation (INV-20) ; exemption unique : numéro historique importé
    CHECK (origine <> 'v6' OR numero IS NULL OR (numero GLOB 'DEV-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
                               AND substr(numero, 11, 2) = substr(date_creation, 3, 2))),
    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
    -- remise globale et acompte prévu
    CHECK ((remise_type = 'aucune') = (remise_valeur IS NULL)),
    CHECK (remise_type <> 'pourcentage' OR (
        remise_valeur GLOB '[0-9]*.[0-9][0-9]'
        AND remise_valeur NOT GLOB '*[^0-9.]*'
        AND remise_valeur NOT GLOB '*.*.*'
        AND remise_valeur NOT GLOB '0[0-9]*'
        AND CAST(REPLACE(remise_valeur, '.', '') AS INTEGER) BETWEEN 0 AND 10000)),
    CHECK (remise_type <> 'montant' OR (
        remise_valeur GLOB '[0-9]*.[0-9][0-9]'
        AND remise_valeur NOT GLOB '*[^0-9.]*'
        AND remise_valeur NOT GLOB '*.*.*'
        AND remise_valeur NOT GLOB '0[0-9]*')),
    CHECK ((acompte_type = 'aucun') = (acompte_valeur IS NULL)),
    CHECK (acompte_type <> 'pourcentage' OR (
        acompte_valeur GLOB '[0-9]*.[0-9][0-9]'
        AND acompte_valeur NOT GLOB '*[^0-9.]*'
        AND acompte_valeur NOT GLOB '*.*.*'
        AND acompte_valeur NOT GLOB '0[0-9]*'
        AND CAST(REPLACE(acompte_valeur, '.', '') AS INTEGER) BETWEEN 0 AND 10000)),
    CHECK (acompte_type <> 'montant' OR (
        acompte_valeur GLOB '[0-9]*.[0-9][0-9]'
        AND acompte_valeur NOT GLOB '*[^0-9.]*'
        AND acompte_valeur NOT GLOB '*.*.*'
        AND acompte_valeur NOT GLOB '0[0-9]*')),
    -- statuts
    CHECK (statut <> 'accepte' OR date_acceptation IS NOT NULL),
    CHECK (statut <> 'refuse' OR date_refus IS NOT NULL),
    CHECK ((statut = 'annule') = (cancelled_at IS NOT NULL)),
    CHECK (cancelled_at IS NULL OR (motif_annulation IS NOT NULL AND motif_annulation <> '')),
    CHECK (frozen_at IS NULL OR statut IN ('accepte', 'annule')),
    CHECK (date_validite IS NULL OR date_validite >= date_creation),
    CHECK (frozen_at IS NULL OR frozen_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (cancelled_at IS NULL OR cancelled_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

INSERT INTO devis_new (id, numero, client_id,
                       client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version,
                       chantier_snapshot, chantier_snapshot_version,
                       date_creation, date_validite, date_acceptation, date_refus, objet, notes, statut,
                       remise_type, remise_valeur, acompte_type, acompte_valeur, total_ht,
                       frozen_at, cancelled_at, motif_refus, motif_annulation,
                       created_at, updated_at, origine, legacy_id, legacy_data)
SELECT id, numero, client_id,
       client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version,
       chantier_snapshot, chantier_snapshot_version,
       date_creation, date_validite, date_acceptation, date_refus, objet, notes, statut,
       remise_type, remise_valeur, acompte_type, acompte_valeur, total_ht,
       frozen_at, cancelled_at, motif_refus, motif_annulation,
       created_at, updated_at, origine, legacy_id, legacy_data
  FROM devis
 ORDER BY id;

-- sqlite_sequence : la nouvelle valeur est >= à l'ancienne (INV-04, étape 7)
UPDATE sqlite_sequence
   SET seq = max(seq, COALESCE((SELECT seq FROM sqlite_sequence WHERE name = 'devis'), 0))
 WHERE name = 'devis_new';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'devis_new', seq FROM sqlite_sequence
 WHERE name = 'devis'
   AND NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = 'devis_new');

DROP TABLE devis;
ALTER TABLE devis_new RENAME TO devis;

CREATE INDEX idx_devis_client_id             ON devis (client_id);
CREATE INDEX idx_devis_statut                ON devis (statut);
CREATE INDEX idx_devis_date_creation         ON devis (date_creation);


-- =====================================================================
-- devis_revisions (§4.6, PT-21) — snapshots complets des versions validées,
-- version initiale incluse (revision IS NULL). Append-only (TR-100).
-- Il n'existe jamais de révision 0. L'index de UNIQUE(devis_id, revision)
-- couvre la FK ; SQLite considère deux NULL comme distincts dans un UNIQUE
-- ordinaire : l'index unique partiel garantit une seule version initiale.
-- =====================================================================
CREATE TABLE devis_revisions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    devis_id       INTEGER NOT NULL REFERENCES devis (id) ON DELETE RESTRICT,
    revision       INTEGER CHECK (revision IS NULL OR revision >= 1),
    schema_contenu INTEGER NOT NULL CHECK (schema_contenu >= 1),
    contenu        TEXT    NOT NULL CHECK (json_valid(contenu) AND json_type(contenu) = 'object'),
    total_ht       TEXT    NOT NULL
                   CHECK (total_ht GLOB '[0-9]*.[0-9][0-9]'
                          AND total_ht NOT GLOB '*[^0-9.]*'
                          AND total_ht NOT GLOB '*.*.*'
                          AND total_ht NOT GLOB '0[0-9]*'),
    valide_at      TEXT    NOT NULL,
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (devis_id, revision),
    CHECK (valide_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

CREATE UNIQUE INDEX uq_devis_revisions_initiale ON devis_revisions (devis_id) WHERE revision IS NULL;


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Les triggers BEFORE s'exécutent avant les CHECK de la ligne.
-- Un parent inexistant n'est jamais traité ici : c'est la FK qui refuse.
-- =====================================================================

-- ---------------------------------------------------------------------
-- clients et fournisseurs : TR-97 [INV-183, INV-06] (PT-4)
-- Aucune suppression, jamais ; code immuable. Avec recursive_triggers=ON, le
-- trigger DELETE refuse aussi le DELETE implicite d'un INSERT OR REPLACE.
-- ---------------------------------------------------------------------
CREATE TRIGGER tr_97_clients_no_delete
BEFORE DELETE ON clients
BEGIN
    SELECT RAISE(ABORT, 'INV-183: un client ne se supprime jamais');
END;

CREATE TRIGGER tr_97_clients_code_immuable
BEFORE UPDATE OF code ON clients
WHEN NEW.code IS NOT OLD.code
BEGIN
    SELECT RAISE(ABORT, 'INV-183: clients.code est immuable');
END;

CREATE TRIGGER tr_97_fournisseurs_no_delete
BEFORE DELETE ON fournisseurs
BEGIN
    SELECT RAISE(ABORT, 'INV-183: un fournisseur ne se supprime jamais');
END;

CREATE TRIGGER tr_97_fournisseurs_code_immuable
BEFORE UPDATE OF code ON fournisseurs
WHEN NEW.code IS NOT OLD.code
BEGIN
    SELECT RAISE(ABORT, 'INV-183: fournisseurs.code est immuable');
END;

-- ---------------------------------------------------------------------
-- devis
-- ---------------------------------------------------------------------

-- TR-01 [INV-23, INV-180] : numero est attribué une fois (NULL -> valeur à la
-- finalisation), puis immuable ; date_creation est immuable. L'année du numéro
-- (cohérente avec date_creation par CHECK) ne change donc jamais.
CREATE TRIGGER tr_01_devis_numero_immuable
BEFORE UPDATE OF numero, date_creation ON devis
WHEN (OLD.numero IS NOT NULL AND NEW.numero IS NOT OLD.numero) OR NEW.date_creation IS NOT OLD.date_creation
BEGIN
    SELECT RAISE(ABORT, 'INV-23: devis.numero et devis.date_creation sont immuables');
END;

-- TR-14 [INV-34] : frozen_at passe de NULL à une valeur, jamais l'inverse
-- (conservé tel quel : PT-8 ouvert).
CREATE TRIGGER tr_14_devis_frozen_at
BEFORE UPDATE OF frozen_at ON devis
WHEN OLD.frozen_at IS NOT NULL AND NEW.frozen_at IS NOT OLD.frozen_at
BEGIN
    SELECT RAISE(ABORT, 'INV-34: devis.frozen_at est irreversible');
END;

-- TR-10 [INV-31] : id et created_at sont immuables dans tous les états.
CREATE TRIGGER tr_10_devis_modifiable
BEFORE UPDATE ON devis
WHEN NEW.id IS NOT OLD.id OR NEW.created_at IS NOT OLD.created_at
BEGIN
    SELECT RAISE(ABORT, 'INV-31: devis.id et devis.created_at sont immuables');
END;

-- TR-10 [INV-180] : client_id est immuable après la finalisation.
CREATE TRIGGER tr_10_devis_client_immuable
BEFORE UPDATE OF client_id ON devis
WHEN OLD.statut <> 'brouillon' AND NEW.client_id IS NOT OLD.client_id
BEGIN
    SELECT RAISE(ABORT, 'INV-180: devis.client_id est immuable apres la finalisation');
END;

-- TR-10 [INV-196] : devis 'en_attente' — le contenu (snapshots et leurs versions,
-- objet, notes, date_validite, remise, acompte, total_ht) ne se modifie que
-- pendant une phase de révision. Statut, dates et motifs liés au statut,
-- revision et revision_en_cours (tr_10_devis_revision) restent libres ici.
CREATE TRIGGER tr_10_devis_en_attente
BEFORE UPDATE ON devis
WHEN OLD.statut = 'en_attente' AND OLD.revision_en_cours = 0
 AND (NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_validite IS NOT OLD.date_validite
        OR NEW.objet IS NOT OLD.objet
        OR NEW.notes IS NOT OLD.notes
        OR NEW.remise_type IS NOT OLD.remise_type
        OR NEW.remise_valeur IS NOT OLD.remise_valeur
        OR NEW.acompte_type IS NOT OLD.acompte_type
        OR NEW.acompte_valeur IS NOT OLD.acompte_valeur
        OR NEW.total_ht IS NOT OLD.total_ht)
BEGIN
    SELECT RAISE(ABORT, 'INV-196: devis en_attente, le contenu ne se modifie que pendant une phase de revision');
END;

-- TR-10 [INV-181, INV-182] : devis 'accepte' ou 'refuse' verrouillé — seuls
-- statut, date_acceptation, date_refus, motif_refus, cancelled_at,
-- motif_annulation, frozen_at (TR-14) et updated_at se modifient (id et
-- created_at : tr_10_devis_modifiable ; numero et date_creation : TR-01 ;
-- client_id : tr_10_devis_client_immuable). Un devis 'refuse' ne peut que
-- redevenir 'en_attente' (réouverture, numéro et contenu inchangés).
CREATE TRIGGER tr_10_devis_verrouille
BEFORE UPDATE ON devis
WHEN OLD.statut IN ('accepte', 'refuse')
BEGIN
    SELECT RAISE(ABORT, 'INV-181: devis accepte ou refuse verrouille, seuls statut, dates et motifs lies au statut et updated_at sont modifiables')
     WHERE NEW.client_id IS NOT OLD.client_id
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_validite IS NOT OLD.date_validite
        OR NEW.objet IS NOT OLD.objet
        OR NEW.notes IS NOT OLD.notes
        OR NEW.revision IS NOT OLD.revision
        OR NEW.revision_en_cours IS NOT OLD.revision_en_cours
        OR NEW.remise_type IS NOT OLD.remise_type
        OR NEW.remise_valeur IS NOT OLD.remise_valeur
        OR NEW.acompte_type IS NOT OLD.acompte_type
        OR NEW.acompte_valeur IS NOT OLD.acompte_valeur
        OR NEW.total_ht IS NOT OLD.total_ht
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data;
    SELECT RAISE(ABORT, 'INV-182: un devis refuse ne peut que redevenir en_attente')
     WHERE OLD.statut = 'refuse' AND NEW.statut NOT IN ('refuse', 'en_attente');
END;

-- TR-10 [INV-31] : devis 'annule' terminal — seul updated_at se modifie.
CREATE TRIGGER tr_10_devis_annule
BEFORE UPDATE ON devis
WHEN OLD.statut = 'annule'
 AND (NEW.client_id IS NOT OLD.client_id
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_validite IS NOT OLD.date_validite
        OR NEW.date_acceptation IS NOT OLD.date_acceptation
        OR NEW.date_refus IS NOT OLD.date_refus
        OR NEW.objet IS NOT OLD.objet
        OR NEW.notes IS NOT OLD.notes
        OR NEW.statut IS NOT OLD.statut
        OR NEW.revision IS NOT OLD.revision
        OR NEW.revision_en_cours IS NOT OLD.revision_en_cours
        OR NEW.remise_type IS NOT OLD.remise_type
        OR NEW.remise_valeur IS NOT OLD.remise_valeur
        OR NEW.acompte_type IS NOT OLD.acompte_type
        OR NEW.acompte_valeur IS NOT OLD.acompte_valeur
        OR NEW.total_ht IS NOT OLD.total_ht
        OR NEW.frozen_at IS NOT OLD.frozen_at
        OR NEW.cancelled_at IS NOT OLD.cancelled_at
        OR NEW.motif_refus IS NOT OLD.motif_refus
        OR NEW.motif_annulation IS NOT OLD.motif_annulation
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data)
BEGIN
    SELECT RAISE(ABORT, 'INV-31: devis annule terminal, seul updated_at est modifiable');
END;

-- TR-10 [INV-196] : transitions de revision / revision_en_cours — démarrage
-- (0 -> 1), abandon (1 -> 0, revision inchangé) ou validation (1 -> 0, revision
-- passe à COALESCE(revision, 0) + 1 et le snapshot de ce numéro existe déjà).
CREATE TRIGGER tr_10_devis_revision
BEFORE UPDATE OF revision, revision_en_cours ON devis
WHEN (NEW.revision IS NOT OLD.revision OR NEW.revision_en_cours IS NOT OLD.revision_en_cours)
 AND NOT ((OLD.revision_en_cours = 0 AND NEW.revision_en_cours = 1 AND NEW.revision IS OLD.revision)
       OR (OLD.revision_en_cours = 1 AND NEW.revision_en_cours = 0 AND NEW.revision IS OLD.revision)
       OR (OLD.revision_en_cours = 1 AND NEW.revision_en_cours = 0
           AND NEW.revision IS COALESCE(OLD.revision, 0) + 1
           AND EXISTS (SELECT 1 FROM devis_revisions r WHERE r.devis_id = OLD.id AND r.revision IS NEW.revision)))
BEGIN
    SELECT RAISE(ABORT, 'INV-196: transition de revision invalide (demarrage, abandon, ou validation avec son snapshot)');
END;

-- TR-10 [INV-196] : un devis ne s'accepte pas pendant une phase de révision.
CREATE TRIGGER tr_10_devis_acceptation
BEFORE UPDATE OF statut ON devis
WHEN NEW.statut = 'accepte' AND OLD.revision_en_cours = 1
BEGIN
    SELECT RAISE(ABORT, 'INV-196: un devis ne s''accepte pas pendant une phase de revision');
END;

-- TR-10 [INV-180, INV-196] : finalisation — le snapshot de la version initiale
-- (devis_revisions, revision NULL) existe déjà quand le devis quitte 'brouillon'.
CREATE TRIGGER tr_10_devis_finalisation
BEFORE UPDATE OF statut ON devis
WHEN OLD.statut = 'brouillon' AND NEW.statut <> 'brouillon'
 AND NOT EXISTS (SELECT 1 FROM devis_revisions r WHERE r.devis_id = OLD.id AND r.revision IS NULL)
BEGIN
    SELECT RAISE(ABORT, 'INV-196: finalisation d''un devis, le snapshot de la version initiale doit exister');
END;

-- TR-98 [INV-180, INV-06] (PT-5) : seul un devis 'brouillon' se supprime. Les
-- lignes et garanties de lignes (FK CASCADE de 003) ne disparaissent donc qu'avec
-- un brouillon. Avec recursive_triggers=ON, refuse aussi le DELETE implicite
-- d'un INSERT OR REPLACE.
CREATE TRIGGER tr_98_devis_no_delete
BEFORE DELETE ON devis
WHEN OLD.statut <> 'brouillon'
BEGIN
    SELECT RAISE(ABORT, 'INV-180: seul un devis brouillon se supprime');
END;

-- TR-18 [INV-175] (004, recréé à l'identique : bons_commande.devis_id existe
-- encore au rang 6 ; adaptation par M-B) : un devis ayant un BC ne quitte
-- 'accepte' que si ce BC est annulé.
CREATE TRIGGER tr_18_devis_statut_avec_bc
BEFORE UPDATE OF statut ON devis
WHEN OLD.statut = 'accepte' AND NEW.statut IS NOT 'accepte'
 AND EXISTS (SELECT 1 FROM bons_commande b WHERE b.devis_id = OLD.id AND b.statut <> 'annule')
BEGIN
    SELECT RAISE(ABORT, 'INV-175: un devis ayant un bon de commande ne quitte accepte que si ce bon de commande est annule');
END;

-- ---------------------------------------------------------------------
-- devis_lignes et devis_ligne_garanties : TR-11 [INV-36, INV-180, INV-196]
-- Liste blanche (PT-2, PT-5, PT-21) : modifiables seulement si le devis est
-- 'brouillon', ou 'en_attente' avec revision_en_cours = 1 ; refusées dans tous
-- les autres cas. Un devis inexistant n'est pas traité ici : c'est la FK.
-- (Suppression d'un brouillon : la ligne parente est déjà supprimée quand les
-- triggers DELETE s'exécutent en cascade ; le brouillon est de toute façon
-- une cible autorisée.)
-- ---------------------------------------------------------------------
CREATE TRIGGER tr_11_devis_lignes_insert
BEFORE INSERT ON devis_lignes
WHEN EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de devis modifiables seulement en brouillon ou pendant une phase de revision');
END;

CREATE TRIGGER tr_11_devis_lignes_update
BEFORE UPDATE ON devis_lignes
WHEN EXISTS (SELECT 1 FROM devis d WHERE d.id = OLD.devis_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
  OR EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de devis modifiables seulement en brouillon ou pendant une phase de revision');
END;

CREATE TRIGGER tr_11_devis_lignes_delete
BEFORE DELETE ON devis_lignes
WHEN EXISTS (SELECT 1 FROM devis d WHERE d.id = OLD.devis_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de devis modifiables seulement en brouillon ou pendant une phase de revision');
END;

CREATE TRIGGER tr_11_devis_ligne_garanties_insert
BEFORE INSERT ON devis_ligne_garanties
WHEN EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = NEW.ligne_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de devis modifiables seulement en brouillon ou pendant une phase de revision');
END;

CREATE TRIGGER tr_11_devis_ligne_garanties_update
BEFORE UPDATE ON devis_ligne_garanties
WHEN EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = OLD.ligne_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
  OR EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = NEW.ligne_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de devis modifiables seulement en brouillon ou pendant une phase de revision');
END;

CREATE TRIGGER tr_11_devis_ligne_garanties_delete
BEFORE DELETE ON devis_ligne_garanties
WHEN EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = OLD.ligne_id
               AND NOT (d.statut = 'brouillon' OR (d.statut = 'en_attente' AND d.revision_en_cours = 1)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de devis modifiables seulement en brouillon ou pendant une phase de revision');
END;

-- ---------------------------------------------------------------------
-- devis_revisions : TR-100 [INV-196] (PT-21) — append-only
-- ---------------------------------------------------------------------
CREATE TRIGGER tr_100_devis_revisions_no_update
BEFORE UPDATE ON devis_revisions
BEGIN
    SELECT RAISE(ABORT, 'INV-196: devis_revisions est append-only');
END;

CREATE TRIGGER tr_100_devis_revisions_no_delete
BEFORE DELETE ON devis_revisions
BEGIN
    SELECT RAISE(ABORT, 'INV-196: devis_revisions est append-only');
END;

-- INSERT : la version initiale (revision NULL) n'est soumise qu'à l'index unique
-- partiel ; une révision numérotée exige un devis 'en_attente' en phase de
-- révision et le numéro consécutif COALESCE(MAX(revision), 0) + 1.
CREATE TRIGGER tr_100_devis_revisions_insert
BEFORE INSERT ON devis_revisions
WHEN NEW.revision IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'INV-196: une revision numerotee ne s''ajoute que pendant une phase de revision (devis en_attente, revision_en_cours = 1)')
     WHERE EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id
                     AND NOT (d.statut = 'en_attente' AND d.revision_en_cours = 1));
    SELECT RAISE(ABORT, 'INV-196: les revisions sont numerotees sans trou (derniere revision + 1)')
     WHERE NEW.revision IS NOT (SELECT COALESCE(MAX(r.revision), 0) + 1 FROM devis_revisions r WHERE r.devis_id = NEW.devis_id);
END;

-- ---------------------------------------------------------------------
-- bons_commande (004) : triggers retirés puis recréés (G-1, G-2)
-- ---------------------------------------------------------------------

-- TR-17 [INV-40, INV-48] : recréé à l'identique de 004 (lit devis ; adaptation
-- par M-B).
CREATE TRIGGER tr_17_bons_commande_insert
BEFORE INSERT ON bons_commande
BEGIN
    SELECT RAISE(ABORT, 'INV-40: un bon de commande nait d''un devis accepte')
     WHERE EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id AND d.statut <> 'accepte');
    SELECT RAISE(ABORT, 'INV-48: bons_commande.client_id doit etre celui du devis')
     WHERE EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id AND d.client_id IS NOT NEW.client_id);
    SELECT RAISE(ABORT, 'INV-40: etat de naissance d''un bon de commande (en_cours, non gele, caches a zero, sans date_100_facture ni motif d''annulation)')
     WHERE NEW.statut IS NOT 'en_cours'
        OR NEW.frozen_at IS NOT NULL
        OR NEW.date_100_facture IS NOT NULL
        OR NEW.motif_annulation IS NOT NULL
        OR NEW.montant_deja_facture_ht IS NOT '0.00'
        OR NEW.avancement IS NOT '0.00';
END;

-- TR-12 [INV-36] : BC gelé (non annulé) — liste blanche de 004 (caches,
-- date_debut, date_fin, cancelled_at, motif_annulation, updated_at) ; la clause du
-- client 'a_rattacher' disparaît avec le statut (INV-183) : client_id est
-- désormais immuable.
CREATE TRIGGER tr_12_bons_commande_gele
BEFORE UPDATE ON bons_commande
WHEN OLD.frozen_at IS NOT NULL AND OLD.statut <> 'annule'
 AND (NEW.id IS NOT OLD.id
        OR NEW.devis_id IS NOT OLD.devis_id
        OR NEW.client_id IS NOT OLD.client_id
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_acceptation IS NOT OLD.date_acceptation
        OR NEW.montant_contractuel_ht IS NOT OLD.montant_contractuel_ht
        OR NEW.remise_type IS NOT OLD.remise_type
        OR NEW.remise_valeur IS NOT OLD.remise_valeur
        OR NEW.acompte_type IS NOT OLD.acompte_type
        OR NEW.acompte_valeur IS NOT OLD.acompte_valeur
        OR NEW.created_at IS NOT OLD.created_at
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data
        OR NEW.legacy_numero IS NOT OLD.legacy_numero)
BEGIN
    SELECT RAISE(ABORT, 'INV-36: bon de commande gele, seuls caches, dates de debut et fin et annulation sont modifiables');
END;

-- TR-12 [INV-173] : BC annulé (gelé ou non) — terminal : seul updated_at est
-- modifiable (clause du client 'a_rattacher' retirée, INV-183).
CREATE TRIGGER tr_12_bons_commande_annule
BEFORE UPDATE ON bons_commande
WHEN OLD.statut = 'annule'
 AND (NEW.id IS NOT OLD.id
        OR NEW.devis_id IS NOT OLD.devis_id
        OR NEW.client_id IS NOT OLD.client_id
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_acceptation IS NOT OLD.date_acceptation
        OR NEW.date_debut IS NOT OLD.date_debut
        OR NEW.date_fin IS NOT OLD.date_fin
        OR NEW.montant_contractuel_ht IS NOT OLD.montant_contractuel_ht
        OR NEW.remise_type IS NOT OLD.remise_type
        OR NEW.remise_valeur IS NOT OLD.remise_valeur
        OR NEW.acompte_type IS NOT OLD.acompte_type
        OR NEW.acompte_valeur IS NOT OLD.acompte_valeur
        OR NEW.montant_deja_facture_ht IS NOT OLD.montant_deja_facture_ht
        OR NEW.avancement IS NOT OLD.avancement
        OR NEW.date_100_facture IS NOT OLD.date_100_facture
        OR NEW.statut IS NOT OLD.statut
        OR NEW.completed_at IS NOT OLD.completed_at
        OR NEW.cancelled_at IS NOT OLD.cancelled_at
        OR NEW.motif_annulation IS NOT OLD.motif_annulation
        OR NEW.frozen_at IS NOT OLD.frozen_at
        OR NEW.created_at IS NOT OLD.created_at
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data
        OR NEW.legacy_numero IS NOT OLD.legacy_numero)
BEGIN
    SELECT RAISE(ABORT, 'INV-173: bon de commande annule terminal, seul updated_at est modifiable');
END;
