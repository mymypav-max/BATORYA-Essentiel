# Documentation — BATORYA Essentiel V6

Ce dossier contient la documentation de référence de BATORYA Essentiel V6 : audits, conception, décisions validées et spécifications fonctionnelles et architecturales.

## Organisation

- `audit/` — audits et analyses de l'existant
- `conception/` — invariants, modèle métier et modèle de données SQLite V6
- `décisions/` — décisions et errata validés
- `specifications/` — cahier des charges fonctionnel et architectural V6

Il n'existe pas de dossier `migration/` autonome à ce stade. La migration V2 → V6 est décrite dans les documents de conception, de décisions et dans le CDC.

## Documents de référence actuels

### Audit
- `audit/audit-fonctionnel-v5.16-v6.md` — audit fonctionnel de l'existant et cadrage V6

### Conception
- `conception/invariants.md` — invariants fonctionnels et techniques validés
- `conception/conventions-techniques-v6.md` — conventions techniques et de code V6
- `conception/modèle-métier-V6.md` — modèle métier V6
- `conception/modèle-données-sqlite-v6-v3.13.md` — modèle de données SQLite **V3.13 (2026-10-03, en relecture)** : intègre les arbitrages métier Q1–Q27 et A–D ; **devient la version courante après validation** ; remplace la V3.12
- `conception/modèle-données-sqlite-v6-v3.12.md` — modèle de données SQLite V3.12, **dernière version validée** (conception de la tranche Bons de commande incluse), conservée jusqu'à la validation de la V3.13

### Décisions
- `décisions/cdc-errata-v6.md` — errata et corrections validés au cours de la consolidation du CDC (E-01 à E-20 ; E-10 à E-20 du 2026-10-03 en relecture)

### Spécifications
- `specifications/cdc-fonctionnel-architectural-v6.md` — CDC fonctionnel et architectural V6 consolidé (V6.2 en relecture : encadrés « Amendement E-10 à E-20 »)

## Règle de cohérence documentaire

Le CDC V6 doit être lu conjointement avec les documents de référence ci-dessus.

Les décisions validées dans les invariants, le modèle métier, le modèle de données SQLite et les errata doivent être cohérentes avec le CDC. Lorsqu'une décision validée a été intégrée au CDC, le CDC présente directement la règle courante ; les documents de décisions conservent la traçabilité des corrections.

Le modèle de données SQLite V3.13 (en relecture) intègre les arbitrages du 2026-10-03 ; tant qu'il n'est pas validé, la V3.12 reste la dernière version validée. Les migrations 001–004 correspondent à la V3.12 et ne sont pas réécrites : leurs écarts avec la V3.13 sont listés au §4.19 du modèle V3.13 et se corrigent par des migrations ultérieures. La V3.12 remplace la V3.11, dont l'historique reste documenté. Les modèles V3.6, V3.7, V3.8, V3.9, V3.10 et V3.11 ont été remplacés et ne doivent pas être réintroduits.

## Périmètre

Cette documentation concerne exclusivement **BATORYA Essentiel V6**.

Les concepts, fonctionnalités ou contraintes propres à BATORYA Entreprise ne doivent pas être introduits dans Essentiel V6 par anticipation.

Le contenu de `docs/` ne constitue pas du code applicatif. Il sert de référence pour la conception et l'implémentation de BATORYA Essentiel V6.
