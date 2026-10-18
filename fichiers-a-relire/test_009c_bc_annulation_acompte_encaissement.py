"""Migration corrective 009c_bc_annulation_acompte_encaissement (rang 15, D-63, test T-54, après 009a et 009b) ; D-05 (validée 2026-09-29), INV-44, errata E-07, scénario C-19 ;
décisions du propriétaire du produit du 2026-10-18 (option A) ; INV-06, INV-53, INV-72, INV-76, INV-173, INV-188 ; conventions techniques §5 (migration corrective NNNx).

009c recrée UN trigger (tr_103_bons_commande_annulation_facturee ; TR-103 ; même nom que 009a) : un BC ne passe à 'annule' que si
  1. aucun encaissement ACTIF (reglements.type = 'encaissement' ∧ cancelled_at IS NULL) n'existe sur une facture du BC (même si la facture est neutralisée par avoirs) ;
  2. aucune situation n'a été émise (même créditée) ;
  3. aucune facture autre qu'un acompte (et qu'un avoir) n'existe, notamment aucun solde (même net nul) ;
  4. chaque acompte est intégralement neutralisé par des avoirs de motif 'correction_erreur' (exception « acompte non réglé » validée : avoir total, PUIS annulation du BC).
Le remboursement n'est pas un encaissement ; un encaissement annulé (y compris importé déjà annulé) ne bloque pas ; les règlements d'un autre BC sont sans effet.

Les tests 006, 007, 009a et 009b décrivent leurs migrations TELLES QUE LIVRÉES (rangs 9, 10, 13 et 14) : ils ne sont pas réécrits. test_009a décrit la règle du net nul (rang 13) ; ce fichier
vérifie le comportement de la chaîne COMPLÈTE (001 à 009c, rang 15), qui remplace cette règle.

Limites de ce que ces tests prouvent (voir aussi l'en-tête de la migration) :
  * un trigger SQLite ne voit que l'ÉTAT au moment de l'UPDATE du BC : il garantit que l'avoir existe AVANT l'annulation (l'ordre inverse est refusé) ; il ne peut PAS garantir
    que l'avoir et l'annulation appartiennent à la même transaction. Cette atomicité relève du service d'annulation (aucun service n'existe dans le dépôt) : le groupe D l'ÉMULE
    (BEGIN IMMEDIATE, avoir, UPDATE du BC, COMMIT ou ROLLBACK) avec les moyens de test existants ; ce n'est pas la preuve d'un service réel ;
  * un facture n'étant jamais annulable dans la chaîne livrée (006 : tr_20, aucun cancelled_at), « situation annulée » s'y réalise par neutralisation (avoir total).
Groupes : A chaîne, B règle (encaissements), C règle (situation, solde, acompte), D ordre et atomicité, E messages, F non-régression, G immuabilité des migrations, H garde de chaîne.
Les comportements spécifiés portent « CONSTAT » : ce ne sont pas des règles.
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39), sauf les témoins qui le précisent.

Exécution : python3 src-tauri/tests/metier/test_009c_bc_annulation_acompte_encaissement.py
"""
import hashlib
import pathlib
import re
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_009b_acompte_garanties_manuelles as B  # noqa: E402  (chaîne 001 à 009b, fabriques de devis, BC, factures, avoirs, règlements)

P = B.P
T = B.T
MIGRATIONS = B.MIGRATIONS
NOM_009C = "009c_bc_annulation_acompte_encaissement.sql"
NOMS = B.NOMS + (NOM_009C,)
SQL_009C = (MIGRATIONS / NOM_009C).read_text(encoding="utf-8")
RANG = 15
TRIGGER = "tr_103_bons_commande_annulation_facturee"
TS_ANNUL = T.TS_ANNUL
c, eur = B.c, B.eur
RE_INV44 = r"^INV-44"
ETATS_NON_ANNULES = ("en_cours", "gele", "termine")

# Les quatre refus de la règle (messages distincts, tous préfixés INV-44), dans l'ordre d'évaluation du trigger.
M_ENCAISSEMENT = r"INV-44.*encaissement actif"
M_SITUATION = r"INV-44.*situation a ete emise"
M_AUTRE_FACTURE = r"INV-44.*facture autre qu'un acompte"
M_ACOMPTE = r"INV-44.*acompte n'est pas integralement neutralise"

# Empreintes SHA-256 (fins de ligne normalisées en LF) des migrations qui ne doivent pas changer : 006, 009a et 009b telles que sur GitHub (main a99d4c2).
EMPREINTES_IMMUABLES = {
    "006_facturation.sql": "085c702176b25ee943ca7a95a741eed6a528cfb0864f74e4b3f3ba74ebc18c8e",
    "009a_bc_annulation_interdite_si_facture.sql": "23c49c6fe44fe77ceef040b2441e3fb7406ecb20e00cf8e9793d43e22545e9e3",
    "009b_acompte_garanties_manuelles.sql": "05677212c5e2459fb8e6b9a0359de6762f9eb9f8c4959789db1f012edd53d088",
}


def migrer15(recursive=True):
    """Chaîne 001 à 009b (rang 14) puis 009c avec le protocole du runner : BEGIN IMMEDIATE, fichier, foreign_key_check, integrity_check, user_version = 15, COMMIT."""
    db = B.migrer14(recursive=recursive)
    T.runner(db, RANG, SQL_009C)
    return db


