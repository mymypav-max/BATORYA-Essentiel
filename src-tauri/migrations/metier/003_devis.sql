-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 003_devis
-- Troisième tranche : devis, lignes de devis, garanties de lignes.
--
-- Référence : modèle de données SQLite V3.10 — §2 (conventions), §2.4
-- (BLOC-IMP, BLOC-SNAP), §2.5 (énumérations), §3.1 (calcul commercial), §4.6
-- (devis), §6 (numérotation DEV), §7.2 (colonnes modifiables), §8 (TR-01,
-- TR-10, TR-11, TR-14), §9 (index), §10.4 (numéro historique), §17.1.
-- Invariants : INV-04, INV-05, INV-06, INV-10, INV-11, INV-14, INV-20, INV-21,
-- INV-22, INV-23, INV-30, INV-31, INV-34, INV-36, INV-37, INV-49, INV-131,
-- INV-134, INV-136. Décisions : D-09, D-24.
--
-- Précisions de DDL retenues pour cette tranche (à consigner dans le modèle) :
--   * Rattachement client : un devis 'refuse' ou 'annule' reste immuable, sauf
--     la modification de client_id (et updated_at) lorsque l'ancien client est
--     'a_rattacher' (INV-49, modèle §4.4) ; même règle pour un devis gelé.
--   * Suppression : aucun trigger sur DELETE devis. La garde « devis avec BC »
--     est la FK RESTRICT de bons_commande.devis_id (tranche BC, INV-06).
--     Supprimer un devis supprime ses lignes et leurs garanties en CASCADE.
--   * statut sans valeur par défaut (le service fournit 'en_attente').
--   * Familles décimales des remises de ligne : pourcentage P2, montant DL (D-09).
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 3 posé par le runner APRÈS succès ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini.
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA.
--
-- Aucune ligne n'est insérée. Le numéro est attribué par le service dans la
-- transaction de création (séquence DEV de numerotation_sequences, année de
-- date_creation ; high-water dans machine.db). Les totaux, arrondis, snapshots,
-- historique, BC, gel (TR-15) et annulation automatique d'acompte relèvent des
-- services et des tranches suivantes : aucune table ni FK vers le BC ici.
--
-- Conventions : toutes les tables sont STRICT (§1) ; TS = TEXT
-- 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé par GLOB ; D = 'YYYY-MM-DD' (date
-- réelle : GLOB + date(x) IS x — date() renvoie NULL pour un mois 00/13 ou un
-- jour 00, et un CHECK évalué à NULL est accepté, donc « = » ne suffit pas) ;
-- D2 = montant à 2 décimales >= 0 ; P2 = pourcentage 0.00 à 100.00 ;
-- DL = décimal à précision libre (§2.3).
-- =====================================================================


