-- =====================================================================
-- BATORYA Essentiel V6 — machine.db — migration 001_initial
-- Référence : modèle de données SQLite V3.8, §5 et §5.1 (INV-02, INV-25,
--             INV-106, INV-150 à INV-152, INV-171, INV-172), §11.4, §12.
--
-- machine.db : jamais sauvegardée, jamais restaurée, aucune donnée commerciale.
-- Les secrets (clé de licence, jetons Gmail) vivent dans le coffre système,
-- jamais ici (INV-151, D-04).
--
-- Exécution par le runner de migrations (côté Rust) :
--   * une seule transaction pour ce fichier ;
--   * PRAGMA user_version = 1 posé par le runner APRÈS succès ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--       foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini.
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA.
--
-- Conventions : toutes les tables sont STRICT (modèle §1) ; TS = TEXT
-- 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé par GLOB (modèle §2.2).
-- Aucune ligne n'est créée par cette migration : les singletons (id = 1) sont
-- créés par le service d'initialisation avec INSERT OR IGNORE (modèle §5.1,
-- INV-172). Aucun trigger dans machine.db : INV-25 et INV-106 sont des gardes
-- de service (D-30).
-- =====================================================================


-- ---------------------------------------------------------------------
-- utilisateur_local (singleton id = 1)
-- Compte local obligatoire au premier démarrage (D-28, INV-171) : identifiant
-- et mot de passe ; nom et prenom facultatifs. Pas de compte en ligne, pas de rôles.
-- mot_de_passe_hash : encodage argon2id complet, jamais en clair (INV-151).
-- deblocage_* : code/token temporaire de déblocage, seul le hash est conservé.
-- ---------------------------------------------------------------------
CREATE TABLE utilisateur_local (
    id                   INTEGER PRIMARY KEY CHECK (id = 1),
    identifiant          TEXT NOT NULL UNIQUE CHECK (identifiant <> ''),
    nom                  TEXT,
    prenom               TEXT,
    mot_de_passe_hash    TEXT NOT NULL,
    deblocage_token_hash TEXT,
    deblocage_expire_at  TEXT,
    created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (nom    IS NULL OR nom    <> ''),
    CHECK (prenom IS NULL OR prenom <> ''),
    -- jamais de mot de passe en clair : seul un encodage argon2id est accepté
    CHECK (mot_de_passe_hash GLOB '$argon2id$*'),
    -- token et expiration vont ensemble
    CHECK ((deblocage_token_hash IS NULL) = (deblocage_expire_at IS NULL)),
    CHECK (deblocage_token_hash IS NULL OR deblocage_token_hash <> ''),
    CHECK (deblocage_expire_at IS NULL OR deblocage_expire_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- licence (singleton id = 1)
-- Licence liée à l'ordinateur / installation (CDC §41). États non secrets
-- uniquement : la clé de licence est dans le coffre système.
-- Vérification tous les 3 mois ; échec => 15 jours de grâce (grace_debut_at).
-- ---------------------------------------------------------------------
CREATE TABLE licence (
    id                          INTEGER PRIMARY KEY CHECK (id = 1),
    identifiant_installation    TEXT NOT NULL CHECK (identifiant_installation <> ''),
    empreinte_machine_hash      TEXT CHECK (empreinte_machine_hash IS NULL OR empreinte_machine_hash <> ''),
    derniere_verification_ok_at TEXT,
    derniere_tentative_at       TEXT,
    grace_debut_at              TEXT,
    created_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (derniere_verification_ok_at IS NULL OR derniere_verification_ok_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (derniere_tentative_at IS NULL OR derniere_tentative_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (grace_debut_at IS NULL OR grace_debut_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- services_etat (singleton id = 1)
-- Services BATORYA : licence / mises à jour / référentiels (CDC §8, §40).
-- ---------------------------------------------------------------------
CREATE TABLE services_etat (
    id                           INTEGER PRIMARY KEY CHECK (id = 1),
    derniere_communication_ok_at TEXT,
    mise_a_jour_disponible       INTEGER NOT NULL DEFAULT 0 CHECK (mise_a_jour_disponible IN (0, 1)),
    created_at                   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at                   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (derniere_communication_ok_at IS NULL OR derniere_communication_ok_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;


-- ---------------------------------------------------------------------
-- stockage_racines
-- Racines de stockage documentaire (INV-106, garde de service). Jamais supprimée : changer de
-- dossier de travail crée une nouvelle racine active ; les documents existants
-- gardent leur racine (référence logique depuis documents.racine_stockage_id).
-- chemin_absolu : modifié uniquement par l'opération explicite de remappage
-- (règle de service, non exprimable en SQL).
-- Au plus une racine active (index unique partiel). Pour changer de racine
-- active : désactiver l'ancienne, puis activer la nouvelle, dans une transaction.
-- ---------------------------------------------------------------------
CREATE TABLE stockage_racines (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    chemin_absolu TEXT NOT NULL UNIQUE CHECK (chemin_absolu <> ''),
    actif         INTEGER NOT NULL DEFAULT 0 CHECK (actif IN (0, 1)),
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

CREATE UNIQUE INDEX ux_stockage_racines_actif ON stockage_racines (actif) WHERE actif = 1;


-- ---------------------------------------------------------------------
-- preferences_sauvegarde (singleton id = 1)
-- Moteur de sauvegarde commun : automatique, manuel, à la fermeture (CDC §8, §42).
-- Valeurs par défaut (D-29) : automatique activée, toutes les 30 minutes,
-- sauvegarde à la fermeture activée.
-- derniere_sauvegarde_at / _statut : NULL avant la première sauvegarde, puis
-- renseignés ensemble ; statut = 'succes' | 'echec'.
-- ---------------------------------------------------------------------
CREATE TABLE preferences_sauvegarde (
    id                         INTEGER PRIMARY KEY CHECK (id = 1),
    auto_active                INTEGER NOT NULL DEFAULT 1 CHECK (auto_active IN (0, 1)),
    frequence_minutes          INTEGER NOT NULL DEFAULT 30 CHECK (frequence_minutes >= 1),
    sauvegarde_fermeture       INTEGER NOT NULL DEFAULT 1 CHECK (sauvegarde_fermeture IN (0, 1)),
    derniere_sauvegarde_at     TEXT,
    derniere_sauvegarde_statut TEXT CHECK (derniere_sauvegarde_statut IS NULL
                                           OR derniere_sauvegarde_statut IN ('succes', 'echec')),

    CHECK (derniere_sauvegarde_at IS NULL OR derniere_sauvegarde_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    -- date et statut de la dernière sauvegarde vont ensemble
    CHECK ((derniere_sauvegarde_at IS NULL) = (derniere_sauvegarde_statut IS NULL))
) STRICT;


-- ---------------------------------------------------------------------
-- gmail_etat (singleton id = 1)
-- État de connexion uniquement ; les jetons sont dans le coffre système
-- (INV-151). connecte = 1 => compte et date connus ; connecte = 0 => effacés.
-- ---------------------------------------------------------------------
CREATE TABLE gmail_etat (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    connecte     INTEGER NOT NULL DEFAULT 0 CHECK (connecte IN (0, 1)),
    compte_email TEXT CHECK (compte_email IS NULL OR compte_email <> ''),
    connecte_at  TEXT,

    CHECK (connecte_at IS NULL OR connecte_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'),
    CHECK ((connecte = 1) = (compte_email IS NOT NULL AND connecte_at IS NOT NULL)),
    CHECK (connecte = 1 OR (compte_email IS NULL AND connecte_at IS NULL))
) STRICT;


-- ---------------------------------------------------------------------
-- sequence_high_water
-- Plus haut numéro jamais attribué par (type_objet, annee) — INV-25 (garde de service), D-27.
-- Écrit par le service AVANT le COMMIT de la base métier (modèle §5, §11.4).
-- max_attribue ne diminue jamais (garde de service) ; un trou est accepté ; un numéro attribué
-- n'est jamais réutilisé.
-- annee : 2 chiffres ; 0 réservé à CLI / FOU (comme numerotation_sequences).
-- Plafonds : 99 999 (documents), 9 999 (CLI / FOU) — modèle §6.
-- ---------------------------------------------------------------------
CREATE TABLE sequence_high_water (
    type_objet   TEXT    NOT NULL CHECK (type_objet IN ('CLI','FOU','DEV','BCD','ACP','FAC','AVO','PVR','DEP')),
    annee        INTEGER NOT NULL DEFAULT 0 CHECK (annee BETWEEN 0 AND 99),
    max_attribue INTEGER NOT NULL DEFAULT 0 CHECK (max_attribue >= 0),
    updated_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    PRIMARY KEY (type_objet, annee),
    CHECK ((type_objet IN ('CLI','FOU')) = (annee = 0)),
    CHECK (max_attribue <= CASE WHEN type_objet IN ('CLI','FOU') THEN 9999 ELSE 99999 END),
    CHECK (updated_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;
