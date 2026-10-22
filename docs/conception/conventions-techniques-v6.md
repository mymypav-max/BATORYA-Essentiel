# BATORYA Essentiel V6 — Conventions techniques et de code

**Version : 0.4 — document évolutif**  
**Périmètre : conventions techniques de développement V6**

## 1. Objet

Ce document définit les conventions techniques applicables au code de BATORYA Essentiel V6.

Il complète les documents de référence fonctionnels et architecturaux. Il ne remplace ni le CDC, ni le modèle de données SQLite, ni le registre des invariants, ni le modèle métier.

Son objectif est de maintenir une arborescence cohérente et prévisible pendant l’implémentation.

Le document est volontairement évolutif : les conventions seront complétées au fur et à mesure de l’avancement réel du développement, sans créer prématurément une architecture non nécessaire.

## 2. Documents de référence

Avant toute implémentation ou modification structurelle, les références suivantes doivent être considérées dans cet ordre de priorité métier et architectural (sous réserve de la règle de précédence ci-dessous) :

1. `docs/specifications/cdc-fonctionnel-architectural-v6.md`
2. `docs/conception/modèle-données-sqlite-v6-v3.12.md`
3. `docs/conception/invariants.md`
4. `docs/conception/modèle-métier-V6.md`
5. `docs/décisions/cdc-errata-v6.md` pour la traçabilité historique uniquement.

**Règle de précédence** (décision du propriétaire du 2026-10-22, rédaction en relecture, non validée officiellement) : lorsqu'un document contredit les invariants (`invariants.md`) ou le modèle de données SQLite courant (V3.14, en relecture ; la V3.12 reste la dernière version validée), ce sont les invariants et/ou le modèle qui prévalent. Le CDC, le modèle métier et les autres documents non encore actualisés ne prévalent pas du seul fait qu'ils conservent une formulation antérieure ; la contradiction est corrigée dans le document concerné ou enregistrée par un erratum (`docs/décisions/cdc-errata-v6.md`). Cette règle ne classe pas les autres documents entre eux.

Une convention de code ne peut pas contredire ces documents.

## 3. Règle générale de création des fichiers

Un nouveau fichier ne doit pas être créé à un emplacement arbitraire.

Pour chaque nouveau fichier, son nom et son emplacement doivent être cohérents avec :

- sa responsabilité ;
- la couche à laquelle il appartient ;
- la convention déjà établie pour le module concerné ;
- les conventions présentes dans ce document.

Si une nouvelle catégorie de fichier ou une nouvelle branche d’arborescence devient nécessaire, elle est d’abord définie dans ce document avant de devenir une convention permanente.

Les fichiers temporaires de travail ne doivent pas être ajoutés au dépôt sous un nom ambigu ou générique.

### Dossier de suivi de session

Le dossier `docs/suivi/` contient le journal de continuité des sessions de travail (`journal-continuite.md`).
Il n'est pas un document de référence : il ne fait autorité ni sur le CDC, ni sur le modèle de données SQLite, ni sur les invariants, ni sur le modèle métier, ni sur les errata, et il ne contient aucune décision.
Il enregistre l'état du dépôt, les actions réalisées, les commandes exécutées et leur résultat.
Les noms de fichiers y sont en minuscules, séparés par des tirets.

## 4. Arborescence technique actuelle

L’arborescence technique actuellement validée est volontairement minimale :

```text
src-tauri/
├── migrations/
│   ├── machine/
│   │   └── 001_initial.sql
│   └── metier/
│       ├── 001_initial.sql
│       ├── 002_fournisseurs.sql
│       └── 003_devis.sql
│
└── tests/
    ├── machine/
    │   └── test_premier_demarrage.py
    └── metier/
        ├── test_001_initial.py
        ├── test_002_fournisseurs.py
        └── test_003_devis.py
```

Cette arborescence sera complétée lorsque les premières implémentations Rust, SQLite métier et interfaces applicatives seront réellement introduites.

Aucune arborescence supplémentaire n’est imposée à ce stade sans besoin concret.