def schema(db):
    return {(t, n): (tbl, sql) for t, n, tbl, sql in db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master")}


def _norm(sql):
    return re.sub(r"\s+", " ", sql).strip().rstrip(";").strip()


def trigger_009c():
    """Définition (normalisée) du CREATE TRIGGER de 009c."""
    for st in T.instructions(SQL_009C):
        code = T.sans_commentaires(st).strip()
        if re.match(r"CREATE\s+TRIGGER\s+" + TRIGGER + r"\b", code, re.I):
            return _norm(code)
    raise AssertionError("009c ne crée pas " + TRIGGER)


class Base15(B.Base14):
    """Base au rang 15. Fabriques héritées (test_005b à test_009b) ; un avoir est « correction_erreur » par défaut (Base14.cols_facture)."""

    def setUp(self):
        self.db = migrer15()
        self._n = 0
        self._npv = {}
        self.desynchroniser_ids()

    def isole(self, gardes):
        """Base du rang 15 dont tous les triggers sont supprimés sauf `gardes` (pour fabriquer un état que les gardes livrées ne laissent pas atteindre)."""
        t = self._sur(migrer15())
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def essaie(self, sql, *args):
        """Instruction SQL puis retour arrière (SAVEPOINT) : None si elle réussit, sinon le message de l'erreur d'intégrité."""
        return P.F.Base9.tente(self, sql, *args)

    # --- annulation du BC (instruction commune de annuler_bc) --------------------------------------------------------------------
    def tente_annuler(self, b):
        """Annulation du BC puis retour arrière (SAVEPOINT) : None si elle réussit, sinon le message de l'erreur d'intégrité."""
        self.db.execute("SAVEPOINT tann")
        try:
            self.annuler_bc(b)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tann")
            self.db.execute("RELEASE tann")

    def refuse(self, b, motif=RE_INV44):
        m = self.tente_annuler(b)
        self.assertIsNotNone(m, "annulation acceptée à tort")
        self.assertRegex(m, motif)
        return m

    def accepte(self, b):
        m = self.tente_annuler(b)
        self.assertIsNone(m, m)

    def statut(self, b):
        return self.un("SELECT statut, cancelled_at, motif_annulation FROM bons_commande WHERE id=?", b)

    def instantane(self):
        """Factures, lignes de facture et règlements, lus tels quels."""
        return (self.tous("SELECT * FROM factures ORDER BY id"), self.tous("SELECT * FROM facture_lignes ORDER BY id"),
                self.tous("SELECT * FROM reglements ORDER BY id"))

    # --- fabrication -----------------------------------------------------------------------------------------------------------
    def bc6000(self):
        """BC en cours (un devis de 6000.00, acompte prévu 1000.00)."""
        return self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])

    def avec(self, type_):
        """BC en cours portant UNE facture du type voulu (acompte 100.00, situation 100.00 couverte, solde au contractuel) ; retourne (bc, facture)."""
        bc = self.bc6000()
        if type_ == "acompte":
            return bc, self.acompte(bc, bc.d[0], "100.00")
        if type_ == "situation":
            return bc, self.situation(bc, "100.00", 1, "0.00")
        return bc, self.solde_final(bc)

    def montant(self, f):
        return self.un("SELECT total_ht FROM factures WHERE id=?", f)[0]

    def encaisse_tout(self, f, **kw):
        return self.encaisse(f, self.montant(f), **kw)

    def avoirs_de(self, f):
        return self.tous("SELECT id, total_ht, motif_avoir FROM factures WHERE origine_facture_id=? ORDER BY id", f)

    def nb_avoirs(self):
        return self.un("SELECT COUNT(*) FROM factures WHERE type='avoir'")[0]

    def service_annulation(self, bc, entre=None):
        """ÉMULATION du service d'annulation (option A) : UNE transaction BEGIN IMMEDIATE ; pour chaque acompte non neutralisé, avoir total (correction_erreur) ;
        `entre()` (point d'injection d'un échec intermédiaire) ; puis UPDATE du BC ; COMMIT. Toute erreur : ROLLBACK de l'ensemble puis l'erreur est relancée."""
        db = self.db
        db.execute("BEGIN IMMEDIATE")
        try:
            for (f, tot) in self.tous("SELECT id, total_ht FROM factures WHERE bc_id=? AND type='acompte' ORDER BY id", bc.b):
                reste = c(tot) - sum(c(x) for (x,) in self.tous("SELECT total_ht FROM factures WHERE origine_facture_id=?", f))
                if reste > 0:
                    self.neutraliser(f)
            if entre:
                entre()
            self.annuler_bc(bc.b)
            db.execute("COMMIT")
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise


