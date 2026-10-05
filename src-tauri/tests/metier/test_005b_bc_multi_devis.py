"""T-46 — Migration corrective 005b_bc_multi_devis (M-B, rang 7) ; modèle V3.13 §4.7, §4.19, §8 (TR-12, TR-13, TR-17, TR-18, TR-99), §14 (CK-13, CK-14),
§17.1 ; conventions techniques §5 (chaîne ordonnée, transaction et user_version, protocole de reconstruction de table, données dans une migration) ;
CADRAGE__005b_bc_multi_devis.md (arbitrages Q-A à Q-D du 2026-10-05).
005b permet « BC 1 <- N devis » : table bc_devis (lien devis <-> BC, jamais modifié), reconstruction de bons_commande (sans devis_id, remise_*, acompte_*),
reconstruction de bc_ligne_garanties (RESTRICT), contenu contractuel du BC immuable dès sa création, lignes et garanties de lignes immuables, rattachement d'un
devis tant que le BC n'est pas annulé. La condition « aucun solde rédigé/validé » (INV-187) est une règle de SERVICE contrôlée par CK-14 : aucun test ne la
suppose garantie par le schéma ; des tests INTERPRETATION verrouillent au contraire que le schéma ne la porte pas.
Les migrations 001 à 005 sont appliquées comme le fait le runner (D-55) ; 005a et 005b le sont par `runner()` qui reproduit le protocole de reconstruction :
foreign_keys=OFF hors transaction, BEGIN IMMEDIATE, fichier, PRAGMA foreign_key_check (vide), PRAGMA integrity_check (ok), PRAGMA user_version = rang dans
la transaction, COMMIT, puis foreign_keys=ON.

Exécution : python3 src-tauri/tests/metier/test_005b_bc_multi_devis.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T46_. Les décisions d'interprétation portent « INTERPRETATION ».
Ces tests ne dépendent d'aucune interface graphique ni d'aucun service : ils ne vérifient que des faits SQL. Les règles de service (choix du rang, copie des lignes
et garanties, calcul du contractuel, condition de solde) y sont reproduites par des requêtes simples ; elles ne sont pas testées comme des contraintes.
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39).
Les tests de 001–005a décrivent chaque migration prise isolément ; ceux-ci décrivent le schéma de la chaîne complète jusqu'au rang 7.
"""
import pathlib
import re
import sqlite3
import types
import unittest


MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations" / "metier"
NOMS = ("001_initial.sql", "002_fournisseurs.sql", "003_devis.sql", "004_bons_commande.sql", "005_depenses.sql",
        "005a_corrections_v313.sql", "005b_bc_multi_devis.sql")
SQLS = [(MIGRATIONS / n).read_text(encoding="utf-8") for n in NOMS]
CHAINE = tuple(enumerate(SQLS, start=1))
SQL_005B = SQLS[6]

TABLES_RANG5 = {"import_anomalies", "numerotation_sequences", "categories_prestations", "categories_depenses", "clients",
                "prestations", "prestation_garanties", "fournisseurs", "devis", "devis_lignes", "devis_ligne_garanties",
                "bons_commande", "bc_lignes", "bc_ligne_garanties", "depenses"}
TABLES_RANG6 = TABLES_RANG5 | {"devis_revisions"}
TABLES_RANG7 = TABLES_RANG6 | {"bc_devis"}
INDEXES_RANG6 = {"idx_prestations_categorie_id", "idx_prestations_actif", "idx_import_anomalies_categorie_statut",
                 "idx_devis_client_id", "idx_devis_statut", "idx_devis_date_creation", "idx_devis_lignes_prestation_id",
                 "idx_bons_commande_client_id", "idx_bons_commande_statut", "idx_bc_lignes_prestation_id", "idx_depenses_bc_id",
                 "idx_depenses_fournisseur_id", "idx_depenses_categorie_id", "idx_depenses_date_depense", "uq_devis_revisions_initiale"}
INDEXES_RANG7 = INDEXES_RANG6                                                              # aucun index nommé en plus ni en moins
TRIGGERS_BC_RANG6 = {"tr_01_bons_commande_numero_immuable", "tr_12_bons_commande_modifiable", "tr_12_bons_commande_gele",
                     "tr_12_bons_commande_annule", "tr_14_bons_commande_frozen_at", "tr_17_bons_commande_insert",
                     "tr_19_bons_commande_no_delete"}
TRIGGERS_AUTRES_TABLES_RANG6 = {"tr_18_devis_statut_avec_bc", "tr_13_bc_lignes_insert", "tr_13_bc_lignes_update",
                                "tr_13_bc_lignes_delete", "tr_13_bc_ligne_garanties_insert", "tr_13_bc_ligne_garanties_update",
                                "tr_13_bc_ligne_garanties_delete"}
TRIGGERS_SUPPRIMES = {"tr_12_bons_commande_modifiable", "tr_12_bons_commande_gele"}
TRIGGERS_NOUVEAUX = {"tr_12_bons_commande_contrat", "tr_99_bc_devis_insert", "tr_99_bc_devis_no_update", "tr_99_bc_devis_no_delete"}
TRIGGERS_RECREES_IDENTIQUES = {"tr_01_bons_commande_numero_immuable", "tr_14_bons_commande_frozen_at", "tr_19_bons_commande_no_delete"}
TRIGGERS_REECRITS = {"tr_12_bons_commande_annule", "tr_17_bons_commande_insert", "tr_18_devis_statut_avec_bc", "tr_13_bc_lignes_insert",
                     "tr_13_bc_lignes_update", "tr_13_bc_lignes_delete", "tr_13_bc_ligne_garanties_insert",
                     "tr_13_bc_ligne_garanties_update", "tr_13_bc_ligne_garanties_delete"}
TRIGGERS_RANG6 = None                                                                      # calculé sur la base du rang 6 (voir migrer)
COLONNES_BC6 = ["id", "numero", "devis_id", "client_id", "client_snapshot", "client_snapshot_version",
                "entreprise_snapshot", "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version",
                "date_creation", "date_acceptation", "date_debut", "date_fin", "montant_contractuel_ht", "remise_type",
                "remise_valeur", "acompte_type", "acompte_valeur", "montant_deja_facture_ht", "avancement",
                "date_100_facture", "statut", "completed_at", "cancelled_at", "motif_annulation", "frozen_at",
                "created_at", "updated_at", "origine", "legacy_id", "legacy_data", "legacy_numero"]
COLONNES_BC = [c for c in COLONNES_BC6 if c not in ("devis_id", "remise_type", "remise_valeur", "acompte_type", "acompte_valeur")]
COLONNES_BC_DEVIS = ["id", "bc_id", "devis_id", "rang", "created_at"]
COLONNES_DEVIS = ["id", "numero", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                  "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_creation", "date_validite",
                  "date_acceptation", "date_refus", "objet", "notes", "statut", "revision", "revision_en_cours", "remise_type",
                  "remise_valeur", "acompte_type", "acompte_valeur", "total_ht", "frozen_at", "cancelled_at", "motif_refus",
                  "motif_annulation", "created_at", "updated_at", "origine", "legacy_id", "legacy_data"]
COLONNES_BC_LIGNES = ["id", "bc_id", "devis_ligne_id", "ordre", "prestation_id", "reference_prestation", "designation", "description",
                      "quantite", "unite", "prix_unitaire_ht", "remise_type", "remise_valeur", "type_prestation", "total_ht",
                      "created_at", "updated_at"]
# colonnes de bons_commande immuables pour un BC non annulé (contenu contractuel, Q4) / modifiables
IMMUABLES_BC = ["id", "numero", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_creation", "date_acceptation",
                "created_at", "origine", "legacy_id", "legacy_data", "legacy_numero"]
MODIFIABLES_BC = [c for c in COLONNES_BC if c not in IMMUABLES_BC]
COLONNES_ANNULE_MODIFIABLES = {"updated_at"}
ETATS_BC = ("en_cours", "gele", "termine", "annule", "annule_gele")
ETATS_BC_NON_ANNULES = ("en_cours", "gele", "termine")
ETATS_BC_ANNULES = ("annule", "annule_gele")

TS = "2026-10-01T10:00:00.000Z"
TS2 = "2026-10-02T11:30:15.123Z"
TS_ANNUL = "2099-01-01T00:00:00.000Z"                                                        # annulation toujours postérieure aux created_at par défaut (horloge réelle)
SNAP = '{"nom": "Dupont"}'
ATTRIBUER = ("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 1) "
             "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, "
             "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') RETURNING dernier_numero")


# --------------------------------------------------------------------------------------------------------------------
# Exécution des migrations
# --------------------------------------------------------------------------------------------------------------------
def sans_commentaires(sql):
    return re.sub(r"--[^\n]*", "", sql)


def instructions(sql):
    """Découpe un fichier de migration en instructions complètes (les triggers contiennent des « ; »)."""
    tampon = ""
    for ligne in sql.splitlines(keepends=True):
        tampon += ligne
        if sqlite3.complete_statement(tampon):
            if sans_commentaires(tampon).strip():
                yield tampon
            tampon = ""
    if sans_commentaires(tampon).strip():
        raise AssertionError("instruction incomplète en fin de fichier : " + tampon)


class ErreurRunner(Exception):
    pass


def appliquer(db, rang, sql):
    """Une migration 001–005 comme le runner (D-55) : BEGIN IMMEDIATE, SQL du fichier, user_version = rang, COMMIT."""
    db.executescript(f"BEGIN IMMEDIATE;\n{sql}\nPRAGMA user_version = {rang};\nCOMMIT;")


def runner(db, rang=6, sql=None, verifier=True):
    """Protocole de reconstruction (conventions §5) : foreign_keys=OFF hors transaction (relu), BEGIN IMMEDIATE, instructions du fichier,
    foreign_key_check (vide), integrity_check (ok), user_version = rang dans la transaction, COMMIT ; ROLLBACK intégral sur toute erreur ;
    puis foreign_keys=ON (relu)."""
    sql = SQLS[rang - 1] if sql is None else sql
    db.execute("PRAGMA foreign_keys=OFF")
    if db.execute("PRAGMA foreign_keys").fetchone()[0] != 0:
        raise ErreurRunner("foreign_keys n'a pas pu être désactivé")
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            for st in instructions(sql):
                db.execute(st)
            if verifier:
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ErreurRunner("foreign_key_check non vide")
                if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ErreurRunner("integrity_check")
            db.execute(f"PRAGMA user_version = {rang}")
            db.execute("COMMIT")
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
    finally:
        db.execute("PRAGMA foreign_keys=ON")
        if db.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise ErreurRunner("foreign_keys n'a pas pu être réactivé")


def migrer(jusqu_a=7, recursive=True):
    """Applique 001 à 005, puis 005a et 005b (ou jusqu'au rang `jusqu_a`). La connexion applique les réglages obligatoires (D-39) :
    foreign_keys=ON et recursive_triggers=ON."""
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA recursive_triggers=" + ("ON" if recursive else "OFF"))
    for rang, sql in CHAINE:
        if rang <= jusqu_a:
            if rang >= 6:
                runner(db, rang)
            else:
                appliquer(db, rang, sql)
    return db



def objets(db, hors_tables=()):
    """Objets du schéma (type, nom, table, sql), sans les tables internes de SQLite."""
    return sorted(r for r in db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")
                  if r[2] not in hors_tables)


def sql_de(db, nom):
    return db.execute("SELECT sql FROM sqlite_master WHERE name=?", (nom,)).fetchone()[0]


def noms(db, type_):
    return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type=? AND name NOT LIKE 'sqlite_%'", (type_,))}


def tout(db):
    """Contenu de toutes les tables, y compris sqlite_sequence."""
    r = {t: db.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall() for t in sorted(noms(db, "table"))}
    r["sqlite_sequence"] = sorted(db.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
    return r


def colonnes(db, table):
    return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]


