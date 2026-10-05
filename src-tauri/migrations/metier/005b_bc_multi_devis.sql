-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration corrective 005b_bc_multi_devis
-- Corrective M-B (rang 7) : un bon de commande regroupe plusieurs devis
-- acceptés (BC 1 <- N devis). Ce n'est PAS une tranche métier : elle ne
-- consomme aucun numéro de tranche (conventions techniques §5, V-2).
--
-- Référence : modèle de données SQLite V3.13 — §4.7 (bons de commande,
-- PT-6), §4.19 (lignes 10 à 15, 17 et 18), §8 (TR-12, TR-13, TR-17, TR-18,
-- TR-99), §14 (CK-13, CK-14), §17.1 (ligne 005b) ; conventions techniques §5
-- (chaîne ordonnée, « Transaction et user_version », protocole de
-- reconstruction de table, « Données dans une migration ») ; CADRAGE__005b_
-- bc_multi_devis.md (décisions Q-A à Q-D, 2026-10-05).
-- Invariants : INV-04, INV-05, INV-36, INV-40, INV-48, INV-173, INV-174,
-- INV-175, INV-184, INV-186, INV-187, INV-188, INV-189, INV-192.
-- Décisions métier : Q4 (contenu contractuel du BC verrouillé), Q17 (devis
-- supplémentaire = nouvel objet, rattachable au même BC, aucun avenant), Q23
-- (rattachement tant que le solde n'est pas rédigé/validé ; un avoir ne
-- rouvre pas). Propositions techniques : PT-5, PT-6, PT-7.
--
-- Arbitrages du 2026-10-05 :
--   * Q-A : bons_commande perd remise_* et acompte_* (portés par chaque devis,
--     INV-189, INV-192) ; la migration refuse de s'exécuter si un BC existant
--     diffère de son devis (aucune perte silencieuse d'information) ;
--   * Q-B : frozen_at ne ferme pas le rattachement : seul un BC annulé refuse
--     l'ajout de lignes et de garanties de lignes ;
--   * Q-C : PT-5 inclus (bc_ligne_garanties : ON DELETE RESTRICT) ; PT-16 (caches
--     d'un BC annulé après avoir) reporté à la tranche Facturation ;
--   * Q-D : reprise des liens existants (une ligne bc_devis par BC existant) ;
--     rang >= 1 et UNIQUE(bc_id, rang) ; ni rang contigu ni rang imposé.
--   Non créé : devis.devis_origine_id (PT-7 ouvert, absent du rang 6) ; frozen_at,
--   tr_14 et leurs CHECK sont conservés tels quels (PT-8 « conservateur »).
--
-- Règle de rattachement (INV-187) : un devis accepté crée un BC ou rejoint un BC
-- existant du même client tant que le solde n'est pas rédigé/validé ; un avoir sur
-- le solde ne rouvre pas ; un BC annulé ne reçoit rien. Seule la part « devis
-- accepté, même client, BC non annulé » est garantie par le schéma (TR-99). La part
-- « solde rédigé/validé » est une règle de SERVICE contrôlée par CK-14 : aucun champ
-- existant ne la porte (date_100_facture : INV-43 ; statut : cache qui revient à
-- en_cours après avoir ; frozen_at : sans rôle de clôture, PT-8) et les factures
-- n'existent pas avant 006.
--
-- Contenu :
--   1. gardes d'exécution (foreign_keys = 0, user_version = 6, aucun écart
--      remise/acompte entre un BC et son devis) ;
--   2. retrait des triggers qui référencent bons_commande (tr_18 sur devis,
--      tr_13 sur bc_lignes et bc_ligne_garanties) ;
--   3. table bc_devis (PT-6) et reprise des liens bons_commande.devis_id ;
--   4. bons_commande reconstruit sans devis_id, remise_*, acompte_* (PT-6, PT-7) ;
--   5. bc_ligne_garanties reconstruit avec ON DELETE RESTRICT (PT-5) ;
--   6. triggers : TR-01, TR-12 (contenu contractuel / annulé), TR-14, TR-17
--      (état de naissance), TR-19 recréés ou adaptés ; TR-13 (lignes et garanties),
--      TR-18 (devis), TR-99 (bc_devis).
--   Aucune structure n'est ajoutée à bc_lignes (le devis d'une ligne se lit par
--   devis_ligne_id) ni à devis (aucune unicité, aucun trigger de devis autre que tr_18).
--
-- Exécution par le runner de migrations (côté Rust) — protocole de
-- reconstruction, conventions §5 :
--   * hors transaction : PRAGMA foreign_keys = OFF, puis relecture (= 0) ;
--   * une seule transaction pour ce fichier (BEGIN IMMEDIATE) ;
--   * ce fichier = étapes 4 à 11 ; puis, dans la transaction :
--     PRAGMA foreign_key_check (résultat vide), PRAGMA integrity_check,
--     PRAGMA user_version = 7 (rang de 005b), COMMIT ; échec = ROLLBACK intégral ;
--   * hors transaction : PRAGMA foreign_keys = ON, puis relecture (= 1) ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--     foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--     recursive_triggers=ON (D-39).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA d'écriture.
-- Aucune ligne métier n'est créée : les seules écritures sont la copie technique
-- des lignes existantes (ids conservés), la conservation de sqlite_sequence et la
-- reprise des liens existants (une ligne bc_devis par BC existant).
-- =====================================================================