# --------------------------------------------------------------------------------------------------------------------
# A — chaîne de migration
# --------------------------------------------------------------------------------------------------------------------
class Chaine(Base15):
    def test_009c_A_fichiers_de_la_chaine_dans_l_ordre(self):
        noms = [p.name for p in sorted(MIGRATIONS.glob("*.sql"))]
        self.assertEqual(noms[:15], list(NOMS))
        self.assertEqual(noms[14], NOM_009C)
        self.assertEqual(len(NOMS), RANG)
        self.assertLess(B.NOM_009B, NOM_009C)                                                       # 009c s'ordonne après 009b
        self.assertTrue(all(n > NOM_009C for n in noms[RANG:]))                                      # toute migration suivante (010, 011, …) s'ordonne après 009c
        self.assertRegex(NOM_009C, r"^[0-9]{3}[a-z]_[a-z0-9_]+\.sql$")                              # convention NNNx_<objet>.sql (conventions techniques §5)

    def test_009c_A_rang_15_et_user_version(self):
        db = B.migrer14()
        self.assertEqual(T.db_user_version(db), 14)
        T.runner(db, RANG, SQL_009C)
        self.assertEqual(T.db_user_version(db), 15)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_009c_A_aucune_transaction_aucun_pragma_aucune_donnee_dans_le_fichier(self):
        code = T.sans_commentaires(SQL_009C)
        self.assertIsNone(re.search(r"\b(COMMIT|ROLLBACK|PRAGMA\s+(?!user_version|foreign_keys)|ALTER|CREATE\s+(TABLE|INDEX|VIEW)(?!\s))", code.replace("CREATE TEMP TABLE", "")))
        self.assertIsNone(re.search(r"\bINSERT\s+INTO\s+(?!garde_009c_)", code))                    # seule l'insertion de la garde (table temporaire) est permise
        self.assertIsNone(re.search(r"\b(UPDATE|DELETE)\b(?![^;]*\bBEFORE\b)", re.sub(r"CREATE TRIGGER.*?END;", "", code, flags=re.S | re.I)))
        self.assertEqual(code.count("BEGIN"), 1)                                                     # le BEGIN du corps du trigger, aucune transaction
        for m in re.findall(r"RAISE\(ABORT, '((?:[^']|'')*)'\)", code):
            self.assertTrue(m.isascii(), m)
            self.assertTrue(m.startswith("INV-44: "), m)

    def test_009c_A_objets_exacts_seul_le_trigger_est_recree_au_rang_15(self):
        avant, apres = schema(B.migrer14()), schema(self.db)
        self.assertEqual(set(apres), set(avant))                                                     # aucun objet créé, aucun supprimé
        modifies = {k for k in avant if avant[k] != apres[k]}
        self.assertEqual(modifies, {("trigger", TRIGGER)})                                           # le seul objet modifié, au caractère près
        self.assertEqual(apres[("trigger", TRIGGER)][0], "bons_commande")
        self.assertEqual(_norm(apres[("trigger", TRIGGER)][1]), trigger_009c())
        self.assertNotEqual(_norm(avant[("trigger", TRIGGER)][1]), trigger_009c())                  # la définition de 009a est bien remplacée

    def test_009c_A_la_garde_refuse_toute_base_qui_n_est_pas_au_rang_14(self):
        for rang, base in ((12, P.migrer12()), (13, B.migrer13()), (15, migrer15())):
            with self.subTest(rang=rang):
                avant = (schema(base), T.db_user_version(base))
                with self.assertRaisesRegex(sqlite3.IntegrityError, "009c exige user_version = 14"):
                    T.runner(base, RANG, SQL_009C)
                self.assertEqual((schema(base), T.db_user_version(base)), avant)                     # ROLLBACK intégral : ni trigger, ni user_version, ni table temporaire
                self.assertEqual(base.execute("SELECT name FROM sqlite_temp_master WHERE name LIKE 'garde_009c%'").fetchall(), [])

    def test_009c_A_une_base_peuplee_au_rang_14_est_migree_sans_perte(self):
        t = self._sur(B.migrer14())
        bc = t.bc6000()
        f = t.acompte(bc, bc.d[0], "100.00")
        t.encaisse(f, "40.00")
        avant = t.instantane()
        T.runner(t.db, RANG, SQL_009C)
        self.assertEqual(t.instantane(), avant)                                                      # aucune donnée lue ni modifiée
        self.assertEqual(T.db_user_version(t.db), 15)
        t.refuse(bc.b, M_ENCAISSEMENT)

    def test_009c_A_un_BC_annule_avant_009c_reste_tel_quel(self):
        # CONSTAT : 009a laisse annuler un BC dont l'acompte est neutralisé ; 009c ne relit ni ne corrige ce BC (aucune donnée n'est touchée).
        t = self._sur(B.migrer14())
        bc = t.bc6000()
        f = t.acompte(bc, bc.d[0], "100.00")
        t.avoir(f)
        t.annuler_bc(bc.b)
        avant = (t.instantane(), t.tous("SELECT * FROM bons_commande ORDER BY id"))
        T.runner(t.db, RANG, SQL_009C)
        self.assertEqual((t.instantane(), t.tous("SELECT * FROM bons_commande ORDER BY id")), avant)
        self.assertEqual(t.statut(bc.b)[0], "annule")


