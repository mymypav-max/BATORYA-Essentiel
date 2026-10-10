"""T-51 — Tranche 009_pv (rang 12) ; modèle V3.13 §2 (conventions), §2.4 (BLOC-IMP, BLOC-SNAP), §2.5 (énumérations), §4.11 (PV), §6 (numérotation PVR), §8 (TR-40, TR-41),
§9 (index), §10 (import) ; invariants INV-05, INV-06, INV-10, INV-20, INV-26, INV-27, INV-30, INV-32, INV-95 à INV-97, INV-131, INV-136, INV-174, INV-177, INV-179 ;
CADRAGE__009_pv.md (validé, après audit contradictoire : QO-1 à QO-5 non spécifiées, Z-8 hors périmètre de migration, PR-3 : aucun CHECK de format ajouté pour la levée).

009 crée UNE table (pv), un index (idx_pv_bc_id) et trois triggers (tr_40 x2, tr_41). Aucun trigger de 009 ne lit ni n'écrit bons_commande, factures, reglements, garanties
ou numerotation_sequences. Responsabilités vérifiées ici :
  * CHECK / index / FK : liste fermée des types, dates réelles (famille D, aucune borne d'année), levée <=> origine <=> suffixe (1 à 99), reserves <=> réception avec réserves,
    format du numéro d'un PV INITIAL V6 (PVR-nnnnn-yy, yy = année de date_reception), numéro non vide et unique, BLOC-SNAP, BLOC-IMP, NOT NULL, FK RESTRICT sans ON UPDATE, STRICT ;
  * triggers : immuabilité et non-suppression, REPLACE et UPSERT compris (tr_40) ; gardes de levée G1 (origine = PV avec réserves), G2 (même BC), G3 (suffixe = max + 1),
    G4 (numéro = numéro de l'origine + '-' + suffixe sur 2 chiffres) (tr_41), sans exemption d'origine (INV-131) ;
  * service (reproduit ici par une émulation, JAMAIS par le schéma) : pré-contrôles avant réservation, réservation PVR (PT-1, D-54), INSERT simple (jamais OR REPLACE / OR IGNORE) ;
    la levée n'a ni séquence ni réservation ;
  * constats : comportements observés là où les sources ne spécifient rien (QO-1, QO-3, QO-4, Z-8). Ils sont signalés « CONSTAT » : ce ne sont PAS des règles.

Réutilisation : ces tests importent test_008_garanties (qui importe test_007_reglements, test_006_facturation, test_005c puis test_005b) pour l'émulation du runner et la
fabrication des devis, BC, lignes, factures et avoirs, sans les modifier. Le rang 12 s'obtient en appliquant 009 sur la chaîne du rang 11 (BEGIN IMMEDIATE, fichier,
PRAGMA user_version = 12, COMMIT).

Exécution : python3 src-tauri/tests/metier/test_009_pv.py
Les méthodes portent le nom test_T51_ suivi du groupe (A chaîne et structure, B CHECK de colonnes, C numérotation (service émulé), D levée TR-41, E immuabilité TR-40,
F FK et suppression des parents, G indépendance, H import (comportement générique du schéma), I diagnostics, J non-régression, K données malformées et contournements,
L atomicité). Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39), sauf les témoins qui le précisent.
Un refus levé par un trigger se reconnaît à son préfixe « INV-nn » ; un refus levé par une contrainte (CHECK, NOT NULL, UNIQUE, FK) n'en porte aucun.
Limites assumées (cadrage §3.6) : ce fichier n'établit PAS la conformité documentaire du SQL (elle repose sur les sources) ; INSERT ... SELECT et UPSERT sont ici
éprouvés explicitement (groupes D, E, K) ; les conclusions sur INSERT OR REPLACE dépendent de recursive_triggers=ON (témoin OFF en groupe E).
"""
import datetime
import hashlib
import pathlib
import re
import sqlite3
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_008_garanties as G  # noqa: E402  (chaîne 001 à 008, fabrication de données, services de facturation et émulation du runner)

R = G.R
F = G.F
T = G.T
MIGRATIONS = G.MIGRATIONS
NOM_009 = "009_pv.sql"
NOMS = G.NOMS + (NOM_009,)
SQL_009 = (MIGRATIONS / NOM_009).read_text(encoding="utf-8")
RANG = 12
TS, TS2, TS_ANNUL = T.TS, T.TS2, T.TS_ANNUL
OMIT = F.OMIT
ATTRIBUER = T.ATTRIBUER

INDEXES_009 = {"idx_pv_bc_id": "bc_id"}
TRIGGERS_009 = {"tr_40_pv_no_update": "pv", "tr_40_pv_no_delete": "pv", "tr_41_pv_insert": "pv"}
COLONNES_PV = ["id", "numero", "bc_id", "type", "date_reception", "client_snapshot", "client_snapshot_version", "entreprise_snapshot", "entreprise_snapshot_version",
               "chantier_snapshot", "chantier_snapshot_version", "observations", "reserves", "origine_pv_id", "suffixe", "created_at", "origine", "legacy_id", "legacy_data"]
NOT_NULL_PV = ["numero", "bc_id", "type", "date_reception", "client_snapshot", "client_snapshot_version", "entreprise_snapshot", "entreprise_snapshot_version",
               "chantier_snapshot", "chantier_snapshot_version", "created_at", "origine"]
SR, AR, LV = "reception_sans_reserves", "reception_avec_reserves", "levee_reserves"
TYPES_PV = (SR, AR, LV)
D_PV = "2026-10-20"                                                                             # date de réception par défaut
ETATS_BC = ("en_cours", "gele", "termine", "annule", "annule_gele")
F_DATES_INVALIDES = G.F_DATES_INVALIDES


# --------------------------------------------------------------------------------------------------------------------
# Chaîne
# --------------------------------------------------------------------------------------------------------------------
def migrer12(recursive=True):
    """Chaîne 001 à 008 (rang 11) puis 009 comme une migration ordinaire : BEGIN IMMEDIATE, fichier, user_version = 12, COMMIT."""
    db = G.migrer11(recursive=recursive)
    T.appliquer(db, RANG, SQL_009)
    return db


def code_sql():
    return T.sans_commentaires(SQL_009)


def instruction_009(debut):
    """Texte (sans commentaire) de l'instruction de 009 qui commence par `debut` : sert à recréer un trigger sur une base alimentée sans garde."""
    trouvees = [s for s in (T.sans_commentaires(x).strip() for x in T.instructions(SQL_009)) if s.startswith(debut)]
    assert len(trouvees) == 1, debut
    return trouvees[0]


# --------------------------------------------------------------------------------------------------------------------
# Oracles indépendants du SQL (le « service » : arithmétique sur chaînes, jamais lue dans la ligne persistée)
# --------------------------------------------------------------------------------------------------------------------
def numero_initial(n, date):
    """PVR-nnnnn-yy, yy = année de date_reception (INV-20, modèle §6)."""
    return "PVR-%05d-%s" % (n, date[2:4])


def numero_levee(numero_origine, suffixe):
    """Numéro de l'origine + '-' + suffixe sur 2 chiffres (TR-41, modèle §4.11)."""
    return "%s-%02d" % (numero_origine, suffixe)


# --------------------------------------------------------------------------------------------------------------------
# Erreurs du service émulé
# --------------------------------------------------------------------------------------------------------------------
class ErreurService(Exception):
    """Pré-contrôle du service refusé AVANT toute réservation de numéro et toute écriture."""


class AnneeHorsBornes(ErreurService):
    """L'année de date_reception d'un PV initial n'est pas dans 2001-2099 (INV-177, D-38 : contrôle du SERVICE, jamais un CHECK)."""


class PlafondNumeros(ErreurService):
    """Le compteur PVR de l'année a atteint 99 999 (modèle §6) : erreur explicite avant réservation."""


class DefautInjecte(Exception):
    """Défaut technique injecté par un test après une étape de l'émission (pour éprouver le rollback intégral)."""


# --------------------------------------------------------------------------------------------------------------------
# Diagnostics de détection propres à ces tests (requêtes de test en lecture seule, PAS des CK du modèle : le traitement des levées par CK-01/CK-02 n'est pas spécifié, Z-7)
# --------------------------------------------------------------------------------------------------------------------
DETECT_LEVEE_ORIGINE = ("SELECT l.id FROM pv l WHERE l.type = 'levee_reserves' AND NOT EXISTS "
                        "(SELECT 1 FROM pv o WHERE o.id = l.origine_pv_id AND o.type = 'reception_avec_reserves' AND o.bc_id = l.bc_id)")
DETECT_LEVEE_NUMERO = ("SELECT l.id FROM pv l JOIN pv o ON o.id = l.origine_pv_id WHERE l.type = 'levee_reserves' "
                       "AND l.numero IS NOT o.numero || '-' || printf('%02d', l.suffixe)")
DETECT_LEVEE_SUFFIXES = ("SELECT origine_pv_id FROM pv WHERE type = 'levee_reserves' GROUP BY origine_pv_id HAVING MAX(suffixe) <> COUNT(*) OR MIN(suffixe) <> 1")
DETECT = {"origine": DETECT_LEVEE_ORIGINE, "numero": DETECT_LEVEE_NUMERO, "suffixes": DETECT_LEVEE_SUFFIXES}


