# COMPLÉMENT DE CADRAGE 009 — PV : contrôle des octets NUL dans les CHECK de format

**Statut : PROPOSITION, à valider par Rémy. Document de travail ; il ne modifie pas `CADRAGE__009_pv.md`.**
Date de l'analyse : 2026-10-09. Dépôt : HEAD `a9fd50f` + fichiers 008/009 non suivis (état local).
Aucun fichier de la tranche 009 (`009_pv.sql`, `test_009_pv.py`, `RAPPORT_MUTATION__009_pv.md`) n'a été modifié pour cette analyse ; seul ce fichier est créé.

Légende (celle du cadrage 009) : **[RD]** règle documentée · **[CT]** conséquence technique · **[PR]** proposition à arbitrer · **[QO]** question ouverte. Ci-dessous, **FAIT** = observé par exécution dans cet environnement ; **HYPOTHÈSE** = non vérifié.

---

## 1. Constat reproductible

Version SQLite utilisée : **3.45.1** (bibliothèque du module `sqlite3` de Python 3.x de l'environnement d'analyse). *HYPOTHÈSE : la version embarquée par l'application Tauri (rusqlite) n'a pas été vérifiée.*

### 1.1 Reproduction minimale (SQL pur, sans rien du dépôt)

```sql
CREATE TABLE t(numero TEXT NOT NULL
  CHECK (numero GLOB 'PVR-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]')) STRICT;
INSERT INTO t VALUES ('PVR-50001-26');                          -- accepté (conforme)
INSERT INTO t VALUES ('PVR-50001-26' || char(0) || 'junk');     -- ACCEPTÉ (17 octets)
SELECT hex(numero), length(numero), length(CAST(numero AS BLOB)) FROM t;
-- ('5056522D35303030312D3236', 12, 12)
-- ('5056522D35303030312D3236006A756E6B', 12, 17)   ← length() de TEXT s'arrête au NUL, pas celle du BLOB
```

Valeurs du même motif (`PVR-50001-26`) selon la position du NUL (FAIT, SQLite 3.45.1) :

| Valeur | octets | `GLOB` | `length(x)` (TEXT) | `length(CAST(x AS BLOB))` | `x = 'PVR-50001-26'` |
|---|---:|:--:|---:|---:|:--:|
| conforme | 12 | 1 | 12 | 12 | 1 |
| NUL final | 13 | **1** | 12 | 13 | 0 |
| NUL puis `junk` | 17 | **1** | 12 | 17 | 0 |
| NUL au milieu (`PVR-5␀1-26`) | 10 | 0 | 5 | 10 | 0 |
| NUL au début | 13 | 0 | 0 | 13 | 0 |

Conséquence : `GLOB` lit la chaîne comme une chaîne C terminée au premier NUL ; `length()` d'un TEXT et `substr()` font de même. Seule une valeur **conforme jusqu'au premier NUL** passe, avec une queue arbitraire derrière.

### 1.2 Reproduction sur le SQL réel de 009 (chaîne 001→008 au rang 11, puis `009_pv.sql` tel quel, base mémoire jetable)