# --------------------------------------------------------------------------------------------------------------------
# B — encaissements (condition 1)
# --------------------------------------------------------------------------------------------------------------------
class Encaissements(Base15):
    def test_INV_44_B1_encaissement_actif_sur_un_acompte_annulation_refusee(self):
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc, f = self.avec("acompte")
                self.encaisse(f, "40.00")                                                            # règlement partiel : l'acompte n'est plus « non réglé »
                self.etat(bc, etat)
                self.refuse(bc.b, M_ENCAISSEMENT)
                with self.assertRaisesRegex(sqlite3.IntegrityError, M_ENCAISSEMENT):
                    self.annuler_bc(bc.b)
                self.assertEqual(self.statut(bc.b)[0], "termine" if etat == "termine" else "en_cours")

    def test_INV_44_B2_encaissement_actif_sur_une_facture_de_solde_annulation_refusee(self):
        bc, so = self.avec("solde")
        self.encaisse_tout(so)
        self.refuse(bc.b, M_ENCAISSEMENT)

    def test_INV_44_B3_encaissement_actif_sur_une_situation_annulation_refusee(self):
        bc, s = self.avec("situation")
        self.encaisse_tout(s)
        self.refuse(bc.b, M_ENCAISSEMENT)

    def test_INV_44_B4_encaissement_actif_malgre_la_neutralisation_de_la_facture_par_avoir(self):
        for type_ in ("acompte", "situation", "solde"):
            with self.subTest(type=type_):
                bc, f = self.avec(type_)
                self.encaisse_tout(f)                                                                # facture réglée, puis intégralement créditée
                self.avoir(f)
                self.assertTrue(self.neutralisee(f))
                self.refuse(bc.b, M_ENCAISSEMENT)

    def test_INV_44_B5_encaissement_actif_sur_acompte_neutralise_refus_meme_si_l_avoir_est_correction_erreur(self):
        bc, f = self.avec("acompte")
        self.encaisse(f, "100.00")
        self.avoir(f)                                                                                 # avoir total de motif correction_erreur
        self.assertEqual([m for (_, _, m) in self.avoirs_de(f)], ["correction_erreur"])
        self.assertEqual(self.nette(bc), 0)
        self.refuse(bc.b, M_ENCAISSEMENT)

    def test_INV_44_B6_encaissement_annule_ne_bloque_pas_comme_encaissement_actif(self):
        bc, f = self.avec("acompte")
        r = self.encaisse(f, "100.00")
        self.annuler(r)
        self.assertEqual(self.un("SELECT COUNT(*) FROM reglements WHERE cancelled_at IS NULL")[0], 0)
        self.refuse(bc.b, M_ACOMPTE)                                                                 # refus pour l'acompte non neutralisé, pas pour l'encaissement
        self.avoir(f)
        self.accepte(bc.b)

    def test_INV_44_B7_annuler_l_encaissement_leve_le_blocage_apres_neutralisation(self):
        bc, f = self.avec("acompte")
        r = self.encaisse(f, "100.00")
        self.avoir(f)
        self.refuse(bc.b, M_ENCAISSEMENT)
        self.annuler(r)
        self.accepte(bc.b)

    def test_INV_44_B8_encaissement_importe_deja_annule_ne_bloque_pas(self):
        bc, f = self.avec("acompte")
        self.encaisse(f, "100.00", origine="import", legacy_id="V2-REG-1", cancelled_at=TS_ANNUL, motif_annulation="Import V2 : annule")
        self.assertEqual(self.un("SELECT origine, cancelled_at IS NOT NULL FROM reglements")[0:2], ("import", 1))
        self.refuse(bc.b, M_ACOMPTE)
        self.avoir(f)
        self.accepte(bc.b)

    def test_INV_44_B9_un_encaissement_annule_et_un_encaissement_actif_bloquent(self):
        bc, f = self.avec("acompte")
        r1 = self.encaisse(f, "30.00")
        self.annuler(r1)
        self.encaisse(f, "30.00")
        self.refuse(bc.b, M_ENCAISSEMENT)

    def test_INV_44_B10_les_reglements_d_un_autre_BC_sont_sans_effet(self):
        bc_a, fa = self.avec("acompte")
        bc_b, fb = self.avec("acompte")
        self.encaisse_tout(fb)                                                                       # encaissement actif sur le BC B seulement
        self.avoir(fa)
        self.accepte(bc_a.b)
        self.refuse(bc_b.b, M_ENCAISSEMENT)
        self.annuler_bc(bc_a.b)
        self.assertEqual(self.statut(bc_a.b)[0], "annule")
        self.assertEqual(self.statut(bc_b.b)[0], "en_cours")

    def test_INV_44_B11_un_remboursement_n_est_pas_un_encaissement_actif(self):
        # État fabriqué par isolement (seul tr_103 conservé) : les gardes de 007 interdisent un remboursement actif sans encaissement actif.
        t = self.isole({TRIGGER})
        bc, f = t.avec("acompte")
        av = t.avoir(f)
        t.rembourse(av, "10.00")
        self.assertEqual(t.tous("SELECT type, cancelled_at FROM reglements"), [("remboursement", None)])
        t.accepte(bc.b)
        t.annuler_bc(bc.b)
        self.assertEqual(t.statut(bc.b)[0], "annule")

    def test_INV_44_B12_un_remboursement_avec_son_encaissement_actif_bloque_par_l_encaissement(self):
        bc, f = self.avec("acompte")
        self.encaisse(f, "100.00")
        av = self.avoir(f)
        self.rembourse(av, "100.00")                                                                  # 007 : remboursement ≤ crédit disponible
        self.assertEqual(sorted(t for (t,) in self.tous("SELECT type FROM reglements")), ["encaissement", "remboursement"])
        self.refuse(bc.b, M_ENCAISSEMENT)

    def test_INV_44_B13_le_lien_passe_par_la_facture_du_BC_pas_par_les_dates_ni_les_numeros(self):
        # un encaissement sur une facture d'un autre BC (même client, même devis impossible) ne se confond pas : deux BC du même client
        bc_a, fa = self.avec("acompte")
        bc_b = self.monde(devis=[{"lignes": ["4000.00"], "acompte": ("montant", "500.00")}], client_id=self.un("SELECT client_id FROM bons_commande WHERE id=?", bc_a.b)[0])
        fb = self.acompte(bc_b, bc_b.d[0], "50.00")
        self.encaisse_tout(fb)
        self.avoir(fa)
        self.accepte(bc_a.b)
        self.refuse(bc_b.b, M_ENCAISSEMENT)


