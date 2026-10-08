-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 006_facturation
-- Sixième tranche (rang 9, après la corrective 005c) : factures (acompte,
-- situation, solde, avoir) et lignes de facture.
--
-- Référence : modèle de données SQLite V3.13 — §2 (conventions), §2.3 (familles
-- décimales), §2.4 (BLOC-IMP, BLOC-SNAP), §4.8 (facturation), §6 (numérotation
-- ACP, FAC, AVO), §8 (TR-02, TR-16, TR-20 à TR-23, TR-99), §9 (index), §10
-- (import), §14 (CK-04, CK-05, CK-06, CK-13, CK-14) ; CADRAGE__006_facturation.md
-- (VR-01 à VR-13, DV-1 à DV-10, QO-3) et décisions de l'étape d'implémentation
-- (acomptes par devis, situations ligne par ligne, référence d'avancement,
-- ordinal de situation par BC).
-- Invariants : INV-04, INV-06, INV-10, INV-11 à INV-14, INV-20, INV-22 à INV-24,
-- INV-46, INV-47, INV-48, INV-52 à INV-62, INV-76, INV-131, INV-173, INV-179,
-- INV-185, INV-187 à INV-190. Décisions : D-23, D-38, D-39, D-48, D-54, D-55.
--
-- Précisions de DDL retenues pour cette tranche :
--   * Deux tables : factures (une seule table typée : la numérotation FAC est
--     partagée par la situation et le solde, UNIQUE(numero) couvre ce rempart) et
--     facture_lignes (photographie des éléments facturés). Aucune table de
--     neutralisation ni d'état : « totalement crédité » est un état DÉRIVÉ (une
--     facture est neutralisée si son total_ht est > 0.00 et que la somme de ses
--     avoirs est égale à son total_ht ; une facture à 0.00 ne l'est jamais).
--   * Une facture est définitive dès son INSERT : aucun UPDATE (tr_20), aucun
--     DELETE (tr_21, y compris le DELETE implicite d'un INSERT OR REPLACE avec
--     recursive_triggers=ON), pas de brouillon (INV-185), pas de statut, pas de
--     cancelled_at, pas de TVA / TTC, pas d'updated_at, pas de frozen_at.
--   * Acompte : devis_id obligatoire (CHECK) ; un seul acompte ACTIF par devis
--     (tr_22) ; nouvel acompte après neutralisation totale seulement avant tout
--     solde. Le plafond « acompte prévu du devis » (aucun / pourcentage /
--     montant) est une règle de service ; le SQL garde le total du devis et le
--     plafond contractuel du BC.
--   * Situation : source de vérité = lignes de facture de type 'avancement'
--     rattachées à une ligne de BC (avancement_precedent_pct, avancement_cumule_pct,
--     montant_ht). Aucune colonne situation_mode, situation_valeur_saisie,
--     montant_contractuel_ht ni avancement global : le pourcentage global est un
--     indicateur dérivé. factures porte seulement situation_numero (ordinal propre
--     au BC, 1 + MAX calculé par le service dans la transaction d'écriture,
--     BEGIN IMMEDIATE ; unicité par BC garantie par uq_factures_bc_situation_numero)
--     et montant_deja_facture_ht (facturation nette avant la situation, figée).
--   * Les calculs g, r, X, N, M, la référence d'avancement ρ calculée par le
--     service, l'exhaustivité des lignes d'avancement, M > 0, le plafond d'acompte
--     prévu, la confirmation d'un solde à 0.00 et date_100_facture sont des règles
--     de SERVICE. Les triggers de cette migration ne gardent que l'intégrité :
--     ils ne calculent aucune valeur et ne modifient aucune donnée.
--   * Lignes : le dépôt d'une ligne sur une facture déjà insérée ne peut pas être
--     refusé par SQLite (limite assumée : le service insère facture et lignes dans
--     la même transaction ; CK-04, CK-05 et CK-16 détectent le reste).
--   * Numérotation : mécanisme V6 existant (numerotation_sequences, high-water dans
--     machine.db, BEGIN IMMEDIATE) ; 006 n'insère aucune ligne de séquence et
--     n'écrit jamais derniere_date. Préfixes ACP-, AVO-, FAC- (format xxx-nnnnn-yy,
--     yy = année de date_emission) pour origine = 'v6' ; numéro libre mais non vide
--     pour origine = 'import' (D-24). Aucune borne d'année : 2001-2099 est une règle
--     de service (D-38).
--   * Import : le SQL ne connaît pas le V2. Une facture importée traverse les mêmes
--     triggers qu'une facture V6 (INV-131) ; aucune colonne legacy_numero.
--   * Les FK pointent vers la clé primaire id, toutes en RESTRICT, sans ON UPDATE.
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 9 (rang de cette migration dans la chaîne ordonnée,
--     D-55) posé par le runner dans la transaction de la migration, avant son
--     COMMIT (conventions techniques §5) ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--       recursive_triggers=ON (D-39).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA. Il ne reconstruit aucune
-- table existante : le protocole foreign_keys = OFF n'est pas requis.
--
-- Aucune ligne n'est insérée. Le numéro est attribué par le service dans la
-- transaction d'émission (séquences ACP / FAC / AVO de numerotation_sequences,
-- année de date_emission ; high-water dans machine.db ; PT-1).
--
-- Conventions : toutes les tables sont STRICT ; TS = TEXT
-- 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé par GLOB ; D = 'YYYY-MM-DD' (date
-- réelle : GLOB + date(x) IS x) ; D2 = montant à 2 décimales >= 0 ; D2S = D2 avec
-- signe '-' admis (jamais '-0.00') ; P2 = pourcentage 0.00 à 100.00 ; DL =
-- décimal à précision libre. Les GLOB sont explicites (pas de {n}). Les montants
-- sont comparés en centimes entiers : CAST(REPLACE(x, '.', '') AS INTEGER).
-- Les triggers sont BEFORE : ils s'exécutent avant les CHECK de la ligne.
-- =====================================================================


