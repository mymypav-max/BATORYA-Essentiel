#!/usr/bin/env python3
"""Preuves d'équivalence des 24 mutants survivants (S01-S24) de la campagne complète 009 (mut009b.py), LIÉES au texte réel de 009_pv.sql.

Usage : python3 -B preuves_equivalence_009.py [RACINE_DU_DEPOT]      (RACINE_DU_DEPOT contient src-tauri/ ; défaut : remonte depuis ce fichier)

Principe (ce qui distingue ce script d'un script qui retape les expressions) :
  1. REGISTRE : chaque survivant est une substitution textuelle (ancien -> nouveau) appliquée au fichier 009_pv.sql LU DANS LE DÉPÔT. Si l'ancien texte n'y figure
     pas exactement une fois, le script ÉCHOUE : une preuve ne peut pas survivre à une modification du SQL qu'elle prétend couvrir.
  2. MUTANT RÉEL : le SQL muté est appliqué par le moteur sur la chaîne 001 -> 008 (le mutant doit être valide, sinon il serait « invalide », pas « survivant »).
  3. PRÉDICATS EXTRAITS DU DDL : les CHECK comparés sont lus dans sqlite_master (DDL réellement créé, original et muté) ; les triggers sont exécutés tels que créés ;
     aucune expression de 009 n'est retapée ici. Les formats de printf sont lus dans le texte du trigger.
  4. DOMAINES : énumérations exhaustives du domaine pertinent (jours juliens, alphabets x années, états de 0 à 3 PV x tentatives de levée, 99 levées successives,
     entiers) ; le moteur SQLite réel évalue l'original et le mutant sur chaque point ; toute divergence fait échouer.
  5. TÉMOINS : pour chaque famille, un mutant NON équivalent, obtenu par substitution textuelle sur le même fichier, DOIT diverger (preuve que la comparaison n'est pas vide).
Ce que ce script ne démontre pas : (a) que S01-S24 sont les seuls survivants d'une campagne (il faut l'outil de mutation ; ce script ne remplace pas la campagne) ; (b) l'équivalence pour un autre moteur que
celui qui l'exécute (la version SQLite est affichée) ; (c) l'équivalence hors du schéma tel que lu (les preuves E1, E3, E5, E6 sont relatives aux CHECK/NOT NULL conservés)."""
import hashlib, importlib.util, itertools, pathlib, re, sqlite3, sys, time

sys.dont_write_bytecode = True
RACINE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RACINE / "src-tauri/tests/metier"))
spec = importlib.util.spec_from_file_location("t9_preuves", RACINE / "src-tauri/tests/metier/test_009_pv.py")
T9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T9)
SQL = T9.SQL_009
OK = True
T0 = time.time()


def check(titre, cond):
    global OK
    print(("OK   " if cond else "ECHEC"), titre, flush=True)
    OK &= bool(cond)


def une_fois(sql, ancien):
    n = sql.count(ancien)
    if n != 1:
        raise SystemExit(f"ECHEC registre : {ancien!r} figure {n} fois dans 009_pv.sql (attendu : 1) - la preuve ne correspond plus au SQL du dépôt")
    return ancien


def muter(sql, ancien, nouveau):
    return sql.replace(une_fois(sql, ancien), nouveau, 1)