-- ---------------------------------------------------------------------
-- devis (§4.6) — BLOC-SNAP, BLOC-IMP
-- numero : DEV-00001-yy, yy = année de date_creation, pour origine = 'v6' ;
-- pour origine = 'import', numéro historique libre mais non vide, unique,
-- immuable (D-24, INV-131). Aucun legacy_numero (réservé à clients et BC).
-- Snapshots client / entreprise / chantier : JSON valide, obligatoires,
-- avec la version du format de chaque JSON (INV-30).
-- remise globale : aucune <=> remise_valeur NULL ; pourcentage P2 ; montant D2.
-- acompte prévu : aucun <=> acompte_valeur NULL ; pourcentage P2 ; montant D2.
-- Statuts : en_attente, accepte, refuse, annule ; l'expiration de la validité
-- est un état dérivé, jamais stocké. frozen_at est posé par TR-15 (tranches
-- factures et règlements) ; ici seul son sens unique est gardé (TR-14).
-- ---------------------------------------------------------------------
CREATE TABLE devis (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                      TEXT    NOT NULL UNIQUE CHECK (numero <> ''),
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
    statut                      TEXT    NOT NULL CHECK (statut IN ('en_attente', 'accepte', 'refuse', 'annule')),
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

    -- numéro V6 : format et année cohérente avec date_creation (INV-20) ; exemption unique : numéro historique importé
    CHECK (origine <> 'v6' OR (numero GLOB 'DEV-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
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


-- ---------------------------------------------------------------------
-- devis_lignes (§4.6) — photographie commerciale de la prestation
-- Ligne libre : prestation_id NULL (aucune pseudo-prestation). La référence
-- saisie est conservée même si la prestation est ensuite désactivée. Le
-- catalogue ne modifie jamais une ligne (INV-37) : aucune action de FK ne
-- propage une modification de prestations vers cette table.
-- quantite > 0 (DL) ; remise de ligne : pourcentage P2, montant DL = montant
-- total de la ligne (D-09) ; total_ht D2 calculé par le service (§3.1).
-- remise_type sans valeur par défaut : le service fournit la valeur.
-- FK devis_id en CASCADE : lignes -> parent avant gel (INV-05) ; l'immutabilité
-- après gel est gardée par TR-11.
-- ---------------------------------------------------------------------
CREATE TABLE devis_lignes (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    devis_id             INTEGER NOT NULL REFERENCES devis (id) ON DELETE CASCADE,
    ordre                INTEGER NOT NULL CHECK (ordre >= 1),
    prestation_id        INTEGER REFERENCES prestations (id) ON DELETE RESTRICT,
    reference_prestation TEXT,
    designation          TEXT    NOT NULL CHECK (designation <> ''),
    description          TEXT,
    quantite             TEXT    NOT NULL
                         CHECK (quantite <> ''
                                AND quantite NOT GLOB '*[^0-9.]*'
                                AND quantite NOT GLOB '*.*.*'
                                AND quantite NOT GLOB '.*'
                                AND quantite NOT GLOB '*.'
                                AND quantite NOT GLOB '*.*0'
                                AND quantite NOT GLOB '0[0-9]*'
                                AND quantite <> '0'),
    unite                TEXT    NOT NULL CHECK (unite IN ('u', 'ens', 'ml', 'm2', 'm3')),
    prix_unitaire_ht     TEXT    NOT NULL
                         CHECK (prix_unitaire_ht <> ''
                                AND prix_unitaire_ht NOT GLOB '*[^0-9.]*'
                                AND prix_unitaire_ht NOT GLOB '*.*.*'
                                AND prix_unitaire_ht NOT GLOB '.*'
                                AND prix_unitaire_ht NOT GLOB '*.'
                                AND prix_unitaire_ht NOT GLOB '*.*0'
                                AND prix_unitaire_ht NOT GLOB '0[0-9]*'),
    remise_type          TEXT    NOT NULL CHECK (remise_type IN ('aucune', 'pourcentage', 'montant')),
    remise_valeur        TEXT,
    type_prestation      TEXT    NOT NULL CHECK (type_prestation IN ('fourniture', 'pose', 'fourniture_pose')),
    total_ht             TEXT    NOT NULL
                         CHECK (total_ht GLOB '[0-9]*.[0-9][0-9]'
                                AND total_ht NOT GLOB '*[^0-9.]*'
                                AND total_ht NOT GLOB '*.*.*'
                                AND total_ht NOT GLOB '0[0-9]*'),
    created_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (devis_id, ordre),
    CHECK ((remise_type = 'aucune') = (remise_valeur IS NULL)),
    CHECK (remise_type <> 'pourcentage' OR (
        remise_valeur GLOB '[0-9]*.[0-9][0-9]'
        AND remise_valeur NOT GLOB '*[^0-9.]*'
        AND remise_valeur NOT GLOB '*.*.*'
        AND remise_valeur NOT GLOB '0[0-9]*'
        AND CAST(REPLACE(remise_valeur, '.', '') AS INTEGER) BETWEEN 0 AND 10000)),
    CHECK (remise_type <> 'montant' OR (
        remise_valeur <> ''
        AND remise_valeur NOT GLOB '*[^0-9.]*'
        AND remise_valeur NOT GLOB '*.*.*'
        AND remise_valeur NOT GLOB '.*'
        AND remise_valeur NOT GLOB '*.'
        AND remise_valeur NOT GLOB '*.*0'
        AND remise_valeur NOT GLOB '0[0-9]*')),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- devis_ligne_garanties (§4.6) — garanties de ligne (snapshots)
-- Copie des garanties du catalogue au moment de la saisie ; jamais source
-- historique du catalogue (INV-37). Le contrat d'import n'en accepte aucune
-- (INV-134). La durée dérive du type : pas de colonne durée.
-- L'index de UNIQUE(ligne_id, garantie_type) couvre la FK.
-- ---------------------------------------------------------------------
CREATE TABLE devis_ligne_garanties (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ligne_id      INTEGER NOT NULL REFERENCES devis_lignes (id) ON DELETE CASCADE,
    garantie_type TEXT    NOT NULL CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale')),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (ligne_id, garantie_type),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK, plus les index de recherche de la tranche.
-- devis_lignes(devis_id, ordre) et devis_ligne_garanties(ligne_id,
-- garantie_type) sont réalisés par leur contrainte UNIQUE.
-- =====================================================================
CREATE INDEX idx_devis_client_id             ON devis (client_id);
CREATE INDEX idx_devis_statut                ON devis (statut);
CREATE INDEX idx_devis_date_creation         ON devis (date_creation);
CREATE INDEX idx_devis_lignes_prestation_id  ON devis_lignes (prestation_id);


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Les triggers BEFORE s'exécutent avant les CHECK de la ligne.
-- =====================================================================

-- TR-01 [INV-23] : numero et date_creation sont immuables ; l'année du numéro
-- (cohérente avec date_creation par CHECK) ne change donc jamais.
CREATE TRIGGER tr_01_devis_numero_immuable
BEFORE UPDATE OF numero, date_creation ON devis
WHEN NEW.numero IS NOT OLD.numero OR NEW.date_creation IS NOT OLD.date_creation
BEGIN
    SELECT RAISE(ABORT, 'INV-23: devis.numero et devis.date_creation sont immuables');
END;

-- TR-10 [INV-31] : devis modifiable ('en_attente', ou 'accepte' non gelé) —
-- seuls id et created_at restent immuables (numero, date_creation : TR-01 ;
-- frozen_at : TR-14, passage NULL -> valeur permis, il est posé par TR-15).
CREATE TRIGGER tr_10_devis_modifiable
BEFORE UPDATE ON devis
WHEN (OLD.statut = 'en_attente' OR (OLD.statut = 'accepte' AND OLD.frozen_at IS NULL))
 AND (NEW.id IS NOT OLD.id OR NEW.created_at IS NOT OLD.created_at)
BEGIN
    SELECT RAISE(ABORT, 'INV-31: devis.id et devis.created_at sont immuables');
END;

-- TR-10 [INV-31, INV-49] : devis 'refuse' ou 'annule' immuable ; seule exception,
-- le rattachement d'un client 'a_rattacher' (client_id, updated_at).
CREATE TRIGGER tr_10_devis_refuse_annule
BEFORE UPDATE ON devis
WHEN OLD.statut IN ('refuse', 'annule')
 AND (NEW.id IS NOT OLD.id
        OR NEW.numero IS NOT OLD.numero
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_creation IS NOT OLD.date_creation
        OR NEW.date_validite IS NOT OLD.date_validite
        OR NEW.date_acceptation IS NOT OLD.date_acceptation
        OR NEW.date_refus IS NOT OLD.date_refus
        OR NEW.objet IS NOT OLD.objet
        OR NEW.notes IS NOT OLD.notes
        OR NEW.statut IS NOT OLD.statut
        OR NEW.remise_type IS NOT OLD.remise_type
        OR NEW.remise_valeur IS NOT OLD.remise_valeur
        OR NEW.acompte_type IS NOT OLD.acompte_type
        OR NEW.acompte_valeur IS NOT OLD.acompte_valeur
        OR NEW.total_ht IS NOT OLD.total_ht
        OR NEW.frozen_at IS NOT OLD.frozen_at
        OR NEW.cancelled_at IS NOT OLD.cancelled_at
        OR NEW.motif_refus IS NOT OLD.motif_refus
        OR NEW.motif_annulation IS NOT OLD.motif_annulation
        OR NEW.created_at IS NOT OLD.created_at
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data
      OR (NEW.client_id IS NOT OLD.client_id
        AND (SELECT statut FROM clients WHERE id = OLD.client_id) IS NOT 'a_rattacher'))
BEGIN
    SELECT RAISE(ABORT, 'INV-31: devis refuse ou annule immuable (seul le rattachement d''un client a_rattacher est permis)');
END;

-- TR-10 [INV-36, INV-49] : devis 'accepte' gelé — seuls statut, cancelled_at,
-- motif_annulation, updated_at et le rattachement d'un client 'a_rattacher'.
CREATE TRIGGER tr_10_devis_gele
BEFORE UPDATE ON devis
WHEN OLD.statut = 'accepte' AND OLD.frozen_at IS NOT NULL
 AND (NEW.id IS NOT OLD.id
        OR NEW.numero IS NOT OLD.numero
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_creation IS NOT OLD.date_creation
        OR NEW.date_validite IS NOT OLD.date_validite
        OR NEW.date_acceptation IS NOT OLD.date_acceptation
        OR NEW.date_refus IS NOT OLD.date_refus
        OR NEW.objet IS NOT OLD.objet
        OR NEW.notes IS NOT OLD.notes
        OR NEW.remise_type IS NOT OLD.remise_type
        OR NEW.remise_valeur IS NOT OLD.remise_valeur
        OR NEW.acompte_type IS NOT OLD.acompte_type
        OR NEW.acompte_valeur IS NOT OLD.acompte_valeur
        OR NEW.total_ht IS NOT OLD.total_ht
        OR NEW.frozen_at IS NOT OLD.frozen_at
        OR NEW.motif_refus IS NOT OLD.motif_refus
        OR NEW.created_at IS NOT OLD.created_at
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data
      OR (NEW.client_id IS NOT OLD.client_id
        AND (SELECT statut FROM clients WHERE id = OLD.client_id) IS NOT 'a_rattacher'))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: devis gele, seuls statut, annulation et rattachement d''un client a_rattacher sont modifiables');
END;

-- TR-14 [INV-34] : frozen_at passe de NULL à une valeur, jamais l'inverse.
CREATE TRIGGER tr_14_devis_frozen_at
BEFORE UPDATE OF frozen_at ON devis
WHEN OLD.frozen_at IS NOT NULL AND NEW.frozen_at IS NOT OLD.frozen_at
BEGIN
    SELECT RAISE(ABORT, 'INV-34: devis.frozen_at est irreversible');
END;

-- TR-11 [INV-36] : lignes de devis — interdit si le devis est gelé ou non modifiable.
-- (Un devis inexistant n'est pas traité ici : c'est la FK qui refuse.)
CREATE TRIGGER tr_11_devis_lignes_insert
BEFORE INSERT ON devis_lignes
WHEN EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de devis non modifiables (devis gele, refuse ou annule)');
END;

CREATE TRIGGER tr_11_devis_lignes_update
BEFORE UPDATE ON devis_lignes
WHEN EXISTS (SELECT 1 FROM devis d WHERE d.id = OLD.devis_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
  OR EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de devis non modifiables (devis gele, refuse ou annule)');
END;

CREATE TRIGGER tr_11_devis_lignes_delete
BEFORE DELETE ON devis_lignes
WHEN EXISTS (SELECT 1 FROM devis d WHERE d.id = OLD.devis_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de devis non modifiables (devis gele, refuse ou annule)');
END;

-- TR-11 [INV-36] : garanties de lignes de devis — même règle, via la ligne.
CREATE TRIGGER tr_11_devis_ligne_garanties_insert
BEFORE INSERT ON devis_ligne_garanties
WHEN EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = NEW.ligne_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de devis non modifiables (devis gele, refuse ou annule)');
END;

CREATE TRIGGER tr_11_devis_ligne_garanties_update
BEFORE UPDATE ON devis_ligne_garanties
WHEN EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = OLD.ligne_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
  OR EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = NEW.ligne_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de devis non modifiables (devis gele, refuse ou annule)');
END;

CREATE TRIGGER tr_11_devis_ligne_garanties_delete
BEFORE DELETE ON devis_ligne_garanties
WHEN EXISTS (SELECT 1 FROM devis_lignes l JOIN devis d ON d.id = l.devis_id WHERE l.id = OLD.ligne_id
               AND (d.statut IN ('refuse', 'annule') OR (d.statut = 'accepte' AND d.frozen_at IS NOT NULL)))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de devis non modifiables (devis gele, refuse ou annule)');
END;
