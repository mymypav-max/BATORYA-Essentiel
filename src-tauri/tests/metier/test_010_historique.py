"""Tranche 010_historique (rang 16, D-64, test T-55) ; modèle de données V3.14 §2.5 (énumérations), §4.14 (table), §8 (TR-60), §15 (D-64), §17.1 ;
invariants INV-110 (journal append-only, événements obligatoires, structure des événements `acceptation`), INV-111 (énumérations fermées), INV-07
(réglages de connexion), INV-175 et conventions techniques §9 (aucun contrôle de miroir dans un CHECK ou un trigger), INV-174 (aucun BC supprimé) ;
décisions du propriétaire du 2026-10-22 (cadrage de la tranche 010).

La migration crée la table `historique` (STRICT), trois index et deux triggers append-only (TR-60) : rien d'autre. Ce test vérifie le SCHÉMA :
  * ce que la table garantit : types, énumérations fermées, JSON valide, absence d'octet NUL dans `donnees` et `created_at` (même mécanisme que 009_pv.sql),
    format de `created_at`, clé étrangère `bc_id`, structure LOCALE des événements
    `acceptation` (dont `bc_id` NON NULL pour les deux natures), append-only (sous réserve de `recursive_triggers=ON`) ;
  * ce que la table ne garantit PAS, et que des témoins documentent : l'existence de `entite_id` (lien polymorphe sans clé étrangère, sans CHECK), la
    concordance de `bc_id` avec le BC du devis dans `bc_devis` (garantie par le service dans la transaction d'acceptation ou de réacceptation), la
    structure de `donnees` hors `acceptation` (`json_valid` seulement : un tableau JSON reste accepté), l'appariement `type_evenement` × `type_entite`.
Aucun contrôle inter-tables n'est testé ici : la migration n'en livre aucun et aucun identifiant de contrôle n'a été attribué à ces règles.

Limites de ce que ces tests prouvent :
  * la protection append-only DÉPEND de `PRAGMA recursive_triggers=ON` (conventions §9) : avec `OFF`, un `INSERT OR REPLACE` sur un id existant écrase la
    ligne sans déclencher le trigger DELETE. Le témoin du groupe F l'établit sur le moteur de test (SQLite du module `sqlite3` de l'interpréteur) ; ce n'est
    pas une garantie universelle, ni une protection valide hors configuration conforme ;
  * aucun trigger supplémentaire n'existe pour fermer ce cas (décision du propriétaire, 2026-10-22) ;
  * `created_at` est contrôlé par sa FORME (GLOB), non par la validité calendaire, comme les autres horodatages de la chaîne.
Groupes : A chaîne, B structure, C énumérations, D `donnees`, `created_at` et références, E événements `acceptation`, F append-only,
G immuabilité des migrations antérieures, H non-régression, M conformité au modèle V3.14.
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39), relu ; sauf le témoin qui le précise.

Exécution : python3 src-tauri/tests/metier/test_010_historique.py
"""
import hashlib
import json
import pathlib
import re
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_009c_bc_annulation_acompte_encaissement as C  # noqa: E402  (chaîne 001 à 009c, fabriques de devis, BC, factures ; runner)

B = C.B
T = C.T
MIGRATIONS = C.MIGRATIONS
NOM_010 = "010_historique.sql"
NOMS = C.NOMS + (NOM_010,)
SQL_010 = (MIGRATIONS / NOM_010).read_text(encoding="utf-8")
RANG = 16
MODELE = pathlib.Path(__file__).resolve().parents[3] / "docs" / "conception" / "modèle-données-sqlite-v6-v3.14.md"
TABLE = "historique"
INDEXES = {"idx_historique_bc_id": ["bc_id"],
           "idx_historique_type_entite_entite_id": ["type_entite", "entite_id"],
           "idx_historique_created_at": ["created_at"]}
TRIGGERS = {"tr_60_historique_no_update": "BEFORE UPDATE ON historique", "tr_60_historique_no_delete": "BEFORE DELETE ON historique"}
RE_INV110 = r"INV-110"

# Énumérations du modèle V3.14 §2.5 (le groupe M vérifie qu'elles sont identiques à celles du modèle).
TYPES_ENTITE = ("client", "fournisseur", "prestation", "devis", "bc", "facture", "reglement", "depense", "pv", "garantie", "planning_evenement",
                "bc_note", "urssaf_periode", "urssaf_correction", "document", "import", "restauration")
TYPES_EVENEMENT = ("creation", "modification", "acceptation", "refus", "annulation", "emission", "reglement", "annulation_reglement", "remboursement",
                   "avoir", "passage_termine", "retour_en_cours", "declenchement_garantie", "rattachement_client", "declaration_urssaf",
                   "correction_urssaf", "import", "restauration")
ACTEURS = ("utilisateur", "systeme", "import")

# Empreintes SHA-256 (fins de ligne normalisées en LF) des quinze migrations livrées avant 010 : aucune ne doit changer (main a99d4c2 + chaîne locale).
EMPREINTES_ANTERIEURES = {
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
    "009a_bc_annulation_interdite_si_facture.sql": "23c49c6fe44fe77ceef040b2441e3fb7406ecb20e00cf8e9793d43e22545e9e3",
    "009b_acompte_garanties_manuelles.sql": "05677212c5e2459fb8e6b9a0359de6762f9eb9f8c4959789db1f012edd53d088",
    "009c_bc_annulation_acompte_encaissement.sql": "dcecf55243e51da529a14c1b0b02a3045c0b986d4c5c7e3a6da46222c54a577e",
}

NUL = chr(0)                                                                                        # octet NUL brut
ECH_NUL = chr(92) + "u0000"                                                                          # échappement JSON de U+0000 : six caractères, aucun octet NUL
GLOB_CREATED_AT = "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'"
ABS = object()                                                                                      # clé absente d'une charge utile
COLONNES = ("type_entite", "entite_id", "bc_id", "type_evenement", "acteur", "donnees", "created_at")


def migrer16(recursive=True):
    """Chaîne 001 à 009c (rang 15) puis 010 avec le protocole du runner : BEGIN IMMEDIATE, fichier, foreign_key_check, integrity_check, user_version = 16, COMMIT."""
    db = C.migrer15(recursive=recursive)
    T.runner(db, RANG, SQL_010)
    return db


def sql_ins(**kw):
    """INSERT dans historique des seules colonnes fournies ; dict et list sont sérialisés en JSON, une chaîne est transmise telle quelle."""
    cols = [c for c in COLONNES if c in kw]
    vals = tuple(json.dumps(kw[c]) if isinstance(kw[c], (dict, list)) else kw[c] for c in cols)
    return "INSERT INTO historique (%s) VALUES (%s)" % (", ".join(cols), ", ".join("?" * len(cols))), vals


def initiale(**ch):
    """Charge utile d'une acceptation initiale (valide) ; ABS retire une clé."""
    d = {"revision": None, "date_acceptation": "2026-10-22", "nature": "initiale"}
    d.update(ch)
    return {k: v for k, v in d.items() if v is not ABS}


def reacceptation(**ch):
    """Charge utile d'une réacceptation (valide) ; ABS retire une clé."""
    d = {"revision": 2, "date_acceptation": "2026-11-02", "nature": "reacceptation",
         "precedente": {"revision": None, "date_acceptation": "2026-10-22"}}
    d.update(ch)
    return {k: v for k, v in d.items() if v is not ABS}


