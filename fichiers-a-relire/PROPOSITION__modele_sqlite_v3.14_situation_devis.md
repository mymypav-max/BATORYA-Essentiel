# PROPOSITION — Modifications du modèle SQLite V3.14 : couverture des situations (`situation_devis`)

**Nature** : document de proposition, **non officiel**. Il prépare la rédaction de `modèle-données-sqlite-v6-v3.14.md`. Il ne modifie ni `docs/`, ni SQL, ni test.
**Date** : 2026-10-18 · **Base décisionnelle** : les 9 décisions validées par le propriétaire le 2026-10-18 (listées dans `ETUDE__rattachement_explicite_situations_devis.md` §0.1).
**Convention de notation** : tout identifiant entre crochets (`INV-[a]`, `TR-[n1]`, `CK-[n1]`, `D-[n]`, `C-[n]`, `T-[n]`) est un **emplacement** : le numéro est à attribuer lors de la rédaction officielle (§7). Le nom `situation_devis` reste provisoire jusqu'à son inscription.

---

## 1. Cadre documentaire respecté

- **Hiérarchie** (conventions §2) : CDC > modèle SQLite > `invariants.md` > modèle métier > errata. Le CDC est **silencieux** sur l'ordre acompte / situation et sur la couverture : rien à y modifier, aucun erratum requis. Les trois documents suivants sont à mettre à jour **dans cet ordre** : modèle SQLite, registre des invariants, modèle métier.
- **Règle anti-régression** (modèle §0) : toute règle nouvelle reçoit un `INV`, une garde et un **test du même nom**. Aucun INV existant ne change de sens ici : **INV-58 et INV-190 restent inchangés** (pas de ligne au journal des modifications).
- **Conventions §5** : le modèle est mis à jour **avant** la migration ; une migration n'est pas réécrite ; triggers nommés `tr_<NN>_<table>_<règle>` ; chaque migration est livrée avec son test. Ici : aucune modification de 001 à 009 ; la règle d'ordre passe par un `DROP TRIGGER` / `CREATE TRIGGER` de `tr_22_factures_acompte` dans 009b, comme 009b le fait déjà pour d'autres triggers de `factures`.
- **Hors périmètre** : PT-11 / M3 (composition des lignes de situation, colonnes de situation) — le modèle ne fait que **mentionner la dépendance** (§2 ligne A2). H6 (annulation du BC) n'est pas touché.

### Précondition de rédaction (B1)
Les numéros de section sont les mêmes dans la V3.12 officielle (`docs/`) et dans la V3.13 en relecture (`MAJ__modèle-données-sqlite-v6-v3.13.md`). **Mais** les passages à modifier (§3.2, §4.8, TR-22) ne disent pas la même chose dans les deux (la V3.12 contient encore `cancelled_at` et ignore `factures.devis_id`, INV-189, INV-190, PT-10, PT-11). Les insertions ci-dessous sont **additives** et valent pour les deux, sauf la ligne TR-22 et le §3.2 qui supposent le texte V3.13. La V3.14 doit donc être bâtie sur la V3.13 (décision B1 du propriétaire).

---

## 2. Carte des modifications

Numéros de ligne : V3.12 officielle / V3.13 en relecture.

