"""T-53 — Couverture des situations par les devis (migration 009b révisée, rang 14) : 13 tests d'acceptation [INV-204, INV-205, D-62].

Source : modèle SQLite V3.14, §13.3 (ligne T-53), §4.8 ter, §8 (TR-22, TR-104, TR-105), §14 (CK-21, CK-22), §15 (D-62), cas C-43 (§13.1).
Les tests sont numérotés comme dans la ligne T-53 du modèle (01 à 13) et portent le nom de l'invariant qu'ils vérifient :
  01 INV-205  acompte refusé sur un devis couvert (C-43 étapes 2 et 7), horodatages identiques ou inversés ; témoin sans couverture
  02 INV-205  acompte accepté sur un devis rattaché après la situation (C-43 étape 4) ; aucune rétroactivité [INV-204]
  03 INV-204  nouvelle situation après A et B : elle couvre A et B, l'ancienne garde {A} ; exhaustivité contre bc_devis
  04 INV-204  situation entièrement créditée : couverture inchangée, acompte toujours refusé [INV-205]
  05 INV-204  devis couvert à 0 % d'avancement propre : couvert, acompte refusé [INV-205]
  06 INV-204  couverture d'un devis d'un autre BC refusée (TR-104)
  07 INV-204  couverture d'une facture qui n'est pas une situation refusée (TR-104)
  08 INV-204  UPDATE, DELETE et INSERT OR REPLACE refusés (TR-105) ; DELETE de la facture ou du devis couvert refusé
  09 INV-204  échec injecté en cours d'émission : ni situation, ni lignes, ni couverture ; trou de numérotation toléré
  10 INV-52 / 57 / 58  plafonds d'acompte, situation à 0.00, autres contrôles de TR-22 : aucune régression
  11 D-62     garde de migration : refus si une situation existe (base et user_version inchangés), acceptation sinon
  12 INV-204  CK-21 et CK-22 détectent chacun leur anomalie et ne bloquent rien (texte identique à celui du modèle)
  13 tous     rejeu 001 → 009a → 009b depuis une base vide et depuis le rang 12 ; 001 à 009 identiques à GitHub

Ce qui n'est PAS dans le SQL (règle de service, émulée ici) : la transaction d'émission (facture → lignes → UNE instruction
INSERT … SELECT sur bc_devis, dans la même BEGIN IMMEDIATE) et l'exhaustivité de la couverture. SQLite ne peut pas l'imposer ; ces tests la vérifient
sur le service émulé, et CK-21 / CK-22 la contrôlent a posteriori (limite assumée : omission partielle sur la dernière situation).
Hors périmètre (aucune règle ajoutée, aucun test) : PT-11 / M3, annulation du BC (H6), situations de montant nul (le test 10 ne vérifie que le refus déjà livré).
Le lanceur de migrations n'est pas dans le dépôt : il est émulé (test_005b : T.runner), comme pour les autres migrations.

Exécution : python3 src-tauri/tests/metier/test_009b_couverture_situations.py
"""
import hashlib
import pathlib
import re
import sqlite3
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_009b_acompte_garanties_manuelles as B  # noqa: E402  (chaîne 001 à 009b, fabriques)

P, T = B.P, B.T
c = B.c
MIGRATIONS = B.MIGRATIONS
RACINE = MIGRATIONS.parents[2]
MODELE = RACINE / "docs" / "conception" / "modèle-données-sqlite-v6-v3.14.md"

# Empreintes SHA-256 des migrations 001 à 009 telles que publiées sur GitHub (main da2969a) : elles sont immuables.
EMPREINTES_001_A_009 = {
    "001_initial.sql": "e7ab947981ef346b662b172dd7922ab633af0c4bde5fcee2db925cc92075ea8e",
    "002_fournisseurs.sql": "885b5dabb83bfe0f131e851d33a5bcb5b9faaab4dc41e3fde08bdb1a117ada37",
    "003_devis.sql": "02806db245262d0c0df575d824259bf5d748f09130f80b5d6b18732cc7255c7c",
    "004_bons_commande.sql": "8aff888dacd059720c9263d208121d8038ddaa176583fd4c7c424473b741b932",
    "005_depenses.sql": "f1b72932c0d512f7324422704556e12105f054e949c006004c6ea7c55aa52648",
    "005a_corrections_v313.sql": "ba740482325114159c5f70daac287a9e75b5cde374ee7f6028ea705a103a0bf5",
    "005b_bc_multi_devis.sql": "00edf532de1eb05ffc638390097aaa4104d8361d3aed4456b9cf84c26d486209",
    "005c_bc_annule_caches_financiers.sql": "88297bf0eb248a68b5d4ebb288742f401d0460497a75d3e5b01494b0855b970a",
    "006_facturation.sql": "085c702176b25ee943ca7a95a741eed6a528cfb0864f74e4b3f3ba74ebc18c8e",
    "007_reglements.sql": "354d7031bda4f6de3a56daee0428abd8ccca8eed144a42e2efe8254048488242",
    "008_garanties.sql": "d1e10df57a507031fc1832de47c67349a06a54a427fa0e5c57049dbb85a348fe",
    "009_pv.sql": "764a2d302969f471bad2e6770f57454eff7659ebd886e5c6aa6be14509d84cb3",
}

