"""T-47 — Migration corrective 005c_bc_annule_caches_financiers (rang 8, D-56) ; modèle V3.13 §4.19 (ligne 12), §7.2 (BC annulé),
§8 (TR-12), §17.1 ; conventions techniques §5 (chaîne ordonnée, transaction et user_version) ; invariants INV-46, INV-164, INV-173, INV-188 ;
cadrage 006 §M.4 et §M.8 (VR-04 à VR-06).
005c remplace UN SEUL objet : le trigger tr_12_bons_commande_annule. Sur un BC annulé, trois caches financiers dérivés
(montant_deja_facture_ht, avancement, date_100_facture) cessent d'être gardés ; les 22 autres colonnes gardées par 005b le restent. Aucune
table, aucun index, aucun CHECK, aucun autre trigger, aucun CK, aucune donnée : le fichier contient exactement deux instructions
(DROP TRIGGER, CREATE TRIGGER). Le message du trigger ne dit plus que updated_at est le seul champ modifiable (préfixe INV-173 conservé).
La légitimité d'un recalcul (sens, montant, lien avec un avoir) n'est PAS portée par le schéma : service financier (INV-46) et CK-06,
tranche 006. Aucun test ne suppose de table de facturation : aucune table `factures` n'existe au rang 8.

Réutilisation : ces tests n'ont pas leur propre fabrique de données ; ils importent le module voisin test_005b_bc_multi_devis (fabrication des
devis, BC, lignes, garanties ; émulation du runner) sans le modifier. Le rang 8 est obtenu en appliquant 005c sur la chaîne du rang 7 ;
005c ne reconstruit aucune table : elle s'applique comme une migration ordinaire (BEGIN IMMEDIATE, fichier, PRAGMA user_version = 8, COMMIT,
foreign_keys=ON conservé) ; le protocole de reconstruction du runner (foreign_keys=OFF, vérifications) est aussi accepté et testé.

Exécution : python3 src-tauri/tests/metier/test_005c_bc_annule_caches_financiers.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T47_ suivi du groupe de la consigne
(A chaîne, B scénario, C caches autorisés, D champs protégés, E frozen_at, F statut, G sans facturation 006, H CHECK, I BC non annulés,
J atomicité, K régressions 005b, L anti-contournement). Les décisions d'interprétation portent « INTERPRETATION ».
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39). Un refus levé par le trigger se reconnaît à son préfixe
« INV-173 » ; un refus levé par une contrainte CHECK ne porte aucun « INV- » (BEFORE UPDATE s'exécute avant les CHECK).
Ordre des triggers : SQLite exécute les triggers d'un même événement dans l'ordre inverse de leur création ; tr_12_bons_commande_annule
est recréé après tr_14_bons_commande_frozen_at, donc pour une modification de frozen_at sur un BC annulé et gelé le message qui sort peut
être INV-173 ou INV-34. Cet ordre n'est pas un contrat : les tests de frozen_at n'exigent que le refus (et l'un des deux préfixes) ;
le préfixe exact n'est asserté qu'avec le trigger isolé.
"""
import pathlib
import re
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_005b_bc_multi_devis as T  # noqa: E402  (module voisin : fabrication de données et émulation du runner)

MIGRATIONS = T.MIGRATIONS
NOM_005C = "005c_bc_annule_caches_financiers.sql"
NOMS = T.NOMS + (NOM_005C,)
SQL_005C = (MIGRATIONS / NOM_005C).read_text(encoding="utf-8")
RANG = 8
TRIGGER = "tr_12_bons_commande_annule"
MESSAGE = "INV-173: bon de commande annule terminal, seules les evolutions autorisees sont modifiables"
ANCIEN_MESSAGE = "INV-173: bon de commande annule terminal, seul updated_at est modifiable"

CACHES = ("montant_deja_facture_ht", "avancement", "date_100_facture")                    # désormais modifiables sur un BC annulé
PROTEGEES = ("id", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot", "entreprise_snapshot_version",
             "chantier_snapshot", "chantier_snapshot_version", "date_acceptation", "date_debut", "date_fin",
             "montant_contractuel_ht", "statut", "completed_at", "cancelled_at", "motif_annulation", "frozen_at", "created_at",
             "origine", "legacy_id", "legacy_data", "legacy_numero")                         # 22 colonnes qui restent gardées par tr_12
GARDEES_PAR_TR01 = ("numero", "date_creation")                                              # INV-23, hors tr_12
LIBRES = ("updated_at",)
ETATS_ANNULES = T.ETATS_BC_ANNULES                                                          # ("annule", "annule_gele")
ETATS_NON_ANNULES = T.ETATS_BC_NON_ANNULES                                                  # ("en_cours", "gele", "termine")
TS = T.TS
TS2 = T.TS2
RE_ANNULE = r"INV-173"
RE_FROZEN = r"INV-(173|34)"                                                                 # ordre des triggers non contractuel (docstring)


# --------------------------------------------------------------------------------------------------------------------
# Chaîne et fabrique
# --------------------------------------------------------------------------------------------------------------------
def migrer8(recursive=True):
    """Chaîne 001 à 005b (rang 7) puis 005c comme une migration ordinaire : BEGIN IMMEDIATE, fichier, user_version = 8, COMMIT."""
    db = T.migrer(7, recursive=recursive)
    T.appliquer(db, RANG, SQL_005C)
    return db


def colonnes_gardees(sql_trigger):
    """Colonnes citées dans le WHEN du trigger sous la forme `NEW.x IS NOT OLD.x`."""
    return re.findall(r"NEW\.(\w+) IS NOT OLD\.\1\b", sql_trigger)


class Base8(T.Base):
    """Base au rang 8 ; les fabriques (client, devis, BC, lignes, garanties) viennent de test_005b."""

    def setUp(self):
        self.db = migrer8()
        self._n = 0

    def tente(self, sql, *args):
        """Exécute l'instruction puis l'annule (SAVEPOINT) : None si elle réussit, sinon le message de l'erreur d'intégrité."""
        self.db.execute("SAVEPOINT tente")
        try:
            self.db.execute(sql, self._a(args))
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tente")
            self.db.execute("RELEASE tente")

    def isole(self, gardes):
        """Base du rang 8 dont tous les triggers sont supprimés sauf `gardes`."""
        t = Base8()
        t.db = migrer8()
        t._n = 0
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def bc_annule_apres_facturation(self):
        """BC gelé, terminé (caches à 100 %), puis annulé : statut annule, completed_at et date_100_facture à NULL, avancement 100.00."""
        bc = self.bc_en_etat("termine")
        self.annuler_bc(bc.b)
        return bc

    def bc(self, b):
        """Ligne complète du BC sous forme de dictionnaire."""
        cur = self.db.execute("SELECT * FROM bons_commande WHERE id=?", (b,))
        return dict(zip([c[0] for c in cur.description], cur.fetchone()))

    def valeur(self, b, col):
        return self.un(f"SELECT {col} FROM bons_commande WHERE id=?", b)[0]