# --------------------------------------------------------------------------------------------------------------------
# Fabrique : BC, PV bruts, service d'émission émulé (reproduit côté test ; le schéma n'en porte aucune règle)
# --------------------------------------------------------------------------------------------------------------------
class Base12(G.Base11):
    """Base au rang 12. Les fabriques de devis, BC, factures, avoirs et garanties viennent de test_005b à 008 ; les PV et le service d'émission sont reproduits ici."""

    DECALAGES = G.Base11.DECALAGES + (("pv", 105),)

    def setUp(self):
        self.db = migrer12()
        self._n = 0
        self._npv = {}
        self.desynchroniser_ids()

    @classmethod
    def _sur(cls, db):
        t = cls()
        t.db = db
        t._n = 0
        t._npv = {}
        t.desynchroniser_ids()
        return t

    def isole(self, gardes):
        """Base du rang 12 dont tous les triggers sont supprimés sauf `gardes`."""
        t = self._sur(migrer12())
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def sans_triggers(self):
        return self.isole(())

    def sans_009(self):
        """Base du rang 12 privée des seuls triggers de 009 : les CHECK, l'index et les FK de pv restent, ainsi que tous les triggers 001–008."""
        t = self._sur(migrer12())
        for nom in TRIGGERS_009:
            t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def seulement_009(self):
        return self.isole(tuple(TRIGGERS_009))

    # --- BC ---------------------------------------------------------------------------------------------------------------
    def bc(self, etat=None, **kw):
        """BC (une ligne, sans garantie de ligne) à l'état voulu ; `kw` : colonnes de bons_commande (ex. origine='import')."""
        m = self.monde_g([[("100.00", ())]], **kw)
        if etat:
            self.etat(m, etat)
        return m

    def snaps(self, b):
        return self.un("SELECT client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version "
                       "FROM bons_commande WHERE id=?", b)

    # --- PV bruts ---------------------------------------------------------------------------------------------------------
    def numero_libre(self, date):
        """Numéro PVR de test (compteur local, hors numerotation_sequences) : jamais réutilisé dans un même test."""
        yy = date[2:4] if isinstance(date, str) and len(date) >= 4 and date[:4].isdigit() else "26"
        self._npv[yy] = self._npv.get(yy, 0) + 1
        return "PVR-%05d-%s" % (self._npv[yy], yy)

    def cols_pv(self, b, type_=SR, **kw):
        """Colonnes d'un PV initial conforme pour le BC `b` ; `kw` remplace, OMIT retire. Un PV avec réserves reçoit un texte de réserves par défaut."""
        s = self.snaps(b) or ("{}", 1, "{}", 1, "{}", 1)                                             # BC absent : gabarit minimal (test de FK / de garde)
        date = kw["date_reception"] if "date_reception" in kw else D_PV
        cols = {"numero": kw["numero"] if "numero" in kw else self.numero_libre(date), "bc_id": b, "type": type_, "date_reception": date,
                "client_snapshot": s[0], "client_snapshot_version": s[1], "entreprise_snapshot": s[2], "entreprise_snapshot_version": s[3],
                "chantier_snapshot": s[4], "chantier_snapshot_version": s[5]}
        if type_ == AR:
            cols["reserves"] = "Reprise de la peinture du couloir"
        cols.update(kw)
        return {k: v for k, v in cols.items() if v is not OMIT}

    def cols_levee(self, parent, **kw):
        """Colonnes d'une levée conforme à TR-41 pour l'origine `parent` (suffixe = max + 1 lu en base, numéro = numéro de l'origine + suffixe) ; `kw` remplace."""
        o = self.un("SELECT numero, bc_id FROM pv WHERE id=?", parent)
        suffixe = kw["suffixe"] if "suffixe" in kw else self.un("SELECT COALESCE(MAX(suffixe), 0) + 1 FROM pv WHERE origine_pv_id=?", parent)[0]
        b = kw["bc_id"] if "bc_id" in kw else (o[1] if o else self.B)
        base_numero = o[0] if o else "PVR-99999-26"
        numero = kw["numero"] if "numero" in kw else numero_levee(base_numero, suffixe if isinstance(suffixe, int) else 0)
        extra = {k: v for k, v in kw.items() if k not in ("numero", "bc_id", "suffixe", "origine_pv_id")}
        return self.cols_pv(b, LV, numero=numero, origine_pv_id=kw["origine_pv_id"] if "origine_pv_id" in kw else parent, suffixe=suffixe, **extra)

    def inserer_pv(self, cols, verbe="INSERT"):
        return self.inserer("pv", cols, verbe)

    def pv(self, b, type_=SR, verbe="INSERT", **kw):
        return self.inserer_pv(self.cols_pv(b, type_, **kw), verbe)

    def levee(self, parent, verbe="INSERT", **kw):
        return self.inserer_pv(self.cols_levee(parent, **kw), verbe)

    def multi(self, lignes, verbe="INSERT"):
        """Un seul INSERT à plusieurs lignes (VALUES) ; les clés manquantes valent NULL."""
        cles = []
        for l_ in lignes:
            cles += [c for c in l_ if c not in cles]
        sql = f"{verbe} INTO pv ({', '.join(cles)}) VALUES " + ", ".join("(" + ", ".join("?" * len(cles)) + ")" for _ in lignes)
        return self.db.execute(sql, tuple(l_.get(c) for l_ in lignes for c in cles))

    def sous_savepoint(self, f):
        """Exécute f puis annule : None si acceptée, sinon le message de l'IntegrityError."""
        self.db.execute("SAVEPOINT tentepv")
        try:
            f()
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tentepv")
            self.db.execute("RELEASE tentepv")

    def tente(self, b, type_=SR, verbe="INSERT", **kw):
        return self.sous_savepoint(lambda: self.pv(b, type_, verbe, **kw))

    def tente_l(self, parent, verbe="INSERT", **kw):
        return self.sous_savepoint(lambda: self.levee(parent, verbe, **kw))

    def ok_(self, m):
        self.assertIsNone(m, m)

    def ko_inv(self, m, inv):
        self.assertIsNotNone(m, "écriture acceptée à tort")
        self.assertRegex(m, inv)

    def ko_check(self, m):
        self.assertIsNotNone(m, "écriture acceptée à tort")
        self.assertNotIn("INV-", m)

    def lignes_pv(self, b=None):
        w, a = ("WHERE bc_id=?", (b,)) if b is not None else ("", ())
        return self.tous(f"SELECT * FROM pv {w} ORDER BY id", *a)

    def levees_de(self, parent):
        return self.tous("SELECT suffixe, numero FROM pv WHERE origine_pv_id=? ORDER BY suffixe", parent)

    # --- numérotation et empreintes ----------------------------------------------------------------------------------------
    def sequences(self):
        return self.tous("SELECT type_objet, annee, dernier_numero, derniere_date FROM numerotation_sequences ORDER BY 1, 2")

    def seq_pv(self):
        """Séquences PVR seules (la création d'un BC consomme une séquence BCD)."""
        return [r_ for r_ in self.sequences() if r_[0] == "PVR"]

    def compteur(self, type_objet="PVR", annee=26):
        r_ = self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet=? AND annee=?", type_objet, annee)
        return r_[0] if r_ else 0

    def empreinte_hors_pv(self):
        """Empreinte de TOUTES les tables sauf pv (et la ligne de sqlite_sequence de pv)."""
        h = hashlib.sha256()
        for (n,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name <> 'pv' ORDER BY name").fetchall():
            h.update(n.encode())
            h.update(repr(self.db.execute(f"SELECT * FROM {n} ORDER BY rowid").fetchall()).encode())
        h.update(repr(self.db.execute("SELECT name, seq FROM sqlite_sequence WHERE name <> 'pv' ORDER BY name").fetchall()).encode())
        return h.hexdigest()

    def empreinte_pv(self):
        return (self.db.execute("SELECT * FROM pv ORDER BY id").fetchall(), self.db.execute("SELECT seq FROM sqlite_sequence WHERE name='pv'").fetchall())

    # --- service d'émission d'un PV initial (émulation de cadrage §4.1) ----------------------------------------------------
    def creer_pv(self, b, type_=SR, date=D_PV, reserves=OMIT, observations=None, apres_reservation=None, avant_commit=None, **kw):
        """1 pré-contrôles AVANT réservation (BC existant, type initial, reserves <=> avec réserves, année 2001-2099, plafond 99 999) ;
        2 réservation du numéro PVR (transaction propre committée, PT-1) ; 3 BEGIN IMMEDIATE, INSERT simple, COMMIT.
        `apres_reservation`, `avant_commit` : défauts injectés."""
        if type_ not in (SR, AR) or self.un("SELECT 1 FROM bons_commande WHERE id=?", b) is None:
            raise ErreurService("type ou BC invalide")
        if reserves is OMIT:
            reserves = "Reprise de la peinture" if type_ == AR else None
        if (reserves is not None) != (type_ == AR):
            raise ErreurService("reserves renseignées si et seulement si réception avec réserves")
        annee = int(date[:4])
        if not 2001 <= annee <= 2099:
            raise AnneeHorsBornes(date)
        yy = int(date[2:4])
        if self.compteur("PVR", yy) >= 99999:
            raise PlafondNumeros(yy)
        self.db.execute("BEGIN IMMEDIATE")
        n = self.un(ATTRIBUER, "PVR", yy)[0]
        self.db.execute("COMMIT")                                                                # numéro réservé : committé AVANT la transaction de l'objet
        numero = numero_initial(n, date)
        if apres_reservation:
            apres_reservation(self, numero)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cols = self.cols_pv(b, type_, numero=numero, date_reception=date, reserves=reserves, observations=observations, **kw)
            pid = self.inserer_pv(cols)                                                          # INSERT simple : jamais OR REPLACE ni OR IGNORE
            if avant_commit:
                avant_commit(self, pid)
            self.db.execute("COMMIT")
            return types.SimpleNamespace(id=pid, numero=numero, n=n)
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def creer_levee(self, parent, date=D_PV, observations=None, avant_commit=None, **kw):
        """Levée : pré-contrôles, suffixe = max + 1 calculé dans la transaction, numéro dérivé de l'origine, INSERT simple. AUCUNE réservation de séquence. Le service ne
        devance pas le plafond de 99 (PR-5, proposition non validée) : le CHECK du suffixe refuse la 100e."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            o = self.un("SELECT numero, bc_id, type FROM pv WHERE id=?", parent)
            if o is None or o[2] != AR:
                raise ErreurService("origine invalide")
            suffixe = self.un("SELECT COALESCE(MAX(suffixe), 0) + 1 FROM pv WHERE origine_pv_id=?", parent)[0]
            pid = self.inserer_pv(self.cols_pv(o[1], LV, numero=numero_levee(o[0], suffixe), date_reception=date, origine_pv_id=parent, suffixe=suffixe,
                                               observations=observations, **kw))
            if avant_commit:
                avant_commit(self, pid)
            self.db.execute("COMMIT")
            return types.SimpleNamespace(id=pid, numero=numero_levee(o[0], suffixe), suffixe=suffixe)
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def echoue(self, exc, reservation, f):
        """f() échoue avec `exc` ; l'état COMPLET de la base (hors compteur de numérotation) est strictement celui d'avant. `reservation` : le compteur PVR avance d'exactement 1
        (trou admis, PT-1) et AUCUN PV ne porte le numéro réservé ; sinon le compteur de numérotation est strictement inchangé."""
        avant, ns, n0 = self.empreinte_base(), self.numerotation(), self.compteur("PVR", 26)
        with self.assertRaises(exc) as cm:
            f()
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.empreinte_base(), avant, "l'état de la base n'est pas restauré")
        if reservation:
            self.assertEqual(self.compteur("PVR", 26), n0 + 1)
            self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE numero=?", numero_initial(n0 + 1, D_PV))[0], 0)
        else:
            self.assertEqual(self.numerotation(), ns)
        return cm.exception


class Mini12(Base12):
    """Un BC (une ligne), un PV initial avec réserves (AR) et un PV initial sans réserves (SR) : jeu de base des tests de colonnes et de gardes.
    SANS_009 : supprime ensuite les triggers de 009 (les CHECK, l'index et les FK restent) pour éprouver les contraintes seules."""

    SANS_009 = False

    def setUp(self):
        super().setUp()
        self.m = self.bc()
        self.B = self.m.b
        self.AR = self.pv(self.B, AR)
        self.SR = self.pv(self.B, SR)
        if self.SANS_009:
            for nom in TRIGGERS_009:
                self.db.execute(f"DROP TRIGGER {nom}")

    def essai_pv(self, type_=SR, **kw):
        return self.tente(self.B, type_, **kw)

    def ok(self, type_=SR, **kw):
        self.ok_(self.essai_pv(type_, **kw))

    def ko(self, type_=SR, **kw):
        self.ko_check(self.essai_pv(type_, **kw))

    def essai_levee(self, parent=None, **kw):
        return self.tente_l(parent or self.AR, **kw)

    def ok_l(self, **kw):
        self.ok_(self.essai_levee(**kw))

    def ko_l(self, **kw):
        self.ko_check(self.essai_levee(**kw))


# ====================================================================================================================
# A — chaîne de migration et structure
# ====================================================================================================================
def base11_peuplee():
    """Base du rang 11 portant des BC facturés avec garanties déclenchées, un avoir et un encaissement : la migration 009 ne doit rien y changer."""
    t = G.Base11._sur(G.migrer11())
    bc = t.monde_g([[("100.00", ("decennale", "biennale")), ("50.00", ("parfait_achevement",))]])
    t.declencher(bc)
    t.monde_g([[("300.00", ("biennale",))]])
    return t


class Chaine(Base12):
    """Groupe A : 001 → … → 008 → 009, rang 12, aucune régression de la chaîne."""

    def test_T51_A_fichiers_de_la_chaine_dans_l_ordre(self):
        self.assertEqual([p.name for p in sorted(MIGRATIONS.glob("*.sql"))[:12]], list(NOMS))
        self.assertEqual(NOMS[-1], "009_pv.sql")
        self.assertEqual(len(NOMS), RANG)

    def test_T51_A_rang_et_user_version(self):
        db = G.migrer11()
        self.assertEqual(T.db_user_version(db), 11)
        T.appliquer(db, RANG, SQL_009)
        self.assertEqual(T.db_user_version(db), 12)
        self.assertEqual(T.db_user_version(self.db), 12)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_T51_A_le_protocole_de_reconstruction_du_runner_est_accepte(self):
        db = G.migrer11()
        T.runner(db, RANG, SQL_009)
        self.assertEqual(T.db_user_version(db), 12)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(T.objets(db), T.objets(self.db))

    def test_T51_A_le_fichier_ne_contient_que_des_creations_sans_transaction_ni_pragma_ni_donnee(self):
        code = code_sql()
        for interdit in (r"\bPRAGMA\b", r"\bCOMMIT\b", r"\bROLLBACK\b", r"\bSAVEPOINT\b", r"BEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)",
                         r"\bALTER\b", r"\bDROP\b", r"\bINSERT\s+INTO\b", r"\bUPDATE\s+\w+\s+SET\b", r"\bDELETE\s+FROM\b", r"\bREPLACE\s+INTO\b",
                         r"\bINSERT\s+OR\b", r"\bCREATE\s+(VIEW|TEMP|TEMPORARY|VIRTUAL)\b", r"\bRETURNING\b", r"\bON\s+UPDATE\b", r"\bCASCADE\b",
                         r"\bON\s+CONFLICT\b", r"\bREAL\b", r"\bFLOAT\b", r"\bDOUBLE\b", r"\bNUMERIC\b", r"\bCREATE\s+UNIQUE\b",
                         r"\bnumerotation_sequences\b", r"\bgaranties\b", r"\bfactures\b", r"\breglements\b", r"\bbons_commande\s*\)?\s*(SET|WHERE)\b",
                         r"\blegacy_numero\b", r"\bplanning\b", r"\bV2\b", r"\bsqlite_master\b"):
            self.assertIsNone(re.search(interdit, code, re.I), interdit)
        sts = [T.sans_commentaires(s).strip() for s in T.instructions(SQL_009)]
        genres = [re.match(r"CREATE\s+(UNIQUE\s+)?(TABLE|INDEX|TRIGGER)", s).group(0).split()[-1] for s in sts]
        self.assertEqual({g_: genres.count(g_) for g_ in ("TABLE", "INDEX", "TRIGGER")}, {"TABLE": 1, "INDEX": 1, "TRIGGER": 3})
        self.assertEqual(len(sts), 5)
        self.assertTrue(all(s.endswith(";") for s in sts))

    def test_T51_A_les_messages_des_triggers_sont_ASCII_et_portent_un_invariant(self):
        messages = re.findall(r"RAISE\s*\(\s*ABORT\s*,\s*'((?:[^']|'')*)'\s*\)", code_sql())
        self.assertEqual(len(messages), 6)                                                   # 1 + 1 + 4
        for m in messages:
            self.assertTrue(m.isascii(), m)
            self.assertRegex(m, r"^INV-(06|26|96): ")
        self.assertEqual(sorted(re.match(r"INV-(\d+)", m).group(1) for m in messages), ["06", "26", "26", "96", "96", "96"])

    def test_T51_A_objets_exacts_au_rang_12(self):
        self.assertEqual(T.noms(self.db, "table") - {"sqlite_sequence"}, F.TABLES_RANG9 | {"reglements", "garanties", "pv"})
        self.assertEqual(T.noms(self.db, "view"), set())
        nommes = {n for n in T.noms(self.db, "index") if not n.startswith("sqlite_")}
        self.assertEqual(nommes, T.INDEXES_RANG7 | F.INDEXES_006 | set(R.INDEXES_007) | set(G.INDEXES_008) | set(INDEXES_009))
        triggers12 = T.noms(self.db, "trigger")
        triggers11 = T.noms(G.migrer11(), "trigger")
        self.assertEqual(triggers12 - triggers11, set(TRIGGERS_009))
        self.assertEqual(triggers11 - triggers12, set())
        for nom, table in TRIGGERS_009.items():
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], table, nom)
        for nom, col in INDEXES_009.items():
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], "pv", nom)
            self.assertEqual([r_[2] for r_ in self.tous(f"PRAGMA index_info({nom})")], [col], nom)
            self.assertEqual(self.un("SELECT [unique] FROM pragma_index_list('pv') WHERE name=?", nom)[0], 0, nom)

    def test_T51_A_les_objets_du_rang_11_sont_identiques_au_caractere_pres(self):
        o11 = {(t, n, tb): s for t, n, tb, s in T.objets(G.migrer11())}
        o12 = {(t, n, tb): s for t, n, tb, s in T.objets(self.db)}
        self.assertEqual(set(o12) - set(o11), {("table", "pv", "pv")} | {("index", n, "pv") for n in INDEXES_009} | {("trigger", n, t) for n, t in TRIGGERS_009.items()})
        self.assertEqual(set(o11) - set(o12), set())
        for cle, sql in o11.items():
            self.assertEqual(o12[cle], sql, cle)

    def test_T51_A_aucune_donnee_n_est_modifiee_par_la_migration(self):
        t11 = base11_peuplee()
        avant = T.tout(t11.db)
        self.assertTrue(avant["factures"] and avant["bons_commande"] and avant["garanties"] and avant["numerotation_sequences"])
        T.appliquer(t11.db, RANG, SQL_009)
        apres = T.tout(t11.db)
        self.assertEqual(apres.pop("pv"), [])
        self.assertEqual(apres, avant)                                                       # y compris sqlite_sequence : rien pour la nouvelle table
        self.assertEqual(T.db_user_version(t11.db), 12)
        self.assertEqual(t11.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(t11.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_T51_A_schema_identique_base_fraiche_et_base_migree_peuplee(self):
        t = base11_peuplee()
        T.appliquer(t.db, RANG, SQL_009)
        self.assertEqual(T.objets(t.db), T.objets(self.db))

    def test_T51_A_atomicite_un_echec_n_importe_ou_annule_tout(self):
        points = ["CREATE TABLE pv (", "CREATE INDEX idx_pv_bc_id", "CREATE TRIGGER tr_40_pv_no_update", "CREATE TRIGGER tr_40_pv_no_delete", "CREATE TRIGGER tr_41_pv_insert"]
        db0 = G.migrer11()
        avant = T.objets(db0)
        for point in points:
            with self.subTest(point=point):
                self.assertEqual(SQL_009.count(point), 1, point)
                coupe = SQL_009.replace(point, "SELECT * FROM table_qui_n_existe_pas;\n" + point, 1)
                db = G.migrer11()
                with self.assertRaises(sqlite3.Error):
                    T.runner(db, RANG, coupe)
                self.assertFalse(db.in_transaction)
                self.assertEqual(T.db_user_version(db), 11)
                self.assertEqual(T.objets(db), avant)
        with self.subTest(point="apres la derniere instruction"):
            db = G.migrer11()
            with self.assertRaises(sqlite3.Error):
                T.runner(db, RANG, SQL_009 + "\nSELECT * FROM table_qui_n_existe_pas;\n")
            self.assertEqual(T.db_user_version(db), 11)
            self.assertEqual(T.objets(db), avant)

    def test_T51_A_rejeu_sur_une_base_deja_au_rang_12_est_refuse_sans_effet(self):
        avant = T.objets(self.db)
        with self.assertRaises(sqlite3.Error):
            T.runner(self.db, RANG, SQL_009)
        self.assertEqual(T.objets(self.db), avant)
        self.assertEqual(T.db_user_version(self.db), 12)

    def test_T51_A_table_stricte_et_colonnes_exactes(self):
        self.assertEqual(self.un("SELECT strict FROM pragma_table_list WHERE name='pv'")[0], 1)
        cols = self.tous("PRAGMA table_info(pv)")
        self.assertEqual([x[1] for x in cols], COLONNES_PV)
        self.assertEqual({x[1]: x[2] for x in cols},
                         {"id": "INTEGER", "numero": "TEXT", "bc_id": "INTEGER", "type": "TEXT", "date_reception": "TEXT", "client_snapshot": "TEXT",
                          "client_snapshot_version": "INTEGER", "entreprise_snapshot": "TEXT", "entreprise_snapshot_version": "INTEGER", "chantier_snapshot": "TEXT",
                          "chantier_snapshot_version": "INTEGER", "observations": "TEXT", "reserves": "TEXT", "origine_pv_id": "INTEGER", "suffixe": "INTEGER",
                          "created_at": "TEXT", "origine": "TEXT", "legacy_id": "TEXT", "legacy_data": "TEXT"})
        self.assertEqual({x[1] for x in cols if x[3]}, set(NOT_NULL_PV))
        self.assertEqual([x[1] for x in cols if x[5]], ["id"])
        defauts = {x[1]: x[4] for x in cols if x[4] is not None}
        self.assertEqual(set(defauts), {"created_at", "origine"})
        self.assertIn("strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", defauts["created_at"])
        self.assertEqual(defauts["origine"], "'v6'")
        self.assertIn("AUTOINCREMENT", self.un("SELECT sql FROM sqlite_master WHERE name='pv'")[0])

    def test_T51_A_colonnes_absentes_et_aucune_colonne_derivee_ni_legacy_numero(self):
        cols = {x[1] for x in self.tous("PRAGMA table_info(pv)")}
        for absente in ("statut", "etat", "actif", "updated_at", "legacy_numero", "client_id", "annee", "sequence", "signataire", "signature", "date_levee",
                        "pv_origine", "motif", "cancelled_at", "frozen_at", "pdf", "document", "garantie_id", "facture_id"):
            self.assertNotIn(absente, cols)

    def test_T51_A_deux_cles_etrangeres_en_restrict_sans_on_update(self):
        fk = {r_[3]: (r_[2], r_[4], r_[5], r_[6]) for r_ in self.tous("PRAGMA foreign_key_list(pv)")}
        self.assertEqual(fk, {"bc_id": ("bons_commande", "id", "NO ACTION", "RESTRICT"), "origine_pv_id": ("pv", "id", "NO ACTION", "RESTRICT")})

    def test_T51_A_index_exacts_unicite_et_aucun_index_redondant(self):
        liste = self.tous("SELECT name, [unique], origin FROM pragma_index_list('pv') ORDER BY name")
        autos = {n for n, _, o in liste if o in ("u", "pk")}
        self.assertEqual({n for n, _, _ in liste}, set(INDEXES_009) | autos)
        self.assertEqual(len(autos), 2)
        uniques = {tuple(r_[2] for r_ in self.tous(f"PRAGMA index_info({n})")) for n, u, _ in liste if u}
        self.assertEqual(uniques, {("numero",), ("origine_pv_id", "suffixe")})
        for nom in INDEXES_009:
            self.assertEqual(len(self.tous(f"PRAGMA index_info({nom})")), 1, nom)
        plan = " ".join(str(r_) for r_ in self.tous("EXPLAIN QUERY PLAN SELECT * FROM pv WHERE origine_pv_id = 1"))
        self.assertIn("sqlite_autoindex_pv_", plan)                                          # l'index du UNIQUE couvre la FK origine_pv_id : aucun index dédié
        plan = " ".join(str(r_) for r_ in self.tous("EXPLAIN QUERY PLAN SELECT * FROM pv WHERE numero = 'x'"))
        self.assertIn("sqlite_autoindex_pv_", plan)

    def test_T51_A_chaque_cle_etrangere_est_couverte_par_un_index_de_tete(self):
        tetes = {self.tous(f"PRAGMA index_info({n})")[0][2] for (n,) in self.tous("SELECT name FROM pragma_index_list('pv')")}
        self.assertEqual(tetes, {"bc_id", "origine_pv_id", "numero"})

    def test_T51_A_les_triggers_de_009_sont_before_et_ne_font_que_garder(self):
        attendu = {"tr_40_pv_no_update": "UPDATE", "tr_40_pv_no_delete": "DELETE", "tr_41_pv_insert": "INSERT"}
        for nom in TRIGGERS_009:
            sql = self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0]
            self.assertRegex(sql, rf"CREATE TRIGGER \w+\s+BEFORE {attendu[nom]} ON pv", nom)
            corps = sql[sql.index("BEGIN"):]
            for interdit in (r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bREPLACE\b", r"\bDROP\b"):
                self.assertIsNone(re.search(interdit, corps, re.I), (nom, interdit))
            self.assertTrue(all(re.match(r"\s*(SELECT RAISE|--)", frag) or not frag.strip()
                                for frag in re.split(r";", T.sans_commentaires(corps).split("BEGIN", 1)[1].rsplit("END", 1)[0])), nom)
        self.assertRegex(self.un("SELECT sql FROM sqlite_master WHERE name='tr_41_pv_insert'")[0], r"WHEN\s+NEW\.type\s*=\s*'levee_reserves'")

    def test_T51_A_noms_des_triggers_au_format_des_tranches_precedentes(self):
        for nom in TRIGGERS_009:
            self.assertRegex(nom, r"^tr_\d{2}_\w+$")
        self.assertEqual({n[:5] for n in TRIGGERS_009}, {"tr_40", "tr_41"})

    def test_T51_A_aucune_sequence_ni_ligne_creee_par_la_migration(self):
        self.assertEqual(self.un("SELECT count(*) FROM numerotation_sequences")[0], 0)
        self.assertNotIn("numerotation_sequences", code_sql())
        db = migrer12()                                                                      # base fraîche : aucune désynchronisation d'identifiants
        self.assertEqual(db.execute("SELECT count(*) FROM pv").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT * FROM sqlite_sequence WHERE name='pv'").fetchall(), [])

    def test_T51_A_les_ids_croissent_et_les_identifiants_des_tables_sont_distincts(self):
        m = self.bc()
        p1 = self.pv(m.b, AR)
        p2 = self.pv(m.b, SR)
        self.assertEqual((p1, p2), (106, 107))                                               # AUTOINCREMENT désynchronisé à 105
        self.assertEqual(len({m.b, p1, p2}), 3)

    def test_T51_A_les_requetes_de_suivi_utilisent_les_index_prevus(self):
        for sql, idx in (("SELECT * FROM pv WHERE bc_id = 1", "idx_pv_bc_id"),
                         ("SELECT * FROM pv WHERE numero = 'PVR-00001-26'", "sqlite_autoindex_pv_"),
                         ("SELECT * FROM pv WHERE origine_pv_id = 1", "sqlite_autoindex_pv_"),
                         ("SELECT * FROM pv WHERE origine_pv_id = 1 AND suffixe = 1", "sqlite_autoindex_pv_")):
            with self.subTest(requete=sql):
                plan = " | ".join(r_[3] for r_ in self.db.execute("EXPLAIN QUERY PLAN " + sql))
                self.assertIn(idx, plan)

    def test_T51_A_la_connexion_de_test_a_les_reglages_de_D_39(self):
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)


# ====================================================================================================================
# B — CHECK de colonnes (sans les triggers de 009 : seules les contraintes sont éprouvées)
# ====================================================================================================================
C_TYPE = "type IN ("
C_DATE = "date_reception GLOB"
C_LEVEE = "(type = 'levee_reserves') = (origine_pv_id IS NOT NULL)"
C_SUFFIXE_PRESENT = "(origine_pv_id IS NOT NULL) = (suffixe IS NOT NULL)"
C_SUFFIXE_BORNES = "suffixe IS NULL OR suffixe BETWEEN 1 AND 99"
C_RESERVES = "(reserves IS NOT NULL) = (type = 'reception_avec_reserves')"
C_NUMERO_VIDE = "numero <> ''"
C_LEGACY_V6 = "origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)"
C_NUMERO_V6 = "numero GLOB 'PVR-"
C_CREATED = "created_at GLOB"
C_ORIGINE = "origine IN ('v6', 'import')"
C_LEGACY_JSON = "json_valid(legacy_data)"
C_UNIQUE_NUMERO = "UNIQUE constraint failed: pv.numero"
C_UNIQUE_SUFFIXE = "UNIQUE constraint failed: pv.origine_pv_id, pv.suffixe"


class CheckPV(Mini12):
    """Groupe B : chaque terme d'un CHECK est arrêté par au moins un jeu de valeurs ; chaque valeur valide est acceptée. Le message de l'erreur identifie la contrainte."""

    SANS_009 = True

    def ko_f(self, fragment, type_=SR, **kw):
        m = self.essai_pv(type_, **kw)
        self.ko_check(m)
        self.assertIn(fragment, m)

    def ko_lf(self, fragment, **kw):
        m = self.essai_levee(**kw)
        self.ko_check(m)
        self.assertIn(fragment, m)

    # --- ligne minimale, défauts -----------------------------------------------------------------------------------------
    def test_T51_B_ligne_minimale_valide_et_defauts(self):
        pid = self.pv(self.B, SR, created_at=OMIT, origine=OMIT)
        r_ = self.un("SELECT origine, created_at, observations, reserves, origine_pv_id, suffixe, legacy_id, legacy_data FROM pv WHERE id=?", pid)
        self.assertEqual(r_[0], "v6")
        self.assertRegex(r_[1], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
        self.assertEqual(r_[2:], (None,) * 6)

    def test_T51_B_created_at_par_defaut_est_l_instant_courant_utc(self):
        pid = self.pv(self.B, SR, created_at=OMIT)
        ts = self.un("SELECT created_at FROM pv WHERE id=?", pid)[0]
        t = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)
        self.assertLess(abs((datetime.datetime.now(datetime.timezone.utc) - t).total_seconds()), 60)

    def test_T51_B_les_deux_types_initiaux_sont_acceptes_et_la_levee_avec_son_origine(self):
        self.ok(SR)
        self.ok(AR)
        self.ok_l()

    # --- type ------------------------------------------------------------------------------------------------------------
    def test_T51_B_type_hors_liste_refuse(self):
        for t in ("", "reception", "Reception_sans_reserves", "RECEPTION_SANS_RESERVES", "reception_sans_reserves ", " reception_sans_reserves", "levee", "levee_reserve",
                  "reception_avec_reserves_", "provisoire", "definitive", "autre", "0", 0, 1):
            with self.subTest(type=t):
                m = self.essai_pv(t, reserves=OMIT if t != AR else "x")
                self.ko_check(m)
                self.assertTrue(C_TYPE in m or "reserves" in m or "type" in m, m)

    def test_T51_B_type_hors_liste_refuse_par_son_propre_check(self):
        for t in ("", "reception", "Reception_sans_reserves", "levee", "autre"):
            with self.subTest(type=t):
                self.ko_f(C_TYPE, t)

    def test_T51_B_type_null_refuse(self):
        m = self.essai_pv(None)
        self.ko_check(m)
        self.assertIn("NOT NULL constraint failed: pv.type", m)

    # --- date_reception (famille D, aucune borne d'année en SQL) -----------------------------------------------------------------
    def test_T51_B_date_reception_valide_acceptee(self):
        for d in ("2026-10-20", "2026-02-28", "2028-02-29", "2000-02-29", "2026-01-01", "2026-12-31", "2000-01-01", "1999-12-31", "2100-02-28", "2100-12-31", "0000-01-01", "0001-01-01",
                  "9999-12-31"):
            with self.subTest(date=d):
                self.ok(SR, date_reception=d)
                self.ok(AR, date_reception=d)

    def test_T51_B_date_reception_invalide_refusee(self):
        for d in F_DATES_INVALIDES + ("", "2026-10-20T10:00:00Z", "2026-10-20 ", " 2026-10-20", "20261020", "2026/10/20", "2026-10-2", "26-10-20", "now", "2026-10-20\n",
                                       "2026-10-20 10:00", "abcd-ef-gh", "10000-01-01"):
            with self.subTest(date=repr(d)):
                self.ko_f(C_DATE, SR, date_reception=d)

    def test_T51_B_date_reception_null_refusee(self):
        m = self.essai_pv(SR, date_reception=None)
        self.ko_check(m)
        self.assertIn("NOT NULL constraint failed: pv.date_reception", m)

    def test_T51_B_date_reception_now_est_une_violation_de_contrainte_et_non_une_erreur_d_evaluation(self):
        """date('now') = date du jour, donc différente de la chaîne 'now' : la contrainte refuse. Avec OR IGNORE la ligne est ignorée (aucune levée d'erreur du CHECK)."""
        avant = self.un("SELECT COUNT(*) FROM pv")[0]
        cols = self.cols_pv(self.B, SR, date_reception="now", numero="PVR-00099-26")
        n = self.db.execute("INSERT OR IGNORE INTO pv (" + ", ".join(cols) + ") VALUES (" + ", ".join("?" * len(cols)) + ")", tuple(cols.values())).rowcount
        self.assertEqual(n, 0)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], avant)

    # --- created_at ------------------------------------------------------------------------------------------------------------
    def test_T51_B_created_at_canonique_accepte_et_hors_format_refuse(self):
        for ts in ("2026-10-20T10:00:00.000Z", "2026-10-20T00:00:00.123Z", "1999-01-01T23:59:59.999Z"):
            with self.subTest(ts=ts):
                self.ok(SR, created_at=ts)
        for ts in ("", "2026-10-20", "2026-10-20T10:00:00Z", "2026-10-20 10:00:00.000Z", "2026-10-20T10:00:00.000", "2026-10-20T10:00:00.00Z", "2026-10-20T10:00:00.0000Z",
                   "2026-10-20T10:00:00.000z", " 2026-10-20T10:00:00.000Z", "2026-10-20T10:00:00.000Z ", "x", "20261020T100000.000Z"):
            with self.subTest(ts=repr(ts)):
                self.ko_f(C_CREATED, SR, created_at=ts)

    # --- NOT NULL ------------------------------------------------------------------------------------------------------------
    def test_T51_B_NOT_NULL_explicite_refuse_sur_chaque_colonne(self):
        self.assertEqual(len(NOT_NULL_PV), 12)
        for c in NOT_NULL_PV:
            with self.subTest(colonne=c):
                m = self.essai_pv(SR, **{c: None})
                self.ko_check(m)
                self.assertIn(f"NOT NULL constraint failed: pv.{c}", m)

    def test_T51_B_colonne_omise_refusee_sauf_defauts(self):
        sans_defaut = [c for c in NOT_NULL_PV if c not in ("created_at", "origine")]
        self.assertEqual(len(sans_defaut), 10)
        for c in sans_defaut:
            with self.subTest(colonne=c):
                m = self.essai_pv(SR, **{c: OMIT})
                self.ko_check(m)
                self.assertIn(f"NOT NULL constraint failed: pv.{c}", m)
        self.ok(SR, created_at=OMIT)
        self.ok(SR, origine=OMIT)

    # --- snapshots ----------------------------------------------------------------------------------------------------------
    def test_T51_B_snapshots_json_invalide_refuse_valide_accepte(self):
        for c in ("client_snapshot", "entreprise_snapshot", "chantier_snapshot"):
            for bad in ("", "x", "{", '{"a":1', "undefined", "{'a':1}", "[1,", "nul"):
                with self.subTest(colonne=c, valeur=bad):
                    self.ko_f(f"json_valid({c})", SR, **{c: bad})
            for good in ("{}", "[]", '{"nom":"Dupont"}', "null", "1", '"x"', "true"):
                with self.subTest(colonne=c, valeur=good):
                    self.ok(SR, **{c: good})

    def test_T51_B_versions_de_snapshot_typees_entier(self):
        for c in ("client_snapshot_version", "entreprise_snapshot_version", "chantier_snapshot_version"):
            with self.subTest(colonne=c):
                self.ok(SR, **{c: 1})
                self.ok(SR, **{c: "2"})                                                      # coercition STRICT sans perte
                for bad in ("a", 1.5, b"1", ""):
                    m = self.essai_pv(SR, **{c: bad})
                    self.ko_check(m)
                    self.assertIn("cannot store", m)

    # --- levée <=> origine <=> suffixe ----------------------------------------------------------------------------------------
    def test_T51_B_les_huit_combinaisons_type_levee_origine_suffixe(self):
        attendu = {(False, False, False): True, (True, True, True): True,
                   (False, False, True): False, (False, True, False): False, (False, True, True): False,
                   (True, False, False): False, (True, False, True): False, (True, True, False): False}
        self.assertEqual(len(attendu), 8)
        for (est_levee, a_origine, a_suffixe), valide in attendu.items():
            with self.subTest(levee=est_levee, origine=a_origine, suffixe=a_suffixe):
                if est_levee and a_origine and a_suffixe:
                    self.ok_l()
                    continue
                kw = {}
                if a_origine:
                    kw["origine_pv_id"] = self.AR
                if a_suffixe:
                    kw["suffixe"] = 1
                type_ = LV if est_levee else SR
                if valide:
                    self.ok(type_, **kw)
                else:
                    m = self.essai_pv(type_, **kw)
                    self.ko_check(m)
                    self.assertTrue(C_LEVEE in m or C_SUFFIXE_PRESENT in m, m)

    def test_T51_B_chaque_terme_levee_origine_suffixe_est_arrete_par_sa_contrainte(self):
        self.ko_f(C_LEVEE, SR, origine_pv_id=self.AR, suffixe=1)                             # PV initial avec origine et suffixe
        self.ko_f(C_LEVEE, AR, origine_pv_id=self.AR, suffixe=1)
        self.ko_f(C_LEVEE, LV)                                                               # levée sans origine ni suffixe
        self.ko_f(C_SUFFIXE_PRESENT, SR, suffixe=3)                                          # suffixe sans origine, type initial
        self.ko_f(C_SUFFIXE_PRESENT, LV, suffixe=OMIT, origine_pv_id=self.AR)                # levée avec origine mais sans suffixe
        self.ko_f(C_LEVEE, LV, suffixe=1)                                                    # levée sans origine mais avec suffixe : les deux contraintes tombent, la 1re est citée

    # --- suffixe -------------------------------------------------------------------------------------------------------------
    def test_T51_B_suffixe_de_1_a_99_accepte(self):
        for s in (1, 2, 9, 10, 50, 98, 99):
            with self.subTest(suffixe=s):
                self.ok_l(suffixe=s)

    def test_T51_B_suffixe_hors_de_1_a_99_refuse(self):
        for s in (0, -1, 100, 101, 255, 1000, -99):
            with self.subTest(suffixe=s):
                self.ko_lf(C_SUFFIXE_BORNES, suffixe=s)

    def test_T51_B_suffixe_mal_type_refuse(self):
        for s in ("a", 2.5, b"1", "1.5"):
            with self.subTest(suffixe=s):
                m = self.essai_levee(suffixe=s, numero="PVR-00001-26-01")
                self.ko_check(m)
        m = self.essai_levee(suffixe="2", numero="PVR-00001-26-02")
        self.assertIsNone(m, m)                                                              # coercition STRICT sans perte

    def test_T51_B_suffixe_unique_par_origine(self):
        self.levee(self.AR)
        self.ko_lf(C_UNIQUE_SUFFIXE, suffixe=1, numero="PVR-00001-26-99")
        m = self.tente_l(self.AR, suffixe=2)
        self.assertIsNone(m, m)

    def test_T51_B_un_meme_suffixe_est_permis_sous_deux_origines_differentes(self):
        ar2 = self.pv(self.B, AR)
        self.levee(self.AR)
        self.ok_(self.tente_l(ar2))                                                          # suffixe 1 sous une autre origine
        self.assertEqual(self.levee(ar2) and self.levees_de(ar2)[0][0], 1)

    def test_T51_B_unicite_origine_suffixe_n_est_pas_applicable_aux_pv_initiaux(self):
        """UNIQUE (origine_pv_id, suffixe) avec NULL ne contraint pas les PV initiaux : autant de PV initiaux que voulu."""
        for _ in range(5):
            self.pv(self.B, SR)
            self.pv(self.B, AR)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE origine_pv_id IS NULL")[0], 12)

    # --- reserves <=> réception avec réserves ---------------------------------------------------------------------------------
    def test_T51_B_reserves_exigees_si_et_seulement_si_reception_avec_reserves(self):
        self.ok(AR, reserves="Reprise de la peinture")
        self.ko_f(C_RESERVES, AR, reserves=None)
        self.ko_f(C_RESERVES, SR, reserves="x")
        self.ko_f(C_RESERVES, SR, reserves="")
        self.ko_lf(C_RESERVES, reserves="x")
        self.ok(SR, reserves=None)
        self.ok_l(reserves=None)

    def test_T51_B_reserves_vide_acceptee_pour_une_reception_avec_reserves_CONSTAT_QO_4(self):
        """CONSTAT, pas une règle : le texte vide n'est pas refusé par le schéma (QO-4 non spécifiée) ; le contrôle éventuel est au service."""
        self.ok(AR, reserves="")
        self.ok(AR, reserves=" ")

    def test_T51_B_observations_libres(self):
        for o in (None, "", "RAS", "é" * 5000):
            with self.subTest(obs=o[:5] if o else o):
                self.ok(SR, observations=o)
                self.ok(AR, observations=o)
                self.ok_l(observations=o)

    # --- numero ------------------------------------------------------------------------------------------------------------
    def test_T51_B_numero_vide_ou_null_refuse(self):
        self.ko_f(C_NUMERO_VIDE, SR, numero="", origine="import")                            # import : seule la non-vacuité s'applique
        m = self.essai_pv(SR, numero=None)
        self.ko_check(m)
        self.assertIn("NOT NULL constraint failed: pv.numero", m)

    def test_T51_B_numero_unique(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        self.ko_f(C_UNIQUE_NUMERO, SR, numero=n)
        self.ko_f(C_UNIQUE_NUMERO, AR, numero=n)
        n2 = self.un("SELECT numero FROM pv WHERE id=?", self.AR)[0]
        self.ko_f(C_UNIQUE_NUMERO, SR, numero=n2)

    def test_T51_B_numero_d_un_pv_initial_v6_au_format_PVR_nnnnn_yy(self):
        for n in ("PVR-50001-26", "PVR-12345-26", "PVR-99999-26", "PVR-00000-26"):
            with self.subTest(numero=n):
                self.ok(SR, numero=n)
                self.ok(AR, numero=n)

    def test_T51_B_numero_initial_v6_hors_format_refuse(self):
        for n in ("PVR-0001-26", "PVR-000001-26", "PVR-00001-2026", "PVR-00001-6", "PVR-0000a-26", "pvr-00001-26", "PVR_00001_26", " PVR-00001-26", "PVR-00001-26 ",
                  "PVR-00001-26\n", "PVR-00001-26-01", "PVR-00001-26-1", "FAC-00001-26", "PV-00001-26", "PVR-00001-26x", "xPVR-00001-26", "PVR-00001-2a", "PVR--0001-26",
                  "PVR-0000-126", "PVR-00001-", "PVR-00001", "00001-26", "PVR-٠٠٠٠١-26", "x"):
            with self.subTest(numero=repr(n)):
                self.ko_f(C_NUMERO_V6, SR, numero=n)
                self.ko_f(C_NUMERO_V6, AR, numero=n)

    def test_T51_B_annee_du_numero_egale_a_l_annee_de_date_reception(self):
        self.ok(SR, date_reception="2026-12-31", numero="PVR-50001-26")
        self.ok(SR, date_reception="2027-01-01", numero="PVR-50001-27")
        self.ko_f(C_NUMERO_V6, SR, date_reception="2026-10-20", numero="PVR-50001-27")
        self.ko_f(C_NUMERO_V6, SR, date_reception="2027-01-01", numero="PVR-50001-26")
        self.ko_f(C_NUMERO_V6, SR, date_reception="2026-12-31", numero="PVR-50001-25")
        self.ko_f(C_NUMERO_V6, AR, date_reception="2026-12-31", numero="PVR-50001-25")

    def test_T51_B_le_schema_ne_borne_pas_l_annee_CONSTAT_INV_177(self):
        """CONSTAT : INV-177 / D-38 : la borne 2001-2099 est un contrôle du SERVICE ; le schéma accepte 2000, 2100 et au-delà dès que le numéro est cohérent."""
        self.ok(SR, date_reception="2000-06-01", numero="PVR-50001-00")
        self.ok(SR, date_reception="2100-06-01", numero="PVR-50001-00")
        self.ok(SR, date_reception="2126-06-01", numero="PVR-50001-26")                      # le schéma ne lit que les 2 chiffres de l'année

    def test_T51_B_le_format_ne_s_applique_pas_a_la_levee_CONSTAT_PR_3(self):
        """CONSTAT PR-3 : aucun CHECK de format pour la levée (la forme est portée par TR-41 / G4, éprouvée au groupe D). Sans trigger, toute valeur non vide convient."""
        for n in ("PVR-00001-26-01", "x", "PVR-00001-27-05", "n'importe quoi", "PVR-50001-26"):
            with self.subTest(numero=n):
                self.ok_l(numero=n)

    # --- octet NUL : GLOB, substr, length() de TEXT et json_valid s'arrêtent au premier octet NUL ; la longueur est contrôlée en octets -----------
    @staticmethod
    def variantes_nul(base):
        """Toutes les façons de placer un octet NUL dans `base` : final, suivi d'une queue (courte, longue), au début, seul, à la place de chaque caractère, inséré à chaque position."""
        v = [base + "\x00", base + "\x00junk", base + "\x00" + "x" * 60, "\x00" + base, "\x00", base + "\x00\x00"]
        v += [base[:i] + "\x00" + base[i + 1:] for i in range(len(base))]
        v += [base[:i] + "\x00" + base[i:] for i in range(len(base) + 1)]
        return list(dict.fromkeys(v))

    def test_T51_B_numero_initial_v6_octet_nul_refuse_a_toute_position(self):
        variantes = self.variantes_nul("PVR-50001-26")
        self.assertGreater(len(variantes), 25)
        for n in variantes:
            for t in (SR, AR):
                with self.subTest(numero=repr(n), type=t):
                    self.ko_f(C_NUMERO_V6, t, numero=n)

    def test_T51_B_numero_initial_v6_conforme_reste_accepte_et_fait_12_octets(self):
        for n, d in (("PVR-00001-01", "2001-03-04"), ("PVR-99999-99", "2099-12-31"), ("PVR-00000-00", "2000-01-01"), ("PVR-50001-26", "2026-10-20"), ("PVR-12345-27", "2027-01-01")):
            with self.subTest(numero=n):
                self.assertEqual(len(n.encode("utf-8")), 12)
                self.ok(SR, numero=n, date_reception=d)
                self.ok(AR, numero=n, date_reception=d)

    def test_T51_B_numero_avec_octet_nul_n_est_pas_un_doublon_accepte_par_UNIQUE(self):
        """Sans le contrôle de longueur, `PVR-x\\0` et `PVR-x` coexisteraient (UNIQUE compare les octets) : deux numéros affichés à l'identique."""
        existant = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        for suite in ("\x00", "\x00junk"):
            with self.subTest(suite=repr(suite)):
                m = self.essai_pv(SR, numero=existant + suite)
                self.ko_f(C_NUMERO_V6, SR, numero=existant + suite)
                self.assertNotIn("UNIQUE", m)

    def test_T51_B_created_at_octet_nul_refuse_a_toute_position(self):
        variantes = self.variantes_nul("2026-10-20T10:11:12.345Z")
        self.assertGreater(len(variantes), 50)
        for ts in variantes:
            with self.subTest(created_at=repr(ts)):
                self.ko_f(C_CREATED, SR, created_at=ts)
                self.ko_lf(C_CREATED, created_at=ts)                                       # la levée porte le même CHECK

    def test_T51_B_created_at_conforme_reste_accepte_et_fait_24_octets_y_compris_le_defaut(self):
        for ts in ("2026-10-20T10:00:00.000Z", "2026-10-20T23:59:59.999Z", "0000-01-01T00:00:00.000Z", "9999-12-31T23:59:59.999Z"):
            with self.subTest(ts=ts):
                self.assertEqual(len(ts.encode("utf-8")), 24)
                self.ok(SR, created_at=ts)
                self.ok_l(created_at=ts)
        pid = self.pv(self.B, SR, created_at=OMIT)
        self.assertEqual(self.un("SELECT length(CAST(created_at AS BLOB)), instr(CAST(created_at AS BLOB), x'00') FROM pv WHERE id=?", pid), (24, 0))

    CHAMPS_JSON = ("client_snapshot", "entreprise_snapshot", "chantier_snapshot", "legacy_data")

    def essai_json(self, champ, valeur):
        """Un PV portant `valeur` dans l'un des quatre champs JSON de 009 (`legacy_data` n'existe que pour origine='import')."""
        if champ == "legacy_data":
            return self.essai_pv(SR, origine="import", legacy_data=valeur)
        return self.essai_pv(SR, **{champ: valeur})

    def test_T51_B_json_octet_nul_brut_refuse_sur_les_quatre_champs(self):
        for c in self.CHAMPS_JSON:
            for bad in ("{}\x00", "{}\x00junk", "{}\x00" + "x" * 60, "\x00{}", "{\x00}", '{"a":"x\x00y"}', '{"a":"\x00"}', "\x00", "[]\x00", "1\x00", "null\x00"):
                with self.subTest(colonne=c, valeur=repr(bad)):
                    m = self.essai_json(c, bad)
                    self.ko_check(m)
                    self.assertIn(f"json_valid({c})", m)

    def test_T51_B_json_echappement_u0000_est_un_json_valide_distinct_de_l_octet_nul(self):
        """`\\u0000` (six caractères) est la forme JSON d'un NUL dans une chaîne : valide, stockée telle quelle, sans octet NUL."""
        for c in self.CHAMPS_JSON:
            for ok_ in ('{"a":"\\u0000"}', '"\\u0000"', '{"\\u0000":1}', '["\\u0000","x\\u0000y"]', '{"a":"\\\\u0000"}'):
                with self.subTest(colonne=c, valeur=ok_):
                    self.assertNotIn("\x00", ok_)
                    self.ok_(self.essai_json(c, ok_))
        for c, j in (("client_snapshot", '{"a":"\\u0000"}'), ("entreprise_snapshot", '"\\u0000"'), ("chantier_snapshot", '["\\u0000"]')):
            with self.subTest(stocke=c):
                pid = self.pv(self.B, SR, **{c: j})
                self.assertEqual(self.un(f"SELECT {c}, length(CAST({c} AS BLOB)), instr(CAST({c} AS BLOB), x'00') FROM pv WHERE id=?", pid), (j, len(j.encode("utf-8")), 0))
        pid = self.pv(self.B, SR, origine="import", legacy_data='{"k":"\\u0000"}')
        self.assertEqual(self.un("SELECT legacy_data, instr(CAST(legacy_data AS BLOB), x'00') FROM pv WHERE id=?", pid), ('{"k":"\\u0000"}', 0))

    def test_T51_B_json_valeurs_conformes_et_malformees_inchangees_sur_les_quatre_champs(self):
        for c in self.CHAMPS_JSON:
            for good in ("{}", "[]", '{"nom":"Dupont"}', "null", "1", '"x"', "true", '{"é":"日本"}', '{"a":[1,2,{"b":null}]}'):
                with self.subTest(colonne=c, valeur=good):
                    self.ok_(self.essai_json(c, good))
            for bad in ("", "x", "{", '{"a":1', "undefined", "{'a':1}", "[1,", "nul"):
                with self.subTest(colonne=c, valeur=bad):
                    m = self.essai_json(c, bad)
                    self.ko_check(m)
                    self.assertIn(f"json_valid({c})", m)

    def test_T51_B_legacy_data_null_reste_accepte_pour_un_pv_importe(self):
        self.ok(SR, origine="import", legacy_data=None)
        self.ok(SR, origine="import", legacy_data=None, legacy_id="L-1")

    # --- BLOC-IMP : comportement générique du schéma (aucun PV n'est importé de la V2) ----------------------------------------------
    def test_T51_B_origine_hors_liste_ou_null_refusee(self):
        for o in ("v7", "", "V6", "IMPORT", "Import", "import ", "v6 ", "manuel", 0):
            with self.subTest(origine=o):
                self.ko_f(C_ORIGINE, SR, origine=o)
        m = self.essai_pv(SR, origine=None)
        self.ko_check(m)
        self.assertIn("NOT NULL constraint failed: pv.origine", m)

    def test_T51_B_origine_import_accepte_un_numero_libre_non_vide(self):
        for n in ("ANCIEN-1", "pv 12/2019", "PVR-1", "x", "PVR-50001-26"):
            with self.subTest(numero=n):
                self.ok(SR, origine="import", numero=n)
                self.ok(AR, origine="import", numero=n, legacy_id="L1", legacy_data='{"a":1}')

    def test_T51_B_origine_import_legacy_optionnels_et_json_controle(self):
        self.ok(SR, origine="import", legacy_id=None, legacy_data=None, numero="I-1")
        self.ok(SR, origine="import", legacy_id="L-9", legacy_data=None, numero="I-2")
        self.ok(SR, origine="import", legacy_id=None, legacy_data="[]", numero="I-3")
        for bad in ("", "{", "x", "{'a':1}"):
            with self.subTest(legacy_data=bad):
                self.ko_f(C_LEGACY_JSON, SR, origine="import", legacy_data=bad, numero="I-4")

    def test_T51_B_origine_v6_exclut_les_champs_legacy(self):
        self.ko_f(C_LEGACY_V6, SR, origine="v6", legacy_id="L1")
        self.ko_f(C_LEGACY_V6, SR, origine="v6", legacy_data="{}")
        self.ko_f(C_LEGACY_V6, SR, origine="v6", legacy_id="L1", legacy_data="{}")
        self.ko_f(C_LEGACY_V6, SR, origine=OMIT, legacy_id="L1")                             # origine par défaut = v6
        self.ko_f(C_LEGACY_V6, SR, origine="v6", legacy_id="")

    def test_T51_B_origine_import_ne_dispense_ni_de_la_non_vacuite_ni_de_l_unicite(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        self.ko_f(C_UNIQUE_NUMERO, SR, origine="import", numero=n)
        self.ko_f(C_NUMERO_VIDE, SR, origine="import", numero="")

    # --- clés étrangères et types STRICT -------------------------------------------------------------------------------------------
    def test_T51_B_cles_etrangeres_existantes_exigees(self):
        for b in (0, -1, 99999):
            with self.subTest(bc=b):
                m = self.sous_savepoint(lambda: self.inserer_pv(self.cols_pv(self.B, SR, bc_id=b)))
                self.ko_check(m)
                self.assertIn("FOREIGN KEY constraint failed", m)
        for o in (0, -1, 99999):
            with self.subTest(origine=o):
                m = self.essai_levee(origine_pv_id=o)
                self.ko_check(m)
                self.assertIn("FOREIGN KEY constraint failed", m)

    def test_T51_B_une_levee_peut_cibler_n_importe_quel_pv_au_niveau_du_schema_seul(self):
        """Sans le trigger TR-41, le schéma n'impose rien sur le TYPE ni le BC de l'origine : c'est le rôle exclusif de tr_41 (groupe D)."""
        self.ok_l(origine_pv_id=self.SR, numero="X-01", suffixe=1)
        autre = self.bc()
        self.ok_(self.tente(autre.b, LV, origine_pv_id=self.AR, suffixe=1, numero="X-02"))

    def test_T51_B_types_stricts_refuses(self):
        for c, bad in (("bc_id", "x"), ("bc_id", 1.5), ("numero", b"PVR-50001-26"), ("type", b"x"), ("date_reception", b"2026-10-20"),
                       ("client_snapshot", b"{}"), ("observations", b"x")):
            with self.subTest(colonne=c, valeur=bad):
                m = self.essai_pv(SR, **{c: bad})
                self.ko_check(m)

    def test_T51_B_les_check_ne_dependent_pas_du_bc_ni_de_son_etat(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                m = self.bc(etat)
                self.ok_(self.tente(m.b, SR))
                self.ok_(self.tente(m.b, AR))

    # --- rigueur du format : chaque position est contrôlée (campagne de mutation : GLOB '?' à la place d'un chiffre) ------------------
    def test_T51_B_chaque_chiffre_du_numero_initial_v6_est_controle_individuellement(self):
        base = "PVR-50001-26"
        for i in list(range(4, 9)) + [10, 11]:
            for c in ("a", "-", " ", ".", "x", "é", "/"):
                n = base[:i] + c + base[i + 1:]
                with self.subTest(position=i, caractere=c):
                    self.ko_f(C_NUMERO_V6, SR, numero=n)
                    self.ko_f(C_NUMERO_V6, AR, numero=n)

    def test_T51_B_chaque_caractere_du_numero_initial_v6_est_controle_y_compris_longueur(self):
        base = "PVR-50001-26"
        for i in range(len(base)):
            with self.subTest(position=i):
                self.ko_f(C_NUMERO_V6, SR, numero=base[:i] + base[i + 1:])                         # un caractère de moins
                self.ko_f(C_NUMERO_V6, SR, numero=base[:i] + "0" + base[i:])                       # un caractère de plus
        self.ko_f(C_NUMERO_V6, SR, numero=base + "0")
        self.ko_f(C_NUMERO_V6, SR, numero="0" + base)

    def test_T51_B_chaque_position_de_created_at_est_controlee(self):
        ts = "2026-10-20T10:11:12.345Z"
        for i in range(len(ts)):
            for c in ("a", "X", " "):
                if ts[i] == c:
                    continue
                with self.subTest(position=i, caractere=c):
                    self.ko_f(C_CREATED, SR, created_at=ts[:i] + c + ts[i + 1:])
            with self.subTest(position=i, retrait=True):
                self.ko_f(C_CREATED, SR, created_at=ts[:i] + ts[i + 1:])
            with self.subTest(position=i, insertion=True):
                self.ko_f(C_CREATED, SR, created_at=ts[:i] + "0" + ts[i:])

    def test_T51_B_chaque_position_de_date_reception_est_controlee(self):
        d = "2026-10-20"
        for i in range(len(d)):
            for c in ("a", "X", " "):
                with self.subTest(position=i, caractere=c):
                    self.ko_f(C_DATE, SR, date_reception=d[:i] + c + d[i + 1:], numero="PVR-50001-26")
            with self.subTest(position=i, retrait=True):
                self.ko_f(C_DATE, SR, date_reception=d[:i] + d[i + 1:], numero="PVR-50001-26")
            with self.subTest(position=i, insertion=True):
                self.ko_f(C_DATE, SR, date_reception=d[:i] + "0" + d[i:], numero="PVR-50001-26")

    def test_T51_B_valeur_sentinelle_hors_liste_pour_type_et_origine(self):
        self.ko_f(C_TYPE, "zzz")
        self.ko_f(C_ORIGINE, SR, origine="zzz")
        self.ko_f(C_ORIGINE, SR, origine="import2")
        self.ko_f(C_ORIGINE, SR, origine="v")

    def test_T51_B_unicite_origine_suffixe_ne_depend_ni_du_bc_ni_de_la_date_ni_du_numero(self):
        """Mutation : UNIQUE (origine_pv_id, suffixe, bc_id) serait plus faible ; l'unicité porte sur la seule paire (origine, suffixe)."""
        self.levee(self.AR)
        autre = self.bc()
        self.ko_lf(C_UNIQUE_SUFFIXE, suffixe=1, bc_id=autre.b, numero="X-77")
        self.ko_lf(C_UNIQUE_SUFFIXE, suffixe=1, numero="X-78", date_reception="2020-01-01", observations="autre")


# ====================================================================================================================
# C — numérotation PVR (réservation par le SERVICE, émulée ; le schéma ne réserve rien)
# ====================================================================================================================
class Numerotation(Base12):
    """Groupe C : séquence PVR par année de date_reception (PT-1 : réservation committée avant l'objet, trous admis, plafond 99 999, TR-02 non applicable).
    La levée n'a ni séquence ni année propres. Les bornes d'année et le plafond sont des contrôles du SERVICE (INV-177, modèle §6)."""

    def test_T51_C_premier_pv_pvr_00001_et_compteur_de_l_annee(self):
        m = self.bc()
        p = self.creer_pv(m.b)
        self.assertEqual(p.numero, "PVR-00001-26")
        self.assertEqual(self.un("SELECT numero FROM pv WHERE id=?", p.id)[0], "PVR-00001-26")
        self.assertEqual(self.seq_pv(), [("PVR", 26, 1, None)])

    def test_T51_C_numeros_consecutifs_pour_les_deux_types(self):
        m = self.bc()
        ps = [self.creer_pv(m.b, t) for t in (SR, AR, SR, AR)]
        self.assertEqual([p.numero for p in ps], [f"PVR-0000{i}-26" for i in (1, 2, 3, 4)])
        self.assertEqual(self.compteur("PVR", 26), 4)

    def test_T51_C_la_sequence_est_globale_a_l_annee_et_non_propre_au_bc(self):
        m1, m2 = self.bc(), self.bc()
        a = self.creer_pv(m1.b)
        b = self.creer_pv(m2.b)
        c = self.creer_pv(m1.b)
        self.assertEqual([a.numero, b.numero, c.numero], ["PVR-00001-26", "PVR-00002-26", "PVR-00003-26"])

    def test_T51_C_l_annee_est_celle_de_date_reception_et_non_celle_de_l_horloge(self):
        m = self.bc()
        a = self.creer_pv(m.b, date="2027-01-05")
        b = self.creer_pv(m.b, date="2026-10-20")
        c = self.creer_pv(m.b, date="2027-12-31")
        d = self.creer_pv(m.b, date="2026-01-01")
        self.assertEqual([a.numero, b.numero, c.numero, d.numero], ["PVR-00001-27", "PVR-00001-26", "PVR-00002-27", "PVR-00002-26"])
        self.assertEqual(self.seq_pv(), [("PVR", 26, 2, None), ("PVR", 27, 2, None)])

    def test_T51_C_changement_d_annee_repart_a_un(self):
        m = self.bc()
        self.creer_pv(m.b, date="2026-12-31")
        p = self.creer_pv(m.b, date="2027-01-01")
        self.assertEqual(p.numero, "PVR-00001-27")

    def test_T51_C_bornes_d_annee_2001_et_2099_acceptees(self):
        m = self.bc()
        self.assertEqual(self.creer_pv(m.b, date="2001-01-01").numero, "PVR-00001-01")
        self.assertEqual(self.creer_pv(m.b, date="2099-12-31").numero, "PVR-00001-99")
        self.assertEqual(self.creer_pv(m.b, AR, date="2099-06-30").numero, "PVR-00002-99")

    def test_T51_C_annee_hors_2001_2099_refusee_par_le_service_sans_reservation(self):
        m = self.bc()
        for d in ("2000-12-31", "2100-01-01", "9999-12-31", "0000-01-01", "1999-12-31", "2000-01-01"):
            with self.subTest(date=d):
                self.echoue(AnneeHorsBornes, False, lambda d=d: self.creer_pv(m.b, date=d))
        self.assertEqual(self.seq_pv(), [])

    def test_T51_C_l_annee_2000_est_aussi_exclue_par_la_numerotation_de_001(self):
        """annee = 0 est réservé aux types CLI/FOU (001) : une séquence PVR de l'année 0 serait refusée. Raison technique de la borne basse 2001."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.un(ATTRIBUER, "PVR", 0)
        self.assertEqual(self.seq_pv(), [])

    def test_T51_C_le_type_pvr_est_accepte_par_la_numerotation_pour_les_annees_1_a_99(self):
        for yy in (1, 26, 99):
            self.assertEqual(self.un(ATTRIBUER, "PVR", yy)[0], 1)

    def test_T51_C_independance_vis_a_vis_des_autres_types_de_numero(self):
        m = self.bc()
        p = self.creer_pv(m.b)
        self.declencher(m)                                                                   # solde : FAC-00001-26
        q = self.creer_pv(m.b)
        types_ = {t: (a, n) for t, a, n, _ in self.sequences()}
        self.assertEqual(types_["PVR"], (26, 2))
        self.assertEqual(types_["FAC"], (26, 1))
        self.assertEqual((p.numero, q.numero), ("PVR-00001-26", "PVR-00002-26"))

    def test_T51_C_aucune_chronologie_TR_02_ni_derniere_date_pour_pvr(self):
        m = self.bc()
        self.creer_pv(m.b, date="2026-10-20")
        p = self.creer_pv(m.b, date="2026-01-05")                                            # date antérieure au PV précédent : acceptée
        q = self.creer_pv(m.b, date="2026-12-31")
        self.assertEqual([p.numero, q.numero], ["PVR-00002-26", "PVR-00003-26"])
        self.assertEqual(self.seq_pv(), [("PVR", 26, 3, None)])                           # derniere_date reste NULL

    def test_T51_C_plusieurs_pv_pour_un_meme_bc_et_une_meme_date_numeros_distincts_CONSTAT(self):
        """CONSTAT, pas une règle : le schéma n'impose aucune unicité de PV initial par BC ni par date."""
        m = self.bc()
        ps = [self.creer_pv(m.b, t, date="2026-10-20") for t in (SR, SR, AR, AR, SR)]
        self.assertEqual(len({p.numero for p in ps}), 5)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE bc_id=?", m.b)[0], 5)

    def test_T51_C_le_numero_persiste_est_celui_de_l_oracle_independant(self):
        m = self.bc()
        for i, d in enumerate(("2026-03-01", "2027-03-01", "2026-04-01", "2026-05-01"), 1):
            p = self.creer_pv(m.b, date=d)
            self.assertEqual(self.un("SELECT numero FROM pv WHERE id=?", p.id)[0], numero_initial(p.n, d))
            self.assertEqual(p.numero[-2:], d[2:4])

    # --- levée : aucune séquence ------------------------------------------------------------------------------------------------
    def test_T51_C_la_levee_ne_reserve_aucun_numero_et_ne_touche_aucune_sequence(self):
        m = self.bc()
        o = self.creer_pv(m.b, AR)
        avant = self.sequences()
        lv = [self.creer_levee(o.id) for _ in range(3)]
        self.assertEqual(self.sequences(), avant)
        self.assertEqual([x.numero for x in lv], [numero_levee(o.numero, i) for i in (1, 2, 3)])
        self.assertEqual(self.compteur("PVR", 26), 1)

    def test_T51_C_la_levee_n_a_pas_d_annee_propre_son_numero_derive_de_l_origine(self):
        m = self.bc()
        o = self.creer_pv(m.b, AR, date="2026-12-30")
        lv = self.creer_levee(o.id, date="2027-02-03")                                       # levée l'année suivante : le numéro garde l'année de l'origine
        self.assertEqual(lv.numero, "PVR-00001-26-01")
        self.assertEqual(self.seq_pv(), [("PVR", 26, 1, None)])

    def test_T51_C_une_levee_ne_decale_pas_le_numero_des_pv_initiaux_suivants(self):
        m = self.bc()
        o = self.creer_pv(m.b, AR)
        self.creer_levee(o.id)
        p = self.creer_pv(m.b, SR)
        self.assertEqual(p.numero, "PVR-00002-26")

    # --- plafond 99 999 -------------------------------------------------------------------------------------------------------------
    def test_T51_C_plafond_99999_erreur_explicite_avant_reservation(self):
        m = self.bc()
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('PVR', 26, 99998)")
        p = self.creer_pv(m.b)
        self.assertEqual(p.numero, "PVR-99999-26")                                           # le dernier numéro est accepté par le CHECK du format
        self.echoue(PlafondNumeros, False, lambda: self.creer_pv(m.b))
        self.assertEqual(self.compteur("PVR", 26), 99999)

    def test_T51_C_au_dela_de_99999_la_reservation_directe_est_refusee_par_001(self):
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('PVR', 26, 99999)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.un(ATTRIBUER, "PVR", 26)
        self.assertEqual(self.compteur("PVR", 26), 99999)

    def test_T51_C_le_plafond_d_une_annee_n_affecte_pas_les_autres(self):
        m = self.bc()
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('PVR', 26, 99999)")
        self.assertEqual(self.creer_pv(m.b, date="2027-02-02").numero, "PVR-00001-27")
        self.echoue(PlafondNumeros, False, lambda: self.creer_pv(m.b, date="2026-02-02"))

    # --- échecs avant réservation / après réservation ---------------------------------------------------------------------------------
    def test_T51_C_pre_controle_en_echec_ne_consomme_aucun_numero(self):
        m = self.bc()
        self.creer_pv(m.b)
        for f in (lambda: self.creer_pv(m.b, LV), lambda: self.creer_pv(9999999), lambda: self.creer_pv(m.b, "autre"),
                  lambda: self.creer_pv(m.b, SR, reserves="x"), lambda: self.creer_pv(m.b, AR, reserves=None)):
            self.echoue(ErreurService, False, f)
        self.assertEqual(self.compteur("PVR", 26), 1)

    def test_T51_C_echec_apres_reservation_laisse_un_trou_jamais_reutilise(self):
        m = self.bc()
        self.creer_pv(m.b)                                                                   # n° 1
        def boum(_t, _numero):
            raise DefautInjecte()
        self.echoue(DefautInjecte, True, lambda: self.creer_pv(m.b, apres_reservation=boum))          # n° 2 réservé puis perdu
        p = self.creer_pv(m.b)
        self.assertEqual(p.numero, "PVR-00003-26")
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE numero='PVR-00002-26'")[0], 0)

    def test_T51_C_echec_avant_commit_annule_le_pv_mais_conserve_la_reservation(self):
        m = self.bc()
        def boum(_t, _pid):
            raise DefautInjecte()
        self.echoue(DefautInjecte, True, lambda: self.creer_pv(m.b, avant_commit=boum))
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], 0)
        self.assertEqual(self.creer_pv(m.b).numero, "PVR-00002-26")

    def test_T51_C_la_reservation_est_committee_avant_la_transaction_de_l_objet(self):
        m = self.bc()
        vu = {}
        def sonde(t, numero):
            vu["en_transaction"] = t.db.in_transaction
            vu["compteur"] = t.compteur("PVR", 26)
            vu["pv"] = t.un("SELECT COUNT(*) FROM pv WHERE numero=?", numero)[0]
        self.creer_pv(m.b, apres_reservation=sonde)
        self.assertEqual(vu, {"en_transaction": False, "compteur": 1, "pv": 0})

    def test_T51_C_un_pv_levee_ne_se_cree_pas_par_le_service_initial(self):
        m = self.bc()
        with self.assertRaises(ErreurService):
            self.creer_pv(m.b, LV)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], 0)