# ------------------------------------------------------------------------------------------------------------------ REGISTRE
m_date = re.search(r"date_reception GLOB ('(?:\[0-9\]|-)+')", SQL)
m_num = re.search(r"numero GLOB ('PVR-(?:\[0-9\]|-)+')", SQL)
assert m_date and m_num and len(re.findall(r"date_reception GLOB '", SQL)) == 1 and len(re.findall(r"numero GLOB '", SQL)) == 1
LIT_DATE, LIT_NUM = m_date.group(1), m_num.group(1)
TOK_D = re.findall(r"\[0-9\]|-", LIT_DATE[1:-1])
TOK_N = re.findall(r"\[0-9\]|-", LIT_NUM[5:-1])                     # après 'PVR-'
assert len(TOK_D) == 10 and len(TOK_N) == 8
glob_date = lambda lit: f"date_reception GLOB {lit}"
glob_num = lambda lit: f"numero GLOB {lit}"
variante = lambda tok, i, pre="": "'" + pre + "".join(tok[:i]) + "?" + "".join(tok[i + 1:]) + "'"
G1 = "FROM pv o WHERE o.id = NEW.origine_pv_id AND o.type = 'reception_avec_reserves'"
G2 = "FROM pv o WHERE o.id = NEW.origine_pv_id AND o.bc_id IS NEW.bc_id"
G4 = "FROM pv o WHERE o.id = NEW.origine_pv_id AND NEW.numero = o.numero"
REGISTRE = [("S01", "E2", "substr(numero, 11, 2) = substr(date_reception, 3, 2)", "substr(numero, 11, 3) = substr(date_reception, 3, 2)")]
for sid, i in zip(("S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09"), (0, 1, 2, 3, 5, 6, 8, 9)):
    REGISTRE.append((sid, "E1", glob_date(LIT_DATE), glob_date(variante(TOK_D, i))))
REGISTRE.append(("S10", "E1", glob_date(LIT_DATE), glob_date(LIT_DATE[:-1] + "*'")))
REGISTRE.append(("S11", "E3", glob_num(LIT_NUM), glob_num(variante(TOK_N, 6, "PVR-"))))
REGISTRE.append(("S12", "E3", glob_num(LIT_NUM), glob_num(variante(TOK_N, 7, "PVR-"))))
REGISTRE.append(("S13", "E4", "printf('%02d', NEW.suffixe)", "printf('%02i', NEW.suffixe)"))
REGISTRE.append(("S14", "E5", G1, G1.replace("FROM pv o ", "FROM pv o, pv x ")))
REGISTRE.append(("S15", "E5", G2, G2.replace("FROM pv o ", "FROM pv o, pv x ")))
REGISTRE.append(("S16", "E5", G4, G4.replace("FROM pv o ", "FROM pv o, pv x ")))
REGISTRE.append(("S17", "E6", "o.bc_id IS NEW.bc_id", "o.bc_id = NEW.bc_id"))
REGISTRE.append(("S18", "E7", "BEFORE UPDATE ON pv\nBEGIN", "BEFORE UPDATE ON pv\nFOR EACH ROW\nBEGIN"))
REGISTRE.append(("S19", "E7", "BEFORE DELETE ON pv\nBEGIN", "BEFORE DELETE ON pv\nFOR EACH ROW\nBEGIN"))
m_ts = re.search(r"created_at GLOB\s*('(?:\[0-9\]|[-T:.Z])+')", SQL)
assert m_ts
LIT_TS = m_ts.group(1)
REGISTRE.append(("S20", "E8", "CHECK (legacy_data IS NULL OR (", "CHECK (0 OR ("))
REGISTRE.append(("S21", "E8", "CHECK (legacy_data IS NULL OR (", "CHECK ( 0  OR ("))
REGISTRE.append(("S22", "E9", glob_num(LIT_NUM), glob_num(LIT_NUM[:-1] + "*'")))
REGISTRE.append(("S23", "E9", LIT_TS, LIT_TS[:-1] + "*'"))
REGISTRE.append(("S24", "E9", LIT_TS, "'*" + LIT_TS[1:]))
assert len(REGISTRE) == 24
# Mutants TUÉS, mais seulement par le test témoin de texte (passe de contrôle « sans groupe A ni témoin K ») : qualifiés ici au même titre que les survivants.
JSON_COLS = ("client_snapshot", "entreprise_snapshot", "chantier_snapshot", "legacy_data")
REGISTRE_KT = []
for _col, _n in (("numero", 12), ("created_at", 24)):
    REGISTRE_KT.append((f"K{len(REGISTRE_KT) + 1:02d}", "E9", f"length(CAST({_col} AS BLOB)) = {_n}", f"length(CAST({_col} AS BLOB)) <= {_n}"))