-- ---------------------------------------------------------------------
-- factures (§4.8) — BLOC-SNAP, BLOC-IMP
-- Une facture est un document émis : numérotée, datée, figée. Le type porte
-- les colonnes propres (devis_id : acompte ; situation_numero et
-- montant_deja_facture_ht : situation ; origine_facture_id et motif_avoir :
-- avoir), gardées par CHECK.
-- ---------------------------------------------------------------------
CREATE TABLE factures (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                      TEXT    NOT NULL UNIQUE,
    type                        TEXT    NOT NULL CHECK (type IN ('acompte', 'situation', 'solde', 'avoir')),
    bc_id                       INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    client_id                   INTEGER NOT NULL REFERENCES clients (id) ON DELETE RESTRICT,
    devis_id                    INTEGER REFERENCES devis (id) ON DELETE RESTRICT,
    -- BLOC-SNAP
    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot)),
    client_snapshot_version     INTEGER NOT NULL,
    entreprise_snapshot         TEXT    NOT NULL CHECK (json_valid(entreprise_snapshot)),
    entreprise_snapshot_version INTEGER NOT NULL,
    chantier_snapshot           TEXT    NOT NULL CHECK (json_valid(chantier_snapshot)),
    chantier_snapshot_version   INTEGER NOT NULL,
    objet                       TEXT,
    date_emission               TEXT    NOT NULL CHECK (date_emission GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_emission) IS date_emission),
    date_echeance               TEXT    CHECK (date_echeance IS NULL OR
                              (date_echeance GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_echeance) IS date_echeance)),
    total_ht                    TEXT    NOT NULL
                                CHECK (total_ht GLOB '[0-9]*.[0-9][0-9]'
                                       AND total_ht NOT GLOB '*[^0-9.]*'
                                       AND total_ht NOT GLOB '*.*.*'
                                       AND total_ht NOT GLOB '0[0-9]*'),
    situation_numero            INTEGER CHECK (situation_numero IS NULL OR situation_numero >= 1),
    montant_deja_facture_ht     TEXT    CHECK (montant_deja_facture_ht IS NULL OR
                                       (montant_deja_facture_ht GLOB '[0-9]*.[0-9][0-9]'
                                        AND montant_deja_facture_ht NOT GLOB '*[^0-9.]*'
                                        AND montant_deja_facture_ht NOT GLOB '*.*.*'
                                        AND montant_deja_facture_ht NOT GLOB '0[0-9]*')),
    origine_facture_id          INTEGER REFERENCES factures (id) ON DELETE RESTRICT,
    motif_avoir                 TEXT,
    created_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP
    origine                     TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id                   TEXT,
    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),

    -- numéro : V6 = préfixe du type + 5 chiffres + année de date_emission (INV-20) ; import = numéro libre non vide (D-24)
    CHECK (numero <> ''),
    CHECK (origine <> 'v6'
           OR (numero GLOB (CASE type WHEN 'acompte' THEN 'ACP-' WHEN 'avoir' THEN 'AVO-' ELSE 'FAC-' END)
                           || '[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
               AND substr(numero, 11, 2) = substr(date_emission, 3, 2))),
    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
    -- avoir : origine obligatoire, motif obligatoire, pas d'échéance ; autres types : échéance obligatoire, ni origine ni motif
    CHECK ((type = 'avoir') = (origine_facture_id IS NOT NULL)),
    CHECK (type <> 'avoir' OR (motif_avoir IS NOT NULL AND motif_avoir <> '' AND date_echeance IS NULL)),
    CHECK (type = 'avoir' OR (date_echeance IS NOT NULL AND motif_avoir IS NULL)),
    CHECK (date_echeance IS NULL OR date_echeance >= date_emission),
    -- acompte : devis d'origine obligatoire (DV-1) ; situation : ordinal et facturation nette avant, figés
    CHECK ((type = 'acompte') = (devis_id IS NOT NULL)),
    CHECK ((type = 'situation') = (situation_numero IS NOT NULL)),
    CHECK ((type = 'situation') = (montant_deja_facture_ht IS NOT NULL)),
    -- total : strictement positif sauf le solde, qui peut valoir 0.00 (INV-55, INV-58)
    CHECK (type = 'solde' OR total_ht <> '0.00'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- facture_lignes (§4.8) — photographie des éléments facturés
-- type_ligne : prestation, synthese, deduction (modèle §4.8) et avancement
-- (situation ligne par ligne : une ligne par ligne de BC applicable, avec
-- avancement_precedent_pct <= avancement_cumule_pct). Seule colonne métier
-- négative : montant_ht, et seulement pour une déduction (INV-62).
-- Aucun BLOC-IMP : les lignes importées sont imbriquées dans leur facture.
-- ---------------------------------------------------------------------
CREATE TABLE facture_lignes (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    facture_id               INTEGER NOT NULL REFERENCES factures (id) ON DELETE RESTRICT,
    ordre                    INTEGER NOT NULL CHECK (ordre >= 1),
    bc_ligne_id              INTEGER REFERENCES bc_lignes (id) ON DELETE RESTRICT,
    reference_prestation     TEXT,
    designation              TEXT    NOT NULL CHECK (designation <> ''),
    description              TEXT,
    quantite                 TEXT    NOT NULL
                             CHECK (quantite <> ''
                                    AND quantite NOT GLOB '*[^0-9.]*'
                                    AND quantite NOT GLOB '*.*.*'
                                    AND quantite NOT GLOB '.*'
                                    AND quantite NOT GLOB '*.'
                                    AND quantite NOT GLOB '*.*0'
                                    AND quantite NOT GLOB '0[0-9]*'
                                    AND quantite <> '0'),
    unite                    TEXT    NOT NULL CHECK (unite IN ('u', 'ens', 'ml', 'm2', 'm3')),
    prix_unitaire_ht         TEXT    NOT NULL
                             CHECK (prix_unitaire_ht <> ''
                                    AND prix_unitaire_ht NOT GLOB '*[^0-9.]*'
                                    AND prix_unitaire_ht NOT GLOB '*.*.*'
                                    AND prix_unitaire_ht NOT GLOB '.*'
                                    AND prix_unitaire_ht NOT GLOB '*.'
                                    AND prix_unitaire_ht NOT GLOB '*.*0'
                                    AND prix_unitaire_ht NOT GLOB '0[0-9]*'),
    remise_type              TEXT    NOT NULL CHECK (remise_type IN ('aucune', 'pourcentage', 'montant')),
    remise_valeur            TEXT,
    type_ligne               TEXT    NOT NULL CHECK (type_ligne IN ('prestation', 'synthese', 'deduction', 'avancement')),
    montant_ht               TEXT    NOT NULL
                             CHECK ((montant_ht GLOB '[0-9]*.[0-9][0-9]'
                                     AND montant_ht NOT GLOB '*[^0-9.]*'
                                     AND montant_ht NOT GLOB '*.*.*'
                                     AND montant_ht NOT GLOB '0[0-9]*')
                                 OR (montant_ht GLOB '-[0-9]*.[0-9][0-9]'
                                     AND substr(montant_ht, 2) NOT GLOB '*[^0-9.]*'
                                     AND montant_ht NOT GLOB '*.*.*'
                                     AND montant_ht NOT GLOB '-0[0-9]*'
                                     AND montant_ht <> '-0.00')),
    avancement_precedent_pct TEXT    CHECK (avancement_precedent_pct IS NULL OR
                                    (avancement_precedent_pct GLOB '[0-9]*.[0-9][0-9]'
                                     AND avancement_precedent_pct NOT GLOB '*[^0-9.]*'
                                     AND avancement_precedent_pct NOT GLOB '*.*.*'
                                     AND avancement_precedent_pct NOT GLOB '0[0-9]*'
                                     AND CAST(REPLACE(avancement_precedent_pct, '.', '') AS INTEGER) <= 10000)),
    avancement_cumule_pct    TEXT    CHECK (avancement_cumule_pct IS NULL OR
                                    (avancement_cumule_pct GLOB '[0-9]*.[0-9][0-9]'
                                     AND avancement_cumule_pct NOT GLOB '*[^0-9.]*'
                                     AND avancement_cumule_pct NOT GLOB '*.*.*'
                                     AND avancement_cumule_pct NOT GLOB '0[0-9]*'
                                     AND CAST(REPLACE(avancement_cumule_pct, '.', '') AS INTEGER) <= 10000)),
    created_at               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (facture_id, ordre),
    CHECK ((remise_type = 'aucune') = (remise_valeur IS NULL)),
    CHECK (remise_type <> 'pourcentage' OR (
        remise_valeur GLOB '[0-9]*.[0-9][0-9]'
        AND remise_valeur NOT GLOB '*[^0-9.]*'
        AND remise_valeur NOT GLOB '*.*.*'
        AND remise_valeur NOT GLOB '0[0-9]*'
        AND CAST(REPLACE(remise_valeur, '.', '') AS INTEGER) <= 10000)),
    CHECK (remise_type <> 'montant' OR (
        remise_valeur <> ''
        AND remise_valeur NOT GLOB '*[^0-9.]*'
        AND remise_valeur NOT GLOB '*.*.*'
        AND remise_valeur NOT GLOB '.*'
        AND remise_valeur NOT GLOB '*.'
        AND remise_valeur NOT GLOB '*.*0'
        AND remise_valeur NOT GLOB '0[0-9]*')),
    -- déduction <=> montant négatif ; une déduction porte la quantité 1 (INV-62)
    CHECK ((type_ligne = 'deduction') = (substr(montant_ht, 1, 1) = '-')),
    CHECK (type_ligne <> 'deduction' OR quantite = '1'),
    -- avancement : les deux pourcentages et la ligne de BC, ou aucun ; 0 <= précédent <= cumulé <= 100
    CHECK ((type_ligne = 'avancement') = (avancement_precedent_pct IS NOT NULL)),
    CHECK ((type_ligne = 'avancement') = (avancement_cumule_pct IS NOT NULL)),
    CHECK (type_ligne <> 'avancement' OR bc_ligne_id IS NOT NULL),
    CHECK (type_ligne <> 'avancement' OR
           CAST(REPLACE(avancement_precedent_pct, '.', '') AS INTEGER) <= CAST(REPLACE(avancement_cumule_pct, '.', '') AS INTEGER)),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK, plus la recherche et les deux unicités de la
-- tranche. numero et (facture_id, ordre) sont réalisés par leur UNIQUE.
--   * uq_factures_bc_situation_numero : un ordinal de situation n'apparaît
--     qu'une fois par BC (les NULL des autres types ne se comparent pas) ;
--   * uq_facture_lignes_avancement : une seule ligne d'avancement par facture
--     et par ligne de BC.
-- =====================================================================
CREATE INDEX idx_factures_bc_id               ON factures (bc_id);
CREATE INDEX idx_factures_client_id           ON factures (client_id);
CREATE INDEX idx_factures_devis_id            ON factures (devis_id);
CREATE INDEX idx_factures_origine_facture_id  ON factures (origine_facture_id);
CREATE INDEX idx_factures_type_date_echeance  ON factures (type, date_echeance);
CREATE INDEX idx_factures_date_emission       ON factures (date_emission);
CREATE UNIQUE INDEX uq_factures_bc_situation_numero ON factures (bc_id, situation_numero);
CREATE INDEX idx_facture_lignes_bc_ligne_id   ON facture_lignes (bc_ligne_id);
CREATE UNIQUE INDEX uq_facture_lignes_avancement ON facture_lignes (facture_id, bc_ligne_id) WHERE type_ligne = 'avancement';


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Les triggers BEFORE s'exécutent avant les CHECK de la ligne.
-- Un parent inexistant n'est jamais traité ici : c'est la FK qui refuse.
-- « Neutralisée » (état dérivé) : total_ht <> '0.00' et somme des avoirs de la
-- facture = total_ht. Seul un solde peut valoir 0.00 (CHECK) : pour un acompte et
-- une situation, « active » se réduit donc à somme des avoirs <> total_ht ; le
-- test <> '0.00' n'est écrit que dans le trigger du solde.
-- Facturation nette d'un BC = Σ acomptes + Σ situations + Σ soldes − Σ avoirs.
-- Contractuel d'un BC = Σ total_ht des devis rattachés (bc_devis). Tous les
-- calculs sont en centimes entiers.
-- =====================================================================

-- TR-20 [INV-53, INV-185] : une facture est immuable dès son INSERT ; aucune
-- colonne ne se modifie (numéro, client, snapshots, dates, montants, origine...),
-- même par une écriture sans changement de valeur.
CREATE TRIGGER tr_20_factures_no_update
BEFORE UPDATE ON factures
BEGIN
    SELECT RAISE(ABORT, 'INV-53: une facture est immuable');
END;

-- TR-21 [INV-06, INV-53] : une facture ne se supprime jamais ; avec
-- recursive_triggers=ON, ce trigger refuse aussi le DELETE implicite d'un
-- INSERT OR REPLACE (par id ou par numero).
CREATE TRIGGER tr_21_factures_no_delete
BEFORE DELETE ON factures
BEGIN
    SELECT RAISE(ABORT, 'INV-06: une facture ne se supprime jamais');
END;

-- TR-21 [INV-53] : les lignes d'une facture ne se modifient ni ne se suppriment
-- jamais (même garantie pour le DELETE implicite d'un INSERT OR REPLACE).
CREATE TRIGGER tr_21_facture_lignes_no_update
BEFORE UPDATE ON facture_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-53: les lignes d''une facture sont immuables');
END;

CREATE TRIGGER tr_21_facture_lignes_no_delete
BEFORE DELETE ON facture_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-53: les lignes d''une facture ne se suppriment jamais');
END;

-- TR-02 [INV-24] : chronologie continue des numéros ACP, FAC (situation et solde
-- partagés) et AVO : date_emission >= derniere_date de la séquence (type, année de
-- date_emission). Garde pure : le service écrit derniere_date dans la transaction
-- d'émission ; sans ligne de séquence (import, avant l'initialisation des
-- séquences) ou avec derniere_date NULL (comparaison NULL, jamais vraie), le
-- trigger ne contraint rien et n'en crée jamais.
CREATE TRIGGER tr_02_factures_chronologie
BEFORE INSERT ON factures
BEGIN
    SELECT RAISE(ABORT, 'INV-24: la date d''emission ne peut pas preceder la derniere date de la sequence de numerotation')
     WHERE EXISTS (SELECT 1 FROM numerotation_sequences s
                    WHERE s.type_objet = CASE NEW.type WHEN 'acompte' THEN 'ACP' WHEN 'avoir' THEN 'AVO' ELSE 'FAC' END
                      AND s.annee = CAST(substr(NEW.date_emission, 3, 2) AS INTEGER)
                      AND NEW.date_emission < s.derniere_date);
END;

-- TR-16 [INV-47, INV-48, INV-188] : le client de la facture est celui du BC ;
-- acompte, situation et solde exigent un BC 'en_cours' (ni annulé, ni terminé) ;
-- un avoir reste possible sur un BC terminé et sur un BC annulé (document existant).
-- Les instructions s'exécutent dans l'ordre : un BC annulé lève INV-188 avant INV-47.
CREATE TRIGGER tr_16_factures_bc
BEFORE INSERT ON factures
BEGIN
    SELECT RAISE(ABORT, 'INV-48: le client de la facture doit etre celui du bon de commande')
     WHERE EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = NEW.bc_id AND b.client_id IS NOT NEW.client_id);
    SELECT RAISE(ABORT, 'INV-188: un bon de commande annule ne recoit ni acompte, ni situation, ni solde')
     WHERE NEW.type IS NOT 'avoir'
       AND EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = NEW.bc_id AND b.statut = 'annule');
    SELECT RAISE(ABORT, 'INV-47: acompte, situation et solde exigent un bon de commande en cours')
     WHERE NEW.type IS NOT 'avoir'
       AND EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = NEW.bc_id AND b.statut <> 'en_cours');
