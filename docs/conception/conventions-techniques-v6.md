# BATORYA Essentiel V6 — Conventions techniques et de code

**Version : 0.1 — document évolutif**  
**Périmètre : conventions techniques de développement V6**

## 1. Objet

Ce document définit les conventions techniques applicables au code de BATORYA Essentiel V6.

Il complète les documents de référence fonctionnels et architecturaux. Il ne remplace ni le CDC, ni le modèle de données SQLite, ni le registre des invariants, ni le modèle métier.

Son objectif est de maintenir une arborescence cohérente et prévisible pendant l’implémentation.

Le document est volontairement évolutif : les conventions seront complétées au fur et à mesure de l’avancement réel du développement, sans créer prématurément une architecture non nécessaire.

## 2. Documents de référence

Avant toute implémentation ou modification structurelle, les références suivantes doivent être considérées dans cet ordre de priorité métier et architectural :

1. `docs/specifications/cdc-fonctionnel-architectural-v6.md`
2. `docs/conception/modèle-données-sqlite-V6-V3.8.md`
3. `docs/conception/invariants.md`
4. `docs/conception/modèle-métier-V6.md`
5. `docs/décisions/cdc-errata-v6.md` pour la traçabilité historique uniquement.

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

## 4. Arborescence technique actuelle

L’arborescence technique actuellement validée est volontairement minimale :

```text
src-tauri/
├── migrations/
│   └── machine/
│       └── 001_initial.sql
│
└── tests/
    └── machine/
        └── test_premier_demarrage.py
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

Les conventions détaillées des migrations métier seront ajoutées lorsque la première migration métier sera définie.

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

Un test doit avoir un nom explicite permettant d’identifier directement le comportement vérifié.

Les tests ne doivent pas devenir une seconde spécification contradictoire : lorsqu’un comportement est modifié volontairement, le test correspondant doit être mis en cohérence avec la décision et les documents de référence.

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

## 10. Nommage

Les noms doivent être explicites et cohérents avec le vocabulaire métier V6.

Il est interdit d’introduire des synonymes techniques ou fonctionnels simplement pour varier les noms d’un même concept.

Le vocabulaire du domaine doit notamment respecter les termes déjà gelés dans le CDC et le modèle métier : client, devis, BC, facture, acompte, situation, solde, avoir, règlement, PV, garantie, prestation, fournisseur, dépense, planification, etc.

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