for _col in JSON_COLS:
    for _nouveau in (f"instr({_col}, x'00') = 0", f"instr(CAST({_col} AS TEXT), x'00') = 0", f"instr(({_col}), x'00') = 0"):
        REGISTRE_KT.append((f"K{len(REGISTRE_KT) + 1:02d}", "E10", f"instr(CAST({_col} AS BLOB), x'00') = 0", _nouveau))
assert len(REGISTRE_KT) == 14
LEN_NUM, LEN_TS = "length(CAST(numero AS BLOB)) = 12", "length(CAST(created_at AS BLOB)) = 24"
# témoins NON équivalents (même mécanisme : substitution textuelle sur le SQL du dépôt)
TEMOINS = {
    "E1": ("W1 : suppression de `date(date_reception) IS date_reception`", "AND date(date_reception) IS date_reception", ""),
    "E2": ("W2 : décalage de position `substr(numero, 10, 2)`", "substr(numero, 11, 2) = substr(date_reception, 3, 2)", "substr(numero, 10, 2) = substr(date_reception, 3, 2)"),
    "E3": ("W3 : `?` sur yy ET suppression de l'égalité avec l'année", None, None),
    "E4": ("W4 : `printf('%d', ...)`", "printf('%02d', NEW.suffixe)", "printf('%d', NEW.suffixe)"),
    "E5": ("W5 : jointure avec une table vide (`import_anomalies x`)", G1, G1.replace("FROM pv o ", "FROM pv o, import_anomalies x ")),
    "E6": ("W6 : `IS NOT` à la place de `IS`", "o.bc_id IS NEW.bc_id", "o.bc_id IS NOT NEW.bc_id"),
    "E8": ("W8 : `legacy_data IS NULL` remplacé par `1` (accepte tout JSON invalide)", "CHECK (legacy_data IS NULL OR (", "CHECK (1 OR ("),
    "E9": ("W9 : `*` en queue du GLOB du numéro ET suppression du contrôle d'octets (queues acceptées)", None, None),
    "E9b": ("W9b : `length(CAST(numero AS BLOB)) >= 12` (accepte les queues après NUL)", LEN_NUM, "length(CAST(numero AS BLOB)) >= 12"),
    "E10": ("W10 : `instr(CAST(client_snapshot AS BLOB), x'01') = 0` (ne cherche plus le NUL)", "instr(CAST(client_snapshot AS BLOB), x'00') = 0", "instr(CAST(client_snapshot AS BLOB), x'01') = 0"),
    "E7": ("W7 : trigger limité à `UPDATE OF observations`", "BEFORE UPDATE ON pv\nBEGIN", "BEFORE UPDATE OF observations ON pv\nBEGIN"),
}


# ------------------------------------------------------------------------------------------------------------------ OUTILS
def monde(sql_009):
    """Chaîne 001 -> 008 puis le SQL de 009 fourni, comme le runner ; deux BC de test."""
    db = T9.G.migrer11()
    T9.T.appliquer(db, T9.RANG, sql_009)
    t = T9.Mini12._sur(db)
    t.b1, t.b2 = t.bc().b, t.bc().b
    return t


def ddl_pv(t):
    s = t.db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='pv'").fetchone()[0]
    return re.sub(r"--[^\n]*", "", s)


def checks_du_ddl(t):
    """Expressions des CHECK (colonne et table) lues dans le DDL créé par le moteur (parenthèses équilibrées, littéraux respectés)."""
    s, out = ddl_pv(t), []
    for m in re.finditer(r"\bCHECK\s*\(", s):
        i, prof, q = m.end(), 1, None
        while prof:
            c = s[i]
            if q:
                q = None if c == q else q
            elif c in "'\"":
                q = c
            elif c == "(":
                prof += 1
            elif c == ")":
                prof -= 1
            i += 1
        out.append(s[m.end():i - 1].strip())
    return out


