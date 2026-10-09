"""T-49 — Tranche 007_reglements (rang 10) ; modèle V3.13 §2.3 (familles décimales), §2.5 (énumérations), §3.3 (paiement), §3.4 (états dérivés), §3.5 (fin du BC),
§4.9 (règlements), §8 (TR-30 à TR-33), §9 (index), §10 (import), §13 (C-02, C-05, C-06, C-10 à C-13, C-35, C-36) ; invariants INV-06, INV-46, INV-60, INV-70 à INV-75,
INV-79, INV-131, INV-163, INV-164, INV-177, INV-184, INV-188 ; CADRAGE__007_reglements.md (validé : Q1 règlement né annulé, Q2 ordre d'import, Q3 aucune validation
inventée sur date_evenement / reference / note ; précision d'intégration « un règlement ne rouvre jamais commercialement le BC »).

007 crée UNE table (reglements), ses trois index et six triggers (tr_30, tr_31 x2, tr_32 x2, tr_33). Aucun trigger de 007 ne lit ni n'écrit bons_commande.
Responsabilités vérifiées ici :
  * CHECK / index : types et modes fermés, famille D2 stricte et montant > 0, dates réelles, annulation en paire, BLOC-IMP, FK RESTRICT, index de recherche ;
  * triggers : cible (tr_30), plafonds d'encaissement et de remboursement (tr_31), immuabilité et non-suppression, REPLACE compris (tr_32), garde de l'annulation
    d'un encaissement (tr_33) ;
  * services (reproduits ici par des fabriques et un oracle Python en centimes entiers, JAMAIS par le schéma) : reste_du, absorbe, credit, états de paiement,
    recalcul financier du BC (termine / en_cours, caches), événements d'historique (hors tranche) ;
  * diagnostics (requêtes en constantes SQL, lecture seule) : CK-06 (volet termine) et trois contrôles nouveaux justifiés par 007 : CK-18 (cible incohérente avec le
    type), CK-19 (encaissements actifs > montant de la facture), CK-20 (remboursements actifs > crédit).

Réutilisation : ces tests importent test_006_facturation (qui importe test_005c puis test_005b) pour l'émulation du runner et la fabrication des devis, BC, lignes et
factures, sans les modifier. Le rang 10 s'obtient en appliquant 007 sur la chaîne du rang 9 (BEGIN IMMEDIATE, fichier, PRAGMA user_version = 10, COMMIT).

Exécution : python3 src-tauri/tests/metier/test_007_reglements.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T49_ suivi du groupe (A chaîne et structure, B CHECK, C FK et index,
D tr_30, E tr_31 encaissement, F tr_31 remboursement, G règlement né annulé, H tr_32, I tr_33, J états dérivés et cas chiffrés, K intégration BC, L import, M diagnostics,
N contournements SQL, O atomicité, P valeurs limites, Q dates, R données malformées, S différentiel contre l'oracle, T compléments issus de la mutation). Les décisions d'interprétation portent
« INTERPRETATION ». Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39).
Un refus levé par un trigger se reconnaît à son préfixe « INV-nn » ; un refus levé par une contrainte (CHECK, NOT NULL, UNIQUE, FK) n'en porte aucun.
"""
import hashlib
import pathlib
import random
import re
import sqlite3
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_006_facturation as F  # noqa: E402  (fabrication de données, services de facturation et émulation du runner)

T, C = F.T, F.C
MIGRATIONS = F.MIGRATIONS
NOM_007 = "007_reglements.sql"
NOMS = F.NOMS + (NOM_007,)
SQL_007 = (MIGRATIONS / NOM_007).read_text(encoding="utf-8")
RANG = 10
TS, TS2, TS_ANNUL = T.TS, T.TS2, T.TS_ANNUL
OMIT = F.OMIT
c, eur, dl = F.c, F.eur, F.dl

INDEXES_007 = {"idx_reglements_facture_id": "facture_id", "idx_reglements_date_evenement": "date_evenement", "idx_reglements_type": "type"}
TRIGGERS_007 = {"tr_30_reglements_cible": "reglements", "tr_31_reglements_encaissement": "reglements", "tr_31_reglements_remboursement": "reglements",
                "tr_32_reglements_update": "reglements", "tr_32_reglements_no_delete": "reglements", "tr_33_reglements_annulation": "reglements"}
COLONNES_REGLEMENTS = ["id", "facture_id", "type", "date_evenement", "montant", "mode", "reference", "note", "cancelled_at", "motif_annulation", "created_at",
                       "origine", "legacy_id", "legacy_data"]
TYPES_R = ("encaissement", "remboursement")
MODES = ("especes", "cheque", "virement", "carte", "autre")
TYPES_F = ("acompte", "situation", "solde")                                                  # factures hors avoir
D_REF = "2026-10-10"                                                                         # date_evenement par défaut

# Écritures MALFORMÉES de montant (famille D2 : forme canonique à deux décimales, jamais négatif, jamais nul) : chacune est refusée par UN terme du CHECK.
MAL_MONTANT = F.MAL_D2 + ("0.00", "0", "0.0", "1", "1.0", "1.234", "12", "٣.٠٠", "1 .00", "1.00.", "1.00e0", "0x1.00", "NaN", "Inf", "null")
DATES_VALIDES = ("2026-10-10", "2028-02-29", "2000-02-29", "2026-12-31", "2026-01-01", "0001-01-01", "9999-12-31", "0000-01-01", "2026-02-28")
DATES_INVALIDES = ("2026-02-29", "2100-02-29", "2026-13-01", "2026-00-10", "2026-04-31", "2026-06-31", "2026-10-32", "2026-10-00", "-0001-01-01", "2026-1-1",
                   "26-10-10", "2026/10/10", "20261010", "2026-10-10 ", " 2026-10-10", "2026-10-10\n", "2026-10-10T00:00:00Z", "2026-10-10T", "٢٠٢٦-١٠-١٠",
                   "10-10-2026", "2026-10-1", "2026-1-10", "", "abcd-ef-gh", "2026-10-10x", "x2026-10-10", "2026-W41-1", "2026-284")
TS_VALIDES = ("2026-10-10T08:00:00.000Z", "2099-01-01T00:00:00.000Z", "2026-02-28T23:59:59.999Z")
TS_INVALIDES = ("2026-10-10", "2026-10-10T08:00:00Z", "2026-10-10 08:00:00.000Z", "2026-10-10T08:00:00.000", "2026-10-10T08:00:00.00Z", "2026-10-10T08:00:00.0000Z",
                "26-10-10T08:00:00.000Z", "2026-10-10T8:00:00.000Z", "2026-10-10T08:00:00.000Z ", " 2026-10-10T08:00:00.000Z", "abc", "")


# --------------------------------------------------------------------------------------------------------------------
# Chaîne
# --------------------------------------------------------------------------------------------------------------------
def migrer10(recursive=True):
    """Chaîne 001 à 006 (rang 9) puis 007 comme une migration ordinaire : BEGIN IMMEDIATE, fichier, user_version = 10, COMMIT."""
    db = F.migrer9(recursive=recursive)
    T.appliquer(db, RANG, SQL_007)
    return db


# --------------------------------------------------------------------------------------------------------------------
# Oracle (le « service » : centimes entiers, jamais de flottant ; formules LITTÉRALES du modèle §3.3, distinctes des écritures SQL des triggers)
# --------------------------------------------------------------------------------------------------------------------
class Compte:
    """Compte d'une facture hors avoir F : M, encaissements actifs, avoirs, remboursements actifs (sur l'ensemble des avoirs de F)."""

    def __init__(self, M):
        self.M = M
        self.enc = []
        self.av = []
        self.remb = []

    @property
    def encaisse(self):
        return sum(self.enc)

    @property
    def somme_avoirs(self):
        return sum(self.av)

    def absorbe(self, enc=None):
        e = self.encaisse if enc is None else enc
        return min(self.somme_avoirs, max(0, self.M - e))

    def reste_du(self, enc=None):
        e = self.encaisse if enc is None else enc
        return max(0, self.M - e - self.absorbe(e))

    def credit(self, enc=None, remb=None):
        r = sum(self.remb) if remb is None else remb
        return max(0, self.somme_avoirs - self.absorbe(enc) - r)

    def credit_brut(self, enc=None):
        """Crédit non écrêté : il n'est jamais négatif tant que les garde-fous tiennent."""
        return self.somme_avoirs - self.absorbe(enc) - sum(self.remb)

    def etat_paiement(self):
        if self.reste_du() == 0:
            return "reglee"
        return "partiellement_reglee" if self.encaisse > 0 else "en_attente"


# --------------------------------------------------------------------------------------------------------------------
# Diagnostics (lecture seule ; chaque requête retourne les lignes en violation)
# --------------------------------------------------------------------------------------------------------------------
_C = "CAST(REPLACE({x}, '.', '') AS INTEGER)"


def _cents(x):
    return _C.format(x=x)


ENC_ACTIFS = "(SELECT COALESCE(SUM(" + _cents("r.montant") + "), 0) FROM reglements r WHERE r.facture_id = {f}.id AND r.type = 'encaissement' AND r.cancelled_at IS NULL)"
SOMME_AV = "(SELECT COALESCE(SUM(" + _cents("av.total_ht") + "), 0) FROM factures av WHERE av.origine_facture_id = {f}.id)"
REMB_ACTIFS = ("(SELECT COALESCE(SUM(" + _cents("r.montant") + "), 0) FROM reglements r JOIN factures a ON a.id = r.facture_id "
               "WHERE a.origine_facture_id = {f}.id AND r.type = 'remboursement' AND r.cancelled_at IS NULL)")
RESTE_DU = ("MAX(0, " + _cents("{f}.total_ht") + " - " + ENC_ACTIFS + " - MIN(" + SOMME_AV + ", MAX(0, " + _cents("{f}.total_ht") + " - " + ENC_ACTIFS + ")))")
# CK-18 : un encaissement doit viser une facture hors avoir, un remboursement un avoir
CK18_CIBLE = ("SELECT r.id FROM reglements r JOIN factures f ON f.id = r.facture_id "
              "WHERE (r.type = 'encaissement' AND f.type = 'avoir') OR (r.type = 'remboursement' AND f.type <> 'avoir')")
# CK-19 : les encaissements actifs d'une facture ne dépassent jamais son montant (donc reste_du reste cohérent)
CK19_ENCAISSEMENTS = ("SELECT f.id FROM factures f WHERE f.type <> 'avoir' AND " + ENC_ACTIFS.format(f="f") + " > " + _cents("f.total_ht"))
# CK-20 : les remboursements actifs d'une origine ne dépassent jamais son crédit (crédit non écrêté >= 0)
CK20_CREDIT = ("SELECT f.id FROM factures f WHERE f.type <> 'avoir' AND "
               + SOMME_AV.format(f="f") + " - MIN(" + SOMME_AV.format(f="f") + ", MAX(0, " + _cents("f.total_ht") + " - " + ENC_ACTIFS.format(f="f") + ")) - "
               + REMB_ACTIFS.format(f="f") + " < 0")
# CK-06 (volet termine) : statut du BC non annulé = solde actif ET somme des reste_du des factures hors avoir nulle
CK06_TERMINE = (
    "SELECT b.id FROM bons_commande b WHERE b.statut <> 'annule' AND "
    "(b.statut = 'termine') IS NOT (EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = b.id AND s.type = 'solde' AND NOT (s.total_ht <> '0.00' AND "
    + SOMME_AV.format(f="s") + " = " + _cents("s.total_ht") + ")) AND NOT EXISTS (SELECT 1 FROM factures f WHERE f.bc_id = b.id AND f.type <> 'avoir' AND "
    + RESTE_DU.format(f="f") + " > 0))")
CK = {"cible": CK18_CIBLE, "encaissements": CK19_ENCAISSEMENTS, "credit": CK20_CREDIT, "termine": CK06_TERMINE}


# --------------------------------------------------------------------------------------------------------------------
# Fabrique : règlements, annulations, services de recalcul (reproduits côté test ; aucune règle de service n'est portée par le schéma)
# --------------------------------------------------------------------------------------------------------------------
class Base10(F.Base9):
    """Base au rang 10. Les fabriques de devis, BC, factures et avoirs viennent de test_006 ; les règlements et le recalcul financier sont reproduits ici."""

    DECALAGES = F.Base9.DECALAGES + (("reglements", 90),)

    def setUp(self):
        self.db = migrer10()
        self._n = 0
        self.desynchroniser_ids()

    def isole(self, gardes):
        """Base du rang 10 dont tous les triggers sont supprimés sauf `gardes`."""
        t = Base10()
        t.db = migrer10()
        t._n = 0
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def sans_triggers(self):
        return self.isole(())

    def seulement_007(self):
        """Triggers de 007 seuls : on peut poser des factures brutes (sans les gardes de 006) pour éprouver 007 isolément."""
        return self.isole(tuple(TRIGGERS_007))

    # --- règlements ------------------------------------------------------------------------------------------------
    def cols_reglement(self, f, type_, montant, **kw):
        cols = {"facture_id": f, "type": type_, "date_evenement": D_REF, "montant": montant, "mode": "virement"}
        cols.update(kw)
        return {k: v for k, v in cols.items() if v is not OMIT}

    def reglement(self, f, type_, montant, **kw):
        """Insertion brute d'un règlement (colonnes obligatoires pré-remplies ; `kw` remplace, OMIT retire)."""
        return self.inserer("reglements", self.cols_reglement(f, type_, montant, **kw))

    def encaisse(self, f, montant, **kw):
        return self.reglement(f, "encaissement", montant, **kw)

    def rembourse(self, avoir, montant, **kw):
        return self.reglement(avoir, "remboursement", montant, **kw)

    def annuler(self, r, motif="Erreur de saisie", quand=TS_ANNUL):
        self.db.execute("UPDATE reglements SET cancelled_at=?, motif_annulation=? WHERE id=?", (quand, motif, r))

    def tente_r(self, f, type_, montant, **kw):
        """Insertion brute d'un règlement annulée juste après : None si acceptée, sinon le message d'erreur."""
        self.db.execute("SAVEPOINT tenter")
        try:
            self.reglement(f, type_, montant, **kw)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tenter")
            self.db.execute("RELEASE tenter")

    def tente_annul(self, r, motif="Erreur de saisie", quand=TS_ANNUL):
        """Annulation d'un règlement essayée puis annulée : None si acceptée, sinon le message d'erreur."""
        return self.tente("UPDATE reglements SET cancelled_at=?, motif_annulation=? WHERE id=?", quand, motif, r)

    def refuse_r(self, inv, f, type_, montant, **kw):
        """Le règlement est refusé par un trigger dont le message porte `inv`."""
        m = self.tente_r(f, type_, montant, **kw)
        self.assertIsNotNone(m, f"règlement {type_} {montant} accepté à tort")
        self.assertRegex(m, inv)

    def refuse_check_r(self, f, type_, montant, **kw):
        """Le règlement est refusé par une contrainte (aucun préfixe INV-)."""
        m = self.tente_r(f, type_, montant, **kw)
        self.assertIsNotNone(m, f"règlement {type_} {montant} accepté à tort")
        self.assertNotIn("INV-", m)

    def accepte_r(self, f, type_, montant, **kw):
        m = self.tente_r(f, type_, montant, **kw)
        self.assertIsNone(m, m)

    def refuse_annul(self, inv, r, **kw):
        m = self.tente_annul(r, **kw)
        self.assertIsNotNone(m, f"annulation du règlement {r} acceptée à tort")
        self.assertRegex(m, inv)

    def accepte_annul(self, r, **kw):
        m = self.tente_annul(r, **kw)
        self.assertIsNone(m, m)

    # --- oracle lié à la base --------------------------------------------------------------------------------------
    def compte(self, f):
        """Compte de la facture hors avoir `f`, relu dans la base mais calculé côté Python (indépendant du SQL des triggers)."""
        k = Compte(self.total(f))
        k.enc = [c(m) for (m,) in self.tous("SELECT montant FROM reglements WHERE facture_id=? AND type='encaissement' AND cancelled_at IS NULL", f)]
        avs = self.tous("SELECT id, total_ht FROM factures WHERE origine_facture_id=?", f)
        k.av = [c(t) for _, t in avs]
        for (a, _) in avs:
            k.remb += [c(m) for (m,) in self.tous("SELECT montant FROM reglements WHERE facture_id=? AND type='remboursement' AND cancelled_at IS NULL", a)]
        return k

    def reste_du(self, f):
        return self.compte(f).reste_du()

    def credit(self, f):
        return self.compte(f).credit()

    def etat_paiement(self, f):
        return self.compte(f).etat_paiement()

    def nb_reglements(self):
        return self.un("SELECT count(*) FROM reglements")[0]

    def cible(self, type_="situation", total="1000.00", **kw):
        """BC dont le contractuel est exactement `total`, portant une facture `type_` de ce montant (acompte, situation ou solde). Retourne (bc, f)."""
        bc = self.monde(devis=[{"lignes": [total]}])
        if type_ == "acompte":
            f = self.facture(bc, "acompte", total, devis_id=bc.d[0], **kw)
        elif type_ == "situation":
            f = self.facture(bc, "situation", total, situation_numero=1, montant_deja_facture_ht="0.00", **kw)
        else:
            f = self.facture(bc, "solde", total, **kw)
        return bc, f

    def cible_credit(self, total="1000.00", avoir="100.00", type_="situation", enc=None):
        """Facture `total` intégralement (ou `enc`) encaissée PUIS créditée d'un avoir : le crédit apparaît (C-06). Retourne (bc, f, a)."""
        bc, f = self.cible(type_, total)
        self.encaisse(f, enc or total)
        return bc, f, self.avoir(f, avoir)

    def cible_avec_avoir(self, total="1000.00", avoir="500.00", type_="situation"):
        """Facture `total` et un avoir `avoir` ; retourne (bc, f, a)."""
        bc, f = self.cible(type_, total)
        return bc, f, self.avoir(f, avoir)

    # --- service financier du BC (INV-46, INV-164) : un seul UPDATE ----------------------------------------------------------
    def reste_du_bc(self, b):
        b = b.b if hasattr(b, "b") else b
        return sum(self.reste_du(f) for (f,) in self.tous("SELECT id FROM factures WHERE bc_id=? AND type<>'avoir'", b))

    def termine_calcule(self, b):
        """termine <=> un solde actif ET somme des reste_du des factures hors avoir nulle (modèle §3.5)."""
        b = b.b if hasattr(b, "b") else b
        return bool(self.soldes_actifs(b)) and self.reste_du_bc(b) == 0

    def recalcul_financier(self, bc, quand=TS):
        """Service financier complet (006 + 007) : caches du BC en UN SEUL UPDATE. BC annulé : seuls les trois caches financiers évoluent (VR-05).
        Passage en_cours -> termine : completed_at = instant du recalcul ; termine -> en_cours : completed_at = NULL (INV-79)."""
        b = bc.b if hasattr(bc, "b") else bc
        nette, ctr = self.nette(b), self.contractuel(b)
        actifs = self.soldes_actifs(b)
        avanc = 10000 if actifs else (min(10000, (2 * nette * 10000 + ctr) // (2 * ctr)) if ctr else 0)
        d100 = min(d for d, _ in actifs) if actifs else None
        statut = self.un("SELECT statut FROM bons_commande WHERE id=?", b)[0]
        if statut == "annule":
            self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht=?, avancement=?, date_100_facture=?, updated_at=? WHERE id=?",
                            (eur(nette), eur(avanc), d100, TS2, b))
        elif self.termine_calcule(b):
            self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht=?, avancement=?, date_100_facture=?, statut='termine', "
                            "completed_at=COALESCE(completed_at, ?), frozen_at=COALESCE(frozen_at, ?), updated_at=? WHERE id=?",
                            (eur(nette), eur(avanc), d100, quand, TS, TS2, b))
        else:
            self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht=?, avancement=?, date_100_facture=?, statut='en_cours', completed_at=NULL, "
                            "frozen_at=COALESCE(frozen_at, CASE WHEN ? IS NOT NULL THEN ? END), updated_at=? WHERE id=?",
                            (eur(nette), eur(avanc), d100, d100, TS, TS2, b))

    def ligne_bc(self, bc):
        b = bc.b if hasattr(bc, "b") else bc
        return self.un("SELECT * FROM bons_commande WHERE id=?", b)

    def empreinte(self, table):
        """Empreinte du contenu d'une table (toutes lignes, toutes colonnes) pour prouver qu'une opération n'y écrit rien."""
        h = hashlib.sha256()
        for ligne in self.db.execute(f"SELECT * FROM {table} ORDER BY 1"):
            h.update(repr(ligne).encode())
        return h.hexdigest()

    def empreinte_schema(self, exclure=()):
        h = hashlib.sha256()
        for nom, sql in self.db.execute("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name"):
            if nom not in exclure and not nom.endswith("_reglements") and "reglements" not in (sql or "").split("(")[0]:
                h.update((nom + "|" + (sql or "")).encode())
        return h.hexdigest()

    def ck(self, sql, *args):
        return self.tous(sql, *args)


