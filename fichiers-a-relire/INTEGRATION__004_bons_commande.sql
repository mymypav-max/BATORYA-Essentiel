-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 004_bons_commande
-- Quatrième tranche : bons de commande, lignes de BC, garanties de lignes de BC.
--
-- Référence : modèle de données SQLite V3.12 — §2 (conventions), §2.4
-- (BLOC-IMP, BLOC-SNAP), §2.5 (énumérations), §4.7 (bons de commande), §4.18
-- (précisions de DDL), §6 (numérotation BCD), §7.2 (colonnes modifiables),
-- §8 (TR-01, TR-12, TR-13, TR-14, TR-17, TR-18, TR-19, TR-96), §9 (index),
-- §14 (CK-13, diagnostic hors SQL).
-- Invariants : INV-04, INV-05, INV-06, INV-10, INV-20, INV-22, INV-23, INV-31,
-- INV-34, INV-36, INV-40, INV-46, INV-48, INV-49, INV-136, INV-173, INV-174,
-- INV-175, INV-176. Décisions : D-34 à D-39.
--
-- Précisions de DDL retenues pour cette tranche :
--   * Un BC n'est jamais supprimé (INV-174) : tr_19 refuse tout DELETE ;
--     bons_commande.devis_id, bc_lignes.bc_id et bc_lignes.devis_ligne_id sont en
--     RESTRICT ; seule bc_ligne_garanties.ligne_id est en CASCADE (garanties ->
--     ligne, avant gel). Aucune clause ON UPDATE.
--   * Un BC annulé est terminal (INV-173) : seuls client_id (rattachement d'un
--     client 'a_rattacher', INV-49) et updated_at restent modifiables.
--   * tr_17 ne contrôle que des invariants locaux : devis 'accepte', client_id
--     du devis, état de naissance. Aucune comparaison avec le devis au-delà ;
--     la cohérence devis <-> BC (liste S) est construite par le service et
--     détectée par CK-13 (requête de diagnostic, jamais un CHECK ni un
--     trigger de miroir). Le devis 'inexistant' reste refusé par la FK.
--   * Dates : date_creation = jour d'enregistrement du BC (son année donne le
--     yy du numéro) ; date_acceptation = date contractuelle copiée du devis ;
--     aucun ordre imposé entre elles. La borne d'année 2001-2099 des dates de
--     numérotation est une règle de service (D-38), jamais un CHECK.
--   * Numéro BCD-nnnnn-yy sans condition d'origine (le convertisseur génère les
--     numéros de BC ; l'ancien numéro va dans legacy_numero, différent de numero).
--   * tr_96_numerotation_sequences_no_delete complète tr_95 (migration 001,
--     immuable) : aucune ligne de séquence ne se supprime, directement ou par
--     le DELETE implicite d'un INSERT OR REPLACE (effectif avec
--     recursive_triggers=ON). L'upsert maîtrisé reste possible.
--   * 'termine' et les caches (montant_deja_facture_ht, avancement,
--     date_100_facture, completed_at) sont écrits par le service financier, en
--     un seul UPDATE ; cette migration n'anticipe aucune table de facturation.
--   * La règle d'annulation (INV-44) dépend de la facturation : elle reste dans
--     le service. Aucune FK vers une table future.
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 4 posé par le runner APRÈS succès ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--       recursive_triggers=ON (D-39).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA.
--
-- Aucune ligne n'est insérée. Le numéro est attribué par le service dans la
-- transaction de création (séquence BCD de numerotation_sequences, année de
-- date_creation ; high-water dans machine.db).
--
-- Conventions : toutes les tables sont STRICT (§1) ; TS = TEXT
-- 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé par GLOB ; D = 'YYYY-MM-DD' (date
-- réelle : GLOB + date(x) IS x — date() renvoie NULL pour un mois 00/13 ou un
-- jour 00, et un CHECK évalué à NULL est accepté, donc « = » ne suffit pas) ;
-- D2 = montant à 2 décimales >= 0 ; P2 = pourcentage 0.00 à 100.00 ;
-- DL = décimal à précision libre (§2.3). Les GLOB sont explicites (pas de {n}).
-- =====================================================================