def peupler_rang5(db):
    """Base au rang 5 : toutes les tables ont des lignes, des trous d'identifiants (séquences AUTOINCREMENT en avance sur le max),
    tous les statuts de devis, un BC gelé avec lignes et garanties, des dépenses."""
    x = db.execute
    x("INSERT INTO clients (code, nom, prenom, adresse, cpville, tel, email, notes, statut) "
      "VALUES ('CLI-0001', 'Dupont', 'Jean', '1 rue A', '75001 Paris', '0102030405', 'a@b.fr', 'note', 'actif')")
    x("INSERT INTO clients (code, nom, statut, created_at, updated_at) VALUES ('CLI-0002', 'Martin', 'archive', "
      "'2026-01-01T08:00:00.000Z', '2026-02-02T09:30:00.000Z')")
    x("INSERT INTO clients (code, nom, statut, origine, legacy_id, legacy_data, legacy_numero) "
      "VALUES ('CLI-0003', 'Durand', 'a_rattacher', 'import', 'L-3', '{\"k\": 3}', 'C-3')")
    x("INSERT INTO clients (code, nom, statut) VALUES ('CLI-0004', 'Temp', 'actif')")
    x("DELETE FROM clients WHERE code='CLI-0004'")                                             # séquence clients = 4, max(id) = 3
    x("INSERT INTO fournisseurs (code, nom, adresse, cpville, tel, email, notes, statut) "
      "VALUES ('FOU-0001', 'Quincaillerie', '2 rue B', '69001 Lyon', '0405060708', 'f@g.fr', 'nf', 'actif')")
    x("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0002', 'Ancien', 'archive')")
    x("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0003', 'Temp', 'actif')")
    x("DELETE FROM fournisseurs WHERE code='FOU-0003'")                                        # séquence fournisseurs = 3, max(id) = 2
    x("INSERT INTO categories_prestations (code, libelle, actif, ordre) VALUES ('PLO', 'Plomberie', 1, 1)")
    x("INSERT INTO prestations (reference, designation, categorie_id, unite, type_prestation, prix_unitaire_ht, actif) "
      "VALUES ('PLO-001', 'Pose', 1, 'u', 'pose', '10', 1)")
    x("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (1, 'decennale')")
    x("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'Matériaux', 1, 1)")
    x("INSERT INTO import_anomalies (type_entite, entite_id, ref_source, categorie, motif) VALUES ('client', 3, 'L-3', 'a_verifier', 'à rattacher')")

    def devis(num, client, statut, **kw):
        cols = {"numero": f"DEV-{num:05d}-26", "client_id": client, "client_snapshot": SNAP, "client_snapshot_version": 1,
                "entreprise_snapshot": '{"entreprise": "E"}', "entreprise_snapshot_version": 2, "chantier_snapshot": '{"chantier": "C"}',
                "chantier_snapshot_version": 3, "date_creation": "2026-03-10", "statut": statut, "total_ht": "31.50",
                "objet": f"Objet {num}", "notes": f"Notes {num}"}
        cols.update(kw)
        x(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
    devis(1, 1, "en_attente", date_validite="2026-04-10", remise_type="pourcentage", remise_valeur="10.00",
          acompte_type="montant", acompte_valeur="5.00")
    x("INSERT INTO devis_lignes (devis_id, ordre, prestation_id, reference_prestation, designation, quantite, unite, "
      "prix_unitaire_ht, remise_type, type_prestation, total_ht) VALUES (1, 1, 1, 'PLO-001', 'Pose prise', '2', 'u', '10.5', 'aucune', 'pose', '21.00')")
    x("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, type_prestation, total_ht) "
      "VALUES (1, 2, 'Ligne libre', '1', 'u', '10.5', 'aucune', 'pose', '10.50')")
    x("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (1, 'decennale'), (1, 'biennale')")
    x("UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=1")
    devis(2, 2, "en_attente", total_ht="0.00", created_at="2026-03-10T08:15:00.000Z", updated_at="2026-03-11T17:45:30.500Z")
    devis(3, 1, "refuse", date_refus="2026-03-20", motif_refus="Trop cher")
    devis(4, 3, "annule", cancelled_at=TS, motif_annulation="Annulé", origine="import", legacy_id="LD-4", legacy_data='{"k": 4}')
    devis(5, 1, "en_attente")
    x("DELETE FROM devis WHERE numero='DEV-00005-26'")                                         # séquence devis = 5, max(id) = 4
    bcn = x(ATTRIBUER, ("BCD", 26)).fetchone()[0]
    x("INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
      "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
      "montant_contractuel_ht, remise_type, remise_valeur, acompte_type, acompte_valeur) "
      "SELECT ?, id, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
      "chantier_snapshot, chantier_snapshot_version, '2026-10-02', date_acceptation, total_ht, remise_type, remise_valeur, "
      "acompte_type, acompte_valeur FROM devis WHERE id=1", (f"BCD-{bcn:05d}-26",))
    x("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, prestation_id, reference_prestation, designation, description, quantite, "
      "unite, prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht) SELECT 1, id, ordre, prestation_id, "
      "reference_prestation, designation, description, quantite, unite, prix_unitaire_ht, remise_type, remise_valeur, "
      "type_prestation, total_ht FROM devis_lignes WHERE devis_id=1 ORDER BY ordre")
    x("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) SELECT bl.id, dg.garantie_type FROM bc_lignes bl "
      "JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id")
    x("UPDATE bons_commande SET frozen_at=? WHERE id=1", (TS,))
    x("UPDATE devis SET frozen_at=? WHERE id=1", (TS,))
    x("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
      "VALUES ('DEP-00001-26', 1, 1, '2026-10-02', '12.50', 1, 'Achat')")
    x("INSERT INTO depenses (numero, fournisseur_id, date_depense, montant, categorie_id, description, cancelled_at, motif_annulation) "
      "VALUES ('DEP-00002-26', 2, '2026-10-03', '8.00', 1, 'Achat 2', ?, 'Erreur')", (TS2,))


def base5_peuplee():
    db = migrer(5)
    peupler_rang5(db)
    return db


class Base(unittest.TestCase):
    """Base au rang 6 (001 à 005 puis 005a) et fabrication de données conformes au schéma V3.13."""

    def setUp(self):
        self.db = migrer()
        self._n = 0

    # --- utilitaires d'assertion -------------------------------------------------
    @staticmethod
    def _a(args):
        """Paramètres liés : accepte aussi un tuple unique (couple (sql, paramètres) construit par une fabrique)."""
        return args[0] if len(args) == 1 and isinstance(args[0], tuple) else args

    def refuse(self, sql, *args):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, self._a(args))

    def refuse_inv(self, inv, sql, *args):
        """Refus levé par un trigger : le message porte l'identifiant de l'invariant."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, inv):
            self.db.execute(sql, self._a(args))

    def refuse_check(self, sql, *args):
        """Refus levé par une contrainte (CHECK, NOT NULL, UNIQUE, FK) et non par un trigger."""
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute(sql, self._a(args))
        self.assertNotIn("INV-", str(cm.exception))

    def un(self, sql, *args):
        return self.db.execute(sql, self._a(args)).fetchone()

    def tous(self, sql, *args):
        return self.db.execute(sql, self._a(args)).fetchall()

    def essai(self, sql, *args):
        """Retourne None si l'instruction réussit, sinon le message d'erreur."""
        try:
            self.db.execute(sql, self._a(args))
            return None
        except sqlite3.IntegrityError as e:
            return str(e)

    def permis(self, sql, *args):
        """L'instruction réussit puis est annulée (la base reste inchangée)."""
        self.db.execute("SAVEPOINT s")
        try:
            self.db.execute(sql, self._a(args))
        finally:
            self.db.execute("ROLLBACK TO s")
            self.db.execute("RELEASE s")

    # --- fabrication de données : tranches 001 à 003 -------------------------------
    def client(self, **kw):
        self._n += 1
        cols = {"code": f"CLI-{self._n:04d}", "nom": "Dupont"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO clients ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def fournisseur(self, **kw):
        self._n += 1
        cols = {"code": f"FOU-{self._n:04d}", "nom": "Fournisseur"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO fournisseurs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def prestation(self, ref="PLO-001"):
        self.db.execute("INSERT INTO categories_prestations (code, libelle, actif, ordre) VALUES (?, 'Libellé', 1, 1)", (f"C-{ref}",))
        cat = self.un("SELECT id FROM categories_prestations WHERE code=?", f"C-{ref}")[0]
        return self.db.execute("INSERT INTO prestations (reference, designation, categorie_id, unite, type_prestation, "
                               "prix_unitaire_ht, actif) VALUES (?, 'Désignation', ?, 'u', 'pose', '10', 1)", (ref, cat)).lastrowid

    def brouillon(self, client_id=None, **kw):
        """Devis brouillon : pas de numéro (PT-2)."""
        cols = {"numero": None, "client_id": client_id or self.client(), "client_snapshot": SNAP, "client_snapshot_version": 1,
                "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1, "chantier_snapshot": SNAP,
                "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": "brouillon", "total_ht": "0.00"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def snapshot_initial(self, d):
        total = self.un("SELECT total_ht FROM devis WHERE id=?", d)[0]
        self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                        "VALUES (?, NULL, 1, '{}', ?, ?)", (d, total, TS))

    def finaliser(self, d, numero=None):
        """Finalisation (INV-180) : snapshot de la version initiale, puis numéro attribué et statut en_attente dans un seul UPDATE."""
        self._n += 1
        numero = numero or f"DEV-{self._n:05d}-26"
        self.snapshot_initial(d)
        self.db.execute("UPDATE devis SET numero=?, statut='en_attente' WHERE id=?", (numero, d))
        return numero

    def devis(self, numero=None, client_id=None, **kw):
        """Devis en_attente (brouillon finalisé)."""
        d = self.brouillon(client_id=client_id, **kw)
        self.finaliser(d, numero)
        return d

    def devis_direct(self, statut="en_attente", **kw):
        """Devis inséré directement dans l'état voulu (conforme aux CHECK), sans snapshot ni ligne : pour les scénarios d'isolation."""
        self._n += 1
        cols = {"numero": None if statut == "brouillon" else f"DEV-{self._n:05d}-26", "client_id": self.client(),
                "client_snapshot": SNAP, "client_snapshot_version": 1, "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1,
                "chantier_snapshot": SNAP, "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": statut,
                "total_ht": "10.00"}
        if statut == "accepte":
            cols["date_acceptation"] = "2026-03-12"
        elif statut == "refuse":
            cols["date_refus"] = "2026-03-15"
            cols["motif_refus"] = "Trop cher"
        elif statut == "annule":
            cols["cancelled_at"] = TS
            cols["motif_annulation"] = "Annulation"
        cols.update(kw)
        return self.db.execute(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def revision_directe(self):
        d = self.devis_direct("brouillon")
        return self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                               "VALUES (?, NULL, 1, '{}', '10.00', ?)", (d, TS)).lastrowid

    def ligne(self, devis_id, ordre=1, **kw):
        cols = {"devis_id": devis_id, "ordre": ordre, "designation": "Pose prise", "quantite": "2", "unite": "u",
                "prix_unitaire_ht": "10.5", "remise_type": "aucune", "type_prestation": "pose", "total_ht": "21.00"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO devis_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def garantie(self, ligne_id, type_="decennale"):
        return self.db.execute("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, ?)", (ligne_id, type_)).lastrowid

    def accepter(self, d):
        self.db.execute("UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=?", (d,))

    def geler_devis(self, d):
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, d))

    def refuser(self, d):
        self.db.execute("UPDATE devis SET statut='refuse', date_refus='2026-03-15', motif_refus='Trop cher' WHERE id=?", (d,))

    def annuler_devis(self, d):
        self.db.execute("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='Annulation' WHERE id=?", (TS, d))

    def contenu_brouillon(self, d, lignes=2):
        """Ligne 1 (prestation du catalogue, deux garanties) et ligne 2 libre, posées pendant le brouillon (TR-11)."""
        self._n += 1
        l1 = self.ligne(d, 1, prestation_id=self.prestation(f"PLO-{self._n:03d}"), reference_prestation="PLO-X")
        g1, g2 = self.garantie(l1, "decennale"), self.garantie(l1, "biennale")
        l2 = self.ligne(d, 2, designation="Ligne libre", total_ht="10.50", quantite="1") if lignes >= 2 else None
        return l1, l2, g1, g2

    def devis_en_etat(self, etat, client_id=None):
        """Devis dans l'état voulu, avec ses lignes (posées en brouillon) : brouillon, en_attente, revision (en_attente avec
        revision_en_cours = 1), accepte, accepte_gele, refuse, annule."""
        d = self.brouillon(client_id=client_id, total_ht="31.50", remise_type="pourcentage", remise_valeur="10.00",
                           acompte_type="montant", acompte_valeur="5.00", objet="Objet", notes="Notes", date_validite="2026-04-10")
        l1, l2, g1, g2 = self.contenu_brouillon(d)
        if etat != "brouillon":
            self.finaliser(d)
        if etat == "revision":
            self.db.execute("UPDATE devis SET revision_en_cours=1 WHERE id=?", (d,))
        elif etat in ("accepte", "accepte_gele"):
            self.accepter(d)
            if etat == "accepte_gele":
                self.geler_devis(d)
        elif etat == "refuse":
            self.refuser(d)
        elif etat == "annule":
            self.annuler_devis(d)
        elif etat not in ("brouillon", "en_attente"):
            raise ValueError(etat)
        return types.SimpleNamespace(d=d, l1=l1, l2=l2, g1=g1, g2=g2)

    def devis_accepte(self, client_id=None, lignes=2, **kw):
        """Devis accepté non gelé : ligne 1 (prestation du catalogue, deux garanties), ligne 2 libre sans garantie."""
        kw.setdefault("total_ht", "31.50")
        kw.setdefault("remise_type", "pourcentage")
        kw.setdefault("remise_valeur", "10.00")
        kw.setdefault("acompte_type", "montant")
        kw.setdefault("acompte_valeur", "5.00")
        d = self.brouillon(client_id=client_id, **kw)
        if lignes >= 1:
            self.contenu_brouillon(d, lignes)
        self.finaliser(d)
        self.accepter(d)
        return d

    # --- fabrication de données : BC et lien devis <-> BC au rang 7 (ce que fait le service de création / de rattachement) ----
    def creer_bc(self, d=None, numero=None, lignes=True, lier=True, rang=1, **kw):
        """BC du devis `d` (par défaut un devis accepté neuf) : copie des données contractuelles, lien bc_devis, lignes et garanties."""
        d = d or self.devis_accepte()
        s = self.db.execute("SELECT client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                            "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                            "COALESCE(date_acceptation, '2026-03-12'), total_ht FROM devis WHERE id=?", (d,)).fetchone()
        cols = dict(zip(["client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                         "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version",
                         "date_acceptation", "montant_contractuel_ht"], s))
        cols["date_creation"] = kw.pop("date_creation", "2026-10-02")
        cols.update(kw)
        if numero is None:
            yy = cols["date_creation"][2:4]
            numero = f"BCD-{self.un(ATTRIBUER, 'BCD', int(yy))[0]:05d}-{yy}"
        cols["numero"] = numero
        b = self.db.execute(f"INSERT INTO bons_commande ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                            tuple(cols.values())).lastrowid
        if lier:
            self.lier(b, d, rang)
            if lignes:
                self.copier_lignes(b, d)
        return b

    def lier(self, b, d, rang=None):
        """Lien bc_devis ; sans rang, le suivant (service : ordre d'association, aucune contrainte de contiguïté)."""
        if rang is None:
            rang = self.un("SELECT COALESCE(MAX(rang), 0) + 1 FROM bc_devis WHERE bc_id=?", b)[0]
        return self.db.execute("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, ?)", (b, d, rang)).lastrowid

    def copier_lignes(self, b, d, max_ordre=99):
        """Copie 1:1 des lignes et garanties de lignes du devis `d` dans le BC ; l'ordre continue après les lignes déjà présentes."""
        decalage = self.un("SELECT COALESCE(MAX(ordre), 0) FROM bc_lignes WHERE bc_id=?", b)[0]
        self.db.execute("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, prestation_id, reference_prestation, designation, "
                        "description, quantite, unite, prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht) "
                        "SELECT ?, dl.id, dl.ordre + ?, dl.prestation_id, dl.reference_prestation, dl.designation, dl.description, "
                        "dl.quantite, dl.unite, dl.prix_unitaire_ht, dl.remise_type, dl.remise_valeur, dl.type_prestation, dl.total_ht "
                        "FROM devis_lignes dl WHERE dl.devis_id = ? AND dl.ordre <= ? ORDER BY dl.ordre", (b, decalage, d, max_ordre))
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) SELECT bl.id, dg.garantie_type "
                        "FROM bc_lignes bl JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id "
                        "JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id WHERE bl.bc_id = ? AND dl.devis_id = ?", (b, d))

    def rattacher(self, b, d=None, rang=None, lignes=True):
        """Rattachement d'un devis à un BC (INV-187) : lien, copie des lignes et garanties, contractuel augmenté — une transaction du service."""
        d = d or self.devis_accepte(client_id=self.client_du_bc(b))
        self.lier(b, d, rang)
        if lignes:
            self.copier_lignes(b, d)
        self.db.execute("UPDATE bons_commande SET montant_contractuel_ht = printf('%d.%02d', "
                        "(CAST(REPLACE(montant_contractuel_ht, '.', '') AS INTEGER) + CAST(REPLACE((SELECT total_ht FROM devis WHERE id=?), '.', '') AS INTEGER)) / 100, "
                        "(CAST(REPLACE(montant_contractuel_ht, '.', '') AS INTEGER) + CAST(REPLACE((SELECT total_ht FROM devis WHERE id=?), '.', '') AS INTEGER)) % 100) "
                        "WHERE id=?", (d, d, b))
        return d

    def client_du_bc(self, b):
        return self.un("SELECT client_id FROM bons_commande WHERE id=?", b)[0]

    def ligne_bc(self, b, dl, ordre, **kw):
        r = self.db.execute("SELECT prestation_id, reference_prestation, designation, description, quantite, unite, "
                            "prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht FROM devis_lignes WHERE id=?",
                            (dl,)).fetchone()
        cols = dict(zip(["prestation_id", "reference_prestation", "designation", "description", "quantite", "unite",
                         "prix_unitaire_ht", "remise_type", "remise_valeur", "type_prestation", "total_ht"], r))
        cols.update({"bc_id": b, "devis_ligne_id": dl, "ordre": ordre})
        cols.update(kw)
        return self.db.execute(f"INSERT INTO bc_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def bc_ligne(self, b, ordre=1):
        return self.un("SELECT id FROM bc_lignes WHERE bc_id=? AND ordre=?", b, ordre)[0]

    def geler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, b))
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id IN (SELECT devis_id FROM bc_devis WHERE bc_id=?)", (TS, b))

    def terminer_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', "
                        "avancement='100.00', montant_deja_facture_ht=montant_contractuel_ht, updated_at=? WHERE id=?", (TS, TS, b))

    def annuler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='Client renonce', "
                        "completed_at=NULL, date_100_facture=NULL, updated_at=? WHERE id=?", (TS_ANNUL, TS, b))

    def bc_en_etat(self, etat, client_id=None, dl3=False, **kw):
        """BC (avec lignes et garanties) dans l'état voulu : en_cours, gele, termine, annule, annule_gele.
        dl3=True ajoute au devis (avant la création du BC) une 3e ligne non copiée dans le BC."""
        d = self.brouillon(client_id=client_id, total_ht="31.50", remise_type="pourcentage", remise_valeur="10.00",
                           acompte_type="montant", acompte_valeur="5.00")
        dl1, dl2, _, _ = self.contenu_brouillon(d)
        extra = self.ligne(d, 3, designation="Ligne à venir", total_ht="5.00", quantite="1") if dl3 else None
        self.finaliser(d)
        self.accepter(d)
        b = self.creer_bc(d, lignes=False, **kw)
        self.copier_lignes(b, d, max_ordre=2)                                                      # la ligne 3 n'est pas copiée dans le BC
        if etat in ("gele", "termine", "annule_gele"):
            self.geler_bc(b)
        if etat == "termine":
            self.terminer_bc(b)
        if etat in ("annule", "annule_gele"):
            self.annuler_bc(b)
        elif etat not in ("en_cours", "gele", "termine"):
            raise ValueError(etat)
        return types.SimpleNamespace(
            d=d, b=b, dl1=dl1, dl2=dl2, dl3=extra, bl1=self.bc_ligne(b, 1), bl2=self.bc_ligne(b, 2),
            bg1=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='decennale'", self.bc_ligne(b, 1))[0],
            bg2=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='biennale'", self.bc_ligne(b, 1))[0])

    def devis_sup(self, bc, lignes=2, **kw):
        """Devis supplémentaire accepté du même client que le BC, avec lignes et garanties (posées en brouillon)."""
        return self.devis_accepte(client_id=self.client_du_bc(bc.b if hasattr(bc, "b") else bc), lignes=lignes, **kw)


def info_colonnes(db, table):
    """(nom, type, notnull, défaut, pk, caché) de PRAGMA table_xinfo."""
    return [tuple(r[1:]) for r in db.execute(f"PRAGMA table_xinfo({table})")]


def cles_etrangeres(db, table):
    """(table parente, colonne, colonne parente, on_update, on_delete)."""
    return sorted((r[2], r[3], r[4], r[5], r[6]) for r in db.execute(f"PRAGMA foreign_key_list({table})"))


def indexes_de(db, table):
    return sorted((r[1], r[2], r[3], r[4]) for r in db.execute(f"PRAGMA index_list({table})"))


def db_user_version(db):
    return db.execute("PRAGMA user_version").fetchone()[0]


def autre_valeur_bc(col, ancienne, autre_client):
    valeurs = {"id": 99999, "numero": "BCD-00099-26", "client_id": autre_client,
               "client_snapshot": '{"autre": 1}', "client_snapshot_version": 7, "entreprise_snapshot": '{"autre": 1}',
               "entreprise_snapshot_version": 7, "chantier_snapshot": '{"autre": 1}', "chantier_snapshot_version": 7,
               "date_creation": "2026-10-03", "date_acceptation": "2026-03-20", "date_debut": "2026-11-01",
               "date_fin": "2026-11-30", "montant_contractuel_ht": "999.99",
               "montant_deja_facture_ht": "12.00", "avancement": "12.00", "date_100_facture": "2026-10-03",
               "statut": "termine", "completed_at": TS2, "cancelled_at": TS2, "motif_annulation": "Autre motif",
               "frozen_at": TS2, "created_at": "2026-01-01T00:00:00.000Z", "updated_at": TS2, "origine": "import",
               "legacy_id": "autre", "legacy_data": '{"autre": 1}', "legacy_numero": "AUTRE-1"}
    v = valeurs[col]
    return v if v != ancienne else (None if ancienne is not None else "x")




class Base6(Base):
    """Base au rang 6 (001 à 005, 005a) : bons_commande porte encore devis_id, remise_* et acompte_* ; sert à fabriquer l'état
    d'une base existante avant d'appliquer 005b."""

    def setUp(self):
        self.db = migrer(6)
        self._n = 0

    # --- fabrication de données : tranche 004 (ce que fait le service de création) ----
    def creer_bc(self, d=None, numero=None, lignes=True, **kw):
        d = d or self.devis_accepte()
        s = self.db.execute("SELECT client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                            "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                            "COALESCE(date_acceptation, '2026-03-12'), total_ht, remise_type, remise_valeur, "
                            "acompte_type, acompte_valeur FROM devis WHERE id=?", (d,)).fetchone()
        cols = dict(zip(["client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                         "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version",
                         "date_acceptation", "montant_contractuel_ht", "remise_type", "remise_valeur", "acompte_type",
                         "acompte_valeur"], s))
        cols["devis_id"] = d
        cols["date_creation"] = kw.pop("date_creation", "2026-10-02")
        cols.update(kw)
        if numero is None:
            yy = cols["date_creation"][2:4]
            numero = f"BCD-{self.un(ATTRIBUER, 'BCD', int(yy))[0]:05d}-{yy}"
        cols["numero"] = numero
        b = self.db.execute(f"INSERT INTO bons_commande ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                            tuple(cols.values())).lastrowid
        if lignes:
            self.copier_lignes(b)
        return b

    def copier_lignes(self, b, max_ordre=99):
        self.db.execute("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, prestation_id, reference_prestation, designation, "
                        "description, quantite, unite, prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht) "
                        "SELECT ?, dl.id, dl.ordre, dl.prestation_id, dl.reference_prestation, dl.designation, dl.description, "
                        "dl.quantite, dl.unite, dl.prix_unitaire_ht, dl.remise_type, dl.remise_valeur, dl.type_prestation, dl.total_ht "
                        "FROM devis_lignes dl JOIN bons_commande b ON b.devis_id = dl.devis_id WHERE b.id = ? AND dl.ordre <= ? ORDER BY dl.ordre",
                        (b, b, max_ordre))
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) SELECT bl.id, dg.garantie_type "
                        "FROM bc_lignes bl JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id WHERE bl.bc_id = ?", (b,))

    def ligne_bc(self, b, dl, ordre, **kw):
        r = self.db.execute("SELECT prestation_id, reference_prestation, designation, description, quantite, unite, "
                            "prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht FROM devis_lignes WHERE id=?",
                            (dl,)).fetchone()
        cols = dict(zip(["prestation_id", "reference_prestation", "designation", "description", "quantite", "unite",
                         "prix_unitaire_ht", "remise_type", "remise_valeur", "type_prestation", "total_ht"], r))
        cols.update({"bc_id": b, "devis_ligne_id": dl, "ordre": ordre})
        cols.update(kw)
        return self.db.execute(f"INSERT INTO bc_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def bc_ligne(self, b, ordre=1):
        return self.un("SELECT id FROM bc_lignes WHERE bc_id=? AND ordre=?", b, ordre)[0]

    def geler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, b))
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=(SELECT devis_id FROM bons_commande WHERE id=?)", (TS, b))

    def terminer_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', "
                        "avancement='100.00', montant_deja_facture_ht=montant_contractuel_ht, updated_at=? WHERE id=?", (TS, TS, b))

    def annuler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='Client renonce', "
                        "completed_at=NULL, date_100_facture=NULL, updated_at=? WHERE id=?", (TS_ANNUL, TS, b))

    def bc_en_etat(self, etat, client_id=None, dl3=False, **kw):
        """BC (avec lignes et garanties) dans l'état voulu : en_cours, gele, termine, annule, annule_gele.
        dl3=True ajoute au devis (avant la création du BC) une 3e ligne non copiée dans le BC."""
        d = self.brouillon(client_id=client_id, total_ht="31.50", remise_type="pourcentage", remise_valeur="10.00",
                           acompte_type="montant", acompte_valeur="5.00")
        dl1, dl2, _, _ = self.contenu_brouillon(d)
        extra = self.ligne(d, 3, designation="Ligne à venir", total_ht="5.00", quantite="1") if dl3 else None
        self.finaliser(d)
        self.accepter(d)
        b = self.creer_bc(d, lignes=False, **kw)
        self.copier_lignes(b, max_ordre=2)                                                         # la ligne 3 n'est pas copiée dans le BC
        if etat in ("gele", "termine", "annule_gele"):
            self.geler_bc(b)
        if etat == "termine":
            self.terminer_bc(b)
        if etat in ("annule", "annule_gele"):
            self.annuler_bc(b)
        elif etat not in ("en_cours", "gele", "termine"):
            raise ValueError(etat)
        return types.SimpleNamespace(
            d=d, b=b, dl1=dl1, dl2=dl2, dl3=extra, bl1=self.bc_ligne(b, 1), bl2=self.bc_ligne(b, 2),
            bg1=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='decennale'", self.bc_ligne(b, 1))[0],
            bg2=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='biennale'", self.bc_ligne(b, 1))[0])


def _fabrique(cls):
    """Instance d'une fabrique de données (sans test propre : la classe n'est pas collectée par unittest)."""
    return type("Fabrique" + cls.__name__, (cls,), {"runTest": lambda self: None})()


def base6_peuplee():
    """Base au rang 6 réaliste : quatre BC (en_cours, gelé, terminé, annulé) avec lignes, garanties et dépenses, des devis dans tous les
    statuts, des snapshots de révision, des trous d'identifiants (séquences AUTOINCREMENT en avance sur le max). Retourne la fabrique."""
    t = _fabrique(Base6)
    t.setUp()
    x = t.db.execute
    bcs = {etat: t.bc_en_etat(etat) for etat in ("en_cours", "gele", "termine", "annule")}
    t.devis_en_etat("brouillon")
    t.devis_en_etat("en_attente")
    t.devis_en_etat("refuse")
    t.devis_en_etat("annule")
    t.devis_accepte()                                                                      # accepté sans BC
    rev = t.devis_en_etat("revision")
    t.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                 "VALUES (?, 1, 1, '{}', '31.50', ?)", (rev.d, TS))
    t.db.execute("UPDATE devis SET revision=1, revision_en_cours=0 WHERE id=?", (rev.d,))
    f = t.fournisseur()
    cat = x("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'Matériaux', 1, 1)").lastrowid
    x("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
      "VALUES ('DEP-00001-26', ?, ?, '2026-10-02', '12.50', ?, 'Achat')", (f, bcs["en_cours"].b, cat))
    x("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
      "VALUES ('DEP-00002-26', ?, ?, '2026-10-03', '8.00', ?, 'Achat annulé BC')", (f, bcs["annule"].b, cat))
    # valeurs non uniformes : une copie qui confond deux colonnes ou impose une valeur constante est détectée
    x("UPDATE bons_commande SET client_snapshot_version = 2, entreprise_snapshot_version = 3, chantier_snapshot_version = 4, "
      "origine = 'import', legacy_id = 'L-7', legacy_data = '{\"k\": 7}', legacy_numero = 'OLD-7' WHERE id = ?", (bcs["en_cours"].b,))
    x("UPDATE bons_commande SET date_debut = '2026-11-01', date_fin = '2026-11-30' WHERE id = ?", (bcs["gele"].b,))
    x("DELETE FROM bc_ligne_garanties WHERE id = ?", (bcs["en_cours"].bg2,))                                   # trou dans les identifiants de garanties
    x("UPDATE sqlite_sequence SET seq = seq + 5 WHERE name IN ('bons_commande', 'bc_ligne_garanties')")      # trous : séquence > max(id)
    t.bcs = bcs
    return t



def sur_rang7(t):
    """Fabrique de données du rang 7 sur la base de `t` (déjà migrée par 005b)."""
    u = _fabrique(Base)
    u.db, u._n = t.db, t._n + 1000
    return u


# points d'échec injectés : le fichier est coupé juste avant le marqueur, puis une instruction qui échoue est ajoutée
POINTS_D_ECHEC = ["DROP TRIGGER tr_18_devis_statut_avec_bc;", "DROP TRIGGER tr_13_bc_ligne_garanties_delete;", "CREATE TABLE bc_devis (",
                  "INSERT INTO bc_devis (bc_id, devis_id, rang, created_at)", "CREATE TABLE bons_commande_new (",
                  "INSERT INTO bons_commande_new (", "DROP TABLE bons_commande;", "ALTER TABLE bons_commande_new RENAME TO bons_commande;",
                  "CREATE INDEX idx_bons_commande_client_id", "CREATE TABLE bc_ligne_garanties_new (", "DROP TABLE bc_ligne_garanties;",
                  "ALTER TABLE bc_ligne_garanties_new RENAME TO bc_ligne_garanties;", "CREATE TRIGGER tr_01_bons_commande_numero_immuable",
                  "CREATE TRIGGER tr_12_bons_commande_contrat", "CREATE TRIGGER tr_17_bons_commande_insert",
                  "CREATE TRIGGER tr_99_bc_devis_insert", "CREATE TRIGGER tr_18_devis_statut_avec_bc", "CREATE TRIGGER tr_13_bc_lignes_insert",
                  "CREATE TRIGGER tr_13_bc_ligne_garanties_delete"]


def schema_sans(db, tables):
    return [o for o in objets(db) if o[2] not in tables]