# --------------------------------------------------------------------------------------------------------------------
# A — chaîne de migration
# --------------------------------------------------------------------------------------------------------------------
class Chaine(Base8):
    """Groupe A : 001 → 002 → 003 → 004 → 005 → 005a → 005b → 005c, rang 8, aucune régression de la chaîne."""

    def test_T47_A_fichiers_de_la_chaine_dans_l_ordre(self):
        self.assertEqual([p.name for p in sorted(MIGRATIONS.glob("*.sql"))[:8]], list(NOMS))
        self.assertEqual(NOMS[-1], "005c_bc_annule_caches_financiers.sql")
        self.assertEqual(len(NOMS), RANG)

    def test_T47_A_rang_et_user_version(self):
        db = T.migrer(7)
        self.assertEqual(T.db_user_version(db), 7)
        T.appliquer(db, RANG, SQL_005C)
        self.assertEqual(T.db_user_version(db), 8)
        self.assertEqual(T.db_user_version(self.db), 8)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)                              # pas de protocole foreign_keys=OFF
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_T47_A_le_protocole_de_reconstruction_du_runner_est_accepte(self):
        db = T.migrer(7)
        T.runner(db, RANG, SQL_005C)                                                        # foreign_keys=OFF, vérifications, user_version, ON
        self.assertEqual(T.db_user_version(db), 8)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(T.sql_de(db, TRIGGER), T.sql_de(self.db, TRIGGER))

    def test_T47_A_le_fichier_ne_contient_que_deux_instructions(self):
        sts = [s.strip() for s in T.instructions(T.sans_commentaires(SQL_005C)) if s.strip()]
        self.assertEqual(len(sts), 2)
        self.assertEqual(sts[0], f"DROP TRIGGER {TRIGGER};")
        self.assertTrue(sts[1].startswith(f"CREATE TRIGGER {TRIGGER}\nBEFORE UPDATE ON bons_commande\nWHEN OLD.statut = 'annule'\n AND ("), sts[1][:120])
        code = T.sans_commentaires(SQL_005C)
        for interdit in (r"\bPRAGMA\b", r"\bCOMMIT\b", r"\bROLLBACK\b", r"\bSAVEPOINT\b", r"BEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)",
                         r"\bCREATE\s+(TABLE|INDEX|UNIQUE|VIEW|TEMP)", r"\bALTER\b", r"\bINSERT\b", r"\bDELETE\b", r"\bCHECK\b", r"\bCK-\d+"):
            self.assertIsNone(re.search(interdit, code), interdit)
        for hors_perimetre in ("factures", "facture_lignes", "avoir", "reglements", "garanties", "depenses", "bc_devis", "devis"):
            self.assertNotIn(hors_perimetre, code, hors_perimetre)                          # 005c n'anticipe pas 006 et ne touche à rien d'autre

    def test_T47_A_aucun_objet_cree_ou_supprime_seul_tr_12_annule_change(self):
        db7 = T.migrer(7)
        o7 = {(t, n, tb): s for t, n, tb, s in T.objets(db7)}
        o8 = {(t, n, tb): s for t, n, tb, s in T.objets(self.db)}
        self.assertEqual(set(o7), set(o8))                                                  # mêmes tables, index, triggers, vues
        diff = {cle for cle in o7 if o7[cle] != o8[cle]}
        self.assertEqual(diff, {("trigger", TRIGGER, "bons_commande")})
        self.assertEqual(T.noms(self.db, "table"), T.TABLES_RANG7)
        self.assertEqual(T.noms(self.db, "view"), set())
        self.assertEqual(T.noms(self.db, "index") - {n for n in T.noms(self.db, "index") if n.startswith("sqlite_")}, T.INDEXES_RANG7 | (
            T.noms(self.db, "index") - T.INDEXES_RANG7 - {n for n in T.noms(self.db, "index") if not n.startswith("sqlite_")}))
        self.assertEqual({n for n in T.noms(self.db, "index") if not n.startswith("sqlite_")}, T.INDEXES_RANG7)
        self.assertEqual(len(T.noms(self.db, "trigger")), len(T.noms(db7, "trigger")))

    def test_T47_A_aucune_donnee_n_est_modifiee_par_la_migration(self):
        t7 = T.Base()
        t7.setUp()                                                                          # rang 7
        for etat in T.ETATS_BC:
            t7.bc_en_etat(etat)
        avant = T.tout(t7.db)
        self.assertTrue(avant["bons_commande"])
        T.appliquer(t7.db, RANG, SQL_005C)
        self.assertEqual(T.tout(t7.db), avant)                                              # lignes et sqlite_sequence inchangées
        self.assertEqual(T.db_user_version(t7.db), 8)

    def test_T47_A_difference_exacte_avec_le_trigger_de_005b(self):
        """Le trigger du rang 8 = celui du rang 7 moins les trois lignes de caches, avec le message générique, et rien d'autre."""
        sql7 = T.sql_de(T.migrer(7), TRIGGER)
        attendu = sql7
        for col in CACHES:
            ligne = f"        OR NEW.{col} IS NOT OLD.{col}\n"
            self.assertEqual(attendu.count(ligne), 1, col)
            attendu = attendu.replace(ligne, "")
        self.assertEqual(attendu.count(ANCIEN_MESSAGE), 1)
        attendu = attendu.replace(ANCIEN_MESSAGE, MESSAGE)
        norm = lambda s: re.sub(r"\s+", " ", s).strip()
        self.assertEqual(norm(T.sql_de(self.db, TRIGGER)), norm(attendu))

    def test_T47_A_liste_des_colonnes_gardees_reconstruite_depuis_005b(self):
        sql7, sql8 = T.sql_de(T.migrer(7), TRIGGER), T.sql_de(self.db, TRIGGER)
        c7, c8 = colonnes_gardees(sql7), colonnes_gardees(sql8)
        self.assertEqual((len(c7), len(c7) == len(set(c7))), (25, True))
        self.assertEqual((len(c8), len(c8) == len(set(c8))), (22, True))
        self.assertEqual(set(c7) - set(c8), set(CACHES))                                    # seules les trois colonnes de caches sont retirées
        self.assertEqual(set(c8) - set(c7), set())                                          # aucune garde ajoutée
        self.assertEqual(set(c8), set(PROTEGEES))                                           # la liste du test = la liste du SQL
        self.assertEqual(len(PROTEGEES), 22)
        toutes = set(T.colonnes(self.db, "bons_commande"))
        self.assertEqual(set(PROTEGEES) | set(CACHES) | set(GARDEES_PAR_TR01) | set(LIBRES), toutes)        # 28 colonnes, partition exacte
        self.assertEqual(len(toutes), 28)
        self.assertEqual(len(set(PROTEGEES) & set(CACHES)), 0)

    def test_T47_A_message_generique_et_prefixe_inv_173(self):
        sql8 = T.sql_de(self.db, TRIGGER)
        self.assertEqual(re.findall(r"RAISE\(ABORT, '([^']*)'\)", sql8), [MESSAGE])
        self.assertTrue(MESSAGE.startswith("INV-173:"))
        self.assertNotIn("updated_at", MESSAGE)
        self.assertNotRegex(MESSAGE, r"\bseul\b")
        for cache in CACHES:
            self.assertNotIn(cache, MESSAGE)                                                # générique : n'énumère pas les caches
        bc = self.bc_en_etat("annule")
        self.assertEqual(self.tente("UPDATE bons_commande SET statut='en_cours' WHERE id=?", bc.b), MESSAGE)

    def test_T47_A_atomicite_de_la_migration(self):
        """Une erreur n'importe où dans le fichier annule tout : le trigger de 005b reste en place, user_version reste 7."""
        db0 = T.migrer(7)
        sql7 = T.sql_de(db0, TRIGGER)
        drop = f"DROP TRIGGER {TRIGGER};\n"
        for nom, sql in (("apres le DROP", drop + "SELECT * FROM table_qui_n_existe_pas;\n"),
                         ("apres le CREATE", SQL_005C + "SELECT * FROM table_qui_n_existe_pas;\n")):
            with self.subTest(erreur=nom):
                db = T.migrer(7)
                with self.assertRaises(sqlite3.Error):
                    T.runner(db, RANG, sql)
                self.assertFalse(db.in_transaction)
                self.assertEqual(T.db_user_version(db), 7)
                self.assertEqual(T.sql_de(db, TRIGGER), sql7)
                self.assertEqual(self.tous.__func__(types_ns(db), "SELECT count(*) FROM sqlite_master WHERE name=?", TRIGGER), [(1,)])