# ====================================================================================================================
# D — levée de réserves : TR-41 (G1 à G4), triggers de 009 en place
# ====================================================================================================================
M_G1 = "INV-96: l'origine d'une levee doit etre un PV recu avec reserves"
M_G2 = "INV-96: la levee doit appartenir au meme bon de commande que son origine"
M_G3 = "INV-26: le suffixe d'une levee est le suffixe maximal de son origine plus un"
M_G4 = "INV-26: le numero d'une levee est celui de son origine suivi du suffixe"


class Levee(Mini12):
    """Groupe D : la levée exige une origine de type réception avec réserves, du même BC (G1, G2) ; suffixe = max des levées de l'origine + 1 (G3) ; numéro = numéro de l'origine +
    '-' + suffixe sur 2 chiffres (G4). Les gardes sont BEFORE INSERT : elles précèdent CHECK, NOT NULL, UNIQUE et FK. Aucune exemption selon l'origine du PV (INV-131)."""

    def nb(self):
        return self.un("SELECT COUNT(*) FROM pv")[0]

    def refus_g(self, m, message):
        self.assertIsNotNone(m, "levée acceptée à tort")
        self.assertIn(message, m)

    # --- cas acceptés --------------------------------------------------------------------------------------------------------
    def test_T51_D_premiere_levee_suffixe_1_numero_de_l_origine_plus_01(self):
        pid = self.levee(self.AR)
        r_ = self.un("SELECT type, bc_id, origine_pv_id, suffixe, numero, reserves, origine FROM pv WHERE id=?", pid)
        self.assertEqual(r_, (LV, self.B, self.AR, 1, "PVR-00001-26-01", None, "v6"))

    def test_T51_D_suffixes_successifs_et_numeros_a_deux_chiffres(self):
        numero_ar = self.un("SELECT numero FROM pv WHERE id=?", self.AR)[0]
        for i in range(1, 13):
            self.levee(self.AR)
        self.assertEqual(self.levees_de(self.AR), [(i, numero_levee(numero_ar, i)) for i in range(1, 13)])
        self.assertEqual(self.levees_de(self.AR)[0][1], "PVR-00001-26-01")
        self.assertEqual(self.levees_de(self.AR)[11][1], "PVR-00001-26-12")

    def test_T51_D_les_suffixes_sont_independants_d_une_origine_a_l_autre(self):
        ar2 = self.pv(self.B, AR)
        for _ in range(3):
            self.levee(self.AR)
        self.levee(ar2)
        self.assertEqual([s for s, _ in self.levees_de(ar2)], [1])
        self.levee(ar2)
        self.assertEqual([s for s, _ in self.levees_de(ar2)], [1, 2])
        self.assertEqual([s for s, _ in self.levees_de(self.AR)], [1, 2, 3])

    def test_T51_D_la_levee_herite_du_bc_de_son_origine_et_garde_le_numero_de_l_origine_en_prefixe(self):
        m2 = self.bc()
        ar2 = self.pv(m2.b, AR)
        pid = self.levee(ar2)
        self.assertEqual(self.un("SELECT bc_id FROM pv WHERE id=?", pid)[0], m2.b)
        self.assertTrue(self.un("SELECT numero FROM pv WHERE id=?", pid)[0].startswith(self.un("SELECT numero FROM pv WHERE id=?", ar2)[0] + "-"))

    def test_T51_D_les_autres_colonnes_de_la_levee_sont_libres_CONSTAT(self):
        """CONSTAT : aucune règle documentée sur date_reception de la levée par rapport à celle de l'origine, ni sur les observations."""
        self.ok_l(date_reception="2020-01-01")
        self.ok_l(date_reception="2099-12-31")
        self.ok_l(observations="Peinture reprise")
        self.ok_l(observations=None)

    def test_T51_D_un_pv_initial_ne_declenche_pas_tr_41(self):
        m = self.essai_pv(SR, origine_pv_id=self.AR, suffixe=1)
        self.ko_check(m)                                                                     # CHECK de type, pas une garde de levée
        self.assertNotIn("INV-", m)

    # --- G1 : origine ----------------------------------------------------------------------------------------------------------
    def test_T51_D_G1_origine_pv_sans_reserves_refusee(self):
        self.refus_g(self.essai_levee(origine_pv_id=self.SR, numero="PVR-00002-26-01", suffixe=1), M_G1)

    def test_T51_D_G1_levee_de_levee_refusee(self):
        lv = self.levee(self.AR)
        numero = self.un("SELECT numero FROM pv WHERE id=?", lv)[0]
        self.refus_g(self.tente(self.B, LV, origine_pv_id=lv, suffixe=1, numero=numero + "-01"), M_G1)

    def test_T51_D_G1_origine_inexistante_refusee_avant_la_fk(self):
        for o in (0, -1, 99999):
            with self.subTest(origine=o):
                self.refus_g(self.tente(self.B, LV, origine_pv_id=o, suffixe=1, numero="PVR-00001-26-01"), M_G1)

    def test_T51_D_G1_origine_null_refusee_avant_le_check_levee(self):
        self.refus_g(self.tente(self.B, LV, origine_pv_id=None, suffixe=None, numero="PVR-00001-26-01"), M_G1)
        self.refus_g(self.tente(self.B, LV, origine_pv_id=OMIT, suffixe=OMIT, numero="PVR-00001-26-01"), M_G1)

    def test_T51_D_G1_origine_importee_de_type_sans_reserves_refusee(self):
        imp = self.pv(self.B, SR, origine="import", numero="ANC-1")
        self.refus_g(self.tente(self.B, LV, origine_pv_id=imp, suffixe=1, numero="ANC-1-01"), M_G1)

    # --- G2 : même bon de commande ----------------------------------------------------------------------------------------------
    def test_T51_D_G2_levee_sur_un_autre_bc_que_son_origine_refusee(self):
        autre = self.bc()
        self.refus_g(self.essai_levee(bc_id=autre.b), M_G2)

    def test_T51_D_G2_bc_inexistant_ou_null_refuse_avant_la_fk_et_le_not_null(self):
        self.refus_g(self.essai_levee(bc_id=99999), M_G2)
        self.refus_g(self.essai_levee(bc_id=None), M_G2)

    def test_T51_D_G2_origine_d_un_autre_bc_meme_si_les_autres_gardes_sont_respectees(self):
        autre = self.bc()
        ar_autre = self.pv(autre.b, AR)
        m = self.tente(self.B, LV, origine_pv_id=ar_autre, suffixe=1, numero=numero_levee(self.un("SELECT numero FROM pv WHERE id=?", ar_autre)[0], 1))
        self.refus_g(m, M_G2)

    # --- G3 : suffixe = max + 1 ---------------------------------------------------------------------------------------------------
    def test_T51_D_G3_premier_suffixe_different_de_1_refuse(self):
        for s in (0, 2, 3, 99, 100, -1):
            with self.subTest(suffixe=s):
                self.refus_g(self.essai_levee(suffixe=s), M_G3)

    def test_T51_D_G3_suffixe_null_refuse_avant_le_check(self):
        self.refus_g(self.essai_levee(suffixe=None, numero="PVR-00001-26-01"), M_G3)

    def test_T51_D_G3_suffixe_deja_utilise_refuse_avant_l_unicite(self):
        self.levee(self.AR)
        self.levee(self.AR)
        for s in (1, 2):
            with self.subTest(suffixe=s):
                m = self.essai_levee(suffixe=s)
                self.refus_g(m, M_G3)
                self.assertNotIn("UNIQUE", m)

    def test_T51_D_G3_saut_de_suffixe_refuse(self):
        self.levee(self.AR)
        self.refus_g(self.essai_levee(suffixe=3), M_G3)
        self.ok_l(suffixe=2)

    def test_T51_D_G3_le_suffixe_maximal_est_celui_des_levees_de_la_meme_origine_seulement(self):
        ar2 = self.pv(self.B, AR)
        for _ in range(4):
            self.levee(self.AR)
        self.refus_g(self.tente_l(ar2, suffixe=5), M_G3)
        self.ok_(self.tente_l(ar2, suffixe=1))

    def test_T51_D_G3_c_est_le_maximum_et_non_le_nombre_de_levees(self):
        """Avec les suffixes 1 et 3 présents (base alimentée sans la garde puis garde recréée), max + 1 = 4 : 4 est accepté, 2 et 3 sont refusés."""
        t = self.sans_009()
        m = t.bc()
        ar = t.pv(m.b, AR)
        t.levee(ar, suffixe=1)
        t.levee(ar, suffixe=3)
        t.db.execute(instruction_009("CREATE TRIGGER tr_41_pv_insert"))
        for s in (2, 3, 1, 5):
            with self.subTest(suffixe=s):
                self.refus_g(t.tente_l(ar, suffixe=s), M_G3)
        self.assertIsNone(t.tente_l(ar, suffixe=4))

    # --- G4 : numéro de la levée ------------------------------------------------------------------------------------------------
    def test_T51_D_G4_numero_different_de_origine_plus_suffixe_refuse(self):
        for n in ("PVR-00001-26-02", "PVR-00001-26-1", "PVR-00001-26-001", "PVR-00001-26", "PVR-00001-26_01", "pvr-00001-26-01", "PVR-00001-26-01 ", " PVR-00001-26-01",
                  "PVR-00002-26-01", "PVR-00001-27-01", "x", "PVR-00001-26-01-01", "PVR-00001-26-1 "):
            with self.subTest(numero=repr(n)):
                self.refus_g(self.essai_levee(numero=n), M_G4)

    def test_T51_D_G4_numero_vide_ou_null_refuse_avant_le_not_null(self):
        self.refus_g(self.essai_levee(numero=""), M_G4)
        self.refus_g(self.essai_levee(numero=None), M_G4)

    def test_T51_D_G4_numero_egal_a_celui_de_l_origine_refuse(self):
        self.refus_g(self.essai_levee(numero="PVR-00001-26"), M_G4)

    def test_T51_D_G4_numero_derive_d_une_autre_origine_refuse(self):
        ar2 = self.pv(self.B, AR)
        n2 = self.un("SELECT numero FROM pv WHERE id=?", ar2)[0]
        self.refus_g(self.essai_levee(numero=numero_levee(n2, 1)), M_G4)

    def test_T51_D_G4_suffixe_a_deux_chiffres_pour_les_valeurs_inferieures_a_10(self):
        self.refus_g(self.essai_levee(numero="PVR-00001-26-1"), M_G4)
        self.ok_l(numero="PVR-00001-26-01")

    def test_T51_D_G4_suffixe_10_et_plus_sans_zero_non_ajoute(self):
        for _ in range(9):
            self.levee(self.AR)
        self.refus_g(self.essai_levee(numero="PVR-00001-26-010"), M_G4)
        self.ok_l(numero="PVR-00001-26-10")

    def test_T51_D_G4_numero_de_la_levee_deja_pris_par_un_pv_refuse_par_g4_ou_l_unicite(self):
        self.levee(self.AR)
        m = self.essai_levee(numero="PVR-00001-26-01")                                       # suffixe 2 avec le numéro du suffixe 1
        self.refus_g(m, M_G4)

    # --- ordre des gardes ---------------------------------------------------------------------------------------------------------
    def test_T51_D_ordre_des_gardes_G1_puis_G2_puis_G3_puis_G4(self):
        autre = self.bc()
        ar_autre = self.pv(autre.b, AR)
        sr_autre = self.pv(autre.b, SR)
        # G1, G2, G3 et G4 violées ensemble : G1
        self.refus_g(self.tente(self.B, LV, origine_pv_id=sr_autre, suffixe=7, numero="x"), M_G1)
        # G2, G3 et G4 violées : G2
        self.refus_g(self.tente(self.B, LV, origine_pv_id=ar_autre, suffixe=7, numero="x"), M_G2)
        # G3 et G4 violées : G3
        self.refus_g(self.tente(self.B, LV, origine_pv_id=self.AR, suffixe=7, numero="x"), M_G3)
        # G4 seule
        self.refus_g(self.tente(self.B, LV, origine_pv_id=self.AR, suffixe=1, numero="x"), M_G4)

    def test_T51_D_les_gardes_precedent_les_check_et_la_fk(self):
        """Une levée cumulant une violation de CHECK (réserves renseignées) et une violation de garde est refusée par la garde (INV-xx), pas par le CHECK."""
        m = self.tente(self.B, LV, origine_pv_id=self.AR, suffixe=1, numero="x", reserves="y")
        self.refus_g(m, M_G4)
        m = self.tente(self.B, LV, origine_pv_id=self.AR, suffixe=1, numero=numero_levee("PVR-00001-26", 1), reserves="y")
        self.ko_check(m)                                                                     # gardes respectées : le CHECK reserves prend le relais
        self.assertIn(C_RESERVES, m)

    # --- plafond de 99 levées -------------------------------------------------------------------------------------------------------
    def test_T51_D_99_levees_acceptees_la_100e_refusee_par_le_check_et_non_par_une_garde(self):
        for _ in range(99):
            self.levee(self.AR)
        self.assertEqual(self.un("SELECT MAX(suffixe), COUNT(*) FROM pv WHERE origine_pv_id=?", self.AR), (99, 99))
        self.assertEqual(self.levees_de(self.AR)[98][1], "PVR-00001-26-99")
        avant = self.empreinte_pv()
        m = self.essai_levee()                                                               # suffixe 100, numéro cohérent : les 4 gardes passent
        self.ko_check(m)
        self.assertIn(C_SUFFIXE_BORNES, m)
        self.assertEqual(self.empreinte_pv(), avant)

    def test_T51_D_la_100e_levee_via_le_service_leve_une_integrity_error_sans_message_metier(self):
        """PR-5 (message de service explicite pour la 100e levée) n'est PAS une obligation validée : le refus vient du CHECK du suffixe."""
        for _ in range(99):
            self.creer_levee(self.AR)
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.creer_levee(self.AR)
        self.assertNotIn("INV-", str(cm.exception))
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE origine_pv_id=?", self.AR)[0], 99)

    def test_T51_D_apres_99_levees_un_suffixe_deja_pris_reste_refuse_par_g3(self):
        for _ in range(99):
            self.levee(self.AR)
        self.refus_g(self.essai_levee(suffixe=99), M_G3)
        self.refus_g(self.essai_levee(suffixe=1), M_G3)

    # --- levée avec réserves, état inchangé après refus -----------------------------------------------------------------------------
    def test_T51_D_une_levee_avec_reserves_est_refusee_par_le_check(self):
        m = self.essai_levee(reserves="x")
        self.ko_check(m)
        self.assertIn(C_RESERVES, m)

    def test_T51_D_un_refus_de_garde_ne_laisse_aucune_trace_ni_dans_la_table_ni_dans_sqlite_sequence(self):
        self.levee(self.AR)
        avant = self.empreinte_pv()
        for kw in ({"suffixe": 5}, {"numero": "x"}, {"origine_pv_id": self.SR}, {"bc_id": 99999}):
            m = self.essai_levee(**kw)
            self.assertIsNotNone(m)
        self.assertEqual(self.empreinte_pv(), avant)

    # --- INSERT à plusieurs lignes, INSERT ... SELECT --------------------------------------------------------------------------------
    def test_T51_D_insert_multilignes_trois_levees_successives_acceptees(self):
        ligne = lambda s: self.cols_levee(self.AR, suffixe=s)
        self.multi([ligne(1), ligne(2), ligne(3)])
        self.assertEqual([s for s, _ in self.levees_de(self.AR)], [1, 2, 3])

    def test_T51_D_insert_multilignes_avec_doublon_de_suffixe_refuse_en_entier(self):
        ligne = lambda s: self.cols_levee(self.AR, suffixe=s)
        avant = self.empreinte_pv()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.multi([ligne(1), ligne(2), ligne(2)])
        self.assertIn(M_G3, str(cm.exception))
        self.assertEqual(self.empreinte_pv(), avant)

    def test_T51_D_insert_multilignes_dans_le_desordre_refuse_en_entier(self):
        ligne = lambda s: self.cols_levee(self.AR, suffixe=s)
        avant = self.empreinte_pv()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.multi([ligne(2), ligne(1)])
        self.assertIn(M_G3, str(cm.exception))
        self.assertEqual(self.empreinte_pv(), avant)

    def test_T51_D_insert_multilignes_origine_et_levee_dans_la_meme_instruction(self):
        o = self.cols_pv(self.B, AR, numero="PVR-50001-26", id=900)
        lv = self.cols_pv(self.B, LV, numero="PVR-50001-26-01", origine_pv_id=900, suffixe=1, id=901)
        self.multi([o, lv])
        self.assertEqual(self.levees_de(900), [(1, "PVR-50001-26-01")])

    def test_T51_D_insert_multilignes_levee_avant_son_origine_refusee(self):
        o = self.cols_pv(self.B, AR, numero="PVR-50001-26", id=900)
        lv = self.cols_pv(self.B, LV, numero="PVR-50001-26-01", origine_pv_id=900, suffixe=1, id=901)
        avant = self.empreinte_pv()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.multi([lv, o])
        self.assertIn(M_G1, str(cm.exception))
        self.assertEqual(self.empreinte_pv(), avant)

    def _lot(self, suffixes):
        """Table temporaire `lot` : une levée candidate par suffixe, dans l'ordre d'insertion donné."""
        self.db.execute("CREATE TEMP TABLE lot (ordre INTEGER, numero TEXT, suffixe INTEGER)")
        for i, s in enumerate(suffixes):
            self.db.execute("INSERT INTO lot VALUES (?, ?, ?)", (i, numero_levee("PVR-00001-26", s), s))

    def _insert_select_lot(self):
        s = self.snaps(self.B)
        return self.db.execute("INSERT INTO pv (numero, bc_id, type, date_reception, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
                               "chantier_snapshot, chantier_snapshot_version, origine_pv_id, suffixe) "
                               "SELECT numero, ?, 'levee_reserves', ?, ?, ?, ?, ?, ?, ?, ?, suffixe FROM lot ORDER BY ordre",
                               (self.B, D_PV, s[0], s[1], s[2], s[3], s[4], s[5], self.AR, ))

    def test_T51_D_insert_select_ordre_croissant_accepte(self):
        self._lot([1, 2, 3])
        self._insert_select_lot()
        self.assertEqual([s for s, _ in self.levees_de(self.AR)], [1, 2, 3])

    def test_T51_D_insert_select_ordre_decroissant_refuse_en_entier(self):
        self._lot([3, 2, 1])
        avant = self.empreinte_pv()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self._insert_select_lot()
        self.assertIn(M_G3, str(cm.exception))
        self.assertEqual(self.empreinte_pv(), avant)

    def test_T51_D_insert_select_depuis_pv_lui_meme_derive_une_levee_conforme(self):
        s = self.snaps(self.B)
        self.db.execute("INSERT INTO pv (numero, bc_id, type, date_reception, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
                        "chantier_snapshot, chantier_snapshot_version, origine_pv_id, suffixe) "
                        "SELECT numero || '-01', bc_id, 'levee_reserves', ?, ?, ?, ?, ?, ?, ?, id, 1 FROM pv WHERE id = ?", (D_PV,) + tuple(s) + (self.AR,))
        self.assertEqual(self.levees_de(self.AR), [(1, "PVR-00001-26-01")])

    def test_T51_D_insert_select_depuis_pv_lui_meme_avec_mauvais_numero_refuse(self):
        s = self.snaps(self.B)
        avant = self.empreinte_pv()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute("INSERT INTO pv (numero, bc_id, type, date_reception, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
                            "chantier_snapshot, chantier_snapshot_version, origine_pv_id, suffixe) "
                            "SELECT numero || '-02', bc_id, 'levee_reserves', ?, ?, ?, ?, ?, ?, ?, id, 1 FROM pv WHERE id = ?", (D_PV,) + tuple(s) + (self.AR,))
        self.assertIn(M_G4, str(cm.exception))
        self.assertEqual(self.empreinte_pv(), avant)

    def test_T51_D_aucun_refus_ne_depend_de_l_etat_du_bc(self):
        """CONSTAT QO-1 : le schéma ne lit pas bons_commande.statut ; une levée est acceptée quel que soit l'état du BC de l'origine."""
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                m = self.bc()
                ar = self.pv(m.b, AR)
                self.etat(m, etat)
                self.ok_(self.tente_l(ar))