| # | Document | Section exacte | Nature | Détail |
|---|---|---|---|---|
| A1 | Modèle SQLite | En-tête et « Historique des versions » (l.20-36 / l.27-44) | ajout d'une ligne | Ligne V3.14 (§3.1) |
| A2 | Modèle SQLite | §3.2 Facturation (l.166 / l.177), après le bloc « Situation » | ajout d'un paragraphe | « Couverture d'une situation » + mention explicite de la dépendance PT-11 (§3.2) |
| A3 | Modèle SQLite | §4.8 Facturation (l.368 / l.495), après `facture_lignes`, avant §4.9 | ajout d'un bloc | Table `situation_devis` (§3.3) |
| A4 | Modèle SQLite | §7.2 Colonnes modifiables (l.576 / l.740) | ajout d'une ligne | `situation_devis` : insertion seule (§3.4) |
| A5 | Modèle SQLite | §8 Triggers (l.595 / l.762) | 1 ligne modifiée, 2 ajoutées | TR-22 (ordre), TR-[n1], TR-[n2] (§3.5) |
| A6 | Modèle SQLite | §9 Index (l.645 / l.816) | ajout | `situation_devis(devis_id)` (§3.6) |
| A7 | Modèle SQLite | §13.1 cas chiffrés (l.787 / l.1008) ; §13.3 tests (l.848 / l.1082) | ajout | C-[n], T-[n] (§3.7, §6) |
| A8 | Modèle SQLite | §14 « Ce que SQLite ne garantit pas » (l.866 / l.1116) | ajout de lignes | limite + CK-[n1], CK-[n2] (§3.8) |
| A9 | Modèle SQLite | §15 Décisions (l.890 / l.1146) | ajout d'une ligne | D-[n] (§3.9) |
| A10 | Modèle SQLite | §16 Matrice de non-régression (l.948 / l.1227) | ajout d'une ligne | (§3.10) |
| A11 | Modèle SQLite | §17.1 Suivi des migrations (l.979 / l.1262) | modification de la ligne 009b | (§3.11) ; **dépend de H7** |
| B | `invariants.md` | table des INV, section facturation (près d'INV-57 / INV-58 / INV-190) | 2 lignes ajoutées | INV-[a], INV-[b] (§4) |
| C | Modèle métier | §10 Facture « Règles » (l.316) ; §12 Situation (l.385 en V3.13) | 1 puce + 3 puces | (§5) |
| — | CDC, errata, conventions | — | **aucune modification** | CDC silencieux ; règle déjà couverte par les conventions §5 |

---

## 3. Texte proposé pour le modèle SQLite

### 3.1 A1 — Historique des versions
> | **V3.14** (date) | **Couverture des situations** : table de liaison `situation_devis` ; une situation couvre tous les devis rattachés à son BC à son émission ; aucun acompte sur un devis couvert ; contrôles de diagnostic CK-[n1] et CK-[n2] ; décision D-[n], invariants INV-[a] et INV-[b] ; implémentation prévue dans la migration 009b |

### 3.2 A2 — §3.2, nouveau paragraphe (après le bloc « Situation »)
> **Couverture d'une situation** [INV-[a], INV-[b]] — **[VALIDÉ — décision du propriétaire du 2026-10-18]**
> - Une situation **couvre** tous les devis rattachés à son BC à l'instant de son émission. La couverture est **enregistrée** (§4.8, `situation_devis`) ; elle n'est jamais déduite d'horodatages, de lignes de facture ou de montants.
> - Un devis rattaché **après** l'émission n'est pas ajouté à une situation existante ; il est couvert par les situations émises ensuite. L'ajout d'un devis ne modifie aucune couverture ni aucune facture déjà émise.
> - **Aucun acompte** ne peut être émis sur un devis couvert par au moins une situation, quels que soient les avoirs, le montant net et l'avancement de cette situation. La règle dépend de l'**émission** de la situation. Un avoir, même total, ne supprime ni la situation ni sa couverture.
> - Un acompte émis **avant** la situation reste valide ; l'acompte d'un devis rattaché après une situation reste possible.
> - Une situation de montant nul reste refusée (`total_ht <> '0.00'`). Un devis couvert peut avoir un avancement propre de 0 %.
> - **Hors périmètre** : la composition des lignes d'une situation et les colonnes de situation (PT-11).

### 3.3 A3 — §4.8, bloc `situation_devis`
> **`situation_devis`** *(nom provisoire)* : `facture_id` NN FK→`factures` (`ON DELETE RESTRICT`, `ON UPDATE RESTRICT`) · `devis_id` NN FK→`devis` (`ON DELETE RESTRICT`, `ON UPDATE RESTRICT`). Table `STRICT, WITHOUT ROWID`.
> **Clé primaire composite `(facture_id, devis_id)`** : une couverture n'a pas d'identité propre ; la clé interdit le doublon. **Pas d'`id` de substitution, pas d'horodatage, pas de `bc_id`** (le BC se déduit de la facture ; la date d'émission est celle de la facture).
> **Contrôles d'intégrité** (triggers, §8) :
> 1. la facture est de type `situation` ;
> 2. le devis appartient au BC de la facture (`bc_devis`) ;
> 3. aucun `UPDATE`, aucun `DELETE` (y compris le `DELETE` implicite d'un `INSERT OR REPLACE` avec `recursive_triggers=ON`).
> Une facture couverte et un devis couvert ne peuvent pas être supprimés (FK `RESTRICT`, INV-06, INV-180). Le type d'une facture (TR-20) et l'appartenance d'un devis à un BC (INV-184) étant immuables, ces contrôles restent vrais.
> **Enregistrement** : dans la transaction d'émission de la situation, par **une seule instruction** `INSERT INTO situation_devis (facture_id, devis_id) SELECT :facture, devis_id FROM bc_devis WHERE bc_id = :bc` (exigences d'atomicité : §6 de la présente proposition). Aucune liste de devis n'est passée en paramètre.
> **Limites** : voir §14. [INV-[a]]

### 3.4 A4 — §7.2, ligne
> | `situation_devis` | — | **insertion seule**, dans la transaction d'émission de la situation ; ni UPDATE ni DELETE | aucune |

### 3.5 A5 — §8 Triggers
Ligne **modifiée** (ajout en gras) :
> | TR-22 | factures / INSERT | acompte ≤ contractuel ; un acompte par devis (PT-10) ; **acompte refusé si son devis est couvert par une situation (`situation_devis`) ; cette garde ne tient compte ni des avoirs, ni du montant net, ni de l'avancement, ni d'aucun horodatage** ; situation : … *(reste inchangé)* | 55 à 58, 189, **INV-[b]** |

Gabarit de la garde (à reporter dans 009b, message au format du projet) :
```sql
SELECT RAISE(ABORT, 'INV-[b]: aucun acompte sur un devis deja couvert par une situation')
 WHERE EXISTS (SELECT 1 FROM situation_devis c WHERE c.devis_id = NEW.devis_id);
```
Lignes **ajoutées** :
> | TR-[n1] | situation_devis / INSERT | `factures.type = 'situation'` pour `facture_id` ; `(factures.bc_id, devis_id)` présent dans `bc_devis` | INV-[a] |
> | TR-[n2] | situation_devis / UPDATE, DELETE | interdits (y compris `DELETE` implicite par `INSERT OR REPLACE` si `recursive_triggers=ON`) | INV-[a] |

Noms SQL (conventions §5) : `tr_[n1]_situation_devis_insert`, `tr_[n2]_situation_devis_update`, `tr_[n2]_situation_devis_delete` ; index `idx_situation_devis_devis_id`.

### 3.6 A6 — §9 Index
> `situation_devis(devis_id)` *(la clé primaire `(facture_id, devis_id)` tient lieu d'index sur `facture_id`)*

### 3.7 A7 — §13.1, cas chiffré C-[n]
> | C-[n] | BC avec devis A (1 000 €, sans acompte émis). S1 à 40 % cumulé ; tentative d'acompte sur A ; rattachement de B (500 €, acompte prévu 30 %) ; acompte sur B ; S2 à 60 % cumulé ; avoir total sur S1 ; nouvelle tentative d'acompte sur A | S1 = 400,00 € couvre {A} ; acompte sur A **refusé** ; contractuel 1 500 € ; acompte sur B 150,00 € **accepté** ; S2 = 900,00 − (400,00 + 150,00) = 350,00 € couvre {A, B} ; S1 reste {A} ; après avoir total sur S1, la couverture de S1 est inchangée et l'acompte sur A reste **refusé** (INV-[a], INV-[b]) |

Les montants sont des exemples de conception à confirmer par un calcul d'oracle lors de l'écriture du test, comme pour les autres cas du §13.

### 3.8 A8 — §14, lignes
> | Toute situation enregistre une couverture, et cette couverture comprend **tous** les devis rattachés à son BC à l'émission | service d'émission (un seul `INSERT … SELECT` dans la transaction, §6 de la présente proposition) + **CK-[n1]** (situation sans aucune couverture) + **CK-[n2]** (couverture non monotone : un devis couvert par une situation n'est plus couvert par une situation plus récente du même BC). SQLite ne peut ni exiger la présence d'enfants au `COMMIT`, ni vérifier l'exhaustivité, ni distinguer l'`INSERT` d'émission d'un `INSERT` tardif sans horodatage. Une couverture erronée mais valide est permanente (immutabilité). |

**D1 et D2 — l'inscription dans le modèle est justifiée** : le modèle (§0 règle 3) exige une garde pour chaque règle ; pour l'omission d'une couverture par le service, un contrôle de diagnostic est la seule garde possible, et le modèle consigne déjà ce type de limite en §14 (CK-13, CK-14). Coût : deux requêtes de lecture. Ils ne bloquent rien.

Requêtes (sondées sur la chaîne 001-009 avec le DDL provisoire en mémoire) :
```sql
-- CK-[n1] (D1) : situation sans aucune couverture
SELECT f.id FROM factures f
 WHERE f.type = 'situation'
   AND NOT EXISTS (SELECT 1 FROM situation_devis c WHERE c.facture_id = f.id);

-- CK-[n2] (D2) : devis couvert par une situation, absent d'une situation plus récente du même BC
SELECT s1.id AS situation_ancienne, s2.id AS situation_recente, c1.devis_id
  FROM factures s1
  JOIN factures s2 ON s2.bc_id = s1.bc_id AND s2.type = 'situation'
                  AND s2.situation_numero > s1.situation_numero
  JOIN situation_devis c1 ON c1.facture_id = s1.id
 WHERE s1.type = 'situation'
   AND NOT EXISTS (SELECT 1 FROM situation_devis c2
                    WHERE c2.facture_id = s2.id AND c2.devis_id = c1.devis_id);
```
Les rattachements ne faisant que croître (`bc_devis` immuable), toute ligne retournée par D2 est une anomalie. Ni D1 ni D2 n'utilisent d'horodatage. **Attention aux numéros** : CK-16 et CK-17 sont déjà employés par les tests de 006 sans figurer au registre du modèle (dernier CK inscrit : CK-15) ; les attribuer après avoir arrêté leur sort (§7).

### 3.9 A9 — §15, décision
> | D-[n] | **Couverture des situations et ordre acompte / situation** : une situation couvre tous les devis rattachés à son BC à l'émission ; aucun acompte sur un devis couvert | déduction par horodatage (proposition de travail du 2026-10-17) ; sélection libre des devis par situation ; lecture de la couverture dans les lignes de facture | **Validée** 2026-10-18 (propriétaire) ; INV-[a], INV-[b] ; D3 (diagnostic à horodatage) non retenu |

### 3.10 A10 — §16, ligne
> | Ordre acompte / situation exprimé par des horodatages (proposition de travail du 2026-10-17) | Remplacé par la couverture enregistrée : INV-[a], INV-[b] · TR-22, TR-[n1], TR-[n2] |

### 3.11 A11 — §17.1, ligne 009b
Compléter le contenu de la ligne du rang 14 : « … + table `situation_devis` (clé composite, index), triggers TR-[n1] et TR-[n2], garde d'acompte de TR-22 fondée sur la couverture, **garde de migration : refus d'application si une situation existe** ; modèle V3.14 ; test `test_009b_…` étendu (T-[n]) ».
**Sous réserve de H7** : si 009b avait été livrée ou appliquée ailleurs, ce contenu irait dans la ligne du rang suivant (15, aujourd'hui « 010 »), non créée.

---

## 4. Texte proposé pour `invariants.md`

> | INV-[a] | **Couverture d'une situation** : une situation couvre tous les devis rattachés à son BC à l'instant de son émission ; la couverture est enregistrée dans la transaction d'émission, ne comprend que des devis du BC de la facture, appartient à une facture de type situation, est immuable ; un devis rattaché ensuite n'est couvert que par les situations émises après | SQL (PK, FK), TRG (TR-[n1], TR-[n2]), SVC (émission atomique), CK ([n1], [n2]) | C-[n], T-[n] |
> | INV-[b] | **Aucun acompte sur un devis couvert** par une situation, quels que soient les avoirs, le montant net et l'avancement de cette situation ; l'acompte émis avant la situation, ou sur un devis rattaché après, reste possible | TRG (TR-22) | C-[n], T-[n] |

Chaque INV exige un test du même nom : `test_INV_[a]_…` et `test_INV_[b]_…`. Aucun INV n'est retiré ni modifié : pas de ligne au journal.

---

## 5. Texte proposé pour le modèle métier

- **§10 Facture, « Règles »** — 1 puce :
  > Un acompte ne peut pas être émis sur un devis déjà couvert par une situation (§12).
- **§12 Situation, « Règles »** — 3 puces :
  > - Une situation **couvre** tous les devis rattachés à son BC au moment de son émission. Un devis rattaché ensuite n'est pas ajouté aux situations déjà émises.
  > - Aucun acompte ne peut être émis sur un devis couvert par une situation, quels que soient les avoirs, le montant net et l'avancement de cette situation.
  > - Une situation de montant nul n'existe pas ; un devis couvert peut cependant avoir un avancement propre de 0 %.

---

## 6. Exigences d'atomicité pour le futur service d'émission

1. L'émission d'une situation est **une seule transaction** `BEGIN IMMEDIATE` (verrou d'écriture dès le début).
2. Dans cette transaction, dans cet ordre : lecture du contexte et calculs → `INSERT` de la facture → `INSERT` des lignes → **`INSERT … SELECT` de la couverture** → `COMMIT`.
3. La couverture est écrite par **une seule instruction** lisant `bc_devis` pour le BC de la facture. Aucun identifiant de devis n'est passé en paramètre : aucun sous-ensemble n'est possible.
4. Toute erreur, y compris celle d'un trigger de couverture, entraîne un `ROLLBACK` complet : ni facture, ni lignes, ni couverture. Le service n'utilise ni `INSERT OR IGNORE`, ni `INSERT OR REPLACE` sur la couverture (cela masquerait une anomalie).
5. Le rattachement d'un devis et l'émission d'une situation sont deux écritures **sérialisées** : un devis est soit rattaché avant l'émission (donc couvert), soit après le `COMMIT` (donc non couvert).
6. Le numéro de facture est attribué dans cette transaction (compteur de `machine.db`) ; un échec peut laisser un trou de numérotation, accepté (CDC l.590, INV-25).
7. Aucun chemin d'écriture dans `situation_devis` hors de ce service (ni import, ni réparation manuelle) sans décision humaine.

---

## 7. Références et identifiants à attribuer (sans numéro définitif)

| Type | Derniers numéros constatés | À attribuer | Précaution |
|---|---|---|---|
| INV | 202 (V3.13 en relecture et patch `h`) | 2 : [a], [b] | numéros absents = réservés, jamais réattribués (registre, mode d'emploi) |
| TR | 102 (V3.13) ; **103** (patch `h`, `tr_103` de 009a) | 2 : [n1], [n2] ; TR-22 modifié, pas de nouveau numéro | ne pas entrer en collision avec TR-103 |
| CK | 15 inscrits ; **CK-16 et CK-17** employés par les tests de 006 sans inscription | 2 : [n1], [n2] | arrêter d'abord le sort de CK-16 / CK-17 |
| D | 61 | 1 : [n] | — |
| C (§13.1) | 42 (V3.13), 41 (patch `h`) | 1 : [n] | contrôler les deux sources |
| T (§13.3) | 52 (T-52 réservé à 010, Planification) | 1 : [n] | ne pas prendre T-52 |
| E (errata) | 21 | 0 | CDC silencieux |
| PT | 21 | 0 | PT-11 reste ouvert ; aucun PT nouveau |
| Nom de table | — | `situation_devis` provisoire | à inscrire ou à changer lors de la rédaction |
| TR-22 | existant | texte modifié | nom de trigger `tr_22_factures_acompte` conservé |

---

## 8. Tests d'acceptation indispensables

**Aucun n'est écrit ni exécuté.** Ils correspondent aux tests 1 à 14 de l'étude (§6) ; les numéros ci-dessous renvoient à l'étude.

| # | Test d'acceptation | Étude |
|---|---|---|
| 1 | Acompte refusé sur un devis couvert (C-[n]) | 1 |
| 2 | Acompte autorisé sur un devis rattaché après la situation | 2 |
| 3 | Nouvelle situation après A et B : couvre A et B ; l'ancienne garde {A} | 3 |
| 4 | Situation entièrement créditée : couverture inchangée, acompte toujours refusé | 4 |
| 5 | Devis couvert à 0 % d'avancement propre : couvert, acompte refusé | 5 |
| 6 | Couverture d'un devis d'un autre BC : refusée | 6 |
| 7 | Couverture d'une facture non situation : refusée | 7 |
| 8 | UPDATE, DELETE, `INSERT OR REPLACE` sur la couverture ; DELETE de la facture ou du devis couvert : refusés | 8 |
| 9 | Échec injecté en cours d'émission : aucune situation, aucune couverture, trou de numérotation toléré | 9 |
| 10 | Plafonds d'acompte, situation de montant nul toujours refusée, autres contrôles : aucune régression | 10 |
| 11 | Garde de migration : refus si une situation existe (base inchangée) ; acceptation sinon | 11 |
| 12 | D1 et D2 détectent les anomalies, ne bloquent rien | 13 |
| 13 | Rejeu 001 → 009a → 009b depuis une base vide et depuis le rang 12 ; 001 à 009 identiques à GitHub ; campagne de mutation | 14 |

Recommandé (non indispensable) : indépendance vis-à-vis des horodatages (étude 12).

---

## 9. Cohérence avec 001 à 009

- **Aucune modification** de 001 à 009 : la table et ses triggers sont **additifs** ; `factures`, `facture_lignes`, `bc_devis`, `devis` ne changent pas de structure.
- `tr_22_factures_acompte` (006) n'est pas réécrit : 009b le remplace par `DROP TRIGGER` / `CREATE TRIGGER`, procédé déjà employé par 009b.
- Les contrôles réutilisent des garanties existantes : immutabilité des factures (TR-20, TR-21), de `bc_devis` (INV-184), suppression de devis (INV-180).
- La règle ne dépend pas de l'état « actif / neutralisée » d'une facture (PT-9 reste ouvert) : elle dépend seulement de l'existence de la couverture.
- Les sondes ont été exécutées sur la chaîne 001-009 de `main` avec le DDL provisoire **en mémoire seulement** : elles confirment les comportements SQLite, elles **ne valident pas** la solution.

---

## 10. Blocages réels avant la rédaction officielle

| # | Blocage | Levée attendue |
|---|---|---|
| B1 | Base de rédaction de la V3.14 : V3.12 (officielle) ou V3.13 (en relecture) | Décision du propriétaire : V3.14 bâtie sur la V3.13 (les migrations livrées la citent déjà) |
| B2 | H7 : 009a / 009b jamais livrées ni appliquées ailleurs ? | Une ligne du propriétaire ; ne conditionne que la ligne 009b du suivi des migrations (A11) |

Aucun autre blocage : les numéros officiels s'attribuent à la rédaction (§7).

---

## 11. Recommandation

**La rédaction du modèle V3.14 peut commencer dès que B1 est tranché** ; B2 peut être levé en parallèle sans retarder le reste. Cette proposition n'est pas la rédaction officielle et n'engage aucune implémentation SQL. L'ordre à respecter : validation de cette proposition → rédaction et validation de la V3.14 → mise à jour de `invariants.md` et du modèle métier → patch 009b révisé avec ses tests → rejeu complet.