-- ---------------------------------------------------------------------
-- Gardes d'exécution (lecture seule, aucune trace) :
--   * foreign_keys doit valoir 0 (étapes 1 et 2 du protocole) ;
--   * user_version doit valoir 6 : 005b est le rang 7 et ne s'applique qu'à une
--     base arrêtée à 005a (chaîne 005a -> 005b ; une base au rang 7 ou plus ne la
--     rejoue pas) ;
--   * aucun BC ne doit différer de son devis par la remise ou l'acompte prévu :
--     ces colonnes disparaissent du BC et l'information ne serait plus
--     récupérable ailleurs que dans le devis (Q-A).
-- Tables temporaires supprimées aussitôt ; échec = erreur de CHECK, donc ROLLBACK.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE garde_005b_foreign_keys_off (
    foreign_keys INTEGER NOT NULL
        CONSTRAINT "005b exige PRAGMA foreign_keys = OFF (protocole de reconstruction)" CHECK (foreign_keys = 0)
);
INSERT INTO garde_005b_foreign_keys_off (foreign_keys) SELECT foreign_keys FROM pragma_foreign_keys;
DROP TABLE garde_005b_foreign_keys_off;

CREATE TEMP TABLE garde_005b_user_version (
    user_version INTEGER NOT NULL
        CONSTRAINT "005b exige user_version = 6 (chaine 005a -> 005b)" CHECK (user_version = 6)
);
INSERT INTO garde_005b_user_version (user_version) SELECT user_version FROM pragma_user_version;
DROP TABLE garde_005b_user_version;

CREATE TEMP TABLE garde_005b_remise_acompte (
    ecarts INTEGER NOT NULL
        CONSTRAINT "005b refuse de perdre la remise ou l'acompte d'un BC different de son devis (CK-13)" CHECK (ecarts = 0)
);
INSERT INTO garde_005b_remise_acompte (ecarts)
SELECT COUNT(*)
  FROM bons_commande b
  JOIN devis d ON d.id = b.devis_id
 WHERE b.remise_type  IS NOT d.remise_type
    OR b.remise_valeur IS NOT d.remise_valeur
    OR b.acompte_type  IS NOT d.acompte_type
    OR b.acompte_valeur IS NOT d.acompte_valeur;
DROP TABLE garde_005b_remise_acompte;