END;

-- TR-22 [INV-52, INV-57, INV-58, INV-189] : acompte. Le devis d'origine est
-- rattaché au BC de la facture ; aucun solde n'existe sur le BC (même totalement
-- crédité) ; un seul acompte actif par devis ; le total ne dépasse ni le total du
-- devis ni, avec la facturation nette avant, le contractuel du BC (devis_id
-- n'est porté que par les acomptes : CHECK de factures). Le plafond de
-- l'acompte PRÉVU du devis est une règle de service.
CREATE TRIGGER tr_22_factures_acompte
BEFORE INSERT ON factures
WHEN NEW.type = 'acompte'
BEGIN
    SELECT RAISE(ABORT, 'INV-189: le devis de l''acompte doit etre rattache au bon de commande de la facture')
     WHERE NOT EXISTS (SELECT 1 FROM bc_devis l WHERE l.bc_id = NEW.bc_id AND l.devis_id = NEW.devis_id);
    SELECT RAISE(ABORT, 'INV-58: aucun acompte apres un solde')
     WHERE EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = NEW.bc_id AND s.type = 'solde');
    SELECT RAISE(ABORT, 'INV-52: un seul acompte actif par devis')
     WHERE EXISTS (SELECT 1 FROM factures a
                    WHERE a.devis_id = NEW.devis_id
                      AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                             FROM factures av WHERE av.origine_facture_id = a.id)
                          <> CAST(REPLACE(a.total_ht, '.', '') AS INTEGER));
    SELECT RAISE(ABORT, 'INV-57: un acompte ne depasse pas le total de son devis')
     WHERE CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER)
         > (SELECT CAST(REPLACE(d.total_ht, '.', '') AS INTEGER) FROM devis d WHERE d.id = NEW.devis_id);
    SELECT RAISE(ABORT, 'INV-57: facturation nette apres acompte superieure au contractuel du bon de commande')
     WHERE (SELECT COALESCE(SUM(CASE WHEN f.type = 'avoir' THEN -CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                                     ELSE CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) END), 0)
              FROM factures f WHERE f.bc_id = NEW.bc_id)
           + CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER)
         > (SELECT COALESCE(SUM(CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)), 0)
              FROM bc_devis l JOIN devis d ON d.id = l.devis_id WHERE l.bc_id = NEW.bc_id);
