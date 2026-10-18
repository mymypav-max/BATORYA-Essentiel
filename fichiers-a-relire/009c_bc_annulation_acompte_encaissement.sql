-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration corrective 009c_bc_annulation_acompte_encaissement
-- Corrective (rang 15, D-63) : l'annulation directe d'un bon de commande (INV-44) est
-- alignée sur les décisions du propriétaire du produit du 2026-10-18. Ce n'est PAS une
-- tranche métier : elle ne consomme aucun numéro de tranche (conventions techniques §5,
-- migration corrective, décision V-2). Son préfixe 009 est celui de la dernière tranche
-- exécutée avant elle. Rang 15 (arbitrage A du 2026-10-18) : les tranches suivantes
-- (010, 011) passent aux rangs 16 et 17 ; elles ne sont pas livrées, aucune migration
-- livrée n'est déplacée, renommée ni réécrite (009a et 009b restent inchangées).
--
-- Référence : modèle de données SQLite V3.14 — §8 (TR-103), §15 (D-63), §17.1 (suivi des
-- migrations, test T-54) ; D-05 (validée 2026-09-29), INV-44, errata E-07, scénario C-19 ;
-- conventions techniques §5. Invariants liés : INV-06 et INV-53 (une facture ne se
-- modifie ni ne se supprime : tr_20, tr_21), INV-173 (BC annulé terminal), INV-188 (un BC
-- annulé ne reçoit ni acompte, ni situation, ni solde ; un avoir reste possible), INV-76
-- (motif d'avoir, tr_23 de 009b), INV-72 (reste dû, TR-31 de 007).
--
-- Ce que remplace cette migration : la règle de 009a (« chaque facture a un montant net
-- nul après avoirs ») laissait annuler un BC dont la situation ou le solde était
-- intégralement crédité, et ne lisait aucun règlement. Elle est remplacée par la règle
-- ci-dessous. Le trigger garde son nom et son numéro (tr_103_bons_commande_annulation_facturee,
-- TR-103) : il est supprimé puis recréé (DROP TRIGGER / CREATE TRIGGER, même nom), comme
-- 005c l'a fait pour tr_12 et 009b pour tr_22 et tr_23.
--
-- Règle appliquée (décisions du propriétaire du produit du 2026-10-18). Le passage d'un BC
-- à 'annule' est refusé si au moins une des conditions suivantes est vraie :
--   1. un encaissement ACTIF existe sur une facture du BC : règlement de type
--      'encaissement' dont cancelled_at est NULL. Il bloque même si la facture a été
--      intégralement neutralisée par des avoirs. Un encaissement annulé (cancelled_at
--      renseigné, y compris un encaissement importé déjà annulé) ne bloque pas. Un
--      remboursement n'est pas un encaissement. Les règlements d'un autre BC sont sans effet
--      (le lien passe par factures.bc_id) ;
--   2. une facture de type 'situation' existe pour ce BC, même annulée, neutralisée ou
--      intégralement créditée par des avoirs ;
--   3. une facture autre qu'un acompte (et qu'un avoir) existe pour ce BC, notamment un
--      solde (D-05 / E-07), même si son net après avoirs est nul ;
--   4. un acompte du BC n'est pas intégralement neutralisé par un avoir de motif
--      'correction_erreur' : son total_ht diffère de la somme des total_ht des avoirs qui
--      le référencent, ou l'un de ces avoirs porte un autre motif.
-- Exception validée (option A) : un acompte NON RÉGLÉ (aucun encaissement actif, condition 1)
-- peut être neutralisé par un avoir total de motif 'correction_erreur', puis le BC peut être
-- annulé, ces opérations étant réalisées dans la même transaction. Cette autorisation ne
-- concerne que l'annulation d'un BC : elle n'étend pas l'usage de 'correction_erreur'
-- (tr_23 de 009b continue de n'accepter que ce motif sur un acompte).
--
-- Un avoir n'est jamais une facture à contrôler : il est le moyen de neutraliser l'acompte.
-- Un acompte PRÉVU au devis (devis.acompte_type / acompte_valeur) n'est pas une facture et
-- ne bloque pas. Un BC sans aucune facture peut être annulé. Un BC déjà annulé n'est pas
-- concerné (tr_12_bons_commande_annule, INV-173).
--
-- Ordre et atomicité. Le trigger lit l'ÉTAT au moment de l'UPDATE du BC (BEFORE UPDATE) : il
-- exige que l'avoir existe déjà. L'ordre inverse (annuler le BC, puis neutraliser
-- l'acompte) est donc refusé, quel que soit le service appelant. SQLite ne peut pas imposer
-- que l'avoir et l'annulation appartiennent à la même transaction : cette atomicité est la
-- responsabilité du service d'annulation (une seule transaction BEGIN IMMEDIATE : avoir
-- puis UPDATE du BC ; COMMIT, ou ROLLBACK de l'ensemble si l'un des deux est refusé), et
-- les tests la vérifient avec l'émulation du runner. Aucun service applicatif n'existe dans
-- le dépôt à ce jour. Si le service commit l'avoir sans annuler le BC, la base reste
-- cohérente : l'acompte est neutralisé, le BC reste 'en_cours', l'annulation reste à faire
-- ou le BC reste exploitable (un nouvel acompte redevient possible, INV-52).
--
-- Objet unique : le trigger tr_103_bons_commande_annulation_facturee (BEFORE UPDATE ON
-- bons_commande), recréé. Il ne s'exécute que pour la transition d'un statut différent de
-- 'annule' vers 'annule' ; il ne lit, ne crée, ne modifie ni ne supprime aucune ligne ; il
-- ne lit aucun cache financier du BC (montant_deja_facture_ht, avancement, date_100_facture)
-- ni l'état dérivé « neutralisée ». Il lit factures et reglements. Quatre RAISE(ABORT)
-- distincts, tous préfixés INV-44, évalués dans l'ordre des conditions 1 à 4 ci-dessus.
--
-- Aucune table, aucun index, aucun CHECK, aucun autre trigger n'est créé, modifié ou
-- supprimé ; aucune reconstruction de table : le protocole foreign_keys = OFF n'est pas
-- requis. Les données ne sont ni lues ni modifiées : un BC annulé et facturé avant cette
-- migration reste tel quel. Une garde d'exécution (lecture seule) exige user_version = 14 :
-- 009c ne s'applique qu'à une base arrêtée à 009b. Le fichier ne contient ni BEGIN/COMMIT ni
-- PRAGMA : le runner l'exécute dans une transaction (BEGIN IMMEDIATE), pose
-- PRAGMA user_version = 15 avant le COMMIT, et un échec entraîne le ROLLBACK intégral.
-- Toute reconstruction future de bons_commande devra recréer ce trigger à l'identique
-- (conventions §5, protocole de reconstruction).
--
-- Limite assumée : un avoir sur un acompte émis AVANT 009b avec un autre motif que
-- 'correction_erreur' (le motif était libre sous 006) ne vaut pas neutralisation au sens de
-- la condition 4 ; l'acompte concerné interdit alors l'annulation du BC.
--
-- Conventions : les montants sont comparés en centimes entiers :
-- CAST(REPLACE(x, '.', '') AS INTEGER). Le trigger est BEFORE : il s'exécute avant les
-- CHECK de la ligne. Messages en ASCII.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Garde d'exécution (lecture seule, aucune trace) : user_version doit valoir 14 (009c est
-- le rang 15 et ne s'applique qu'à une base arrêtée à 009b). Table temporaire supprimée
-- aussitôt ; échec = erreur de CHECK, donc ROLLBACK.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE garde_009c_user_version (
    user_version INTEGER NOT NULL
        CONSTRAINT "009c exige user_version = 14 (chaine 009b -> 009c)" CHECK (user_version = 14)
);
INSERT INTO garde_009c_user_version (user_version) SELECT user_version FROM pragma_user_version;
DROP TABLE garde_009c_user_version;


