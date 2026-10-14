# D4 — Fiche de report vers la V3.14 (modèle de données)

> **Zone non officielle.** À utiliser pour la reconstruction de V3.14 **à partir de V3.12**. Les numéros de ligne sont ceux de `docs/conception/modèle-données-sqlite-v6-v3.12.md` à `d1d8bb9`. La V3.12 n'est pas modifiée.
> Rien ici n'est validé tant que Rémy n'a pas confirmé la forme (voir A §7).

## 1. Règle stricte d'annulation du BC (si autorisée)
| Ligne | Texte actuel | Texte proposé |
|---|---|---|
| 898 (D-05) | « Annulation directe du BC **interdite** dès qu'une facture autre qu'un acompte non réglé existe (V3.4 conservé), plus strict que CDC §17 (voir errata E-07) » ; alternative écartée : « autoriser avec solde impayé et sans situation » ; « **Validée** 2026-09-29 » | « Annulation directe du BC **interdite** dès qu'au moins une facture (acompte, situation, solde ou avoir) est rattachée au BC, réglée ou non, avoir total compris ; un acompte prévu au devis, sans facture émise, ne bloque pas (errata E-07 révisé) » ; alternatives écartées : « autoriser avec acompte non réglé ; autoriser avec solde impayé et sans situation ; rétablir le droit par un avoir total ; se fonder sur les caches du BC » ; statut : « D-05 validée 2026-09-29, **révisée** 2026-10-13 (décision de Rémy) » — format d'annotation à arbitrer (`docs/` n'en connaît aucun) |
| 332 | « La règle complète d'**annulation** (INV-44 : factures, situations, encaissements) reste dans le service : elle dépend des tables de facturation et de règlement, que la migration BC n'anticipe pas. La base n'empêche que les incohérences structurelles (annulé terminal, caches, lignes figées). » | « La règle d'**annulation** (INV-44) est portée par le service (motif obligatoire, historique) **et** garantie en base à partir de la migration corrective 009a (TR-103) : la transition vers `annule` est refusée dès qu'une facture référence le BC. La migration BC (004) n'anticipait pas cette garde. La base garantit en outre les incohérences structurelles (annulé terminal, caches, lignes figées). » |
| 356 | `\| Annulation du BC (INV-44) \| — \| oui \| — \|` | `\| Annulation du BC (INV-44) \| TR-103 (009a) \| oui (motif, historique) \| — \|` |
| 640 | « Autres règles de **service** sans trigger : … annulation du BC (INV-44), … » | retirer « annulation du BC (INV-44) » de cette liste |
| 605-617 (tableau des triggers) | — | ajouter `\| TR-103 \| bons_commande / UPDATE de `statut` vers `annule` \| refusé si `OLD.statut <> 'annule'` et qu'une ligne de `factures` référence le BC ; message `INV-44` \| 44 \|` (trigger `tr_103_bons_commande_annulation_facturee` de la proposition 009a) |
| 809 (C-19) | « Situation annulée, puis BC : annulation directe demandée → refusée (INV-44) » | conserver et ajouter : acompte **prévu** sans facture → annulation permise ; facture d'acompte non réglée → refusée ; facture réglée → refusée ; avoir total → refusée ; émission de facture échouée ou défaite par rollback → permise ; BC annulé **avant** 009a : aucun effet rétroactif (les UPDATE de caches restent permis, la transition n'est pas rejouée) |
| 366, 717 | « BC historique annulé (import) : … factures éventuelles… → annulation du BC, puis du devis (TR-18) » | selon l'arbitrage M-04 : supprimer, ou « Aucun BC annulé n'est importé » (sous réserve de la cascade, dossier F) |