class Migration(unittest.TestCase):
    def test_T46_chaine_ordonnee_jusqu_a_005b(self):
        self.assertEqual(NOMS, ("001_initial.sql", "002_fournisseurs.sql", "003_devis.sql", "004_bons_commande.sql",
                                "005_depenses.sql", "005a_corrections_v313.sql", "005b_bc_multi_devis.sql"))
        self.assertEqual(sorted(p.name for p in MIGRATIONS.glob("*.sql"))[:7], sorted(NOMS))

    def test_T46_rang_7_et_reglages_de_connexion(self):
        db = migrer()
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 7)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(db.execute("PRAGMA recursive_triggers").fetchone()[0], 1)
        self.assertEqual(migrer(6).execute("PRAGMA user_version").fetchone()[0], 6)
        self.assertEqual(migrer(5).execute("PRAGMA user_version").fetchone()[0], 5)

    def test_T46_le_fichier_ne_contient_ni_transaction_ni_pragma_ni_schema_version_ni_donnee_metier(self):
        sql = re.sub(r"\"[^\"]*\"|'[^']*'", "''", sans_commentaires(SQL_005B))                  # hors libellés de contraintes et messages
        for interdit in (r"\bBEGIN\s*;", r"\bBEGIN\s+(IMMEDIATE|EXCLUSIVE|DEFERRED|TRANSACTION)", r"\bCOMMIT\b", r"\bROLLBACK\b",
                         r"\bSAVEPOINT\b", r"\bPRAGMA\b", r"\bVACUUM\b", r"\bINSERT\s+OR\s+REPLACE\b", r"\bREPLACE\s+INTO\b",
                         r"\bschema_version\b", r"\bATTACH\b", r"\bDELETE\s+FROM\b", r"\bUPDATE\s+(?!sqlite_sequence)\w+\s+SET\b"):
            with self.subTest(interdit=interdit):
                self.assertIsNone(re.search(interdit, sql, re.I))
        self.assertNotIn("schema_version", sans_commentaires(SQL_005B))
        # les seules écritures de données : copie technique, séquences, reprise des liens existants, gardes en lecture seule
        inserts = re.findall(r"\bINSERT\s+INTO\s+(\w+)", sql, re.I)
        self.assertEqual(sorted(inserts), ["bc_devis", "bc_ligne_garanties_new", "bons_commande_new", "garde_005b_foreign_keys_off",
                                           "garde_005b_remise_acompte", "garde_005b_user_version", "sqlite_sequence", "sqlite_sequence"])
        # aucun INSERT ... VALUES : toute écriture est un INSERT ... SELECT depuis une table existante
        self.assertIsNone(re.search(r"\bVALUES\b", sql, re.I))

    def test_T46_le_fichier_ne_touche_ni_001_ni_003_ni_005_ni_les_objets_hors_perimetre(self):
        sql = sans_commentaires(SQL_005B)
        self.assertNotRegex(sql, r"\b(depenses|categories_depenses|categories_prestations|prestations|prestation_garanties|"
                                 r"import_anomalies|numerotation_sequences|fournisseurs|devis_revisions|devis_ligne_garanties|"
                                 r"devis_origine_id)\b")
        self.assertEqual(sorted(re.findall(r"\bDROP\s+TABLE\s+(\w+)", sql, re.I)),
                         ["bc_ligne_garanties", "bons_commande", "garde_005b_foreign_keys_off", "garde_005b_remise_acompte",
                          "garde_005b_user_version"])
        self.assertEqual(sorted(re.findall(r"\bCREATE\s+(?:TEMP\s+)?TABLE\s+(\w+)", sql, re.I)),
                         ["bc_devis", "bc_ligne_garanties_new", "bons_commande_new", "garde_005b_foreign_keys_off",
                          "garde_005b_remise_acompte", "garde_005b_user_version"])
        self.assertEqual(sorted(re.findall(r"\bALTER\s+TABLE\s+(\w+)", sql, re.I)), ["bc_ligne_garanties_new", "bons_commande_new"])
        # bc_lignes et devis ne sont ni reconstruits ni modifiés
        self.assertNotRegex(sql, r"\bCREATE\s+TABLE\s+(bc_lignes|devis)\b")
        self.assertNotRegex(sql, r"\bALTER\s+TABLE\s+(bc_lignes|devis)\b")
        # seul tr_18 est retouché côté devis
        self.assertEqual(sorted(re.findall(r"\bTRIGGER\s+(tr_\w+)\s+(?:BEFORE|AFTER)\s+\w+(?:\s+OF\s+[\w, ]+)?\s+ON\s+devis\b", sql, re.I)),
                         ["tr_18_devis_statut_avec_bc"])

    def test_T46_objets_exacts_au_rang_7(self):
        db = migrer()
        self.assertEqual(noms(db, "table"), TABLES_RANG7)
        self.assertEqual(noms(db, "index"), INDEXES_RANG7)
        triggers6 = noms(migrer(6), "trigger")
        self.assertEqual(noms(db, "trigger"), (triggers6 - TRIGGERS_SUPPRIMES) | TRIGGERS_NOUVEAUX)
        self.assertEqual(len(noms(db, "trigger")), len(triggers6) - 2 + 4)
        self.assertEqual(noms(db, "view"), set())
        self.assertEqual(db.execute("SELECT count(*) FROM sqlite_temp_master").fetchone()[0], 0)       # gardes supprimées

    def test_T46_integrite_fk_et_user_version_apres_005b(self):
        for nom in ("fraiche", "rang5_peuplee", "rang6_peuplee", "rang6_vide"):
            with self.subTest(base=nom):
                if nom == "fraiche":
                    db = migrer()
                elif nom == "rang5_peuplee":
                    db = base5_peuplee()
                    runner(db, 6)
                    runner(db, 7)
                elif nom == "rang6_peuplee":
                    db = base6_peuplee().db
                    runner(db, 7)
                else:
                    db = migrer(6)
                    runner(db, 7)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 7)
                self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                self.assertFalse(db.in_transaction)

    def test_T46_schema_identique_base_fraiche_base_migree_peuplee_et_base_migree_vide(self):
        fraiche = migrer()
        peuplee5 = base5_peuplee()
        runner(peuplee5, 6)
        runner(peuplee5, 7)
        peuplee6 = base6_peuplee().db
        runner(peuplee6, 7)
        vide6 = migrer(6)
        runner(vide6, 7)
        self.assertEqual(objets(fraiche), objets(peuplee5))
        self.assertEqual(objets(fraiche), objets(peuplee6))
        self.assertEqual(objets(fraiche), objets(vide6))

    def test_T46_les_donnees_existantes_sont_conservees_table_par_table(self):
        t = base6_peuplee()
        db = t.db
        avant = tout(db)
        bc_avant = db.execute(f"SELECT {','.join(COLONNES_BC)} FROM bons_commande ORDER BY id").fetchall()
        bg_avant = db.execute("SELECT id, ligne_id, garantie_type, created_at FROM bc_ligne_garanties ORDER BY id").fetchall()
        runner(db, 7)
        apres = tout(db)
        for table in sorted(TABLES_RANG6 - {"bons_commande"}):
            with self.subTest(table=table):
                self.assertEqual(avant[table], apres[table])
        for table in ("bc_lignes", "bc_ligne_garanties", "devis", "devis_lignes", "devis_ligne_garanties", "devis_revisions", "depenses",
                      "clients", "fournisseurs"):
            self.assertGreater(len(apres[table]), 0, table)
        self.assertEqual(db.execute(f"SELECT {','.join(COLONNES_BC)} FROM bons_commande ORDER BY id").fetchall(), bc_avant)
        self.assertEqual(bg_avant, apres["bc_ligne_garanties"])
        self.assertEqual(len(bc_avant), 4)
        self.assertEqual(colonnes(db, "bons_commande"), COLONNES_BC)
        self.assertEqual(len(apres["bc_devis"]), 4)

    def test_T46_la_reprise_cree_exactement_un_lien_par_bc_existant_et_rien_d_autre(self):
        t = base6_peuplee()
        db = t.db
        anciens = db.execute("SELECT id, devis_id, created_at FROM bons_commande ORDER BY id").fetchall()
        avant = tout(db)
        runner(db, 7)
        liens = db.execute("SELECT id, bc_id, devis_id, rang, created_at FROM bc_devis ORDER BY id").fetchall()
        self.assertEqual(liens, [(i + 1, bc, d, 1, ca) for i, (bc, d, ca) in enumerate(anciens)])        # ids dans l'ordre des BC, rang 1
        self.assertEqual([r[1] for r in liens], sorted(b.b for b in t.bcs.values()))
        self.assertEqual(len({r[2] for r in liens}), 4)                                                   # un devis par BC
        # aucune autre donnée créée : tout le reste est identique, y compris les compteurs de séquence hors bc_devis
        apres = tout(db)
        for table in sorted(set(avant) - {"bons_commande", "sqlite_sequence"}):
            self.assertEqual(avant[table], apres[table], table)
        seq_avant, seq_apres = dict(avant["sqlite_sequence"]), dict(apres["sqlite_sequence"])
        self.assertEqual(seq_apres.pop("bc_devis"), 4)
        self.assertEqual(seq_apres, seq_avant)
        # chaque lien relit bien le devis d'origine du BC : mêmes client, mêmes totaux et même date d'acceptation (CK-13 sur l'existant)
        self.assertEqual(db.execute("SELECT count(*) FROM bc_devis l JOIN bons_commande b ON b.id=l.bc_id JOIN devis d ON d.id=l.devis_id "
                                    "WHERE d.client_id=b.client_id AND d.total_ht=b.montant_contractuel_ht "
                                    "AND d.date_acceptation=b.date_acceptation").fetchone()[0], 4)

    def test_T46_ids_numeros_dates_et_caches_des_bc_sont_conserves(self):
        t = base6_peuplee()
        db = t.db
        avant = {r[0]: r for r in db.execute("SELECT id, numero, date_creation, date_acceptation, created_at, updated_at, statut, frozen_at, "
                                             "completed_at, cancelled_at, motif_annulation, date_100_facture, avancement, "
                                             "montant_deja_facture_ht, montant_contractuel_ht, client_snapshot, chantier_snapshot, origine "
                                             "FROM bons_commande")}
        runner(db, 7)
        for r in db.execute("SELECT id, numero, date_creation, date_acceptation, created_at, updated_at, statut, frozen_at, "
                            "completed_at, cancelled_at, motif_annulation, date_100_facture, avancement, montant_deja_facture_ht, "
                            "montant_contractuel_ht, client_snapshot, chantier_snapshot, origine FROM bons_commande"):
            self.assertEqual(r, avant[r[0]])
        self.assertEqual(sorted(avant), sorted(b.b for b in t.bcs.values()))
        self.assertEqual({r[6] for r in avant.values()}, {"en_cours", "termine", "annule"})
        # les clés étrangères entrantes (bc_lignes.bc_id, depenses.bc_id) pointent toujours les mêmes BC
        self.assertEqual(db.execute("SELECT DISTINCT bc_id FROM bc_lignes ORDER BY 1").fetchall(), [(b,) for b in sorted(avant)])
        self.assertEqual(db.execute("SELECT bc_id FROM depenses ORDER BY id").fetchall(), [(t.bcs["en_cours"].b,), (t.bcs["annule"].b,)])

    def test_T46_les_sequences_autoincrement_sont_conservees_et_jamais_regressives(self):
        t = base6_peuplee()
        db = t.db
        avant = dict(db.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
        self.assertGreater(avant["bons_commande"], 4)                                                 # trous : séquence > max(id)
        self.assertGreater(avant["bc_ligne_garanties"], db.execute("SELECT max(id) FROM bc_ligne_garanties").fetchone()[0])
        runner(db, 7)
        apres = dict(db.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
        for nom in ("bons_commande", "bc_ligne_garanties", "bc_lignes", "devis", "clients", "depenses"):
            self.assertEqual(apres[nom], avant[nom], nom)
        self.assertEqual(sorted(set(apres) - set(avant)), ["bc_devis"])                                # aucune ligne *_new résiduelle
        noms_seq = [r[0] for r in db.execute("SELECT name FROM sqlite_sequence")]
        self.assertEqual(len(noms_seq), len(set(noms_seq)))
        suivant = avant["bons_commande"] + 1
        t = sur_rang7(t)
        d = t.devis_accepte()
        self.assertEqual(t.creer_bc(d, lignes=False), suivant)                                          # l'id d'un BC n'est jamais réattribué
        gs = avant["bc_ligne_garanties"]
        t.copier_lignes(suivant, d)
        self.assertEqual(db.execute("SELECT min(id) FROM bc_ligne_garanties WHERE id > ?", (gs,)).fetchone()[0], gs + 1)

    def test_T46_sequence_conservee_meme_quand_les_tables_sont_vides(self):
        db = migrer(6)
        db.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('bons_commande', 7)")
        db.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('bc_ligne_garanties', 9)")
        runner(db, 7)
        self.assertEqual(db.execute("SELECT count(*) FROM bons_commande").fetchone(), (0,))
        self.assertEqual(db.execute("SELECT count(*) FROM bc_devis").fetchone(), (0,))
        self.assertEqual(dict(db.execute("SELECT name, seq FROM sqlite_sequence WHERE name IN ('bons_commande', 'bc_ligne_garanties')")),
                         {"bons_commande": 7, "bc_ligne_garanties": 9})
        self.assertEqual(db.execute("SELECT count(*) FROM sqlite_sequence WHERE name IN ('bons_commande_new', 'bc_ligne_garanties_new')").fetchone(), (0,))

    def test_T46_ids_conserves_avec_trous_et_references_intactes(self):
        """Une copie qui renumérote les lignes (sans copier id) casserait bc_lignes.bc_id, depenses.bc_id et bc_devis.bc_id."""
        t = base6_peuplee()
        db = t.db
        db.execute("UPDATE sqlite_sequence SET seq = seq + 10 WHERE name = 'bons_commande'")
        d = t.devis_accepte()
        b = t.creer_bc(d)                                                                             # id = ancienne séquence + 1 : trou
        self.assertGreater(b, 14)
        avant_l = db.execute("SELECT id, bc_id, devis_ligne_id, ordre FROM bc_lignes ORDER BY id").fetchall()
        avant_b = db.execute("SELECT id, numero FROM bons_commande ORDER BY id").fetchall()
        runner(db, 7)
        self.assertEqual(db.execute("SELECT id, numero FROM bons_commande ORDER BY id").fetchall(), avant_b)
        self.assertEqual(db.execute("SELECT id, bc_id, devis_ligne_id, ordre FROM bc_lignes ORDER BY id").fetchall(), avant_l)
        self.assertEqual(db.execute("SELECT bc_id, devis_id FROM bc_devis WHERE bc_id=?", (b,)).fetchall(), [(b, d)])
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_T46_base_fraiche_et_base_vide_au_rang_6_ne_creent_aucune_ligne(self):
        db = migrer(6)
        runner(db, 7)
        for table in sorted(noms(db, "table")):
            self.assertEqual(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0], 0, table)
        self.assertEqual(db.execute("SELECT count(*) FROM sqlite_sequence WHERE seq <> 0").fetchone()[0], 0)       # au plus des compteurs à zéro

    def test_T46_5b_est_atomique_un_echec_n_importe_ou_annule_tout(self):
        for point in POINTS_D_ECHEC:
            with self.subTest(echec_avant=point):
                db = base6_peuplee().db
                avant, schema_avant = tout(db), objets(db)
                self.assertIn(point, SQL_005B)
                coupe = SQL_005B[:SQL_005B.index(point)] + "\nINSERT INTO table_inexistante_005b VALUES (1);\n"
                with self.assertRaises(sqlite3.Error):
                    runner(db, 7, sql=coupe)
                self.assertFalse(db.in_transaction)
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 6)
                self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                self.assertEqual(objets(db), schema_avant)
                self.assertEqual(tout(db), avant)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
                runner(db, 7)                                                                         # le rejeu complet réussit ensuite
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 7)

    def test_T46_echec_apres_la_derniere_instruction_annule_aussi(self):
        db = base6_peuplee().db
        avant, schema_avant = tout(db), objets(db)
        with self.assertRaises(sqlite3.Error):
            runner(db, 7, sql=SQL_005B + "\nINSERT INTO table_inexistante_005b VALUES (1);\n")
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (6, schema_avant, avant))

    def test_T46_le_commit_n_a_lieu_qu_apres_les_verifications(self):
        """user_version est posé dans la transaction et ne devient durable qu'au COMMIT, après foreign_key_check : une orpheline
        (dépense d'un BC inexistant) fait tout annuler, user_version reste 6."""
        db = base6_peuplee().db
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
                   "VALUES ('DEP-00003-26', 1, 999, '2026-10-04', '1.00', 1, 'Orpheline')")
        db.execute("PRAGMA foreign_keys=ON")
        avant, schema_avant = tout(db), objets(db)
        with self.assertRaises(ErreurRunner):
            runner(db, 7)
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (6, schema_avant, avant))

    def test_T46_rejeu_sur_une_base_deja_au_rang_7_est_refuse_sans_effet(self):
        db = migrer()
        avant, schema_avant = tout(db), objets(db)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "user_version = 6"):
            runner(db, 7)
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (7, schema_avant, avant))

    def test_T46_version_incompatible_005b_ne_s_applique_qu_au_rang_6(self):
        for rang in (1, 2, 3, 4, 5):
            with self.subTest(rang=rang):
                db = migrer(rang)
                schema_avant = objets(db)
                with self.assertRaisesRegex(sqlite3.IntegrityError, "user_version = 6"):
                    runner(db, 7)
                self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db)), (rang, schema_avant))
        db = sqlite3.connect(":memory:", isolation_level=None)                                       # base vide (user_version 0)
        with self.assertRaises(sqlite3.Error):
            runner(db, 7)
        db = migrer(6)
        db.execute("PRAGMA user_version = 8")                                                         # base d'une version plus récente
        with self.assertRaisesRegex(sqlite3.IntegrityError, "user_version = 6"):
            runner(db, 7)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 8)

    def test_T46_la_chaine_normale_004_005_005a_005b(self):
        db = migrer(4)
        appliquer(db, 5, SQLS[4])
        runner(db, 6)
        runner(db, 7)
        self.assertEqual(objets(db), objets(migrer()))

    def test_T46_foreign_keys_actif_le_fichier_se_refuse_sans_rien_perdre(self):
        """Avec foreign_keys=ON, DROP TABLE bons_commande ne serait pas sûr : la garde l'interdit."""
        db = base6_peuplee().db
        avant, schema_avant = tout(db), objets(db)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "foreign_keys = OFF"):
            db.executescript(f"BEGIN IMMEDIATE;\n{SQL_005B}\nPRAGMA user_version = 7;\nCOMMIT;")
        if db.in_transaction:
            db.execute("ROLLBACK")
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (6, schema_avant, avant))

    def test_T46_les_gardes_ne_laissent_aucune_trace(self):
        db = migrer()
        self.assertEqual(db.execute("SELECT count(*) FROM sqlite_temp_master").fetchone()[0], 0)
        self.assertFalse([n for n in noms(db, "table") if "garde" in n])

    def test_T46_garde_la_remise_ou_l_acompte_d_un_bc_different_de_son_devis_bloque_la_migration(self):
        """Q-A : remise_* et acompte_* disparaissent du BC ; la migration refuse de perdre une information qui diffère du devis (CK-13)."""
        for modif in ("remise_type='montant', remise_valeur='3.00'", "remise_valeur='11.00'", "remise_type='aucune', remise_valeur=NULL",
                      "acompte_type='pourcentage', acompte_valeur='10.00'", "acompte_valeur='6.00'", "acompte_type='aucun', acompte_valeur=NULL"):
            with self.subTest(ecart=modif):
                t = base6_peuplee()
                t.db.execute(f"UPDATE bons_commande SET {modif} WHERE id=?", (t.bcs["en_cours"].b,))
                avant, schema_avant = tout(t.db), objets(t.db)
                with self.assertRaisesRegex(sqlite3.IntegrityError, "refuse de perdre la remise ou l'acompte"):
                    runner(t.db, 7)
                self.assertEqual((t.db.execute("PRAGMA user_version").fetchone()[0], objets(t.db), tout(t.db)), (6, schema_avant, avant))
                self.assertEqual(t.db.execute("SELECT count(*) FROM sqlite_temp_master").fetchone()[0], 0)

    def test_T46_garde_remise_acompte_ne_bloque_pas_un_bc_identique_a_son_devis_y_compris_valeurs_nulles(self):
        t = base6_peuplee()
        d0 = t.devis_accepte(remise_type="aucune", remise_valeur=None, acompte_type="aucun", acompte_valeur=None)
        t.creer_bc(d0)
        d1 = t.devis_accepte(remise_type="montant", remise_valeur="3.00", acompte_type="pourcentage", acompte_valeur="30.00")
        t.creer_bc(d1)
        runner(t.db, 7)
        self.assertEqual(t.db.execute("SELECT count(*) FROM bc_devis").fetchone()[0], 6)
        # les valeurs restent lisibles côté devis
        self.assertEqual(t.db.execute("SELECT remise_type, remise_valeur, acompte_type, acompte_valeur FROM devis WHERE id=?", (d1,)).fetchone(),
                         ("montant", "3.00", "pourcentage", "30.00"))

    def test_T46_non_regression_des_objets_hors_perimetre_sql_identique(self):
        db6, db7 = migrer(6), migrer()
        s6 = {o[1]: o for o in objets(db6)}
        s7 = {o[1]: o for o in objets(db7)}
        concernes_tables = {"bons_commande", "bc_ligne_garanties"}
        concernes_triggers = TRIGGERS_BC_RANG6 | TRIGGERS_AUTRES_TABLES_RANG6
        for nom, obj in sorted(s6.items()):
            if nom in concernes_tables or nom in concernes_triggers or nom in ("idx_bons_commande_client_id", "idx_bons_commande_statut"):
                continue
            with self.subTest(objet=nom):
                self.assertEqual(obj, s7[nom])                                                          # type, table, SQL : au caractère près
        # les 28 triggers de 005a hors BC (et tous ceux de 001 à 005) sont inchangés
        inchanges = noms(db6, "trigger") - concernes_triggers
        self.assertGreaterEqual(len(inchanges), 30)
        for nom in sorted(inchanges):
            self.assertEqual(s6[nom], s7[nom], nom)
        # index recréés à l'identique
        for nom in ("idx_bons_commande_client_id", "idx_bons_commande_statut"):
            self.assertEqual(s6[nom][1:], s7[nom][1:])

    def test_T46_G3_les_triggers_recrees_identiques_restent_ceux_de_004(self):
        db6, db7 = migrer(6), migrer()
        for nom in sorted(TRIGGERS_RECREES_IDENTIQUES):
            with self.subTest(trigger=nom):
                self.assertEqual(sql_de(db6, nom), sql_de(db7, nom))
                self.assertEqual(db7.execute("SELECT tbl_name FROM sqlite_master WHERE name=?", (nom,)).fetchone()[0], "bons_commande")
                self.assertNotRegex(sql_de(db7, nom).lower(), r"\b(from|join)\s+(clients|devis)\b")

    def test_T46_G1_les_triggers_de_bons_commande_ne_lisent_ni_clients_ni_a_rattacher(self):
        db = migrer()
        for nom in sorted(TRIGGERS_BC_RANG6 - TRIGGERS_SUPPRIMES) + ["tr_12_bons_commande_contrat"]:
            with self.subTest(trigger=nom):
                self.assertNotRegex(sql_de(db, nom).lower(), r"clients|a_rattacher")
                self.assertNotRegex(sql_de(db, nom), r"devis_id|remise_|acompte_")
        # client_id reste inconditionnellement verrouillé (le client 'a_rattacher' n'existe plus, INV-183)
        for nom in ("tr_12_bons_commande_contrat", "tr_12_bons_commande_annule"):
            self.assertIn("NEW.client_id IS NOT OLD.client_id", sql_de(db, nom))

    def test_T46_G2_tr17_tr18_lisent_des_colonnes_et_tables_existantes(self):
        """Les triggers recréés ne référencent plus bons_commande.devis_id : chacun s'exécute sur la table reconstruite."""
        t = Base()
        t.setUp()
        bc = t.bc_en_etat("en_cours")
        self.assertEqual(t.db.execute("SELECT tbl_name FROM sqlite_master WHERE name='tr_18_devis_statut_avec_bc'").fetchone()[0], "devis")
        self.assertEqual(t.db.execute("SELECT tbl_name FROM sqlite_master WHERE name='tr_17_bons_commande_insert'").fetchone()[0], "bons_commande")
        t.refuse_inv("INV-175", "UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", TS, bc.d)       # tr_18 s'exécute
        t.refuse_inv("INV-40", "INSERT INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                     "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                     "montant_contractuel_ht, statut, cancelled_at, motif_annulation) VALUES ('BCD-00077-26', 1, '{}', 1, '{}', 1, '{}', 1, "
                     "'2026-10-02', '2026-03-12', '1.00', 'annule', ?, 'm')", TS)                                                       # tr_17 s'exécute

    def test_T46_les_donnees_des_autres_tranches_sont_inchangees_apres_005b_sur_base_peuplee_au_rang_5(self):
        db = base5_peuplee()
        runner(db, 6)
        avant = tout(db)
        runner(db, 7)
        apres = tout(db)
        for table in sorted(TABLES_RANG6 - {"bons_commande"}):
            self.assertEqual(avant[table], apres[table], table)
        self.assertEqual(db.execute("SELECT id, numero, client_id FROM bons_commande").fetchall(), [(1, avant["bons_commande"][0][1], 1)])
        self.assertEqual(db.execute("SELECT bc_id, devis_id, rang FROM bc_devis").fetchall(), [(1, 1, 1)])
        self.assertEqual(db.execute("SELECT statut, frozen_at FROM bons_commande WHERE id=1").fetchone(), ("en_cours", TS))


    def test_T46_un_bc_orphelin_de_son_devis_bloque_la_migration_sans_rien_perdre(self):
        """Base endommagée (FK désactivées par un outil externe) : un BC dont le devis n'existe plus ne peut être ni repris dans bc_devis ni
        comparé à son devis ; la migration est refusée et rien n'est modifié."""
        t = base6_peuplee()
        db = t.db
        db.execute("DROP TRIGGER tr_17_bons_commande_insert")
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                   "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                   "montant_contractuel_ht, remise_type, acompte_type) VALUES ('BCD-00099-26', 9999, 1, '{}', 1, '{}', 1, '{}', 1, "
                   "'2026-10-02', '2026-03-12', '1.00', 'aucune', 'aucun')")
        db.execute("PRAGMA foreign_keys=ON")
        avant = tout(db)
        with self.assertRaises(Exception):
            runner(db, 7)
        self.assertEqual(tout(db), avant)
        self.assertEqual(db_user_version(db), 6)
        self.assertEqual(sorted(noms(db, "table")), sorted(TABLES_RANG6))


