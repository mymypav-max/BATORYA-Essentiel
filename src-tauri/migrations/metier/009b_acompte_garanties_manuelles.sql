-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration corrective 009b_acompte_garanties_manuelles
-- Corrective (rang 14, après 009_pv et 009a_bc_annulation_interdite_si_facture) : alignement du SQL livré sur les décisions
-- métier validées de la révision F (2026-10-17) :
--   * acompte : plafonné par l'acompte PRÉVU du devis (jusqu'à 100 % du marché) ;
--   * situation : jamais à 100 % du contractuel (nette après < contractuel) ;
--   * solde : strictement positif, aucun solde à 0.00, égal au contractuel FINAL
--     (contractuel moins avoirs « prestations non réalisées » portant sur un solde)
--     moins la facturation nette avant le solde ;
--   * avoirs : motif en liste fermée (correction_erreur | prestation_non_realisee) ;
--     un avoir sur acompte ne corrige qu'une erreur ;
--   * ordre des factures : aucun acompte sur un devis COUVERT par une situation
--     (V3.14, D-62, INV-204, INV-205). Une situation couvre tous les devis rattachés
--     à son BC à son émission ; la couverture est ENREGISTRÉE dans la table
--     situation_devis (clé (facture_id, devis_id)), par le service, dans la
--     transaction d'émission. Un devis rattaché après l'émission n'est pas couvert
--     par cette situation (aucune rétroactivité) : son acompte reste possible. La
--     règle ne lit ni les avoirs, ni le montant net, ni l'avancement, ni aucun
--     horodatage. S'ajoute à « aucun acompte après un solde », déjà porté par 006 ;
--     l'acompte est facultatif (les situations peuvent commencer sans acompte) ; un
--     acompte prévu à 100 % et entièrement facturé ne clôture pas le cycle (aucun
--     solde à 0.00, aucune règle de cumul supplémentaire) ;
--   * garanties : déclenchement MANUEL, sans facture de solde ni facture de
--     déclenchement obligatoire ; périmètre contractuel réel (retrait ciblé d'une
--     prestation) ; traçabilité conservée.
--
-- Référence : modèle de données SQLite V3.14 — §3.2 (couverture d'une situation),
-- §4.7 bis, §4.8 bis et ter (situation_devis), §8 (TR-22, TR-104, TR-105), §9, §13
-- (C-43), §14 (CK-21, CK-22), §15 (D-62), §17.1 (test T-53) ; modèle métier §10 et
-- §12 ; V3.13 (révision F) pour les règles de facturation et de garanties
-- conservées : §4.8, §4.10, §8 (TR-22, TR-50, TR-51).
-- Invariants : INV-52, INV-55, INV-57, INV-58, INV-76, INV-85 à INV-90, INV-134,
-- INV-189 (message livré par 006), et les NOUVEAUX INV-204 (couverture d'une
-- situation) et INV-205 (aucun acompte sur un devis couvert). Identifiants V3.14
-- nouveaux : INV-204, INV-205, TR-104, TR-105, D-62 (CK-21 et CK-22 sont des
-- requêtes de diagnostic, jamais des objets SQL). Les autres triggers reprennent
-- les numéros TR-22, TR-50 et TR-51 existants.
--
-- Les migrations 006 et 008 (livrées, susceptibles d'avoir été appliquées) restent
-- INCHANGÉES : cette corrective s'ajoute à la fin de la chaîne (conventions §5).
--
-- Contenu :
--   1. gardes d'exécution (foreign_keys = 0, user_version = 13, AUCUNE situation
--      existante : D-62) ;
--   1 bis. situation_devis (V3.14, §4.8 ter) : table, index, TR-104 (insertion),
--      TR-105 (aucun UPDATE ni DELETE) ;
--   2. facturation : tr_22_factures_acompte, tr_22_factures_situation,
--      tr_22_factures_solde et tr_23_factures_avoir supprimés puis recréés
--      (DROP TRIGGER / CREATE TRIGGER, même nom) ; la garde d'ordre de
--      tr_22_factures_acompte lit situation_devis. Aucune table de facturation n'est reconstruite : la clause
--      CHECK « type = 'solde' OR total_ht <> '0.00' » de 006 reste en place (elle
--      n'est pas contradictoire pour un acompte, une situation ou un avoir) ; le
--      refus du solde à 0.00 est porté par le trigger. Les données existantes ne
--      sont ni lues ni modifiées : un éventuel solde à 0.00 historique reste
--      une ligne d'historique immuable (TR-20) ;
--   3. garanties : table reconstruite (protocole de reconstruction, conventions
--      §5) pour rendre facture_declenchement_id NULLABLE (un déclenchement manuel
--      n'est lié à aucune facture ; la colonne ne sert plus qu'à l'historique des
--      garanties créées sous l'ancienne règle) ; données copiées avec leurs ids ;
--      sqlite_sequence conservée ; index et triggers recréés ;
--   4. bc_ligne_retraits_garantie : nouvelle table, append-only, une ligne par
--      prestation (ligne de BC) retirée du périmètre contractuel des garanties.
--      Le suivi ACTIF d'une garantie est un état DÉRIVÉ : une garantie est active
--      tant que sa ligne de BC n'a pas de retrait. La garantie elle-même n'est
--      jamais modifiée ni supprimée (TR-50) : sa traçabilité est conservée.
--
-- Garde de migration (D-62) : 009b REFUSE de s'appliquer si `factures` contient au
-- moins une situation. Une situation préexistante n'a aucune couverture fiable :
-- aucun lien n'est inventé, aucune donnée n'est modifiée, aucun mécanisme de
-- reprise n'existe. L'échec est une erreur de CHECK (garde TEMP) : le runner annule
-- la transaction, base et user_version inchangés.
--
-- Hors périmètre (règles de SERVICE, non portées par le SQL) :
--   * l'ÉMISSION de la situation et l'enregistrement de sa couverture : le service
--     écrit, dans la même transaction BEGIN IMMEDIATE, la facture, ses lignes, puis
--     UNE instruction « INSERT INTO situation_devis (facture_id, devis_id) SELECT
--     :facture, devis_id FROM bc_devis WHERE bc_id = :bc ». SQLite ne peut ni
--     exiger au COMMIT qu'une situation ait une couverture, ni vérifier qu'elle
--     est exhaustive, ni distinguer cet INSERT d'un INSERT tardif : l'exhaustivité
--     est garantie par le service et vérifiée par les tests (T-53), avec les
--     diagnostics CK-21 et CK-22 ;
--   * la composition des lignes d'une situation (PT-11 / M3), l'annulation du BC
--     (H6) et la situation de montant nul (refusée, règle inchangée) ne sont pas
--     modifiées par cette migration ;
--   * le déclenchement manuel (qui, quand, quelles prestations) et la date de
--     déclenchement : à concevoir ;
--   * la moins-value acceptée n'a pas de table (schéma des réductions à concevoir,
--     PT-12) : la ligne de retrait de motif « moins_value » est écrite par le
--     service après acceptation d'une moins-value TOTALE de la prestation ; le SQL
--     ne peut pas le vérifier ;
--   * une moins-value ou un avoir PARTIEL ne retire pas la prestation par défaut :
--     le traitement du périmètre résiduel est À CONCEVOIR ; seul le service écrit
--     un retrait ;
--   * le contractuel COURANT (montants acceptés moins réductions par ligne de BC
--     acceptées non annulées) : le stockage des réductions n'est pas défini (modèle
--     SQLite §3.2 et §3.8, PT-12 : À CONCEVOIR) ; aucune réduction ne peut donc
--     exister en base, et le contractuel lu par les triggers est Σ total_ht des
--     devis rattachés (le montant accepté). Le contractuel FINAL, lui, déduit les
--     avoirs « prestations non réalisées » sur solde, qui existent en base : il est
--     porté par tr_22_factures_solde ;
--   * historique : un avoir déjà présent dont le motif n'est pas dans la liste
--     fermée (écrit sous 006, motif libre) est conservé tel quel ; il n'est jamais
--     compté comme « prestation non réalisée ».
--
-- Exécution par le runner de migrations (côté Rust) — protocole de
-- reconstruction, conventions §5 :
--   * hors transaction : PRAGMA foreign_keys = OFF, puis relecture (= 0) ;
--   * une seule transaction pour ce fichier (BEGIN IMMEDIATE) ;
--   * ce fichier = étapes 4 à 11 ; puis, dans la transaction :
--     PRAGMA foreign_key_check (résultat vide), PRAGMA integrity_check,
--     PRAGMA user_version = 14 (rang de 009b), COMMIT ; échec = ROLLBACK intégral ;
--   * hors transaction : PRAGMA foreign_keys = ON, puis relecture (= 1) ;
--   * réglages de connexion à chaque ouverture (hors de ce fichier) :
--     foreign_keys=ON, journal_mode=WAL, synchronous=FULL, busy_timeout défini,
--     recursive_triggers=ON (D-39).
-- Ce fichier ne contient donc ni BEGIN/COMMIT ni PRAGMA d'écriture.
-- Aucune ligne métier n'est créée : la seule écriture est la copie technique des
-- garanties existantes (ids conservés) et la conservation de sqlite_sequence.
--
-- Conventions : tables STRICT ; TS = TEXT 'YYYY-MM-DDTHH:MM:SS.SSSZ' (UTC) contrôlé
-- par GLOB ; D = 'YYYY-MM-DD' (date réelle : GLOB + date(x) IS x). Les montants
-- sont comparés en centimes entiers : CAST(REPLACE(x, '.', '') AS INTEGER).
-- Les triggers sont BEFORE : ils s'exécutent avant les CHECK de la ligne.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Gardes d'exécution (lecture seule, aucune trace) :
--   * foreign_keys doit valoir 0 (étapes 1 et 2 du protocole) ;
--   * user_version doit valoir 13 : 009b est le rang 14 et ne s'applique qu'à une
--     base arrêtée à 009a (chaîne 009 -> 009a -> 009b) ;
--   * aucune situation ne doit exister (D-62) : sa couverture ne pourrait pas être
--     reconstruite de façon fiable ; aucune donnée n'est lue au-delà du comptage.
-- Tables temporaires supprimées aussitôt ; échec = erreur de CHECK, donc ROLLBACK.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE garde_009b_foreign_keys_off (
    foreign_keys INTEGER NOT NULL
        CONSTRAINT "009b exige PRAGMA foreign_keys = OFF (protocole de reconstruction)" CHECK (foreign_keys = 0)
);
INSERT INTO garde_009b_foreign_keys_off (foreign_keys) SELECT foreign_keys FROM pragma_foreign_keys;
DROP TABLE garde_009b_foreign_keys_off;

CREATE TEMP TABLE garde_009b_user_version (
    user_version INTEGER NOT NULL
        CONSTRAINT "009b exige user_version = 13 (chaine 009a -> 009b)" CHECK (user_version = 13)
);
INSERT INTO garde_009b_user_version (user_version) SELECT user_version FROM pragma_user_version;
DROP TABLE garde_009b_user_version;

CREATE TEMP TABLE garde_009b_aucune_situation (
    nb_situations INTEGER NOT NULL
        CONSTRAINT "009b refuse de s'appliquer: au moins une situation existe deja, sa couverture ne peut pas etre reconstruite de facon fiable (aucun lien invente, aucune donnee modifiee)" CHECK (nb_situations = 0)
);
INSERT INTO garde_009b_aucune_situation (nb_situations) SELECT COUNT(*) FROM factures WHERE type = 'situation';
DROP TABLE garde_009b_aucune_situation;


-- =====================================================================
-- 1 bis. situation_devis (V3.14 §4.8 ter) — couverture d'une situation [INV-204]
-- Une ligne = « la situation facture_id couvre le devis devis_id ». Clé primaire
-- composite : pas d'id de substitution, pas d'horodatage (la date d'émission est
-- celle de la facture), pas de bc_id (le BC se déduit de la facture). Les FK
-- RESTRICT empêchent de supprimer une facture ou un devis couvert. La clé tient
-- lieu d'index sur facture_id. Table STRICT ordinaire (WITHOUT ROWID n'est employé
-- par aucune migration livrée).
-- =====================================================================
CREATE TABLE situation_devis (
    facture_id INTEGER NOT NULL REFERENCES factures (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    devis_id   INTEGER NOT NULL REFERENCES devis (id)    ON DELETE RESTRICT ON UPDATE RESTRICT,

    PRIMARY KEY (facture_id, devis_id)
) STRICT;

CREATE INDEX idx_situation_devis_devis_id ON situation_devis (devis_id);

-- TR-104 [INV-204] : à l'INSERT, la facture est une situation et le devis appartient
-- au BC de la facture (le lien bc_devis existe). Un parent inexistant n'est pas
-- traité ici : c'est la FK qui refuse. `type` et `bc_id` d'une facture (tr_20) et
-- l'appartenance d'un devis à un BC (tr_99_bc_devis_no_update / no_delete) étant
-- immuables, ces deux vérités le restent après l'insertion.
CREATE TRIGGER tr_104_situation_devis_insert
BEFORE INSERT ON situation_devis
BEGIN
    SELECT RAISE(ABORT, 'INV-204: la couverture ne porte que sur une facture de type situation')
     WHERE EXISTS (SELECT 1 FROM factures f WHERE f.id = NEW.facture_id AND f.type <> 'situation');
    SELECT RAISE(ABORT, 'INV-204: le devis couvert doit etre rattache au bon de commande de la situation')
     WHERE EXISTS (SELECT 1 FROM factures f
                    WHERE f.id = NEW.facture_id
                      AND NOT EXISTS (SELECT 1 FROM bc_devis l WHERE l.bc_id = f.bc_id AND l.devis_id = NEW.devis_id));
END;

-- TR-105 [INV-204] : une couverture ne se modifie ni ne se supprime jamais ; avec
-- recursive_triggers=ON, le trigger DELETE refuse aussi le DELETE implicite d'un
-- INSERT OR REPLACE.
CREATE TRIGGER tr_105_situation_devis_update
BEFORE UPDATE ON situation_devis
BEGIN
    SELECT RAISE(ABORT, 'INV-204: la couverture d''une situation ne se modifie jamais');
END;

CREATE TRIGGER tr_105_situation_devis_delete
BEFORE DELETE ON situation_devis
BEGIN
    SELECT RAISE(ABORT, 'INV-204: la couverture d''une situation ne se supprime jamais');
END;


-- =====================================================================
-- 2. Facturation — triggers recréés (même nom, même numéro TR-22)
-- Contractuel d'un BC = Σ total_ht des devis rattachés (bc_devis), comme en 006.
-- Facturation nette d'un BC = Σ acomptes + Σ situations + Σ soldes − Σ avoirs.
-- Tous les calculs sont en centimes entiers.
-- =====================================================================
DROP TRIGGER tr_22_factures_acompte;
DROP TRIGGER tr_22_factures_situation;
DROP TRIGGER tr_22_factures_solde;
DROP TRIGGER tr_23_factures_avoir;

-- TR-22 [INV-52, INV-57, INV-58, INV-189, INV-205] : acompte. Le devis d'origine est
-- rattaché au BC de la facture ; aucun solde n'existe sur le BC (même totalement
-- crédité) ; un seul acompte actif par devis ; le total ne dépasse pas l'acompte
-- PRÉVU du devis (aucun : plafond nul, donc aucune facture d'acompte ; pourcentage :
-- arrondi HALF_UP du total_ht du devis × pourcentage ; montant : la valeur
-- saisie) ni le total du devis, ni, avec la facturation nette avant, le contractuel
-- du BC. Un acompte prévu à 100 % du marché est donc admis jusqu'à ce total, sans
-- confirmation particulière. La facturation de l'acompte reste facultative : aucun
-- trigger n'exige un acompte avant une situation ou un solde.
CREATE TRIGGER tr_22_factures_acompte
BEFORE INSERT ON factures
WHEN NEW.type = 'acompte'
BEGIN
    SELECT RAISE(ABORT, 'INV-189: le devis de l''acompte doit etre rattache au bon de commande de la facture')
     WHERE NOT EXISTS (SELECT 1 FROM bc_devis l WHERE l.bc_id = NEW.bc_id AND l.devis_id = NEW.devis_id);
    SELECT RAISE(ABORT, 'INV-58: aucun acompte apres un solde')
     WHERE EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = NEW.bc_id AND s.type = 'solde');
    -- Ordre des factures (V3.14, D-62, INV-205) : aucun acompte sur un devis COUVERT par
    -- une situation, c'est-à-dire présent dans situation_devis. La couverture est
    -- enregistrée à l'émission de la situation (tous les devis alors rattachés au BC) ;
    -- un devis rattaché ensuite n'est couvert par aucune situation antérieure, son
    -- acompte reste possible. La garde ne lit ni les avoirs (une situation déjà créditée,
    -- même totalement, reste émise et couvre toujours ses devis), ni le montant net, ni
    -- le pourcentage, ni aucun horodatage, et n'emploie pas l'état dérivé « neutralisée ».
    -- L'acompte reste facultatif et un acompte émis AVANT la situation reste valide.
    SELECT RAISE(ABORT, 'INV-205: aucun acompte sur un devis deja couvert par une situation')
     WHERE EXISTS (SELECT 1 FROM situation_devis c WHERE c.devis_id = NEW.devis_id);
    SELECT RAISE(ABORT, 'INV-52: un seul acompte actif par devis')
     WHERE EXISTS (SELECT 1 FROM factures a
                    WHERE a.devis_id = NEW.devis_id
                      AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)
                             FROM factures av WHERE av.origine_facture_id = a.id)
                          <> CAST(REPLACE(a.total_ht, '.', '') AS INTEGER));
    SELECT RAISE(ABORT, 'INV-57: un acompte ne depasse pas l''acompte prevu de son devis (aucun acompte prevu : aucune facture d''acompte)')
     WHERE CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER)
         > (SELECT CASE d.acompte_type
                     WHEN 'aucun'   THEN 0
                     WHEN 'montant' THEN CAST(REPLACE(d.acompte_valeur, '.', '') AS INTEGER)
                     ELSE (CAST(REPLACE(d.total_ht, '.', '') AS INTEGER) * CAST(REPLACE(d.acompte_valeur, '.', '') AS INTEGER) + 5000) / 10000
                   END
              FROM devis d WHERE d.id = NEW.devis_id);
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

