"""Classe par famille les 797 mutants de la campagne 009 (tués / invalides / survivants) à partir des sorties brutes enregistrées.
Usage : python3 -B classify009b.py RACINE_DEPOT [DOSSIER_SORTIES_CAMPAGNE]
  RACINE_DEPOT : dossier contenant src-tauri/ ; DOSSIER_SORTIES_CAMPAGNE (défaut : ../../sorties_brutes/campagne_complete/) :
  tueurs_campagne_complete.json, survivants_campagne_complete.txt, invalides_campagne_complete.txt.
Reproduit sorties_brutes/campagne_complete/classification_familles.txt."""
import sys, re, json, collections, pathlib
sys.dont_write_bytecode = True
ICI = pathlib.Path(__file__).resolve().parent
if len(sys.argv) not in (2, 3):
    sys.exit("usage : classify009b.py RACINE_DEPOT [DOSSIER_SORTIES_CAMPAGNE]")
RACINE = pathlib.Path(sys.argv[1]).resolve()
SORT = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else ICI.parent.parent / "sorties_brutes" / "campagne_complete"
sys.path.insert(0, str(ICI))
import genmut009b as genmut009
m = genmut009.charger(root=str(RACINE), workd=str(ICI / "_inexistant_"))
kill = json.load(open(SORT / "tueurs_campagne_complete.json", encoding="utf-8"))
surv = [l[4:].rstrip() for l in open(SORT / "survivants_campagne_complete.txt", encoding="utf-8") if l.startswith("### ")]
inval = [l[4:].rstrip() for l in open(SORT / "invalides_campagne_complete.txt", encoding="utf-8") if l.startswith("### ")]
names = list(m)
assert len(kill) + len(surv) + len(inval) == len(names), (len(kill), len(surv), len(inval))
def fam(n):
    if re.match(r"(nul_|cast_)", n): return "CHECK / contrôles d'octets (longueur, NUL) et CAST"
    if n.startswith("tr_40"): return "Trigger tr_40 (immuabilité) — toutes opérations"
    if n.startswith("tr_41"):
        rest = n.split(" ", 1)[1]
        if re.match(r"(msg_|raise_|stmt_)", rest): return "Trigger tr_41 / RAISE, messages, instructions (suppression, permutation)"
        if re.match(r"(R\d|g3_|max_|plus1|sep|printf|new_col|alias|is_to_eq|when_|coalesce|col#)", rest): return "Trigger tr_41 / WHEN et gardes G1–G4 (conjoncts, opérateurs, littéraux, colonnes, EXISTS, MAX+1, printf)"
        return "Trigger tr_41 / forme, événement, table cible"
    if n.startswith("drop_trigger"): return "Suppression d'un trigger"
    if re.match(r"(drop_index|index_)", n): return "Index (suppression, colonne remplacée, unicité)"
    if re.match(r"(not_null|not_null_add|default|strict_off|autoinc|coltype_swap|in_minus|in_plus|unique|table_unique|fk_)", n): return "Table / colonnes, types, listes IN, NOT NULL, DEFAULT, STRICT, AUTOINCREMENT, FK, UNIQUE"
    return "Table / CHECK (arbre AND/OR, opérateurs, GLOB, littéraux, substr, between, json_valid, date())"
tot = collections.defaultdict(lambda: [0, 0, 0, 0])
for n in names:
    f = fam(n); tot[f][0] += 1
    if n in kill: tot[f][1] += 1
    elif n in surv: tot[f][3] += 1
    else: tot[f][2] += 1
for f, v in sorted(tot.items()): print(f"| {f} | {v[0]} | {v[1]} | {v[2]} | {v[3]} |")
print("TOTAL", [sum(v[i] for v in tot.values()) for i in range(4)])
# tueurs par groupe
g = collections.Counter(k.split(".")[0] for k in kill.values())
print(dict(g))
solo = collections.Counter(kill.values())
print("tests tueurs distincts:", len(solo), "; top:", solo.most_common(5))