# ====================================================================================================================
# E — immuabilité (TR-40) : aucune mise à jour, aucune suppression, REPLACE et UPSERT compris
# ====================================================================================================================
M_UPD = "INV-96: un PV est immuable"
M_DEL = "INV-06: un PV ne se supprime jamais"
VALEURS_UPDATE = {"numero": "'PVR-77777-26'", "bc_id": "bc_id + 0", "type": "'reception_sans_reserves'", "date_reception": "'2026-11-02'", "client_snapshot": "'{\"a\":2}'",
                  "client_snapshot_version": "client_snapshot_version + 1", "entreprise_snapshot": "'{\"a\":2}'", "entreprise_snapshot_version": "entreprise_snapshot_version + 1",
                  "chantier_snapshot": "'{\"a\":2}'", "chantier_snapshot_version": "chantier_snapshot_version + 1", "observations": "'modifie'", "reserves": "'modifie'",
                  "origine_pv_id": "NULL", "suffixe": "NULL", "created_at": "'2027-01-01T00:00:00.000Z'", "origine": "'import'", "legacy_id": "'L'", "legacy_data": "'{}'",
                  "id": "id + 1000"}


class Immuabilite(Mini12):
    """Groupe E : tr_40_pv_no_update et tr_40_pv_no_delete (BEFORE) refusent toujours, même un no-op ; avec recursive_triggers=ON le DELETE implicite d'un REPLACE est refusé aussi."""

    def avant(self):
        return self.empreinte_pv()

    def lignes(self):
        """Lignes de pv seules : un INSERT OR IGNORE / DO NOTHING ignoré peut avoir consommé un id AUTOINCREMENT (sqlite_sequence), sans écrire aucune ligne."""
        return self.tous("SELECT * FROM pv ORDER BY id")

    def refuse(self, sql, args=(), message=M_UPD):
        avant = self.avant()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute(sql, args)
        self.assertIn(message, str(cm.exception))
        self.assertEqual(self.avant(), avant, "la table a été modifiée")

    def cols_sql(self, cols):
        return "(" + ", ".join(cols) + ") VALUES (" + ", ".join("?" * len(cols)) + ")"

    # --- UPDATE --------------------------------------------------------------------------------------------------------------------
    def test_T51_E_update_de_chaque_colonne_refuse_avec_une_valeur_differente(self):
        self.assertEqual(set(VALEURS_UPDATE), set(COLONNES_PV))
        for c, v in VALEURS_UPDATE.items():
            with self.subTest(colonne=c):
                self.refuse(f"UPDATE pv SET {c} = {v} WHERE id = {self.SR}")

    def test_T51_E_update_no_op_de_chaque_colonne_refuse(self):
        for c in COLONNES_PV:
            with self.subTest(colonne=c):
                self.refuse(f"UPDATE pv SET {c} = {c} WHERE id = {self.AR}")

    def test_T51_E_update_d_une_levee_refuse(self):
        lv = self.levee(self.AR)
        self.refuse(f"UPDATE pv SET observations = 'x' WHERE id = {lv}")
        self.refuse(f"UPDATE pv SET suffixe = 2 WHERE id = {lv}")

    def test_T51_E_update_multi_lignes_refuse_sans_effet_partiel(self):
        self.levee(self.AR)
        self.refuse("UPDATE pv SET observations = 'tous'")
        self.refuse("UPDATE pv SET observations = observations")

    def test_T51_E_update_qui_ne_touche_aucune_ligne_n_est_pas_un_UPDATE_de_PV_CONSTAT(self):
        """CONSTAT : un trigger FOR EACH ROW ne se déclenche pas quand le WHERE ne retient aucune ligne : aucune ligne n'est modifiée."""
        avant = self.avant()
        cur = self.db.execute("UPDATE pv SET observations = 'x' WHERE id = -5")
        self.assertEqual(cur.rowcount, 0)
        self.assertEqual(self.avant(), avant)

    def test_T51_E_update_avec_clause_de_conflit_refuse(self):
        for verbe in ("OR REPLACE", "OR IGNORE", "OR ABORT", "OR FAIL"):
            with self.subTest(verbe=verbe):
                self.refuse(f"UPDATE {verbe} pv SET observations = 'x' WHERE id = {self.SR}")

    def test_T51_E_update_qui_provoque_un_conflit_d_unicite_refuse_par_le_trigger_et_non_remplace(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.AR)[0]
        self.refuse(f"UPDATE OR REPLACE pv SET numero = '{n}' WHERE id = {self.SR}")
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], 2)

    def test_T51_E_update_par_sous_requete_ou_from_refuse(self):
        self.refuse("UPDATE pv SET observations = (SELECT 'x') WHERE id IN (SELECT id FROM pv)")

    def test_T51_E_aucune_modification_residuelle_apres_les_refus(self):
        avant = self.avant()
        for c, v in VALEURS_UPDATE.items():
            try:
                self.db.execute(f"UPDATE pv SET {c} = {v} WHERE id = {self.AR}")
            except sqlite3.IntegrityError:
                pass
        self.assertEqual(self.avant(), avant)

    # --- UPSERT ---------------------------------------------------------------------------------------------------------------------
    def _upsert(self, numero, suite):
        cols = self.cols_pv(self.B, SR, numero=numero)
        return f"INSERT INTO pv {self.cols_sql(cols)} ON CONFLICT {suite}", tuple(cols.values())

    def test_T51_E_upsert_do_update_sur_numero_refuse(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        sql, args = self._upsert(n, "(numero) DO UPDATE SET observations = 'ecrase'")
        self.refuse(sql, args)

    def test_T51_E_upsert_do_update_sans_cible_refuse(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        sql, args = self._upsert(n, "DO UPDATE SET observations = excluded.observations")
        # SQLite exige une cible pour DO UPDATE sauf en dernière clause : forme acceptée par la grammaire, refusée par TR-40
        avant = self.avant()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute(sql, args)
        self.assertIn(M_UPD, str(cm.exception))
        self.assertEqual(self.avant(), avant)

    def test_T51_E_upsert_do_nothing_laisse_la_table_identique_et_n_ecrit_rien(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        avant = self.lignes()
        sql, args = self._upsert(n, "(numero) DO NOTHING")
        self.assertEqual(self.db.execute(sql, args).rowcount, 0)
        self.assertEqual(self.lignes(), avant)
        sql, args = self._upsert(n, "DO NOTHING")
        self.assertEqual(self.db.execute(sql, args).rowcount, 0)
        self.assertEqual(self.lignes(), avant)

    def test_T51_E_upsert_sur_une_levee_en_conflit_est_refuse_par_la_garde_avant_le_conflit(self):
        self.levee(self.AR)
        cols = self.cols_levee(self.AR, suffixe=1, numero="PVR-00001-26-01")
        avant = self.avant()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute(f"INSERT INTO pv {self.cols_sql(cols)} ON CONFLICT (numero) DO UPDATE SET observations = 'x'", tuple(cols.values()))
        self.assertIn(M_G3, str(cm.exception))
        self.assertEqual(self.avant(), avant)

    def test_T51_E_upsert_sans_conflit_est_un_insert_ordinaire(self):
        sql, args = self._upsert("PVR-60001-26", "(numero) DO UPDATE SET observations = 'x'")
        self.db.execute(sql, args)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE numero='PVR-60001-26'")[0], 1)

    # --- DELETE ----------------------------------------------------------------------------------------------------------------------
    def test_T51_E_delete_simple_refuse_pour_chaque_type(self):
        lv = self.levee(self.AR)
        for pid in (self.SR, self.AR, lv):
            with self.subTest(pv=pid):
                self.refuse(f"DELETE FROM pv WHERE id = {pid}", message=M_DEL)

    def test_T51_E_delete_multi_lignes_et_sans_where_refuses(self):
        self.levee(self.AR)
        self.refuse("DELETE FROM pv", message=M_DEL)
        self.refuse("DELETE FROM pv WHERE type <> 'levee_reserves'", message=M_DEL)
        self.refuse(f"DELETE FROM pv WHERE bc_id = {self.B}", message=M_DEL)

    def test_T51_E_delete_qui_ne_retient_aucune_ligne_ne_fait_rien_CONSTAT(self):
        avant = self.avant()
        self.assertEqual(self.db.execute("DELETE FROM pv WHERE id = -5").rowcount, 0)
        self.assertEqual(self.avant(), avant)

    def test_T51_E_delete_d_une_origine_portant_des_levees_refuse_par_tr_40_avant_la_fk(self):
        self.levee(self.AR)
        self.refuse(f"DELETE FROM pv WHERE id = {self.AR}", message=M_DEL)

    def test_T51_E_delete_ne_laisse_aucune_trace_et_conserve_sqlite_sequence(self):
        avant = self.avant()
        for _ in range(3):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("DELETE FROM pv")
        self.assertEqual(self.avant(), avant)

    # --- INSERT OR REPLACE / REPLACE INTO (recursive_triggers = ON) --------------------------------------------------------------------
    def test_T51_E_replace_par_id_refuse(self):
        cols = self.cols_pv(self.B, SR, id=self.SR, observations="remplace", numero="PVR-60002-26")
        self.refuse(f"INSERT OR REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()), message=M_DEL)

    def test_T51_E_replace_par_numero_refuse(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        cols = self.cols_pv(self.B, SR, numero=n, observations="remplace")
        self.refuse(f"INSERT OR REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()), message=M_DEL)

    def test_T51_E_replace_into_par_id_et_par_numero_refuse(self):
        cols = self.cols_pv(self.B, AR, id=self.AR, numero="PVR-60003-26")
        self.refuse(f"REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()), message=M_DEL)
        n = self.un("SELECT numero FROM pv WHERE id=?", self.AR)[0]
        cols = self.cols_pv(self.B, AR, numero=n)
        self.refuse(f"REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()), message=M_DEL)

    def test_T51_E_replace_par_origine_et_suffixe_refuse(self):
        """Une levée de même (origine, suffixe) : la garde G3 la refuse avant tout REPLACE (le DELETE implicite n'est jamais atteint)."""
        self.levee(self.AR)
        cols = self.cols_levee(self.AR, suffixe=1, numero="PVR-00001-26-01", observations="remplace")
        self.refuse(f"INSERT OR REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()), message=M_G3)
        self.refuse(f"REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()), message=M_G3)

    def test_T51_E_replace_par_origine_et_suffixe_sur_base_sans_garde_g3_est_arrete_par_le_delete_implicite(self):
        """Isole la troisième variante de REPLACE : sans tr_41, le conflit UNIQUE (origine, suffixe) déclenche le DELETE implicite, refusé par tr_40_pv_no_delete."""
        t = self.isole(("tr_40_pv_no_delete",))
        m = t.bc()
        ar = t.pv(m.b, AR)
        t.levee(ar)
        cols = t.cols_levee(ar, suffixe=1, numero="PVR-00001-26-01", observations="remplace")
        avant = t.empreinte_pv()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            t.db.execute(f"INSERT OR REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()))
        self.assertIn(M_DEL, str(cm.exception))
        self.assertEqual(t.empreinte_pv(), avant)

    def test_T51_E_replace_sans_conflit_est_un_insert_ordinaire(self):
        cols = self.cols_pv(self.B, SR, numero="PVR-60004-26")
        self.db.execute(f"INSERT OR REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()))
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], 3)

    # --- TEMOIN recursive_triggers = OFF -------------------------------------------------------------------------------------------------
    def test_T51_E_TEMOIN_avec_recursive_triggers_OFF_un_replace_par_id_remplace_un_pv(self):
        """TÉMOIN (D-39) : la protection contre REPLACE dépend de recursive_triggers=ON, posé à la connexion. Ce test DOCUMENTE la dépendance ; il ne la corrige pas."""
        self.db.execute("PRAGMA recursive_triggers=OFF")
        try:
            cols = self.cols_pv(self.B, SR, id=self.SR, observations="remplace", numero="PVR-60005-26")
            self.db.execute(f"INSERT OR REPLACE INTO pv {self.cols_sql(cols)}", tuple(cols.values()))
            self.assertEqual(self.un("SELECT observations, numero FROM pv WHERE id=?", self.SR), ("remplace", "PVR-60005-26"))
        finally:
            self.db.execute("PRAGMA recursive_triggers=ON")
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)

    def test_T51_E_TEMOIN_avec_recursive_triggers_OFF_update_et_delete_restent_refuses(self):
        self.db.execute("PRAGMA recursive_triggers=OFF")
        try:
            self.refuse(f"UPDATE pv SET observations = 'x' WHERE id = {self.SR}")
            self.refuse(f"DELETE FROM pv WHERE id = {self.SR}", message=M_DEL)
            cols = self.cols_pv(self.B, SR)
            n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
            sql, args = self._upsert(n, "(numero) DO UPDATE SET observations = 'x'")
            self.refuse(sql, args)
        finally:
            self.db.execute("PRAGMA recursive_triggers=ON")

    # --- OR IGNORE sur l'insertion : ce que le service ne doit pas utiliser --------------------------------------------------------------
    def test_T51_E_insert_or_ignore_ignore_un_check_violé_en_silence_donc_le_service_utilise_un_insert_simple(self):
        avant = self.lignes()
        cols = self.cols_pv(self.B, SR, type="inconnu")
        n = self.db.execute(f"INSERT OR IGNORE INTO pv {self.cols_sql(cols)}", tuple(cols.values())).rowcount
        self.assertEqual(n, 0)
        self.assertEqual(self.lignes(), avant)

    def test_T51_E_insert_or_ignore_ignore_un_doublon_de_numero_en_silence(self):
        n = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
        avant = self.lignes()
        cols = self.cols_pv(self.B, SR, numero=n)
        self.assertEqual(self.db.execute(f"INSERT OR IGNORE INTO pv {self.cols_sql(cols)}", tuple(cols.values())).rowcount, 0)
        self.assertEqual(self.lignes(), avant)

    def test_T51_E_insert_or_ignore_ne_contourne_pas_les_gardes_de_levee(self):
        avant = self.avant()
        for kw in ({"suffixe": 5}, {"numero": "x"}, {"origine_pv_id": self.SR}, {"bc_id": 99999}):
            with self.subTest(**kw):
                self.assertIsNotNone(self.tente_l(self.AR, "INSERT OR IGNORE", **kw))
        self.assertEqual(self.avant(), avant)

    def test_T51_E_insert_or_ignore_d_une_levee_valide_est_accepte(self):
        self.assertIsNone(self.tente_l(self.AR, "INSERT OR IGNORE"))


# ====================================================================================================================
# F — clés étrangères et suppression des parents
# ====================================================================================================================
class Parents(Mini12):
    """Groupe F : bc_id et origine_pv_id (RESTRICT). Chaîne complète d'abord (TR-19 puis FK), puis base sans triggers pour isoler la FK. Les limites des sondes du cadrage (§3.6) sont levées ici."""

    def test_T51_F_bc_inexistant_refuse_pour_un_pv_initial_avec_les_triggers_en_place(self):
        for t in (SR, AR):
            for b in (0, -1, 99999):
                with self.subTest(type=t, bc=b):
                    m = self.sous_savepoint(lambda: self.inserer_pv(self.cols_pv(self.B, t, bc_id=b)))
                    self.ko_check(m)
                    self.assertIn("FOREIGN KEY constraint failed", m)

    def test_T51_F_suppression_d_un_bc_portant_un_pv_refusee_chaine_complete_TR_19(self):
        avant = self.empreinte_base()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute("DELETE FROM bons_commande WHERE id=?", (self.B,))
        self.assertIn("INV-174", str(cm.exception))
        self.assertEqual(self.empreinte_base(), avant)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], 2)

    def test_T51_F_suppression_d_un_bc_refusee_par_les_fk_sur_base_sans_triggers(self):
        t = self.sans_triggers()
        m = t.bc()
        t.pv(m.b, AR)
        avant = t.empreinte_base()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            t.db.execute("DELETE FROM bons_commande WHERE id=?", (m.b,))
        self.assertIn("FOREIGN KEY constraint failed", str(cm.exception))
        self.assertEqual(t.empreinte_base(), avant)

    def test_T51_F_la_fk_bc_id_de_pv_est_active_foreign_key_check_designe_pv(self):
        """Attribue la protection à la FK de pv : FK désactivées, le BC est supprimé, foreign_key_check nomme pv comme enfant orphelin."""
        t = self.sans_triggers()
        m = t.bc()
        p = t.pv(m.b, AR)
        t.db.execute("PRAGMA foreign_keys=OFF")
        t.db.execute("DELETE FROM bons_commande WHERE id=?", (m.b,))
        orphelins = [r_ for r_ in t.tous("PRAGMA foreign_key_check") if r_[0] == "pv"]
        self.assertEqual(orphelins, [("pv", p, "bons_commande", orphelins[0][3])])

    def test_T51_F_suppression_d_un_pv_origine_portant_des_levees_refusee_chaine_complete(self):
        self.levee(self.AR)
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute("DELETE FROM pv WHERE id=?", (self.AR,))
        self.assertIn(M_DEL, str(cm.exception))

    def test_T51_F_suppression_d_un_pv_origine_portant_des_levees_refusee_par_la_fk_sans_triggers(self):
        t = self.sans_triggers()
        m = t.bc()
        ar = t.pv(m.b, AR)
        t.levee(ar)
        avant = t.empreinte_base()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            t.db.execute("DELETE FROM pv WHERE id=?", (ar,))
        self.assertIn("FOREIGN KEY constraint failed", str(cm.exception))
        self.assertEqual(t.empreinte_base(), avant)

    def test_T51_F_sans_triggers_le_schema_seul_ne_protege_ni_une_levee_ni_un_pv_sans_enfant_CONSTAT(self):
        """CONSTAT : l'immuabilité vient des triggers TR-40, non de la FK : sans eux une levée ou un PV sans enfant se supprime."""
        t = self.sans_triggers()
        m = t.bc()
        ar = t.pv(m.b, AR)
        lv = t.levee(ar)
        self.assertEqual(t.db.execute("DELETE FROM pv WHERE id=?", (lv,)).rowcount, 1)
        self.assertEqual(t.db.execute("DELETE FROM pv WHERE id=?", (ar,)).rowcount, 1)

    def test_T51_F_modifier_l_id_d_une_origine_portant_des_levees_est_refuse_par_la_fk(self):
        t = self.sans_triggers()
        m = t.bc()
        ar = t.pv(m.b, AR)
        t.levee(ar)
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            t.db.execute("UPDATE pv SET id = id + 1000 WHERE id=?", (ar,))
        self.assertIn("FOREIGN KEY constraint failed", str(cm.exception))

    def refus_fk(self, t, sql, args, differee):
        """Immédiat : refus à l'instruction. Différé : l'instruction passe, le COMMIT est refusé ; dans les deux cas la transaction est annulée et rien n'est supprimé."""
        if differee:
            t.db.execute(sql, args)
            with self.assertRaises(sqlite3.IntegrityError) as cm:
                t.db.execute("COMMIT")
            self.assertIn("FOREIGN KEY constraint failed", str(cm.exception))
            if t.db.in_transaction:
                t.db.execute("ROLLBACK")
        else:
            with self.assertRaises(sqlite3.IntegrityError) as cm:
                t.db.execute(sql, args)
            self.assertIn("FOREIGN KEY constraint failed", str(cm.exception))
            t.db.execute("ROLLBACK")

    def test_T51_F_la_fk_bc_id_de_pv_retient_seule_le_bc_immediatement_meme_avec_controle_differe(self):
        """Tous les autres enfants du BC sont retirés (base sans triggers) : seule la FK de pv retient encore le BC. Le refus tombe à l'instruction, ou au plus tard
        au COMMIT si PRAGMA defer_foreign_keys=ON (constat SQLite 3.45 : ce pragma diffère aussi RESTRICT) ; ni CASCADE ni SET NULL n'emportent le PV."""
        t = self.sans_triggers()
        m = t.bc()
        p = t.pv(m.b, AR)
        t.db.execute("DELETE FROM bc_ligne_garanties WHERE ligne_id IN (SELECT id FROM bc_lignes WHERE bc_id=?)", (m.b,))
        t.db.execute("DELETE FROM bc_lignes WHERE bc_id=?", (m.b,))
        t.db.execute("DELETE FROM bc_devis WHERE bc_id=?", (m.b,))
        autres = [r_ for r_ in t.tous("PRAGMA foreign_key_check")]
        self.assertEqual(autres, [])
        for differee in (False, True):
            with self.subTest(differee=differee):
                t.db.execute("BEGIN")
                if differee:
                    t.db.execute("PRAGMA defer_foreign_keys=ON")
                self.refus_fk(t, "DELETE FROM bons_commande WHERE id=?", (m.b,), differee)
                self.assertEqual(t.un("SELECT COUNT(*) FROM bons_commande WHERE id=?", m.b)[0], 1)
                self.assertEqual(t.un("SELECT COUNT(*) FROM pv WHERE id=?", p)[0], 1)

    def test_T51_F_la_fk_origine_pv_id_s_oppose_immediatement_a_la_suppression_de_l_origine_meme_avec_controle_differe(self):
        t = self.sans_triggers()
        m = t.bc()
        ar = t.pv(m.b, AR)
        lv = t.levee(ar)
        for differee in (False, True):
            with self.subTest(differee=differee):
                t.db.execute("BEGIN")
                if differee:
                    t.db.execute("PRAGMA defer_foreign_keys=ON")
                self.refus_fk(t, "DELETE FROM pv WHERE id=?", (ar,), differee)
                self.assertEqual(t.un("SELECT COUNT(*) FROM pv WHERE id IN (?, ?)", ar, lv)[0], 2)

    def test_T51_F_identifiants_volontairement_distincts_bc_pv_origine(self):
        lv = self.levee(self.AR)
        self.assertEqual(len({self.B, self.AR, self.SR, lv}), 4)
        self.assertEqual(self.un("SELECT bc_id, origine_pv_id FROM pv WHERE id=?", lv), (self.B, self.AR))
        self.assertNotEqual(self.B, self.AR)

    def test_T51_F_confusion_d_identifiants_refusee(self):
        # l'id du BC utilisé comme origine : aucun PV n'a cet id
        self.refus = self.tente(self.B, LV, origine_pv_id=self.B, suffixe=1, numero="PVR-00001-26-01")
        self.assertIn(M_G1, self.refus)
        # l'id d'un PV utilisé comme BC : aucun BC n'a cet id
        m = self.sous_savepoint(lambda: self.inserer_pv(self.cols_pv(self.B, SR, bc_id=self.AR)))
        self.assertIn("FOREIGN KEY constraint failed", m)
        m = self.essai_levee(bc_id=self.AR)
        self.assertIn(M_G2, m)

    def test_T51_F_foreign_key_check_vide_apres_un_scenario_complet(self):
        for _ in range(3):
            self.levee(self.AR)
        autre = self.bc()
        self.pv(autre.b, AR)
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])


# ====================================================================================================================
# G — indépendance (CT-1, CT-2, §4.3, INV-95) : un PV n'agit sur aucune autre table
# ====================================================================================================================
class Independance(Base12):
    """Groupe G : un PV (initial, avec ou sans réserves, levée) ne crée, ne modifie ni ne supprime une facture, un règlement, une garantie, une ligne de BC, un cache de BC
    (INV-95, §4.3). Les cas non spécifiés (QO-1, QO-3) sont des CONSTATS, pas des règles."""

    def empreintes(self):
        """Empreinte par table, plus sqlite_sequence par nom."""
        out = {}
        for (n,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
            out[n] = hashlib.sha256(repr(self.db.execute(f"SELECT * FROM {n} ORDER BY rowid").fetchall()).encode()).hexdigest()
        for n, seq in self.db.execute("SELECT name, seq FROM sqlite_sequence").fetchall():
            out["seq:" + n] = seq
        return out

    def modifiees(self, avant):
        apres = self.empreintes()
        return {k for k in set(avant) | set(apres) if avant.get(k) != apres.get(k)}

    def test_T51_G_insertion_brute_d_un_pv_ne_modifie_que_pv(self):
        m = self.bc()
        avant = self.empreintes()
        a = self.pv(m.b, AR)
        self.assertEqual(self.modifiees(avant), {"pv", "seq:pv"})
        avant = self.empreintes()
        self.pv(m.b, SR)
        self.assertEqual(self.modifiees(avant), {"pv", "seq:pv"})
        avant = self.empreintes()
        self.levee(a)
        self.assertEqual(self.modifiees(avant), {"pv", "seq:pv"})

    def test_T51_G_le_service_d_emission_ne_modifie_que_pv_et_la_sequence_PVR(self):
        m = self.bc()
        avant = self.empreintes()
        o = self.creer_pv(m.b, AR)
        self.assertEqual(self.modifiees(avant), {"pv", "seq:pv", "numerotation_sequences", "seq:numerotation_sequences"})
        avant = self.empreintes()
        self.creer_levee(o.id)
        self.assertEqual(self.modifiees(avant), {"pv", "seq:pv"})                            # la levée ne touche aucune autre table, pas même la numérotation

    def test_T51_G_aucune_ligne_de_numerotation_sequences_n_est_ecrite_par_le_sql(self):
        m = self.bc()
        avant = self.sequences()
        o = self.pv(m.b, AR)
        self.levee(o)
        self.assertEqual(self.sequences(), avant)

    def test_T51_G_pv_sur_chaque_etat_de_bc_CONSTAT_QO_1(self):
        """CONSTAT, pas une règle : 009 ne lit pas bons_commande.statut (CT-1, PR-4) ; le PV est accepté quel que soit l'état et ne change pas l'état."""
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                m = self.bc(etat)
                statut = self.un("SELECT statut, frozen_at, completed_at FROM bons_commande WHERE id=?", m.b)
                avant = self.empreinte_hors_pv()
                a = self.pv(m.b, AR)
                self.pv(m.b, SR)
                self.levee(a)
                self.assertEqual(self.un("SELECT statut, frozen_at, completed_at FROM bons_commande WHERE id=?", m.b), statut)
                self.assertEqual(self.empreinte_hors_pv(), avant)

    def test_T51_G_un_pv_sur_un_bc_sans_facture_est_accepte(self):
        m = self.bc()
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE bc_id=?", m.b)[0], 0)
        self.pv(m.b, SR)

    def test_T51_G_dates_non_contraintes_par_le_bc_ni_par_le_present_CONSTAT_QO_3(self):
        m = self.bc()
        for d in ("1990-01-01", "2026-10-09", "2099-12-31"):
            with self.subTest(date=d):
                self.assertIsNone(self.tente(m.b, SR, date_reception=d))
                self.assertIsNone(self.tente(m.b, AR, date_reception=d))

    def test_T51_G_pv_avant_et_apres_le_solde(self):
        m = self.bc()
        avant_solde = self.pv(m.b, SR)
        self.declencher(m)
        apres_solde = self.pv(m.b, AR)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE bc_id=?", m.b)[0], 2)
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertNotEqual(avant_solde, apres_solde)

    def test_T51_G_le_pv_ne_conditionne_ni_le_solde_ni_l_etat_termine(self):
        avec, sans = self.bc(), self.bc()
        self.pv(avec.b, AR)                                                                  # réserves non levées
        ra, rs = self.declencher(avec), self.declencher(sans)
        self.assertEqual(self.etat_bc(avec)[0], self.etat_bc(sans)[0])
        self.assertEqual(self.etat_bc(avec)[3:], self.etat_bc(sans)[3:])
        self.assertEqual((ra.mode, ra.inseres), (rs.mode, rs.inseres))

    def test_T51_G_les_garanties_restent_intactes_apres_pv_et_levee(self):
        m = self.monde_g()
        self.declencher(m)
        avant = self.lignes_g()
        self.assertTrue(avant)
        o = self.pv(m.b, AR)
        self.levee(o)
        self.levee(o)
        self.pv(m.b, SR)
        self.assertEqual(self.lignes_g(), avant)

    def test_T51_G_T14_garanties_identiques_champ_par_champ_avec_pv_et_levee_intercales(self):
        m = self.monde_g()
        o = self.pv(m.b, AR)                                                                 # PV avant le solde
        r1 = self.declencher(m, "2026-10-05")
        avant = self.lignes_g()
        self.levee(o)
        self.pv(m.b, SR)
        self.neutraliser(r1.solde)                                                           # avoir total
        self.recalcul_financier(m)
        self.levee(o)
        r2 = self.declencher(m, "2026-10-20")                                                # nouveau solde : rejeu T-14
        self.assertEqual((r2.mode, r2.inseres, r2.R), ("REJEU", 0, r1.solde))
        self.assertEqual(self.lignes_g(), avant)
        self.assertEqual({g_[4] for g_ in avant}, {"2026-10-05"})                              # date de déclenchement jamais déplacée (INV-87)
        self.assertEqual(self.levees_de(o)[0][0], 1)

    def test_T51_G_les_caches_du_bc_sont_intacts_apres_pv_et_levee(self):
        m = self.monde_g()
        self.declencher(m)
        avant = self.releve(m.b)
        o = self.pv(m.b, AR)
        self.levee(o)
        self.assertEqual(self.releve(m.b), avant)

    def test_T51_G_les_triggers_de_009_ne_lisent_que_pv(self):
        tables = {n for n in T.noms(self.db, "table")} - {"pv"}
        for nom in TRIGGERS_009:
            sql = T.sans_commentaires(self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0])
            self.assertEqual({x.lower() for x in re.findall(r"\b(?:FROM|JOIN)\s+(\w+)", sql, re.I)} - {"pv"}, set(), nom)
            for t_ in tables:
                self.assertIsNone(re.search(rf"\b{t_}\b", sql), (nom, t_))

    def test_T51_G_aucune_table_ne_reference_pv_sauf_pv_elle_meme(self):
        cibles = {}
        for n in T.noms(self.db, "table"):
            if n.startswith("sqlite_"):
                continue
            for r_ in self.tous(f"PRAGMA foreign_key_list({n})"):
                if r_[2] == "pv":
                    cibles.setdefault(n, []).append(r_[3])
        self.assertEqual(cibles, {"pv": ["origine_pv_id"]})

    def test_T51_G_009_ne_pose_aucun_trigger_sur_une_autre_table(self):
        for nom in TRIGGERS_009:
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], "pv")
        self.assertEqual(T.noms(self.db, "trigger") - T.noms(G.migrer11(), "trigger"), set(TRIGGERS_009))

    def test_T51_G_la_date_de_debut_du_suivi_des_garanties_n_est_jamais_deplacee(self):
        m = self.monde_g()
        r = self.declencher(m, "2026-10-05")
        avant = self.lignes_g()
        o = self.pv(m.b, AR, date_reception="2026-11-30")
        self.levee(o, date_reception="2027-03-01")
        self.assertEqual({g_[4] for g_ in self.lignes_g()}, {"2026-10-05"})
        self.assertEqual(self.lignes_g(), avant)

    def test_T51_G_pv_de_deux_bc_sans_interference(self):
        m1, m2 = self.bc(), self.bc()
        a1, a2 = self.pv(m1.b, AR), self.pv(m2.b, AR)
        self.levee(a1)
        self.levee(a2)
        self.levee(a1)
        self.assertEqual([s for s, _ in self.levees_de(a1)], [1, 2])
        self.assertEqual([s for s, _ in self.levees_de(a2)], [1])
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE bc_id=?", m1.b)[0], 3)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE bc_id=?", m2.b)[0], 2)


# ====================================================================================================================
# H — comportement GÉNÉRIQUE du schéma pour origine='import' (aucun PV n'est importé de la V2 : décision de Rémy ; aucun parcours d'import V2 de PV n'est construit)
# ====================================================================================================================
class Import(Base12):
    """Groupe H : les mécanismes génériques du modèle (BLOC-IMP, INV-131) sont conservés tels que prévus au cadrage ; ces tests n'implémentent ni ne simulent AUCUN import V2.
    Ils constatent que TR-40 et TR-41 s'appliquent sans exemption d'origine (INV-131). Les cas de levée liée à un PV importé relèvent de Z-8 / QO-2 (non spécifié, hors
    périmètre de migration) : CONSTATS de comportement, jamais posés en règle métier."""

    def setUp(self):
        super().setUp()
        self.m = self.bc()
        self.B = self.m.b

    def imp(self, type_=SR, **kw):
        kw.setdefault("numero", "ANCIEN-%d" % (self._n + 1))
        self._n += 1
        kw.setdefault("origine", "import")
        kw.setdefault("legacy_id", "L%d" % self._n)
        kw.setdefault("legacy_data", '{"source": "test"}')
        return self.pv(self.B, type_, **kw)

    def test_T51_H_un_pv_initial_origine_import_accepte_un_numero_libre_et_les_champs_legacy(self):
        pid = self.imp(SR, numero="PV 12/2019", legacy_id="42", legacy_data='{"x": 1}')
        self.assertEqual(self.un("SELECT numero, origine, legacy_id, legacy_data FROM pv WHERE id=?", pid), ("PV 12/2019", "import", "42", '{"x": 1}'))
        self.imp(AR, numero="x")

    def test_T51_H_numero_vide_refuse_et_numero_deja_pris_par_un_pv_v6_refuse(self):
        v6 = self.pv(self.B, SR)
        n = self.un("SELECT numero FROM pv WHERE id=?", v6)[0]
        self.ko_check(self.sous_savepoint(lambda: self.imp(SR, numero="")))
        m = self.sous_savepoint(lambda: self.imp(SR, numero=n))
        self.ko_check(m)
        self.assertIn(C_UNIQUE_NUMERO, m)

    def test_T51_H_le_pv_importe_traverse_tr_40(self):
        p = self.imp(AR)
        for sql, msg in ((f"UPDATE pv SET observations='x' WHERE id={p}", M_UPD), (f"DELETE FROM pv WHERE id={p}", M_DEL)):
            with self.subTest(sql=sql):
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.db.execute(sql)
                self.assertIn(msg, str(cm.exception))

    def test_T51_H_les_gardes_de_levee_s_appliquent_sans_exemption_d_origine_INV_131(self):
        o = self.imp(AR, numero="ANC-9")
        # levée importée : mêmes G1 à G4
        self.assertIn(M_G3, self.tente_l(o, origine="import", legacy_id="L9", suffixe=2) or "")
        self.assertIn(M_G4, self.tente_l(o, origine="import", legacy_id="L9", numero="ANC-9-1") or "")
        self.assertIn(M_G1, self.tente(self.B, LV, origine="import", legacy_id="L9", origine_pv_id=self.imp(SR, numero="ANC-S"), suffixe=1, numero="ANC-S-01") or "")
        autre = self.bc()
        self.assertIn(M_G2, self.tente_l(o, origine="import", legacy_id="L9", bc_id=autre.b) or "")
        # levée importée conforme : acceptée
        self.assertIsNone(self.tente_l(o, origine="import", legacy_id="L9", legacy_data=None))

    def test_T51_H_une_chaine_importee_conforme_origines_puis_levees_par_suffixe_croissant(self):
        o1 = self.imp(AR, numero="ANC-1")
        o2 = self.imp(AR, numero="ANC-2")
        for o in (o1, o2):
            for s in (1, 2, 3):
                self.levee(o, origine="import", legacy_id=f"L{o}-{s}")
        self.assertEqual(self.levees_de(o1), [(1, "ANC-1-01"), (2, "ANC-1-02"), (3, "ANC-1-03")])
        self.assertEqual(self.levees_de(o2), [(1, "ANC-2-01"), (2, "ANC-2-02"), (3, "ANC-2-03")])

    def test_T51_H_levee_importee_inseree_avant_son_origine_refusee_par_G1(self):
        o = self.cols_pv(self.B, AR, id=900, numero="ANC-A", origine="import", legacy_id="a")
        lv = self.cols_pv(self.B, LV, id=901, numero="ANC-A-01", origine="import", legacy_id="b", origine_pv_id=900, suffixe=1)
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.inserer_pv(lv)
        self.assertIn(M_G1, str(cm.exception))
        self.inserer_pv(o)
        self.inserer_pv(lv)

    def test_T51_H_levee_importee_avec_suffixe_2_sans_1_refusee_par_G3(self):
        o = self.imp(AR, numero="ANC-B")
        m = self.tente(self.B, LV, origine="import", legacy_id="b", origine_pv_id=o, suffixe=2, numero="ANC-B-02")
        self.assertIn(M_G3, m)

    def test_T51_H_levee_v6_sur_une_origine_importee_a_numero_libre_CONSTAT_Z_8(self):
        """CONSTAT, pas une règle (Z-8 / QO-2 non spécifiés, hors périmètre de migration) : G4 dérive le numéro de la levée du numéro libre de l'origine ; aucun CHECK de
        format n'existe pour la levée (PR-3) ; aucune exemption n'est ajoutée."""
        o = self.imp(AR, numero="Ancien PV n°3")
        pid = self.levee(o)
        self.assertEqual(self.un("SELECT numero, origine, legacy_id FROM pv WHERE id=?", pid), ("Ancien PV n°3-01", "v6", None))

    def test_T51_H_numero_d_un_pv_initial_importe_egal_au_futur_numero_d_une_levee_bloque_ce_suffixe_CONSTAT(self):
        """CONSTAT : l'unicité du numéro s'applique à tous. Un PV importé qui porte déjà le numéro « origine-01 » rend la levée n° 1 impossible (UNIQUE), donc toutes les levées
        de cette origine (G3 exige le suffixe 1). Scénario hors périmètre de migration ; aucune règle n'est inventée pour le résoudre."""
        o = self.pv(self.B, AR)
        n = self.un("SELECT numero FROM pv WHERE id=?", o)[0]
        self.imp(SR, numero=n + "-01")
        m = self.essai_levee_h(o)
        self.ko_check(m)
        self.assertIn(C_UNIQUE_NUMERO, m)
        self.assertIn(M_G3, self.tente_l(o, suffixe=2))

    def essai_levee_h(self, o):
        return self.tente_l(o)

    def test_T51_H_pas_de_colonne_legacy_numero(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute("INSERT INTO pv (legacy_numero) VALUES ('x')")
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute("SELECT legacy_numero FROM pv")

    def test_T51_H_le_sql_ne_contient_aucune_exemption_de_numero_historique(self):
        code = code_sql()
        self.assertEqual(len(re.findall(r"PVR-", code)), 1)                                  # un seul format : celui du PV initial V6
        m = re.search(r"CHECK\s*\(\s*origine\s*<>\s*'v6'\s+OR\s+type\s*=\s*'levee_reserves'\s+OR\s*\(\s*numero\s+GLOB\s+'PVR-", code)
        self.assertIsNotNone(m)                                                              # conditionné par origine='v6' et exclut la levée
        corps = " ".join(self.un("SELECT sql FROM sqlite_master WHERE name=?", n)[0] for n in TRIGGERS_009)
        corps = re.sub(r"'(?:[^']|'')*'", "''", T.sans_commentaires(corps))                   # hors littéraux (messages)
        self.assertIsNone(re.search(r"\borigine\b", corps))                                    # aucun trigger ne distingue l'origine v6 / import
        self.assertIsNone(re.search(r"\bimport\b|\blegacy", corps))

    def test_T51_H_aucun_parcours_d_import_v2_de_pv_dans_le_sql(self):
        code = code_sql()
        for interdit in (r"\bINSERT\s+(INTO|OR)\b", r"\bV2\b", r"\bhistorique\b", r"\bmigration_v2\b", r"\bimport_log\b"):
            self.assertIsNone(re.search(interdit, code, re.I), interdit)

    def test_T51_H_origine_v6_exclut_legacy_meme_pour_une_levee(self):
        o = self.pv(self.B, AR)
        m = self.tente_l(o, legacy_id="L1")
        self.ko_check(m)
        self.assertIn(C_LEGACY_V6, m)

    def test_T51_H_un_pv_import_n_a_aucun_effet_sur_les_sequences_de_numerotation(self):
        avant = self.sequences()
        self.imp(SR)
        self.imp(AR)
        self.assertEqual(self.sequences(), avant)


# ====================================================================================================================
# I — diagnostics (lecture seule)
# ====================================================================================================================
class Diagnostics(Base12):
    """Groupe I : CK-03 (foreign_key_check couvre pv). Le traitement des levées par CK-01/CK-02 n'est pas spécifié (Z-7) : les requêtes ci-dessous sont des détecteurs DE TEST,
    jamais des CK du modèle. Elles ne modifient rien."""

    def alimente_sans_gardes(self):
        """Base du rang 12 sans les triggers de 009 : on y écrit des incohérences que les gardes interdiraient."""
        t = self.sans_009()
        m = t.bc()
        autre = t.bc()
        ar = t.pv(m.b, AR)
        sr = t.pv(m.b, SR)
        return t, m, autre, ar, sr

    def lire(self, t, cle):
        return [r_[0] for r_ in t.tous(DETECT[cle])]

    def test_T51_I_base_saine_aucune_anomalie_et_foreign_key_check_vide(self):
        m = self.bc()
        ar = self.pv(m.b, AR)
        for _ in range(3):
            self.levee(ar)
        self.pv(m.b, SR)
        for cle in DETECT:
            self.assertEqual(self.lire(self, cle), [], cle)
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertEqual(self.tous("PRAGMA foreign_key_check(pv)"), [])

    def test_T51_I_levee_sur_origine_sans_reserves_detectee(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        lv = t.levee(sr, numero="x", suffixe=1)
        self.assertEqual(self.lire(t, "origine"), [lv])

    def test_T51_I_levee_sur_origine_d_un_autre_bc_detectee(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        lv = t.levee(ar, bc_id=autre.b)
        self.assertEqual(self.lire(t, "origine"), [lv])

    def test_T51_I_levee_de_levee_detectee(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        l1 = t.levee(ar)
        l2 = t.levee(l1, suffixe=1, numero="y")
        self.assertEqual(self.lire(t, "origine"), [l2])

    def test_T51_I_numero_de_levee_incoherent_detecte(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        lv = t.levee(ar, numero="autre")
        self.assertEqual(self.lire(t, "numero"), [lv])

    def test_T51_I_trou_de_suffixe_detecte(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        t.levee(ar, suffixe=1)
        t.levee(ar, suffixe=3)
        self.assertEqual(self.lire(t, "suffixes"), [ar])

    def test_T51_I_suffixes_ne_commencant_pas_a_1_detectes(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        t.levee(ar, suffixe=2)
        self.assertEqual(self.lire(t, "suffixes"), [ar])

    def test_T51_I_les_detecteurs_sont_independants_les_uns_des_autres(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        t.levee(ar, numero="autre")                                                          # seul le numéro est faux
        self.assertEqual((self.lire(t, "origine"), self.lire(t, "suffixes")), ([], []))
        self.assertEqual(len(self.lire(t, "numero")), 1)

    def test_T51_I_foreign_key_check_detecte_un_orphelin_de_pv(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        lv = t.levee(ar)
        t.db.execute("PRAGMA foreign_keys=OFF")
        t.db.execute("DELETE FROM pv WHERE id=?", (ar,))
        orph = [r_ for r_ in t.tous("PRAGMA foreign_key_check(pv)")]
        self.assertEqual([(r_[0], r_[1], r_[2]) for r_ in orph], [("pv", lv, "pv")])

    def test_T51_I_les_diagnostics_sont_en_lecture_seule(self):
        t, m, autre, ar, sr = self.alimente_sans_gardes()
        t.levee(ar, numero="z")
        avant = t.empreinte_base(True)
        for cle in DETECT:
            self.lire(t, cle)
        t.tous("PRAGMA foreign_key_check")
        t.tous("PRAGMA integrity_check")
        self.assertEqual(t.empreinte_base(True), avant)


# ====================================================================================================================
# J — non-régression de la chaîne
# ====================================================================================================================
class NonRegression(Base12):
    """Groupe J : 009 n'altère ni le schéma ni les gardes de 001 à 008 ; les flux de facturation, de règlement et de garantie fonctionnent au rang 12."""

    def objets_hors_pv(self):
        return {(t_, n, tb): s for t_, n, tb, s in T.objets(self.db) if tb != "pv" and not n.startswith("sqlite_autoindex_pv")}

    def test_T51_J_flux_complet_006_007_008_au_rang_12_puis_pv_et_levee(self):
        bc = self.monde_g()
        self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        s = self.solde_g(bc, "2026-10-06")
        self.recalcul_financier(bc)
        self.avoir(s, "100.00")
        self.encaisse(s, "100.00")
        o = self.creer_pv(bc.b, AR)
        self.creer_levee(o.id)
        self.creer_pv(bc.b, SR)
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])

    def test_T51_J_le_schema_hors_pv_est_inchange_apres_un_usage_intensif(self):
        avant = self.objets_hors_pv()
        m = self.monde_g()
        self.declencher(m)
        o = self.creer_pv(m.b, AR)
        for _ in range(5):
            self.creer_levee(o.id)
        self.assertEqual(self.objets_hors_pv(), avant)

    def test_T51_J_les_gardes_des_tranches_precedentes_restent_actives(self):
        m = self.monde_g()
        r = self.declencher(m)
        g = self.lignes_g(m.b)[0][0]
        for sql, args in (("UPDATE garanties SET date_fin_suivi='2099-01-01' WHERE id=?", (g,)), ("DELETE FROM garanties WHERE id=?", (g,)),
                          ("DELETE FROM factures WHERE id=?", (r.solde,)), ("DELETE FROM bons_commande WHERE id=?", (m.b,)),
                          ("UPDATE factures SET total_ht='1.00' WHERE id=?", (r.solde,))):
            with self.subTest(sql=sql):
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.db.execute(sql, args)
                self.assertRegex(str(cm.exception), r"^INV-\d+")

    def test_T51_J_la_numerotation_des_autres_types_n_est_pas_modifiee_par_les_pv(self):
        m = self.monde_g()
        self.creer_pv(m.b, SR)
        r = self.declencher(m)
        self.assertRegex(r.numero, r"^FAC-00001-26$")
        self.assertEqual(self.dernier("FAC", 26), 1)

    def test_T51_J_user_version_12_et_chaine_rejouee_depuis_les_fichiers_sur_une_base_vide(self):
        db = sqlite3.connect(":memory:", isolation_level=None)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA recursive_triggers=ON")
        for rang, nom in enumerate(NOMS, 1):
            sql = (MIGRATIONS / nom).read_text(encoding="utf-8")
            if rang >= 6:
                T.runner(db, rang, sql)
            else:
                T.appliquer(db, rang, sql)
            self.assertEqual(T.db_user_version(db), rang)
        self.assertEqual(T.objets(db), T.objets(self.db))
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_T51_J_les_triggers_de_001_a_008_sont_identiques_au_rang_12(self):
        t11 = {(n, tb): s for _, n, tb, s in T.objets(G.migrer11()) if _ == "trigger"}
        t12 = {(n, tb): s for _, n, tb, s in T.objets(self.db) if _ == "trigger" and tb != "pv"}
        self.assertEqual(t11, t12)

    def test_T51_J_les_fichiers_001_a_008_ne_mentionnent_ni_pv_comme_table_creee_ni_le_rang_12(self):
        for nom in NOMS[:-1]:
            sql = T.sans_commentaires((MIGRATIONS / nom).read_text(encoding="utf-8"))
            self.assertIsNone(re.search(r"CREATE\s+TABLE\s+pv\b", sql, re.I), nom)


# ====================================================================================================================
# K — données malformées et contournements de connexion
# ====================================================================================================================
class Malformees(Mini12):
    """Groupe K : types STRICT, octet NUL, chaînes hostiles, années extrêmes, id explicites, réglages de connexion (témoins : ils documentent ce que les PRAGMA désactivent)."""

    def test_T51_K_types_incompatibles_refuses_par_la_table_stricte(self):
        for col, v in (("numero", b"PVR-50001-26"), ("type", b"reception_sans_reserves"), ("date_reception", b"2026-10-20"), ("created_at", b"2026-10-20T10:00:00.000Z"),
                       ("bc_id", 1.5), ("bc_id", "abc"), ("bc_id", ""), ("bc_id", b"1"), ("client_snapshot_version", 1.5), ("client_snapshot_version", "a"),
                       ("entreprise_snapshot", b"{}"), ("chantier_snapshot_version", b"1"), ("origine", b"v6"), ("observations", b"x"), ("reserves", b"x")):
            with self.subTest(col=col, valeur=v):
                m = self.essai_pv(AR if col == "reserves" else SR, **{col: v})
                self.ko_check(m)
                self.assertRegex(m, r"cannot store|constraint failed|NOT NULL|FOREIGN KEY")

    def test_T51_K_coercitions_sans_perte_de_la_table_stricte_CONSTAT(self):
        """CONSTAT : STRICT convertit sans perte une chaîne numérique en entier ; la garde G3 voit la valeur déjà convertie."""
        pid = self.pv(self.B, SR, bc_id=str(self.B), observations=5)
        self.assertEqual(self.un("SELECT typeof(bc_id), bc_id, typeof(observations), observations FROM pv WHERE id=?", pid), ("integer", self.B, "text", "5"))
        lv = self.levee(self.AR, suffixe="1", numero="PVR-00001-26-01")
        self.assertEqual(self.un("SELECT typeof(suffixe), suffixe FROM pv WHERE id=?", lv), ("integer", 1))

    def test_T51_K_suffixe_reel_ou_blob_refuse_et_texte_non_numerique_refuse(self):
        for s in (1.5, b"1", "abc", ""):
            with self.subTest(suffixe=s):
                self.assertIsNotNone(self.essai_levee(suffixe=s, numero="PVR-00001-26-01"))

    def test_T51_K_octet_nul_dans_les_textes(self):
        for col in ("date_reception",):
            for v in ("2026-10-20\x00", "2026-10-20\x00x", "\x002026-10-20"):
                with self.subTest(col=col, valeur=v):
                    self.ko_check(self.essai_pv(SR, **{col: v, "numero": "PVR-50001-26"}))
        for t in (SR + "\x00", "reception\x00_sans_reserves", "\x00"):
            with self.subTest(type=t):
                self.ko_check(self.essai_pv(t))
        # G4 compare par égalité binaire : un octet NUL dans le numéro de la levée est refusé
        self.assertIn(M_G4, self.essai_levee(numero="PVR-00001-26-01\x00"))

    def test_T51_K_octet_nul_apres_le_numero_ou_le_created_at_refuse(self):
        """Un octet NUL ne peut suivre ni un numéro de PV initial V6 ni un created_at : GLOB, substr et length() de TEXT s'arrêtent au premier octet NUL, la longueur
        est donc contrôlée en octets (length(CAST(x AS BLOB))). Ces valeurs étaient acceptées avant la correction ; tous les autres cas sont au groupe B."""
        for t in (SR, AR):
            self.ko_check(self.essai_pv(t, numero="PVR-50001-26\x00"))
            self.ko_check(self.essai_pv(t, numero="PVR-50001-26\x00junk"))
        self.ko_check(self.essai_pv(SR, created_at="2026-10-20T10:00:00.000Z\x00"))
        self.ko_check(self.essai_pv(SR, created_at="2026-10-20T10:00:00.000Z\x00junk"))

    def test_T51_K_une_origine_v6_a_numero_nul_n_existe_pas_donc_aucune_levee_n_en_derive(self):
        avant = self.un("SELECT COUNT(*) FROM pv")[0]
        for n in ("PVR-50001-26\x00", "PVR-50001-26\x00junk"):
            with self.subTest(numero=repr(n)):
                self.ko_check(self.essai_pv(AR, numero=n))
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], avant)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE instr(CAST(numero AS BLOB), x'00') > 0")[0], 0)

    def test_T51_K_numero_de_levee_avec_octet_nul_refuse_par_G4_a_toute_position(self):
        origine = self.un("SELECT numero FROM pv WHERE id=?", self.AR)[0]
        attendu = origine + "-01"
        variantes = [attendu + "\x00", attendu + "\x00junk", origine + "\x00-01", "\x00" + attendu, origine + "-0\x001", origine + "-\x0001", origine[:5] + "\x00" + attendu[5:]]
        for n in variantes:
            with self.subTest(numero=repr(n)):
                self.assertIn(M_G4, self.essai_levee(numero=n))
        self.ok_l(numero=attendu)

    def test_T51_K_CONSTAT_origine_import_numero_libre_avec_octet_nul_accepte_Z8(self):
        """CONSTAT, non une règle : INV-131 exempte le numéro historique d'un PV importé (numéro libre, non vide, unique) ; 009 ne change pas cette exemption et ne
        contrôle pas l'octet NUL d'un numéro importé. Le NUL d'une telle origine se retrouve dans la levée dérivée par G4 (Z-8 / QO-2 : aucun PV V2 n'est importé).
        Si Rémy décidait d'interdire le NUL dans les numéros importés, ce test devrait être inversé : c'est une évolution de la règle INV-131, à décider explicitement."""
        for n in ("ANCIEN\x00", "ANCIEN\x00junk", "\x00ANCIEN", "AN\x00CIEN", "\x00"):
            with self.subTest(numero=repr(n)):
                self.ok(SR, origine="import", numero=n)
        self.ko_check(self.essai_pv(SR, origine="import", numero=""))                      # non vide : inchangé
        oid = self.pv(self.B, AR, origine="import", numero="ANCIEN\x00")
        lid = self.levee(oid)                                                              # levée dérivée : acceptée par G4 (égalité binaire), le NUL est recopié
        self.assertEqual(self.un("SELECT numero FROM pv WHERE id=?", lid)[0], "ANCIEN\x00-01")

    def test_T51_K_TEMOIN_sans_les_controles_de_longueur_et_d_octet_nul_les_valeurs_a_queue_passent(self):
        """Témoin : la même migration 009 privée de ses conjonctes NUL accepte les valeurs à queue ; les conjonctes sont donc la seule garde."""
        sql = SQL_009
        sql = re.sub(r"\n\s+AND length\(CAST\((numero|created_at) AS BLOB\)\) = (12|24)", "", sql)
        sql, n_json = re.subn(r" AND instr\(CAST\((\w+) AS BLOB\), x'00'\) = 0", "", sql)
        self.assertEqual(n_json, 4)
        self.assertEqual(sql.count("AS BLOB"), SQL_009.count("AS BLOB") - 6)
        db = G.migrer11()
        T.appliquer(db, RANG, sql)
        t = self._sur(db)
        t.m = t.bc()
        t.B = t.m.b
        self.assertIsNone(t.tente(t.B, SR, numero="PVR-50001-26\x00junk"))
        self.assertIsNone(t.tente(t.B, SR, created_at="2026-10-20T10:00:00.000Z\x00junk"))
        for c in ("client_snapshot", "entreprise_snapshot", "chantier_snapshot"):
            self.assertIsNone(t.tente(t.B, SR, **{c: "{}\x00junk"}))
        self.assertIsNone(t.tente(t.B, SR, origine="import", legacy_data="{}\x00junk"))

    def test_T51_K_chaines_hostiles_et_tres_longues_traitees_comme_des_donnees(self):
        for v in ("x'; DROP TABLE pv;--", "' OR '1'='1", "%", "x" * 100000):
            with self.subTest(taille=len(v)):
                self.assertIsNone(self.essai_pv(SR, numero=v, origine="import"))
                self.assertIsNone(self.essai_pv(SR, observations=v))
                self.assertIsNone(self.essai_pv(AR, reserves=v))
        self.assertEqual(self.un("SELECT COUNT(*) FROM sqlite_master WHERE name='pv'")[0], 1)

    def test_T51_K_annees_bissextiles_et_extremes(self):
        for d in ("2024-02-29", "2000-02-29", "0000-02-29", "9999-12-31"):
            with self.subTest(date=d):
                self.assertIsNone(self.essai_pv(SR, date_reception=d))
        for d in ("2023-02-29", "1900-02-29", "2100-02-29", "9999-12-32", "2026-04-31"):
            with self.subTest(date=d):
                self.ko_check(self.essai_pv(SR, date_reception=d))

    def test_T51_K_insert_default_values_refuse(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO pv DEFAULT VALUES")

    def test_T51_K_id_explicite_deja_pris_refuse_et_autoincrement_ne_recule_jamais(self):
        cols = self.cols_pv(self.B, SR, id=self.SR)
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.inserer_pv(cols)
        self.assertIn("UNIQUE constraint failed: pv.id", str(cm.exception))
        self.pv(self.B, SR, id=5000)
        self.assertEqual(self.pv(self.B, SR), 5001)
        self.assertEqual(self.un("SELECT seq FROM sqlite_sequence WHERE name='pv'")[0], 5001)

    def test_T51_K_insertion_en_masse_de_pv_initiaux(self):
        lignes = [self.cols_pv(self.B, SR if i % 2 else AR) for i in range(300)]
        cles = ["numero", "bc_id", "type", "date_reception", "client_snapshot", "client_snapshot_version", "entreprise_snapshot", "entreprise_snapshot_version",
                "chantier_snapshot", "chantier_snapshot_version", "reserves"]
        self.db.execute("INSERT INTO pv (" + ", ".join(cles) + ") VALUES " + ", ".join("(" + ", ".join("?" * len(cles)) + ")" for _ in lignes),
                        tuple(l_.get(c) for l_ in lignes for c in cles))
        self.assertEqual(self.un("SELECT COUNT(*), COUNT(DISTINCT numero) FROM pv")[0:2], (302, 302))

    # --- témoins de réglages de connexion --------------------------------------------------------------------------------------------
    def test_T51_K_TEMOIN_ignore_check_constraints_ne_desactive_que_les_check_pas_les_triggers(self):
        """TÉMOIN : PRAGMA ignore_check_constraints désactive les CHECK mais jamais les triggers ni les FK. Le réglage ne fait pas partie de la connexion applicative (D-39)."""
        self.db.execute("PRAGMA ignore_check_constraints=ON")
        try:
            self.assertIsNone(self.essai_pv("inconnu"))                                      # un CHECK n'est plus évalué
            self.assertIn(M_G3, self.essai_levee(suffixe=5))                                 # les gardes TR-41 restent actives
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("UPDATE pv SET observations='x'")
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("DELETE FROM pv")
        finally:
            self.db.execute("PRAGMA ignore_check_constraints=OFF")
        self.ko_check(self.essai_pv("inconnu"))

    def test_T51_K_TEMOIN_foreign_keys_OFF_laisse_passer_un_bc_inexistant_et_foreign_key_check_le_detecte(self):
        """TÉMOIN : foreign_keys=ON est un réglage de connexion (D-39). OFF, un PV orphelin s'insère ; foreign_key_check le détecte ; G1 (trigger) refuse toujours l'origine inexistante."""
        self.db.execute("PRAGMA foreign_keys=OFF")
        try:
            pid = self.pv(self.B, SR, bc_id=987654)
            self.assertEqual(self.tous("PRAGMA foreign_key_check(pv)")[0][:3], ("pv", pid, "bons_commande"))
        finally:
            self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA foreign_keys=OFF")
        try:
            self.assertIn(M_G1, self.tente(self.B, LV, origine_pv_id=987654, suffixe=1, numero="x"))
        finally:
            self.db.execute("PRAGMA foreign_keys=ON")

    def test_T51_K_les_reglages_de_connexion_sont_ceux_de_D_39_apres_les_temoins(self):
        self.assertEqual((self.un("PRAGMA foreign_keys")[0], self.un("PRAGMA recursive_triggers")[0], self.un("PRAGMA ignore_check_constraints")[0]), (1, 1, 0))


# ====================================================================================================================
# L — atomicité
# ====================================================================================================================
class Atomicite(Base12):
    """Groupe L : un échec n'écrit rien (INSERT multi-lignes, SAVEPOINT, transaction), émission du PV (service émulé) avant/après réservation, levée sans suffixe consommé."""

    def setUp(self):
        super().setUp()
        self.m = self.bc()
        self.B = self.m.b

    def test_T51_L_insert_multilignes_partiellement_invalide_ne_laisse_rien(self):
        ok1 = self.cols_pv(self.B, SR)
        ok2 = self.cols_pv(self.B, SR)
        ko = self.cols_pv(self.B, SR, type="inconnu")
        avant = self.empreinte_pv()
        cles = list(ok1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO pv (" + ", ".join(cles) + ") VALUES " + ", ".join("(" + ", ".join("?" * len(cles)) + ")" for _ in range(3)),
                            tuple(l_[c] for l_ in (ok1, ok2, ko) for c in cles))
        self.assertEqual(self.empreinte_pv(), avant)

    def test_T51_L_savepoint_rollback_et_release(self):
        self.db.execute("BEGIN")
        self.db.execute("SAVEPOINT a")
        p = self.pv(self.B, AR)
        self.db.execute("SAVEPOINT b")
        self.levee(p)
        self.db.execute("ROLLBACK TO b")
        self.assertEqual(self.levees_de(p), [])
        self.levee(p)
        self.db.execute("RELEASE a")
        self.db.execute("COMMIT")
        self.assertEqual(self.levees_de(p), [(1, self.un("SELECT numero FROM pv WHERE id=?", p)[0] + "-01")])

    def test_T51_L_rollback_de_transaction_efface_pv_levee_et_sqlite_sequence(self):
        avant = self.empreinte_pv()
        self.db.execute("BEGIN IMMEDIATE")
        p = self.pv(self.B, AR)
        self.levee(p)
        self.levee(p)
        self.db.execute("ROLLBACK")
        self.assertEqual(self.empreinte_pv(), avant)

    def test_T51_L_un_abort_de_trigger_n_annule_que_l_instruction_donc_le_service_annule_la_transaction(self):
        """RAISE(ABORT) annule l'instruction fautive et conserve les écritures précédentes de la transaction ; c'est pourquoi le service émulé fait ROLLBACK sur toute erreur."""
        self.db.execute("BEGIN IMMEDIATE")
        p = self.pv(self.B, AR)
        with self.assertRaises(sqlite3.IntegrityError):
            self.levee(p, suffixe=9, numero="x")
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE id=?", p)[0], 1)
        self.db.execute("COMMIT")
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE id=?", p)[0], 1)

    def test_T51_L_echec_de_l_insert_apres_reservation_trou_et_aucun_pv(self):
        self.echoue(sqlite3.IntegrityError, True, lambda: self.creer_pv(self.B, SR, client_snapshot="{"))
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], 0)
        self.assertEqual(self.creer_pv(self.B, SR).numero, "PVR-00002-26")

    def test_T51_L_echec_avant_reservation_compteur_inchange(self):
        self.creer_pv(self.B, SR)
        self.echoue(ErreurService, False, lambda: self.creer_pv(self.B, AR, reserves=None))
        self.echoue(AnneeHorsBornes, False, lambda: self.creer_pv(self.B, SR, date="2100-01-01"))
        self.assertEqual(self.compteur("PVR", 26), 1)

    def test_T51_L_echec_apres_insert_avant_commit_aucun_pv_partiel(self):
        def boum(_t, _pid):
            raise DefautInjecte()
        for t in (SR, AR):
            with self.subTest(type=t):
                self.echoue(DefautInjecte, True, lambda t=t: self.creer_pv(self.B, t, avant_commit=boum))
        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], 0)
        self.assertEqual(self.compteur("PVR", 26), 2)

    def test_T51_L_echec_d_une_levee_ne_consomme_aucun_suffixe_ni_numero(self):
        o = self.creer_pv(self.B, AR)
        def boum(_t, _pid):
            raise DefautInjecte()
        avant = self.empreinte_base(True)
        with self.assertRaises(DefautInjecte):
            self.creer_levee(o.id, avant_commit=boum)
        with self.assertRaises(sqlite3.IntegrityError):
            self.creer_levee(o.id, reserves="x")                                             # CHECK reserves
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.empreinte_base(True), avant)
        self.assertEqual(self.creer_levee(o.id).suffixe, 1)
        self.assertEqual(self.compteur("PVR", 26), 1)

    def test_T51_L_la_100e_levee_echoue_sans_effet_residuel(self):
        o = self.creer_pv(self.B, AR)
        for _ in range(99):
            self.creer_levee(o.id)
        avant = self.empreinte_base(True)
        with self.assertRaises(sqlite3.IntegrityError):
            self.creer_levee(o.id)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.empreinte_base(True), avant)

    def test_T51_L_integrite_apres_une_serie_de_succes_et_d_echecs(self):
        o = self.creer_pv(self.B, AR)
        for i in range(10):
            self.creer_levee(o.id)
            with self.assertRaises(sqlite3.IntegrityError):
                self.creer_levee(o.id, reserves="x")
            self.creer_pv(self.B, SR)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        for cle, sql in DETECT.items():
            self.assertEqual(self.tous(sql), [], cle)
        self.assertEqual([s for s, _ in self.levees_de(o.id)], list(range(1, 11)))

    # --- sémantique ABORT de chaque garde (RAISE(ABORT) : l'instruction fautive est annulée, la transaction reste ouverte avec ses écritures précédentes) ------------
    def _sites(self):
        sr = self.pv(self.B, SR)
        ar = self.pv(self.B, AR)
        autre = self.bc()
        ar2 = self.pv(autre.b, AR)
        return {
            "G1": (M_G1, lambda: self.inserer_pv(self.cols_levee(sr, numero="x", suffixe=1))),
            "G2": (M_G2, lambda: self.inserer_pv(self.cols_levee(ar2, bc_id=self.B))),
            "G3": (M_G3, lambda: self.inserer_pv(self.cols_levee(ar, suffixe=5))),
            "G4": (M_G4, lambda: self.inserer_pv(self.cols_levee(ar, numero="x"))),
            "TR40_update": (M_UPD, lambda: self.db.execute("UPDATE pv SET observations='x' WHERE id=?", (ar,))),
            "TR40_delete": (M_DEL, lambda: self.db.execute("DELETE FROM pv WHERE id=?", (ar,))),
        }

    def test_T51_L_chaque_garde_est_un_abort_la_transaction_reste_ouverte_avec_ses_ecritures_precedentes(self):
        for site, (message, f) in self._sites().items():
            with self.subTest(garde=site):
                self.db.execute("BEGIN IMMEDIATE")
                precedent = self.pv(self.B, SR)
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    f()
                self.assertIn(message, str(cm.exception))
                self.assertTrue(self.db.in_transaction, "RAISE(ROLLBACK) a terminé la transaction")
                self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE id=?", precedent)[0], 1)
                self.db.execute("COMMIT")
                self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE id=?", precedent)[0], 1)

    def test_T51_L_une_instruction_multilignes_dont_la_derniere_ligne_est_refusee_n_ecrit_aucune_ligne(self):
        """RAISE(FAIL) conserverait les lignes déjà écrites par l'instruction ; RAISE(ABORT) les annule toutes."""
        sr = self.pv(self.B, SR)
        ar = self.pv(self.B, AR)
        autre = self.bc()
        ar2 = self.pv(autre.b, AR)
        ok = lambda s: self.cols_levee(ar, suffixe=s)
        cas = {
            "G1": ([ok(1), self.cols_levee(sr, numero="x-01", suffixe=1)], M_G1),
            "G2": ([ok(1), self.cols_levee(ar2, bc_id=self.B)], M_G2),
            "G3": ([ok(1), self.cols_levee(ar, suffixe=5)], M_G3),
            "G4": ([ok(1), self.cols_levee(ar, suffixe=2, numero="x")], M_G4),
        }
        for site, (lignes, message) in cas.items():
            with self.subTest(garde=site):
                avant = self.tous("SELECT * FROM pv ORDER BY id")
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.multi(lignes)
                self.assertIn(message, str(cm.exception))
                self.assertEqual(self.tous("SELECT * FROM pv ORDER BY id"), avant)

    def test_T51_L_upsert_et_replace_multilignes_refuses_n_ecrivent_aucune_ligne(self):
        sr = self.pv(self.B, SR)
        existant = self.un("SELECT numero FROM pv WHERE id=?", sr)[0]
        nouveau, conflit = self.cols_pv(self.B, SR, numero="PVR-70001-26"), self.cols_pv(self.B, SR, numero=existant)
        cles = list(nouveau)
        vals = "(" + ", ".join("?" * len(cles)) + ")"
        args = tuple(nouveau[c] for c in cles) + tuple(conflit[c] for c in cles)
        for suite, message, verbe in (("ON CONFLICT (numero) DO UPDATE SET observations = 'z'", M_UPD, "INSERT"), ("", M_DEL, "INSERT OR REPLACE")):
            with self.subTest(verbe=verbe):
                avant = self.tous("SELECT * FROM pv ORDER BY id")
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.db.execute(f"{verbe} INTO pv ({', '.join(cles)}) VALUES {vals}, {vals} {suite}", args)
                self.assertIn(message, str(cm.exception))
                self.assertEqual(self.tous("SELECT * FROM pv ORDER BY id"), avant)


if __name__ == "__main__":
    unittest.main()