def _norm(sql):
    return re.sub(r"\s+", " ", sql).strip().rstrip(";").strip()


def modele():
    return MODELE.read_text(encoding="utf-8")


def liste_modele(cle):
    m = re.search(r"^\| `" + re.escape(cle) + r"` \| (.*) \|$", modele(), re.M)
    return tuple(re.findall(r"`([^`]+)`", m.group(1)))


class Base16(C.Base15):
    """Base au rang 16 (chaîne 001 à 010). Fabriques héritées (test_005b à test_009c) ; un BC réel n'est créé qu'à la demande."""

    def setUp(self):
        self.db = migrer16()
        self._n = 0
        self._npv = {}
        self.desynchroniser_ids()
        self._bc = None

    def un_bc(self):
        if self._bc is None:
            self._bc = self.bc6000()
        return self._bc.b

    def un_devis(self):
        self.un_bc()
        return self._bc.d[0]

    def ajoute(self, **kw):
        sql, p = sql_ins(**kw)
        return self.db.execute(sql, p).lastrowid

    def insere(self, **kw):
        """Insertion acceptée : None si elle réussit, sinon le message d'erreur (échec du test)."""
        sql, p = sql_ins(**kw)
        m = self.essai(sql, p)
        self.assertIsNone(m, m)

    def rejette(self, **kw):
        """Insertion refusée par une contrainte (CHECK, NOT NULL, FK, STRICT) et non par un trigger."""
        sql, p = sql_ins(**kw)
        self.refuse_check(sql, p)

    def acceptation(self, donnees, **kw):
        base = dict(type_entite="devis", entite_id=self.un_devis(), bc_id=self.un_bc(), type_evenement="acceptation", donnees=donnees)
        base.update(kw)
        return base

    def lignes(self):
        return self.tous("SELECT * FROM historique ORDER BY id")


# --------------------------------------------------------------------------------------------------------------------
# A — chaîne de migration
# --------------------------------------------------------------------------------------------------------------------
class Chaine(Base16):
    def test_010_A_fichiers_de_la_chaine_dans_l_ordre(self):
        noms = [p.name for p in sorted(MIGRATIONS.glob("*.sql"))]
        self.assertEqual(noms[:16], list(NOMS))
        self.assertEqual(noms[15], NOM_010)
        self.assertEqual(len(NOMS), RANG)
        self.assertLess(C.NOM_009C, NOM_010)                                                        # 010 s'ordonne après 009c
        self.assertTrue(all(n > NOM_010 for n in noms[RANG:]))                                      # toute migration suivante (010a, 011, …) s'ordonne après 010
        self.assertRegex(NOM_010, r"^[0-9]{3}_[a-z0-9_]+\.sql$")                                    # tranche métier NNN_<objet>.sql (conventions techniques §5)

    def test_010_A_rang_16_et_user_version(self):
        db = C.migrer15()
        self.assertEqual(T.db_user_version(db), 15)
        T.runner(db, RANG, SQL_010)
        self.assertEqual(T.db_user_version(db), 16)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_010_A_aucune_transaction_aucun_pragma_aucune_donnee_dans_le_fichier(self):
        code = T.sans_commentaires(SQL_010)
        self.assertIsNone(re.search(r"\b(COMMIT|ROLLBACK|SAVEPOINT|RELEASE|ALTER)\b", code, re.I))
        self.assertIsNone(re.search(r"\bPRAGMA\s", code, re.I))                                     # la garde lit pragma_user_version (fonction), aucun PRAGMA de réglage
        self.assertIsNone(re.search(r"\bBEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)\b", code, re.I))
        self.assertEqual(len(re.findall(r"\bBEGIN\b", code, re.I)), 2)                              # les BEGIN des corps des deux triggers, aucune transaction
        self.assertIsNone(re.search(r"\bDELETE\s+FROM\b|\bUPDATE\s+\w+\s+SET\b|\bREPLACE\b", code, re.I))
        self.assertEqual(re.findall(r"\bINSERT\s+INTO\s+(\w+)", code, re.I), ["garde_010_user_version"])      # seule l'insertion de la garde (table temporaire)
        self.assertEqual(re.findall(r"\bDROP\s+(\w+)\s+(\w+)", code, re.I), [("TABLE", "garde_010_user_version")])

    def test_010_A_objets_crees_exacts_aucun_objet_existant_modifie(self):
        creations = re.findall(r"CREATE\s+(TEMP\s+TABLE|TABLE|INDEX|TRIGGER)\s+(\w+)", T.sans_commentaires(SQL_010), re.I)
        self.assertEqual(sorted((t.upper().replace("TEMP TABLE", "TEMP"), n) for t, n in creations),
                         sorted([("TEMP", "garde_010_user_version"), ("TABLE", TABLE)] + [("INDEX", i) for i in INDEXES] + [("TRIGGER", t) for t in TRIGGERS]))
        avant, apres = C.schema(C.migrer15()), C.schema(self.db)
        nouveaux = set(apres) - set(avant)
        self.assertEqual(nouveaux, {("table", TABLE)} | {("index", i) for i in INDEXES} | {("trigger", t) for t in TRIGGERS})
        self.assertEqual({k for k in avant if k not in apres or avant[k] != apres[k]}, set())       # aucun objet existant supprimé ni modifié
        self.assertEqual(self.tous("SELECT name FROM sqlite_temp_master WHERE name LIKE 'garde_010%'"), [])

    def test_010_A_la_garde_refuse_toute_base_qui_n_est_pas_au_rang_15(self):
        for rang, base in ((13, B.migrer13()), (14, B.migrer14()), (16, migrer16())):
            with self.subTest(rang=rang):
                avant = (C.schema(base), T.db_user_version(base))
                with self.assertRaisesRegex(sqlite3.IntegrityError, "010 exige user_version = 15"):
                    T.runner(base, RANG, SQL_010)
                self.assertEqual((C.schema(base), T.db_user_version(base)), avant)                  # ROLLBACK intégral : ni table, ni user_version, ni table temporaire
                self.assertEqual(base.execute("SELECT name FROM sqlite_temp_master WHERE name LIKE 'garde_010%'").fetchall(), [])

    def test_010_A_une_base_peuplee_au_rang_15_est_migree_sans_perte(self):
        t = self._sur(C.migrer15())
        bc, _ = t.avec("acompte")
        avant = T.tout(t.db)
        T.runner(t.db, RANG, SQL_010)
        apres = T.tout(t.db)
        self.assertEqual(apres.pop(TABLE), [])                                                      # table créée vide : aucune donnée insérée par la migration
        self.assertEqual(apres, avant)                                                              # toutes les autres tables, séquences comprises, sont identiques
        self.assertEqual(T.db_user_version(t.db), 16)

    def test_010_A_un_echec_en_cours_de_fichier_ne_laisse_aucune_trace(self):
        """Témoin du protocole (ROLLBACK intégral) : un fichier identique mais dont la dernière instruction échoue ne crée rien."""
        db = C.migrer15()
        avant = (C.schema(db), T.db_user_version(db))
        with self.assertRaises(sqlite3.Error):
            T.runner(db, RANG, SQL_010 + "\nCREATE TABLE historique (x INTEGER);\n")
        self.assertEqual((C.schema(db), T.db_user_version(db)), avant)