## 2. Corrections internes de V3.12 à faire dans V3.14 (erreurs matérielles)
| Ligne | Problème | Correction |
|---|---|---|
| 862 | T-29 « à écrire avec la migration 004 » alors que l.483 et l.973 disent « intégré » | « écrit et intégré avec la migration 004 » |
| 992 | « copies en relecture, tests du dépôt non exécutés » pour les tests 001-003 renforcés | les tests sont dans le dépôt (28, 18, 68 tests) : reformuler |
| §13 | titres 13.2 et 13.3 sans 13.1 | ajouter le titre ou renuméroter (attention aux renvois « §13.2 », « §13.3 ») |
| 981-990 | tableau §17.1 coupé par une ligne vide (l.987) | supprimer la ligne vide ; compléter avec la table du §4 ci-dessous |
| §17.1 / 003 | l'official dit V3.11, l'en-tête de 003 cite V3.10 | consigner l'écart sans modifier 003 |

## 3. Identifiants à régulariser lors de V3.14 (aucun nouveau numéro attribué ici)
| Famille | Où ils apparaissent | Source de définition retrouvée | À faire |
|---|---|---|---|
| D-40 à D-61 | migrations 005 à 009, tests, `MAJ…v3.13.md` | `MAJ__modèle…v3.13.md` (registre D) et messages de Rémy ; **D-55, D-56 validées dans leur périmètre** ; D-58 non vérifiée ; D-61 contient « pas de V3.14 » (contredit la décision du 13/10) | reprendre uniquement ceux dont la validation est établie |
| E-10 à E-20 | `MAJ__cdc-errata-v6.md` | idem ; E-15 et le D-46 associé portent la règle d'annulation **inverse** | ne pas reprendre E-15 tel quel (M-03) |
| INV-179 à INV-203 | migrations, tests, `MAJ__invariants.md` | `MAJ__invariants.md` | reprendre un par un ; INV-188 dépend de la règle d'annulation |
| TR-97 à TR-102 | 005, 005a, 005b | `MAJ…v3.13.md` §8 | idem |
| TR-99 | `bc_devis` (INSERT/UPDATE/DELETE dans la MAJ) ; 006 : `tr_99_bc_devis_apres_solde` | `MAJ…v3.13.md` l.782 ; `006` l.483 | une ligne de registre par trigger |
| TR-103 | proposition 009a | `PROPOSITION_DIFF__009a_V2…diff` | attribuer après arbitrage du rang et du registre |
| TR-51 | migration 008 | `CADRAGE__008_garanties.md` seulement | le modèle V3.12 définit TR-50 puis TR-60 (TR-51 libre dans le registre officiel) : TR-51 est utilisé par 008 sans définition officielle ; intégrer au registre si la reprise est validée |

## 4. Table de correspondance migration → rang → modèle cité (pour §17.1)
| Migration | Rang (`user_version`) | Modèle cité dans l'en-tête | Statut du modèle cité |
|---|---|---|---|
| `machine/001_initial` | chaîne `machine` distincte | V3.8 | historique |
| `001_initial` | 1 | V3.9 | historique |
| `002_fournisseurs` | 2 | V3.10 | historique |
| `003_devis` | 3 | V3.10 (le §17.1 officiel dit V3.11) | historique ; écart à consigner |
| `004_bons_commande` | 4 | V3.12 | validé |
| `005_depenses` | 5 | V3.13 | **proposition non validée** |
| `005a_corrections_v313` | 6 | V3.13 | idem |
| `005b_bc_multi_devis` | 7 | V3.13 | idem |
| `005c_bc_annule_caches_financiers` | 8 | V3.13 | idem |
| `006_facturation` | 9 | V3.13 | idem |
| `007_reglements` | 10 | V3.13 | idem |
| `008_garanties` | 11 | V3.13 | idem |
| `009_pv` | 12 | V3.13 | idem |
| `009a_bc_annulation_interdite_si_facture` (proposition) | 13 proposé (« privilégié », sous réserve du contrôle des bases de développement [NV]) | — | non livrée |

Sources : en-têtes des migrations (`mig.py`). Le rang est la position dans la chaîne ; les noms de fichiers ne sont pas modifiés (conventions l.83).
