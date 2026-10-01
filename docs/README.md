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
- `conception/modèle-données-sqlite-v6-v3.11.md` — modèle de données SQLite V3.11, référence validée

### Décisions
- `décisions/cdc-errata-v6.md` — errata et corrections validés au cours de la consolidation du CDC

### Spécifications
- `specifications/cdc-fonctionnel-architectural-v6.md` — CDC fonctionnel et architectural V6 consolidé

## Règle de cohérence documentaire

Le CDC V6 doit être lu conjointement avec les documents de référence ci-dessus.

Les décisions validées dans les invariants, le modèle métier, le modèle de données SQLite et les errata doivent être cohérentes avec le CDC. Lorsqu'une décision validée a été intégrée au CDC, le CDC présente directement la règle courante ; les documents de décisions conservent la traçabilité des corrections.

Le modèle de données SQLite V3.11 est la référence validée pour le schéma de données. Les modèles V3.6, V3.7, V3.8, V3.9 et V3.10 ont été remplacés et ne doivent pas être réintroduits.

## Périmètre

Cette documentation concerne exclusivement **BATORYA Essentiel V6**.

Les concepts, fonctionnalités ou contraintes propres à BATORYA Entreprise ne doivent pas être introduits dans Essentiel V6 par anticipation.

Le contenu de `docs/` ne constitue pas du code applicatif. Il sert de référence pour la conception et l'implémentation de BATORYA Essentiel V6.