# ====================================================================================================================
# A — chaîne de migration et structure
# ====================================================================================================================
def code_sql():
    return T.sans_commentaires(SQL_007)


def base9_peuplee():
    """Base du rang 9 portant un BC, un acompte, une situation, un avoir : une migration 007 ne doit rien y changer."""
    t = F.Base9()
    t.setUp()
    bc = t.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
    a = t.acompte(bc, bc.d[0], "1000.00")
    t.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
    t.avoir(a, "100.00")
    return t


class Chaine(Base10):
    """Groupe A : 001 → … → 006 → 007, rang 10, aucune régression de la chaîne."""

    def test_T49_A_fichiers_de_la_chaine_dans_l_ordre(self):
        self.assertEqual([p.name for p in sorted(MIGRATIONS.glob("*.sql"))[:10]], list(NOMS))
        self.assertEqual(NOMS[-1], "007_reglements.sql")
        self.assertEqual(len(NOMS), RANG)

    def test_T49_A_rang_et_user_version(self):
        db = F.migrer9()
        self.assertEqual(T.db_user_version(db), 9)
        T.appliquer(db, RANG, SQL_007)
        self.assertEqual(T.db_user_version(db), 10)
        self.assertEqual(T.db_user_version(self.db), 10)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_T49_A_le_protocole_de_reconstruction_du_runner_est_accepte(self):
        db = F.migrer9()
        T.runner(db, RANG, SQL_007)
        self.assertEqual(T.db_user_version(db), 10)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(T.objets(db), T.objets(self.db))

    def test_T49_A_le_fichier_ne_contient_que_des_creations_sans_transaction_ni_pragma_ni_donnee(self):
        code = code_sql()
        for interdit in (r"\bPRAGMA\b", r"\bCOMMIT\b", r"\bROLLBACK\b", r"\bSAVEPOINT\b", r"BEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)",
                         r"\bALTER\b", r"\bDROP\b", r"\bINSERT\s+INTO\b", r"\bUPDATE\s+\w+\s+SET\b", r"\bDELETE\s+FROM\b", r"\bREPLACE\s+INTO\b",
                         r"\bINSERT\s+OR\b", r"\bCREATE\s+(VIEW|TEMP|TEMPORARY|VIRTUAL)\b", r"\bRETURNING\b", r"\bON\s+UPDATE\b", r"\bCASCADE\b",
                         r"\bON\s+CONFLICT\b", r"\bbons_commande\b", r"\bREAL\b", r"\bFLOAT\b", r"\bDOUBLE\b", r"\bNUMERIC\b"):
            self.assertIsNone(re.search(interdit, code, re.I), interdit)
        sts = [T.sans_commentaires(s).strip() for s in T.instructions(SQL_007)]
        genres = [re.match(r"CREATE\s+(UNIQUE\s+)?(TABLE|INDEX|TRIGGER)", s).group(0).split()[-1] for s in sts]
        self.assertEqual({g_: genres.count(g_) for g_ in ("TABLE", "INDEX", "TRIGGER")}, {"TABLE": 1, "INDEX": 3, "TRIGGER": 6})
        self.assertEqual(len(sts), 10)
        self.assertTrue(all(s.endswith(";") for s in sts))
        self.assertEqual(len(re.findall(r"\bCREATE\s+UNIQUE\b", code)), 0)

    def test_T49_A_les_messages_des_triggers_sont_ASCII_et_portent_un_invariant(self):
        messages = re.findall(r"RAISE\s*\(\s*ABORT\s*,\s*'((?:[^']|'')*)'\s*\)", code_sql())
        self.assertEqual(len(messages), 8)                                                   # 2 + 1 + 1 + 2 + 1 + 1
        for m in messages:
            self.assertTrue(m.isascii(), m)
            self.assertRegex(m, r"^INV-(70|71|72|74|75): ")

    def test_T49_A_objets_exacts_au_rang_10(self):
        self.assertEqual(T.noms(self.db, "table") - {"sqlite_sequence"}, F.TABLES_RANG9 | {"reglements"})
        self.assertEqual(T.noms(self.db, "view"), set())
        nommes = {n for n in T.noms(self.db, "index") if not n.startswith("sqlite_")}
        self.assertEqual(nommes, T.INDEXES_RANG7 | F.INDEXES_006 | set(INDEXES_007))
        triggers10 = T.noms(self.db, "trigger")
        triggers9 = T.noms(F.migrer9(), "trigger")
        self.assertEqual(triggers10 - triggers9, set(TRIGGERS_007))
        self.assertEqual(triggers9 - triggers10, set())
        for nom, table in TRIGGERS_007.items():
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], table, nom)
        for nom, col in INDEXES_007.items():
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], "reglements", nom)
            self.assertEqual([r[2] for r in self.tous(f"PRAGMA index_info({nom})")], [col], nom)
            self.assertEqual(self.un(f"SELECT [unique] FROM pragma_index_list('reglements') WHERE name=?", nom)[0], 0, nom)

    def test_T49_A_les_objets_du_rang_9_sont_identiques_au_caractere_pres(self):
        o9 = {(t, n, tb): s for t, n, tb, s in T.objets(F.migrer9())}
        o10 = {(t, n, tb): s for t, n, tb, s in T.objets(self.db)}
        self.assertEqual(set(o10) - set(o9), {("table", "reglements", "reglements")} | {("index", n, "reglements") for n in INDEXES_007}
                         | {("trigger", n, t) for n, t in TRIGGERS_007.items()})
        self.assertEqual(set(o9) - set(o10), set())
        for cle, sql in o9.items():
            self.assertEqual(o10[cle], sql, cle)

    def test_T49_A_aucune_donnee_n_est_modifiee_par_la_migration(self):
        t9 = base9_peuplee()
        avant = T.tout(t9.db)
        self.assertTrue(avant["factures"] and avant["bons_commande"])
        T.appliquer(t9.db, RANG, SQL_007)
        apres = T.tout(t9.db)
        self.assertEqual(apres.pop("reglements"), [])
        self.assertEqual(apres, avant)                                                       # y compris sqlite_sequence : rien pour la nouvelle table
        self.assertEqual(T.db_user_version(t9.db), 10)
        self.assertEqual(t9.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(t9.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_T49_A_schema_identique_base_fraiche_et_base_migree_peuplee(self):
        t = base9_peuplee()
        T.appliquer(t.db, RANG, SQL_007)
        self.assertEqual(T.objets(t.db), T.objets(self.db))

    def test_T49_A_atomicite_un_echec_n_importe_ou_annule_tout(self):
        points = ["CREATE TABLE reglements (", "CREATE INDEX idx_reglements_facture_id", "CREATE INDEX idx_reglements_date_evenement", "CREATE INDEX idx_reglements_type",
                  "CREATE TRIGGER tr_30_reglements_cible", "CREATE TRIGGER tr_31_reglements_encaissement", "CREATE TRIGGER tr_31_reglements_remboursement",
                  "CREATE TRIGGER tr_32_reglements_update", "CREATE TRIGGER tr_32_reglements_no_delete", "CREATE TRIGGER tr_33_reglements_annulation"]
        db0 = F.migrer9()
        avant = T.objets(db0)
        for point in points:
            with self.subTest(point=point):
                self.assertEqual(SQL_007.count(point), 1, point)
                coupe = SQL_007.replace(point, "SELECT * FROM table_qui_n_existe_pas;\n" + point, 1)
                db = F.migrer9()
                with self.assertRaises(sqlite3.Error):
                    T.runner(db, RANG, coupe)
                self.assertFalse(db.in_transaction)
                self.assertEqual(T.db_user_version(db), 9)
                self.assertEqual(T.objets(db), avant)
        with self.subTest(point="apres la derniere instruction"):
            db = F.migrer9()
            with self.assertRaises(sqlite3.Error):
                T.runner(db, RANG, SQL_007 + "\nSELECT * FROM table_qui_n_existe_pas;\n")
            self.assertEqual(T.db_user_version(db), 9)
            self.assertEqual(T.objets(db), avant)

    def test_T49_A_rejeu_sur_une_base_deja_au_rang_10_est_refuse_sans_effet(self):
        avant = T.objets(self.db)
        with self.assertRaises(sqlite3.Error):
            T.runner(self.db, RANG, SQL_007)
        self.assertEqual(T.objets(self.db), avant)
        self.assertEqual(T.db_user_version(self.db), 10)

    def test_T49_A_table_stricte_et_colonnes_exactes(self):
        self.assertEqual(self.un("SELECT strict FROM pragma_table_list WHERE name='reglements'")[0], 1)
        cols = self.tous("PRAGMA table_info(reglements)")
        self.assertEqual([x[1] for x in cols], COLONNES_REGLEMENTS)
        self.assertEqual({x[1]: x[2] for x in cols}, {"id": "INTEGER", "facture_id": "INTEGER", "type": "TEXT", "date_evenement": "TEXT", "montant": "TEXT",
                                                    "mode": "TEXT", "reference": "TEXT", "note": "TEXT", "cancelled_at": "TEXT", "motif_annulation": "TEXT",
                                                    "created_at": "TEXT", "origine": "TEXT", "legacy_id": "TEXT", "legacy_data": "TEXT"})
        self.assertEqual({x[1] for x in cols if x[3]}, {"facture_id", "type", "date_evenement", "montant", "mode", "created_at", "origine"})
        self.assertEqual([x[1] for x in cols if x[5]], ["id"])
        defauts = {x[1]: x[4] for x in cols if x[4] is not None}
        self.assertEqual(set(defauts), {"created_at", "origine"})
        self.assertEqual(defauts["origine"], "'v6'")
        self.assertIn("strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", defauts["created_at"])
        self.assertIn("AUTOINCREMENT", self.un("SELECT sql FROM sqlite_master WHERE name='reglements'")[0])

    def test_T49_A_aucune_colonne_derivee_ni_statut_ni_numero_ni_avoir_id(self):
        cols = {x[1] for x in self.tous("PRAGMA table_info(reglements)")}
        for absente in ("numero", "statut", "etat", "etat_paiement", "reste_du", "credit", "absorbe", "avoir_id", "bc_id", "client_id", "updated_at", "frozen_at",
                        "montant_ttc", "tva", "date_paiement", "devise", "banque"):
            self.assertNotIn(absente, cols)

    def test_T49_A_cle_etrangere_unique_vers_factures_en_restrict_sans_on_update(self):
        fk = self.tous("PRAGMA foreign_key_list(reglements)")
        self.assertEqual(len(fk), 1)
        self.assertEqual((fk[0][2], fk[0][3], fk[0][4], fk[0][5], fk[0][6]), ("factures", "facture_id", "id", "NO ACTION", "RESTRICT"))

    def test_T49_A_aucune_sequence_de_numerotation_pour_les_reglements(self):
        self.assertEqual(self.un("SELECT count(*) FROM numerotation_sequences")[0], 0)
        self.refuse_check("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('REG', 26, 1)")
        self.refuse_check("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('RGL', 26, 1)")
        self.assertNotIn("numerotation_sequences", code_sql())

    def test_T49_A_aucune_ligne_inseree_et_pas_de_sequence_avant_le_premier_reglement(self):
        db = migrer10()                                                                      # base fraîche : aucune désynchronisation d'identifiants
        self.assertEqual(db.execute("SELECT count(*) FROM reglements").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT * FROM sqlite_sequence WHERE name='reglements'").fetchall(), [])

    def test_T49_A_les_ids_ne_sont_jamais_reutilises(self):
        bc, f = self.cible()
        r1 = self.encaisse(f, "1.00")
        r2 = self.encaisse(f, "1.00")
        self.assertEqual(r2, r1 + 1)
        self.annuler(r2)
        r3 = self.encaisse(f, "1.00")
        self.assertEqual(r3, r2 + 1)

    def test_T49_A_la_connexion_de_test_a_les_reglages_de_D_39(self):
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)


# ====================================================================================================================
# B — CHECK de la table reglements (formes, énumérations, annulation en paire, BLOC-IMP)
# ====================================================================================================================
class CheckReglements(Base10):
    """Groupe B : chaque terme d'un CHECK est arrêté par au moins un jeu de valeurs ; chaque valeur valide est acceptée."""

    def setUp(self):
        super().setUp()
        self.bc, self.f = self.cible("situation", "1000000.00")                              # grande capacité : seuls les CHECK sont éprouvés
        self.bc2, self.f2, self.a = self.cible_credit("1000.00", "100.00")                  # crédit disponible 100.00 sur self.a

    # --- valeurs valides ---------------------------------------------------------------------------------------------
    def test_T49_B_ligne_minimale_valide_et_valeurs_par_defaut(self):
        r = self.encaisse(self.f, "100.00")
        ligne = dict(zip(COLONNES_REGLEMENTS, self.un("SELECT * FROM reglements WHERE id=?", r)))
        self.assertEqual({k: ligne[k] for k in ligne if k != "created_at" and k != "id"},
                         {"facture_id": self.f, "type": "encaissement", "date_evenement": D_REF, "montant": "100.00", "mode": "virement", "reference": None,
                          "note": None, "cancelled_at": None, "motif_annulation": None, "origine": "v6", "legacy_id": None, "legacy_data": None})
        self.assertRegex(ligne["created_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    def test_T49_B_les_deux_types_sont_acceptes(self):
        self.encaisse(self.f, "1.00")
        self.rembourse(self.a, "1.00")
        self.assertEqual(self.tous("SELECT type FROM reglements WHERE id > (SELECT max(id) - 2 FROM reglements) ORDER BY id"), [("encaissement",), ("remboursement",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_T49_B_les_cinq_modes_sont_acceptes(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.accepte_r(self.f, "encaissement", "1.00", mode=mode)
        self.assertEqual(len(MODES), 5)

    def test_T49_B_montants_valides_aux_bornes_de_la_forme(self):
        for m in ("0.01", "0.10", "0.99", "1.00", "9.99", "10.00", "12.34", "100.00", "999999.99", "10.50", "20.05", "50000.00"):
            with self.subTest(montant=m):
                self.accepte_r(self.f, "encaissement", m)

    # --- type et mode : énumérations fermées -------------------------------------------------------------------------------
    def test_T49_B_type_hors_enumeration_refuse(self):
        for t in ("", "Encaissement", "ENCAISSEMENT", "paiement", "remboursemen", "avoir", "encaissement ", " encaissement", "encaissement\n", "regl", None, 0, 1):
            with self.subTest(type=t):
                self.refuse_check_r(self.f, t, "1.00")

    def test_T49_B_type_est_obligatoire(self):
        self.refuse_check_r(self.f, OMIT, "1.00")

    def test_T49_B_mode_hors_enumeration_refuse(self):
        for m in ("", "Virement", "VIREMENT", "espece", "especes ", "chèque", "check", "cb", "paypal", "prelevement", " virement", "autre\n", None, 0):
            with self.subTest(mode=m):
                self.refuse_check_r(self.f, "encaissement", "1.00", mode=m)

    def test_T49_B_mode_est_obligatoire_sans_valeur_par_defaut(self):
        self.refuse_check_r(self.f, "encaissement", "1.00", mode=OMIT)

    # --- montant ---------------------------------------------------------------------------------------------------------
    def test_T49_B_montants_malformes_refuses_par_la_famille_D2(self):
        for m in MAL_MONTANT:
            with self.subTest(montant=m):
                self.refuse_check_r(self.f, "encaissement", m)

    def test_T49_B_montant_zero_refuse_et_un_centime_accepte(self):
        self.refuse_check_r(self.f, "encaissement", "0.00")
        self.accepte_r(self.f, "encaissement", "0.01")

    def test_T49_B_montant_negatif_refuse_pour_les_deux_types(self):
        for m in ("-0.01", "-1.00", "-1000.00"):
            with self.subTest(montant=m):
                self.refuse_check_r(self.f, "encaissement", m)
                self.refuse_check_r(self.a, "remboursement", m)

    def test_T49_B_montant_est_obligatoire(self):
        self.refuse_check_r(self.f, "encaissement", OMIT)
        self.refuse_check_r(self.f, "encaissement", None)

    def test_T49_B_montant_de_type_non_texte_refuse(self):
        for m in (5, 5.5, 100, b"1.00", 1.0):
            with self.subTest(montant=m):
                self.refuse_check_r(self.f, "encaissement", m)

    def test_T49_B_montant_stocke_tel_quel_en_texte(self):
        r = self.encaisse(self.f, "12.30")
        self.assertEqual(self.un("SELECT montant, typeof(montant) FROM reglements WHERE id=?", r), ("12.30", "text"))

    # --- date_evenement --------------------------------------------------------------------------------------------------
    def test_T49_B_dates_valides_acceptees_sans_borne_d_annee(self):
        for d in DATES_VALIDES:
            with self.subTest(date=d):
                self.accepte_r(self.f, "encaissement", "1.00", date_evenement=d)

    def test_T49_B_dates_invalides_refusees(self):
        for d in DATES_INVALIDES:
            with self.subTest(date=d):
                self.refuse_check_r(self.f, "encaissement", "1.00", date_evenement=d)

    def test_T49_B_date_est_obligatoire(self):
        self.refuse_check_r(self.f, "encaissement", "1.00", date_evenement=OMIT)
        self.refuse_check_r(self.f, "encaissement", "1.00", date_evenement=None)

    def test_T49_B_date_de_type_non_texte_refusee(self):
        for d in (20261010, 2026.1010):
            with self.subTest(date=d):
                self.refuse_check_r(self.f, "encaissement", "1.00", date_evenement=d)

    # --- annulation : date et motif en paire -----------------------------------------------------------------------------
    def test_T49_B_annulation_complete_acceptee_a_l_insertion(self):
        for ts in TS_VALIDES:
            with self.subTest(ts=ts):
                self.accepte_r(self.f, "encaissement", "1.00", cancelled_at=ts, motif_annulation="Doublon")

    def test_T49_B_date_sans_motif_et_motif_sans_date_refuses(self):
        self.refuse_check_r(self.f, "encaissement", "1.00", cancelled_at=TS_VALIDES[0])
        self.refuse_check_r(self.f, "encaissement", "1.00", motif_annulation="Doublon")

    def test_T49_B_motif_vide_refuse(self):
        self.refuse_check_r(self.f, "encaissement", "1.00", cancelled_at=TS_VALIDES[0], motif_annulation="")
        self.refuse_check_r(self.f, "encaissement", "1.00", motif_annulation="")

    def test_T49_B_horodatage_d_annulation_invalide_refuse(self):
        for ts in TS_INVALIDES:
            with self.subTest(ts=ts):
                self.refuse_check_r(self.f, "encaissement", "1.00", cancelled_at=ts, motif_annulation="x")

    def test_T49_B_INTERPRETATION_cancelled_at_est_controle_par_sa_forme_seulement(self):
        """Comme created_at (005, 006) : le GLOB vérifie la forme, pas le calendrier ; aucune relation avec created_at ni date_evenement (Q3)."""
        self.accepte_r(self.f, "encaissement", "1.00", cancelled_at="2026-13-45T99:99:99.999Z", motif_annulation="x")
        self.accepte_r(self.f, "encaissement", "1.00", cancelled_at="1999-01-01T00:00:00.000Z", motif_annulation="x", date_evenement="2026-10-10")

    # --- created_at ----------------------------------------------------------------------------------------------------------
    def test_T49_B_created_at_valide_accepte_et_invalide_refuse(self):
        for ts in TS_VALIDES:
            with self.subTest(ts=ts):
                self.accepte_r(self.f, "encaissement", "1.00", created_at=ts)
        for ts in TS_INVALIDES:
            with self.subTest(ts=ts):
                self.refuse_check_r(self.f, "encaissement", "1.00", created_at=ts)

    def test_T49_B_created_at_est_obligatoire(self):
        self.refuse_check_r(self.f, "encaissement", "1.00", created_at=None)

    def test_T49_B_created_at_par_defaut_est_un_instant_UTC_recent(self):
        r = self.encaisse(self.f, "1.00")
        ts = self.un("SELECT created_at FROM reglements WHERE id=?", r)[0]
        self.assertGreaterEqual(ts, "2026-01-01T00:00:00.000Z")
        self.assertEqual(self.un("SELECT ? <= strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", ts)[0], 1)

    # --- BLOC-IMP ------------------------------------------------------------------------------------------------------
    def test_T49_B_origine_hors_enumeration_refusee(self):
        for o in ("V6", "imported", "", " import", "import ", None, "legacy"):
            with self.subTest(origine=o):
                self.refuse_check_r(self.f, "encaissement", "1.00", origine=o)

    def test_T49_B_origine_import_porte_legacy(self):
        r = self.encaisse(self.f, "1.00", origine="import", legacy_id="R-17", legacy_data='{"paye": true}')
        self.assertEqual(self.un("SELECT origine, legacy_id, legacy_data FROM reglements WHERE id=?", r), ("import", "R-17", '{"paye": true}'))
        self.accepte_r(self.f, "encaissement", "1.00", origine="import")
        self.accepte_r(self.f, "encaissement", "1.00", origine="import", legacy_id="R-18")
        self.accepte_r(self.f, "encaissement", "1.00", origine="import", legacy_data="{}")

    def test_T49_B_origine_v6_exclut_legacy(self):
        self.refuse_check_r(self.f, "encaissement", "1.00", legacy_id="R-17")
        self.refuse_check_r(self.f, "encaissement", "1.00", legacy_data="{}")
        self.refuse_check_r(self.f, "encaissement", "1.00", origine="v6", legacy_id="R-17", legacy_data="{}")
        self.accepte_r(self.f, "encaissement", "1.00", origine="v6")

    def test_T49_B_legacy_data_doit_etre_du_json_valide(self):
        for j in ("", "{", "abc", "{'a': 1}", "[1,", "nul", "{\"a\":}"):
            with self.subTest(json=j):
                self.refuse_check_r(self.f, "encaissement", "1.00", origine="import", legacy_data=j)
        for j in ("{}", "[]", "null", "1", "\"x\"", '{"a": [1, 2, {"b": null}]}'):
            with self.subTest(json=j):
                self.accepte_r(self.f, "encaissement", "1.00", origine="import", legacy_data=j)

    def test_T49_B_origine_par_defaut_v6(self):
        r = self.encaisse(self.f, "1.00")
        self.assertEqual(self.un("SELECT origine FROM reglements WHERE id=?", r)[0], "v6")

    # --- reference et note : texte libre, aucune validation (Q3) -----------------------------------------------------------
    def test_T49_B_reference_et_note_sont_libres(self):
        for v in (None, "", " ", "CHQ 0012345", "é à ü ç — 漢字 🙂", "x" * 10000, "ligne1\nligne2", "'; DROP TABLE reglements; --", "  espaces  ", "0", "NULL"):
            with self.subTest(valeur=v[:30] if isinstance(v, str) else v):
                r = self.encaisse(self.f, "1.00", reference=v, note=v)
                self.assertEqual(self.un("SELECT reference, note FROM reglements WHERE id=?", r), (v, v))
        self.assertEqual(self.un("SELECT count(*) FROM sqlite_master WHERE name='reglements'")[0], 1)

    def test_T49_B_reference_et_note_de_type_non_texte_deviennent_du_texte(self):
        r = self.encaisse(self.f, "1.00", reference=12345, note=1.5)
        self.assertEqual(self.un("SELECT reference, typeof(reference), note, typeof(note) FROM reglements WHERE id=?", r), ("12345", "text", "1.5", "text"))

    # --- facture_id ------------------------------------------------------------------------------------------------------
    def test_T49_B_facture_est_obligatoire(self):
        self.refuse_check_r(OMIT, "encaissement", "1.00")
        self.refuse_check_r(None, "encaissement", "1.00")

    def test_T49_B_facture_inexistante_refusee_par_la_cle_etrangere_et_non_par_un_trigger(self):
        for fid in (999999, 0, -1, self.bc.b, self.bc.cli, self.bc.d[0]):
            with self.subTest(facture_id=fid):
                m = self.tente_r(fid, "encaissement", "1.00")
                self.assertIsNotNone(m)
                self.assertNotIn("INV-", m)
                m = self.tente_r(fid, "remboursement", "1.00")
                self.assertIsNotNone(m)
                self.assertNotIn("INV-", m)

    def test_T49_B_aucune_unicite_deux_reglements_identiques_sont_legitimes(self):
        self.encaisse(self.f, "10.00", reference="CHQ1")
        self.encaisse(self.f, "10.00", reference="CHQ1")
        self.encaisse(self.f, "10.00", reference="CHQ1", date_evenement=D_REF, mode="virement")
        self.assertEqual(self.un("SELECT count(DISTINCT montant||reference||date_evenement||mode||facture_id||type), count(*) FROM reglements WHERE facture_id=?", self.f), (1, 3))

    def test_T49_B_insertion_multi_lignes_atomique_si_une_ligne_est_invalide(self):
        avant = self.nb_reglements()
        m = self.tente("INSERT INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '1.00', 'carte'), (?, 'encaissement', ?, '0.00', 'carte')",
                       self.f, D_REF, self.f, D_REF)
        self.assertIsNotNone(m)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '1.00', 'carte'), (?, 'encaissement', ?, '0.00', 'carte')",
                            (self.f, D_REF, self.f, D_REF))
        self.assertEqual(self.nb_reglements(), avant)


# ====================================================================================================================
# C — clé étrangère et index
# ====================================================================================================================
class CleEtrangereEtIndex(Base10):
    """Groupe C : FK RESTRICT (double barrière avec tr_21 de 006) et index de recherche."""

    def test_T49_C_la_suppression_d_une_facture_est_refusee_par_006(self):
        bc, f = self.cible()
        self.encaisse(f, "10.00")
        self.refuse_inv("INV-06", "DELETE FROM factures WHERE id=?", f)

    def test_T49_C_sans_trigger_la_FK_RESTRICT_protege_encore_la_facture(self):
        t = self.sans_triggers()
        bc, f = t.cible()
        t.encaisse(f, "10.00")
        t.refuse_check("DELETE FROM factures WHERE id=?", f)
        self.assertEqual(t.un("SELECT count(*) FROM factures WHERE id=?", f)[0], 1)
        t.refuse_check("UPDATE factures SET id=id+1000 WHERE id=?", f)

    def test_T49_C_sans_trigger_la_FK_refuse_un_reglement_orphelin(self):
        t = self.sans_triggers()
        m = t.tente_r(424242, "encaissement", "1.00")
        self.assertIsNotNone(m)
        self.assertIn("FOREIGN KEY", m)

    def test_T49_C_foreign_key_check_reste_vide_apres_des_operations_valides(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.rembourse(a, "50.00")
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])

    def test_T49_C_les_index_servent_les_recherches_par_facture_date_et_type(self):
        for colonne, index in (("facture_id", "idx_reglements_facture_id"), ("date_evenement", "idx_reglements_date_evenement"), ("type", "idx_reglements_type")):
            with self.subTest(colonne=colonne):
                plan = " ".join(str(x) for x in self.tous(f"EXPLAIN QUERY PLAN SELECT * FROM reglements WHERE {colonne} = ?", "x"))
                self.assertIn(index, plan)

    def test_T49_C_aucun_index_unique_ni_partiel_sur_reglements(self):
        for (nom,) in self.tous("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='reglements' AND name NOT LIKE 'sqlite_%'"):
            self.assertIsNone(self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0].find("UNIQUE") + 1 or None)
        self.assertEqual(self.un("SELECT count(*) FROM pragma_index_list('reglements') WHERE [unique]=1 AND origin='c'")[0], 0)
        self.assertEqual(self.un("SELECT count(*) FROM pragma_index_list('reglements') WHERE partial=1")[0], 0)


# ====================================================================================================================
# D — tr_30 : cible d'un règlement [INV-71]
# ====================================================================================================================
class Cible(Base10):
    """Groupe D : un encaissement porte sur une facture hors avoir ; un remboursement sur un avoir."""

    def test_INV_71_un_encaissement_est_accepte_sur_acompte_situation_et_solde(self):
        for type_ in TYPES_F:
            with self.subTest(type=type_):
                bc, f = self.cible(type_, "500.00")
                self.accepte_r(f, "encaissement", "500.00")
                self.assertIsNotNone(self.encaisse(f, "500.00"))

    def test_INV_71_un_encaissement_sur_un_avoir_est_refuse(self):
        bc, f, a = self.cible_avec_avoir("1000.00", "500.00")
        self.refuse_r("INV-71", a, "encaissement", "1.00")
        self.refuse_r("INV-71", a, "encaissement", "500.00")
        self.refuse_r("INV-71", a, "encaissement", "0.01")

    def test_INV_71_un_encaissement_sur_un_avoir_d_acompte_de_situation_ou_de_solde_est_refuse(self):
        for type_ in TYPES_F:
            with self.subTest(type=type_):
                bc, f, a = self.cible_avec_avoir("1000.00", "100.00", type_)
                self.refuse_r("INV-71", a, "encaissement", "10.00")

    def test_INV_71_un_remboursement_est_accepte_sur_un_avoir_d_acompte_de_situation_et_de_solde(self):
        for type_ in TYPES_F:
            with self.subTest(type=type_):
                bc, f, a = self.cible_credit("1000.00", "100.00", type_)
                self.accepte_r(a, "remboursement", "100.00")
                self.assertIsNotNone(self.rembourse(a, "100.00"))

    def test_INV_71_un_remboursement_sur_une_facture_hors_avoir_est_refuse(self):
        for type_ in TYPES_F:
            with self.subTest(type=type_):
                bc, f, a = self.cible_credit("1000.00", "100.00", type_)
                self.refuse_r("INV-71", f, "remboursement", "1.00")
                self.refuse_r("INV-71", f, "remboursement", "100.00")

    def test_INV_71_le_refus_de_cible_a_une_seule_cause_meme_hors_plafond(self):
        """Un encaissement géant sur un avoir ou un remboursement géant sur une facture : le message est INV-71, jamais INV-72 / INV-74 (gardes exclusives)."""
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.refuse_r("INV-71", a, "encaissement", "99999.00")
        self.refuse_r("INV-71", f, "remboursement", "99999.00")
        m = self.tente_r(a, "encaissement", "99999.00")
        self.assertNotRegex(m, "INV-72|INV-74")
        m = self.tente_r(f, "remboursement", "99999.00")
        self.assertNotRegex(m, "INV-72|INV-74")

    def test_INV_71_la_cible_est_verifiee_aussi_pour_un_reglement_ne_annule_et_un_reglement_importe(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.refuse_r("INV-71", a, "encaissement", "1.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        self.refuse_r("INV-71", f, "remboursement", "1.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        self.refuse_r("INV-71", a, "encaissement", "1.00", origine="import", legacy_id="R1")
        self.refuse_r("INV-71", f, "remboursement", "1.00", origine="import", legacy_id="R2")

    def test_INV_71_la_cible_d_un_avoir_d_un_autre_BC_ou_d_une_autre_facture_ne_change_rien(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        bc2, f2 = self.cible("situation", "300.00")
        self.refuse_r("INV-71", a, "encaissement", "1.00")
        self.accepte_r(f2, "encaissement", "300.00")
        self.refuse_r("INV-71", f2, "remboursement", "1.00")

    def test_INV_71_type_et_cible_sont_immuables_apres_l_insertion(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        e = self.reglement(a, "remboursement", "10.00")
        self.refuse_inv("INV-70", "UPDATE reglements SET type='encaissement' WHERE id=?", e)
        self.refuse_inv("INV-70", "UPDATE reglements SET facture_id=? WHERE id=?", f, e)

    def test_INV_71_il_n_existe_pas_de_colonne_avoir_id_le_remboursement_porte_facture_id(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        e = self.rembourse(a, "10.00")
        self.assertEqual(self.un("SELECT facture_id, (SELECT type FROM factures WHERE id=facture_id) FROM reglements WHERE id=?", e), (a, "avoir"))

    def test_INV_71_la_facture_inexistante_est_laissee_a_la_cle_etrangere(self):
        self.refuse_check_r(987654, "encaissement", "1.00")
        self.refuse_check_r(987654, "remboursement", "1.00")

    def test_INV_71_type_invalide_n_est_traite_ni_par_tr_30_ni_par_tr_31(self):
        bc, f = self.cible()
        self.refuse_check_r(f, "paiement", "1.00")
        self.refuse_check_r(f, "paiement", "99999999.00")


# ====================================================================================================================
# E — tr_31 : plafond d'un encaissement [INV-72]
# ====================================================================================================================
class PlafondEncaissement(Base10):
    """Groupe E : un encaissement actif ne dépasse pas reste_du = max(0, M - encaissements actifs - absorbe)."""

    def test_INV_72_encaissement_complet_exactement_au_montant_de_la_facture(self):
        for type_ in TYPES_F:
            with self.subTest(type=type_):
                bc, f = self.cible(type_, "1000.00")
                self.refuse_r("INV-72", f, "encaissement", "1000.01")
                self.accepte_r(f, "encaissement", "1000.00")
                self.encaisse(f, "1000.00")
                self.assertEqual(self.reste_du(f), 0)
                self.assertEqual(self.etat_paiement(f), "reglee")

    def test_INV_72_encaissement_au_dessus_du_reste_du_d_un_centime_est_refuse(self):
        bc, f = self.cible("situation", "150.00")
        self.refuse_r("INV-72", f, "encaissement", "150.01")
        self.refuse_r("INV-72", f, "encaissement", "151.00")
        self.refuse_r("INV-72", f, "encaissement", "200.00")                                 # C-11 : reste dû 150.00, encaissement 200.00

    def test_INV_72_C_11_reste_du_150_encaissement_200_refuse(self):
        bc, f = self.cible("solde", "250.00")
        self.encaisse(f, "100.00")
        self.assertEqual(self.reste_du(f), 15000)
        self.refuse_r("INV-72", f, "encaissement", "200.00")
        self.refuse_r("INV-72", f, "encaissement", "150.01")
        self.accepte_r(f, "encaissement", "150.00")

    def test_INV_72_encaissements_partiels_successifs_jusqu_au_solde_exact(self):
        bc, f = self.cible("situation", "1000.00")
        for m, reste in (("0.01", 99999), ("99.99", 90000), ("400.00", 50000), ("250.00", 25000), ("249.99", 1), ("0.01", 0)):
            self.refuse_r("INV-72", f, "encaissement", eur(self.reste_du(f) + 1))
            self.encaisse(f, m)
            self.assertEqual(self.reste_du(f), reste, m)
        self.refuse_r("INV-72", f, "encaissement", "0.01")

    def test_INV_72_plusieurs_reglements_se_cumulent(self):
        bc, f = self.cible("acompte", "300.00")
        self.encaisse(f, "100.00")
        self.encaisse(f, "100.00")
        self.refuse_r("INV-72", f, "encaissement", "100.01")
        self.encaisse(f, "100.00")
        self.refuse_r("INV-72", f, "encaissement", "0.01")
        self.assertEqual(self.un("SELECT count(*) FROM reglements WHERE facture_id=?", f)[0], 3)

    def test_C_02_acompte_encaisse_partiellement_reste_du_et_etat(self):
        bc, f = self.cible("acompte", "200.00")
        self.encaisse(f, "50.00")
        self.assertEqual(self.reste_du(f), 15000)
        self.assertEqual(self.etat_paiement(f), "partiellement_reglee")

    def test_INV_72_les_encaissements_d_une_autre_facture_ne_comptent_pas(self):
        bc, f = self.cible("situation", "100.00")
        bc2, f2 = self.cible("situation", "100.00")
        self.encaisse(f2, "100.00")
        self.accepte_r(f, "encaissement", "100.00")
        self.refuse_r("INV-72", f, "encaissement", "100.01")

    def test_INV_72_deux_factures_du_meme_BC_ont_chacune_leur_plafond(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        s = self.facture(bc, "situation", "500.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        self.encaisse(a, "1000.00")
        self.refuse_r("INV-72", a, "encaissement", "0.01")
        self.accepte_r(s, "encaissement", "500.00")
        self.refuse_r("INV-72", s, "encaissement", "500.01")

    def test_INV_72_les_encaissements_d_une_facture_ne_comptent_pas_pour_son_avoir_ni_l_inverse(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.assertEqual(self.reste_du(f), 0)
        self.refuse_r("INV-72", f, "encaissement", "0.01")

    def test_INV_72_les_avoirs_reduisent_le_reste_du(self):
        bc, f = self.cible("situation", "1000.00")
        self.avoir(f, "300.00")
        self.assertEqual(self.reste_du(f), 70000)
        self.refuse_r("INV-72", f, "encaissement", "700.01")
        self.accepte_r(f, "encaissement", "700.00")
        self.avoir(f, "200.00")
        self.assertEqual(self.reste_du(f), 50000)
        self.refuse_r("INV-72", f, "encaissement", "500.01")
        self.encaisse(f, "500.00")
        self.refuse_r("INV-72", f, "encaissement", "0.01")

    def test_INV_72_l_absorption_depend_des_encaissements_deja_faits(self):
        """C-06 : l'encaissement vient AVANT l'avoir, l'état final est valide (crédit) ; l'ordre inverse est refusé (plafond au moment de l'insertion)."""
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "600.00")
        self.avoir(f, "500.00")
        k = self.compte(f)
        self.assertEqual((k.absorbe(), k.reste_du(), k.credit()), (40000, 0, 10000))
        bc2, f2 = self.cible("situation", "1000.00")
        self.avoir(f2, "500.00")
        self.refuse_r("INV-72", f2, "encaissement", "600.00")
        self.accepte_r(f2, "encaissement", "500.00")

    def test_INV_72_facture_totalement_creditee_refuse_tout_encaissement(self):
        for type_ in TYPES_F:
            with self.subTest(type=type_):
                bc, f = self.cible(type_, "400.00")
                self.neutraliser(f)
                self.assertTrue(self.neutralisee(f))
                self.assertEqual(self.reste_du(f), 0)
                self.refuse_r("INV-72", f, "encaissement", "0.01")
                self.refuse_r("INV-72", f, "encaissement", "400.00")

    def test_INV_72_facture_creditee_apres_un_encaissement_partiel(self):
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "300.00")
        self.avoir(f, "700.00")                                                              # avoir total du reste : absorbe 700, reste dû 0
        self.assertEqual(self.reste_du(f), 0)
        self.refuse_r("INV-72", f, "encaissement", "0.01")
        self.assertEqual(self.compte(f).credit(), 0)

    def test_INV_72_solde_a_zero_n_accepte_aucun_encaissement(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        self.facture(bc, "situation", "1000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        so = self.facture(bc, "solde", "0.00")
        self.assertEqual(self.reste_du(so), 0)
        self.assertEqual(self.etat_paiement(so), "reglee")                                   # reglee même sans encaissement (modèle §3.4)
        self.refuse_r("INV-72", so, "encaissement", "0.01")
        self.refuse_r("INV-72", so, "encaissement", "1.00")

    def test_INV_72_un_reglement_annule_ne_compte_plus_et_libere_la_capacite(self):
        bc, f = self.cible("situation", "100.00")
        r1 = self.encaisse(f, "100.00")
        self.refuse_r("INV-72", f, "encaissement", "0.01")
        self.annuler(r1)
        self.assertEqual(self.reste_du(f), 10000)
        self.accepte_r(f, "encaissement", "100.00")
        self.refuse_r("INV-72", f, "encaissement", "100.01")
        r2 = self.encaisse(f, "40.00")
        self.encaisse(f, "60.00")
        self.refuse_r("INV-72", f, "encaissement", "0.01")
        self.annuler(r2)
        self.accepte_r(f, "encaissement", "40.00")
        self.refuse_r("INV-72", f, "encaissement", "40.01")

    def test_INV_72_un_remboursement_ne_modifie_pas_le_plafond_d_encaissement(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")                                    # C-13 : facture 1000 payée, avoir 100
        self.rembourse(a, "100.00")
        self.assertEqual(self.reste_du(f), 0)
        self.refuse_r("INV-72", f, "encaissement", "0.01")

    def test_INV_72_plafond_par_type_de_facture_et_BC_dans_tous_les_etats(self):
        for etat in ("en_cours", "gele", "termine", "annule", "annule_gele"):
            with self.subTest(etat=etat):
                bc, f = self.cible("situation", "100.00")
                self.etat(bc, etat)
                self.accepte_r(f, "encaissement", "100.00")
                self.refuse_r("INV-72", f, "encaissement", "100.01")

    def test_INV_72_import_et_origine_v6_ont_le_meme_plafond(self):
        bc, f = self.cible("situation", "100.00")
        self.accepte_r(f, "encaissement", "100.00", origine="import", legacy_id="R1")
        self.refuse_r("INV-72", f, "encaissement", "100.01", origine="import", legacy_id="R1")
        self.refuse_r("INV-72", f, "encaissement", "100.01", origine="v6")

    def test_INV_72_encaissement_geant_refuse_meme_au_dela_de_64_bits(self):
        bc, f = self.cible("situation", "1000.00")
        for m in ("99999999999999.99", "999999999999999999.99", "99999999999999999999999.99"):
            with self.subTest(montant=m):
                self.refuse_r("INV-72", f, "encaissement", m)

    def test_INV_72_les_centimes_sont_exacts_pas_de_derive_flottante(self):
        bc, f = self.cible("situation", "0.30")
        for _ in range(3):
            self.encaisse(f, "0.10")
        self.assertEqual(self.reste_du(f), 0)
        self.refuse_r("INV-72", f, "encaissement", "0.01")
        bc, f = self.cible("situation", "1234567.89")
        self.encaisse(f, "1234567.88")
        self.refuse_r("INV-72", f, "encaissement", "0.02")
        self.accepte_r(f, "encaissement", "0.01")

    def test_INV_72_le_plafond_ne_s_applique_qu_a_la_facture_visee_avec_ids_desynchronises(self):
        """Les identifiants de facture, de BC, de client et de règlement sont tous différents : une jointure sur la mauvaise colonne ne passerait pas."""
        bc, f = self.cible("situation", "100.00")
        bc2, f2 = self.cible("situation", "5000.00")
        self.assertNotEqual(f, bc.b)
        self.encaisse(f2, "4000.00")
        self.refuse_r("INV-72", f, "encaissement", "100.01")
        self.accepte_r(f2, "encaissement", "1000.00")
        self.refuse_r("INV-72", f2, "encaissement", "1000.01")

    def test_INV_72_la_somme_des_encaissements_ne_depasse_jamais_le_montant_de_la_facture(self):
        bc, f = self.cible("situation", "100.00")
        self.encaisse(f, "60.00")
        self.encaisse(f, "40.00")
        self.assertEqual(self.ck(CK19_ENCAISSEMENTS), [])
        self.assertEqual(sum(self.compte(f).enc), self.total(f))


# ====================================================================================================================
# F — tr_31 : plafond d'un remboursement [INV-74]
# ====================================================================================================================
class PlafondRemboursement(Base10):
    """Groupe F : un remboursement actif ne dépasse pas le crédit de la facture d'origine de l'avoir visé."""

    def test_INV_74_C_06_facture_1000_encaisse_600_avoir_500_credit_100(self):
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "600.00")
        a = self.avoir(f, "500.00")
        k = self.compte(f)
        self.assertEqual((k.absorbe(), k.reste_du(), k.credit()), (40000, 0, 10000))
        self.refuse_r("INV-74", a, "remboursement", "100.01")
        self.accepte_r(a, "remboursement", "100.00")
        self.rembourse(a, "100.00")
        self.assertEqual(self.credit(f), 0)
        self.refuse_r("INV-74", a, "remboursement", "0.01")

    def test_INV_74_C_13_facture_payee_avoir_100_remboursement_100_credit_zero(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.rembourse(a, "100.00")
        self.assertEqual(self.credit(f), 0)
        self.refuse_r("INV-74", a, "remboursement", "0.01")

    def test_INV_74_sans_encaissement_l_avoir_est_absorbe_et_le_credit_est_nul(self):
        bc, f, a = self.cible_avec_avoir("1000.00", "500.00")
        self.assertEqual(self.credit(f), 0)
        self.refuse_r("INV-74", a, "remboursement", "0.01")
        self.refuse_r("INV-74", a, "remboursement", "500.00")

    def test_INV_74_avoir_total_sur_facture_impayee_aucun_credit(self):
        bc, f = self.cible("situation", "300.00")
        a = self.neutraliser(f)
        self.assertEqual(self.credit(f), 0)
        self.refuse_r("INV-74", a, "remboursement", "0.01")

    def test_INV_74_le_credit_vient_de_l_exces_d_encaissement_sur_ce_qui_reste_a_payer(self):
        """credit = Σ avoirs − absorbe : avoir 300 sur 1000, encaissé 900 (avant l'avoir) -> absorbe = min(300, 100) = 100, crédit 200."""
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "900.00")
        a = self.avoir(f, "300.00")
        self.assertEqual(self.credit(f), 20000)
        self.refuse_r("INV-74", a, "remboursement", "200.01")
        self.accepte_r(a, "remboursement", "200.00")

    def test_INV_74_remboursements_partiels_successifs_jusqu_au_credit_exact(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        for m, credit in (("0.01", 9999), ("49.99", 5000), ("30.00", 2000), ("20.00", 0)):
            self.refuse_r("INV-74", a, "remboursement", eur(self.credit(f) + 1))
            self.rembourse(a, m)
            self.assertEqual(self.credit(f), credit, m)
        self.refuse_r("INV-74", a, "remboursement", "0.01")

    def test_INV_74_le_credit_se_calcule_par_facture_d_origine_et_un_remboursement_peut_viser_n_importe_quel_avoir(self):
        """Deux avoirs 300 + 300 sur une facture 1000 payée : crédit commun 600 ; modèle §3.3 : « un remboursement peut viser n'importe quel avoir actif de cette origine »."""
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "1000.00")
        a1 = self.avoir(f, "300.00")
        a2 = self.avoir(f, "300.00")
        self.assertEqual(self.credit(f), 60000)
        self.accepte_r(a1, "remboursement", "600.00")                                         # INTERPRETATION : pas de plafond par avoir (le modèle plafonne l'origine)
        self.rembourse(a1, "400.00")
        self.accepte_r(a2, "remboursement", "200.00")
        self.refuse_r("INV-74", a2, "remboursement", "200.01")
        self.refuse_r("INV-74", a1, "remboursement", "200.01")
        self.rembourse(a2, "200.00")
        self.refuse_r("INV-74", a1, "remboursement", "0.01")
        self.refuse_r("INV-74", a2, "remboursement", "0.01")
        self.assertEqual(self.credit(f), 0)

    def test_INV_74_deux_origines_ont_deux_credits_separes(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        s = self.facture(bc, "situation", "2000.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        self.encaisse(a, "1000.00")
        self.encaisse(s, "2000.00")
        av_a = self.avoir(a, "100.00")
        av_s = self.avoir(s, "700.00")
        self.assertEqual((self.credit(a), self.credit(s)), (10000, 70000))
        self.refuse_r("INV-74", av_a, "remboursement", "100.01")
        self.accepte_r(av_a, "remboursement", "100.00")
        self.accepte_r(av_s, "remboursement", "700.00")
        self.refuse_r("INV-74", av_s, "remboursement", "700.01")
        self.rembourse(av_a, "100.00")
        self.refuse_r("INV-74", av_a, "remboursement", "0.01")
        self.accepte_r(av_s, "remboursement", "700.00")                                      # le crédit de l'autre origine est intact

    def test_INV_74_un_reglement_de_remboursement_annule_libere_le_credit(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        r = self.rembourse(a, "100.00")
        self.refuse_r("INV-74", a, "remboursement", "0.01")
        self.annuler(r)
        self.assertEqual(self.credit(f), 10000)
        self.accepte_r(a, "remboursement", "100.00")
        self.refuse_r("INV-74", a, "remboursement", "100.01")

    def test_INV_74_un_encaissement_annule_ne_cree_pas_de_credit(self):
        """Facture 1000 : encaissement 1000 annulé, encaissement 900 actif, avoir 300 : absorbe = min(300, 100) = 100, crédit 200 (l'annulé ne compte pas)."""
        bc, f = self.cible("situation", "1000.00")
        e0 = self.encaisse(f, "1000.00")
        self.annuler(e0)
        self.encaisse(f, "900.00")
        a = self.avoir(f, "300.00")
        self.assertEqual(self.credit(f), 20000)
        self.refuse_r("INV-74", a, "remboursement", "200.01")
        self.accepte_r(a, "remboursement", "200.00")

    def test_INV_74_un_encaissement_ajoute_apres_l_avoir_ne_cree_jamais_de_credit(self):
        """Avoir d'abord : l'encaissement est plafonné par M − Σ avoirs (tr_31), donc aucun crédit ne peut naître après coup."""
        bc, f, a = self.cible_avec_avoir("1000.00", "300.00")
        self.refuse_r("INV-72", f, "encaissement", "700.01")
        self.encaisse(f, "700.00")
        self.assertEqual(self.credit(f), 0)
        self.refuse_r("INV-74", a, "remboursement", "0.01")

    def test_INV_74_un_remboursement_de_facture_d_acompte_de_situation_et_de_solde(self):
        for type_ in TYPES_F:
            with self.subTest(type=type_):
                bc, f, a = self.cible_credit("700.00", "70.00", type_)
                self.refuse_r("INV-74", a, "remboursement", "70.01")
                self.accepte_r(a, "remboursement", "70.00")

    def test_INV_74_le_BC_peut_etre_dans_n_importe_quel_etat(self):
        for etat in ("en_cours", "gele", "termine", "annule", "annule_gele"):
            with self.subTest(etat=etat):
                bc, f, a = self.cible_credit("1000.00", "100.00")
                self.etat(bc, etat)
                self.accepte_r(a, "remboursement", "100.00")
                self.refuse_r("INV-74", a, "remboursement", "100.01")

    def test_INV_74_import_et_v6_ont_le_meme_plafond(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.accepte_r(a, "remboursement", "100.00", origine="import", legacy_id="R9")
        self.refuse_r("INV-74", a, "remboursement", "100.01", origine="import", legacy_id="R9")

    def test_INV_74_remboursement_geant_refuse(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        for m in ("99999999999999.99", "999999999999999999.99", "99999999999999999999999.99"):
            with self.subTest(montant=m):
                self.refuse_r("INV-74", a, "remboursement", m)

    def test_INV_74_le_credit_d_une_autre_origine_ne_compte_pas_avec_ids_desynchronises(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        bc2, f2, a2 = self.cible_credit("5000.00", "2000.00")
        self.rembourse(a2, "2000.00")
        self.assertNotEqual(a, a2)
        self.refuse_r("INV-74", a, "remboursement", "100.01")
        self.accepte_r(a, "remboursement", "100.00")

    def test_INV_74_les_centimes_sont_exacts(self):
        bc, f, a = self.cible_credit("1000.00", "0.30")
        for _ in range(3):
            self.rembourse(a, "0.10")
        self.refuse_r("INV-74", a, "remboursement", "0.01")
        self.assertEqual(self.credit(f), 0)

    def test_INV_74_le_plafond_vient_de_l_etat_au_moment_de_l_insertion(self):
        """Un avoir ajouté APRÈS fait monter le crédit disponible ; un remboursement déjà fait ne se « rejoue » pas."""
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.rembourse(a, "100.00")
        a2 = self.avoir(f, "50.00")
        self.assertEqual(self.credit(f), 5000)
        self.accepte_r(a2, "remboursement", "50.00")
        self.refuse_r("INV-74", a2, "remboursement", "50.01")


# ====================================================================================================================
# G — règlement né annulé (import d'un état historique) [Q1 validée]
# ====================================================================================================================
class ReglementNeAnnule(Base10):
    """Groupe G : un règlement peut être inséré directement annulé ; il ne consomme aucune capacité ; tr_30 reste applicable ; l'annulation est irréversible."""

    def test_Q1_un_encaissement_ne_annule_depasse_le_reste_du_sans_etre_refuse(self):
        bc, f = self.cible("situation", "100.00")
        self.encaisse(f, "100.00")
        self.accepte_r(f, "encaissement", "100.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        self.accepte_r(f, "encaissement", "99999.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")

    def test_Q1_un_remboursement_ne_annule_depasse_le_credit_sans_etre_refuse(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.accepte_r(a, "remboursement", "99999.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        bc2, f2, a2 = self.cible_avec_avoir("1000.00", "100.00")                             # aucun crédit du tout
        self.accepte_r(a2, "remboursement", "100.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")

    def test_Q1_un_reglement_ne_annule_ne_consomme_aucune_capacite(self):
        bc, f = self.cible("situation", "100.00")
        r = self.encaisse(f, "100.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        self.assertEqual(self.reste_du(f), 10000)
        self.encaisse(f, "100.00")
        self.refuse_r("INV-72", f, "encaissement", "0.01")
        self.assertEqual(self.un("SELECT cancelled_at FROM reglements WHERE id=?", r)[0], TS_ANNUL)

    def test_Q1_un_remboursement_ne_annule_ne_consomme_aucun_credit(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.rembourse(a, "100.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        self.assertEqual(self.credit(f), 10000)
        self.rembourse(a, "100.00")
        self.refuse_r("INV-74", a, "remboursement", "0.01")

    def test_Q1_le_reglement_ne_annule_n_empeche_pas_l_annulation_d_un_encaissement_actif(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.rembourse(a, "100.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        e = self.un("SELECT id FROM reglements WHERE type='encaissement' AND facture_id=?", f)[0]
        self.accepte_annul(e)

    def test_Q1_tr_30_s_applique_toujours(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.refuse_r("INV-71", a, "encaissement", "1.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        self.refuse_r("INV-71", f, "remboursement", "1.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")

    def test_Q1_les_contraintes_de_forme_et_la_paire_d_annulation_s_appliquent_toujours(self):
        bc, f = self.cible("situation", "100.00")
        self.refuse_check_r(f, "encaissement", "1.00", cancelled_at=TS_ANNUL)
        self.refuse_check_r(f, "encaissement", "1.00", motif_annulation="x")
        self.refuse_check_r(f, "encaissement", "0.00", cancelled_at=TS_ANNUL, motif_annulation="x")
        self.refuse_check_r(f, "encaissement", "1.00", cancelled_at="hier", motif_annulation="x")

    def test_Q1_origine_import_et_origine_v6_sont_traitees_de_la_meme_facon(self):
        bc, f = self.cible("situation", "100.00")
        self.encaisse(f, "100.00")
        self.accepte_r(f, "encaissement", "500.00", cancelled_at=TS_ANNUL, motif_annulation="Annulé V2", origine="import", legacy_id="R1")
        self.accepte_r(f, "encaissement", "500.00", cancelled_at=TS_ANNUL, motif_annulation="Annulé", origine="v6")

    def test_Q1_un_reglement_ne_annule_ne_peut_plus_etre_ni_reactive_ni_re_annule_ni_modifie(self):
        bc, f = self.cible("situation", "100.00")
        r = self.encaisse(f, "100.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        self.refuse_inv("INV-70", "UPDATE reglements SET cancelled_at=NULL, motif_annulation=NULL WHERE id=?", r)
        self.refuse_inv("INV-70", "UPDATE reglements SET cancelled_at=?, motif_annulation='Autre' WHERE id=?", TS_VALIDES[0], r)
        self.refuse_inv("INV-70", "UPDATE reglements SET montant='1.00' WHERE id=?", r)
        self.refuse_inv("INV-70", "DELETE FROM reglements WHERE id=?", r)

    def test_Q1_un_historique_complet_peut_etre_represente(self):
        """Facture 1000 : encaissement 1000 annulé (doublon), encaissement 1000 actif, avoir 100 : état final valide, crédit 100."""
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "1000.00", cancelled_at="2026-10-11T09:00:00.000Z", motif_annulation="Doublon de saisie", date_evenement="2026-10-09")
        self.encaisse(f, "1000.00", date_evenement="2026-10-10")
        a = self.avoir(f, "100.00")
        self.assertEqual(self.credit(f), 10000)
        self.assertEqual(self.ck(CK19_ENCAISSEMENTS), [])
        self.assertEqual(self.ck(CK20_CREDIT), [])
        self.assertIsNotNone(a)


# ====================================================================================================================
# H — tr_32 : immuabilité, annulation unique, non-suppression [INV-70]
# ====================================================================================================================
class Immuabilite(Base10):
    """Groupe H : seules cancelled_at et motif_annulation se renseignent, une seule fois ; aucune suppression (REPLACE compris)."""

    COLONNES_FIGEES = (("id", 123456), ("facture_id", None), ("type", "remboursement"), ("date_evenement", "2027-01-01"), ("montant", "1.00"), ("mode", "carte"),
                       ("reference", "AUTRE"), ("note", "AUTRE"), ("created_at", "2000-01-01T00:00:00.000Z"), ("origine", "import"), ("legacy_id", "L"),
                       ("legacy_data", "{}"))

    def setUp(self):
        super().setUp()
        self.bc, self.f = self.cible("situation", "1000.00")
        self.r = self.encaisse(self.f, "100.00", reference="CHQ-1", note="n")

    def test_INV_70_chaque_colonne_figee_refuse_toute_modification(self):
        for col, valeur in self.COLONNES_FIGEES:
            valeur = self.bc2_facture() if col == "facture_id" else valeur
            with self.subTest(colonne=col):
                self.refuse_inv("INV-70", f"UPDATE reglements SET {col}=? WHERE id=?", valeur, self.r)

    def bc2_facture(self):
        bc2, f2 = self.cible("situation", "1000.00")
        return f2

    def test_INV_70_modification_vers_null_refusee_pour_les_colonnes_facultatives(self):
        for col in ("reference", "note"):
            with self.subTest(colonne=col):
                self.refuse_inv("INV-70", f"UPDATE reglements SET {col}=NULL WHERE id=?", self.r)
        r2 = self.encaisse(self.f, "1.00", reference=None, note=None)
        for col in ("reference", "note"):
            with self.subTest(colonne=col, depuis="NULL"):
                self.refuse_inv("INV-70", f"UPDATE reglements SET {col}='x' WHERE id=?", r2)

    def test_INV_70_un_update_multiple_est_refuse_si_une_seule_colonne_figee_change(self):
        self.refuse_inv("INV-70", "UPDATE reglements SET cancelled_at=?, motif_annulation='x', montant='99.00' WHERE id=?", TS_ANNUL, self.r)
        self.assertEqual(self.un("SELECT montant, cancelled_at FROM reglements WHERE id=?", self.r), ("100.00", None))

    def test_INV_70_UPDATE_OR_REPLACE_et_OR_IGNORE_ne_contournent_pas(self):
        for verbe in ("OR REPLACE", "OR IGNORE", "OR FAIL", "OR ROLLBACK", "OR ABORT"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT v")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-70"):
                    self.db.execute(f"UPDATE {verbe} reglements SET montant='1.00' WHERE id=?", (self.r,))
                self.db.execute("ROLLBACK TO v")
                self.db.execute("RELEASE v")
        self.assertEqual(self.un("SELECT montant FROM reglements WHERE id=?", self.r)[0], "100.00")

    def test_INV_70_l_annulation_pose_la_date_et_le_motif_ensemble(self):
        self.annuler(self.r, "Erreur de saisie", TS_ANNUL)
        self.assertEqual(self.un("SELECT cancelled_at, motif_annulation, montant, type FROM reglements WHERE id=?", self.r),
                         (TS_ANNUL, "Erreur de saisie", "100.00", "encaissement"))

    def test_INV_70_l_annulation_exige_date_et_motif(self):
        self.refuse_check("UPDATE reglements SET cancelled_at=? WHERE id=?", TS_ANNUL, self.r)
        self.refuse_check("UPDATE reglements SET motif_annulation='x' WHERE id=?", self.r)
        self.refuse_check("UPDATE reglements SET cancelled_at=?, motif_annulation='' WHERE id=?", TS_ANNUL, self.r)
        self.refuse_check("UPDATE reglements SET cancelled_at='2026-10-10', motif_annulation='x' WHERE id=?", self.r)
        for ts in TS_INVALIDES:
            with self.subTest(ts=ts):
                self.refuse_check("UPDATE reglements SET cancelled_at=?, motif_annulation='x' WHERE id=?", ts, self.r)
        self.assertIsNone(self.un("SELECT cancelled_at FROM reglements WHERE id=?", self.r)[0])

    def test_INV_70_une_annulation_n_a_lieu_qu_une_seule_fois(self):
        self.annuler(self.r)
        self.refuse_annul("INV-70", self.r, motif="Deuxième tentative")
        self.refuse_annul("INV-70", self.r, quand="2100-01-01T00:00:00.000Z")
        self.refuse_inv("INV-70", "UPDATE reglements SET motif_annulation='Autre' WHERE id=?", self.r)
        self.refuse_inv("INV-70", "UPDATE reglements SET cancelled_at=? WHERE id=?", TS_VALIDES[0], self.r)
        self.assertEqual(self.un("SELECT cancelled_at, motif_annulation FROM reglements WHERE id=?", self.r), (TS_ANNUL, "Erreur de saisie"))

    def test_INV_70_une_annulation_est_irreversible(self):
        self.annuler(self.r)
        self.refuse_inv("INV-70", "UPDATE reglements SET cancelled_at=NULL, motif_annulation=NULL WHERE id=?", self.r)
        self.refuse_inv("INV-70", "UPDATE reglements SET cancelled_at=NULL WHERE id=?", self.r)
        self.assertIsNotNone(self.un("SELECT cancelled_at FROM reglements WHERE id=?", self.r)[0])

    def test_INV_70_un_reglement_annule_est_totalement_immuable_meme_sans_changement_de_valeur(self):
        self.annuler(self.r)
        self.refuse_inv("INV-70", "UPDATE reglements SET montant=montant WHERE id=?", self.r)
        self.refuse_inv("INV-70", "UPDATE reglements SET id=id WHERE id=?", self.r)
        self.refuse_inv("INV-70", "UPDATE reglements SET note=note WHERE id=?", self.r)

    def test_INV_70_un_update_sans_changement_sur_un_reglement_actif_reste_sans_effet(self):
        """tr_32 compare avec IS NOT : une écriture identique ne modifie rien et n'est pas une annulation."""
        avant = self.un("SELECT * FROM reglements WHERE id=?", self.r)
        self.db.execute("UPDATE reglements SET montant=montant, type=type, reference=reference, note=note, cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (self.r,))
        self.assertEqual(self.un("SELECT * FROM reglements WHERE id=?", self.r), avant)

    def test_INV_70_un_update_sans_ligne_ne_declenche_rien(self):
        self.db.execute("UPDATE reglements SET montant='1.00' WHERE id=-1")
        self.assertEqual(self.un("SELECT montant FROM reglements WHERE id=?", self.r)[0], "100.00")

    def test_INV_70_un_update_global_est_refuse_atomiquement(self):
        r2 = self.encaisse(self.f, "5.00")
        self.annuler(r2)                                                                     # r2 annulé : l'UPDATE global l'atteint et doit tout annuler
        self.refuse_inv("INV-70", "UPDATE reglements SET note='x'")
        self.assertEqual(self.un("SELECT note FROM reglements WHERE id=?", self.r)[0], "n")

    def test_INV_70_un_reglement_ne_se_supprime_jamais_actif_ou_annule(self):
        self.refuse_inv("INV-70", "DELETE FROM reglements WHERE id=?", self.r)
        self.annuler(self.r)
        self.refuse_inv("INV-70", "DELETE FROM reglements WHERE id=?", self.r)
        self.refuse_inv("INV-70", "DELETE FROM reglements")
        self.refuse_inv("INV-70", "DELETE FROM reglements WHERE facture_id=?", self.f)
        self.assertEqual(self.nb_reglements(), 1)

    def test_INV_70_un_delete_sans_ligne_ne_declenche_rien(self):
        self.db.execute("DELETE FROM reglements WHERE id=-1")
        self.assertEqual(self.nb_reglements(), 1)

    def test_INV_70_INSERT_OR_REPLACE_sur_un_id_existant_est_refuse(self):
        for etat in ("actif", "annule"):
            with self.subTest(etat=etat):
                if etat == "annule":
                    self.annuler(self.r)
                avant = self.un("SELECT * FROM reglements WHERE id=?", self.r)
                self.db.execute("SAVEPOINT v")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-70"):
                    self.db.execute("INSERT OR REPLACE INTO reglements (id, facture_id, type, date_evenement, montant, mode) VALUES (?, ?, 'encaissement', ?, '1.00', 'carte')",
                                    (self.r, self.f, D_REF))
                self.db.execute("ROLLBACK TO v")
                self.db.execute("RELEASE v")
                self.assertEqual(self.un("SELECT * FROM reglements WHERE id=?", self.r), avant)

    def test_INV_70_REPLACE_INTO_est_refuse_comme_INSERT_OR_REPLACE(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-70"):
            self.db.execute("REPLACE INTO reglements (id, facture_id, type, date_evenement, montant, mode) VALUES (?, ?, 'encaissement', ?, '1.00', 'carte')",
                            (self.r, self.f, D_REF))
        self.assertEqual(self.un("SELECT montant FROM reglements WHERE id=?", self.r)[0], "100.00")

    def test_INV_70_INSERT_OR_REPLACE_sans_conflit_est_un_insert_ordinaire(self):
        n = self.nb_reglements()
        self.db.execute("INSERT OR REPLACE INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '1.00', 'carte')", (self.f, D_REF))
        self.assertEqual(self.nb_reglements(), n + 1)
        self.db.execute("INSERT OR IGNORE INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '1.00', 'carte')", (self.f, D_REF))
        self.assertEqual(self.nb_reglements(), n + 2)

    def test_INV_70_INSERT_OR_IGNORE_ne_masque_aucun_refus_de_trigger(self):
        n = self.nb_reglements()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-72"):
            self.db.execute("INSERT OR IGNORE INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '99999.00', 'carte')", (self.f, D_REF))
        self.assertEqual(self.nb_reglements(), n)

    def test_INV_70_TEMOIN_sans_recursive_triggers_le_replace_efface_le_reglement(self):
        """Démontre pourquoi D-39 est obligatoire : sans recursive_triggers, INSERT OR REPLACE supprime un règlement sans passer par tr_32."""
        t = Base10()
        t.db = migrer10(recursive=False)
        t._n = 0
        t.desynchroniser_ids()
        bc, f = t.cible("situation", "1000.00")
        r = t.encaisse(f, "100.00")
        t.db.execute("INSERT OR REPLACE INTO reglements (id, facture_id, type, date_evenement, montant, mode) VALUES (?, ?, 'encaissement', ?, '1.00', 'carte')", (r, f, D_REF))
        self.assertEqual(t.un("SELECT montant FROM reglements WHERE id=?", r)[0], "1.00")
        self.assertEqual(t.un("PRAGMA recursive_triggers")[0], 0)
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)

    def test_INV_70_les_triggers_d_immuabilite_ne_lisent_aucune_autre_table(self):
        sql = " ".join(self.un("SELECT sql FROM sqlite_master WHERE name=?", n)[0] for n in ("tr_32_reglements_update", "tr_32_reglements_no_delete"))
        self.assertNotRegex(sql, r"\b(FROM|JOIN)\b")

    def test_INV_70_l_annulation_d_un_remboursement_n_est_pas_refusee_par_tr_32(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        rb = self.rembourse(a, "100.00")
        self.accepte_annul(rb)
        self.annuler(rb)
        self.assertEqual(self.credit(f), 10000)


# ====================================================================================================================
# I — tr_33 : annulation d'un encaissement [INV-75]
# ====================================================================================================================
class AnnulationEncaissement(Base10):
    """Groupe I : l'annulation d'un encaissement est refusée si elle rend le crédit inférieur aux remboursements actifs."""

    def test_C_12_annulation_refusee_si_le_credit_deviendrait_inferieur_aux_remboursements(self):
        bc, f = self.cible("situation", "1000.00")
        e = self.encaisse(f, "600.00")
        a = self.avoir(f, "500.00")
        self.rembourse(a, "100.00")
        self.assertEqual(self.credit(f), 0)
        self.refuse_annul("INV-75", e)
        self.assertIsNone(self.un("SELECT cancelled_at FROM reglements WHERE id=?", e)[0])

    def test_INV_75_annulation_acceptee_si_aucun_remboursement(self):
        bc, f = self.cible("situation", "1000.00")
        e = self.encaisse(f, "600.00")
        self.avoir(f, "500.00")
        self.accepte_annul(e)
        self.annuler(e)
        self.assertEqual(self.reste_du(f), 50000)
        self.assertEqual(self.credit(f), 0)

    def test_INV_75_annulation_acceptee_apres_annulation_du_remboursement(self):
        bc, f = self.cible("situation", "1000.00")
        e = self.encaisse(f, "600.00")
        a = self.avoir(f, "500.00")
        rb = self.rembourse(a, "100.00")
        self.refuse_annul("INV-75", e)
        self.annuler(rb)
        self.accepte_annul(e)

    def test_INV_75_borne_exacte_le_credit_egal_aux_remboursements_est_accepte(self):
        """M = 1000, avoir 500, encaissements 500 + 100 + 200 = 800 -> absorbe 200, crédit 300 ; remboursement 100.
        Annuler 200 : absorbe 400, crédit 100 = remboursements -> accepté ; annuler ensuite 100 : crédit 0 < 100 -> refusé."""
        bc, f = self.cible("situation", "1000.00")
        e1 = self.encaisse(f, "500.00")
        e2 = self.encaisse(f, "100.00")
        e3 = self.encaisse(f, "200.00")
        a = self.avoir(f, "500.00")
        self.assertEqual(self.credit(f), 30000)
        self.rembourse(a, "100.00")
        self.assertEqual(self.credit(f), 20000)
        self.accepte_annul(e3)
        self.annuler(e3)
        self.assertEqual(self.compte(f).somme_avoirs - self.compte(f).absorbe(), 10000)       # crédit avant remboursement = 100 = Σ remboursements
        self.refuse_annul("INV-75", e2)
        self.refuse_annul("INV-75", e1)

    def test_INV_75_un_centime_de_trop_est_refuse(self):
        bc, f = self.cible("situation", "1000.00")
        e1 = self.encaisse(f, "500.00")
        e2 = self.encaisse(f, "100.01")
        a = self.avoir(f, "500.00")                                                          # encaissé 600.01 -> absorbe 399.99, crédit 100.01
        self.assertEqual(self.compte(f).somme_avoirs - self.compte(f).absorbe(), 10001)
        self.rembourse(a, "100.01")
        self.refuse_annul("INV-75", e2)
        self.refuse_annul("INV-75", e1)

    def test_INV_75_un_centime_de_marge_est_accepte(self):
        bc, f = self.cible("situation", "1000.00")
        e1 = self.encaisse(f, "500.00")
        e2 = self.encaisse(f, "100.01")
        e3 = self.encaisse(f, "0.01")
        a = self.avoir(f, "500.00")                                                          # encaissé 600.02 -> crédit 100.02
        self.rembourse(a, "100.01")
        self.accepte_annul(e3)                                                               # encaissé 600.01 -> crédit 100.01 = remboursements
        self.annuler(e3)
        self.refuse_annul("INV-75", e2)

    def test_INV_75_l_annulation_d_un_encaissement_libere_du_reste_du(self):
        bc, f = self.cible("situation", "100.00")
        e = self.encaisse(f, "100.00")
        self.annuler(e)
        self.assertEqual(self.reste_du(f), 10000)
        self.assertEqual(self.etat_paiement(f), "en_attente")
        self.accepte_r(f, "encaissement", "100.00")

    def test_INV_75_seul_un_remboursement_de_la_meme_origine_compte(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        s = self.facture(bc, "situation", "2000.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        ea = self.encaisse(a, "1000.00")
        es = self.encaisse(s, "2000.00")
        av_a = self.avoir(a, "100.00")
        av_s = self.avoir(s, "100.00")
        self.rembourse(av_a, "100.00")                                                       # remboursement de l'origine a
        self.accepte_annul(es)                                                               # annuler l'encaissement de s : le crédit de s devient 0, 0 remboursements chez s
        self.refuse_annul("INV-75", ea)                                                      # annuler celui de a : crédit 0 < 100
        self.assertIsNotNone(av_s)

    def test_INV_75_un_remboursement_annule_ne_compte_pas(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        rb = self.rembourse(a, "100.00")
        self.annuler(rb)
        e = self.un("SELECT id FROM reglements WHERE type='encaissement' AND facture_id=?", f)[0]
        self.accepte_annul(e)

    def test_INV_75_un_remboursement_ne_annule_ne_compte_pas(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.rembourse(a, "100.00", cancelled_at=TS_ANNUL, motif_annulation="Historique")
        e = self.un("SELECT id FROM reglements WHERE type='encaissement' AND facture_id=?", f)[0]
        self.accepte_annul(e)

    def test_INV_75_un_encaissement_deja_annule_ne_compte_pas_dans_le_calcul(self):
        """M=1000, avoir 500 ; e1 600 actif, e2 150 annulé auparavant ; remboursement 100 : annuler e1 est refusé comme sans e2."""
        bc, f = self.cible("situation", "1000.00")
        e1 = self.encaisse(f, "600.00")
        e2 = self.encaisse(f, "150.00")
        self.annuler(e2)
        a = self.avoir(f, "500.00")
        self.rembourse(a, "100.00")
        self.refuse_annul("INV-75", e1)

    def test_INV_75_l_annulation_d_un_encaissement_ne_depend_pas_des_autres_factures(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        bc2, f2, a2 = self.cible_credit("1000.00", "100.00")
        self.rembourse(a2, "100.00")
        e = self.un("SELECT id FROM reglements WHERE type='encaissement' AND facture_id=?", f)[0]
        self.accepte_annul(e)

    def test_INV_75_l_annulation_est_possible_sur_un_BC_dans_tous_les_etats(self):
        for etat in ("en_cours", "gele", "termine", "annule", "annule_gele"):
            with self.subTest(etat=etat):
                bc, f = self.cible("situation", "100.00")
                e = self.encaisse(f, "100.00")
                self.etat(bc, etat)
                self.accepte_annul(e)

    def test_INV_75_import_et_v6_sont_traites_de_la_meme_facon(self):
        bc, f = self.cible("situation", "1000.00")
        e = self.encaisse(f, "600.00", origine="import", legacy_id="R1")
        a = self.avoir(f, "500.00")
        self.rembourse(a, "100.00", origine="import", legacy_id="R2")
        self.refuse_annul("INV-75", e)

    def test_INV_75_la_garde_vise_le_seul_passage_de_actif_a_annule_d_un_encaissement(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        e = self.un("SELECT id FROM reglements WHERE type='encaissement' AND facture_id=?", f)[0]
        rb = self.rembourse(a, "100.00")
        self.accepte_annul(rb)                                                               # un remboursement s'annule toujours
        self.annuler(rb)
        self.refuse_inv("INV-70", "UPDATE reglements SET montant='1.00' WHERE id=?", e)      # une modification autre est refusée par tr_32, pas par tr_33

    def test_INV_75_message_d_annulation_refusee_n_est_pas_celui_de_l_immuabilite(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        e = self.un("SELECT id FROM reglements WHERE type='encaissement' AND facture_id=?", f)[0]
        self.rembourse(a, "100.00")
        m = self.tente_annul(e)
        self.assertRegex(m, "INV-75")
        self.assertNotRegex(m, "INV-70")

    def test_INV_79_annuler_puis_recalculer_ramene_le_BC_de_termine_a_en_cours(self):
        """INV-79 : le recalcul en chaîne relève du SERVICE ; le SQL n'écrit pas dans bons_commande."""
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        e = self.encaisse(so, "1000.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")
        self.annuler(e)
        self.assertEqual(self.etat_bc(bc)[0], "termine")                                     # le trigger n'a rien écrit
        self.recalcul_financier(bc)
        statut, completed, d100, avanc, nette = self.etat_bc(bc)
        self.assertEqual((statut, completed, avanc), ("en_cours", None, "100.00"))


# ====================================================================================================================
# J — états dérivés et cas chiffrés du modèle (C-02, C-05, C-06, C-08, C-10, C-11, C-36)
# ====================================================================================================================
class CasChiffres(Base10):
    """Groupe J : les cas chiffrés du modèle (§17) et les états de paiement, recalculés par l'oracle Python."""

    def monde_acompte(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "200.00")}])
        return bc, self.acompte(bc, bc.d[0], "200.00")

    def test_C_02_acompte_encaisse_50_reste_du_150_partiellement_reglee(self):
        bc, a = self.monde_acompte()
        self.assertEqual((self.reste_du(a), self.etat_paiement(a)), (20000, "en_attente"))
        self.encaisse(a, "50.00")
        self.assertEqual((self.reste_du(a), self.etat_paiement(a)), (15000, "partiellement_reglee"))
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")                                    # aucun gel, aucun changement de statut (PT-8)

    def test_C_11_reste_du_150_encaissement_200_refuse_150_accepte(self):
        bc, a = self.monde_acompte()
        self.encaisse(a, "50.00")
        self.refuse_r("INV-72", a, "encaissement", "200.00")
        self.refuse_r("INV-72", a, "encaissement", "150.01")
        self.encaisse(a, "150.00")
        self.assertEqual((self.reste_du(a), self.etat_paiement(a)), (0, "reglee"))

    def test_C_05_acompte_200_situation_400_solde_250_puis_150_termine(self):
        bc, a = self.monde_acompte()
        s = self.facture(bc, "situation", "400.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        so = self.solde(bc)
        self.assertEqual(self.total(so), c("400.00"))
        self.encaisse(a, "200.00")
        self.encaisse(s, "400.00")
        self.encaisse(so, "250.00")
        self.assertEqual(self.reste_du(so), 15000)
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")
        self.encaisse(so, "150.00")
        self.recalcul_financier(bc)
        statut, completed, d100, avanc, _ = self.etat_bc(bc)
        self.assertEqual((statut, completed is not None, avanc), ("termine", True, "100.00"))
        self.assertEqual(self.ck(CK06_TERMINE), [])

    def test_C_06_facture_1000_encaisse_600_avoir_500(self):
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "600.00")
        a = self.avoir(f, "500.00")
        k = self.compte(f)
        self.assertEqual((k.absorbe(), k.reste_du(), k.credit()), (40000, 0, 10000))
        self.assertEqual(self.etat_paiement(f), "reglee")

    def test_C_08_acompte_200_situation_800_solde_a_zero_le_BC_n_est_pas_termine_tant_que_l_acompte_ou_la_situation_est_due(self):
        bc, a = self.monde_acompte()
        s = self.facture(bc, "situation", "800.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        so = self.solde(bc)
        self.assertEqual(self.total(so), 0)
        self.assertEqual((self.reste_du(so), self.etat_paiement(so)), (0, "reglee"))          # reglee même sans encaissement (modèle §3.3)
        self.refuse_r("INV-72", so, "encaissement", "0.01")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")
        self.encaisse(a, "200.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")                                    # la situation reste due
        self.encaisse(s, "800.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")

    def test_C_10_solde_400_impaye_avoir_400_le_reste_du_du_solde_est_nul(self):
        """Volet financier de C-10 : l'avoir absorbe le reste dû (aucun encaissement). Le statut du BC suit la décision 006 (VR-07/D) :
        l'avoir TOTAL neutralise le solde, donc plus de solde actif -> en_cours (écart documentaire signalé dans le cadrage)."""
        bc, a = self.monde_acompte()
        s = self.facture(bc, "situation", "400.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        so = self.solde(bc)
        self.encaisse(a, "200.00")
        self.encaisse(s, "400.00")
        av = self.avoir(so, "400.00")
        k = self.compte(so)
        self.assertEqual((k.absorbe(), k.reste_du(), k.credit()), (40000, 0, 0))
        self.assertEqual(self.reste_du_bc(bc), 0)
        self.assertEqual(self.tous("SELECT count(*) FROM reglements WHERE facture_id=?", so), [(0,)])   # aucun encaissement URSSAF
        self.assertFalse(self.termine_calcule(bc))
        self.refuse_r("INV-74", av, "remboursement", "0.01")

    def test_C_10_variante_avoir_partiel_sur_le_solde_reste_du_reduit_et_BC_termine_a_Sigma_reste_nul(self):
        bc, a = self.monde_acompte()
        s = self.facture(bc, "situation", "400.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        so = self.solde(bc)
        self.encaisse(a, "200.00")
        self.encaisse(s, "400.00")
        self.encaisse(so, "300.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")
        self.avoir(so, "100.00")                                                             # absorbe 100 -> reste_du solde 0, solde toujours actif
        self.assertEqual(self.reste_du(so), 0)
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")
        self.assertEqual(self.ck(CK06_TERMINE), [])

    def test_C_36_BC_annule_portant_acompte_paye_situations_et_encaissements(self):
        bc, a = self.monde_acompte()
        s = self.facture(bc, "situation", "400.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        ea = self.encaisse(a, "200.00")
        es = self.encaisse(s, "100.00")
        avant = self.nb_reglements()
        self.etat(bc, "annule")
        self.assertEqual(self.nb_reglements(), avant)                                        # règlements conservés
        self.assertEqual(self.etat_bc(bc)[0], "annule")
        self.accepte_r(s, "encaissement", "300.00")                                           # règlement sur document existant : possible
        self.encaisse(s, "300.00")
        self.accepte_annul(es)
        self.annuler(es)
        av = self.avoir(a, "50.00")                                                           # avoir sur document existant : possible (INV-188)
        self.accepte_r(av, "remboursement", "50.00")
        self.refuse_f("INV-188", bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht=eur(self.nette(bc)))
        self.refuse_f("INV-188", bc, "solde", eur(self.contractuel(bc) - self.nette(bc)))
        self.assertEqual(self.etat_bc(bc)[0], "annule")
        self.assertIsNotNone(ea)

    def test_C_36_aucun_nouvel_acompte_sur_un_BC_annule(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "200.00")}])
        self.etat(bc, "annule")
        self.refuse_f("INV-188", bc, "acompte", "200.00", devis_id=bc.d[0])

    def test_etats_de_paiement_aux_bornes(self):
        bc, f = self.cible("situation", "100.00")
        self.assertEqual(self.etat_paiement(f), "en_attente")
        self.encaisse(f, "0.01")
        self.assertEqual(self.etat_paiement(f), "partiellement_reglee")
        self.encaisse(f, "99.98")
        self.assertEqual(self.etat_paiement(f), "partiellement_reglee")
        self.encaisse(f, "0.01")
        self.assertEqual(self.etat_paiement(f), "reglee")

    def test_etat_d_une_facture_couverte_par_avoir_sans_encaissement_est_reglee(self):
        bc, f = self.cible("situation", "100.00")
        self.avoir(f, "100.00")
        self.assertEqual((self.reste_du(f), self.etat_paiement(f)), (0, "reglee"))

    def test_une_facture_a_zero_est_reglee_sans_encaissement_et_n_en_accepte_aucun(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "200.00")}])
        self.acompte(bc, bc.d[0], "200.00")
        self.facture(bc, "situation", "800.00", situation_numero=1, montant_deja_facture_ht="200.00")
        so = self.solde(bc)
        self.assertEqual(self.etat_paiement(so), "reglee")
        self.refuse_r("INV-72", so, "encaissement", "0.01")

    def test_le_reste_du_du_BC_est_la_somme_des_restes_dus_hors_avoir(self):
        bc, a = self.monde_acompte()
        s = self.facture(bc, "situation", "400.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))
        self.encaisse(a, "50.00")
        self.encaisse(s, "100.00")
        self.avoir(s, "50.00")
        self.assertEqual(self.reste_du_bc(bc), 15000 + 25000)

    def test_l_ordre_des_encaissements_n_a_pas_d_effet_sur_l_etat(self):
        import itertools
        for ordre in itertools.permutations(("10.00", "20.00", "30.00")):
            with self.subTest(ordre=ordre):
                bc, f = self.cible("situation", "60.00")
                for m in ordre:
                    self.encaisse(f, m)
                self.assertEqual((self.reste_du(f), self.etat_paiement(f)), (0, "reglee"))
                self.refuse_r("INV-72", f, "encaissement", "0.01")


# ====================================================================================================================
# K — intégration BC : un règlement n'est jamais une réouverture commerciale
# ====================================================================================================================
class IntegrationBC(Base10):
    """Groupe K : 007 n'écrit jamais dans bons_commande ; le retour `termine -> en_cours` est un recalcul de service qui ne réautorise rien (006 reste en vigueur)."""

    def bc_termine(self, acompte=False):
        spec = {"lignes": ["1000.00"]}
        if acompte:
            spec["acompte"] = ("montant", "100.00")
        bc = self.monde(devis=[spec])
        so = self.solde(bc)
        e = self.encaisse(so, "1000.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")
        return bc, so, e

    def test_aucun_trigger_de_007_ne_touche_bons_commande(self):
        for nom in TRIGGERS_007:
            with self.subTest(trigger=nom):
                sql = self.un("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", nom)[0]
                self.assertNotRegex(sql, r"bons_commande|bc_historique|bc_devis|UPDATE\s+\w+\s+SET|INSERT\s+INTO|DELETE\s+FROM")

    def test_un_reglement_ne_modifie_pas_le_BC_dans_aucun_etat(self):
        for etat in ("en_cours", "gele", "termine", "annule", "annule_gele"):
            with self.subTest(etat=etat):
                bc, f = self.cible("situation", "1000.00")
                self.etat(bc, etat)
                avant = (self.ligne_bc(bc), self.empreinte("bons_commande"), self.empreinte("factures"))
                e = self.encaisse(f, "400.00")
                a = self.avoir(f, "100.00")
                avant_a = (self.ligne_bc(bc), self.empreinte("bons_commande"))
                self.annuler(e)
                self.assertEqual(self.ligne_bc(bc), avant_a[0])
                self.assertEqual(self.empreinte("bons_commande"), avant_a[1])
                self.assertEqual(avant[0], avant_a[0])

    def test_l_historique_du_BC_n_est_pas_alimente_par_les_triggers_007(self):
        bc, f = self.cible("situation", "1000.00")
        n = {t: self.un(f"SELECT count(*) FROM {t}")[0] for t in ("bc_historique",)} if self.un("SELECT count(*) FROM sqlite_master WHERE name='bc_historique'")[0] else {}
        e = self.encaisse(f, "1000.00")
        self.annuler(e)
        for t, v in n.items():
            self.assertEqual(self.un(f"SELECT count(*) FROM {t}")[0], v)

    def test_cycle_complet_en_cours_termine_en_cours_termine(self):
        bc, so, e = self.bc_termine()
        self.annuler(e)
        self.assertEqual(self.etat_bc(bc)[0], "termine")                                     # 007 n'a rien écrit : le recalcul est un service
        self.assertEqual(self.ck(CK06_TERMINE), [(bc.b,)])                                    # la dérive est détectable par CK-06
        self.recalcul_financier(bc)
        statut, completed, d100, avanc, _ = self.etat_bc(bc)
        self.assertEqual((statut, completed, avanc), ("en_cours", None, "100.00"))           # solde toujours actif : 100 % facturé
        self.assertIsNotNone(d100)
        self.assertEqual(self.ck(CK06_TERMINE), [])
        self.encaisse(so, "1000.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")
        self.assertEqual(self.ck(CK06_TERMINE), [])

    def test_apres_le_retour_en_cours_aucune_reouverture_commerciale_n_est_possible(self):
        """Précision d'intégration (cadrage §2bis) : devis, acompte, situation, second solde actif restent refusés par 006."""
        bc, so, e = self.bc_termine(acompte=True)
        self.annuler(e)
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")
        self.refuse_f("INV-58", bc, "acompte", "100.00", devis_id=bc.d[0])
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_f("INV-52", bc, "solde", "0.00")
        self.refuse_f("INV-52", bc, "solde", "1000.00")
        autre = self.brouillon(client_id=bc.cli)
        self.finaliser(autre)
        self.accepter(autre)
        self.db.execute("SAVEPOINT x")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-187"):
            self.rattacher(bc.b, autre)
        self.db.execute("ROLLBACK TO x")
        self.db.execute("RELEASE x")
        self.assertEqual(self.tous("SELECT count(*) FROM bc_devis WHERE bc_id=?", bc.b), [(1,)])

    def test_apres_le_retour_en_cours_un_avoir_et_un_reglement_restent_possibles(self):
        bc, so, e = self.bc_termine()
        self.annuler(e)
        self.recalcul_financier(bc)
        self.accepte_r(so, "encaissement", "1000.00")
        self.accepte_r(so, "encaissement", "400.00")
        self.encaisse(so, "400.00")
        self.avoir(so, "100.00")                                                              # avoir partiel sur le solde : toujours possible

    def test_retour_en_cours_apres_avoir_total_sur_le_solde_ne_reouvre_ni_devis_ni_acompte_ni_situation(self):
        bc, so, e = self.bc_termine(acompte=True)
        self.annuler(e)
        self.recalcul_financier(bc)
        a = self.neutraliser(so)                                                              # avoir total : plus de solde actif
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")
        self.assertIsNone(self.etat_bc(bc)[2])                                                # date_100_facture NULL
        self.refuse_f("INV-58", bc, "acompte", "100.00", devis_id=bc.d[0])
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        autre = self.brouillon(client_id=bc.cli)
        self.finaliser(autre)
        self.accepter(autre)
        self.db.execute("SAVEPOINT x")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-187"):
            self.rattacher(bc.b, autre)
        self.db.execute("ROLLBACK TO x")
        self.db.execute("RELEASE x")
        self.assertIsNotNone(a)

    def test_un_BC_termine_accepte_un_remboursement_et_une_annulation_de_remboursement(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        self.encaisse(so, "1000.00")
        a = self.avoir(so, "100.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")                                      # avoir partiel : BC reste termine (VR-07)
        rb = self.rembourse(a, "100.00")
        self.annuler(rb)
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")

    def test_remboursement_ou_son_annulation_ne_change_pas_le_statut_du_BC(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        self.encaisse(so, "1000.00")
        a = self.avoir(so, "100.00")
        rb = self.rembourse(a, "100.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.reste_du_bc(bc), 0)
        self.annuler(rb)
        self.assertEqual(self.reste_du_bc(bc), 0)                                             # un remboursement ne modifie jamais un reste dû

    def test_BC_annule_les_caches_financiers_evoluent_et_le_statut_reste_annule(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        e = self.encaisse(so, "1000.00")
        self.recalcul_financier(bc)
        self.etat(bc, "annule")
        self.assertEqual(self.etat_bc(bc)[0], "annule")
        self.avoir(so, "1000.00")
        self.recalcul_financier(bc)
        statut, completed, d100, avanc, nette = self.etat_bc(bc)
        self.assertEqual((statut, nette), ("annule", "0.00"))
        self.assertIsNone(d100)
        self.accepte_annul(e)

    def test_BC_annule_aucune_creation_de_facture_malgre_un_reglement(self):
        bc = self.monde(devis=[{"lignes": ["2000.00"]}])
        f = self.facture(bc, "situation", "1000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.etat(bc, "annule")
        self.encaisse(f, "1000.00")
        self.refuse_f("INV-188", bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht="1000.00")
        self.refuse_f("INV-188", bc, "solde", "1000.00")

    def test_le_BC_encore_termine_apres_annulation_sans_recalcul_refuse_toujours_l_acompte(self):
        bc, so, e = self.bc_termine(acompte=True)
        self.annuler(e)                                                                       # pas de recalcul : le BC est encore termine
        self.refuse_f("INV-58", bc, "acompte", "100.00", devis_id=bc.d[0])                   # un solde existe : 006 interdit tout acompte

    def test_un_reglement_n_a_aucun_effet_sur_les_factures_ni_leurs_lignes(self):
        bc, f = self.cible("situation", "1000.00")
        avant = (self.empreinte("factures"), self.empreinte("facture_lignes"), self.empreinte("numerotation_sequences"))
        e = self.encaisse(f, "300.00")
        self.annuler(e)
        self.encaisse(f, "1000.00")
        self.assertEqual((self.empreinte("factures"), self.empreinte("facture_lignes"), self.empreinte("numerotation_sequences")), avant)

    def test_une_facture_avec_reglement_reste_immuable_selon_006(self):
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "300.00")
        m = self.tente("UPDATE factures SET total_ht='999.00' WHERE id=?", f)
        self.assertIsNotNone(m)
        self.assertRegex(m, "INV-")


# ====================================================================================================================
# L — import (origine = 'import') : mêmes garde-fous, états historiques représentables
# ====================================================================================================================
class ImportReglements(Base10):
    """Groupe L : l'import n'est exempté d'aucun garde-fou (INV-131) ; l'ordre d'import est porté par le contrat du convertisseur (Q2)."""

    def imp(self, n, **kw):
        kw.setdefault("origine", "import")
        kw.setdefault("legacy_id", f"R{n}")
        kw.setdefault("legacy_data", '{"src":"v2","n":%d}' % n)
        return kw

    def test_un_reglement_importe_est_accepte_avec_ses_colonnes_legacy(self):
        bc, f = self.cible("situation", "1000.00")
        r = self.encaisse(f, "400.00", **self.imp(1))
        self.assertEqual(self.un("SELECT origine, legacy_id, json_valid(legacy_data) FROM reglements WHERE id=?", r), ("import", "R1", 1))

    def test_les_garde_fous_s_appliquent_a_l_import(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.refuse_r("INV-72", f, "encaissement", "0.01", **self.imp(2))
        self.refuse_r("INV-74", a, "remboursement", "100.01", **self.imp(3))
        self.refuse_r("INV-71", a, "encaissement", "1.00", **self.imp(4))
        self.refuse_r("INV-71", f, "remboursement", "1.00", **self.imp(5))
        e = self.un("SELECT id FROM reglements WHERE facture_id=?", f)[0]
        rb = self.rembourse(a, "100.00", **self.imp(6))
        self.refuse_annul("INV-75", e)
        self.refuse_inv("INV-70", "DELETE FROM reglements WHERE id=?", rb)
        self.refuse_inv("INV-70", "UPDATE reglements SET montant='1.00' WHERE id=?", rb)

    def test_Q2_l_ordre_d_import_porte_la_contrainte_encaissement_avant_avoir_est_accepte(self):
        """Historique C-06 importé dans l'ordre chronologique (encaissement 600, puis avoir 500) : accepté."""
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "600.00", **self.imp(1))
        self.avoir(f, "500.00")
        self.assertEqual(self.credit(f), 10000)
        self.assertEqual(self.ck(CK19_ENCAISSEMENTS), [])

    def test_Q2_importer_l_avoir_avant_l_encaissement_historique_est_refuse_par_le_SQL(self):
        """Limite documentée (Q2) : ce n'est PAS une règle métier ; le convertisseur doit corriger l'ordre ou déclarer le règlement non importé (P-04, §10.4)."""
        bc, f, a = self.cible_avec_avoir("1000.00", "500.00")
        self.refuse_r("INV-72", f, "encaissement", "600.00", **self.imp(1))
        self.accepte_r(f, "encaissement", "500.00", **self.imp(1))                            # la part compatible reste importable

    def test_Q1_un_reglement_historiquement_annule_est_importable_tel_quel(self):
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "1000.00", **self.imp(1))
        r = self.encaisse(f, "1000.00", cancelled_at="2026-01-02T03:04:05.000Z", motif_annulation="Annulé dans la V2", **self.imp(2))
        self.assertIsNotNone(self.un("SELECT cancelled_at FROM reglements WHERE id=?", r)[0])
        self.assertEqual(self.reste_du(f), 0)
        self.refuse_annul("INV-70", r)

    def test_historique_complet_importe_et_diagnostics_vides(self):
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "400.00", **self.imp(1))
        self.encaisse(f, "600.00", cancelled_at=TS_ANNUL, motif_annulation="Doublon", **self.imp(2))
        self.encaisse(f, "600.00", **self.imp(3))
        a = self.avoir(f, "100.00")
        self.rembourse(a, "100.00", **self.imp(4))
        self.rembourse(a, "999.00", cancelled_at=TS_ANNUL, motif_annulation="Erreur", **self.imp(5))
        for nom, sql in CK.items():
            if nom != "termine":
                with self.subTest(ck=nom):
                    self.assertEqual(self.ck(sql), [])
        self.assertEqual(self.credit(f), 0)

    def test_BLOC_IMP_origine_v6_exige_legacy_vide_et_import_accepte_legacy_nul(self):
        bc, f = self.cible("situation", "1000.00")
        self.refuse_check_r(f, "encaissement", "1.00", origine="v6", legacy_id="X")
        self.refuse_check_r(f, "encaissement", "1.00", origine="v6", legacy_data="{}")
        self.refuse_check_r(f, "encaissement", "1.00", origine="autre")
        self.refuse_check_r(f, "encaissement", "1.00", origine="import", legacy_data="pas du json")
        self.accepte_r(f, "encaissement", "1.00", origine="import")

    def test_import_en_masse_dans_une_seule_transaction_est_atomique(self):
        bc, f = self.cible("situation", "100.00")
        n = self.nb_reglements()
        self.db.execute("SAVEPOINT imp")
        self.encaisse(f, "60.00", **self.imp(1))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-72"):
            self.encaisse(f, "60.00", **self.imp(2))
        self.db.execute("ROLLBACK TO imp")
        self.db.execute("RELEASE imp")
        self.assertEqual(self.nb_reglements(), n)

    def test_un_reglement_sans_facture_importee_est_refuse_par_la_cle_etrangere(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.reglement(987654, "encaissement", "1.00", **self.imp(1))
        self.assertEqual(self.nb_reglements(), 0)

    def test_deux_reglements_importes_peuvent_porter_le_meme_legacy_id(self):
        """Aucun index unique n'est posé sur (origine, legacy_id) : cadrage §4, 007 ne numérote ni ne dédoublonne."""
        bc, f = self.cible("situation", "1000.00")
        self.encaisse(f, "1.00", origine="import", legacy_id="DUP")
        self.encaisse(f, "1.00", origine="import", legacy_id="DUP")
        self.assertEqual(self.nb_reglements(), 2)


# ====================================================================================================================
# M — diagnostics CK-18, CK-19, CK-20, CK-06 (volet termine)
# ====================================================================================================================
class Diagnostics(Base10):
    """Groupe M : les diagnostics sont vides sur un état produit par les triggers, et détectent l'état corrompu quand les triggers sont retirés."""

    def monde_riche_r(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.rembourse(a, "40.00")
        bc2, f2 = self.cible("acompte", "300.00")
        self.encaisse(f2, "300.00")
        self.annuler(self.un("SELECT id FROM reglements WHERE facture_id=?", f2)[0])
        self.encaisse(f2, "120.00")
        return (bc, f, a), (bc2, f2)

    def test_les_diagnostics_sont_vides_sur_un_etat_produit_par_les_triggers(self):
        self.monde_riche_r()
        for nom, sql in CK.items():
            with self.subTest(ck=nom):
                self.assertEqual(self.ck(sql), [])

    def test_les_diagnostics_sont_vides_sur_une_base_vide(self):
        for nom, sql in CK.items():
            with self.subTest(ck=nom):
                self.assertEqual(self.ck(sql), [])

    def test_CK18_detecte_un_encaissement_sur_un_avoir_et_un_remboursement_sur_une_facture(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.db.execute("DROP TRIGGER tr_30_reglements_cible")
        r1 = self.encaisse(a, "1.00")
        r2 = self.rembourse(f, "1.00")
        self.assertEqual(sorted(x for (x,) in self.ck(CK18_CIBLE)), sorted([r1, r2]))

    def test_CK18_ignore_les_reglements_annules_historiques_mal_cibles_n_existent_pas(self):
        """Un règlement né annulé est lui aussi contrôlé par tr_30 : CK-18 couvre TOUS les règlements, annulés compris."""
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.db.execute("DROP TRIGGER tr_30_reglements_cible")
        r = self.encaisse(a, "1.00", cancelled_at=TS_ANNUL, motif_annulation="x")
        self.assertEqual(self.ck(CK18_CIBLE), [(r,)])

    def test_CK19_detecte_un_depassement_d_encaissements(self):
        bc, f = self.cible("situation", "100.00")
        self.db.execute("DROP TRIGGER tr_31_reglements_encaissement")
        self.encaisse(f, "100.00")
        self.assertEqual(self.ck(CK19_ENCAISSEMENTS), [])
        self.encaisse(f, "0.01")
        self.assertEqual(self.ck(CK19_ENCAISSEMENTS), [(f,)])

    def test_CK19_ne_compte_pas_les_encaissements_annules(self):
        bc, f = self.cible("situation", "100.00")
        self.db.execute("DROP TRIGGER tr_31_reglements_encaissement")
        self.encaisse(f, "100.00", cancelled_at=TS_ANNUL, motif_annulation="x")
        self.encaisse(f, "100.00")
        self.assertEqual(self.ck(CK19_ENCAISSEMENTS), [])

    def test_CK20_detecte_un_remboursement_au_dela_du_credit(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        self.db.execute("DROP TRIGGER tr_31_reglements_remboursement")
        self.rembourse(a, "100.00")
        self.assertEqual(self.ck(CK20_CREDIT), [])
        self.rembourse(a, "0.01")
        self.assertEqual(self.ck(CK20_CREDIT), [(f,)])

    def test_CK20_detecte_une_annulation_d_encaissement_qui_aurait_du_etre_refusee(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        e = self.un("SELECT id FROM reglements WHERE facture_id=?", f)[0]
        self.rembourse(a, "100.00")
        self.db.execute("DROP TRIGGER tr_33_reglements_annulation")
        self.annuler(e)
        self.assertEqual(self.ck(CK20_CREDIT), [(f,)])

    def test_CK06_detecte_un_BC_termine_dont_un_reste_du_est_non_nul(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        e = self.encaisse(so, "1000.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.ck(CK06_TERMINE), [])
        self.annuler(e)
        self.assertEqual(self.ck(CK06_TERMINE), [(bc.b,)])

    def test_CK06_detecte_un_BC_en_cours_dont_tout_est_regle_avec_solde_actif(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        self.assertEqual(self.ck(CK06_TERMINE), [])
        self.encaisse(so, "1000.00")
        self.assertEqual(self.ck(CK06_TERMINE), [(bc.b,)])
        self.recalcul_financier(bc)
        self.assertEqual(self.ck(CK06_TERMINE), [])

    def test_CK06_ignore_les_BC_annules(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        self.encaisse(so, "1000.00")
        self.etat(bc, "annule")
        self.assertEqual(self.ck(CK06_TERMINE), [])

    def test_les_diagnostics_sont_en_lecture_seule(self):
        self.monde_riche_r()
        avant = self.empreinte("reglements"), self.empreinte("factures"), self.empreinte("bons_commande")
        for sql in CK.values():
            self.ck(sql)
        self.assertEqual((self.empreinte("reglements"), self.empreinte("factures"), self.empreinte("bons_commande")), avant)


# ====================================================================================================================
# N — anti-contournement SQL
# ====================================================================================================================
class Contournement(Base10):
    """Groupe N : chaque trigger est l'unique garde de son invariant (témoin : sans lui la violation passe) ; les écritures multi-lignes sont évaluées ligne par ligne."""

    def scenario_violation(self, nom):
        """Retourne une fonction qui provoque la violation protégée par le trigger `nom`."""
        if nom == "tr_30_reglements_cible":
            bc, f, a = self.cible_credit("1000.00", "100.00")
            return lambda: self.encaisse(a, "1.00")
        if nom == "tr_31_reglements_encaissement":
            bc, f = self.cible("situation", "100.00")
            return lambda: self.encaisse(f, "100.01")
        if nom == "tr_31_reglements_remboursement":
            bc, f, a = self.cible_credit("1000.00", "100.00")
            return lambda: self.rembourse(a, "100.01")
        if nom == "tr_32_reglements_update":
            bc, f = self.cible("situation", "100.00")
            r = self.encaisse(f, "10.00")
            return lambda: self.db.execute("UPDATE reglements SET montant='99.00' WHERE id=?", (r,))
        if nom == "tr_32_reglements_no_delete":
            bc, f = self.cible("situation", "100.00")
            r = self.encaisse(f, "10.00")
            return lambda: self.db.execute("DELETE FROM reglements WHERE id=?", (r,))
        if nom == "tr_33_reglements_annulation":
            bc, f, a = self.cible_credit("1000.00", "100.00")
            e = self.un("SELECT id FROM reglements WHERE facture_id=?", f)[0]
            self.rembourse(a, "100.00")
            return lambda: self.annuler(e)
        raise AssertionError(nom)

    def test_chaque_trigger_est_le_seul_garde_de_son_invariant_temoin_par_suppression(self):
        for nom in TRIGGERS_007:
            with self.subTest(trigger=nom):
                t = type(self)("test_chaque_trigger_est_le_seul_garde_de_son_invariant_temoin_par_suppression")
                t.setUp()
                violation = t.scenario_violation(nom)
                t.db.execute("SAVEPOINT v")
                with self.assertRaises(sqlite3.IntegrityError):
                    violation()
                t.db.execute("ROLLBACK TO v")
                t.db.execute(f"DROP TRIGGER {nom}")
                violation()                                                                     # sans le trigger, la violation passe : il est bien le seul garde

    def test_le_catalogue_des_triggers_007_est_exact_et_chacun_est_BEFORE(self):
        lus = {n: s for n, s in self.tous("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='reglements'")}
        self.assertEqual(sorted(lus), sorted(TRIGGERS_007))
        for nom, sql in lus.items():
            self.assertRegex(sql, r"CREATE TRIGGER \w+\s+BEFORE (INSERT|UPDATE|DELETE) ON reglements")

    def test_un_INSERT_multi_lignes_est_evalue_ligne_par_ligne_et_refuse_en_bloc(self):
        bc, f = self.cible("situation", "100.00")
        n = self.nb_reglements()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-72"):
            self.db.execute("INSERT INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '60.00', 'carte'), (?, 'encaissement', ?, '60.00', 'carte')",
                            (f, D_REF, f, D_REF))
        self.assertEqual(self.nb_reglements(), n)

    def test_un_INSERT_SELECT_est_evalue_ligne_par_ligne_et_refuse_en_bloc(self):
        bc, f = self.cible("situation", "100.00")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-72"):
            self.db.execute("INSERT INTO reglements (facture_id, type, date_evenement, montant, mode) "
                            "SELECT ?, 'encaissement', ?, '40.00', 'carte' FROM (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3)", (f, D_REF))
        self.assertEqual(self.nb_reglements(), 0)

    def test_un_INSERT_multi_lignes_dont_le_total_tient_est_accepte(self):
        bc, f = self.cible("situation", "100.00")
        self.db.execute("INSERT INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '60.00', 'carte'), (?, 'encaissement', ?, '40.00', 'carte')",
                        (f, D_REF, f, D_REF))
        self.assertEqual(self.reste_du(f), 0)

    def test_un_UPDATE_multi_lignes_d_annulation_est_evalue_ligne_par_ligne(self):
        """M=1000, avoir 500, encaissements 500 + 50 + 50 + 200 = 800 (absorbe 200, crédit 300), remboursement 100.
        Annuler 50 + 50 : crédit 200 >= 100 (accepté) ; y ajouter 200 : encaissé 500, crédit 0 < 100 (refusé en bloc, rien n'est annulé)."""
        bc, f = self.cible("situation", "1000.00")
        e1 = self.encaisse(f, "500.00")
        e2 = self.encaisse(f, "50.00")
        e3 = self.encaisse(f, "50.00")
        e4 = self.encaisse(f, "200.00")
        a = self.avoir(f, "500.00")
        self.rembourse(a, "100.00")
        self.db.execute("SAVEPOINT v")
        self.db.execute("UPDATE reglements SET cancelled_at=?, motif_annulation='lot' WHERE id IN (?, ?)", (TS_ANNUL, e2, e3))
        self.assertEqual(self.tous("SELECT count(*) FROM reglements WHERE cancelled_at IS NOT NULL"), [(2,)])
        self.db.execute("ROLLBACK TO v")
        self.db.execute("RELEASE v")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-75"):
            self.db.execute("UPDATE reglements SET cancelled_at=?, motif_annulation='lot' WHERE id IN (?, ?, ?)", (TS_ANNUL, e2, e3, e4))
        self.assertEqual(self.tous("SELECT count(*) FROM reglements WHERE cancelled_at IS NOT NULL"), [(0,)])
        self.assertIsNotNone(e1)

    def test_un_UPDATE_multi_lignes_annulant_encaissement_et_remboursement_depend_de_l_ordre_des_lignes(self):
        """Limite documentée : tr_33 évalue chaque ligne dans l'ordre de parcours. L'encaissement (id inférieur) est vu AVANT l'annulation du remboursement."""
        bc, f, a = self.cible_credit("1000.00", "100.00")
        e = self.un("SELECT id FROM reglements WHERE facture_id=?", f)[0]
        rb = self.rembourse(a, "100.00")
        self.assertLess(e, rb)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-75"):
            self.db.execute("UPDATE reglements SET cancelled_at=?, motif_annulation='lot' WHERE id IN (?, ?)", (TS_ANNUL, e, rb))
        self.annuler(rb)                                                                     # l'ordre correct : le remboursement d'abord
        self.annuler(e)
        self.assertEqual(self.tous("SELECT count(*) FROM reglements WHERE cancelled_at IS NULL"), [(0,)])

    def test_PRAGMA_ignore_check_constraints_ne_desactive_pas_les_triggers(self):
        bc, f = self.cible("situation", "100.00")
        self.db.execute("PRAGMA ignore_check_constraints=ON")
        try:
            self.refuse_r("INV-72", f, "encaissement", "100.01")
            self.refuse_r("INV-71", f, "remboursement", "1.00")
        finally:
            self.db.execute("PRAGMA ignore_check_constraints=OFF")

    def test_TEMOIN_foreign_keys_OFF_laisse_passer_une_cible_inexistante(self):
        """Témoin de D-39 : la protection FK est un réglage de connexion ; la connexion applicative doit l'activer."""
        t = type(self)("test_TEMOIN_foreign_keys_OFF_laisse_passer_une_cible_inexistante")
        t.setUp()
        t.db.execute("PRAGMA foreign_keys=OFF")
        t.reglement(424242, "encaissement", "1.00")
        self.assertEqual(t.tous("PRAGMA foreign_key_check"), [("reglements", t.un("SELECT id FROM reglements")[0], "factures", 0)])

    def test_une_ecriture_sur_une_facture_ne_contourne_pas_les_reglements(self):
        """Les règlements ne sont pas portés par factures : pas de colonne dérivée, rien à falsifier côté factures."""
        cols = {r[1] for r in self.tous("PRAGMA table_info(factures)")}
        self.assertFalse({"reste_du", "encaisse", "credit", "etat_paiement", "payee_le"} & cols)

    def test_un_trigger_007_ne_contient_aucune_ecriture(self):
        for nom in TRIGGERS_007:
            sql = self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0]
            self.assertNotRegex(sql, r"(?i)\b(INSERT|DELETE|REPLACE)\s+(INTO|FROM)\b|\bUPDATE\s+\w+\s+SET\b")
            self.assertEqual(len(re.findall(r"RAISE\(ABORT", sql)), len(re.findall(r"RAISE\(", sql)))

    def test_les_autres_tables_n_ont_pas_de_trigger_007(self):
        for tbl in ("factures", "bons_commande", "devis"):
            for (nom,) in self.tous("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?", tbl):
                self.assertNotIn("reglement", nom)

    def test_creer_un_reglement_n_exige_aucun_privilege_de_trigger_en_dehors_du_schema(self):
        """Pas de TEMP TRIGGER ni de fonction applicative : un trigger de 007 ne dépend que de fonctions SQL natives."""
        for nom in TRIGGERS_007:
            sql = self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0]
            for fonction in set(re.findall(r"\b([a-z_]+)\s*\(", sql)):
                self.assertIn(fonction.upper(), {"RAISE", "CAST", "REPLACE", "COALESCE", "SUM", "MIN", "MAX", "EXISTS", "SELECT", "IN"} | {"ABORT"}, f"{nom} utilise {fonction}")


# ====================================================================================================================
# O — atomicité / rollback
# ====================================================================================================================
class Atomicite(Base10):
    """Groupe O : un refus n'écrit rien (ni ligne, ni séquence) ; règlement et recalcul du BC se valident ou s'annulent ensemble."""

    def sequence(self):
        r = self.tous("SELECT seq FROM sqlite_sequence WHERE name='reglements'")
        return r[0][0] if r else None

    def test_un_refus_trigger_ne_laisse_ni_ligne_ni_avance_de_sequence(self):
        bc, f = self.cible("situation", "100.00")
        self.encaisse(f, "10.00")
        seq, n = self.sequence(), self.nb_reglements()
        self.refuse_r("INV-72", f, "encaissement", "100.00")
        self.assertEqual((self.sequence(), self.nb_reglements()), (seq, n))
        r = self.encaisse(f, "10.00")
        self.assertEqual(r, self.un("SELECT MAX(id) FROM reglements")[0])

    def test_un_refus_CHECK_ne_laisse_ni_ligne_ni_avance_de_sequence(self):
        bc, f = self.cible("situation", "100.00")
        self.encaisse(f, "10.00")
        seq, n = self.sequence(), self.nb_reglements()
        self.refuse_check_r(f, "encaissement", "0.00")
        self.assertEqual((self.sequence(), self.nb_reglements()), (seq, n))

    def test_un_refus_n_annule_pas_les_ecritures_precedentes_de_la_transaction(self):
        bc, f = self.cible("situation", "100.00")
        self.encaisse(f, "10.00")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-72"):
            self.encaisse(f, "100.00")
        self.assertEqual(self.nb_reglements(), 1)
        self.encaisse(f, "20.00")
        self.assertEqual(self.nb_reglements(), 2)

    def test_INSERT_OR_ROLLBACK_ne_transforme_pas_un_refus_de_trigger_en_rollback_de_transaction(self):
        """RAISE(ABORT) n'est pas modifié par la clause de conflit : seule l'instruction est annulée."""
        bc, f = self.cible("situation", "100.00")
        self.encaisse(f, "10.00")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-72"):
            self.db.execute("INSERT OR ROLLBACK INTO reglements (facture_id, type, date_evenement, montant, mode) VALUES (?, 'encaissement', ?, '100.00', 'carte')", (f, D_REF))
        self.assertEqual(self.nb_reglements(), 1)

    def test_reglement_et_recalcul_du_BC_sont_atomiques(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        self.db.execute("SAVEPOINT svc")
        self.encaisse(so, "1000.00")
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")
        self.db.execute("ROLLBACK TO svc")
        self.db.execute("RELEASE svc")
        self.assertEqual(self.nb_reglements(), 0)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")

    def test_annulation_et_retour_en_cours_sont_atomiques(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        e = self.encaisse(so, "1000.00")
        self.recalcul_financier(bc)
        avant = self.ligne_bc(bc)
        self.db.execute("SAVEPOINT svc")
        self.annuler(e)
        self.recalcul_financier(bc)
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")
        self.db.execute("ROLLBACK TO svc")
        self.db.execute("RELEASE svc")
        self.assertEqual(self.ligne_bc(bc), avant)
        self.assertIsNone(self.un("SELECT cancelled_at FROM reglements WHERE id=?", e)[0])

    def test_une_annulation_refusee_ne_change_rien(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        e = self.un("SELECT id FROM reglements WHERE facture_id=?", f)[0]
        self.rembourse(a, "100.00")
        avant = self.empreinte("reglements")
        self.refuse_annul("INV-75", e)
        self.assertEqual(self.empreinte("reglements"), avant)

    def test_un_SAVEPOINT_imbrique_restaure_exactement_l_etat(self):
        bc, f = self.cible("situation", "100.00")
        avant = self.empreinte("reglements")
        self.db.execute("SAVEPOINT a")
        e = self.encaisse(f, "40.00")
        self.db.execute("SAVEPOINT b")
        self.annuler(e)
        self.encaisse(f, "60.00")
        self.db.execute("ROLLBACK TO b")
        self.assertIsNone(self.un("SELECT cancelled_at FROM reglements WHERE id=?", e)[0])
        self.assertEqual(self.nb_reglements(), 1)
        self.db.execute("ROLLBACK TO a")
        self.db.execute("RELEASE a")
        self.assertEqual(self.empreinte("reglements"), avant)

    def test_la_migration_007_n_ecrit_aucune_ligne_et_fixe_le_rang(self):
        db = F.migrer9()
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 9)
        T.appliquer(db, RANG, SQL_007)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 10)
        self.assertEqual(db.execute("SELECT count(*) FROM reglements").fetchone()[0], 0)

    def test_rollback_complet_de_la_transaction_ne_laisse_aucun_reglement(self):
        bc, f = self.cible("situation", "100.00")
        seq0 = self.sequence()
        self.db.execute("BEGIN")
        self.encaisse(f, "10.00")
        self.encaisse(f, "20.00")
        self.db.execute("ROLLBACK")
        self.assertEqual(self.nb_reglements(), 0)
        self.assertEqual(self.sequence(), seq0)


# ====================================================================================================================
# P — valeurs limites et centimes
# ====================================================================================================================
class ValeursLimites(Base10):
    """Groupe P : bornes en centimes ; limite connue au-delà de int64 (comme 006)."""

    def test_le_plus_petit_montant_et_le_plus_petit_ecart(self):
        bc, f = self.cible("situation", "0.02")
        self.accepte_r(f, "encaissement", "0.01")
        self.encaisse(f, "0.01")
        self.encaisse(f, "0.01")
        self.refuse_r("INV-72", f, "encaissement", "0.01")

    def test_une_facture_d_un_centime(self):
        bc, f = self.cible("situation", "0.01")
        self.refuse_r("INV-72", f, "encaissement", "0.02")
        self.encaisse(f, "0.01")
        self.assertEqual(self.etat_paiement(f), "reglee")

    def test_centimes_sans_derive_cumul_de_cent_encaissements_d_un_centime(self):
        bc, f = self.cible("situation", "1.00")
        for _ in range(100):
            self.encaisse(f, "0.01")
        self.assertEqual(self.reste_du(f), 0)
        self.refuse_r("INV-72", f, "encaissement", "0.01")

    def test_cumul_de_sept_tiers_sans_erreur_d_arrondi(self):
        bc, f = self.cible("situation", "0.10")
        for _ in range(3):
            self.encaisse(f, "0.03")
        self.refuse_r("INV-72", f, "encaissement", "0.02")
        self.encaisse(f, "0.01")
        self.assertEqual(self.reste_du(f), 0)

    def test_montants_proches_de_2_puissance_53_en_centimes_restent_exacts(self):
        tot = "90071992547409.93"                                                           # 2^53 + 1 centimes
        bc, f = self.cible("situation", tot)
        self.refuse_r("INV-72", f, "encaissement", "90071992547409.94")
        self.encaisse(f, "90071992547409.92")
        self.accepte_r(f, "encaissement", "0.01")
        self.refuse_r("INV-72", f, "encaissement", "0.02")

    def test_gros_montant_realiste_en_milliards(self):
        bc, f = self.cible("situation", "12345678901.23")
        self.encaisse(f, "12345678901.22")
        self.refuse_r("INV-72", f, "encaissement", "0.02")
        self.accepte_r(f, "encaissement", "0.01")

    def test_LIMITE_CONNUE_au_dela_de_int64_en_centimes_la_conversion_sature(self):
        """9 223 372 036 854 775 807 centimes (≈ 9,2·10^16 €) : CAST(... AS INTEGER) sature au-delà. Même limite documentée que 006 ; hors usage Essentiel."""
        self.assertEqual(self.un("SELECT CAST(REPLACE('92233720368547758.07', '.', '') AS INTEGER)")[0], 9223372036854775807)
        self.assertEqual(self.un("SELECT CAST(REPLACE('92233720368547758.08', '.', '') AS INTEGER)")[0], 9223372036854775807)
        self.assertEqual(self.un("SELECT CAST(REPLACE('99999999999999999999.99', '.', '') AS INTEGER)")[0], 9223372036854775807)

    def test_un_encaissement_geant_sur_une_facture_ordinaire_est_toujours_refuse(self):
        bc, f = self.cible("situation", "1000.00")
        for m in ("92233720368547758.07", "92233720368547758.08", "99999999999999999999999.99", "999999999999999999999999999999.99"):
            with self.subTest(montant=m):
                self.refuse_r("INV-72", f, "encaissement", m)

    def test_un_montant_enorme_n_est_jamais_accepte_comme_nul_ou_negatif(self):
        bc, f = self.cible("situation", "1000.00")
        self.assertEqual(self.un("SELECT typeof(CAST(REPLACE('1.00', '.', '') AS INTEGER))")[0], "integer")
        self.refuse_check_r(f, "encaissement", "-92233720368547758.08")
        self.refuse_check_r(f, "encaissement", "0.00")

    def test_identifiants_proches_de_int64_pour_facture_id_sont_refuses_par_la_cle_etrangere(self):
        for fid in (9223372036854775807, -9223372036854775808, 0, -1):
            with self.subTest(facture_id=fid):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.reglement(fid, "encaissement", "1.00")
        self.assertEqual(self.nb_reglements(), 0)

    def test_id_explicite_maximal_puis_insertion_suivante_est_refusee_proprement(self):
        bc, f = self.cible("situation", "100.00")
        self.reglement(f, "encaissement", "1.00", id=9223372036854775807)
        with self.assertRaises(sqlite3.Error):
            self.reglement(f, "encaissement", "1.00")                                          # AUTOINCREMENT : plus d'identifiant disponible (SQLITE_FULL)
        self.assertEqual(self.nb_reglements(), 1)

    def test_montant_a_la_longueur_maximale_raisonnable(self):
        bc, f = self.cible("situation", "1000.00")
        self.refuse_r("INV-72", f, "encaissement", "1" * 5000 + ".00")                         # forme canonique valide, capacité dépassée
        self.refuse_check_r(f, "encaissement", "0." + "0" * 5000)
        self.assertIsNotNone(self.tente_r(f, "encaissement", "1" * 5000 + ".000"))               # refusé (le trigger, évalué avant les CHECK, voit déjà un dépassement)


# ====================================================================================================================
# Q — dates (format uniquement, aucune chronologie : Q3)
# ====================================================================================================================
class Dates(Base10):
    """Groupe Q : date_evenement exige une date calendaire AAAA-MM-JJ ; aucune relation chronologique n'est imposée (Q3)."""

    def test_annees_bissextiles(self):
        bc, f = self.cible("situation", "1000.00")
        for d, ok in (("2028-02-29", True), ("2024-02-29", True), ("2000-02-29", True), ("2026-02-29", False), ("1900-02-29", False), ("2100-02-29", False)):
            with self.subTest(date=d):
                (self.accepte_r if ok else self.refuse_check_r)(f, "encaissement", "1.00", date_evenement=d)

    def test_jours_et_mois_impossibles_et_formats_voisins(self):
        bc, f = self.cible("situation", "1000.00")
        for d in ("2026-04-31", "2026-06-31", "2026-13-01", "2026-00-10", "2026-01-00", "2026-1-01", "2026-01-1", "26-01-01", "2026/01/01", "20260101",
                  "2026-01-01 ", " 2026-01-01", "2026-01-01T00:00:00Z", "2026-01-01\n", "", "x", "٢٠٢٦-٠١-٠١"):
            with self.subTest(date=d):
                self.refuse_check_r(f, "encaissement", "1.00", date_evenement=d)

    def test_bornes_de_calendrier_acceptees(self):
        bc, f = self.cible("situation", "1000.00")
        for d in ("0001-01-01", "9999-12-31", "2026-01-01", "2026-12-31", "2026-10-10"):
            with self.subTest(date=d):
                self.accepte_r(f, "encaissement", "1.00", date_evenement=d)

    def test_aucune_chronologie_date_anterieure_a_la_facture_ou_a_l_avoir_ou_dans_le_futur(self):
        bc, f, a = self.cible_credit("100000.00", "100.00")
        bc2, f2 = self.cible("situation", "100000.00")
        date_f = self.un("SELECT date_emission FROM factures WHERE id=?", f)[0]
        self.assertTrue(date_f)
        f = f2
        self.accepte_r(f, "encaissement", "1.00", date_evenement="1999-01-01")
        self.accepte_r(a, "remboursement", "1.00", date_evenement="1999-01-01")
        self.accepte_r(a, "remboursement", "1.00", date_evenement="2999-12-31")
        self.accepte_r(f, "encaissement", "1.00", date_evenement="2999-12-31")

    def test_la_date_d_annulation_est_libre_vis_a_vis_de_la_date_du_reglement(self):
        bc, f = self.cible("situation", "1000.00")
        r = self.encaisse(f, "10.00", date_evenement="2026-10-10")
        self.annuler(r, quand="2000-01-01T00:00:00.000Z")
        self.assertEqual(self.un("SELECT cancelled_at FROM reglements WHERE id=?", r)[0], "2000-01-01T00:00:00.000Z")

    def test_created_at_par_defaut_est_un_horodatage_UTC_millisecondes(self):
        bc, f = self.cible("situation", "1000.00")
        r = self.encaisse(f, "10.00")
        v = self.un("SELECT created_at FROM reglements WHERE id=?", r)[0]
        self.assertRegex(v, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    def test_la_date_ne_change_ni_le_reste_du_ni_l_acceptation(self):
        for d in ("1999-01-01", "2026-10-10", "2999-12-31"):
            with self.subTest(date=d):
                bc, f = self.cible("situation", "100.00")
                self.encaisse(f, "100.00", date_evenement=d)
                self.refuse_r("INV-72", f, "encaissement", "0.01", date_evenement=d)


# ====================================================================================================================
# R — données malformées
# ====================================================================================================================
class DonneesMalformees(Base10):
    """Groupe R : une donnée malformée est toujours refusée (jamais acceptée, jamais d'exception autre qu'IntegrityError) ; les textes libres sont stockés tels quels."""

    VALEURS = (None, "", " ", "abc", "1,00", "1e2", "١.٠٠", b"1.00", 1, 1.0, 1.5, True, "0x10", "NaN", "Infinity", "-0.00", "--1.00", "1.00.00", "'; DROP TABLE reglements;--")

    def test_montant_malforme_est_refuse_sans_autre_exception(self):
        bc, f = self.cible("situation", "1000.00")
        for v in self.VALEURS:
            with self.subTest(montant=v):
                m = self.tente_r(f, "encaissement", v)
                self.assertIsNotNone(m, repr(v))
        self.assertEqual(self.nb_reglements(), 0)

    def test_montant_malforme_sur_remboursement_est_refuse(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        n = self.nb_reglements()
        for v in self.VALEURS:
            with self.subTest(montant=v):
                self.assertIsNotNone(self.tente_r(a, "remboursement", v), repr(v))
        self.assertEqual(self.nb_reglements(), n)

    def test_type_et_mode_malformes_sont_refuses(self):
        bc, f = self.cible("situation", "1000.00")
        for v in (None, "", "ENCAISSEMENT", "Encaissement", " encaissement", "encaissement ", "paiement", "remboursement\x00", 1, b"encaissement"):
            with self.subTest(type=v):
                self.assertIsNotNone(self.tente_r(f, v, "1.00"), repr(v))
        for v in (None, "", "ESPECES", "Especes", "virement ", "bitcoin", 1, b"carte"):
            with self.subTest(mode=v):
                self.assertIsNotNone(self.tente_r(f, "encaissement", "1.00", mode=v), repr(v))

    def test_facture_id_malforme_est_refuse(self):
        for v in (None, "abc", "1", 1.5, b"\x01", "", -1, 0, 10**12):
            with self.subTest(facture_id=v):
                self.assertIsNotNone(self.tente_r(v, "encaissement", "1.00"), repr(v))
        self.assertEqual(self.nb_reglements(), 0)

    def test_horodatage_et_motif_malformes_sont_refuses(self):
        bc, f = self.cible("situation", "1000.00")
        for ts in (None, "", "2026-10-10", "2026-10-10T00:00:00Z", "2026-10-10T00:00:00.000", "2026-10-10 00:00:00.000Z", 20261010, 1.5, b"2026-10-10T00:00:00.000Z"):
            with self.subTest(cancelled_at=ts):
                m = self.tente_r(f, "encaissement", "1.00", cancelled_at=ts, motif_annulation="x")
                if ts is None:
                    self.assertIsNotNone(m)                                                    # motif sans date : la paire est incohérente
                else:
                    self.assertIsNotNone(m, repr(ts))
        for motif in ("", None, b"x"):
            with self.subTest(motif=motif):
                self.assertIsNotNone(self.tente_r(f, "encaissement", "1.00", cancelled_at=TS_ANNUL, motif_annulation=motif), repr(motif))

    def test_textes_libres_stockes_verbatim_sans_validation_Q3(self):
        bc, f = self.cible("situation", "1000.00")
        textes = ("'; DROP TABLE reglements;--", "\" OR 1=1 --", "ligne1\nligne2", "é à ç € 漢字 🙂", "   ", "x" * 100000, "a\x00b", "<script>alert(1)</script>", "NULL", "")
        for t_ in textes:
            with self.subTest(texte=t_[:20]):
                r = self.encaisse(f, "0.01", reference=t_, note=t_)
                self.assertEqual(self.un("SELECT reference, note FROM reglements WHERE id=?", r), (t_, t_))
        self.assertEqual(self.tous("SELECT count(*) FROM sqlite_master WHERE name='reglements'"), [(1,)])

    def test_reference_et_note_blob_sont_refuses_et_les_nombres_sont_convertis_en_texte_par_STRICT(self):
        bc, f = self.cible("situation", "1000.00")
        self.assertIsNotNone(self.tente_r(f, "encaissement", "1.00", reference=b"x"))
        self.assertIsNotNone(self.tente_r(f, "encaissement", "1.00", note=b"x"))
        r = self.encaisse(f, "1.00", reference=12, note=1.5)
        self.assertEqual(self.un("SELECT typeof(reference), reference, typeof(note), note FROM reglements WHERE id=?", r), ("text", "12", "text", "1.5"))

    def test_LIMITE_TRANSVERSE_un_octet_NUL_apres_la_forme_canonique_traverse_les_GLOB(self):
        """Limite héritée de la convention D2 (GLOB travaille sur la chaîne C, arrêtée au premier NUL) : commune à toutes les tables 001-006, non propre à 007.
        Les triggers de 007 lisent le montant en centimes (CAST) : l'arithmétique n'est pas trompée par l'octet NUL."""
        bc, f = self.cible("situation", "1000.00")
        r = self.encaisse(f, "1.00\x00")
        self.assertEqual(self.un("SELECT length(CAST(montant AS BLOB)), length(montant) FROM reglements WHERE id=?", r), (5, 4))
        self.refuse_r("INV-72", f, "encaissement", "999.01")
        self.accepte_r(f, "encaissement", "999.00")
        self.refuse_check_r(f, "encaissement", "1.00", date_evenement="2026-10-10\x00")        # les dates sont protégées par `date(x) IS x`, la limite ne vise que les montants

    def test_colonne_inconnue_est_refusee(self):
        bc, f = self.cible("situation", "1000.00")
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute("INSERT INTO reglements (facture_id, type, date_evenement, montant, mode, banque) VALUES (?, 'encaissement', ?, '1.00', 'carte', 'x')", (f, D_REF))

    def test_legacy_data_malforme_est_refuse(self):
        bc, f = self.cible("situation", "1000.00")
        for v in ("", "{", "pas json", "[1,", "{'a':1}", b"{}"):
            with self.subTest(legacy_data=v):
                self.assertIsNotNone(self.tente_r(f, "encaissement", "1.00", origine="import", legacy_id="L", legacy_data=v), repr(v))
        for v in ("{}", "[]", "null", "1", '"x"'):
            with self.subTest(legacy_data=v):
                self.accepte_r(f, "encaissement", "1.00", origine="import", legacy_id="L", legacy_data=v)


# ====================================================================================================================
# S — fuzz déterministe contre l'oracle (formules littérales du modèle §3.3, indépendantes du SQL)
# ====================================================================================================================
class FuzzOracle(Base10):
    """Groupe S : séquences pseudo-aléatoires (graine fixe) d'encaissements, avoirs, remboursements et annulations ; l'acceptation SQL égale celle de l'oracle."""

    GRAINES = range(1000, 1140)
    OPERATIONS = 18

    def monde_fuzz(self, rnd):
        tot = rnd.choice((10000, 25050, 100000, 7))
        acomp = max(1, tot * rnd.choice((10, 25, 40)) // 100)
        bc = self.monde(devis=[{"lignes": [eur(tot)], "acompte": ("montant", eur(acomp))}])
        a = self.acompte(bc, bc.d[0], eur(acomp))
        s = None
        if tot - acomp > 0:
            s = self.facture(bc, "situation", eur(tot - acomp), situation_numero=1, montant_deja_facture_ht=eur(acomp))
        facts = [{"id": a, "M": acomp, "enc": [], "avoirs": []}]
        if s:
            facts.append({"id": s, "M": tot - acomp, "enc": [], "avoirs": []})
        return facts

    @staticmethod
    def oracle(fact):
        k = Compte(fact["M"])
        k.enc = [m for (_, m, actif) in fact["enc"] if actif]
        k.av = [av["amt"] for av in fact["avoirs"]]
        k.remb = [m for av in fact["avoirs"] for (_, m, actif) in av["remb"] if actif]
        return k

    def sequence(self, graine):
        rnd = random.Random(graine)
        facts = self.monde_fuzz(rnd)
        if rnd.random() < 0.7:                                                                  # amorce : facture payée en 1 à 3 parts, puis avoir -> crédit (C-06/C-13)
            fact = rnd.choice(facts)
            reste, parts = fact["M"], rnd.randint(1, 3)
            for i in range(parts):
                x = reste if i == parts - 1 else rnd.randint(0, reste)
                if x > 0:
                    fact["enc"].append((self.encaisse(fact["id"], eur(x)), x, True))
                    reste -= x
            x = rnd.randint(1, fact["M"])
            fact["avoirs"].append({"id": self.avoir(fact["id"], eur(x)), "amt": x, "remb": []})
        for _ in range(self.OPERATIONS):
            fact = rnd.choice(facts)
            k = self.oracle(fact)
            op = rnd.choice(("enc", "enc", "avoir", "remb", "remb", "remb", "annul_e", "annul_e", "annul_r", "ne_annule"))
            if op == "enc":
                x = rnd.choice((1, k.reste_du(), k.reste_du(), k.reste_du() + 1, rnd.randint(1, max(1, fact["M"]))))
                if x <= 0:
                    continue
                attendu = x <= k.reste_du()
                m = self.tente_r(fact["id"], "encaissement", eur(x))
                self.assertEqual(m is None, attendu, (graine, op, x, fact["M"], k.reste_du(), m))
                if attendu:
                    rid = self.encaisse(fact["id"], eur(x))
                    fact["enc"].append((rid, x, True))
            elif op == "avoir":
                libre = fact["M"] - k.somme_avoirs
                if libre <= 0:
                    continue
                x = rnd.choice((libre, rnd.randint(1, libre)))
                aid = self.avoir(fact["id"], eur(x))
                fact["avoirs"].append({"id": aid, "amt": x, "remb": []})
            elif op == "remb":
                if not fact["avoirs"]:
                    continue
                av = rnd.choice(fact["avoirs"])
                x = rnd.choice((1, k.credit(), k.credit(), k.credit() + 1, max(1, k.credit() // 2), rnd.randint(1, 5000)))
                if x <= 0:
                    continue
                attendu = x <= k.credit()
                m = self.tente_r(av["id"], "remboursement", eur(x))
                self.assertEqual(m is None, attendu, (graine, op, x, k.credit(), m))
                if attendu:
                    rid = self.rembourse(av["id"], eur(x))
                    av["remb"].append((rid, x, True))
            elif op == "annul_e":
                actifs = [(i, e) for i, e in enumerate(fact["enc"]) if e[2]]
                if not actifs:
                    continue
                i, (rid, x, _) = rnd.choice(actifs)
                reste = [m for j, (_, m, ac) in enumerate(fact["enc"]) if ac and j != i]
                k2 = self.oracle(fact)
                credit_apres = k2.somme_avoirs - k2.absorbe(sum(reste))
                attendu = credit_apres >= sum(k2.remb)
                m = self.tente_annul(rid)
                self.assertEqual(m is None, attendu, (graine, op, x, credit_apres, sum(k2.remb), m))
                if attendu:
                    self.annuler(rid)
                    fact["enc"][i] = (rid, x, False)
                else:
                    self.assertRegex(m, "INV-75")
            elif op == "annul_r":
                cand = [(av, j) for av in fact["avoirs"] for j, r in enumerate(av["remb"]) if r[2]]
                if not cand:
                    continue
                av, j = rnd.choice(cand)
                rid, x, _ = av["remb"][j]
                self.assertIsNone(self.tente_annul(rid), (graine, op))
                self.annuler(rid)
                av["remb"][j] = (rid, x, False)
            else:                                                                               # règlement né annulé : toujours accepté s'il vise le bon type de cible
                x = rnd.randint(1, 3 * fact["M"])
                self.accepte_r(fact["id"], "encaissement", eur(x), cancelled_at=TS_ANNUL, motif_annulation="historique")
                if fact["avoirs"]:
                    self.accepte_r(rnd.choice(fact["avoirs"])["id"], "remboursement", eur(x), cancelled_at=TS_ANNUL, motif_annulation="historique")
            for f_ in facts:
                kk = self.oracle(f_)
                self.assertEqual((self.reste_du(f_["id"]), self.credit(f_["id"])), (kk.reste_du(), kk.credit()), (graine, op))
        for nom in ("cible", "encaissements", "credit"):
            self.assertEqual(self.ck(CK[nom]), [], (graine, nom))

    def test_fuzz_deterministe_contre_l_oracle(self):
        for g in self.GRAINES:
            with self.subTest(graine=g):
                t = type(self)("test_fuzz_deterministe_contre_l_oracle")
                t.setUp()
                t.sequence(g)

    def test_l_oracle_est_independant_et_conforme_aux_cas_du_modele(self):
        k = Compte(100000)
        k.enc, k.av = [60000], [50000]
        self.assertEqual((k.absorbe(), k.reste_du(), k.credit()), (40000, 0, 10000))
        k = Compte(100000)
        k.enc, k.av, k.remb = [100000], [10000], [10000]
        self.assertEqual((k.absorbe(), k.reste_du(), k.credit()), (0, 0, 0))
        k = Compte(40000)
        k.av = [40000]
        self.assertEqual((k.absorbe(), k.reste_du(), k.credit()), (40000, 0, 0))


# ====================================================================================================================
# T — compléments issus de la campagne de mutation (lacunes de test réelles qualifiées une à une)
# ====================================================================================================================
class ComplementsMutation(Base10):
    """Groupe T : jetons d'énumération hors liste, annulation d'un règlement importé, défense en profondeur de tr_31/tr_33 si tr_30 est contourné."""

    # --- jetons hors liste (mutants `in_plus`) -------------------------------------------------------------------------
    def test_T49_T_un_jeton_inconnu_est_refuse_pour_type_mode_et_origine(self):
        bc, f = self.cible("situation", "1000.00")
        self.refuse_check_r(f, "zzz", "1.00")
        self.refuse_check_r(f, "encaissement", "1.00", mode="zzz")
        self.refuse_check_r(f, "encaissement", "1.00", origine="zzz")
        self.refuse_check_r(f, "encaissement", "1.00", origine="zzz", legacy_id="L")
        self.assertEqual(self.nb_reglements(), 0)

    # --- annulation d'un règlement importé : les colonnes legacy_* ne s'opposent pas à l'annulation (mutants tr_32 legacy -> cancelled_at) ----
    def importe(self, f, montant="100.00", type_="encaissement", **kw):
        return self.reglement(f, type_, montant, origine="import", legacy_id="R-42", legacy_data='{"src": "v2", "n": 42}', **kw)

    def test_T49_T_un_encaissement_importe_s_annule_et_conserve_ses_colonnes_legacy(self):
        bc, f = self.cible("situation", "1000.00")
        r = self.importe(f)
        avant = self.un("SELECT origine, legacy_id, legacy_data FROM reglements WHERE id=?", r)
        self.accepte_annul(r)
        self.annuler(r)
        self.assertEqual(self.un("SELECT origine, legacy_id, legacy_data FROM reglements WHERE id=?", r), avant)
        self.assertEqual(self.un("SELECT cancelled_at FROM reglements WHERE id=?", r)[0], TS_ANNUL)

    def test_T49_T_un_remboursement_importe_s_annule(self):
        bc, f, a = self.cible_credit("1000.00", "100.00")
        r = self.importe(a, "100.00", "remboursement")
        self.accepte_annul(r)
        self.annuler(r)
        self.assertEqual(self.credit(f), 10000)

    def test_T49_T_les_colonnes_legacy_d_un_reglement_importe_restent_figees(self):
        bc, f = self.cible("situation", "1000.00")
        r = self.importe(f)
        for col, val in (("legacy_id", "R-43"), ("legacy_id", None), ("legacy_data", '{"src": "v3"}'), ("legacy_data", None), ("origine", "v6")):
            with self.subTest(colonne=col, valeur=val):
                self.refuse_inv("INV-70", f"UPDATE reglements SET {col}=? WHERE id=?", val, r)
        self.annuler(r)
        self.refuse_inv("INV-70", "UPDATE reglements SET legacy_id='R-43' WHERE id=?", r)

    def test_T49_T_un_reglement_v6_a_legacy_nul_s_annule(self):
        bc, f = self.cible("situation", "1000.00")
        r = self.encaisse(f, "100.00")
        self.annuler(r)
        self.assertEqual(self.un("SELECT origine, legacy_id, legacy_data FROM reglements WHERE id=?", r), ("v6", None, None))

    # --- défense en profondeur : tr_30 contourné (supprimé) ne fausse ni les plafonds ni la garde d'annulation ---------------------
    def sans_tr_30(self):
        t = type(self)("test_T49_T_un_jeton_inconnu_est_refuse_pour_type_mode_et_origine")
        t.setUp()
        t.db.execute("DROP TRIGGER tr_30_reglements_cible")
        return t

    def test_T49_T_tr_31_encaissement_ne_compte_que_les_encaissements(self):
        t = self.sans_tr_30()
        bc, f = t.cible("situation", "1000.00")
        t.rembourse(f, "600.00")                                                              # remboursement parasite sur une facture hors avoir (état que tr_30 interdit)
        t.accepte_r(f, "encaissement", "1000.00")
        t.refuse_r("INV-72", f, "encaissement", "1000.01")

    def test_T49_T_tr_31_remboursement_ne_compte_que_les_encaissements_de_l_origine(self):
        t = self.sans_tr_30()
        bc, f = t.cible("situation", "1000.00")
        t.encaisse(f, "500.00")
        a = t.avoir(f, "600.00")                                                              # absorbe 500, crédit 100
        t.rembourse(f, "400.00")                                                              # parasite : ne doit pas passer pour un encaissement
        t.refuse_r("INV-74", a, "remboursement", "100.01")
        t.accepte_r(a, "remboursement", "100.00")

    def test_T49_T_tr_31_remboursement_ne_compte_que_les_remboursements(self):
        t = self.sans_tr_30()
        bc, f, a = t.cible_credit("1000.00", "100.00")
        t.encaisse(a, "60.00")                                                                # encaissement parasite sur un avoir
        t.accepte_r(a, "remboursement", "100.00")
        t.refuse_r("INV-74", a, "remboursement", "100.01")

    def test_T49_T_tr_33_ne_compte_que_les_remboursements(self):
        t = self.sans_tr_30()
        bc, f, a = t.cible_credit("1000.00", "100.00")
        e = t.un("SELECT id FROM reglements WHERE facture_id=? AND type='encaissement'", f)[0]
        t.encaisse(a, "60.00")                                                                # encaissement parasite sur l'avoir : pas un remboursement
        t.accepte_annul(e)

    def test_T49_T_tr_33_ne_compte_que_les_encaissements_de_l_origine(self):
        t = self.sans_tr_30()
        bc, f, a = t.cible_credit("1000.00", "100.00")
        e = t.un("SELECT id FROM reglements WHERE facture_id=? AND type='encaissement'", f)[0]
        t.rembourse(a, "30.00")                                                               # vrai remboursement
        t.rembourse(f, "950.00")                                                              # remboursement parasite sur la facture : pas un encaissement
        t.refuse_annul("INV-75", e)

    # --- périmètre exact de tr_33 (clause WHEN) : seule l'annulation d'un encaissement actif est évaluée -----------------------------
    def monde_protege(self):
        """M=1000, encaissements 300 (annulé) + 1000 (actif), avoir 100, remboursement 100 : crédit = Σ remboursements, toute minoration du crédit serait refusée."""
        bc, f = self.cible("situation", "1000.00")
        e0 = self.encaisse(f, "300.00")
        self.annuler(e0)
        e1 = self.encaisse(f, "1000.00")
        a = self.avoir(f, "100.00")
        rb = self.rembourse(a, "100.00")
        self.assertEqual(self.credit(f), 0)
        return f, a, e0, e1, rb

    def test_T49_T_un_UPDATE_sans_changement_d_un_encaissement_actif_n_est_pas_une_annulation(self):
        f, a, e0, e1, rb = self.monde_protege()
        avant = self.un("SELECT * FROM reglements WHERE id=?", e1)
        self.db.execute("UPDATE reglements SET note=note WHERE id=?", (e1,))
        self.db.execute("UPDATE reglements SET montant=montant, cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (e1,))
        self.assertEqual(self.un("SELECT * FROM reglements WHERE id=?", e1), avant)
        self.refuse_annul("INV-75", e1)                                                       # alors que la vraie annulation reste refusée

    def test_T49_T_tout_UPDATE_d_un_encaissement_deja_annule_est_refuse_par_l_immuabilite_INV_70(self):
        f, a, e0, e1, rb = self.monde_protege()
        self.refuse_annul("INV-70", e0, motif="Deuxième tentative")
        self.refuse_inv("INV-70", "UPDATE reglements SET montant='1.00' WHERE id=?", e0)
        self.refuse_inv("INV-70", "UPDATE reglements SET cancelled_at=NULL, motif_annulation=NULL WHERE id=?", e0)

    def test_T49_T_l_annulation_d_un_remboursement_n_est_jamais_evaluee_par_tr_33(self):
        f, a, e0, e1, rb = self.monde_protege()
        self.accepte_annul(rb)
        self.annuler(rb)
        self.assertEqual(self.credit(f), 10000)

    def test_T49_T_la_modification_d_un_remboursement_est_refusee_par_tr_32_et_pas_par_tr_33(self):
        f, a, e0, e1, rb = self.monde_protege()
        m = self.tente("UPDATE reglements SET montant='1.00' WHERE id=?", rb)
        self.assertRegex(m, "INV-70")
        self.assertNotRegex(m, "INV-75")


if __name__ == "__main__":
    unittest.main()
