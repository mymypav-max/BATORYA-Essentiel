"""T-50 — Tranche 008_garanties (rang 11) ; modèle V3.13 §2 (conventions), §2.5 (énumérations), §4.10 (garanties), §8 (TR-50), §9 (index), §10 (import),
§14 (CK-07) ; invariants INV-05, INV-06, INV-10, INV-85 à INV-90, INV-95, INV-131, INV-134, INV-174, INV-177, INV-188 ; CADRAGE__008_garanties.md (validé :
QO-1 oui = gardes G3 et G4, QO-2 oui = CHECK de durée exacte G5 y compris 29/02 -> 28/02, QO-3 non = aucune garde « premier solde » en SQL, dates extrêmes §3.6,
post-condition renforcée du service §4.1).

008 crée UNE table (garanties), ses trois index et trois triggers (tr_50 x2, tr_51). Aucun trigger de 008 ne lit ni n'écrit reglements, bons_commande ou les avoirs.
Responsabilités vérifiées ici :
  * CHECK / index / FK : liste fermée des types, dates réelles (famille D, année sur 4 chiffres), fin > début, durée exacte par type (29/02 -> 28/02), UNIQUE
    (ligne, type), NOT NULL, FK RESTRICT sans ON UPDATE, STRICT ;
  * triggers : immuabilité et non-suppression, REPLACE et UPSERT compris (tr_50) ; gardes d'insertion G1 (ligne du BC), G2 (solde du même BC), G3 (garantie de ligne
    existante, QO-1), G4 (date = date d'émission, QO-1) (tr_51) ; aucune garde « premier solde » (QO-3) ;
  * service (reproduit ici par une émulation, JAMAIS par le schéma) : mode PREMIER / REJEU, pré-contrôles avant réservation du numéro, INSERT OR IGNORE,
    post-condition C1 à C8 dans la transaction, rollback intégral, numérotation (PT-1) ; oracles indépendants des dates de fin (entiers purs et datetime) ;
  * diagnostics (requêtes en constantes SQL, lecture seule) : CK-07a (garantie manquante), CK-07b (garantie incohérente), CK-07c (non premier solde).

Réutilisation : ces tests importent test_007_reglements (qui importe test_006_facturation, test_005c puis test_005b) pour l'émulation du runner et la fabrication des
devis, BC, lignes, factures et avoirs, sans les modifier. Le rang 11 s'obtient en appliquant 008 sur la chaîne du rang 10 (BEGIN IMMEDIATE, fichier,
PRAGMA user_version = 11, COMMIT).

Exécution : python3 src-tauri/tests/metier/test_008_garanties.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T50_ suivi du groupe (A chaîne et structure, B CHECK de colonnes,
C unicité et idempotence, D durées et 29/02, E FK et suppression des parents, F tr_50, G tr_51, H scénarios métier, I import, J diagnostics, K non-régression,
L données malformées et contournements, M atomicité, N dates extrêmes, O post-condition du service et atomicité de l'émission). Les décisions d'interprétation portent
« INTERPRETATION ». Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39).
Un refus levé par un trigger se reconnaît à son préfixe « INV-nn » ; un refus levé par une contrainte (CHECK, NOT NULL, UNIQUE, FK) n'en porte aucun.
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
import test_007_reglements as R  # noqa: E402  (chaîne 001 à 007, fabrication de données, services de facturation et émulation du runner)

F = R.F
T, C = F.T, F.C
MIGRATIONS = F.MIGRATIONS
NOM_008 = "008_garanties.sql"
NOMS = R.NOMS + (NOM_008,)
SQL_008 = (MIGRATIONS / NOM_008).read_text(encoding="utf-8")
RANG = 11
TS, TS2, TS_ANNUL = T.TS, T.TS2, T.TS_ANNUL
OMIT = F.OMIT
c, eur, dl = F.c, F.eur, F.dl

INDEXES_008 = {"idx_garanties_bc_id": "bc_id", "idx_garanties_facture_declenchement_id": "facture_declenchement_id", "idx_garanties_date_fin_suivi": "date_fin_suivi"}
TRIGGERS_008 = {"tr_50_garanties_update": "garanties", "tr_50_garanties_no_delete": "garanties", "tr_51_garanties_insert": "garanties"}
COLONNES_GARANTIES = ["id", "bc_id", "bc_ligne_id", "garantie_type", "date_declenchement", "date_fin_suivi", "facture_declenchement_id", "created_at"]
TYPES_G = ("parfait_achevement", "biennale", "decennale")
DUREE = {"parfait_achevement": 1, "biennale": 2, "decennale": 10}
D_REF = "2026-10-05"                                                                          # date d'émission du solde par défaut


# --------------------------------------------------------------------------------------------------------------------
# Chaîne
# --------------------------------------------------------------------------------------------------------------------
def migrer11(recursive=True):
    """Chaîne 001 à 007 (rang 10) puis 008 comme une migration ordinaire : BEGIN IMMEDIATE, fichier, user_version = 11, COMMIT."""
    db = R.migrer10(recursive=recursive)
    T.appliquer(db, RANG, SQL_008)
    return db


def code_sql():
    return T.sans_commentaires(SQL_008)


def sql_temoin(sans_g5=True, sans_tr51=True):
    """Texte de 008 privé du CHECK de durée exacte G5 et/ou du trigger tr_51 : base « témoin » (fixture de test, hors livrable) qui laisse exister une valeur fausse
    pour prouver que la post-condition du service tient seule."""
    code = code_sql()
    if sans_g5:
        a, b = code.index("CHECK (date_fin_suivi = printf("), code.index("CHECK (created_at GLOB")
        code = code[:a] + code[b:]
    if sans_tr51:
        code = code[:code.index("CREATE TRIGGER tr_51_garanties_insert")]
    return code


# --------------------------------------------------------------------------------------------------------------------
# Oracles indépendants de la date de fin de suivi (le « service » : arithmétique civile, jamais date(x, '+N year'))
# --------------------------------------------------------------------------------------------------------------------
def bissextile(y):
    """Règle grégorienne 4 / 100 / 400, propre au test."""
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def fin_attendue(debut, type_):
    """Oracle 1 — entiers purs, sans SQLite ni datetime : 'YYYY-MM-DD' de la fin de suivi, ou None si l'année de fin dépasse 9999 (non représentable).
    29 février -> 28 février (INV-88)."""
    y, m, d = int(debut[:4]), int(debut[5:7]), int(debut[8:10])
    y2 = y + DUREE[type_]
    if (m, d) == (2, 29):
        d = 28
    return None if y2 > 9999 else "%04d-%02d-%02d" % (y2, m, d)


def fin_attendue_dt(debut, type_):
    """Oracle 2 — indépendant du premier : datetime.date (années 1 à 9999) ; repli sur le 28 février si le 29/02 n'existe pas dans l'année cible. None si non
    représentable. L'année 0000 est hors datetime : seul l'oracle 1 la vérifie."""
    y, m, d = int(debut[:4]), int(debut[5:7]), int(debut[8:10])
    try:
        return datetime.date(y + DUREE[type_], m, d).isoformat()
    except ValueError:
        if (m, d) == (2, 29) and y + DUREE[type_] <= 9999:
            return datetime.date(y + DUREE[type_], 2, 28).isoformat()
        return None


def jour_plus(date, n):
    """Date décalée de n jours ; None hors de l'intervalle de datetime (années 1 à 9999)."""
    try:
        return (datetime.date.fromisoformat(date) + datetime.timedelta(days=n)).isoformat()
    except (OverflowError, ValueError):
        return None


# --------------------------------------------------------------------------------------------------------------------
# Erreurs du service émulé
# --------------------------------------------------------------------------------------------------------------------
class DateFinSuiviHorsFormat(Exception):
    """Une date de fin de suivi n'est pas représentable (année > 9999) : détectée AVANT toute écriture et avant la réservation du numéro."""

    def __init__(self, bc, ligne, type_, debut):
        super().__init__(f"fin de suivi non representable : bc={bc} ligne={ligne} type={type_} debut={debut}")
        self.bc, self.ligne, self.type, self.debut = bc, ligne, type_, debut


class PostConditionGaranties(Exception):
    """Violation des contrôles C1 à C8 (§4.1). `phase` : 'pre' (pré-contrôle, avant réservation) ou 'post' (post-condition, avant le COMMIT)."""

    def __init__(self, violations, phase="post"):
        super().__init__(f"{phase}: {violations}")
        self.violations, self.phase = violations, phase

    @property
    def codes(self):
        return {v[0] for v in self.violations}


class DefautInjecte(Exception):
    """Défaut technique injecté par un test après une étape de l'émission (pour éprouver le rollback intégral)."""


# --------------------------------------------------------------------------------------------------------------------
# Diagnostics CK-07 (lecture seule ; chaque requête retourne les lignes en violation)
# --------------------------------------------------------------------------------------------------------------------
# CK-07a : toute paire (ligne de BC, type) de bc_ligne_garanties d'un BC ayant (ou ayant eu) un solde est présente dans garanties
CK07A_MANQUANTE = ("SELECT bl.id, bg.garantie_type FROM bc_ligne_garanties bg JOIN bc_lignes bl ON bl.id = bg.ligne_id "
                   "WHERE EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = bl.bc_id AND s.type = 'solde') "
                   "AND NOT EXISTS (SELECT 1 FROM garanties g WHERE g.bc_ligne_id = bl.id AND g.garantie_type = bg.garantie_type)")
# CK-07b : garantie incohérente
CK07B_INCOHERENTE = ("SELECT g.id FROM garanties g WHERE "
                     "NOT EXISTS (SELECT 1 FROM bc_ligne_garanties bg WHERE bg.ligne_id = g.bc_ligne_id AND bg.garantie_type = g.garantie_type) "
                     "OR NOT EXISTS (SELECT 1 FROM bc_lignes bl WHERE bl.id = g.bc_ligne_id AND bl.bc_id = g.bc_id) "
                     "OR NOT EXISTS (SELECT 1 FROM factures f WHERE f.id = g.facture_declenchement_id AND f.type = 'solde' AND f.bc_id = g.bc_id) "
                     "OR NOT EXISTS (SELECT 1 FROM factures f WHERE f.id = g.facture_declenchement_id AND f.date_emission = g.date_declenchement) "
                     "OR g.date_fin_suivi IS NOT printf('%04d', CAST(substr(g.date_declenchement, 1, 4) AS INTEGER) "
                     "+ CASE g.garantie_type WHEN 'parfait_achevement' THEN 1 WHEN 'biennale' THEN 2 ELSE 10 END) "
                     "|| CASE WHEN substr(g.date_declenchement, 6, 5) = '02-29' THEN '-02-28' ELSE substr(g.date_declenchement, 5) END "
                     "OR EXISTS (SELECT 1 FROM bons_commande b WHERE b.id = g.bc_id AND b.origine = 'import')")
# CK-07c : la facture de déclenchement n'est pas le premier solde (plus petit id) de son BC — diagnostic seul
CK07C_NON_PREMIER = ("SELECT g.id FROM garanties g WHERE g.facture_declenchement_id <> "
                     "(SELECT MIN(s.id) FROM factures s WHERE s.bc_id = g.bc_id AND s.type = 'solde')")
CK = {"manquante": CK07A_MANQUANTE, "incoherente": CK07B_INCOHERENTE, "non_premier": CK07C_NON_PREMIER}


# --------------------------------------------------------------------------------------------------------------------
# Fabrique : monde de garanties, insertions brutes, service d'émission émulé (reproduit côté test ; le schéma n'en porte aucune règle)
# --------------------------------------------------------------------------------------------------------------------
FORME_D = re.compile(r"\d{4}-\d\d-\d\d")


class Base11(R.Base10):
    """Base au rang 11. Les fabriques de devis, BC, factures et avoirs viennent de test_005b / 006 ; les garanties et le service d'émission sont reproduits ici."""

    DECALAGES = R.Base10.DECALAGES + (("garanties", 95),)

    def setUp(self):
        self.db = migrer11()
        self._n = 0
        self.desynchroniser_ids()

    @classmethod
    def _sur(cls, db):
        t = cls()
        t.db = db
        t._n = 0
        t.desynchroniser_ids()
        return t

    def isole(self, gardes):
        """Base du rang 11 dont tous les triggers sont supprimés sauf `gardes`."""
        t = self._sur(migrer11())
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def sans_triggers(self):
        return self.isole(())

    def temoin(self, **kw):
        """Base témoin : 008 privé de G5 et de tr_51 (par défaut). Les triggers 001–007 restent en place."""
        db = R.migrer10()
        T.appliquer(db, RANG, sql_temoin(**kw))
        return self._sur(db)

    # --- monde : un BC avec ses devis acceptés, leurs lignes et leurs garanties de ligne ----------------------------------
    def monde_g(self, devis=None, client_id=None, **kw):
        """BC en cours. `devis` : liste de devis, chacun liste de (montant D2, (types de garantie…)). Défaut : un devis de deux lignes,
        (decennale, biennale) et (parfait_achevement). `kw` : colonnes de bons_commande (ex. origine='import')."""
        devis = devis if devis is not None else [[("4000.00", ("decennale", "biennale")), ("2000.00", ("parfait_achevement",))]]
        cli = client_id or self.client()
        ds = []
        for i, lignes in enumerate(devis, 1):
            brut = sum(c(m) for m, _ in lignes)
            d = self.brouillon(client_id=cli, total_ht=eur(brut), acompte_type="aucun", acompte_valeur=None, remise_type="aucune")
            for k, (m, ts) in enumerate(lignes, 1):
                lid = self.ligne(d, k, designation=f"Ligne {i}.{k}", quantite="1", prix_unitaire_ht=dl(m), total_ht=m)
                for ty in ts:
                    self.garantie(lid, ty)
            self.finaliser(d)
            self.accepter(d)
            ds.append(d)
        b = self.creer_bc(ds[0], **kw)
        for d in ds[1:]:
            self.rattacher(b, d)
        bls = [[r_[0] for r_ in self.tous("SELECT bl.id FROM bc_lignes bl JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id WHERE dl.devis_id = ? ORDER BY dl.ordre", d)]
               for d in ds]
        return types.SimpleNamespace(b=b, cli=cli, d=ds, bl=bls, lignes=[x for sous in bls for x in sous])

    def attendues(self, b):
        """E : paires (ligne de BC, type) de bc_ligne_garanties des lignes du BC `b`."""
        return self.tous("SELECT l.id, g.garantie_type FROM bc_ligne_garanties g JOIN bc_lignes l ON l.id = g.ligne_id WHERE l.bc_id=? "
                         "ORDER BY l.id, g.garantie_type", b)

    def solde_g(self, bc, date=D_REF, **kw):
        """Solde émis à `date` (échéance le même jour : la chronologie n'impose rien d'autre)."""
        kw.setdefault("date_echeance", date)
        return self.solde(bc, date_emission=date, **kw)

    def eur_solde(self, f):
        """Total (D2) d'une facture."""
        return self.un("SELECT total_ht FROM factures WHERE id=?", f)[0]

    def date_de(self, f):
        return self.un("SELECT date_emission FROM factures WHERE id=?", f)[0]

    def bc_de_ligne(self, ligne):
        return self.un("SELECT bc_id FROM bc_lignes WHERE id=?", ligne)[0]

    # --- garanties brutes -------------------------------------------------------------------------------------------------
    def cols_g(self, ligne, type_, facture, **kw):
        """Colonnes d'une garantie conforme au solde `facture` ; `kw` remplace, OMIT retire."""
        date = kw["date_declenchement"] if "date_declenchement" in kw else self.date_de(facture)
        fin = fin_attendue(date, type_) if isinstance(date, str) and FORME_D.fullmatch(date) and type_ in DUREE else "2036-10-05"
        cols = {"bc_id": self.bc_de_ligne(ligne), "bc_ligne_id": ligne, "garantie_type": type_, "date_declenchement": date,
                "date_fin_suivi": fin if fin is not None else "10000-01-01", "facture_declenchement_id": facture}
        cols.update(kw)
        return {k: v for k, v in cols.items() if v is not OMIT}

    def garantie_g(self, ligne, type_, facture, verbe="INSERT", **kw):
        return self.inserer("garanties", self.cols_g(ligne, type_, facture, **kw), verbe)

    def tente_g(self, ligne, type_, facture, verbe="INSERT", **kw):
        """Insertion brute annulée juste après : None si acceptée, sinon le message d'erreur."""
        self.db.execute("SAVEPOINT tenterg")
        try:
            self.garantie_g(ligne, type_, facture, verbe, **kw)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tenterg")
            self.db.execute("RELEASE tenterg")

    def refuse_g(self, inv, ligne, type_, facture, **kw):
        m = self.tente_g(ligne, type_, facture, **kw)
        self.assertIsNotNone(m, f"garantie {type_} acceptée à tort ({kw})")
        self.assertRegex(m, inv)

    def refuse_check_g(self, ligne, type_, facture, **kw):
        m = self.tente_g(ligne, type_, facture, **kw)
        self.assertIsNotNone(m, f"garantie {type_} acceptée à tort ({kw})")
        self.assertNotIn("INV-", m)

    def accepte_g(self, ligne, type_, facture, **kw):
        m = self.tente_g(ligne, type_, facture, **kw)
        self.assertIsNone(m, m)

    def creer_toutes(self, bc, solde, **kw):
        """Insère une garantie par paire de bc_ligne_garanties, conforme au solde (création normale, en SQL direct)."""
        return [self.garantie_g(l_, t_, solde, **kw) for (l_, t_) in self.attendues(bc.b)]

    def lignes_g(self, b=None):
        """Contenu complet de garanties (tri par id), éventuellement restreint aux garanties d'un BC."""
        w, a = ("WHERE bc_id=?", (b,)) if b is not None else ("", ())
        return self.tous(f"SELECT * FROM garanties {w} ORDER BY id", *a)

    # --- périmètre, valeurs attendues et contrôles C1 à C8 (§4.1) ---------------------------------------------------------
    def perimetre(self, b):
        """P : garanties dont bc_id = b OU dont la ligne appartient à une ligne de b."""
        return self.tous("SELECT g.id, g.bc_id, g.bc_ligne_id, g.garantie_type, g.date_declenchement, g.date_fin_suivi, g.facture_declenchement_id, g.created_at "
                         "FROM garanties g WHERE g.bc_id=? OR g.bc_ligne_id IN (SELECT id FROM bc_lignes WHERE bc_id=?) ORDER BY g.id", b, b)

    def soldes_bc(self, b):
        """Soldes du BC (neutralisés ou non), du plus petit id au plus grand."""
        return [i for (i,) in self.tous("SELECT id FROM factures WHERE bc_id=? AND type='solde' ORDER BY id", b)]

    def controles(self, b, R_id, mode, inseres, avant):
        """C1 à C8 : valeurs attendues RECALCULÉES depuis le premier solde R et bc_ligne_garanties (oracle 1) — ni lues dans les garanties persistées, ni tirées
        du CHECK SQL. Retourne la liste des violations (code, détails…)."""
        D = self.date_de(R_id)
        E = {(l_, t_): fin_attendue(D, t_) for (l_, t_) in self.attendues(b)}
        P = self.perimetre(b)
        par = {}
        for g in P:
            par.setdefault((g[2], g[3]), []).append(g)
        v = []
        for k in sorted(E):
            if len(par.get(k, [])) != 1:
                v.append(("C1", k[0], k[1], len(par.get(k, []))))
        for g in P:
            gid, gbc, gl, gt, gd, gf, gfac, _ = g
            if (gl, gt) not in E:
                v.append(("C2", gid))
            if gbc != b or self.un("SELECT bc_id FROM bc_lignes WHERE id=?", gl) != (b,):
                v.append(("C3", gid))
            if gfac != R_id:
                v.append(("C4", gid))
            if gd != D:
                v.append(("C5", gid))
            if gf != E.get((gl, gt), fin_attendue(D, gt) if gt in DUREE else None):
                v.append(("C6", gid))
        if mode == "PREMIER" and inseres is not None and inseres != len(E):
            v.append(("C7", inseres, len(E)))
        if mode == "REJEU" and inseres is not None and (inseres != 0 or avant != P):
            v.append(("C7", inseres, 0))
        if mode == "PREMIER" and avant:
            v.append(("C8", len(avant)))                                                        # relevé AVANT les insertions
        return v

    # --- numérotation et empreintes ----------------------------------------------------------------------------------------
    def dernier(self, type_objet="FAC", annee=26):
        r_ = self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet=? AND annee=?", type_objet, annee)
        return r_[0] if r_ else 0

    def numerotation(self):
        return self.tous("SELECT type_objet, annee, dernier_numero FROM numerotation_sequences ORDER BY 1, 2")

    def empreinte_base(self, avec_numerotation=False):
        """Empreinte de TOUTES les tables (et de sqlite_sequence), hors numerotation_sequences par défaut."""
        h = hashlib.sha256()
        for (n,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
            if n == "numerotation_sequences" and not avec_numerotation:
                continue
            h.update(n.encode())
            h.update(repr(self.db.execute(f"SELECT * FROM {n} ORDER BY rowid").fetchall()).encode())
        seq = self.db.execute("SELECT name, seq FROM sqlite_sequence ORDER BY name").fetchall()
        if not avec_numerotation:
            seq = [x for x in seq if x[0] != "numerotation_sequences"]
        h.update(repr(seq).encode())
        return h.hexdigest()

    def releve(self, b):
        """État lisible du BC : factures, lignes de facture, garanties, caches du BC."""
        return {"factures": self.tous("SELECT id, numero, type, date_emission, total_ht FROM factures WHERE bc_id=? ORDER BY id", b),
                "lignes_facture": self.un("SELECT COUNT(*) FROM facture_lignes WHERE facture_id IN (SELECT id FROM factures WHERE bc_id=?)", b)[0],
                "garanties": self.perimetre(b),
                "bc": self.un("SELECT statut, avancement, montant_deja_facture_ht, date_100_facture, completed_at, frozen_at, updated_at FROM bons_commande WHERE id=?", b),
                "reglements": self.un("SELECT COUNT(*) FROM reglements")[0]}

    # --- service d'émission du solde (émulation de §4.1) -------------------------------------------------------------------
    def declencher(self, bc, date=D_REF, defaut=None, autre=None, precontroles=True, apres_insert=None, apres_caches=None, avant_commit=None, tenter_rejeu=False):
        """Émission d'un solde avec création des garanties dans la même transaction.
        1 pré-contrôles (avant réservation) ; 2 réservation du numéro (transaction propre, PT-1) ; 3 BEGIN IMMEDIATE, facture solde et lignes, mode et R relus ;
        4 PREMIER : C8 puis INSERT OR IGNORE par paire ; REJEU : tentative avec les valeurs de R, 0 attendu ; 5 caches du BC ; 6 post-condition C1 à C8 ; 7 COMMIT.
        `defaut(i, ligne_de_valeurs, ctx)` modifie (ou supprime : None) la i-ème insertion ; `apres_insert`, `apres_caches`, `avant_commit` : défauts injectés.
        En REJEU le service n'insère rien (`tenter_rejeu` ou `defaut` : tentative avec les valeurs de R, qui doit renvoyer 0)."""
        b = bc.b
        soldes = self.soldes_bc(b)
        if precontroles:
            R0 = soldes[0] if soldes else None
            D0 = date if R0 is None else self.date_de(R0)
            for (l_, t_) in self.attendues(b):
                if fin_attendue(D0, t_) is None:
                    raise DateFinSuiviHorsFormat(b, l_, t_, D0)
            if R0 is not None:
                v = self.controles(b, R0, "REJEU", None, None)
                if v:
                    raise PostConditionGaranties(v, "pre")
        self.db.execute("BEGIN IMMEDIATE")
        numero = self.numero("solde", date)
        self.db.execute("COMMIT")                                                                # numéro réservé : committé AVANT la transaction de l'objet
        self.db.execute("BEGIN IMMEDIATE")
        try:
            s = self.solde_g(bc, date, numero=numero)
            anciens = [x for x in self.soldes_bc(b) if x < s]
            mode = "REJEU" if anciens else "PREMIER"
            Rid = anciens[0] if anciens else s
            D = self.date_de(Rid)
            avant = self.perimetre(b)
            if mode == "PREMIER" and avant:
                raise PostConditionGaranties([("C8", len(avant))])
            ctx = types.SimpleNamespace(b=b, s=s, R=Rid, D=D, date=date, autre=autre, mode=mode, numero=numero)
            inseres = 0
            for i, (l_, t_) in enumerate(self.attendues(b) if (mode == "PREMIER" or tenter_rejeu or defaut is not None) else ()):
                row = {"bc_id": b, "bc_ligne_id": l_, "garantie_type": t_, "date_declenchement": D, "date_fin_suivi": fin_attendue(D, t_), "facture_declenchement_id": Rid}
                if defaut is not None:
                    row = defaut(i, row, ctx)
                    if row is None:
                        continue
                inseres += self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                                           "VALUES (?, ?, ?, ?, ?, ?)", (row["bc_id"], row["bc_ligne_id"], row["garantie_type"], row["date_declenchement"],
                                                                         row["date_fin_suivi"], row["facture_declenchement_id"])).rowcount
            if apres_insert:
                apres_insert(self, ctx)
            self.recalcul_financier(bc)
            if apres_caches:
                apres_caches(self, ctx)
            v = self.controles(b, Rid, mode, inseres, avant)
            if v:
                raise PostConditionGaranties(v)
            if avant_commit:
                avant_commit(self, ctx)
            self.db.execute("COMMIT")
            return types.SimpleNamespace(solde=s, mode=mode, inseres=inseres, numero=numero, R=Rid, D=D)
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def echoue(self, bc, exc, reservation, **kw):
        """L'émission échoue avec `exc` ; l'état COMPLET de la base (hors compteur de numérotation) est strictement celui d'avant. `reservation` : le compteur FAC de
        l'année a avancé d'exactement 1 (trou admis, PT-1) et AUCUNE facture ne porte le numéro réservé ; sinon le compteur de numérotation est strictement inchangé."""
        b = bc.b
        date = kw.get("date", D_REF)
        yy = int(date[2:4])
        avant, rel, ns, n0 = self.empreinte_base(), self.releve(b), self.numerotation(), self.dernier("FAC", yy)
        with self.assertRaises(exc) as cm:
            self.declencher(bc, **kw)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.empreinte_base(), avant, "l'état de la base n'est pas restauré")
        self.assertEqual(self.releve(b), rel)
        if reservation:
            self.assertEqual(self.dernier("FAC", yy), n0 + 1)
            self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE numero=?", f"FAC-{n0 + 1:05d}-{yy:02d}")[0], 0)
        else:
            self.assertEqual(self.numerotation(), ns)
        return cm.exception