INFO_BC_DEVIS = [("id", "INTEGER", 0, None, 1, 0), ("bc_id", "INTEGER", 1, None, 0, 0), ("devis_id", "INTEGER", 1, None, 0, 0),
                 ("rang", "INTEGER", 1, None, 0, 0), ("created_at", "TEXT", 1, "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", 0, 0)]


def est_strict(db, table):
    """Table STRICT d'après PRAGMA table_list (le mot « STRICT » se trouve aussi dans « RESTRICT » : jamais de recherche textuelle)."""
    return db.execute("SELECT strict FROM pragma_table_list(?) WHERE schema = 'main'", (table,)).fetchone()[0] == 1


def definitions(sql):
    """Définitions de premier niveau d'un CREATE TABLE (colonnes et contraintes), commentaires retirés et espaces normalisés."""
    sql = re.sub(r"--[^\n]*", "", sql)
    corps = sql[sql.index("(") + 1:sql.rindex(")")]
    sortie, profondeur, courant, guillemet = [], 0, "", None
    for c in corps:
        if guillemet:
            courant += c
            guillemet = None if c == guillemet else guillemet
            continue
        if c in "'\"":
            guillemet = c
        elif c == "(":
            profondeur += 1
        elif c == ")":
            profondeur -= 1
        if c == "," and profondeur == 0:
            sortie.append(courant)
            courant = ""
        else:
            courant += c
    sortie.append(courant)
    return [re.sub(r"\s+", " ", d).strip() for d in sortie if d.strip()]


class Structure(Base):
    """Structure finale au rang 7 : bc_devis, bons_commande sans devis_id / remise_* / acompte_*, bc_ligne_garanties en RESTRICT."""

    def test_T46_bons_commande_colonnes_exactes_sans_devis_id_remise_ni_acompte(self):
        self.assertEqual(colonnes(self.db, "bons_commande"), COLONNES_BC)
        for retiree in ("devis_id", "remise_type", "remise_valeur", "acompte_type", "acompte_valeur"):
            self.assertNotIn(retiree, colonnes(self.db, "bons_commande"))
            self.assertNotRegex(sql_de(self.db, "bons_commande"), retiree)

    def test_T46_les_colonnes_conservees_ont_le_meme_type_nullite_defaut_et_cle(self):
        db6 = migrer(6)
        anciennes = {c[0]: c for c in info_colonnes(db6, "bons_commande")}
        nouvelles = info_colonnes(self.db, "bons_commande")
        self.assertEqual([c[0] for c in nouvelles], COLONNES_BC)
        for c in nouvelles:
            with self.subTest(colonne=c[0]):
                self.assertEqual(c, anciennes[c[0]])
        self.assertTrue(est_strict(self.db, "bons_commande"))
        self.assertIn("AUTOINCREMENT", sql_de(self.db, "bons_commande"))

    def test_T46_bc_devis_structure_exacte(self):
        self.assertEqual(info_colonnes(self.db, "bc_devis"), INFO_BC_DEVIS)
        sql = sql_de(self.db, "bc_devis")
        self.assertTrue(est_strict(self.db, "bc_devis"))
        self.assertIn("AUTOINCREMENT", sql)
        self.assertEqual(cles_etrangeres(self.db, "bc_devis"),
                         [("bons_commande", "bc_id", "id", "NO ACTION", "RESTRICT"), ("devis", "devis_id", "id", "NO ACTION", "RESTRICT")])

    def test_T46_bc_devis_unicites_et_index(self):
        indexes = indexes_de(self.db, "bc_devis")
        self.assertEqual(len(indexes), 2)
        self.assertTrue(all(i[1] == 1 for i in indexes))                                                # deux index uniques
        colonnes_indexees = sorted(tuple(r[2] for r in self.db.execute(f"PRAGMA index_info({i[0]})")) for i in indexes)
        self.assertEqual(colonnes_indexees, [("bc_id", "rang"), ("devis_id",)])                         # couvrent bc_id (préfixe) et devis_id

    def test_T46_cles_etrangeres_des_tables_du_bc(self):
        self.assertEqual(cles_etrangeres(self.db, "bons_commande"), [("clients", "client_id", "id", "NO ACTION", "RESTRICT")])
        self.assertEqual(cles_etrangeres(self.db, "bc_lignes"),
                         [("bons_commande", "bc_id", "id", "NO ACTION", "RESTRICT"), ("devis_lignes", "devis_ligne_id", "id", "NO ACTION", "RESTRICT"),
                          ("prestations", "prestation_id", "id", "NO ACTION", "RESTRICT")])
        self.assertEqual(cles_etrangeres(self.db, "depenses")[0], ("bons_commande", "bc_id", "id", "NO ACTION", "RESTRICT"))
        self.assertIn(("devis", "devis_id", "id", "NO ACTION", "RESTRICT"), cles_etrangeres(self.db, "devis_revisions"))

    def test_T46_PT5_bc_ligne_garanties_ligne_id_en_restrict_et_le_reste_inchange(self):
        self.assertEqual(cles_etrangeres(self.db, "bc_ligne_garanties"), [("bc_lignes", "ligne_id", "id", "NO ACTION", "RESTRICT")])
        self.assertEqual(cles_etrangeres(migrer(6), "bc_ligne_garanties"), [("bc_lignes", "ligne_id", "id", "NO ACTION", "CASCADE")])
        self.assertEqual(info_colonnes(self.db, "bc_ligne_garanties"), info_colonnes(migrer(6), "bc_ligne_garanties"))
        self.assertEqual(sorted(tuple(r[2] for r in self.db.execute(f"PRAGMA index_info({i[0]})")) for i in indexes_de(self.db, "bc_ligne_garanties")),
                         [("ligne_id", "garantie_type")])
        self.assertTrue(est_strict(self.db, "bc_ligne_garanties"))

    def test_T46_bc_lignes_devis_devis_lignes_et_devis_revisions_sont_inchanges(self):
        db6 = migrer(6)
        for table in ("bc_lignes", "devis", "devis_lignes", "devis_ligne_garanties", "devis_revisions", "clients", "fournisseurs", "depenses"):
            with self.subTest(table=table):
                self.assertEqual(sql_de(self.db, table), sql_de(db6, table))
        self.assertEqual(colonnes(self.db, "bc_lignes"), COLONNES_BC_LIGNES)
        self.assertEqual(colonnes(self.db, "devis"), COLONNES_DEVIS)
        self.assertNotIn("devis_id", colonnes(self.db, "bc_lignes"))                                   # le devis d'une ligne se lit par devis_ligne_id

    def test_T46_devis_origine_id_n_existe_dans_aucune_table(self):
        for table in sorted(noms(self.db, "table")):
            with self.subTest(table=table):
                self.assertNotIn("devis_origine_id", colonnes(self.db, table))

    def test_T46_aucun_trigger_ni_index_ne_reference_une_colonne_retiree(self):
        for ty, nom, table, sql in objets(self.db):
            if ty in ("trigger", "index") and sql:
                with self.subTest(objet=nom):
                    self.assertNotRegex(sql, r"b\.devis_id|bons_commande\.devis_id|NEW\.devis_id.*bons_commande|\bremise_type\b.*bons_commande")
        for nom in noms(self.db, "trigger"):
            if sql_de(self.db, nom) and "bons_commande" in sql_de(self.db, nom):
                with self.subTest(trigger=nom):
                    self.assertNotRegex(sql_de(self.db, nom), r"OLD\.devis_id|NEW\.remise|NEW\.acompte|OLD\.remise|OLD\.acompte")

    def test_T46_tous_les_triggers_sont_before_et_les_insert_or_replace_sont_gardes(self):
        for ty, nom, table, sql in objets(self.db):
            if ty == "trigger":
                with self.subTest(trigger=nom):
                    self.assertRegex(sql, r"\bBEFORE\b")
                    self.assertNotRegex(sql, r"\bAFTER\b|\bINSTEAD\b")

    def test_T46_rang_check_strict_et_types(self):
        bc = self.bc_en_etat("en_cours")
        d1 = self.devis_sup(bc)
        for rang in (0, -1, None, "a", 1.5, "1.5", ""):
            with self.subTest(rang=rang):
                self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, ?)", bc.b, d1, rang)
        self.db.execute("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, '2')", (bc.b, d1))     # STRICT : '2' converti en entier
        self.assertEqual(self.un("SELECT rang, typeof(rang) FROM bc_devis WHERE devis_id=?", d1), (2, "integer"))

    def test_T46_created_at_du_lien_defaut_valide_et_format_controle(self):
        bc = self.bc_en_etat("en_cours")
        d1, d2 = self.devis_sup(bc), self.devis_sup(bc)
        self.lier(bc.b, d1)
        self.assertRegex(self.un("SELECT created_at FROM bc_devis WHERE devis_id=?", d1)[0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
        self.db.execute("INSERT INTO bc_devis (bc_id, devis_id, rang, created_at) VALUES (?, ?, 5, ?)", (bc.b, d2, TS))
        self.assertEqual(self.un("SELECT created_at FROM bc_devis WHERE devis_id=?", d2)[0], TS)
        d3 = self.devis_sup(bc)
        for mauvais in ("2026-10-01", "2026-10-01T10:00:00Z", "hier", "", None):
            with self.subTest(created_at=mauvais):
                self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang, created_at) VALUES (?, ?, 9, ?)", bc.b, d3, mauvais)

    def test_T46_les_check_de_bons_commande_sont_conserves(self):
        bc = self.bc_en_etat("en_cours")
        gele = self.bc_en_etat("gele")
        sql = lambda m, b=bc.b: ("UPDATE bons_commande SET " + m + " WHERE id=?", (b,))
        cas = [("numero hors format", "numero='BCD-1-26'"), ("numero année incohérente", "numero='BCD-00099-25'"),
               ("montant sans 2 décimales", "montant_contractuel_ht='1.5'"), ("montant avec zéros de tête", "montant_contractuel_ht='01.50'"),
               ("montant non numérique", "montant_contractuel_ht='abc'"), ("avancement > 100", "avancement='100.01'"),
               ("avancement hors format", "avancement='5'"), ("statut inconnu", "statut='autre'"),
               ("termine sans completed_at", "statut='termine', date_100_facture='2026-10-02', avancement='100.00'"),
               ("completed_at sans termine", f"completed_at='{TS}'"), ("annule sans cancelled_at", "statut='annule'"),
               ("cancelled_at sans motif", f"cancelled_at='{TS}', motif_annulation=''"), ("date_fin < date_debut", "date_debut='2026-12-01', date_fin='2026-11-01'"),
               ("date_100_facture sans avancement 100", "date_100_facture='2026-10-02'"), ("date mal formée", "date_debut='01/11/2026'"),
               ("completed_at mal formé", "statut='termine', completed_at='hier', date_100_facture='2026-10-02', avancement='100.00'")]
        for nom, m in cas:
            with self.subTest(violation=nom):
                s, a = sql(m)
                self.refuse(s, a)
        # PT-8 « conservateur » : frozen_at et ses deux CHECK sont conservés
        self.refuse_check("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', avancement='100.00' WHERE id=?", TS, bc.b)
        self.refuse_check("UPDATE bons_commande SET date_100_facture='2026-10-02', avancement='100.00' WHERE id=?", bc.b)
        self.permis("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', avancement='100.00' WHERE id=?", TS, gele.b)
        self.refuse_check("UPDATE bons_commande SET frozen_at='hier' WHERE id=?", bc.b)
        # BLOC-IMP+
        self.refuse_check("INSERT INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                          "montant_contractuel_ht, legacy_id) VALUES ('BCD-00071-26', 1, '{}', 1, '{}', 1, '{}', 1, '2026-10-02', '2026-03-12', '1.00', 'L')")
        self.refuse_check("INSERT INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                          "montant_contractuel_ht, origine, legacy_numero) VALUES ('BCD-00072-26', 1, '{}', 1, '{}', 1, '{}', 1, '2026-10-02', '2026-03-12', "
                          "'1.00', 'import', 'BCD-00072-26')")
        self.refuse_check("INSERT INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                          "montant_contractuel_ht) VALUES ('BCD-00073-26', 1, 'pas du json', 1, '{}', 1, '{}', 1, '2026-10-02', '2026-03-12', '1.00')")

    def test_T46_les_anciennes_colonnes_de_bons_commande_ne_sont_plus_insérables(self):
        base = ("INSERT INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                "montant_contractuel_ht, {c}) VALUES ('BCD-00070-26', ?, '{{}}', 1, '{{}}', 1, '{{}}', 1, '2026-10-02', '2026-03-12', '1.00', ?)")
        cl = self.client()
        for col, val in (("devis_id", 1), ("remise_type", "aucune"), ("remise_valeur", None), ("acompte_type", "aucun"), ("acompte_valeur", None)):
            with self.subTest(colonne=col):
                with self.assertRaises(sqlite3.OperationalError):
                    self.db.execute(base.format(c=col), (cl, val))
        self.assertEqual(self.un("SELECT count(*) FROM bons_commande")[0], 0)

    def test_T46_bc_lignes_et_garanties_conservent_leurs_contraintes(self):
        bc = self.bc_en_etat("en_cours", dl3=True)
        autre = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.lier(bc.b, autre)
        dl = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", autre)[0]
        for nom, kw in (("quantité nulle", {"quantite": "0"}), ("quantité zéro de tête", {"quantite": "01"}), ("unité inconnue", {"unite": "kg"}),
                        ("prix avec zéro final", {"prix_unitaire_ht": "1.50"}), ("total à 1 décimale", {"total_ht": "1.5"}),
                        ("remise incohérente", {"remise_type": "montant"}), ("désignation vide", {"designation": ""}),
                        ("ordre nul", {"ordre": 0}), ("type_prestation inconnu", {"type_prestation": "x"})):
            with self.subTest(violation=nom):
                ordre = kw.pop("ordre", 10)
                self.refuse_check("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                                  "type_prestation, total_ht) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", bc.b, dl, ordre, kw.get("designation", "L"),
                                  kw.get("quantite", "1"), kw.get("unite", "u"), kw.get("prix_unitaire_ht", "1.5"), kw.get("remise_type", "aucune"),
                                  kw.get("type_prestation", "pose"), kw.get("total_ht", "1.50"))
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'autre')", bc.bl1)
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", bc.bl1)             # UNIQUE(ligne_id, type)

    def test_T46_bons_commande_est_exactement_celui_de_004_moins_devis_id_remise_et_acompte(self):
        """Colonnes, NOT NULL, UNIQUE, défauts, FK et chacun des CHECK (tables et colonnes) sont ceux de 004, à l'ordre près, hors les 5 colonnes retirées
        et les 6 CHECK de remise / d'acompte."""
        d6 = definitions(sql_de(migrer(6), "bons_commande"))
        retirees = [d for d in d6 if d.startswith(("devis_id ", "remise_type ", "remise_valeur ", "acompte_type ", "acompte_valeur "))
                    or (d.startswith("CHECK") and re.search(r"remise_|acompte_", d))]
        self.assertEqual(len(retirees), 5 + 6)
        attendu = [d for d in d6 if d not in retirees]
        d7 = definitions(sql_de(self.db, "bons_commande"))
        self.assertEqual(d7, attendu)
        self.assertGreater(len(d7), 40)
        self.assertTrue(est_strict(self.db, "bons_commande"))

    def test_T46_bc_ligne_garanties_est_exactement_celui_de_004_avec_restrict(self):
        d6 = definitions(sql_de(migrer(6), "bc_ligne_garanties"))
        self.assertEqual(sum("ON DELETE CASCADE" in d for d in d6), 1)
        self.assertEqual(definitions(sql_de(self.db, "bc_ligne_garanties")), [d.replace("ON DELETE CASCADE", "ON DELETE RESTRICT") for d in d6])
        self.assertTrue(est_strict(self.db, "bc_ligne_garanties"))

    def test_T46_les_autres_tables_du_bc_et_du_devis_sont_strict(self):
        for t in sorted(TABLES_RANG7):
            with self.subTest(table=t):
                self.assertTrue(est_strict(self.db, t))