-- TR-22 [INV-57, INV-58, INV-190] : situation (inchangé par V3.14 : la couverture est écrite par le service après l'INSERT de la facture). Aucun solde n'existe sur le BC
-- (même totalement crédité) ; montant_deja_facture_ht est exactement la
-- facturation nette du BC avant la situation ; la facturation nette après la
-- situation reste STRICTEMENT inférieure au contractuel : une situation ne porte
-- jamais le cumul à 100 % du marché. Le montant (X - N, strictement positif) et
-- les lignes sont une règle de service.
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
    SELECT RAISE(ABORT, 'INV-57: une situation ne porte jamais la facturation nette a 100 % du contractuel du bon de commande')
     WHERE (SELECT COALESCE(SUM(CASE WHEN f.type = 'avoir' THEN -CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                                     ELSE CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) END), 0)
              FROM factures f WHERE f.bc_id = NEW.bc_id)
           + CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER)
         >= (SELECT COALESCE(SUM(CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)), 0)
               FROM bc_devis l JOIN devis d ON d.id = l.devis_id WHERE l.bc_id = NEW.bc_id);
END;

-- TR-22 [INV-52, INV-55, INV-58] : solde. Aucun solde actif sur le BC (un solde à
-- 0.00 historique n'est jamais neutralisé) ; le total est STRICTEMENT positif :
-- aucun solde à 0.00 n'est émis ; total_ht = contractuel du BC - facturation nette
-- avant, exactement, où le contractuel FINAL = Σ total_ht des devis rattachés moins
-- Σ des avoirs « prestation_non_realisee » dont l'origine est un solde du BC (les
-- sommes de ces avoirs ne sont jamais refacturables, INV-58 ; un avoir
-- « correction_erreur » ou un avoir sur situation ne réduit rien). Lorsque la
-- facturation nette atteint déjà le contractuel final, le reste à facturer est nul
-- et aucun solde ne peut être émis. Après un solde totalement crédité par un avoir
-- de correction, un nouveau solde est possible ; il ne l'est pas pour la part
-- créditée au titre de prestations non réalisées. Aucun acompte préalable n'est
-- exigé. Le contractuel COURANT (réductions) n'est pas lu : voir « Hors périmètre ».
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
    SELECT RAISE(ABORT, 'INV-55: un solde est strictement positif, aucun solde a 0.00 n''est emis')
     WHERE NEW.total_ht = '0.00';
    SELECT RAISE(ABORT, 'INV-58: le solde est le contractuel final du bon de commande (moins les avoirs prestations non realisees sur solde) moins la facturation nette avant le solde')
     WHERE CAST(REPLACE(NEW.total_ht, '.', '') AS INTEGER) IS NOT
           (SELECT COALESCE(SUM(CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)), 0)
              FROM bc_devis l JOIN devis d ON d.id = l.devis_id WHERE l.bc_id = NEW.bc_id)
         - (SELECT COALESCE(SUM(CAST(REPLACE(a.total_ht, '.', '') AS INTEGER)), 0)
              FROM factures a JOIN factures o ON o.id = a.origine_facture_id
             WHERE a.bc_id = NEW.bc_id AND a.type = 'avoir'
               AND a.motif_avoir = 'prestation_non_realisee' AND o.type = 'solde')
         - (SELECT COALESCE(SUM(CASE WHEN f.type = 'avoir' THEN -CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                                     ELSE CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) END), 0)
              FROM factures f WHERE f.bc_id = NEW.bc_id);
