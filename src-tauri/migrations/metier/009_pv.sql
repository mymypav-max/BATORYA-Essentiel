-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 009_pv
-- Neuvième tranche (rang 12, après 008_garanties) : procès-verbaux de
-- réception (PV) et leurs levées de réserves.
--
-- Référence : modèle de données SQLite V3.13 — §2 (conventions), §2.4
-- (BLOC-IMP, BLOC-SNAP), §2.5 (énumérations fermées), §4.11 (PV), §6
-- (numérotation PVR), §8 (TR-40, TR-41), §9 (index), §10 (import) ;
-- CADRAGE__009_pv.md (validé, après audit contradictoire).
-- Invariants : INV-05, INV-06, INV-10, INV-20, INV-26, INV-27, INV-30, INV-32,
-- INV-95, INV-96, INV-97, INV-131, INV-136, INV-174, INV-177, INV-179.
-- Décisions : D-24, D-34, D-38, D-39, D-44, D-55.
--
-- Précisions de DDL retenues pour cette tranche :
--   * Une seule table : pv. Un PV est un objet documentaire FACULTATIF (INV-95) :
--     il ne conditionne ni le solde, ni l'état Terminé, ni les garanties, et n'en
--     modifie aucune. Plusieurs PV initiaux par BC ne sont pas interdits. Il est
--     immuable dès son INSERT (TR-40 : aucun UPDATE, aucun DELETE) ; il n'a ni
--     statut, ni cancelled_at, ni motif_annulation, ni updated_at, ni
--     legacy_numero (réservé aux clients et aux BC), ni table fille.
--   * Une levée de réserves n'est pas une modification du PV initial : c'est un
--     NOUVEAU PV (type 'levee_reserves') qui référence, par origine_pv_id, un PV
--     'reception_avec_reserves' du MÊME BC ; une levée ne porte jamais sur une
--     levée. Son suffixe vaut max + 1 pour cette origine (1 à 99) et son numéro est
--     celui de l'origine suivi de '-' et du suffixe sur deux chiffres (TR-41).
--     Elle n'a ni séquence de numérotation ni année propre (modèle §6).
--   * Le seul rempart contre la réutilisation d'un suffixe est la non-suppression
--     d'une levée (aucune séquence) : tr_40_pv_no_delete, qui refuse aussi le
--     DELETE implicite d'un INSERT OR REPLACE lorsque recursive_triggers=ON (D-39).
--   * Numéro : UNIQUE NOT NULL non vide pour toute origine. Pour un PV INITIAL
--     origine = 'v6' : 'PVR-' + 5 chiffres + '-' + année sur 2 chiffres égale à
--     celle de date_reception (INV-20, modèle §6, §10.4). Pour origine = 'import'
--     le format n'est pas contrôlé (INV-27, INV-131, D-24). AUCUN contrôle de
--     format n'est ajouté pour la levée : son traitement n'est pas spécifié
--     (cadrage PR-3, Z-8) ; son numéro est imposé par la garde G4 du trigger
--     tr_41_pv_insert, sans exemption d'origine (INV-131).
--   * Import : aucun PV n'est importé depuis la V2 (information confirmée par Rémy,
--     hors sources). Cette décision ne supprime pas le mécanisme générique du
--     modèle : les colonnes origine, legacy_id et legacy_data (BLOC-IMP, §2.4)
--     existent et les mêmes gardes s'appliquent à toute origine. Aucun parcours
--     d'import V2 de PV et aucune exception de numérotation d'un PV historique
--     ne sont construits ici.
--   * Aucune borne d'année en SQL : 2001-2099 est une règle de SERVICE (INV-177,
--     D-38). La réservation du numéro PVR (compteur par année de date_reception)
--     est faite par le service dans une transaction propre, committée avant
--     l'objet (PT-1, D-54) ; ce fichier n'écrit pas dans numerotation_sequences.
--     Aucune règle sur le statut du BC, la cohérence des dates ou la non-vacuité
--     de reserves n'est posée (cadrage QO-1, QO-3, QO-4 : non spécifiées).
--   * L'index de UNIQUE (origine_pv_id, suffixe) couvre la FK origine_pv_id :
--     aucun index pv (origine_pv_id) supplémentaire (règle de tête, §9 ; PR-1).
--   * Les FK pointent vers la clé primaire id, en RESTRICT, sans ON UPDATE.
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 12 (rang de cette migration dans la chaîne ordonnée,
--     D-55) posé par le runner dans la transaction de la migration, avant son
--     COMMIT (conventions techniques §5) ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--       recursive_triggers=ON (D-39).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA. Il ne reconstruit aucune
-- table existante : le protocole foreign_keys = OFF n'est pas requis.
--
-- Aucune ligne n'est insérée. Aucune table existante n'est lue ni modifiée.
--
-- Conventions : table STRICT ; TS = TEXT 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé
-- par GLOB ; D = 'YYYY-MM-DD' (date réelle : GLOB + date(x) IS x, aucune borne
-- d'année en SQL, INV-177).
-- Les triggers sont BEFORE : ils s'exécutent avant les CHECK de la ligne.
-- =====================================================================


-- ---------------------------------------------------------------------
-- pv (§4.11)
-- ---------------------------------------------------------------------
CREATE TABLE pv (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                      TEXT    NOT NULL UNIQUE,
    bc_id                       INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    type                        TEXT    NOT NULL CHECK (type IN ('reception_sans_reserves', 'reception_avec_reserves', 'levee_reserves')),
    date_reception              TEXT    NOT NULL
                                CHECK (date_reception GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_reception) IS date_reception),
    -- BLOC-SNAP : json_valid lit le TEXT comme une chaîne C (arrêt au premier octet NUL, queue ignorée) ; un octet NUL brut est donc refusé par
    -- instr(CAST(x AS BLOB), x'00') ; l'échappement JSON \u0000 (six caractères, sans octet NUL) reste valide
    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot) AND instr(CAST(client_snapshot AS BLOB), x'00') = 0),
    client_snapshot_version     INTEGER NOT NULL,
    entreprise_snapshot         TEXT    NOT NULL CHECK (json_valid(entreprise_snapshot) AND instr(CAST(entreprise_snapshot AS BLOB), x'00') = 0),
    entreprise_snapshot_version INTEGER NOT NULL,
    chantier_snapshot           TEXT    NOT NULL CHECK (json_valid(chantier_snapshot) AND instr(CAST(chantier_snapshot AS BLOB), x'00') = 0),
    chantier_snapshot_version   INTEGER NOT NULL,
    observations                TEXT,
    reserves                    TEXT,
    origine_pv_id               INTEGER REFERENCES pv (id) ON DELETE RESTRICT,
    suffixe                     INTEGER,
    created_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP
    origine                     TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id                   TEXT,
    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR (json_valid(legacy_data) AND instr(CAST(legacy_data AS BLOB), x'00') = 0)),

    UNIQUE (origine_pv_id, suffixe),
    CHECK (numero <> ''),
    -- levée de réserves <=> origine renseignée <=> suffixe renseigné ; suffixe de 1 à 99 (INV-97)
    CHECK ((type = 'levee_reserves') = (origine_pv_id IS NOT NULL)),
    CHECK ((origine_pv_id IS NOT NULL) = (suffixe IS NOT NULL)),
    CHECK (suffixe IS NULL OR suffixe BETWEEN 1 AND 99),
    -- réserves renseignées <=> réception avec réserves (INV-97)
    CHECK ((reserves IS NOT NULL) = (type = 'reception_avec_reserves')),
    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
    -- numéro d'un PV INITIAL V6 : PVR + 5 chiffres + année de date_reception (INV-20) ;
    -- import : numéro libre non vide ; levée : aucun contrôle de format ajouté (PR-3), son numéro est imposé par G4.
    -- GLOB, substr et length() de TEXT s'arrêtent au premier octet NUL : la longueur est donc contrôlée en octets
    -- (CAST ... AS BLOB) pour qu'aucune queue ne suive le format (numéro V6 : 12 octets ; created_at : 24 octets).
    CHECK (origine <> 'v6' OR type = 'levee_reserves'
           OR (numero GLOB 'PVR-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
               AND substr(numero, 11, 2) = substr(date_reception, 3, 2)
               AND length(CAST(numero AS BLOB)) = 12)),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'
        AND length(CAST(created_at AS BLOB)) = 24)
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK. origine_pv_id est couvert par l'index
-- automatique de UNIQUE (origine_pv_id, suffixe) : aucun index dédié.
-- =====================================================================
CREATE INDEX idx_pv_bc_id ON pv (bc_id);


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Aucune exemption d'origine (INV-131). Aucune lecture de bons_commande.statut,
-- factures, reglements ou garanties : un PV est indépendant de l'état et de la
-- facturation du BC (INV-95).
-- =====================================================================