END;

-- TR-22 [INV-57, INV-58, INV-190] : situation. Aucun solde n'existe sur le BC
-- (même totalement crédité) ; montant_deja_facture_ht est exactement la
-- facturation nette du BC avant la situation ; la facturation nette après la
-- situation ne dépasse pas le contractuel (100 % atteignable). Le montant
-- (X - N, strictement positif) et les lignes sont une règle de service.
CREATE TRIGGER tr_22_factures_situation
BEFORE INSERT ON factures
WHEN NEW.type = 'situation'
BEGIN
    SELECT RAISE(ABORT, 'INV-58: aucune situation apres un solde')
     WHERE EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = NEW.bc_id AND s.type = 'solde');
    SELECT RAISE(ABORT, 'INV-57: montant_deja_facture_ht doit etre la facturation nette du bon de commande avant la situation')
     WHERE CAST(REPLACE(NEW.montant_deja_facture_ht, '.', '') AS INTEGER) IS NOT
           (SELECT COALESCE(SUM(CASE WHEN f.type = 'avoir' THEN -CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                                     ELSE CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) END), 0)
              FROM factures f WHERE f.bc_id = NEW.bc_id);
    SELECT RAISE(ABORT, 'INV-57: facturation nette apres situation superieure au contractuel du bon de commande')
     WHERE (SELECT COALESCE(SUM(CASE WHEN f.type = 'avoir' THEN -CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                                     ELSE CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) END), 0)
              FROM factures f WHERE f.bc_id = NEW.bc_id)
           + CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER)
         > (SELECT COALESCE(SUM(CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)), 0)
              FROM bc_devis l JOIN devis d ON d.id = l.devis_id WHERE l.bc_id = NEW.bc_id);
