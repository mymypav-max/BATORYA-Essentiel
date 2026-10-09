-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 007_reglements
-- Septième tranche (rang 10, après 006_facturation) : règlements
-- (encaissements et remboursements).
--
-- Référence : modèle de données SQLite V3.13 — §2 (conventions), §2.3 (familles
-- décimales), §2.4 (BLOC-IMP), §2.5 (énumérations fermées), §3.3 (paiement),
-- §3.4 (états dérivés), §3.5 (fin du BC), §4.9 (règlements), §8 (TR-30 à TR-33),
-- §9 (index), §10 (import) ; CADRAGE__007_reglements.md (validé).
-- Invariants : INV-04, INV-05, INV-10, INV-11 à INV-14, INV-70 à INV-75,
-- INV-79, INV-131, INV-184, INV-188. Décisions : D-34, D-39, D-48, D-55.
--
-- Précisions de DDL retenues pour cette tranche :
--   * Une seule table : reglements. Un règlement porte sur UNE facture
--     (facture_id obligatoire, D-48) ; une facture peut en recevoir plusieurs.
--     Un remboursement porte sur un AVOIR (facture_id = l'avoir) : il n'existe
--     pas de colonne avoir_id (INV-71). Aucun numéro : un règlement est désigné
--     par son id ; aucune séquence n'est créée ni modifiée.
--   * type : encaissement | remboursement ; mode : especes | cheque | virement |
--     carte | autre (énumérations fermées, §2.5). mode est obligatoire ;
--     reference et note sont libres (aucun CHECK de contenu, aucune chronologie
--     sur date_evenement : aucune source ne les prévoit).
--   * montant : famille D2 stricte, strictement positif ('0.00' refusé).
--     Tous les calculs sont faits en centimes entiers (CAST(REPLACE(x, '.', '')
--     AS INTEGER)), jamais en flottant.
--   * Annulation : cancelled_at + motif_annulation, posés ensemble, UNE seule
--     fois, irréversibles. Un règlement peut naître déjà annulé (import d'un état
--     historique) : il ne consomme alors aucune capacité, donc tr_31 et tr_33 ne
--     s'appliquent qu'aux règlements ACTIFS ; tr_30 s'applique toujours.
--   * « Actif » : un règlement est actif tant que cancelled_at IS NULL. Aucune
--     facture ne s'annule et aucun avoir ne s'annule (E-14) : la cible d'un
--     règlement est toujours « active » ; une facture entièrement créditée a un
--     reste dû nul (INV-72), donc tr_31 y refuse tout encaissement.
--   * Les formules du modèle §3.3 sont écrites telles quelles dans les triggers :
--       absorbe  = min(somme des avoirs, max(0, M - encaissements actifs))
--       reste_du = max(0, M - encaissements actifs - absorbe)
--       credit   = somme des avoirs - absorbe - remboursements actifs
--     (crédit calculé PAR FACTURE D'ORIGINE ; un remboursement peut viser
--     n'importe quel avoir de cette origine). Comme un encaissement est limité au
--     reste dû, la somme des encaissements actifs ne dépasse jamais M et le
--     crédit n'est jamais négatif : seule l'annulation d'un encaissement peut le
--     faire baisser, d'où tr_33.
--   * Les triggers ne font que garder : ils ne calculent aucun cache, n'écrivent
--     aucune donnée et ne lisent ni n'écrivent bons_commande. L'état du BC
--     (termine, en_cours, caches, completed_at), l'historique et les états de
--     paiement sont des règles de SERVICE (INV-46, INV-164, INV-60). Un règlement
--     ne réautorise donc jamais un devis, un acompte, une situation ou un solde :
--     ces fermetures sont celles de 006 (tr_16, tr_22, tr_99).
--   * Import : le SQL ne connaît pas le V2. Un règlement importé traverse les
--     mêmes triggers qu'un règlement V6 (INV-131) ; aucune exemption d'origine.
--   * Les FK pointent vers la clé primaire id, en RESTRICT, sans ON UPDATE.
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 10 (rang de cette migration dans la chaîne ordonnée,
--     D-55) posé par le runner dans la transaction de la migration, avant son
--     COMMIT (conventions techniques §5) ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--       recursive_triggers=ON (D-39).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA. Il ne reconstruit aucune
-- table existante : le protocole foreign_keys = OFF n'est pas requis.
--
-- Aucune ligne n'est insérée.
--
-- Conventions : table STRICT ; TS = TEXT 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé
-- par GLOB ; D = 'YYYY-MM-DD' (date réelle : GLOB + date(x) IS x, aucune borne
-- d'année en SQL, INV-177) ; D2 = montant à 2 décimales >= 0 (forme canonique).
-- Les triggers sont BEFORE : ils s'exécutent avant les CHECK de la ligne.
-- =====================================================================


-- ---------------------------------------------------------------------
-- reglements (§4.9) — BLOC-IMP
-- ---------------------------------------------------------------------
CREATE TABLE reglements (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    facture_id       INTEGER NOT NULL REFERENCES factures (id) ON DELETE RESTRICT,
    type             TEXT    NOT NULL CHECK (type IN ('encaissement', 'remboursement')),
    date_evenement   TEXT    NOT NULL
                     CHECK (date_evenement GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_evenement) IS date_evenement),
    montant          TEXT    NOT NULL
                     CHECK (montant GLOB '[0-9]*.[0-9][0-9]'
                            AND montant NOT GLOB '*[^0-9.]*'
                            AND montant NOT GLOB '*.*.*'
                            AND montant NOT GLOB '0[0-9]*'
                            AND montant <> '0.00'),
    mode             TEXT    NOT NULL CHECK (mode IN ('especes', 'cheque', 'virement', 'carte', 'autre')),
    reference        TEXT,
    note             TEXT,
    cancelled_at     TEXT    CHECK (cancelled_at IS NULL OR cancelled_at GLOB
                             '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    motif_annulation TEXT    CHECK (motif_annulation IS NULL OR motif_annulation <> ''),
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP
    origine          TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id        TEXT,
    legacy_data      TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),

    -- annulation : date et motif ensemble, ou aucun des deux
    CHECK ((cancelled_at IS NULL) = (motif_annulation IS NULL)),
    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK, plus la recherche par date et par type.
-- Aucun index unique : deux paiements identiques sont légitimes.
-- =====================================================================
CREATE INDEX idx_reglements_facture_id     ON reglements (facture_id);
CREATE INDEX idx_reglements_date_evenement ON reglements (date_evenement);
CREATE INDEX idx_reglements_type           ON reglements (type);


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Un parent inexistant n'est jamais traité ici : c'est la FK qui refuse.
-- Tous les calculs sont en centimes entiers. Pour une facture F hors avoir
-- de total M : encaissements actifs = somme des règlements 'encaissement' non
-- annulés de F ; avoirs = factures dont origine_facture_id = F ; remboursements
-- actifs de F = règlements 'remboursement' non annulés portant sur l'un de ses
-- avoirs.
-- =====================================================================

-- TR-30 [INV-71] : un encaissement porte sur une facture hors avoir ; un
-- remboursement porte sur un avoir. Posé à l'INSERT seulement : facture_id et
-- type sont immuables (tr_32), donc la cohérence ne change plus jamais.
CREATE TRIGGER tr_30_reglements_cible
BEFORE INSERT ON reglements
BEGIN
    SELECT RAISE(ABORT, 'INV-71: un encaissement porte sur une facture hors avoir')
     WHERE NEW.type = 'encaissement'
       AND EXISTS (SELECT 1 FROM factures f WHERE f.id = NEW.facture_id AND f.type = 'avoir');
    SELECT RAISE(ABORT, 'INV-71: un remboursement porte sur un avoir')
     WHERE NEW.type = 'remboursement'
       AND EXISTS (SELECT 1 FROM factures f WHERE f.id = NEW.facture_id AND f.type <> 'avoir');
END;

-- TR-31 [INV-72] : un encaissement actif ne dépasse pas le reste dû de la
-- facture : montant <= max(0, M - encaissements actifs - absorbe), absorbe =
-- min(somme des avoirs, max(0, M - encaissements actifs)). Le montant étant
-- strictement positif, la forme équivalente montant > M - encaissements actifs -
-- somme des avoirs refuse tout encaissement sur une facture à 0.00 ou
-- entièrement créditée. Le type de la cible est gardé par tr_30 : ce trigger ne
-- s'applique qu'à une cible hors avoir, pour que chaque refus ait une seule cause.
CREATE TRIGGER tr_31_reglements_encaissement
BEFORE INSERT ON reglements
WHEN NEW.type = 'encaissement' AND NEW.cancelled_at IS NULL
BEGIN
    SELECT RAISE(ABORT, 'INV-72: un encaissement ne depasse pas le reste du de la facture')
     WHERE EXISTS (SELECT 1 FROM factures f
                    WHERE f.id = NEW.facture_id AND f.type <> 'avoir'
                      AND CAST(REPLACE(NEW.montant, '.', '') AS INTEGER)
                        > CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                          - (SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)
                               FROM reglements r
                              WHERE r.facture_id = f.id AND r.type = 'encaissement' AND r.cancelled_at IS NULL)
                          - (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                               FROM factures av WHERE av.origine_facture_id = f.id));
END;

-- TR-31 [INV-74] : un remboursement actif ne dépasse pas le crédit disponible de
-- la facture d'ORIGINE de l'avoir visé (un remboursement peut viser n'importe
-- quel avoir de cette origine) : credit = somme des avoirs - absorbe -
-- remboursements actifs, absorbe = min(somme des avoirs, max(0, M -
-- encaissements actifs)). Ce trigger ne s'applique qu'à une cible qui est un
-- avoir ; tr_30 refuse les autres.
CREATE TRIGGER tr_31_reglements_remboursement
BEFORE INSERT ON reglements
WHEN NEW.type = 'remboursement' AND NEW.cancelled_at IS NULL
BEGIN
    SELECT RAISE(ABORT, 'INV-74: un remboursement ne depasse pas le credit disponible')
     WHERE EXISTS (SELECT 1 FROM factures a JOIN factures o ON o.id = a.origine_facture_id
                    WHERE a.id = NEW.facture_id AND a.type = 'avoir'
                      AND CAST(REPLACE(NEW.montant, '.', '') AS INTEGER)
                        > (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                             FROM factures av WHERE av.origine_facture_id = o.id)
                          - min((SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                                   FROM factures av WHERE av.origine_facture_id = o.id),
                                max(0, CAST(REPLACE(o.total_ht, '.', '') AS INTEGER)
                                       - (SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)
                                            FROM reglements r
                                           WHERE r.facture_id = o.id AND r.type = 'encaissement' AND r.cancelled_at IS NULL)))
                          - (SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)
                               FROM reglements r JOIN factures a2 ON a2.id = r.facture_id
                              WHERE a2.origine_facture_id = o.id AND r.type = 'remboursement' AND r.cancelled_at IS NULL));