# --------------------------------------------------------------------------------------------------------------------
# C — situation, solde, acompte (conditions 2, 3 et 4)
# --------------------------------------------------------------------------------------------------------------------
class Factures(Base15):
    def test_INV_44_C1_une_situation_emise_bloque_meme_neutralisee_par_avoir(self):
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc, s = self.avec("situation")
                self.etat(bc, etat)
                self.refuse(bc.b, M_SITUATION)                                                       # non créditée
                self.avoir(s)
                self.assertTrue(self.neutralisee(s))
                self.assertEqual(self.nette(bc), 0)
                self.refuse(bc.b, M_SITUATION)                                                       # intégralement créditée : toujours refusée

    def test_INV_44_C2_une_situation_partiellement_creditee_bloque(self):
        bc, s = self.avec("situation")
        self.avoir(s, "10.00")
        self.refuse(bc.b, M_SITUATION)

    def test_INV_44_C3_une_facture_de_solde_bloque_meme_si_le_net_apres_avoirs_est_nul(self):
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc, so = self.avec("solde")
                self.etat(bc, etat)
                self.refuse(bc.b, M_AUTRE_FACTURE)
                self.avoir(so)
                self.assertTrue(self.neutralisee(so))
                self.assertEqual(self.nette(bc), 0)
                self.refuse(bc.b, M_AUTRE_FACTURE)

    def test_INV_44_C4_situation_solde_et_encaissement_combines(self):
        bc = self.bc6000()
        s = self.situation(bc, "100.00", 1, "0.00")
        self.encaisse(s, "100.00")
        so = self.solde_final(bc)
        self.refuse(bc.b, M_ENCAISSEMENT)                                                            # l'encaissement est évalué en premier
        self.avoir(s)
        self.avoir(so)
        self.assertEqual(self.nette(bc), 0)
        self.refuse(bc.b, M_ENCAISSEMENT)                                                            # même tout crédité
        self.annuler(self.un("SELECT id FROM reglements")[0])
        self.refuse(bc.b, M_SITUATION)                                                               # sans encaissement : la situation bloque encore
        bc2 = self.bc6000()
        self.situation(bc2, "100.00", 1, "0.00")
        self.solde_final(bc2)
        self.refuse(bc2.b, M_SITUATION)

    def test_INV_44_C5_acompte_non_regle_non_neutralise_annulation_refusee(self):
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc, f = self.avec("acompte")
                self.etat(bc, etat)
                self.refuse(bc.b, M_ACOMPTE)

    def test_INV_44_C6_acompte_non_regle_integralement_neutralise_par_correction_erreur_annulation_autorisee(self):
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc, f = self.avec("acompte")
                self.etat(bc, etat)
                a = self.avoir(f)                                                                    # avoir total, motif correction_erreur (défaut de Base14)
                self.assertEqual(self.avoirs_de(f), [(a, "100.00", "correction_erreur")])
                avant = self.instantane()
                self.accepte(bc.b)
                self.annuler_bc(bc.b)
                self.assertEqual(self.statut(bc.b)[0], "annule")
                self.assertEqual(self.instantane(), avant)                                           # factures, lignes, avoirs, règlements : strictement intacts
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 2)

    def test_INV_44_C7_neutralisation_incomplete_annulation_refusee(self):
        bc, f = self.avec("acompte")
        self.avoir(f, "10.00")
        self.refuse(bc.b, M_ACOMPTE)
        self.avoir(f, "89.99")                                                                        # il reste 0.01
        self.refuse(bc.b, M_ACOMPTE)
        self.avoir(f, "0.01")
        self.accepte(bc.b)

    def test_INV_44_C8_avoirs_partiels_correction_erreur_cumules_jusqu_a_zero_annulation_autorisee(self):
        bc, f = self.avec("acompte")
        for part in ("40.00", "35.00", "25.00"):
            self.avoir(f, part)
        self.assertEqual(self.nette(bc), 0)
        self.accepte(bc.b)

    def test_INV_44_C9_avoir_absent_annulation_refusee_puis_acceptee_apres_l_avoir(self):
        bc, f = self.avec("acompte")
        self.assertEqual(self.avoirs_de(f), [])
        self.refuse(bc.b, M_ACOMPTE)
        self.avoir(f)
        self.accepte(bc.b)

    def test_INV_44_C10_un_avoir_total_d_un_autre_motif_ne_vaut_pas_neutralisation(self):
        # CONSTAT : depuis 009b (tr_23), un avoir sur acompte ne peut être que correction_erreur ; un avoir d'un autre motif n'existe que dans une base antérieure à 009b
        # (006 laissait le motif libre). État fabriqué par isolement (seul tr_103 conservé).
        t = self.isole({TRIGGER})
        bc, f = t.avec("acompte")
        t.avoir(f, motif_avoir="Erreur de facturation")
        t.refuse(bc.b, M_ACOMPTE)
        bc2, f2 = t.avec("acompte")
        t.avoir(f2, "60.00", motif_avoir="correction_erreur")
        t.avoir(f2, "40.00", motif_avoir="prestation_non_realisee")
        t.refuse(bc2.b, M_ACOMPTE)                                                                    # net nul, mais un avoir n'est pas correction_erreur

    def test_INV_44_C11_tr_23_n_accepte_sur_un_acompte_que_correction_erreur_la_dispense_ne_s_etend_pas(self):
        bc, f = self.avec("acompte")
        m = self.tente_f(bc, "avoir", "100.00", origine_facture_id=f, motif_avoir="prestation_non_realisee")
        self.assertRegex(m, "INV-76")
        m = self.tente_f(bc, "avoir", "100.00", origine_facture_id=f, motif_avoir="Annulation du BC")
        self.assertRegex(m, "INV-76")
        self.assertEqual(self.avoirs_de(f), [])

    def test_INV_44_C12_plusieurs_acomptes_sur_plusieurs_devis_tous_doivent_etre_neutralises(self):
        bc = self.monde_devis([("1000.00", "montant", "300.00"), ("500.00", "montant", "300.00")])
        a1 = self.acompte(bc, bc.d[0], "100.00")
        a2 = self.acompte(bc, bc.d[1], "100.00")
        self.refuse(bc.b, M_ACOMPTE)
        self.avoir(a1)
        self.refuse(bc.b, M_ACOMPTE)                                                                  # le second acompte reste à neutraliser
        self.avoir(a2)
        self.accepte(bc.b)

    def test_INV_44_C13_acompte_neutralise_puis_remplace_le_nouvel_acompte_bloque_a_son_tour(self):
        bc, f = self.avec("acompte")
        self.avoir(f)
        f2 = self.acompte(bc, bc.d[0], "80.00")                                                       # INV-52 : nouvel acompte possible après neutralisation totale
        self.refuse(bc.b, M_ACOMPTE)
        self.avoir(f2)
        self.accepte(bc.b)

    def test_INV_44_C16_defense_un_sur_credit_d_acompte_n_est_pas_une_neutralisation(self):
        # État inatteignable avec les gardes livrées (tr_23 : Σ avoirs <= total de l'origine, INV-76), fabriqué par isolement : l'égalité exacte du net est exigée.
        t = self.isole({TRIGGER})
        bc, f = t.avec("acompte")
        t.avoir(f)
        t.avoir(f, "10.00")
        self.assertGreater(sum(c(x) for (_, x, _) in t.avoirs_de(f)), c(t.montant(f)))
        t.refuse(bc.b, M_ACOMPTE)

    def test_INV_44_C14_un_acompte_prevu_au_devis_n_est_pas_une_facture(self):
        bc = self.bc6000()
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 0)
        self.accepte(bc.b)
        self.annuler_bc(bc.b)
        self.assertEqual(self.statut(bc.b)[0], "annule")

    def test_INV_44_C15_une_facture_autre_qu_un_acompte_bloque_aussi_avec_un_acompte_neutralise(self):
        bc = self.bc6000()
        a = self.acompte(bc, bc.d[0], "100.00")
        self.avoir(a)
        self.accepte(bc.b)
        so = self.solde_final(bc)
        self.refuse(bc.b, M_AUTRE_FACTURE)
        self.avoir(so)
        self.refuse(bc.b, M_AUTRE_FACTURE)