## 5. Migrations SQLite

Les migrations SQLite sont versionnées et séquentielles.

La migration initiale de `machine.db` est :

```text
src-tauri/migrations/machine/001_initial.sql
```

Règles :

- le numéro de migration est séquentiel ;
- le nom d’une migration déjà créée ne doit jamais être changé pour convenance ;
- une migration déjà appliquée n’est pas réécrite pour modifier rétroactivement le schéma ;
- une évolution de schéma donne lieu à une nouvelle migration ;
- les migrations ne contiennent pas de logique métier applicative ;
- le runner de migrations est responsable de la transaction et de la mise à jour de `PRAGMA user_version` selon le modèle SQLite ;
- une migration ne doit pas introduire de trigger ou de contrainte qui contredit les invariants ou les responsabilités explicitement attribuées aux services.

### Migrations de la base métier

La base métier a ses propres migrations, séparées de celles de `machine.db` :

```text
src-tauri/migrations/metier/001_initial.sql
src-tauri/migrations/metier/002_fournisseurs.sql
src-tauri/migrations/metier/003_devis.sql
```

Règles :

- une migration de tranche correspond à une tranche du schéma définie dans le suivi des migrations du modèle de données SQLite ; elle contient les tables de la tranche, avec leurs triggers et leurs index ;
- la première migration métier s’appelle `001_initial.sql`. Il existe deux catégories de migrations métier, distinguées par leur nom (décision V-2, confirmée par le propriétaire le 2026-10-18) :
  - une **tranche métier** : `NNN_<objet>.sql` (numéro séquentiel, objet en minuscules sans accent) ;
  - une **migration corrective** : `NNNx_<objet>.sql` (trois chiffres suivis d’**une lettre minuscule**, objet en minuscules sans accent) ; elle corrige ou fait évoluer le schéma déjà livré sans être une tranche métier, et ne consomme aucun numéro de tranche. Le préfixe `NNN` est celui de la dernière tranche exécutée avant elle ; la lettre ordonne les correctives rattachées à la même tranche (`005a` avant `005b`, `009a` avant `009b`, `009b` avant `009c`) ;
  - aucune autre catégorie de nom n’existe ;
- le modèle de données SQLite passe à la version suivante et est mis à jour **avant** la création ou la modification d’une migration ; l’en-tête d’une migration cite la version courante du modèle, qu’elle soit validée ou en relecture ;
- une migration n’insère aucune ligne : listes de référence, catalogue par défaut et singletons relèvent du jeu de données d’installation ou du service d’initialisation (l’emplacement du jeu de données sera défini dans ce document lorsqu’il sera introduit) ;
- noms SQL : triggers `tr_<NN>_<table>_<règle>` où `NN` est le numéro `TR-NN` du modèle ; index `idx_<table>_<colonnes>` ; les contraintes `UNIQUE` de colonnes restent déclarées dans la table ;
- chaque migration métier est livrée avec son test (section 7).

## 6. machine.db

`machine.db` est distincte de la base métier.

Elle ne contient aucune donnée commerciale ou métier.

Les responsabilités actuellement définies comprennent notamment :

- compte local ;
- licence ;
- état des services BATORYA ;
- racines de stockage ;
- préférences de sauvegarde ;
- état Gmail ;
- high-water de numérotation.

Les secrets ne sont pas stockés dans `machine.db` lorsqu’ils doivent résider dans le coffre sécurisé du système d’exploitation.

L’initialisation des singletons de `machine.db` relève du service d’initialisation au premier démarrage. La migration `001_initial.sql` ne crée aucune ligne de singleton.

## 7. Tests

Les tests sont regroupés par responsabilité.

Le test actuellement défini pour le premier démarrage de `machine.db` est :

```text
src-tauri/tests/machine/test_premier_demarrage.py
```

Les tests des migrations métier sont :

```text
src-tauri/tests/metier/test_001_initial.py
src-tauri/tests/metier/test_002_fournisseurs.py
src-tauri/tests/metier/test_003_devis.py
```