class Mini(Base11):
    """Un BC à UNE ligne portant les trois garanties de ligne, et son solde émis (D_REF) : jeu de base des tests de colonnes et de gardes.
    SANS_008 : supprime ensuite les triggers de 008 (les CHECK et les FK restent) pour éprouver les contraintes seules."""

    SANS_008 = False

    def setUp(self):
        super().setUp()
        self.m = self.monde_g([[("100.00", TYPES_G)]])
        self.L = self.m.lignes[0]
        self.S = self.solde_g(self.m)
        if self.SANS_008:
            for nom in TRIGGERS_008:
                self.db.execute(f"DROP TRIGGER {nom}")

    def essai_g(self, type_="decennale", **kw):
        return self.tente_g(self.L, type_, self.S, **kw)

    def ok(self, type_="decennale", **kw):
        m = self.essai_g(type_, **kw)
        self.assertIsNone(m, m)

    def ko(self, type_="decennale", **kw):
        self.refuse_check_g(self.L, type_, self.S, **kw)


# ====================================================================================================================
# A — chaîne de migration et structure
# ====================================================================================================================
def base10_peuplee():
    """Base du rang 10 portant un BC facturé (situation, solde, avoir, encaissement) et un BC en cours : la migration 008 ne doit rien y changer."""
    t = Base11._sur(R.migrer10())
    bc = t.monde_g()
    t.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
    s = t.solde_g(bc, "2026-10-06")
    t.recalcul_financier(bc)
    t.avoir(s, "100.00")
    t.encaisse(s, "100.00")
    t.monde_g([[("300.00", ("biennale",))]])
    return t