END;


-- TR-23 [INV-58, INV-76] : avoir. Contrôles de 006 conservés (l'origine n'est pas un
-- avoir ; même bon de commande ; Σ des avoirs <= total de l'origine) ; s'y ajoutent,
-- pour tout NOUVEL avoir : le motif appartient à la liste fermée (correction_erreur |
-- prestation_non_realisee) ; un avoir sur un acompte ne corrige qu'une erreur de
-- l'acompte (jamais une moins-value, un abandon ou un marché inférieur à l'acompte).
-- Un motif absent reste refusé par le CHECK de factures. Les avoirs existants ne
-- sont pas relus.
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
    SELECT RAISE(ABORT, 'INV-76: le motif d''un avoir est correction_erreur ou prestation_non_realisee')
     WHERE NEW.motif_avoir IS NOT NULL
       AND NEW.motif_avoir NOT IN ('correction_erreur', 'prestation_non_realisee');
    SELECT RAISE(ABORT, 'INV-76: un avoir sur un acompte ne corrige qu''une erreur de l''acompte')
     WHERE NEW.motif_avoir = 'prestation_non_realisee'
       AND EXISTS (SELECT 1 FROM factures o WHERE o.id = NEW.origine_facture_id AND o.type = 'acompte');
END;


-- =====================================================================
-- 3. garanties (§4.10) — reconstruction : facture_declenchement_id nullable
-- Un déclenchement manuel n'est lié à aucune facture. La colonne est conservée
-- (historique des garanties créées au premier solde sous la règle antérieure) ;
-- son retrait éventuel est À CONCEVOIR. Aucun autre changement de structure :
-- mêmes colonnes, mêmes CHECK, même UNIQUE(bc_ligne_id, garantie_type).
-- Étape 4 : aucun trigger posé sur une autre table ne référence garanties ; les
-- triggers de garanties disparaissent avec la table.
-- =====================================================================
CREATE TABLE garanties_new (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    bc_id                    INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    bc_ligne_id              INTEGER NOT NULL REFERENCES bc_lignes (id) ON DELETE RESTRICT,
    garantie_type            TEXT    NOT NULL CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale')),
    date_declenchement       TEXT    NOT NULL
                             CHECK (date_declenchement GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_declenchement) IS date_declenchement),
    date_fin_suivi           TEXT    NOT NULL
                             CHECK (date_fin_suivi GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_fin_suivi) IS date_fin_suivi),
    facture_declenchement_id INTEGER REFERENCES factures (id) ON DELETE RESTRICT,
    created_at               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (bc_ligne_id, garantie_type),
    CHECK (date_fin_suivi > date_declenchement),
    CHECK (date_fin_suivi = printf('%04d', CAST(substr(date_declenchement, 1, 4) AS INTEGER)
                                         + CASE garantie_type WHEN 'parfait_achevement' THEN 1 WHEN 'biennale' THEN 2 ELSE 10 END)
                            || CASE WHEN substr(date_declenchement, 6, 5) = '02-29' THEN '-02-28' ELSE substr(date_declenchement, 5) END),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

