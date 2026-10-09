# SYNTHÈSE 009 — octet NUL : tests finaux, corrections de documentation, reproductibilité de la mutation

**Statut : SYNTHÈSE DE PROPOSITIONS, rien n'est appliqué.** Ni SQL, ni tests, ni rapport de mutation, ni cadrage ou document officiel n'ont été modifiés ; rien n'est poussé ; la tranche 010 n'est pas commencée. Les trois autres livrables : `PROPOSITION_DIFF__009_pv__controle_nul.md` (SQL, révision 2), `PROPOSITION_DIFF_TESTS__009_pv__controle_nul.md`, `PLAN_REMEDIATION__001_008__controle_nul.md`.
Date : 2026-10-10. SQLite 3.45.1, Python 3.11.15. Tous les essais ont été faits sur des copies jetables du dépôt.

---

## 1. Synthèse des tests

| Mesure | Résultat |
|---|---|
| `test_009_pv` : SQL actuel, tests actuels (état du dépôt) | 255 tests, OK |
| `test_009_pv` : SQL révisé + diff des tests | **268 tests, OK** — aucun échec « attendu » |
| Suite complète 001 → 009 (`unittest discover`, SQL et tests révisés) | **1 866 tests, OK** (1 598 + 268) |
| Test machine (`tests/machine`) | 13 tests, OK |
| Les 14 nouveaux tests sur le **SQL actuel** | 7 échouent (42 sous-tests) : ils détectent bien le défaut |
| SQL révisé privé de D1 / de D2 / de D3 | 5 / 3 / 2 tests échouent : chaque groupe de conjoncts est surveillé par ses propres tests |
| Mutation — aperçu limité aux conjoncts ajoutés (42 mutants) | **42 tués** (voir §4.5 : 6 d'entre eux ne le sont que par un test de texte, équivalents probables) |
| Mutation — campagne complète | **non relancée** (suit l'autorisation, D5) |

Commande : `cd src-tauri/tests/metier && python3 -B -m unittest discover -s . -p "test_*.py"`.

---

## 2. Corrections minimales de la docstring du test et du rapport de mutation

### 2.1 Docstring du test (comprise dans le diff des tests)

- *Ancien* (`test_T51_K_LIMITE_…`) : `LIMITE constatée, NON corrigée par 009 (cadrage validé) : … C'est le comportement de TOUS les CHECK GLOB de la chaîne (created_at depuis 001). Ce test documente la limite : il ne la valide pas.`
- *Nouveau* (`test_T51_K_octet_nul_apres_le_numero_ou_le_created_at_refuse`) : `Un octet NUL ne peut suivre ni un numéro de PV initial V6 ni un created_at : GLOB, substr et length() de TEXT s'arrêtent au premier octet NUL, la longueur est donc contrôlée en octets (length(CAST(x AS BLOB))). Ces valeurs étaient acceptées avant la correction ; tous les autres cas sont au groupe B.`
- Nouveau test témoin Z-8 : sa docstring dit qu'il s'agit d'un **constat, non d'une règle**, que 009 ne change pas l'exemption d'INV-131, et que l'interdire serait une évolution de règle à décider explicitement.
- *Si la correction n'est pas autorisée* (variante de repli) : `LIMITE constatée, NON corrigée dans la livraison 009 (aucune décision documentaire sur ce point ; voir COMPLEMENT_ANALYSE__009_pv__controle_nul.md) : … C'est le comportement des CHECK à GLOB seul de la chaîne (horodatages, numéros, codes, décimaux) ; les dates (date(x) IS x) et les listes IN y échappent. …`

### 2.2 `RAPPORT_MUTATION__009_pv.md` (à appliquer **après** la relance complète ; aucun chiffre n'est inventé ici)

| # | Où | Ancien | Nouveau |
|---|---|---|---|
| R1 | §5, puce « Limite non corrigée… » (l.123) | `**Limite non corrigée, commune à tous les CHECK GLOB de la chaîne** : … non corrigé en SQL (aucune règle documentaire ne l'exige).` | `**Octet NUL — corrigé dans 009, limite subsistante hors 009** : GLOB, substr, length() de TEXT et json_valid s'arrêtent au premier octet NUL. 009 contrôle donc la longueur en octets (length(CAST(x AS BLOB)) = 12 pour le numéro du PV initial V6, = 24 pour created_at) et refuse l'octet NUL brut dans les quatre champs JSON ; l'échappement JSON \u0000 reste valide. Le cadrage 009 ne contenait pas de décision sur ce point ; INV-20 et le type TS du modèle définissent le format. Restent hors correction, par décision de périmètre : origine='import' (numéro libre, INV-131 ; le NUL d'un tel numéro se propage à la levée par G4, Z-8), la levée (PR-3) et les migrations 001–008 (plan de remédiation).` |
| R2 | en-tête (l.3-4) | `(170 lignes …)` ; `(255 tests, 669 sous-tests)` | `(175 lignes …)` ; `(268 tests, [N] sous-tests à recompter)` |
| R3 | §1 (tableaux, historique des passes) | 692 / 670 / 3 / 0 / 19 | **à régénérer par la campagne complète sur le SQL et les tests finaux** ; ajouter une « passe 4 : correction NUL (D1–D3) » |
| R4 | §1, phrase « Aucune lacune métier dans le SQL (le SQL n'a pas changé…) » | idem | `Le SQL a changé après la campagne initiale (correction NUL, D1–D3) ; la campagne a été relancée en entier sur le SQL et les tests finaux.` |
| R5 | §3, titre « Lacunes réelles… (tests uniquement, SQL inchangé) » | idem | `Lacunes réelles découvertes et corrigées (tests ; puis correction SQL NUL)` + une ligne 5 : « octet NUL : 14 tests ajoutés, 1 remplacé (groupes B et K) » |
| R6 | §4, E2 | `Prouvé sur 2 400 chaînes acceptées par le GLOB, queues après un octet NUL comprises` | `Le CHECK impose aussi length(CAST(numero AS BLOB)) = 12 : aucune queue ne suit le 12ᵉ caractère, NUL compris. Prouvé par preuves_equivalence_009.py sur 240 000 (numéro, date) dont 400 acceptés.` (chiffres du script, domaine inchangé) |
| R7 | §4 : identifiants et lignes des survivants | `L82`, `L111`… | à recalculer ; S01–S19 deviennent les entrées du registre du script de preuve |
| R8 | l.5 (outils) et §5 (méthode) | `outils de travail hors dépôt` ; `script equiv009.py` | si le script de lien est adopté (D7) : `les preuves E1–E7 sont rejouées par preuves_equivalence_009.py, qui lit 009_pv.sql du dépôt` ; sinon conserver et ajouter sha256 + longueur des outils |

---

## 3. Le problème de reproductibilité (rappel)

`equiv009.py` se rejoue seul (30 s, « TOUT EST OK ») mais il **retape les expressions** : il ne lit pas `009_pv.sql`. Rien ne prouve donc que la preuve concerne le texte livré, ni que les 19 mutants correspondent à des modifications du fichier réel, ni qu'une évolution du SQL ne rende pas la preuve caduque. Le rejeu seul ne démontre pas ce lien.

## 4. Solution proposée : un script de preuve **lié au SQL du dépôt** (non ajouté au dépôt)

Fichier proposé : `src-tauri/tests/metier/outils/preuves_equivalence_009.py` (hors du motif `test_*.py` : non collecté par `unittest discover`, exécuté à la demande). sha256 `0243351cbd5f4db5ed9948e1ddcd2c3a55e089088f098b07f59cbb8b57d66a0c`, 327 lignes, source en annexe. Il n'est **pas** dans le dépôt ; il est dans la copie de travail.

### 4.1 Comment le lien est établi

1. **Registre = substitutions textuelles sur le fichier réel.** S01–S19 sont des couples (ancien, nouveau) appliqués à `009_pv.sql` **lu dans le dépôt**. Si un ancien texte ne figure pas **exactement une fois**, le script s'arrête avant tout calcul (« la preuve ne correspond plus au SQL du dépôt »).
2. **Mutant réel.** Chaque SQL muté est appliqué par le moteur sur la chaîne 001→008 (un mutant qui ne se migre pas serait « invalide », pas « survivant »).
3. **Prédicats lus dans le DDL créé.** Les CHECK comparés (date, numéro) sont extraits de `sqlite_master` pour l'original **et** le mutant ; les formats `printf` sont lus dans le texte du trigger ; les triggers sont exécutés tels que créés. Aucune expression de 009 n'est retapée dans le script.
4. **Domaines exhaustifs, évalués par le moteur réel** : 5 373 485 jours juliens (E1) ; 240 000 couples numéro×date, queues NUL comprises (E2) ; 6 760 000 couples alphabet²×années (E3) ; 101 001 entiers pour le format `printf` + 99 levées successives avec numéros conformes et mal formés (E4) ; 156 états de 0 à 3 PV × 8 316 tentatives de levée par les triggers réels (E5, E6) ; 1 047 tentatives d'`UPDATE`/`DELETE`/`REPLACE` (E7).
5. **Témoins non équivalents (7)**, obtenus eux aussi par substitution sur le même fichier, qui **doivent** diverger : suppression de `date(x) IS x`, `substr(numero,10,2)`, `?` sur `yy` + suppression de l'égalité, `printf('%d')`, jointure avec table vide, `IS NOT`, trigger `UPDATE OF observations` (divergences de 3 à 2 490 000).
6. **Prémisses vérifiées.** E1 exige que le CHECK de date contienne toujours `date(date_reception) IS date_reception` ; sinon le script s'arrête.

### 4.2 Résultats

| Exécution | Résultat |
|---|---|
| Sur le `009_pv.sql` **actuel** (sha256 `d32b20a4…`) | 29 contrôles OK (1 registre, 2 références, 19 survivants, 7 témoins), **TOUT EST OK**, 209 s |
| Sur le `009_pv.sql` **révisé** (sha256 `764a2d30…`) | 29 contrôles OK, **TOUT EST OK**, 213 s |
| SQL périmé (opérandes de G2 permutés) | arrêt immédiat : « `…o.bc_id IS NEW.bc_id` figure 0 fois dans 009_pv.sql (attendu : 1) » |
| Prémisse E1 supprimée du SQL | arrêt : « le CHECK de date_reception ne contient plus `date(date_reception) IS date_reception` » |

Les 19 survivants restent équivalents sur le SQL révisé (la correction NUL ne change pas leur classification ; pour S01 seul le nombre de points acceptés passe de 2 400 à 400).

### 4.3 Ce que cela démontre et ne démontre pas

- **Démontre** : les 19 mutants sont bien des modifications du fichier du dépôt, valides pour le moteur, et équivalents sur le domaine pertinent, avec un contrôle de fraîcheur automatique et des témoins qui divergent ; E1, E3, E5, E6 restent **relatives** aux conjoncts conservés (`date(x) IS x`, `NOT NULL`).
- **Ne démontre pas** : (a) que S01–S19 sont **les seuls** survivants — il faut l'outil de campagne (`mut009.py`, hors dépôt) ; (b) l'équivalence pour un autre moteur que celui qui exécute (la version est affichée) ; (c) E7 (`FOR EACH ROW` dupliqué) autrement que par différentiel de comportement et par la documentation SQLite (le mot-clé est le comportement par défaut) ; (d) que le registre sera mis à jour : après une nouvelle campagne il faut y verser les nouveaux survivants.
- Les preuves en domaine fini s'appuient, comme avant, sur un argument structurel (positions de caractères, conjonction avec `date(x) IS x`) ; le script exécute l'énumération sur le texte réel, il ne remplace pas l'argument.

### 4.4 Options d'adoption (rien n'est ajouté ni versionné ici)

| Option | Contenu | Remarque |
|---|---|---|
| **A** | Versionner le script (327 lignes) dans le dépôt, exécution manuelle ou en CI hors suite rapide | Lien SQL ↔ preuve permanent ; 3,5 min |
| **B** | Idem + test opt-in (variable d'environnement) qui l'appelle | Intégré à `unittest`, désactivé par défaut |
| **C** | Ne pas versionner : annexer le code et son sha256 au rapport de mutation | Traçabilité, pas de rejeu depuis le dépôt |
| **D** | Versionner aussi l'outil de campagne (`mut009.py`, `genmut009.py`, `classify009.py`) | Seule option qui rend la **complétude** vérifiable ; ≈ 630 lignes, ancêtres 006–008 aussi hors dépôt |

Recommandation : A (ou B) pour le lien SQL ↔ preuves ; D uniquement si Rémy veut la reproductibilité complète de la campagne. À décider séparément de D1–D5.

### 4.5 Aperçu de campagne sur les conjoncts NUL ajoutés (≠ campagne complète)

42 mutants (constantes 12→11/13 et 24→23/25, `=`→`<>`/`<=`/`>=`, `CAST AS BLOB` retiré ou `AS TEXT`, conjoncte supprimé, `AND`→`OR`, `= 0`→`<> 0`/`>= 0`, `x'00'`→`x'01'`, par colonne), joués contre les 268 tests : **42 tués, 0 survivant, 0 invalide**. Réserve : pour 6 d'entre eux, le seul test qui échoue est le témoin K (il vérifie le **texte** des conjoncts) ; sans lui ils survivraient. Ce sont des **équivalents probables**, à qualifier par la campagne complète :

| Mutant | Raison probable |
|---|---|
| `length(CAST(numero AS BLOB)) <= 12`, idem `<= 24` pour `created_at` | le `GLOB` impose déjà ≥ 12 (resp. 24) octets : `<=` ≡ `=` |
| `instr(client_snapshot, x'00') = 0` (sans `CAST`), idem pour les trois autres colonnes JSON | sur SQLite 3.45.1, `instr(TEXT, BLOB)` compare déjà les octets ; le `CAST` est conservé pour une sémantique explicite et indépendante de la version |

---

## 5. Points qui restent à arbitrer

| # | Point | Où |
|---|---|---|
| 1 | Valider le diff SQL tel quel (D1 + D2 + D3) | diff SQL |
| 2 | Z-8-NUL : conserver l'exemption d'import telle quelle (recommandé, aucune évolution implicite) ou interdire le NUL dans les numéros importés (évolution d'INV-131) | diff SQL §3.2 |
| 3 | Valider le diff des tests, dont le remplacement du test-constat et l'adaptation de `C_LEGACY_JSON` | diff tests |
| 4 | Autoriser la modification de `009_pv.sql` et de `test_009_pv.py`, puis la **relance complète** des tests et de la campagne de mutation, puis la mise à jour du rapport (R1–R8) | D5 |
| 5 | Choisir l'option d'adoption du script de preuve (A/B/C/D) | §4.4 |
| 6 | 001–008 : vagues V0–V3, mode M3 ou M4, bases existantes (P-1 à P-6) | plan de remédiation |
| 7 | Mention documentaire éventuelle dans le cadrage 009 (non nécessaire à l'implémentation) | D6, complément §5.2 d |
| 8 | Version de SQLite embarquée par Tauri : non vérifiée (le diff n'emploie que `length`, `instr`, `CAST AS BLOB`) | à confirmer |
| 9 | Les services Rust/TS : filtrent-ils déjà les NUL ? (hors dépôt) ; écrivent-ils `created_at` explicitement ? | plan P-3 |

---

## Annexe — `preuves_equivalence_009.py` (non ajouté au dépôt)

```python
#!/usr/bin/env python3
"""Preuves d'équivalence des 19 mutants survivants de la campagne 009, LIÉES au texte réel de 009_pv.sql.

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
Ce que ce script ne démontre pas : (a) que S01-S19 sont les seuls survivants d'une campagne (il faut l'outil de mutation) ; (b) l'équivalence pour un autre moteur que
celui qui l'exécute (la version SQLite est affichée) ; (c) l'équivalence hors du schéma tel que lu (les preuves E1, E3, E5, E6 sont relatives aux CHECK/NOT NULL conservés)."""
import hashlib, importlib.util, itertools, pathlib, re, sqlite3, sys, time

sys.dont_write_bytecode = True
RACINE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[3]
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
assert len(REGISTRE) == 19
# témoins NON équivalents (même mécanisme : substitution textuelle sur le SQL du dépôt)
TEMOINS = {
    "E1": ("W1 : suppression de `date(date_reception) IS date_reception`", "AND date(date_reception) IS date_reception", ""),
    "E2": ("W2 : décalage de position `substr(numero, 10, 2)`", "substr(numero, 11, 2) = substr(date_reception, 3, 2)", "substr(numero, 10, 2) = substr(date_reception, 3, 2)"),
    "E3": ("W3 : `?` sur yy ET suppression de l'égalité avec l'année", None, None),
    "E4": ("W4 : `printf('%d', ...)`", "printf('%02d', NEW.suffixe)", "printf('%d', NEW.suffixe)"),
    "E5": ("W5 : jointure avec une table vide (`import_anomalies x`)", G1, G1.replace("FROM pv o ", "FROM pv o, import_anomalies x ")),
    "E6": ("W6 : `IS NOT` à la place de `IS`", "o.bc_id IS NEW.bc_id", "o.bc_id IS NOT NEW.bc_id"),
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
for _sid, _fam, _a, _n in REGISTRE:                                  # contrôle de fraîcheur AVANT tout calcul : chaque ancre doit exister une fois dans le SQL du dépôt
    une_fois(SQL, _a)
check("registre : les 19 ancres de S01-S19 figurent chacune exactement une fois dans 009_pv.sql", True)
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
    if famille == "E7":
        r = parcours_immuabilite(tm)
        return f"{len(r)} tentatives d'UPDATE/DELETE/REPLACE", differe(CACHE["imm"], r)


for sid, famille, ancien, nouveau in REGISTRE:
    detail, dv = evaluer(sid, famille, ancien, nouveau)
    check(f"{sid} ({famille}) mutant valide, ancre unique ; {detail} ; divergences = {dv}", dv == 0)
print()
for famille, (nom, ancien, nouveau) in TEMOINS.items():
    if famille == "E3":
        sql_m = muter(muter(SQL, glob_num(LIT_NUM), glob_num(variante(TOK_N, 6, "PVR-"))), "substr(numero, 11, 2) = substr(date_reception, 3, 2)", "1 = 1")
        tm = monde(sql_m)
        dv = e3(ORIG, tm)[2]
    else:
        detail, dv = evaluer("W", famille, ancien, nouveau, temoin=True)
    check(f"TÉMOIN {famille} {nom} : divergences = {dv} (doit être > 0)", dv > 0)
print(f"\nDurée : {time.time() - T0:.0f} s")
print("TOUT EST OK" if OK else "ECHEC")
raise SystemExit(0 if OK else 1)
```