Pour les migrations métier : un fichier de test par migration, dans `src-tauri/tests/metier/`, nommé `test_<nom de la migration>.py` ; les méthodes de test portent le nom de l’invariant vérifié (`test_INV_xx_…`), conformément au registre des invariants.

Les connexions de test appliquent les mêmes réglages que les connexions applicatives (« Réglages de connexion SQLite », §9), dont `PRAGMA recursive_triggers=ON` posé **explicitement**. Chaque fichier de test de migration contient un contrôle que ce réglage est effectivement actif et, lorsque la migration porte des triggers de protection applicables, un test ciblé vérifiant qu'`INSERT OR REPLACE` ne les contourne pas.

Un test doit avoir un nom explicite permettant d’identifier directement le comportement vérifié.

Les tests ne doivent pas devenir une seconde spécification contradictoire : lorsqu’un comportement est modifié volontairement, le test correspondant doit être mis en cohérence avec la décision et les documents de référence.

### 7.1 Campagne de mutation des migrations métier

Chaque nouvelle tranche de migration métier doit être accompagnée de sa campagne de mutation sur la migration et son fichier de test.

L'objectif est de terminer la campagne avec **0 survivant non qualifié**. Un survivant peut uniquement être conservé lorsqu'il est démontré et documenté comme mutant équivalent ou inatteignable ; il ne doit pas être laissé sans qualification.

Cette campagne complète les tests fonctionnels classiques : un résultat « tous les tests passent » ne suffit pas à considérer la couverture de la tranche comme sécurisée.

Lorsqu'une correction est apportée à une migration déjà existante, les tests de cette tranche doivent être rejoués et la campagne de mutation concernée doit être réévaluée avant de poursuivre sur une nouvelle tranche.

Lorsque les tests d'une tranche déjà intégrée sont modifiés sans que sa migration change (par exemple le renforcement des tests 001–003 par `recursive_triggers=ON`), une **nouvelle campagne de mutation** (0 survivant non qualifié) doit être exécutée **avant l'intégration** des tests modifiés.

## 8. Séparation des responsabilités

Principe général V6 :

```text
UI
 ↓
Services applicatifs
 ↓
Règles métier / domaine
 ↓
Repositories
 ↓
SQLite
```

Les détails de cette séparation seront précisés lorsque les premières couches applicatives seront implémentées.

Principe déjà fixé :

- l’UI ne doit pas porter seule des règles métier critiques ;
- l’UI ne doit pas accéder directement aux bases SQLite pour contourner les services ou repositories ;
- les règles métier ne doivent pas être dupliquées dans plusieurs interfaces ;
- les accès aux données doivent rester centralisés dans les responsabilités prévues à cet effet.

## 9. SQLite et accès aux données

Les règles de données définies par le modèle SQLite et les invariants constituent la référence.

Une contrainte déjà portée par SQLite ne doit pas être recréée inutilement dans plusieurs couches uniquement pour « faire pareil ».

Inversement, une règle explicitement définie comme garde de service ne doit pas être déplacée arbitrairement dans un trigger SQLite.

La responsabilité de chaque règle doit rester conforme au modèle de données et aux invariants.

### Réglages de connexion SQLite

Chaque ouverture de connexion pose les réglages suivants, hors des migrations (qui ne contiennent aucun `PRAGMA`) :

- `PRAGMA foreign_keys=ON` ;
- `PRAGMA journal_mode=WAL` ;
- `PRAGMA synchronous=FULL` ;
- `PRAGMA busy_timeout` défini ;
- `PRAGMA recursive_triggers=ON`.

`recursive_triggers=ON` est obligatoire : sans lui, `INSERT OR REPLACE` supprime la ligne existante **sans déclencher** ses triggers `BEFORE DELETE`, ce qui contourne les gardes de non-suppression et d'immutabilité (vérifié). Les tests de migration doivent ouvrir leur connexion avec ces mêmes réglages.

### Écritures interdites ou encadrées