class Chaine(Base11):
    """Groupe A : 001 → … → 007 → 008, rang 11, aucune régression de la chaîne."""

    def test_T50_A_fichiers_de_la_chaine_dans_l_ordre(self):
        self.assertEqual([p.name for p in sorted(MIGRATIONS.glob("*.sql"))[:11]], list(NOMS))
        self.assertEqual(NOMS[-1], "008_garanties.sql")
        self.assertEqual(len(NOMS), RANG)

    def test_T50_A_rang_et_user_version(self):
        db = R.migrer10()
        self.assertEqual(T.db_user_version(db), 10)
        T.appliquer(db, RANG, SQL_008)
        self.assertEqual(T.db_user_version(db), 11)
        self.assertEqual(T.db_user_version(self.db), 11)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_T50_A_le_protocole_de_reconstruction_du_runner_est_accepte(self):
        db = R.migrer10()
        T.runner(db, RANG, SQL_008)
        self.assertEqual(T.db_user_version(db), 11)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(T.objets(db), T.objets(self.db))

    def test_T50_A_le_fichier_ne_contient_que_des_creations_sans_transaction_ni_pragma_ni_donnee(self):
        code = code_sql()
        for interdit in (r"\bPRAGMA\b", r"\bCOMMIT\b", r"\bROLLBACK\b", r"\bSAVEPOINT\b", r"BEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)",
                         r"\bALTER\b", r"\bDROP\b", r"\bINSERT\s+INTO\b", r"\bUPDATE\s+\w+\s+SET\b", r"\bDELETE\s+FROM\b", r"\bREPLACE\s+INTO\b",
                         r"\bINSERT\s+OR\b", r"\bCREATE\s+(VIEW|TEMP|TEMPORARY|VIRTUAL)\b", r"\bRETURNING\b", r"\bON\s+UPDATE\b", r"\bCASCADE\b",
                         r"\bON\s+CONFLICT\b", r"\bREAL\b", r"\bFLOAT\b", r"\bDOUBLE\b", r"\bNUMERIC\b", r"\bCREATE\s+UNIQUE\b",
                         r"\breglements\b", r"\bnumerotation_sequences\b", r"\bhistorique\b", r"\bbc_devis\b", r"\bdevis\b", r"\bprestation_garanties\b"):
            self.assertIsNone(re.search(interdit, code, re.I), interdit)
        sts = [T.sans_commentaires(s).strip() for s in T.instructions(SQL_008)]
        genres = [re.match(r"CREATE\s+(UNIQUE\s+)?(TABLE|INDEX|TRIGGER)", s).group(0).split()[-1] for s in sts]
        self.assertEqual({g_: genres.count(g_) for g_ in ("TABLE", "INDEX", "TRIGGER")}, {"TABLE": 1, "INDEX": 3, "TRIGGER": 3})
        self.assertEqual(len(sts), 7)
        self.assertTrue(all(s.endswith(";") for s in sts))

    def test_T50_A_les_messages_des_triggers_sont_ASCII_et_portent_un_invariant(self):
        messages = re.findall(r"RAISE\s*\(\s*ABORT\s*,\s*'((?:[^']|'')*)'\s*\)", code_sql())
        self.assertEqual(len(messages), 6)                                                   # 1 + 1 + 4
        for m in messages:
            self.assertTrue(m.isascii(), m)
            self.assertRegex(m, r"^INV-(85|86|87|90): ")
        self.assertEqual(sorted(re.match(r"INV-(\d+)", m).group(1) for m in messages), ["85", "86", "87", "87", "87", "90"])

    def test_T50_A_objets_exacts_au_rang_11(self):
        self.assertEqual(T.noms(self.db, "table") - {"sqlite_sequence"}, F.TABLES_RANG9 | {"reglements", "garanties"})
        self.assertEqual(T.noms(self.db, "view"), set())
        nommes = {n for n in T.noms(self.db, "index") if not n.startswith("sqlite_")}
        self.assertEqual(nommes, T.INDEXES_RANG7 | F.INDEXES_006 | set(R.INDEXES_007) | set(INDEXES_008))
        triggers11 = T.noms(self.db, "trigger")
        triggers10 = T.noms(R.migrer10(), "trigger")
        self.assertEqual(triggers11 - triggers10, set(TRIGGERS_008))
        self.assertEqual(triggers10 - triggers11, set())
        for nom, table in TRIGGERS_008.items():
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], table, nom)
        for nom, col in INDEXES_008.items():
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], "garanties", nom)
            self.assertEqual([r_[2] for r_ in self.tous(f"PRAGMA index_info({nom})")], [col], nom)
            self.assertEqual(self.un("SELECT [unique] FROM pragma_index_list('garanties') WHERE name=?", nom)[0], 0, nom)

    def test_T50_A_les_objets_du_rang_10_sont_identiques_au_caractere_pres(self):
        o10 = {(t, n, tb): s for t, n, tb, s in T.objets(R.migrer10())}
        o11 = {(t, n, tb): s for t, n, tb, s in T.objets(self.db)}
        self.assertEqual(set(o11) - set(o10), {("table", "garanties", "garanties")} | {("index", n, "garanties") for n in INDEXES_008}
                         | {("trigger", n, t) for n, t in TRIGGERS_008.items()})
        self.assertEqual(set(o10) - set(o11), set())
        for cle, sql in o10.items():
            self.assertEqual(o11[cle], sql, cle)

    def test_T50_A_aucune_donnee_n_est_modifiee_par_la_migration(self):
        t10 = base10_peuplee()
        avant = T.tout(t10.db)
        self.assertTrue(avant["factures"] and avant["bons_commande"] and avant["bc_ligne_garanties"] and avant["reglements"])
        T.appliquer(t10.db, RANG, SQL_008)
        apres = T.tout(t10.db)
        self.assertEqual(apres.pop("garanties"), [])
        self.assertEqual(apres, avant)                                                       # y compris sqlite_sequence : rien pour la nouvelle table
        self.assertEqual(T.db_user_version(t10.db), 11)
        self.assertEqual(t10.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(t10.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_T50_A_schema_identique_base_fraiche_et_base_migree_peuplee(self):
        t = base10_peuplee()
        T.appliquer(t.db, RANG, SQL_008)
        self.assertEqual(T.objets(t.db), T.objets(self.db))

    def test_T50_A_atomicite_un_echec_n_importe_ou_annule_tout(self):
        points = ["CREATE TABLE garanties (", "CREATE INDEX idx_garanties_bc_id", "CREATE INDEX idx_garanties_facture_declenchement_id",
                  "CREATE INDEX idx_garanties_date_fin_suivi", "CREATE TRIGGER tr_50_garanties_update", "CREATE TRIGGER tr_50_garanties_no_delete",
                  "CREATE TRIGGER tr_51_garanties_insert"]
        db0 = R.migrer10()
        avant = T.objets(db0)
        for point in points:
            with self.subTest(point=point):
                self.assertEqual(SQL_008.count(point), 1, point)
                coupe = SQL_008.replace(point, "SELECT * FROM table_qui_n_existe_pas;\n" + point, 1)
                db = R.migrer10()
                with self.assertRaises(sqlite3.Error):
                    T.runner(db, RANG, coupe)
                self.assertFalse(db.in_transaction)
                self.assertEqual(T.db_user_version(db), 10)
                self.assertEqual(T.objets(db), avant)
        with self.subTest(point="apres la derniere instruction"):
            db = R.migrer10()
            with self.assertRaises(sqlite3.Error):
                T.runner(db, RANG, SQL_008 + "\nSELECT * FROM table_qui_n_existe_pas;\n")
            self.assertEqual(T.db_user_version(db), 10)
            self.assertEqual(T.objets(db), avant)

    def test_T50_A_rejeu_sur_une_base_deja_au_rang_11_est_refuse_sans_effet(self):
        avant = T.objets(self.db)
        with self.assertRaises(sqlite3.Error):
            T.runner(self.db, RANG, SQL_008)
        self.assertEqual(T.objets(self.db), avant)
        self.assertEqual(T.db_user_version(self.db), 11)

    def test_T50_A_table_stricte_et_colonnes_exactes(self):
        self.assertEqual(self.un("SELECT strict FROM pragma_table_list WHERE name='garanties'")[0], 1)
        cols = self.tous("PRAGMA table_info(garanties)")
        self.assertEqual([x[1] for x in cols], COLONNES_GARANTIES)
        self.assertEqual({x[1]: x[2] for x in cols}, {"id": "INTEGER", "bc_id": "INTEGER", "bc_ligne_id": "INTEGER", "garantie_type": "TEXT", "date_declenchement": "TEXT",
                                                    "date_fin_suivi": "TEXT", "facture_declenchement_id": "INTEGER", "created_at": "TEXT"})
        self.assertEqual({x[1] for x in cols if x[3]}, {"bc_id", "bc_ligne_id", "garantie_type", "date_declenchement", "date_fin_suivi", "facture_declenchement_id", "created_at"})
        self.assertEqual([x[1] for x in cols if x[5]], ["id"])
        defauts = {x[1]: x[4] for x in cols if x[4] is not None}
        self.assertEqual(set(defauts), {"created_at"})
        self.assertIn("strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", defauts["created_at"])
        self.assertIn("AUTOINCREMENT", self.un("SELECT sql FROM sqlite_master WHERE name='garanties'")[0])

    def test_T50_A_aucune_colonne_statut_ni_derivee_ni_numero_ni_bloc_imp(self):
        cols = {x[1] for x in self.tous("PRAGMA table_info(garanties)")}
        for absente in ("statut", "etat", "active", "actif", "a_surveiller", "echue", "numero", "updated_at", "origine", "legacy_id", "legacy_data", "legacy_numero",
                        "prestation_id", "designation", "reference_prestation", "client_id", "motif", "cancelled_at", "frozen_at", "duree", "annees"):
            self.assertNotIn(absente, cols)

    def test_T50_A_trois_cles_etrangeres_en_restrict_sans_on_update(self):
        fk = {r_[3]: (r_[2], r_[4], r_[5], r_[6]) for r_ in self.tous("PRAGMA foreign_key_list(garanties)")}
        self.assertEqual(fk, {"bc_id": ("bons_commande", "id", "NO ACTION", "RESTRICT"), "bc_ligne_id": ("bc_lignes", "id", "NO ACTION", "RESTRICT"),
                              "facture_declenchement_id": ("factures", "id", "NO ACTION", "RESTRICT")})

    def test_T50_A_index_exacts_unicite_et_aucun_index_redondant(self):
        liste = self.tous("SELECT name, [unique], origin FROM pragma_index_list('garanties') ORDER BY name")
        self.assertEqual({n for n, _, _ in liste}, set(INDEXES_008) | {"sqlite_autoindex_garanties_1"})
        self.assertEqual([(n, u, o) for n, u, o in liste if u], [("sqlite_autoindex_garanties_1", 1, "u")])
        self.assertEqual([r_[2] for r_ in self.tous("PRAGMA index_info(sqlite_autoindex_garanties_1)")], ["bc_ligne_id", "garantie_type"])
        for nom in INDEXES_008:
            self.assertEqual(len(self.tous(f"PRAGMA index_info({nom})")), 1, nom)
        plan = " ".join(str(r_) for r_ in self.tous("EXPLAIN QUERY PLAN SELECT * FROM garanties WHERE bc_ligne_id = 1"))
        self.assertIn("sqlite_autoindex_garanties_1", plan)                                  # Z-5 : l'index de UNIQUE couvre la FK bc_ligne_id

    def test_T50_A_chaque_cle_etrangere_est_couverte_par_un_index_de_tete(self):
        tetes = {self.tous(f"PRAGMA index_info({n})")[0][2] for (n,) in self.tous("SELECT name FROM pragma_index_list('garanties')")}
        self.assertEqual(tetes, {"bc_id", "facture_declenchement_id", "date_fin_suivi", "bc_ligne_id"})

    def test_T50_A_les_triggers_de_008_sont_before_et_ne_font_que_garder(self):
        for nom in TRIGGERS_008:
            sql = self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0]
            self.assertRegex(sql, r"CREATE TRIGGER \w+\s+BEFORE (INSERT|UPDATE|DELETE) ON garanties", nom)
            corps = sql[sql.index("BEGIN"):]
            for interdit in (r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bREPLACE\b", r"\bDROP\b"):
                self.assertIsNone(re.search(interdit, corps, re.I), (nom, interdit))
            self.assertTrue(all(re.match(r"\s*(SELECT RAISE|--)", frag) or not frag.strip() for frag in re.split(r";", T.sans_commentaires(corps).split("BEGIN", 1)[1].rsplit("END", 1)[0])), nom)

    def test_T50_A_noms_des_triggers_au_format_des_tranches_precedentes(self):
        for nom in TRIGGERS_008:
            self.assertRegex(nom, r"^tr_\d{2}_\w+$")
        self.assertEqual({n[:5] for n in TRIGGERS_008}, {"tr_50", "tr_51"})

    def test_T50_A_aucune_sequence_de_numerotation_pour_les_garanties(self):
        self.assertEqual(self.un("SELECT count(*) FROM numerotation_sequences")[0], 0)
        self.refuse_check("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('GAR', 26, 1)")
        self.assertNotIn("numerotation_sequences", code_sql())

    def test_T50_A_aucune_ligne_inseree_et_pas_de_sequence_avant_la_premiere_garantie(self):
        db = migrer11()                                                                      # base fraîche : aucune désynchronisation d'identifiants
        self.assertEqual(db.execute("SELECT count(*) FROM garanties").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT * FROM sqlite_sequence WHERE name='garanties'").fetchall(), [])

    def test_T50_A_les_ids_croissent_et_les_identifiants_des_tables_sont_distincts(self):
        m = self.monde_g([[("100.00", ("decennale", "biennale"))]])
        s = self.solde_g(m)
        g1 = self.garantie_g(m.lignes[0], "decennale", s)
        g2 = self.garantie_g(m.lignes[0], "biennale", s)
        self.assertEqual((g1, g2), (96, 97))                                                 # AUTOINCREMENT désynchronisé à 95
        self.assertEqual(len({m.b, m.lignes[0], s, g1}), 4)

    def test_T50_A_les_requetes_de_suivi_utilisent_les_index_prevus(self):
        """Chaque index se justifie par une requête : parent BC, solde déclencheur, échéances de suivi ; la ligne de BC est servie par l'index automatique du UNIQUE."""
        for sql, idx in (("SELECT * FROM garanties WHERE bc_id = 1", "idx_garanties_bc_id"),
                         ("SELECT * FROM garanties WHERE facture_declenchement_id = 1", "idx_garanties_facture_declenchement_id"),
                         ("SELECT * FROM garanties WHERE date_fin_suivi <= '2030-01-01'", "idx_garanties_date_fin_suivi"),
                         ("SELECT * FROM garanties WHERE bc_ligne_id = 1", "sqlite_autoindex_garanties_1"),
                         ("SELECT * FROM garanties WHERE bc_ligne_id = 1 AND garantie_type = 'decennale'", "sqlite_autoindex_garanties_1")):
            with self.subTest(requete=sql):
                plan = " | ".join(r_[3] for r_ in self.db.execute("EXPLAIN QUERY PLAN " + sql))
                self.assertIn(idx, plan)

    def test_T50_A_la_connexion_de_test_a_les_reglages_de_D_39(self):
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)


# ====================================================================================================================
# B — CHECK de colonnes (sans les triggers de 008 : seules les contraintes sont éprouvées)
# ====================================================================================================================
class CheckGaranties(Mini):
    """Groupe B : chaque terme d'un CHECK est arrêté par au moins un jeu de valeurs ; chaque valeur valide est acceptée. Les parents (BC, ligne, solde) sont réels."""

    SANS_008 = True

    def test_T50_B_ligne_minimale_valide_et_valeurs_par_defaut(self):
        g_ = self.garantie_g(self.L, "decennale", self.S)
        ligne = dict(zip(COLONNES_GARANTIES, self.un("SELECT * FROM garanties WHERE id=?", g_)))
        self.assertEqual({k: ligne[k] for k in ligne if k not in ("created_at", "id")},
                         {"bc_id": self.m.b, "bc_ligne_id": self.L, "garantie_type": "decennale", "date_declenchement": D_REF, "date_fin_suivi": "2036-10-05",
                          "facture_declenchement_id": self.S})
        self.assertRegex(ligne["created_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_T50_B_les_trois_types_sont_acceptes_et_aucun_autre(self):
        for t_ in TYPES_G:
            with self.subTest(type=t_):
                self.ok(t_)
        for t_ in ("Decennale", "DECENNALE", "decennale ", " decennale", "decennal", "parfait_achevement2", "parfait achevement", "biennal", "triennale", "garantie", "",
                   "décennale", "decennale\n", "1", "annuelle"):
            with self.subTest(type=t_):
                self.ko(t_, date_fin_suivi="2036-10-05")

    def test_T50_B_type_null_refuse(self):
        self.refuse_check_g(self.L, "decennale", self.S, garantie_type=None)

    def test_T50_B_created_at_par_defaut_est_l_horodatage_UTC_courant(self):
        """Le DEFAULT produit l'heure UTC courante (mois, jour, heure justes), pas seulement une chaîne de la bonne forme."""
        avant = datetime.datetime.now(datetime.timezone.utc)
        g_ = self.garantie_g(self.L, "decennale", self.S)
        apres = datetime.datetime.now(datetime.timezone.utc)
        t_ = datetime.datetime.strptime(self.un("SELECT created_at FROM garanties WHERE id=?", g_)[0], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)
        self.assertLessEqual(avant - datetime.timedelta(seconds=1), t_)
        self.assertLessEqual(t_, apres + datetime.timedelta(seconds=1))

    def test_T50_B_la_valeur_now_est_un_refus_de_contrainte_jamais_une_erreur_d_evaluation_de_date(self):
        """date('now') est non déterministe : évaluée dans un CHECK elle lèverait une OperationalError (que INSERT OR IGNORE n'ignore PAS) au lieu d'un refus de contrainte.
        Le GLOB, placé avant date(x) dans la conjonction, l'écarte : INSERT simple -> IntegrityError sans INV ; INSERT OR IGNORE -> 0 ligne et aucune erreur."""
        for v in ("now", "NOW", "Now"):
            for col in ("date_declenchement", "date_fin_suivi"):
                with self.subTest(colonne=col, valeur=v):
                    self.ko(**{col: v})
                    cols = self.cols_g(self.L, "decennale", self.S, **{col: v})
                    self.db.execute("SAVEPOINT now_")
                    cur = self.db.execute("INSERT OR IGNORE INTO garanties (%s) VALUES (%s)" % (", ".join(cols), ", ".join("?" * len(cols))), tuple(cols.values()))
                    self.assertEqual(cur.rowcount, 0)
                    self.db.execute("ROLLBACK TO now_")
                    self.db.execute("RELEASE now_")

    def test_T50_B_un_jeton_de_type_inconnu_est_refuse_meme_avec_la_duree_de_la_decennale(self):
        """La branche ELSE (+10 ans) du CHECK de durée accepterait n'importe quel jeton : la liste fermée IN (...) est la SEULE garde du type. Chaque jeton inconnu est
        refusé avec chacune des trois durées, y compris la valeur exacte de la branche ELSE."""
        for t_ in ("zzz", "xxx", "x", "autre", "dommage_ouvrage", "decennale2", "parfait", "10", "0", "null", "NULL", "true", "garantie_decennale"):
            for fin in ("2027-10-05", "2028-10-05", "2036-10-05"):
                with self.subTest(type=t_, fin=fin):
                    self.ko(t_, date_fin_suivi=fin)

    def test_T50_B_temoin_sans_liste_fermee_la_formule_de_duree_seule_accepterait_un_jeton_inconnu(self):
        """Témoin : table de balayage privée de CHECK (garantie_type IN ...) -> 'zzz' avec +10 ans est accepté par la formule seule (ELSE 10)."""
        ddl = ddl_balayage(self.un("SELECT sql FROM sqlite_master WHERE type='table' AND name='garanties'")[0])
        sans_liste = ddl.replace("CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale'))", "")
        self.assertNotEqual(sans_liste, ddl)
        for texte, attendu in ((ddl, 0), (sans_liste, 1)):
            mem = sqlite3.connect(":memory:")
            mem.execute(texte)
            mem.execute("INSERT OR IGNORE INTO bal (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                        "VALUES (1, 1, 'zzz', '2026-10-05', '2036-10-05', 1)")
            self.assertEqual(mem.execute("SELECT COUNT(*) FROM bal").fetchone()[0], attendu)
            mem.close()

    def test_T50_B_dates_reelles_au_format_aaaa_mm_jj(self):
        for d_ in ("2026-10-05", "2028-02-29", "2000-02-29", "2026-12-31", "2026-01-01", "0001-01-01", "0000-01-01", "2026-02-28", "1999-12-31"):
            with self.subTest(date=d_):
                self.ok(date_declenchement=d_, date_fin_suivi=fin_attendue(d_, "decennale"))
        for d_ in F_DATES_INVALIDES:
            with self.subTest(date=d_):
                self.ko(date_declenchement=d_, date_fin_suivi="2036-10-05")

    def test_T50_B_date_de_fin_reelle_au_format_aaaa_mm_jj(self):
        for d_ in F_DATES_INVALIDES:
            with self.subTest(date=d_):
                self.ko(date_fin_suivi=d_)
        with self.subTest("valide"):
            self.ok(date_fin_suivi="2036-10-05")

    def test_T50_B_fin_strictement_posterieure_au_declenchement(self):
        # CHECK « fin > début » : isolé en regard de la durée exacte (G5) par la base témoin (sans G5)
        t = self.temoin()                                                                    # sans G5 ni tr_51 : seul « fin > début » reste à éprouver
        m = t.monde_g([[("100.00", TYPES_G)]])
        s = t.solde_g(m)
        for fin, ok in (("2026-10-05", False), ("2026-10-04", False), ("2025-10-05", False), ("2026-10-06", True), ("2027-10-05", True), ("2036-10-05", True)):
            with self.subTest(fin=fin):
                m_ = t.tente_g(m.lignes[0], "decennale", s, date_fin_suivi=fin)
                if ok:
                    self.assertIsNone(m_, m_)
                else:
                    self.assertIsNotNone(m_)
                    self.assertNotIn("INV-", m_)

    def test_T50_B_created_at_horodatage_canonique(self):
        for v in ("2026-10-10T08:00:00.000Z", "2099-01-01T00:00:00.000Z", "2026-02-28T23:59:59.999Z"):
            with self.subTest(created_at=v):
                self.ok(created_at=v)
        for v in ("2026-10-10", "2026-10-10T08:00:00Z", "2026-10-10 08:00:00.000Z", "2026-10-10T08:00:00.000", "2026-10-10T08:00:00.00Z", "2026-10-10T08:00:00.0000Z",
                  "26-10-10T08:00:00.000Z", "2026-10-10T8:00:00.000Z", "2026-10-10T08:00:00.000Z ", " 2026-10-10T08:00:00.000Z", "abc", ""):
            with self.subTest(created_at=v):
                self.ko(created_at=v)
        with self.subTest("null"):
            self.ko(created_at=None)

    def test_T50_B_created_at_prend_une_valeur_par_defaut_valide(self):
        g_ = self.garantie_g(self.L, "decennale", self.S, created_at=OMIT)
        self.assertRegex(self.un("SELECT created_at FROM garanties WHERE id=?", g_)[0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")

    def test_T50_B_colonnes_obligatoires_not_null(self):
        for col in ("bc_id", "bc_ligne_id", "garantie_type", "date_declenchement", "date_fin_suivi", "facture_declenchement_id"):
            with self.subTest(col=col):
                self.ko(**{col: None})
                self.ko(**{col: OMIT})

    def test_T50_B_une_garantie_est_toujours_rattachee_a_un_BC_une_ligne_et_une_facture_sans_exception(self):
        """INV-90, INV-134 : aucune garantie « non native » à clés nulles."""
        for col in ("bc_id", "bc_ligne_id", "facture_declenchement_id"):
            with self.subTest(col=col):
                self.ko(**{col: None})

    def test_T50_B_les_cles_etrangeres_inexistantes_sont_refusees(self):
        for col, v in (("bc_id", 999999), ("bc_ligne_id", 999999), ("facture_declenchement_id", 999999), ("bc_id", 0), ("bc_ligne_id", -1)):
            with self.subTest(col=col, valeur=v):
                self.ko(**{col: v})

    def test_T50_B_la_table_est_stricte_une_valeur_de_mauvais_type_est_refusee(self):
        for col, v in (("garantie_type", 5), ("date_declenchement", 20261005), ("date_fin_suivi", 20361005), ("created_at", 1.5), ("bc_id", "x"), ("bc_ligne_id", "abc"),
                       ("facture_declenchement_id", 1.5), ("date_declenchement", b"2026-10-05"), ("garantie_type", b"decennale")):
            with self.subTest(col=col, valeur=v):
                self.ko(**{col: v})

    def test_T50_B_pas_de_bloc_imp_ni_colonne_statut_a_renseigner(self):
        for col in ("origine", "legacy_id", "legacy_data", "statut", "updated_at", "numero"):
            with self.subTest(col=col):
                with self.assertRaisesRegex(sqlite3.OperationalError, r"no column named|has no column"):
                    self.essai_g(**{col: "x"})

    def test_T50_B_id_explicite_accepte_puis_unique(self):
        self.ok(id=5000)
        g_ = self.garantie_g(self.L, "decennale", self.S, id=5001)
        self.assertEqual(g_, 5001)
        self.refuse_check_g(self.L, "biennale", self.S, id=5001)                                # PRIMARY KEY


F_DATES_INVALIDES = ("2026-02-29", "2100-02-29", "2026-13-01", "2026-00-10", "2026-04-31", "2026-06-31", "2026-10-32", "2026-10-00", "-0001-01-01", "2026-1-1",
                     "26-10-10", "2026/10/10", "20261010", "2026-10-10 ", " 2026-10-10", "2026-10-10\n", "2026-10-10T00:00:00Z", "2026-10-10T", "٢٠٢٦-١٠-١٠",
                     "10-10-2026", "2026-10-1", "2026-1-10", "", "abcd-ef-gh", "2026-10-10x", "x2026-10-10", "2026-W41-1", "2026-284", "10000-01-01", "2026-10-10 00:00", "now", "NOW", "Now")


# ====================================================================================================================
# C — unicité et idempotence (INSERT OR IGNORE, rejeu au solde suivant : QO-3)
# ====================================================================================================================
class Unicite(Base11):
    """Groupe C : UNIQUE (ligne, type), rejeu idempotent sans erreur, première date conservée, aucune garde « premier solde » (QO-3)."""

    def setUp(self):
        super().setUp()
        self.m = self.monde_g([[("100.00", ("decennale", "biennale")), ("50.00", ("decennale",))]])
        self.L1, self.L2 = self.m.lignes
        self.S1 = self.solde_g(self.m, "2026-10-05")

    def second_solde(self, date="2026-10-20"):
        """Nouveau solde après avoir total sur le premier (T-14) : le BC repasse en_cours (recalcul dérivé)."""
        self.avoir(self.S1)
        self.recalcul_financier(self.m)
        return self.solde_g(self.m, date)

    def test_T50_C_un_doublon_ligne_type_est_refuse_par_la_contrainte_unique(self):
        self.garantie_g(self.L1, "decennale", self.S1)
        self.refuse_check_g(self.L1, "decennale", self.S1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 1)

    def test_T50_C_le_meme_type_sur_deux_lignes_et_deux_types_sur_une_ligne_sont_acceptes(self):
        self.garantie_g(self.L1, "decennale", self.S1)
        self.garantie_g(self.L2, "decennale", self.S1)
        self.garantie_g(self.L1, "biennale", self.S1)
        self.assertEqual(self.tous("SELECT bc_ligne_id, garantie_type FROM garanties ORDER BY id"),
                         [(self.L1, "decennale"), (self.L2, "decennale"), (self.L1, "biennale")])

    def test_T50_C_insert_or_ignore_rejoue_ne_cree_aucune_ligne_et_conserve_la_premiere_date(self):
        self.garantie_g(self.L1, "decennale", self.S1)
        avant = self.lignes_g()
        n = self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                            "VALUES (?, ?, 'decennale', '2026-10-05', '2036-10-05', ?)", (self.m.b, self.L1, self.S1)).rowcount
        self.assertEqual(n, 0)
        self.assertEqual(self.lignes_g(), avant)

    def test_T50_C_QO3_le_rejeu_au_second_solde_est_idempotent_sans_erreur_et_sans_garde_premier_solde(self):
        """Date et facture de déclenchement DIFFÉRENTES (second solde) : les gardes G1 à G4 sont satisfaites, l'unicité ignore la ligne : 0 ligne, aucune erreur."""
        for (l_, t_) in self.attendues(self.m.b):
            self.garantie_g(l_, t_, self.S1)
        avant = self.lignes_g()
        s2 = self.second_solde("2026-10-20")
        for (l_, t_) in self.attendues(self.m.b):
            n = self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                                "VALUES (?, ?, ?, '2026-10-20', ?, ?)", (self.m.b, l_, t_, fin_attendue("2026-10-20", t_), s2)).rowcount
            self.assertEqual(n, 0)
        self.assertEqual(self.lignes_g(), avant)
        self.assertEqual({r_[4] for r_ in self.lignes_g()}, {"2026-10-05"})

    def test_T50_C_un_rejeu_partiel_ne_cree_que_les_garanties_manquantes(self):
        self.garantie_g(self.L1, "decennale", self.S1)
        premiere = self.lignes_g()
        total = 0
        for (l_, t_) in self.attendues(self.m.b):
            total += self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                                     "VALUES (?, ?, ?, '2026-10-05', ?, ?)", (self.m.b, l_, t_, fin_attendue("2026-10-05", t_), self.S1)).rowcount
        self.assertEqual(total, 2)
        self.assertEqual(self.lignes_g()[0], premiere[0])
        self.assertEqual(len(self.lignes_g()), 3)

    def test_T50_C_INV_87_un_rejeu_dont_une_garde_est_fausse_n_est_pas_ignore_mais_refuse(self):
        """Un trigger BEFORE s'exécute avant la détection du doublon : INSERT OR IGNORE d'une ligne déjà présente mais de date fausse = ABORT, pas 0 ligne.
        C'est la raison pour laquelle une garde « premier solde » en SQL (G6) a été abandonnée (QO-3 : NON)."""
        self.garantie_g(self.L1, "decennale", self.S1)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                            "VALUES (?, ?, 'decennale', '2026-10-06', '2036-10-06', ?)", (self.m.b, self.L1, self.S1))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-86"):
            self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                            "VALUES (?, ?, 'parfait_achevement', '2026-10-05', '2027-10-05', ?)", (self.m.b, self.L1, self.S1))

    def test_T50_C_UPSERT_do_update_est_refuse(self):
        self.garantie_g(self.L1, "decennale", self.S1)
        avant = self.lignes_g()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute("INSERT INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                            "VALUES (?, ?, 'decennale', '2026-10-05', '2036-10-05', ?) ON CONFLICT (bc_ligne_id, garantie_type) DO UPDATE SET date_fin_suivi = excluded.date_fin_suivi",
                            (self.m.b, self.L1, self.S1))
        self.assertEqual(self.lignes_g(), avant)

    def test_T50_C_UPSERT_do_nothing_est_equivalent_a_ignore(self):
        self.garantie_g(self.L1, "decennale", self.S1)
        avant = self.lignes_g()
        n = self.db.execute("INSERT INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                            "VALUES (?, ?, 'decennale', '2026-10-05', '2036-10-05', ?) ON CONFLICT DO NOTHING", (self.m.b, self.L1, self.S1)).rowcount
        self.assertEqual(n, 0)
        self.assertEqual(self.lignes_g(), avant)

    def test_T50_C_insert_or_replace_est_refuse(self):
        self.garantie_g(self.L1, "decennale", self.S1)
        avant = self.lignes_g()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.garantie_g(self.L1, "decennale", self.S1, verbe="INSERT OR REPLACE")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute("REPLACE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                            "VALUES (?, ?, 'decennale', '2026-10-05', '2036-10-05', ?)", (self.m.b, self.L1, self.S1))
        self.assertEqual(self.lignes_g(), avant)

    def test_T50_C_temoin_recursive_triggers_off_le_replace_echappe_au_trigger_de_suppression(self):
        """Limite assumée (D-39) : avec recursive_triggers=OFF, le DELETE implicite d'un REPLACE n'est pas gardé (réglage de connexion obligatoire = ON)."""
        t = Base11._sur(migrer11(recursive=False))
        m = t.monde_g([[("100.00", ("decennale",))]])
        s = t.solde_g(m)
        g_ = t.garantie_g(m.lignes[0], "decennale", s)
        g2 = t.garantie_g(m.lignes[0], "decennale", s, verbe="INSERT OR REPLACE")
        self.assertNotEqual(g_, g2)
        self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], 1)
        ligne = Base11._sur(migrer11(recursive=True))
        self.assertEqual(ligne.un("PRAGMA recursive_triggers")[0], 1)

    def test_T50_C_un_ignore_ne_cree_aucune_ligne_mais_peut_consommer_un_id_de_la_sequence(self):
        """Propriété de SQLite (AUTOINCREMENT) : l'id est alloué avant la détection du doublon ; un trou d'id est sans conséquence (aucune règle ne repose sur les ids)."""
        self.garantie_g(self.L1, "decennale", self.S1)
        avant, seq = self.lignes_g(), self.un("SELECT seq FROM sqlite_sequence WHERE name='garanties'")[0]
        self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                        "VALUES (?, ?, 'decennale', '2026-10-05', '2036-10-05', ?)", (self.m.b, self.L1, self.S1))
        self.assertEqual(self.lignes_g(), avant)
        self.assertGreaterEqual(self.un("SELECT seq FROM sqlite_sequence WHERE name='garanties'")[0], seq)

    def test_T50_C_aucune_garde_premier_solde_une_garantie_peut_referencer_un_second_solde_si_G1_a_G4_passent(self):
        """INTERPRETATION (QO-3 : NON) : la règle « premier solde » est portée par le service ; le SQL accepte une garantie sur un 2ᵉ solde (CK-07c la diagnostique)."""
        s2 = self.second_solde("2026-10-20")
        g_ = self.garantie_g(self.L1, "decennale", s2)
        self.assertEqual(self.un("SELECT facture_declenchement_id, date_declenchement FROM garanties WHERE id=?", g_), (s2, "2026-10-20"))
        self.assertEqual(self.tous(CK07C_NON_PREMIER), [(g_,)])


# ====================================================================================================================
# D — durées par type et 29 février (QO-2, G5)
# ====================================================================================================================
DATES_DEBUT = ("2026-10-05", "2026-01-31", "2026-12-31", "2026-01-01", "2026-02-28", "2027-02-28", "2026-03-01", "2026-06-30", "2028-02-28", "2028-03-01",
               "2028-02-29", "2000-02-29", "2096-02-29", "9996-02-29", "2024-02-29", "0004-02-29", "0000-02-29", "0001-01-01", "0000-01-01", "1900-02-28", "2100-02-28")


class Durees(Mini):
    """Groupe D : date_fin_suivi = date_declenchement + 1 / 2 / 10 ans, 29 février -> 28 février, vérifié par le CHECK G5 (base sans triggers de 008)."""

    SANS_008 = True

    def test_T50_D_table_de_verite_trois_types_par_dates_la_valeur_de_l_oracle_est_acceptee(self):
        for d_ in DATES_DEBUT:
            for t_ in TYPES_G:
                fin = fin_attendue(d_, t_)
                if fin is None:
                    continue
                with self.subTest(debut=d_, type=t_, fin=fin):
                    self.ok(t_, date_declenchement=d_, date_fin_suivi=fin)

    def test_T50_D_valeurs_fausses_refusees_pour_chaque_cas(self):
        for d_ in DATES_DEBUT:
            for t_ in TYPES_G:
                fin = fin_attendue(d_, t_)
                if fin is None:
                    continue
                faux = {jour_plus(fin, 1), jour_plus(fin, -1), "%04d%s" % (int(fin[:4]) + 1, fin[4:]) if int(fin[:4]) < 9999 else None,
                        "%04d%s" % (int(fin[:4]) - 1, fin[4:]) if int(fin[:4]) > 0 else None}
                for autre in TYPES_G:
                    if autre != t_ and fin_attendue(d_, autre) not in (None, fin):
                        faux.add(fin_attendue(d_, autre))                                   # type permuté
                for f_ in faux:
                    if f_ is None or f_ == fin:
                        continue
                    with self.subTest(debut=d_, type=t_, faux=f_):
                        self.ko(t_, date_declenchement=d_, date_fin_suivi=f_)

    def test_T50_D_le_29_fevrier_devient_le_28_fevrier_pour_les_trois_types(self):
        for d_ in ("2028-02-29", "2000-02-29", "2096-02-29", "9996-02-29", "2024-02-29"):
            y = int(d_[:4])
            for t_ in TYPES_G:
                attendu = "%04d-02-28" % (y + DUREE[t_]) if y + DUREE[t_] <= 9999 else None
                if attendu is None:
                    continue
                with self.subTest(debut=d_, type=t_):
                    self.ok(t_, date_declenchement=d_, date_fin_suivi=attendu)
                    self.ko(t_, date_declenchement=d_, date_fin_suivi="%04d-03-01" % (y + DUREE[t_]))            # ce que donnerait date(x, '+N year')
                    self.ko(t_, date_declenchement=d_, date_fin_suivi="%04d-02-29" % (y + DUREE[t_]))             # 29/02 conservé : date inexistante
                    self.ko(t_, date_declenchement=d_, date_fin_suivi="%04d-02-27" % (y + DUREE[t_]))

    def test_T50_D_un_28_fevrier_et_un_1er_mars_restent_inchanges(self):
        for d_, fin in (("2027-02-28", "2028-02-28"), ("2027-03-01", "2028-03-01"), ("2028-02-28", "2029-02-28"), ("2028-03-01", "2029-03-01")):
            with self.subTest(debut=d_):
                self.ok("parfait_achevement", date_declenchement=d_, date_fin_suivi=fin)
        self.ko("parfait_achevement", date_declenchement="2028-02-28", date_fin_suivi="2029-03-01")

    def test_T50_D_temoin_les_modificateurs_de_date_SQLite_donneraient_le_1er_mars(self):
        """Ce que le service ne doit PAS faire : date('2028-02-29', '+1 year') = '2029-03-01' (sondé)."""
        self.assertEqual(self.un("SELECT date('2028-02-29', '+1 year')")[0], "2029-03-01")
        self.assertEqual(self.un("SELECT date('2000-02-29', '+10 years')")[0], "2010-03-01")
        self.assertNotEqual(self.un("SELECT date('2028-02-29', '+1 year')")[0], fin_attendue("2028-02-29", "parfait_achevement"))
        self.ko("parfait_achevement", date_declenchement="2028-02-29", date_fin_suivi=self.un("SELECT date('2028-02-29', '+1 year')")[0])

    def test_T50_D_CT3_une_annee_cible_n_est_jamais_bissextile_quand_l_origine_l_est(self):
        """Équivalence démontrée par exhaustion : « 29/02 -> 28/02 » (INV-88) = « 28/02 si l'année cible n'est pas bissextile » (Mod. §4.10)."""
        for y in range(0, 9999):
            if bissextile(y):
                for n in DUREE.values():
                    self.assertFalse(bissextile(y + n), (y, n))

    def test_T50_D_la_duree_est_exacte_mois_et_jour_conserves(self):
        for d_ in ("2026-01-31", "2026-03-31", "2026-05-31", "2026-08-31", "2026-12-31", "2026-04-30"):
            for t_ in TYPES_G:
                fin = "%04d%s" % (int(d_[:4]) + DUREE[t_], d_[4:])
                with self.subTest(debut=d_, type=t_):
                    self.ok(t_, date_declenchement=d_, date_fin_suivi=fin)
                    self.ko(t_, date_declenchement=d_, date_fin_suivi=jour_plus(fin, -1))
                    self.ko(t_, date_declenchement=d_, date_fin_suivi=jour_plus(fin, 1))

    def test_T50_D_les_durees_ne_se_confondent_pas_entre_types(self):
        d_ = "2026-10-05"
        for t_, bon in (("parfait_achevement", "2027-10-05"), ("biennale", "2028-10-05"), ("decennale", "2036-10-05")):
            for autre, f_ in (("parfait_achevement", "2027-10-05"), ("biennale", "2028-10-05"), ("decennale", "2036-10-05")):
                with self.subTest(type=t_, fin=f_):
                    if f_ == bon:
                        self.ok(t_, date_declenchement=d_, date_fin_suivi=f_)
                    else:
                        self.ko(t_, date_declenchement=d_, date_fin_suivi=f_)

    def test_T50_D_le_check_de_duree_est_porte_par_la_table_et_pas_par_un_trigger(self):
        sql = self.un("SELECT sql FROM sqlite_master WHERE name='garanties'")[0]
        self.assertIn("'02-29'", sql)
        self.assertIn("'parfait_achevement' THEN 1", sql)
        self.assertIn("'biennale' THEN 2", sql)
        self.assertIn("ELSE 10", sql)

    def test_T50_D_la_message_de_refus_d_une_mauvaise_duree_n_a_aucun_prefixe_INV(self):
        m = self.essai_g("decennale", date_fin_suivi="2035-10-05")
        self.assertIsNotNone(m)
        self.assertIn("CHECK constraint failed", m)
        self.assertNotIn("INV-", m)

    def test_T50_D_balayage_differentiel_contre_les_deux_oracles(self):
        """Années 1990 à 2110 × 4 dates × 3 types : SQL (CHECK G5) = oracle 1 = oracle 2."""
        lignes = []
        for y in range(1990, 2111):
            dates = ["%04d-01-01" % y, "%04d-02-28" % y, "%04d-12-31" % y] + (["%04d-02-29" % y] if bissextile(y) else [])
            for d_ in dates:
                for t_ in TYPES_G:
                    o1, o2 = fin_attendue(d_, t_), fin_attendue_dt(d_, t_)
                    self.assertEqual(o1, o2, (d_, t_))
                    lignes.append((d_, t_, o1))
        self.assertGreater(len(lignes), 1000)
        for d_, t_, f_ in lignes:
            self.db.execute("SAVEPOINT balayage")
            try:
                self.db.execute("INSERT INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) VALUES (?, ?, ?, ?, ?, ?)",
                                (self.m.b, self.L, t_, d_, f_, self.S))
            except sqlite3.IntegrityError as e:
                self.fail(f"{d_} {t_} {f_} : {e}")
            finally:
                self.db.execute("ROLLBACK TO balayage")
                self.db.execute("RELEASE balayage")


# ====================================================================================================================
# E — clés étrangères et suppression des parents
# ====================================================================================================================
class Parents(Mini):
    """Groupe E : BC, ligne de BC et facture référencés par une garantie ne sont jamais supprimables ; FK RESTRICT sans ON UPDATE."""

    def setUp(self):
        super().setUp()
        self.g = self.garantie_g(self.L, "decennale", self.S)

    def test_T50_E_les_identifiants_des_quatre_tables_sont_distincts(self):
        self.assertEqual(len({self.m.b, self.L, self.S, self.g}), 4)
        self.assertEqual(self.un("SELECT bc_id, bc_ligne_id, facture_declenchement_id FROM garanties WHERE id=?", self.g), (self.m.b, self.L, self.S))

    def test_T50_E_un_BC_reference_ne_se_supprime_pas(self):
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", self.m.b)

    def test_T50_E_une_ligne_de_BC_referencee_ne_se_supprime_pas(self):
        self.refuse_inv("INV-186", "DELETE FROM bc_lignes WHERE id=?", self.L)

    def test_T50_E_une_facture_referencee_ne_se_supprime_pas(self):
        self.refuse_inv("INV-06", "DELETE FROM factures WHERE id=?", self.S)

    def test_T50_E_les_garanties_de_ligne_de_BC_ne_se_suppriment_pas(self):
        self.refuse_inv("INV-186", "DELETE FROM bc_ligne_garanties WHERE ligne_id=?", self.L)

    def test_T50_E_la_FK_restrict_refuse_la_suppression_des_parents_sur_base_sans_triggers(self):
        t = self.sans_triggers()
        m = t.monde_g([[("100.00", ("decennale",))]])
        s = t.solde_g(m)
        t.garantie_g(m.lignes[0], "decennale", s)
        for table, cle in (("factures", s), ("bc_lignes", m.lignes[0]), ("bons_commande", m.b)):
            with self.subTest(table=table):
                m_ = t.tente(f"DELETE FROM {table} WHERE id=?", cle)
                self.assertIsNotNone(m_)
                self.assertIn("FOREIGN KEY constraint failed", m_)
        self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], 1)

    def test_T50_E_la_FK_n_a_aucune_clause_on_update_la_cle_d_un_parent_ne_change_pas(self):
        t = self.sans_triggers()
        m = t.monde_g([[("100.00", ("decennale",))]])
        s = t.solde_g(m)
        t.garantie_g(m.lignes[0], "decennale", s)
        for table, cle in (("factures", s), ("bc_lignes", m.lignes[0]), ("bons_commande", m.b)):
            with self.subTest(table=table):
                m_ = t.tente(f"UPDATE {table} SET id = id + 5000 WHERE id=?", cle)
                self.assertIsNotNone(m_)
                self.assertIn("FOREIGN KEY constraint failed", m_)

    def test_T50_E_une_garantie_ne_peut_pas_viser_un_parent_inexistant(self):
        for col in ("bc_id", "bc_ligne_id", "facture_declenchement_id"):
            with self.subTest(col=col):
                m_ = self.tente_g(self.L, "biennale", self.S, **{col: 987654})
                self.assertIsNotNone(m_)

    def test_T50_E_des_colonnes_permutees_sont_refusees(self):
        """Leçon 006 : les ids des tables sont désynchronisés ; une jointure sur la mauvaise colonne ne passe pas par hasard."""
        self.assertIsNotNone(self.tente_g(self.L, "biennale", self.S, bc_id=self.L, bc_ligne_id=self.m.b))
        self.assertIsNotNone(self.tente_g(self.L, "biennale", self.S, facture_declenchement_id=self.m.b))
        self.assertIsNotNone(self.tente_g(self.L, "biennale", self.S, bc_id=self.S))

    def test_T50_E_foreign_keys_off_laisse_passer_un_orphelin_que_foreign_key_check_detecte(self):
        t = self.sans_triggers()
        m = t.monde_g([[("100.00", ("decennale",))]])
        s = t.solde_g(m)
        t.db.execute("PRAGMA foreign_keys=OFF")
        t.db.execute("INSERT INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) VALUES (?, 987654, 'decennale', '2026-10-05', '2036-10-05', ?)",
                     (m.b, s))
        self.assertEqual(len(t.tous("PRAGMA foreign_key_check")), 1)
        t.db.execute("PRAGMA foreign_keys=ON")

    def test_T50_E_aucune_cascade_supprimer_un_parent_n_est_pas_possible_meme_apres_un_avoir_total(self):
        self.avoir(self.S)
        self.refuse_inv("INV-06", "DELETE FROM factures WHERE id=?", self.S)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 1)