class LienBcDevis(Base):
    """bc_devis (PT-6) et TR-99 : un devis dans un seul BC ; à l'INSERT, devis accepté, même client, BC non annulé ; jamais modifié ni supprimé."""

    def test_INV_40_seul_un_devis_accepte_se_rattache_a_un_bc(self):
        bc = self.bc_en_etat("en_cours")
        cl = self.client_du_bc(bc.b)
        for etat in ("brouillon", "en_attente", "revision", "refuse", "annule"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat, client_id=cl)
                self.refuse_inv("INV-40", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b, dv.d)
        for etat in ("accepte", "accepte_gele"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat, client_id=cl)
                self.lier(bc.b, dv.d)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE bc_id=?", bc.b)[0], 3)

    def test_INV_48_un_bc_ne_regroupe_que_des_devis_du_meme_client(self):
        bc = self.bc_en_etat("en_cours")
        autre = self.devis_accepte(client_id=self.client())
        self.refuse_inv("INV-48", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b, autre)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE bc_id=?", bc.b)[0], 1)
        self.lier(bc.b, self.devis_accepte(client_id=self.client_du_bc(bc.b)))

    def test_INV_48_le_controle_du_client_se_fait_aussi_pour_le_premier_devis_du_bc(self):
        """Le BC naît sans lien (TR-17 ne lit plus le devis) : le premier lien porte le contrôle du client et du statut du devis (C5)."""
        d = self.devis_accepte()
        b = self.creer_bc(d, lignes=False, lier=False)
        self.refuse_inv("INV-48", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 1)",
                        self.creer_bc(self.devis_accepte(), lignes=False, lier=False), d)
        self.lier(b, d)
        dv = self.devis_en_etat("en_attente", client_id=self.client_du_bc(b))
        b2 = self.creer_bc(self.devis_accepte(), lignes=False, lier=False)
        self.refuse_inv("INV-40|INV-48", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 1)", b2, dv.d)

    def test_INV_188_un_bc_annule_ne_recoit_aucun_devis(self):
        for etat in ETATS_BC_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
                self.refuse_inv("INV-188", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b, d)
                self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE devis_id=?", d)[0], 0)

    def test_INV_187_INTERPRETATION_le_schema_ne_porte_pas_la_regle_du_solde_ni_dans_un_sens_ni_dans_l_autre(self):
        """INV-187, INV-43, E-16 : « tant que le solde n'est pas rédigé/validé » est une règle de service (CK-14), car aucune donnée de 005b ne la
        matérialise : date_100_facture, statut 'termine' et frozen_at sont des caches (qui reviennent après avoir) ou sans rôle de clôture (PT-8).
        Le schéma accepte donc le lien quels que soient ces champs ; il ne peut ni refuser un rattachement interdit ni en refuser un permis."""
        combinaisons = {"en_cours neuf": "en_cours", "gelé": "gele", "terminé (date_100_facture posée)": "termine"}
        for nom, etat in combinaisons.items():
            with self.subTest(bc=nom):
                bc = self.bc_en_etat(etat)
                d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
                self.lier(bc.b, d)
        # avoir total sur le solde : le BC revient en_cours, date_100_facture NULL, frozen_at reste (irréversible) : le schéma accepte encore
        bc = self.bc_en_etat("termine")
        self.db.execute("UPDATE bons_commande SET statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='60.00' WHERE id=?", (bc.b,))
        self.assertEqual(self.un("SELECT statut, date_100_facture, frozen_at IS NOT NULL FROM bons_commande WHERE id=?", bc.b), ("en_cours", None, 1))
        self.lier(bc.b, self.devis_accepte(client_id=self.client_du_bc(bc.b)))

    def test_INV_175_un_devis_n_appartient_qu_a_un_seul_bc(self):
        bc = self.bc_en_etat("en_cours")
        cl = self.client_du_bc(bc.b)
        b2 = self.creer_bc(self.devis_accepte(client_id=cl), lignes=False)
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 5)", b2, bc.d)                 # devis du premier BC
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 5)", bc.b, bc.d)               # deux fois dans le même BC
        d = self.devis_accepte(client_id=cl)
        self.lier(bc.b, d)
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 9)", b2, d)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE devis_id=?", d)[0], 1)

    def test_INV_187_un_bc_peut_avoir_plusieurs_devis_chaque_devis_dans_un_seul_bc(self):
        bc = self.bc_en_etat("en_cours")
        for _ in range(4):
            self.lier(bc.b, self.devis_accepte(client_id=self.client_du_bc(bc.b)))
        self.assertEqual(self.tous("SELECT rang FROM bc_devis WHERE bc_id=? ORDER BY rang", bc.b), [(1,), (2,), (3,), (4,), (5,)])
        self.assertEqual(self.un("SELECT count(DISTINCT devis_id) FROM bc_devis")[0], 5)

    def test_INV_187_INTERPRETATION_Q_D_rang_ni_contigu_ni_impose(self):
        """Q-D : le rang est un ordre d'association, pas un invariant métier. Seuls rang >= 1 et UNIQUE(bc_id, rang) sont posés : le premier lien peut
        avoir un rang quelconque, les rangs peuvent avoir des trous, et un même rang peut exister dans deux BC."""
        cl = self.client()
        b1 = self.creer_bc(self.devis_accepte(client_id=cl), lignes=False, rang=7)
        self.assertEqual(self.un("SELECT rang FROM bc_devis WHERE bc_id=?", b1)[0], 7)
        self.lier(b1, self.devis_accepte(client_id=cl), 2)
        self.lier(b1, self.devis_accepte(client_id=cl), 100)
        self.assertEqual(self.tous("SELECT rang FROM bc_devis WHERE bc_id=? ORDER BY rang", b1), [(2,), (7,), (100,)])
        b2 = self.creer_bc(self.devis_accepte(client_id=cl), lignes=False, rang=7)                                  # même rang dans un autre BC
        self.assertEqual(self.un("SELECT rang FROM bc_devis WHERE bc_id=?", b2)[0], 7)
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 7)", b1, self.devis_accepte(client_id=cl))
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 100)", b1, self.devis_accepte(client_id=cl))

    def test_INV_184_un_lien_ne_se_modifie_jamais_colonne_par_colonne(self):
        bc = self.bc_en_etat("en_cours")
        autre = self.bc_en_etat("en_cours")
        d2 = self.devis_accepte(client_id=self.client_du_bc(autre.b))
        lien = self.un("SELECT id FROM bc_devis WHERE bc_id=?", bc.b)[0]
        for col, val in (("id", 999), ("bc_id", autre.b), ("devis_id", d2), ("rang", 9), ("created_at", TS2)):
            with self.subTest(colonne=col):
                self.refuse_inv("INV-184", f"UPDATE bc_devis SET {col}=? WHERE id=?", val, lien)
        self.refuse_inv("INV-184", "UPDATE bc_devis SET rang=rang WHERE id=?", lien)                                # même sans changement de valeur
        self.refuse_inv("INV-184", "UPDATE bc_devis SET rang=9, created_at=? WHERE id=?", TS2, lien)
        self.refuse_inv("INV-184", "UPDATE bc_devis SET rang=rang + 1")
        self.assertEqual(self.un("SELECT bc_id, devis_id, rang FROM bc_devis WHERE id=?", lien), (bc.b, bc.d, 1))

    def test_INV_184_un_lien_ne_se_supprime_jamais_ni_par_replace(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                lien = self.un("SELECT id FROM bc_devis WHERE bc_id=?", bc.b)[0]
                # sur un BC annulé, le REPLACE est déjà refusé à l'INSERT (INV-188) : il n'y a aucun chemin pour remplacer le lien
                inv = "INV-188" if etat in ETATS_BC_ANNULES else "INV-184"
                self.refuse_inv("INV-184", "DELETE FROM bc_devis WHERE bc_id=?", bc.b)
                self.refuse_inv(inv, "INSERT OR REPLACE INTO bc_devis (id, bc_id, devis_id, rang) VALUES (?, ?, ?, 1)", lien, bc.b, bc.d)   # clé primaire
                self.refuse_inv(inv, "INSERT OR REPLACE INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 1)", bc.b, bc.d)                 # devis_id
        self.refuse_inv("INV-184", "DELETE FROM bc_devis")
        bc = self.bc_en_etat("en_cours")
        d2 = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.refuse_inv("INV-184", "INSERT OR REPLACE INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 1)", bc.b, d2)      # sur (bc_id, rang)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis")[0], 6)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE devis_id=?", d2)[0], 0)

    def test_INV_184_les_actions_ignorees_sans_recursive_triggers_sont_couvertes_par_les_cle_etrangeres(self):
        """Hors réglage D-39 (recursive_triggers=OFF), le DELETE implicite d'un REPLACE ne déclenche pas le trigger : le lien serait remplacé.
        Le réglage est donc obligatoire (vérifié par test_T46_rang_7_et_reglages_de_connexion) ; ce test documente ce que perdrait une base mal
        configurée, comme pour 003 et 004."""
        db = migrer(recursive=False)
        t = Base()
        t.db, t._n = db, 0
        bc = t.bc_en_etat("en_cours")
        db.execute("INSERT OR REPLACE INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 1)", (bc.b, bc.d))
        self.assertEqual(db.execute("SELECT count(*) FROM bc_devis").fetchone()[0], 1)
        db2 = migrer()
        t2 = Base()
        t2.db, t2._n = db2, 0
        bc2 = t2.bc_en_etat("en_cours")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-184"):
            db2.execute("INSERT OR REPLACE INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 1)", (bc2.b, bc2.d))

    def test_T46_lien_vers_un_bc_ou_un_devis_inexistant_refuse_par_la_cle_etrangere(self):
        bc = self.bc_en_etat("en_cours")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (999, ?, 2)", d)
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, 999, 2)", bc.b)
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (999, 999, 2)")
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (NULL, ?, 2)", d)
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, NULL, 2)", bc.b)

    def test_T46_RESTRICT_un_bc_ou_un_devis_lie_ne_peut_pas_disparaitre(self):
        """Les triggers de suppression (TR-19, TR-98) sont retirés : ce sont alors les clés étrangères RESTRICT de bc_devis qui protègent."""
        bc = self.bc_en_etat("en_cours")
        for nom in sorted(noms(self.db, "trigger")):
            self.db.execute(f"DROP TRIGGER {nom}")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM bons_commande WHERE id=?", (bc.b,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM devis WHERE id=?", (bc.d,))
        self.db.execute("DELETE FROM bc_ligne_garanties")                                                            # sans trigger : possible
        self.db.execute("DELETE FROM bc_lignes")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM bons_commande WHERE id=?", (bc.b,))                                        # le lien suffit
        self.db.execute("DELETE FROM bc_devis")
        self.db.execute("DELETE FROM bons_commande WHERE id=?", (bc.b,))

    def test_INV_187_rattacher_ne_modifie_aucune_colonne_du_devis(self):
        bc = self.bc_en_etat("en_cours")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        avant = self.un(f"SELECT {','.join(COLONNES_DEVIS)} FROM devis WHERE id=?", d)
        self.rattacher(bc.b, d)
        self.assertEqual(self.un(f"SELECT {','.join(COLONNES_DEVIS)} FROM devis WHERE id=?", d), avant)
        self.assertEqual(self.un("SELECT statut, numero, revision, revision_en_cours, frozen_at FROM devis WHERE id=?", d)[0], "accepte")


class DevisStatutAvecBC(Base):
    """TR-18 [INV-175] : un devis rattaché à un BC (par bc_devis) ne quitte 'accepte' que si ce BC est annulé ; aucune cascade BC -> devis."""

    SORTIES = ("statut='annule', cancelled_at='%s', motif_annulation='m'" % TS, "statut='en_attente'", "statut='refuse', date_refus='2026-03-20'")

    def test_INV_175_un_devis_rattache_ne_quitte_pas_accepte_tant_que_son_bc_n_est_pas_annule(self):
        for etat in ETATS_BC_NON_ANNULES:
            bc = self.bc_en_etat(etat)
            d2 = self.rattacher(bc.b)
            d3 = self.rattacher(bc.b)
            for d in (bc.d, d2, d3):                                                                  # le devis d'origine et chaque devis rattaché
                for m in self.SORTIES:
                    with self.subTest(bc=etat, devis=d, sortie=m):
                        self.refuse_inv("INV-175", f"UPDATE devis SET {m} WHERE id=?", d)
            self.assertEqual(self.tous("SELECT statut FROM devis WHERE id IN (?, ?, ?)", bc.d, d2, d3), [("accepte",)] * 3)

    def test_INV_175_un_bc_annule_libere_chacun_de_ses_devis_sans_cascade(self):
        bc = self.bc_en_etat("en_cours")
        d2, d3 = self.rattacher(bc.b), self.rattacher(bc.b)
        self.annuler_bc(bc.b)
        self.assertEqual(self.tous("SELECT statut FROM devis WHERE id IN (?, ?, ?) ORDER BY id", bc.d, d2, d3), [("accepte",)] * 3)   # aucune cascade
        self.assertEqual(self.tous("SELECT cancelled_at IS NULL FROM devis WHERE id IN (?, ?, ?)", bc.d, d2, d3), [(1,)] * 3)
        for d in (bc.d, d2, d3):
            for m in self.SORTIES:
                with self.subTest(devis=d, sortie=m):
                    self.permis(f"UPDATE devis SET {m} WHERE id=?", d)

    def test_INV_175_un_bc_annule_gele_libere_ses_devis_gele_seul_l_annulation_reste_possible(self):
        bc = self.bc_en_etat("annule_gele")
        d2 = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.assertEqual(self.un("SELECT frozen_at IS NOT NULL FROM devis WHERE id=?", bc.d)[0], 1)
        self.permis("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", TS, bc.d)
        self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", d2)[0], "accepte")

    def test_INV_175_la_garde_est_par_devis_un_devis_d_un_bc_annule_est_libre_pas_celui_d_un_autre_bc(self):
        b1, b2 = self.bc_en_etat("en_cours"), self.bc_en_etat("en_cours")
        self.annuler_bc(b1.b)
        self.permis("UPDATE devis SET statut='en_attente' WHERE id=?", b1.d)
        self.refuse_inv("INV-175", "UPDATE devis SET statut='en_attente' WHERE id=?", b2.d)
        # un devis du BC annulé rattaché avant l'annulation est libre, celui d'un BC vivant ne l'est pas, même s'ils partagent le client
        c = self.client_du_bc(b2.b)
        d3 = self.rattacher(b2.b)
        self.refuse_inv("INV-175", "UPDATE devis SET statut='en_attente' WHERE id=?", d3)
        self.assertEqual(self.client_du_bc(b2.b), c)

    def test_INV_175_un_devis_accepte_sans_bc_est_libre_et_les_autres_colonnes_aussi(self):
        d = self.devis_accepte()
        self.permis("UPDATE devis SET statut='en_attente' WHERE id=?", d)
        bc = self.bc_en_etat("en_cours")
        self.permis("UPDATE devis SET updated_at=? WHERE id=?", TS2, bc.d)                            # pas de changement de statut
        self.permis("UPDATE devis SET statut='accepte' WHERE id=?", bc.d)                             # statut inchangé
        self.refuse_inv("INV-181", "UPDATE devis SET total_ht='40.00' WHERE id=?", bc.d)              # contenu verrouillé (005a)

    def test_INV_175_la_garde_ne_depend_ni_de_devis_id_ni_du_rang(self):
        """Le devis de rang quelconque est gardé : la lecture passe par bc_devis, plus par bons_commande.devis_id (supprimé)."""
        cl = self.client()
        b = self.creer_bc(self.devis_accepte(client_id=cl), lignes=False, rang=42)
        d = self.devis_accepte(client_id=cl)
        self.lier(b, d, 3)
        self.refuse_inv("INV-175", "UPDATE devis SET statut='en_attente' WHERE id=?", d)
        self.refuse_inv("INV-175", "UPDATE devis SET statut='en_attente' WHERE id=(SELECT devis_id FROM bc_devis WHERE rang=42)")


class MultiDevis(Base):
    """BC 1 <- N devis : chaque devis garde son identité ; lignes et garanties de tous les devis dans le même BC."""

    def test_INV_187_un_bc_avec_un_seul_devis(self):
        bc = self.bc_en_etat("en_cours")
        self.assertEqual(self.tous("SELECT devis_id, rang FROM bc_devis WHERE bc_id=?", bc.b), [(bc.d, 1)])
        self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)

    def test_INV_187_un_bc_avec_plusieurs_devis_distincts_conservant_leur_identite(self):
        bc = self.bc_en_etat("en_cours")
        avant = self.un(f"SELECT {','.join(COLONNES_DEVIS)} FROM devis WHERE id=?", bc.d)
        d2 = self.rattacher(bc.b)
        d3 = self.rattacher(bc.b)
        devis = (bc.d, d2, d3)
        self.assertEqual(self.tous("SELECT devis_id, rang FROM bc_devis WHERE bc_id=? ORDER BY rang", bc.b), [(d, i + 1) for i, d in enumerate(devis)])
        numeros = [self.un("SELECT numero FROM devis WHERE id=?", d)[0] for d in devis]
        self.assertEqual(len(set(numeros)), 3)
        self.assertTrue(all(re.match(r"^DEV-\d{5}$", n[:9]) for n in numeros))
        for d in devis:
            self.assertEqual(self.un("SELECT statut, client_id, revision_en_cours FROM devis WHERE id=?", d), ("accepte", self.client_du_bc(bc.b), 0))
        self.assertEqual(self.un(f"SELECT {','.join(COLONNES_DEVIS)} FROM devis WHERE id=?", bc.d), avant)                      # identité intacte
        # lignes : 2 par devis, rattachées à leur devis par devis_ligne_id, ordre continu et sans doublon
        self.assertEqual(self.tous("SELECT dl.devis_id, count(*) FROM bc_lignes bl JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id "
                                   "WHERE bl.bc_id=? GROUP BY dl.devis_id ORDER BY dl.devis_id", bc.b), [(d, 2) for d in devis])
        self.assertEqual(self.tous("SELECT ordre FROM bc_lignes WHERE bc_id=? ORDER BY ordre", bc.b), [(i,) for i in range(1, 7)])
        # garanties : 2 (ligne 1 de chaque devis) par devis
        self.assertEqual(self.un("SELECT count(*) FROM bc_ligne_garanties g JOIN bc_lignes l ON l.id=g.ligne_id WHERE l.bc_id=?", bc.b)[0], 6)
        # contractuel = somme des totaux des devis (maintenue par le service, contrôlée par CK-13/CK-14)
        self.assertEqual(self.un("SELECT montant_contractuel_ht FROM bons_commande WHERE id=?", bc.b)[0], "94.50")
        self.assertEqual(self.un("SELECT printf('%.2f', sum(CAST(d.total_ht AS REAL))) FROM bc_devis l JOIN devis d ON d.id=l.devis_id WHERE l.bc_id=?", bc.b)[0], "94.50")

    def test_INV_187_chaque_devis_conserve_sa_remise_et_son_acompte_le_bc_n_en_porte_plus(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.devis_sup(bc, remise_type="montant", remise_valeur="3.00", acompte_type="pourcentage", acompte_valeur="30.00")
        d3 = self.devis_sup(bc, remise_type="aucune", remise_valeur=None, acompte_type="aucun", acompte_valeur=None)
        self.rattacher(bc.b, d2)
        self.rattacher(bc.b, d3)
        self.assertEqual(self.tous("SELECT d.id, remise_type, remise_valeur, acompte_type, acompte_valeur FROM bc_devis l JOIN devis d ON d.id=l.devis_id "
                                   "WHERE l.bc_id=? ORDER BY l.rang", bc.b),
                         [(bc.d, "pourcentage", "10.00", "montant", "5.00"), (d2, "montant", "3.00", "pourcentage", "30.00"), (d3, "aucune", None, "aucun", None)])
        self.assertTrue({"remise_type", "acompte_type"}.isdisjoint(colonnes(self.db, "bons_commande")))

    def test_INV_176_INTERPRETATION_le_bc_garde_les_snapshots_et_la_date_du_devis_d_origine(self):
        """PT-6/PT-7 : date_acceptation du BC = devis d'origine, chaque devis rattaché garde la sienne ; le BC garde ses snapshots (ceux de sa
        création), même si le devis rattaché porte un autre chantier."""
        bc = self.bc_en_etat("en_cours")
        avant = self.un("SELECT date_acceptation, client_snapshot, entreprise_snapshot, chantier_snapshot, chantier_snapshot_version FROM bons_commande WHERE id=?", bc.b)
        d2 = self.devis_sup(bc, chantier_snapshot='{"chantier": "Autre chantier"}', chantier_snapshot_version=9)
        self.rattacher(bc.b, d2)
        self.assertEqual(self.un("SELECT date_acceptation, client_snapshot, entreprise_snapshot, chantier_snapshot, chantier_snapshot_version FROM bons_commande WHERE id=?", bc.b), avant)
        self.assertEqual(self.un("SELECT chantier_snapshot, chantier_snapshot_version FROM devis WHERE id=?", d2), ('{"chantier": "Autre chantier"}', 9))
        # la date d'acceptation du devis rattaché peut différer de celle du BC
        d3 = self.devis_direct("accepte", client_id=self.client_du_bc(bc.b), date_acceptation="2026-05-01")
        self.lier(bc.b, d3)
        self.assertEqual(self.un("SELECT date_acceptation FROM devis WHERE id=?", d3)[0], "2026-05-01")
        self.assertEqual(self.un("SELECT date_acceptation FROM bons_commande WHERE id=?", bc.b)[0], avant[0])

    def test_INV_36_le_rattachement_n_autorise_pas_a_modifier_le_contenu_d_un_devis_deja_integre(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.rattacher(bc.b)
        for d in (bc.d, d2):
            with self.subTest(devis=d):
                self.refuse_inv("INV-181", "UPDATE devis SET total_ht='99.00' WHERE id=?", d)
                self.refuse_inv("INV-181", "UPDATE devis SET objet='autre' WHERE id=?", d)
                self.refuse_inv("INV-181", "UPDATE devis SET remise_type='montant', remise_valeur='1.00' WHERE id=?", d)
                self.refuse_inv("INV-181", "UPDATE devis SET acompte_type='aucun', acompte_valeur=NULL WHERE id=?", d)
                self.refuse_inv("INV-181", "UPDATE devis SET chantier_snapshot='{}' WHERE id=?", d)
                self.refuse_inv("INV-180|INV-181", "UPDATE devis SET client_id=? WHERE id=?", self.client(), d)
                l = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d)[0]
                self.refuse_inv("INV-36", "UPDATE devis_lignes SET designation='x' WHERE id=?", l)
                self.refuse_inv("INV-36", "DELETE FROM devis_lignes WHERE id=?", l)
                self.refuse_inv("INV-36", "INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                                "type_prestation, total_ht) VALUES (?, 9, 'N', '1', 'u', '1.5', 'aucune', 'pose', '1.50')", d)
                self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET garantie_type='parfait_achevement' WHERE ligne_id=?", l)
                self.refuse_inv("INV-36", "INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", l)
                self.refuse_inv("INV-36", "DELETE FROM devis_ligne_garanties WHERE ligne_id=?", l)

    def test_INV_187_ajout_d_un_devis_apres_acompte_et_situations_et_avant_solde(self):
        """Un acompte ou des situations déjà émis ne ferment pas le BC (INV-187) : leurs caches évoluent, le rattachement reste possible."""
        bc = self.bc_en_etat("gele")
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht='9.45', avancement='30.00', updated_at=? WHERE id=?", (TS2, bc.b))
        d = self.rattacher(bc.b)
        self.assertEqual(self.un("SELECT montant_contractuel_ht, montant_deja_facture_ht, avancement FROM bons_commande WHERE id=?", bc.b),
                         ("63.00", "9.45", "30.00"))
        self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 4)
        self.assertEqual(self.un("SELECT rang FROM bc_devis WHERE devis_id=?", d)[0], 2)

    def test_INV_175_les_lignes_ne_peuvent_etre_copiees_qu_apres_le_lien(self):
        bc = self.bc_en_etat("en_cours")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        dl = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d)[0]
        self.refuse_inv("INV-175", "INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                        "type_prestation, total_ht) VALUES (?, ?, 3, 'L', '1', 'u', '1.5', 'aucune', 'pose', '1.50')", bc.b, dl)
        self.lier(bc.b, d)
        self.ligne_bc(bc.b, dl, 3)

    def test_INV_175_le_numero_d_ordre_continue_apres_les_lignes_existantes(self):
        """§4.19 ligne 18 : UNIQUE(bc_id, ordre) n'empêche pas le multi-devis, le service numérote à la suite ; recopier l'ordre du devis échoue."""
        bc = self.bc_en_etat("en_cours")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.lier(bc.b, d)
        dl = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d)[0]
        self.refuse_check("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                          "type_prestation, total_ht) VALUES (?, ?, 1, 'L', '1', 'u', '1.5', 'aucune', 'pose', '1.50')", bc.b, dl)
        self.ligne_bc(bc.b, dl, 3)

    def test_T46_rattachement_atomique_un_echec_au_milieu_annule_le_lien_les_lignes_et_le_montant(self):
        bc = self.bc_en_etat("en_cours")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        avant = tout(self.db)
        self.db.execute("SAVEPOINT rattachement")
        with self.assertRaises(sqlite3.IntegrityError):
            self.lier(bc.b, d)
            self.copier_lignes(bc.b, d)
            self.db.execute("UPDATE bons_commande SET montant_contractuel_ht='94.50' WHERE id=?", (bc.b,))
            self.copier_lignes(bc.b, d)                                                                # deuxième copie : UNIQUE(devis_ligne_id)
        self.db.execute("ROLLBACK TO rattachement")
        self.db.execute("RELEASE rattachement")
        self.assertEqual(tout(self.db), avant)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE devis_id=?", d)[0], 0)
        self.assertEqual(self.un("SELECT montant_contractuel_ht FROM bons_commande WHERE id=?", bc.b)[0], "31.50")
        self.rattacher(bc.b, d)                                                                          # le rejeu correct réussit

    def test_T46_deux_bc_du_meme_client_gardent_chacun_leurs_devis(self):
        cl = self.client()
        b1 = self.creer_bc(self.devis_accepte(client_id=cl))
        b2 = self.creer_bc(self.devis_accepte(client_id=cl))
        d = self.rattacher(b1)
        self.assertEqual(self.tous("SELECT bc_id FROM bc_devis WHERE devis_id=?", d), [(b1,)])
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE bc_id=?", b2)[0], 1)
        self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", b1)[0], 4)
        self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", b2)[0], 2)

    def test_T46_numeros_de_devis_toujours_uniques_un_devis_supplementaire_a_son_propre_numero(self):
        bc = self.bc_en_etat("en_cours")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        numero = self.un("SELECT numero FROM devis WHERE id=?", d)[0]
        self.assertNotEqual(numero, self.un("SELECT numero FROM devis WHERE id=?", bc.d)[0])
        self.refuse_inv("INV-23", "UPDATE devis SET numero='DEV-09999-26' WHERE id=?", d)