def types_ns(db):
    """Petit objet portant `.db` pour réutiliser les utilitaires de Base sur une connexion quelconque."""
    class _N:
        pass
    n = _N()
    n.db = db
    n._a = staticmethod(Base8._a)
    return n


# --------------------------------------------------------------------------------------------------------------------
# B — scénario de base ; C — caches autorisés ; G — aucune table de facturation
# --------------------------------------------------------------------------------------------------------------------
class ScenarioDeBase(Base8):
    """Groupe B : créer un BC valide puis l'annuler ; vérifier l'état attendu avant les autres tests."""

    def test_T47_B_bc_valide_puis_annule(self):
        for etat in ETATS_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                r = self.bc(bc.b)
                self.assertEqual((r["statut"], r["cancelled_at"], r["motif_annulation"], r["completed_at"]),
                                 ("annule", T.TS_ANNUL, "Client renonce", None))
                self.assertEqual((r["montant_deja_facture_ht"], r["avancement"], r["date_100_facture"]), ("0.00", "0.00", None))
                self.assertEqual(r["frozen_at"], TS if etat == "annule_gele" else None)
                self.assertEqual(r["montant_contractuel_ht"], "31.50")
                self.assertEqual(self.tous("SELECT count(*) FROM bc_lignes WHERE bc_id=?", bc.b), [(2,)])

    def test_T47_B_l_annulation_est_un_acte_possible_depuis_chaque_etat_non_annule(self):
        """L'UPDATE qui annule part d'un BC non annulé (OLD.statut <> 'annule') : tr_12_annule ne s'applique pas."""
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.annuler_bc(bc.b)
                r = self.bc(bc.b)
                self.assertEqual((r["statut"], r["completed_at"], r["date_100_facture"]), ("annule", None, None))

    def test_T47_B_bc_termine_puis_annule_conserve_ses_caches(self):
        bc = self.bc_annule_apres_facturation()
        r = self.bc(bc.b)
        self.assertEqual((r["statut"], r["montant_deja_facture_ht"], r["avancement"], r["date_100_facture"], r["completed_at"]),
                         ("annule", "31.50", "100.00", None, None))
        self.assertEqual(r["frozen_at"], TS)                                                # posé pour terminer le BC, conservé (irréversible)


class CachesAutorises(Base8):
    """Groupes C et G : les trois caches financiers d'un BC annulé évoluent, sans facture 006 ni autre table."""

    MAJ = "UPDATE bons_commande SET {} WHERE id=?"

    def appliquer_maj(self, b, sets, *valeurs):
        self.db.execute(self.MAJ.format(sets), (*valeurs, b))

    def test_T47_C_montant_deja_facture_seul(self):
        for etat in ETATS_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                avant = self.bc(bc.b)
                self.appliquer_maj(bc.b, "montant_deja_facture_ht=?", "12.50")
                apres = self.bc(bc.b)
                self.assertEqual(apres["montant_deja_facture_ht"], "12.50")
                self.assertEqual({k: v for k, v in apres.items() if k != "montant_deja_facture_ht"},
                                 {k: v for k, v in avant.items() if k != "montant_deja_facture_ht"})

    def test_T47_C_avancement_seul(self):
        for etat in ETATS_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                avant = self.bc(bc.b)
                self.appliquer_maj(bc.b, "avancement=?", "50.00")
                apres = self.bc(bc.b)
                self.assertEqual(apres["avancement"], "50.00")
                self.assertEqual({k: v for k, v in apres.items() if k != "avancement"}, {k: v for k, v in avant.items() if k != "avancement"})

    def test_T47_C_date_100_facture_seule_pose_puis_retiree(self):
        """BC annulé gelé dont l'avancement est déjà 100.00 (annulé après facturation complète) : date_100_facture seule (CHECK satisfaits)."""
        bc = self.bc_annule_apres_facturation()
        avant = self.bc(bc.b)
        self.appliquer_maj(bc.b, "date_100_facture=?", "2026-10-02")
        poses = self.bc(bc.b)
        self.assertEqual(poses["date_100_facture"], "2026-10-02")
        self.assertEqual({k: v for k, v in poses.items() if k != "date_100_facture"}, {k: v for k, v in avant.items() if k != "date_100_facture"})
        self.appliquer_maj(bc.b, "date_100_facture=NULL")                                   # le sens du recalcul (avoir total) est celui du service
        self.assertEqual(self.bc(bc.b), avant)

    def test_T47_C_les_trois_caches_et_updated_at_dans_un_seul_update(self):
        """Avoir total puis nouvelle facturation complète, comme le fera le service : un seul UPDATE, statut inchangé."""
        bc = self.bc_annule_apres_facturation()
        avant = self.bc(bc.b)
        self.appliquer_maj(bc.b, "montant_deja_facture_ht=?, avancement=?, date_100_facture=?, updated_at=?", "31.50", "100.00", "2026-10-05", TS2)
        apres = self.bc(bc.b)
        self.assertEqual((apres["montant_deja_facture_ht"], apres["avancement"], apres["date_100_facture"], apres["updated_at"]),
                         ("31.50", "100.00", "2026-10-05", TS2))
        for col in PROTEGEES + GARDEES_PAR_TR01:
            self.assertEqual(apres[col], avant[col], col)                                   # aucune autre colonne n'a bougé
        self.assertEqual(apres["statut"], "annule")                                         # un avoir ne rend pas le BC actif
        self.appliquer_maj(bc.b, "montant_deja_facture_ht=?, avancement=?, date_100_facture=NULL, updated_at=?", "0.00", "0.00", TS)
        apres = self.bc(bc.b)
        self.assertEqual((apres["montant_deja_facture_ht"], apres["avancement"], apres["date_100_facture"], apres["statut"]),
                         ("0.00", "0.00", None, "annule"))

    def test_T47_C_updated_at_seul_et_combine_avec_chaque_cache(self):
        for etat in ETATS_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.appliquer_maj(bc.b, "updated_at=?", TS2)
                self.assertEqual(self.valeur(bc.b, "updated_at"), TS2)
                self.appliquer_maj(bc.b, "montant_deja_facture_ht=?, updated_at=?", "5.00", T.TS)
                self.appliquer_maj(bc.b, "avancement=?, updated_at=?", "10.00", TS2)
                self.assertEqual(self.tous("SELECT montant_deja_facture_ht, avancement, updated_at FROM bons_commande WHERE id=?", bc.b),
                                 [("5.00", "10.00", TS2)])

    def test_T47_C_dans_une_transaction_explicite(self):
        bc = self.bc_annule_apres_facturation()
        self.db.execute("BEGIN IMMEDIATE")
        self.appliquer_maj(bc.b, "montant_deja_facture_ht=?, avancement=?, date_100_facture=NULL, updated_at=?", "10.00", "30.00", TS2)
        self.db.execute("COMMIT")
        self.assertEqual(self.tous("SELECT montant_deja_facture_ht, avancement, date_100_facture, statut FROM bons_commande WHERE id=?", bc.b),
                         [("10.00", "30.00", None, "annule")])

    def test_T47_C_le_trigger_tr_12_annule_seul_ne_garde_plus_les_caches(self):
        """Avec tr_12_annule pour seul trigger, les trois caches passent : ce trigger n'en est plus le garde."""
        for etat in ETATS_ANNULES:
            for nom, sets, vals in (("montant", "montant_deja_facture_ht=?", ("9.00",)), ("avancement", "avancement=?", ("9.00",)),
                                    ("tous", "montant_deja_facture_ht=?, avancement=?, updated_at=?", ("9.00", "9.00", TS2))):
                with self.subTest(etat=etat, maj=nom):
                    t = self.isole({TRIGGER})
                    bc = t.bc_en_etat(etat)
                    self.assertIsNone(t.tente(self.MAJ.format(sets), (*vals, bc.b)))
        t = self.isole({TRIGGER})
        bc = t.bc_annule_apres_facturation()
        self.assertIsNone(t.tente(self.MAJ.format("date_100_facture=?"), ("2026-10-02", bc.b)))

    def test_T47_G_aucune_table_de_facturation_n_est_necessaire(self):
        """Pas de fausse table 006 : le schéma du rang 8 n'a ni factures ni lignes de factures, et les caches évoluent quand même."""
        tables = T.noms(self.db, "table")
        self.assertTrue({"factures", "facture_lignes", "reglements", "garanties", "avoirs"}.isdisjoint(tables))
        self.assertEqual(tables, T.TABLES_RANG7)
        bc = self.bc_annule_apres_facturation()
        self.appliquer_maj(bc.b, "montant_deja_facture_ht=?, avancement=?, date_100_facture=NULL", "0.00", "0.00")
        self.assertEqual(self.tous("SELECT montant_deja_facture_ht, avancement FROM bons_commande WHERE id=?", bc.b), [("0.00", "0.00")])
        self.assertEqual(T.noms(self.db, "table"), tables)