# Diagnostics du modèle V3.14, §14 (le test 12 vérifie que ce texte est identique à celui du modèle).
CK_21 = """SELECT f.id FROM factures f
 WHERE f.type = 'situation'
   AND NOT EXISTS (SELECT 1 FROM situation_devis c WHERE c.facture_id = f.id)"""
CK_22 = """SELECT s1.id AS situation_ancienne, s2.id AS situation_recente, c1.devis_id
  FROM factures s1
  JOIN factures s2 ON s2.bc_id = s1.bc_id AND s2.type = 'situation'
                  AND s2.situation_numero > s1.situation_numero
  JOIN situation_devis c1 ON c1.facture_id = s1.id
 WHERE s1.type = 'situation'
   AND NOT EXISTS (SELECT 1 FROM situation_devis c2
                    WHERE c2.facture_id = s2.id AND c2.devis_id = c1.devis_id)"""

TS_AVANT = "2049-12-31T00:00:00.000Z"          # antérieur à la situation de test (TS_EMISSION = 2050-01-01)
TS_APRES = "2051-01-01T00:00:00.000Z"          # postérieur


class ErreurInjectee(Exception):
    """Échec simulé en cours de transaction d'émission."""


class Base53(B.Base14):
    # --- service d'émission émulé --------------------------------------------------------------------------------------------
    def pct(self, bc, p, devis=None):
        """{ligne de BC: avancement cumulé en centièmes} pour toutes les lignes du BC (ou celles des devis indiqués)."""
        return {bl: p for bl, did, _ in self.lignes_de_bc(bc) if devis is None or did in devis}

    def emission(self, bc, pcts):
        """Émission d'une situation comme le service : UNE transaction BEGIN IMMEDIATE = facture, lignes (emettre_situation), couverture
        (un seul INSERT … SELECT sur bc_devis), COMMIT."""
        self.assertFalse(self.db.in_transaction)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            f = self.emettre_situation(bc, pcts)
            self.couvrir(f, bc)
            self.db.execute("COMMIT")
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        return f

    def tentative_emission(self, etape, bc, numero, autre_bc=None):
        """Émission dont le service échoue à l'`etape` donnée (échec injecté, ou refus SQL réel) : ROLLBACK intégral ; retourne l'erreur."""
        self.assertFalse(self.db.in_transaction)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if etape == "apres_facture":
                self.facture(bc, "situation", "400.00", situation_numero=1, montant_deja_facture_ht="0.00", numero=numero)
            else:
                f = self.emettre_situation(bc, self.pct(bc, 4000))
                if etape in ("apres_couverture", "refus_trigger"):
                    self.couvrir(f, bc)
                if etape == "refus_trigger":                                                            # échec SQL réel : couverture d'un devis étranger au BC
                    self.db.execute("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", (f, autre_bc.d[0]))
            raise ErreurInjectee(etape)
        except (ErreurInjectee, sqlite3.IntegrityError) as e:
            self.db.execute("ROLLBACK")
            return e

    def devis_ids(self, bc):
        return [d for (d,) in self.tous("SELECT devis_id FROM bc_devis WHERE bc_id=? ORDER BY devis_id", bc.b)]

    def refus(self, sql, *args):
        """Message de l'erreur d'intégrité d'une instruction annulée juste après ; échec du test si elle réussit."""
        self.db.execute("SAVEPOINT refus53")
        try:
            self.db.execute(sql, args)
            m = None
        except sqlite3.IntegrityError as e:
            m = str(e)
        finally:
            self.db.execute("ROLLBACK TO refus53")
            self.db.execute("RELEASE refus53")
        self.assertIsNotNone(m, f"instruction acceptée à tort : {sql}")
        return m

    def acompte_sur(self, bc, d, total, **kw):
        """None si l'acompte serait accepté, sinon le message du refus (l'insertion est annulée)."""
        return self.tente_f(bc, "acompte", total, devis_id=d, **kw)

    def nette_de(self, facture):
        """Montant net d'une facture : son total moins les avoirs qui la créditent (centimes)."""
        tot = c(self.un("SELECT total_ht FROM factures WHERE id=?", facture)[0])
        return tot - sum(c(t) for (t,) in self.tous("SELECT total_ht FROM factures WHERE origine_facture_id=? AND type='avoir'", facture))

    def photo(self):
        """Contenu complet de toutes les tables de la base (pour prouver qu'une opération n'écrit rien)."""
        out = {}
        for (nom,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
            out[nom] = self.db.execute(f"SELECT * FROM {nom} ORDER BY 1, 2").fetchall()
        return out

    # --- scénario C-43 (modèle V3.14, §13.1) ---------------------------------------------------------------------------------
    def c43(self):
        """Étapes 1 à 7 de C-43. Retourne les observations de chaque étape (tout est lu dans la base)."""
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        r = types.SimpleNamespace(bc=bc, A=bc.d[0])
        r.s1 = self.emission(bc, self.pct(bc, 4000))                                                    # étape 1 : S1 à 40 % cumulé
        r.s1_total = self.un("SELECT total_ht FROM factures WHERE id=?", r.s1)[0]
        r.couv_s1 = self.couverture(r.s1)
        r.m2 = self.acompte_sur(bc, r.A, "100.00")                                                      # étape 2
        r.B = self.devis_accepte_a(bc, "500.00", "pourcentage", "30.00")
        self.rattacher_a(bc, r.B)                                                                       # étape 3
        r.contractuel = self.contractuel(bc)
        r.couv_s1_apres_b = self.couverture(r.s1)
        r.m4 = self.acompte_sur(bc, r.B, "150.00")                                                      # étape 4 : contrôle puis émission réelle
        r.m4_depasse = self.acompte_sur(bc, r.B, "150.01")
        r.acompte_b = self.acompte(bc, r.B, "150.00")
        r.m4_second = self.acompte_sur(bc, r.B, "0.01")
        r.couv_b_avant_s2 = self.tous("SELECT facture_id FROM situation_devis WHERE devis_id=?", r.B)
        r.s2 = self.emission(bc, self.pct(bc, 6000))                                                    # étape 5 : S2 à 60 % cumulé
        r.s2_total = self.un("SELECT total_ht FROM factures WHERE id=?", r.s2)[0]
        r.couv_s2 = self.couverture(r.s2)
        r.avoir = self.avoir(r.s1)                                                                      # étape 6 : avoir total sur S1
        r.couv_s1_apres_avoir = self.couverture(r.s1)
        r.m7 = self.acompte_sur(bc, r.A, "100.00")                                                      # étape 7
        return r


# ====================================================================================================================
# T-53 — les 13 tests
# ====================================================================================================================
class T53(Base53):
    # 01 --------------------------------------------------------------------------------------------------------------------
    def test_INV_205_01_acompte_refuse_sur_un_devis_couvert_etapes_2_et_7_horodatages_indifferents_et_temoin(self):
        # Témoin : S1 émise SANS couverture enregistrée ; le même acompte est accepté, quels que soient les horodatages (aucune règle d'ordre implicite).
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        A = bc.d[0]
        s1 = self.emettre_situation(bc, self.pct(bc, 4000))
        self.assertEqual(self.un("SELECT total_ht FROM factures WHERE id=?", s1)[0], "400.00")
        self.assertEqual(self.couverture(s1), [])
        for ts in (None, TS_AVANT, TS_APRES):
            kw = {} if ts is None else {"created_at": ts}
            self.assertIsNone(self.acompte_sur(bc, A, "100.00", **kw), f"témoin : acompte refusé sans couverture (created_at={ts})")
        # La couverture est enregistrée (service d'émission) : le refus vient d'elle seule.
        self.couvrir(s1, bc)
        self.assertEqual(self.couverture(s1), [A])
        for ts in (None, TS_AVANT, TS_APRES):                                                           # identique, inversé (acompte « avant »), postérieur
            kw = {} if ts is None else {"created_at": ts}
            m = self.acompte_sur(bc, A, "100.00", **kw)
            self.assertIsNotNone(m, f"acompte accepté à tort sur un devis couvert (created_at={ts})")
            self.assertRegex(m, "INV-205: aucun acompte sur un devis deja couvert par une situation")
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE type='acompte'")[0], 0)
        # Étapes 2 et 7 de C-43 sur le scénario complet : refus dans les deux cas ; le montant net de S1 (0 à l'étape 7) n'intervient pas.
        r = self.c43()
        self.assertRegex(r.m2, "INV-205")
        self.assertRegex(r.m7, "INV-205")
        self.assertEqual(self.nette_de(r.s1), 0)
        # le refus vient bien de la couverture : ni solde, ni autre acompte sur A (les autres contrôles de TR-22 ne s'appliquent donc pas)
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE devis_id=?", r.A)[0], 0)
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=? AND type='solde'", r.bc.b)[0], 0)

    # 02 --------------------------------------------------------------------------------------------------------------------
    def test_INV_205_02_acompte_accepte_sur_un_devis_rattache_apres_la_situation_sans_retroactivite(self):
        r = self.c43()
        # étape 3 : B rattaché, contractuel 1 500.00, S1 reste {A}
        self.assertEqual(r.contractuel, c("1500.00"))
        self.assertEqual(r.couv_s1, [r.A])
        self.assertEqual(r.couv_s1_apres_b, [r.A])
        # étape 4 : B n'est couvert par aucune situation ; l'acompte de 150.00 (= 30 % × 500) est accepté puis émis
        self.assertEqual(r.couv_b_avant_s2, [])
        self.assertIsNone(r.m4, r.m4)
        self.assertEqual(self.un("SELECT type, bc_id, devis_id, total_ht FROM factures WHERE id=?", r.acompte_b), ("acompte", r.bc.b, r.B, "150.00"))
        # le plafond reste actif sur un devis non couvert : le centime au-dessus (ou un second acompte) est refusé par INV-57 / INV-52, jamais par INV-205
        self.assertRegex(r.m4_depasse, "INV-57")
        self.assertRegex(r.m4_second, "INV-52")
        self.assertNotRegex(r.m4_depasse + r.m4_second, "INV-205")
        # le rattachement et l'acompte n'ont créé aucune couverture : avant S2, seul S1 → {A} existait
        self.assertEqual(self.tous("SELECT facture_id, devis_id FROM situation_devis WHERE facture_id=?", r.s1), [(r.s1, r.A)])

    # 03 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_03_nouvelle_situation_apres_A_et_B_couvre_A_et_B_l_ancienne_garde_A(self):
        r = self.c43()
        self.assertEqual(r.s1_total, "400.00")
        self.assertEqual(r.s2_total, "350.00")                                                          # 900 − (400 + 150)
        self.assertEqual(r.couv_s1, [r.A])
        self.assertEqual(r.couv_s2, sorted([r.A, r.B]))
        self.assertEqual(self.couverture(r.s1), [r.A], "S1 ne devient jamais {A, B}")
        # exhaustivité : la couverture de S2 est EXACTEMENT l'ensemble des devis rattachés à son émission
        self.assertEqual(r.couv_s2, self.devis_ids(r.bc))
        self.assertEqual(self.un("SELECT COUNT(*) FROM situation_devis")[0], 3)
        # aucune situation sans couverture (CK-21), aucune couverture non monotone (CK-22)
        self.assertEqual(self.tous(CK_21), [])
        self.assertEqual(self.tous(CK_22), [])
        # trois devis rattachés avant l'émission : la couverture les contient tous, sans liste passée en paramètre
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00"), ("500.00", "pourcentage", "30.00"), ("300.00", "aucun", None)])
        s = self.emission(bc, self.pct(bc, 2000))
        self.assertEqual(len(bc.d), 3)
        self.assertEqual(self.couverture(s), sorted(bc.d))

    # 04 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_04_situation_entierement_creditee_couverture_inchangee_acompte_toujours_refuse(self):
        r = self.c43()
        self.assertEqual(self.un("SELECT type, origine_facture_id, total_ht FROM factures WHERE id=?", r.avoir), ("avoir", r.s1, "400.00"))
        self.assertEqual(self.nette_de(r.s1), 0)
        self.assertEqual(r.couv_s1_apres_avoir, [r.A])                                                  # étape 6 : couverture de S1 inchangée
        self.assertEqual(self.couverture(r.s1), [r.A])
        self.assertRegex(r.m7, "INV-205")                                                               # étape 7
        # cas isolé : un seul devis, une seule situation, totalement créditée, aucun autre document
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        s = self.emission(bc, self.pct(bc, 4000))
        self.avoir(s)
        self.assertEqual(self.nette(bc), 0)
        self.assertEqual(self.couverture(s), bc.d)
        for total in ("100.00", "0.01"):
            self.assertRegex(self.acompte_sur(bc, bc.d[0], total), "INV-205")
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE type='acompte' AND bc_id=?", bc.b)[0], 0)

    # 05 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_05_devis_couvert_a_0_pour_cent_d_avancement_propre_est_couvert_acompte_refuse(self):
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00"), ("500.00", "pourcentage", "30.00")])
        A, Bd = bc.d
        s = self.emission(bc, self.pct(bc, 4000, devis={A}))                                           # progrès sur A seul ; B reste à 0 %
        lignes_b = [bl for bl, did, _ in self.lignes_de_bc(bc) if did == Bd]
        avanc_b = self.tous("SELECT avancement_cumule_pct FROM facture_lignes WHERE facture_id=? AND type_ligne='avancement' AND bc_ligne_id IN (%s)" %
                            ",".join("?" * len(lignes_b)), s, *lignes_b)
        self.assertEqual(len(avanc_b), len(lignes_b))
        self.assertTrue(all(c(p) == 0 for (p,) in avanc_b), avanc_b)                                    # B : 0 % d'avancement propre
        self.assertEqual(self.couverture(s), sorted([A, Bd]))                                           # couvert malgré tout
        self.assertRegex(self.acompte_sur(bc, Bd, "150.00"), "INV-205")
        self.assertRegex(self.acompte_sur(bc, Bd, "0.01"), "INV-205")
        self.assertRegex(self.acompte_sur(bc, A, "100.00"), "INV-205")

    # 06 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_06_couverture_d_un_devis_d_un_autre_bc_refusee(self):
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        s = self.emission(bc, self.pct(bc, 4000))
        autre = self.monde_devis([("700.00", "pourcentage", "30.00")])                                  # devis rattaché à un AUTRE BC
        libre = self.devis_accepte_a(bc, "200.00", "aucun", None)                                       # devis accepté du même client, rattaché à aucun BC
        s_autre = self.emission(autre, self.pct(autre, 2000))
        avant = self.tous("SELECT facture_id, devis_id FROM situation_devis ORDER BY 1, 2")
        self.assertEqual(avant, sorted([(s, bc.d[0]), (s_autre, autre.d[0])]))
        for d, nom in ((autre.d[0], "devis d'un autre BC"), (libre, "devis non rattaché")):
            with self.subTest(devis=nom):
                m = self.refus("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", s, d)
                self.assertRegex(m, "INV-204: le devis couvert doit etre rattache au bon de commande de la situation")
        m = self.refus("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", s_autre, bc.d[0])
        self.assertRegex(m, "INV-204: le devis couvert doit etre rattache")
        # devis inexistant : il n'est rattaché à aucun BC, le trigger le refuse (INV-204) ; facture inexistante : refus par la clé étrangère, sans préfixe INV-
        m = self.refus("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", s, 987654)
        self.assertRegex(m, "INV-204: le devis couvert doit etre rattache")
        m = self.refus("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", 987654, bc.d[0])
        self.assertRegex(m, "FOREIGN KEY")
        self.assertNotIn("INV-", m)
        self.assertEqual(self.tous("SELECT facture_id, devis_id FROM situation_devis ORDER BY 1, 2"), avant)

    # 07 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_07_couverture_d_une_facture_qui_n_est_pas_une_situation_refusee(self):
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        A = bc.d[0]
        acompte = self.acompte(bc, A, "100.00")
        avoir = self.avoir(acompte, "40.00")
        solde = self.solde_final(bc)
        for f, type_ in ((acompte, "acompte"), (avoir, "avoir"), (solde, "solde")):
            with self.subTest(type=type_):
                self.assertEqual(self.un("SELECT type FROM factures WHERE id=?", f)[0], type_)
                m = self.refus("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", f, A)
                self.assertRegex(m, "INV-204: la couverture ne porte que sur une facture de type situation")
                # même par l'instruction du service d'émission (INSERT … SELECT) : refus
                m = self.refus("INSERT INTO situation_devis (facture_id, devis_id) SELECT ?, devis_id FROM bc_devis WHERE bc_id = ?", f, bc.b)
                self.assertRegex(m, "INV-204: la couverture ne porte que sur une facture de type situation")
        self.assertEqual(self.un("SELECT COUNT(*) FROM situation_devis")[0], 0)

    # 08 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_08_update_delete_replace_refuses_et_suppression_de_la_facture_ou_du_devis_couvert_refusee(self):
        r = self.c43()
        avant = self.photo()
        lignes = self.tous("SELECT facture_id, devis_id FROM situation_devis ORDER BY 1, 2")
        self.assertEqual(len(lignes), 3)
        f, d = lignes[0]
        autre_f, autre_d = lignes[-1]
        m = self.refus("UPDATE situation_devis SET devis_id = ? WHERE facture_id = ? AND devis_id = ?", autre_d, f, d)
        self.assertRegex(m, "INV-204: la couverture d'une situation ne se modifie jamais")
        m = self.refus("UPDATE situation_devis SET facture_id = ? WHERE facture_id = ? AND devis_id = ?", autre_f, f, d)
        self.assertRegex(m, "INV-204: la couverture d'une situation ne se modifie jamais")
        m = self.refus("UPDATE situation_devis SET devis_id = devis_id")                               # même sans changement de valeur
        self.assertRegex(m, "INV-204: la couverture d'une situation ne se modifie jamais")
        m = self.refus("DELETE FROM situation_devis WHERE facture_id = ? AND devis_id = ?", f, d)
        self.assertRegex(m, "INV-204: la couverture d'une situation ne se supprime jamais")
        m = self.refus("DELETE FROM situation_devis")
        self.assertRegex(m, "INV-204: la couverture d'une situation ne se supprime jamais")
        # INSERT OR REPLACE sur une clé existante : le DELETE implicite (recursive_triggers=ON) est refusé
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        m = self.refus("INSERT OR REPLACE INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", f, d)
        self.assertRegex(m, "INV-204: la couverture d'une situation ne se supprime jamais")
        # clé en double (INSERT simple) : refus de contrainte, sans préfixe INV-
        m = self.refus("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", f, d)
        self.assertRegex(m, "UNIQUE")
        self.assertNotIn("INV-", m)
        # suppression de la facture couverte ou du devis couvert : refusée (clé étrangère RESTRICT, ou règle propre de la table parente)
        for sql, arg in (("DELETE FROM factures WHERE id = ?", f), ("DELETE FROM devis WHERE id = ?", d)):
            self.assertTrue(self.refus(sql, arg), sql)
        # et la clé étrangère seule suffit : ni CASCADE, ni SET NULL (lu dans le schéma)
        fks = {(row[2], row[3], row[5], row[6]) for row in self.db.execute("PRAGMA foreign_key_list(situation_devis)").fetchall()}
        self.assertEqual(fks, {("factures", "facture_id", "RESTRICT", "RESTRICT"), ("devis", "devis_id", "RESTRICT", "RESTRICT")})
        self.assertEqual(self.photo(), avant)                                                           # aucune donnée de la base n'a bougé
        self.assertEqual(self.tous("SELECT facture_id, devis_id FROM situation_devis ORDER BY 1, 2"), lignes)

    # 09 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_09_echec_injecte_en_cours_d_emission_ni_situation_ni_lignes_ni_couverture_trou_de_numerotation_tolere(self):
        for etape in ("apres_facture", "apres_lignes", "apres_couverture", "refus_trigger"):
            with self.subTest(etape=etape):
                bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
                autre_bc = self.monde_devis([("700.00", "aucun", None)]) if etape == "refus_trigger" else None
                numero_perdu = self.numero("situation", "2026-10-05")                                  # attribué (et validé) AVANT la transaction d'émission
                avant = self.photo()
                err = self.tentative_emission(etape, bc, numero_perdu, autre_bc)
                if etape == "refus_trigger":
                    self.assertIsInstance(err, sqlite3.IntegrityError)
                    self.assertRegex(str(err), "INV-204")
                else:
                    self.assertIsInstance(err, ErreurInjectee)
                self.assertFalse(self.db.in_transaction)
                self.assertEqual(self.photo(), avant)                                                   # ni situation, ni lignes, ni couverture, rien d'autre
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=? AND type='situation'", bc.b)[0], 0)
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE numero=?", numero_perdu)[0], 0)
                # nouvelle émission : elle réussit, porte l'ordinal 1 (rien n'a été consommé) et SA couverture est complète
                f = self.emission(bc, self.pct(bc, 4000))
                self.assertEqual(self.un("SELECT situation_numero FROM factures WHERE id=?", f)[0], 1)
                self.assertEqual(self.couverture(f), bc.d)
                nouveau = self.un("SELECT numero FROM factures WHERE id=?", f)[0]
                self.assertNotEqual(nouveau, numero_perdu)
                self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=? AND type='situation'", bc.b)[0], 1)
                # trou de numérotation toléré : le numéro perdu n'existe nulle part et la suite est acceptée
                self.assertEqual(int(nouveau.split("-")[1]), int(numero_perdu.split("-")[1]) + 1)

    # 10 --------------------------------------------------------------------------------------------------------------------
    def test_INV_052_057_058_10_plafonds_et_autres_controles_de_TR_22_sans_regression(self):
        # devis non couvert : plafond = acompte prévu (30 % × 1 000 = 300.00)
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        A = bc.d[0]
        self.assertIsNone(self.acompte_sur(bc, A, "300.00"))
        self.assertRegex(self.acompte_sur(bc, A, "300.01"), "INV-57")
        # un seul acompte actif par devis (INV-52) ; un avoir total le libère
        a1 = self.acompte(bc, A, "100.00")
        self.assertRegex(self.acompte_sur(bc, A, "100.00"), "INV-52")
        self.avoir(a1)
        self.assertIsNone(self.acompte_sur(bc, A, "100.00"))
        # devis rattaché au BC de la facture (INV-189)
        autre = self.monde_devis([("500.00", "pourcentage", "30.00")])
        self.assertRegex(self.acompte_sur(bc, autre.d[0], "10.00"), "INV-189")
        # une situation reste plafonnée à moins de 100 % du contractuel (INV-57)
        self.assertRegex(self.tente_f(bc, "situation", "1000.00", situation_numero=1, montant_deja_facture_ht="0.00"), "INV-57")
        self.assertIsNone(self.tente_f(bc, "situation", "999.99", situation_numero=1, montant_deja_facture_ht="0.00"))
        # une situation de montant nul est toujours refusée par la contrainte livrée en 006 (sans préfixe INV-) ; 009b n'ajoute aucune règle
        m = self.tente_f(bc, "situation", "0.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertIsNotNone(m)
        self.assertRegex(m, "CHECK")
        self.assertNotIn("INV-", m)
        # solde jamais à 0.00 (INV-55) ; aucun acompte après un solde (INV-58)
        bc2 = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        self.assertRegex(self.tente_f(bc2, "solde", "0.00"), "INV-55")
        self.solde_final(bc2)
        self.assertRegex(self.acompte_sur(bc2, bc2.d[0], "100.00"), "INV-58")
        # sur un devis couvert ET hors plafond, l'acompte reste refusé (jamais accepté)
        bc3 = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        self.emission(bc3, self.pct(bc3, 4000))
        m = self.acompte_sur(bc3, bc3.d[0], "300.01")
        self.assertIsNotNone(m)
        self.assertRegex(m, "INV-205")

    # 11 --------------------------------------------------------------------------------------------------------------------
    def test_D62_11_garde_de_migration_refus_si_une_situation_existe_base_et_user_version_inchanges_acceptation_sinon(self):
        # --- refus : une situation existe (quelle que soit son histoire, y compris totalement créditée, y compris sur un autre BC)
        for variante in ("situation", "situation_creditee", "situation_d_un_autre_bc"):
            with self.subTest(variante=variante):
                t = Base53._sur(B.migrer13())
                bc = t.monde_devis([("1000.00", "pourcentage", "30.00")])
                t.acompte(bc, bc.d[0], "100.00")
                bc_s = t.monde_devis([("800.00", "aucun", None)]) if variante == "situation_d_un_autre_bc" else bc
                s = t.emettre_situation(bc_s, {bl: 4000 for bl, _, _ in t.lignes_de_bc(bc_s)})
                if variante == "situation_creditee":
                    t.avoir(s)
                db = t.db
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 13)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM factures WHERE type='situation'").fetchone()[0], 1)
                schema = db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY name").fetchall()
                donnees = t.photo()
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    T.runner(db, B.RANG, B.SQL_009B)
                self.assertRegex(str(cm.exception), "009b refuse de s'appliquer")
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 13)                  # rang inchangé
                self.assertEqual(db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY name").fetchall(), schema)   # schéma inchangé
                self.assertEqual(t.photo(), donnees)                                                    # aucune donnée modifiée, aucun lien fabriqué
                self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name = 'situation_devis'").fetchone()[0], 0)
                self.assertEqual(db.execute("SELECT name FROM sqlite_temp_master").fetchall(), [])      # la table de garde TEMP n'a pas survécu
                self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)                    # réglage rétabli par le lanceur
                self.assertFalse(db.in_transaction)

        # --- acceptation : aucune situation (acompte, avoir, solde autorisés) ; données préservées, couverture vide
        t = Base53._sur(B.migrer13())
        bc = t.monde_devis([("1000.00", "pourcentage", "30.00")])
        a = t.acompte(bc, bc.d[0], "100.00")
        t.avoir(a, "40.00")
        t.solde_final(bc)
        db = t.db
        self.assertEqual(db.execute("SELECT COUNT(*) FROM factures WHERE type='situation'").fetchone()[0], 0)
        avant = t.photo()
        T.runner(db, B.RANG, B.SQL_009B)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 14)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name = 'situation_devis'").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM situation_devis").fetchone()[0], 0)
        apres = t.photo()
        for nom, lignes in avant.items():
            self.assertEqual(apres[nom], lignes, f"table {nom} modifiée par la migration")
        self.assertEqual(set(apres) - set(avant), {"situation_devis", "bc_ligne_retraits_garantie"})
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
        self.assertEqual(db.execute("SELECT name FROM sqlite_temp_master").fetchall(), [])

    # 12 --------------------------------------------------------------------------------------------------------------------
    def test_INV_204_12_CK_21_et_CK_22_detectent_chacun_leur_anomalie_et_ne_bloquent_rien(self):
        # texte identique à celui du modèle V3.14 (§14)
        modele = MODELE.read_text(encoding="utf-8")
        bloc = re.search(r"-- CK-21 :.*?```", modele, re.S).group(0)
        normaliser = lambda s: re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", s)).replace("```", "").strip().rstrip(";").strip()   # noqa: E731
        self.assertIn(normaliser(CK_21), normaliser(bloc))
        self.assertIn(normaliser(CK_22), normaliser(bloc))
        for sql in (CK_21, CK_22):
            self.assertTrue(sql.lstrip().upper().startswith("SELECT"))
            self.assertNotIn("created_at", sql)                                                         # aucun horodatage
        # base saine (C-43) : aucune ligne
        self.c43()
        self.assertEqual(self.tous(CK_21), [])
        self.assertEqual(self.tous(CK_22), [])
        # CK-21 : une situation sans aucune couverture (SQL ne l'interdit pas : l'exhaustivité est une règle de service)
        bc = self.monde_devis([("1000.00", "pourcentage", "30.00")])
        s_nue = self.emettre_situation(bc, self.pct(bc, 1000))
        self.assertEqual(self.tous(CK_21), [(s_nue,)])
        self.assertEqual(self.tous(CK_22), [])
        # CK-22 : S1 couvre {A, B}, S2 (plus récente, même BC) ne couvre que {A} → B disparaît
        bc2 = self.monde_devis([("1000.00", "pourcentage", "30.00"), ("500.00", "pourcentage", "30.00")])
        A, Bd = bc2.d
        s1 = self.emission(bc2, self.pct(bc2, 1000))
        s2 = self.emettre_situation(bc2, self.pct(bc2, 2000))
        self.db.execute("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", (s2, A))   # couverture partielle posée à la main
        self.assertEqual(self.tous(CK_22), [(s1, s2, Bd)])
        self.assertEqual(self.tous(CK_21), [(s_nue,)])                                                  # CK-21 n'a pas bougé : S2 a une couverture (partielle)
        # limite assumée : l'omission partielle sur la DERNIÈRE situation n'est visible d'aucun des deux diagnostics
        bc3 = self.monde_devis([("1000.00", "pourcentage", "30.00"), ("500.00", "pourcentage", "30.00")])
        s3 = self.emettre_situation(bc3, self.pct(bc3, 1000))
        self.db.execute("INSERT INTO situation_devis (facture_id, devis_id) VALUES (?, ?)", (s3, bc3.d[0]))
        self.assertEqual([x for x in self.tous(CK_21) if x[0] == s3], [])
        self.assertEqual([x for x in self.tous(CK_22) if s3 in x[:2]], [])
        # les diagnostics sont de pures lectures : rien n'est écrit, rien n'est bloqué
        avant = self.photo()
        for sql in (CK_21, CK_22):
            self.tous(sql)
        self.assertEqual(self.photo(), avant)
        self.assertFalse(self.db.in_transaction)

    # 13 --------------------------------------------------------------------------------------------------------------------
    def test_T53_13_rejeu_001_009a_009b_depuis_une_base_vide_et_depuis_le_rang_12_001_a_009_identiques_a_GitHub(self):
        # 001 à 009 : octet pour octet ceux de GitHub (main da2969a)
        for nom, empreinte in EMPREINTES_001_A_009.items():
            with self.subTest(fichier=nom):
                self.assertEqual(hashlib.sha256((MIGRATIONS / nom).read_bytes()).hexdigest(), empreinte)
        noms = [p.name for p in sorted(MIGRATIONS.glob("*.sql"))]
        self.assertEqual(noms[:12], list(EMPREINTES_001_A_009))
        self.assertEqual(noms[12:], [B.NOM_009A, B.NOM_009B])
        # depuis une base vide : 001 → 009 → 009a → 009b
        db = B.migrer14()
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 14)
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
        self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE name LIKE '%situation_devis%' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall(),
                         [("idx_situation_devis_devis_id",), ("situation_devis",), ("tr_104_situation_devis_insert",),
                          ("tr_105_situation_devis_delete",), ("tr_105_situation_devis_update",)])
        # depuis le rang 12 portant des données : 009a puis 009b, données préservées, couverture vide
        t = Base53._sur(P.migrer12())
        bc = t.monde_devis([("1000.00", "pourcentage", "30.00")])
        a = t.acompte(bc, bc.d[0], "100.00")
        t.avoir(a, "40.00")
        t.solde_final(bc)
        avant = t.photo()
        self.assertEqual(t.db.execute("PRAGMA user_version").fetchone()[0], 12)
        T.appliquer(t.db, B.RANG_009A, B.SQL_009A)
        self.assertEqual(t.db.execute("PRAGMA user_version").fetchone()[0], 13)
        T.runner(t.db, B.RANG, B.SQL_009B)
        self.assertEqual(t.db.execute("PRAGMA user_version").fetchone()[0], 14)
        apres = t.photo()
        for nom, lignes in avant.items():
            self.assertEqual(apres[nom], lignes, f"table {nom} modifiée par le rejeu")
        self.assertEqual(apres["situation_devis"], [])
        self.assertEqual(t.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(t.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
        # 009b ne se rejoue pas (rang 14 ≠ 13) : refus, rang inchangé
        with self.assertRaises((sqlite3.IntegrityError, T.ErreurRunner)):
            T.runner(t.db, B.RANG, B.SQL_009B)
        self.assertEqual(t.db.execute("PRAGMA user_version").fetchone()[0], 14)
        # schéma identique à celui de la base construite depuis le vide
        schema = lambda d: d.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name").fetchall()   # noqa: E731
        self.assertEqual(schema(t.db), schema(db))


if __name__ == "__main__":
    unittest.main()