class ContratBC(Base):
    """Contenu contractuel du BC (Q4, INV-186) : immuable dès la création, hors montant contractuel, caches, dates de début et fin, annulation.
    Triggers : tr_01, tr_12_contrat, tr_12_annule, tr_14, tr_17, tr_19 (+ tr_96)."""

    COMMUNES = ("date_debut='2026-11-01'", "date_fin='2026-11-30'", "date_debut='2026-11-01', date_fin='2026-11-30'",
                "montant_contractuel_ht='99.00'", "montant_deja_facture_ht='10.00'", "updated_at='%s'" % TS2,
                "statut='annule', cancelled_at='%s', motif_annulation='Client renonce', completed_at=NULL, date_100_facture=NULL" % TS)
    MODIFS_PAR_ETAT = {
        "en_cours": COMMUNES + ("avancement='10.00'", "frozen_at='%s'" % TS),
        "gele": COMMUNES + ("avancement='10.00'", "date_100_facture='2026-10-02', avancement='100.00'",
                            "statut='termine', completed_at='%s', date_100_facture='2026-10-02', avancement='100.00'" % TS),
        "termine": COMMUNES + ("avancement='100.00'",
                               "statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='60.00'")}

    def test_T46_toutes_les_colonnes_de_bons_commande_ont_une_valeur_de_test(self):
        self.assertEqual(colonnes(self.db, "bons_commande"), COLONNES_BC)
        self.assertEqual(sorted(IMMUABLES_BC + MODIFIABLES_BC), sorted(COLONNES_BC))
        bc = self.bc_en_etat("gele")
        for col, ancienne in zip(COLONNES_BC, self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)):
            autre_valeur_bc(col, ancienne, 1)

    def test_INV_23_numero_et_date_creation_du_bc_immuables_dans_chaque_etat(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET date_creation='2026-10-03' WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero=NULL WHERE id=?", bc.b)

    def test_INV_186_le_contenu_contractuel_est_immuable_colonne_par_colonne_des_la_creation(self):
        """Q4 : même un BC en_cours (004 le laissait libre) ne peut plus changer ses snapshots, son client, sa date d'acceptation ni son origine."""
        autre = self.client()
        for etat in ETATS_BC_NON_ANNULES:
            bc = self.bc_en_etat(etat)
            ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
            for col, ancienne in zip(COLONNES_BC, ligne):
                if col not in IMMUABLES_BC:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-23|INV-186", f"UPDATE bons_commande SET {col}=? WHERE id=?", autre_valeur_bc(col, ancienne, autre), bc.b)
            self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), ligne)

    def test_INV_186_une_modification_melangee_d_une_colonne_libre_et_d_une_colonne_verrouillee_est_refusee_en_entier(self):
        autre = self.client()
        for etat in ETATS_BC_NON_ANNULES:
            bc = self.bc_en_etat(etat)
            avant = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
            for m in ("avancement='20.00', client_id=%d" % autre, "montant_contractuel_ht='1.00', client_snapshot='{}'",
                      "date_debut='2026-11-01', date_acceptation='2026-04-01'", "date_fin='2026-11-02', origine='import'",
                      "updated_at='%s', chantier_snapshot='{}'" % TS2, "montant_contractuel_ht='1.00', legacy_numero='X'"):
                with self.subTest(etat=etat, melange=m):
                    self.refuse(f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)
            self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), avant)

    def test_INV_186_les_colonnes_libres_restent_modifiables_dans_chaque_etat_non_annule(self):
        for etat in ETATS_BC_NON_ANNULES:
            bc = self.bc_en_etat(etat)
            for m in self.MODIFS_PAR_ETAT[etat]:
                with self.subTest(etat=etat, modif=m):
                    self.permis(f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)

    def test_INV_186_le_montant_contractuel_reste_modifiable_meme_gele_ou_termine(self):
        """Le rattachement d'un devis augmente le contractuel d'un BC gelé (Q-B, 004 le refusait) : le montant n'est plus un champ verrouillé."""
        for etat in ETATS_BC_NON_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.db.execute("UPDATE bons_commande SET montant_contractuel_ht='63.00' WHERE id=?", (bc.b,))
                self.assertEqual(self.un("SELECT montant_contractuel_ht FROM bons_commande WHERE id=?", bc.b)[0], "63.00")

    def test_INV_186_INTERPRETATION_le_gel_ne_ferme_plus_rien_dans_le_contenu_du_bc(self):
        """Q-B : frozen_at du BC n'est plus qu'un marqueur irréversible (INV-34) ; geler un BC ne change pas ce qu'on peut y modifier."""
        non_gele, gele = self.bc_en_etat("en_cours"), self.bc_en_etat("gele")
        for bc in (non_gele, gele):
            for m in self.COMMUNES + ("avancement='10.00'",):
                with self.subTest(bc=bc.b, modif=m):
                    self.permis(f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)
            self.refuse_inv("INV-186", "UPDATE bons_commande SET client_snapshot='{}' WHERE id=?", bc.b)

    def test_INV_36_cycle_de_statut_en_cours_termine_en_cours_annule(self):
        bc = self.bc_en_etat("gele")
        self.terminer_bc(bc.b)
        self.assertEqual(self.un("SELECT statut, completed_at IS NOT NULL FROM bons_commande WHERE id=?", bc.b), ("termine", 1))
        self.db.execute("UPDATE bons_commande SET statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='60.00', "
                        "montant_deja_facture_ht='18.90' WHERE id=?", (bc.b,))
        self.annuler_bc(bc.b)
        self.assertEqual(self.un("SELECT statut, frozen_at IS NOT NULL, cancelled_at IS NOT NULL FROM bons_commande WHERE id=?", bc.b), ("annule", 1, 1))

    def test_INV_173_bc_annule_terminal_colonne_par_colonne(self):
        autre = self.client()
        for etat in ETATS_BC_ANNULES:
            bc = self.bc_en_etat(etat)
            ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
            for col, ancienne in zip(COLONNES_BC, ligne):
                if col in COLONNES_ANNULE_MODIFIABLES:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-23|INV-34|INV-173", f"UPDATE bons_commande SET {col}=? WHERE id=?",
                                    autre_valeur_bc(col, ancienne, autre), bc.b)
            self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), ligne)
            self.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (TS2, bc.b))
            for m in ("statut='en_cours', cancelled_at=NULL, motif_annulation=NULL", "cancelled_at=NULL", "motif_annulation='Autre'",
                      "date_debut='2026-11-01'", "montant_deja_facture_ht='1.00'", "montant_contractuel_ht='99.00'"):
                with self.subTest(etat=etat, reouverture=m):
                    self.refuse_inv("INV-173", f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)

    def test_INV_173_un_bc_annule_ne_change_pas_de_client(self):
        for etat in ETATS_BC_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-173", "UPDATE bons_commande SET client_id=?, updated_at=? WHERE id=?", self.client(), TS2, bc.b)

    def test_INV_34_frozen_at_du_bc_ne_revient_jamais_a_null(self):
        bc = self.bc_en_etat("en_cours")
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, bc.b))
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc.b)
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc.b)
        self.db.execute("UPDATE bons_commande SET frozen_at=frozen_at, updated_at=? WHERE id=?", (TS2, bc.b))
        bc2 = self.bc_en_etat("annule")
        self.refuse_inv("INV-173", "UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc2.b)         # un BC annulé ne se gèle pas

    def test_INV_40_etat_de_naissance_du_bc(self):
        for mod in ({"montant_deja_facture_ht": "5.00"}, {"avancement": "5.00"}, {"frozen_at": TS},
                    {"date_100_facture": "2026-10-02"}, {"motif_annulation": "m"}):
            with self.subTest(mod=mod):
                d = self.devis_accepte()
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-40"):
                    self.creer_bc(d, lignes=False, **mod)
        self.creer_bc(self.devis_accepte(), lignes=True)

    def test_INV_40_le_statut_de_naissance_est_en_cours(self):
        for statut, extra in (("termine", {"completed_at": TS}), ("annule", {"cancelled_at": TS, "motif_annulation": "m"})):
            with self.subTest(statut=statut):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.creer_bc(self.devis_accepte(), lignes=False, statut=statut, **extra)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-40"):
            self.creer_bc(self.devis_accepte(), lignes=False, statut="en_cours", frozen_at=TS)

    def test_INV_40_INTERPRETATION_C5_le_bc_naissant_ne_lit_plus_le_devis_le_lien_porte_les_controles(self):
        """TR-17 ne peut pas lire le devis (le lien n'existe pas encore à l'INSERT du BC) : un BC sans lien est accepté par le schéma, et le
        premier lien (TR-99) refuse devis non accepté ou d'un autre client. La création d'un BC reste atomique côté service (savepoint)."""
        d = self.devis_en_etat("en_attente")
        self.db.execute("SAVEPOINT s")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-40"):
            self.creer_bc(d.d, lignes=False)
        self.db.execute("ROLLBACK TO s")
        self.db.execute("RELEASE s")
        self.assertEqual(self.un("SELECT count(*) FROM bons_commande")[0], 0)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis")[0], 0)
        autre = self.devis_accepte()
        self.db.execute("SAVEPOINT s")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-48"):
            self.creer_bc(autre, lignes=False, client_id=self.client())
        self.db.execute("ROLLBACK TO s")
        self.db.execute("RELEASE s")
        self.assertEqual(self.un("SELECT count(*) FROM bons_commande")[0], 0)
        b = self.creer_bc(self.devis_accepte(), lignes=False, lier=False)                                   # BC sans lien : le schéma l'accepte
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE bc_id=?", b)[0], 0)

    def test_INV_174_un_bc_ne_se_supprime_jamais(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", bc.b)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande")
        bc = self.bc_en_etat("en_cours")
        numero = self.un("SELECT numero FROM bons_commande WHERE id=?", bc.b)[0]
        self.refuse_inv("INV-174", "INSERT OR REPLACE INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, "
                        "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                        "date_acceptation, montant_contractuel_ht) SELECT ?, client_id, client_snapshot, 1, entreprise_snapshot, 1, "
                        "chantier_snapshot, 1, '2026-10-02', '2026-03-12', total_ht FROM devis WHERE id=?", numero, bc.d)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE bc_id=?", bc.b)[0], 1)

    def test_INV_188_aucune_cascade_l_annulation_du_bc_ne_modifie_ni_devis_ni_liens_ni_lignes(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.rattacher(bc.b)
        avant = {t: self.tous(f"SELECT * FROM {t} ORDER BY id") for t in ("devis", "devis_lignes", "bc_devis", "bc_lignes", "bc_ligne_garanties",
                                                                          "devis_ligne_garanties", "devis_revisions")}
        self.annuler_bc(bc.b)
        for t, lignes in avant.items():
            self.assertEqual(self.tous(f"SELECT * FROM {t} ORDER BY id"), lignes, t)
        self.assertEqual(self.tous("SELECT statut FROM devis WHERE id IN (?, ?) ORDER BY id", bc.d, d2), [("accepte",), ("accepte",)])

    def test_INV_95_96_protection_de_numerotation_sequences(self):
        self.un(ATTRIBUER, "BCD", 26)
        self.un(ATTRIBUER, "BCD", 26)
        self.refuse_inv("ne se supprime jamais", "DELETE FROM numerotation_sequences WHERE type_objet='BCD'")
        self.refuse_inv("ne se supprime jamais", "DELETE FROM numerotation_sequences")
        self.refuse_inv("ne se supprime jamais", "INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 9)")
        self.refuse_inv("INV-", "UPDATE numerotation_sequences SET dernier_numero=1 WHERE type_objet='BCD'")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD'")[0], 2)

    def test_T46_numero_du_bc_unique_et_au_format(self):
        bc = self.bc_en_etat("en_cours")
        numero = self.un("SELECT numero FROM bons_commande WHERE id=?", bc.b)[0]
        self.assertRegex(numero, r"^BCD-\d{5}-\d{2}$")
        d = self.devis_accepte()
        self.refuse_check("INSERT INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                          "montant_contractuel_ht) SELECT ?, client_id, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, "
                          "'2026-10-02', '2026-03-12', total_ht FROM devis WHERE id=?", numero, d)
        self.refuse_check("INSERT INTO bons_commande (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                          "montant_contractuel_ht) SELECT 'BCD-1', client_id, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, "
                          "'2026-10-02', '2026-03-12', total_ht FROM devis WHERE id=?", d)

    def test_T46_triggers_001_et_005_toujours_actifs(self):
        f = self.fournisseur()
        cat = self.db.execute("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'M', 1, 1)").lastrowid
        self.db.execute("INSERT INTO depenses (numero, fournisseur_id, date_depense, montant, categorie_id, description) "
                        "VALUES ('DEP-00001-26', ?, '2026-10-02', '1.00', ?, 'x')", (f, cat))
        i = self.un("SELECT id FROM depenses")[0]
        self.refuse_inv("INV-", "UPDATE depenses SET numero='DEP-00002-26' WHERE id=?", i)
        self.refuse_inv("INV-", "DELETE FROM depenses WHERE id=?", i)
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation='Erreur' WHERE id=?", (TS2, i))
        self.refuse_inv("INV-", "UPDATE depenses SET montant='2.00' WHERE id=?", i)
        self.refuse_inv("INV-", "DELETE FROM depenses WHERE id=?", i)
        self.fournisseur(code="FOU-0900")
        self.refuse_inv("INV-183", "DELETE FROM fournisseurs WHERE id=?", f)


class LignesEtGaranties(Base):
    """bc_lignes et bc_ligne_garanties (TR-13) : INSERT tant que le BC n'est pas annulé (Q-B) et, pour une ligne, depuis un devis rattaché ;
    UPDATE et DELETE toujours refusés (INV-186) ; PT-5 : garanties en RESTRICT."""

    def _ligne_sql(self, nb=None):
        return ("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, type_prestation, "
                "total_ht) VALUES (?, ?, ?, 'L', '1', 'u', '1.5', 'aucune', 'pose', '1.50')")

    def test_INV_175_une_ligne_se_copie_dans_chaque_etat_non_annule_y_compris_gele_et_termine(self):
        """Q-B : le gel du BC ne ferme plus l'ajout de lignes (004 le refusait), seule l'annulation le ferme."""
        for etat in ETATS_BC_NON_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat, dl3=True)
                self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)
                self.ligne_bc(bc.b, bc.dl3, 3)
                self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 3)

    def test_INV_173_aucune_ligne_ni_garantie_ne_s_ajoute_a_un_bc_annule(self):
        for etat in ETATS_BC_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat, dl3=True)
                self.refuse_inv("INV-173", self._ligne_sql(), bc.b, bc.dl3, 3)
                self.refuse_inv("INV-173", "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", bc.bl1)
                self.refuse_inv("INV-173", "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", bc.bl2)
                self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)

    def test_INV_173_un_bc_annule_apres_rattachement_refuse_les_lignes_du_devis_rattache(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.rattacher(bc.b, lignes=False)
        dl = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d2)[0]
        self.annuler_bc(bc.b)
        self.refuse_inv("INV-173", self._ligne_sql(), bc.b, dl, 9)

    def test_INV_175_une_ligne_doit_venir_d_un_devis_rattache_au_bc(self):
        bc = self.bc_en_etat("en_cours")
        cl = self.client_du_bc(bc.b)
        libre = self.devis_accepte(client_id=cl)                                                        # même client, non rattaché
        autre_client = self.devis_accepte()
        sur_autre_bc = self.bc_en_etat("en_cours")
        for nom, d in (("devis non rattaché", libre), ("autre client", autre_client), ("devis d'un autre BC", sur_autre_bc.d)):
            with self.subTest(source=nom):
                dl = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d)[0]
                self.refuse_inv("INV-175", self._ligne_sql(), bc.b, dl, 9)
        self.lier(bc.b, libre)                                                                          # une fois rattaché, la ligne est permise
        dl = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", libre)[0]
        self.db.execute(self._ligne_sql(), (bc.b, dl, 9))

    def test_INV_175_la_ligne_d_un_devis_rattache_a_deux_bc_distincts_n_existe_pas(self):
        """Un devis n'appartient qu'à un BC (UNIQUE(devis_id)) : ses lignes ne peuvent donc entrer que dans ce BC."""
        b1, b2 = self.bc_en_etat("en_cours"), self.bc_en_etat("en_cours")
        dl = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", b1.d)[0]
        self.refuse_inv("INV-175", self._ligne_sql(), b2.b, dl, 9)

    def test_T46_unicite_devis_ligne_id_et_ordre_par_bc(self):
        bc = self.bc_en_etat("en_cours", dl3=True)
        self.refuse_check(self._ligne_sql(), bc.b, bc.dl1, 3)                                           # même ligne de devis deux fois
        self.refuse_check(self._ligne_sql(), bc.b, bc.dl3, 1)                                           # ordre déjà pris
        self.ligne_bc(bc.b, bc.dl3, 3)

    def test_INV_186_une_ligne_de_bc_ne_se_modifie_jamais_colonne_par_colonne_dans_chaque_etat(self):
        for etat in ETATS_BC:
            bc = self.bc_en_etat(etat)
            for col in COLONNES_BC_LIGNES:
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-186", f"UPDATE bc_lignes SET {col}={col} WHERE id=?", bc.bl1)
            self.refuse_inv("INV-186", "UPDATE bc_lignes SET designation='x', quantite='9'")
            self.refuse_inv("INV-186", "UPDATE bc_lignes SET bc_id=? WHERE id=?", self.bc_en_etat("en_cours").b, bc.bl1)
            self.assertEqual(self.un("SELECT designation FROM bc_lignes WHERE id=?", bc.bl1)[0], "Pose prise")

    def test_INV_186_une_ligne_de_bc_ne_se_supprime_jamais_ni_par_replace(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-186", "DELETE FROM bc_lignes WHERE id=?", bc.bl2)
                self.refuse_inv("INV-186", "DELETE FROM bc_lignes WHERE bc_id=?", bc.b)
                inv = "INV-173" if etat in ETATS_BC_ANNULES else "INV-186"
                self.refuse_inv(inv, "INSERT OR REPLACE INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, "
                                "prix_unitaire_ht, remise_type, type_prestation, total_ht) VALUES (?, ?, 1, 'L', '1', 'u', '1.5', 'aucune', 'pose', '1.50')",
                                bc.b, bc.dl2)                                                            # remplace sur devis_ligne_id / (bc_id, ordre)
                self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)
        self.refuse_inv("INV-186", "DELETE FROM bc_lignes")

    def test_INV_173_les_garanties_se_copient_dans_chaque_etat_non_annule(self):
        for etat in ETATS_BC_NON_ANNULES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (bc.bl2,))
                self.assertEqual(self.un("SELECT count(*) FROM bc_ligne_garanties WHERE ligne_id=?", bc.bl2)[0], 1)

    def test_INV_186_INTERPRETATION_le_schema_ne_relie_pas_une_garantie_de_bc_a_celle_du_devis(self):
        """La copie des garanties du devis est une règle de service (comme les lignes, §4.19) : le schéma accepte une garantie de BC absente du devis."""
        bc = self.bc_en_etat("en_cours")
        self.assertEqual(self.un("SELECT count(*) FROM devis_ligne_garanties WHERE ligne_id=? AND garantie_type='parfait_achevement'", bc.dl1)[0], 0)
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (bc.bl1,))

    def test_T46_unicite_garantie_par_ligne_et_type_valide(self):
        bc = self.bc_en_etat("en_cours")
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", bc.bl1)
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'inconnue')", bc.bl2)
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (999, 'parfait_achevement')")
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (NULL, 'parfait_achevement')")

    def test_INV_186_une_garantie_de_bc_ne_se_modifie_ni_ne_se_supprime_jamais(self):
        for etat in ETATS_BC:
            bc = self.bc_en_etat(etat)
            for col in colonnes(self.db, "bc_ligne_garanties"):
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-186", f"UPDATE bc_ligne_garanties SET {col}={col} WHERE id=?", bc.bg1)
            with self.subTest(etat=etat, op="delete"):
                self.refuse_inv("INV-186", "DELETE FROM bc_ligne_garanties WHERE id=?", bc.bg1)
                self.refuse_inv("INV-186", "DELETE FROM bc_ligne_garanties WHERE ligne_id=?", bc.bl1)
                self.refuse_inv("INV-186", "UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", bc.bl2, bc.bg1)
                inv = "INV-173" if etat in ETATS_BC_ANNULES else "INV-186"
                self.refuse_inv(inv, "INSERT OR REPLACE INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", bc.bl1)
        self.refuse_inv("INV-186", "DELETE FROM bc_ligne_garanties")

    def test_PT5_la_suppression_d_une_ligne_de_bc_n_emporte_plus_ses_garanties(self):
        """PT-5 : bc_ligne_garanties.ligne_id est en RESTRICT au rang 7 (CASCADE au rang 6). Preuve par FK : triggers retirés."""
        t6 = base6_peuplee()
        for nom in sorted(noms(t6.db, "trigger")):
            t6.db.execute(f"DROP TRIGGER {nom}")
        bl = t6.un("SELECT ligne_id FROM bc_ligne_garanties LIMIT 1")[0]
        t6.db.execute("DELETE FROM bc_lignes WHERE id=?", (bl,))                                       # rang 6 : emporte les garanties
        self.assertEqual(t6.un("SELECT count(*) FROM bc_ligne_garanties WHERE ligne_id=?", bl)[0], 0)
        bc = self.bc_en_etat("en_cours")
        for nom in sorted(noms(self.db, "trigger")):
            self.db.execute(f"DROP TRIGGER {nom}")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM bc_lignes WHERE id=?", (bc.bl1,))                             # rang 7 : refusé par la FK
        self.assertEqual(self.un("SELECT count(*) FROM bc_ligne_garanties WHERE ligne_id=?", bc.bl1)[0], 2)
        self.assertEqual(cles_etrangeres(self.db, "bc_ligne_garanties"), [("bc_lignes", "ligne_id", "id", "NO ACTION", "RESTRICT")])


