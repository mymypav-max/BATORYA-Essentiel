-- =====================================================================
-- BATORYA Essentiel V6 — base métier — migration corrective 005c_bc_annule_caches_financiers
-- Corrective (rang 8, D-56) : un bon de commande annulé continue de recevoir
-- les recalculs de ses caches financiers dérivés. Ce n'est PAS une tranche
-- métier : elle ne consomme aucun numéro de tranche (conventions techniques §5,
-- V-2) ; 006 passe au rang 9.
--
-- Référence : modèle de données SQLite V3.13 — §4.19 (ligne 12), §7.2 (BC
-- annulé), §8 (TR-12), §17.1 (ligne 005c), D-56, PT-16 (volet TR-12) ;
-- conventions techniques §5 (chaîne ordonnée, « Transaction et user_version »).
-- Invariants : INV-46, INV-164, INV-173, INV-188.
--
-- Objet unique : remplacer tr_12_bons_commande_annule (créé en 004, recréé en
-- 005a puis en 005b). 005b l'avait laissé à « seul updated_at est modifiable »
-- (PT-16 reporté) ; INV-173 et INV-188 autorisent pourtant les opérations de
-- correction de documents existants (avoirs), qui font évoluer les caches.
--   * retirés de la liste des colonnes gardées (3) : montant_deja_facture_ht,
--     avancement, date_100_facture — caches financiers dérivés ;
--   * conservées (22) : id, client_id, snapshots et versions (6), date_acceptation,
--     date_debut, date_fin, montant_contractuel_ht, statut, completed_at,
--     cancelled_at, motif_annulation, frozen_at, created_at, origine, legacy_id,
--     legacy_data, legacy_numero ; numero et date_creation restent gardés par
--     tr_01 (INV-23) et updated_at est libre ;
--   * événement, condition (OLD.statut = 'annule'), nom et préfixe de message
--     (INV-173) inchangés ; le texte du message ne dit plus que updated_at est le
--     seul champ modifiable.
-- Les CHECK de bons_commande restent actifs et imposent que avancement et
-- date_100_facture changent ensemble (date_100_facture => avancement = 100.00 et
-- frozen_at non NULL ; termine => date_100_facture ; statut / completed_at /
-- cancelled_at cohérents). Le sens et la légitimité d'un recalcul relèvent du
-- service financier (INV-46) et du contrôle CK-06, pas de ce fichier.
--
-- Aucune table, aucun index, aucun autre trigger, aucun CHECK, aucun CK n'est
-- créé, modifié ou supprimé ; tr_14 (frozen_at) est inchangé. Aucune donnée.
-- Aucune reconstruction de table : le protocole foreign_keys = OFF n'est pas
-- requis. Le fichier ne contient ni BEGIN/COMMIT ni PRAGMA : le runner l'exécute
-- dans une transaction (BEGIN IMMEDIATE), pose PRAGMA user_version = 8 avant le
-- COMMIT, et un échec entraîne le ROLLBACK intégral (D-55).
-- =====================================================================

-- TR-12 [INV-173, INV-188] : BC annulé — terminal pour son contenu commercial ;
-- seuls updated_at et les trois caches financiers dérivés évoluent (PT-16).
DROP TRIGGER tr_12_bons_commande_annule;

CREATE TRIGGER tr_12_bons_commande_annule
BEFORE UPDATE ON bons_commande
WHEN OLD.statut = 'annule'
 AND (NEW.id IS NOT OLD.id
        OR NEW.client_id IS NOT OLD.client_id
        OR NEW.client_snapshot IS NOT OLD.client_snapshot
        OR NEW.client_snapshot_version IS NOT OLD.client_snapshot_version
        OR NEW.entreprise_snapshot IS NOT OLD.entreprise_snapshot
        OR NEW.entreprise_snapshot_version IS NOT OLD.entreprise_snapshot_version
        OR NEW.chantier_snapshot IS NOT OLD.chantier_snapshot
        OR NEW.chantier_snapshot_version IS NOT OLD.chantier_snapshot_version
        OR NEW.date_acceptation IS NOT OLD.date_acceptation
        OR NEW.date_debut IS NOT OLD.date_debut
        OR NEW.date_fin IS NOT OLD.date_fin
        OR NEW.montant_contractuel_ht IS NOT OLD.montant_contractuel_ht
        OR NEW.statut IS NOT OLD.statut
        OR NEW.completed_at IS NOT OLD.completed_at
        OR NEW.cancelled_at IS NOT OLD.cancelled_at
        OR NEW.motif_annulation IS NOT OLD.motif_annulation
        OR NEW.frozen_at IS NOT OLD.frozen_at
        OR NEW.created_at IS NOT OLD.created_at
        OR NEW.origine IS NOT OLD.origine
        OR NEW.legacy_id IS NOT OLD.legacy_id
        OR NEW.legacy_data IS NOT OLD.legacy_data
        OR NEW.legacy_numero IS NOT OLD.legacy_numero)
BEGIN
    SELECT RAISE(ABORT, 'INV-173: bon de commande annule terminal, seules les evolutions autorisees sont modifiables');
END;