- `INSERT OR REPLACE` et `REPLACE` sont **interdits**. On utilise `INSERT`, `UPDATE` ou un UPSERT explicitement maîtrisé (`INSERT … ON CONFLICT(…) DO UPDATE`) ; `INSERT OR IGNORE` reste permis lorsque l'idempotence est voulue (singletons de `machine.db`, création des garanties).
- Raison : préserver les garanties apportées par les triggers et éviter les suppressions implicites.
- Cette interdiction est une **convention technique** : elle n'est pas imposée mécaniquement (aucun contrôle du mot `REPLACE`) ; les tests vérifient le comportement de protection (§7). Un REPLACE ne déclenche pas les triggers `UPDATE` (par exemple TR-95) : `numerotation_sequences` est donc aussi protégée par `tr_96_numerotation_sequences_no_delete` (TR-96, migration 004), effectif face au REPLACE grâce à `recursive_triggers=ON`. Les migrations déjà appliquées restent immuables : une protection manquante s'ajoute par une migration ultérieure.
- Un contrôle qui compare des lignes de plusieurs tables n'est jamais un `CHECK` ni un trigger de miroir : c'est une requête de contrôle `CK-xx` (modèle de données §14).
- Les requêtes de contrôle `CK-xx` sont exécutées après un import et après une restauration, y compris CK-13 (cohérence devis ↔ BC). CK-13 est un contrôle diagnostique : il ne corrige rien.
- Restauration : si un contrôle d'intégrité obligatoire échoue ou si CK-13 retourne une incohérence, la restauration est considérée comme échouée ; l'état restauré ne devient pas l'état de travail validé et la sauvegarde de sécurité créée avant la restauration permet le retour à l'état précédent. Le détail technique relève du module Sauvegarde / Restauration.

## 10. Nommage

Les noms doivent être explicites et cohérents avec le vocabulaire métier V6.

Il est interdit d’introduire des synonymes techniques ou fonctionnels simplement pour varier les noms d’un même concept.

Le vocabulaire du domaine doit notamment respecter les termes définis dans le CDC V6.1 et le modèle métier : client, devis, BC, facture, acompte, situation, solde, avoir, règlement, PV, garantie, prestation, fournisseur, dépense, planification, etc.

Les conventions détaillées de nommage Rust, TypeScript, React et SQL seront ajoutées avant la création des premières séries importantes de fichiers dans ces technologies.

## 11. Pas d’anticipation architecturale

V6 ne doit pas être sur-architecturé.

Ne pas créer prématurément :

- des couches sans responsabilité réelle ;
- des abstractions génériques sans second usage ;
- des modules vides uniquement pour préparer une architecture hypothétique ;
- des systèmes de plugins ou d’extensions non demandés ;
- des mécanismes destinés à BATORYA Entreprise.

BATORYA Entreprise est hors périmètre de V6 et ne doit pas influencer les choix d’implémentation d’Essentiel.

## 12. Évolution du document

Ce document est un référentiel vivant.

Une convention n’est ajoutée que lorsqu’elle est :

- nécessaire ;
- suffisamment claire ;
- compatible avec les documents de référence ;
- utile à plusieurs fichiers ou modules, ou nécessaire pour éviter une dérive d’architecture.

Les conventions détaillées seront donc ajoutées au moment où l’implémentation les rend nécessaires.

## 13. Règle de travail avec les assistants de développement

Lorsqu’un assistant de développement produit un nouveau fichier, il doit respecter l’arborescence et les conventions déjà définies.

Il ne doit pas :

- renommer arbitrairement un fichier existant ;
- déplacer un fichier existant sans raison architecturale explicite ;
- créer une nouvelle couche uniquement pour résoudre localement un problème ;
- modifier un document de référence sans signaler précisément la modification ;
- introduire une fonctionnalité hors du périmètre V6.

Lorsqu’un emplacement ou une convention n’est pas encore défini, l’assistant peut proposer une solution, mais celle-ci doit être validée avant de devenir une convention du projet.