END;

-- TR-22 [INV-52, INV-58] : solde. Aucun solde actif sur le BC (un solde à 0.00
-- n'est jamais neutralisé) ; total_ht = contractuel du BC - facturation nette
-- avant, exactement (peut valoir 0.00 : la confirmation est une règle de
-- service). Après un solde totalement crédité, un nouveau solde est possible.
CREATE TRIGGER tr_22_factures_solde
BEFORE INSERT ON factures
WHEN NEW.type = 'solde'
BEGIN
    SELECT RAISE(ABORT, 'INV-52: un seul solde actif par bon de commande')
     WHERE EXISTS (SELECT 1 FROM factures s
                    WHERE s.bc_id = NEW.bc_id AND s.type = 'solde'
                      AND NOT (s.total_ht <> '0.00'
                               AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                                      FROM factures av WHERE av.origine_facture_id = s.id)
                                   = CAST(REPLACE(s.total_ht, '.', '') AS INTEGER)));
    SELECT RAISE(ABORT, 'INV-58: le solde est le contractuel du bon de commande moins la facturation nette avant le solde')
     WHERE CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER) IS NOT
           (SELECT COALESCE(SUM(CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)), 0)
              FROM bc_devis l JOIN devis d ON d.id = l.devis_id WHERE l.bc_id = NEW.bc_id)
         - (SELECT COALESCE(SUM(CASE WHEN f.type = 'avoir' THEN -CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                                     ELSE CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) END), 0)
              FROM factures f WHERE f.bc_id = NEW.bc_id);
