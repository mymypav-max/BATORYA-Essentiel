# PROPOSITION DE CORRECTIONS DOCUMENTAIRES — 009, octet NUL (pour revue, rien d'appliqué aux documents officiels)

Date : 2026-10-10. Objet : corriger les formulations qui attribuaient à tort au cadrage 009 une décision explicite sur le défaut NUL. Vérification faite par recherche textuelle dans `009_pv.sql`, `test_009_pv.py`, `RAPPORT_MUTATION__009_pv.md`, `CADRAGE__009_pv.md`, `CADRAGE__007_reglements.md`, `RAPPORT_MUTATION__00[78]*`, `COMPLEMENT_*`.

## 1. Déjà corrigé dans les fichiers dont tu as autorisé la modification (rien à décider)

| Fichier | Formulation fautive (avant) | État |
|---|---|---|
| `test_009_pv.py`, docstring de `test_T51_K_LIMITE_…` | « LIMITE constatée, NON corrigée par 009 (cadrage validé) … comportement de TOUS les CHECK GLOB de la chaîne » | test remplacé par `test_T51_K_octet_nul_apres_le_numero_ou_le_created_at_refuse` ; la docstring ne cite plus le cadrage (diff de tests validé, appliqué) |
| `RAPPORT_MUTATION__009_pv.md` §5 | « Limite non corrigée, commune à tous les CHECK `GLOB` de la chaîne … (aucune règle documentaire ne l'exige) » | remplacée par « Octet NUL — corrigé dans 009, limite subsistante hors 009 », qui précise que **le cadrage 009 ne contenait pas de décision sur ce point** (rapport mis à jour après la campagne complète) |

## 2. Documents officiels : aucune formulation fausse trouvée, trois mentions optionnelles

Aucune phrase de `CADRAGE__009_pv.md` n'affirme que le défaut NUL est accepté ou refusé : il ne fait que prévoir des tests de données malformées (§5 point 8, §6 groupe K). **Aucune modification n'est nécessaire à la conformité.** Mentions que tu pourrais souhaiter, pour que le cadrage reflète la décision du 2026-10-10 :

| # | Où | Ancien | Nouveau (proposé) |
|---|---|---|---|
| D-1 | `CADRAGE__009_pv.md` §5, point 8 (l.282) | `… REAL/BLOB/NUL dans colonnes TEXT (STRICT) ; casse du `type`.` | `… REAL/BLOB/NUL dans colonnes TEXT (STRICT) ; octet NUL après le numéro initial V6 (12 octets attendus), après `created_at` (24 octets attendus) et NUL brut dans `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot`, `legacy_data` (refusés ; l'échappement JSON \u0000 reste valide — décision du 2026-10-10) ; casse du `type`.` |
| D-2 | `CADRAGE__009_pv.md` §3.1 (contraintes de table), nouvelle puce | — | `Contrôle d'octets (décision du 2026-10-10) : GLOB, substr, length() de TEXT et json_valid s'arrêtent au premier octet NUL ; 009 ajoute length(CAST(numero AS BLOB)) = 12 (PV initial V6 uniquement ; origine='import' et levée inchangées : INV-131, PR-3, Z-8), length(CAST(created_at AS BLOB)) = 24 et instr(CAST(c AS BLOB), x'00') = 0 sur les quatre champs JSON.` |
| D-3 | `CADRAGE__007_reglements.md` §6 « Limites connues » (2) (l.193) | limite NUL pour les montants, « documentée, non traitée par 007 » | **inchangé** : toujours exact pour 001–008. Seul renvoi à ajouter, si tu le souhaites : `(traitement proposé : PLAN_REMEDIATION__001_008__controle_nul.md)` |

Hors périmètre de cette proposition : modèle de données, invariants et conventions n'ont pas été relus pour une mention du format de `created_at` en octets ; je ne les modifie pas et n'invente pas de numéro de ligne.