def le_check(t, cle):
    r = [c for c in checks_du_ddl(t) if cle in c]
    assert len(r) == 1, (cle, len(r))
    return r[0]


def trigger_sql(t, nom):
    return t.db.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (nom,)).fetchone()[0]


def differe(a, b):
    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))


# ------------------------------------------------------------------------------------------------------------------ DOMAINES
J = "WITH RECURSIVE j(n) AS (SELECT 0 UNION ALL SELECT n + 1 FROM j WHERE n < 5373484), t(date_reception) AS (SELECT date(n) FROM j) "
CANDIDATS_DATE = ["2026-10-20", "2026-1-20", "2026-10-2", "a026-10-20", "2026-10-20x", "x2026-10-20", "2026-10-20\0", "2026-10-20\0z", "2026-13-01", "20261020", "2026/10/20", "",
                  "2026-10-20 ", " 2026-10-20", "2026-10-200", "-4713-11-24", "0000-01-01", "9999-12-31"]


def _variantes(base, alphabet, tails):
    """base conforme ; substitutions d'un ou deux caractères (positions toutes), troncatures + queues : 12/24 octets conformes et leurs voisins hors format."""
    out = {base}
    n = len(base)
    for i in range(n):
        for a in alphabet:
            out.add(base[:i] + a + base[i + 1:])
    for i, j in itertools.combinations(range(n), 2):
        for a in alphabet:
            for b in alphabet:
                out.add(base[:i] + a + base[i + 1:j] + b + base[j + 1:])
    for k in range(n + 1):
        for r in range(0, 5):
            for t in itertools.product(tails, repeat=r):
                out.add(base[:k] + "".join(t))
        for t in itertools.product(tails, repeat=min(3, n - k + 1)):
            out.add(base[:k] + "".join(t) + base[k + len(t):] if k + len(t) <= n else base[:k] + "".join(t))
    return sorted(out)


ALPHA_E9 = ["0", "x", "-", "\0", "\u00e9", "*"]
TAILS_E9 = ["x", "\0", "0", "\u00e9"]


def e8(to, tm):
    eo, em = le_check(to, "json_valid(legacy_data)"), le_check(tm, "json_valid(legacy_data)")
    dom = [None, "", "null", "{}", "[]", '{"a":1}', '{"k":"v\\u0000w"}', "{", "x", '{"a":1}\0', "\0", '{"a":1}\0{', " ", "1", "true", '"\\u0000"', "\0{}", "{}\0", "é", '{"é":"\0"}']
    pas = lambda e: f"(({e}) IS NOT 0)"
    n, dv = 0, 0
    for v in dom:
        a, b = to.db.execute(f"SELECT {pas(eo)}, {pas(em)} FROM (SELECT ? AS legacy_data)", (v,)).fetchone()
        n += 1
        dv += a != b
    vo = to.db.execute(f"SELECT ({eo}) FROM (SELECT NULL AS legacy_data)").fetchone()[0]
    vm = tm.db.execute(f"SELECT ({em}) FROM (SELECT NULL AS legacy_data)").fetchone()[0]
    return n, f"sur NULL : valeur du CHECK original = {vo!r}, mutant = {vm!r} (NULL ne fait pas échouer un CHECK)", dv + (vo == 0) + (vm == 0)


def e10(to, tm, col):
    eo, em = le_check(to, f"json_valid({col})"), le_check(tm, f"json_valid({col})")
    dom = [None, "", "{}", "[]", '{"a":1}', '{"k":"v\\u0000w"}', "{", "x", '{"a":1}\0', "\0", '{"a":1}\0{', "\0{}", "{}\0", "{}\0\0", '{"a":"\0"}', '{"\0":1}', '"\0"', "\x01", '{"a":"\x01"}',
           '{"é":"\0"}', "é\0", '{"a":1}' + "\0" * 5, "\0" * 5 + '{"a":1}', '[1,2,3]\0[4]', "null", "true", "1\0", '"\\u0000"']
    dom += [d[:i] + "\0" + d[i:] for d in ('{"a":1}', '{"k":"vw"}', "[1,2]", '"abc"') for i in range(len(d) + 1)]
    n = dv = acc = 0
    for v in dom:
        a, b = to.db.execute(f"SELECT (({eo}) IS NOT 0), (({em}) IS NOT 0) FROM (SELECT ? AS {col})", (v,)).fetchone()
        n += 1; dv += a != b; acc += a
    return n, acc, dv


