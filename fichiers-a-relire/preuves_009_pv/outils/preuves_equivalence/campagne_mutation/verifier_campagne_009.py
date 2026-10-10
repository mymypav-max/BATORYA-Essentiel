#!/usr/bin/env python3
"""Vérifie la COHÉRENCE des sorties brutes de la campagne de mutation 009 (797 mutants : 770 tués, 3 invalides, 24 survivants), sans relancer toute la campagne.

Usage : python3 -B verifier_campagne_009.py RACINE_DEPOT [--rejeu N] [--graine G] [--travail DOSSIER]
  RACINE_DEPOT : dossier contenant src-tauri/ (SQL et tests révisés).
  Sorties lues : ../../sorties_brutes/campagne_complete/ (mut009_complete.log, tueurs_campagne_complete.json, survivants_campagne_complete.txt, invalides_campagne_complete.txt).

Partie 1 (toujours, ≈ 1 s, sans exécuter les tests) :
  - regénère les mutants avec mut009b.py (même code de génération) et exige 797 mutants distincts ;
  - exige que tués (770) + invalides (3) + survivants (24) forment une PARTITION exacte de ces 797 noms (pas de doublon, pas d'intrus, pas d'oubli) ;
  - recoupe avec les totaux imprimés par la campagne (mut009_complete.log) ;
  - exige que chaque test « tueur » enregistré existe dans test_009_pv.py (classe.méthode) ;
  - exige que les SQL mutés soient tous différents du SQL du dépôt.
Partie 2 (facultative, --rejeu N) : REJOUE avec mut009b.py les 3 invalides, les 24 survivants et N mutants tués tirés au hasard (graine fixée), puis compare avec les sorties enregistrées
  (même statut ; même test tueur pour les tués). Ce n'est PAS la campagne complète : les (770 - N) autres tués ne sont vérifiés que par la partie 1.
Code de sortie : 0 = tout cohérent ; 1 = incohérence ; 2 = fichier manquant."""
import argparse, ast, collections, json, pathlib, random, re, subprocess, sys, tempfile
sys.dont_write_bytecode = True
ICI = pathlib.Path(__file__).resolve().parent
SORT = ICI.parent.parent / "sorties_brutes" / "campagne_complete"
ap = argparse.ArgumentParser()
ap.add_argument("racine"); ap.add_argument("--rejeu", type=int, default=0); ap.add_argument("--graine", type=int, default=2026)
ap.add_argument("--travail", default=None)
a = ap.parse_args()
R = pathlib.Path(a.racine).resolve()
need = [ICI / "mut009b.py", ICI / "genmut009b.py", R / "src-tauri/migrations/metier/009_pv.sql", R / "src-tauri/tests/metier/test_009_pv.py",
        SORT / "mut009_complete.log", SORT / "tueurs_campagne_complete.json", SORT / "survivants_campagne_complete.txt", SORT / "invalides_campagne_complete.txt"]
for f in need:
    if not f.is_file():
        print("ERREUR D'ENVIRONNEMENT : introuvable :", f, file=sys.stderr); raise SystemExit(2)
ok = True
def chk(cond, msg):
    global ok
    print(("OK    " if cond else "ECHEC ") + msg); ok &= bool(cond)

sys.path.insert(0, str(ICI))
import genmut009b
mut = genmut009b.charger(root=str(R), workd=str(ICI / "_inexistant_"))   # {nom: sql muté}
orig = (R / "src-tauri/migrations/metier/009_pv.sql").read_text(encoding="utf-8")
tues = json.loads((SORT / "tueurs_campagne_complete.json").read_text(encoding="utf-8"))
noms = lambda f: [l[4:].rstrip() for l in (SORT / f).read_text(encoding="utf-8").splitlines() if l.startswith("### ")]
surv, inval = noms("survivants_campagne_complete.txt"), noms("invalides_campagne_complete.txt")
log = (SORT / "mut009_complete.log").read_text(encoding="utf-8")

