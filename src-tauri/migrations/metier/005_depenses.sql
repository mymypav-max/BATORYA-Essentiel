-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration 005_depenses
-- Cinquième tranche (rang 5) : dépenses.
--
-- Référence : modèle de données SQLite V3.13 — §2 (conventions), §3.5, §4.12
-- (dépenses), §6 (numérotation DEP), §8 (TR-01, TR-101, TR-102), §9 (index),
-- §10.3 (blocs refusés à l'import), §17.1 (chaîne des migrations) ;
-- CADRAGE__005_depenses.md (décisions DV-1 à DV-12, C-1, T-1).
-- Invariants : INV-04, INV-05, INV-06, INV-07, INV-10, INV-11, INV-14, INV-20,
-- INV-22, INV-23, INV-100, INV-177, INV-179, INV-183, INV-188, INV-193,
-- INV-197, INV-201. Décisions : D-12, D-18, D-23, D-31, D-38, D-39, D-50,
-- D-55. Propositions techniques : PT-1 (tranché), PT-14.
--
-- Précisions de DDL retenues pour cette tranche :
--   * Une dépense est un objet numéroté, définitif dès sa création : aucun
--     DELETE (tr_101), numéro immuable (tr_01), numéro jamais réutilisé
--     (UNIQUE ; séquence DEP de numerotation_sequences, migration 001).
--   * Aucune colonne statut : une dépense est active tant que cancelled_at IS
--     NULL. L'annulation (cancelled_at + motif_annulation, posés ensemble) est
--     irréversible, et une dépense annulée est totalement immuable (tr_102,
--     INV-197), updated_at compris.
--   * Une seule date métier : date_depense (date réelle, saisie par
--     l'utilisateur, a posteriori possible). Son année donne le yy du numéro
--     (CHECK) ; created_at et updated_at sont des données techniques.
--   * montant : un seul montant, HT, décimal exact à 2 décimales stocké en TEXT
--     (jamais REAL), strictement positif. Aucune colonne de TVA, de TTC, de
--     facture, d'échéance ni de paiement.
--   * Les FK pointent uniquement vers la clé primaire id des tables parentes
--     (fournisseurs 002, bons_commande 004, categories_depenses 001), toutes en
--     RESTRICT, sans clause ON UPDATE. Cette migration ne lit aucune autre
--     colonne des tables parentes (en particulier ni fournisseurs.statut, ni
--     bons_commande.devis_id, ni bons_commande.statut).
--   * Un BC annulé reste une cible valide : aucune FK, aucun CHECK ni aucun
--     trigger ne dépend de l'état du BC. Les règles de rattachement (30 jours
--     après date_100_facture, confirmation, BC annulé sans délai, catégorie
--     active, fournisseur existant, cohérence année DEP / date_depense à la
--     correction, borne d'année 2001-2099 de D-38) sont des règles de service,
--     jamais des CHECK ni des triggers inter-tables.
--   * piece_jointe_racine_id est une référence logique vers machine.db
--     (stockage_racines) : aucune FK possible entre deux bases.
--   * Pas d'historique propre aux dépenses, pas de BLOC-IMP : le bloc
--     'depenses' est refusé par import-v6.json (modèle §10.3, D-23). Donc
--     ni origine, ni legacy_id, ni legacy_data, ni legacy_numero.
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 5 (rang de cette migration dans la chaîne ordonnée,
--     D-55) posé par le runner dans la transaction de la migration, avant son
--     COMMIT (conventions techniques §5) ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--       recursive_triggers=ON (D-39). Avec recursive_triggers=ON, tr_101 refuse
--       aussi le DELETE implicite d'un INSERT OR REPLACE (INV-07).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA. Il ne reconstruit
-- aucune table existante et ne corrige aucune migration précédente.
--
-- Aucune ligne n'est insérée. Le numéro est attribué par le service (séquence
-- DEP de numerotation_sequences, année de date_depense ; high-water dans
-- machine.db ; PT-1).
--
-- Conventions : table STRICT (§1) ; TS = TEXT 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC)
-- contrôlé par GLOB ; D = 'YYYY-MM-DD' (date réelle : GLOB + date(x) IS x —
-- date() renvoie NULL pour un mois 00/13 ou un jour 00, et un CHECK évalué à
-- NULL est accepté, donc « = » ne suffit pas) ; D2 = montant à 2 décimales.
-- Les GLOB sont explicites (pas de {n}).
-- =====================================================================