# ====================================================================================================================
# F — tr_50 : une garantie ne se modifie ni ne se supprime jamais
# ====================================================================================================================
class Immuabilite(Mini):
    """Groupe F : TR-50 (INV-87)."""

    def setUp(self):
        super().setUp()
        self.ids = self.creer_toutes(self.m, self.S)
        self.avant = self.lignes_g()

    def intact(self):
        self.assertEqual(self.lignes_g(), self.avant)

    def test_T50_F_chaque_colonne_est_figee(self):
        valeurs = {"id": 777, "bc_id": self.m.b + 1, "bc_ligne_id": self.L + 1, "garantie_type": "biennale", "date_declenchement": "2026-10-06",
                   "date_fin_suivi": "2037-10-05", "facture_declenchement_id": self.S + 1, "created_at": "2000-01-01T00:00:00.000Z"}
        self.assertEqual(set(valeurs), set(COLONNES_GARANTIES))
        for col, v in valeurs.items():
            with self.subTest(col=col):
                self.refuse_inv("INV-87", f"UPDATE garanties SET {col}=? WHERE id=?", v, self.ids[0])
                self.intact()

    def test_T50_F_une_ecriture_sans_effet_est_aussi_refusee(self):
        for col in COLONNES_GARANTIES:
            with self.subTest(col=col):
                self.refuse_inv("INV-87", f"UPDATE garanties SET {col}={col} WHERE id=?", self.ids[0])
        self.intact()

    def test_T50_F_update_or_replace_et_or_ignore_sont_refuses(self):
        for verbe in ("OR REPLACE", "OR IGNORE", "OR ABORT", "OR FAIL", "OR ROLLBACK"):
            with self.subTest(verbe=verbe):
                self.refuse_inv("INV-87", f"UPDATE {verbe} garanties SET date_fin_suivi='2099-01-01' WHERE id=?", self.ids[0])
        self.intact()

    def test_T50_F_update_de_toutes_les_lignes_est_refuse(self):
        self.refuse_inv("INV-87", "UPDATE garanties SET date_fin_suivi = date_fin_suivi")
        self.intact()

    def test_T50_F_update_sans_ligne_concernee_n_a_aucun_effet(self):
        n = self.db.execute("UPDATE garanties SET date_fin_suivi='2099-01-01' WHERE id=-1").rowcount
        self.assertEqual(n, 0)
        self.intact()

    def test_T50_F_delete_simple_multi_lignes_et_total_sont_refuses(self):
        for sql in ("DELETE FROM garanties WHERE id=%d" % self.ids[0], "DELETE FROM garanties WHERE bc_id=%d" % self.m.b, "DELETE FROM garanties",
                    "DELETE FROM garanties WHERE garantie_type='decennale'", "DELETE FROM garanties WHERE id IN (SELECT id FROM garanties)"):
            with self.subTest(sql=sql):
                self.refuse_inv("INV-87", sql)
                self.intact()

    def test_T50_F_delete_sans_ligne_concernee_n_a_aucun_effet(self):
        self.assertEqual(self.db.execute("DELETE FROM garanties WHERE id=-1").rowcount, 0)
        self.intact()

    def test_T50_F_insert_or_replace_est_refuse_par_le_delete_implicite(self):
        for i, (l_, t_) in enumerate(self.attendues(self.m.b)):
            with self.subTest(ligne=l_, type=t_):
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
                    self.garantie_g(l_, t_, self.S, verbe="INSERT OR REPLACE")
        self.intact()

    def test_T50_F_les_messages_de_tr_50_portent_INV_87(self):
        self.assertIn("INV-87", self.essai("UPDATE garanties SET date_fin_suivi='2099-01-01'"))
        self.assertIn("INV-87", self.essai("DELETE FROM garanties"))

    def test_T50_F_aucune_exemption_d_origine_ni_de_contexte(self):
        """INV-131 : pas de colonne origine ; le refus ne dépend ni de la facture, ni du BC, ni de l'état du BC."""
        for etat in ("gele", "termine", "annule"):
            with self.subTest(etat=etat):
                t = Base11._sur(migrer11())
                m = t.monde_g([[("100.00", ("decennale",))]])
                s = t.solde_g(m)
                g_ = t.garantie_g(m.lignes[0], "decennale", s)
                if etat == "annule":
                    t.etat(m, "annule")
                elif etat == "gele":
                    t.etat(m, "gele")
                else:
                    t.recalcul_financier(m)
                self.assertIn("INV-87", t.tente("UPDATE garanties SET date_fin_suivi='2099-01-01' WHERE id=?", g_))
                self.assertIn("INV-87", t.tente("DELETE FROM garanties WHERE id=?", g_))

    def test_T50_F_apres_un_echec_la_base_est_intacte_et_utilisable(self):
        self.assertIsNotNone(self.essai("DELETE FROM garanties"))
        self.intact()
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], len(self.ids))

    def test_T50_F_un_avoir_un_reglement_et_son_annulation_ne_touchent_pas_les_garanties(self):
        self.avoir(self.S, "10.00")
        r_ = self.encaisse(self.S, "50.00")
        self.annuler(r_)
        self.encaisse(self.S, "40.00")
        self.intact()


# ====================================================================================================================
# G — tr_51 : gardes d'insertion G1 à G4 (QO-1) ; aucune garde « premier solde » (QO-3)
# ====================================================================================================================
class Gardes(Base11):
    """Groupe G : un parent inexistant est refusé par G1/G2 (INV-90, INV-85) avant la FK ; G3 (INV-86) et G4 (INV-87) sont les gardes de QO-1."""

    def setUp(self):
        super().setUp()
        self.m = self.monde_g([[("100.00", ("decennale", "biennale")), ("50.00", ("decennale",)), ("20.00", ())]])
        self.L1, self.L2, self.L3 = self.m.lignes
        self.ac = self.acompte(self.m, self.m.d[0], "10.00", date_emission="2026-10-01", date_echeance="2026-10-01")
        self.sit = self.emettre_situation(self.m, {self.L1: 5000, self.L2: 5000, self.L3: 5000}, date_emission="2026-10-02", date_echeance="2026-10-02")
        self.S = self.solde_g(self.m, "2026-10-05")
        self.av = self.avoir(self.S, "10.00", date_emission="2026-10-06")
        self.m2 = self.monde_g([[("80.00", ("decennale",))]])
        self.S2 = self.solde_g(self.m2, "2026-10-07")
        self.M2L = self.m2.lignes[0]

    # --- valeurs acceptées -------------------------------------------------------------------------------------------
    def test_T50_G_la_valeur_now_est_refusee_par_G4_ou_par_le_CHECK_et_jamais_evaluee_par_date(self):
        """Avec les triggers : une date de déclenchement 'now' est arrêtée par G4 (INV-87, BEFORE) ; une date de fin 'now' (déclenchement conforme) par le CHECK, sans INV."""
        for v in ("now", "NOW"):
            with self.subTest(valeur=v):
                self.refuse_g("INV-87", self.L1, "decennale", self.S, date_declenchement=v, date_fin_suivi="2036-10-05")
                self.refuse_check_g(self.L1, "decennale", self.S, date_fin_suivi=v)

    def test_T50_G_toutes_les_garanties_conformes_sont_acceptees(self):
        for (l_, t_) in self.attendues(self.m.b):
            with self.subTest(ligne=l_, type=t_):
                self.accepte_g(l_, t_, self.S)
        self.accepte_g(self.M2L, "decennale", self.S2)

    # --- G1 : la ligne existe et appartient au BC ---------------------------------------------------------------------
    def test_T50_G1_bc_id_incoherent_avec_la_ligne(self):
        self.refuse_g("INV-90", self.L1, "decennale", self.S, bc_id=self.m2.b)

    def test_T50_G1_ligne_d_un_autre_BC(self):
        self.refuse_g("INV-90", self.M2L, "decennale", self.S, bc_id=self.m.b)
        self.refuse_g("INV-90", self.M2L, "decennale", self.S2, bc_id=self.m.b)

    def test_T50_G1_ligne_inexistante_ou_nulle_refusee_par_la_garde_avant_la_FK(self):
        for ligne in (987654, 0, -1, None):
            with self.subTest(ligne=ligne):
                self.refuse_g("INV-90", self.L1, "decennale", self.S, bc_ligne_id=ligne)

    def test_T50_G1_bc_inexistant_ou_nul(self):
        for bc_id in (987654, 0, None):
            with self.subTest(bc_id=bc_id):
                self.refuse_g("INV-90", self.L1, "decennale", self.S, bc_id=bc_id)

    # --- G2 : la facture de déclenchement est un solde du même BC ------------------------------------------------------
    def test_T50_G2_acompte_situation_et_avoir_refuses(self):
        for nom, f_ in (("acompte", self.ac), ("situation", self.sit), ("avoir", self.av)):
            with self.subTest(type=nom):
                self.refuse_g("INV-85", self.L1, "decennale", f_)

    def test_T50_G2_solde_d_un_autre_BC_refuse(self):
        self.refuse_g("INV-85", self.L1, "decennale", self.S2)
        self.refuse_g("INV-85", self.M2L, "decennale", self.S, bc_id=self.m2.b)

    def test_T50_G2_facture_inexistante_ou_nulle_refusee_par_la_garde_avant_la_FK(self):
        for f_ in (987654, 0, -1, None):
            with self.subTest(facture=f_):
                self.refuse_g("INV-85", self.L1, "decennale", self.S, facture_declenchement_id=f_, date_declenchement="2026-10-05")

    def test_T50_G2_un_premier_solde_totalement_credite_reste_une_facture_de_declenchement_valide(self):
        """« Actif » est une notion dérivée (PT-9) : seul le type 'solde' est gardé (E-14 : un avoir ne rouvre ni n'annule rien)."""
        self.neutraliser(self.S)
        self.accepte_g(self.L1, "decennale", self.S)

    # --- G3 : la paire existe dans bc_ligne_garanties (QO-1) -----------------------------------------------------------
    def test_T50_G3_type_absent_des_garanties_de_la_ligne(self):
        self.refuse_g("INV-86", self.L2, "biennale", self.S)
        self.refuse_g("INV-86", self.L2, "parfait_achevement", self.S)
        self.refuse_g("INV-86", self.L1, "parfait_achevement", self.S)

    def test_T50_G3_ligne_sans_aucune_garantie_de_ligne(self):
        for t_ in TYPES_G:
            with self.subTest(type=t_):
                self.refuse_g("INV-86", self.L3, t_, self.S)

    def test_T50_G3_type_inconnu_est_refuse_par_la_garde_avant_le_CHECK(self):
        self.refuse_g("INV-86", self.L1, "triennale", self.S, date_fin_suivi="2036-10-05")
        self.refuse_g("INV-86", self.L1, None, self.S, date_fin_suivi="2036-10-05")

    # --- G4 : la date de déclenchement est la date d'émission (QO-1) -----------------------------------------------------
    def test_T50_G4_date_differente_de_la_date_d_emission(self):
        for d_ in ("2026-10-04", "2026-10-06", "2025-10-05", "2027-10-05", "2026-11-05", "2026-09-05"):
            with self.subTest(date=d_):
                self.refuse_g("INV-87", self.L1, "decennale", self.S, date_declenchement=d_)

    def test_T50_G4_date_nulle_ou_mal_formee_refusee_par_la_garde_avant_le_CHECK(self):
        for d_ in (None, "", "2026-10-5", "autre"):
            with self.subTest(date=d_):
                self.refuse_g("INV-87", self.L1, "decennale", self.S, date_declenchement=d_, date_fin_suivi="2036-10-05")

    def test_T50_G4_la_date_est_celle_de_la_facture_visee_et_pas_celle_du_premier_solde(self):
        """Une garantie rattachée à un solde ultérieur porte la date de CE solde (G4 seul) ; la règle « premier solde » est au service (QO-3)."""
        self.neutraliser(self.S)
        self.recalcul_financier(self.m)
        s2 = self.solde_g(self.m, "2026-10-20")
        self.accepte_g(self.L1, "decennale", s2)
        self.refuse_g("INV-87", self.L1, "decennale", s2, date_declenchement="2026-10-05")

    # --- ordre des gardes, absence de G6, indépendance -------------------------------------------------------------------
    def test_T50_G_ordre_des_gardes_G1_puis_G2_puis_G3_puis_G4(self):
        # viole G1 et G2, G3, G4 : G1 d'abord
        self.refuse_g("INV-90", self.M2L, "biennale", self.S2, bc_id=self.m.b, date_declenchement="2000-01-01")
        # viole G2, G3 et G4 : G2 d'abord
        self.refuse_g("INV-85", self.L2, "biennale", self.ac, date_declenchement="2000-01-01")
        # viole G3 et G4 : G3 d'abord
        self.refuse_g("INV-86", self.L2, "biennale", self.S, date_declenchement="2000-01-01")

    def test_T50_G_QO3_aucune_garde_premier_solde_dans_le_sql(self):
        corps = T.sans_commentaires(self.un("SELECT sql FROM sqlite_master WHERE name='tr_51_garanties_insert'")[0])
        self.assertNotRegex(corps, r"MIN\s*\(|premier|ORDER BY|LIMIT|id\s*<\s*NEW|s\.id\s*<")
        self.assertEqual(len(re.findall(r"RAISE\s*\(", corps)), 4)

    def test_T50_G_les_gardes_ne_lisent_ni_les_reglements_ni_le_statut_du_BC_ni_les_avoirs(self):
        corps = T.sans_commentaires(self.un("SELECT sql FROM sqlite_master WHERE name='tr_51_garanties_insert'")[0])
        for interdit in ("reglements", "statut", "cancelled_at", "origine_facture_id", "avoir", "total_ht", "frozen_at", "completed_at"):
            self.assertNotIn(interdit, corps)

    def test_T50_G_CT5_aucune_garde_sur_l_etat_du_BC_une_garantie_est_acceptee_sur_un_BC_gele_termine_ou_annule(self):
        for etat in ("gele", "termine", "annule"):
            with self.subTest(etat=etat):
                t = Base11._sur(migrer11())
                m = t.monde_g([[("100.00", ("decennale",))]])
                s = t.solde_g(m)
                t.etat(m, etat) if etat != "termine" else t.recalcul_financier(m)
                t.accepte_g(m.lignes[0], "decennale", s)

    def test_T50_G_la_garde_de_QO1_G3_rend_impossible_une_garantie_sur_une_ligne_sans_garantie_de_ligne(self):
        n = self.un("SELECT COUNT(*) FROM garanties")[0]
        self.refuse_g("INV-86", self.L3, "decennale", self.S)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], n)

    def test_T50_G_les_gardes_ne_modifient_aucune_donnee(self):
        avant = self.empreinte_base(True)
        for _ in range(3):
            self.tente_g(self.L2, "biennale", self.S)
            self.tente_g(self.L1, "decennale", self.S)
        self.assertEqual(self.empreinte_base(True), avant)