END;

-- TR-32 [INV-70] : un règlement n'est jamais modifié ; seules cancelled_at et
-- motif_annulation peuvent être renseignées, UNE seule fois (un règlement déjà
-- annulé est totalement immuable : pas de réactivation, pas de changement de
-- motif). Les colonnes figées sont comparées avec IS NOT : une écriture qui ne
-- change aucune valeur sur un règlement actif reste sans effet.
CREATE TRIGGER tr_32_reglements_update
BEFORE UPDATE ON reglements
BEGIN
    SELECT RAISE(ABORT, 'INV-70: seules cancelled_at et motif_annulation d''un reglement peuvent etre renseignees')
     WHERE NEW.id IS NOT OLD.id
        OR NEW.facture_id IS NOT OLD.facture_id
        OR NEW.type IS NOT OLD.type
        OR NEW.date_evenement IS NOT OLD.date_evenement
        OR NEW.montant IS NOT OLD.montant
        OR NEW.mode IS NOT OLD.mode
        OR NEW.reference IS NOT OLD.reference
        OR NEW.note IS NOT OLD.note
        OR NEW.created_at IS NOT OLD.created_at
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data;
    SELECT RAISE(ABORT, 'INV-70: un reglement ne s''annule qu''une seule fois')
     WHERE OLD.cancelled_at IS NOT NULL;