END;

-- TR-23 [INV-76] : avoir. L'origine n'est pas un avoir, appartient au même BC, et
-- la somme des avoirs de l'origine (avec celui-ci) ne dépasse pas son total_ht ;
-- une origine à 0.00 n'accepte donc aucun avoir. Un avoir ne rouvre rien (aucune
-- règle de rattachement ici).
CREATE TRIGGER tr_23_factures_avoir
BEFORE INSERT ON factures
WHEN NEW.type = 'avoir'
BEGIN
    SELECT RAISE(ABORT, 'INV-76: l''origine d''un avoir n''est pas un avoir')
     WHERE EXISTS (SELECT 1 FROM factures o WHERE o.id = NEW.origine_facture_id AND o.type = 'avoir');
    SELECT RAISE(ABORT, 'INV-76: l''avoir et sa facture d''origine appartiennent au meme bon de commande')
     WHERE EXISTS (SELECT 1 FROM factures o WHERE o.id = NEW.origine_facture_id AND o.bc_id IS NOT NEW.bc_id);
    SELECT RAISE(ABORT, 'INV-76: la somme des avoirs ne depasse pas le total de la facture d''origine')
     WHERE CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER)
           + (SELECT COALESCE(SUM(CAST(REPLACE(a.total_ht, '.', '') AS INTEGER)), 0)
                FROM factures a WHERE a.origine_facture_id = NEW.origine_facture_id)
         > (SELECT CAST(REPLACE(o.total_ht, '.', '') AS INTEGER) FROM factures o WHERE o.id = NEW.origine_facture_id);
