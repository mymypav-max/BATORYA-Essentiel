"""Migration corrective 009a_bc_annulation_interdite_si_facture (rang 13, D-55) ; D-05 (validée 2026-09-29, exception « acompte non réglé » supprimée par la
décision du 2026-10-13, règle du net nul par avoirs précisée le 2026-10-17), INV-44, errata E-07, scénario C-19 ; INV-06, INV-53, INV-173, INV-188 ; migrations 005c (D-56), 006 ; conventions techniques §5
(chaîne ordonnée, transaction et user_version).
Aucun identifiant T n'est attribué à ce fichier : le modèle n'en prévoit pas pour 009a (T-52 est réservé à la tranche 010).

009a crée UN trigger (tr_103_bons_commande_annulation_facturee ; TR-103, numéro libre à inscrire au modèle de données) : un BC ne passe à 'annule' que si CHACUNE de
ses factures (acompte, situation, solde) a un montant NET nul après avoirs (net = total_ht moins Σ total_ht des avoirs qui la référencent). Le règlement n'est pas le
critère ; les factures et les avoirs restent en base. Aucune table, aucun index, aucun CHECK, aucune donnée. Un acompte PRÉVU (devis.acompte_*) n'est pas une facture
et ne bloque pas. Règle validée par le propriétaire du produit le 2026-10-17 (elle remplace la règle stricte du 2026-10-13).

Principes de ces tests :
  * le refus est toujours attribué au trigger (préfixe « INV-44 ») : la même instruction d'annulation (annuler_bc, identique à celle des autres fichiers) est acceptée
    sur un BC sans facture, donc seule la présence d'une facture explique le refus ;
  * la facturation réelle (lignes de `factures`) n'est jamais confondue avec les caches financiers du BC (montant_deja_facture_ht, avancement, date_100_facture) ;
  * un BC DÉJÀ annulé ne relève pas de 009a : il est fabriqué au rang 12 (annulation alors permise), puis la chaîne est portée au rang 13 ;
  * les tests de 006 et 005c décrivent leurs rangs (9 et 8) et ne sont pas modifiés ; ce fichier rejoue au rang 13 le point de départ de leurs scénarios d'annulation.
Les méthodes portent le nom de l'invariant (test_INV_44_…) ou test_009a_ suivi du groupe (A chaîne, B règle, C chemins d'écriture, D atomicité, E BC déjà annulé,
F non-régression, G contournements, H constats et diagnostics, I garde de chaîne : le trigger survit aux migrations suivantes). Les décisions d'interprétation portent « INTERPRETATION » ; les comportements observés mais non
spécifiés portent « CONSTAT » : ce ne sont pas des règles.
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39), sauf les témoins qui le précisent.

Exécution : python3 src-tauri/tests/metier/test_009a_bc_annulation_interdite_si_facture.py
"""
import pathlib
import re
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_009_pv as P  # noqa: E402  (chaîne 001 à 009, fabrication de données, services de facturation et émulation du runner)

T = P.T
MIGRATIONS = P.MIGRATIONS
NOM_009A = "009a_bc_annulation_interdite_si_facture.sql"
NOMS = P.NOMS + (NOM_009A,)
SQL_009A = (MIGRATIONS / NOM_009A).read_text(encoding="utf-8")
RANG = 13
TRIGGER = "tr_103_bons_commande_annulation_facturee"
TS, TS2, TS_ANNUL = T.TS, T.TS2, T.TS_ANNUL
c, eur = P.F.c, P.F.eur
RE_INV44 = r"^INV-44"
TYPES = ("acompte", "situation", "solde")
ETATS_NON_ANNULES = ("en_cours", "gele", "termine")

# Diagnostic de DÉTECTION propre à ces tests (requête en lecture seule, PAS un CK du modèle) : BC annulés portant au moins une facture.
DETECT_BC_ANNULE_FACTURE = ("SELECT b.id FROM bons_commande b WHERE b.statut = 'annule' "
                            "AND EXISTS (SELECT 1 FROM factures f WHERE f.bc_id = b.id) ORDER BY b.id")


def migrer13(recursive=True):
    """Chaîne 001 à 009 (rang 12) puis 009a comme une migration ordinaire : BEGIN IMMEDIATE, fichier, user_version = 13, COMMIT."""
    db = P.migrer12(recursive=recursive)
    T.appliquer(db, RANG, SQL_009A)
    return db