def e9(to, tm, famille_col):
    col, lit_len = ("numero", LEN_NUM) if famille_col == "numero" else ("created_at", LEN_TS)
    eo, em = le_check(to, f"{col} GLOB"), le_check(tm, f"{col} GLOB")
    if lit_len not in eo:                                                   # prémisse de E9 : le contrôle d'octets doit être dans le CHECK réel
        raise SystemExit(f"ECHEC prémisse E9 : le CHECK de {col} ne contient plus `{lit_len}` - la preuve E9 ne s'applique plus")
    if col == "numero":
        base = "PVR-12345-26"
        doms = [(v, d) for v in _variantes(base, ALPHA_E9, TAILS_E9) for d in ("2026-06-15", "2031-01-01")]
        src = "(SELECT ? AS numero, ? AS date_reception, ? AS origine, ? AS type)"
        combos = [("v6", "reception_sans_reserves"), ("v6", "reception_avec_reserves"), ("import", "reception_sans_reserves")]
        n = dv = acc = 0
        for (v, d) in doms:
            for (o_, t_) in combos:
                a, b = to.db.execute(f"SELECT ({eo}) IS NOT ({em}), ({eo}) FROM (SELECT ? AS numero, ? AS date_reception, ? AS origine, ? AS type)", (v, d, o_, t_)).fetchone()
                n += 1; dv += a; acc += (to.db.execute(f"SELECT ({eo}) FROM {src}", (v, d, o_, t_)).fetchone()[0] == 1)
    else:
        base = "2026-10-20T14:30:15.123Z"
        n = dv = acc = 0
        for v in _variantes(base, ALPHA_E9, TAILS_E9):
            a, b = to.db.execute(f"SELECT ({eo}) IS NOT ({em}), ({eo}) FROM (SELECT ? AS created_at)", (v,)).fetchone()
            n += 1; dv += a; acc += (b == 1)
    return n, acc, dv


def e1(to, tm):
    eo, em = le_check(to, "date_reception GLOB"), le_check(tm, "date_reception GLOB")
    if "date(date_reception) IS date_reception" not in eo:                      # la prémisse de E1 doit être dans le CHECK réel
        raise SystemExit("ECHEC prémisse E1 : le CHECK de date_reception ne contient plus `date(date_reception) IS date_reception` - la preuve E1 ne s'applique plus")
    n, acc, dv = to.db.execute(J + f"SELECT COUNT(*), SUM({eo}), SUM(({eo}) IS NOT ({em})) FROM t").fetchone()
    cd = sum(to.db.execute(f"SELECT ({eo}) IS NOT ({em}) FROM (SELECT ? AS date_reception)", (x,)).fetchone()[0] for x in CANDIDATS_DATE)
    return n, acc, dv + cd


NUMS = ["PVR-%05d-%02d" % (n, y) for n in (0, 1, 12345, 99999) for y in range(100)]
TAILS = ["", "\0", "\0x", "\0abc", "\0\0", "\0é"]
ALPHA = list("0123456789abcxyzXYZ -.%/é\0")


def charger_domaines(db):
    db.execute("CREATE TEMP TABLE d_num (numero TEXT, date_reception TEXT, origine TEXT, type TEXT)")
    dates = [("%d-06-15" % y if y >= 1000 else "%04d-06-15" % y) for y in range(2000, 2100)]
    db.executemany("INSERT INTO d_num SELECT ?, ?, 'v6', 'reception_sans_reserves'", [(n + t, d) for n in NUMS for t in TAILS for d in dates])
    db.execute("CREATE TEMP TABLE ann (date_reception TEXT)")
    db.executemany("INSERT INTO ann VALUES (?)", [("%04d-01-01" % y,) for y in range(10000)])
    db.execute("CREATE TEMP TABLE cc (c TEXT)")
    db.executemany("INSERT INTO cc VALUES (?)", [(c,) for c in ALPHA])


