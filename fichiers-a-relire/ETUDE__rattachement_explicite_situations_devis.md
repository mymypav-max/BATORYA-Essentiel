# ÉTUDE DE CONCEPTION — Rattachement explicite des situations aux devis (révision 4, cadrage clôturé, base V3.12)

**Nature** : document de travail (relecture), **non officiel**. Aucun fichier SQL, test, `docs/` ni migration n'est modifié.
**Date** : 2026-10-18 · **Remplace** la révision 3 (commit d8a7afc). Révision 4 : base documentaire V3.12, H7 ramené à un fait vérifié, `WITHOUT ROWID` retiré, citations INV-180 / INV-190 retirées, blocages réduits à un seul.
**Clôture (2026-10-18)** : cadrage clos ; modèle officiel V3.14 rédigé (en relecture) ; identifiants attribués : INV-204, INV-205, TR-104, TR-105, CK-21, CK-22, D-62, C-43, T-53 ; D1 / D2 deviennent CK-21 / CK-22. En cas d'écart, les documents officiels font foi.
**Suite** : la proposition de modification du modèle SQLite est dans `fichiers-a-relire/PROPOSITION__modele_sqlite_v3.14_situation_devis.md`.
**Identifiants** : le nom `situation_devis` et tous les numéros (`INV-`, `TR-`, `CK-`, `D-`, `C-`, `T-`) restent **provisoires** jusqu'à leur inscription dans le modèle.

---

## 0. Où en est le cadrage

### 0.1 Décisions validées par le propriétaire (2026-10-18)