class RevisionsEtDevisSupplementaires(Base):
    """Q17 : un devis supplémentaire est un travail en plus, pas une révision ; il garde son numéro, ses snapshots et sa propre version initiale."""

    def test_Q17_un_devis_supplementaire_a_son_numero_sa_version_initiale_et_aucune_revision(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.rattacher(bc.b)
        self.assertEqual(self.tous("SELECT revision, count(*) FROM devis_revisions WHERE devis_id IN (?, ?) GROUP BY devis_id", bc.d, d2),
                         [(None, 1), (None, 1)])
        self.assertEqual(self.tous("SELECT revision, revision_en_cours FROM devis WHERE id IN (?, ?) ORDER BY id", bc.d, d2), [(None, 0), (None, 0)])
        self.assertNotEqual(self.un("SELECT numero FROM devis WHERE id=?", d2)[0], self.un("SELECT numero FROM devis WHERE id=?", bc.d)[0])

    def test_Q17_rattacher_un_devis_n_ecrit_ni_revision_ni_snapshot(self):
        bc = self.bc_en_etat("gele")
        d2 = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        avant = self.tous("SELECT * FROM devis_revisions ORDER BY id")
        self.rattacher(bc.b, d2)
        self.assertEqual(self.tous("SELECT * FROM devis_revisions ORDER BY id"), avant)

    def test_INV_196_un_devis_rattache_ne_se_revise_plus(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.rattacher(bc.b)
        for d in (bc.d, d2):
            with self.subTest(devis=d):
                self.refuse_inv("INV-181|INV-196", "UPDATE devis SET revision_en_cours=1 WHERE id=?", d)
                self.refuse_inv("INV-181|INV-196", "UPDATE devis SET revision=1 WHERE id=?", d)
                self.refuse_inv("INV-196", "INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                                "VALUES (?, 1, 1, '{}', '1.00', ?)", d, TS)

    def test_INV_196_les_snapshots_des_devis_rattaches_restent_append_only(self):
        bc = self.bc_en_etat("en_cours")
        r = self.un("SELECT id FROM devis_revisions WHERE devis_id=?", bc.d)[0]
        self.refuse_inv("INV-196", "UPDATE devis_revisions SET contenu='{}' WHERE id=?", r)
        self.refuse_inv("INV-196", "DELETE FROM devis_revisions WHERE id=?", r)
        self.refuse_check("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                          "VALUES (?, NULL, 1, '{}', '1.00', ?)", bc.d, TS)                              # une seule version initiale par devis

    def test_Q17_un_devis_en_revision_ou_en_attente_ne_se_rattache_pas_une_fois_accepte_il_le_peut(self):
        bc = self.bc_en_etat("en_cours")
        cl = self.client_du_bc(bc.b)
        for etat in ("en_attente", "revision"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat, client_id=cl)
                self.refuse_inv("INV-40", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b, dv.d)
        dv = self.devis_en_etat("en_attente", client_id=cl)
        self.accepter(dv.d)
        self.lier(bc.b, dv.d)

    def test_Q17_les_revisions_d_un_devis_independant_ne_touchent_pas_le_bc(self):
        bc = self.bc_en_etat("en_cours")
        libre = self.devis_en_etat("revision", client_id=self.client_du_bc(bc.b))
        avant = (self.tous("SELECT * FROM bc_devis"), self.tous("SELECT * FROM bons_commande"), self.tous("SELECT * FROM bc_lignes"))
        self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                        "VALUES (?, 1, 1, '{}', '31.50', ?)", (libre.d, TS))
        self.db.execute("UPDATE devis SET revision=1, revision_en_cours=0 WHERE id=?", (libre.d,))
        self.assertEqual((self.tous("SELECT * FROM bc_devis"), self.tous("SELECT * FROM bons_commande"), self.tous("SELECT * FROM bc_lignes")), avant)
        self.accepter(libre.d)
        self.lier(bc.b, libre.d)
        self.assertEqual(self.un("SELECT revision FROM devis WHERE id=?", libre.d)[0], 1)

    def test_T46_pas_de_devis_origine_id_un_devis_supplementaire_n_a_aucun_lien_de_parente(self):
        """Décision par défaut du cadrage (C2) : devis_origine_id n'est pas créé ; le lien d'origine d'un BC est le rang de plus petite valeur."""
        for table in ("devis", "bons_commande", "bc_devis", "devis_revisions"):
            self.assertNotIn("devis_origine_id", colonnes(self.db, table))
        bc = self.bc_en_etat("en_cours")
        self.rattacher(bc.b)
        self.assertEqual(self.un("SELECT devis_id FROM bc_devis WHERE bc_id=? ORDER BY rang LIMIT 1", bc.b)[0], bc.d)


class Compatibilite(Base):
    """Rejeu sur le schéma reconstruit des garanties 003/004 qui portent sur les tables touchées : REPLACE, suppressions, mutation des clés
    parentes, FK, rollback, dépenses."""

    def test_INV_183_un_client_avec_bc_ne_se_supprime_ni_ne_change_de_cle(self):
        bc = self.bc_en_etat("en_cours")
        cl = self.client_du_bc(bc.b)
        self.refuse_inv("INV-183", "DELETE FROM clients WHERE id=?", cl)
        self.refuse_inv("INV-183", "INSERT OR REPLACE INTO clients (id, code, nom) VALUES (?, 'CLI-9999', 'X')", cl)
        self.refuse("UPDATE clients SET id=? WHERE id=?", cl + 1000, cl)
        self.assertEqual(self.un("SELECT client_id FROM bons_commande WHERE id=?", bc.b)[0], cl)

    def test_T46_cle_parente_du_bc_et_du_devis_non_mutable(self):
        bc = self.bc_en_etat("en_cours")
        for sql, args in (("UPDATE bons_commande SET id=? WHERE id=?", (bc.b + 1000, bc.b)),
                          ("UPDATE devis SET id=? WHERE id=?", (bc.d + 1000, bc.d)),
                          ("UPDATE bc_lignes SET id=? WHERE id=?", (bc.bl1 + 1000, bc.bl1)),
                          ("UPDATE devis_lignes SET id=? WHERE id=?", (bc.dl1 + 1000, bc.dl1)),
                          ("UPDATE bc_devis SET bc_id=? WHERE devis_id=?", (bc.b + 1000, bc.d))):
            with self.subTest(sql=sql):
                self.refuse(sql, *args)
        self.assertEqual(self.un("SELECT bc_id, devis_id FROM bc_devis WHERE devis_id=?", bc.d), (bc.b, bc.d))

    def test_T46_les_cles_parentes_sont_protegees_par_la_FK_meme_sans_trigger(self):
        """Avec les triggers retirés, la FK refuse seule la mutation de la clé d'un parent référencé (aucune action ON UPDATE)."""
        bc = self.bc_en_etat("en_cours")
        for nom in sorted(noms(self.db, "trigger")):
            self.db.execute(f"DROP TRIGGER {nom}")
        for sql, args in (("UPDATE bons_commande SET id=? WHERE id=?", (bc.b + 1000, bc.b)), ("UPDATE devis SET id=? WHERE id=?", (bc.d + 1000, bc.d)),
                          ("UPDATE bc_lignes SET id=? WHERE id=?", (bc.bl1 + 1000, bc.bl1))):
            with self.subTest(sql=sql):
                self.refuse(sql, *args)

    def test_INV_180_un_devis_rattache_ne_se_supprime_jamais(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.rattacher(bc.b)
        for d in (bc.d, d2):
            with self.subTest(devis=d):
                self.refuse_inv("INV-180", "DELETE FROM devis WHERE id=?", d)
                self.refuse_inv("INV-180", "INSERT OR REPLACE INTO devis (id, numero, client_id, client_snapshot, client_snapshot_version, "
                                "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                                "statut, total_ht) VALUES (?, NULL, ?, '{}', 1, '{}', 1, '{}', 1, '2026-03-10', 'brouillon', '0.00')",
                                d, self.client_du_bc(bc.b))
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis WHERE bc_id=?", bc.b)[0], 2)

    def test_INV_36_les_lignes_et_garanties_d_un_devis_rattache_restent_immuables(self):
        bc = self.bc_en_etat("en_cours")
        d2 = self.rattacher(bc.b)
        for d in (bc.d, d2):
            l = self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d)[0]
            g = self.un("SELECT id FROM devis_ligne_garanties WHERE ligne_id=? LIMIT 1", l)[0]
            with self.subTest(devis=d):
                self.refuse_inv("INV-36", "UPDATE devis_lignes SET designation='x' WHERE id=?", l)
                self.refuse_inv("INV-36", "DELETE FROM devis_lignes WHERE id=?", l)
                self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", g)
                self.refuse_inv("INV-36", "DELETE FROM devis_ligne_garanties WHERE id=?", g)

    def test_T46_un_parent_referencé_par_un_enfant_RESTRICT_ne_se_supprime_pas_meme_sans_trigger(self):
        bc = self.bc_en_etat("en_cours")
        cat = self.db.execute("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'M', 1, 1)").lastrowid
        f = self.fournisseur()
        self.db.execute("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
                        "VALUES ('DEP-00001-26', ?, ?, '2026-10-02', '12.50', ?, 'Achat')", (f, bc.b, cat))
        for nom in sorted(noms(self.db, "trigger")):
            self.db.execute(f"DROP TRIGGER {nom}")
        for sql, args in (("DELETE FROM bons_commande WHERE id=?", (bc.b,)), ("DELETE FROM devis WHERE id=?", (bc.d,)),
                          ("DELETE FROM clients WHERE id=?", (self.client_du_bc(bc.b),)), ("DELETE FROM devis_lignes WHERE id=?", (bc.dl1,)),
                          ("DELETE FROM bc_lignes WHERE id=?", (bc.bl1,)), ("DELETE FROM fournisseurs WHERE id=?", (f,))):
            with self.subTest(sql=sql):
                self.refuse(sql, *args)

    def test_T46_depenses_rattachees_a_un_bc_multi_devis(self):
        """005 : une dépense référence un BC (pas un devis) ; un BC à N devis reçoit des dépenses comme un BC à un devis, et reste non supprimable."""
        bc = self.bc_en_etat("gele")
        self.rattacher(bc.b)
        cat = self.db.execute("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'M', 1, 1)").lastrowid
        f = self.fournisseur()
        self.db.execute("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
                        "VALUES ('DEP-00001-26', ?, ?, '2026-10-02', '12.50', ?, 'Achat')", (f, bc.b, cat))
        self.assertEqual(self.un("SELECT count(*) FROM depenses WHERE bc_id=?", bc.b)[0], 1)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", bc.b)
        self.refuse_check("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-00002-26', ?, 999, '2026-10-02', '1.00', ?, 'x')", f, cat)

    def test_T46_rollback_de_la_creation_complete_d_un_bc_multi_devis_ne_laisse_aucune_trace(self):
        avant = tout(self.db)
        self.db.execute("BEGIN")
        bc = self.bc_en_etat("en_cours")
        self.rattacher(bc.b)
        self.annuler_bc(bc.b)
        self.assertEqual(self.un("SELECT count(*) FROM bc_devis")[0], 2)
        self.db.execute("ROLLBACK")
        self.assertEqual(tout(self.db), avant)                                                          # tables, sqlite_sequence, numérotation

    def test_T46_echec_d_une_transaction_au_milieu_du_rattachement_laisse_le_bc_intact(self):
        bc = self.bc_en_etat("en_cours")
        autre_client = self.devis_accepte()
        avant = tout(self.db)
        self.db.execute("BEGIN")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.lier(bc.b, d)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-48"):
            self.lier(bc.b, autre_client)
        self.db.execute("ROLLBACK")
        self.assertEqual(tout(self.db), avant)

    def test_T46_une_connexion_sans_recursive_triggers_perd_les_gardes_de_REPLACE_comme_en_003_et_004(self):
        db = migrer(recursive=False)
        t = Base()
        t.db, t._n = db, 0
        bc = t.bc_en_etat("en_cours")
        db.execute("INSERT OR REPLACE INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                   "type_prestation, total_ht) VALUES (?, ?, 2, 'REMPLACE', '1', 'u', '1.5', 'aucune', 'pose', '1.50')", (bc.b, bc.dl2))
        self.assertEqual(db.execute("SELECT designation FROM bc_lignes WHERE devis_ligne_id=?", (bc.dl2,)).fetchone()[0], "REMPLACE")

    def test_T46_aucune_table_ni_trigger_ne_reference_devis_id_de_bons_commande(self):
        for type_, nom, tbl, sql in objets(self.db):
            if sql and type_ in ("trigger", "view"):
                with self.subTest(objet=nom):
                    self.assertNotRegex(sql, r"\bb\.devis_id\b|\bbons_commande\.devis_id\b")
                    if tbl == "bons_commande":
                        self.assertNotIn("devis_id", sql)
        self.assertEqual(self.tous("SELECT name FROM sqlite_master WHERE type='view'"), [])


class Isolation(Base):
    """Chaque trigger touché par 005b refuse seul la violation qui lui est propre ; retiré, la violation passe (il est donc le garde) ;
    recréé à partir de son SQL, il la refuse de nouveau."""

    def prep_scenarios(self):
        """nom -> liste de (préparation(t) retournant l'action, motif du message)."""
        def s(*items):
            return list(items)

        def x(t, sql, *args):
            return lambda: t.db.execute(sql, args)
        sc = {}
        sc["tr_01_bons_commande_numero_immuable"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", bc.b)()), "INV-23"),
            (lambda t: (lambda bc=t.bc_en_etat("gele"): x(t, "UPDATE bons_commande SET date_creation='2026-10-03' WHERE id=?", bc.b)()), "INV-23"))
        sc["tr_12_bons_commande_contrat"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "UPDATE bons_commande SET client_snapshot='{}' WHERE id=?", bc.b)()), "INV-186"),
            (lambda t: (lambda bc=t.bc_en_etat("gele"), c=t.client(): x(t, "UPDATE bons_commande SET client_id=? WHERE id=?", c, bc.b)()), "INV-186"),
            (lambda t: (lambda bc=t.bc_en_etat("termine"): x(t, "UPDATE bons_commande SET date_acceptation='2026-04-01' WHERE id=?", bc.b)()), "INV-186"))
        sc["tr_12_bons_commande_annule"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("annule"): x(t, "UPDATE bons_commande SET date_debut='2026-11-01' WHERE id=?", bc.b)()), "INV-173"),
            (lambda t: (lambda bc=t.bc_en_etat("annule_gele"), c=t.client(): x(t, "UPDATE bons_commande SET client_id=? WHERE id=?", c, bc.b)()), "INV-173"),
            (lambda t: (lambda bc=t.bc_en_etat("annule"): x(t, "UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", bc.b)()), "INV-173"))
        sc["tr_14_bons_commande_frozen_at"] = s((lambda t: (lambda bc=t.bc_en_etat("gele"): x(t, "UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc.b)()), "INV-34"))
        sc["tr_17_bons_commande_insert"] = s(
            (lambda t: (lambda d=t.devis_accepte(): t.creer_bc(d, lignes=False, montant_deja_facture_ht="5.00")), "INV-40"),
            (lambda t: (lambda d=t.devis_accepte(): t.creer_bc(d, lignes=False, avancement="5.00")), "INV-40"),
            (lambda t: (lambda d=t.devis_accepte(): t.creer_bc(d, lignes=False, frozen_at=TS)), "INV-40"),
            (lambda t: (lambda d=t.devis_accepte(): t.creer_bc(d, lignes=False, motif_annulation="m")), "INV-40"))
        sc["tr_19_bons_commande_no_delete"] = s((lambda t: (lambda b=t.creer_bc(t.devis_accepte(), lignes=False, lier=False): x(t, "DELETE FROM bons_commande WHERE id=?", b)()), "INV-174"))
        sc["tr_18_devis_statut_avec_bc"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", TS, bc.d)()), "INV-175"),
            (lambda t: (lambda bc=t.bc_en_etat("gele"): x(t, "UPDATE devis SET statut='en_attente' WHERE id=?", t.rattacher(bc.b))()), "INV-175"),     # devis supplémentaire
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "UPDATE devis SET statut='refuse', date_refus='2026-03-20' WHERE id=?", bc.d)()), "INV-175"))
        sc["tr_99_bc_devis_insert"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b,
                                                              t.devis_en_etat("en_attente", client_id=t.client_du_bc(bc.b)).d)()), "INV-40"),
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b,
                                                              t.devis_accepte())()), "INV-48"),
            (lambda t: (lambda bc=t.bc_en_etat("annule"): x(t, "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", bc.b,
                                                            t.devis_accepte(client_id=t.client_du_bc(bc.b)))()), "INV-188"))
        sc["tr_99_bc_devis_no_update"] = s((lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "UPDATE bc_devis SET rang=9 WHERE bc_id=?", bc.b)()), "INV-184"))
        sc["tr_99_bc_devis_no_delete"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "DELETE FROM bc_devis WHERE bc_id=?", bc.b)()), "INV-184"),
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "INSERT OR REPLACE INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 1)", bc.b, bc.d)()), "INV-184"))
        sc["tr_13_bc_lignes_insert"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("annule", dl3=True): t.ligne_bc(bc.b, bc.dl3, 3)), "INV-173"),
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"), d=t.devis_accepte(): t.ligne_bc(
                bc.b, t.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d)[0], 9)), "INV-175"),                           # devis non rattaché
            (lambda t: (lambda bc=t.bc_en_etat("gele"), o=t.bc_en_etat("en_cours", dl3=True): t.ligne_bc(bc.b, o.dl3, 9)), "INV-175"))             # devis d'un autre BC
        sc["tr_13_bc_lignes_update"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "UPDATE bc_lignes SET designation='x' WHERE id=?", bc.bl1)()), "INV-186"),
            (lambda t: (lambda bc=t.bc_en_etat("annule"): x(t, "UPDATE bc_lignes SET quantite='9' WHERE id=?", bc.bl2)()), "INV-186"))
        sc["tr_13_bc_lignes_delete"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "DELETE FROM bc_lignes WHERE id=?", bc.bl2)()), "INV-186"),
            (lambda t: (lambda bc=t.bc_en_etat("termine"): x(t, "DELETE FROM bc_lignes WHERE id=?", bc.bl2)()), "INV-186"))
        sc["tr_13_bc_ligne_garanties_insert"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("annule"): x(t, "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", bc.bl1)()), "INV-173"),
            (lambda t: (lambda bc=t.bc_en_etat("annule_gele"): x(t, "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", bc.bl2)()), "INV-173"))
        sc["tr_13_bc_ligne_garanties_update"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", bc.bg1)()), "INV-186"),
            (lambda t: (lambda bc=t.bc_en_etat("annule"): x(t, "UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", bc.bg1)()), "INV-186"))
        sc["tr_13_bc_ligne_garanties_delete"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("en_cours"): x(t, "DELETE FROM bc_ligne_garanties WHERE id=?", bc.bg1)()), "INV-186"),
            (lambda t: (lambda bc=t.bc_en_etat("gele"): x(t, "DELETE FROM bc_ligne_garanties WHERE id=?", bc.bg1)()), "INV-186"))
        return sc

    def isole(self, gardes):
        """Base 001-005b dont tous les triggers sont supprimés sauf `gardes`."""
        t = Base()
        t.db = migrer()
        t._n = 0
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def test_T46_tous_les_triggers_touches_ont_un_scenario(self):
        attendus = TRIGGERS_NOUVEAUX | TRIGGERS_REECRITS | TRIGGERS_RECREES_IDENTIQUES
        self.assertEqual(set(self.prep_scenarios()), attendus)
        self.assertTrue(attendus <= noms(self.db, "trigger"))

    def test_T46_chaque_trigger_refuse_seul_retire_la_violation_passe_recree_il_refuse_de_nouveau(self):
        for nom, scenarios in sorted(self.prep_scenarios().items()):
            for i, (preparer, motif) in enumerate(scenarios):
                with self.subTest(trigger=nom, scenario=i):
                    seul = self.isole({nom})
                    sql = sql_de(seul.db, nom)
                    with self.assertRaisesRegex(sqlite3.IntegrityError, motif):
                        preparer(seul)()
                    seul.db.execute(f"DROP TRIGGER {nom}")                                                  # temporairement supprimé…
                    preparer(seul)()                                                                       # …plus aucune garde : la violation passe
                    seul.db.execute(sql)                                                                   # …puis recréé à partir de son SQL
                    with self.assertRaisesRegex(sqlite3.IntegrityError, motif):
                        preparer(seul)()
                    self.assertEqual(sql_de(seul.db, nom), sql)

    def test_T46_colonnes_du_contrat_chaque_garde_seule(self):
        """Colonne par colonne, tr_12_contrat refuse seul : une colonne oubliée dans sa liste n'est pas masquée par un autre trigger
        (numero et date_creation relèvent de tr_01, testés plus haut)."""
        nom = "tr_12_bons_commande_contrat"
        autre = self.client()
        for etat in ETATS_BC_NON_ANNULES:
            for col in IMMUABLES_BC:
                if col in ("numero", "date_creation"):
                    continue
                with self.subTest(etat=etat, colonne=col):
                    t = self.isole({nom})
                    bc = t.bc_en_etat(etat)
                    ancienne = t.un(f"SELECT {col} FROM bons_commande WHERE id=?", bc.b)[0]
                    with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-186"):
                        t.db.execute(f"UPDATE bons_commande SET {col}=? WHERE id=?", (autre_valeur_bc(col, ancienne, autre), bc.b))

    def test_T46_colonnes_libres_ne_sont_arretees_par_aucun_trigger(self):
        """Contrepartie : avec tous les triggers, les colonnes libres du BC ne sont refusées par aucune garde (liste blanche exacte)."""
        for etat, modifs in ContratBC.MODIFS_PAR_ETAT.items():
            for m in modifs:
                with self.subTest(etat=etat, modif=m):
                    self.permis(f"UPDATE bons_commande SET {m} WHERE id=?", self.bc_en_etat(etat).b)

    def test_T46_colonnes_du_bc_annule_chaque_garde_seule(self):
        nom = "tr_12_bons_commande_annule"
        autre = self.client()
        for etat in ETATS_BC_ANNULES:
            for col in COLONNES_BC:
                if col in ("numero", "date_creation") or col in COLONNES_ANNULE_MODIFIABLES:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    t = self.isole({nom})
                    bc = t.bc_en_etat(etat)
                    ancienne = t.un(f"SELECT {col} FROM bons_commande WHERE id=?", bc.b)[0]
                    with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-173"):
                        t.db.execute(f"UPDATE bons_commande SET {col}=? WHERE id=?", (autre_valeur_bc(col, ancienne, autre), bc.b))
            with self.subTest(etat=etat, colonne="updated_at"):
                t = self.isole({nom})
                t.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (TS2, t.bc_en_etat(etat).b))

    def test_T46_colonnes_de_lignes_et_garanties_chaque_garde_seule(self):
        for etat in ETATS_BC:
            t = self.isole({"tr_13_bc_lignes_update", "tr_13_bc_ligne_garanties_update"})
            bc = t.bc_en_etat(etat)
            for col in COLONNES_BC_LIGNES:
                with self.subTest(etat=etat, table="bc_lignes", colonne=col):
                    with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-186"):
                        t.db.execute(f"UPDATE bc_lignes SET {col}={col} WHERE id=?", (bc.bl1,))
            for col in colonnes(t.db, "bc_ligne_garanties"):
                with self.subTest(etat=etat, table="bc_ligne_garanties", colonne=col):
                    with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-186"):
                        t.db.execute(f"UPDATE bc_ligne_garanties SET {col}={col} WHERE id=?", (bc.bg1,))

    def test_T46_aucun_scenario_n_est_arrete_par_une_contrainte_sans_le_trigger(self):
        """Garde-fou des scénarios ci-dessus : sans trigger, la violation passe ; elle n'est donc pas masquée par un CHECK ou une FK."""
        for nom, scenarios in sorted(self.prep_scenarios().items()):
            for i, (preparer, _) in enumerate(scenarios):
                with self.subTest(trigger=nom, scenario=i):
                    sans = self.isole(set())
                    preparer(sans)()