# --------------------------------------------------------------------------------------------------------------------
# B — structure
# --------------------------------------------------------------------------------------------------------------------
class Structure(Base16):
    def test_010_B_table_stricte_et_colonnes_exactes(self):
        self.assertTrue(T.est_strict(self.db, TABLE))
        self.assertEqual(T.info_colonnes(self.db, TABLE), [
            ("id", "INTEGER", 0, None, 1, 0),
            ("type_entite", "TEXT", 1, None, 0, 0),
            ("entite_id", "INTEGER", 0, None, 0, 0),
            ("bc_id", "INTEGER", 0, None, 0, 0),
            ("type_evenement", "TEXT", 1, None, 0, 0),
            ("acteur", "TEXT", 1, "'utilisateur'", 0, 0),
            ("donnees", "TEXT", 0, None, 0, 0),
            ("created_at", "TEXT", 1, "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", 0, 0),
        ])
        self.assertNotIn("updated_at", T.colonnes(self.db, TABLE))                                  # pas de updated_at : journal append-only

    def test_010_B_controles_d_octets_NUL_presents_dans_le_DDL_de_donnees_et_created_at(self):
        ddl = _norm(T.sql_de(self.db, TABLE))
        self.assertIn("donnees IS NULL OR (json_valid(donnees) AND instr(CAST(donnees AS BLOB), x'00') = 0)", ddl)
        self.assertIn("AND length(CAST(created_at AS BLOB)) = 24", ddl)

    def test_010_B_cle_primaire_autoincrement_identifiants_jamais_reutilises(self):
        self.assertIn("AUTOINCREMENT", T.sql_de(self.db, TABLE).upper())
        a = self.ajoute(type_entite="client", type_evenement="creation")
        b = self.ajoute(type_entite="client", type_evenement="creation")
        self.assertEqual((a, b), (1, 2))
        self.assertEqual(self.un("SELECT seq FROM sqlite_sequence WHERE name='historique'")[0], 2)

    def test_010_B_une_seule_cle_etrangere_bc_id_vers_bons_commande_RESTRICT_sans_ON_UPDATE(self):
        self.assertEqual(T.cles_etrangeres(self.db, TABLE), [("bons_commande", "bc_id", "id", "NO ACTION", "RESTRICT")])

    def test_010_B_entite_id_sans_cle_etrangere_lien_polymorphe(self):
        self.assertNotIn("entite_id", {r[3] for r in self.tous("PRAGMA foreign_key_list(historique)")})

    def test_010_B_trois_index_non_uniques_et_aucun_index_unique_hors_cle_primaire(self):
        index = {r[1]: (r[2], r[3]) for r in self.tous("PRAGMA index_list(historique)")}
        self.assertEqual(set(index), set(INDEXES))                                                  # exactement les trois index prévus, aucun index automatique
        for nom, colonnes in INDEXES.items():
            with self.subTest(index=nom):
                self.assertEqual(index[nom], (0, "c"))                                              # non unique, créé par CREATE INDEX
                self.assertEqual([r[2] for r in self.tous(f"PRAGMA index_info({nom})")], colonnes)
        self.assertEqual([n for n, (u, _) in index.items() if u], [])

    def test_010_B_exactement_deux_triggers_append_only_aucun_troisieme(self):
        triggers = dict(self.tous("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='historique'"))
        self.assertEqual(set(triggers), set(TRIGGERS))
        for nom, debut in TRIGGERS.items():
            with self.subTest(trigger=nom):
                self.assertTrue(_norm(triggers[nom]).startswith(f"CREATE TRIGGER {nom} {debut} BEGIN SELECT RAISE(ABORT, 'INV-110: "), triggers[nom])

    def test_010_B_les_messages_des_triggers_sont_ASCII_et_portent_INV_110(self):
        for nom, sql in self.tous("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='historique'"):
            msgs = re.findall(r"RAISE\(ABORT, '((?:[^']|'')*)'\)", sql)
            self.assertEqual(len(msgs), 1, nom)
            self.assertTrue(msgs[0].isascii(), (nom, msgs[0]))
            self.assertRegex(msgs[0], r"^INV-110: ", (nom, msgs[0]))


# --------------------------------------------------------------------------------------------------------------------
# C — énumérations fermées (INV-111)
# --------------------------------------------------------------------------------------------------------------------
class Enumerations(Base16):
    def test_INV_111_C1_chaque_type_entite_autorise_est_accepte(self):
        for te in TYPES_ENTITE:
            with self.subTest(type_entite=te):
                self.insere(type_entite=te, type_evenement="creation")

    def test_INV_111_C2_chaque_type_evenement_autorise_est_accepte(self):
        for ev in TYPES_EVENEMENT:
            with self.subTest(type_evenement=ev):
                if ev == "acceptation":
                    self.insere(**self.acceptation(initiale()))
                else:
                    self.insere(type_entite="bc", type_evenement=ev)

    def test_INV_111_C3_chaque_acteur_autorise_est_accepte_et_le_defaut_est_utilisateur(self):
        for a in ACTEURS:
            with self.subTest(acteur=a):
                self.insere(type_entite="bc", type_evenement="creation", acteur=a)
        r = self.ajoute(type_entite="bc", type_evenement="creation")
        self.assertEqual(self.un("SELECT acteur FROM historique WHERE id=?", r)[0], "utilisateur")

    def test_INV_111_C4_type_entite_hors_liste_ou_mal_forme_refuse(self):
        for v in ("gel", "suppression", "", "Client", "CLIENT", "devis ", "bons_commande", "planning_evenements"):
            with self.subTest(valeur=v):
                self.rejette(type_entite=v, type_evenement="creation")

    def test_INV_111_C5_type_evenement_hors_liste_ou_mal_forme_refuse(self):
        for v in ("suppression", "gel", "", "Creation", "ACCEPTATION", "acceptation ", "annulation_automatique"):
            with self.subTest(valeur=v):
                self.rejette(type_entite="bc", type_evenement=v)

    def test_INV_111_C6_acteur_hors_liste_ou_mal_forme_refuse(self):
        for v in ("admin", "", "Systeme", "utilisateur ", "systeme,import"):
            with self.subTest(valeur=v):
                self.rejette(type_entite="bc", type_evenement="creation", acteur=v)

    def test_INV_111_C7_les_trois_colonnes_obligatoires_refusent_NULL(self):
        for col in ("type_entite", "type_evenement", "acteur", "created_at"):
            with self.subTest(colonne=col):
                cols = {"type_entite": "bc", "type_evenement": "creation", "acteur": "systeme", "created_at": "2026-10-22T10:00:00.000Z"}
                cols[col] = None
                self.rejette(**cols)

    def test_INV_111_C8_suppression_n_est_pas_un_type_evenement(self):
        self.assertNotIn("suppression", TYPES_EVENEMENT)
        self.assertEqual(len(TYPES_EVENEMENT), 18)
        self.assertEqual(len(TYPES_ENTITE), 17)
        self.assertEqual(len(set(TYPES_EVENEMENT)), 18)