# ====================================================================================================================
# H — scénarios métier (service d'émission émulé)
# ====================================================================================================================
class Metier(Base11):
    """Groupe H : C-04, C-07, C-08, C-33/T-14, C-34, DV-5, DV-9, indépendance du paiement, de l'état du BC et des PV ; E-14 (un avoir ne rouvre ni n'annule rien)."""

    def verifie_creation(self, m, res, date=D_REF):
        """Une garantie par paire de bc_ligne_garanties, valeurs recalculées par les oracles, rattachée au solde R."""
        attendu = self.attendues(m.b)
        self.assertEqual(res.inseres, len(attendu))
        lignes = self.perimetre(m.b)
        self.assertEqual([(g_[2], g_[3]) for g_ in lignes], attendu)
        for g_ in lignes:
            self.assertEqual((g_[1], g_[4], g_[5], g_[6]), (m.b, date, fin_attendue(date, g_[3]), res.solde))
            self.assertEqual(g_[5], fin_attendue_dt(date, g_[3]))

    def test_T50_H_C04_le_solde_cree_les_garanties_de_toutes_les_lignes(self):
        m = self.monde_g()
        res = self.declencher(m)
        self.assertEqual(res.mode, "PREMIER")
        self.assertEqual(res.inseres, 3)
        self.verifie_creation(m, res)
        self.assertEqual(self.tous(CK07A_MANQUANTE) + self.tous(CK07B_INCOHERENTE) + self.tous(CK07C_NON_PREMIER), [])

    def test_T50_H_un_BC_sans_garantie_de_ligne_ne_cree_aucune_ligne_et_sans_erreur(self):
        m = self.monde_g([[("100.00", ()), ("50.00", ())]])
        res = self.declencher(m)
        self.assertEqual((res.mode, res.inseres), ("PREMIER", 0))
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(self.un("SELECT type FROM factures WHERE id=?", res.solde)[0], "solde")
        self.assertEqual(self.tous(CK07A_MANQUANTE), [])

    def test_T50_H_C34_multi_devis_les_lignes_de_tous_les_devis_ont_leurs_garanties(self):
        m = self.monde_g([[("100.00", ("decennale",))], [("50.00", ("biennale", "parfait_achevement")), ("30.00", ("decennale",))]])
        self.assertEqual(len(m.bl), 2)
        res = self.declencher(m)
        self.verifie_creation(m, res)
        self.assertEqual({g_[2] for g_ in self.perimetre(m.b)}, set(m.lignes))
        self.assertEqual(res.inseres, 4)

    def test_T50_H_CT4_toutes_les_lignes_existent_au_premier_solde_un_rattachement_apres_solde_est_refuse(self):
        m = self.monde_g()
        self.declencher(m)
        d = self.devis_accepte(client_id=m.cli)
        self.refuse_inv("INV-187", "INSERT INTO bc_devis (bc_id, devis_id, rang) VALUES (?, ?, 2)", m.b, d)

    def test_T50_H_C08_DV9_un_solde_a_zero_est_un_solde_qui_declenche_les_garanties(self):
        m = self.monde_g()
        self.emettre_situation(m, {m.lignes[0]: 10000, m.lignes[1]: 10000})
        self.assertEqual(self.contractuel(m.b) - self.nette(m.b), 0)
        res = self.declencher(m)
        self.assertEqual(self.total(res.solde), 0)
        self.verifie_creation(m, res)

    def test_T50_H_DV5_une_situation_a_100_pour_cent_sans_solde_ne_declenche_aucune_garantie(self):
        m = self.monde_g()
        self.emettre_situation(m, {m.lignes[0]: 10000, m.lignes[1]: 10000})
        self.recalcul_financier(m)
        self.assertEqual(self.etat_bc(m)[:4], ("en_cours", None, None, "100.00"))              # 100 % d'avancement : ce n'est pas un solde (DV-5)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(self.soldes_bc(m.b), [])
        self.assertEqual(self.tous(CK07A_MANQUANTE), [])                                      # BC sans solde : rien d'attendu

    def test_T50_H_C07_un_avoir_partiel_sur_le_solde_laisse_les_garanties_inchangees(self):
        m = self.monde_g()
        res = self.declencher(m)
        avant = self.lignes_g()
        self.avoir(res.solde, "10.00")
        self.recalcul_financier(m)
        self.assertEqual(self.lignes_g(), avant)

    def test_T50_H_T14_un_avoir_total_sur_le_solde_conserve_les_garanties_puis_un_nouveau_solde_les_rejoue_a_l_identique(self):
        m = self.monde_g()
        r1 = self.declencher(m, "2026-10-05")
        avant = self.lignes_g()
        self.neutraliser(r1.solde)
        self.recalcul_financier(m)
        self.assertEqual(self.etat_bc(m)[:3], ("en_cours", None, None))                       # solde neutralisé : plus de 100 % facturé
        self.assertEqual(self.lignes_g(), avant)
        r2 = self.declencher(m, "2026-10-20")
        self.assertEqual((r2.mode, r2.inseres, r2.R), ("REJEU", 0, r1.solde))
        self.assertEqual(self.lignes_g(), avant)                                              # champ par champ, id compris
        self.assertEqual({g_[4] for g_ in avant}, {"2026-10-05"})
        self.assertEqual(self.un("SELECT date_100_facture FROM bons_commande WHERE id=?", m.b)[0], "2026-10-20")      # VR-10 : cache ≠ date de déclenchement
        self.assertEqual({g_[6] for g_ in self.lignes_g()}, {r1.solde})

    def test_T50_H_un_troisieme_solde_rejoue_a_l_identique_lui_aussi(self):
        m = self.monde_g()
        r1 = self.declencher(m, "2026-10-05")
        avant = self.lignes_g()
        for date in ("2026-10-20", "2026-11-03"):
            self.neutraliser(self.soldes_bc(m.b)[-1])
            self.recalcul_financier(m)
            r = self.declencher(m, date)
            self.assertEqual((r.mode, r.inseres, r.R), ("REJEU", 0, r1.solde))
            self.assertEqual(self.lignes_g(), avant)
        self.assertEqual(len(self.soldes_bc(m.b)), 3)

    def test_T50_H_un_solde_impaye_cree_les_garanties_independance_du_paiement(self):
        m = self.monde_g()
        res = self.declencher(m)
        self.assertEqual(self.reste_du(res.solde), self.total(res.solde))                      # rien n'est encaissé
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", m.b)[0], "en_cours")
        self.verifie_creation(m, res)

    def test_T50_H_reglement_annulation_et_remboursement_ne_modifient_aucune_garantie(self):
        m = self.monde_g()
        res = self.declencher(m)
        avant = self.lignes_g()
        e = self.encaisse(res.solde, self.eur_solde(res.solde))
        self.recalcul_financier(m)
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", m.b)[0], "termine")
        self.assertEqual(self.lignes_g(), avant)
        a = self.avoir(res.solde, "100.00")
        r_ = self.rembourse(a, "100.00")
        self.annuler(r_)
        self.annuler(e)
        self.recalcul_financier(m)
        self.assertEqual(self.lignes_g(), avant)

    def test_T50_H_un_BC_annule_apres_le_solde_conserve_ses_garanties(self):
        m = self.monde_g()
        res = self.declencher(m)
        avant = self.lignes_g()
        self.etat(m, "annule")
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", m.b)[0], "annule")
        self.assertEqual(self.lignes_g(), avant)
        self.assertIn("INV-87", self.tente("DELETE FROM garanties"))

    def test_T50_H_un_avoir_sur_un_BC_annule_ou_termine_ne_touche_pas_les_garanties(self):
        for etat in ("annule", "termine"):
            with self.subTest(etat=etat):
                t = Base11._sur(migrer11())
                m = t.monde_g()
                res = t.declencher(m)
                avant = t.lignes_g()
                if etat == "annule":
                    t.etat(m, "annule")
                else:
                    t.encaisse(res.solde, t.eur_solde(res.solde))
                    t.recalcul_financier(m)
                t.avoir(res.solde, "5.00")
                t.recalcul_financier(m)
                self.assertEqual(t.lignes_g(), avant)

    def test_T50_H_un_BC_annule_ne_peut_plus_recevoir_de_solde_donc_aucune_nouvelle_naissance_de_garantie(self):
        m = self.monde_g()
        self.etat(m, "annule")
        self.assertIsNotNone(self.tente_f(m, "solde", "10.00"))
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_H_la_date_de_declenchement_est_la_date_d_emission_et_pas_la_date_du_jour(self):
        m = self.monde_g()
        res = self.declencher(m, "2026-03-15")
        self.assertEqual({g_[4] for g_ in self.lignes_g()}, {"2026-03-15"})
        self.assertNotEqual(self.un("SELECT created_at FROM garanties LIMIT 1")[0][:10], "2026-03-15")
        self.verifie_creation(m, res, "2026-03-15")

    def test_T50_H_le_29_fevrier_donne_le_28_fevrier_de_l_annee_cible_par_le_service(self):
        m = self.monde_g()
        res = self.declencher(m, "2028-02-29", )
        self.verifie_creation(m, res, "2028-02-29")
        self.assertEqual(sorted({g_[5] for g_ in self.lignes_g()}), ["2029-02-28", "2030-02-28", "2038-02-28"])

    def test_T50_H_chaque_type_a_sa_duree_et_chaque_ligne_ses_types(self):
        m = self.monde_g([[("10.00", ("parfait_achevement", "biennale", "decennale")), ("10.00", ("biennale",)), ("10.00", ("decennale",))]])
        res = self.declencher(m, "2026-10-05")
        par = {(g_[2], g_[3]): g_[5] for g_ in self.lignes_g()}
        self.assertEqual(par, {(m.lignes[0], "parfait_achevement"): "2027-10-05", (m.lignes[0], "biennale"): "2028-10-05", (m.lignes[0], "decennale"): "2036-10-05",
                               (m.lignes[1], "biennale"): "2028-10-05", (m.lignes[2], "decennale"): "2036-10-05"})
        self.assertEqual(res.inseres, 5)

    def test_T50_H_deux_BC_ont_chacun_leurs_garanties_sans_interference(self):
        m1, m2 = self.monde_g(), self.monde_g([[("80.00", ("decennale", "biennale"))]])
        r1 = self.declencher(m1, "2026-10-05")
        r2 = self.declencher(m2, "2026-10-06")
        self.assertEqual({g_[1] for g_ in self.perimetre(m1.b)}, {m1.b})
        self.assertEqual({g_[1] for g_ in self.perimetre(m2.b)}, {m2.b})
        self.assertEqual({g_[6] for g_ in self.perimetre(m2.b)}, {r2.solde})
        self.assertEqual({g_[6] for g_ in self.perimetre(m1.b)}, {r1.solde})
        self.assertEqual(self.tous(CK07A_MANQUANTE) + self.tous(CK07B_INCOHERENTE) + self.tous(CK07C_NON_PREMIER), [])

    def test_T50_H_un_BC_en_cours_sans_solde_n_a_aucune_garantie_et_aucun_manquement(self):
        m = self.monde_g()
        self.acompte(m, m.d[0], "10.00")
        self.emettre_situation(m, {m.lignes[0]: 5000, m.lignes[1]: 5000})
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(self.tous(CK07A_MANQUANTE), [])

    def test_T50_H_aucun_PV_aucune_reception_aucune_reserve_dans_le_perimetre_de_008(self):
        """INV-95 : la réception, les réserves et leur levée n'agissent pas sur les garanties ; le SQL n'en connaît rien."""
        for terme in ("pv", "reserve", "reception", "levee", "procès", "proces"):
            self.assertNotRegex(code_sql().lower(), r"\b" + terme + r"\b")

    def test_T50_H_les_garanties_ne_sont_jamais_recalculees_apres_leur_creation(self):
        m = self.monde_g()
        r1 = self.declencher(m, "2026-10-05")
        avant = self.lignes_g()
        self.neutraliser(r1.solde)
        self.recalcul_financier(m)
        self.declencher(m, "2027-01-15")
        self.assertEqual(self.lignes_g(), avant)
        self.assertEqual({g_[5] for g_ in avant if g_[3] == "decennale"}, {"2036-10-05"})


# ====================================================================================================================
# I — import : aucune garantie importée ; aucune exemption d'origine
# ====================================================================================================================
class Import(Base11):
    """Groupe I : INV-134, D-16, D-23, INV-131 — un BC importé n'a aucune garantie de ligne, donc aucune garantie ; mêmes gardes pour toute origine."""

    def bc_importe(self):
        m = self.monde_g([[("100.00", ()), ("50.00", ())]], origine="import", legacy_id="r1")
        s = self.solde_g(m, origine="import", numero="X-1", legacy_id="1", legacy_data="{}")
        return m, s

    def test_T50_I_un_BC_importe_n_a_aucune_garantie_de_ligne(self):
        m, _ = self.bc_importe()
        self.assertEqual(self.attendues(m.b), [])
        self.assertEqual(self.un("SELECT origine FROM bons_commande WHERE id=?", m.b)[0], "import")

    def test_T50_I_aucune_garantie_n_est_inserable_sur_un_BC_importe_G3(self):
        m, s = self.bc_importe()
        for l_ in m.lignes:
            for t_ in TYPES_G:
                with self.subTest(ligne=l_, type=t_):
                    self.refuse_g("INV-86", l_, t_, s)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_I_le_service_n_emet_aucune_garantie_pour_un_BC_importe_et_n_echoue_pas(self):
        m = self.monde_g([[("100.00", ())]], origine="import", legacy_id="r1")
        res = self.declencher(m)
        self.assertEqual((res.mode, res.inseres), ("PREMIER", 0))
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(self.tous(CK07A_MANQUANTE) + self.tous(CK07B_INCOHERENTE), [])

    def test_T50_I_INV_131_les_memes_gardes_s_appliquent_a_une_facture_importee_sur_un_BC_v6(self):
        m = self.monde_g([[("100.00", ("decennale",))]])
        s = self.solde_g(m, "2026-10-05", origine="import", numero="X-9", legacy_id="9", legacy_data="{}")
        self.accepte_g(m.lignes[0], "decennale", s)
        self.refuse_g("INV-87", m.lignes[0], "decennale", s, date_declenchement="2026-10-06")
        self.refuse_g("INV-86", m.lignes[0], "biennale", s)

    def test_T50_I_une_ligne_de_BC_importee_sans_garantie_de_ligne_ne_recoit_aucune_garantie(self):
        m = self.monde_g([[("100.00", ())]], origine="import", legacy_id="r2")
        self.assertEqual(self.tous("SELECT * FROM bc_ligne_garanties WHERE ligne_id=?", m.lignes[0]), [])
        s = self.solde_g(m, origine="import", numero="X-2")
        self.refuse_g("INV-86", m.lignes[0], "decennale", s)

    def test_T50_I_CK07_est_vide_apres_import_d_un_BC_et_de_ses_factures(self):
        m, s = self.bc_importe()
        for ck in CK.values():
            self.assertEqual(self.tous(ck), [], ck[:40])

    def test_T50_I_la_table_garanties_n_a_aucune_colonne_d_import(self):
        cols = {x[1] for x in self.tous("PRAGMA table_info(garanties)")}
        self.assertEqual(cols & {"origine", "legacy_id", "legacy_data", "legacy_numero"}, set())
        self.assertNotIn("origine", code_sql().replace("origine_facture_id", ""))

    def test_T50_I_un_BC_importe_avec_solde_et_un_BC_natif_coexistent(self):
        m, _ = self.bc_importe()
        n = self.monde_g()
        res = self.declencher(n)
        self.assertEqual(res.inseres, 3)
        self.assertEqual({g_[1] for g_ in self.lignes_g()}, {n.b})
        self.assertEqual(self.tous(CK07A_MANQUANTE) + self.tous(CK07B_INCOHERENTE), [])


# ====================================================================================================================
# J — diagnostics CK-07a / CK-07b / CK-07c (lecture seule)
# ====================================================================================================================
class Diagnostics(Base11):
    """Groupe J : CK-07 n'a pas de formule dans les sources ; il est découpé en a (manquante), b (incohérente), c (non premier solde, diagnostic seul)."""

    def setUp(self):
        super().setUp()
        self.t = self.temoin()                                                               # sans G5 ni tr_51 : on peut installer une donnée fausse
        self.m = self.t.monde_g([[("100.00", ("decennale", "biennale")), ("50.00", ("decennale",))]])
        self.L1, self.L2 = self.m.lignes
        self.S = self.t.solde_g(self.m, "2026-10-05")
        self.m2 = self.t.monde_g([[("80.00", ("decennale",))]])
        self.S2 = self.t.solde_g(self.m2, "2026-10-06")

    def conformes(self):
        self.t.creer_toutes(self.m, self.S)
        self.t.creer_toutes(self.m2, self.S2)

    def vide(self, *noms):
        for n in noms:
            self.assertEqual(self.t.tous(CK[n]), [], n)

    def test_T50_J_une_base_conforme_ne_remonte_rien(self):
        self.conformes()
        self.vide("manquante", "incoherente", "non_premier")

    def test_T50_J_CK07a_un_solde_sans_aucune_garantie_remonte_toutes_les_paires(self):
        self.assertEqual(sorted(self.t.tous(CK07A_MANQUANTE)), sorted(self.t.attendues(self.m.b) + self.t.attendues(self.m2.b)))

    def test_T50_J_CK07a_une_seule_paire_manquante(self):
        self.conformes()
        self.t.db.execute("DROP TRIGGER tr_50_garanties_no_delete")
        self.t.db.execute("DELETE FROM garanties WHERE bc_ligne_id=? AND garantie_type='biennale'", (self.L1,))
        self.assertEqual(self.t.tous(CK07A_MANQUANTE), [(self.L1, "biennale")])

    def test_T50_J_CK07a_voit_un_BC_dont_le_solde_est_totalement_credite_Z4(self):
        """CK-07 limité aux « soldes actifs » serait aveugle ici alors que les garanties doivent persister (INV-87, T-14)."""
        self.t.neutraliser(self.S)
        propres = lambda: [x for x in self.t.tous(CK07A_MANQUANTE) if x[0] in self.m.lignes]
        self.assertEqual(len(propres()), 3)
        self.t.creer_toutes(self.m, self.S)
        self.assertEqual(propres(), [])

    def test_T50_J_CK07a_un_BC_sans_solde_n_attend_aucune_garantie(self):
        m3 = self.t.monde_g([[("10.00", TYPES_G)]])
        self.assertEqual([x for x in self.t.tous(CK07A_MANQUANTE) if x[0] in m3.lignes], [])

    def test_T50_J_CK07b_garantie_orpheline_paire_absente_de_bc_ligne_garanties(self):
        self.conformes()
        g_ = self.t.garantie_g(self.L2, "biennale", self.S)
        self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [(g_,)])

    def test_T50_J_CK07b_mauvais_BC(self):
        g_ = self.t.garantie_g(self.L1, "decennale", self.S, bc_id=self.m2.b)
        self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [(g_,)])

    def test_T50_J_CK07b_facture_non_solde_ou_d_un_autre_BC(self):
        m3 = self.t.monde_g([[("10.00", ("decennale",))]])
        ac = self.t.acompte(m3, m3.d[0], "5.00")
        g1 = self.t.garantie_g(m3.lignes[0], "decennale", ac)
        g2 = self.t.garantie_g(self.L1, "biennale", self.S2, date_declenchement="2026-10-06")
        self.assertEqual(sorted(self.t.tous(CK07B_INCOHERENTE)), sorted([(g1,), (g2,)]))

    def test_T50_J_CK07b_date_de_declenchement_erronee(self):
        g_ = self.t.garantie_g(self.L1, "decennale", self.S, date_declenchement="2026-10-06", date_fin_suivi="2036-10-06")
        self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [(g_,)])

    def test_T50_J_CK07b_date_de_fin_erronee(self):
        for fin in ("2036-10-06", "2035-10-05", "2037-10-05", "2027-10-05"):
            with self.subTest(fin=fin):
                self.t.db.execute("SAVEPOINT x")
                g_ = self.t.garantie_g(self.L1, "decennale", self.S, date_fin_suivi=fin)
                self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [(g_,)])
                self.t.db.execute("ROLLBACK TO x")
                self.t.db.execute("RELEASE x")

    def test_T50_J_CK07b_29_fevrier_mal_traite_est_detecte(self):
        m = self.t.monde_g([[("10.00", ("parfait_achevement",))]])
        s = self.t.solde_g(m, "2028-02-29")
        g_ = self.t.garantie_g(m.lignes[0], "parfait_achevement", s, date_fin_suivi="2029-03-01")
        self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [(g_,)])
        self.t.db.execute("DROP TRIGGER tr_50_garanties_update")
        self.t.db.execute("UPDATE garanties SET date_fin_suivi='2029-02-28' WHERE id=?", (g_,))
        self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [])

    def test_T50_J_CK07b_garantie_sur_un_BC_importe(self):
        t = self.t.sans_triggers()
        m = t.monde_g([[("100.00", ())]], origine="import", legacy_id="r1")
        s = t.solde_g(m, origine="import", numero="X-1")
        g_ = t.inserer("garanties", {"bc_id": m.b, "bc_ligne_id": m.lignes[0], "garantie_type": "decennale", "date_declenchement": D_REF, "date_fin_suivi": "2036-10-05",
                                     "facture_declenchement_id": s})
        self.assertEqual(t.tous(CK07B_INCOHERENTE), [(g_,)])

    def test_T50_J_CK07c_la_facture_n_est_pas_le_premier_solde_diagnostic_seul(self):
        self.t.neutraliser(self.S)
        self.t.recalcul_financier(self.m)
        s2 = self.t.solde_g(self.m, "2026-10-20")
        g_ = self.t.garantie_g(self.L1, "decennale", s2)
        self.assertEqual(self.t.tous(CK07C_NON_PREMIER), [(g_,)])
        self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [])                                  # b ne le voit pas : c'est la règle « premier solde » (service)

    def test_T50_J_CK07c_le_premier_solde_neutralise_reste_le_premier(self):
        self.conformes()
        self.t.neutraliser(self.S)
        self.vide("non_premier")

    def test_T50_J_les_requetes_sont_en_lecture_seule(self):
        self.conformes()
        self.t.garantie_g(self.L2, "biennale", self.S)
        avant = self.t.empreinte_base(True)
        for ck in CK.values():
            self.t.tous(ck)
        self.assertEqual(self.t.empreinte_base(True), avant)
        for ck in CK.values():
            self.assertRegex(ck.lstrip(), r"^SELECT\b")
            self.assertNotRegex(ck, r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER)\b")

    def test_T50_J_chaque_defaut_n_est_attribue_qu_a_la_garantie_concernee(self):
        self.conformes()
        self.t.db.execute("DROP TRIGGER tr_50_garanties_update")
        ids = [r_[0] for r_ in self.t.tous("SELECT id FROM garanties WHERE bc_id=? ORDER BY id", self.m.b)]
        self.t.db.execute("UPDATE garanties SET date_fin_suivi='2099-01-01' WHERE id=?", (ids[1],))
        self.assertEqual(self.t.tous(CK07B_INCOHERENTE), [(ids[1],)])


# ====================================================================================================================
# K — non-régression des tranches 001 à 007
# ====================================================================================================================
class NonRegression(Base11):
    """Groupe K : 008 n'écrit ni ne lit d'autre table ; les flux de 006 et 007 fonctionnent à l'identique sur la base du rang 11."""

    TABLES_EXTERNES = ("bons_commande", "bc_lignes", "bc_ligne_garanties", "factures", "facture_lignes", "reglements", "numerotation_sequences", "clients", "devis",
                       "devis_lignes", "devis_ligne_garanties", "bc_devis")

    def empreintes(self):
        return {t_: self.db.execute(f"SELECT * FROM {t_} ORDER BY rowid").fetchall() for t_ in self.TABLES_EXTERNES}

    def test_T50_K_creer_et_refuser_des_garanties_n_ecrit_dans_aucune_autre_table(self):
        m = self.monde_g()
        s = self.solde_g(m)
        avant = self.empreintes()
        for (l_, t_) in self.attendues(m.b):
            self.garantie_g(l_, t_, s)
        self.tente_g(m.lignes[1], "biennale", s)
        self.tente_g(m.lignes[0], "decennale", s, date_declenchement="2000-01-01")
        self.essai("UPDATE garanties SET date_fin_suivi='2099-01-01'")
        self.essai("DELETE FROM garanties")
        self.assertEqual(self.empreintes(), avant)

    def test_T50_K_les_triggers_de_008_ne_sont_poses_que_sur_garanties(self):
        for (n, tbl) in self.tous("SELECT name, tbl_name FROM sqlite_master WHERE type='trigger' AND name LIKE 'tr_5%'"):
            self.assertEqual(tbl, "garanties", n)
        self.assertEqual(set(TRIGGERS_008) & {n for (n,) in self.tous("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name<>'garanties'")}, set())

    def test_T50_K_le_flux_complet_de_006_et_007_fonctionne_sur_la_base_du_rang_11(self):
        m = self.monde_g([[("4000.00", ("decennale",)), ("2000.00", ("biennale",))]])
        a = self.acompte(m, m.d[0], "500.00")
        self.emettre_situation(m, {m.lignes[0]: 5000, m.lignes[1]: 5000})
        res = self.declencher(m, "2026-10-09")
        e = self.encaisse(res.solde, "100.00")
        av = self.avoir(a, "100.00")
        self.annuler(e)
        self.recalcul_financier(m)
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 2)

    def test_T50_K_les_gardes_de_006_et_007_sont_toujours_actives(self):
        m = self.monde_g()
        s = self.solde_g(m)
        self.refuse_inv("INV-06", "DELETE FROM factures WHERE id=?", s)
        self.refuse_inv("INV-70", "DELETE FROM reglements WHERE id=?", self.encaisse(s, "1.00"))
        self.assertIn("INV-72", self.tente_r(s, "encaissement", "999999.00") or "")

    def test_T50_K_la_base_du_rang_11_est_coherente_apres_un_scenario_complet(self):
        m = self.monde_g()
        self.declencher(m)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertEqual(T.db_user_version(self.db), 11)

    def test_T50_K_le_schema_des_tranches_001_a_007_est_inchange_apres_usage(self):
        avant = {(t_, n, tb): s for t_, n, tb, s in T.objets(R.migrer10())}
        m = self.monde_g()
        self.declencher(m)
        apres = {(t_, n, tb): s for t_, n, tb, s in T.objets(self.db)}
        for cle, sql in avant.items():
            self.assertEqual(apres[cle], sql, cle)

    def test_T50_K_bc_ligne_garanties_et_devis_ligne_garanties_ne_sont_pas_modifiees_par_008(self):
        m = self.monde_g()
        avant = self.tous("SELECT * FROM bc_ligne_garanties ORDER BY id") + self.tous("SELECT * FROM devis_ligne_garanties ORDER BY id")
        self.declencher(m)
        self.assertEqual(self.tous("SELECT * FROM bc_ligne_garanties ORDER BY id") + self.tous("SELECT * FROM devis_ligne_garanties ORDER BY id"), avant)