| # | Décision |
|---|---|
| V1 | Une situation couvre **tous les devis rattachés à son BC à son émission**. Un devis rattaché ensuite n'est jamais ajouté rétroactivement à une situation existante. |
| V2 | **Aucun acompte** sur un devis déjà couvert par une situation, indépendamment des avoirs, du montant net ou de l'avancement de cette situation. |
| V3 | Table de liaison `situation_devis` (nom provisoire) : clé primaire composite `(facture_id, devis_id)`, clés étrangères, contrôles d'intégrité. **Pas de colonne `id` de substitution, pas d'horodatage** sans besoin démontré. |
| V4 | La couverture est enregistrée **dans la transaction d'émission**, par un `INSERT … SELECT` sur tous les devis alors rattachés au BC. |
| V5 | Diagnostics **D1 et D2** (sans horodatage) conservés. **D3 non intégré.** |
| V6 | La migration **refuse explicitement de s'appliquer** si une situation existe déjà, sans modifier les données ni fabriquer de rattachement. |
| V7 | Règle actuelle **inchangée** : une situation de montant nul est refusée. Un devis couvert peut avoir un avancement propre de 0 %. |
| V8 | M3 / PT-11 : sujet distinct, à concevoir, **non traité ici**. |
| V9 | H6 (annulation d'un BC) : écart documentaire distinct, **ne bloque pas** ce chantier. |

### 0.2 Reste à confirmer

- **H7** — statut de 009a / 009b : **fait vérifié dans le dépôt** (§1.3), non une question posée. 009a / 009b ne sont pas livrées ; le dépôt ne montre aucune application ailleurs et ne peut pas la démontrer non plus. Hypothèse de travail retenue : non livrées, sans demande de confirmation.
- **Base documentaire** — la V3.14 est bâtie sur la **V3.12 officielle** (décision du 2026-10-18 03:30) ; la V3.13 n'est pas promue. Classement des écarts et contrôle des identifiants : proposition, §1 et §2.

### 0.3 Hors périmètre de ce chantier

- **M3 / PT-11** : composition des lignes d'une situation et colonnes de situation (§4).
- **H6** : écart entre le CDC §17 (« situation émise, même annulée, interdit l'annulation directe ») et la règle d'annulation par net nul du 2026-10-17 14:34.

---

## 1. État réel du dépôt et références

### 1.1 GitHub, `main`

- `main` = **29cba9f** (2026-10-18 03:22). Derniers commits : dépôt des révisions 2 et 3 de cette étude et de la première proposition, et un commit de charte graphique étranger au sujet. Migrations et patchs : **inchangés depuis de672cd**.
- Chaîne métier présente (`src-tauri/migrations/metier/`) : 001, 002, 003, 004, 005, 005a, 005b, 005c, 006, 007, 008, 009 (rangs 1 à 12). **Aucune base de données** dans l'arborescence.
- Absentes : `009a_bc_annulation_interdite_si_facture` (rang 13) et `009b_acompte_garanties_manuelles` (rang 14).

### 1.2 Références utilisées (inchangées depuis la révision 2, citations vérifiées)

| Sujet | Source |
|---|---|
| Hiérarchie | `docs/conception/conventions-techniques-v6.md` §2 l.16-26 ; règles de migration §5 l.70-108 (modèle mis à jour **avant** la migration ; chaque migration livrée avec son test ; triggers `tr_<NN>_<table>_<règle>`) ; §11 (pas de sur-architecture) |
| Composition des lignes (M3, hors périmètre) | INV-62 (`docs/conception/invariants.md` l.104) ; modèle SQLite V3.12 l.390 ; modèle métier §11 l.336 ; 006 : `tr_22_facture_lignes_insert` l.449 |
| Situation globale au BC | `MAJ__invariants.md` l.221 (INV-190), l.96 (INV-57) ; `MAJ__modèle-métier-V6.md` §12 l.391 ; `MAJ__modèle-données-sqlite-v6-v3.13.md` l.184, l.433, D-48 l.1197, PT-11 l.1394 |
| Plusieurs devis sur un BC | `MAJ__modèle-métier-V6.md` l.269 : acompte ou situations déjà émis **ne ferment pas** le BC |
| Montant nul | `006_facturation.sql` l.145 : `CHECK (type='solde' OR total_ht <> '0.00')` ; règle de service `M > 0` |
| Règle d'ordre à horodatages (à remplacer) | `consignation-V3.14-h.patch` (009b, `tr_22_factures_acompte`) |

**Nuance documentaire à conserver** : INV-190, « situation globale au BC », PT-11 et D-48 ne figurent **pas** dans `docs/` (registre officiel arrêté à INV-178) ; ils sont dans les documents de travail `MAJ__*`. Le mot « couvre » et la règle d'ordre acompte / situation ne sont écrits **nulle part** hors du patch `h`. La proposition de modèle (document séparé) les inscrit.

### 1.3 H7 — résultat factuel de la vérification

Éléments contrôlés, et seulement ceux-là :

| Élément | Constat |
|---|---|
| Branche | un seul `main` ; pas d'autre branche ; aucun tag |
| Arborescence | 009a et 009b **absentes** de `src-tauri/migrations/metier/` à 29cba9f |
| Patchs | `consignation-V3.14.patch` et `-b` à `-h` (fichiers texte dans `fichiers-a-relire/`), dernier = `-h` (f8b244f, 2026-10-17). Les fichiers SQL 009a / 009b n'y existent que comme contenu de patch. Outil associé : `classify009b.py` (campagne de mutation) |
| Statut déclaré | dans le tableau de suivi des migrations du patch `h` : rang 13 (009a) et rang 14 (009b) « **créée, à relire** » ; rang 15 (010) « prévue, non créée ». Les rangs 1 à 12 sont « livrée ». Les rapports de la révision G précisent qu'**aucune migration livrée (001 à 009) n'est modifiée** |
| `docs/` officiel | aucune mention de 009a / 009b |
| Code d'application | aucun lanceur de migrations ni code applicatif dans le dépôt (SQL, tests, documents) : le dépôt ne peut donc pas montrer qu'une migration a été **appliquée** à une base |
| Déclaration du propriétaire | l'environnement local ne contient aucune base métier hors dépôt (énoncé M4, 2026-10-18) |

**Conclusion** : 009a et 009b ne sont **pas livrées** dans la chaîne de `main` ; leur statut documentaire est « créée, à relire ». C'est un fait vérifié, qui suffit au cadrage. **Limite** : le dépôt ne permet pas d'exclure qu'un SQL issu des patchs ait été exécuté dans un autre environnement ; je ne le prétends pas et je ne demande pas de confirmation.

---

## 2. Orientations devenues décisions validées (V1, V2, V7)

- **V1 — couverture à l'émission.** Exemple : A rattaché, S1 émise, B rattaché ensuite → S1 couvre {A} pour toujours ; S2 émise après B couvre {A, B}. Aucun mécanisme de sélection d'un sous-ensemble : le périmètre est « tous les devis rattachés à l'instant de l'émission ».
  *Nuance de sources* : INV-190 et §12 définissent le périmètre du **calcul du montant**, pas une relation de couverture ; la relation est une règle nouvelle à inscrire (proposition de modèle).
- **V2 — ordre acompte / situation.** La règle dépend de l'**émission**, pas du montant net, des avoirs ni du pourcentage. Le SQL livré dérive un état « neutralisée » utilisé par d'autres triggers (situation de référence, solde) : **le trigger d'acompte ne doit pas le réutiliser**. La table de couverture ne lit ni avoirs, ni montants, ni pourcentages : la règle est respectée par construction.
- **V7 — montant nul.** Une situation de montant 0.00 reste impossible (CHECK + règle de service). La règle « aucun acompte après situation » concerne donc des situations de montant > 0. Un devis couvert peut cependant avoir un avancement propre de 0 % (l'avancement porte sur d'autres devis) : il est couvert quand même.

---

## 3. Modèle technique retenu (V3, V4, V5)

### 3.1 Structure

```sql
CREATE TABLE situation_devis (               -- nom provisoire
    facture_id INTEGER NOT NULL REFERENCES factures (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    devis_id   INTEGER NOT NULL REFERENCES devis    (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    PRIMARY KEY (facture_id, devis_id)
) STRICT;
CREATE INDEX idx_situation_devis_devis_id ON situation_devis (devis_id);
```

Pas de `id`, pas de `created_at`, pas de `bc_id` (redondant : le BC se déduit de la facture). Les conventions de tables imposent `STRICT` (en-tête de 006). **`WITHOUT ROWID` est retiré** : aucune migration livrée (001 à 009) ne l'emploie ; la révision 3 le prévoyait à tort.

### 3.2 Intégrité en base (sondée sur la chaîne 001-009)

Les clés étrangères seules ne garantissent que l'**existence**. Il faut des triggers :

| Contrôle | Mécanisme | Sonde |
|---|---|---|
| La facture est une situation | `BEFORE INSERT` | lien vers un acompte : refusé |
| Le devis appartient au BC de la facture | `BEFORE INSERT`, lecture de `bc_devis` | devis d'un autre BC : refusé |
| Pas de doublon | PK | refusé |
| Couverture immuable | `BEFORE UPDATE`, `BEFORE DELETE` | refusés, y compris `INSERT OR REPLACE` avec `recursive_triggers=ON` |
| Facture / devis couvert non supprimable | FK `RESTRICT` ; facture : INV-06 / TR-21 existants | refusés |
| Type de facture et appartenance au BC figés | `tr_20` (factures) et INV-184† (`bc_devis`, triggers `tr_99_bc_devis_no_update` / `no_delete`) existants | acquis |

Conventions §9 : `INSERT OR REPLACE` interdit, `recursive_triggers=ON` obligatoire : le trigger `DELETE` reste un filet. Clé étrangère composite `(bc_id, devis_id) → bc_devis` écartée : elle exigerait un `UNIQUE(bc_id, devis_id)` absent de `bc_devis` et une colonne `bc_id` redondante.

### 3.3 Enregistrement et atomicité (V4)

Dans la transaction `BEGIN IMMEDIATE` de l'émission : calculs → `INSERT` facture → `INSERT` lignes → **une seule instruction** `INSERT INTO situation_devis (facture_id, devis_id) SELECT :facture, devis_id FROM bc_devis WHERE bc_id = :bc` → `COMMIT`. Aucune liste en paramètre : aucun sous-ensemble possible côté service. Le verrou d'écriture sérialise émission et rattachement : un devis est soit rattaché avant (couvert), soit après le `COMMIT` (non couvert). Toute erreur → `ROLLBACK` : ni facture, ni lignes, ni couverture (sonde). Le trou de numérotation éventuel (compteur dans `machine.db`) est accepté par le CDC (l.590).

### 3.4 Trigger d'acompte (V2)

`tr_22_factures_acompte` (006, l.345) porte déjà cinq contrôles : devis rattaché au BC (INV-189†), aucun solde (INV-58), un seul acompte actif par devis (INV-52), ≤ total du devis et nette ≤ contractuel (INV-57) ; la chaîne de `main` n'a **aucune** règle d'ordre situation → acompte (sonde : un acompte sur A est accepté après S1). Dans 009b, la condition à horodatages du patch `h` est remplacée par la garde ci-dessous (qui s'ajoute aux cinq contrôles) :

```sql
SELECT RAISE(ABORT, 'INV-[b]: aucun acompte sur un devis deja couvert par une situation')
 WHERE EXISTS (SELECT 1 FROM situation_devis c WHERE c.devis_id = NEW.devis_id);
```

Indépendant des avoirs, du montant, du pourcentage et des horodatages (plus de cas d'égalité d'horodatage). N'affecte ni les acomptes émis avant la situation, ni un devis rattaché après (sonde : acompte sur B autorisé après S1 {A}).

### 3.5 Ajout ultérieur d'un devis

`bc_devis` n'écrit jamais dans la couverture (INV-187† / INV-188† inchangés). S1 reste {A}. S2, par l'`INSERT … SELECT`, couvre {A, B} (sonde).

### 3.6 Limites de SQLite et diagnostics (V5)

SQLite **ne peut pas** : exiger au `COMMIT` qu'une situation ait une couverture ; garantir que la couverture est complète ; distinguer l'`INSERT` d'émission d'un `INSERT` tardif (sondes). Une couverture erronée mais valide serait permanente (tout est immuable) ; seule une migration corrective, sur décision humaine, pourrait y remédier.

Diagnostics retenus, sans horodatage, jamais bloquants :

| Contrôle | Détecte | Requête (sondée) |
|---|---|---|
| **D1** | situation sans aucune couverture | `SELECT f.id FROM factures f WHERE f.type='situation' AND NOT EXISTS (SELECT 1 FROM situation_devis c WHERE c.facture_id=f.id)` |
| **D2** | couverture non monotone : un devis couvert par une situation n'est plus couvert par une situation plus récente du même BC | jointure de deux situations du même BC (`situation_numero` croissant) et de la couverture de la plus ancienne, avec `NOT EXISTS` sur la couverture de la plus récente |

D1 et D2 sont inscrits dans le modèle (§14 du modèle ; proposition §4.8). **D3 (diagnostic à horodatage) n'est pas intégré** (V5) : l'omission partielle sur la dernière situation reste donc détectable seulement par les tests du service. Ce choix est assumé, il n'est pas rouvert ici.

---

## 4. M3 / PT-11 — hors périmètre (mémoire)

Pour mémoire, sans rouvrir : les documents (INV-62, modèle SQLite, modèle métier) prévoient **1 ligne `synthese`** pour une situation ; 006 accepte `avancement` et `deduction` et refuse `synthese`. La décision de travail du 2026-10-17 (D) traite les lignes `avancement` comme « historiques ». La correction dépend de **PT-11** (colonnes de situation), encore à concevoir.

**Indépendance** : la couverture ne lit pas les lignes de facture et ne dépend d'aucune composition de lignes. Elle peut être spécifiée, validée et implémentée sans M3. Les triggers concernés sont distincts (009b réécrit des triggers de `factures` ; M3 toucherait `tr_22_facture_lignes_insert`). Seul couplage de test : l'aide `emettre_situation` du test 006 (construit des lignes `avancement`) ; les tests de couverture n'ont besoin que de **créer une situation puis d'inscrire sa couverture**.

---

## 5. Stratégie de migration (V6)

### 5.1 Placement

009b n'est pas livrée (§1.3). **Recommandation inchangée : intégrer la couverture dans 009b avant sa livraison** — table, index, deux groupes de triggers, réécriture de la condition d'ordre dans `tr_22_factures_acompte`, garde du §5.2. 001 à 009 ne sont pas touchées. Pas de 009c : elle ne ferait que remplacer, dans la même chaîne non livrée, une règle à horodatages écrite quelques lignes plus haut. Pas de 010.

**Hypothèse de travail (H7)** : 009b n'est pas livrée (fait vérifié, §1.3). Si elle l'avait été ou appliquée ailleurs, la couverture irait dans le rang suivant (15, « 010 »), à ne créer qu'après décision explicite. Rien ne le montre ; aucune confirmation n'est demandée. Seule la ligne 14 du suivi des migrations (§17.1) en dépend. Le rang et le numéro de la chaîne 009a / 009b relèvent d'AR-06 (copie de travail).

Impact d'une intégration dans 009b : adapter la dizaine de tests d'ordre de 009b (ils fabriquent des situations brutes, sans couverture), supprimer le test « ex æquo d'horodatage = refus », relancer la campagne de mutation.

### 5.2 Garde sur situation préexistante

La migration s'arrête avec un message explicite si `factures` contient au moins une situation. Garde en lecture seule, sur le modèle livré dans 005b (`CREATE TEMP TABLE garde_… (… CHECK …)`, `INSERT … SELECT`, `DROP TABLE`) et repris par 009b. **Échec** : la contrainte `CHECK` lève une erreur, le script s'arrête et le lanceur annule la transaction ; base et `user_version` inchangés. Le lanceur n'est pas dans le dépôt : ce comportement n'est vérifiable que par imitation en test. Aucune donnée modifiée, aucun lien fabriqué, aucun mécanisme de récupération. Aucune base réelle n'a été vérifiée par cette étude ; le dépôt n'en contient pas.

**Conduite à tenir si une base avec situations apparaissait** : ne pas appliquer la migration ; sauvegarder ; lister les situations en lecture seule ; faire arbitrer par le propriétaire. Le problème (couverture non reconstituable) ne serait **pas** résolu par la garde, seulement rendu visible. Rien n'est conçu pour ce cas hypothétique ni pour l'import V2 (précédé d'une application de conversion distincte).

---

## 6. Tests

**Aucun n'est écrit ni exécuté.** Seules des sondes jetables (DDL en mémoire, hors dépôt) l'ont été : elles confirment les comportements SQLite ci-dessus, **sans valider la solution**.

| # | Test | Attendu |
|---|---|---|
| 1 | S1 sur A, puis acompte sur A (y compris `created_at` identiques ou inversés) ; témoin sans couverture | refusé ; témoin accepté |
| 2 | S1 sur A, rattachement de B, acompte sur B | autorisé si les autres règles le sont |
| 3 | Situation émise après A et B | couvre A et B ; S1 garde {A} |
| 4 | Situation entièrement créditée | couverture inchangée ; acompte sur le devis refusé |
| 5 | Situation couvrant un devis à 0 % d'avancement propre | devis couvert ; acompte refusé |
| 6 | Couverture vers un devis d'un autre BC | refusée |
| 7 | Couverture vers une facture non situation | refusée |
| 8 | UPDATE, DELETE, `INSERT OR REPLACE` sur la couverture ; DELETE de la facture ou du devis couvert | refusés |
| 9 | Échec injecté entre l'`INSERT` facture et l'`INSERT … SELECT` | aucune situation, aucune couverture ; trou de numérotation toléré |
| 10 | Plafonds d'acompte et autres contrôles existants ; situation de montant nul toujours refusée (V7) | aucune régression |
| 11 | Garde V6 : base avec une situation / sans situation | migration refusée, base inchangée / acceptée |
| 12 | CK-21 et CK-22 (anciens D1 et D2) | signalent respectivement une situation sans couverture et une couverture non monotone |
| 13 | Rejeu du cas chiffré (§4.7 de la proposition) avec témoin ; rejeu de la chaîne 001 → 009a → 009b depuis une base vide et depuis le rang 12 ; empreintes de 001 à 009 identiques à GitHub ; campagne de mutation | tout vert |

**13 tests**, comme dans la proposition et dans le modèle officiel (T-53). L'ancien test « indépendance vis-à-vis des horodatages » est intégré au test 1.

(Les anciens tests relatifs à M3 — cohérence avec la règle de synthèse — sortent du chantier.)

---

## 7. Blocages

**Aucun blocage restant** : B1 (identifiants) est levé par l'attribution des planchers de non-collision le 2026-10-18 ; la base de rédaction (V3.12) et H7 étaient déjà tranchés. Dépendances ouvertes non bloquantes : AR-06 (rang de 009a / 009b), AR-08 (partie « solde » de TR-22), PT-11 / M3 (hors périmètre), coordination des numéros T-53 / C-43 / D-62 avec les plans de travail 009a (V3) et 011, non validés.

---

## 8. Recommandation

**Le cadrage documentaire est clos et le modèle officiel V3.14 est rédigé (en relecture).** Étape suivante : patch 009b révisé (table, index, triggers TR-104 / TR-105, garde d'acompte de TR-22 fondée sur la couverture, garde de migration) et ses 13 tests T-53, puis rejeu complet de la chaîne. Rien n'est validé tant que ce n'est pas implémenté et testé.
