-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration corrective 009a_bc_annulation_interdite_si_facture
-- Corrective (rang 13, D-55) : un bon de commande ne peut passer à 'annule' que si
-- chacune de ses factures (acompte, situation, solde) a été ramenée à un montant NET
-- nul par des avoirs. Ce n'est PAS une tranche métier : elle ne consomme aucun numéro de
-- tranche (conventions techniques §5, V-2). Son préfixe 009 est celui de la dernière
-- tranche exécutée avant elle. Rang 13 proposé le 2026-10-13. Révision G (2026-10-17) :
-- la corrective 009b_acompte_garanties_manuelles prend le rang 14, la tranche suivante
-- (010) passe au rang 15 et la suivante (011) au rang 16 ; ces tranches ne sont pas
-- livrées, aucune migration livrée n'est déplacée ni renommée. Règle précisée par le
-- propriétaire du produit le 2026-10-17 (14:34) : elle remplace la règle stricte du
-- 2026-10-13 (« interdite dès qu'une facture existe, un avoir total ne rétablit jamais le
-- droit »). Le trigger de la proposition du 2026-10-13 n'est donc plus repris à l'identique.
--
-- Référence : D-05 (validée 2026-09-29), INV-44, errata E-07, scénario C-19 ;
-- modèle de données SQLite ; D-55 et D-56 (chaîne ordonnée, correctives) ;
-- conventions techniques §5. Invariants liés : INV-06 et INV-53 (une facture ne se
-- modifie ni ne se supprime : tr_20, tr_21), INV-173 (BC annulé terminal), INV-188
-- (un BC annulé ne reçoit ni acompte, ni situation, ni solde).
--
-- Règle appliquée (validée par le propriétaire du produit le 2026-10-17) :
--   * un BC sans aucune facture peut être annulé ;
--   * un acompte PRÉVU au devis (devis.acompte_type / acompte_valeur : donnée
--     commerciale prévisionnelle) n'est pas une facture et ne bloque pas ;
--   * un BC portant des factures ne peut être annulé que si CHACUNE a un montant net
--     nul : net = total_ht de la facture (acompte, situation ou solde) moins la somme
--     des total_ht des avoirs dont origine_facture_id est cette facture. Une seule
--     facture à net non nul (aucun avoir, avoir partiel) suffit à refuser ;
--   * une facture non réglée ne s'ignore pas : le règlement n'est PAS le critère (aucune
--     table de règlements n'est lue) ; une facture réglée mais non créditée bloque autant
--     qu'une facture impayée ;
--   * un avoir n'est pas une facture à contrôler : il est le moyen de ramener la facture
--     d'origine à zéro. Les factures et les avoirs restent en base (tr_20, tr_21) : le
--     trigger ne lit, ne crée, ne modifie ni ne supprime aucune ligne ;
--   * une tentative d'émission refusée ou défaite par ROLLBACK ne laisse aucune ligne
--     dans factures : elle ne bloque pas ;
--   * un BC déjà annulé n'est pas concerné : tr_12_bons_commande_annule (INV-173),
--     tr_16_factures_bc (avoir encore possible, INV-188) et les évolutions
--     autorisées par la corrective 005c (D-56) restent inchangés.
-- L'exception « acompte non réglé » de D-05 / INV-44 n'est pas reprise : elle
-- supposait l'annulation d'une facture dans la même transaction, que 006 a rendue
-- impossible (aucun UPDATE, aucun cancelled_at : tr_20) ; la voie d'annulation d'une
-- facture est l'avoir. Aucun import de BC annulé n'est prévu : la migration ne crée
-- aucune exception à ce titre.
--
-- Objet unique : CREATE TRIGGER tr_103_bons_commande_annulation_facturee (BEFORE
-- UPDATE ON bons_commande). Identifiant : TR-103, premier numéro libre (le plus grand
-- numéro posé par les migrations, ou cité par les documents, est 102) ; il est à
-- inscrire dans le tableau des triggers du modèle de données.
--   * événement : toute modification de bons_commande ; le trigger ne s'exécute que
--     pour la transition d'un statut différent de 'annule' vers 'annule' ; il est
--     BEFORE : il s'exécute avant les CHECK de la ligne et avant toute écriture, donc
--     avant la modification du statut (RAISE(ABORT) défait l'instruction ; la
--     transaction englobante reste ouverte et cohérente, son ROLLBACK appartient au
--     service) ;
--   * condition : il existe une ligne de factures de ce BC, de type différent de
--     'avoir', dont le total_ht (en centimes) diffère de la somme des total_ht des avoirs
--     qui la référencent (origine_facture_id). Le test porte sur les factures et les
--     avoirs eux-mêmes, jamais sur un cache financier du BC (montant_deja_facture_ht,
--     avancement, date_100_facture), ni sur un règlement, ni sur l'état dérivé
--     « neutralisée » ;
--   * les factures et les avoirs ne se modifient ni ne se suppriment (tr_20, tr_21) :
--     le contrôle ne se contourne pas en déplaçant ou en retirant une facture ;
--   * le préfixe de message INV-44 est celui de l'invariant (docs/).
-- Le trigger ne s'applique pas aux lignes déjà annulées avant cette migration : aucune
-- donnée n'est lue, créée, modifiée ni corrigée. Un BC annulé et facturé avant 009a
-- reste tel quel ; une requête de détection est proposée dans les tests, hors schéma.
--
-- Aucune table, aucun index, aucun CHECK, aucun autre trigger n'est créé, modifié ou
-- supprimé ; aucune reconstruction de table : le protocole foreign_keys = OFF n'est
-- pas requis. Toute reconstruction future de bons_commande devra recréer ce trigger à
-- l'identique (conventions §5, protocole de reconstruction) ; le test de garde de
-- chaîne de test_009a le vérifie. Le fichier ne contient ni BEGIN/COMMIT ni PRAGMA :
-- le runner l'exécute dans une transaction (BEGIN IMMEDIATE), pose
-- PRAGMA user_version = 13 avant le COMMIT, et un échec entraîne le ROLLBACK
-- intégral (D-55).
-- =====================================================================

-- INV-44 [D-05] : annulation directe du BC refusée tant qu'une de ses factures
-- (acompte, situation, solde) conserve un montant net non nul après avoirs.
CREATE TRIGGER tr_103_bons_commande_annulation_facturee
BEFORE UPDATE ON bons_commande
WHEN NEW.statut = 'annule' AND OLD.statut <> 'annule'
 AND EXISTS (SELECT 1 FROM factures f
              WHERE f.bc_id = OLD.id
                AND f.type <> 'avoir'
                AND CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)
                    <> (SELECT COALESCE(SUM(CAST(REPLACE(a.total_ht, '.', '') AS INTEGER)), 0)
                          FROM factures a
                         WHERE a.type = 'avoir' AND a.origine_facture_id = f.id))
BEGIN
    SELECT RAISE(ABORT, 'INV-44: annulation du bon de commande interdite, au moins une facture conserve un montant net non nul apres avoirs (D-05)');
END;