CK13_MONTANT = ("SELECT b.id FROM bons_commande b WHERE EXISTS (SELECT 1 FROM bc_devis l WHERE l.bc_id = b.id) AND b.montant_contractuel_ht <> "
                "(SELECT printf('%d.%02d', sum(CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)) / 100, sum(CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)) % 100) "
                "FROM bc_devis l JOIN devis d ON d.id = l.devis_id WHERE l.bc_id = b.id)")
CK13_LIGNES = ("SELECT l.devis_id FROM bc_devis l WHERE (SELECT count(*) FROM devis_lignes dl WHERE dl.devis_id = l.devis_id) "
               "<> (SELECT count(*) FROM bc_lignes bl JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id WHERE bl.bc_id = l.bc_id AND dl.devis_id = l.devis_id)")
CK13_DEVIS_ANNULE = ("SELECT l.devis_id FROM bc_devis l JOIN devis d ON d.id = l.devis_id JOIN bons_commande b ON b.id = l.bc_id "
                     "WHERE d.statut = 'annule' AND b.statut <> 'annule'")
CK14_SANS_LIEN = "SELECT b.id FROM bons_commande b WHERE NOT EXISTS (SELECT 1 FROM bc_devis l WHERE l.bc_id = b.id)"
CK14_DEVIS_NON_ACCEPTE = ("SELECT l.devis_id FROM bc_devis l JOIN devis d ON d.id = l.devis_id JOIN bons_commande b ON b.id = l.bc_id "
                          "WHERE d.statut <> 'accepte' AND b.statut <> 'annule'")
CK14_AUTRE_CLIENT = ("SELECT l.devis_id FROM bc_devis l JOIN devis d ON d.id = l.devis_id JOIN bons_commande b ON b.id = l.bc_id "
                     "WHERE d.client_id <> b.client_id")
CK14_APRES_ANNULATION = ("SELECT l.devis_id FROM bc_devis l JOIN bons_commande b ON b.id = l.bc_id "
                         "WHERE b.cancelled_at IS NOT NULL AND l.created_at > b.cancelled_at")
CK14_DEVIS_DANS_PLUSIEURS_BC = "SELECT devis_id FROM bc_devis GROUP BY devis_id HAVING count(*) > 1"
CK13 = {"montant": CK13_MONTANT, "lignes": CK13_LIGNES, "devis_annule": CK13_DEVIS_ANNULE}
CK14 = {"sans_lien": CK14_SANS_LIEN, "devis_non_accepte": CK14_DEVIS_NON_ACCEPTE, "autre_client": CK14_AUTRE_CLIENT,
        "apres_annulation": CK14_APRES_ANNULATION, "devis_dans_plusieurs_bc": CK14_DEVIS_DANS_PLUSIEURS_BC}


class ControlesCK(Base):
    """CK-13 (cohérence devis <-> BC, dont contractuel = Σ des devis liés) et CK-14 (rattachement multi-devis, dont « BC sans aucun devis lié »)
    sont des requêtes de diagnostic : aucune n'est un trigger ni un CHECK ; le schéma 005b laisse passer chaque état qu'elles détectent
    (C5). Un résultat non vide annule un import ou fait échouer une restauration ; ces requêtes ne modifient jamais les données."""

    def _resultats(self):
        return ({k: self.tous(q) for k, q in CK13.items()}, {k: self.tous(q) for k, q in CK14.items()})

    def _vide(self):
        ck13, ck14 = self._resultats()
        self.assertEqual((ck13, ck14), ({k: [] for k in CK13}, {k: [] for k in CK14}))

    def test_CK13_CK14_vides_sur_des_donnees_coherentes_y_compris_multi_devis(self):
        self._vide()                                                                                    # base vide
        self.bc_en_etat("en_cours")
        self._vide()
        bc = self.bc_en_etat("gele")
        self.rattacher(bc.b)
        self.rattacher(bc.b, rang=40)
        self.annuler_bc(self.bc_en_etat("en_cours").b)
        self._vide()

    def test_CK14_un_BC_sans_aucun_devis_lie_est_diagnostique(self):
        """C5 : TR-17 ne lit plus le devis, un BC sans ligne bc_devis est accepté par SQLite ; CK-14 le détecte. Ce n'est pas un trigger bloquant."""
        orphelin = self.creer_bc(self.devis_accepte(), lignes=False, lier=False)
        ck13, ck14 = self._resultats()
        self.assertEqual(ck14["sans_lien"], [(orphelin,)])
        self.assertEqual([v for k, v in ck14.items() if k != "sans_lien"], [[]] * 4)
        self.assertEqual(ck13, {k: [] for k in CK13})                                                   # pas un écart CK-13
        autre = self.bc_en_etat("en_cours")
        self.assertEqual(self.tous(CK14_SANS_LIEN), [(orphelin,)])                                      # les BC liés ne sont pas signalés
        self.lier(orphelin, self.un("SELECT devis_id FROM (SELECT ? AS devis_id)", self.un("SELECT id FROM devis WHERE id NOT IN (SELECT devis_id FROM bc_devis) LIMIT 1")[0])[0])
        self.assertEqual(self.tous(CK14_SANS_LIEN), [])
        self.assertTrue(autre.b)

    def test_CK14_BC_sans_lien_aucun_trigger_ne_l_impose(self):
        """Règle : intégrité structurelle -> SQL ; cohérence inter-tables -> diagnostic CK ; orchestration -> service. Aucun trigger ni CHECK de bons_commande
        ne lit bc_devis ; créer un BC puis son lien reste deux instructions d'une même transaction de service."""
        for (nom,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='bons_commande'"):
            self.assertNotIn("bc_devis", sql_de(self.db, nom), nom)
        self.assertNotIn("bc_devis", sql_de(self.db, "bons_commande"))
        self.db.execute("BEGIN")
        b = self.creer_bc(self.devis_accepte(), lignes=False, lier=False)
        self.assertEqual(self.tous(CK14_SANS_LIEN), [(b,)])                                             # état intermédiaire légitime dans la transaction
        self.db.execute("ROLLBACK")
        self.assertEqual(self.tous(CK14_SANS_LIEN), [])

    def test_CK13_contractuel_different_de_la_somme_des_devis_lies_est_diagnostique_par_CK13_et_non_CK14(self):
        """Le contrôle « montant contractuel = Σ total_ht des devis liés » est classé CK-13 (§14 : définition détaillée de CK-13 et tableau §4.19) ;
        le résumé de CK-14 du §14 le répète : écart documentaire à corriger, pas de double contrôle."""
        bc = self.bc_en_etat("en_cours")
        self.rattacher(bc.b)
        self._vide()
        self.db.execute("UPDATE bons_commande SET montant_contractuel_ht='10.00' WHERE id=?", (bc.b,))       # permis par le schéma (Q-B)
        ck13, ck14 = self._resultats()
        self.assertEqual(ck13["montant"], [(bc.b,)])
        self.assertEqual(ck14, {k: [] for k in CK14})
        self.db.execute("UPDATE bons_commande SET montant_contractuel_ht='63.00' WHERE id=?", (bc.b,))
        self._vide()

    def test_CK13_devis_rattache_sans_ses_lignes_et_devis_annule_dans_un_bc_vivant(self):
        bc = self.bc_en_etat("en_cours")
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.lier(bc.b, d)                                                                              # lien sans copie des lignes
        ck13, ck14 = self._resultats()
        self.assertEqual((ck13["lignes"], ck14), ([(d,)], {k: [] for k in CK14}))
        self.copier_lignes(bc.b, d)
        self.assertEqual(self.tous(CK13_LIGNES), [])
        self.db.execute("DROP TRIGGER tr_18_devis_statut_avec_bc")                                      # importé / restauré sans la garde
        self.db.execute("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", (TS, d))
        ck13, ck14 = self._resultats()
        self.assertEqual(ck13["devis_annule"], [(d,)])

    def test_CK14_devis_lie_non_accepte_dans_un_bc_non_annule(self):
        bc = self.bc_en_etat("en_cours")
        d = self.rattacher(bc.b)
        self.db.execute("DROP TRIGGER tr_18_devis_statut_avec_bc")
        self.db.execute("UPDATE devis SET statut='en_attente' WHERE id=?", (d,))
        ck13, ck14 = self._resultats()
        self.assertEqual(ck14["devis_non_accepte"], [(d,)])
        self.assertEqual(ck13["devis_annule"], [])                                                      # statut en_attente : CK-14 seul
        self.annuler_bc(bc.b)
        self.assertEqual(self.tous(CK14_DEVIS_NON_ACCEPTE), [])                                         # BC annulé : le devis est libre (INV-175)

    def test_CK14_devis_d_un_autre_client_que_celui_du_bc(self):
        bc = self.bc_en_etat("en_cours")
        autre = self.devis_accepte()
        self.db.execute("DROP TRIGGER tr_99_bc_devis_insert")                                           # base importée sans la garde
        self.lier(bc.b, autre)
        self.assertEqual(self.tous(CK14_AUTRE_CLIENT), [(autre,)])

    def test_CK14_devis_rattache_apres_l_annulation_du_bc(self):
        bc = self.bc_en_etat("en_cours")
        self.annuler_bc(bc.b)
        d = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.assertEqual(self.tous(CK14_APRES_ANNULATION), [])
        self.db.execute("DROP TRIGGER tr_99_bc_devis_insert")
        self.db.execute("INSERT INTO bc_devis (bc_id, devis_id, rang, created_at) VALUES (?, ?, 2, '2100-01-01T00:00:00.000Z')", (bc.b, d))
        self.assertEqual(self.tous(CK14_APRES_ANNULATION), [(d,)])

    def test_CK14_un_devis_dans_plusieurs_bc_est_impossible_par_le_schema_et_la_requete_reste_vide(self):
        bc = self.bc_en_etat("en_cours")
        autre = self.bc_en_etat("en_cours", client_id=self.client_du_bc(bc.b))                           # même client : seul UNIQUE(devis_id) s'oppose
        self.refuse_check("INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 9)", autre.b, bc.d)
        self.assertEqual(self.tous(CK14_DEVIS_DANS_PLUSIEURS_BC), [])

    def test_CK13_CK14_ne_modifient_jamais_les_donnees(self):
        bc = self.bc_en_etat("gele")
        self.rattacher(bc.b)
        self.creer_bc(self.devis_accepte(), lignes=False, lier=False)
        avant = tout(self.db)
        self._resultats()
        self.assertEqual(tout(self.db), avant)
        for q in list(CK13.values()) + list(CK14.values()):
            self.assertTrue(q.lstrip().upper().startswith("SELECT"))

    def test_CK14_sur_le_resultat_de_la_migration_chaque_BC_repris_a_un_lien(self):
        """Après 005b sur une base existante, CK-14 « sans lien » et CK-13 sont vides : la reprise ne crée aucun BC orphelin."""
        t = base6_peuplee()
        runner(t.db, 7)
        u = sur_rang7(t)
        self.assertEqual(u.tous(CK14_SANS_LIEN), [])
        self.assertEqual({k: u.tous(q) for k, q in CK14.items()}, {k: [] for k in CK14})
        self.assertEqual(u.tous(CK13_MONTANT), [])


class ArbitragesRelecture(Base):
    """Vérifications finales de la contre-relecture : Q-A (aucune perte ni normalisation), Q-B (cinq cas), Q-D (reprise exacte), devis_origine_id."""

    def test_QA_la_garde_refuse_toute_difference_meme_minime_ou_de_forme(self):
        """Aucune normalisation : '10.00' et '10.01', le type seul, NULL et valeur sont des écarts ; la garde porte sur tous les BC (pas le premier)."""
        for modif in ("remise_valeur='10.01'", "remise_type='montant'", "acompte_type='pourcentage'", "acompte_valeur='5.01'",
                      "remise_type='aucune', remise_valeur=NULL, acompte_type='aucun', acompte_valeur=NULL"):
            with self.subTest(ecart=modif):
                t = base6_peuplee()
                d = t.devis_accepte(remise_type="aucune", remise_valeur=None, acompte_type="aucun", acompte_valeur=None)
                t.creer_bc(d)
                dernier = t.creer_bc(t.devis_accepte())                                                  # dernier BC de la base (en_cours, remise 10 %, acompte 5.00)
                t.db.execute(f"UPDATE bons_commande SET {modif} WHERE id=?", (dernier,))
                avant = tout(t.db)
                with self.assertRaisesRegex(sqlite3.IntegrityError, "refuse de perdre la remise ou l'acompte"):
                    runner(t.db, 7)
                self.assertEqual((db_user_version(t.db), tout(t.db)), (6, avant))

    def test_QA_la_garde_est_la_seule_cause_de_refus_sur_une_base_par_ailleurs_saine(self):
        t = base6_peuplee()
        runner(t.db, 7)                                                                                  # aucune différence : passe
        self.assertEqual(db_user_version(t.db), 7)

    def test_QA_apres_migration_remise_et_acompte_restent_integralement_dans_les_devis(self):
        t = base6_peuplee()
        avant = t.tous("SELECT id, remise_type, remise_valeur, acompte_type, acompte_valeur FROM devis ORDER BY id")
        du_bc = t.tous("SELECT d.id, b.remise_type, b.remise_valeur, b.acompte_type, b.acompte_valeur FROM bons_commande b JOIN devis d ON d.id=b.devis_id ORDER BY d.id")
        runner(t.db, 7)
        self.assertEqual(t.tous("SELECT id, remise_type, remise_valeur, acompte_type, acompte_valeur FROM devis ORDER BY id"), avant)
        for ligne in du_bc:                                                                              # ce que portait le BC est exactement ce que porte son devis
            self.assertIn(ligne, avant)

    def test_QB_cinq_cas_de_rattachement_sur_bc_gele_non_gele_et_annule(self):
        # 1. BC non gelé + nouveau devis -> OK
        bc = self.bc_en_etat("en_cours")
        self.assertIsNone(self.un("SELECT frozen_at FROM bons_commande WHERE id=?", bc.b)[0])
        d1 = self.devis_accepte(client_id=self.client_du_bc(bc.b))
        self.lier(bc.b, d1)
        # 2. BC gelé + nouveau devis -> OK
        gele = self.bc_en_etat("gele")
        self.assertIsNotNone(self.un("SELECT frozen_at FROM bons_commande WHERE id=?", gele.b)[0])
        d2 = self.devis_accepte(client_id=self.client_du_bc(gele.b))
        self.lier(gele.b, d2)
        # 3. BC annulé + nouveau devis -> REFUS
        annule = self.bc_en_etat("annule")
        d3 = self.devis_accepte(client_id=self.client_du_bc(annule.b))
        self.refuse_inv("INV-188", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", annule.b, d3)
        # 4. BC gelé + ajout de lignes provenant du nouveau devis -> OK
        self.copier_lignes(gele.b, d2)
        self.assertEqual(self.un("SELECT count(*) FROM bc_lignes WHERE bc_id=?", gele.b)[0], 4)
        self.assertIsNotNone(self.un("SELECT frozen_at FROM bons_commande WHERE id=?", gele.b)[0])
        # 5. modification d'une ligne contractuelle existante -> REFUS (BC gelé et non gelé)
        for b in (gele, bc):
            self.refuse_inv("INV-186", "UPDATE bc_lignes SET quantite='99' WHERE id=?", b.bl1)
            self.refuse_inv("INV-186", "DELETE FROM bc_lignes WHERE id=?", b.bl2)
            self.refuse_inv("INV-186", "UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", b.bg1)

    def test_QD_la_reprise_est_exacte_sans_renumerotation_ni_contiguite_imposee(self):
        t = base6_peuplee()
        db = t.db
        liens6 = db.execute("SELECT id, devis_id FROM bons_commande ORDER BY id").fetchall()
        numeros = db.execute("SELECT id, numero, date_creation, date_acceptation, created_at, updated_at FROM bons_commande ORDER BY id").fetchall()
        devis = db.execute("SELECT * FROM devis ORDER BY id").fetchall()
        seq = dict(db.execute("SELECT name, seq FROM sqlite_sequence"))
        runner(db, 7)
        self.assertEqual(db.execute("SELECT bc_id, devis_id FROM bc_devis ORDER BY bc_id").fetchall(), liens6)                # lien historique exact
        self.assertEqual(db.execute("SELECT id, numero, date_creation, date_acceptation, created_at, updated_at FROM bons_commande ORDER BY id").fetchall(), numeros)
        self.assertEqual(db.execute("SELECT * FROM devis ORDER BY id").fetchall(), devis)                                      # identité des devis
        seq7 = dict(db.execute("SELECT name, seq FROM sqlite_sequence"))
        self.assertEqual({k: v for k, v in seq7.items() if k != "bc_devis"}, seq)
        self.assertEqual(db.execute("SELECT DISTINCT rang FROM bc_devis").fetchall(), [(1,)])                                  # un seul lien par BC : rang >= 1
        # ni contiguïté ni rang imposés pour la suite : trous et premier rang quelconque acceptés, liens repris intacts
        u = sur_rang7(t)
        bc = t.bcs["en_cours"].b
        u.lier(bc, u.devis_accepte(client_id=u.client_du_bc(bc)), 50)
        u.lier(bc, u.devis_accepte(client_id=u.client_du_bc(bc)), 7)
        self.assertEqual(u.tous("SELECT rang FROM bc_devis WHERE bc_id=? ORDER BY rang", bc), [(1,), (7,), (50,)])
        self.assertEqual(u.un("SELECT devis_id FROM bc_devis WHERE bc_id=? AND rang=1", bc)[0], t.bcs["en_cours"].d)

    def test_DECISION_devis_origine_id_n_est_cree_nulle_part(self):
        """Décision explicite 005b : aucune colonne devis_origine_id. Le devis historique d'un BC se lit par son lien repris (rang initial) dans bc_devis ;
        aucune colonne supplémentaire dans bons_commande ni dans devis. Toute introduction ultérieure exige une décision dédiée."""
        for table in sorted(noms(self.db, "table")):
            self.assertNotIn("devis_origine_id", colonnes(self.db, table), table)
        for type_, nom, tbl, sql in objets(self.db):
            self.assertNotIn("devis_origine_id", sql or "", nom)
        self.assertNotIn("devis_origine_id", sans_commentaires(SQL_005B))
        bc = self.bc_en_etat("en_cours")
        self.rattacher(bc.b)
        self.assertEqual(self.un("SELECT devis_id FROM bc_devis WHERE bc_id=? ORDER BY rang LIMIT 1", bc.b)[0], bc.d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