END;

-- TR-22 [INV-62, INV-190] : lignes de facture. (1) type de ligne admis selon le
-- type de la facture (acompte : synthese ; situation : avancement, deduction ;
-- solde : prestation, deduction ; avoir : prestation, synthese) ; (2) la ligne de
-- BC référencée appartient au BC de la facture ; (3) ligne d'avancement : le
-- pourcentage précédent est le cumulé de la même ligne de BC dans la situation de
-- référence ρ — la situation NON neutralisée d'ordinal le plus grand parmi celles
-- d'ordinal inférieur à celui de la situation (même BC) — ou 0.00 s'il n'y en a
-- pas ou si cette ligne n'y figure pas. Le trigger ne calcule aucun montant ;
-- l'exhaustivité des lignes (une par ligne de BC applicable) est une règle de
-- service contrôlée par CK-16.
CREATE TRIGGER tr_22_facture_lignes_insert
BEFORE INSERT ON facture_lignes
BEGIN
    SELECT RAISE(ABORT, 'INV-62: type de ligne incompatible avec le type de la facture')
     WHERE EXISTS (SELECT 1 FROM factures f
                    WHERE f.id = NEW.facture_id
                      AND NOT ((f.type = 'acompte'   AND NEW.type_ligne = 'synthese')
                            OR (f.type = 'situation' AND NEW.type_ligne IN ('avancement', 'deduction'))
                            OR (f.type = 'solde'     AND NEW.type_ligne IN ('prestation', 'deduction'))
                            OR (f.type = 'avoir'     AND NEW.type_ligne IN ('prestation', 'synthese'))));
    SELECT RAISE(ABORT, 'INV-62: la ligne de bon de commande doit appartenir au bon de commande de la facture')
     WHERE EXISTS (SELECT 1 FROM factures f, bc_lignes bl
                    WHERE f.id = NEW.facture_id AND bl.id = NEW.bc_ligne_id AND bl.bc_id IS NOT f.bc_id);
    SELECT RAISE(ABORT, 'INV-190: avancement precedent different de l''avancement cumule de la situation de reference')
     WHERE NEW.type_ligne = 'avancement'
       AND CAST(REPLACE(NEW.avancement_precedent_pct, '.', '') AS INTEGER) IS NOT
           COALESCE((SELECT CAST(REPLACE(rl.avancement_cumule_pct, '.', '') AS INTEGER)
                       FROM facture_lignes rl
                      WHERE rl.type_ligne = 'avancement'
                        AND rl.bc_ligne_id = NEW.bc_ligne_id
                        AND rl.facture_id =
                            (SELECT s.id FROM factures f, factures s
                              WHERE f.id = NEW.facture_id
                                AND s.bc_id = f.bc_id
                                AND s.situation_numero < f.situation_numero
                                AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                                       FROM factures av WHERE av.origine_facture_id = s.id)
                                    <> CAST(REPLACE(s.total_ht, '.', '') AS INTEGER)
                              ORDER BY s.situation_numero DESC LIMIT 1)), 0);
END;

-- TR-99 [INV-187] : aucun devis ne se rattache à un BC dès qu'un solde existe,
-- même totalement crédité (005b laissait cette condition au service et à CK-14
-- « avant la tranche Facturation »).
CREATE TRIGGER tr_99_bc_devis_apres_solde
BEFORE INSERT ON bc_devis
BEGIN
    SELECT RAISE(ABORT, 'INV-187: aucun devis ne se rattache a un bon de commande ayant un solde, meme totalement credite')
     WHERE EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = NEW.bc_id AND s.type = 'solde');
END;