-- ---------------------------------------------------------------------
-- depenses (§4.12)
-- fournisseur_id : facultatif (NULL = dépense sans fournisseur) ; modifiable
-- tant que la dépense est active (changer, retirer, ajouter).
-- bc_id : facultatif (NULL = dépense globale) ; rattachement, changement et
-- détachement possibles tant que la dépense est active.
-- montant : D2 strictement positif — GLOB '[0-9]*.[0-9][0-9]' (au moins un
-- chiffre, exactement 2 décimales), aucun caractère hors chiffres et point,
-- un seul point, aucun zéro de tête, et différent de '0.00' (seule forme de
-- zéro que ce motif accepte). Les négatifs sont exclus par le jeu de
-- caractères ; INV-14 ne les autorise pas pour les dépenses.
-- description : obligatoire, non vide.
-- cancelled_at / motif_annulation : posés ensemble ou absents ensemble.
-- ---------------------------------------------------------------------
CREATE TABLE depenses (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                 TEXT    NOT NULL UNIQUE,
    fournisseur_id         INTEGER REFERENCES fournisseurs (id) ON DELETE RESTRICT,
    bc_id                  INTEGER REFERENCES bons_commande (id) ON DELETE RESTRICT,
    date_depense           TEXT    NOT NULL
                           CHECK (date_depense GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                                  AND date(date_depense) IS date_depense),
    montant                TEXT    NOT NULL
                           CHECK (montant GLOB '[0-9]*.[0-9][0-9]'
                                  AND montant NOT GLOB '*[^0-9.]*'
                                  AND montant NOT GLOB '*.*.*'
                                  AND montant NOT GLOB '0[0-9]*'
                                  AND montant <> '0.00'),
    categorie_id           INTEGER NOT NULL REFERENCES categories_depenses (id) ON DELETE RESTRICT,
    description            TEXT    NOT NULL CHECK (description <> ''),
    piece_jointe_chemin    TEXT    CHECK (piece_jointe_chemin IS NULL OR piece_jointe_chemin <> ''),
    piece_jointe_racine_id INTEGER,
    notes                  TEXT,
    cancelled_at           TEXT,
    motif_annulation       TEXT    CHECK (motif_annulation IS NULL OR motif_annulation <> ''),
    created_at             TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at             TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    -- numéro : format et année cohérente avec date_depense (INV-20), sans condition d'origine
    CHECK (numero GLOB 'DEP-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
           AND substr(numero, 11, 2) = substr(date_depense, 3, 2)),
    -- pièce jointe : chemin et racine ensemble, ou aucun des deux
    CHECK ((piece_jointe_chemin IS NULL) = (piece_jointe_racine_id IS NULL)),
    -- annulation : date et motif ensemble, ou aucun des deux
    CHECK ((cancelled_at IS NULL) = (motif_annulation IS NULL)),
    CHECK (cancelled_at IS NULL OR cancelled_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- =====================================================================
-- Index (§9) — un index par FK, plus la recherche par date métier.
-- numero est couvert par son UNIQUE.
-- =====================================================================
CREATE INDEX idx_depenses_bc_id          ON depenses (bc_id);
CREATE INDEX idx_depenses_fournisseur_id ON depenses (fournisseur_id);
CREATE INDEX idx_depenses_categorie_id   ON depenses (categorie_id);
CREATE INDEX idx_depenses_date_depense   ON depenses (date_depense);


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Les trois sont locaux à une ligne et ne lisent aucune autre table.
-- Les triggers BEFORE s'exécutent avant les CHECK de la ligne.
-- =====================================================================

-- TR-01 [INV-23] : numero immuable ; l'année (yy) de date_depense, cohérente
-- avec celle du numéro par CHECK, ne change jamais. Une correction de
-- date_depense dans la même année reste permise ; une correction qui changerait
-- l'année se règle par annulation puis nouvelle dépense (jamais par
-- renumérotation).
CREATE TRIGGER tr_01_depenses_numero_immuable
BEFORE UPDATE OF numero, date_depense ON depenses
WHEN NEW.numero IS NOT OLD.numero
  OR substr(NEW.date_depense, 3, 2) IS NOT substr(OLD.date_depense, 3, 2)
BEGIN
    SELECT RAISE(ABORT, 'INV-23: depenses.numero et l''annee de depenses.date_depense sont immuables');
END;

-- TR-101 [INV-06] : aucune dépense n'est jamais supprimée, active ou annulée.
-- Avec recursive_triggers=ON, ce trigger refuse aussi le DELETE implicite d'un
-- INSERT OR REPLACE.
CREATE TRIGGER tr_101_depenses_no_delete
BEFORE DELETE ON depenses
BEGIN
    SELECT RAISE(ABORT, 'INV-06: une depense ne se supprime jamais');
END;

-- TR-102 [INV-197] : une dépense annulée est totalement immuable. Aucune liste
-- de colonnes : tout UPDATE d'une ligne déjà annulée est refusé, y compris
-- updated_at seul, le retour de cancelled_at à NULL et la modification du
-- motif. L'annulation elle-même (OLD.cancelled_at IS NULL) n'est pas visée.
CREATE TRIGGER tr_102_depenses_annulee_immuable
BEFORE UPDATE ON depenses
WHEN OLD.cancelled_at IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'INV-197: une depense annulee est totalement immuable');
END;