def e2(to, tm):
    ed, en_o, en_m = le_check(to, "date_reception GLOB"), le_check(to, "numero GLOB"), le_check(tm, "numero GLOB")
    return to.db.execute(f"SELECT COUNT(*), SUM(({ed}) AND ({en_o})), SUM((({ed}) AND ({en_o})) IS NOT (({ed}) AND ({en_m}))) FROM d_num").fetchone()


def e3(to, tm):
    ed, en_o, en_m = le_check(to, "date_reception GLOB"), le_check(to, "numero GLOB"), le_check(tm, "numero GLOB")
    src = "(SELECT 'PVR-50001-' || a.c || b.c AS numero, ann.date_reception, 'v6' AS origine, 'reception_sans_reserves' AS type FROM cc a, cc b, ann)"
    return to.db.execute(f"SELECT COUNT(*), SUM(({ed}) AND ({en_o})), SUM((({ed}) AND ({en_o})) IS NOT (({ed}) AND ({en_m}))) FROM {src}").fetchone()


def formats_printf(t):
    return re.findall(r"printf\('([^']*)'", trigger_sql(t, "tr_41_pv_insert"))


# --- états de 0 à 3 PV et tentatives de levée, exécutés par les triggers réels --------------------------------------------------------------
KINDS = ("AR1", "SR1", "AR2", "SR2", "LV")


def construire(t, etat):
    ids, res = [], []
    for k in etat:
        try:
            if k == "LV":
                p = next((i for i, kk in zip(ids, etat) if kk == "AR1"), None)
                if p is None:
                    return None
                ids.append(t.levee(p))
            else:
                ids.append(t.pv(t.b1 if k.endswith("1") else t.b2, T9.AR if k.startswith("AR") else T9.SR))
        except sqlite3.IntegrityError as e:
            res.append(str(e))
            return None
    return ids


def tentatives(t, ids):
    out = []
    numeros = {i: t.un("SELECT numero FROM pv WHERE id=?", i)[0] for i in ids}
    for parent in list(ids) + [999, None]:
        for bc in (t.b1, t.b2, None):
            for suf in (1, 2, None):
                bon = "%s-%02d" % (numeros.get(parent, "PVR-99999-26"), suf or 0)
                for num in (bon, "ZZZ"):
                    cols = t.cols_pv(t.b1, T9.LV, numero=num, origine_pv_id=parent, suffixe=suf, bc_id=bc)
                    out.append(t.sous_savepoint(lambda: t.inserer_pv(cols)))
    return out


def parcours_etats(t):
    res = []
    for k in range(4):
        for etat in itertools.product(KINDS, repeat=k):
            t.db.execute("SAVEPOINT etat")
            ids = construire(t, etat)
            res.append((etat, None if ids is None else tentatives(t, ids)))
            t.db.execute("ROLLBACK TO etat")
            t.db.execute("RELEASE etat")
    return res


def parcours_levees_successives(t):
    """99 levées successives sur une origine : suffixes 1 a 100, numéro conforme et numéro mal formé à chaque pas (atteint G4 avec tout suffixe accessible)."""
    res = []
    t.db.execute("SAVEPOINT succ")
    o = t.pv(t.b1, T9.AR)
    num = t.un("SELECT numero FROM pv WHERE id=?", o)[0]
    for k in range(1, 101):
        for n in ("%s-%02d" % (num, k), "%s-%d" % (num, k), "%s-%03d" % (num, k)):
            cols = t.cols_pv(t.b1, T9.LV, numero=n, origine_pv_id=o, suffixe=k)
            res.append(t.sous_savepoint(lambda: t.inserer_pv(cols)))
        if k <= 99:
            try:
                t.levee(o)
            except sqlite3.IntegrityError as e:                  # un mutant non équivalent peut refuser la levée conforme : la divergence est alors enregistrée
                res.append(str(e))
                break
    t.db.execute("ROLLBACK TO succ")
    t.db.execute("RELEASE succ")
    return res


