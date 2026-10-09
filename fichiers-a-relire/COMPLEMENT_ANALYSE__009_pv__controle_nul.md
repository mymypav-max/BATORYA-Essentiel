# COMPLÉMENT D'ANALYSE 009 — PV : octet NUL, inventaire 001–008, vérification de la correction, tests, mutation, documentation

**Statut : ANALYSE EN LECTURE SEULE, à valider par Rémy. Rien n'est appliqué.**
Suite de `COMPLEMENT_CADRAGE__009_pv__controle_nul.md` (qu'elle complète et, sur un point, corrige : §5.3). Date : 2026-10-09. Dépôt : HEAD `a9fd50f` + fichiers 008/009 non suivis (état local).
Aucun SQL, aucun test, aucun rapport de mutation, aucun document officiel n'a été modifié. Seuls deux fichiers sont créés dans `fichiers-a-relire/` : celui-ci et `PROPOSITION_DIFF__009_pv__controle_nul.md` (diff SQL **non appliqué**, séparé comme demandé). Rien n'est poussé.

Légende : **FAIT** = observé par exécution ici (SQLite **3.45.1**, Python 3.11.15) ; **HYPOTHÈSE** = non vérifié ; **[RD]/[PR]** = légende du cadrage. *La version de SQLite embarquée par l'application Tauri n'a pas été vérifiée (HYPOTHÈSE : identique).*

---

## 0. Ce qu'il faut retenir (10 lignes)

1. Le défaut est **reproduit** sur `pv.numero` (PV initial V6) et `pv.created_at` : `GLOB`, `substr` et `length()` de TEXT s'arrêtent au premier NUL ; `PVR-50001-26␀junk` et `…Z␀junk` sont acceptés.
2. **Inventaire 001–008** : sur 137 colonnes dont la validité repose sur `GLOB`, `IN`, `date(x) IS x` ou `json_valid`, **90 sont vulnérables, 47 ne le sont pas** (§1). Les dates (16) et les énumérations `IN` (31) résistent ; horodatages (41), décimaux (26), JSON (17), numéros (4), codes (2) ne résistent pas.
3. La famille décimale « DL » (quantités, prix unitaires, remises de lignes ; 10 colonnes) est **plus exposée** que le précédent documenté en 007 §6 (2) : un NUL **au début ou au milieu** passe aussi (aucun `GLOB` positif).
4. Le cadrage 007 §6 (2) **documente déjà** une limite NUL pour les montants D2 de 001–006, et la déclare « non propre à 007 ». Ce précédent **ne couvre ni `numero` ni `created_at` de 009**, et le cadrage 009 ne contient aucune décision équivalente (§5).
5. Correction proposée (inchangée) : `length(CAST(numero AS BLOB)) = 12` et `length(CAST(created_at AS BLOB)) = 24`. **Vérifiée** sur 23 825 cas contre un oracle octet-à-octet : 0 divergence (avant : 1 400 + 840 acceptés à tort) ; 0 rejet d'une valeur conforme ; couvre NUL final, NUL + queue, NUL inséré/remplacé, NUL au début, NUL seul (§2).
6. **Propagation** : une origine V6 `PVR-50001-26␀` ne peut plus exister, donc aucune levée ne peut en dériver. **Reste** : une origine `import` à numéro libre contenant un NUL transmet ce NUL à sa levée (G4, égalité binaire) — hors correction, relève de Z-8 (§2.4).
7. Tests : 1 test existant à inverser, 13 cas à ajouter pour la correction minimale (+6 pour l'option JSON) ; 9 cas déjà couverts (§3).
8. Mutation : les 19 survivants sont des équivalents **prouvés par un script qui ne lit pas le SQL du dépôt** et **hors dépôt** ; reproductible aujourd'hui seulement si l'on dispose du script (30 s), pas depuis le dépôt seul (§4). Distinct de la correction NUL, dont il ne dépend pas.
9. Documentation : 3 formulations à corriger (docstring du test, rapport §5, mon propre §7.2-1) ; cadrage et documents officiels **non touchés** sans autorisation (§5).
10. Décisions attendues : §7. Je m'arrête là.

---

## 1. Inventaire 001–008 : colonnes dont la validation peut présenter le même défaut

### 1.1 Méthode (reproductible)

- Schéma après application des migrations 001→008 (rang 11) dans une base mémoire jetable ; extraction de chaque `CHECK` de colonne et de table (`schema_dump.py`). Lecture seule du dépôt.
- Classement de chaque colonne par mécanisme : **TS** (`GLOB` horodatage), **D** (`GLOB` + `date(x) IS x`), **DEC** (décimaux TEXT D2/DL : `GLOB` + `NOT GLOB`), **NUM** (`PRÉFIXE-nnnnn-yy` + `substr`), **CODE** (`CLI-nnnn`/`FOU-nnnn`), **ENUM** (`IN (…)`), **JSON** (`json_valid`).
- Pour chaque colonne : **essai de reproduction** — clone STRICT du `CHECK` réel (ou `INSERT` réel sur la chaîne complète, FK actives, triggers, quand les autres CHECK l'exigeaient) avec une valeur conforme, puis ses variantes : NUL final, NUL + queue, NUL + queue longue, NUL au milieu (remplacement et insertion), NUL au début, NUL seul. Une colonne n'est classée « vulnérable » que si au moins une variante est **acceptée** ; « non vulnérable » si **toutes** sont refusées **et** la valeur conforme est acceptée.
- Une colonne n'est donc pas présumée vulnérable parce qu'elle utilise `GLOB` : les dates sont protégées par `date(x) IS x` (égalité binaire), les énumérations par `IN` (comparaison binaire).

### 1.2 Résultat

| Classe | Mécanisme | Colonnes | Vulnérables | Non vulnérables |
|---|---|---:|---:|---:|
| TS | `GLOB` horodatage 24 car. | 41 | **41** | 0 |
| DEC | `GLOB` + `NOT GLOB` (D2, DL) | 26 | **26** | 0 |
| JSON | `json_valid(x)` | 17 | **17** | 0 |
| NUM | `PRÉFIXE-nnnnn-yy` + `substr` | 4 | **4** | 0 |
| CODE | `CLI-nnnn` / `FOU-nnnn` | 2 | **2** | 0 |
| D | `GLOB` + `date(x) IS x` | 16 | 0 | **16** |
| ENUM | `IN (…)` | 31 | 0 | **31** |
| **Total** | | **137** | **90** | **47** |

(La colonne `numerotation_sequences.type_objet`, non évaluée par la recherche automatique, a été évaluée à la main : `'CLI'||char(0) IN (…)` vaut 0 → non vulnérable ; elle est comptée dans les 31.)

### 1.3 Constats saillants

- **Horodatages (41).** Tous les `created_at`/`updated_at`/`*_at` à `GLOB` seul acceptent NUL final et NUL + queue. Dans le schéma actuel ils sont remplis par `DEFAULT (strftime(…))`, qui ne produit jamais de NUL ; le risque n'existe que si le service écrit explicitement la colonne. *Écriture explicite côté service : non vérifié.*
- **Décimaux (26).** Famille **D2** (montants `0.00`) : NUL final / queue acceptés — c'est le cas documenté par 007 §6 (2). Famille **DL** (10 colonnes : `quantite`, `prix_unitaire_ht`, `remise_valeur` de `devis_lignes`, `bc_lignes`, `facture_lignes`, plus `prestations.prix_unitaire_ht`) : **un NUL au début ou au milieu passe aussi** — la valeur `␀` suivie de n'importe quoi est acceptée, car ces CHECK n'ont aucun `GLOB` positif. Confirmé par `INSERT` réel sur `prestations`. Les calculs (`CAST`, `REPLACE`) lisent jusqu'au NUL : la valeur lue diffère de la valeur stockée. *Effet sur les services/triggers de calcul : non étudié.*
- **JSON (17).** `json_valid('{}'||char(0)||'junk')` vaut 1 : snapshots, `legacy_data`, `contenu`, `donnees` acceptent une queue après NUL. Un NUL placé **à l'intérieur** du JSON (`{␀}`) est refusé ; l'échappement légitime `"\u0000"` (texte, sans octet NUL) reste accepté.
- **Numéros (4) et codes (2).** Même défaut que `pv.numero` (`devis`, `bons_commande`, `factures`, `depenses` ; `clients.code`, `fournisseurs.code`). Pour les codes, `UNIQUE` ne protège pas : `CLI-0001` et `CLI-0001␀` coexistent.
- **Non vulnérables (47).** 16 dates (`GLOB` + `date(x) IS x`) et 31 énumérations (`IN`) : toutes variantes refusées.

### 1.4 Limites de cet inventaire (à ne pas dépasser)

- Il porte sur les **CHECK**. Les triggers 001–008 n'utilisent pas `GLOB` (vérifié par recherche textuelle dans les migrations) ; leurs lectures de colonnes (`CAST`, `substr`, comparaisons) n'ont pas été auditées pour ce défaut.
- Les services Rust/TS qui écrivent ces colonnes ne sont pas dans le dépôt analysé : qu'ils filtrent ou non les NUL en amont est **inconnu**.
- Aucune migration 001–008 n'est modifiée ni proposée à la modification ici (D4, §7).

### 1.5 Tableau détaillé (une ligne par groupe de colonnes de même règle ; 70 lignes)

| Table | Colonnes | Fichier(s) définissant la règle courante | Règle de format | Risque identifié | Essai de reproduction |
|---|---|---|---|---|---|
| `bc_devis` | `created_at` | 005b | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `bc_ligne_garanties` | `garantie_type` | 005b (antérieur : 004) | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `bc_ligne_garanties` | `created_at` | 005b (antérieur : 004) | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `bc_lignes` | `quantite`, `prix_unitaire_ht`, `remise_valeur` | 004 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, **NUL au début et au milieu** (famille DL : aucun `GLOB` positif) ; la valeur `␀`+n'importe quoi passe · clone STRICT du CHECK réel |
| `bc_lignes` | `unite`, `remise_type`, `type_prestation` | 004 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `bc_lignes` | `total_ht`, `remise_valeur` | 004 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `bc_lignes` | `created_at`, `updated_at` | 004 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `bons_commande` | `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot`, `legacy_data` | 005b (antérieur : 004) | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `bons_commande` | `date_creation`, `date_acceptation`, `date_debut`, `date_fin`, `date_100_facture` | 005b (antérieur : 004) | D `YYYY-MM-DD` — `GLOB` + `date(x) IS x` | aucun (`date(x) IS x` échoue) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `bons_commande` | `montant_contractuel_ht`, `montant_deja_facture_ht`, `avancement` | 005b (antérieur : 004) | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `bons_commande` | `statut`, `origine` | 005b (antérieur : 004) | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `bons_commande` | `numero` | 005b (antérieur : 004) | `PRÉFIXE-nnnnn-yy` + `substr(numero,11,2)=substr(date,3,2)` — `GLOB` + `substr` | idem + numéro non conforme stocké ; `yy` lu avant le NUL | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `bons_commande` | `completed_at`, `cancelled_at`, `frozen_at`, `created_at`, `updated_at` | 005b (antérieur : 004) | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `categories_depenses` | `created_at`, `updated_at` | 001 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `categories_prestations` | `created_at`, `updated_at` | 001 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `clients` | `code` | 005a (antérieur : 001) | `CLI-nnnn` / `FOU-nnnn` — `GLOB` seul | deux codes affichés à l'identique coexistent malgré `UNIQUE` (`CLI-0001␀` ≠ `CLI-0001`) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · INSERT réel (chaîne complète, FK ON, triggers) |
| `clients` | `origine` | 005a (antérieur : 001) | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `clients` | `legacy_data` | 005a (antérieur : 001) | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · INSERT réel (chaîne complète, FK ON, triggers) |
| `clients` | `created_at`, `updated_at` | 005a (antérieur : 001) | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · INSERT réel (chaîne complète, FK ON, triggers) |
| `depenses` | `date_depense` | 005 | D `YYYY-MM-DD` — `GLOB` + `date(x) IS x` | aucun (`date(x) IS x` échoue) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `depenses` | `montant` | 005 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · INSERT réel (chaîne complète, FK ON, triggers) |
| `depenses` | `numero` | 005 | `PRÉFIXE-nnnnn-yy` + `substr(numero,11,2)=substr(date,3,2)` — `GLOB` + `substr` | idem + numéro non conforme stocké ; `yy` lu avant le NUL | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · INSERT réel (chaîne complète, FK ON, triggers) |
| `depenses` | `cancelled_at`, `created_at`, `updated_at` | 005 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis` | `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot`, `legacy_data` | 005a (antérieur : 003) | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis` | `date_creation`, `date_validite`, `date_acceptation`, `date_refus` | 005a (antérieur : 003) | D `YYYY-MM-DD` — `GLOB` + `date(x) IS x` | aucun (`date(x) IS x` échoue) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `devis` | `statut`, `remise_type`, `acompte_type`, `origine` | 005a (antérieur : 003) | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `devis` | `total_ht`, `remise_valeur`, `acompte_valeur` | 005a (antérieur : 003) | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis` | `numero` | 005a | `PRÉFIXE-nnnnn-yy` + `substr(numero,11,2)=substr(date,3,2)` — `GLOB` + `substr` | idem + numéro non conforme stocké ; `yy` lu avant le NUL | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis` | `frozen_at`, `cancelled_at`, `created_at`, `updated_at` | 005a (antérieur : 003) | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis_ligne_garanties` | `garantie_type` | 003 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `devis_ligne_garanties` | `created_at` | 003 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis_lignes` | `quantite`, `prix_unitaire_ht`, `remise_valeur` | 003 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, **NUL au début et au milieu** (famille DL : aucun `GLOB` positif) ; la valeur `␀`+n'importe quoi passe · clone STRICT du CHECK réel |
| `devis_lignes` | `unite`, `remise_type`, `type_prestation` | 003 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `devis_lignes` | `total_ht`, `remise_valeur` | 003 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis_lignes` | `created_at`, `updated_at` | 003 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis_revisions` | `contenu` | 005a | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis_revisions` | `total_ht` | 005a | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `devis_revisions` | `valide_at`, `created_at` | 005a | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `facture_lignes` | `quantite`, `prix_unitaire_ht`, `remise_valeur` | 006 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, **NUL au début et au milieu** (famille DL : aucun `GLOB` positif) ; la valeur `␀`+n'importe quoi passe · clone STRICT du CHECK réel |
| `facture_lignes` | `unite`, `remise_type`, `type_ligne` | 006 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `facture_lignes` | `montant_ht`, `avancement_precedent_pct`, `avancement_cumule_pct`, `remise_valeur` | 006 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `facture_lignes` | `created_at` | 006 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `factures` | `type`, `origine` | 006 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `factures` | `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot`, `legacy_data` | 006 | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `factures` | `date_emission`, `date_echeance` | 006 | D `YYYY-MM-DD` — `GLOB` + `date(x) IS x` | aucun (`date(x) IS x` échoue) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `factures` | `total_ht`, `montant_deja_facture_ht` | 006 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `factures` | `numero` | 006 | `PRÉFIXE-nnnnn-yy` + `substr(numero,11,2)=substr(date,3,2)` — `GLOB` + `substr` | idem + numéro non conforme stocké ; `yy` lu avant le NUL | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `factures` | `created_at` | 006 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `fournisseurs` | `code` | 002 | `CLI-nnnn` / `FOU-nnnn` — `GLOB` seul | deux codes affichés à l'identique coexistent malgré `UNIQUE` (`CLI-0001␀` ≠ `CLI-0001`) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · INSERT réel (chaîne complète, FK ON, triggers) |
| `fournisseurs` | `created_at`, `updated_at` | 002 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `garanties` | `garantie_type` | 008 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `garanties` | `date_declenchement`, `date_fin_suivi` | 008 | D `YYYY-MM-DD` — `GLOB` + `date(x) IS x` | aucun (`date(x) IS x` échoue) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `garanties` | `created_at` | 008 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `import_anomalies` | `categorie`, `statut` | 001 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `import_anomalies` | `donnees` | 001 | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · INSERT réel (chaîne complète, FK ON, triggers) |
| `import_anomalies` | `created_at`, `traite_at` | 001 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `numerotation_sequences` | `type_objet` | 001 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | non évalué par la recherche → évalué à la main (`'CLI'‖␀ IN (…)` = 0) : NON VULNÉRABLE · clone STRICT du CHECK réel |
| `numerotation_sequences` | `derniere_date` | 001 | D `YYYY-MM-DD` — `GLOB` + `date(x) IS x` | aucun (`date(x) IS x` échoue) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `numerotation_sequences` | `created_at`, `updated_at` | 001 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `prestation_garanties` | `garantie_type` | 001 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `prestation_garanties` | `created_at` | 001 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `prestations` | `unite`, `type_prestation`, `origine` | 001 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `prestations` | `prix_unitaire_ht` | 001 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, **NUL au début et au milieu** (famille DL : aucun `GLOB` positif) ; la valeur `␀`+n'importe quoi passe · INSERT réel (chaîne complète, FK ON, triggers) |
| `prestations` | `legacy_data` | 001 | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `prestations` | `created_at`, `updated_at` | 001 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `reglements` | `type`, `mode`, `origine` | 007 | liste fermée `IN (...)` (comparaison binaire) | aucun (comparaison binaire) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `reglements` | `date_evenement` | 007 | D `YYYY-MM-DD` — `GLOB` + `date(x) IS x` | aucun (`date(x) IS x` échoue) | NON VULNÉRABLE — toutes variantes refusées · clone STRICT du CHECK réel |
| `reglements` | `montant` | 007 | familles décimales TEXT (D2/DL…) — `GLOB` positifs + `NOT GLOB '*[^0-9.]*'` etc. | montant/quantité stocké avec queue ; `CAST`/`REPLACE` lisent jusqu'au NUL (valeur lue ≠ valeur stockée) ; précédent documenté : cadrage 007 §6 (2) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `reglements` | `cancelled_at`, `created_at` | 007 | TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (24 car.) — `GLOB` seul | horodatage stocké avec octets parasites ; tri/comparaison de chaînes faussés (`x␀ > x`) ; en pratique rempli par `DEFAULT` (écriture explicite côté service : non vérifié) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |
| `reglements` | `legacy_data` | 007 | `json_valid(x)` (le contrôle ne porte pas sur un `GLOB`) | document stocké avec queue ; `json_valid`, `json_extract`, `json_type` lisent jusqu'au NUL (conséquence sur les lecteurs non étudiée) | VULNÉRABLE — acceptés : NUL final, NUL+queue, NUL+queue longue ; refusés : NUL au milieu, au début · clone STRICT du CHECK réel |

---

## 2. Migration 009 : formats normatifs et vérification de la correction

### 2.1 Formats normatifs exacts

| Colonne | Format normatif | Source | Traduction SQL actuelle (`009_pv.sql`) | Longueur |
|---|---|---|---|---|
| `pv.numero`, **PV initial V6** (`origine='v6'`, `type <> 'levee_reserves'`) | `PVR-` + 5 chiffres + `-` + 2 chiffres ; `yy` = année de `date_reception` | **[RD]** INV-20 (`invariants` l.47) ; modèle §6 (l.709, `PVR-00001-26`) ; modèle §10.4 et INV-131 (exemption limitée à `origine='import'`) ; cadrage 009 l.88 et l.195 | `numero GLOB 'PVR-[0-9]{5}-[0-9]{2}' AND substr(numero,11,2) = substr(date_reception,3,2)` (CHECK de table, l.111-113) | **12 octets** ASCII (le motif impose 12 caractères ASCII : caractères = octets) |
| `pv.numero`, **levée** | `<numéro de l'origine>-<suffixe sur 2 chiffres>` (`PVR-00001-26-01`) | **[RD]** INV-20 ; modèle §4.11 / §6 (l.710) ; cadrage 009 l.70 | **aucun CHECK de format** (**[PR-3]**) ; imposé par le trigger G4 : `NEW.numero = o.numero || '-' || printf('%02d', NEW.suffixe)` (égalité binaire) | 15 octets si l'origine est au format V6 |
| `pv.numero`, `origine='import'` | libre, non vide, unique ; immuable | **[RD]** INV-27, INV-131, modèle §10.4 | `CHECK (numero <> '')` + `UNIQUE` | libre |
| `pv.created_at` | `YYYY-MM-DDTHH:MM:SS.SSSZ` (UTC), type **TS**, contrôlé par `GLOB` | **[RD]** modèle (table des types, l.79 : « **TS** … `GLOB` ») ; INV-10 ; cadrage 009 l.198 | `created_at GLOB '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3}Z'` (l.114-115) ; défaut `strftime('%Y-%m-%dT%H:%M:%fZ','now')` | **24 octets** ASCII |
| `pv.date_reception` | `YYYY-MM-DD` (date réelle) | **[RD]** INV-10 | `GLOB … AND date(date_reception) IS date_reception` | non concerné (protégé) |

**Constat de lecture.** Le modèle prescrit `GLOB` comme *mécanisme* de contrôle du type TS ; il prescrit aussi le *format* (24 caractères exacts). Une valeur `…Z␀junk` viole le format et passe le mécanisme : la correction proposée ne change aucune règle, elle rend le mécanisme conforme à la règle. Elle ajoute un conjoncte à côté du `GLOB` prescrit ; elle ne le remplace pas.

### 2.2 Pourquoi `length(CAST(x AS BLOB)) = n` est suffisant (raisonnement)

Si le `GLOB` réussit, les `n` premiers caractères **avant le premier NUL** sont exactement le motif. Un NUL éventuel est donc situé après eux, et la longueur en octets (le BLOB n'est pas tronqué au NUL) dépasse `n`. Inversement une valeur conforme a exactement `n` octets, sans NUL. La colonne est `TEXT` en table `STRICT` : un BLOB est refusé en amont, la conversion ne s'applique qu'à du TEXT.

### 2.3 Résultats d'exécution (SQLite 3.45.1, SQL réel de 009 + variante corrigée en mémoire)

| Cas | Exemple | SQL actuel | SQL corrigé |
|---|---|:--:|:--:|
| NUL final | `PVR-50001-26␀` | **accepté** | refusé |
| NUL + queue | `PVR-50001-26␀junk` | **accepté** | refusé |
| NUL + queue longue (≥ 50 octets) | | **accepté** | refusé |
| NUL au milieu (remplacement de chaque caractère) | `PVR-5␀001-26` | refusé | refusé |
| NUL inséré à chaque position | | refusé | refusé |
| NUL au début ; NUL seul | `␀PVR-50001-26`, `␀` | refusé | refusé |
| Idem pour `created_at` : NUL final / NUL + queue | `…00.000Z␀`, `…Z␀junk` | **accepté** | refusé |
| `created_at` : NUL au milieu / début | | refusé | refusé |
| `yy` ≠ année de `date_reception` | `PVR-50001-27` / 2026 | refusé | refusé |
| **Valeurs conformes** (200 numéros, 120 `created_at`, défaut `strftime`) | | accepté | **accepté** |
| `created_at` d'une levée conforme / avec NUL + queue | | accepté / **accepté** | accepté / refusé |
| `date_reception` (NUL final, + queue, milieu, début) | | refusé | refusé (inchangé) |

**Fuzz différentiel** : 23 825 cas (11 436 `numero`, 12 389 `created_at` : conformes, near-miss, NUL à chaque position, queues) comparés à un oracle Python octet-à-octet (regex stricte sur les octets). SQL actuel : **1 400** numéros et **840** `created_at` acceptés à tort. SQL corrigé : **0 divergence**, aucun faux rejet.
**Suite existante** (255 tests) rejouée sur copie corrigée : 254 passent ; seul `test_T51_K_LIMITE_le_GLOB_de_sqlite_s_arrete_au_premier_octet_nul_CONSTAT` échoue — attendu, il constate l'acceptation.

### 2.4 Propagation depuis le numéro d'origine (levée)

La levée n'a pas de CHECK de format ; son numéro est `origine.numero || '-' || suffixe` par égalité **binaire** (G4). Un NUL déjà présent dans l'origine est donc recopié.

| Origine | Levée dérivée | SQL actuel | SQL corrigé |
|---|---|:--:|:--:|
| V6 `PVR-50001-26␀` | `PVR-50001-26␀-01` | origine **acceptée**, levée **acceptée** | **origine refusée** → aucune levée possible |
| V6 conforme | `PVR-50002-26-01` | accepté | accepté |
| V6 conforme | `…-01␀`, `…-01␀junk`, `…␀-01`, `…-0␀1` | refusés (G4) | refusés (G4) |
| `import` `ANCIEN␀` (numéro libre) | `ANCIEN␀-01` | origine et levée **acceptées** | **acceptées (inchangé)** |

Conclusion : pour l'origine V6, la correction supprime la propagation à la source. Pour l'origine `import`, le NUL reste possible **par conception** (numéro libre, INV-131) et se propage à la levée. Ce cas relève de Z-8 / QO-2 (hors périmètre de migration : la V2 ne contient aucun PV) ; **je ne propose pas de l'inclure**. Il sera consigné par un test témoin (§3, cas 11).

### 2.5 Portabilité (HYPOTHÈSE sur la version embarquée)

`length(CAST(x AS BLOB))` est disponible dans toutes les versions de SQLite ; `octet_length()` exige ≥ 3.43 (non retenu tant que la version Tauri n'est pas vérifiée). Aucune fonction JSON1 ni `instr` n'est requise pour la correction minimale.

### 2.6 Option JSON (hors correction minimale — à décider séparément)

Les snapshots et `legacy_data` de 009 utilisent `json_valid` : `{}␀junk` est accepté (FAIT). Option B : `json_valid(x) AND instr(CAST(x AS BLOB), x'00') = 0`. Vérifié : `{}`, `{"a":1}`, `"\u0000"` échappé, Unicode, `[]`, `5` acceptés ; `{}␀`, `{}␀junk`, `{␀}`, `␀{}` refusés. Cette option élargit le périmètre à cinq colonnes ; elle **n'est pas** incluse dans le diff principal (D3).

---

## 3. Tests de non-régression : déjà couvert / manquant (aucun test modifié)

### 3.1 Déjà couvert (comportement inchangé par la correction)

| # | Cas | Test existant (`test_009_pv.py`) | Réserve |
|---|---|---|---|
| C1 | Numéro V6 conforme accepté | `test_T51_B_numero_d_un_pv_initial_v6_au_format_PVR_nnnnn_yy` (l.872) | pas de bornes `99999-99` explicites |
| C2 | Numéro hors format refusé (préfixe, chiffres, séparateur, longueur ±1 à chaque position) | `…_hors_format_refuse` (l.878), `…_chaque_chiffre_…` (l.975), `…_chaque_caractere_…_y_compris_longueur` (l.984) | **aucun jeu de caractères ne contient NUL** |
| C3 | `yy` ≠ année de `date_reception` | `…_annee_du_numero_egale_…` (l.886) | |
| C4 | `created_at` conforme accepté / hors format refusé, chaque position | `test_T51_B_created_at_canonique_…` (l.717), `…_chaque_position_de_created_at_…` (l.993) | substituants `a`, `X`, espace : pas de NUL |
| C5 | NUL dans `date_reception` (final, final + queue, début) refusé | `test_T51_K_octet_nul_dans_les_textes` (l.2435) | |
| C6 | NUL dans `type` refusé | idem (l.2440) | |
| C7 | Numéro de levée avec NUL final refusé par G4 | idem (l.2444) | NUL final seulement |
| C8 | `UNIQUE(numero)` ; numéro libre pour `origine='import'` | l.865 ; l.915 | sans NUL |
| C9 | `numero` / `created_at` immuables par `UPDATE` (le NUL ne peut entrer que par `INSERT`) | `test_T51_E_update_de_chaque_colonne_refuse_avec_une_valeur_differente` (l.1581 ; `VALEURS_UPDATE` l.1553, qui inclut `numero` et `created_at`) | |

### 3.2 À adapter (1 test, correction minimale)

| # | Test | Adaptation |
|---|---|---|
| A1 | `test_T51_K_LIMITE_le_GLOB_de_sqlite_s_arrete_au_premier_octet_nul_CONSTAT` (l.2446-2451) | Il assertit l'**acceptation** (`assertIsNone`) de `PVR-50001-26␀`, `…␀junk`, `created_at …Z␀`. À inverser en assertions de **rejet** (CHECK, sans préfixe `INV-`) et à renommer sans « LIMITE / CONSTAT » ; docstring à réécrire (§5). |
| A2 | *(option JSON seulement)* constante `C_LEGACY_JSON` (l.631) | Fragment « `legacy_data IS NULL OR json_valid(legacy_data)` » = texte exact du CHECK : 4 sous-tests de `test_T51_B_origine_import_legacy_optionnels_et_json_controle` (`''`, `'{'`, `'x'`, `"{'a':1}"`) échouent avec l'option B **sans changement de comportement**. Raccourcir le fragment en `json_valid(legacy_data)`. |

Les constantes `C_NUMERO_V6` (`numero GLOB 'PVR-`) et `C_CREATED` (`created_at GLOB`) sont des préfixes : elles restent valides après la correction minimale.

### 3.3 À ajouter — correction minimale (13 cas)

| # | Cas | Attendu | Tue |
|---|---|---|---|
| M1 | Numéro V6 sans réserves, NUL final ; l'origine refusée ⇒ **aucune ligne** et aucune levée dérivable | rejet CHECK (`C_NUMERO_V6`) | suppression du conjoncte numéro |
| M2 | NUL + queue ; NUL + queue ≥ 50 octets | rejet | `=` → `>=`, constante 12 → 13 |
| M3 | Numéro V6 **avec réserves**, NUL final | rejet | |
| M4 | NUL remplaçant chacun des 12 caractères, inséré à chacune des 13 positions, au début, seul | rejet (non-régression : déjà refusés) | |
| M5 | Numéros conformes aux bornes : `PVR-00001-yy`, `PVR-99999-99`, années 01, 26, 99 | accepté (anti-faux-rejet) | `= 12` → `<> 12`, 11 |
| M6 | `created_at` explicite : NUL final, NUL + queue | rejet (`C_CREATED`) | suppression du conjoncte `created_at` |
| M7 | `created_at` : NUL à chaque position, au début | rejet | |
| M8 | `created_at` conforme : `….000Z`, `….999Z`, valeur par défaut | accepté | constante 24 → 23/25 |
| M9 | `created_at` d'une **levée** avec NUL + queue | rejet | |
| M10 | `UNIQUE` : `PVR-50001-26` puis `PVR-50001-26␀` | second refusé **par le CHECK** (message CHECK, pas UNIQUE) | |
| M11 | `origine='import'`, numéro libre avec NUL ; levée dérivée de cette origine | accepté — **témoin de périmètre Z-8**, nommé « CONSTAT », ne valide pas | |
| M12 | Témoin : table de contrôle = DDL de 009 **sans** le conjoncte de longueur ; insertion de `…␀junk` | accepté ⇒ le conjoncte de longueur est la **seule** garde | |
| M13 | Levée dont le numéro porte un NUL au milieu / une queue (origine conforme) | rejet par G4 (C7 ne couvre que le NUL final) | |

### 3.4 À ajouter — option JSON (6 cas, seulement si D3 = oui)

J1 snapshot (3 colonnes) NUL final → rejet · J2 snapshot NUL + queue → rejet · J3 `legacy_data` (`origine='import'`) NUL final / queue → rejet · J4 JSON conformes acceptés, dont `"\u0000"` échappé et Unicode · J5 NUL dans le JSON (`{␀}`) toujours refusé (non-régression) · J6 témoin sans `instr` : `{}␀junk` accepté.

### 3.5 Bilan

9 cas déjà couverts (C1–C9) · 1 test à adapter (+1 avec l'option JSON) · 13 cas à ajouter (+6 avec l'option JSON). Tout ajout ou adaptation est **subordonné à D5** ; aucun test n'est modifié ici.

---

## 4. Mutation : rendre les preuves des 19 survivants reproductibles depuis le dépôt

*(Point distinct de la correction NUL : il n'élargit pas son périmètre et n'en dépend pas.)*

### 4.1 État actuel : ce qui est reproductible, ce qui ne l'est pas

Les 19 survivants (S01–S19) sont tous qualifiés équivalents (E1–E7). Le rapport 009 (l.5) précise que les outils sont « hors dépôt ».

| Outil (hors dépôt) | Lignes | sha256 (16 prem.) | Rôle | Lisible depuis le dépôt ? |
|---|---:|---|---|:--:|
| `mut009.py` | 585 | `d8dcd8636731be01` | génère et exécute les 692 mutants sur une copie du dépôt (`mut009.py ROOT WORKD [ONLY]`) ; produit `survivors009.txt`, `invalides009.txt`, `killers009.json` | **non** (outil absent) |
| `genmut009.py` | 13 | `6dbc84f853772548` | liste les mutants sans les exécuter (enveloppe de `mut009.py`) | non |
| `classify009.py` | 33 | `c6e9881212e5aceb` | classe survivants/tués/invalides à partir de `mut009_final_*.json/.txt` | non — dépend en plus de **sorties de campagne** non versionnées |
| `equiv009.py` | 122 | `2f6bb8f303db2a4d` | preuves E1–E6 sur le moteur SQLite réel, domaines énumérés, avec témoins ; sortie « TOUT EST OK » | non |
| *(E7)* | — | — | `FOR EACH ROW` dupliqué : argument textuel (comportement par défaut de SQLite), **aucun script** | — |
| `mut006/007/008.py` & dérivés | — | — | ancêtres de `mut009.py` (le rapport dit « dérivés de ceux de 008 ») : eux aussi hors dépôt | non |

**Rejouabilité constatée (FAIT)** : `equiv009.py` se rejoue seul en ≈ 30 s avec Python 3.11.15 / SQLite 3.45.1 : 15 lignes « OK » (preuves et témoins), 0 « ECHEC », « TOUT EST OK ».
**Limite de fond** : `equiv009.py` **ne lit pas `009_pv.sql`**. Les expressions mutées (`substr(numero,11,3)`, GLOB de date affaibli, `%02i`, jointures `pv o, pv x`, `IS`→`=`) y sont **retapées à la main**. Si le SQL change, la preuve reste « OK » sans que rien ne dise qu'elle concerne encore le bon texte. Ce que le dépôt ne permet pas de vérifier : (1) que les 19 mutants énumérés correspondent au SQL livré ; (2) que les preuves portent sur les expressions réelles ; (3) la campagne de 692 mutants elle-même.
Les preuves sont aussi **relatives** au moteur 3.45.1 et au reste du schéma (rapport §5 : E1, E3, E5, E6 ; kills structurels `NO ACTION` ≡ `RESTRICT` non démontrés pour une autre version).

### 4.2 Outils manquants pour une reproductibilité complète depuis le dépôt

1. Générateur/exécuteur de mutants (`mut009.py` + `genmut009.py`) et ses dépendances de tranche (`mut008.py`… si l'on veut comparer les campagnes).
2. Script de preuves (`equiv009.py`) **relié au SQL réel** (extraction des expressions depuis `009_pv.sql`).
3. Données de campagne : liste des survivants (S01–S19 avec identifiant, ligne, description, preuve), killers, invalides.
4. Environnement épinglé : Python 3.11.15, SQLite 3.45.1 (les preuves sont relatives au moteur).
5. Commande de relance documentée et résultat attendu (692 / 670 / 3 / 0 / 19, ou nouveaux chiffres après correction).

### 4.3 Options (rien n'est ajouté ni versionné ici)

| Option | Contenu | Reproductibilité | Coût / réserve |
|---|---|---|---|
| **O1** Versionner les 4 outils dans un dossier d'outils du dépôt (`tools/mutation/` ou `src-tauri/tests/outils/`) + README + liste des survivants en données | complète pour 009 | ≈ 750 lignes de code de travail à maintenir ; à étendre à 006–008 pour la cohérence ; décision de structure du dépôt (hors de mes pouvoirs) |
| **O2** Annexe au rapport 009 : code de `equiv009.py` (122 lignes) en annexe | preuves E1–E6 relisibles et rejouables par copier-coller | ne couvre ni la campagne ni le lien avec le SQL réel |
| **O3** Archive figée hors dépôt (tar des 4 outils + sorties de campagne) avec **sha256 consigné dans le rapport** | traçabilité (on sait quel outil a produit quoi) ; rejouable par qui possède l'archive | pas reproductible depuis le dépôt seul |
| **O4** Test d'équivalence dans la suite : charge `009_pv.sql`, extrait les expressions, rejoue E1–E6 | le lien SQL ↔ preuve devient automatique et casse si le SQL change | ≈ 30 s (E5 domine, allégeable) ; ne remplace pas la campagne de mutation |
| **O5** Minimum : consigner dans le rapport version Python/SQLite, sha256 + longueur des 4 outils, commande de relance exacte | traçabilité seulement | n'ajoute rien de rejouable |

**Recommandation (si Rémy veut agir)** : O5 + O3 immédiatement (aucun fichier ajouté au dépôt), O1 ou O4 si la reproductibilité depuis le dépôt devient une exigence de qualité. À décider séparément (D7).

### 4.4 Effet de la correction NUL sur la mutation (si autorisée)

- **Campagne complète à relancer** : le SQL et la suite changent ; les numéros de ligne des noms de mutants (`L111`, `L114`) changent ; les chiffres 692 / 670 / 3 / 19 ne sont plus valables avant relance.
- **Nouveaux mutants** sur les deux conjonctes (constantes 12 → 11/13 et 24 → 23/25, `CAST … AS BLOB` retiré, `AND` → `OR`, conjoncte supprimé, `=` → `<>` / `<=` / `>=`). Les cas M1–M13 sont conçus pour les tuer.
- **Équivalents probables à prévoir (non démontrés)** : `length(…) <= 12` (resp. `<= 24`) ≡ `= 12` (resp. `= 24`) car le `GLOB` impose déjà ≥ 12 (resp. 24) octets avant tout NUL ; à qualifier **après** relance, par preuve exhaustive, sans présumer.
- **Preuves existantes à refaire** : E2 (`substr(numero,11,3)`, rédigée « queues NUL comprises ») et E3 ; `equiv009.py` doit être mis à jour (donc modifié) ; E1, E4–E7 sont inchangés dans leur principe.

---

## 5. Documentation : corrections minimales

### 5.1 Ce que disent les sources (lecture)

| Source | Ce qu'elle dit réellement | Décision explicite sur le NUL ? |
|---|---|:--:|
| `CADRAGE__009_pv.md` §5 point 8 (l.282) et §6 groupe K (l.304) | prévoit des **tests** « REAL/BLOB/NUL dans colonnes TEXT (STRICT) » ; n'énonce pas le résultat attendu pour `numero`/`created_at` | **non** |
| `CADRAGE__009_pv.md` §3.6 (« Limites des sondes ») | ne mentionne aucun NUL | **non** |
| `CADRAGE__009_pv.md` l.195, l.198 | format `PVR-nnnnn-yy` [RD] et `created_at : GLOB TS` [RD] | non (règles de format) |
| `CADRAGE__007_reglements.md` §6 « Limites connues » (2), l.193 | **documente** : « un montant `'1.00' \|\| char(0)` traverse les `GLOB` de la famille D2 … limite commune à toutes les tables 001–006 … non propre à 007 » | **oui, mais pour les montants D2 de 001–006 et 007 seulement** |
| `RAPPORT_MUTATION__009_pv.md` §5, l.123 | « Limite non corrigée, commune à tous les CHECK `GLOB` de la chaîne … (aucune règle documentaire ne l'exige) » | attribue implicitement une décision |
| `test_009_pv.py` l.2447 (docstring) | « LIMITE constatée, NON corrigée par 009 (cadrage validé) … comportement de TOUS les CHECK GLOB de la chaîne » | **attribue explicitement** une décision au cadrage |

**Lecture.** Le cadrage 009 n'a pas décidé de laisser le défaut. Le précédent de 007 §6 (2) est réel mais étroit : il décrit un NUL **final** sur des **montants D2**, dans des tables où les calculs passent par `CAST`/centimes. Il n'autorise ni l'extension aux numéros PV (INV-20), ni aux horodatages TS. Les trois formulations ci-dessous prêtent donc à tort une décision au cadrage, et deux affirment « tous les CHECK GLOB » alors que les dates (`date(x) IS x`) et les énumérations (`IN`) y échappent (§1).

### 5.2 Corrections minimales proposées (non appliquées)

**(a) Docstring de `test_T51_K_LIMITE_…` (`test_009_pv.py`, l.2447-2448)**
- *Ancien* : `LIMITE constatée, NON corrigée par 009 (cadrage validé) : GLOB ne lit pas au-delà d'un octet NUL ; … C'est le comportement de TOUS les CHECK GLOB de la chaîne (created_at depuis 001). Ce test documente la limite : il ne la valide pas.`
- *Nouveau, si la correction n'est pas autorisée* : `LIMITE constatée, NON corrigée dans la livraison 009 (aucune décision documentaire sur ce point ; voir COMPLEMENT_ANALYSE__009_pv__controle_nul.md) : GLOB ne lit pas au-delà d'un octet NUL ; … C'est le comportement des CHECK à GLOB seul de la chaîne (horodatages depuis 001, numéros, codes, décimaux) ; les dates (date(x) IS x) et les listes IN y échappent. Ce test documente la limite : il ne la valide pas.`
- *Si la correction est autorisée* : le test est inversé (A1, §3.2) et la docstring devient `Un octet NUL ne peut pas suivre un numéro PV initial V6 ni un created_at : la longueur est contrôlée en octets (GLOB, substr et length() de TEXT s'arrêtent au premier NUL).`

**(b) `RAPPORT_MUTATION__009_pv.md` §5, l.123**
- *Ancien* : `Limite non corrigée, commune à tous les CHECK GLOB de la chaîne : … Constaté et consigné par un test (groupe K), non corrigé en SQL (aucune règle documentaire ne l'exige).`
- *Nouveau, si la correction n'est pas autorisée* : `Limite constatée, non corrigée dans cette livraison, commune aux CHECK à GLOB seul de la chaîne (horodatages, numéros, codes, décimaux ; pas les dates ni les listes IN) : GLOB et substr s'arrêtent au premier octet NUL ; un numero ou un created_at avec queue après un NUL passe le CHECK de format. Constaté et consigné par un test (groupe K). Le cadrage 009 ne contient pas de décision sur ce point ; INV-20 et le modèle (type TS) définissent le format que cette limite ne respecte pas. Voir COMPLEMENT_ANALYSE__009_pv__controle_nul.md.`
- *Si la correction est autorisée* : puce remplacée par la description du conjoncte de longueur et renvoi à la relance de campagne (chiffres recalculés ; §4.4).

**(c) `COMPLEMENT_CADRAGE__009_pv__controle_nul.md` §7.2 (mon fichier précédent)**
- Point 1 : **ajouter** le précédent omis — « Le cadrage 007 §6 « Limites connues » (2) documente une limite NUL pour les montants D2 des tables 001–006 et 007 (NUL final, calculs en centimes) ; ce précédent ne couvre ni `numero`, ni `created_at`, ni la famille DL, et n'est pas repris par le cadrage 009. »
- Point 2 : remplacer « HYPOTHÈSE de même comportement, non vérifiée colonne par colonne » par le résultat vérifié du §1 du présent document (90/137 colonnes vulnérables ; 47 non vulnérables).
- Réponse à D4 : renvoyer au présent §1 pour la liste exacte.

**(d) `CADRAGE__009_pv.md` — aucune modification nécessaire** à l'implémentation. *Facultatif, seulement sur autorisation expresse (D6)* : ajouter à la fin du §3.6, sur le modèle de 007 §6, une ligne « Limite connue : `GLOB`, `substr` et `length()` de TEXT s'arrêtent au premier octet NUL ; la longueur de `numero` (PV initial V6) et de `created_at` est contrôlée en octets (`length(CAST(x AS BLOB))`) ; `date_reception` est protégée par `date(x) IS x` ; la levée et `origine='import'` ne sont pas concernés (PR-3, Z-8). » Les documents officiels (modèle, invariants, conventions) ne sont **pas** modifiés ; une mention de convention (« TS = `GLOB` + longueur en octets ») relèverait d'une décision séparée.

Aucune autre occurrence du défaut n'a été trouvée dans les MAJ__*.md, les cadrages 005–008 (hors 007 §6) ni le rapport 007 (l.110, qui renvoie au cadrage 007 §6 et reste exact).

---

## 6. Tableau de synthèse

| # | Point demandé | Résultat | Preuve | Reste à décider |
|---|---|---|---|---|
| 1 | Inventaire 001–008 | 137 colonnes évaluées : **90 vulnérables** (TS 41, DEC 26, JSON 17, NUM 4, CODE 2), **47 non vulnérables** (dates 16, énumérations 31) ; famille DL (10 col.) plus exposée (NUL au début/milieu) | §1, tableau de 70 lignes ; essais sur clone STRICT du CHECK réel et `INSERT` réels | D4 : traiter ou documenter 001–008 (hors 009) |
| 2a | Formats normatifs 009 | `numero` V6 initial : 12 octets `PVR-nnnnn-yy` ; `created_at` : 24 octets TS ; levée : dérivée par G4 (PR-3) ; import : libre | §2.1 (INV-20, INV-10, modèle l.79/709/710, §10.4) | — |
| 2b | La correction couvre-t-elle les cas ? | **Oui** : NUL final, NUL + queue, NUL inséré/remplacé, début, seul, NUL propagé d'une origine V6 ; 0 faux rejet ; 0 divergence sur 23 825 cas | §2.3-2.4 | D1, D2 |
| 2c | Propagation | Supprimée pour l'origine V6 ; **subsiste pour l'origine `import`** (numéro libre, Z-8) | §2.4 | D3 (confirmer hors périmètre) |
| 3 | Tests | 9 couverts ; 1 à inverser ; 13 à ajouter (+6 et 1 à adapter si JSON) | §3 | D5 |
| 4 | Mutation / 19 survivants | équivalents prouvés par `equiv009.py` (rejouable seul, 30 s) mais **hors dépôt et non relié au SQL réel** ; 4 outils + sorties de campagne à fournir | §4 | D7 (O1–O5) |
| 5 | Documentation | 3 formulations à corriger (docstring, rapport §5, mon §7.2-1) ; cadrage et documents officiels inchangés | §5 | D6 (mention facultative) |
| 6 | Diff SQL | proposé séparément, **non appliqué** | `PROPOSITION_DIFF__009_pv__controle_nul.md` | D5 |

---

## 7. Décisions attendues (aucune n'est présumée)

1. **D1** — Corriger `numero` (PV initial V6) par `length(CAST(numero AS BLOB)) = 12` ? (oui / non)
2. **D2** — Corriger `created_at` par `length(CAST(created_at AS BLOB)) = 24` ? (oui / non). *À confirmer par Rémy : le service écrit-il `created_at` explicitement, ou toujours via `DEFAULT` ?*
3. **D3** — Confirmer hors correction : `date_reception` (déjà protégée), la levée (PR-3), `origine='import'` et la propagation d'un NUL d'import (Z-8) ; et trancher l'**option JSON** (5 colonnes de 009) : oui / non.
4. **D4** — 001–008 (90 colonnes) : audit/correction dédiés, ou acceptation documentée sur le modèle de 007 §6 (2) ? Aucune migration existante n'est touchée sans autorisation expresse.
5. **D5** — Autoriser : modification de `009_pv.sql` (diff séparé), de `test_009_pv.py` (§3), du `RAPPORT_MUTATION__009_pv.md` (corrections §5.2 + relance complète des tests et des mutations, §4.4) ; sinon, autoriser seulement les corrections de formulation §5.2 (a)(b) « correction non autorisée ».
6. **D6** — Mention documentaire dans le cadrage 009 (§5.2 d) : oui / non.
7. **D7** — Reproductibilité des preuves de mutation (§4.3) : O1…O5 ou statu quo ; **sans lien avec D1–D5**.

Je ne démarre ni la correction, ni la relance, ni la tranche 010 avant ta décision explicite.