# ====================================================================================================================
# L — données malformées et contournements
# ====================================================================================================================
class Malformees(Mini):
    """Groupe L : types STRICT, octet NUL, espaces, casse, années extrêmes, réglages de connexion."""

    SANS_008 = True

    def test_T50_L_types_incompatibles_refuses_par_la_table_stricte(self):
        for col, v in (("garantie_type", b"decennale"), ("date_declenchement", b"2026-10-05"), ("date_fin_suivi", b"2036-10-05"), ("created_at", b"2026-10-10T08:00:00.000Z"),
                       ("bc_id", b"1"), ("bc_ligne_id", 1.5), ("facture_declenchement_id", "abc"), ("bc_id", "1 "), ("bc_ligne_id", "")):
            with self.subTest(col=col, valeur=v):
                self.ko(**{col: v})

    def test_T50_L_octet_nul_espaces_et_casse_dans_les_textes(self):
        for v in ("decennale\x00", "decen\x00nale", "\x00", "decennale ", " decennale", "Decennale", "DECENNALE", "\tdecennale", "decennale "):
            with self.subTest(type=v):
                self.ko(v, date_fin_suivi="2036-10-05")
        for col in ("date_declenchement", "date_fin_suivi"):
            for v in ("2026-10-05\x00", "2026-10-05\x00x", "\x002026-10-05", "2026-10-05 ", " 2026-10-05", "2026-10-05\t"):
                with self.subTest(col=col, valeur=v):
                    self.ko(**{col: v})

    def test_T50_L_chaines_hostiles_et_tres_longues(self):
        for v in ("decennale'; DROP TABLE garanties;--", "' OR '1'='1", "%", "x" * 100000):
            with self.subTest(taille=len(v)):
                self.ko(v, date_fin_suivi="2036-10-05")
        self.assertEqual(self.un("SELECT COUNT(*) FROM sqlite_master WHERE name='garanties'")[0], 1)

    def test_T50_L_annees_extremes_valides_du_calendrier(self):
        for d_, t_ in (("0000-01-01", "decennale"), ("0000-02-29", "parfait_achevement"), ("0001-12-31", "biennale"), ("9989-12-31", "decennale"), ("9998-12-31", "parfait_achevement"),
                       ("9997-12-31", "biennale"), ("9996-02-29", "biennale")):
            with self.subTest(debut=d_, type=t_):
                self.ok(t_, date_declenchement=d_, date_fin_suivi=fin_attendue(d_, t_))

    def test_T50_L_annees_dont_la_fin_n_est_pas_representable_refusees_par_contrainte(self):
        for d_, t_ in (("9999-12-31", "parfait_achevement"), ("9999-01-01", "decennale"), ("9998-06-01", "biennale"), ("9990-06-01", "decennale"), ("9998-01-01", "decennale")):
            self.assertIsNone(fin_attendue(d_, t_))
            for fin in ("10000-12-31", "%04d-12-31" % 9999, "0000-12-31", "9999-12-31"):
                with self.subTest(debut=d_, type=t_, fin=fin):
                    self.ko(t_, date_declenchement=d_, date_fin_suivi=fin)

    def test_T50_L_temoin_ignore_check_constraints_contourne_les_CHECK_mais_pas_les_FK(self):
        """Réglage de connexion hors périmètre (D-39) : documenté, jamais utilisé par l'application ; la post-condition du service (C6) reste le filet."""
        self.db.execute("PRAGMA ignore_check_constraints=ON")
        try:
            self.ok(date_fin_suivi="2035-01-01")
            self.ko(bc_id=987654)
        finally:
            self.db.execute("PRAGMA ignore_check_constraints=OFF")
        self.ko(date_fin_suivi="2035-01-01")

    def test_T50_L_foreign_keys_et_recursive_triggers_sont_actives_sur_la_connexion_de_test(self):
        self.assertEqual((self.un("PRAGMA foreign_keys")[0], self.un("PRAGMA recursive_triggers")[0]), (1, 1))

    def test_T50_L_chiffres_non_ascii_et_formes_voisines_refuses(self):
        for v in ("٢٠٢٦-١٠-٠٥", "２０２６-１０-０５", "2026‐10‐05", "2026−10−05", "2026.10.05", "2026-10-05T00:00:00.000Z", "+2026-10-05", "-2026-10-05"):
            with self.subTest(valeur=v):
                self.ko(date_declenchement=v, date_fin_suivi="2036-10-05")
                self.ko(date_fin_suivi=v)


    def test_T50_L_STRICT_refuse_un_type_incompatible_par_un_message_de_typage(self):
        """Sans STRICT, 'abc' ou 1.5 dans une colonne INTEGER serait stocké tel quel puis refusé par la FK : seul STRICT produit « cannot store … value »."""
        for col, v, ty in (("bc_ligne_id", "abc", "TEXT"), ("bc_id", 1.5, "REAL"), ("facture_declenchement_id", "x", "TEXT"), ("garantie_type", b"decennale", "BLOB"),
                           ("date_declenchement", b"2026-10-05", "BLOB"), ("date_fin_suivi", b"2036-10-05", "BLOB")):
            with self.subTest(colonne=col, valeur=v):
                self.assertRegex(self.essai_g(**{col: v}) or "", r"cannot store %s value in" % ty)

    def test_T50_L_AUTOINCREMENT_un_id_supprime_n_est_jamais_reattribue(self):
        """Base sans triggers de 008 (suppression possible en SQL direct) : sans AUTOINCREMENT, l'id du dernier enregistrement supprimé serait réattribué."""
        self.garantie_g(self.L, "decennale", self.S)
        g2 = self.garantie_g(self.L, "biennale", self.S)
        self.db.execute("DELETE FROM garanties WHERE id=?", (g2,))
        g3 = self.garantie_g(self.L, "parfait_achevement", self.S)
        self.assertGreater(g3, g2)
        self.assertEqual(self.un("SELECT seq FROM sqlite_sequence WHERE name='garanties'")[0], g3)