-- ---------------------------------------------------------------------
-- bons_commande (§4.7) — BLOC-SNAP, BLOC-IMP+
-- Un BC par devis (UNIQUE devis_id). Il naît 'en_cours' (défauts de colonnes,
-- tr_17 et CHECK statut <-> completed_at / cancelled_at). Snapshots, remise,
-- acompte et montant contractuel sont copiés du devis par le service.
-- Caches (montant_deja_facture_ht, avancement, date_100_facture, statut,
-- completed_at) : écrits par le service financier en un seul UPDATE ; seuls les
-- CHECK « sûrs » sont posés. Aucun CHECK montant_deja_facture_ht <=
-- montant_contractuel_ht (relation transitoirement fausse dans une transaction
-- de modification) ni entre date_acceptation et date_creation.
-- ---------------------------------------------------------------------
CREATE TABLE bons_commande (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                      TEXT    NOT NULL UNIQUE,
    devis_id                    INTEGER NOT NULL UNIQUE REFERENCES devis (id) ON DELETE RESTRICT,
    client_id                   INTEGER NOT NULL REFERENCES clients (id) ON DELETE RESTRICT,
    -- BLOC-SNAP
    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot)),
    client_snapshot_version     INTEGER NOT NULL,
    entreprise_snapshot         TEXT    NOT NULL CHECK (json_valid(entreprise_snapshot)),
    entreprise_snapshot_version INTEGER NOT NULL,
    chantier_snapshot           TEXT    NOT NULL CHECK (json_valid(chantier_snapshot)),
    chantier_snapshot_version   INTEGER NOT NULL,
    date_creation               TEXT    NOT NULL CHECK (date_creation GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_creation) IS date_creation),
    date_acceptation            TEXT    NOT NULL CHECK (date_acceptation GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_acceptation) IS date_acceptation),
    date_debut                  TEXT    CHECK (date_debut IS NULL OR
                              (date_debut GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_debut) IS date_debut)),
    date_fin                    TEXT    CHECK (date_fin IS NULL OR
                              (date_fin GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_fin) IS date_fin)),
    montant_contractuel_ht      TEXT    NOT NULL
                                CHECK (montant_contractuel_ht GLOB '[0-9]*.[0-9][0-9]'
                                       AND montant_contractuel_ht NOT GLOB '*[^0-9.]*'
                                       AND montant_contractuel_ht NOT GLOB '*.*.*'
                                       AND montant_contractuel_ht NOT GLOB '0[0-9]*'),
    remise_type                 TEXT    NOT NULL CHECK (remise_type IN ('aucune', 'pourcentage', 'montant')),
    remise_valeur               TEXT,
    acompte_type                TEXT    NOT NULL CHECK (acompte_type IN ('aucun', 'pourcentage', 'montant')),
    acompte_valeur              TEXT,
    -- caches (service financier)
    montant_deja_facture_ht     TEXT    NOT NULL DEFAULT '0.00'
                                CHECK (montant_deja_facture_ht GLOB '[0-9]*.[0-9][0-9]'
                                       AND montant_deja_facture_ht NOT GLOB '*[^0-9.]*'
                                       AND montant_deja_facture_ht NOT GLOB '*.*.*'
                                       AND montant_deja_facture_ht NOT GLOB '0[0-9]*'),
    avancement                  TEXT    NOT NULL DEFAULT '0.00'
                                CHECK (avancement GLOB '[0-9]*.[0-9][0-9]'
                                       AND avancement NOT GLOB '*[^0-9.]*'
                                       AND avancement NOT GLOB '*.*.*'
                                       AND avancement NOT GLOB '0[0-9]*'
                                       AND CAST(REPLACE(avancement, '.', '') AS INTEGER) BETWEEN 0 AND 10000),
    date_100_facture            TEXT    CHECK (date_100_facture IS NULL OR
                              (date_100_facture GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_100_facture) IS date_100_facture)),
    statut                      TEXT    NOT NULL DEFAULT 'en_cours' CHECK (statut IN ('en_cours', 'termine', 'annule')),
    completed_at                TEXT,
    cancelled_at                TEXT,
    motif_annulation            TEXT,
    frozen_at                   TEXT,
    created_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP+
    origine                     TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id                   TEXT,
    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),
    legacy_numero               TEXT,

    -- numéro : format et année cohérente avec date_creation (INV-20), sans condition d'origine
    CHECK (numero GLOB 'BCD-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
           AND substr(numero, 11, 2) = substr(date_creation, 3, 2)),
    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL AND legacy_numero IS NULL)),
    CHECK (legacy_numero IS NULL OR legacy_numero <> numero),
    -- remise globale et acompte prévu (mêmes règles que devis, sans défaut)
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
    -- statuts et caches sûrs
    CHECK ((statut = 'termine') = (completed_at IS NOT NULL)),
    CHECK (statut <> 'termine' OR date_100_facture IS NOT NULL),
    CHECK ((statut = 'annule') = (cancelled_at IS NOT NULL)),
    CHECK (cancelled_at IS NULL OR (motif_annulation IS NOT NULL AND motif_annulation <> '')),
    CHECK (statut <> 'termine' OR frozen_at IS NOT NULL),
    CHECK (date_100_facture IS NULL OR frozen_at IS NOT NULL),
    CHECK (date_100_facture IS NULL OR avancement = '100.00'),
    CHECK (date_debut IS NULL OR date_fin IS NULL OR date_fin >= date_debut),
    CHECK (completed_at IS NULL OR completed_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (cancelled_at IS NULL OR cancelled_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (frozen_at IS NULL OR frozen_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- bc_lignes (§4.7) — copie des lignes du devis du BC (1:1)
-- Mêmes colonnes que devis_lignes + bc_id et devis_ligne_id.
-- bc_id en RESTRICT : un BC n'est jamais supprimé (INV-174) ; les lignes
-- régénérées avant gel le sont par un DELETE explicite, gardé par tr_13.
-- devis_ligne_id : UNIQUE (une ligne de devis n'apparaît qu'une fois, dans un
-- seul BC), RESTRICT. Pas de colonne active (aucune facture ne référence une
-- ligne de BC avant le gel). Ligne libre : prestation_id NULL.
-- ---------------------------------------------------------------------
CREATE TABLE bc_lignes (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    bc_id                INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    devis_ligne_id       INTEGER NOT NULL UNIQUE REFERENCES devis_lignes (id) ON DELETE RESTRICT,
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

    UNIQUE (bc_id, ordre),
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
-- bc_ligne_garanties (§4.7) — garanties de ligne snapshotées au niveau du BC
-- Copiées de devis_ligne_garanties à la création, jamais lues du catalogue
-- (INV-37). Un BC importé n'en a aucune (INV-134). Aucune génération
-- automatique : la gestion métier des garanties relève de la tranche Garanties.
-- L'index de UNIQUE(ligne_id, garantie_type) couvre la FK.
-- ---------------------------------------------------------------------
CREATE TABLE bc_ligne_garanties (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ligne_id      INTEGER NOT NULL REFERENCES bc_lignes (id) ON DELETE CASCADE,
    garantie_type TEXT    NOT NULL CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale')),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (ligne_id, garantie_type),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK, plus les index de recherche de la tranche.
-- numero, devis_id, bc_lignes.devis_ligne_id, bc_lignes(bc_id, ordre) et
-- bc_ligne_garanties(ligne_id, garantie_type) sont réalisés par leur UNIQUE.
-- =====================================================================
CREATE INDEX idx_bons_commande_client_id    ON bons_commande (client_id);
CREATE INDEX idx_bons_commande_statut       ON bons_commande (statut);
CREATE INDEX idx_bc_lignes_prestation_id    ON bc_lignes (prestation_id);


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Les triggers BEFORE s'exécutent avant les CHECK de la ligne.
-- Un parent inexistant n'est jamais traité ici : c'est la FK qui refuse.
-- =====================================================================

-- TR-01 [INV-23] : numero et date_creation sont immuables ; l'année du numéro
-- (cohérente avec date_creation par CHECK) ne change donc jamais.
CREATE TRIGGER tr_01_bons_commande_numero_immuable
BEFORE UPDATE OF numero, date_creation ON bons_commande
WHEN NEW.numero IS NOT OLD.numero OR NEW.date_creation IS NOT OLD.date_creation
BEGIN
    SELECT RAISE(ABORT, 'INV-23: bons_commande.numero et bons_commande.date_creation sont immuables');
END;

-- TR-12 [INV-36] : BC ni gelé ni annulé — seuls id, devis_id et created_at
-- restent immuables (numero, date_creation : TR-01 ; frozen_at : TR-14, le
-- passage NULL -> valeur est permis, il est posé par TR-15).
CREATE TRIGGER tr_12_bons_commande_modifiable
BEFORE UPDATE ON bons_commande
WHEN OLD.frozen_at IS NULL AND OLD.statut <> 'annule'
 AND (NEW.id IS NOT OLD.id OR NEW.devis_id IS NOT OLD.devis_id OR NEW.created_at IS NOT OLD.created_at)
BEGIN
    SELECT RAISE(ABORT, 'INV-36: bons_commande.id, devis_id et created_at sont immuables');
END;

-- TR-12 [INV-36, INV-49] : BC gelé (non annulé) — liste blanche du modèle §7.2 :
-- caches (montant_deja_facture_ht, avancement, date_100_facture, statut,
-- completed_at), date_debut, date_fin, cancelled_at, motif_annulation,
-- updated_at, et le rattachement d'un client 'a_rattacher' (client_id).
-- numero et date_creation sont gardés par TR-01, frozen_at par TR-14.
CREATE TRIGGER tr_12_bons_commande_gele
BEFORE UPDATE ON bons_commande
WHEN OLD.frozen_at IS NOT NULL AND OLD.statut <> 'annule'
 AND (NEW.id IS NOT OLD.id
        OR NEW.devis_id IS NOT OLD.devis_id
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
        OR NEW.legacy_numero IS NOT OLD.legacy_numero
      OR (NEW.client_id IS NOT OLD.client_id
        AND (SELECT statut FROM clients WHERE id = OLD.client_id) IS NOT 'a_rattacher'))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: bon de commande gele, seuls caches, dates de debut et fin, annulation et rattachement d''un client a_rattacher sont modifiables');
END;

-- TR-12 [INV-173, INV-49] : BC annulé (gelé ou non) — terminal : seuls updated_at
-- et le rattachement d'un client 'a_rattacher' (client_id) sont modifiables.
-- numero et date_creation sont gardés par TR-01.
CREATE TRIGGER tr_12_bons_commande_annule
BEFORE UPDATE ON bons_commande
WHEN OLD.statut = 'annule'
 AND (NEW.id IS NOT OLD.id
        OR NEW.devis_id IS NOT OLD.devis_id
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
        OR NEW.legacy_numero IS NOT OLD.legacy_numero
      OR (NEW.client_id IS NOT OLD.client_id
        AND (SELECT statut FROM clients WHERE id = OLD.client_id) IS NOT 'a_rattacher'))
BEGIN
    SELECT RAISE(ABORT, 'INV-173: bon de commande annule terminal (seul le rattachement d''un client a_rattacher est permis)');
END;

-- TR-14 [INV-34] : frozen_at passe de NULL à une valeur, jamais l'inverse.
CREATE TRIGGER tr_14_bons_commande_frozen_at
BEFORE UPDATE OF frozen_at ON bons_commande
WHEN OLD.frozen_at IS NOT NULL AND NEW.frozen_at IS NOT OLD.frozen_at
BEGIN
    SELECT RAISE(ABORT, 'INV-34: bons_commande.frozen_at est irreversible');
END;

-- TR-17 [INV-40, INV-48] : invariants locaux à la création — le devis existant
-- est 'accepte', client_id est celui du devis, état de naissance. Aucune
-- comparaison du BC avec le devis au-delà (construite par le service, détectée
-- par CK-13). completed_at et cancelled_at NULL sont forcés par les CHECK
-- statut <-> completed_at / cancelled_at.
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

-- TR-19 [INV-174] : aucun BC n'est jamais supprimé, quel que soit son état.
-- Avec recursive_triggers=ON, ce trigger refuse aussi le DELETE implicite d'un
-- INSERT OR REPLACE.
CREATE TRIGGER tr_19_bons_commande_no_delete
BEFORE DELETE ON bons_commande
BEGIN
    SELECT RAISE(ABORT, 'INV-174: un bon de commande ne se supprime jamais');
END;

-- TR-18 [INV-175] : un devis ayant un BC ne quitte 'accepte' que si ce BC est annulé.
CREATE TRIGGER tr_18_devis_statut_avec_bc
BEFORE UPDATE OF statut ON devis
WHEN OLD.statut = 'accepte' AND NEW.statut IS NOT 'accepte'
 AND EXISTS (SELECT 1 FROM bons_commande b WHERE b.devis_id = OLD.id AND b.statut <> 'annule')
BEGIN
    SELECT RAISE(ABORT, 'INV-175: un devis ayant un bon de commande ne quitte accepte que si ce bon de commande est annule');
END;

-- TR-13 [INV-36, INV-173, INV-175] : lignes de BC — interdit si le BC est gelé
-- ou annulé ; la ligne de devis référencée appartient au devis du BC (INSERT et
-- UPDATE). Un BC ou une ligne de devis inexistants sont refusés par les FK.
CREATE TRIGGER tr_13_bc_lignes_insert
BEFORE INSERT ON bc_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de bon de commande non modifiables (BC gele ou annule)')
     WHERE EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = NEW.bc_id
                     AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'));
    SELECT RAISE(ABORT, 'INV-175: la ligne de devis doit appartenir au devis du bon de commande')
     WHERE EXISTS (SELECT 1 FROM bons_commande b, devis_lignes dl
                    WHERE b.id = NEW.bc_id AND dl.id = NEW.devis_ligne_id AND dl.devis_id <> b.devis_id);
END;

CREATE TRIGGER tr_13_bc_lignes_update
BEFORE UPDATE ON bc_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de bon de commande non modifiables (BC gele ou annule)')
     WHERE EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = OLD.bc_id
                     AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'))
        OR EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = NEW.bc_id
                     AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'));
    SELECT RAISE(ABORT, 'INV-175: la ligne de devis doit appartenir au devis du bon de commande')
     WHERE EXISTS (SELECT 1 FROM bons_commande b, devis_lignes dl
                    WHERE b.id = NEW.bc_id AND dl.id = NEW.devis_ligne_id AND dl.devis_id <> b.devis_id);
END;

CREATE TRIGGER tr_13_bc_lignes_delete
BEFORE DELETE ON bc_lignes
WHEN EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = OLD.bc_id
               AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: lignes de bon de commande non modifiables (BC gele ou annule)');
END;

-- TR-13 [INV-36, INV-173] : garanties de lignes de BC — même règle, via la ligne.
-- (Suppression en CASCADE depuis la ligne : la ligne parente est déjà supprimée
-- quand ce trigger s'exécute ; la garde repose alors sur tr_13_bc_lignes_delete.)
CREATE TRIGGER tr_13_bc_ligne_garanties_insert
BEFORE INSERT ON bc_ligne_garanties
WHEN EXISTS (SELECT 1 FROM bc_lignes l JOIN bons_commande b ON b.id = l.bc_id WHERE l.id = NEW.ligne_id
               AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de bon de commande non modifiables (BC gele ou annule)');
END;

CREATE TRIGGER tr_13_bc_ligne_garanties_update
BEFORE UPDATE ON bc_ligne_garanties
WHEN EXISTS (SELECT 1 FROM bc_lignes l JOIN bons_commande b ON b.id = l.bc_id WHERE l.id = OLD.ligne_id
               AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'))
  OR EXISTS (SELECT 1 FROM bc_lignes l JOIN bons_commande b ON b.id = l.bc_id WHERE l.id = NEW.ligne_id
               AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de bon de commande non modifiables (BC gele ou annule)');
END;

CREATE TRIGGER tr_13_bc_ligne_garanties_delete
BEFORE DELETE ON bc_ligne_garanties
WHEN EXISTS (SELECT 1 FROM bc_lignes l JOIN bons_commande b ON b.id = l.bc_id WHERE l.id = OLD.ligne_id
               AND (b.frozen_at IS NOT NULL OR b.statut = 'annule'))
BEGIN
    SELECT RAISE(ABORT, 'INV-36: garanties de lignes de bon de commande non modifiables (BC gele ou annule)');
END;

-- TR-96 [INV-22] : une ligne de numerotation_sequences ne se supprime jamais.
-- Complète tr_95 (UPDATE, migration 001 immuable) : un REPLACE ne déclenche pas
-- les triggers UPDATE ; avec recursive_triggers=ON, son DELETE implicite
-- déclenche ce trigger. L'upsert maîtrisé (ON CONFLICT DO UPDATE) reste permis.
CREATE TRIGGER tr_96_numerotation_sequences_no_delete
BEFORE DELETE ON numerotation_sequences
BEGIN
    SELECT RAISE(ABORT, 'INV-22: numerotation_sequences ne se supprime jamais');
END;
