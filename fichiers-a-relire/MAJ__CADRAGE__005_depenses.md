# BATORYA Essentiel V6 — Cadrage de la tranche 005 « Dépenses » — version révisée (revue critique finale 2026-10-03 ; DV-1, DV-2, DV-3 tranchées le 2026-10-04)

**Mise à jour 2026-10-04** : **DV-1** (versionnement des migrations), **DV-2** (mécanisme d'annulation) et **DV-3** (annulation irréversible) sont **tranchées** (§7 bis). La tranche 005 reste la tranche **métier Dépenses** (`005_depenses.sql`, rang 5) ; M-A et M-B sont des **correctives** ultérieures (`005a`, `005b`, rangs 6 et 7) qui s'exécutent avant 006 et ne renumérotent aucune tranche. Les décisions **DV-4 à DV-10** restent à valider. Le texte de la version précédente qui contredisait ces décisions est corrigé (liste en §6 : C-M à C-O).

**Statut** : cadrage **en relecture**, à valider avant toute écriture de `005_depenses.sql` et de `test_005_depenses.py`. Aucune migration, aucun test, aucun code, aucun trigger réel, aucun fichier officiel (`docs/**`) n'a été créé ou modifié par cette révision.
**Périmètre** : BATORYA **Essentiel** uniquement. Rien de BATORYA Entreprise, rien des tranches 006 et suivantes (facturation, règlements, garanties, PV, planification, URSSAF, historique, documents).
**Base** : dépôt `mymypav-max/BATORYA-Essentiel`, migrations 001–004 et tests 001–004 **inchangés** depuis la première version de ce cadrage (état `548f61f` → `origin/main` : aucune différence sous `src-tauri/migrations` et `src-tauri/tests`) ; copies de travail `MAJ__*` de `fichiers-a-relire/` (modèle SQLite **V3.13**, invariants INV-179 à INV-196, errata E-10 à E-20, décisions D-40 à D-54) comme référence documentaire de travail lorsqu'elles corrigent les anciennes versions.
**Remplace** la première version de ce cadrage, dont le corps reposait sur des hypothèses **devenues caduques** (liste en §9). Les anciennes questions Q1 à Q9 sont reprises, tranchées ou reformulées en décisions **DV-1 à DV-10** (§7).

**Classement utilisé partout** (colonne « Nature », exclusivement) :

| Nature | Sens |
|---|---|
| **Règle documentée** | énoncée par un document V6 (CDC, errata, Métier, Modèle, invariants, audit de conservation validé) ou par une migration existante |
| **Déduction technique** | conséquence SQL/SQLite d'une règle documentée ; aucune règle métier nouvelle |
| **Proposition** | choix de conception de ma part, non décidé par le métier |
| **Décision à valider** | point que les sources ne tranchent pas ; **aucune règle n'est créée par déduction** |

Légende : « Modèle » = modèle SQLite V3.13 (copie de travail) ; « Métier » = modèle métier V6 ; « INV » = invariants ; « D-xx », « C-xx », « T-xx », « TR-xx », « CK-xx », « PT-xx » = identifiants du Modèle ; « Audit conservation » = `AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES` (D1 à D6, validées).

---

## 0. Synthèse

| Sujet | Contenu de la tranche |
|---|---|
| Tables | **1** : `depenses` (catégories dans 001, fournisseurs dans 002, BC dans 004) |
| Triggers | **3 certains** : TR-01 (numéro et année immuables), **garde de suppression** (INV-06, Audit conservation §7.3 n°1) et **verrou d'une dépense annulée** (TR-102) (DV-3, option A validée). Aucun trigger inter-tables, aucun trigger sur les tables des tranches précédentes |
| Index | **4** (Modèle §9) : `bc_id`, `fournisseur_id`, `categorie_id`, `date_depense` |
| Cycle de vie | création → correction (erreur de saisie) → **annulation** (principe validé : E-19, INV-193, D-50) ; **jamais de suppression** ; **aucun statut** ; mécanisme d'annulation = `cancelled_at` + `motif_annulation`, **sans `statut`** (**DV-2 validée le 2026-10-04**) ; annulation **irréversible**, sans réactivation (**DV-3, option A, validée**) |
| BC annulé | une dépense **peut y être créée et y rester liée** (D5, INV-188, INV-100, INV-193) — règle documentée ; ses prolongements (rattachement d'une dépense existante, 30 jours) restent à valider (DV-6, DV-7) |
| Fournisseur | **facultatif**, par identifiant, **sans statut ni archivage** (E-12, INV-183) : la règle « fournisseur actif » de la première version est **retirée** |
| TVA | **aucune** (franchise) : un seul `montant` D2 ; ni taux, ni TTC, ni ventilation |
| Import | **aucun** : `depenses` (et `fournisseurs`) sont des blocs **refusés** de `import-v6.json` (Modèle §10.3, D-23) ; ni `origine`, ni `legacy_*` |
| Numérotation | `DEP-nnnnn-yy`, `yy` = année de `date_depense`, mécanisme **PT-1 tranché** ; aucun doublon > absence de trou |
| Contrôles CK | **aucun nouveau CK** ; CK-01, CK-02, CK-03 couvrent `depenses` ; CK-10 à étendre (libellé) ; CK-13 et CK-14 non concernés |
| Pré-requis documentaire | modèle **V3.13 validé avant** la migration (conventions §5) ; **place dans la chaîne tranchée** (DV-1, V-1 à V-5) : `005_depenses.sql` = rang 5 ; M-A (`005a`) et M-B (`005b`) viennent après et avant 006 |
| Décisions à valider | **7** restantes (§7 : DV-4 à DV-10), dont DV-5/DV-6 (rattachement) ; DV-1, DV-2 et DV-3 **tranchées** le 2026-10-04 (§7 bis) |

---

## 1. Règles documentées (base de la tranche)

| # | Règle | Nature | Source |
|---|---|---|---|
| R1 | Une dépense est une charge enregistrée, pour l'analyse de gestion et de marge ; elle ne réduit **jamais** le CA URSSAF | Règle documentée | CDC §28 ; Métier §17, §18 ; INV-100, INV-120 |
| R2 | Une dépense est **globale** (sans BC) ou **rattachée à un BC** | Règle documentée | CDC §28 ; Métier §18 ; Modèle §4.12 |
| R3 | Fournisseur **facultatif** (« lorsque nécessaire »), référencé **par identifiant** | Règle documentée | CDC §28 ; Métier §18, §19 ; INV-100 |
| R4 | Aucune gestion du paiement : ni statut payé/non payé, ni échéance, ni règlement fournisseur, ni dépenses à payer | Règle documentée | CDC §28 (hors périmètre) ; Métier §18 ; INV-100 |
| R5 | `montant` : « montant réellement payé », franchise de TVA, 2 décimales exactes (D2), jamais `0.00`, jamais négatif | Règle documentée | Métier §2.1, §18 ; Modèle §2.3, §4.12 ; INV-11, INV-14 |
| R6 | **Plus de fournisseur archivé** : tout fournisseur reste sélectionnable pour une nouvelle dépense | Règle documentée | Métier §17, §19 ; E-12 ; INV-100, INV-183 |
| R7 | Un fournisseur est **conservé définitivement** : code immuable, aucune suppression, aucun archivage ni statut | Règle documentée | INV-183 ; Métier §19 ; D-43 |
| R8 | **Règle des 30 jours** : à compter de `date_100_facture`, rattachement normal pendant 30 jours calendaires ; ensuite **confirmation simple** (« clôturé depuis X jours », X = jours écoulés − 30, C-22 : 45 jours → 15) ; ni déblocage, ni délai maximal ; **règle de service, aucun trigger** | Règle documentée | CDC §15 ; Métier §17 ; Modèle §4.12 (`date_du_jour > date_100_facture + 30 jours`), D-31, C-21, C-22 ; INV-103 |
| R9 | La clôture des dépenses n'affecte ni le statut financier du BC, ni son historique, ni les dépenses déjà rattachées ; le BC n'expose que `date_100_facture` | Règle documentée | Modèle §3.5 |
| R10 | Numéro `DEP-00001-yy`, séquence `DEP`, `yy` = année de **`date_depense`** ; **jamais attribué deux fois** ; trou accepté et jamais récupéré ; plafond 99 999 ; pas de chronologie continue (TR-02 ne concerne pas DEP) | Règle documentée | Modèle §6 ; Métier §2.2 ; INV-20, INV-22, INV-24, INV-179 ; D-54 |
| R11 | `numero` immuable ; `date_depense` modifiable **tant que l'année (yy) ne change pas** ; sinon : annulation puis nouvelle saisie | Règle documentée | Modèle §4.12, §6, §8 (TR-01) ; INV-23 |
| R12 | Borne d'année **2001–2099** de `date_depense` : contrôle du **service**, jamais un CHECK | Règle documentée | INV-177 ; D-38 |
| R13 | Catégorie obligatoire (liste de référence modifiable : ordre, **état actif**) | Règle documentée | Modèle §4.3, §4.12 ; D-12, D-18 ; Métier §4.2 |
| R14 | Pièce jointe facultative : `piece_jointe_chemin` et `piece_jointe_racine_id`, « les deux ou aucun » ; chemins relatifs à une racine identifiée | Règle documentée | Modèle §4.12 ; INV-106 |
| R15 | `description` obligatoire ; `notes` facultatif ; dates de création et de modification | Règle documentée | Modèle §4.12 ; Métier §18 |
| R16 | Une dépense **corrigeable** pour erreur de saisie, **annulable** lorsqu'elle ne doit plus participer aux calculs ; une dépense annulée reste en base avec numéro, historique et relations, exclue des totaux et calculs opérationnels concernés (liste : PT-14) ; **aucune suppression d'une dépense numérotée** | Règle documentée | E-19 ; INV-193 ; INV-06 ; D-50 ; Audit conservation D5 ; Métier §2.4, §18 |
| R17 | **Une dépense peut être créée sur un BC annulé et y rester liée** | Règle documentée | Audit conservation D5, §7.1 n°4 ; INV-188, INV-100, INV-193 ; Métier §18 ; CDC §28 (E-19) |
| R18 | `depenses` **n'est pas importable** (bloc refusé de `import-v6.json`) | Règle documentée | Modèle §10.3 ; D-23 ; en-tête de `002_fournisseurs.sql` |
| R19 | FK en `RESTRICT` par défaut, jamais de `ON UPDATE`, `id` AUTOINCREMENT, tables `STRICT`, `recursive_triggers=ON`, `INSERT OR REPLACE` interdit par convention | Règle documentée | Modèle §1, §2.1 ; INV-04, INV-05, INV-07 ; D-39 |
| R20 | Index `depenses(bc_id)`, `(fournisseur_id)`, `(categorie_id)`, `(date_depense)` | Règle documentée | Modèle §9 |
| R21 | TR-01 couvre explicitement les dépenses (« `numero` immuable ; année de la date de numérotation immuable ») | Règle documentée | Modèle §8 |
| R22 | L'annulation d'un objet annulable est tracée (« date et motif ») ; l'annulation d'une dépense est un événement tracé de l'historique | Règle documentée | Métier §2.4, §26 (événements tracés) ; INV-110, INV-194 |

---

## 2. Revue des points (1 à 12)

### 2.1 BC annulé — point prioritaire

Le cadrage d'origine déclarait le sujet « sans règle » (Q2, trois options A/B/C). **C'est caduc** : l'Audit de conservation (D5, validée) et INV-188 le tranchent dans son principe. Reste ce que les sources ne disent **pas**.

| Question | Conclusion | Nature | Source |
|---|---|---|---|
| Créer une **nouvelle** dépense avec un BC annulé | **Autorisé** (« règle métier volontaire » : achat réel après rétractation du client) | Règle documentée | Audit conservation D5 et §7.1 n°4 ; INV-188 ; INV-100 ; Métier §18 |
| Une dépense déjà rattachée quand le BC **devient** annulé | **Reste rattachée** ; l'annulation du BC ne modifie aucune dépense (aucun trigger de 001–004 ne touche `depenses` ; pas de cascade) | Règle documentée (conservation) ; Déduction technique (absence de trigger) | INV-188, INV-193 ; Audit conservation §7.2 n°3 ; 004 |
| Une dépense **annulée** peut rester liée à un BC annulé | Oui | Règle documentée | INV-193 |
| Rattacher une dépense **existante** (globale ou d'un autre BC) à un BC **déjà annulé** | **Non documenté** : D5 vise la *création* (« créée et rattachée ») | **Décision à valider** | DV-6 |
| **Détacher** une dépense d'un BC annulé (`bc_id` → NULL) ou la déplacer | **Non documenté** (détachement et changement de BC sont silencieux, annulé ou non) | **Décision à valider** | DV-5 |
| **Modifier** (montant, description, catégorie…) une dépense active liée à un BC annulé | Aucune source ne distingue ce cas : INV-173 ne gèle que les données commerciales du **BC** ; une dépense n'en est pas une. Le SQL de 004 n'interdit rien. L'**absence de restriction** est l'état par défaut, **non une règle validée** | Déduction technique ; confirmation dans DV-5 | INV-173 ; Audit conservation §7.2 n°4 |
| **30 jours** sur un BC annulé | `date_100_facture` NULL → aucun point de départ, la règle ne s'applique pas. Mais depuis E-15/D-46 un BC peut être annulé **avec** un solde actif (D-05 remplacée) : `date_100_facture` peut alors être non NULL ; l'Audit conservation (§7.3 n°5) laisse expressément ce cas à préciser | **Décision à valider** | DV-7 |

**Correction d'une erreur de la première version** : elle affirmait « un BC annulé a en principe `date_100_facture` NULL (annulation avec solde actif interdite, D-05 / INV-44) ». D-05 est **remplacée** (D-46, E-15, INV-44) : l'annulation est possible quel que soit l'état de la facturation. L'affirmation est supprimée.

### 2.2 États du BC (vérifiés séparément, sans transposition depuis devis ou factures)

Les statuts réels du BC (004, CHECK) sont `en_cours`, `termine`, `annule`. Le **gel** n'est pas un statut ; le « gel commercial » est **supprimé** en V3.13 (Métier, « Plus de gel commercial » ; PT-8) et `frozen_at` est appelé à être adapté.

| État du BC | Nouvelle dépense / nouveau rattachement | Nature | Source |
|---|---|---|---|
| `en_cours`, `date_100_facture` NULL | libre | Règle documentée | R8 |
| `en_cours`, 100 % facturé depuis ≤ 30 jours | libre, sans confirmation | Règle documentée | C-21, INV-103 |
| `en_cours`, 100 % facturé depuis > 30 jours | confirmation simple (« clôturé depuis X jours ») | Règle documentée | C-22, D-31 |
| `termine` | la règle porte sur `date_100_facture` (toujours renseignée, CHECK de 004), non sur le statut : **même règle, aucune règle propre à `termine`** | Déduction technique | D-31 ; 004 (`statut <> 'termine' OR date_100_facture IS NOT NULL`) |
| « gelé » | **aucun effet** ; aucune règle de dépense ne doit dépendre de `frozen_at` (en cours de révision, PT-8). Une dépense n'écrit rien dans `bons_commande` | Déduction technique | Métier (gel supprimé) ; PT-8 ; 004 |
| `annule` | création et maintien du lien : documentés ; autres cas : **voir §2.1** | Règle documentée / Décision à valider | R17 ; DV-5, DV-6, DV-7 |

Rien n'est repris des règles propres aux devis (verrouillage) ou aux factures (avoirs, TR-16).

| Évènement sur le BC | Effet sur les dépenses rattachées | Nature | Source |
|---|---|---|---|
| régénération des lignes / modification du devis | aucun (`bons_commande.id` stable) | Déduction technique | 004 |
| annulation du BC | aucun (conservation, pas de cascade) | Règle documentée | INV-188 |
| passage `termine` ↔ `en_cours` | aucun | Déduction technique | D-31, R9 |
| suppression du BC | impossible (TR-19) | Règle documentée | INV-174, D-35 |

### 2.3 Fournisseur

| Question | Conclusion | Nature | Source |
|---|---|---|---|
| Obligatoire ? | **Non** : `fournisseur_id` NULL admis | Règle documentée | R3 |
| Fournisseur utilisable pour une nouvelle dépense | **Tout fournisseur existant** ; il n'existe ni archive, ni statut, ni réactivation. La règle « fournisseur actif » de la première version est **supprimée** | Règle documentée | R6, R7 ; E-12 ; INV-183 |
| Changer ou retirer le fournisseur d'une dépense existante | **Non documenté** | **Décision à valider** | DV-5 |
| Modification ultérieure des données du fournisseur | autorisée (INV-183) ; la dépense référence l'identifiant : elle présente les données **courantes**, aucune copie du nom dans `depenses` | Règle documentée (modification) ; Déduction technique (pas de copie) | INV-183, INV-100 |
| Suppression physique du fournisseur | **interdite** (INV-183) ; garde SQL côté dépenses : FK `RESTRICT` ; la garde sur `fournisseurs` (TR-97, PT-4) appartient à la migration corrective M-A, **pas à 005** | Règle documentée ; Proposition (PT-4, hors 005) | INV-183, INV-05 ; 002 (en-tête) |
| Fournisseur « qui ne peut plus être utilisé » | **n'existe pas** | Règle documentée | R6 |

**Contradiction avec la migration 002 (immuable)** : `fournisseurs.statut` (`actif`/`archive`, NOT NULL) existe encore. Il disparaîtra par la corrective M-A (`005a`, PT-3, contenu en proposition) : suppression de l'index `idx_fournisseurs_statut` puis de la colonne, **sans reconstruction de `fournisseurs`** (vérifié ; la FK `depenses.fournisseur_id` n'est donc pas affectée). **Conséquence pour 005** : le DDL, les triggers et les tests de `depenses` ne lisent, ne testent et ne présupposent **jamais** `fournisseurs.statut` (les fixtures de test fournissent la valeur imposée par 002 sans la commenter). Aucune notion d'archivage n'est réintroduite.

### 2.4 Dépense globale (`bc_id` NULL)

| Question | Conclusion | Nature | Source |
|---|---|---|---|
| Autorisée | Oui | Règle documentée | R2 |
| Règles propres | Aucune règle distincte n'est documentée. La règle des 30 jours concerne le **rattachement à un BC** : elle n'a pas d'objet tant que `bc_id` est NULL | Règle documentée ; Déduction technique | INV-103 |
| Numéro | identique (DEP) | Règle documentée | R10 |
| Rattacher plus tard à un BC / détacher / changer de BC | **Non documenté** | **Décision à valider** | DV-5 |
| Prise en compte dans les analyses (globales ou par BC) | analyses calculées, jamais stockées, **hors tranche** ; la première version affirmait « elle entre dans les analyses globales de marge » : non documenté, **retiré** | Décision à valider (hors 005) | Métier §17 |

### 2.5 Dates (notions distinctes)

| Notion | Conclusion | Nature | Source |
|---|---|---|---|
| **Date de dépense** (`date_depense`) | date réelle `YYYY-MM-DD` (`GLOB` + `date(x) IS x`), NOT NULL ; borne 2001–2099 au **service** ; modifiable dans la même année | Règle documentée | R10–R12 ; INV-10, INV-177 |
| Sens de `date_depense` (date de la facture fournisseur ou date du paiement) | les documents disent « date » et « montant réellement payé » sans trancher | **Décision à valider** (libellé, sans effet SQL) | DV-8 |
| **Date de facture** (fournisseur) | **aucune colonne** : rien dans les documents ne la prévoit ; ne pas la confondre avec `date_100_facture`, colonne **du BC** (début des 30 jours) | Décision à valider (confirmer l'absence) | DV-8 ; INV-43 |
| **Date de saisie** | `created_at` (TS UTC, défaut maître) ; `updated_at` pour la modification ; ce ne sont pas des dates métier et une date métier n'est jamais déduite d'un timestamp | Règle documentée | Modèle §2.2 ; INV-10 |
| **Date d'échéance** | **exclue** | Règle documentée | R4 (Métier §18, INV-100) |
| **Date d'annulation** | `cancelled_at` (TS UTC, millisecondes) ; « date et motif » exigés par le Métier §2.4 ; colonne **validée** (DV-2) | Règle documentée (date et motif ; DV-2 validée le 2026-10-04) | Métier §2.4 ; DV-2 |
| **Date de l'année du numéro** | `date_depense` | Règle documentée | R10 ; Métier §2.2 |
| Cohérence `date_depense` ↔ dates du BC ou date du jour (date future, antérieure au BC) | aucune règle ⇒ **aucun contrôle** en 005 | Décision à valider (confirmer) | DV-8 |
| Point de départ des 30 jours | `date_100_facture` du BC, comparée au **jour courant local** à la date du rattachement (pas à `date_depense`) | Règle documentée | R8 ; Modèle §2.2 |

### 2.6 Montants — exclusivement sans TVA

| Sujet | Conclusion | Nature | Source |
|---|---|---|---|
| Colonne | **une seule** : `montant`, D2, TEXT canonique ; aucun `REAL` | Règle documentée | R5 ; INV-11 |
| TVA, TTC, ventilation, récupération | **absents** (franchise de TVA) ; aucune colonne ni règle | Règle documentée | CDC §2 ; Métier (en-tête, §18) ; Modèle §4.12 |
| Zéro et négatif | `0.00` refusé ; négatif refusé (les négatifs autorisés par INV-14 excluent les dépenses ; D2 est ≥ 0) | Règle documentée | Modèle §4.12 ; INV-14, §2.3 |
| Précision et arrondi | 2 décimales saisies, conservées exactes ; **aucun calcul ni arrondi** à l'écriture | Déduction technique | INV-11 ; CDC (arrondi par ligne de document, sans objet ici) |
| Sommes (totaux par BC, marge) | calculées par le service, **hors tranche**, en centimes entiers, jamais en flottant | Déduction technique | INV-11 ; Métier §17 |
| Avoir fournisseur, remboursement reçu | **non représentables** (aucun négatif) : limite connue | Règle documentée (limite) | INV-14 ; DV-9 pour la confirmer |

### 2.7 Cycle de vie

| Étape | Conclusion | Nature | Source |
|---|---|---|---|
| Création | une dépense naît numérotée ; **aucun brouillon de dépense** n'existe dans les documents | Déduction technique | INV-180/185 (brouillon : devis seulement) |
| Modification (correction d'erreur de saisie) | autorisée pour une dépense active ; `numero` et année de `date_depense` immuables | Règle documentée | R11, R16 |
| Champs corrigeables (fournisseur, BC, catégorie, pièce jointe…) | non détaillés | **Décision à valider** | DV-5 |
| Validation | **aucune** : aucun statut de validation n'est prévu ; aucun n'est créé | Déduction technique | INV-100 ; Métier §18 |
| Annulation (principe) | annulable ; objet conservé ; exclu des calculs concernés ; motif et date | Règle documentée | R16, R22 |
| Annulation (mécanisme) | **pas de colonne `statut`** : `cancelled_at` + `motif_annulation`, annulation ⇔ `cancelled_at IS NOT NULL` (même logique que les règlements, INV-70 ; 004 : `(statut='annule') = (cancelled_at IS NOT NULL)`) ; timestamp UTC en millisecondes ; motif obligatoire et non vide ; les deux colonnes cohérentes (toutes deux NULL ou toutes deux renseignées) | Règle documentée (DV-2 validée le 2026-10-04) | DV-2 ; PT-14 |
| Dépense annulée : modifiable ? réactivable ? | **non modifiable, non réactivable** : annulation **irréversible** ; aucune modification métier d'une dépense annulée ; une nouvelle dépense est un **nouvel objet** avec un **nouveau numéro** (jamais de réutilisation) | Règle documentée (DV-3, option A, validée le 2026-10-04) | DV-3 ; Audit conservation §7.3 n°4 |
| Calculs d'où une dépense annulée est exclue | « liste à définir » | **Décision à valider** (hors SQL) | DV-4 ; PT-14 |
| Suppression physique | **jamais** (objet numéroté dès sa création) ; la proposition de la première version (suppression permise, Q3/INV-181) est **abandonnée** | Règle documentée | INV-06, INV-193 ; Audit conservation §7.3 n°2 |
| Archivage | **n'existe pas** pour une dépense (l'annulation en tient lieu) | Déduction technique | INV-183 (réservé clients/fournisseurs) |

Conséquences de l'absence de statut : **conservation** — rien ne peut disparaître (garde DELETE, annulation non destructrice) ; **correction** — une erreur courante se corrige par modification ; une erreur d'**année** ou une dépense à ne plus compter se règle par **annulation puis nouvelle saisie** (R11), ce qui consomme un numéro (trou accepté, jamais réutilisé).

### 2.8 Numérotation `DEP-nnnnn-yy` (cohérence avec PT-1)

| Sujet | Conclusion | Nature | Source |
|---|---|---|---|
| Année du numéro | année de **`date_depense`** (et non l'année courante) ; CHECK `substr(numero,11,2) = substr(date_depense,3,2)`, même construction que 004 (`BCD`/`date_creation`, sans condition d'origine) ; `depenses` n'a pas d'`origine` | Règle documentée (année) ; Déduction technique (CHECK) | Modèle §6 ; INV-23 ; 004 |
| Moment d'attribution | **à la création de la dépense** (aucun brouillon) selon PT-1 : réservation `n = max(compteur, high-water) + 1` sous `BEGIN IMMEDIATE`, high-water écrit durablement (échec ⇒ aucun numéro), compteur committé ; la dépense est créée dans une **transaction distincte** | Règle documentée (PT-1 tranché) ; Déduction technique (application à DEP) | Modèle §11.4 ; INV-25, INV-179 ; D-54 |
| Protection contre les doublons | `UNIQUE(numero)` (dernier rempart SQL) ; compteur `numerotation_sequences` (TR-95, TR-96) ; high-water de `machine.db` ; CK-01 et CK-02 à la restauration | Règle documentée | INV-22, INV-25, INV-179 |
| Conservation définitive | aucune suppression (garde DELETE) ; `numero` immuable (TR-01) | Règle documentée | INV-06, INV-23 |
| Après annulation | le numéro reste attaché à la dépense annulée ; **jamais libéré ni réutilisé** | Règle documentée | INV-06 (« annulation et refus ne libèrent jamais un numéro ») |
| Trous | acceptés, jamais récupérés (crash entre réservation et création, annulation + ressaisie) | Règle documentée | INV-22, INV-179, D-54 |
| Priorité | aucun doublon > absence de trous | Règle documentée | D-54 |
| Année 2000 / `yy = 00` | impossible côté séquence (`annee = 0` réservé à CLI/FOU, CHECK de 001) ; borne de service 2001–2099, pas de CHECK | Règle documentée | INV-177 ; 001 |
| `DEP-00000-yy` | accepté par le motif (comme `BCD-00000-yy` en 004) ; la séquence démarre à 1 | Déduction technique | 004 |
| Plafond | 99 999 par année, erreur explicite | Règle documentée | Modèle §6 |
| Exemption de format à l'import | **aucune** (pas d'import de dépenses) | Règle documentée | R18 ; INV-131 |

### 2.9 Import V6

| Sujet | Conclusion | Nature | Source |
|---|---|---|---|
| Blocs `depenses` et `fournisseurs` dans `import-v6.json` | **refusés** (« La V2 ne les fournit pas » ; ouvrir un bloc = nouvelle `contrat_version`) | Règle documentée | Modèle §10.3 ; D-23 ; en-tête de 002 |
| BLOC-IMP sur `depenses` | **retiré** : aucun `origine`, aucun `legacy_id`, aucun `legacy_data`, aucun `legacy_numero` | Règle documentée | D-23 |
| `import_anomalies` pour des dépenses | aucune | Déduction technique | §10.3 |
| Numéros DEP importés | sans objet | Déduction technique | §10.3 |
| Convertisseur V2 → V6 | **hors périmètre** de la tranche | Règle documentée | périmètre du brief |
| Format d'import de dépenses | **aucun n'est proposé** ; les dépenses sont **hors import** jusqu'à une décision documentaire contraire | Règle documentée | D-23 |

Note technique (sans conséquence tant que l'import reste exclu) : introduire plus tard `origine`/`legacy_*` avec leurs CHECK de table obligerait à reconstruire `depenses` (SQLite ne permet pas d'ajouter un CHECK de table par `ALTER`) et exigerait aussi un bloc `fournisseurs` — **Déduction technique**.

### 2.10 Relations et intégrité

| Relation | Cardinalité | FK / ON DELETE / ON UPDATE | Unicité | Index | Modification ou suppression du parent | Nature |
|---|---|---|---|---|---|---|
| Dépense → Fournisseur | facultative (NULL) | `REFERENCES fournisseurs(id) ON DELETE RESTRICT` ; aucun `ON UPDATE` | non | `idx_depenses_fournisseur_id` | données modifiables sans effet ; suppression interdite (FK, INV-183) | Règle documentée |
| Dépense → BC | facultative (NULL) | `REFERENCES bons_commande(id) ON DELETE RESTRICT` ; aucun `ON UPDATE` | non | `idx_depenses_bc_id` | annulation du BC sans effet ; suppression du BC impossible (TR-19) | Règle documentée |
| Dépense → Catégorie | obligatoire | `REFERENCES categories_depenses(id) ON DELETE RESTRICT` ; aucun `ON UPDATE` | non | `idx_depenses_categorie_id` | une catégorie utilisée n'est pas supprimée ; elle est désactivée (`actif`) | Règle documentée (RESTRICT) ; Déduction technique (désactivation) |
| Pièce jointe → racine de stockage | facultative, liée à `piece_jointe_chemin` | **aucune FK** : `machine.db` est une base distincte (référence logique, comme `documents.racine_stockage_id`) ; contrôlée par CK-10 | non | — | racine « non localisable » après restauration sur une autre machine | Déduction technique ; Proposition (extension de CK-10) |
| Dépense → `historique` | aucun lien SQL | polymorphe (`type_entite = 'depense'`, existence : CK-09) ; table `historique` hors tranche | — | — | — | Règle documentée |
| Dépense → URSSAF, client, document | **aucune** | — | — | — | le client d'un BC n'est pas copié sur la dépense | Règle documentée (INV-120, D-34) |

Aucun `CASCADE`, aucun `SET NULL`, aucun `ON UPDATE`. Index supplémentaire sur `numero` : inutile (l'`UNIQUE` en crée un).

### 2.11 Couche de chaque règle (SQL / trigger / service / CK)

| Règle | CHECK / UNIQUE / FK | Trigger | Service | Contrôle | Nature |
|---|---|---|---|---|---|
| Format, unicité du numéro | CHECK GLOB + UNIQUE | — | attribution PT-1 | CK-01, CK-02 | Règle documentée |
| Année du numéro = année de `date_depense` | CHECK `substr` | TR-01 (message INV-23) | — | CK-01 | Règle documentée ; Déduction technique |
| `numero` et année immuables | — | **TR-01** | — | — | Règle documentée (R21) |
| Dates réelles | CHECK GLOB + `date(x) IS x` | — | — | — | Règle documentée |
| Borne 2001–2099 | **jamais un CHECK** | — | oui (création, modification) | — | Règle documentée |
| `montant` D2, > 0 | CHECK | — | saisie à 2 décimales | — | Règle documentée |
| Pièce jointe : les deux ou aucun | CHECK | — | stockage du fichier | CK-10 (étendu) | Règle documentée |
| Existence des parents | FK RESTRICT | — | — | CK-03 | Règle documentée |
| **Suppression interdite** (y compris `INSERT OR REPLACE`) | — | **BEFORE DELETE** (TR-101 proposé) | — | — | Règle documentée (principe) ; Proposition (trigger) |
| Annulation : date et motif ensemble ; motif non vide | CHECK | — | motif demandé | — | Proposition (PT-14) |
| Dépense annulée verrouillée / irréversible | — | TR-102 (certain) | oui | — | Règle documentée (DV-3 option A) ; détail du trigger : Déduction technique |
| 30 jours + confirmation | — | **non** | oui | — | Règle documentée (service) |
| Rattachement à un BC annulé, détachement, changement de BC | — | **non** | selon DV-5, DV-6 | — | Décision à valider |
| Catégorie active | — | non | selon DV-4 | — | Décision à valider |
| Dépense ne réduit pas le CA URSSAF | — | — | calcul URSSAF | — | Règle documentée |
| Exclusion des dépenses annulées des totaux | — | — | requêtes d'analyse | — | Règle documentée (principe) ; liste : Décision à valider |
| Import | **aucun** | — | — | CK-12 sans objet | Règle documentée |

**Aucune règle complexe ni inter-tables n'est convertie en trigger** : 30 jours, BC annulé, catégorie active, cohérence date ↔ BC restent au service. Les deux triggers certains sont **locaux à une ligne** (TR-01 comme pour devis et BC ; garde DELETE comme TR-19 / TR-90 / TR-96).

**Contrôles existants (CK-01, 02, 03, 10, 13, 14) — conclusion explicite : aucun nouveau CK n'est nécessaire.** Déduction technique, subordonnée à DV-2 (si l'annulation devait introduire un total dénormalisé — ce n'est pas proposé).

| Contrôle | Couvre `depenses` ? | Action |
|---|---|---|
| CK-01 numéros uniques et conformes au format V6 | oui (aucune exemption d'origine pour DEP) | citer `depenses` explicitement dans la requête |
| CK-02 séquences ≥ max des numéros V6 | oui ; l'année est lue dans le numéro (`yy`), la séquence est `(DEP, yy)` | idem |
| CK-03 (`foreign_key_check`) | oui, générique | aucune |
| CK-09 existence des `entite_id` polymorphes | oui dès que `historique` existe (hors tranche) | aucune |
| CK-10 racines connues | **libellé limité aux « racines de documents »** | étendre aux pièces jointes de dépenses (précision documentaire, **Proposition**) |
| CK-13 (devis ↔ BC) | non concerné | aucune |
| CK-14 (rattachement multi-devis) | non concerné | si un CK de dépenses était un jour voulu : **CK-16**, jamais CK-14 |

### 2.12 Conservation et suppression

| Principe validé | Application à la dépense | Nature | Source |
|---|---|---|---|
| Un objet à numéro définitif n'est pas supprimé physiquement | une dépense est numérotée dès sa création : **jamais supprimée**, annulée ou non | Règle documentée | INV-06, INV-193 ; Audit conservation D1, D5 |
| Le numéro n'est jamais réutilisé | séquence + high-water + `UNIQUE` ; l'annulation ne libère rien | Règle documentée | INV-06, INV-22, INV-179 |
| L'annulation conserve l'objet | `cancelled_at` / `motif_annulation`, relations (BC, fournisseur, catégorie) et pièce jointe non supprimées | Règle documentée (objet, relations) ; Déduction technique (fichier de la pièce jointe conservé) | INV-193 |
| Suppression seulement des objets non définitifs | aucune dépense n'est « non définitive » | Déduction technique | INV-06 |
| Contournement par `INSERT OR REPLACE` | refusé **par la garde DELETE** avec `recursive_triggers=ON` ; **non protégé** si le réglage est OFF (convention INV-07) — constaté sur prototype (SQLite 3.45.1) : DELETE refusé dans les deux cas, REPLACE refusé seulement avec ON | Déduction technique | INV-07 ; Modèle §1, §4.19 |

La première version (A-4) constatait qu'un REPLACE contournait TR-01 faute de garde DELETE ; **la garde DELETE, désormais exigée par INV-06, supprime ce contournement** (réglage actif).

---

## 3. Modèle de données proposé (esquisse, non destinée à être copiée telle quelle)

| Colonne | Type | Contraintes | Nature | Source |
|---|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | Règle documentée | INV-04 |
| `numero` | TEXT | NOT NULL UNIQUE ; `GLOB 'DEP-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'` | Règle documentée | INV-20, R10 |
| `fournisseur_id` | INTEGER | NULL ; FK → `fournisseurs(id)` ON DELETE RESTRICT | Règle documentée | R3 |
| `bc_id` | INTEGER | NULL ; FK → `bons_commande(id)` ON DELETE RESTRICT | Règle documentée | R2 |
| `date_depense` | TEXT (D) | NOT NULL ; `GLOB` aaaa-mm-jj et `date(x) IS x` ; **aucune borne d'année** | Règle documentée | INV-10, INV-177 |
| `montant` | TEXT (D2) | NOT NULL ; motif D2 ; `<> '0.00'` | Règle documentée | R5 |
| `categorie_id` | INTEGER | NOT NULL ; FK → `categories_depenses(id)` ON DELETE RESTRICT | Règle documentée | R13 |
| `description` | TEXT | NOT NULL ; `<> ''` (le non-vide : convention de nommage des autres tables) | Règle documentée (NOT NULL) ; Déduction technique (`<> ''`) | R15 |
| `piece_jointe_chemin` | TEXT | NULL ; si présent `<> ''` | Règle documentée | R14 |
| `piece_jointe_racine_id` | INTEGER | NULL ; sans FK | Déduction technique | R14 |
| `notes` | TEXT | NULL | Règle documentée | R15 |
| `cancelled_at` | TEXT (TS) | NULL ; GLOB TS UTC millisecondes (classes `[0-9]`, mêmes que 003/004) | **Règle documentée** (DV-2 validée) | R16, R22 |
| `motif_annulation` | TEXT | NULL ; `<> ''` si présent | **Règle documentée** (DV-2 validée) | R22 |
| `created_at`, `updated_at` | TEXT (TS) | NOT NULL ; défaut instant UTC ms ; `GLOB` | Règle documentée | Modèle §2.2 |

CHECK de table : `substr(numero,11,2) = substr(date_depense,3,2)` (Déduction technique) ; `(piece_jointe_chemin IS NULL) = (piece_jointe_racine_id IS NULL)` (Règle documentée) ; `(cancelled_at IS NULL) = (motif_annulation IS NULL)` (Règle documentée, DV-2 validée).

**Absent volontairement** : `statut` ; `origine`, `legacy_id`, `legacy_data`, `legacy_numero` ; `taux_tva`, `montant_tva`, `montant_ttc` ; `date_facture`, `date_echeance`, `date_paiement` ; `frozen_at` ; toute colonne de cache sur `bons_commande` (aucun total des dépenses stocké) ; borne 2001–2099 ; contrôle fournisseur/catégorie/BC annulé/30 jours (service).

Triggers : **TR-01** `tr_01_depenses_numero_immuable` (`BEFORE UPDATE OF numero, date_depense`, `WHEN NEW.numero IS NOT OLD.numero OR substr(NEW.date_depense,3,2) IS NOT substr(OLD.date_depense,3,2)`, message `INV-23: …`) — formulation prototypée dans la première version, toujours valable ; **TR-101** (numéro proposé, le premier libre après TR-100) `BEFORE DELETE ON depenses` : `RAISE(ABORT, 'INV-06: …')` ; **TR-102** (certain, DV-3 option A) : `BEFORE UPDATE` refusé lorsque `OLD.cancelled_at IS NOT NULL` (aucune modification métier, aucune réactivation ; l'annulation elle-même est un `UPDATE` d'une ligne non annulée). *Point de détail non décidé* : le sort d'un éventuel `updated_at` isolé sur une dépense annulée (liste blanche ou refus total) — à confirmer avant d'écrire le trigger.

Index : `idx_depenses_bc_id`, `idx_depenses_fournisseur_id`, `idx_depenses_categorie_id`, `idx_depenses_date_depense` ; hors tranche : `historique`, `documents`, factures, règlements, garanties, PV, planning, URSSAF.

---

## 4. Structure proposée de `005_depenses.sql` (à n'écrire qu'après validation)

`PRAGMA user_version` (rang 5) posé par le runner **dans la transaction de la migration, avant son `COMMIT`** (conventions §5) ; ni `BEGIN/COMMIT` ni `PRAGMA` dans le fichier ; aucune ligne insérée ; en-tête citant le **modèle V3.13 validé**. Ordre : (1) en-tête (références Modèle §2, §3.5, §4.12, §6, §8, §9, §10.3, §17.1 ; INV-04, 05, 06, 10, 11, 14, 20 à 23, 100, 103, 177, 188, 193 ; D-12, D-18, D-23, D-31, D-38, D-39, D-50 ; PT-1, PT-14) ; (2) table `depenses` STRICT ; (3) TR-01, TR-101 et TR-102 ; (4) quatre index. **Fichier `005_depenses.sql`, tranche métier de rang 5 (DV-1 tranchée).**

---

## 5. Structure proposée de `test_005_depenses.py`

Test à numéroter dans le Modèle §13.3 (T-30 est pris par la numérotation en V3.13, T-43 est le dernier : attribuer le prochain numéro libre). Connexion : `foreign_keys=ON`, `recursive_triggers=ON` posés explicitement, chaîne **001 → 005** appliquée (rangs 1 à 5 ; le test pose `user_version = 5`, qui est ici à la fois le rang et le numéro) ; noms `test_INV_xx_…`. Les tests 003/004 vérifiant l'absence de `depenses` ne sont pas touchés. Les règles de **service** (30 jours, confirmation, borne d'année, rattachement à un BC annulé, catégorie active) se testent côté Rust : **hors de cette tranche** ; ici, uniquement les **faits SQL** (ce que la base accepte et refuse).

| Groupe | Contenu | Tests (estim.) |
|---|---|---|
| Structure | `PRAGMA recursive_triggers` actif ; 1 table `STRICT`, colonnes exactes (types, NOT NULL, défauts) ; aucune ligne ; 2 ou 3 triggers (noms) ; 4 index (noms, colonnes, plan de requête qui les utilise) ; `foreign_key_check` vide ; **absence** de `statut`, `origine`, `legacy_*`, TVA/TTC, `date_facture`, `date_echeance`, `frozen_at` ; tables 001–004 inchangées | 9 |
| Création | dépense minimale ; globale ; avec fournisseur ; avec BC `en_cours` ; avec pièce jointe ; défauts `created_at`/`updated_at` ; annulation absente à la création | 7 |
| Numérotation | format `GLOB` explicite ; année = année de `date_depense` (et non l'année courante) ; séquence `DEP` par année ; plafond 99 999 ; `annee = 0` refusé pour `DEP` ; TR-95/TR-96 inchangés ; **numéro non réutilisé après annulation** ; **trou toléré** par la base ; `UNIQUE(numero)` ; deux attributions → deux numéros | 10 |
| TR-01 | `numero` immuable ; changement d'année refusé (message `INV-23`) ; changement de jour dans la même année accepté ; chaque opérande du `WHEN` isolé ; autres colonnes modifiables | 8 |
| Garde DELETE | `DELETE` refusé (dépense active, annulée, globale, rattachée) ; message `INV-06` ; `INSERT OR REPLACE` par `id` et par `numero` refusés avec `recursive_triggers=ON` ; témoin documenté avec OFF ; aucune ligne perdue | 7 |
| Annulation | `cancelled_at`/`motif_annulation` ensemble ou aucun ; motif vide refusé ; format TS ; une dépense annulée conserve `numero`, `bc_id`, `fournisseur_id`, `categorie_id` ; modification et réactivation refusées (DV-3 option A) | 7 |
| Dates | calendrier exhaustif (bissextiles, 30/31 jours) ; `date(x) IS x` ; années 1900, 2000, 2100 acceptées par le SQL (règle de service) | 5 |
| Montants HT / précision | D2 valides (`0.01`, `1250.50`, valeur maximale raisonnable) ; invalides (`0.00`, `1.5`, `-1.00`, `1a.00`, `1.2.50`, `01.00`, `1e2`, espaces, `""`, NULL, float) ; **texte conservé octet pour octet** (`0.10`, `0.30`) ; somme en centimes entiers exacte (`0.10 + 0.20 = 0.30`) ; aucune colonne TVA | 8 |
| Textes et pièce jointe | `description` vide/NULL ; chemin vide ; chemin sans racine et inversement ; les deux ou aucun | 5 |
| FK | `fournisseur_id`, `bc_id`, `categorie_id` inexistants refusés ; suppression d'un fournisseur / d'une catégorie / d'un BC référencés refusée (RESTRICT, TR-19) ; aucun `ON UPDATE` | 6 |
| Fournisseur | NULL accepté ; tout fournisseur existant accepté ; **aucun test ne lit ni n'asserte `fournisseurs.statut`** ; modification des données du fournisseur sans effet sur la dépense | 4 |
| BC (faits SQL) | `en_cours` ; `en_cours` 100 % depuis 20 et 45 jours ; `termine` ; **`annule` : création acceptée et lien conservé** (règle documentée) ; annulation du BC (UPDATE légitime) sans effet sur ses dépenses ; la création n'écrit rien dans `bons_commande` ; changement/détachement de `bc_id` acceptés par le SQL (la règle est au service) | 8 |
| Dépense globale | création ; rattachement ultérieur et détachement acceptés par le SQL (règle de service : DV-5) | 3 |
| Modification | colonnes modifiables hors `numero`/année ; `updated_at` (valeur fournie par le service) ; TR-01 reste actif | 3 |
| Import | **aucun test de bloc** (blocs refusés) : seulement l'absence de `origine`/`legacy_*` et d'`import_anomalies` de dépense | 2 |
| Identifiants décalés | clients, fournisseurs, catégories, BC, dépenses avec des `id` tous différents pour détecter une confusion de colonnes | 3 |
| Contrôles de restauration | requêtes CK-01/02/03 (et CK-10 étendu) : doublon de numéro, séquence en retard, FK orpheline, racine inconnue | 5 |
| **Total estimé** | | **≈ 100** |

**Campagne de mutation (conventions §7.1), au niveau de rigueur de 004** — objectif : **0 survivant non qualifié**. Mutants génériques : suppression ou inversion de chaque CHECK ; chaque jeton des motifs `GLOB` (positions, classes, `NOT GLOB`) ; `IN` ↔ `NOT IN` ; chaque `NOT NULL` ; chaque `UNIQUE` ; chaque FK (`RESTRICT` → `CASCADE`/`SET NULL`/`NO ACTION`/absente) ; `IS`/`IS NOT` ↔ `=`/`<>` (pièges `NULL`) ; `OLD`/`NEW` ; `date(x) IS x`. Mutants propres à 005 : confusion d'identifiants entre colonnes ; chaque opérande du `WHEN` de TR-01 ; `UPDATE OF` incomplet ; offsets de `substr` du numéro (11,2) et de la date (3,2) ; conjoncts D2 (jeu de caractères, double point, zéros de tête, `0.00`, signe) ; « les deux ou aucun » de la pièce jointe et de l'annulation ; **suppression du trigger DELETE**, `BEFORE` ↔ `AFTER`, message ; index supprimé ou colonne modifiée (plan de requête) ; **trigger absent + `recursive_triggers=OFF`** (REPLACE) ; mutation de l'ordre 001 → 00x. Survivants attendus à qualifier (mêmes classes qu'en 004) : `GLOB` de date redondant avec `date(x) IS x` ; clause « année » de TR-01 redondante avec le CHECK `substr` quand `numero` est inchangé (tuée seulement par le message `INV-23`) ; `BEFORE` ↔ `AFTER` avec `RAISE(ABORT)` (équivalent) ; disjonctions laissant passer `NULL`.

---

## 6. Points soulevés par la revue (corrections apportées à la première version)

| # | Constat | Nature | Traitement |
|---|---|---|---|
| C-A | Q2 « dépense sur BC annulé : aucune règle » | caduque | tranchée dans son principe (R17) ; reste DV-5/6/7 |
| C-B | « fournisseur archivé / actif » (R6, R7, §3.1) | caduque | supprimée (E-12, INV-183) |
| C-C | « aucune annulation, suppression permise » (Q3, INV-181 proposé, §2.1) | caduque | annulation (PT-14) ; suppression interdite ; garde DELETE |
| C-D | « A-4 : REPLACE contourne TR-01 » | traité | garde DELETE ; test documenté |
| C-E | « annulation d'un BC avec solde actif interdite (D-05) » | caduque | D-05 remplacée (D-46, E-15) |
| C-F | Numéros INV-179 à INV-182 proposés pour Dépenses | déjà attribués | nouvelles règles de Dépenses : **INV-197 et suivants** |
| C-G | « CK-14 de cohérence des dépenses » | collision | CK-14 est le rattachement multi-devis ; éventuel CK de dépenses : CK-16 ; non proposé |
| C-H | « Base `548f61f`, 9 décisions » | périmé | base actualisée ; DV-1 à DV-10 |
| C-I | « Dépense globale entre dans les analyses » | non documenté | retiré |
| C-J | Catégorie inactive, sens de `date_depense` : présentés comme propositions de règle | silence | Décisions à valider (DV-4, DV-8) |
| C-K | T-30 réservé à la tranche dans la première version | collision | T-30 = numérotation en V3.13 ; numéro à réattribuer |
| C-L | Migration 002 contient encore `fournisseurs.statut` | contradiction migration/documents | traitée par la corrective M-A (`005a`, PT-3), hors 005 ; 005 n'y touche pas (§2.3) |
| C-M | DV-1 de la version précédente : recommandation « (b) M-A et M-B d'abord, Dépenses ensuite », mention d'une migration `005_corrections_v313` et d'un « numéro de fichier de 005 dépendant de DV-1 » | **contredit** la décision V-1 à V-5 (2026-10-04) | corrigé : 005 = Dépenses (rang 5) ; M-A/M-B = `005a`/`005b` (rangs 6 et 7), avant 006 ; aucune tranche renumérotée |
| C-N | Risque annoncé : « reconstruction de `fournisseurs` avec FK entrante `RESTRICT` » et « montage le plus fragile de SQLite » | **surévalué / inexact** | `fournisseurs` ne se reconstruit pas (`DROP INDEX` puis `DROP COLUMN`) ; le vrai cas est la reconstruction de `bons_commande` par M-B, référencée par `depenses.bc_id` : couverte par le protocole de reconstruction (conventions §5) |
| C-O | DV-2 « Proposition (PT-14) » et DV-3 « Décision à valider » dans les tableaux §2, §3, §5, §8 | **périmé** | DV-2 et DV-3 (option A) validées le 2026-10-04 ; natures mises à jour, TR-102 certain |

Statuts documentaires périmés à corriger hors de ce cadrage (annexe B) : en-têtes de `docs/README.md` et d'`invariants.md` (« V3.12 non validée »), `modèle-métier` (renvois V3.10/V3.11), `conventions-techniques` §4/§5/§7 (001–003 seulement), Modèle §4.12 (« sera déterminé lors de la conception de la tranche Dépenses »), ligne vide du tableau §17.1 avant 004.

---

## 7. Décisions à valider avant l'écriture de `005_depenses.sql`

Les décisions **DV-4 à DV-10** ci-dessous sont de Nature **Décision à valider** (DV-1, DV-2 et DV-3 sont tranchées : §7 bis). Les recommandations sont des **Propositions**, non des règles.

| # | Décision | Options | Recommandation (proposition) | Effet sur le DDL / le test |
|---|---|---|---|---|
| **DV-4** | **Effets de l'annulation** : liste des totaux et calculs d'où une dépense annulée est exclue (marge par BC, marge globale, autres) ; **catégorie inactive** sélectionnable ou non pour une nouvelle dépense | liste à fournir ; oui/non | à définir avec PT-14 ; catégorie inactive non sélectionnable **seulement si le métier le confirme** (rien ne le dit) | Non (service, analyses) |
| **DV-5** | **Champs corrigeables d'une dépense active** : changer ou retirer le fournisseur ; changer de BC, **rattacher** une dépense globale, **détacher** ; changer de catégorie ; remplacer la pièce jointe ; confirmer que la modification d'une dépense liée à un BC annulé n'est soumise à aucune restriction | tout permis / certains champs figés | à décider ; si permis, toute **nouvelle** cible est soumise aux règles d'un nouveau rattachement | Non |
| **DV-6** | **Rattacher une dépense existante à un BC déjà annulé** (D5 vise la création) | permis / refusé | permis par cohérence avec D5, **à confirmer** | Non |
| **DV-7** | **30 jours sur un BC annulé** dont `date_100_facture` est non NULL (annulation avec solde actif, E-15) ; sort de `date_100_facture` à l'annulation | règle INV-103 inchangée / pas de confirmation sur BC annulé | à décider (Audit conservation §7.3 n°5) | Non |
| **DV-8** | **Sens de `date_depense`** (date de la facture fournisseur ou du paiement) ; absence de `date_facture` ; absence de contrôle de cohérence avec les dates du BC | libellé à fixer au Métier §18 | à fixer (« montant réellement payé » oriente vers la date effective) | Non |
| **DV-9** | **Limites connues** à confirmer : pas de montant négatif (avoir fournisseur, remboursement reçu non représentables) ; pas de TVA ; gel (`frozen_at`) sans effet sur les dépenses | confirmer | confirmer | Non |
| **DV-10** | **Historique** : événements à journaliser pour une dépense (l'annulation l'est ; création, modification ?) et **pièce jointe** (format du chemin, sort du fichier à l'annulation) | PT-15 / service | rattacher à PT-15 ; chemin relatif contrôlé au service + CK-10 étendu | Non |

### 7 bis. Décisions tranchées le 2026-10-04 (DV-1, DV-2, DV-3)

**DV-1 — Versionnement et place de 005 (V-1 à V-5, D-55)** — *remplace entièrement la formulation précédente (options (a)/(b), recommandation « M-A et M-B d'abord », numéro de fichier de 005 « dépendant de DV-1 »), devenue caduque.*

| Point | Décision | Nature |
|---|---|---|
| Ordre métier réservé | 001 Initial → 002 Fournisseurs → 003 Devis → 004 Bons de commande → **005 Dépenses** → 006 Facturation → 007 Règlements → 008 Garanties → 009 PV → 010 Planification (V-1) | Règle documentée (validée) |
| Nature de 005 | **tranche métier Dépenses**, fichier `005_depenses.sql`, **rang 5** | Règle documentée (validée) |
| M-A et M-B | **migrations correctives** `005a_corrections_v313.sql` (rang 6) et `005b_bc_multi_devis.sql` (rang 7), **après 005 et avant 006** ; elles ne sont pas des tranches, ne consomment aucun numéro de tranche et **ne renumérotent aucune tranche** ; 006 reste Facturation (rang 8) (V-2, V-4) | Règle documentée (validée) ; **contenu** de M-A/M-B : toujours en proposition |
| `user_version` | = rang dans la chaîne ordonnée, pas numéro de fichier ; après 005 : `user_version = 5` (V-3) | Règle documentée (validée) |
| Base déjà à `user_version = 4` | applique 005 (→ 5), puis M-A (→ 6) et M-B (→ 7) lorsqu'elles seront livrées, puis 006 (→ 8) | Déduction technique |
| Runner et protocole de reconstruction | **chantier technique distinct** de 005 (V-5) ; 005 ne reconstruit aucune table | Règle documentée (validée) |
| Conséquence sur `fournisseurs` | pas de reconstruction : `DROP INDEX idx_fournisseurs_statut` puis `DROP COLUMN statut` (M-A) | Déduction technique (vérifiée) |
| Conséquence sur `depenses` | M-B reconstruira `bons_commande`, qui sera référencée par `depenses.bc_id` : le protocole (conventions §5 : noms et `id` conservés, triggers dépendants recréés, `foreign_key_check`) le couvre ; le test de M-B devra contenir des dépenses | Déduction technique |

**DV-2 — Mécanisme d'annulation (validée).** `cancelled_at` + `motif_annulation`, **sans colonne `statut`** ; timestamp UTC en millisecondes (TEXT) ; motif obligatoire et non vide ; cohérence des deux colonnes (toutes deux NULL ou toutes deux renseignées). Effet : 2 colonnes, CHECK de cohérence, CHECK de format du timestamp.

**DV-3 — Dépense annulée (option A validée).** Annulation **irréversible**, **aucune réactivation**, **aucune modification métier** d'une dépense annulée. Une nouvelle dépense est un **nouvel objet** avec un **nouveau numéro** (INV-179 : un numéro n'est jamais attribué deux fois). Effet : TR-102 est certain ; la table et les tests le reflètent (§3, §5).

Ce qui reste **non décidé** dans ce périmètre : la liste des calculs d'où une dépense annulée est exclue (DV-4) ; le détail de TR-102 pour un éventuel `updated_at` isolé (point de conception, à confirmer).

**Non soumis à décision** (déjà documentés) : import exclu (D-23, §10.3) ; suppression interdite (INV-06) ; BC annulé accepte la création de dépenses (D5) ; fournisseur sans statut (E-12) ; format et année du numéro ; mécanisme PT-1. **Réouverture éventuelle** de l'un d'eux : à signaler explicitement, car elle modifierait le DDL.

**Ordre conseillé** : DV-5 à DV-7 conditionnent INV-197 et suivants et les tests de service ; DV-4, DV-8 à DV-10 sont sans effet SQL. DV-1, DV-2 et DV-3, qui conditionnaient le DDL, les triggers et les tests, sont tranchées (§7 bis).

---

## 8. Tableau de synthèse

| Sujet | Conclusion | Nature | Source | Action |
|---|---|---|---|---|
| Création sur BC annulé | autorisée | Règle documentée | Audit conservation D5 ; INV-188 | R17 ; test SQL positif |
| Dépense existante quand le BC est annulé | reste rattachée, aucun effet | Règle documentée | INV-188, INV-193 | test |
| Rattacher une dépense existante à un BC annulé | non documenté | Décision à valider | Audit §7.3 | DV-6 |
| Détacher / changer de BC | non documenté | Décision à valider | — | DV-5 |
| Modifier une dépense liée à un BC annulé | aucune restriction documentée | Déduction technique | INV-173 | DV-5 |
| 30 jours sur BC annulé (`date_100_facture` non NULL) | à préciser | Décision à valider | Audit §7.3 n°5 | DV-7 |
| BC `en_cours` / `termine` | règle D-31 sur `date_100_facture` | Règle documentée / Déduction technique | D-31, 004 | §2.2 |
| BC « gelé » | sans effet ; gel supprimé en V3.13 | Déduction technique | Métier ; PT-8 | DV-9 |
| Fournisseur facultatif, par identifiant | oui | Règle documentée | CDC §28 ; INV-100 | — |
| Fournisseur actif / archivé | n'existe plus | Règle documentée | E-12 ; INV-183 | règle retirée |
| Changer le fournisseur d'une dépense | non documenté | Décision à valider | — | DV-5 |
| Suppression du fournisseur | interdite ; FK RESTRICT ; garde PT-4 hors 005 | Règle documentée / Proposition | INV-183 | M-A |
| `fournisseurs.statut` dans 002 | contradiction, traitée par la corrective M-A (`005a`) | Déduction technique | 002 ; PT-3 | aucune dans 005 |
| Dépense globale autorisée | oui | Règle documentée | CDC §28 | — |
| Dépense globale : règles propres | aucune documentée | Règle documentée | INV-103 | — |
| `date_depense` | date réelle, année du numéro, modifiable même année | Règle documentée | Modèle §6 | — |
| Sens de `date_depense` ; date de facture | non tranché ; pas de colonne | Décision à valider | Métier §18 | DV-8 |
| Date de saisie | `created_at` | Règle documentée | Modèle §2.2 | — |
| Échéance | exclue | Règle documentée | Métier §18 | — |
| Date d'annulation | `cancelled_at` | Règle documentée (DV-2 validée) | DV-2 ; PT-14 | aucune |
| Montant | un seul D2, sans TVA, > 0 | Règle documentée | Modèle §4.12 ; INV-14 | CHECK |
| Précision, arrondi, somme | exacts, sans calcul à l'écriture | Déduction technique | INV-11 | tests |
| Avoir fournisseur / négatif | non représentable | Règle documentée | INV-14 | DV-9 |
| Statut | aucun | Déduction technique | INV-100 | — |
| Annulation (principe) | validée | Règle documentée | E-19 ; INV-193 | — |
| Annulation (colonnes) | `cancelled_at` + `motif_annulation`, sans `statut` | Règle documentée (DV-2 validée) | DV-2 ; PT-14 | aucune |
| Dépense annulée modifiable / réactivable | non modifiable, non réactivable (irréversible) | Règle documentée (DV-3 option A validée) | DV-3 ; Audit §7.3 n°4 | aucune (TR-102) |
| Exclusions de totaux | liste à définir | Décision à valider | PT-14 | DV-4 |
| Suppression physique | interdite | Règle documentée | INV-06 ; INV-193 | garde DELETE |
| Garde DELETE (trigger) | TR-101 | Proposition | Audit §7.3 n°1 | écrire après validation |
| Numérotation : année | `date_depense` | Règle documentée | Modèle §6 | — |
| Numérotation : attribution | à la création, PT-1 | Règle documentée / Déduction technique | §11.4 | — |
| Numérotation : doublons, trous, réutilisation | aucun doublon > trou ; jamais réutilisé | Règle documentée | INV-22, INV-179 | — |
| Import | exclu, aucun `origine` ni `legacy_*` | Règle documentée | §10.3 ; D-23 | — |
| Relations / ON DELETE | RESTRICT partout, aucun ON UPDATE | Règle documentée | INV-05 | — |
| Index | 4 | Règle documentée | Modèle §9 | — |
| CK-01, 02, 03 | couvrent `depenses` | Déduction technique | §14 | citer `depenses` |
| CK-10 | à étendre aux pièces jointes de dépenses | Proposition | §14 | doc |
| CK-13, CK-14 | non concernés ; aucun nouveau CK | Déduction technique | §14 | — |
| Triggers inter-tables | aucun | Déduction technique | D-36, INV-103 | — |
| Ordre et rang des migrations | `005_depenses` = rang 5 ; `005a`/`005b` rangs 6 et 7 ; `006_facturation` = rang 8 | Règle documentée (V-1 à V-5, D-55) | Modèle §17.1 ; conventions §5 | aucune |
| Tests / mutation | ≈ 100 tests, campagne 004 | Proposition | conventions §7.1 | après validation |

---

## Annexe A — Recherche documentaire

Termes interrogés : *dépense, DEP-, fournisseur, TVA, franchise, supprim\*, annul\*, 30 jours, date_100_facture, clôtur\*, import, legacy, origine, archiv\*, restauration, CK-, TR-, INV-100, INV-103, INV-177, INV-188, INV-193, D5, E-12, E-15, E-19, PT-14*. Sources : CDC §2, §15, §17, §28, §29 (+ amendements E-15, E-19) ; Métier §2.1, §2.2, §2.4, §4.2, §17, §18, §19 ; Modèle §2.2, §2.3, §3.5, §4.3, §4.4, §4.12, §6, §8, §9, §10.3, §11.4, §13.1 (C-21, C-22), §14, §15 (D-12, D-18, D-23, D-31, D-38, D-39, D-43, D-46, D-50, D-54), §17.1, §19 (PT-1, PT-3, PT-4, PT-8, PT-14) ; INV-04 à 07, 10, 11, 14, 20 à 25, 43 à 45, 100, 103, 106, 110, 120, 173, 177, 183, 188, 193 ; Audit conservation D1 à D6, §7 ; migrations 001 (`categories_depenses`, `numerotation_sequences` — `DEP` déjà dans la liste fermée), 002 (en-tête, `statut`), 004 (`date_100_facture`, statuts, TR-12/13/14/17/19, TR-96) ; tests 001–004 (aucun test de dépense).

## Annexe B — Impact documentaire (à reporter ; **rien n'a été modifié dans `docs/**`**)

| Fichier | Correction nécessaire |
|---|---|
| Modèle SQLite → **V3.13 validé** | §4.12 : retirer « sera déterminé lors de la conception de la tranche Dépenses », consigner DV-1 à DV-10 (DV-1 à DV-3 tranchées le 2026-10-04) ; §4.19 : précisions de DDL de la migration Dépenses ; §8 : TR-101 (et TR-102) ; §13.3 : numéro de test libre ; §14 : CK-01, 02, 03, 10 ; §15 : décisions ; §17.1 : ligne Dépenses (rang 5) — l'ordre et la chaîne sont déjà portés par la copie de travail V3.13 (D-55) ; la ligne vide du tableau est corrigée dans cette copie |
| `invariants.md` | INV-197 et suivants pour les règles nouvelles de Dépenses (DV-3, DV-5 à DV-7) ; journal ; statut de la version |
| `modèle-métier-V6.md` | §18 : sens de `date_depense` (DV-8), règles de rattachement (DV-5 à DV-7) ; §17 : définition de X ; en-tête |
| `conventions-techniques-v6.md` | §5 : chaîne ordonnée et protocole déjà portés par la copie de travail 0.6 ; §7 : ajouter `test_004` (liste restée à 001–003) et, plus tard, `test_005_depenses.py` ; §4 : ajouter la migration Dépenses à sa livraison |
| `docs/README.md` | statut de la V3.13 |
| `cdc-fonctionnel-architectural-v6.md` | §15 / §28 : formulation « depuis X jours » ; BC annulé, seulement si DV-6/DV-7 le modifient |

---

**Risque** : si DV-4 à DV-10 sont tranchés après l'écriture du SQL, seuls des tests de service et des invariants changent (aucune de ces décisions ne modifie la table) ; en revanche le détail de TR-102 (sort de `updated_at` sur une dépense annulée) doit être confirmé avant l'écriture du trigger. Le runner et le protocole de reconstruction n'existent pas encore : 005 ne les utilise pas (aucune reconstruction), mais M-B reconstruira `bons_commande`, désormais référencée par `depenses.bc_id`.
**Micro-amélioration** : trancher d'abord DV-5 à DV-7 (rattachement, BC annulé, 30 jours) — ce sont les seules décisions restantes qui créent des invariants INV-197 et suivants.
