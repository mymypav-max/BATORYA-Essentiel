-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 008_garanties
-- Huitième tranche (rang 11, après 007_reglements) : garanties de BC
-- (parfait achèvement, biennale, décennale) déclenchées par le premier solde.
--
-- Référence : modèle de données SQLite V3.13 — §2 (conventions), §2.5
-- (énumérations fermées), §4.10 (garanties), §8 (TR-50), §9 (index), §10 (import) ;
-- CADRAGE__008_garanties.md (validé : QO-1 oui, QO-2 oui, QO-3 non, dates extrêmes,
-- post-condition renforcée du service §4.1).
-- Invariants : INV-05, INV-06, INV-10, INV-85 à INV-90, INV-95, INV-131, INV-134,
-- INV-174, INV-177, INV-188. Décisions : D-16, D-23, D-34, D-39, D-44, D-55.
--
-- Précisions de DDL retenues pour cette tranche :
--   * Une seule table : garanties. Une garantie naît à l'émission du PREMIER solde
--     d'un BC, une par couple (ligne de BC, type de garantie de la ligne) ; elle
--     est créée par le SERVICE (INSERT OR IGNORE, idempotent, première date
--     conservée), jamais par un trigger (INV-86). Elle n'a ni statut, ni
--     updated_at, ni numéro, ni BLOC-IMP : aucune garantie n'est importée
--     (INV-134, D-23), un BC importé n'en porte aucune.
--   * date_declenchement = date d'émission du solde (INV-87) ; date_fin_suivi =
--     date_declenchement + 1 an (parfait achèvement), + 2 ans (biennale) ou
--     + 10 ans (décennale), le 29 février devenant le 28 février (INV-88). Les
--     dates sont de la famille D (année sur 4 chiffres) : une date de fin
--     d'année > 9999 n'est pas représentable et est refusée par CHECK ; le SQL
--     n'ajoute AUCUNE borne d'année métier (INV-177). Le service calcule les
--     dates avant toute écriture et contrôle ce qui a été créé (cadrage §3.6 et
--     §4.1) : INSERT OR IGNORE ignore aussi les violations de CHECK / NOT NULL.
--   * Une garantie ne se modifie ni ne se supprime jamais (INV-87, TR-50) :
--     un avoir (même total) sur le solde, un règlement, un PV ou sa levée ne
--     l'altèrent pas. Aucun trigger n'est donc posé sur factures, reglements ou
--     bc_ligne_garanties ; les triggers de cette tranche ne lisent ni reglements,
--     ni bons_commande.statut, ni les avoirs (une garantie est indépendante du
--     paiement et de l'état du BC).
--   * « Premier solde » : règle de SERVICE (QO-3 : aucune garde SQL, pour que le
--     rejeu INSERT OR IGNORE au solde suivant reste idempotent et sans erreur).
--   * Les FK pointent vers la clé primaire id, en RESTRICT, sans ON UPDATE.
--   * L'index de UNIQUE (bc_ligne_id, garantie_type) couvre la FK bc_ligne_id :
--     aucun index garanties (bc_ligne_id) supplémentaire (règle de tête, §9).
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 11 (rang de cette migration dans la chaîne ordonnée,
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
-- garanties (§4.10) — pas de BLOC-IMP
-- ---------------------------------------------------------------------
CREATE TABLE garanties (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    bc_id                    INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    bc_ligne_id              INTEGER NOT NULL REFERENCES bc_lignes (id) ON DELETE RESTRICT,
    garantie_type            TEXT    NOT NULL CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale')),
    date_declenchement       TEXT    NOT NULL
                             CHECK (date_declenchement GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_declenchement) IS date_declenchement),
    date_fin_suivi           TEXT    NOT NULL
                             CHECK (date_fin_suivi GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_fin_suivi) IS date_fin_suivi),
    facture_declenchement_id INTEGER NOT NULL REFERENCES factures (id) ON DELETE RESTRICT,
    created_at               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (bc_ligne_id, garantie_type),
    CHECK (date_fin_suivi > date_declenchement),
    -- QO-2 (G5) : durée exacte par type (+1 / +2 / +10 ans), le 29 février devenant
    -- le 28 février. Pour une origine bissextile Y, les années Y+1, Y+2 et Y+10 ne
    -- sont jamais bissextiles : « 29/02 -> 28/02 » (INV-88) est donc équivalent à
    -- « 28/02 si l'année cible n'est pas bissextile » (modèle §4.10). Écriture
    -- purement textuelle et entière : date(x, '+N year') donnerait le 1er mars.
    CHECK (date_fin_suivi = printf('%04d', CAST(substr(date_declenchement, 1, 4) AS INTEGER)
                                         + CASE garantie_type WHEN 'parfait_achevement' THEN 1 WHEN 'biennale' THEN 2 ELSE 10 END)
                            || CASE WHEN substr(date_declenchement, 6, 5) = '02-29' THEN '-02-28' ELSE substr(date_declenchement, 5) END),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK, plus la recherche des échéances de suivi.
-- bc_ligne_id est couvert par l'index automatique de UNIQUE (bc_ligne_id,
-- garantie_type) : aucun index dédié.
-- =====================================================================
CREATE INDEX idx_garanties_bc_id                    ON garanties (bc_id);
CREATE INDEX idx_garanties_facture_declenchement_id ON garanties (facture_declenchement_id);
CREATE INDEX idx_garanties_date_fin_suivi           ON garanties (date_fin_suivi);


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Un parent inexistant n'est jamais traité en tant que tel : c'est la FK qui
-- refuse. Aucune exemption d'origine (INV-131).
-- =====================================================================