| Colonne / cas | Valeur | Résultat observé (SQL actuel) |
|---|---|---|
| `numero`, PV initial V6, sans réserves | `PVR-50001-26` | accepté (attendu) |
| idem | `PVR-50001-26␀` | **accepté** |
| idem | `PVR-50001-26␀junk`, `PVR-50001-26␀` + 50 `x` | **accepté** |
| idem | NUL au milieu, au début, `␀` seul | refusé |
| `numero`, PV initial V6, avec réserves | `PVR-50001-26␀` | **accepté** |
| `numero`, `origine='import'` | `ANCIEN/12␀`, `␀` | accepté (numéro libre non vide, par conception : Z-8, hors format) |
| `date_reception` | `2026-10-20␀`, `2026-10-20␀x`, NUL au milieu, NUL au début | **refusé dans tous les cas** |
| `created_at` (valeur explicite) | `2026-10-20T10:00:00.000Z␀`, `…Z␀junk` | **accepté** |
| `created_at` | NUL au milieu, NUL au début | refusé |
| `created_at` | valeur par défaut (`strftime`) | accepté (toujours 24 octets) |
| `UNIQUE(numero)` | `PVR-50001-26␀` alors que `PVR-50001-26` existe | **accepté** (comparaison binaire : deux numéros affichés à l'identique coexistent) |
| ligne stockée | `hex(numero)` = `5056522D35303030312D323600` | 12 caractères lus par `length(numero)`, **13 octets** stockés |

Scripts de reproduction (hors dépôt, rejouables sur demande) : `scratchpad/nul/repro_min.py`, `repro_009.py`, `repro_levee.py`.

---

## 2. Écart

| | Attendu | Accepté réellement |
|---|---|---|
| `numero` d'un PV initial V6 | exactement `PVR-nnnnn-yy`, soit 12 caractères / 12 octets, `yy` = année de `date_reception` — **[RD]** INV-20, Mod. §6, Mod. §10.4 ; cadrage 009 §3 | `PVR-nnnnn-yy` **suivi d'un octet NUL puis de n'importe quels octets** (la contrainte `substr(numero, 11, 2) = substr(date_reception, 3, 2)` est elle aussi aveugle après le NUL) |
| `created_at` | exactement `YYYY-MM-DDTHH:MM:SS.mmmZ` (24 octets) — **[RD]** INV-10, Mod. §2 (TS) | idem : motif conforme + NUL + queue |

Ce n'est pas une règle métier nouvelle : **le format est déjà exigé** ; le CHECK écrit ne l'applique pas à toute la valeur stockée.

---

## 3. Périmètre (colonne par colonne — rien n'est généralisé sans vérification)

| Contrôle | Concerné ? | Base de la conclusion |
|---|---|---|
| `numero` du **PV initial V6** (`origine='v6'`, types sans réserves / avec réserves) | **OUI** (queue après un NUL) | FAIT §1.2 |
| `numero` d'une **levée** | **Pas de CHECK de format** (PR-3, Z-8) → le défaut GLOB ne s'y applique pas directement. La garde **G4** (`NEW.numero = o.numero \|\| '-' \|\| printf('%02d', suffixe)`) compare **en binaire** : un NUL ajouté au numéro d'une levée dont l'origine est conforme est refusé (déjà testé : `test_T51_K_octet_nul_dans_les_textes`). **Mais G4 propage un NUL déjà présent dans l'origine** : origine `PVR-50001-26␀` → levée `PVR-50001-26␀-01` **acceptée** (FAIT, `repro_levee.py`). | FAIT |
| `numero` d'une origine `origine='import'` (numéro libre) | Hors format par conception (Z-8, hors périmètre de migration, aucun PV V2). Un NUL y est accepté ; **non couvert par la correction proposée** et non à traiter ici (ce serait une règle nouvelle sur les numéros historiques). | FAIT (acceptation) / périmètre : cadrage §2, Z-8 |
| `date_reception` | **NON concerné** : le `GLOB` laisse passer `AAAA-MM-JJ␀…`, mais `date(x) IS x` échoue (`date()` renvoie la date sans la queue, donc différente de `x` en comparaison binaire). Refus constaté sur NUL final, NUL + queue, milieu, début. | FAIT §1.1/§1.2 |
| `created_at` | **OUI pour une valeur explicite** ; la valeur par défaut produit toujours 24 octets. *HYPOTHÈSE : le service écrit normalement `created_at` par défaut ; non vérifié (pas de service dans ce dépôt).* S'applique aussi aux lignes de type levée (même colonne, même CHECK). | FAIT / HYPOTHÈSE |
| CHECK `json_valid`, `type IN (…)`, `origine IN (…)`, `numero <> ''` | Non examinés ici : ce ne sont pas des contrôles de format `GLOB`. (`type`/`origine` : `IN` compare en binaire — refusés dans le test existant `test_T51_K_octet_nul_dans_les_textes` pour `type`.) | test existant |
| Autres migrations 001→008 | **NON VÉRIFIÉ colonne par colonne.** Le même opérateur `GLOB` y est utilisé (nombre de lignes contenant `GLOB` : 001 : 22 ; 002 : 4 ; 003 : 60 ; 004 : 71 ; 005 : 12 ; 005a : 38 ; 005b : 25 ; 005c : 0 ; 006 : 54 ; 007 : 8 ; 008 : 4 ; 009 : 4 — lignes, pas colonnes). Le test existant affirme déjà « created_at depuis 001 » ; cette affirmation n'est pas reprise ici comme vérifiée. | HYPOTHÈSE, **hors périmètre** |

---

## 4. Correction technique minimale proposée **[PR]** (aucune règle métier modifiée)

Ajouter, **dans les deux CHECK concernés seulement**, un conjoncte de longueur exacte **en octets** :

```sql
-- numero, PV initial V6 (CHECK de format du numéro)
CHECK (origine <> 'v6' OR type = 'levee_reserves'
       OR (numero GLOB 'PVR-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
           AND substr(numero, 11, 2) = substr(date_reception, 3, 2)
           AND length(CAST(numero AS BLOB)) = 12)),

-- created_at (CHECK de format)
CHECK (created_at GLOB
    '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'
    AND length(CAST(created_at AS BLOB)) = 24)
```

**Pourquoi c'est suffisant** (raisonnement, vérifié par exécution) : si le `GLOB` réussit, les 12 (resp. 24) premiers caractères avant le premier NUL sont exactement le motif ; s'il existait un NUL, il serait situé après eux et la longueur en octets dépasserait 12 (resp. 24). Un NUL en deçà fait déjà échouer le `GLOB`. Le motif n'admet que de l'ASCII : octets = caractères.

**Variante corrigée exécutée** (en mémoire, sans écrire dans le dépôt) :
- `PVR-50001-26␀`, `…␀junk`, `…␀`+50 `x`, NUL milieu/début/seul : **tous refusés**, avec ou sans réserves ;
- `created_at` NUL final / queue / milieu / début : **tous refusés** ;
- valeurs conformes (`PVR-50001-26`, `created_at` explicite `…00.000Z` et `…00.999Z`, valeur par défaut) : **acceptées** ;
- `date_reception` et `origine='import'` : comportement **inchangé** ;
- origine `PVR-50001-26␀` : désormais impossible à créer, donc la levée `…␀-01` ne peut plus en dériver ;
- **la suite existante (255 tests) rejouée sur cette variante : 254 passent ; seul `test_T51_K_LIMITE_le_GLOB_de_sqlite_s_arrete_au_premier_octet_nul_CONSTAT` échoue, ce qui est attendu** (il constate l'acceptation). Aucun faux positif sur les cas valides existants.

**Alternatives examinées (FAIT, SQLite 3.45.1)**

| Formulation | Rejette NUL + queue ? | Accepte le conforme ? | Remarque |
|---|:--:|:--:|---|
| `length(x) = 12` (TEXT) | **non** | oui | inutilisable : s'arrête au NUL |
| `length(CAST(x AS BLOB)) = 12` | oui | oui | **retenue** : fonctionne sur toutes les versions de SQLite |
| `octet_length(x) = 12` | oui | oui | fonction apparue en 3.43 ; *version embarquée par Tauri non vérifiée* → non retenue |
| `instr(CAST(x AS BLOB), x'00') = 0` | oui | oui | correcte mais n'impose pas la longueur ; moins directe |
| `CAST(x AS BLOB) GLOB motif` | oui | **non** (rejette aussi le conforme) | inutilisable |
| `x NOT GLOB '*[^ -~]*'` | non | oui | s'arrête au NUL |

**Non proposé** : aucun conjoncte sur `date_reception` (déjà protégé, §3) ; aucun CHECK de format sur la levée (PR-3 inchangé) ; aucune modification des mécanismes `origine='import'` ; aucune borne d'année.

---

## 5. Tests à ajouter ou corriger (après validation uniquement)

**À corriger**
- `test_T51_K_LIMITE_le_GLOB_de_sqlite_s_arrete_au_premier_octet_nul_CONSTAT` : remplacer le constat d'acceptation par une assertion de **rejet** (renommer sans « LIMITE » / « CONSTAT »), et retirer de sa docstring l'affirmation « NON corrigée par 009 (cadrage validé) » (voir §7.2).

**À ajouter (groupe B ou K)** — chaque cas avec assertion explicite de rejet, via `essai_pv` / `ko_check` :

| Cas | Valeur | Attendu |
|---|---|---|
| numéro V6 sans réserves, NUL final | `PVR-50001-26␀` | rejet (CHECK) |
| idem, NUL puis queue | `PVR-50001-26␀junk` | rejet |
| idem, queue longue (≥ 50 octets) | | rejet |
| idem, NUL au milieu / au début / seul | | rejet (non-régression, déjà refusé) |
| numéro V6 **avec réserves**, NUL final | | rejet |
| numéro conforme, plusieurs `nnnnn` et `yy` | `PVR-00001-26`, `PVR-99999-99`… | accepté (anti faux-positif) |
| `created_at` explicite NUL final / NUL + queue | | rejet |
| `created_at` NUL milieu / début | | rejet (non-régression) |
| `created_at` conforme `….000Z`, `….999Z`, défaut | | accepté |
| `created_at` d'une **levée** avec NUL | | rejet |
| `date_reception` NUL final / queue / milieu / début | | rejet (non-régression, **inchangé**) |
| origine V6 `PVR-…␀` impossible → pas de levée dérivée d'un NUL | | rejet à la création de l'origine |
| levée dont le numéro porte un NUL ajouté (origine conforme) | | rejet par G4 (existant, conservé) |
| `origine='import'`, numéro libre avec NUL | | **accepté — à documenter comme constat de périmètre (Z-8), pas comme règle** |
| `UNIQUE(numero)` : `PVR-50001-26` puis `PVR-50001-26␀` | | le second est rejeté par le CHECK (plus par accident d'unicité) |
| table témoin (copie de 009 sans le conjoncte de longueur) | numéro `…␀junk` | accepté — prouve que **le conjoncte de longueur est la seule garde** (même principe que le témoin « sans liste IN ») |

Les conjonctes ajoutés étant les seuls à rejeter ces valeurs, les cas ci-dessus tuent les mutants du §6.

---

## 6. Impact sur la mutation

- **Campagne complète à relancer** (SQL modifié, suite modifiée) : les numéros de lignes `L111` / `L114` des noms de mutants changent, la liste des mutants change, les chiffres du rapport (692 / 670 / 3 / 19) ne sont plus valables.
- **Mutants nouvellement générés** : sur chaque conjoncte ajouté — constante `12` → `11`/`13`, `24` → `23`/`25`, `CAST(… AS BLOB)` retiré (ce qui rétablirait le défaut : tué uniquement par les nouveaux tests NUL), `CAST … AS TEXT`, `=` → `<=`/`>=`, `AND` → `OR`, conjoncte supprimé.
- **Qualifications existantes à refaire** : S01 (`substr(numero, 11, 3)`, preuve E2 rédigée « queues NUL comprises ») ; S11-S12 (chiffres de `yy` du numéro, E3) ; S02-S10 sur la ligne `date_reception` ne sont **pas** concernés par la correction mais changent de numérotation de ligne si le fichier est décalé. La preuve E2 deviendrait plus simple (longueur exacte imposée) ; elle doit néanmoins être rejouée, pas supposée.
- **Rapport** : §5, puce « Limite non corrigée … GLOB … octet NUL » à remplacer ; §3 (lacunes) à compléter.
- **Statut avant relance** : aucun résultat de mutation n'est à considérer comme acquis pour la nouvelle version.

---

## 7. Impact documentaire

### 7.1 Sources normatives concernées (non modifiées)
- **INV-20** (format `PVR-00001-yy`, « contrôle de format sans exception » sauf PV importés), **Mod. §6**, **Mod. §10.4**, **INV-131** : définissent le format ; la correction ne fait que l'appliquer à toute la valeur — **[CT]**, pas une règle nouvelle.
- **INV-10** et **Mod. §2** (types `D` / `TS`) : spécifient le contrôle d'un TS comme « `GLOB` » (tableau des conventions, l.70) ; le conjoncte de longueur **étend** la formulation « `GLOB` » seule. Ce n'est pas une contradiction (la valeur reste au format), mais la convention écrite ne mentionne pas l'octet NUL.
- **`invariants.md` (contrôle de non-régression, point 6)** et **Mod. §2 l.77 (« Motifs GLOB »)** : ne traitent que du quantificateur `{n}` et de `date(x)=x`. Aucun texte lu ne mentionne le comportement de `GLOB` face à un NUL (recherche de `NUL`, `octet`, `length(` dans `docs/conception/` : aucune occurrence pertinente).
- Cadrage 009 : §3 (format), §3.6 (limites des sondes), §5 cas 8 (« REAL/BLOB/NUL dans colonnes TEXT (STRICT) ») : le NUL est prévu comme **cas de données malformées à tester**, pas comme limite acceptée.

### 7.2 Divergences constatées
1. **Texte du test et du rapport 009 non étayé par le cadrage.** La docstring de `test_T51_K_LIMITE_…` dit « NON corrigée par 009 (cadrage validé) » et le rapport (§5) dit « aucune règle documentaire ne l'exige ». Le cadrage 009 **ne liste pas** cette limite dans son §3.6 et ne décide pas de la laisser ; INV-20 exige le format. Ces deux phrases sont à corriger après décision : elles prêtent au cadrage une décision qu'il ne contient pas.
2. **Asymétrie avec 001→008.** Les autres migrations utilisent `GLOB` seul (HYPOTHÈSE de même comportement, non vérifiée colonne par colonne). Si 009 reçoit le conjoncte de longueur, 009 sera la seule migration à l'avoir. Les migrations antérieures ne sont **pas** à modifier dans le cadre de cette proposition.
3. **Cadrage et documents officiels** : aucune modification proposée ici ; une éventuelle mention (convention « TS / format : `GLOB` + longueur en octets ») relèverait d'une décision séparée de Rémy.

---

## 8. Décisions attendues avant toute modification de `009_pv.sql`

1. **D1** — Corriger dans 009 le `numero` du PV initial V6 par le conjoncte `length(CAST(numero AS BLOB)) = 12` ? (oui / non / autre formulation)
2. **D2** — Corriger dans 009 `created_at` par `length(CAST(created_at AS BLOB)) = 24` ? (oui / non). Si l'application ne fournit jamais `created_at` explicitement, la décision peut être différée sans effet métier — *information à confirmer par Rémy*.
3. **D3** — Confirmer que `date_reception`, la levée (PR-3) et `origine='import'` restent **hors correction**.
4. **D4** — Traitement de 001→008 (même mécanisme, non vérifié) : hors de cette tranche ; à décider séparément (audit dédié, ou acceptation documentée), sans toucher aux migrations existantes sans autorisation explicite.
5. **D5** — Autoriser, une fois D1-D3 tranchées : modification de `009_pv.sql` (2 conjonctes), de `test_009_pv.py` (§5), de `RAPPORT_MUTATION__009_pv.md` (relance complète, §6), et correction de la docstring / de la phrase du rapport (§7.2-1).
6. **D6** — Décider si une mention documentaire de la convention est souhaitée (§7.2-3) ; non nécessaire à l'implémentation.

Tant que ces décisions ne sont pas prises : **aucune modification** de `009_pv.sql`, `test_009_pv.py` ou du rapport de mutation.