-- TR-40 [INV-96, INV-32] : un PV est immuable dès son INSERT, même par une
-- écriture sans effet. Refuse aussi UPDATE OR REPLACE / OR IGNORE et la branche
-- ON CONFLICT DO UPDATE d'un UPSERT (qui déclenche BEFORE UPDATE).
CREATE TRIGGER tr_40_pv_no_update
BEFORE UPDATE ON pv
BEGIN
    SELECT RAISE(ABORT, 'INV-96: un PV est immuable');
END;

-- TR-40 [INV-96, INV-06] : un PV ne se supprime jamais. Avec
-- recursive_triggers=ON, ce trigger refuse aussi le DELETE implicite d'un
-- INSERT OR REPLACE.
CREATE TRIGGER tr_40_pv_no_delete
BEFORE DELETE ON pv
BEGIN
    SELECT RAISE(ABORT, 'INV-06: un PV ne se supprime jamais');
END;

-- TR-41 [INV-96, INV-26] : gardes d'insertion d'une levée de réserves (G1 à G4).
-- Un parent inexistant est refusé par G1 avant la FK. Le plafond de 99 levées est
-- porté par le CHECK du suffixe (G3 accepte max + 1 = 100, le CHECK le refuse).
CREATE TRIGGER tr_41_pv_insert
BEFORE INSERT ON pv
WHEN NEW.type = 'levee_reserves'
BEGIN
    -- G1 : l'origine existe et est un PV avec réserves (donc jamais une levée de levée).
    SELECT RAISE(ABORT, 'INV-96: l''origine d''une levee doit etre un PV recu avec reserves')
     WHERE NOT EXISTS (SELECT 1 FROM pv o WHERE o.id = NEW.origine_pv_id AND o.type = 'reception_avec_reserves');
    -- G2 : l'origine appartient au même BC.
    SELECT RAISE(ABORT, 'INV-96: la levee doit appartenir au meme bon de commande que son origine')
     WHERE NOT EXISTS (SELECT 1 FROM pv o WHERE o.id = NEW.origine_pv_id AND o.bc_id IS NEW.bc_id);
    -- G3 : suffixe = max + 1 pour cette origine (1 si aucune levée).
    SELECT RAISE(ABORT, 'INV-26: le suffixe d''une levee est le suffixe maximal de son origine plus un')
     WHERE NEW.suffixe IS NOT (SELECT COALESCE(MAX(p.suffixe), 0) + 1 FROM pv p WHERE p.origine_pv_id = NEW.origine_pv_id);
    -- G4 : numéro = numéro de l'origine + '-' + suffixe sur 2 chiffres.
    SELECT RAISE(ABORT, 'INV-26: le numero d''une levee est celui de son origine suivi du suffixe')
     WHERE NOT EXISTS (SELECT 1 FROM pv o WHERE o.id = NEW.origine_pv_id AND NEW.numero = o.numero || '-' || printf('%02d', NEW.suffixe));
END;