def parcours_immuabilite(t):
    res = []
    etats = ((), ("AR1",), ("AR1", "SR1", "LV"))
    for etat in etats:
        t.db.execute("SAVEPOINT imm")
        ids = construire(t, etat)
        cibles = ("", " WHERE id = %d" % (ids[0] if ids else 1), " WHERE id = 99999")
        for col, expr in T9.VALEURS_UPDATE.items():
            for cible in cibles:
                for verbe in ("UPDATE", "UPDATE OR IGNORE", "UPDATE OR REPLACE"):
                    for e in (expr, col):
                        res.append(t.sous_savepoint(lambda: t.db.execute(f"{verbe} pv SET {col} = {e}{cible}")))
        for cible in cibles:
            res.append(t.sous_savepoint(lambda: t.db.execute(f"DELETE FROM pv{cible}")))
            res.append(t.sous_savepoint(lambda: t.db.execute(f"INSERT OR REPLACE INTO pv (id, numero, bc_id, type, date_reception, client_snapshot, client_snapshot_version, "
                                                           f"entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version) "
                                                           f"SELECT id, numero, bc_id, type, date_reception, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                                                           f"entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version FROM pv{cible}")))
        res.append(t.un("SELECT COUNT(*) FROM pv")[0])
        t.db.execute("ROLLBACK TO imm")
        t.db.execute("RELEASE imm")
    return res


# ------------------------------------------------------------------------------------------------------------------ EXÉCUTION
print(f"Dépôt : {RACINE}\n009_pv.sql sha256 = {hashlib.sha256(SQL.encode('utf-8')).hexdigest()}\nSQLite {sqlite3.sqlite_version} | Python {sys.version.split()[0]}\n")
for _sid, _fam, _a, _n in REGISTRE + REGISTRE_KT:                                  # contrôle de fraîcheur AVANT tout calcul : chaque ancre doit exister une fois dans le SQL du dépôt
    une_fois(SQL, _a)
check(f"registre : les {len(REGISTRE)} + {len(REGISTRE_KT)} ancres de S01-S{len(REGISTRE):02d} et K01-K{len(REGISTRE_KT):02d} figurent chacune exactement une fois dans 009_pv.sql", True)
ORIG = monde(SQL)
charger_domaines(ORIG.db)
CACHE = {"etats": parcours_etats(ORIG), "succ": parcours_levees_successives(ORIG), "imm": parcours_immuabilite(ORIG)}
check(f"base : les tentatives de référence produisent des refus ET des acceptations ({len(CACHE['etats'])} états, {sum(len(r) for _, r in CACHE['etats'] if r)} tentatives)",
      any(x is None for _, r in CACHE["etats"] if r for x in r) and any(x is not None for _, r in CACHE["etats"] if r for x in r))
check("base : immuabilité de référence : toute tentative d'UPDATE/DELETE sur un PV existant est refusée par INV-96/INV-06",
      any(isinstance(x, str) and ("INV-96" in x or "INV-06" in x) for x in CACHE["imm"]))
print()


def evaluer(sid, famille, ancien, nouveau, temoin=False):
    sql_m = muter(SQL, ancien, nouveau) if ancien is not None else None
    tm = monde(sql_m)                                              # le mutant doit être valide
    if famille == "E1":
        n, acc, dv = e1(ORIG, tm)
        return f"{n} points (image de date()), {acc} acceptés par l'original", dv
    if famille == "E2":
        n, acc, dv = e2(ORIG, tm)
        return f"{n} (numéro, date) dont {acc} acceptés", dv
    if famille == "E3":
        n, acc, dv = e3(ORIG, tm)
        return f"{n} (numéro, date) dont {acc} acceptés", dv
    if famille == "E4":
        fo, fm = formats_printf(ORIG), formats_printf(tm)
        q = ("WITH RECURSIVE s(n) AS (SELECT -1000 UNION ALL SELECT n + 1 FROM s WHERE n < 100000) SELECT COUNT(*), SUM(printf(?, n) IS NOT printf(?, n)) FROM s")
        n, dv = ORIG.db.execute(q, (fo[0], fm[0])).fetchone()
        dv += differe(CACHE["succ"], parcours_levees_successives(tm))
        return f"{n} entiers (format lu dans le trigger : {fo[0]!r} / {fm[0]!r}) + {len(CACHE['succ'])} tentatives de levée successives", dv
    if famille in ("E5", "E6"):
        r = parcours_etats(tm)
        return f"{len(r)} états de 0 à 3 PV, {sum(len(x) for _, x in r if x)} tentatives", sum(a != b for a, b in zip(CACHE["etats"], r)) + abs(len(r) - len(CACHE["etats"]))
    if famille == "E8":
        n, txt, dv = e8(ORIG, tm)
        return f"{n} valeurs de legacy_data (NULL, JSON valide, invalide, NUL brut, \\u0000) ; {txt}", dv
    if famille == "E10":
        col = next(c for c in JSON_COLS if c in ancien)
        n, acc, dv = e10(ORIG, tm, col)
        return f"{n} valeurs de {col} (NULL, JSON valide/invalide, NUL brut en toute position, \\u0000, 0x01, multi-octets) dont {acc} acceptées", dv
    if famille == "E9":
        col = "numero" if "numero" in ancien else "created_at"
        n, acc, dv = e9(ORIG, tm, col)
        return f"{n} évaluations du CHECK de {col} (substitutions d'1 à 2 caractères, troncatures, queues avec NUL, caractère multi-octets{', branche import comprise' if col == 'numero' else ''}) dont {acc} acceptées", dv
    if famille == "E7":
        r = parcours_immuabilite(tm)
        return f"{len(r)} tentatives d'UPDATE/DELETE/REPLACE", differe(CACHE["imm"], r)


for sid, famille, ancien, nouveau in REGISTRE:
    detail, dv = evaluer(sid, famille, ancien, nouveau)
    check(f"{sid} ({famille}) mutant valide, ancre unique ; {detail} ; divergences = {dv}", dv == 0)
print("\nMutants tués seulement par le test témoin de texte (passe de contrôle), qualifiés comme les survivants :")
for sid, famille, ancien, nouveau in REGISTRE_KT:
    detail, dv = evaluer(sid, famille, ancien, nouveau)
    check(f"{sid} ({famille}) mutant valide, ancre unique ; {detail} ; divergences = {dv}", dv == 0)
print()
for famille, (nom, ancien, nouveau) in TEMOINS.items():
    if famille == "E3":
        sql_m = muter(muter(SQL, glob_num(LIT_NUM), glob_num(variante(TOK_N, 6, "PVR-"))), "substr(numero, 11, 2) = substr(date_reception, 3, 2)", "1 = 1")
        tm = monde(sql_m)
        dv = e3(ORIG, tm)[2]
    elif famille == "E9":
        sql_m = muter(muter(SQL, glob_num(LIT_NUM), glob_num(LIT_NUM[:-1] + "*'")), "AND " + LEN_NUM, "")
        tm = monde(sql_m)
        dv = e9(ORIG, tm, "numero")[2]
    else:
        detail, dv = evaluer("W", famille[:3] if famille.startswith("E10") else famille[:2], ancien, nouveau, temoin=True)
    check(f"TÉMOIN {famille} {nom} : divergences = {dv} (doit être > 0)", dv > 0)
print(f"\nDurée : {time.time() - T0:.0f} s")
print("TOUT EST OK" if OK else "ECHEC")
raise SystemExit(0 if OK else 1)