-- INV-44 [D-05, D-63] : annulation directe du BC refusée en présence d'un encaissement
-- actif, d'une situation, d'une facture autre qu'un acompte, ou d'un acompte non
-- intégralement neutralisé par un avoir correction_erreur.
DROP TRIGGER tr_103_bons_commande_annulation_facturee;

CREATE TRIGGER tr_103_bons_commande_annulation_facturee
BEFORE UPDATE ON bons_commande
WHEN NEW.statut = 'annule' AND OLD.statut <> 'annule'
BEGIN
    SELECT RAISE(ABORT, 'INV-44: annulation du bon de commande interdite, un encaissement actif existe sur une facture du bon de commande')
     WHERE EXISTS (SELECT 1
                     FROM reglements r JOIN factures f ON f.id = r.facture_id
                    WHERE f.bc_id = OLD.id
                      AND r.type = 'encaissement' AND r.cancelled_at IS NULL);
    SELECT RAISE(ABORT, 'INV-44: annulation du bon de commande interdite, une situation a ete emise (meme annulee ou creditee)')
     WHERE EXISTS (SELECT 1 FROM factures f WHERE f.bc_id = OLD.id AND f.type = 'situation');
    SELECT RAISE(ABORT, 'INV-44: annulation du bon de commande interdite, une facture autre qu''un acompte existe (D-05)')
     WHERE EXISTS (SELECT 1 FROM factures f WHERE f.bc_id = OLD.id AND f.type NOT IN ('acompte', 'avoir'));
    SELECT RAISE(ABORT, 'INV-44: annulation du bon de commande interdite, un acompte n''est pas integralement neutralise par un avoir correction_erreur')
     WHERE EXISTS (SELECT 1 FROM factures f
                    WHERE f.bc_id = OLD.id AND f.type = 'acompte'
                      AND (CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                           <> (SELECT COALESCE(SUM(CAST(REPLACE(a.total_ht, '.', '') AS INTEGER)), 0)
                                 FROM factures a
                                WHERE a.type = 'avoir' AND a.origine_facture_id = f.id)
                           OR EXISTS (SELECT 1 FROM factures a
                                       WHERE a.type = 'avoir' AND a.origine_facture_id = f.id
                                         AND a.motif_avoir IS NOT 'correction_erreur')));
END;