# --------------------------------------------------------------------------------------------------------------------
# D — champs protégés ; E — frozen_at ; F — statut et terminalité
# --------------------------------------------------------------------------------------------------------------------
class ChampsProteges(Base8):
    """Groupes D, E et F : les 22 colonnes encore gardées le sont une par une, y compris frozen_at et statut."""

    def test_INV_173_chaque_champ_protege_est_refuse_par_tr_12_seul(self):
        """Colonne par colonne, avec tr_12_annule pour unique trigger : une ligne supprimée du WHEN ne serait masquée par aucune autre garde
        (le BEFORE UPDATE s'exécute avant les CHECK : une colonne couplée à un CHECK est quand même refusée par le message INV-173)."""
        autre = self.client()
        for etat in ETATS_ANNULES:
            t = self.isole({TRIGGER})
            bc = t.bc_en_etat(etat)
            for col in PROTEGEES:
                with self.subTest(etat=etat, colonne=col):
                    ancienne = t.valeur(bc.b, col)
                    nouvelle = T.autre_valeur_bc(col, ancienne, autre)
                    self.assertNotEqual(nouvelle, ancienne)
                    msg = t.tente(f"UPDATE bons_commande SET {col}=? WHERE id=?", nouvelle, bc.b)
                    self.assertIsNotNone(msg)
                    self.assertEqual(msg, MESSAGE)
                    self.assertEqual(t.valeur(bc.b, col), ancienne)

    def test_INV_173_chaque_champ_protege_est_refuse_avec_tous_les_triggers(self):
        autre = self.client()
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            for col in PROTEGEES:
                with self.subTest(etat=etat, colonne=col):
                    ancienne = self.valeur(bc.b, col)
                    msg = self.tente(f"UPDATE bons_commande SET {col}=? WHERE id=?", T.autre_valeur_bc(col, ancienne, autre), bc.b)
                    self.assertIsNotNone(msg)
                    self.assertRegex(msg, RE_FROZEN if col == "frozen_at" else RE_ANNULE)
                    self.assertEqual(self.valeur(bc.b, col), ancienne)

    def test_INV_173_champ_protege_et_cache_dans_le_meme_update_refus_en_bloc(self):
        """Un cache autorisé ne fait pas passer un champ protégé dans la même instruction ; l'instruction échoue sans rien écrire."""
        autre = self.client()
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            for col in PROTEGEES:
                with self.subTest(etat=etat, colonne=col):
                    avant = self.bc(bc.b)
                    with self.assertRaisesRegex(sqlite3.IntegrityError, RE_FROZEN if col == "frozen_at" else RE_ANNULE):
                        self.db.execute(f"UPDATE bons_commande SET montant_deja_facture_ht='9.00', avancement='9.00', {col}=?, updated_at=? WHERE id=?",
                                        (T.autre_valeur_bc(col, avant[col], autre), TS2, bc.b))
                    self.assertEqual(self.bc(bc.b), avant)

    def test_INV_173_numero_et_date_creation_restent_gardes_par_tr_01_et_updated_at_est_libre(self):
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            with self.subTest(etat=etat):
                self.assertRegex(self.tente("UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", bc.b), "INV-23")
                self.assertRegex(self.tente("UPDATE bons_commande SET date_creation='2026-10-03' WHERE id=?", bc.b), "INV-23")
                self.assertIsNone(self.tente("UPDATE bons_commande SET updated_at=? WHERE id=?", TS2, bc.b))

    def test_T47_E_frozen_at_reste_non_modifiable_sur_un_bc_annule(self):
        for etat, valeurs in (("annule", (TS2,)), ("annule_gele", (TS2, None, TS))):
            bc = self.bc_en_etat(etat)
            for v in valeurs:
                with self.subTest(etat=etat, nouvelle=v):
                    ancienne = self.valeur(bc.b, "frozen_at")
                    msg = self.tente("UPDATE bons_commande SET frozen_at=? WHERE id=?", v, bc.b) if v != ancienne else "identique"
                    if v == ancienne:                                                       # même valeur : pas une modification
                        self.assertIsNone(self.tente("UPDATE bons_commande SET frozen_at=? WHERE id=?", v, bc.b))
                        continue
                    self.assertIsNotNone(msg)                                               # le refus est le contrat ; pas l'ordre des messages
                    self.assertRegex(msg, RE_FROZEN)
                    self.assertEqual(self.valeur(bc.b, "frozen_at"), ancienne)

    def test_T47_E_tr_12_seul_garde_la_pose_initiale_de_frozen_at_sur_un_bc_annule(self):
        """tr_14 laisse passer NULL → valeur : sur un BC annulé non gelé, seul tr_12_annule refuse (INV-173) ; gelé, tr_14 refuse aussi (INV-34)."""
        t14 = self.isole({"tr_14_bons_commande_frozen_at"})
        bc = t14.bc_en_etat("annule")
        self.assertIsNone(t14.tente("UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc.b))              # tr_14 seul : NULL → valeur accepté
        bc = t14.bc_en_etat("annule_gele")
        self.assertRegex(t14.tente("UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc.b), "INV-34")
        self.assertRegex(t14.tente("UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc.b), "INV-34")
        t12 = self.isole({TRIGGER})
        for etat in ETATS_ANNULES:
            bc = t12.bc_en_etat(etat)
            self.assertEqual(t12.tente("UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc.b), MESSAGE)    # trigger isolé : préfixe exact

    def test_T47_F_un_bc_annule_ne_repasse_ni_en_cours_ni_gele_ni_termine(self):
        for fabrique in ("annule", "annule_gele", "apres_facturation"):
            bc = self.bc_annule_apres_facturation() if fabrique == "apres_facturation" else self.bc_en_etat(fabrique)
            for statut in ("en_cours", "gele", "termine"):
                with self.subTest(bc=fabrique, statut=statut):
                    avant = self.bc(bc.b)
                    msg = self.tente("UPDATE bons_commande SET statut=? WHERE id=?", statut, bc.b)
                    self.assertIsNotNone(msg)
                    self.assertEqual(msg, MESSAGE)                                          # le trigger passe avant les CHECK (BEFORE UPDATE)
                    self.assertEqual(self.bc(bc.b), avant)

    def test_T47_F_reouverture_qui_satisfait_tous_les_check_est_quand_meme_refusee(self):
        """Le refus vient du trigger, pas d'un CHECK : les deux réouvertures ci-dessous respectent toutes les contraintes de la table."""
        bc = self.bc_en_etat("annule_gele")
        reouvrir_en_cours = ("UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (bc.b,))
        reouvrir_termine = ("UPDATE bons_commande SET statut='termine', cancelled_at=NULL, motif_annulation=NULL, completed_at=?, "
                            "date_100_facture='2026-10-03', avancement='100.00' WHERE id=?", (TS2, bc.b))
        for nom, (sql, args) in (("en_cours", reouvrir_en_cours), ("termine", reouvrir_termine)):
            with self.subTest(vers=nom):
                self.assertEqual(self.tente(sql, *args), MESSAGE)
        # contrepartie : sans tr_12_annule, ces deux instructions passent (elles sont valides pour les CHECK) — le trigger est donc l'unique garde
        t = self.isole(set())
        bc2 = t.bc_en_etat("annule_gele")
        self.assertIsNone(t.tente(reouvrir_en_cours[0], bc2.b))
        self.assertIsNone(t.tente(reouvrir_termine[0], TS2, bc2.b))
        # et recréé à partir de son SQL, il refuse de nouveau
        t.db.execute(T.sql_de(self.db, TRIGGER))
        self.assertEqual(t.tente(reouvrir_en_cours[0], bc2.b), MESSAGE)

    def test_T47_F_annuler_ne_se_defait_pas_en_deux_temps(self):
        """cancelled_at, motif_annulation et completed_at ne peuvent pas être vidés ou posés un par un sur un BC annulé."""
        bc = self.bc_en_etat("annule_gele")
        for sets in ("cancelled_at=NULL", "motif_annulation=NULL", "completed_at=?", "cancelled_at=?", "motif_annulation=?"):
            with self.subTest(sets=sets):
                args = (TS2,) if "?" in sets else ()
                self.assertEqual(self.tente(f"UPDATE bons_commande SET {sets} WHERE id=?", *args, bc.b), MESSAGE)


# --------------------------------------------------------------------------------------------------------------------
# H — cohérence des CHECK
# --------------------------------------------------------------------------------------------------------------------
class CheckEtCoherence(Base8):
    """Groupe H : les CHECK de bons_commande restent actifs ; 005c ne contourne aucun couplage."""

    def refuse_par_check(self, sql, *args):
        """Refus de contrainte (CHECK) : l'instruction échoue et le message ne porte aucun « INV- » (ce n'est pas un trigger)."""
        msg = self.tente(sql, *args)
        self.assertIsNotNone(msg, sql)
        self.assertNotIn("INV-", msg)
        self.assertIn("CHECK constraint failed", msg)
        return msg

    def test_T47_H_005c_ne_modifie_pas_le_ddl_de_bons_commande(self):
        self.assertEqual(T.sql_de(self.db, "bons_commande"), T.sql_de(T.migrer(7), "bons_commande"))
        ddl = T.sql_de(self.db, "bons_commande")
        for check in ("CHECK ((statut = 'termine') = (completed_at IS NOT NULL))", "CHECK (statut <> 'termine' OR date_100_facture IS NOT NULL)",
                      "CHECK ((statut = 'annule') = (cancelled_at IS NOT NULL))", "CHECK (statut <> 'termine' OR frozen_at IS NOT NULL)",
                      "CHECK (date_100_facture IS NULL OR frozen_at IS NOT NULL)", "CHECK (date_100_facture IS NULL OR avancement = '100.00')"):
            self.assertIn(check, ddl)

    def test_T47_H_date_100_facture_implique_avancement_100(self):
        for etat in ("annule_gele", "gele"):                                                # frozen_at posé : seul le couplage avancement reste en jeu
            bc = self.bc_en_etat(etat)
            for avancement in ("0.00", "99.99", "50.00"):
                with self.subTest(etat=etat, avancement=avancement):
                    self.db.execute("UPDATE bons_commande SET avancement=? WHERE id=?", (avancement, bc.b))
                    self.refuse_par_check("UPDATE bons_commande SET date_100_facture='2026-10-02' WHERE id=?", bc.b)
            self.assertIsNone(self.tente("UPDATE bons_commande SET avancement='100.00', date_100_facture='2026-10-02' WHERE id=?", bc.b))

    def test_T47_H_date_100_facture_implique_frozen_at(self):
        for etat in ("annule", "en_cours"):                                                 # non gelé
            bc = self.bc_en_etat(etat)
            with self.subTest(etat=etat):
                self.refuse_par_check("UPDATE bons_commande SET avancement='100.00', date_100_facture='2026-10-02' WHERE id=?", bc.b)
                self.assertIsNone(self.tente("UPDATE bons_commande SET avancement='100.00' WHERE id=?", bc.b))        # le cache sans date_100 reste libre

    def test_T47_H_statut_termine_implique_frozen_at_et_date_100_facture(self):
        bc = self.bc_en_etat("en_cours")                                                    # non gelé
        self.refuse_par_check("UPDATE bons_commande SET statut='termine', completed_at=?, avancement='100.00', date_100_facture='2026-10-02' "
                              "WHERE id=?", TS, bc.b)                                       # pas de frozen_at (et date_100 impossible sans lui)
        self.geler_bc(bc.b)
        self.refuse_par_check("UPDATE bons_commande SET statut='termine', completed_at=?, avancement='100.00' WHERE id=?", TS, bc.b)   # sans date_100
        self.assertIsNone(self.tente("UPDATE bons_commande SET statut='termine', completed_at=?, avancement='100.00', "
                                     "date_100_facture='2026-10-02' WHERE id=?", TS, bc.b))
        t = self.isole(set())                                                               # termine sans date_100_facture mais avec frozen_at : pas via un autre garde
        b2 = t.bc_en_etat("gele")
        msg = t.tente("UPDATE bons_commande SET statut='termine', completed_at=? WHERE id=?", TS, b2.b)
        self.assertIn("CHECK constraint failed", msg)

    def test_T47_H_coherence_statut_completed_at(self):
        bc = self.bc_en_etat("gele")
        self.refuse_par_check("UPDATE bons_commande SET completed_at=? WHERE id=?", TS, bc.b)                  # completed_at sans statut termine
        self.refuse_par_check("UPDATE bons_commande SET statut='termine', avancement='100.00', date_100_facture='2026-10-02' WHERE id=?", bc.b)  # termine sans completed_at

    def test_T47_H_coherence_statut_cancelled_at(self):
        bc = self.bc_en_etat("en_cours")
        self.refuse_par_check("UPDATE bons_commande SET cancelled_at=?, motif_annulation='m' WHERE id=?", TS, bc.b)   # cancelled_at sans statut annule
        self.refuse_par_check("UPDATE bons_commande SET statut='annule' WHERE id=?", bc.b)                              # annule sans cancelled_at
        self.refuse_par_check("UPDATE bons_commande SET statut='annule', cancelled_at=? WHERE id=?", TS, bc.b)         # sans motif
        self.assertIsNone(self.tente("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", TS, bc.b))

    def test_T47_H_les_check_restent_actifs_sur_un_bc_annule_meme_sans_le_trigger(self):
        """Sans tr_12_annule, les CHECK refusent encore ce qui rendrait un BC annulé incohérent : 005c ne les contourne pas."""
        t = self.isole(set())
        bc = t.bc_en_etat("annule")
        for sets, args in (("statut='en_cours'", ()), ("cancelled_at=NULL", ()), ("completed_at=?", (TS,)), ("motif_annulation=NULL", ()),
                           ("date_100_facture='2026-10-02'", ()), ("avancement='100.00', date_100_facture='2026-10-02'", ())):
            with self.subTest(sets=sets):
                msg = t.tente(f"UPDATE bons_commande SET {sets} WHERE id=?", *args, bc.b)
                self.assertIsNotNone(msg)
                self.assertIn("CHECK constraint failed", msg)
        bc2 = t.bc_en_etat("annule_gele")
        self.assertIn("CHECK constraint failed", t.tente("UPDATE bons_commande SET date_100_facture='2026-10-02' WHERE id=?", bc2.b))    # avancement ≠ 100
        self.assertIsNone(t.tente("UPDATE bons_commande SET avancement='100.00', date_100_facture='2026-10-02' WHERE id=?", bc2.b))

    def test_T47_H_les_formats_des_caches_et_de_updated_at_restent_controles_sur_un_bc_annule(self):
        """Les colonnes que 005c libère (et updated_at) gardent leurs CHECK de format : seule la garde du trigger a été levée."""
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            for valeur in ("abc", "1", "1.5", "01.00", "-1.00", "1.00.0", "", "1,00"):
                with self.subTest(etat=etat, colonne="montant_deja_facture_ht", valeur=valeur):
                    self.refuse_par_check("UPDATE bons_commande SET montant_deja_facture_ht=? WHERE id=?", valeur, bc.b)
            for valeur in ("100.01", "101.00", "1", "abc", "-1.00", "05.00", "10000.00", ""):
                with self.subTest(etat=etat, colonne="avancement", valeur=valeur):
                    self.refuse_par_check("UPDATE bons_commande SET avancement=? WHERE id=?", valeur, bc.b)
            for valeur in ("now", "2026-10-05", "2026-10-05 10:00:00.000", "", "05/10/2026"):
                with self.subTest(etat=etat, colonne="updated_at", valeur=valeur):
                    self.refuse_par_check("UPDATE bons_commande SET updated_at=? WHERE id=?", valeur, bc.b)
        bc = self.bc_en_etat("annule_gele")
        self.db.execute("UPDATE bons_commande SET avancement='100.00' WHERE id=?", (bc.b,))
        for valeur in ("2026-02-30", "02/10/2026", "2026-10-2", "20261002", "abc", "", "2026-13-01"):
            with self.subTest(colonne="date_100_facture", valeur=valeur):
                self.refuse_par_check("UPDATE bons_commande SET date_100_facture=? WHERE id=?", valeur, bc.b)
        for valeur in ("0.00", "0.01", "31.50", "99999.99"):                                 # valeurs bien formées acceptées (pas de plafond SQL : service)
            with self.subTest(colonne="montant_deja_facture_ht", ok=valeur):
                self.assertIsNone(self.tente("UPDATE bons_commande SET montant_deja_facture_ht=? WHERE id=?", valeur, bc.b))
        self.assertIsNone(self.tente("UPDATE bons_commande SET avancement='0.00' WHERE id=?", bc.b))
        self.assertIsNone(self.tente("UPDATE bons_commande SET date_100_facture='2026-02-28' WHERE id=?", bc.b))

    def test_T47_H_avec_tous_les_triggers_une_incoherence_de_cache_est_refusee_par_le_check_pas_par_tr_12(self):
        bc = self.bc_en_etat("annule_gele")
        msg = self.refuse_par_check("UPDATE bons_commande SET date_100_facture='2026-10-02' WHERE id=?", bc.b)
        self.assertIn("date_100_facture IS NULL OR avancement = '100.00'", msg)
        bc = self.bc_en_etat("annule")
        msg = self.refuse_par_check("UPDATE bons_commande SET avancement='100.00', date_100_facture='2026-10-02' WHERE id=?", bc.b)
        self.assertIn("date_100_facture IS NULL OR frozen_at IS NOT NULL", msg)


# --------------------------------------------------------------------------------------------------------------------
# I — BC non annulés
# --------------------------------------------------------------------------------------------------------------------
class BCNonAnnules(Base8):
    """Groupe I : 005c ne change rien pour un BC non annulé ; tr_12_annule ne s'applique qu'à OLD.statut = 'annule'."""

    def test_T47_I_comportement_identique_au_rang_7_pour_les_bc_non_annules(self):
        """Test différentiel : mêmes données, même instruction, rang 7 et rang 8 ; accepté / refusé et message identiques, colonne par colonne."""
        for etat in ETATS_NON_ANNULES:
            t7 = T.Base()
            t7.setUp()
            t8 = Base8()
            t8.setUp()
            b7, b8 = t7.bc_en_etat(etat), t8.bc_en_etat(etat)
            autre7, autre8 = t7.client(), t8.client()
            self.assertEqual((b7.b, autre7), (b8.b, autre8))
            acceptees = refusees = 0
            for col in T.COLONNES_BC:
                with self.subTest(etat=etat, colonne=col):
                    v7 = T.autre_valeur_bc(col, t7.valeur(b7.b, col) if hasattr(t7, "valeur") else t7.un(f"SELECT {col} FROM bons_commande WHERE id=?", b7.b)[0], autre7)
                    v8 = T.autre_valeur_bc(col, t8.valeur(b8.b, col), autre8)
                    self.assertEqual(v7, v8)
                    sql = f"UPDATE bons_commande SET {col}=? WHERE id=?"
                    r7, r8 = _tente(t7, sql, v7, b7.b), _tente(t8, sql, v8, b8.b)
                    self.assertEqual(r7, r8)
                    acceptees, refusees = acceptees + (r8 is None), refusees + (r8 is not None)
            self.assertGreater(acceptees, 0)
            self.assertGreater(refusees, 0)

    def test_T47_I_en_dehors_de_l_etat_annule_tr_12_annule_ne_leve_jamais_inv_173(self):
        """Avec tr_12_annule pour seul trigger, aucune modification d'un BC non annulé ne porte INV-173 (un CHECK peut refuser, pas ce trigger)."""
        autre = self.client()
        for etat in ETATS_NON_ANNULES:
            t = self.isole({TRIGGER})
            bc = t.bc_en_etat(etat)
            for col in PROTEGEES + CACHES + LIBRES:
                with self.subTest(etat=etat, colonne=col):
                    msg = t.tente(f"UPDATE bons_commande SET {col}=? WHERE id=?", T.autre_valeur_bc(col, t.valeur(bc.b, col), autre), bc.b)
                    self.assertTrue(msg is None or "INV-173" not in msg, msg)

    def test_T47_I_colonnes_librement_modifiables_d_un_bc_non_annule(self):
        """Contrepartie positive : date_debut, date_fin, caches et updated_at passent sur un BC non annulé (le trigger ne s'applique pas)."""
        for etat in ETATS_NON_ANNULES:
            for sets, args in (("date_debut='2026-11-01'", ()), ("date_fin='2026-11-30'", ()), ("montant_deja_facture_ht='7.00'", ()),
                               ("avancement='20.00'" if etat != "termine" else "avancement='100.00'", ()), ("updated_at=?", (TS2,))):
                with self.subTest(etat=etat, sets=sets):
                    bc = self.bc_en_etat(etat)
                    self.assertIsNone(self.tente(f"UPDATE bons_commande SET {sets} WHERE id=?", *args, bc.b))

    def test_T47_I_les_transitions_de_statut_d_un_bc_non_annule_ne_sont_pas_arretees_par_tr_12_annule(self):
        t = self.isole({TRIGGER})
        for etat in ETATS_NON_ANNULES:
            with self.subTest(etat=etat):
                bc = t.bc_en_etat(etat)
                self.assertIsNone(t.tente("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='m', completed_at=NULL, "
                                          "date_100_facture=NULL WHERE id=?", T.TS_ANNUL, bc.b))
        bc = t.bc_en_etat("termine")
        self.assertIsNone(t.tente("UPDATE bons_commande SET statut='en_cours', completed_at=NULL WHERE id=?", bc.b))      # termine → en_cours (état dérivé)


def _tente(t, sql, *args):
    """tente() sur une instance quelconque de T.Base (rang 7 ou 8)."""
    t.db.execute("SAVEPOINT tente")
    try:
        t.db.execute(sql, args)
        return None
    except sqlite3.IntegrityError as e:
        return str(e)
    finally:
        t.db.execute("ROLLBACK TO tente")
        t.db.execute("RELEASE tente")


# --------------------------------------------------------------------------------------------------------------------
# J — atomicité
# --------------------------------------------------------------------------------------------------------------------
class Atomicite(Base8):
    """Groupe J : une transaction qui autorise les caches puis tente une modification interdite est annulée si elle échoue."""

    def test_T47_J_cache_autorise_puis_modification_interdite_annule_la_transaction(self):
        bc = self.bc_annule_apres_facturation()
        avant = self.bc(bc.b)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht='0.00', avancement='0.00', date_100_facture=NULL WHERE id=?", (bc.b,))
            self.assertEqual(self.valeur(bc.b, "avancement"), "0.00")                       # visible dans la transaction
            with self.assertRaisesRegex(sqlite3.IntegrityError, RE_ANNULE):
                self.db.execute("UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (bc.b,))
            self.db.execute("ROLLBACK")                                                     # le service annule la transaction sur l'échec
        finally:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
        self.assertEqual(self.bc(bc.b), avant)

    def test_T47_J_savepoint_la_modification_autorisee_precedente_est_conservee_si_seule_l_interdite_est_annulee(self):
        bc = self.bc_annule_apres_facturation()
        self.db.execute("BEGIN IMMEDIATE")
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht='5.00', avancement='20.00', updated_at=? WHERE id=?", (TS2, bc.b))
        self.db.execute("SAVEPOINT interdit")
        with self.assertRaisesRegex(sqlite3.IntegrityError, RE_ANNULE):
            self.db.execute("UPDATE bons_commande SET client_snapshot='{}' WHERE id=?", (bc.b,))
        self.db.execute("ROLLBACK TO interdit")
        self.db.execute("RELEASE interdit")
        self.db.execute("COMMIT")
        r = self.bc(bc.b)
        self.assertEqual((r["montant_deja_facture_ht"], r["avancement"], r["updated_at"], r["client_snapshot"] != "{}"), ("5.00", "20.00", TS2, True))

    def test_T47_J_une_instruction_multi_lignes_refusee_n_ecrit_rien(self):
        """UPDATE sans WHERE sur tous les BC : permis pour un BC en cours, interdit pour le BC annulé → l'instruction entière est annulée."""
        en_cours = self.bc_en_etat("en_cours")
        annule = self.bc_en_etat("annule")
        avant = (self.bc(en_cours.b), self.bc(annule.b))
        with self.assertRaisesRegex(sqlite3.IntegrityError, RE_ANNULE):
            self.db.execute("UPDATE bons_commande SET date_debut='2026-11-01'")
        self.assertEqual((self.bc(en_cours.b), self.bc(annule.b)), avant)
        self.db.execute("UPDATE bons_commande SET avancement='10.00'")                      # un cache : permis pour les deux
        self.assertEqual(self.tous("SELECT avancement FROM bons_commande ORDER BY id"), [("10.00",), ("10.00",)])

    def test_T47_J_echec_d_une_migration_n_a_pas_d_effet_partiel_sur_les_caches(self):
        """INTERPRETATION : l'application de 005c n'efface ni ne déplace aucune donnée ; un BC annulé migré garde ses caches à l'identique."""
        t7 = T.Base()
        t7.setUp()
        bc = t7.bc_en_etat("termine")
        t7.annuler_bc(bc.b)
        avant = t7.un("SELECT montant_deja_facture_ht, avancement, date_100_facture, statut FROM bons_commande WHERE id=?", bc.b)
        with self.assertRaises(sqlite3.Error):
            T.runner(t7.db, RANG, SQL_005C + "SELECT * FROM table_qui_n_existe_pas;\n")
        self.assertEqual(t7.un("SELECT montant_deja_facture_ht, avancement, date_100_facture, statut FROM bons_commande WHERE id=?", bc.b), avant)
        self.assertEqual(_tente(t7, "UPDATE bons_commande SET avancement='5.00' WHERE id=?", bc.b), MESSAGE.replace(
            "seules les evolutions autorisees sont modifiables", "seul updated_at est modifiable"))   # toujours le trigger de 005b : rien n'a été appliqué


# --------------------------------------------------------------------------------------------------------------------
# K — régressions 005b ; L — anti-contournement
# --------------------------------------------------------------------------------------------------------------------
class Regression005b(Base8):
    """Groupe K : comportements structurants de 005b, vérifiés sur la chaîne complète du rang 8 (pas la campagne entière de test_005b)."""

    def test_T47_K_tr_01_numero_et_date_creation_immuables(self):
        for etat in T.ETATS_BC:
            bc = self.bc_en_etat(etat)
            with self.subTest(etat=etat):
                self.assertRegex(self.tente("UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", bc.b), "INV-23")

    def test_T47_K_tr_12_contrat_garde_le_contenu_contractuel_des_bc_non_annules(self):
        autre = self.client()
        for etat in ETATS_NON_ANNULES:
            bc = self.bc_en_etat(etat)
            for col in ("client_id", "client_snapshot", "entreprise_snapshot_version", "chantier_snapshot", "date_acceptation", "origine", "legacy_id"):
                with self.subTest(etat=etat, colonne=col):
                    msg = self.tente(f"UPDATE bons_commande SET {col}=? WHERE id=?", T.autre_valeur_bc(col, self.valeur(bc.b, col), autre), bc.b)
                    self.assertRegex(msg, "INV-186")

    def test_T47_K_tr_14_frozen_at_irreversible_sur_un_bc_non_annule(self):
        bc = self.bc_en_etat("gele")
        self.assertRegex(self.tente("UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc.b), "INV-34")
        self.assertRegex(self.tente("UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc.b), "INV-(34|186)")

    def test_T47_K_tr_17_etat_de_naissance_les_caches_naissent_a_zero(self):
        """005c n'ouvre pas la naissance : un BC qui naît avec des caches non nuls reste refusé (INV-40)."""
        for col, valeur in (("montant_deja_facture_ht", "5.00"), ("avancement", "5.00"), ("frozen_at", TS), ("motif_annulation", "m")):
            with self.subTest(colonne=col):
                self.db.execute("SAVEPOINT s")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-40"):
                    self.creer_bc(self.devis_accepte(), lignes=False, **{col: valeur})
                self.db.execute("ROLLBACK TO s")
                self.db.execute("RELEASE s")

    def test_T47_K_tr_13_lignes_et_garanties_d_un_bc_annule_restent_figees(self):
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat, dl3=True)
            with self.subTest(etat=etat):
                self.refuse_inv("INV-173", "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", bc.bl2)
                self.assertRegex(self.tente("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                                            "remise_type, type_prestation, total_ht) SELECT ?, id, 3, designation, quantite, unite, prix_unitaire_ht, "
                                            "remise_type, type_prestation, total_ht FROM devis_lignes WHERE id=?", bc.b, bc.dl3), "INV-173")
                self.refuse_inv("INV-186", "UPDATE bc_lignes SET quantite='9' WHERE id=?", bc.bl2)
                self.refuse_inv("INV-186", "DELETE FROM bc_lignes WHERE id=?", bc.bl2)
                self.refuse_inv("INV-186", "UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", bc.bg1)
                self.refuse_inv("INV-186", "DELETE FROM bc_ligne_garanties WHERE id=?", bc.bg1)

    def test_T47_K_tr_99_un_bc_annule_ne_recoit_aucun_devis_et_les_liens_sont_figes(self):
        bc = self.bc_en_etat("annule")
        self.refuse_inv("INV-188", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b, self.devis_accepte(client_id=self.client_du_bc(bc.b)))
        vivant = self.bc_en_etat("en_cours")
        self.refuse_inv("INV-184", "UPDATE bc_devis SET rang=9 WHERE bc_id=?", vivant.b)
        self.refuse_inv("INV-184", "DELETE FROM bc_devis WHERE bc_id=?", vivant.b)

    def test_T47_K_les_caches_evoluent_sans_toucher_aux_devis_ni_aux_lignes(self):
        """INV-188 : aucune cascade ; la mise à jour des caches d'un BC annulé ne modifie ni devis, ni liens, ni lignes, ni garanties."""
        bc = self.bc_annule_apres_facturation()
        tables = ("devis", "devis_lignes", "devis_ligne_garanties", "bc_devis", "bc_lignes", "bc_ligne_garanties", "devis_revisions")
        avant = {t: self.tous(f"SELECT * FROM {t} ORDER BY id") for t in tables}
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht='1.00', avancement='3.00', date_100_facture=NULL, updated_at=? WHERE id=?", (TS2, bc.b))
        for t, lignes in avant.items():
            self.assertEqual(self.tous(f"SELECT * FROM {t} ORDER BY id"), lignes, t)
        self.assertEqual(self.tous("SELECT statut FROM devis WHERE id=?", bc.d), [("accepte",)])           # le devis n'est pas annulé en cascade

    def test_T47_K_tr_18_un_devis_rattache_ne_quitte_accepte_que_si_son_bc_est_annule(self):
        bc = self.bc_en_etat("en_cours")
        self.refuse_inv("INV-175", "UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", TS, bc.d)

    def test_T47_K_la_chaine_001_005b_est_inchangee(self):
        """Les fichiers 001 à 005b ne sont pas lus autrement que par leur rang : leurs objets sont identiques au rang 7 (cf. groupe A)."""
        self.assertEqual(T.NOMS, NOMS[:7])
        self.assertEqual(T.TRIGGERS_REECRITS & {TRIGGER}, {TRIGGER})
        self.assertEqual(T.noms(self.db, "table"), T.TABLES_RANG7)


class AntiContournement(Base8):
    """Groupe L : la protection du BC annulé ne se contourne ni par REPLACE, ni par remplacement de ligne, ni par UPSERT, ni par
    UPDATE OR REPLACE / OR IGNORE. Les contraintes structurelles de 004/005b couvrent déjà ces voies (tr_19 avec recursive_triggers=ON, D-39) :
    005c n'ajoute aucune protection SQL, ce groupe en fixe le comportement."""

    COLS = ("numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
            "chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, montant_contractuel_ht")

    def ligne_naissance(self, b):
        return self.un(f"SELECT {self.COLS} FROM bons_commande WHERE id=?", b)

    def test_INV_174_delete_et_replace_d_un_bc_annule_sont_refuses(self):
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            avant = self.bc(bc.b)
            r = self.ligne_naissance(bc.b)
            marques = ",".join("?" * 12)
            with self.subTest(etat=etat):
                self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", bc.b)
                self.refuse_inv("INV-174", f"INSERT OR REPLACE INTO bons_commande (id, {self.COLS}) VALUES ({marques})", bc.b, *r)
                self.refuse_inv("INV-174", f"REPLACE INTO bons_commande (id, {self.COLS}) VALUES ({marques})", bc.b, *r)
                self.refuse_inv("INV-174", f"INSERT OR REPLACE INTO bons_commande ({self.COLS}) VALUES ({','.join('?' * 11)})", *r)    # conflit sur numero
                self.assertEqual(self.bc(bc.b), avant)

    def test_T47_L_remplacer_la_ligne_par_delete_puis_insert_est_impossible(self):
        bc = self.bc_en_etat("annule_gele")
        r = self.ligne_naissance(bc.b)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", bc.b)
        self.assertEqual(self.tous("SELECT count(*) FROM bons_commande WHERE id=?", bc.b), [(1,)])
        self.refuse("INSERT INTO bons_commande (id, " + self.COLS + ") VALUES (" + ",".join("?" * 12) + ")", bc.b, *r)    # l'id existe déjà

    def test_T47_L_upsert_do_update_applique_tr_12_annule(self):
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            r = self.ligne_naissance(bc.b)
            ins = f"INSERT INTO bons_commande (id, {self.COLS}) VALUES (?,{','.join('?' * 11)}) ON CONFLICT(id) DO UPDATE SET "
            with self.subTest(etat=etat):
                self.refuse_inv(RE_ANNULE, ins + "statut='en_cours', cancelled_at=NULL, motif_annulation=NULL", bc.b, *r)
                self.refuse_inv(RE_ANNULE, ins + "montant_contractuel_ht='1.00'", bc.b, *r)
                self.refuse_inv(RE_ANNULE, ins + "montant_deja_facture_ht='9.00', date_debut='2026-11-01'", bc.b, *r)
                self.assertIsNone(self.tente(ins + "montant_deja_facture_ht='9.00', avancement='9.00'", bc.b, *r))           # cache : même voie que l'UPDATE

    def test_T47_L_update_or_replace_et_update_or_ignore_ne_contournent_pas_la_garde(self):
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            avant = self.bc(bc.b)
            for verbe in ("UPDATE OR REPLACE", "UPDATE OR IGNORE", "UPDATE OR ROLLBACK", "UPDATE OR ABORT", "UPDATE OR FAIL"):
                with self.subTest(etat=etat, verbe=verbe):
                    self.db.execute("SAVEPOINT s")
                    with self.assertRaisesRegex(sqlite3.IntegrityError, RE_ANNULE):
                        self.db.execute(f"{verbe} bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (bc.b,))
                    if self.db.in_transaction:
                        self.db.execute("ROLLBACK TO s")
                        self.db.execute("RELEASE s")
                    self.assertEqual(self.bc(bc.b), avant)

    def test_T47_L_rename_de_l_identifiant_et_du_numero_refuses(self):
        for etat in ETATS_ANNULES:
            bc = self.bc_en_etat(etat)
            with self.subTest(etat=etat):
                self.refuse_inv(RE_ANNULE, "UPDATE bons_commande SET id=id+1000 WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero='BCD-00098-26' WHERE id=?", bc.b)

    def test_T47_L_INTERPRETATION_temoin_sans_recursive_triggers_le_replace_n_est_pas_arrete(self):
        """Témoin D-39 : le REPLACE ne déclenche pas le trigger DELETE si recursive_triggers=OFF ; c'est pourquoi ce réglage est obligatoire
        à chaque connexion (conventions §5). 005c ne porte pas ce réglage et n'ajoute aucune protection : on fixe seulement le constat."""
        t = Base8()
        t.db = migrer8(recursive=False)
        t._n = 0
        self.assertEqual(t.un("PRAGMA recursive_triggers")[0], 0)
        b = t.creer_bc(t.devis_accepte(), lignes=False, lier=False)                         # sans enfant : le REPLACE ne se heurte à aucune FK
        t.annuler_bc(b)
        r = t.un(f"SELECT {self.COLS} FROM bons_commande WHERE id=?", b)
        t.db.execute(f"INSERT OR REPLACE INTO bons_commande (id, {self.COLS}) VALUES (?,{','.join('?' * 11)})", (b, *r))
        self.assertEqual(t.valeur(b, "statut"), "en_cours")                                 # le BC annulé a été remplacé : la connexion est le garde


if __name__ == "__main__":
    unittest.main()