# ====================================================================================================================
# M — atomicité des écritures
# ====================================================================================================================
class Atomicite(Base11):
    """Groupe M : une écriture multi-lignes partiellement invalide n'écrit rien (INSERT simple) ; SAVEPOINT / ROLLBACK ; le piège de INSERT OR IGNORE."""

    def setUp(self):
        super().setUp()
        self.m = self.monde_g([[("100.00", TYPES_G)]])
        self.L = self.m.lignes[0]
        self.S = self.solde_g(self.m)

    SELECT3 = ("SELECT ?, ?, v.t, ?, v.f, ? FROM (SELECT 'parfait_achevement' AS t, '2027-10-05' AS f UNION ALL SELECT 'biennale', '2028-10-05' "
               "UNION ALL SELECT 'decennale', ?) v")
    COLS = "(bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id)"

    def test_T50_M_un_insert_select_dont_une_ligne_viole_une_garde_n_ecrit_rien(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute(f"INSERT INTO garanties {self.COLS} SELECT ?, ?, v.t, ?, v.f, ? FROM (SELECT 'parfait_achevement' AS t, '2027-10-05' AS f UNION ALL SELECT 'biennale', '2028-10-05' "
                            "UNION ALL SELECT 'decennale', '2036-10-05') v", (self.m.b, self.L, "2026-10-06", self.S))
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_M_un_insert_select_dont_une_ligne_viole_un_CHECK_n_ecrit_rien(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(f"INSERT INTO garanties {self.COLS} SELECT ?, ?, v.t, '2026-10-05', v.f, ? FROM (SELECT 'parfait_achevement' AS t, '2027-10-05' AS f UNION ALL SELECT 'biennale', '2028-10-05' "
                            "UNION ALL SELECT 'decennale', '2035-10-05') v", (self.m.b, self.L, self.S))
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_M_temoin_insert_or_ignore_select_masque_une_violation_de_CHECK_et_cree_un_lot_partiel(self):
        """Le piège de §3.6 : seuls les RAISE(ABORT) des triggers et les FK échappent à OR IGNORE ; un CHECK violé est ignoré SANS ERREUR."""
        n = self.db.execute(f"INSERT OR IGNORE INTO garanties {self.COLS} SELECT ?, ?, v.t, '2026-10-05', v.f, ? FROM (SELECT 'parfait_achevement' AS t, '2027-10-05' AS f "
                            "UNION ALL SELECT 'biennale', '2028-10-05' UNION ALL SELECT 'decennale', '2035-10-05') v", (self.m.b, self.L, self.S)).rowcount
        self.assertEqual(n, 2)
        self.assertEqual(sorted(r_[0] for r_ in self.tous("SELECT garantie_type FROM garanties")), ["biennale", "parfait_achevement"])
        self.assertEqual([x[0] for x in self.tous(CK07A_MANQUANTE) and [(self.tous(CK07A_MANQUANTE)[0][1],)]], ["decennale"])           # CK-07a la voit

    def test_T50_M_temoin_insert_or_ignore_n_ignore_pas_un_trigger_ni_une_FK(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute(f"INSERT OR IGNORE INTO garanties {self.COLS} VALUES (?, ?, 'decennale', '2026-10-06', '2036-10-06', ?)", (self.m.b, self.L, self.S))
        t = self.sans_triggers()
        m = t.monde_g([[("10.00", ("decennale",))]])
        s = t.solde_g(m)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            t.db.execute(f"INSERT OR IGNORE INTO garanties {self.COLS} VALUES (?, ?, 'decennale', '2026-10-05', '2036-10-05', 987654)", (m.b, m.lignes[0]))

    def test_T50_M_savepoint_et_rollback_annulent_les_garanties_et_restaurent_sqlite_sequence(self):
        seq = self.tous("SELECT name, seq FROM sqlite_sequence ORDER BY name")
        self.db.execute("SAVEPOINT s")
        for (l_, t_) in self.attendues(self.m.b):
            self.garantie_g(l_, t_, self.S)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 3)
        self.db.execute("ROLLBACK TO s")
        self.db.execute("RELEASE s")
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(self.tous("SELECT name, seq FROM sqlite_sequence ORDER BY name"), seq)

    def test_T50_M_une_transaction_annulee_apres_creation_ne_laisse_aucune_garantie(self):
        self.db.execute("BEGIN IMMEDIATE")
        for (l_, t_) in self.attendues(self.m.b):
            self.garantie_g(l_, t_, self.S)
        self.db.execute("ROLLBACK")
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_M_une_erreur_de_garde_dans_un_savepoint_n_annule_pas_les_ecritures_precedentes_hors_savepoint(self):
        g_ = self.garantie_g(self.L, "decennale", self.S)
        self.assertIsNotNone(self.tente_g(self.L, "biennale", self.S, date_declenchement="2000-01-01"))
        self.assertEqual(self.tous("SELECT id FROM garanties"), [(g_,)])

    def lot(self, *lignes):
        """INSERT multi-lignes (VALUES) de garanties : chaque ligne est un tuple (bc, ligne, type, début, fin, facture)."""
        return ("INSERT INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) VALUES "
                + ", ".join(["(?, ?, ?, ?, ?, ?)"] * len(lignes)), tuple(x for l_ in lignes for x in l_))

    def test_T50_M_tr51_un_lot_dont_la_deuxieme_ligne_viole_une_garde_n_ecrit_aucune_ligne(self):
        """RAISE(ABORT) défait toute l'instruction (la 1re ligne, valide, n'est pas conservée) ; RAISE(FAIL) la conserverait."""
        m2 = self.monde_g([[("10.00", ("decennale",))]])
        s2 = self.solde_g(m2, "2026-11-02")
        valide = (self.m.b, self.L, "parfait_achevement", D_REF, fin_attendue(D_REF, "parfait_achevement"), self.S)
        mauvaises = {"INV-90": (self.m.b, m2.lignes[0], "decennale", D_REF, "2036-10-05", self.S),                     # G1 : ligne d'un autre BC
                     "INV-85": (self.m.b, self.L, "biennale", D_REF, "2028-10-05", s2),                                 # G2 : solde d'un autre BC
                     "INV-86": (m2.b, m2.lignes[0], "biennale", "2026-11-02", "2028-11-02", s2),                      # G3 : couple absent de bc_ligne_garanties
                     "INV-87": (self.m.b, self.L, "biennale", "2026-10-06", "2028-10-06", self.S)}                      # G4 : date ≠ date d'émission
        for inv, mauvaise in mauvaises.items():
            with self.subTest(garde=inv):
                sql, args = self.lot(valide, mauvaise)
                with self.assertRaisesRegex(sqlite3.IntegrityError, inv):
                    self.db.execute(sql, args)
                self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
        sql, args = self.lot(valide, (self.m.b, self.L, "biennale", D_REF, "2028-10-05", self.S))                     # témoin : deux lignes valides sont écrites
        self.db.execute(sql, args)
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 2)

    def test_T50_M_tr50_un_UPSERT_et_un_REPLACE_multi_lignes_n_ecrivent_aucune_ligne(self):
        """La 2e ligne tombe sur le UNIQUE : la branche DO UPDATE (ou le DELETE implicite du REPLACE) est refusée par tr_50 ; la 1re ligne, valide, est défaite."""
        g_ = self.garantie_g(self.L, "decennale", self.S)
        avant = self.lignes_g()
        nouvelle = (self.m.b, self.L, "biennale", D_REF, "2028-10-05", self.S)
        conflit = (self.m.b, self.L, "decennale", D_REF, "2036-10-05", self.S)
        sql, args = self.lot(nouvelle, conflit)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute(sql + " ON CONFLICT (bc_ligne_id, garantie_type) DO UPDATE SET date_fin_suivi = '2099-01-01'", args)
        self.assertEqual(self.lignes_g(), avant)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute(sql.replace("INSERT INTO", "INSERT OR REPLACE INTO", 1), args)
        self.assertEqual(self.lignes_g(), avant)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-87"):
            self.db.execute("UPDATE garanties SET date_fin_suivi = '2099-01-01'")
        self.assertEqual(self.lignes_g(), avant)
        self.assertEqual(self.tous("SELECT id FROM garanties"), [(g_,)])


# ====================================================================================================================
# N — dates extrêmes (§3.6) : oracles indépendants, balayage, seuils, piège INSERT OR IGNORE, voie nominale
# ====================================================================================================================
def cas_balayage():
    """Toutes les années 0000-9999 x {01-01, 02-28, 02-29 si bissextile, 12-31} x 3 types."""
    for y in range(0, 10000):
        for md in ("01-01", "02-28", "02-29", "12-31"):
            if md == "02-29" and not bissextile(y):
                continue
            for t_ in TYPES_G:
                yield "%04d-%s" % (y, md), t_


def ddl_balayage(sql_garanties):
    """DDL de garanties privé de ses REFERENCES et de son UNIQUE (les CHECK sont conservés tels quels), sous le nom `bal` : table de balayage hors schéma réel."""
    ddl = re.sub(r"REFERENCES \w+ \(id\) ON DELETE RESTRICT", "", sql_garanties)
    ddl = ddl.replace("UNIQUE (bc_ligne_id, garantie_type),", "").replace("CREATE TABLE garanties", "CREATE TABLE bal", 1)
    return ddl


class Extremes(Base11):
    """Groupe N : date_fin_suivi non représentable (année de fin > 9999), oracles 1 et 2, balayage de 97 275 cas, seuils nommés, piège de INSERT OR IGNORE, service émulé."""

    def vide(self):
        return self.un("SELECT COUNT(*) FROM garanties")[0]

    # --- oracles -----------------------------------------------------------------------------------------------------
    def test_T50_N_les_deux_oracles_concordent_sur_tout_le_balayage(self):
        n = nulls = 0
        for d_, t_ in cas_balayage():
            n += 1
            o1 = fin_attendue(d_, t_)
            nulls += o1 is None
            if d_.startswith("0000"):
                self.assertIsNotNone(o1, (d_, t_))                                    # l'année 0000 est hors datetime : seul l'oracle 1 la couvre
                continue
            self.assertEqual(o1, fin_attendue_dt(d_, t_), (d_, t_))
        self.assertEqual(n, 97275)
        self.assertEqual(nulls, 41)

    def test_T50_N_l_oracle_1_sur_les_valeurs_clefs(self):
        for d_, t_, att in (("2028-02-29", "parfait_achevement", "2029-02-28"), ("2028-02-29", "biennale", "2030-02-28"), ("2028-02-29", "decennale", "2038-02-28"),
                            ("9996-02-29", "biennale", "9998-02-28"), ("9996-02-29", "decennale", None), ("0000-02-29", "decennale", "0010-02-28"),
                            ("9989-12-31", "decennale", "9999-12-31"), ("9990-01-01", "decennale", None), ("9999-12-31", "parfait_achevement", None),
                            ("0000-01-01", "parfait_achevement", "0001-01-01"), ("2026-10-05", "decennale", "2036-10-05")):
            self.assertEqual(fin_attendue(d_, t_), att, (d_, t_))

    def test_T50_N_bissextile_regle_gregorienne(self):
        for y, att in ((0, True), (4, True), (100, False), (400, True), (1900, False), (2000, True), (2024, True), (2100, False), (2026, False), (9996, True), (9999, False)):
            self.assertEqual(bissextile(y), att, y)
            if y:
                self.assertEqual(bissextile(y), (datetime.date(y, 1, 1) + datetime.timedelta(days=59)).day == 29, y)

    # --- balayage SQL ------------------------------------------------------------------------------------------------
    def test_T50_N_balayage_le_CHECK_accepte_exactement_la_valeur_de_l_oracle_quand_elle_existe(self):
        ddl = ddl_balayage(self.un("SELECT sql FROM sqlite_master WHERE type='table' AND name='garanties'")[0])
        self.assertNotIn("REFERENCES", ddl)
        self.assertNotIn("UNIQUE", ddl)
        self.assertIn("printf('%04d'", ddl)
        mem = sqlite3.connect(":memory:")
        mem.execute(ddl)
        cas = list(cas_balayage())
        positifs, negatifs, attendus = [], [], set()
        for k, (d_, t_) in enumerate(cas):
            fin = fin_attendue(d_, t_)
            if fin is None:
                positifs.append((k, k, t_, d_, "%d%s" % (int(d_[:4]) + DUREE[t_], d_[4:])))                    # année de fin à 5 chiffres : doit être refusée
                continue
            attendus.add(k)
            positifs.append((k, k, t_, d_, fin))
            y = int(fin[:4])
            faux = {jour_plus(fin, 1), jour_plus(fin, -1), "%04d%s" % (y + 1, fin[4:]) if y < 9999 else None, "%04d%s" % (y - 1, fin[4:]) if y > 0 else None}
            if d_[5:] == "02-29":
                faux.add("%04d-03-01" % y)
            for f_ in faux:
                if f_ and f_ != fin:
                    negatifs.append((len(cas) + len(negatifs), k, t_, d_, f_))
        mem.execute("BEGIN")
        mem.executemany("INSERT OR IGNORE INTO bal (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) VALUES (?, ?, ?, ?, ?, 1)",
                        [(a, a, t_, d_, f_) for a, _, t_, d_, f_ in positifs])
        acceptes = {r_[0] for r_ in mem.execute("SELECT bc_id FROM bal")}
        self.assertEqual(acceptes, attendus)
        self.assertEqual(len(acceptes), 97275 - 41)
        mem.execute("DELETE FROM bal")
        mem.executemany("INSERT OR IGNORE INTO bal (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) VALUES (?, ?, ?, ?, ?, 1)",
                        [(a, a, t_, d_, f_) for a, _, t_, d_, f_ in negatifs])
        self.assertEqual(mem.execute("SELECT COUNT(*) FROM bal").fetchone()[0], 0)
        self.assertGreater(len(negatifs), 300000)
        mem.execute("ROLLBACK")
        mem.close()

    # --- seuils nommés (CHECK de la table réelle, triggers retirés) ---------------------------------------------------
    def base_seuils(self):
        t = self.sans_triggers()
        m = t.monde_g([[("100.00", ())]])
        s = t.solde_g(m)
        return t, m.lignes[0], s

    def inserer_seuil(self, t, ligne, s, d_, type_, fin):
        return t.tente_g(ligne, type_, s, date_declenchement=d_, date_fin_suivi=fin, bc_id=t.bc_de_ligne(ligne))

    def test_T50_N_seuils_exacts_par_type(self):
        t, ligne, s = self.base_seuils()
        for type_, dernier_ok, premier_ko in (("parfait_achevement", 9998, 9999), ("biennale", 9997, 9998), ("decennale", 9989, 9990)):
            for md in ("01-01", "06-15", "12-31"):
                d_ok, d_ko = "%04d-%s" % (dernier_ok, md), "%04d-%s" % (premier_ko, md)
                with self.subTest(type=type_, accepte=d_ok):
                    self.assertIsNone(self.inserer_seuil(t, ligne, s, d_ok, type_, fin_attendue(d_ok, type_)), type_)
                with self.subTest(type=type_, refuse=d_ko):
                    for fin in ("%d%s" % (premier_ko + DUREE[type_], d_ko[4:]), "9999" + d_ko[4:], "%04d%s" % (premier_ko + DUREE[type_] - 10000, d_ko[4:])):
                        m_ = self.inserer_seuil(t, ligne, s, d_ko, type_, fin)
                        self.assertIsNotNone(m_, fin)
                        self.assertNotIn("INV-", m_)

    def test_T50_N_9999_12_31_est_refuse_pour_les_trois_types(self):
        t, ligne, s = self.base_seuils()
        for type_ in TYPES_G:
            for fin in ("9999-12-31", "10000-12-31", "0000-12-31", "0001-12-31"):
                with self.subTest(type=type_, fin=fin):
                    m_ = self.inserer_seuil(t, ligne, s, "9999-12-31", type_, fin)
                    self.assertIsNotNone(m_)
                    self.assertNotIn("INV-", m_)

    def test_T50_N_9996_02_29_bissextile_fins_au_28_fevrier_decennale_refusee(self):
        t, ligne, s = self.base_seuils()
        self.assertIsNone(self.inserer_seuil(t, ligne, s, "9996-02-29", "parfait_achevement", "9997-02-28"))
        self.assertIsNone(self.inserer_seuil(t, ligne, s, "9996-02-29", "biennale", "9998-02-28"))
        for fin in ("10006-02-28", "9999-12-31", "9998-02-28", "9996-02-28"):
            self.assertIsNotNone(self.inserer_seuil(t, ligne, s, "9996-02-29", "decennale", fin), fin)

    def test_T50_N_refus_par_contrainte_sans_prefixe_INV_aucune_ligne_et_sequence_inchangee(self):
        t, ligne, s = self.base_seuils()
        seq = t.tous("SELECT name, seq FROM sqlite_sequence ORDER BY name")
        avant = t.empreinte_base(True)
        for fin in ("10000-06-01", "10010-06-01", "100000-06-01", "9999-06-01"):
            with self.assertRaises(sqlite3.IntegrityError) as cm:
                t.garantie_g(ligne, "decennale", s, date_declenchement="9990-06-01", date_fin_suivi=fin)
            self.assertNotIn("INV-", str(cm.exception))
            self.assertRegex(str(cm.exception), r"CHECK constraint failed|NOT NULL")
        self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(t.tous("SELECT name, seq FROM sqlite_sequence ORDER BY name"), seq)
        self.assertEqual(t.empreinte_base(True), avant)

    # --- piège INSERT OR IGNORE --------------------------------------------------------------------------------------
    def naif(self, m, date):
        """INSERT OR IGNORE naïf du service (une instruction par paire), fin 'brute' = année + N sans bornage : retourne la somme des rowcount."""
        n = 0
        for (l_, t_) in self.attendues(m.b):
            y = int(date[:4]) + DUREE[t_]
            fin = fin_attendue(date, t_) or ("%d%s" % (y, date[4:]) if date[5:] != "02-29" else "%d-02-28" % y)
            n += self.db.execute("INSERT OR IGNORE INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                                 "VALUES (?, ?, ?, ?, ?, ?)", (m.b, l_, t_, date, fin, self.un("SELECT id FROM factures WHERE bc_id=? AND type='solde' ORDER BY id", m.b)[0])).rowcount
        return n

    def test_T50_N_piege_insert_or_ignore_ecrit_un_lot_partiel_sans_erreur(self):
        for date, att in (("9989-06-01", 3), ("9990-06-01", 2), ("9997-06-01", 2), ("9998-06-01", 1), ("9999-06-01", 0), ("9999-12-31", 0)):
            with self.subTest(date=date):
                t = self._sur(migrer11())
                m = t.monde_g([[("100.00", TYPES_G)]])
                t.solde_g(m, date)
                self.assertEqual(t.naif(m, date), att)                                  # aucune erreur levée : le lot est silencieusement partiel
                self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], att)
                self.assertEqual(len(t.tous(CK07A_MANQUANTE)), 3 - att)                 # le diagnostic a posteriori le voit

    def test_T50_N_le_service_leve_DateFinSuiviHorsFormat_avant_toute_ecriture_et_avant_la_reservation(self):
        for date in ("9990-06-01", "9997-06-01", "9998-06-01", "9999-06-01", "9999-12-31"):
            with self.subTest(date=date):
                m = self.monde_g([[("100.00", TYPES_G)]])
                avant, num = self.empreinte_base(True), self.numerotation()
                with self.assertRaises(DateFinSuiviHorsFormat) as cm:
                    self.declencher(m, date)
                self.assertEqual((cm.exception.bc, cm.exception.debut), (m.b, date))
                self.assertIn(cm.exception.type, TYPES_G)
                self.assertIn(cm.exception.ligne, m.lignes)
                self.assertFalse(self.db.in_transaction)
                self.assertEqual(self.empreinte_base(True), avant)                      # numérotation comprise
                self.assertEqual(self.numerotation(), num)
                self.assertEqual(self.soldes_bc(m.b), [])
                self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_N_echec_du_pre_controle_ne_consomme_aucun_numero(self):
        m = self.monde_g([[("100.00", TYPES_G)]])
        self.echoue(m, DateFinSuiviHorsFormat, False, date="9990-06-01")

    def test_T50_N_sans_pre_controle_la_post_condition_C1_C7_rattrape_le_lot_partiel_et_annule_tout(self):
        """Pré-contrôle neutralisé par le test : le service ne s'appuie alors que sur la post-condition ; trou de numérotation admis (échec après réservation)."""
        for date in ("9990-06-01", "9998-06-01", "9999-12-31"):
            with self.subTest(date=date):
                m = self.monde_g([[("100.00", TYPES_G)]])
                exc = self.echoue(m, PostConditionGaranties, True, date=date, precontroles=False)
                self.assertIn("C1", exc.codes)
                self.assertIn("C7", exc.codes)
                self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
                self.assertEqual(self.soldes_bc(m.b), [])

    def test_T50_N_le_pre_controle_ne_signale_que_les_types_concernes(self):
        m = self.monde_g([[("100.00", ("parfait_achevement",))]])
        with self.assertRaises(DateFinSuiviHorsFormat):
            self.declencher(m, "9999-06-01")
        r_ = self.declencher(m, "9998-12-31")                                           # 9998 + 1 = 9999 : représentable
        self.assertEqual(r_.inseres, 1)
        self.assertEqual(self.lignes_g(m.b)[0][5], "9999-12-31")

    def test_T50_N_deux_lignes_dont_une_seule_depasse_leve_l_erreur_pour_celle_ci(self):
        m = self.monde_g([[("100.00", ("parfait_achevement",)), ("50.00", ("decennale",))]])
        with self.assertRaises(DateFinSuiviHorsFormat) as cm:
            self.declencher(m, "9990-06-01")
        self.assertEqual((cm.exception.ligne, cm.exception.type), (m.lignes[1], "decennale"))

    # --- cas qui doivent réussir ---------------------------------------------------------------------------------------
    def test_T50_N_un_BC_sans_garantie_de_ligne_reussit_a_9999_12_31(self):
        m = self.monde_g([[("100.00", ())]])
        r_ = self.declencher(m, "9999-12-31")
        self.assertEqual((r_.mode, r_.inseres), ("PREMIER", 0))
        self.assertEqual(self.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(self.date_de(r_.solde), "9999-12-31")

    def test_T50_N_parfait_achevement_seul_a_9998_12_31(self):
        m = self.monde_g([[("100.00", ("parfait_achevement",))]])
        r_ = self.declencher(m, "9998-12-31")
        self.assertEqual(r_.inseres, 1)
        (g_,) = self.lignes_g(m.b)
        self.assertEqual((g_[4], g_[5]), ("9998-12-31", "9999-12-31"))

    def test_T50_N_les_trois_types_a_9989_12_31_la_decennale_atteint_9999_12_31(self):
        m = self.monde_g([[("100.00", TYPES_G)]])
        r_ = self.declencher(m, "9989-12-31")
        self.assertEqual(r_.inseres, 3)
        self.assertEqual(sorted(g_[5] for g_ in self.lignes_g(m.b)), ["9990-12-31", "9991-12-31", "9999-12-31"])

    def test_T50_N_solde_nominal_2099_fins_jusqu_a_2109(self):
        m = self.monde_g([[("100.00", TYPES_G)]])
        r_ = self.declencher(m, "2099-12-31")
        self.assertEqual(r_.inseres, 3)
        self.assertEqual(sorted(g_[5] for g_ in self.lignes_g(m.b)), ["2100-12-31", "2101-12-31", "2109-12-31"])

    def test_T50_N_bornes_basses_0000_01_01_et_0001_01_01(self):
        t, ligne, s = self.base_seuils()
        for d_ in ("0000-01-01", "0001-01-01"):
            for type_ in TYPES_G:
                self.assertIsNone(self.inserer_seuil(t, ligne, s, d_, type_, fin_attendue(d_, type_)), (d_, type_))
        self.assertIsNotNone(self.inserer_seuil(t, ligne, s, "0000-01-01", "parfait_achevement", "0000-01-01"))

    def test_T50_N_LIMITE_la_validite_calendaire_est_celle_de_date_de_SQLite_y_compris_l_an_300(self):
        """Limite héritée de la convention D (date(x) IS x), commune à toutes les tables : SQLite tient 0300-02-29 pour une date réelle (écart de son algorithme : l'an 300
        n'est pas bissextile au calendrier grégorien). 008 n'ajoute aucun calendrier (INV-177) : l'acceptation suit date(), sans valeur codée en dur."""
        t, ligne, s = self.base_seuils()
        self.assertFalse(bissextile(300))
        reelle = bool(self.un("SELECT date('0300-02-29') IS '0300-02-29'")[0])
        self.assertEqual(self.inserer_seuil(t, ligne, s, "0300-02-29", "parfait_achevement", "0301-02-28") is None, reelle)
        for d_ in ("0100-02-29", "0200-02-29", "0500-02-29", "1900-02-29", "2100-02-29", "9900-02-29"):
            with self.subTest(date=d_):
                self.assertIsNotNone(self.inserer_seuil(t, ligne, s, d_, "parfait_achevement", fin_attendue(d_, "parfait_achevement")))

    # --- voie nominale : INV-177 est une affaire de service ----------------------------------------------------------------
    def test_T50_N_le_SQL_accepte_une_facture_9990_et_ses_garanties_INV_177_est_un_controle_de_service(self):
        m = self.monde_g([[("100.00", ("parfait_achevement",))]])
        s = self.solde_g(m, "9990-06-01")
        self.assertEqual(self.date_de(s), "9990-06-01")
        self.garantie_g(m.lignes[0], "parfait_achevement", s)
        self.assertEqual(self.lignes_g(m.b)[0][5], "9991-06-01")

    def test_T50_N_yy_00_est_refuse_par_la_sequence_et_pas_par_008(self):
        m = self.monde_g([[("100.00", TYPES_G)]])
        avant = self.empreinte_base(True)
        for date in ("9900-01-01", "2100-01-01", "2000-01-01", "0000-01-01"):
            with self.subTest(date=date):
                with self.assertRaises((sqlite3.IntegrityError, ValueError, TypeError)) as cm:
                    self.numero("solde", date)
                self.assertNotIn("garantie", str(cm.exception).lower())
                if self.db.in_transaction:
                    self.db.execute("ROLLBACK")
        self.assertEqual(self.empreinte_base(True), avant)

    # --- diagnostics sur base alimentée en SQL direct ----------------------------------------------------------------------
    def test_T50_N_CK07_detecte_une_fin_tronquee_et_une_garantie_absente_a_une_date_extreme(self):
        t = self.temoin()
        m = t.monde_g([[("100.00", TYPES_G)]])
        s = t.solde_g(m, "9990-06-01")
        l_ = m.lignes[0]
        t.garantie_g(l_, "parfait_achevement", s)
        t.garantie_g(l_, "biennale", s, date_fin_suivi="9999-06-01")                    # tronquée : fausse
        self.assertEqual(t.tous(CK07A_MANQUANTE), [(l_, "decennale")])
        bad = t.tous(CK07B_INCOHERENTE)
        self.assertEqual(len(bad), 1)
        self.assertEqual(t.un("SELECT garantie_type FROM garanties WHERE id=?", bad[0][0])[0], "biennale")


# ====================================================================================================================
# O — post-condition C1 à C8 du service et atomicité de l'émission (§4.1)
# ====================================================================================================================
def boum(*_):
    raise DefautInjecte()


def sans(i_cible):
    """Défaut : retire la i-ème insertion du lot."""
    return lambda i, row, ctx: None if i == i_cible else row


def modif(i_cible, **champs):
    """Défaut : remplace des champs de la i-ème insertion (une valeur appelable reçoit (row, ctx))."""
    def f(i, row, ctx):
        if i != i_cible:
            return row
        return dict(row, **{k: (v(row, ctx) if callable(v) else v) for k, v in champs.items()})
    return f


class PostCondition(Base11):
    """Groupe O : l'émission d'un solde et la création des garanties forment UNE transaction ; toute violation de C1 à C8 l'annule intégralement. Les valeurs attendues
    sont recalculées depuis le premier solde R et bc_ligne_garanties (oracle 1), jamais lues dans les garanties persistées ni dans le CHECK. Chaque échec est vérifié
    par l'état persisté avant / après (empreinte de toute la base, relevé du BC, compteur de numérotation), pas seulement par l'exception."""

    def sans_008(self):
        t = self._sur(migrer11())
        for nom in TRIGGERS_008:
            t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def neuf(self, base="reel", devis=None, **kw):
        t = {"reel": lambda: self._sur(migrer11()), "temoin": self.temoin, "sans008": self.sans_008}[base]()
        return t, t.monde_g(devis, **kw)

    def historique(self, t, m, jusqu_a_s2=True):
        """Premier solde émis par le service (PREMIER), neutralisé, puis un 2ᵉ solde neutralisé à son tour : base prête pour un REJEU ; les triggers tr_50 sont retirés
        (SQL direct) pour pouvoir installer ensuite une garantie historique incohérente. Retourne (r1, s2)."""
        r1 = t.declencher(m, "2026-10-05")
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        s2 = None
        if jusqu_a_s2:
            s2 = t.solde_g(m, "2026-10-12")
            t.neutraliser(s2)
            t.recalcul_financier(m)
        for nom in ("tr_50_garanties_update", "tr_50_garanties_no_delete"):
            t.db.execute(f"DROP TRIGGER {nom}")
        return r1, s2

    # ---- O1 : garantie absente après INSERT OR IGNORE -----------------------------------------------------------------------
    def test_T50_O1_une_paire_retiree_du_lot_donne_C1_et_C7_et_annule_tout(self):
        t, m = self.neuf()
        exc = t.echoue(m, PostConditionGaranties, True, defaut=sans(1))
        self.assertEqual((exc.phase, exc.codes), ("post", {"C1", "C7"}))
        self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], 0)
        self.assertEqual(t.soldes_bc(m.b), [])

    def test_T50_O1_toutes_les_paires_retirees_une_violation_C1_par_paire(self):
        t, m = self.neuf()
        exc = t.echoue(m, PostConditionGaranties, True, defaut=lambda i, row, ctx: None)
        self.assertEqual(sorted(v[:3] for v in exc.violations if v[0] == "C1"), sorted(("C1", l_, t_) for (l_, t_) in t.attendues(m.b)))
        self.assertIn("C7", exc.codes)

    def test_T50_O1_une_fin_fausse_refusee_par_le_CHECK_G5_puis_ignoree_donne_C1(self):
        t, m = self.neuf()
        exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(0, date_fin_suivi=lambda row, ctx: jour_plus(row["date_fin_suivi"], 1)))
        self.assertEqual(exc.codes, {"C1", "C7"})

    def test_T50_O1_une_fin_NULL_ignoree_par_NOT_NULL_donne_C1(self):
        t, m = self.neuf()
        exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(2, date_fin_suivi=None))
        self.assertEqual(exc.codes, {"C1", "C7"})

    def test_T50_O1_le_lot_complet_et_conforme_passe_les_huit_controles(self):
        t, m = self.neuf()
        r_ = t.declencher(m)
        self.assertEqual((r_.mode, r_.inseres), ("PREMIER", 3))
        self.assertEqual(t.controles(m.b, r_.R, "PREMIER", 3, []), [])
        self.assertEqual(t.tous(CK07A_MANQUANTE) + t.tous(CK07B_INCOHERENTE) + t.tous(CK07C_NON_PREMIER), [])

    # ---- O2 : garantie rattachée à la mauvaise facture / préexistante en PREMIER ---------------------------------------------
    def test_T50_O2a_PREMIER_avec_garantie_preexistante_donne_C8_etat_releve_avant_les_insertions(self):
        t = self.sans_008()
        m, m2 = t.monde_g(), t.monde_g([[("10.00", ("decennale",))]])
        s_autre = t.solde_g(m2)
        t.garantie_g(m.lignes[1], "decennale", s_autre, bc_id=m.b)                       # garantie du BC m rattachée à un solde d'un autre BC
        exc = t.echoue(m, PostConditionGaranties, True)
        self.assertEqual((exc.phase, exc.codes), ("post", {"C8"}))
        self.assertEqual(exc.violations, [("C8", 1)])

    def test_T50_O2b_REJEU_dont_les_garanties_historiques_pointent_le_2e_solde_C4_C5_C6_au_pre_controle(self):
        t, m = self.neuf("sans008")
        r1 = t.declencher(m, "2026-10-05")
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        s2 = t.solde_g(m, "2026-10-20")
        t.neutraliser(s2)
        t.recalcul_financier(m)
        t.db.execute("DROP TRIGGER IF EXISTS tr_50_garanties_update")
        for (gid,) in t.tous("SELECT id FROM garanties ORDER BY id"):
            t.db.execute("UPDATE garanties SET facture_declenchement_id=?, date_declenchement=?, date_fin_suivi=? WHERE id=?",
                         (s2, "2026-10-20", fin_attendue("2026-10-20", t.un("SELECT garantie_type FROM garanties WHERE id=?", gid)[0]), gid))
        exc = t.echoue(m, PostConditionGaranties, False, date="2026-11-03")             # G1-G4 satisfaites (date du 2e solde) ; détecté AVANT la réservation
        self.assertEqual((exc.phase, exc.codes), ("pre", {"C4", "C5", "C6"}))

    def test_T50_O2b_pre_controle_neutralise_la_post_condition_detecte_la_meme_chose_en_transaction(self):
        t, m = self.neuf("sans008")
        r1 = t.declencher(m, "2026-10-05")
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        s2 = t.solde_g(m, "2026-10-20")
        t.neutraliser(s2)
        t.recalcul_financier(m)
        t.db.execute("DROP TRIGGER IF EXISTS tr_50_garanties_update")
        t.db.execute("UPDATE garanties SET facture_declenchement_id=?", (s2,))
        exc = t.echoue(m, PostConditionGaranties, True, date="2026-11-03", precontroles=False)
        self.assertEqual((exc.phase, exc.codes), ("post", {"C4"}))

    # ---- O3 : date_declenchement fausse ---------------------------------------------------------------------------------------
    def test_T50_O3_base_temoin_date_fausse_plus_ou_moins_un_jour_donne_C5(self):
        for delta in (1, -1, 31, -365):
            with self.subTest(delta=delta):
                t, m = self.neuf("temoin")
                exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(0, date_declenchement=lambda row, ctx: jour_plus(ctx.D, delta)))
                self.assertEqual(exc.codes, {"C5"})

    def test_T50_O3_base_temoin_date_du_nouveau_solde_au_lieu_de_celle_de_R_donne_C5(self):
        t, m = self.neuf("temoin")
        r1 = t.declencher(m, "2026-10-05")
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        t.db.execute("DROP TRIGGER tr_50_garanties_no_delete")
        t.db.execute("DELETE FROM garanties WHERE id=(SELECT MIN(id) FROM garanties)")
        exc = t.echoue(m, PostConditionGaranties, False, date="2026-10-20")              # pré-contrôle : paire manquante (C1) en REJEU
        self.assertEqual((exc.phase, exc.codes), ("pre", {"C1"}))

    def test_T50_O3_base_reelle_l_insertion_du_service_leve_INV_87_G4_et_tout_est_annule(self):
        t, m = self.neuf()
        exc = t.echoue(m, sqlite3.IntegrityError, True, defaut=modif(1, date_declenchement=lambda row, ctx: jour_plus(ctx.D, 1)))
        self.assertIn("INV-87", str(exc))

    # ---- O4 : date_fin_suivi fausse -------------------------------------------------------------------------------------------
    def test_T50_O4_base_temoin_fins_fausses_donnent_C6(self):
        faux = {"+1 jour": lambda row, ctx: jour_plus(row["date_fin_suivi"], 1), "-1 jour": lambda row, ctx: jour_plus(row["date_fin_suivi"], -1),
                "+1 an": lambda row, ctx: "%04d%s" % (int(row["date_fin_suivi"][:4]) + 1, row["date_fin_suivi"][4:]),
                "-1 an": lambda row, ctx: "%04d%s" % (int(row["date_fin_suivi"][:4]) - 1, row["date_fin_suivi"][4:]),
                "type permute": lambda row, ctx: fin_attendue(ctx.D, "decennale" if row["garantie_type"] != "decennale" else "biennale")}
        for nom, f_ in faux.items():
            with self.subTest(faute=nom):
                t, m = self.neuf("temoin")
                exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(0, date_fin_suivi=f_))
                self.assertEqual(exc.codes, {"C6"})

    def test_T50_O4_base_temoin_29_fevrier_conserve_ou_01_mars_C1_ou_C6(self):
        t, m = self.neuf("temoin", [[("100.00", ("parfait_achevement",))]])
        exc = t.echoue(m, PostConditionGaranties, True, date="2028-02-29", defaut=modif(0, date_fin_suivi="2029-03-01"))     # ce que donnerait date(x, '+1 year')
        self.assertEqual(exc.codes, {"C6"})
        t, m = self.neuf("temoin", [[("100.00", ("parfait_achevement",))]])
        exc = t.echoue(m, PostConditionGaranties, True, date="2028-02-29", defaut=modif(0, date_fin_suivi="2029-02-29"))     # 29/02 conservé : date inexistante, CHECK de date -> ignoré
        self.assertEqual(exc.codes, {"C1", "C7"})

    def test_T50_O4_base_reelle_le_CHECK_G5_refuse_OR_IGNORE_ignore_C1_detecte(self):
        for f_ in (lambda row, ctx: jour_plus(row["date_fin_suivi"], -1), lambda row, ctx: "%04d-03-01" % (int(row["date_fin_suivi"][:4]))):
            t, m = self.neuf()
            exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(0, date_fin_suivi=f_))
            self.assertEqual(exc.codes, {"C1", "C7"})

    # ---- O5 : mauvais BC ou mauvaise ligne ------------------------------------------------------------------------------------
    def test_T50_O5_base_temoin_bc_id_d_un_autre_BC_donne_C3(self):
        t, m = self.neuf("temoin")
        m2 = t.monde_g([[("10.00", ("decennale",))]])
        exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(0, bc_id=m2.b))
        self.assertEqual(exc.codes, {"C3"})

    def test_T50_O5_base_temoin_ligne_d_un_autre_BC_avec_le_bon_bc_id_donne_C1_C2_C3(self):
        t, m = self.neuf("temoin")
        m2 = t.monde_g([[("10.00", ("decennale",))]])
        exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(0, bc_ligne_id=m2.lignes[0], garantie_type="decennale", date_fin_suivi=fin_attendue(D_REF, "decennale")))
        self.assertEqual(exc.codes, {"C1", "C2", "C3"})

    def test_T50_O5_base_temoin_bc_et_ligne_d_un_autre_BC_garantie_hors_perimetre_donne_C1(self):
        t, m = self.neuf("temoin")
        m2 = t.monde_g([[("10.00", ("decennale",))]])
        exc = t.echoue(m, PostConditionGaranties, True, defaut=modif(0, bc_id=m2.b, bc_ligne_id=m2.lignes[0], garantie_type="decennale"))
        self.assertEqual(exc.codes, {"C1"})
        self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_O5_base_reelle_G1_refuse_et_tout_est_annule(self):
        for champs in ({"bc_id": "autre"}, {"bc_ligne_id": "autre"}):
            with self.subTest(champs=champs):
                t, m = self.neuf()
                m2 = t.monde_g([[("10.00", ("decennale",))]])
                vals = {"bc_id": m2.b} if "bc_id" in champs else {"bc_ligne_id": m2.lignes[0], "garantie_type": "decennale"}
                exc = t.echoue(m, sqlite3.IntegrityError, True, defaut=modif(0, **vals))
                self.assertIn("INV-90", str(exc))

    # ---- O6 : rejeu légitime au 2e solde --------------------------------------------------------------------------------------
    def test_T50_O6_rejeu_legitime_zero_garantie_creee_historique_identique_champ_par_champ(self):
        t, m = self.neuf()
        r1 = t.declencher(m, "2026-10-05")
        avant = t.lignes_g()
        self.assertEqual(len(avant), 3)
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        n0, ns = t.dernier("FAC", 26), t.numerotation()
        r2 = t.declencher(m, "2026-10-20", tenter_rejeu=True)                              # tentative INSERT OR IGNORE avec les valeurs de R : 0 attendu
        self.assertEqual((r2.mode, r2.inseres, r2.R, r2.D), ("REJEU", 0, r1.solde, "2026-10-05"))
        self.assertEqual(t.lignes_g(), avant)                                              # id, bc, ligne, type, dates, facture, created_at
        self.assertEqual({g_[6] for g_ in t.lignes_g()}, {r1.solde})
        self.assertEqual({g_[4] for g_ in t.lignes_g()}, {"2026-10-05"})
        # le nouveau solde, ses lignes, son numéro et les caches sont bien persistés
        self.assertEqual(r2.numero, f"FAC-{n0 + 1:05d}-26")
        self.assertEqual(t.un("SELECT numero, type, date_emission FROM factures WHERE id=?", r2.solde), (r2.numero, "solde", "2026-10-20"))
        self.assertGreater(t.un("SELECT COUNT(*) FROM facture_lignes WHERE facture_id=?", r2.solde)[0], 0)
        self.assertEqual(t.un("SELECT date_100_facture FROM bons_commande WHERE id=?", m.b)[0], "2026-10-20")     # distinct de date_declenchement
        self.assertEqual(t.dernier("FAC", 26), n0 + 1)
        self.assertEqual(t.tous(CK07A_MANQUANTE) + t.tous(CK07B_INCOHERENTE) + t.tous(CK07C_NON_PREMIER), [])

    def test_T50_O6_troisieme_solde_meme_resultat_et_numeros_consecutifs(self):
        t, m = self.neuf()
        r1 = t.declencher(m, "2026-10-05")
        avant = t.lignes_g()
        nums = [r1.numero]
        for date in ("2026-10-20", "2026-11-03"):
            t.neutraliser(t.soldes_bc(m.b)[-1])
            t.recalcul_financier(m)
            r = t.declencher(m, date, tenter_rejeu=True)
            self.assertEqual((r.mode, r.inseres, r.R), ("REJEU", 0, r1.solde))
            nums.append(r.numero)
            self.assertEqual(t.lignes_g(), avant)
        self.assertEqual([int(x.split("-")[1]) for x in nums], [1, 2, 3])

    def test_T50_O6_BC_sans_garantie_de_ligne_aucune_garantie_aucune_erreur_en_PREMIER_comme_en_REJEU(self):
        t, m = self.neuf("reel", [[("100.00", ())]])
        r1 = t.declencher(m, "2026-10-05")
        self.assertEqual((r1.mode, r1.inseres), ("PREMIER", 0))
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        r2 = t.declencher(m, "2026-10-20", tenter_rejeu=True)
        self.assertEqual((r2.mode, r2.inseres), ("REJEU", 0))
        self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], 0)

    def test_T50_O6_un_solde_a_zero_ne_peut_pas_etre_rejoue_INV_52_et_CHECK_des_avoirs(self):
        """Un solde à 0.00 ne se neutralise pas (CHECK : avoir > 0) : un 2ᵉ solde est refusé (INV-52), le REJEU à 0.00 est inatteignable."""
        t, m = self.neuf()
        t.emettre_situation(m, {m.lignes[0]: 10000, m.lignes[1]: 10000})
        r1 = t.declencher(m, "2026-10-05")
        self.assertEqual(t.total(r1.solde), 0)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK constraint failed"):
            t.neutraliser(r1.solde)
        exc = t.echoue(m, sqlite3.IntegrityError, True, date="2026-10-20")
        self.assertIn("INV-52", str(exc))
        self.assertEqual(len(t.lignes_g()), 3)

    # ---- O7 : restauration complète de l'état -----------------------------------------------------------------------------------
    def test_T50_O7_chaque_scenario_d_echec_restaure_exactement_l_etat(self):
        suivis = ("factures", "facture_lignes", "garanties", "reglements", "bons_commande")
        scenarios = [
            ("O1 paire retirée", "reel", PostConditionGaranties, dict(defaut=sans(0))),
            ("O1 fin ignorée", "reel", PostConditionGaranties, dict(defaut=modif(1, date_fin_suivi=lambda row, ctx: jour_plus(row["date_fin_suivi"], 1)))),
            ("O3 INV-87", "reel", sqlite3.IntegrityError, dict(defaut=modif(2, date_declenchement=lambda row, ctx: jour_plus(ctx.D, -1)))),
            ("O3 C5", "temoin", PostConditionGaranties, dict(defaut=modif(0, date_declenchement=lambda row, ctx: jour_plus(ctx.D, 1)))),
            ("O4 C6", "temoin", PostConditionGaranties, dict(defaut=modif(1, date_fin_suivi=lambda row, ctx: jour_plus(row["date_fin_suivi"], 1)))),
            ("O5 C1 paire retirée", "temoin", PostConditionGaranties, dict(defaut=sans(1))),
            ("O13 après INSERT", "reel", DefautInjecte, dict(apres_insert=boum)),
            ("O13 après caches", "reel", DefautInjecte, dict(apres_caches=boum)),
            ("O13 avant COMMIT", "reel", DefautInjecte, dict(avant_commit=boum)),
        ]
        for nom, base, exc_t, kw in scenarios:
            with self.subTest(scenario=nom):
                t, m = self.neuf(base)
                avant = {tb: t.tous(f"SELECT * FROM {tb} ORDER BY id") for tb in suivis}
                seq = t.tous("SELECT name, seq FROM sqlite_sequence WHERE name <> 'numerotation_sequences' ORDER BY name")
                t.echoue(m, exc_t, True, **kw)
                self.assertEqual({tb: t.tous(f"SELECT * FROM {tb} ORDER BY id") for tb in suivis}, avant)
                self.assertEqual(t.tous("SELECT name, seq FROM sqlite_sequence WHERE name <> 'numerotation_sequences' ORDER BY name"), seq)
                self.assertEqual(t.un("SELECT COUNT(*) FROM garanties")[0], 0)

    # ---- O8 : numérotation ---------------------------------------------------------------------------------------------------------
    def test_T50_O8_echec_avant_reservation_le_compteur_est_inchange(self):
        t, m = self.neuf("reel", [[("100.00", TYPES_G)]])
        t.echoue(m, DateFinSuiviHorsFormat, False, date="9990-06-01")
        t2, m2 = self.neuf("temoin")
        r1 = t2.declencher(m2, "2026-10-05")
        t2.neutraliser(r1.solde)
        t2.recalcul_financier(m2)
        t2.db.execute("DROP TRIGGER IF EXISTS tr_50_garanties_update")
        t2.db.execute("UPDATE garanties SET date_declenchement='2026-10-06' WHERE id=(SELECT MIN(id) FROM garanties)")
        t2.echoue(m2, PostConditionGaranties, False, date="2026-10-20")

    def test_T50_O8_echec_apres_reservation_trou_jamais_reutilise_le_suivant_prend_N_plus_1(self):
        t, m = self.neuf()
        n0 = t.dernier("FAC", 26)
        t.echoue(m, PostConditionGaranties, True, defaut=sans(0))
        self.assertEqual(t.dernier("FAC", 26), n0 + 1)                                    # trou : N+1 réservé, aucune facture ne le porte
        r_ = t.declencher(m)
        self.assertEqual(r_.numero, f"FAC-{n0 + 2:05d}-26")                               # jamais N+1
        self.assertEqual(t.un("SELECT numero FROM factures WHERE id=?", r_.solde)[0], f"FAC-{n0 + 2:05d}-26")
        self.assertEqual(t.un("SELECT COUNT(*) FROM factures WHERE numero=?", f"FAC-{n0 + 1:05d}-26")[0], 0)
        self.assertEqual(t.dernier("FAC", 26), n0 + 2)

    def test_T50_O8_le_compteur_ne_decroit_jamais_sur_une_suite_d_echecs_et_de_succes(self):
        t, m = self.neuf()
        suite = [t.dernier("FAC", 26)]
        for kw in (dict(defaut=sans(0)), dict(apres_insert=boum), dict(apres_caches=boum), dict(avant_commit=boum)):
            with self.assertRaises((PostConditionGaranties, DefautInjecte)):
                t.declencher(m, **kw)
            suite.append(t.dernier("FAC", 26))
        t.declencher(m)
        suite.append(t.dernier("FAC", 26))
        self.assertEqual(suite, list(range(suite[0], suite[0] + 6)))
        self.assertEqual(t.un("SELECT COUNT(*) FROM factures WHERE type='solde'")[0], 1)

    def test_T50_O8_un_echec_sans_reservation_entre_deux_echecs_avec_reservation_ne_change_pas_le_compteur(self):
        t, m = self.neuf("reel", [[("100.00", TYPES_G)]])
        n0 = t.dernier("FAC", 26)
        with self.assertRaises(PostConditionGaranties):
            t.declencher(m, defaut=sans(0))
        with self.assertRaises(DateFinSuiviHorsFormat):
            t.declencher(m, "9990-06-01")
        self.assertEqual(t.dernier("FAC", 26), n0 + 1)
        self.assertEqual(t.dernier("FAC", 90), 0)

    # ---- O9 : garantie historique incohérente en REJEU --------------------------------------------------------------------------
    CAS_REJEU = {
        "mauvaise facture": ("UPDATE garanties SET facture_declenchement_id=:s2 WHERE id=:g0", {"C4"}),
        "date": ("UPDATE garanties SET date_declenchement='2026-10-06' WHERE id=:g0", {"C5"}),
        "fin": ("UPDATE garanties SET date_fin_suivi='2099-01-01' WHERE id=:g0", {"C6"}),
        "mauvais BC": ("UPDATE garanties SET bc_id=:b2 WHERE id=:g0", {"C3"}),
        "mauvaise ligne": ("UPDATE garanties SET bc_ligne_id=:l2 WHERE id=:g0", {"C1", "C2", "C3"}),
        "surplus": ("INSERT INTO garanties (bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi, facture_declenchement_id) "
                    "VALUES (:b, :lsurplus, 'decennale', '2026-10-05', '2036-10-05', :r1)", {"C2"}),
        "paire manquante": ("DELETE FROM garanties WHERE id=:g0", {"C1"}),
    }

    def installer_cas(self, nom):
        t, m = self.neuf("temoin")
        m2 = t.monde_g([[("10.00", ("decennale",))]])
        r1, s2 = self.historique(t, m)
        g0 = t.un("SELECT MIN(id) FROM garanties")[0]
        sql, att = self.CAS_REJEU[nom]
        t.db.execute(sql, {"s2": s2, "g0": g0, "b2": m2.b, "l2": m2.lignes[0], "b": m.b, "lsurplus": m.lignes[1], "r1": r1.solde})
        return t, m, att

    def test_T50_O9_pre_controle_rien_n_est_corrige_ni_supprime_fail_closed_compteur_inchange(self):
        for nom in self.CAS_REJEU:
            with self.subTest(cas=nom):
                t, m, att = self.installer_cas(nom)
                exc = t.echoue(m, PostConditionGaranties, False, date="2026-10-20")
                self.assertEqual((exc.phase, exc.codes), ("pre", att))

    def test_T50_O9_pre_controle_neutralise_la_post_condition_en_transaction_detecte_et_annule(self):
        for nom in self.CAS_REJEU:
            with self.subTest(cas=nom):
                t, m, att = self.installer_cas(nom)
                exc = t.echoue(m, PostConditionGaranties, True, date="2026-10-20", precontroles=False)
                self.assertEqual((exc.phase, exc.codes), ("post", att))

    def test_T50_O9_la_tentative_de_rejeu_ne_corrige_rien_meme_avec_les_bonnes_valeurs(self):
        t, m, _ = self.installer_cas("date")
        avant = t.lignes_g()
        with self.assertRaises(PostConditionGaranties):
            t.declencher(m, "2026-10-20", tenter_rejeu=True)
        self.assertEqual(t.lignes_g(), avant)

    # ---- O10 : surplus (C2) -------------------------------------------------------------------------------------------------------
    def test_T50_O10_surplus_en_REJEU_garantie_hors_bc_ligne_garanties_C2(self):
        t, m, att = self.installer_cas("surplus")
        self.assertEqual(att, {"C2"})
        self.assertEqual(t.tous(CK07B_INCOHERENTE), [(t.un("SELECT MAX(id) FROM garanties")[0],)])

    def test_T50_O10_surplus_preexistant_en_PREMIER_C8_prime_C2_est_vu_aussi_par_le_diagnostic(self):
        t = self.sans_008()
        m, m2 = t.monde_g(), t.monde_g([[("10.00", ("decennale",))]])
        s_autre = t.solde_g(m2)
        g_ = t.garantie_g(m.lignes[1], "decennale", s_autre, bc_id=m.b)
        self.assertEqual(t.tous(CK07B_INCOHERENTE), [(g_,)])
        exc = t.echoue(m, PostConditionGaranties, True)
        self.assertEqual(exc.codes, {"C8"})

    def test_T50_O10_garantie_portee_par_un_BC_importe_C2(self):
        t = self.temoin()
        m = t.monde_g([[("100.00", ())]], origine="import", legacy_id="r1")
        s = t.solde_g(m, origine="import", numero="X-1", legacy_id="1", legacy_data="{}")
        g_ = t.garantie_g(m.lignes[0], "decennale", s)
        self.assertEqual(t.attendues(m.b), [])
        self.assertEqual(t.controles(m.b, s, "REJEU", None, None), [("C2", g_)])
        self.assertEqual(t.tous(CK07B_INCOHERENTE), [(g_,)])

    # ---- O11 : 29 février -----------------------------------------------------------------------------------------------------------
    def test_T50_O11_premier_solde_au_29_fevrier_2028_fins_au_28_fevrier_post_condition_satisfaite(self):
        t, m = self.neuf("reel", [[("100.00", TYPES_G)]])
        r_ = t.declencher(m, "2028-02-29")
        self.assertEqual((r_.mode, r_.inseres, r_.D), ("PREMIER", 3, "2028-02-29"))
        self.assertEqual({g_[3]: g_[5] for g_ in t.lignes_g()}, {"parfait_achevement": "2029-02-28", "biennale": "2030-02-28", "decennale": "2038-02-28"})
        self.assertEqual(t.controles(m.b, r_.R, "PREMIER", 3, []), [])

    def test_T50_O11_une_fin_au_01_mars_injectee_donne_C6_en_temoin_et_C1_en_base_reelle(self):
        t, m = self.neuf("temoin", [[("100.00", ("biennale",))]])
        exc = t.echoue(m, PostConditionGaranties, True, date="2028-02-29", defaut=modif(0, date_fin_suivi="2030-03-01"))
        self.assertEqual(exc.codes, {"C6"})
        t, m = self.neuf("reel", [[("100.00", ("biennale",))]])
        exc = t.echoue(m, PostConditionGaranties, True, date="2028-02-29", defaut=modif(0, date_fin_suivi="2030-03-01"))
        self.assertEqual(exc.codes, {"C1", "C7"})

    def test_T50_O11_rejeu_apres_un_premier_solde_au_29_fevrier(self):
        t, m = self.neuf("reel", [[("100.00", TYPES_G)]])
        r1 = t.declencher(m, "2028-02-29")
        avant = t.lignes_g()
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        r2 = t.declencher(m, "2028-03-15", tenter_rejeu=True)
        self.assertEqual((r2.mode, r2.inseres), ("REJEU", 0))
        self.assertEqual(t.lignes_g(), avant)

    # ---- O12 : indépendance des valeurs attendues ---------------------------------------------------------------------------------------
    def test_T50_O12_les_fins_persistees_par_le_service_concordent_avec_l_oracle_2(self):
        for date in ("2026-10-05", "2028-02-29", "2096-02-29", "2026-12-31", "2024-02-28", "2099-12-31", "2027-03-01"):
            with self.subTest(date=date):
                t, m = self.neuf("reel", [[("100.00", TYPES_G)]])
                r_ = t.declencher(m, date)
                for g_ in t.lignes_g(m.b):
                    self.assertEqual(g_[5], fin_attendue_dt(date, g_[3]))
                    self.assertEqual(g_[5], fin_attendue(date, g_[3]))
                    self.assertEqual(g_[4], date)
                    self.assertEqual(g_[6], r_.R)

    def test_T50_O12_temoin_valeurs_attendues_tirees_de_la_ligne_persistee_valideraient_une_ligne_fausse(self):
        t = self.temoin()
        m = t.monde_g()
        s = t.solde_g(m)
        t.creer_toutes(m, s, date_declenchement="2026-10-06")                               # date fausse, fin cohérente avec cette date fausse
        naif = [g_[0] for g_ in t.perimetre(m.b) if g_[5] != fin_attendue(g_[4], g_[3])]
        self.assertEqual(naif, [])                                                          # contrôle « auto-référent » : faux accord
        self.assertEqual({v[0] for v in t.controles(m.b, s, "REJEU", None, None)}, {"C5", "C6"})

    def test_T50_O12_temoin_valeurs_attendues_tirees_du_nouveau_solde_rejetteraient_un_rejeu_legitime(self):
        t, m = self.neuf()
        r1 = t.declencher(m, "2026-10-05")
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        r2 = t.declencher(m, "2026-10-20", tenter_rejeu=True)
        P = t.perimetre(m.b)
        faux_rejet = [g_[0] for g_ in P if g_[4] != t.date_de(r2.solde)]
        self.assertEqual(len(faux_rejet), 3)                                                # attendu « date du nouveau solde » : tout serait rejeté à tort
        self.assertEqual(t.controles(m.b, r1.solde, "REJEU", 0, P), [])                    # attendu « date de R » : légitime

    # ---- O13 : ordre ---------------------------------------------------------------------------------------------------------------------------
    def test_T50_O13_defaut_apres_les_INSERT_rollback_integral(self):
        t, m = self.neuf()
        vu = []
        t.echoue(m, DefautInjecte, True, apres_insert=lambda s, ctx: (vu.append(s.un("SELECT COUNT(*) FROM garanties")[0]), boum()))
        self.assertEqual(vu, [3])                                                           # les garanties existaient dans la transaction, puis ont disparu

    def test_T50_O13_defaut_apres_l_ecriture_des_caches_rollback_des_caches_aussi(self):
        t, m = self.neuf()
        rel0 = t.releve(m.b)["bc"]
        vu = []
        t.echoue(m, DefautInjecte, True, apres_caches=lambda s, ctx: (vu.append(s.releve(m.b)["bc"]), boum()))
        self.assertNotEqual(vu[0], rel0)                                                    # les caches avaient bien été écrits
        self.assertEqual(t.releve(m.b)["bc"], rel0)

    def test_T50_O13_defaut_juste_avant_le_COMMIT_rollback_integral(self):
        t, m = self.neuf()
        vu = []
        t.echoue(m, DefautInjecte, True, avant_commit=lambda s, ctx: (vu.append((s.db.in_transaction, s.un("SELECT COUNT(*) FROM garanties")[0])), boum()))
        self.assertEqual(vu, [(True, 3)])

    def test_T50_O13_la_post_condition_s_execute_apres_les_INSERT_une_garantie_supprimee_apres_coup_est_vue(self):
        t, m = self.neuf("temoin")
        t.db.execute("DROP TRIGGER tr_50_garanties_no_delete")
        exc = t.echoue(m, PostConditionGaranties, True, apres_insert=lambda s, ctx: s.db.execute("DELETE FROM garanties WHERE id=(SELECT MIN(id) FROM garanties)"))
        self.assertEqual(exc.codes, {"C1"})

    def test_T50_O13_la_post_condition_s_execute_apres_les_caches_un_surplus_ajoute_apres_coup_est_vu(self):
        t, m = self.neuf("temoin")
        ajout = lambda s, ctx: s.garantie_g(m.lignes[1], "decennale", ctx.s)
        exc = t.echoue(m, PostConditionGaranties, True, apres_caches=ajout)
        self.assertEqual(exc.codes, {"C2"})

    def test_T50_O13_le_commit_n_est_atteint_que_si_les_huit_controles_passent(self):
        t, m = self.neuf()
        atteint = []
        with self.assertRaises(PostConditionGaranties):
            t.declencher(m, defaut=sans(0), avant_commit=lambda s, ctx: atteint.append(1))
        self.assertEqual(atteint, [])
        t.declencher(m, avant_commit=lambda s, ctx: atteint.append(1))
        self.assertEqual(atteint, [1])

    # ---- les contrôles C1 à C8 pris isolément ------------------------------------------------------------------------------------------------
    def reussi(self, base="temoin"):
        t, m = self.neuf(base)
        r_ = t.declencher(m)
        for nom in ("tr_50_garanties_update", "tr_50_garanties_no_delete"):
            t.db.execute(f"DROP TRIGGER IF EXISTS {nom}")
        return t, m, r_

    def test_T50_O_controles_une_base_conforme_passe_C1_a_C8_en_PREMIER_et_en_REJEU(self):
        t, m, r_ = self.reussi()
        P = t.perimetre(m.b)
        self.assertEqual(t.controles(m.b, r_.R, "PREMIER", 3, []), [])
        self.assertEqual(t.controles(m.b, r_.R, "REJEU", 0, P), [])

    def test_T50_O_controle_C1_paire_absente_ou_en_double_est_detectee(self):
        t, m, r_ = self.reussi()
        t.db.execute("DELETE FROM garanties WHERE id=(SELECT MIN(id) FROM garanties)")
        self.assertEqual({v[0] for v in t.controles(m.b, r_.R, "REJEU", None, None)}, {"C1"})

    def test_T50_O_controle_C7_PREMIER_nombre_insere_different_de_E(self):
        t, m, r_ = self.reussi()
        self.assertEqual(t.controles(m.b, r_.R, "PREMIER", 2, []), [("C7", 2, 3)])
        self.assertEqual(t.controles(m.b, r_.R, "PREMIER", 4, []), [("C7", 4, 3)])

    def test_T50_O_controle_C7_REJEU_insertion_non_nulle_ou_perimetre_modifie(self):
        t, m, r_ = self.reussi()
        P = t.perimetre(m.b)
        self.assertEqual(t.controles(m.b, r_.R, "REJEU", 1, P), [("C7", 1, 0)])
        self.assertEqual(t.controles(m.b, r_.R, "REJEU", 0, P[:-1]), [("C7", 0, 0)])
        self.assertEqual(t.controles(m.b, r_.R, "REJEU", 0, []), [("C7", 0, 0)])

    def test_T50_O_controle_C8_s_appuie_sur_l_etat_releve_avant_les_insertions_pas_sur_l_etat_au_COMMIT(self):
        t, m, r_ = self.reussi()
        self.assertEqual(len(t.perimetre(m.b)), 3)                                         # au COMMIT la table n'est pas vide : c'est normal en PREMIER
        self.assertEqual(t.controles(m.b, r_.R, "PREMIER", 3, []), [])                    # relevé « avant » vide : C8 satisfait
        self.assertEqual(t.controles(m.b, r_.R, "PREMIER", 3, t.perimetre(m.b)), [("C8", 3)])           # relevé « avant » non vide : C8 violé
        self.assertEqual(t.controles(m.b, r_.R, "REJEU", 0, t.perimetre(m.b)), [])         # en REJEU un historique préexistant est attendu

    def test_T50_O_PREMIER_et_REJEU_sont_decides_par_l_existence_d_un_solde_anterieur(self):
        t, m = self.neuf()
        r1 = t.declencher(m, "2026-10-05")
        self.assertEqual(r1.mode, "PREMIER")
        t.neutraliser(r1.solde)
        t.recalcul_financier(m)
        self.assertEqual(t.declencher(m, "2026-10-20").mode, "REJEU")                       # le solde antérieur est neutralisé : il reste « le premier solde »


if __name__ == "__main__":
    unittest.main()