# --------------------------------------------------------------------------------------------------------------------
# D — ordre des opérations et atomicité
# --------------------------------------------------------------------------------------------------------------------
class OrdreEtAtomicite(Base15):
    def test_INV_44_D1_ordre_inverse_annuler_le_BC_avant_l_avoir_est_refuse(self):
        bc, f = self.avec("acompte")
        avant = self.instantane()
        with self.assertRaisesRegex(sqlite3.IntegrityError, M_ACOMPTE):
            self.annuler_bc(bc.b)
        self.assertEqual(self.statut(bc.b)[0], "en_cours")
        self.assertEqual(self.instantane(), avant)
        self.avoir(f)                                                                                 # l'avoir ne peut venir qu'AVANT l'annulation
        self.annuler_bc(bc.b)
        self.assertEqual(self.statut(bc.b)[0], "annule")

    def test_INV_44_D2_service_emule_succes_avoir_total_puis_annulation_dans_une_transaction(self):
        bc, f = self.avec("acompte")
        self.service_annulation(bc)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.statut(bc.b)[0], "annule")
        self.assertEqual(self.avoirs_de(f)[0][1:], ("100.00", "correction_erreur"))
        self.assertEqual(self.nette(bc), 0)

    def test_INV_44_D3_service_emule_un_refus_de_l_annulation_defait_aussi_l_avoir(self):
        bc, f = self.avec("acompte")
        self.encaisse(f, "40.00")                                                                     # l'avoir passe (007 ne le lit pas), l'annulation est refusée
        avant = self.instantane()
        with self.assertRaisesRegex(sqlite3.IntegrityError, M_ENCAISSEMENT):
            self.service_annulation(bc)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.instantane(), avant)                                                    # aucune neutralisation partielle ne subsiste
        self.assertEqual(self.nb_avoirs(), 0)
        self.assertEqual(self.statut(bc.b)[0], "en_cours")

    def test_INV_44_D4_service_emule_une_situation_bloque_et_aucun_avoir_ne_subsiste(self):
        bc = self.bc6000()
        a = self.acompte(bc, bc.d[0], "100.00")
        self.situation(bc, "100.00", 1, "100.00")
        avant = self.instantane()
        with self.assertRaisesRegex(sqlite3.IntegrityError, M_SITUATION):
            self.service_annulation(bc)
        self.assertEqual(self.instantane(), avant)
        self.assertEqual(self.avoirs_de(a), [])
        self.assertEqual(self.statut(bc.b)[0], "en_cours")

    def test_INV_44_D5_service_emule_echec_intermediaire_entre_l_avoir_et_l_annulation(self):
        bc, f = self.avec("acompte")
        avant = self.instantane()

        def panne():
            self.assertEqual(self.nb_avoirs(), 1)                                                     # l'avoir existe dans la transaction
            raise RuntimeError("panne entre l'avoir et l'annulation")

        with self.assertRaisesRegex(RuntimeError, "panne"):
            self.service_annulation(bc, entre=panne)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.instantane(), avant)
        self.assertEqual(self.nb_avoirs(), 0)
        self.assertEqual(self.statut(bc.b)[0], "en_cours")

    def test_INV_44_D6_service_emule_plusieurs_acomptes_un_refus_defait_tous_les_avoirs(self):
        bc = self.monde_devis([("1000.00", "montant", "300.00"), ("500.00", "montant", "300.00")])
        a1 = self.acompte(bc, bc.d[0], "100.00")
        a2 = self.acompte(bc, bc.d[1], "100.00")
        self.encaisse(a2, "10.00")
        avant = self.instantane()
        with self.assertRaisesRegex(sqlite3.IntegrityError, M_ENCAISSEMENT):
            self.service_annulation(bc)
        self.assertEqual(self.instantane(), avant)
        self.assertEqual(self.avoirs_de(a1) + self.avoirs_de(a2), [])

    def test_INV_44_D7_CONSTAT_sans_transaction_l_avoir_seul_persiste_et_la_base_reste_coherente(self):
        # LIMITE ASSUMÉE : SQLite ne peut pas imposer que l'avoir et l'annulation soient dans la même transaction. Un service qui commit l'avoir puis voit l'annulation
        # refusée laisse un acompte neutralisé et un BC en cours : état valide, aucune annulation partielle ; l'atomicité est la responsabilité du service.
        bc, f = self.avec("acompte")
        self.encaisse(f, "40.00")
        self.avoir(f)                                                                                 # autocommit : persiste
        self.refuse(bc.b, M_ENCAISSEMENT)
        self.assertEqual(self.nb_avoirs(), 1)
        self.assertEqual(self.statut(bc.b)[0], "en_cours")
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_INV_44_D8_un_UPDATE_multi_BC_dont_un_est_bloque_est_refuse_en_entier(self):
        libre, f1 = self.avec("acompte")
        self.avoir(f1)
        bloque, f2 = self.avec("acompte")
        self.db.execute("SAVEPOINT multi")
        try:
            with self.assertRaisesRegex(sqlite3.IntegrityError, M_ACOMPTE):
                self.db.execute("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='Client renonce', completed_at=NULL, date_100_facture=NULL, updated_at=? "
                                "WHERE id IN (?, ?)", (TS_ANNUL, T.TS, libre.b, bloque.b))
        finally:
            self.db.execute("ROLLBACK TO multi")
            self.db.execute("RELEASE multi")
        self.assertEqual((self.statut(libre.b)[0], self.statut(bloque.b)[0]), ("en_cours", "en_cours"))