-- TR-50 [INV-87] : une garantie ne se modifie jamais, même par une écriture sans
-- effet. Refuse aussi UPDATE OR REPLACE / OR IGNORE et la branche
-- ON CONFLICT DO UPDATE d'un UPSERT (qui déclenche BEFORE UPDATE).
CREATE TRIGGER tr_50_garanties_update
BEFORE UPDATE ON garanties
BEGIN
    SELECT RAISE(ABORT, 'INV-87: une garantie ne se modifie jamais');
END;

-- TR-50 [INV-87, INV-06] : une garantie ne se supprime jamais. Avec
-- recursive_triggers=ON, ce trigger refuse aussi le DELETE implicite d'un
-- INSERT OR REPLACE.
CREATE TRIGGER tr_50_garanties_no_delete
BEFORE DELETE ON garanties
BEGIN
    SELECT RAISE(ABORT, 'INV-87: une garantie ne se supprime jamais');
END;

-- TR-51 [INV-85, INV-86, INV-87, INV-90, INV-134] : gardes d'insertion (G1 à G4).
-- La règle « premier solde » n'est PAS gardée ici (QO-3 : NON).
CREATE TRIGGER tr_51_garanties_insert
BEFORE INSERT ON garanties
BEGIN
    -- G1 : la ligne existe et appartient au BC de la garantie.
    SELECT RAISE(ABORT, 'INV-90: la ligne de BC doit appartenir au bon de commande de la garantie')
     WHERE NOT EXISTS (SELECT 1 FROM bc_lignes l WHERE l.id = NEW.bc_ligne_id AND l.bc_id = NEW.bc_id);
    -- G2 : la facture de déclenchement est un solde du même BC (« actif » est une
    -- notion dérivée : un premier solde totalement crédité reste valide).
    SELECT RAISE(ABORT, 'INV-85: la facture de declenchement doit etre un solde du bon de commande')
     WHERE NOT EXISTS (SELECT 1 FROM factures f WHERE f.id = NEW.facture_declenchement_id AND f.bc_id = NEW.bc_id AND f.type = 'solde');
    -- G3 (QO-1) : le couple (ligne, type) existe dans bc_ligne_garanties ; rend
    -- impossible toute garantie sur un BC importé (aucune garantie de ligne).
    SELECT RAISE(ABORT, 'INV-86: la garantie doit exister parmi les garanties de la ligne de BC')
     WHERE NOT EXISTS (SELECT 1 FROM bc_ligne_garanties g WHERE g.ligne_id = NEW.bc_ligne_id AND g.garantie_type IS NEW.garantie_type);
    -- G4 (QO-1) : la date de déclenchement est la date d'émission de la facture.
    SELECT RAISE(ABORT, 'INV-87: la date de declenchement est la date d''emission du solde')
     WHERE NOT EXISTS (SELECT 1 FROM factures f WHERE f.id = NEW.facture_declenchement_id AND f.date_emission IS NEW.date_declenchement);
END;