# --------------------------------------------------------------------------------------------------------------------
# D — donnees, created_at, références (bc_id, entite_id)
# --------------------------------------------------------------------------------------------------------------------
class Donnees(Base16):
    def test_INV_110_D1_donnees_NULL_accepte_hors_acceptation(self):
        r = self.ajoute(type_entite="bc", type_evenement="passage_termine", donnees=None)
        self.assertIsNone(self.un("SELECT donnees FROM historique WHERE id=?", r)[0])

    def test_INV_110_D2_donnees_objet_json_valide_accepte(self):
        for d in ({}, {"a": 1}, {"client_avant": 3, "client_apres": 8}, {"imbrique": {"x": [1, 2, {"y": None}]}}):
            with self.subTest(donnees=d):
                self.insere(type_entite="client", type_evenement="rattachement_client", donnees=d)

    def test_INV_110_D3_donnees_non_json_refuse(self):
        for d in ("abc", "{", "{'a': 1}", "", "[1,", '{"a": }', "nul"):
            with self.subTest(donnees=d):
                self.rejette(type_entite="bc", type_evenement="modification", donnees=d)

    def test_INV_110_D4_temoin_un_tableau_ou_un_scalaire_json_reste_accepte_hors_acceptation(self):
        """CONSTAT, pas une règle : le contrat SQL est `donnees IS NULL OR (json_valid(donnees) AND sans octet NUL brut)` ; aucune restriction à un objet (décision du propriétaire, 2026-10-22)."""
        for d in ([1, 2, 3], [], "[1]", "5", '"x"', "null", "true"):
            with self.subTest(donnees=d):
                self.insere(type_entite="bc", type_evenement="modification", donnees=d)

    def test_INV_110_D5_created_at_par_defaut_a_la_forme_attendue(self):
        r = self.ajoute(type_entite="bc", type_evenement="creation")
        v = self.un("SELECT created_at FROM historique WHERE id=?", r)[0]
        self.assertRegex(v, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    def test_INV_110_D6_created_at_explicite_valide_accepte(self):
        for v in ("2026-10-22T10:00:00.000Z", "2026-02-28T23:59:59.999Z", "1999-01-01T00:00:00.001Z"):
            with self.subTest(created_at=v):
                r = self.ajoute(type_entite="bc", type_evenement="creation", created_at=v)
                self.assertEqual(self.un("SELECT created_at FROM historique WHERE id=?", r)[0], v)

    def test_INV_110_D7_created_at_mal_forme_refuse(self):
        for v in ("2026-10-22", "2026-10-22 10:00:00", "2026-10-22T10:00:00Z", "2026-10-22T10:00:00.12Z", "2026-10-22T10:00:00.1234Z",
                  "2026-10-22T10:00:00.123z", "22/10/2026", "", "2026-10-22T10:00:00.123", "x026-10-22T10:00:00.123Z"):
            with self.subTest(created_at=v):
                self.rejette(type_entite="bc", type_evenement="creation", created_at=v)

    def test_INV_110_D8_bc_id_existant_accepte_et_NULL_permis_hors_acceptation(self):
        b = self.un_bc()
        self.insere(type_entite="bc", entite_id=b, bc_id=b, type_evenement="passage_termine")
        for te, ev in (("client", "creation"), ("fournisseur", "modification"), ("import", "import"), ("restauration", "restauration"), ("devis", "refus")):
            with self.subTest(type_entite=te, type_evenement=ev):
                self.insere(type_entite=te, type_evenement=ev, bc_id=None)

    def test_INV_110_D9_bc_id_inconnu_refuse_par_la_cle_etrangere(self):
        b = self.un_bc()
        for inconnu in (b + 1000, 0, -1):
            with self.subTest(bc_id=inconnu):
                sql, p = sql_ins(type_entite="bc", entite_id=1, bc_id=inconnu, type_evenement="passage_termine")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
                    self.db.execute(sql, p)

    def isole_bc(self, b):
        """Retire les gardes de suppression livrées et les enfants du BC `b` pour que la seule clé étrangère de `historique` puisse s'opposer à sa suppression."""
        for trigger in ("tr_19_bons_commande_no_delete", "tr_99_bc_devis_no_delete", "tr_13_bc_lignes_delete", "tr_13_bc_ligne_garanties_delete"):
            self.db.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        self.db.execute("DELETE FROM bc_ligne_garanties WHERE ligne_id IN (SELECT id FROM bc_lignes WHERE bc_id=?)", (b,))
        self.db.execute("DELETE FROM bc_lignes WHERE bc_id=?", (b,))
        self.db.execute("DELETE FROM bc_devis WHERE bc_id=?", (b,))

    def test_INV_110_D10_un_BC_reference_ne_se_supprime_pas(self):
        """TR-19 (INV-174) refuse déjà la suppression d'un BC. Second témoin : gardes livrées et enfants retirés, seule la clé étrangère `historique.bc_id` (RESTRICT)
        s'oppose à la suppression d'un BC référencé ; un BC isolé de la même façon mais non référencé se supprime."""
        b = self.un_bc()
        self.ajoute(type_entite="bc", entite_id=b, bc_id=b, type_evenement="passage_termine")
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", (b,))
        autre = self.monde(devis=[{"lignes": ["100.00"]}]).b
        self.isole_bc(b)
        self.isole_bc(autre)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
            self.db.execute("DELETE FROM bons_commande WHERE id=?", (b,))
        self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande WHERE id=?", b)[0], 1)
        self.db.execute("DELETE FROM bons_commande WHERE id=?", (autre,))                            # non référencé : supprimé, donc le refus ci-dessus vient bien de historique
        self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande WHERE id=?", autre)[0], 0)

    def test_INV_110_D11_temoin_entite_id_n_est_ni_une_cle_etrangere_ni_controle_par_un_CHECK(self):
        """CONSTAT, pas une règle : `entite_id` désigne la clé primaire de l'entité quand `type_entite` correspond à une table métier, mais le schéma ne le vérifie pas
        (lien polymorphe, §2.1) ; une référence orpheline et un NULL sont acceptés pour tout type, y compris pour les types dont l'entité est supprimable."""
        for te in TYPES_ENTITE:
            with self.subTest(type_entite=te, entite_id="inexistant"):
                self.insere(type_entite=te, entite_id=987654321, type_evenement="creation")
            with self.subTest(type_entite=te, entite_id="NULL"):
                self.insere(type_entite=te, entite_id=None, type_evenement="creation")
        self.insere(type_entite="client", entite_id=0, type_evenement="creation")
        self.insere(type_entite="client", entite_id=-5, type_evenement="creation")

    def test_INV_110_D12_les_evenements_import_et_restauration_s_enregistrent_sans_entite(self):
        a = self.ajoute(type_entite="import", entite_id=None, type_evenement="import", acteur="import",
                        donnees={"source": "sauvegarde.json", "anomalies": 0})
        b = self.ajoute(type_entite="restauration", entite_id=None, type_evenement="restauration", acteur="systeme")
        self.assertEqual(self.tous("SELECT id, entite_id, bc_id FROM historique ORDER BY id"), [(a, None, None), (b, None, None)])

    def test_INV_110_D13_entite_id_et_bc_id_refusent_un_texte_non_entier_table_STRICT(self):
        self.refuse_check("INSERT INTO historique (type_entite, entite_id, type_evenement) VALUES ('bc', 'abc', 'creation')")
        self.refuse_check("INSERT INTO historique (type_entite, bc_id, type_evenement) VALUES ('bc', 'abc', 'creation')")
        self.refuse_check("INSERT INTO historique (type_entite, entite_id, type_evenement) VALUES ('bc', 1.5, 'creation')")


    # --- octets NUL (même mécanisme que 009_pv.sql) -------------------------------------------------------------------------------
    def test_INV_110_D14_donnees_avec_octet_NUL_brut_refuse_quelle_que_soit_sa_position(self):
        """json_valid lit le TEXT comme une chaîne C : une queue après un NUL est ignorée. Témoin : pour les cas à queue, json_valid SEUL accepterait la valeur."""
        for d in ("{}" + NUL + "junk", '{"a":1}' + NUL + "{", "[1]" + NUL + "]", "null" + NUL + "x", "{}" + NUL, "{}" + NUL * 3):
            with self.subTest(donnees=repr(d)):
                self.assertEqual(self.un("SELECT json_valid(?)", d)[0], 1)                                   # json_valid seul l'accepterait
                self.assertGreater(self.un("SELECT instr(CAST(? AS BLOB), x'00')", d)[0], 0)
                self.rejette(type_entite="bc", type_evenement="modification", donnees=d)
        for d in (NUL, NUL + "{}", '{"a":"x' + NUL + 'y"}'):
            with self.subTest(donnees=repr(d)):
                self.rejette(type_entite="bc", type_evenement="modification", donnees=d)

    def test_INV_110_D15_echappement_JSON_u0000_sans_octet_NUL_reste_valide_hors_acceptation(self):
        """CONSTAT : l'échappement `\\u0000` (six caractères) n'est pas un octet NUL ; il reste accepté dans un événement libre."""
        for d in ('{"a":"x' + ECH_NUL + 'y"}', '"' + ECH_NUL + '"', '["' + ECH_NUL + '"]'):
            with self.subTest(donnees=d):
                self.assertEqual(self.un("SELECT instr(CAST(? AS BLOB), x'00')", d)[0], 0)
                self.insere(type_entite="bc", type_evenement="modification", donnees=d)

    def test_INV_110_D16_donnees_JSON_non_ASCII_sans_NUL_accepte(self):
        for d in ({"a": "é"}, {"é": ["à", "ü"]}, "\u00e9"):
            with self.subTest(donnees=d):
                self.insere(type_entite="client", type_evenement="modification", donnees=d if isinstance(d, (dict, list)) else json.dumps(d))

    def test_INV_110_D17_created_at_avec_octet_NUL_refuse_quelle_que_soit_sa_position(self):
        """GLOB s'arrête au premier NUL : la queue est contrôlée en octets (length(CAST(created_at AS BLOB)) = 24). Témoin : GLOB SEUL accepterait les cas à queue."""
        base = "2026-10-22T10:00:00.000Z"
        for v in (base + NUL, base + NUL + "junk", base + NUL * 3):
            with self.subTest(created_at=repr(v)):
                self.assertEqual(self.un("SELECT ? GLOB " + GLOB_CREATED_AT, v)[0], 1)                      # GLOB seul l'accepterait
                self.rejette(type_entite="bc", type_evenement="creation", created_at=v)
        for v in (base[:10] + NUL + base[10:], NUL + base, base[:-1] + NUL, base[:12] + NUL + base[12:], NUL):
            with self.subTest(created_at=repr(v)):
                self.rejette(type_entite="bc", type_evenement="creation", created_at=v)

    def test_INV_110_D18_created_at_de_24_octets_conforme_reste_accepte(self):
        r = self.ajoute(type_entite="bc", type_evenement="creation", created_at="2026-10-22T10:00:00.000Z")
        self.assertEqual(self.un("SELECT length(CAST(created_at AS BLOB)) FROM historique WHERE id=?", r)[0], 24)


    def test_INV_110_D19_created_at_chaque_position_du_format_est_controlee(self):
        """Le format AAAA-MM-JJTHH:MM:SS.mmmZ est contrôlé à CHACUNE des 24 positions (17 chiffres, 7 séparateurs) : une valeur conforme dont UN caractère est remplacé
        est refusée. Un GLOB qui remplacerait une position par `?` accepterait ces valeurs. Un chiffre est remplacé par une lettre ; un séparateur par une lettre et par
        un chiffre. Témoin : la valeur de départ est acceptée."""
        base = "2026-10-22T10:00:00.000Z"
        self.assertEqual(len(base), 24)
        self.assertEqual(sum(c.isdigit() for c in base), 17)
        self.insere(type_entite="bc", type_evenement="creation", created_at=base)
        for i, attendu in enumerate(base):
            for remplacant in (("x",) if attendu.isdigit() else ("x", "0")):
                with self.subTest(position=i + 1, attendu=attendu, remplace_par=remplacant):
                    self.rejette(type_entite="bc", type_evenement="creation", created_at=base[:i] + remplacant + base[i + 1:])


# --------------------------------------------------------------------------------------------------------------------
# E — événements `acceptation` (structure locale de la ligne ; INV-110)
# --------------------------------------------------------------------------------------------------------------------
class Acceptation(Base16):
    def ok(self, donnees, **kw):
        self.insere(**self.acceptation(donnees, **kw))

    def ko(self, donnees, **kw):
        self.rejette(**self.acceptation(donnees, **kw))

    # --- cas valides, tous avec bc_id ---------------------------------------------------------------------------------------------
    def test_INV_110_E1_acceptation_initiale_version_initiale_revision_null_avec_bc_id(self):
        self.ok(initiale())

    def test_INV_110_E2_acceptation_initiale_d_une_version_revisee_revision_entiere_avec_bc_id(self):
        for rev in (1, 2, 17, 2147483647):
            with self.subTest(revision=rev):
                self.ok(initiale(revision=rev))

    def test_INV_110_E3_reacceptation_complete_avec_bc_id(self):
        self.ok(reacceptation())
        self.ok(reacceptation(revision=1, precedente={"revision": 3, "date_acceptation": "2026-10-30"}))
        self.ok(reacceptation(precedente={"revision": None, "date_acceptation": "2026-10-22"}))

    def test_INV_110_E4_acteur_et_valeurs_par_defaut_de_la_table_s_appliquent_a_l_acceptation(self):
        r = self.ajoute(**self.acceptation(initiale()))
        self.assertEqual(self.un("SELECT acteur, type_entite FROM historique WHERE id=?", r), ("utilisateur", "devis"))
        for a in ACTEURS:
            with self.subTest(acteur=a):
                self.ok(initiale(), acteur=a)

    def test_INV_110_E5_une_precedente_valide_est_toleree_sur_une_acceptation_initiale(self):
        """CONSTAT : le CHECK valide `precedente` dès qu'elle est présente, quelle que soit la nature ; il ne l'exige que pour une réacceptation."""
        self.ok(initiale(precedente={"revision": None, "date_acceptation": "2026-09-01"}))

    # --- bc_id obligatoire pour les deux natures (décision du 2026-10-22) -----------------------------------------------------------
    def test_INV_110_E6_acceptation_initiale_sans_bc_id_refusee(self):
        self.ko(initiale(), bc_id=None)

    def test_INV_110_E7_reacceptation_sans_bc_id_refusee(self):
        self.ko(reacceptation(), bc_id=None)

    def test_INV_110_E8_bc_id_non_NULL_ne_suffit_pas_pour_les_autres_gardes(self):
        self.ko(None)                                                                                # donnees NULL
        self.ko(initiale(), type_entite="bc")
        self.ko(initiale(nature=ABS))

    def test_INV_110_E9_le_bc_id_NULL_reste_permis_pour_les_evenements_autres_que_acceptation_meme_sur_un_devis(self):
        for ev in ("refus", "creation", "modification", "annulation"):
            with self.subTest(type_evenement=ev):
                self.insere(type_entite="devis", entite_id=self.un_devis(), type_evenement=ev, bc_id=None)

    # --- type_entite, entite_id, donnees --------------------------------------------------------------------------------------------
    def test_INV_110_E10_type_entite_autre_que_devis_refuse(self):
        for te in ("bc", "facture", "client", "import", "restauration", "document"):
            with self.subTest(type_entite=te):
                self.ko(initiale(), type_entite=te)

    def test_INV_110_E11_entite_id_NULL_refuse(self):
        self.ko(initiale(), entite_id=None)
        self.ko(reacceptation(), entite_id=None)

    def test_INV_110_E12_donnees_absentes_ou_qui_ne_sont_pas_un_objet_refusees(self):
        for d in (None, [], [1], "[1]", "5", '"x"', "null", "true", "abc", "{"):
            with self.subTest(donnees=d):
                self.ko(d)

    # --- date_acceptation -----------------------------------------------------------------------------------------------------------
    def test_INV_110_E13_date_acceptation_absente_ou_de_mauvais_type_refusee(self):
        for v in (ABS, None, 20261022, 2026.1022, True, ["2026-10-22"], {"d": "2026-10-22"}):
            with self.subTest(date=v):
                self.ko(initiale(date_acceptation=v))

    def test_INV_110_E14_date_acceptation_mal_formee_refusee(self):
        for v in ("", "22/10/2026", "2026-10-22T00:00:00", "2026-10-22 ", " 2026-10-22", "2026-1-2", "26-10-22", "2026/10/22", "20261022", "abcd-ef-gh"):
            with self.subTest(date=v):
                self.ko(initiale(date_acceptation=v))

    def test_INV_110_E15_date_acceptation_impossible_refusee(self):
        for v in ("2026-02-30", "2026-13-01", "2026-00-10", "2026-10-32", "2026-04-31", "2027-02-29", "0000-00-00", "2026-10-00"):
            with self.subTest(date=v):
                self.ko(initiale(date_acceptation=v))
        self.ok(initiale(date_acceptation="2028-02-29"))                                             # année bissextile : valide

    # --- revision ---------------------------------------------------------------------------------------------------------------------
    def test_INV_110_E16_revision_absente_ou_invalide_refusee(self):
        for v in (ABS, 0, -1, -17, "2", "1", 1.5, 2.0 + 0.5, True, False, [1], {"n": 1}, ""):
            with self.subTest(revision=v):
                self.ko(initiale(revision=v))

    # --- nature -----------------------------------------------------------------------------------------------------------------------
    def test_INV_110_E17_nature_absente_inconnue_ou_de_mauvais_type_refusee(self):
        for v in (ABS, None, "autre", "Initiale", "REACCEPTATION", "initiale ", "", 1, True, ["initiale"]):
            with self.subTest(nature=v):
                self.ko(initiale(nature=v))

    # --- réacceptation ----------------------------------------------------------------------------------------------------------------
    def test_INV_110_E18_reacceptation_sans_revision_ou_avec_revision_null_ou_non_entiere_refusee(self):
        for v in (ABS, None, "2", 1.5, 0, -2):
            with self.subTest(revision=v):
                self.ko(reacceptation(revision=v))

    def test_INV_110_E19_reacceptation_sans_precedente_ou_avec_precedente_non_objet_refusee(self):
        for v in (ABS, None, "x", [], [{"revision": None, "date_acceptation": "2026-10-22"}], 5, True):
            with self.subTest(precedente=v):
                self.ko(reacceptation(precedente=v))

    def test_INV_110_E20_precedente_mal_formee_refusee_quelle_que_soit_la_nature(self):
        mauvaises = [
            {"revision": None},                                                                      # date absente
            {"revision": None, "date_acceptation": None},
            {"revision": None, "date_acceptation": 20261022},
            {"revision": None, "date_acceptation": "22/10/2026"},
            {"revision": None, "date_acceptation": "2026-02-30"},
            {"date_acceptation": "2026-10-22"},                                                      # revision absente
            {"revision": "1", "date_acceptation": "2026-10-22"},
            {"revision": 1.5, "date_acceptation": "2026-10-22"},
            {"revision": True, "date_acceptation": "2026-10-22"},
        ]
        for p in mauvaises:
            with self.subTest(precedente=p):
                self.ko(reacceptation(precedente=p))
                self.ko(initiale(precedente=p))

    def test_INV_110_E21_precedente_revision_null_ou_entiere_acceptee_y_compris_zero_ou_negative(self):
        """CONSTAT : le CHECK ne contraint que le TYPE de `precedente.revision` (null ou entier), pas sa valeur ; la règle `revision >= 1` ne porte que sur la version acceptée."""
        self.ok(reacceptation(precedente={"revision": 0, "date_acceptation": "2026-10-22"}))
        self.ok(reacceptation(precedente={"revision": -4, "date_acceptation": "2026-10-22"}))

    # --- ce que le CHECK ne vérifie pas (témoins) ------------------------------------------------------------------------------------
    def test_INV_175_E22_temoin_le_CHECK_ne_lit_aucune_autre_table(self):
        """CONSTAT : un devis inexistant, ou rattaché à un autre BC, est accepté par le schéma ; la concordance de `bc_id` avec `bc_devis` est garantie par le service
        dans la transaction d'acceptation ou de réacceptation, jamais par le CHECK ni par un trigger (INV-175, conventions §9)."""
        self.ok(initiale(), entite_id=987654321)
        autre = self.monde(devis=[{"lignes": ["100.00"]}])
        self.assertNotEqual(autre.b, self.un_bc())
        self.ok(initiale(), entite_id=self.un_devis(), bc_id=autre.b)                              # bc_id d'un autre BC que celui du devis : accepté par le schéma

    def test_INV_175_E23_le_texte_de_la_table_ne_reference_aucune_autre_table_hors_la_cle_etrangere(self):
        sql = T.sans_commentaires(T.sql_de(self.db, TABLE))
        self.assertNotRegex(sql, r"(?i)\bSELECT\b")
        self.assertIsNone(re.search(r"\b(bc_devis|devis_lignes|bc_lignes|factures|reglements)\b", sql))
        self.assertEqual(re.findall(r"REFERENCES\s+(\w+)", sql), ["bons_commande"])
        self.assertEqual(self.tous("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='historique' AND sql LIKE '%bc_devis%'"), [])

    def test_INV_110_E24_les_autres_types_d_evenement_ne_sont_soumis_a_aucune_structure_particuliere(self):
        for ev in TYPES_EVENEMENT:
            if ev == "acceptation":
                continue
            with self.subTest(type_evenement=ev):
                self.insere(type_entite="devis", entite_id=1, bc_id=None, type_evenement=ev, donnees={"date_acceptation": "pas une date"})


    def test_INV_110_E25_octet_NUL_brut_apres_la_charge_utile_d_une_acceptation_refuse(self):
        for suite in (NUL, NUL + "junk", NUL + "{"):
            with self.subTest(suite=repr(suite)):
                donnees = json.dumps(initiale()) + suite
                self.assertEqual(self.un("SELECT json_valid(?)", donnees)[0], 1)                             # json_valid seul l'accepterait
                self.ko(donnees)
                self.ko(json.dumps(reacceptation()) + suite)

    def test_INV_110_E26_echappement_u0000_dans_un_champ_de_l_acceptation_refuse(self):
        """json.dumps sérialise le caractère NUL en échappement `\\u0000` ; json_extract le restitue en chaîne portant un NUL, que date() et IN refusent."""
        self.ko(initiale(date_acceptation="2026-10-22" + NUL))
        self.ko(initiale(date_acceptation="2026-10-22" + NUL + "zz"))
        self.ko(initiale(nature="initiale" + NUL))
        self.ko(reacceptation(nature="reacceptation" + NUL))
        self.ko(reacceptation(precedente={"revision": None, "date_acceptation": "2026-10-22" + NUL}))
        self.ko(reacceptation(precedente={"revision": None, "date_acceptation": "2026-10-22" + NUL + "zz"}))


# --------------------------------------------------------------------------------------------------------------------
# F — append-only (TR-60, INV-110) ; dépendance à recursive_triggers=ON (INV-07, conventions §9)
# --------------------------------------------------------------------------------------------------------------------
class AppendOnly(Base16):
    def setUp(self):
        super().setUp()
        b = self.un_bc()
        self.r1 = self.ajoute(type_entite="bc", entite_id=b, bc_id=b, type_evenement="creation", donnees={"v": 1})
        self.r2 = self.ajoute(type_entite="bc", entite_id=b, bc_id=b, type_evenement="modification", donnees={"v": 2})
        self.avant = self.lignes()

    def intact(self):
        self.assertEqual(self.lignes(), self.avant)

    def test_INV_07_F1_la_connexion_de_test_pose_recursive_triggers_ON_et_le_relit(self):
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(migrer16().execute("PRAGMA recursive_triggers").fetchone()[0], 1)           # réglage par défaut du fabricant de base de test
        self.assertEqual(migrer16(recursive=False).execute("PRAGMA recursive_triggers").fetchone()[0], 0)

    def test_INV_110_F2_update_refuse_valeur_modifiee(self):
        self.refuse_inv(RE_INV110, "UPDATE historique SET donnees=? WHERE id=?", ('{"v": 9}', self.r1))
        self.intact()

    def test_INV_110_F3_update_refuse_chaque_colonne(self):
        for col, val in (("type_entite", "client"), ("entite_id", 5), ("bc_id", None), ("type_evenement", "refus"), ("acteur", "systeme"),
                         ("donnees", None), ("created_at", "2026-01-01T00:00:00.000Z"), ("id", 99)):
            with self.subTest(colonne=col):
                self.refuse_inv(RE_INV110, f"UPDATE historique SET {col}=? WHERE id=?", (val, self.r1))
        self.intact()

    def test_INV_110_F4_update_refuse_meme_sans_changement_de_valeur(self):
        self.refuse_inv(RE_INV110, "UPDATE historique SET id=id WHERE id=?", (self.r1,))
        self.refuse_inv(RE_INV110, "UPDATE historique SET type_evenement=type_evenement")
        self.intact()

    def test_INV_110_F5_update_or_replace_vers_un_id_existant_refuse(self):
        self.refuse_inv(RE_INV110, "UPDATE OR REPLACE historique SET id=? WHERE id=?", (self.r2, self.r1))
        self.intact()

    def test_INV_110_F6_upsert_do_update_refuse(self):
        self.refuse_inv(RE_INV110, "INSERT INTO historique (id, type_entite, type_evenement) VALUES (?, 'bc', 'refus') "
                                   "ON CONFLICT(id) DO UPDATE SET type_evenement='refus'", (self.r1,))
        self.intact()

    def test_INV_110_F7_temoin_upsert_do_nothing_n_a_aucun_effet(self):
        c = self.db.execute("INSERT INTO historique (id, type_entite, type_evenement) VALUES (?, 'bc', 'refus') ON CONFLICT(id) DO NOTHING", (self.r1,))
        self.assertEqual(c.rowcount, 0)
        self.intact()

    def test_INV_110_F8_delete_avec_where_refuse(self):
        self.refuse_inv(RE_INV110, "DELETE FROM historique WHERE id=?", (self.r1,))
        self.refuse_inv(RE_INV110, "DELETE FROM historique WHERE type_evenement='creation'")
        self.intact()

    def test_INV_110_F9_delete_sans_where_refuse(self):
        self.refuse_inv(RE_INV110, "DELETE FROM historique")
        self.intact()

    def test_INV_110_F10_insert_or_replace_sur_un_id_existant_refuse_avec_recursive_triggers_ON(self):
        self.refuse_inv(RE_INV110, "INSERT OR REPLACE INTO historique (id, type_entite, type_evenement, donnees) VALUES (?, 'bc', 'refus', '{\"v\": 7}')", (self.r1,))
        self.refuse_inv(RE_INV110, "REPLACE INTO historique (id, type_entite, type_evenement) VALUES (?, 'bc', 'refus')", (self.r2,))
        self.intact()

    def test_INV_110_F11_replace_avec_un_nouvel_id_est_une_insertion_les_lignes_existantes_restent_intactes(self):
        """SQL permet cette insertion (REPLACE reste interdit par convention, INV-07) : aucune ligne existante n'est supprimée."""
        self.db.execute("INSERT OR REPLACE INTO historique (id, type_entite, type_evenement) VALUES (500, 'bc', 'refus')")
        self.db.execute("REPLACE INTO historique (type_entite, type_evenement) VALUES ('bc', 'refus')")
        self.assertEqual(self.lignes()[:len(self.avant)], self.avant)
        self.assertEqual(len(self.lignes()), len(self.avant) + 2)

    def test_INV_110_F12_insert_or_ignore_sur_un_id_existant_sans_effet(self):
        c = self.db.execute("INSERT OR IGNORE INTO historique (id, type_entite, type_evenement) VALUES (?, 'bc', 'refus')", (self.r1,))
        self.assertEqual(c.rowcount, 0)
        self.intact()

    def test_INV_110_F13_aucun_index_unique_hors_cle_primaire_donc_aucune_cle_de_conflit_autre_que_id(self):
        """Une clé UNIQUE supplémentaire ferait qu'un REPLACE avec un nouvel id supprimerait la ligne en conflit : elle est exclue de la table."""
        self.assertEqual([r for r in self.tous("PRAGMA index_list(historique)") if r[2]], [])
        self.assertNotRegex(T.sans_commentaires(T.sql_de(self.db, TABLE)), r"(?i)\bUNIQUE\b")

    def test_INV_110_F14_les_messages_de_refus_sont_ceux_des_deux_triggers(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, r"INV-110: un evenement d'historique ne se modifie jamais"):
            self.db.execute("UPDATE historique SET donnees=NULL WHERE id=?", (self.r1,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, r"INV-110: un evenement d'historique ne se supprime jamais"):
            self.db.execute("DELETE FROM historique WHERE id=?", (self.r1,))

    def test_INV_07_F15_temoin_recursive_triggers_OFF_REPLACE_ecrase_la_ligne_sans_declencher_le_trigger(self):
        """CONSTAT sur le moteur de test, PAS une protection : avec `recursive_triggers=OFF`, un INSERT OR REPLACE sur un id existant supprime la ligne sans déclencher
        `tr_60_historique_no_delete`. Hors configuration conforme (conventions §9), la protection n'est pas absolue ; aucun trigger supplémentaire n'est prévu.
        UPDATE, DELETE et UPSERT DO UPDATE restent refusés quel que soit le réglage."""
        db = migrer16(recursive=False)
        self.assertEqual(db.execute("PRAGMA recursive_triggers").fetchone()[0], 0)
        db.execute("INSERT INTO historique (id, type_entite, type_evenement, donnees) VALUES (1, 'client', 'creation', '{\"v\": 1}')")
        for sql in ("UPDATE historique SET donnees=NULL WHERE id=1", "DELETE FROM historique WHERE id=1", "DELETE FROM historique",
                    "INSERT INTO historique (id, type_entite, type_evenement) VALUES (1, 'bc', 'refus') ON CONFLICT(id) DO UPDATE SET type_evenement='refus'"):
            with self.subTest(sql=sql):
                with self.assertRaisesRegex(sqlite3.IntegrityError, RE_INV110):
                    db.execute(sql)
        self.assertEqual(db.execute("SELECT type_evenement, donnees FROM historique WHERE id=1").fetchall(), [("creation", '{"v": 1}')])
        db.execute("INSERT OR REPLACE INTO historique (id, type_entite, type_evenement, donnees) VALUES (1, 'bc', 'refus', '{\"v\": 7}')")     # accepté : constat
        self.assertEqual(db.execute("SELECT type_entite, type_evenement, donnees FROM historique WHERE id=1").fetchall(), [("bc", "refus", '{"v": 7}')])


    def test_INV_110_F16_un_refus_TR60_annule_l_instruction_fautive_mais_preserve_la_transaction(self):
        """RAISE(ABORT) n'annule que l'instruction refusée : l'événement écrit plus tôt dans la MÊME transaction (le service écrit l'événement avec l'opération qu'il
        décrit) reste en place, la transaction reste ouverte et peut être validée. RAISE(ROLLBACK) annulerait toute la transaction."""
        b = self.un_bc()
        refus = (("UPDATE historique SET donnees = '{\"v\": 9}' WHERE id = ?", "ne se modifie jamais"),
                 ("DELETE FROM historique WHERE id = ?", "ne se supprime jamais"))
        for sql, message in refus:
            with self.subTest(refus=sql):
                self.db.execute("BEGIN")
                try:
                    i = self.ajoute(type_entite="bc", entite_id=b, bc_id=b, type_evenement="modification", donnees={"v": 3})
                    apres_insertion = self.lignes()
                    self.assertEqual(len(apres_insertion), len(self.avant) + 1)
                    with self.assertRaisesRegex(sqlite3.IntegrityError, message):
                        self.db.execute(sql, (i,))
                    self.assertTrue(self.db.in_transaction)                                                 # la transaction n'a pas été annulée
                    self.assertEqual(self.lignes(), apres_insertion)                                        # instruction annulée, écriture antérieure intacte
                    self.db.execute("COMMIT")
                except BaseException:
                    if self.db.in_transaction:
                        self.db.execute("ROLLBACK")
                    raise
                self.assertEqual(self.lignes(), apres_insertion)                                            # l'écriture antérieure est bien validée
                self.avant = self.lignes()


# --------------------------------------------------------------------------------------------------------------------
# G — immuabilité des migrations antérieures
# --------------------------------------------------------------------------------------------------------------------
class Immuabilite(unittest.TestCase):
    def test_010_G_les_quinze_migrations_anterieures_sont_inchangees(self):
        self.assertEqual(len(EMPREINTES_ANTERIEURES), 15)
        for nom, empreinte in EMPREINTES_ANTERIEURES.items():
            with self.subTest(migration=nom):
                contenu = (MIGRATIONS / nom).read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(hashlib.sha256(contenu).hexdigest(), empreinte)
        self.assertEqual(list(EMPREINTES_ANTERIEURES), list(C.NOMS))                                # exactement les quinze migrations de la chaîne livrée

    def test_010_G_la_migration_010_ne_figure_pas_dans_les_empreintes_anterieures(self):
        self.assertNotIn(NOM_010, EMPREINTES_ANTERIEURES)


# --------------------------------------------------------------------------------------------------------------------
# H — non-régression de la chaîne
# --------------------------------------------------------------------------------------------------------------------
class NonRegression(Base16):
    def test_010_H_le_trigger_tr_103_de_009c_est_identique_et_effectif_au_rang_16(self):
        defs = [_norm(r[0]) for r in self.tous("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (C.TRIGGER,))]
        self.assertEqual(defs, [C.trigger_009c()])
        bc, _ = self.avec("acompte")
        self.refuse(bc.b, C.M_ACOMPTE)

    def test_010_H_la_chaine_complete_est_saine_au_rang_16_avec_des_evenements(self):
        b = self.un_bc()
        self.insere(type_entite="bc", entite_id=b, bc_id=b, type_evenement="passage_termine")
        self.insere(**self.acceptation(initiale()))
        self.assertEqual(T.db_user_version(self.db), 16)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_010_H_une_base_au_rang_16_peuplee_par_la_chaine_conserve_ses_donnees_metier(self):
        bc, f = self.avec("acompte")
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "en_cours")
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", bc.b)[0], 1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM historique")[0], 0)                          # la chaîne ne crée aucun événement : le service les écrit


# --------------------------------------------------------------------------------------------------------------------
# M — conformité au modèle de données V3.14 (§2.5, §4.14)
# --------------------------------------------------------------------------------------------------------------------
class Modele(unittest.TestCase):
    def test_010_M_les_enumerations_du_test_sont_celles_du_modele_2_5(self):
        self.assertEqual(liste_modele("historique.type_entite"), TYPES_ENTITE)
        self.assertEqual(liste_modele("historique.type_evenement"), TYPES_EVENEMENT)
        self.assertEqual(liste_modele("historique.acteur"), ACTEURS)

    def test_010_M_les_enumerations_de_la_migration_sont_celles_du_modele(self):
        code = T.sans_commentaires(SQL_010)
        for colonne, valeurs in (("type_entite", TYPES_ENTITE), ("type_evenement", TYPES_EVENEMENT), ("acteur", ACTEURS)):
            m = re.search(r"CHECK\s*\(\s*" + colonne + r"\s+IN\s*\(([^)]*)\)\s*\)", code)
            self.assertIsNotNone(m, colonne)
            self.assertEqual(tuple(re.findall(r"'([^']*)'", m.group(1))), valeurs, colonne)

    def test_010_M_le_CHECK_des_evenements_acceptation_est_identique_a_l_expression_de_reference_du_modele(self):
        bloc = re.search(r"### 4\.14 Historique.*?```sql\n(.*?)```", modele(), re.S)
        self.assertIsNotNone(bloc)
        reference = _norm(bloc.group(1))
        self.assertTrue(reference.startswith("CHECK (type_evenement <> 'acceptation' OR ("), reference[:80])
        self.assertIn("type_entite = 'devis' AND entite_id IS NOT NULL AND bc_id IS NOT NULL", reference)    # bc_id non NULL pour les deux natures
        self.assertIn(reference, _norm(T.sans_commentaires(SQL_010)))

    def test_010_M_les_index_et_triggers_de_la_migration_figurent_dans_le_modele_4_14(self):
        section = re.search(r"### 4\.14 Historique.*?### 4\.15", modele(), re.S).group(0)
        for nom in list(INDEXES) + list(TRIGGERS):
            with self.subTest(objet=nom):
                self.assertIn(nom, section)
        self.assertIn("recursive_triggers=ON", section)

    def test_010_M_le_modele_documente_la_decision_bc_id_non_NULL_et_le_numero_de_test(self):
        m = modele()
        self.assertIsNotNone(re.search(r"^\| T-55 \| `test_010_historique\.py`", m, re.M))
        self.assertIsNotNone(re.search(r"^\| D-64 \| \*\*Tranche `historique`\*\*", m, re.M))
        self.assertIn("jamais NULL pour un événement `acceptation`", m)


if __name__ == "__main__":
    unittest.main(verbosity=1)
