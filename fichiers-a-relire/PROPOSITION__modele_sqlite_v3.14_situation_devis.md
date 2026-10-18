# PROPOSITION — Modifications du modèle SQLite V3.14 : couverture des situations (`situation_devis`) — révision 2

**Nature** : document de proposition, **non officiel**, destiné à servir de base de validation. Il prépare la rédaction de `modèle-données-sqlite-v6-v3.14.md`. Il ne modifie ni `docs/`, ni SQL, ni test.
**Date** : 2026-10-18 · **Remplace** la première version (commit 29cba9f).
**Décisions fonctionnelles** : les 9 décisions validées par le propriétaire le 2026-10-18 (étude, §0.1). Elles ne sont pas rouvertes ici.
**Suite (2026-10-18)** : proposition validée sur le fond par le propriétaire ; **rédaction officielle effectuée** dans `docs/conception/modèle-données-sqlite-v6-v3.14.md`, `invariants.md` et `modèle-métier-V6.md` (en relecture). Ce document est conservé comme trace de la validation ; **en cas d'écart, les documents officiels font foi**.
**Identifiants attribués** (planchers du §2.2 adoptés le 2026-10-18) : INV-[a] = **INV-204** (couverture) · INV-[b] = **INV-205** (aucun acompte sur un devis couvert) · TR-[γ] = **TR-104** (insertion) · TR-[δ] = **TR-105** (UPDATE / DELETE) · CK-[α] = **CK-21** · CK-[β] = **CK-22** · D-[ε] = **D-62** · C-[η] = **C-43** · T-[ζ] = **T-53** (13 tests d'acceptation). Noms SQL : `tr_104_situation_devis_insert`, `tr_105_situation_devis_update`, `tr_105_situation_devis_delete`. Les numéros du texte ci-dessous restent écrits sous forme d'emplacements.
**Notation** : `INV-[a]`, `TR-[γ]`, `CK-[α]`, `D-[ε]`, `C-[η]`, `T-[ζ]` sont des **emplacements** ; † désigne un identifiant de travail absent du registre officiel (§2). Le nom `situation_devis` reste provisoire.

---

## 1. Base documentaire : V3.12 officielle, et écarts V3.13 utiles

### 1.1 Règle appliquée
La V3.14 est construite à partir du modèle **officiel V3.12** (`docs/conception/modèle-données-sqlite-v6-v3.12.md`). La V3.13 (`fichiers-a-relire/MAJ__modèle-données-sqlite-v6-v3.13.md`) n'est **pas** une référence validée et n'est pas promue ici. La copie de travail `fichiers-a-relire/audit-global-coherence/V3.14__01_modele-donnees-sqlite-v6-v3.14-TRAVAIL.md` (dérivée de la V3.12, non validée) sert seulement de **repère d'emplacement** ; aucune de ses affirmations n'est reprise sans vérification dans le SQL livré.

### 1.2 Constat qui structure la proposition
La V3.12 décrit un BC rattaché à **un seul** devis (`bons_commande.devis_id` UNIQUE, l.308) et une table `factures` **sans** `devis_id` (l.370). Les deux notions dont dépend la couverture — « les devis rattachés à un BC » et « l'acompte d'un devis » — **n'existent donc pas dans la V3.12**. Elles viennent des migrations livrées 005b (`bc_devis`) et 006 (`factures.devis_id`), et de la V3.13. Elles sont déjà dans le périmètre prévu de la V3.14 (copie de travail : ⟦VAL A⟧ pour `bc_devis`, constat ⟦SQL 006⟧ pour `factures.devis_id`) : la proposition les traite comme **prérequis déjà validés**, repris uniquement pour ce qui est nécessaire, et ne les rouvre pas.

### 1.3 Écarts V3.12 ↔ V3.13 qui touchent cette évolution
Classes : **1** laisser hors V3.14 (non validé) · **2** reprendre uniquement l'élément nécessaire et validé · **3** dépendance exigeant une décision humaine.

| Élément | V3.12 officielle | V3.13 (relecture) | SQL livré | Classe et traitement |
|---|---|---|---|---|
| `bc_devis`, BC multi-devis (PT-6 ; INV-184†, INV-187†, INV-188†) | absent (BC ↔ devis 1:1) | table proposée | 005b : table + triggers `tr_99_bc_devis_*` | **2** — reprendre la définition de `bc_devis` **telle que livrée**, l'immuabilité (INV-184†) et le rattachement tant qu'aucun solde n'existe (INV-187†) comme prérequis cités. Ne pas reprendre le reste de PT-6. Déjà au programme de la V3.14 (⟦VAL A⟧) : aucune décision nouvelle |
| `factures.devis_id`, acompte par devis (PT-10 ; INV-189† ; D-48†) | absent ; INV-52 officiel : un seul acompte par BC | PT-10 proposé ; D-48 « validée 2026-10-03 » | 006 : colonne, `CHECK ((type='acompte') = (devis_id IS NOT NULL))`, `tr_22_factures_acompte` | **2** — reprendre la colonne, le CHECK et la ligne TR-22 **telle que livrée** ; citer D-48† par sa **date de validation** (consignée seulement en V3.13). La mise à jour d'INV-52 (un acompte par devis) relève de la V3.14 générale, pas de ce chantier |
| TR-22 | l.615 : acompte ≤ contractuel ; situation ; solde ; aucun acompte / situation si solde actif | + « un acompte par devis (PT-10) » + « unicité active (PT-9) » | acompte : 5 contrôles ; situation : 3 ; solde | **2** pour la clause « par devis » (déjà livrée) ; **1** pour PT-9 (la règle de couverture n'emploie aucune notion d'« actif »). La clause de couverture s'**ajoute** à la ligne TR-22 de la V3.14 ; la partie « solde » de la même ligne est en cours d'arbitrage (AR-08, copie de travail) : clause séparable, à coordonner à la rédaction |
| INV-190† (situation globale ; colonnes PT-11) | absent | présent | 006 l'emploie pour la continuité d'avancement par ligne | **1** pour la partie colonnes / mode de saisie ; **3** dépendance M3 (hors périmètre, mentionnée au §3.2). **Cette proposition ne cite plus INV-190** : « tous les devis rattachés » est porté par INV-[a] |
| PT-11 | absent | À CONCEVOIR | colonnes absentes de `factures` | **1** hors V3.14 ; **3** dépendance explicite de M3, **non traitée** |
| PT-10 (mécanisme) | absent | proposition | colonne livrée | **1** pour le texte PT-10 (non repris) ; le fait livré est repris (ligne 2) |
| D-48† | absent (registre officiel : D-39) | « Validée 2026-10-03 » | — | **2** — cité par date ; numéro officiel : AR-01 |
| INV-180† (suppression d'un devis brouillon) | absent | présent | — | **non cité** : la FK `RESTRICT` de `situation_devis.devis_id` interdit à elle seule de supprimer un devis couvert |
| TR-20, TR-21, INV-06, INV-25 | officiels (TR-20 l.613 autorise `cancelled_at` et `client_id`) | réécrits (aucun UPDATE) | `tr_20` : aucun UPDATE | **inchangé** : la proposition n'emploie que « `type` et `bc_id` d'une facture ne changent pas », vrai dans les deux textes |
| Références « modèle V3.13 » dans les migrations et tests livrés | — | — | 8 fichiers SQL et 8 fichiers de test (001-009) | **1** — immuables, aucune action ; le futur 009b citera « V3.14 » |

Aucune décision nouvelle n'est créée : les classes **3** renvoient à M3 / PT-11 (hors périmètre, validé) et à AR-01 / AR-06 / AR-08 de la copie de travail, déjà ouverts.

---

## 2. Contrôle des identifiants (limité à ceux de cette évolution)

Méthode : lecture des registres officiels (`docs/`), de la V3.13 et de ses `MAJ__*`, de la copie de travail V3.14 et de sa matrice (§5), des migrations et tests 001-009, des ajouts du patch `h`. Script de lecture jetable, hors dépôt.

### 2.1 Table de contrôle

| Identifiant | Source(s) | Usage réel | Décision recommandée |
|---|---|---|---|
| CK-13 | officiel (V3.12 §14) ; 004, 005b, 006 | diagnostic devis ↔ BC | cité, inchangé |
| CK-14† | V3.13 ; 005b, 006 et leurs tests | devis rattaché après solde | ne pas réutiliser ; non cité |
| CK-15† | V3.13 ; 005a (SQL) | snapshot de version initiale d'un devis | ne pas réutiliser |
| CK-16† | 006 (SQL, 10 occurrences en test) ; patch `h` | lignes d'avancement d'une situation (exhaustivité, doublon, ligne étrangère) | **ne pas réattribuer** ; absent des registres |
| CK-17† | tests 006 ; copie de travail | cohérence montant / pourcentages | **ne pas réattribuer** |
| CK-18†, CK-19†, CK-20† | **tests 007 seuls** ; absents de la V3.13, de la copie de travail et de sa matrice (qui s'arrête à CK-17†) | diagnostics des règlements | **divergence nouvelle** : à porter à AR-01 ; ne pas réutiliser |
| Nos D1 / D2 | — | diagnostics de couverture | emplacements **CK-[α]**, **CK-[β]** ; plancher de non-collision : CK-21 |
| INV-52, 57, 58, 06, 25 | officiel | acompte unique, plafonds, ordre après solde, factures non supprimables, trou de numérotation | cités, inchangés |
| INV-184†, INV-189† | SQL livré (messages 005b / 006) ; V3.13 | immuabilité de `bc_devis` ; acompte lié à son devis | cités avec †, comme prérequis |
| INV-190† | 006 (continuité d'avancement) ; V3.13 (situation globale) | deux emplois différents du même numéro | **non cité** (§1.3) |
| Nos INV | — | couverture ; ordre acompte / situation | emplacements **INV-[a]**, **INV-[b]**. Dernier INV officiel : INV-178 ; INV-179† à INV-203† déjà employés (SQL jusqu'à 201, V3.13 jusqu'à 202, copie de travail 203). Plancher : INV-204 |
| TR-22 | officiel | trigger d'acompte / situation / solde | ligne **modifiée**, aucun numéro nouveau |
| TR-101† | SQL 005 et tests ; **absent de la V3.13** | dépenses jamais supprimées | divergence ; ne pas réutiliser |
| TR-97† à TR-102†, TR-103† | SQL / V3.13 (97-102) ; patch `h` (103, `tr_103` de 009a, non livrée) | divers | ne pas réutiliser |
| Nos TR | — | contrôle d'insertion ; interdiction UPDATE / DELETE | emplacements **TR-[γ]**, **TR-[δ]** ; plancher : TR-104. Dernier officiel : TR-96 (série non contiguë) |
| D-48† | V3.13 | acompte par devis, situation globale | cité par date |
| Notre D | — | décision de couverture | emplacement **D-[ε]** ; dernier officiel D-39 ; D-40† à D-61† employés ; plancher D-62 |
| Notre C | — | cas chiffré | emplacement **C-[η]** ; dernier officiel C-29 ; C-30† à C-42† ; plancher C-43 |
| Notre T | — | test d'acceptation | emplacement **T-[ζ]** ; dernier officiel T-29 ; T-30† à T-52† ; **T-44, T-45, T-46 utilisés par les tests (005, 005a, 005b) mais absents du registre V3.13** ; T-52 réservé à 010 ; plancher T-53 |
| Errata (E-) | officiel E-09 ; E-10† à E-21† | — | **aucun erratum** (CDC silencieux sur l'ordre acompte / situation) |

### 2.2 Conclusion et incertitudes
- **Aucun numéro n'est attribué.** Le registre officiel ne permet pas de déterminer le « prochain » numéro sans ambiguïté : les séries † occupent les numéros qui le suivraient (matrice §5 de la copie de travail ; statut des † = AR-01, ouvert).
- Le **plancher de non-collision** est le plus petit numéro supérieur à tout numéro employé dans **n'importe quelle** source, divergences comprises. Il ne dépend pas du maximum d'un seul registre. Il reste sans collision quelle que soit l'issue d'AR-01 : les numéros cités par 001-009 sont immuables (messages SQL) ; pour D, C, T, E, un plancher évite de toute façon les numéros employés.
- Incertitudes : (i) statut officiel des † (AR-01) ; (ii) TR-103† appartient à un patch non livré (si 009a est renumérotée, il est libéré mais pas réutilisé) ; (iii) la matrice de la copie de travail omet CK-18† à CK-20† et T-44 à T-46.

---

## 3. Cadre documentaire et carte des modifications

### 3.1 Cadre
- Hiérarchie (conventions §2) : CDC > modèle SQLite > `invariants.md` > modèle métier > errata. Le CDC est silencieux sur la couverture et l'ordre acompte / situation : **aucun erratum**.
- Règle anti-régression (modèle §0) : toute règle nouvelle = un INV, une garde, **un test du même nom**. Aucun INV existant ne change de sens ici.
- Conventions §5 : le modèle est mis à jour **avant** la migration ; 001 à 009 immuables ; triggers `tr_<NN>_<table>_<règle>` ; index `idx_<table>_<colonnes>`.
- Conventions §9 : `INSERT OR REPLACE` interdit ; `recursive_triggers=ON` obligatoire sur toute connexion, tests compris.

### 3.2 Hors périmètre (mention de dépendance)
**PT-11 / M3** (composition des lignes d'une situation ; colonnes de situation) : sujet distinct, à concevoir. La couverture ne lit aucune ligne de facture et n'en dépend pas. **H6** (annulation du BC) : séparé. **Situation de montant nul** : règle actuelle inchangée (refus).

### 3.3 Carte
Numéros de ligne : V3.12 officielle / copie de travail V3.14.

| # | Document | Section | Nature |
|---|---|---|---|
| A1 | Modèle SQLite | « Historique des versions » (l.20-36 / l.28) | 1 ligne |
| A2 | Modèle SQLite | §3.2 Facturation (l.166 / l.177) | 1 paragraphe |
| A3 | Modèle SQLite | §4.8 Facturation (l.368 / l.422-445), après `facture_lignes` | 1 bloc |
| A4 | Modèle SQLite | §7.2 Colonnes modifiables (l.576 / l.632) | 1 ligne |
| A5 | Modèle SQLite | §8 Triggers (l.595, TR-22 l.615 / l.652, TR-22 l.672) | 1 ligne modifiée, 2 ajoutées |
| A6 | Modèle SQLite | §9 Index (l.645 / l.705) | 1 ligne |
| A7 | Modèle SQLite | §13.1 cas (l.787 / l.849) et §13.3 tests (l.848 / l.923) | 1 cas, 1 test |
| A8 | Modèle SQLite | §14 (l.866 / l.941) | 1 ligne + 2 CK |
| A9 | Modèle SQLite | §15 Décisions (l.890 / l.977) | 1 ligne |
| A10 | Modèle SQLite | §16 Matrice (l.948 / l.1042) | 1 ligne |
| A11 | Modèle SQLite | §17.1 Suivi des migrations (l.979 / l.1078) | 1 ligne ajoutée (009b) |
| B | `invariants.md` | table des INV, facturation (après INV-58) | 2 lignes |
| C | `modèle-métier-V6.md` | §10 Facture, « Règles » (l.278-316) ; §12 Situation, « Règles » (l.344-362) | 1 puce + 3 puces |
| — | CDC, errata, conventions | — | aucune modification |

---

## 4. Texte proposé pour le modèle SQLite

### 4.1 A1 — Historique des versions
> | **V3.14** (date) | **Couverture des situations** : table de liaison `situation_devis` ; une situation couvre tous les devis rattachés à son BC à son émission ; aucun acompte sur un devis couvert ; contrôles de diagnostic CK-[α] et CK-[β] ; décision D-[ε], invariants INV-[a] et INV-[b] ; migration 009b |

### 4.2 A2 — §3.2, nouveau paragraphe
> **Couverture d'une situation** [INV-[a], INV-[b]] — **[VALIDÉ — décision du propriétaire du 2026-10-18]**
> - Le contractuel d'un BC est la somme des devis qui lui sont rattachés (`bc_devis`). Une situation **couvre** tous les devis rattachés à son BC à l'instant de son émission. La couverture est **enregistrée** (§4.8, `situation_devis`) ; elle n'est jamais déduite d'horodatages, de lignes de facture ou de montants.
> - Un devis rattaché **après** l'émission n'est pas ajouté à une situation existante ; il est couvert par les situations émises ensuite. L'ajout d'un devis ne modifie aucune couverture ni aucune facture déjà émise.
> - **Aucun acompte** ne peut être émis sur un devis couvert par au moins une situation, quels que soient les avoirs, le montant net et l'avancement de cette situation. La règle dépend de l'**émission** de la situation ; un avoir, même total, ne supprime ni la situation ni sa couverture.
> - Un acompte émis **avant** la situation reste valide ; l'acompte d'un devis rattaché après une situation reste possible.
> - Une situation de montant nul reste refusée (`total_ht <> '0.00'`). Un devis couvert peut avoir un avancement propre de 0 %.
> - **Hors périmètre** : la composition des lignes d'une situation et les colonnes de situation (PT-11).

### 4.3 A3 — §4.8, bloc `situation_devis`
> **`situation_devis`** *(nom provisoire)* : `facture_id` NN FK→`factures` (`ON DELETE RESTRICT`, `ON UPDATE RESTRICT`) · `devis_id` NN FK→`devis` (`ON DELETE RESTRICT`, `ON UPDATE RESTRICT`). Table `STRICT`.
> **Clé primaire composite `(facture_id, devis_id)`** : une couverture n'a pas d'identité propre ; la clé interdit le doublon. **Pas d'`id` de substitution, pas d'horodatage, pas de `bc_id`** (le BC se déduit de la facture ; la date d'émission est celle de la facture).
> **Contrôles d'intégrité** (triggers, §8) : (1) la facture est de type `situation` ; (2) le devis appartient au BC de la facture (`bc_devis`) ; (3) aucun `UPDATE`, aucun `DELETE` (y compris le `DELETE` implicite d'un `INSERT OR REPLACE`).
> Une facture couverte et un devis couvert ne peuvent pas être supprimés (FK `RESTRICT`, INV-06 / TR-21 pour les factures). Le `type` et le `bc_id` d'une facture (TR-20) et l'appartenance d'un devis à un BC (INV-184†) étant immuables, les contrôles (1) et (2) restent vrais après l'insertion.
> **Enregistrement** : dans la transaction d'émission de la situation, par **une seule instruction** `INSERT INTO situation_devis (facture_id, devis_id) SELECT :facture, devis_id FROM bc_devis WHERE bc_id = :bc` (exigences d'atomicité : §6). Aucune liste de devis n'est passée en paramètre.
> **Limites** : §14. [INV-[a]]

### 4.4 A4 — §7.2, ligne (colonnes « Table | Non gelé | Gelé »)
> | `situation_devis` | insertion seule, dans la transaction d'émission de la situation | aucune modification (ni UPDATE ni DELETE) |

### 4.5 A5 — §8 Triggers
Ligne **modifiée** (ajout en gras, le reste de la ligne étant celui de la V3.14 réconciliée avec 006) :
> | TR-22 | factures / INSERT | … ; **acompte refusé si son devis est couvert par une situation (`situation_devis`) : la garde ne tient compte ni des avoirs, ni du montant net, ni de l'avancement, ni d'aucun horodatage** ; … | …, **INV-[b]** |

Gabarit de la garde (à reporter dans 009b ; elle s'ajoute aux cinq contrôles existants de `tr_22_factures_acompte` : devis rattaché au BC, aucun solde, un acompte actif par devis, ≤ total du devis, nette ≤ contractuel) :
```sql
SELECT RAISE(ABORT, 'INV-[b]: aucun acompte sur un devis deja couvert par une situation')
 WHERE EXISTS (SELECT 1 FROM situation_devis c WHERE c.devis_id = NEW.devis_id);
```
Lignes **ajoutées** :
> | TR-[γ] | situation_devis / INSERT | `factures.type = 'situation'` pour `facture_id` ; `(factures.bc_id, devis_id)` présent dans `bc_devis` | INV-[a] |
> | TR-[δ] | situation_devis / UPDATE, DELETE | interdits (y compris `DELETE` implicite par `INSERT OR REPLACE`) | INV-[a] |

Noms SQL : `tr_[γ]_situation_devis_insert`, `tr_[δ]_situation_devis_update`, `tr_[δ]_situation_devis_delete`.

### 4.6 A6 — §9 Index
> `situation_devis(devis_id)` — `idx_situation_devis_devis_id` *(la clé primaire tient lieu d'index sur `facture_id`)*

### 4.7 A7 — §13.1, cas chiffré C-[η]
Préconditions : BC `en_cours` ; devis A (1 000,00 €, acompte prévu 30 %), devis B (500,00 €, acompte prévu 30 %) ; dates d'émission croissantes (TR-02).

| Étape | Action | Résultat | Règle qui décide |
|---|---|---|---|
| 1 | BC avec A seul ; S1 à 40 % cumulé | S1 = 400,00 €, couvre {A} | formule §3.2 ; couverture INV-[a] |
| 2 | Acompte de 100,00 € sur A | **refusé** | **couverture** (INV-[b]) : 100 ≤ 30 % × 1 000, nette 500 ≤ 1 000, aucun solde, aucun autre acompte sur A — aucune autre règle ne refuse |
| 3 | Rattachement de B | contractuel 1 500,00 € ; S1 reste {A} | INV-[a] (aucune rétroactivité) |
| 4 | Acompte de 150,00 € sur B | **accepté** | B n'est couvert par aucune situation ; 150 = 30 % × 500 ; nette 550 ≤ 1 500 |
| 5 | S2 à 60 % cumulé | S2 = 900 − (400 + 150) = 350,00 €, couvre {A, B} | formule §3.2 ; INV-[a] |
| 6 | Avoir total sur S1 (400,00 €) | couverture de S1 inchangée : {A} | INV-[a] (aucun lien avec les avoirs) |
| 7 | Acompte de 100,00 € sur A | **refusé** | **couverture** (INV-[b]) ; le montant net de S1 (0) n'intervient pas |

**Témoin** : à l'étape 2, dans le même état **sans couverture enregistrée**, la chaîne 001-009 telle qu'elle est **accepte** l'acompte. Le refus vient donc bien de la couverture, et d'aucune règle implicite. (Rejeu effectué en mémoire, voir §8 ; à retranscrire en test lors de l'implémentation.)

### 4.8 A8 — §14, ligne et diagnostics
> | Toute situation enregistre une couverture, et celle-ci comprend **tous** les devis rattachés à son BC à l'émission | service d'émission (un seul `INSERT … SELECT` dans la transaction, §6) **vérifié par les tests** + **CK-[α]** (situation sans aucune couverture) + **CK-[β]** (couverture non monotone : un devis couvert par une situation n'est plus couvert par une situation plus récente du même BC). SQLite ne peut ni exiger la présence d'enfants au `COMMIT`, ni vérifier l'exhaustivité, ni distinguer l'`INSERT` d'émission d'un `INSERT` tardif sans horodatage. **L'exhaustivité est donc garantie par le service et vérifiée par les tests**, non par SQLite. Une couverture erronée mais valide est permanente (immuabilité). |

**D1 et D2 — inscription justifiée** : le modèle (§0 règle 3) exige une garde pour chaque règle ; pour l'omission d'une couverture par le service, un diagnostic est la seule garde possible, et le §14 consigne déjà ce type de limite (CK-13). Deux requêtes de lecture, aucun horodatage, rien de bloquant. **D3 (diagnostic à horodatage) est écarté.** Requêtes (exécutées avec succès sur la chaîne 001-009 et le DDL provisoire en mémoire : cas sain → aucune ligne ; situation sans couverture → D1 la signale ; couverture non monotone → D2 la signale) :
```sql
-- CK-[α] (D1)
SELECT f.id FROM factures f
 WHERE f.type = 'situation'
   AND NOT EXISTS (SELECT 1 FROM situation_devis c WHERE c.facture_id = f.id);

-- CK-[β] (D2)
SELECT s1.id AS situation_ancienne, s2.id AS situation_recente, c1.devis_id
  FROM factures s1
  JOIN factures s2 ON s2.bc_id = s1.bc_id AND s2.type = 'situation'
                  AND s2.situation_numero > s1.situation_numero
  JOIN situation_devis c1 ON c1.facture_id = s1.id
 WHERE s1.type = 'situation'
   AND NOT EXISTS (SELECT 1 FROM situation_devis c2
                    WHERE c2.facture_id = s2.id AND c2.devis_id = c1.devis_id);
```
Les rattachements ne faisant que croître (`bc_devis` immuable), toute ligne de D2 est une anomalie. Limite assumée : l'omission partielle sur la **dernière** situation n'est visible ni de D1 ni de D2 ; elle n'est couverte que par les tests du service (D3 écarté).

### 4.9 A9 — §15, décision
> | D-[ε] | **Couverture des situations et ordre acompte / situation** : une situation couvre tous les devis rattachés à son BC à l'émission ; aucun acompte sur un devis couvert | déduction par horodatage (proposition de travail du 2026-10-17) ; sélection libre des devis par situation ; lecture de la couverture dans les lignes de facture | **Validée** 2026-10-18 (propriétaire) ; INV-[a], INV-[b] ; D3 non retenu |

### 4.10 A10 — §16, ligne
> | Ordre acompte / situation exprimé par des horodatages (proposition de travail du 2026-10-17, non retenue) | Remplacé par la couverture enregistrée : INV-[a], INV-[b] · TR-22, TR-[γ], TR-[δ] |

### 4.11 A11 — §17.1, ligne ajoutée (colonnes « Migration | Contenu | Modèle | Test »)
> | `src-tauri/migrations/metier/009b_acompte_garanties_manuelles.sql` | *(contenu existant de 009b)* + table `situation_devis` (clé composite, index), triggers TR-[γ] et TR-[δ], garde d'acompte de TR-22 fondée sur la couverture, **garde de migration : refus d'application si une situation existe** ; rang 14 de la chaîne (rang et numéro : AR-06) | V3.14 | T-[ζ] |

Si 009b avait été livrée ou appliquée hors dépôt (rien ne le montre : §8), ce contenu irait dans la migration du rang suivant.

---

## 5. Textes pour `invariants.md` et le modèle métier

**`invariants.md`** (table des INV, après INV-58) :
> | INV-[a] | **Couverture d'une situation** : une situation couvre tous les devis rattachés à son BC à l'instant de son émission ; la couverture est enregistrée dans la transaction d'émission, ne comprend que des devis du BC de la facture, appartient à une facture de type situation, est immuable ; un devis rattaché ensuite n'est couvert que par les situations émises après | SQL (PK, FK), TRG (TR-[γ], TR-[δ]), SVC (émission atomique), CK ([α], [β]) | C-[η], T-[ζ] |
> | INV-[b] | **Aucun acompte sur un devis couvert** par une situation, quels que soient les avoirs, le montant net et l'avancement de cette situation ; l'acompte émis avant la situation, ou sur un devis rattaché après, reste possible | TRG (TR-22) | C-[η], T-[ζ] |

Tests du même nom : `test_INV_[a]_…`, `test_INV_[b]_…`. Aucun INV retiré ni modifié : pas de ligne au journal.

**`modèle-métier-V6.md`** : §10 Facture, « Règles » — 1 puce : « Un acompte ne peut pas être émis sur un devis déjà couvert par une situation (§12). » §12 Situation, « Règles » — 3 puces : « Une situation couvre tous les devis rattachés à son BC au moment de son émission ; un devis rattaché ensuite n'est pas ajouté aux situations déjà émises. » · « Aucun acompte ne peut être émis sur un devis couvert par une situation, quels que soient les avoirs, le montant net et l'avancement de cette situation. » · « Une situation de montant nul n'existe pas ; un devis couvert peut cependant avoir un avancement propre de 0 %. »

---

## 6. Exigences d'atomicité pour le futur service d'émission

1. L'émission d'une situation est **une seule transaction `BEGIN IMMEDIATE`**.
2. Dans cette transaction, dans cet ordre : lecture du contexte et calculs → `INSERT` de la facture → `INSERT` des lignes → **`INSERT … SELECT` de la couverture** → `COMMIT`.
3. La couverture est écrite par **une seule instruction** lisant `bc_devis` pour le BC de la facture ; aucun identifiant de devis n'est passé en paramètre.
4. Toute erreur, y compris d'un trigger de couverture, entraîne un `ROLLBACK` complet : ni facture, ni lignes, ni couverture. Le service n'emploie ni `INSERT OR REPLACE` (interdit, conventions §9) ni `INSERT OR IGNORE` sur la couverture.
5. Rattachement d'un devis et émission d'une situation sont des écritures **sérialisées** : un devis est soit rattaché avant l'émission (couvert), soit après le `COMMIT` (non couvert).
6. Le numéro est attribué dans cette transaction (compteur de `machine.db`) ; un échec peut laisser un trou de numérotation, accepté (CDC l.590, INV-25).
7. Aucun autre chemin d'écriture dans `situation_devis` sans décision humaine.
8. **Exhaustivité** : SQLite ne la garantit pas ; elle est garantie par le service (points 2 et 3) et **vérifiée par les tests** (§9, tests 3 et 9) et par CK-[α] / CK-[β].

---

## 7. Garde de migration

La migration refuse de s'appliquer si `factures` contient au moins une ligne de type `situation`, sans modifier de donnée ni fabriquer de rattachement. Aucune situation n'ayant de couverture avant cette migration, toute situation préexistante est « sans rattachement fiable ». Forme : table `TEMP` à contrainte `CHECK`, alimentée par un `SELECT` de comptage, supprimée aussitôt — modèle déjà livré dans 005b (gardes `garde_005b_*`). Comportement en échec : la contrainte lève une erreur, le script s'arrête et le lanceur annule la transaction (005b l.62 et l.83) : base et `user_version` inchangés. Le lanceur n'étant pas dans le dépôt, ce comportement n'est imité que par les tests (non vérifiable ailleurs). Pas de récupération d'historique, pas de mécanisme d'import.

---

## 8. Vérification technique ciblée

| Point | Constat dans les migrations livrées | Compatibilité |
|---|---|---|
| Tables et colonnes cibles | `factures(id INTEGER PRIMARY KEY AUTOINCREMENT, type, bc_id, devis_id, …)` ; `bc_devis(id, bc_id, devis_id UNIQUE, rang, created_at)` ; `devis(id)` | FK `situation_devis → factures(id)` et `→ devis(id)` possibles ✓ |
| Identification d'une situation | `type TEXT NOT NULL CHECK (type IN ('acompte','situation','solde','avoir'))` ; `CHECK ((type='situation') = (situation_numero IS NOT NULL))` ; **aucune colonne `statut`, aucun `cancelled_at`** | la proposition n'emploie que `type = 'situation'` ✓ ; la V3.12 décrit encore `cancelled_at` et `statut` : jamais utilisés ici |
| TR-22 actuel | `tr_22_factures_acompte` : `BEFORE INSERT … WHEN NEW.type='acompte'`, 5 contrôles, **aucune règle d'ordre situation → acompte** | la garde s'ajoute ; 009b remplace le trigger par `DROP` / `CREATE` ; sa condition à horodatages du patch `h` est à remplacer |
| `STRICT` | présent sur les tables de 005b et 006 | repris ✓ |
| `WITHOUT ROWID` | **0 occurrence dans 001-009** | **retiré de la proposition** (incompatible avec « conventions déjà présentes ») ; clé primaire composite d'une table `STRICT` ordinaire |
| Triggers et index | `tr_<NN>_<table>_<règle>`, `idx_<table>_<colonnes>` ; `BEFORE INSERT` avec `RAISE(ABORT, 'INV-xx: …')` | repris ✓ |
| Migrations transactionnelles | aucune migration ne contient `BEGIN`, `COMMIT` ni `PRAGMA` ; le lanceur gère la transaction | repris ✓ |
| `INSERT OR REPLACE` | interdit (conventions §9) ; `recursive_triggers=ON` obligatoire | trigger `DELETE` conservé comme filet ✓ |
| Garde de migration | modèle 005b / 009b (table `TEMP` + `CHECK`) | §7 ✓ |
| Statut de 009a / 009b (H7) | absentes de l'arborescence ; « créée, à relire » dans les tableaux de suivi du patch `h` ; aucun lanceur ni base dans le dépôt | traitées comme **non livrées** (fait vérifié ; l'application hors dépôt n'est ni démontrée ni exclue) |

**Corrections minimales apportées à la première version** : retrait de `WITHOUT ROWID` ; retrait des citations INV-180 et INV-190 ; ajout des préconditions du cas chiffré (acompte prévu 30 %, dates croissantes) pour que chaque refus ou acceptation découle de la couverture ; lignes A11 et §17.1 reformulées en ajout ; abandon de la numérotation de la V3.13.

**Rejeu du cas chiffré (sondes jetables, hors dépôt)** sur la chaîne 001-009 de `main` avec le DDL provisoire et la garde en mémoire : S1 = 400,00 (couvre A) ; acompte 100 sur A refusé ; contractuel 1 500,00 ; acompte 150 sur B accepté ; S2 = 350,00 (couvre A et B, S1 reste {A}) ; avoir total sur S1 (400,00) : couverture de S1 inchangée ; acompte 100 sur A refusé. **Témoin** sans couverture ni garde : acompte 100 sur A accepté. Ces sondes **ne valident pas** la solution.

---

## 9. Tests d'acceptation indispensables

**Aucun n'est écrit ni exécuté.**

| # | Test d'acceptation |
|---|---|
| 1 | Acompte refusé sur un devis couvert (étapes 2 et 7 du cas C-[η]), y compris avec des `created_at` identiques ou inversés ; **témoin** : accepté sans couverture |
| 2 | Acompte autorisé sur un devis rattaché après la situation (étape 4) |
| 3 | Nouvelle situation après A et B : couvre A et B ; l'ancienne garde {A} (**exhaustivité vérifiée par le test**) |
| 4 | Situation entièrement créditée : couverture inchangée, acompte toujours refusé |
| 5 | Devis couvert à 0 % d'avancement propre : couvert, acompte refusé |
| 6 | Couverture d'un devis d'un autre BC : refusée |
| 7 | Couverture d'une facture non situation : refusée |
| 8 | UPDATE, DELETE, `INSERT OR REPLACE` sur la couverture ; DELETE de la facture ou du devis couvert : refusés |
| 9 | Échec injecté en cours d'émission : ni situation ni couverture ; trou de numérotation toléré |
| 10 | Plafonds d'acompte, situation de montant nul toujours refusée, autres contrôles : aucune régression |
| 11 | Garde de migration : refus si une situation existe (base inchangée) ; acceptation sinon |
| 12 | CK-[α] et CK-[β] détectent les anomalies et ne bloquent rien |
| 13 | Rejeu 001 → 009a → 009b depuis une base vide et depuis le rang 12 ; 001 à 009 identiques à GitHub ; campagne de mutation |

---

## 10. Cohérence avec 001 à 009
Aucune modification de 001 à 009. Objets **additifs** : `factures`, `facture_lignes`, `bc_devis`, `devis` ne changent pas de structure. `tr_22_factures_acompte` (006) n'est pas réécrit : 009b le remplace. Les contrôles réutilisent des garanties existantes (TR-20, TR-21, INV-184†). La règle ne dépend ni de l'état « actif / neutralisée » d'une facture (PT-9 ouvert) ni d'aucun horodatage.

---

## 11. Blocages réels avant la rédaction officielle

| # | Blocage | Portée |
|---|---|---|
| B1 | **Identifiants** : valider les planchers du §2 (INV-204, INV-205, TR-104, TR-105, CK-21, CK-22, D-62, C-43, T-53) comme attribution, ou arbitrer AR-01 | Ne bloque pas la rédaction du texte (emplacements). Bloque le **SQL** : les noms de triggers dépendent des numéros TR (conventions §5) |

Dépendances ouvertes **non bloquantes** : AR-06 (rang et numéro de 009a / 009b), AR-08 (partie « solde » de TR-22), PT-11 / M3 (hors périmètre). H7 n'est plus un blocage : fait vérifié dans le dépôt (§8).

---

## 12. Conclusion

**La proposition était prête à valider ; elle est validée (2026-10-18)** : la base est la V3.12, les écarts V3.13 sont classés, les identifiants sont contrôlés sans réattribution silencieuse, et le cas chiffré découle de la seule couverture. La rédaction officielle de la V3.14 peut commencer avec les emplacements ; **une seule décision (B1) conditionne le passage au SQL**. Ordre : validation de la proposition → rédaction de la V3.14 (avec `invariants.md` et le modèle métier) → patch 009b révisé et ses tests → rejeu complet.