-- =====================================================================
-- Étape 4 — retrait des triggers qui référencent bons_commande et ne sont pas
-- posés sur lui (ceux de bons_commande disparaissent avec la table).
-- =====================================================================
DROP TRIGGER tr_18_devis_statut_avec_bc;
DROP TRIGGER tr_13_bc_lignes_insert;
DROP TRIGGER tr_13_bc_lignes_update;
DROP TRIGGER tr_13_bc_lignes_delete;
DROP TRIGGER tr_13_bc_ligne_garanties_insert;
DROP TRIGGER tr_13_bc_ligne_garanties_update;
DROP TRIGGER tr_13_bc_ligne_garanties_delete;


-- =====================================================================
-- bc_devis (§4.7, PT-6) — lien devis <-> BC
-- Un devis n'appartient qu'à un BC (UNIQUE devis_id) ; un BC a un ou plusieurs
-- devis. rang : ordre d'association (>= 1, unique dans un BC) ; ni contigu ni
-- imposé (Q-D). Jamais modifié ni supprimé (TR-99). Les deux FK sont couvertes
-- par leur UNIQUE (devis_id ; bc_id via UNIQUE(bc_id, rang)).
-- =====================================================================
CREATE TABLE bc_devis (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    bc_id      INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    devis_id   INTEGER NOT NULL UNIQUE REFERENCES devis (id) ON DELETE RESTRICT,
    rang       INTEGER NOT NULL CHECK (rang >= 1),
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (bc_id, rang),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

-- Reprise des liens existants (migration de données volontaire, Q-D) : un lien par
-- BC existant, vers son devis ; rang 1 ; created_at du BC ; ordre des ids.
-- Les triggers de bc_devis n'existent pas encore : copie technique, aucune garde.
INSERT INTO bc_devis (bc_id, devis_id, rang, created_at)
SELECT id, devis_id, 1, created_at
  FROM bons_commande
 ORDER BY id;


-- =====================================================================
-- bons_commande (§4.7) — reconstruction (PT-6, PT-7)
-- Changements par rapport à 004 :
--   * devis_id retiré (remplacé par bc_devis) ;
--   * remise_type, remise_valeur, acompte_type, acompte_valeur et leurs CHECK
--     retirés (portés par chaque devis) ;
--   * tout le reste est identique, dont frozen_at et ses CHECK (PT-8).
-- =====================================================================
CREATE TABLE bons_commande_new (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                      TEXT    NOT NULL UNIQUE,
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

INSERT INTO bons_commande_new (id, numero, client_id, client_snapshot, client_snapshot_version,
                               entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot,
                               chantier_snapshot_version, date_creation, date_acceptation, date_debut,
                               date_fin, montant_contractuel_ht, montant_deja_facture_ht, avancement,
                               date_100_facture, statut, completed_at, cancelled_at, motif_annulation,
                               frozen_at, created_at, updated_at, origine, legacy_id, legacy_data,
                               legacy_numero)
SELECT id, numero, client_id, client_snapshot, client_snapshot_version,
       entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot,
       chantier_snapshot_version, date_creation, date_acceptation, date_debut,
       date_fin, montant_contractuel_ht, montant_deja_facture_ht, avancement,
       date_100_facture, statut, completed_at, cancelled_at, motif_annulation,
       frozen_at, created_at, updated_at, origine, legacy_id, legacy_data,
       legacy_numero
  FROM bons_commande
 ORDER BY id;

-- sqlite_sequence : la nouvelle valeur est >= à l'ancienne (INV-04, étape 7)
UPDATE sqlite_sequence
   SET seq = max(seq, COALESCE((SELECT seq FROM sqlite_sequence WHERE name = 'bons_commande'), 0))
 WHERE name = 'bons_commande_new';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'bons_commande_new', seq FROM sqlite_sequence
 WHERE name = 'bons_commande'
   AND NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = 'bons_commande_new');

DROP TABLE bons_commande;
ALTER TABLE bons_commande_new RENAME TO bons_commande;

CREATE INDEX idx_bons_commande_client_id    ON bons_commande (client_id);
CREATE INDEX idx_bons_commande_statut       ON bons_commande (statut);


-- =====================================================================
-- bc_ligne_garanties (§4.7) — reconstruction : ligne_id en RESTRICT (PT-5)
-- La clause ON DELETE ne se modifie pas en place. Aucun autre changement.
-- L'index de UNIQUE(ligne_id, garantie_type) couvre la FK.
-- =====================================================================
CREATE TABLE bc_ligne_garanties_new (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ligne_id      INTEGER NOT NULL REFERENCES bc_lignes (id) ON DELETE RESTRICT,
    garantie_type TEXT    NOT NULL CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale')),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (ligne_id, garantie_type),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

INSERT INTO bc_ligne_garanties_new (id, ligne_id, garantie_type, created_at)
SELECT id, ligne_id, garantie_type, created_at
  FROM bc_ligne_garanties
 ORDER BY id;

-- sqlite_sequence : la nouvelle valeur est >= à l'ancienne (INV-04, étape 7)
UPDATE sqlite_sequence
   SET seq = max(seq, COALESCE((SELECT seq FROM sqlite_sequence WHERE name = 'bc_ligne_garanties'), 0))
 WHERE name = 'bc_ligne_garanties_new';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'bc_ligne_garanties_new', seq FROM sqlite_sequence
 WHERE name = 'bc_ligne_garanties'
   AND NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = 'bc_ligne_garanties_new');

DROP TABLE bc_ligne_garanties;
ALTER TABLE bc_ligne_garanties_new RENAME TO bc_ligne_garanties;


-- =====================================================================
-- Triggers — ils ne font que garder : aucun ne modifie de donnée.
-- Les triggers BEFORE s'exécutent avant les CHECK de la ligne.
-- Un parent inexistant n'est jamais traité ici : c'est la FK qui refuse.
-- =====================================================================

-- ---------------------------------------------------------------------
-- bons_commande
-- ---------------------------------------------------------------------

-- TR-01 [INV-23] : recréé à l'identique de 004 (G-3).
CREATE TRIGGER tr_01_bons_commande_numero_immuable
BEFORE UPDATE OF numero, date_creation ON bons_commande
WHEN NEW.numero IS NOT OLD.numero OR NEW.date_creation IS NOT OLD.date_creation
BEGIN
    SELECT RAISE(ABORT, 'INV-23: bons_commande.numero et bons_commande.date_creation sont immuables');
END;

-- TR-12 [INV-36, INV-186, Q4] : contenu contractuel du BC non annulé, gelé ou non,
-- immuable dès sa création (remplace tr_12_bons_commande_modifiable et _gele de
-- 004/005a). Immuables : id, client_id, snapshots et leurs versions,
-- date_acceptation (devis d'origine), created_at, origine, legacy_*. Restent
-- modifiables : montant_contractuel_ht (rattachement d'un devis ; sa cohérence est
-- contrôlée par CK-13/CK-14), caches, date_debut, date_fin, annulation, frozen_at
-- (TR-14), updated_at. numero et date_creation : TR-01.
CREATE TRIGGER tr_12_bons_commande_contrat
BEFORE UPDATE ON bons_commande
WHEN OLD.statut <> 'annule'
 AND (NEW.id IS NOT OLD.id
        OR NEW.client_id IS NOT OLD.client_id
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_acceptation IS NOT OLD.date_acceptation
        OR NEW.created_at IS NOT OLD.created_at
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data
        OR NEW.legacy_numero IS NOT OLD.legacy_numero)
BEGIN
    SELECT RAISE(ABORT, 'INV-186: contenu contractuel du bon de commande immuable (seuls montant contractuel, caches, dates de debut et fin et annulation sont modifiables)');
END;

-- TR-12 [INV-173] : BC annulé — terminal : seul updated_at est modifiable
-- (005a sans devis_id, remise_*, acompte_* ; PT-16 reporté à la Facturation).
CREATE TRIGGER tr_12_bons_commande_annule
BEFORE UPDATE ON bons_commande
WHEN OLD.statut = 'annule'
 AND (NEW.id IS NOT OLD.id
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

-- TR-14 [INV-34] : recréé à l'identique de 004 (G-3, PT-8 conservateur).
CREATE TRIGGER tr_14_bons_commande_frozen_at
BEFORE UPDATE OF frozen_at ON bons_commande
WHEN OLD.frozen_at IS NOT NULL AND NEW.frozen_at IS NOT OLD.frozen_at
BEGIN
    SELECT RAISE(ABORT, 'INV-34: bons_commande.frozen_at est irreversible');
END;

-- TR-17 [INV-40] : état de naissance seul. « Devis accepté » et « client du devis »
-- sont vérifiés à l'INSERT du lien (TR-99) : le lien ne peut pas précéder le BC.
-- Aucune comparaison du BC avec ses devis (construite par le service, détectée par
-- CK-13). completed_at et cancelled_at NULL sont forcés par les CHECK
-- statut <-> completed_at / cancelled_at.
CREATE TRIGGER tr_17_bons_commande_insert
BEFORE INSERT ON bons_commande
BEGIN
    SELECT RAISE(ABORT, 'INV-40: etat de naissance d''un bon de commande (en_cours, non gele, caches a zero, sans date_100_facture ni motif d''annulation)')
     WHERE NEW.statut IS NOT 'en_cours'
        OR NEW.frozen_at IS NOT NULL
        OR NEW.date_100_facture IS NOT NULL
        OR NEW.motif_annulation IS NOT NULL
        OR NEW.montant_deja_facture_ht IS NOT '0.00'
        OR NEW.avancement IS NOT '0.00';
END;

-- TR-19 [INV-174] : recréé à l'identique de 004 (G-3). Avec recursive_triggers=ON,
-- il refuse aussi le DELETE implicite d'un INSERT OR REPLACE.
CREATE TRIGGER tr_19_bons_commande_no_delete
BEFORE DELETE ON bons_commande
BEGIN
    SELECT RAISE(ABORT, 'INV-174: un bon de commande ne se supprime jamais');
END;

-- ---------------------------------------------------------------------
-- bc_devis (TR-99, PT-6)
-- ---------------------------------------------------------------------

-- TR-99 [INV-40, INV-48, INV-187, INV-188] : à l'INSERT du lien, le devis est
-- 'accepte', du même client que le BC, et le BC n'est pas annulé. La condition
-- « aucun solde rédigé/validé » est une règle de service (CK-14), jamais un
-- trigger avant la tranche Facturation.
CREATE TRIGGER tr_99_bc_devis_insert
BEFORE INSERT ON bc_devis
BEGIN
    SELECT RAISE(ABORT, 'INV-40: seul un devis accepte se rattache a un bon de commande')
     WHERE EXISTS (SELECT 1 FROM devis d WHERE d.id = NEW.devis_id AND d.statut <> 'accepte');
    SELECT RAISE(ABORT, 'INV-48: le devis doit etre de meme client que le bon de commande')
     WHERE EXISTS (SELECT 1 FROM devis d, bons_commande b
                    WHERE d.id = NEW.devis_id AND b.id = NEW.bc_id AND d.client_id IS NOT b.client_id);
    SELECT RAISE(ABORT, 'INV-188: un bon de commande annule ne recoit aucun devis')
     WHERE EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = NEW.bc_id AND b.statut = 'annule');
END;

-- Une relation historique ne change jamais de cible (INV-184) ; avec
-- recursive_triggers=ON, le trigger DELETE refuse aussi le REPLACE.
CREATE TRIGGER tr_99_bc_devis_no_update
BEFORE UPDATE ON bc_devis
BEGIN
    SELECT RAISE(ABORT, 'INV-184: un rattachement devis / bon de commande ne se modifie jamais');
END;

CREATE TRIGGER tr_99_bc_devis_no_delete
BEFORE DELETE ON bc_devis
BEGIN
    SELECT RAISE(ABORT, 'INV-184: un rattachement devis / bon de commande ne se supprime jamais');
END;

-- ---------------------------------------------------------------------
-- devis
-- ---------------------------------------------------------------------

-- TR-18 [INV-175] : un devis rattaché à un BC ne quitte 'accepte' que si ce BC est
-- annulé (lecture par bc_devis). Aucune cascade BC -> devis (INV-188).
CREATE TRIGGER tr_18_devis_statut_avec_bc
BEFORE UPDATE OF statut ON devis
WHEN OLD.statut = 'accepte' AND NEW.statut IS NOT 'accepte'
 AND EXISTS (SELECT 1 FROM bc_devis l JOIN bons_commande b ON b.id = l.bc_id
              WHERE l.devis_id = OLD.id AND b.statut <> 'annule')
BEGIN
    SELECT RAISE(ABORT, 'INV-175: un devis ayant un bon de commande ne quitte accepte que si ce bon de commande est annule');
END;

-- ---------------------------------------------------------------------
-- bc_lignes et bc_ligne_garanties (TR-13) — INV-36, INV-173, INV-175, INV-186
-- INSERT : BC non annulé (le gel n'intervient plus, Q-B) et, pour une ligne, ligne
-- de devis appartenant à un devis rattaché à ce BC. UPDATE et DELETE : toujours
-- refusés (contenu contractuel immuable, Q4) ; le DELETE implicite d'un INSERT OR
-- REPLACE l'est aussi (recursive_triggers=ON).
-- ---------------------------------------------------------------------
CREATE TRIGGER tr_13_bc_lignes_insert
BEFORE INSERT ON bc_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-173: lignes de bon de commande non ajoutables (BC annule)')
     WHERE EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = NEW.bc_id AND b.statut = 'annule');
    SELECT RAISE(ABORT, 'INV-175: la ligne de devis doit appartenir a un devis rattache au bon de commande')
     WHERE EXISTS (SELECT 1 FROM bons_commande b, devis_lignes dl
                    WHERE b.id = NEW.bc_id AND dl.id = NEW.devis_ligne_id
                      AND NOT EXISTS (SELECT 1 FROM bc_devis l WHERE l.bc_id = b.id AND l.devis_id = dl.devis_id));
END;

CREATE TRIGGER tr_13_bc_lignes_update
BEFORE UPDATE ON bc_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-186: lignes de bon de commande non modifiables');
END;

CREATE TRIGGER tr_13_bc_lignes_delete
BEFORE DELETE ON bc_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-186: lignes de bon de commande non supprimables');
END;

CREATE TRIGGER tr_13_bc_ligne_garanties_insert
BEFORE INSERT ON bc_ligne_garanties
WHEN EXISTS (SELECT 1 FROM bc_lignes l JOIN bons_commande b ON b.id = l.bc_id
              WHERE l.id = NEW.ligne_id AND b.statut = 'annule')
BEGIN
    SELECT RAISE(ABORT, 'INV-173: garanties de lignes de bon de commande non ajoutables (BC annule)');
END;

CREATE TRIGGER tr_13_bc_ligne_garanties_update
BEFORE UPDATE ON bc_ligne_garanties
BEGIN
    SELECT RAISE(ABORT, 'INV-186: garanties de lignes de bon de commande non modifiables');
END;

CREATE TRIGGER tr_13_bc_ligne_garanties_delete
BEFORE DELETE ON bc_ligne_garanties
BEGIN
    SELECT RAISE(ABORT, 'INV-186: garanties de lignes de bon de commande non supprimables');
END;