print("== Partie 1 : cohérence statique ==")
chk(len(mut) == 797, f"mutants distincts régénérés : {len(mut)} (attendu 797)")
chk(re.search(r"966 mutants générés, 797 distincts", log) is not None, "le journal de campagne annonce « 966 mutants générés, 797 distincts »")
chk((len(tues), len(surv), len(inval)) == (770, 24, 3), f"fichiers enregistrés : tués={len(tues)} survivants={len(surv)} invalides={len(inval)} (attendu 770 / 24 / 3)")
m = re.search(r"\{'tué': (\d+), 'survivant': (\d+), 'invalide': (\d+)\}", log)
chk(m is not None and tuple(map(int, m.groups())) == (770, 24, 3), f"totaux imprimés par la campagne : {m.group(0) if m else 'introuvables'}")
chk("TIMEOUTS: []" in log, "aucun délai dépassé (TIMEOUTS: [])")
chk(len(set(surv)) == len(surv) and len(set(inval)) == len(inval), "pas de doublon dans les survivants ni dans les invalides")
E_t, E_s, E_i, E_all = set(tues), set(surv), set(inval), set(mut)
chk(not (E_t & E_s) and not (E_t & E_i) and not (E_s & E_i), "tués, survivants et invalides sont deux à deux disjoints")
chk(E_t | E_s | E_i == E_all, f"leur réunion est exactement l'ensemble des 797 mutants (intrus : {sorted((E_t|E_s|E_i) - E_all)[:3]} ; oubliés : {sorted(E_all - (E_t|E_s|E_i))[:3]})")
chk(all(t != orig for t in mut.values()), "chaque SQL muté diffère du SQL du dépôt")
chk(len(set(mut.values())) == len(mut), "les 797 SQL mutés sont deux à deux distincts")
# tests tueurs : classe.méthode existent dans le fichier de test
arbre = ast.parse((R / "src-tauri/tests/metier/test_009_pv.py").read_text(encoding="utf-8"))
defs = {(c.name, f.name) for c in ast.walk(arbre) if isinstance(c, ast.ClassDef) for f in c.body if isinstance(f, ast.FunctionDef)}
tueurs = collections.Counter(tues.values())
inconnus = [t for t in tueurs if tuple(t.split(".", 1)) not in defs]
chk(not inconnus, f"les {len(tueurs)} tests tueurs distincts existent tous dans test_009_pv.py (inconnus : {inconnus[:3]}) ; groupes : {dict(collections.Counter(t.split('.')[0] for t in tues.values()))}")
chk("?" not in tueurs, "aucun mutant tué dont le test tueur est inconnu (« ? »)")

if a.rejeu:
    print(f"\n== Partie 2 : rejeu avec mut009b.py de {len(inval)} invalides + {len(surv)} survivants + {a.rejeu} tués tirés au hasard (graine {a.graine}) ==")
    tire = sorted(random.Random(a.graine).sample(sorted(tues), a.rejeu))
    sel = sorted(E_i | E_s) + tire
    motif = "^(?:" + "|".join(re.escape(n) for n in sel) + ")$"
    wd = pathlib.Path(a.travail) if a.travail else pathlib.Path(tempfile.mkdtemp(prefix="rejeu009_"))
    wd.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, "-B", str(ICI / "mut009b.py"), str(R), str(wd), motif], capture_output=True, text=True)
    (wd / "rejeu.log").write_text(r.stdout + r.stderr, encoding="utf-8")
    chk(r.returncode == 0, f"mut009b.py terminé (code {r.returncode}) ; journal : {wd / 'rejeu.log'}")
    lire = lambda f: [l[4:].rstrip() for l in (wd / f).read_text(encoding="utf-8").splitlines() if l.startswith("### ")]
    s2, i2, k2 = set(lire("survivors009.txt")), set(lire("invalides009.txt")), json.loads((wd / "killers009.json").read_text(encoding="utf-8"))
    chk(s2 == E_s, f"survivants rejoués = les {len(E_s)} survivants enregistrés ({len(s2)} rejoués)")
    chk(i2 == E_i, f"invalides rejoués = les {len(E_i)} invalides enregistrés ({len(i2)} rejoués)")
    chk(set(k2) == set(tire), f"les {len(tire)} mutants tirés sont tous retrouvés tués ({len(k2)} tués au rejeu)")
    diff = {n: (tues[n], k2.get(n)) for n in tire if tues[n] != k2.get(n)}
    chk(not diff, f"même test tueur qu'à la campagne pour les {len(tire)} tués tirés (écarts : {list(diff.items())[:3]})")
print("\nCOHÉRENT" if ok else "\nINCOHÉRENCE")
raise SystemExit(0 if ok else 1)