# --------------------------------------------------------------------------------------------------------------------
# E — messages
# --------------------------------------------------------------------------------------------------------------------
class Messages(Base15):
    def test_009c_E_quatre_messages_distincts_prefixes_INV_44_et_ASCII(self):
        msgs = re.findall(r"RAISE\(ABORT, '((?:[^']|'')*)'\)", T.sans_commentaires(SQL_009C))
        self.assertEqual(len(msgs), 4)
        self.assertEqual(len(set(msgs)), 4)
        for m in msgs:
            self.assertTrue(m.startswith("INV-44: annulation du bon de commande interdite"), m)
            self.assertTrue(m.isascii(), m)
        for motif, m in zip((M_ENCAISSEMENT, M_SITUATION, M_AUTRE_FACTURE, M_ACOMPTE), msgs):
            self.assertRegex(m.replace("''", "'"), motif)

    def test_009c_E_chaque_cause_produit_son_message(self):
        bc, f = self.avec("acompte")
        self.refuse(bc.b, M_ACOMPTE)
        self.encaisse(f, "10.00")
        self.refuse(bc.b, M_ENCAISSEMENT)
        bc2, s = self.avec("situation")
        self.refuse(bc2.b, M_SITUATION)
        bc3, so = self.avec("solde")
        self.refuse(bc3.b, M_AUTRE_FACTURE)

    def test_009c_E_l_ordre_d_evaluation_est_encaissement_situation_autre_facture_acompte(self):
        bc = self.bc6000()
        a = self.acompte(bc, bc.d[0], "100.00")
        s = self.situation(bc, "100.00", 1, "100.00")
        self.refuse(bc.b, M_SITUATION)                                                               # situation + acompte non neutralisé
        self.encaisse(a, "10.00")
        self.refuse(bc.b, M_ENCAISSEMENT)                                                            # + encaissement actif

    def test_009c_E_le_message_ne_se_confond_pas_avec_un_refus_d_un_autre_trigger(self):
        bc, f = self.avec("acompte")
        m = self.tente_f(bc, "avoir", "999.00", origine_facture_id=f)
        self.assertIsNotNone(m)
        self.assertNotRegex(m, RE_INV44)