INSERT INTO garanties_new (id, bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id, created_at)
SELECT id, bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id, created_at
  FROM garanties
 ORDER BY id;

-- sqlite_sequence : la nouvelle valeur est >= à l'ancienne (INV-04, étape 7)
UPDATE sqlite_sequence
   SET seq = max(seq, COALESCE((SELECT seq FROM sqlite_sequence WHERE name = 'garanties'), 0))
 WHERE name = 'garanties_new';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'garanties_new', seq FROM sqlite_sequence
 WHERE name = 'garanties'
   AND NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = 'garanties_new');

DROP TABLE garanties;
ALTER TABLE garanties_new RENAME TO garanties;

CREATE INDEX idx_garanties_bc_id                    ON garanties (bc_id);
CREATE INDEX idx_garanties_facture_declenchement_id ON garanties (facture_declenchement_id);
CREATE INDEX idx_garanties_date_fin_suivi           ON garanties (date_fin_suivi);


-- =====================================================================
-- 4. bc_ligne_retraits_garantie (§4.10) — prestation retirée du périmètre
-- contractuel des garanties. Append-only : jamais modifiée ni supprimée.
--   * UNIQUE(bc_ligne_id) : une prestation n'est retirée qu'une fois (aucun double
--     retrait, quelle qu'en soit la cause) ; l'index couvre la FK ;
--   * motif_retrait : 'moins_value' (moins-value acceptée, écrite par le service ;
--     aucune table de réductions n'existe encore) ou
--     'avoir_prestation_non_realisee' (avoir pour prestations non réalisées émis
--     sur une facture de solde : avoir_id obligatoire) ; un avoir d'erreur ou un
--     avoir sur situation ne retire jamais la prestation ;
--   * date_retrait : jour d'effet du retrait, saisi par le service ;
--   * une garantie est ACTIVE tant que sa ligne de BC n'a pas de retrait (état
--     dérivé) ; les garanties des autres prestations restent inchangées.
-- =====================================================================
CREATE TABLE bc_ligne_retraits_garantie (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    bc_id         INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    bc_ligne_id   INTEGER NOT NULL UNIQUE REFERENCES bc_lignes (id) ON DELETE RESTRICT,
    motif_retrait TEXT    NOT NULL CHECK (motif_retrait IN ('moins_value', 'avoir_prestation_non_realisee')),
    avoir_id      INTEGER REFERENCES factures (id) ON DELETE RESTRICT,
    date_retrait  TEXT    NOT NULL
                  CHECK (date_retrait GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_retrait) IS date_retrait),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK ((motif_retrait = 'avoir_prestation_non_realisee') = (avoir_id IS NOT NULL)),
    CHECK (created_at GLOB
        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

CREATE INDEX idx_bc_ligne_retraits_garantie_bc_id    ON bc_ligne_retraits_garantie (bc_id);
CREATE INDEX idx_bc_ligne_retraits_garantie_avoir_id ON bc_ligne_retraits_garantie (avoir_id);


-- =====================================================================
-- Triggers (§8) — ils ne font que garder : aucun ne modifie de donnée.
-- Un parent inexistant n'est jamais traité en tant que tel : c'est la FK qui
-- refuse. Aucune exemption d'origine (INV-131).
-- =====================================================================

-- TR-50 [INV-87] : une garantie ne se modifie jamais, même par une écriture sans
-- effet (recréé à l'identique de 008).
CREATE TRIGGER tr_50_garanties_update
BEFORE UPDATE ON garanties
BEGIN
    SELECT RAISE(ABORT, 'INV-87: une garantie ne se modifie jamais');
END;

-- TR-50 [INV-87, INV-06] : une garantie ne se supprime jamais (recréé à l'identique
-- de 008). Le retrait d'une prestation passe par bc_ligne_retraits_garantie.
CREATE TRIGGER tr_50_garanties_no_delete
BEFORE DELETE ON garanties
BEGIN
    SELECT RAISE(ABORT, 'INV-87: une garantie ne se supprime jamais');
END;

-- TR-50 [INV-87] : un retrait de prestation ne se modifie ni ne se supprime jamais.
CREATE TRIGGER tr_50_bc_ligne_retraits_garantie_update
BEFORE UPDATE ON bc_ligne_retraits_garantie
BEGIN
    SELECT RAISE(ABORT, 'INV-87: un retrait de prestation du perimetre des garanties ne se modifie jamais');
END;

CREATE TRIGGER tr_50_bc_ligne_retraits_garantie_no_delete
BEFORE DELETE ON bc_ligne_retraits_garantie
BEGIN
    SELECT RAISE(ABORT, 'INV-87: un retrait de prestation du perimetre des garanties ne se supprime jamais');
END;

-- TR-51 [INV-85, INV-86, INV-87, INV-90, INV-134] : gardes d'insertion d'une
-- garantie (G1 à G5). Le déclenchement est MANUEL : aucune garde ne lit un solde,
-- l'état du BC, un règlement ou un avoir ; G2 et G4 ne s'appliquent que si une
-- facture est renseignée (historique de l'ancienne règle).
CREATE TRIGGER tr_51_garanties_insert
BEFORE INSERT ON garanties
BEGIN
    -- G1 : la ligne existe et appartient au BC de la garantie.
    SELECT RAISE(ABORT, 'INV-90: la ligne de BC doit appartenir au bon de commande de la garantie')
     WHERE NOT EXISTS (SELECT 1 FROM bc_lignes l WHERE l.id = NEW.bc_ligne_id AND l.bc_id = NEW.bc_id);
    -- G2 : si une facture est renseignée, c'est un solde du même BC.
    SELECT RAISE(ABORT, 'INV-85: la facture de declenchement, si elle est renseignee, doit etre un solde du bon de commande')
     WHERE NEW.facture_declenchement_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM factures f WHERE f.id = NEW.facture_declenchement_id AND f.bc_id = NEW.bc_id AND f.type = 'solde');
    -- G3 : le couple (ligne, type) existe dans bc_ligne_garanties ; rend impossible
    -- toute garantie sur un BC importé (aucune garantie de ligne).
    SELECT RAISE(ABORT, 'INV-86: la garantie doit exister parmi les garanties de la ligne de BC')
     WHERE NOT EXISTS (SELECT 1 FROM bc_ligne_garanties g WHERE g.ligne_id = NEW.bc_ligne_id AND g.garantie_type IS NEW.garantie_type);
    -- G4 : si une facture est renseignée, la date de déclenchement est sa date d'émission.
    SELECT RAISE(ABORT, 'INV-87: la date de declenchement est la date d''emission de la facture de declenchement')
     WHERE NEW.facture_declenchement_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM factures f WHERE f.id = NEW.facture_declenchement_id AND f.date_emission IS NEW.date_declenchement);
    -- G5 : une prestation retirée du périmètre contractuel ne peut plus être déclenchée.
    SELECT RAISE(ABORT, 'INV-85: la prestation a ete retiree du perimetre contractuel des garanties')
     WHERE EXISTS (SELECT 1 FROM bc_ligne_retraits_garantie r WHERE r.bc_ligne_id = NEW.bc_ligne_id);
END;

-- TR-51 [INV-76, INV-85, INV-90] : gardes d'insertion d'un retrait de prestation.
-- R1 : la ligne de BC appartient au BC du retrait.
-- R2 : motif « avoir » : l'avoir est un avoir du même BC, de motif
--      'prestation_non_realisee', émis sur une facture de type SOLDE ; un avoir
--      d'erreur ou un avoir sur situation ou acompte ne retire aucune prestation.
-- R3 : motif « avoir » : une ligne de l'avoir référence la ligne de BC retirée.
-- Le motif « moins_value » n'a pas de source en base (PT-12) : il est écrit par le
-- service après acceptation d'une moins-value totale de la prestation.
CREATE TRIGGER tr_51_bc_ligne_retraits_garantie_insert
BEFORE INSERT ON bc_ligne_retraits_garantie
BEGIN
    SELECT RAISE(ABORT, 'INV-90: la ligne de BC doit appartenir au bon de commande du retrait')
     WHERE NOT EXISTS (SELECT 1 FROM bc_lignes l WHERE l.id = NEW.bc_ligne_id AND l.bc_id = NEW.bc_id);
    SELECT RAISE(ABORT, 'INV-76: seul un avoir pour prestations non realisees emis sur un solde du meme bon de commande retire une prestation')
     WHERE NEW.avoir_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM factures a JOIN factures o ON o.id = a.origine_facture_id
                        WHERE a.id = NEW.avoir_id
                          AND a.type = 'avoir'
                          AND a.motif_avoir = 'prestation_non_realisee'
                          AND a.bc_id = NEW.bc_id
                          AND o.type = 'solde');
    SELECT RAISE(ABORT, 'INV-76: une ligne de l''avoir doit referencer la prestation retiree')
     WHERE NEW.avoir_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM facture_lignes fl WHERE fl.facture_id = NEW.avoir_id AND fl.bc_ligne_id = NEW.bc_ligne_id);
END;


-- =====================================================================
-- Suivi ACTIF des garanties (décision 3.3) — vue de lecture, sans donnée propre.
-- Une garantie déclenchée est en suivi actif tant que sa ligne de BC (prestation)
-- ne figure pas dans bc_ligne_retraits_garantie. Un retrait ne touche que la ligne
-- de sa prestation : les autres garanties restent actives ; la garantie retirée
-- n'est ni modifiée ni supprimée (elle reste dans garanties : historique).
-- =====================================================================
CREATE VIEW v_garanties_suivi_actif AS
SELECT g.id, g.bc_id, g.bc_ligne_id, g.garantie_type, g.date_declenchement,
       g.date_fin_suivi, g.facture_declenchement_id, g.created_at
  FROM garanties g
 WHERE NOT EXISTS (SELECT 1 FROM bc_ligne_retraits_garantie r WHERE r.bc_ligne_id = g.bc_ligne_id);