def schema(db):
    return {(t, n): (tbl, sql) for t, n, tbl, sql in db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master")}


class Base13(P.Base12):
    """Base au rang 13. Fabriques de devis, BC, factures et avoirs : test_005b à test_009."""

    def setUp(self):
        self.db = migrer13()
        self._n = 0
        self._npv = {}
        self.desynchroniser_ids()

    def isole(self, gardes):
        """Base du rang 13 dont tous les triggers sont supprimés sauf `gardes`."""
        t = self._sur(migrer13())
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def essaie(self, sql, *args):
        """Instruction SQL puis retour arrière (SAVEPOINT) : None si elle réussit, sinon le message de l'erreur d'intégrité.
        (test_009 redéfinit `tente` pour les PV : on appelle ici celui de test_006.)"""
        return P.F.Base9.tente(self, sql, *args)

    def tente_annuler(self, b):
        """Annulation du BC (instruction commune de annuler_bc) puis retour arrière : None si elle réussit, sinon le message de l'erreur d'intégrité."""
        self.db.execute("SAVEPOINT tann")
        try:
            self.annuler_bc(b)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tann")
            self.db.execute("RELEASE tann")

    def refuse_annuler(self, b):
        m = self.tente_annuler(b)
        self.assertIsNotNone(m, "annulation acceptée à tort")
        self.assertRegex(m, RE_INV44)

    def avec_facture(self, type_):
        """BC en cours (un devis de 6000.00 et un acompte prévu) portant une facture du type voulu ; retourne (bc, facture)."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        if type_ == "acompte":
            f = self.facture(bc, "acompte", "100.00", devis_id=bc.d[0])
            self.ligne_f(f, 1, "synthese", "100.00")
        elif type_ == "situation":
            f = self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        else:
            f = self.solde(bc)
        return bc, f

    def statut(self, b):
        return self.un("SELECT statut, cancelled_at, motif_annulation FROM bons_commande WHERE id=?", b)

    def bc_complet(self, b):
        cur = self.db.execute("SELECT * FROM bons_commande WHERE id=?", (b,))
        return cur.fetchone()


# --------------------------------------------------------------------------------------------------------------------
# A — chaîne de migration
# --------------------------------------------------------------------------------------------------------------------
class Chaine(Base13):
    def test_009a_A_fichiers_de_la_chaine_dans_l_ordre(self):
        self.assertEqual([p.name for p in sorted(MIGRATIONS.glob("*.sql"))[:13]], list(NOMS))
        self.assertEqual(len(NOMS), RANG)
        self.assertLess("009_pv.sql", NOM_009A)                                                  # 009a s'ordonne après la tranche 009
        self.assertTrue(all(p.name > NOM_009A for p in sorted(MIGRATIONS.glob("*.sql"))[RANG:]))  # toute migration suivante (010, 011, …) s'ordonne après 009a

    def test_009a_A_rang_et_user_version(self):
        db = P.migrer12()
        self.assertEqual(T.db_user_version(db), 12)
        T.appliquer(db, RANG, SQL_009A)
        self.assertEqual(T.db_user_version(db), 13)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_009a_A_le_protocole_de_reconstruction_du_runner_est_accepte(self):
        db = P.migrer12()
        T.runner(db, RANG, SQL_009A)
        self.assertEqual(T.db_user_version(db), 13)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_009a_A_le_fichier_ne_contient_qu_un_trigger_sans_transaction_ni_pragma_ni_donnee(self):
        instr = [T.sans_commentaires(s).strip() for s in T.instructions(SQL_009A)]
        self.assertEqual(len(instr), 1)
        self.assertTrue(instr[0].startswith(f"CREATE TRIGGER {TRIGGER}"))
        code = T.sans_commentaires(SQL_009A)
        self.assertIsNone(re.search(r"\b(INSERT|DELETE|DROP|ALTER|PRAGMA|COMMIT|ROLLBACK|CREATE\s+(TABLE|INDEX|VIEW))\b", code))
        self.assertEqual(code.count("BEGIN"), 1)                                                 # le BEGIN du corps du trigger, aucune transaction
        self.assertTrue(re.search(r"RAISE\(ABORT, '([^']*)'\)", code).group(1).isascii())

    def test_009a_A_objets_exacts_seul_le_trigger_est_ajoute_au_rang_12(self):
        avant, apres = schema(P.migrer12()), schema(self.db)
        self.assertEqual(set(apres) - set(avant), {("trigger", TRIGGER)})
        self.assertEqual(set(avant) - set(apres), set())
        self.assertEqual({k: v for k, v in apres.items() if k[1] != TRIGGER}, avant)             # aucun objet existant n'est modifié, au caractère près
        self.assertEqual(apres[("trigger", TRIGGER)][0], "bons_commande")

    def test_009a_A_aucune_donnee_n_est_modifiee_par_la_migration(self):
        t = Base13._sur(P.migrer12())
        bc = t.monde(devis=[{"lignes": ["100.00"]}])
        t.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        tables = [n for (n,) in t.tous("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        avant = {n: t.tous(f"SELECT * FROM {n}") for n in tables}
        T.appliquer(t.db, RANG, SQL_009A)
        self.assertEqual({n: t.tous(f"SELECT * FROM {n}") for n in tables}, avant)

    def test_009a_A_rejeu_sur_une_base_deja_au_rang_13_est_refuse_sans_effet(self):
        avant = schema(self.db)
        with self.assertRaises(sqlite3.OperationalError):
            T.appliquer(self.db, RANG, SQL_009A)
        if self.db.in_transaction:
            self.db.execute("ROLLBACK")
        self.assertEqual(schema(self.db), avant)
        self.assertEqual(T.db_user_version(self.db), 13)

    def test_009a_A_schema_identique_base_fraiche_et_base_migree_peuplee(self):
        t = Base13._sur(P.migrer12())
        bc = t.monde(devis=[{"lignes": ["100.00"]}])
        t.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        T.appliquer(t.db, RANG, SQL_009A)
        self.assertEqual(schema(t.db), schema(self.db))


# --------------------------------------------------------------------------------------------------------------------
# B — la règle : D-05, INV-44
# --------------------------------------------------------------------------------------------------------------------
class Regle(Base13):
    def test_INV_44_un_BC_sans_facture_peut_etre_annule(self):
        for etat in ("en_cours", "gele"):
            with self.subTest(etat=etat):
                bc = self.monde(devis=[{"lignes": ["100.00"]}])
                self.etat(bc, etat)
                self.assertIsNone(self.tente_annuler(bc.b))
                self.annuler_bc(bc.b)
                self.assertEqual(self.statut(bc.b)[0], "annule")

    def test_INV_44_un_acompte_prevu_au_devis_sans_facture_n_empeche_pas_l_annulation(self):
        # acompte PRÉVU (devis.acompte_*, donnée commerciale) ≠ facture d'acompte (ligne de `factures`) : seule la seconde bloque
        colonnes = [c[1] for c in self.tous("PRAGMA table_info(bons_commande)")]
        self.assertEqual([c for c in colonnes if c.startswith("acompte")], [])                   # 005a : le BC ne porte aucune colonne d'acompte
        for prevu in (("montant", "1000.00"), ("pourcentage", "30.00")):
            with self.subTest(acompte=prevu):
                bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": prevu}])
                self.assertEqual(self.un("SELECT acompte_type, acompte_valeur FROM devis WHERE id=?", bc.d[0]), prevu)
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 0)
                self.assertIsNone(self.tente_annuler(bc.b))
                self.annuler_bc(bc.b)
                self.assertEqual(self.statut(bc.b)[0], "annule")
                self.assertEqual(self.un("SELECT acompte_type, acompte_valeur FROM devis WHERE id=?", bc.d[0]), prevu)   # le devis garde son acompte prévu

    def test_INV_44_une_facture_d_acompte_bloque_qu_elle_soit_reglee_ou_non(self):
        for regle in (False, True):
            with self.subTest(regle=regle):
                bc, f = self.avec_facture("acompte")
                avant = self.un("SELECT COUNT(*) FROM reglements")[0]
                if regle:
                    self.encaisse(f, "100.00")                                                   # facture soldée : reste dû 0.00
                self.assertEqual(self.un("SELECT COUNT(*) FROM reglements")[0], avant + (1 if regle else 0))
                self.refuse_annuler(bc.b)
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 1)

    def test_INV_44_une_emission_echouee_ou_defaite_par_rollback_n_est_pas_une_facture_existante(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        m = self.tente_f(bc, "acompte", "99999.00", devis_id=bc.d[0])                           # émission refusée par un trigger de facturation
        self.assertIsNotNone(m)
        self.assertNotRegex(m, RE_INV44)
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 0)
        self.assertIsNone(self.tente_annuler(bc.b))
        self.db.execute("SAVEPOINT em")                                                         # émission défaite par ROLLBACK TO
        self.facture(bc, "acompte", "100.00", devis_id=bc.d[0])
        self.refuse_annuler(bc.b)                                                               # tant qu'elle est présente dans la transaction, elle bloque
        self.db.execute("ROLLBACK TO em")
        self.db.execute("RELEASE em")
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 0)
        self.assertIsNone(self.tente_annuler(bc.b))
        self.db.execute("BEGIN")                                                                # émission défaite par ROLLBACK de la transaction
        self.facture(bc, "acompte", "100.00", devis_id=bc.d[0])
        self.db.execute("ROLLBACK")
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 0)
        self.annuler_bc(bc.b)
        self.assertEqual(self.statut(bc.b)[0], "annule")

    def test_INV_44_un_BC_avec_acompte_situation_ou_solde_ne_peut_pas_etre_annule(self):
        for type_ in TYPES:
            for etat in ETATS_NON_ANNULES:
                with self.subTest(type=type_, etat=etat):
                    bc, f = self.avec_facture(type_)
                    self.etat(bc, etat)
                    avant = self.bc_complet(bc.b)
                    self.refuse_annuler(bc.b)
                    with self.assertRaisesRegex(sqlite3.IntegrityError, RE_INV44):
                        self.annuler_bc(bc.b)
                    self.assertEqual(self.bc_complet(bc.b), avant)                                # aucune colonne n'a bougé
                    self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 1)

    # --- règle du 2026-10-17 : annulation permise si chaque facture a un net nul après avoirs ------------------------------------
    def instantane_historique(self):
        """Factures, lignes de facture et règlements, lus tels quels (preuve que l'annulation ne modifie ni ne supprime rien)."""
        return (self.tous("SELECT * FROM factures ORDER BY id"), self.tous("SELECT * FROM facture_lignes ORDER BY id"),
                self.tous("SELECT * FROM reglements ORDER BY id"))

    def test_INV_44_cas1_facture_non_reglee_sans_avoir_annulation_refusee(self):
        for type_ in TYPES:
            for etat in ETATS_NON_ANNULES:
                with self.subTest(type=type_, etat=etat):
                    bc, f = self.avec_facture(type_)
                    self.etat(bc, etat)
                    self.assertEqual(self.un("SELECT COUNT(*) FROM reglements")[0], 0)                  # aucune facture réglée : l'impayé ne s'ignore pas
                    self.refuse_annuler(bc.b)

    def test_INV_44_cas2_facture_integralement_creditee_annulation_autorisee(self):
        for type_ in TYPES:
            for etat in ETATS_NON_ANNULES:
                with self.subTest(type=type_, etat=etat):
                    bc, f = self.avec_facture(type_)
                    self.etat(bc, etat)
                    a = self.avoir(f)                                                                    # avoir total : net de la facture = 0.00
                    self.assertTrue(self.neutralisee(f))
                    avant = self.instantane_historique()
                    self.assertIsNone(self.tente_annuler(bc.b))
                    self.annuler_bc(bc.b)
                    self.assertEqual(self.statut(bc.b)[0], "annule")
                    self.assertEqual(self.instantane_historique(), avant)                               # factures, lignes, avoirs : strictement intacts
                    self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 2)
                    self.assertEqual(self.un("SELECT type, origine_facture_id FROM factures WHERE id=?", a), ("avoir", f))

    def test_INV_44_cas2_le_reglement_n_est_pas_le_critere(self):
        # facture réglée mais non créditée : refus ; facture non réglée mais créditée : autorisation (le règlement ne change rien dans les deux sens)
        bc, f = self.avec_facture("acompte")
        self.encaisse(f, "100.00")
        self.refuse_annuler(bc.b)
        bc2, f2 = self.avec_facture("acompte")
        self.avoir(f2)
        self.assertEqual(self.un("SELECT COUNT(*) FROM reglements WHERE facture_id=?", f2)[0], 0)
        self.assertIsNone(self.tente_annuler(bc2.b))

    def test_INV_44_cas2_avoirs_partiels_cumules_jusqu_a_zero_annulation_autorisee(self):
        for type_ in TYPES:
            with self.subTest(type=type_):
                bc, f = self.avec_facture(type_)
                total = self.total(f)
                self.avoir(f, "10.00")
                self.refuse_annuler(bc.b)
                self.avoir(f, eur(total - c("10.00") - c("0.01")))
                self.refuse_annuler(bc.b)                                                                # il reste 0.01 : net non nul
                self.avoir(f, "0.01")
                self.assertEqual(self.nette(bc), 0)
                self.assertIsNone(self.tente_annuler(bc.b))

    def test_INV_44_cas3_facture_partiellement_creditee_annulation_refusee(self):
        for type_ in TYPES:
            with self.subTest(type=type_):
                bc, f = self.avec_facture(type_)
                self.avoir(f, "10.00")
                self.assertFalse(self.neutralisee(f))
                self.refuse_annuler(bc.b)
                self.avoir(f, eur(self.total(f) - c("10.00") - c("0.01")))                              # reste 0.01
                self.refuse_annuler(bc.b)

    def test_INV_44_cas4_plusieurs_factures_dont_une_seule_conserve_un_net_non_nul_annulation_refusee(self):
        bc, ac, sit = self.deux_factures()
        self.avoir(ac)                                                                                  # l'acompte est ramené à zéro, la situation non
        self.refuse_annuler(bc.b)
        bc2, ac2, sit2 = self.deux_factures()
        self.avoir(sit2)                                                                                # la situation est ramenée à zéro, l'acompte non
        self.refuse_annuler(bc2.b)
        bc3, ac3, sit3 = self.deux_factures()
        self.avoir(ac3)
        self.avoir(sit3, "10.00")                                                                       # partielle sur la dernière
        self.refuse_annuler(bc3.b)
        bc4, ac4, sit4 = self.deux_factures()                                                           # trois factures : acompte et situation créditées, solde non
        self.avoir(sit4)
        self.avoir(ac4)
        sol = self.solde(bc4)
        self.refuse_annuler(bc4.b)
        self.avoir(sol)
        self.assertIsNone(self.tente_annuler(bc4.b))                                                    # le dernier avoir lève le dernier blocage

    def test_INV_44_cas5_plusieurs_factures_toutes_ramenees_a_zero_annulation_autorisee(self):
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc, ac, sit = self.deux_factures()
                sol = self.solde(bc)
                self.avoir(sol)
                self.avoir(sit)
                self.refuse_annuler(bc.b)                                                               # l'acompte n'est pas encore crédité
                self.avoir(ac)
                self.etat(bc, etat)
                avant = self.instantane_historique()
                self.assertEqual(self.nette(bc), 0)
                self.assertIsNone(self.tente_annuler(bc.b))
                self.annuler_bc(bc.b)
                self.assertEqual(self.statut(bc.b)[0], "annule")
                self.assertEqual(self.instantane_historique(), avant)
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=? AND type<>'avoir'", bc.b)[0], 3)
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=? AND type='avoir'", bc.b)[0], 3)

    def test_INV_44_le_net_s_apprecie_facture_par_facture_pas_sur_le_total_du_BC(self):
        # Même net global nul que dans le cas 5, mais l'avoir d'une facture ne compense pas une autre facture : seuls les avoirs d'origine = la facture comptent.
        bc, ac, sit = self.deux_factures()
        self.avoir(sit)
        self.avoir(ac, "50.00")
        self.assertEqual(self.nette(bc), c("50.00"))
        self.refuse_annuler(bc.b)

    def test_INV_44_un_avoir_n_est_pas_une_facture_a_ramener_a_zero(self):
        # L'avoir lui-même (net = son total) ne bloque pas : seule la facture d'origine est contrôlée.
        bc, f = self.avec_facture("situation")
        a = self.avoir(f)
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=? AND type='avoir' AND origine_facture_id IS NOT NULL", bc.b)[0], 1)
        self.assertIsNotNone(a)
        self.assertIsNone(self.tente_annuler(bc.b))

    def deux_factures(self):
        """BC (6000.00, acompte prévu 1000.00) portant un acompte de 100.00 puis une situation de 100.00 ; retourne (bc, acompte, situation)."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        ac = self.facture(bc, "acompte", "100.00", devis_id=bc.d[0])
        self.ligne_f(ac, 1, "synthese", "100.00")
        sit = self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="100.00")
        return bc, ac, sit

    def test_INV_44_les_factures_d_un_BC_ne_bloquent_pas_l_annulation_d_un_autre_BC(self):
        bc_facture, _ = self.avec_facture("situation")
        autre = self.monde(devis=[{"lignes": ["100.00"]}])
        self.refuse_annuler(bc_facture.b)
        self.assertIsNone(self.tente_annuler(autre.b))
        self.annuler_bc(autre.b)
        self.assertEqual(self.statut(autre.b)[0], "annule")
        self.assertEqual(self.statut(bc_facture.b)[0], "en_cours")

    def test_INV_44_le_refus_porte_sur_la_facture_pas_sur_les_caches_financiers_du_BC(self):
        # INTERPRETATION : caches (montant_deja_facture_ht, avancement, date_100_facture, completed_at) sans AUCUNE ligne de factures ne constituent pas une facturation.
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.geler_bc(bc.b)
        self.terminer_bc(bc.b)
        self.assertEqual(self.un("SELECT statut, avancement, date_100_facture IS NOT NULL FROM bons_commande WHERE id=?", bc.b), ("termine", "100.00", 1))
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 0)
        self.assertIsNone(self.tente_annuler(bc.b))                                              # scénario de test_005c (« BC terminé puis annulé ») : sans facture, permis par le SQL
        # la même situation avec une facture réelle est refusée
        bc2, _ = self.avec_facture("solde")
        self.geler_bc(bc2.b)
        self.terminer_bc(bc2.b)
        self.refuse_annuler(bc2.b)

    def test_INV_44_le_message_nomme_l_invariant_et_la_decision(self):
        bc, _ = self.avec_facture("acompte")
        m = self.tente_annuler(bc.b)
        self.assertEqual(m, "INV-44: annulation du bon de commande interdite, au moins une facture conserve un montant net non nul apres avoirs (D-05)")

    def test_INV_44_les_ecritures_qui_ne_sont_pas_une_annulation_restent_possibles(self):
        bc, _ = self.avec_facture("situation")
        self.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (TS2, bc.b))
        self.geler_bc(bc.b)
        self.terminer_bc(bc.b)                                                                   # passage à 'termine' : écriture du service financier, hors périmètre
        self.assertEqual(self.statut(bc.b)[0], "termine")
        self.db.execute("UPDATE bons_commande SET statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='50.00' WHERE id=?", (bc.b,))
        self.assertEqual(self.statut(bc.b)[0], "en_cours")

    def test_009a_B_le_scenario_de_depart_de_T48_L_est_refuse_au_rang_13(self):
        # test_006 (rang 9) : « monde_matrice » (une situation de 100.00) puis annulation. Au rang 13, ce point de départ ne peut plus se produire.
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_annuler(bc.b)                                                                # BC en cours
        self.geler_bc(bc.b)
        self.refuse_annuler(bc.b)                                                                # BC gelé : « annule_gele » de test_006 est inatteignable
        self.assertEqual(self.statut(bc.b)[0], "en_cours")


# --------------------------------------------------------------------------------------------------------------------
# C — chemins d'écriture vers 'annule'
# --------------------------------------------------------------------------------------------------------------------
class Chemins(Base13):
    ANNULER = ("statut='annule', cancelled_at='2099-01-01T00:00:00.000Z', motif_annulation='x', completed_at=NULL, date_100_facture=NULL")

    def test_009a_C_le_trigger_s_execute_avant_les_CHECK(self):
        # statut='annule' sans cancelled_at violerait un CHECK ; le refus qui sort est celui du trigger (BEFORE UPDATE)
        bc, _ = self.avec_facture("situation")
        m = self.essaie("UPDATE bons_commande SET statut='annule' WHERE id=?", bc.b)
        self.assertRegex(m, RE_INV44)
        bc2 = self.monde(devis=[{"lignes": ["100.00"]}])
        m2 = self.essaie("UPDATE bons_commande SET statut='annule' WHERE id=?", bc2.b)            # sans facture : c'est le CHECK qui refuse
        self.assertIsNotNone(m2)
        self.assertNotIn("INV-", m2)

    def test_009a_C_UPDATE_OR_REPLACE_et_autres_clauses_de_conflit(self):
        bc, _ = self.avec_facture("acompte")
        for verbe in ("UPDATE", "UPDATE OR REPLACE", "UPDATE OR IGNORE", "UPDATE OR ROLLBACK", "UPDATE OR FAIL", "UPDATE OR ABORT"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT v")
                try:
                    with self.assertRaisesRegex(sqlite3.IntegrityError, RE_INV44):
                        self.db.execute(f"{verbe} bons_commande SET {self.ANNULER} WHERE id=?", (bc.b,))
                finally:
                    if self.db.in_transaction:
                        self.db.execute("ROLLBACK TO v")
                        self.db.execute("RELEASE v")
                self.assertEqual(self.statut(bc.b)[0], "en_cours")

    def test_009a_C_UPSERT_vers_annule_est_refuse(self):
        bc, _ = self.avec_facture("situation")
        m = self.essaie("INSERT INTO bons_commande SELECT * FROM bons_commande WHERE id=? AND true "
                       f"ON CONFLICT (id) DO UPDATE SET {self.ANNULER}", bc.b)
        self.assertRegex(m, RE_INV44)                                                            # la branche DO UPDATE déclenche BEFORE UPDATE
        self.assertEqual(self.statut(bc.b)[0], "en_cours")

    def test_009a_C_INSERT_OR_REPLACE_d_un_BC_annule_est_refuse(self):
        bc, _ = self.avec_facture("situation")
        ligne = list(self.bc_complet(bc.b))
        cols = [c[1] for c in self.db.execute("PRAGMA table_info(bons_commande)")]
        d = dict(zip(cols, ligne))
        d.update(statut="annule", cancelled_at="2099-01-01T00:00:00.000Z", motif_annulation="x", completed_at=None, date_100_facture=None)
        m = self.essaie(f"INSERT OR REPLACE INTO bons_commande ({','.join(d)}) VALUES ({','.join('?' * len(d))})", *d.values())
        self.assertRegex(m, r"INV-40|INV-174")                                                   # état de naissance (tr_17) ou non-suppression (tr_19) : jamais d'annulation par INSERT
        self.assertEqual(self.statut(bc.b)[0], "en_cours")

    def test_009a_C_UPDATE_FROM_et_sous_requete_vers_annule_sont_refuses(self):
        bc, _ = self.avec_facture("situation")
        m = self.essaie("UPDATE bons_commande SET statut = v.s, cancelled_at='2099-01-01T00:00:00.000Z', motif_annulation='x' "
                       "FROM (SELECT 'annule' AS s) AS v WHERE bons_commande.id=?", bc.b)
        self.assertRegex(m, RE_INV44)
        m = self.essaie("UPDATE bons_commande SET statut = (SELECT 'annule'), cancelled_at='2099-01-01T00:00:00.000Z', motif_annulation='x' WHERE id=?", bc.b)
        self.assertRegex(m, RE_INV44)

    def test_009a_C_le_trigger_agit_seul_sans_les_autres_triggers(self):
        t = self.isole((TRIGGER,))
        bc = t.monde(devis=[{"lignes": ["100.00"]}])
        t.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        t.refuse_annuler(bc.b)
        bc2 = t.monde(devis=[{"lignes": ["100.00"]}])
        self.assertIsNone(t.tente_annuler(bc2.b))

    def test_009a_C_independant_de_recursive_triggers_et_de_foreign_keys(self):
        db = migrer13(recursive=False)
        t = Base13._sur(db)
        bc = t.monde(devis=[{"lignes": ["100.00"]}])
        t.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertEqual(db.execute("PRAGMA recursive_triggers").fetchone()[0], 0)
        t.refuse_annuler(bc.b)
        db.execute("PRAGMA foreign_keys=OFF")
        t.refuse_annuler(bc.b)
        db.execute("PRAGMA foreign_keys=ON")


# --------------------------------------------------------------------------------------------------------------------
# D — atomicité : le contrôle précède la modification, la transaction reste cohérente
# --------------------------------------------------------------------------------------------------------------------
class Atomicite(Base13):
    def test_009a_D_un_refus_ne_laisse_aucune_ecriture_et_la_transaction_reste_utilisable(self):
        bc, _ = self.avec_facture("situation")
        avant = self.bc_complet(bc.b)
        self.db.execute("BEGIN")
        self.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (TS2, bc.b))        # écriture antérieure de la même transaction
        with self.assertRaisesRegex(sqlite3.IntegrityError, RE_INV44):
            self.annuler_bc(bc.b)
        self.assertTrue(self.db.in_transaction)                                                  # RAISE(ABORT) : l'instruction est défaite, la transaction reste ouverte
        self.assertEqual(self.un("SELECT statut, updated_at FROM bons_commande WHERE id=?", bc.b), ("en_cours", TS2))
        self.db.execute("ROLLBACK")                                                              # le service décide du ROLLBACK
        self.assertEqual(self.bc_complet(bc.b), avant)

    def test_009a_D_une_instruction_multi_lignes_est_atomique(self):
        sans = self.monde(devis=[{"lignes": ["100.00"]}])
        avec, _ = self.avec_facture("situation")
        m = self.essaie("UPDATE bons_commande SET statut='annule', cancelled_at='2099-01-01T00:00:00.000Z', motif_annulation='x' WHERE id IN (?, ?)", sans.b, avec.b)
        self.assertRegex(m, RE_INV44)
        self.db.execute("BEGIN")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE bons_commande SET statut='annule', cancelled_at='2099-01-01T00:00:00.000Z', motif_annulation='x' WHERE id IN (?, ?)",
                            (sans.b, avec.b))
        self.assertEqual(self.statut(sans.b)[0], "en_cours")                                    # le BC sans facture n'est pas annulé non plus
        self.db.execute("ROLLBACK")

    def test_009a_D_annulation_et_emission_dans_la_meme_transaction(self):
        # une facture émise plus tôt dans la même transaction bloque l'annulation qui suit ; l'annulation accomplie avant interdit toute émission (INV-188)
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        self.db.execute("BEGIN")
        self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        with self.assertRaisesRegex(sqlite3.IntegrityError, RE_INV44):
            self.annuler_bc(bc.b)
        self.db.execute("ROLLBACK")
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 0)
        self.annuler_bc(bc.b)
        self.refuse_f("INV-188", bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")


# --------------------------------------------------------------------------------------------------------------------
# E — BC déjà annulé : comportement inchangé (INV-173, INV-188, avoirs, 005c)
# --------------------------------------------------------------------------------------------------------------------
class DejaAnnule(Base13):
    def base_migree(self):
        """BC portant une situation, annulé AU RANG 12 (permis alors), puis chaîne portée au rang 13 : retourne (assistant au rang 13, bc, situation)."""
        t = Base13._sur(P.migrer12())
        bc = t.monde(devis=[{"lignes": ["1000.00"]}])
        s = t.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        t.recalcul_bc(bc)
        t.annuler_bc(bc.b)
        T.appliquer(t.db, RANG, SQL_009A)
        return t, bc, s

    def test_009a_E_la_migration_ne_touche_pas_un_BC_annule_et_facture_avant_elle(self):
        t, bc, s = self.base_migree()
        self.assertEqual(t.statut(bc.b)[0], "annule")
        self.assertEqual(t.tous(DETECT_BC_ANNULE_FACTURE), [(bc.b,)])                          # détectable, ni corrigé ni refusé
        self.assertEqual(T.db_user_version(t.db), 13)

    def test_009a_E_un_avoir_reste_possible_sur_un_BC_annule_et_ne_le_rouvre_pas(self):
        t, bc, s = self.base_migree()
        t.accepte_f(bc, "avoir", "10.00", origine_facture_id=s)
        a = t.avoir(s, "25.00")
        self.assertIsNotNone(a)
        t.neutraliser(s)
        t.recalcul_bc(bc)                                                                        # D-56 : les caches évoluent encore sur un BC annulé
        self.assertEqual(t.statut(bc.b)[0], "annule")
        self.assertEqual(t.etat_bc(bc)[4], "0.00")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-173"):
            t.db.execute("UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (bc.b,))

    def test_009a_E_un_BC_annule_ne_recoit_ni_acompte_ni_situation_ni_solde(self):
        t, bc, s = self.base_migree()
        t.refuse_f("INV-188", bc, "acompte", "100.00", devis_id=bc.d[0])
        nette = t.nette(bc.b)
        t.refuse_f("INV-188", bc, "situation", "100.00", situation_numero=2, montant_deja_facture_ht=P.F.eur(nette))
        t.refuse_f("INV-188", bc, "solde", P.F.eur(t.contractuel(bc.b) - nette))

    def test_009a_E_un_UPDATE_sans_changement_de_statut_sur_un_BC_annule_n_est_pas_vise_par_009a(self):
        t, bc, s = self.base_migree()
        self.assertIsNone(t.essaie("UPDATE bons_commande SET statut='annule' WHERE id=?", bc.b))   # statut identique : ni 009a ni tr_12 ne s'en mêlent
        self.assertIsNone(t.essaie("UPDATE bons_commande SET updated_at=? WHERE id=?", TS2, bc.b))

    def test_009a_E_un_BC_annule_sans_facture_ne_peut_recevoir_aucun_avoir(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.annuler_bc(bc.b)
        autre, s = self.avec_facture("situation")
        self.refuse_f("INV-76", bc, "avoir", "10.00", origine_facture_id=s)                      # l'origine d'un avoir appartient au même BC (tr_23)


# --------------------------------------------------------------------------------------------------------------------
# F — non-régression : D-05, D-56 et triggers existants
# --------------------------------------------------------------------------------------------------------------------
class NonRegression(Base13):
    def test_009a_F_les_triggers_existants_de_bons_commande_et_de_factures_sont_inchanges(self):
        avant, apres = schema(P.migrer12()), schema(self.db)
        for nom in ("tr_12_bons_commande_annule", "tr_12_bons_commande_contrat", "tr_14_bons_commande_frozen_at", "tr_17_bons_commande_insert",
                    "tr_19_bons_commande_no_delete", "tr_01_bons_commande_numero_immuable", "tr_16_factures_bc", "tr_20_factures_no_update",
                    "tr_21_factures_no_delete", "tr_22_factures_acompte", "tr_22_factures_situation", "tr_22_factures_solde", "tr_23_factures_avoir"):
            with self.subTest(trigger=nom):
                self.assertEqual(apres[("trigger", nom)], avant[("trigger", nom)])

    def test_009a_F_D56_les_trois_caches_evoluent_encore_sur_un_BC_annule_et_les_22_autres_colonnes_restent_gardees(self):
        # 005c (D-56) : la liste des colonnes gardées de tr_12_bons_commande_annule n'est pas modifiée par 009a
        sql = schema(self.db)[("trigger", "tr_12_bons_commande_annule")][1]
        gardees = re.findall(r"NEW\.(\w+) IS NOT OLD\.\1\b", sql)
        self.assertEqual(len(gardees), 22)
        self.assertEqual(set(gardees) & {"montant_deja_facture_ht", "avancement", "date_100_facture"}, set())
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.annuler_bc(bc.b)                                                                    # BC annulé sans facture
        self.assertIsNone(self.essaie("UPDATE bons_commande SET montant_deja_facture_ht='10.00', avancement='50.00', updated_at=? WHERE id=?", TS2, bc.b))
        self.assertRegex(self.essaie("UPDATE bons_commande SET montant_contractuel_ht='1.00' WHERE id=?", bc.b), "INV-173")
        self.assertRegex(self.essaie("UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", bc.b), "INV-173")

    def test_009a_F_D05_acompte_situation_solde_et_BC_terminal(self):
        # rappels de 006 / 004 au rang 13 : la matrice des états du BC par type de facture n'a pas changé
        for etat, attendu in (("en_cours", None), ("gele", None), ("termine", "INV-47"), ("annule", "INV-188"), ("annule_gele", "INV-188")):
            with self.subTest(etat=etat):
                bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
                if etat in ("termine", "annule", "annule_gele"):
                    self.etat(bc, etat)                                                            # état fabriqué SANS facture : possible au rang 13
                m = self.tente_f(bc, "acompte", "100.00", devis_id=bc.d[0])
                if attendu is None:
                    self.assertIsNone(m)
                else:
                    self.assertRegex(m, attendu)

    def test_009a_F_un_BC_ne_se_supprime_toujours_pas(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-174"):
            self.db.execute("DELETE FROM bons_commande WHERE id=?", (bc.b,))


# --------------------------------------------------------------------------------------------------------------------
# G — contournements
# --------------------------------------------------------------------------------------------------------------------
class Contournements(Base13):
    def test_009a_G_on_ne_deplace_ni_ne_supprime_la_facture_pour_pouvoir_annuler(self):
        bc, f = self.avec_facture("situation")
        autre = self.monde(devis=[{"lignes": ["100.00"]}])
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-53"):
            self.db.execute("UPDATE factures SET bc_id=? WHERE id=?", (autre.b, f))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-06"):
            self.db.execute("DELETE FROM factures WHERE id=?", (f,))
        with self.assertRaises(sqlite3.IntegrityError):                                          # INSERT OR REPLACE : refusé (garde d'INSERT ou tr_21)
            self.db.execute("INSERT OR REPLACE INTO factures (id, numero, type, bc_id, client_id, client_snapshot, client_snapshot_version, "
                            "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_emission, "
                            "date_echeance, total_ht, situation_numero, montant_deja_facture_ht) SELECT id, numero, type, bc_id, client_id, client_snapshot, "
                            "client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                            "date_emission, date_echeance, total_ht, situation_numero, montant_deja_facture_ht FROM factures WHERE id=?", (f,))
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE id=? AND bc_id=?", f, bc.b)[0], 1)
        self.refuse_annuler(bc.b)

    def test_009a_G_une_facture_importee_bloque_comme_une_facture_V6(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", legacy_id="V2-1", numero="FAC-HISTO-1")
        self.refuse_annuler(bc.b)


# --------------------------------------------------------------------------------------------------------------------
# H — constats et diagnostics (aucune règle nouvelle)
# --------------------------------------------------------------------------------------------------------------------
class Constats(Base13):
    def test_009a_H_un_BC_importe_et_facture_ne_s_annule_pas(self):
        # Aucun import de BC annulé n'est prévu (arbitrage du 2026-10-13) et aucune exception n'est créée : un BC importé (origine='import', avec legacy_numero)
        # qui porte une facture historique relève de la même règle que tout BC. Complète test_009a_G_une_facture_importee_bloque_comme_une_facture_V6.
        bc = self.bc(origine="import", legacy_id="V2-7", legacy_numero="V2-BC-7")
        self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", legacy_id="V2-9", numero="FAC-HISTO-9")
        self.refuse_annuler(bc.b)

    def test_009a_H_requete_de_detection_des_BC_annules_et_factures(self):
        # requête de test, hors schéma, destinée aux bases migrées depuis le rang 12 ; vide sur toute base alimentée au rang 13
        self.assertEqual(self.tous(DETECT_BC_ANNULE_FACTURE), [])
        bc, _ = self.avec_facture("acompte")
        self.refuse_annuler(bc.b)
        self.assertEqual(self.tous(DETECT_BC_ANNULE_FACTURE), [])
        autre = self.monde(devis=[{"lignes": ["100.00"]}])
        self.annuler_bc(autre.b)
        self.assertEqual(self.tous(DETECT_BC_ANNULE_FACTURE), [])


# --------------------------------------------------------------------------------------------------------------------
# I — garde de chaîne : une migration ultérieure ne supprime pas le trigger sans le recréer à l'identique
# --------------------------------------------------------------------------------------------------------------------
def _norm(sql):
    return " ".join(sql.replace(";", " ").split())


def trigger_attendu():
    """Définition du trigger telle que 009a la crée (sans commentaires ni « ; » final, espaces normalisés)."""
    instr = [T.sans_commentaires(s).strip() for s in T.instructions(SQL_009A)]
    return _norm(instr[0])


# Une migration qui supprime ou renomme `bons_commande` (reconstruction de table) ou supprime le trigger doit le recréer à l'identique. Une reconstruction de
# `factures` ne supprime pas le trigger (il est porté par `bons_commande`) : elle est couverte par le contrôle dynamique (le refus doit rester effectif).
RE_SUPPRIME_LE_TRIGGER = re.compile(
    r"\bDROP\s+TABLE(\s+IF\s+EXISTS)?\s+bons_commande\b"
    r"|\bALTER\s+TABLE\s+bons_commande\s+RENAME\s+TO\b"
    r"|\bDROP\s+TRIGGER(\s+IF\s+EXISTS)?\s+" + TRIGGER + r"\b", re.I)


def problemes_de_recreation(sql):
    """Contrôle statique d'une migration ultérieure : liste vide si elle ne touche pas au trigger ou le recrée à l'identique."""
    if not RE_SUPPRIME_LE_TRIGGER.search(T.sans_commentaires(sql)):
        return []
    for st in T.instructions(sql):
        c = T.sans_commentaires(st).strip()
        if re.match(r"CREATE\s+TRIGGER\s+" + TRIGGER + r"\b", c, re.I):
            return [] if _norm(c) == trigger_attendu() else ["le trigger est recréé avec une définition différente"]
    return ["bons_commande ou le trigger est supprimé sans recréer " + TRIGGER]


def migrations_suivantes():
    """Migrations livrées après 009a (rang 14, 15, …) : vide tant que 010 n'existe pas."""
    return [(RANG + 1 + i, p.name, p.read_text(encoding="utf-8")) for i, p in enumerate(sorted(MIGRATIONS.glob("*.sql"))[RANG:])]


class GardeChaine(Base13):
    def definition(self, db):
        return [_norm(r[0]) for r in db.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (TRIGGER,))]

    def suite_conserve_le_trigger(self, suite):
        """Rejoue `suite` (liste de (rang, nom, sql)) sur une base du rang 13 peuplée : le trigger reste identique et le refus reste effectif après chaque migration."""
        t = self._sur(migrer13())
        bc, _ = t.avec_facture("acompte")                                                          # pas de situation : 009b (D-62) refuse de s'appliquer sur une base qui en contient
        for rang, nom, sql in suite:
            T.runner(t.db, rang, sql)
            self.assertEqual(self.definition(t.db), [trigger_attendu()], nom)
            t.refuse_annuler(bc.b)

    def test_009a_I_le_trigger_est_identique_et_effectif_apres_chaque_migration_suivante(self):
        self.assertEqual(self.definition(self.db), [trigger_attendu()])                          # au rang 13 (et sur toute chaîne jouée jusqu'ici)
        self.suite_conserve_le_trigger(migrations_suivantes())                                    # 010, 011, … quand elles existeront

    def test_009a_I_toute_migration_suivante_qui_supprime_bons_commande_recree_le_trigger(self):
        for rang, nom, sql in migrations_suivantes():
            with self.subTest(migration=nom):
                self.assertEqual(problemes_de_recreation(sql), [], nom)

    def test_009a_I_temoin_une_migration_qui_supprime_le_trigger_est_detectee(self):
        sql = f"DROP TRIGGER {TRIGGER};"
        self.assertTrue(problemes_de_recreation(sql))
        with self.assertRaises(AssertionError):
            self.suite_conserve_le_trigger([(14, "x_supprime.sql", sql)])

    def test_009a_I_temoin_reconstruction_de_bons_commande_sans_recreation_est_detectee(self):
        self.assertTrue(problemes_de_recreation("CREATE TABLE bons_commande_new (id INTEGER);\nDROP TABLE bons_commande;\nALTER TABLE bons_commande_new RENAME TO bons_commande;"))
        self.assertTrue(problemes_de_recreation("ALTER TABLE bons_commande RENAME TO bons_commande_old;"))

    def test_009a_I_temoin_recreation_a_l_identique_est_acceptee_et_alteree_est_refusee(self):
        corps = T.sans_commentaires(next(T.instructions(SQL_009A))).strip()
        self.assertEqual(problemes_de_recreation(f"DROP TRIGGER {TRIGGER};\n{corps}\n"), [])
        self.assertEqual(problemes_de_recreation(f"-- commentaire\nDROP TABLE bons_commande;\n{corps}\n"), [])
        alteree = corps.replace(" AND OLD.statut <> 'annule'", "")
        self.assertNotEqual(alteree, corps)
        self.assertTrue(problemes_de_recreation(f"DROP TRIGGER {TRIGGER};\n{alteree}\n"))
        self.suite_conserve_le_trigger([(14, "x_recree.sql", f"DROP TRIGGER {TRIGGER};\n{corps}\n")])    # recréé à l'identique : la suite passe
        with self.assertRaises(AssertionError):
            self.suite_conserve_le_trigger([(14, "x_altere.sql", f"DROP TRIGGER {TRIGGER};\n{alteree}\n")])

    def test_009a_I_temoin_une_migration_qui_rend_le_trigger_inoperant_sans_le_modifier_est_detectee(self):
        # définition intacte mais plus aucune facture à trouver (reconstruction de `factures` qui perd les lignes) : seul le contrôle du refus le voit
        with self.assertRaises(AssertionError):
            self.suite_conserve_le_trigger([(14, "x_vide.sql", "DROP TRIGGER tr_21_factures_no_delete;\nDROP TRIGGER tr_21_facture_lignes_no_delete;\nDELETE FROM facture_lignes;\nDELETE FROM factures;\n")])

    def test_009a_I_temoin_les_migrations_qui_ne_touchent_pas_au_trigger_ne_sont_pas_signalees(self):
        self.assertEqual(problemes_de_recreation("CREATE TABLE autre (id INTEGER);\nALTER TABLE bons_commande ADD COLUMN x TEXT;"), [])
        self.assertEqual(problemes_de_recreation("-- DROP TABLE bons_commande dans un commentaire\nCREATE INDEX i ON factures(bc_id);"), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