END;

-- TR-32 [INV-70] : un règlement ne se supprime jamais, actif ou annulé. Avec
-- recursive_triggers=ON, ce trigger refuse aussi le DELETE implicite d'un
-- INSERT OR REPLACE.
CREATE TRIGGER tr_32_reglements_no_delete
BEFORE DELETE ON reglements
BEGIN
    SELECT RAISE(ABORT, 'INV-70: un reglement ne se supprime jamais');
END;

-- TR-33 [INV-75] : l'annulation d'un encaissement actif est refusée si elle rend
-- le crédit de la facture inférieur à la somme des remboursements actifs de son
-- origine. Après l'annulation, les encaissements actifs sont ceux d'aujourd'hui
-- moins le montant de celui-ci ; le crédit se recalcule avec ce total (un
-- encaissement de moins augmente absorbe, donc diminue le crédit). Seule
-- l'annulation d'un encaissement peut faire baisser le crédit : l'annulation d'un
-- remboursement l'augmente et n'est jamais refusée ici.
CREATE TRIGGER tr_33_reglements_annulation
BEFORE UPDATE ON reglements
WHEN OLD.type = 'encaissement' AND OLD.cancelled_at IS NULL AND NEW.cancelled_at IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'INV-75: annulation refusee, le credit deviendrait inferieur aux remboursements actifs')
     WHERE EXISTS (SELECT 1 FROM factures o
                    WHERE o.id = OLD.facture_id
                      AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                             FROM factures av WHERE av.origine_facture_id = o.id)
                          - min((SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                                   FROM factures av WHERE av.origine_facture_id = o.id),
                                max(0, CAST(REPLACE(o.total_ht, '.', '') AS INTEGER)
                                       - ((SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)
                                             FROM reglements r
                                            WHERE r.facture_id = o.id AND r.type = 'encaissement' AND r.cancelled_at IS NULL)
                                          - CAST(REPLACE(OLD.montant, '.', '') AS INTEGER))))
                        < (SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)
                             FROM reglements r JOIN factures a2 ON a2.id = r.facture_id
                            WHERE a2.origine_facture_id = o.id AND r.type = 'remboursement' AND r.cancelled_at IS NULL));
END;
