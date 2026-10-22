-- =====================================================================
-- BATORYA Essentiel V6 — base métier — tranche 010_historique
-- Tranche métier (rang 16, D-64, test T-55) : crée la table `historique`, journal des
-- événements métier (append-only). Elle est livrée avant l'activation de la réacceptation
-- des devis (E-22, INV-206) : les événements `acceptation` y conservent la version et la
-- date métier de chaque acceptation. La planification, auparavant numérotée 010 dans des
-- documents de travail, devient la tranche 011.
--
-- Référence : modèle de données SQLite V3.14 (en relecture) — §2.5 (énumérations), §4.14
-- (spécification de la table), §8 (TR-60), §15 (D-64), §17.1 (suivi des migrations, test
-- T-55) ; invariants INV-110 (journal append-only, événements obligatoires, structure des
-- événements `acceptation`) et INV-111 (énumérations fermées) ; INV-175 et conventions
-- techniques §9 (aucun contrôle de miroir dans un CHECK ou un trigger) ; conventions
-- techniques §5 (tranche NNN_<objet>.sql). Le DDL ci-dessous reprend le §4.14 sans ajout.
--
-- Objets créés (aucun objet existant n'est modifié ni supprimé) :
--   * la table `historique` (STRICT) : id INTEGER PRIMARY KEY AUTOINCREMENT ; type_entite
--     (17 valeurs, §2.5) ; entite_id INTEGER NULL ; bc_id INTEGER NULL, clé étrangère vers
--     bons_commande (ON DELETE RESTRICT, sans ON UPDATE) ; type_evenement (18 valeurs, §2.5) ;
--     acteur (utilisateur, systeme, import ; défaut utilisateur) ; donnees TEXT NULL (JSON
--     valide) ; created_at (horodatage UTC au format AAAA-MM-JJTHH:MM:SS.mmmZ, défaut
--     maintenant). Pas de updated_at ;
--   * contrôle des octets NUL (même mécanisme que 009_pv.sql) : json_valid lit le TEXT comme une chaîne C (arrêt au premier octet NUL, queue
--     ignorée) et GLOB s'arrête aussi au premier NUL ; `donnees` refuse donc tout octet NUL brut (instr(CAST(donnees AS BLOB), x'00') = 0 ;
--     l'échappement JSON \u0000, sans octet NUL, reste valide, et il est refusé dans les champs de l'acceptation par date() et par IN) et
--     `created_at` est contrôlé en octets (length(CAST(created_at AS BLOB)) = 24).
--     La table étant append-only, une valeur fautive ne pourrait pas être corrigée après coup ;
--   * un CHECK de table propre aux événements `acceptation` (structure locale de la ligne,
--     sans lecture d'une autre table) : type_entite = 'devis', entite_id et bc_id non NULL
--     QUELLE QUE SOIT LA NATURE (acceptation initiale ou réacceptation), donnees objet JSON
--     portant date_acceptation (date calendaire), revision (entier >= 1 ou null) et nature
--     ('initiale' ou 'reacceptation') ; une réacceptation exige revision entier et
--     precedente (objet portant date_acceptation et revision). Chaque test de présence est
--     écrit avec IS ou COALESCE : un CHECK qui s'évalue à NULL est accepté par SQLite ;
--   * trois index : idx_historique_bc_id, idx_historique_type_entite_entite_id,
--     idx_historique_created_at ;
--   * deux triggers append-only (TR-60) : tr_60_historique_no_update et
--     tr_60_historique_no_delete. Aucun troisième trigger.
--
-- Décisions du cadrage (propriétaire, 2026-10-22), appliquées ici :
--   * aucun CHECK sur entite_id : c'est la clé primaire de l'entité concernée quand
--     type_entite désigne une table métier, sans clé étrangère (lien polymorphe, §2.1) ; une
--     référence vers une entité supprimable peut subsister ; `import` et `restauration` n'ont
--     pas de table cible, leur entite_id est NULL par convention ;
--   * hors `acceptation`, le contrat SQL de donnees est NULL ou JSON valide (json_valid),
--     sans restriction à un objet ; le contenu de l'événement `import` (§10.7) et l'ancien et
--     le nouveau client_id de `rattachement_client` (INV-49) relèvent du contrat de service ;
--   * la concordance de bc_id avec le BC associé au devis dans bc_devis est garantie par le
--     SERVICE, dans la transaction d'acceptation ou de réacceptation : elle est inter-tables
--     et n'est ni un CHECK, ni un trigger (INV-175), ni une requête de contrôle de cette
--     migration ;
--   * aucune donnée n'est insérée, aucun contrôle général n'est livré.
--
-- Limite assumée : la protection append-only dépend de PRAGMA recursive_triggers=ON, posé à
-- chaque ouverture de connexion (conventions techniques §9). Sans ce réglage, un INSERT OR
-- REPLACE ou un REPLACE INTO sur un id existant supprime la ligne sans déclencher
-- tr_60_historique_no_delete (UPDATE, DELETE et UPSERT DO UPDATE restent refusés). La
-- protection n'est donc pas absolue hors configuration conforme ; aucun trigger
-- supplémentaire n'est prévu (décision du propriétaire, 2026-10-22). Aucun index unique
-- autre que la clé primaire ne doit être ajouté à cette table : un REPLACE supprimerait la
-- ligne en conflit.
--
-- Exécution : aucune reconstruction de table (le protocole foreign_keys = OFF n'est pas
-- requis) ; une garde d'exécution (lecture seule) exige user_version = 15 : 010 ne
-- s'applique qu'à une base arrêtée à 009c. Le fichier ne contient ni BEGIN/COMMIT ni PRAGMA
-- de réglage : le runner l'exécute dans une transaction (BEGIN IMMEDIATE), pose
-- PRAGMA user_version = 16 avant le COMMIT, et un échec entraîne le ROLLBACK intégral.
-- Messages des triggers en ASCII, préfixés INV-110.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Garde d'exécution (lecture seule, aucune trace) : user_version doit valoir 15 (010 est
-- le rang 16 et ne s'applique qu'à une base arrêtée à 009c). Table temporaire supprimée
-- aussitôt ; échec = erreur de CHECK, donc ROLLBACK.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE garde_010_user_version (
    user_version INTEGER NOT NULL
        CONSTRAINT "010 exige user_version = 15 (chaine 009c -> 010)" CHECK (user_version = 15)
);
INSERT INTO garde_010_user_version (user_version) SELECT user_version FROM pragma_user_version;
DROP TABLE garde_010_user_version;