# --------------------------------------------------------------------------------------------------------------------
# F — non-régression
# --------------------------------------------------------------------------------------------------------------------
class NonRegression(Base15):
    def test_009c_F_un_BC_sans_facture_s_annule_comme_avant(self):
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc6000()
                self.etat(bc, etat)
                self.accepte(bc.b)

    def test_009c_F_le_trigger_ne_s_applique_qu_a_la_transition_vers_annule(self):
        bc, f = self.avec("acompte")
        self.encaisse(f, "100.00")
        self.geler_bc(bc.b)                                                                            # autres transitions et autres colonnes : aucun effet de tr_103
        self.terminer_bc(bc.b)
        self.assertEqual(self.statut(bc.b)[0], "termine")
        self.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (T.TS2, bc.b))
        self.refuse(bc.b, M_ENCAISSEMENT)

    def test_009c_F_un_BC_deja_annule_reste_terminal_et_un_avoir_reste_possible(self):
        bc, f = self.avec("acompte")
        self.avoir(f, "60.00")
        self.avoir(f, "40.00")
        self.annuler_bc(bc.b)
        self.assertEqual(self.statut(bc.b)[0], "annule")
        with self.assertRaises(sqlite3.IntegrityError) as cm:                                         # INV-173 : un BC annulé est terminal (tr_12), pas de message INV-44
            self.db.execute("UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (bc.b,))
        self.assertNotRegex(str(cm.exception), RE_INV44)
        self.assertIsNotNone(self.tente_f(bc, "acompte", "10.00", devis_id=bc.d[0]))                  # INV-188 : plus de nouvelle facture d'acompte, de situation ni de solde

    def test_009c_F_les_gardes_de_facturation_et_de_reglement_restent_en_place(self):
        bc, f = self.avec("acompte")
        self.assertRegex(self.tente_f(bc, "acompte", "10.00", devis_id=bc.d[0]), "INV-52")             # un seul acompte actif par devis
        self.assertRegex(self.essaie("UPDATE factures SET objet='x' WHERE id=?", f), "INV-53")
        self.assertRegex(self.essaie("DELETE FROM factures WHERE id=?", f), "INV-06")
        self.assertRegex(self.tente_r(f, "encaissement", "500.00"), "INV-72")

    def test_009c_F_la_couverture_des_situations_et_l_ordre_acompte_situation_ne_changent_pas(self):
        bc = self.bc6000()
        s = self.situation(bc, "100.00", 1, "0.00")
        self.assertEqual(self.couverture(s), [bc.d[0]])                                               # TR-104/TR-105, INV-205
        self.assertRegex(self.tente_f(bc, "acompte", "10.00", devis_id=bc.d[0]), "INV-205")
        self.refuse(bc.b, M_SITUATION)

    def test_009c_F_le_trigger_ne_modifie_aucune_donnee(self):
        bc, f = self.avec("acompte")
        avant = (self.instantane(), self.tous("SELECT * FROM bons_commande ORDER BY id"))
        self.refuse(bc.b, M_ACOMPTE)
        self.assertEqual((self.instantane(), self.tous("SELECT * FROM bons_commande ORDER BY id")), avant)


# --------------------------------------------------------------------------------------------------------------------
# G — immuabilité des migrations 006, 009a et 009b
# --------------------------------------------------------------------------------------------------------------------
class Immuabilite(Base15):
    def test_009c_G_les_migrations_006_009a_et_009b_sont_identiques_a_GitHub(self):
        for nom, empreinte in EMPREINTES_IMMUABLES.items():
            with self.subTest(fichier=nom):
                contenu = (MIGRATIONS / nom).read_bytes().replace(b"\r\n", b"\n")                      # core.autocrlf=true sous Windows : l'empreinte porte sur le blob Git (LF)
                self.assertEqual(hashlib.sha256(contenu).hexdigest(), empreinte)


# --------------------------------------------------------------------------------------------------------------------
# H — garde de chaîne : le trigger de 009c survit aux migrations suivantes
# --------------------------------------------------------------------------------------------------------------------
RE_SUPPRIME_LE_TRIGGER = re.compile(
    r"\bDROP\s+TABLE(\s+IF\s+EXISTS)?\s+bons_commande\b"
    r"|\bALTER\s+TABLE\s+bons_commande\s+RENAME\s+TO\b"
    r"|\bDROP\s+TRIGGER(\s+IF\s+EXISTS)?\s+" + TRIGGER + r"\b", re.I)


def problemes_de_recreation(sql, attendu=None):
    """Contrôle statique d'une migration ultérieure : liste vide si elle ne touche pas au trigger ou le recrée à l'identique de 009c."""
    attendu = attendu or trigger_009c()
    if not RE_SUPPRIME_LE_TRIGGER.search(T.sans_commentaires(sql)):
        return []
    for st in T.instructions(sql):
        code = T.sans_commentaires(st).strip()
        if re.match(r"CREATE\s+TRIGGER\s+" + TRIGGER + r"\b", code, re.I):
            return [] if _norm(code) == attendu else ["le trigger est recréé avec une définition différente"]
    return ["bons_commande ou le trigger est supprimé sans recréer " + TRIGGER]


def migrations_suivantes():
    """Migrations livrées après 009c (rang 16, 17, …) : vide tant que 010 n'existe pas."""
    return [(RANG + 1 + i, p.name, p.read_text(encoding="utf-8")) for i, p in enumerate(sorted(MIGRATIONS.glob("*.sql"))[RANG:])]


class GardeChaine(Base15):
    def definition(self, db):
        return [_norm(r[0]) for r in db.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (TRIGGER,))]

    def suite_conserve_le_trigger(self, suite):
        """Rejoue `suite` sur une base du rang 15 peuplée : le trigger reste identique à 009c et le refus reste effectif après chaque migration."""
        t = self._sur(migrer15())
        bc, _ = t.avec("acompte")
        for rang, nom, sql in suite:
            T.runner(t.db, rang, sql)
            self.assertEqual(self.definition(t.db), [trigger_009c()], nom)
            t.refuse(bc.b, M_ACOMPTE)

    def test_009c_H_le_trigger_est_identique_et_effectif_apres_chaque_migration_suivante(self):
        self.assertEqual(self.definition(self.db), [trigger_009c()])
        self.suite_conserve_le_trigger(migrations_suivantes())                                         # 010, 011, … quand elles existeront

    def test_009c_H_toute_migration_suivante_qui_supprime_bons_commande_recree_le_trigger(self):
        for rang, nom, sql in migrations_suivantes():
            with self.subTest(migration=nom):
                self.assertEqual(problemes_de_recreation(sql), [], nom)

    def test_009c_H_temoins_suppression_reconstruction_et_recreation(self):
        self.assertTrue(problemes_de_recreation(f"DROP TRIGGER {TRIGGER};"))
        self.assertTrue(problemes_de_recreation("CREATE TABLE bons_commande_new (id INTEGER);\nDROP TABLE bons_commande;\nALTER TABLE bons_commande_new RENAME TO bons_commande;"))
        corps = trigger_009c()
        self.assertEqual(problemes_de_recreation(f"DROP TRIGGER {TRIGGER};\n{corps};\n"), [])
        alteree = corps.replace(" AND OLD.statut <> 'annule'", "")
        self.assertNotEqual(alteree, corps)
        self.assertTrue(problemes_de_recreation(f"DROP TRIGGER {TRIGGER};\n{alteree};\n"))
        self.suite_conserve_le_trigger([(16, "x_recree.sql", f"DROP TRIGGER {TRIGGER};\n{corps};\n")])
        with self.assertRaises(AssertionError):
            self.suite_conserve_le_trigger([(16, "x_altere.sql", f"DROP TRIGGER {TRIGGER};\n{alteree};\n")])
        with self.assertRaises(AssertionError):
            self.suite_conserve_le_trigger([(16, "x_supprime.sql", f"DROP TRIGGER {TRIGGER};")])

    def test_009c_H_temoin_les_migrations_qui_ne_touchent_pas_au_trigger_ne_sont_pas_signalees(self):
        self.assertEqual(problemes_de_recreation("CREATE TABLE autre (id INTEGER);\nALTER TABLE bons_commande ADD COLUMN x TEXT;"), [])
        self.assertEqual(problemes_de_recreation("-- DROP TABLE bons_commande dans un commentaire\nCREATE INDEX i ON factures(bc_id);"), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