-- ---------------------------------------------------------------------
-- historique (§4.14) — journal append-only des événements métier [INV-110, INV-111]
-- ---------------------------------------------------------------------
CREATE TABLE historique (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    type_entite    TEXT    NOT NULL
                   CHECK (type_entite IN ('client', 'fournisseur', 'prestation', 'devis', 'bc', 'facture', 'reglement', 'depense',
                                          'pv', 'garantie', 'planning_evenement', 'bc_note', 'urssaf_periode', 'urssaf_correction',
                                          'document', 'import', 'restauration')),
    entite_id      INTEGER,
    bc_id          INTEGER REFERENCES bons_commande (id) ON DELETE RESTRICT,
    type_evenement TEXT    NOT NULL
                   CHECK (type_evenement IN ('creation', 'modification', 'acceptation', 'refus', 'annulation', 'emission', 'reglement',
                                             'annulation_reglement', 'remboursement', 'avoir', 'passage_termine', 'retour_en_cours',
                                             'declenchement_garantie', 'rattachement_client', 'declaration_urssaf', 'correction_urssaf',
                                             'import', 'restauration')),
    acteur         TEXT    NOT NULL DEFAULT 'utilisateur'
                   CHECK (acteur IN ('utilisateur', 'systeme', 'import')),
    donnees        TEXT    CHECK (donnees IS NULL OR (json_valid(donnees) AND instr(CAST(donnees AS BLOB), x'00') = 0)),
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                   CHECK (created_at GLOB
                          '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'
                          AND length(CAST(created_at AS BLOB)) = 24),

    -- Structure locale des événements `acceptation` (§4.14) : aucune lecture d'une autre table.
    CHECK (type_evenement <> 'acceptation' OR (
          type_entite = 'devis' AND entite_id IS NOT NULL AND bc_id IS NOT NULL
      AND donnees IS NOT NULL AND json_valid(donnees) AND json_type(donnees) IS 'object'
      AND json_type(donnees, '$.date_acceptation') IS 'text'
      AND COALESCE(json_extract(donnees, '$.date_acceptation') GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]', 0)
      AND date(json_extract(donnees, '$.date_acceptation')) IS json_extract(donnees, '$.date_acceptation')
      AND COALESCE(json_type(donnees, '$.revision'), 'absent') IN ('null', 'integer')
      AND (json_type(donnees, '$.revision') IS 'null' OR COALESCE(json_extract(donnees, '$.revision') >= 1, 0))
      AND json_type(donnees, '$.nature') IS 'text'
      AND COALESCE(json_extract(donnees, '$.nature') IN ('initiale', 'reacceptation'), 0)
      AND (json_extract(donnees, '$.nature') IS NOT 'reacceptation'
           OR (json_type(donnees, '$.revision') IS 'integer' AND json_type(donnees, '$.precedente') IS 'object'))
      AND (json_type(donnees, '$.precedente') IS NULL
           OR (json_type(donnees, '$.precedente') IS 'object'
               AND json_type(donnees, '$.precedente.date_acceptation') IS 'text'
               AND COALESCE(json_extract(donnees, '$.precedente.date_acceptation') GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]', 0)
               AND date(json_extract(donnees, '$.precedente.date_acceptation')) IS json_extract(donnees, '$.precedente.date_acceptation')
               AND COALESCE(json_type(donnees, '$.precedente.revision'), 'absent') IN ('null', 'integer')))
    ))
) STRICT;

CREATE INDEX idx_historique_bc_id ON historique (bc_id);
CREATE INDEX idx_historique_type_entite_entite_id ON historique (type_entite, entite_id);
CREATE INDEX idx_historique_created_at ON historique (created_at);


-- ---------------------------------------------------------------------
-- TR-60 [INV-110] : historique est append-only. Deux triggers BEFORE, aucun autre. Avec
-- recursive_triggers=ON (conventions §9), le trigger DELETE refuse aussi la suppression
-- implicite d'un INSERT OR REPLACE sur un id existant.
-- ---------------------------------------------------------------------
CREATE TRIGGER tr_60_historique_no_update
BEFORE UPDATE ON historique
BEGIN
    SELECT RAISE(ABORT, 'INV-110: un evenement d''historique ne se modifie jamais');
END;

CREATE TRIGGER tr_60_historique_no_delete
BEFORE DELETE ON historique
BEGIN
    SELECT RAISE(ABORT, 'INV-110: un evenement d''historique ne se supprime jamais');
END;
