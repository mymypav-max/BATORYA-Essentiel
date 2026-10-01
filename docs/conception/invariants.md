# BATORYA Essentiel V6 — Registre des invariants

Version du registre : 4 — 2026-10-01 (rattaché au modèle SQLite V3.9 ; V2 : migration V2 externalisée, V3 : high-water, V4 : compte local et initialisation de `machine.db`, voir le journal en bas)
Statut : **pièce obligatoire du modèle de données**

## Mode d'emploi

- Un invariant (**INV-xx**) est une règle métier ou technique déjà validée. Son numéro est **stable** : il n'est jamais réutilisé ni renuméroté. Les numéros absents de la séquence (trous entre sections) sont **réservés** : ils ne sont jamais attribués rétroactivement, une nouvelle règle reçoit le numéro suivant le plus élevé (INV-171, …).
- Chaque INV a une **garde** et **un test du même nom** (`test_INV_xx`) : SQL (CHECK, UNIQUE, FK, index partiel), TRG (trigger `TR-xx`), SVC (service applicatif), CK (requête de contrôle `CK-xx`).
- Avant de valider une nouvelle version du modèle, on la compare à ce registre. **Aucun INV ne disparaît ou ne change de sens sans ligne dans le journal des retraits/modifications** (en bas), avec date, motif et décision.
- Toute règle nouvelle : ajouter une ligne (nouveau numéro), sa garde, son test.
- Colonne « Cas » : cas chiffré de référence du §13 du modèle.

---

## A. Architecture et données

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-01 | SQLite est la source de vérité ; l'UI n'exécute jamais de SQL ; accès SQLite côté Rust uniquement | SVC | |
| INV-02 | Deux bases : métier (sauvegardée/restaurée) et `machine.db` (jamais incluse, jamais écrasée par une restauration) | SVC, test de restauration | |
| INV-03 | Aucune donnée métier n'est transmise au service distant (licence, mises à jour, référentiels seuls) | SVC | |
| INV-04 | `id` = `INTEGER PRIMARY KEY AUTOINCREMENT`, jamais réutilisé ; un numéro métier n'est jamais une clé étrangère | SQL | |
| INV-05 | FK en `RESTRICT` ; `CASCADE` uniquement pour lignes → parent avant gel, `*_ligne_garanties`, `prestation_garanties` | SQL | |
| INV-06 | Aucune suppression physique des entités historiques (clients/fournisseurs/prestations utilisés, devis avec BC, BC facturés, factures, règlements, PV, garanties, historique) : archivage, annulation, avoir | SQL, TRG | |
| INV-07 | À chaque connexion : `foreign_keys=ON`, WAL, `synchronous=FULL`, `busy_timeout` | SVC, test | |
| INV-08 | Migrations de schéma numérotées, atomiques, `user_version` mis à jour après succès ; `machine.db` a le sien | SVC, test | |
| INV-09 | Toute opération métier multi-tables est une transaction unique ; aucune opération partielle | SVC, test | |

## B. Dates et montants

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-10 | Dates métier `YYYY-MM-DD` (date réelle) ; timestamps `*_at` ISO UTC ; planning en heure locale ; une date métier n'est jamais déduite d'un timestamp | SQL | |
| INV-11 | Aucun `REAL` pour un montant ; TEXT canonique contrôlé (familles D2, D2S, DL, P2) | SQL | C-14 |
| INV-12 | Arithmétique SQL des montants uniquement par centimes entiers ; jamais `CAST REAL`, `SUM` ou `ORDER BY` sur TEXT décimal | SVC, revue de DDL | |
| INV-13 | Arrondi HALF_UP (valeur absolue), un seul arrondi par ligne ; total = Σ lignes arrondies − remise globale arrondie | SVC | C-14 à C-17 |
| INV-14 | Précision libre uniquement pour `quantite`, `prix_unitaire_ht`, remise « montant » de ligne, taux ; tout autre montant : 2 décimales ; négatifs limités à `facture_lignes.montant_ht` (déduction), `ca_encaisse`, `ecart`, `urssaf_details.base`, `montant_retenu` | SQL | |
| INV-15 | Import : tout montant du fichier `import-v6.json` est à la précision de sa famille décimale, sinon le fichier est rejeté ; V6 ne réarrondit pas à l'import (l'arrondi des totaux V2 non arrondis est fait par le convertisseur) | SVC, CK | T-21 |

## C. Numérotation

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-20 | Formats V6 : `CLI-0001`, `FOU-0001`, `DEV|BCD|FAC|ACP|AVO|PVR|DEP-00001-yy`, levée `PVR-00001-yy-01` ; `yy` = année de la date métier ; contrôle de format sans exception, sauf devis, factures et PV `origine='import'` (INV-131) | SQL | |
| INV-21 | Séquence unique par `(type_objet, annee)` ; `annee=0` pour CLI/FOU ; situation et solde partagent FAC ; ACP et AVO séparés | SQL | |
| INV-22 | Attribution atomique dans la transaction de création ; numéro jamais réattribué ; erreur explicite au plafond (99 999 / 9 999) ; `dernier_numero` ne diminue jamais | SVC, TRG (TR-95), SQL | T-20 |
| INV-23 | `numero` immuable ; l'année (yy) de la date de numérotation ne change jamais ; `date_creation` devis/BC immuable | TRG (TR-01) | |
| INV-24 | ACP, FAC, AVO : `date_emission` ≥ dernière date de la séquence (pas pour DEV, BCD, PVR, DEP) | TRG (TR-02) | |
| INV-25 | `sequence_high_water` (machine.db) : `max_attribue` ne diminue jamais automatiquement ; initialisé à l'import depuis `sequences` (INV-135) ; après restauration, `dernier_numero` = max(restauré, `max_attribue`) et `max_attribue` = max(`max_attribue`, `dernier_numero` restauré) ; au démarrage normal, si `max_attribue` > `dernier_numero` (crash avant COMMIT), `max_attribue` est conservé, le prochain numéro est `max_attribue` + 1, le trou est accepté et journalisé ; aucun numéro attribué n'est réutilisé | SVC, test | C-18, T-22, T-24 |
| INV-26 | Suffixe PV de levée = max + 1 par PV d'origine, dans la transaction | TRG (TR-41), SQL | |
| INV-27 | Les devis, factures et PV importés gardent le numéro historique remis au client, jamais transformé en numéro V6 ; les BC et codes clients importés reçoivent un numéro V6 du convertisseur (ancien code dans `legacy_numero`) | SQL, CK-01 | T-23 |

## D. Snapshots, gel, contrat

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-30 | Devis, BC, factures, PV portent des snapshots versionnés (client, entreprise, chantier) ; le catalogue, la fiche client et les paramètres n'altèrent jamais un document existant | SQL, SVC | |
| INV-31 | Devis/BC non gelés : snapshots réécrits à chaque sauvegarde ; devis modifiable seulement si `en_attente`, ou `accepte` non gelé ; `refuse`/`annule` immuables | TRG (TR-10) | |
| INV-32 | Factures et PV figés dès l'INSERT (aucun brouillon) | TRG (TR-20, TR-40) | |
| INV-33 | `frozen_at` posé par trigger sur devis et BC, même transaction, au premier de : encaissement actif (même partiel) d'un acompte, insertion d'une situation, insertion d'un solde | TRG (TR-15) | C-02, T-09, T-10, T-11 |
| INV-34 | `frozen_at` est irréversible ; l'annulation d'une facture ne dégèle pas | TRG (TR-14) | T-09 |
| INV-35 | Un acompte émis non encaissé ne gèle pas ; modifier le devis/BC l'annule automatiquement dans la même transaction (acteur `systeme`, motif automatique) | SVC, test | C-01, T-08 |
| INV-36 | Après gel : lignes, garanties de lignes, remises, acompte prévu, client, chantier, snapshots, montant contractuel immuables | TRG (TR-10 à TR-13) | |
| INV-37 | Une modification du catalogue ne modifie jamais lignes ni garanties d'un devis, BC ou facture existants | SQL, test | T-07 |
| INV-38 | Le devis est le seul point d'édition ; sa modification régénère `bc_lignes`, garanties de lignes, montant contractuel et snapshots du BC dans la même transaction | SVC, test | |
| INV-39 | `montant_contractuel_ht` = Σ lignes du BC − remise globale arrondie | SVC, CK-05 | |

## E. Bon de commande

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-40 | Un devis accepté produit un seul BC (création atomique, idempotente) ; le BC naît `en_cours` | SQL (`UNIQUE(devis_id)`), TRG (TR-17) | T-01 |
| INV-41 | Le statut du BC n'est pas librement modifiable par l'utilisateur | SVC | |
| INV-42 | BC `termine` ⇔ solde actif ET Σ reste dû des factures actives hors avoir = 0 ; un solde à 0.00 ne suffit pas ; l'avoir n'est pas un encaissement mais réduit le reste dû via `absorbe` | SVC, CK-06, SQL (`termine ⇔ completed_at`) | C-05, C-08, C-10 |
| INV-43 | `date_100_facture` = date d'émission du premier solde actif ; conservée par avoir, règlement, remboursement ; `NULL` seulement à l'annulation du solde ; distincte de `garanties.date_declenchement` | SVC, CK-06 | C-07, C-20 |
| INV-44 | Annulation directe du BC : interdite si encaissement actif, ou si une situation a été émise (même annulée) ; autorisée avec acompte non réglé, annulé dans la même transaction ; toute autre facture interdit l'annulation (décision D-05) | SVC, test | C-01, C-19 |
| INV-45 | BC annulé : devis `annule`, PDF du devis dans `Devis/Annule`, exclu du CA engagé, aucune nouvelle facturation ; CA engagé = Σ max(0, (contractuel − avoirs) − (encaissements − remboursements)) des BC `en_cours` | SVC, test | C-13 |
| INV-46 | Caches BC (`montant_deja_facture_ht`, `avancement`, `date_100_facture`, `statut`, `completed_at`) recalculés par un service financier unique, même transaction ; source de vérité = factures + règlements | SVC, CK-06 | |
| INV-47 | Facturation possible uniquement sur un BC `en_cours` | TRG (TR-16) | |
| INV-48 | `client_id` cohérent entre devis, BC et factures | TRG (TR-16, TR-17) | |
| INV-49 | La seule modification autorisée de `client_id` sur un document gelé ou une facture est le rattachement d'un client `a_rattacher` (tracé) | TRG (TR-20) | |

## F. Facturation

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-52 | Un seul acompte actif, un seul solde actif, une situation active par numéro et par BC | SQL (index partiels) | C-20, T-02, T-03 |
| INV-53 | Facture immuable dès l'INSERT (contenu, lignes, numéro, montants, snapshots) ; seuls `cancelled_at`/`motif_annulation` (une fois) et le rattachement client évoluent ; jamais supprimée | TRG (TR-20, TR-21) | |
| INV-54 | `Σ facture_lignes.montant_ht = factures.total_ht` (aucune exemption, y compris pour les données importées) | SVC, CK-05 | C-08, T-19 |
| INV-55 | `total_ht` : acompte, situation, avoir > 0.00 ; solde ≥ 0.00 ; aucun TTC ; type `complete` inexistant ; solde toujours de type `solde` | SQL | C-08 |
| INV-56 | Facturation nette = Σ acomptes + situations + solde actifs − Σ avoirs actifs | SVC, test | C-09 |
| INV-57 | Situation = arrondi(contractuel × cumul %) − nette avant ; nette après ≤ contractuel ; acompte ≤ contractuel ; seule la dernière situation active est annulable | TRG (TR-22, TR-24), SVC | C-03, C-09 |
| INV-58 | Solde = contractuel − nette avant solde ; solde actif ⇒ plus d'acompte ni de situation ; aucun avoir ne rouvre la facturation ni ne crée de nouveau solde | TRG (TR-22, TR-23), SVC | C-04, C-07, C-08, T-12 |
| INV-59 | `date_echeance` obligatoire hors avoir, NULL pour un avoir, ≥ `date_emission` | SQL | |
| INV-60 | Le statut d'une facture n'est jamais persisté ; `en_retard` est un indicateur transversal dérivé ; facture à `reste_du=0` = `reglee` | SVC (pas de colonne) | C-02 |
| INV-61 | Une facture ayant un encaissement actif ou un avoir actif ne s'annule pas (correction par avoir) ; acompte/situation non annulable si situation ou solde actif postérieur ; `cancelled_at` irréversible | TRG (TR-24) | C-19 |
| INV-62 | Composition des lignes : acompte = 1 ligne `synthese` ; situation = 1 ligne `synthese` du montant de la situation ; solde = lignes BC + lignes `deduction` ; négatifs uniquement `deduction` | SQL, SVC | C-08 |

## G. Règlements, avoirs, remboursements

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-70 | Un règlement (`encaissement` ou `remboursement`) a un montant > 0, n'est jamais supprimé ni modifié ; seule l'annulation (`cancelled_at` + motif, une fois) est possible | SQL, TRG (TR-32) | |
| INV-71 | Un encaissement cible une facture hors avoir active ; un remboursement cible un avoir actif ; pas de colonne `avoir_id` | TRG (TR-30) | |
| INV-72 | Encaissement ≤ reste dû ; aucun encaissement sur facture annulée | TRG (TR-31) | C-11 |
| INV-73 | `absorbe = min(Σ avoirs actifs, max(0, M − encaissements))` ; `reste_du = max(0, M − encaissements − absorbe)` ; `credit = Σ avoirs − absorbe − Σ remboursements` (par facture d'origine, jamais < 0) | SVC, test | C-06 |
| INV-74 | Remboursement ≤ crédit disponible | TRG (TR-31) | C-06 |
| INV-75 | Annulation d'un encaissement refusée si elle rend le crédit < Σ remboursements actifs | TRG (TR-33) | C-12 |
| INV-76 | Avoir : origine obligatoire, non avoir, non annulée, même BC ; motif obligatoire ; Σ avoirs actifs ≤ montant de l'origine ; pas d'imputation libre d'un crédit sur une autre facture | SQL, TRG (TR-23) | |
| INV-77 | Un avoir avec remboursement actif rattaché ne s'annule pas ; son annulation est refusée si elle rend le crédit < Σ remboursements actifs | TRG (TR-24) | |
| INV-78 | L'avoir ne supprime ni ne modifie la facture d'origine ; une facture payée n'est jamais supprimée | TRG (TR-21) | |
| INV-79 | L'annulation d'un règlement ou d'un avoir recalcule en chaîne facture, BC (`termine → en_cours`, `completed_at=NULL`, événement historique) | SVC, test | C-05, T-13 |
| INV-80 | Un avoir n'est jamais « en retard » ; état dérivé : `credit_disponible`, `solde`, `annule` | SVC | |

## H. Garanties

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-85 | Le suivi démarre à l'émission d'un solde (100 % facturé), indépendamment du paiement, du PV, de la réception, des réserves | SVC, test | C-04 |
| INV-86 | Garanties contractuelles snapshotées par ligne de devis/BC ; création lue dans `bc_ligne_garanties`, idempotente (`INSERT OR IGNORE`), `UNIQUE(bc_ligne_id, garantie_type)` | SQL, SVC | C-20 |
| INV-87 | `date_declenchement` = date d'émission du premier solde, immuable ; annulation du solde, avoir, règlement ne suppriment ni ne modifient une garantie | TRG (TR-50) | C-07, C-20, T-14 |
| INV-88 | `date_fin_suivi` = +1 an / +2 ans / +10 ans ; 29 février → 28 février ; toujours présentée comme « Suivi interne BATORYA — date indicative » | SVC, test | |
| INV-89 | Aucun statut de garantie persisté ; état dérivé des dates | SVC (pas de colonne) | |
| INV-90 | Une garantie appartient toujours à un BC ; native : ligne et facture de déclenchement NOT NULL | SQL | |

## I. PV, dépenses, planning, notes

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-95 | Le PV est facultatif ; il ne conditionne ni le solde, ni Terminé, ni les garanties | SVC | |
| INV-96 | PV immuable dès l'INSERT ; une levée est un nouveau PV référençant un PV `reception_avec_reserves` du même BC ; jamais de levée sur levée ; `UNIQUE(origine_pv_id, suffixe)` | TRG (TR-40, TR-41), SQL | T-15 |
| INV-97 | `reserves` renseigné ⇔ `reception_avec_reserves` ; levée ⇔ `origine_pv_id` et `suffixe` renseignés | SQL | |
| INV-100 | Dépense : fournisseur par identifiant, BC optionnel ; ni statut de paiement, ni échéance, ni règlement fournisseur ; ne réduit jamais le CA URSSAF | SQL (pas de colonne), SVC | |
| INV-101 | Planning : `fin ≥ début` ; `intervention`/`travaux` avec BC ; `conge`/`indisponibilite` sans BC ; aucun effet sur le statut du BC ; le Gantt lit `date_debut/date_fin` du BC | SQL, SVC | |
| INV-102 | Les notes BC sont libres, modifiables, supprimables ; pas de tâches, aucun effet sur les montants | SVC | |

## J. Documents et historique

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-105 | `UNIQUE(type_entite, entite_id, type_document, numero_version)` ; contenu immuable ; régénération = nouvelle version ; seul `chemin_relatif` est modifiable ; aucun DELETE | SQL, TRG (TR-70) | |
| INV-106 | Chemins relatifs à une racine identifiée ; racines jamais supprimées ; changer de dossier crée une nouvelle racine ; anciens documents gardent leur racine ; `chemin_absolu` modifié seulement par remappage explicite | SVC | |
| INV-107 | Le PDF n'est jamais la source de vérité ; il se régénère depuis SQLite et les snapshots | SVC | |
| INV-108 | Arborescence annuelle `Devis/{En_attente,Accepte,Refuse,Annule}`, `Factures/{Acomptes,Situations,Soldes,Avoirs}`, `PV` ; le BC n'a pas de PDF | SVC | |
| INV-110 | `historique` est append-only (aucun UPDATE/DELETE) ; gel, émission, règlement, annulation, remboursement, avoir, passage/retour de Terminé, garantie, rattachement, URSSAF, import, restauration y sont tracés | TRG (TR-60), SVC | |
| INV-111 | `historique.type_entite` et `type_evenement` sont des énumérations fermées ; acteur `utilisateur`, `systeme` ou `import` | SQL | |

## K. URSSAF

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-120 | Le CA URSSAF repose sur les encaissements réels (date réelle ; paiement partiel = montant reçu) ; les dépenses ne le réduisent pas ; avoirs et remboursements selon le référentiel applicable | SVC | C-10 |
| INV-121 | Référentiels append-only, `UNIQUE(version)`, `UNIQUE(date_debut_effet)`, date strictement croissante ; version applicable à une période = celle en vigueur à sa `date_debut` | TRG (TR-80), SQL | |
| INV-122 | Profil URSSAF append-only ; `date_debut_activite` constante entre versions | TRG (TR-81) | |
| INV-123 | Périodes : `date_debut ≤ date_fin`, uniques, sans chevauchement ; période à CA nul créée ; première période éventuellement partielle ; `periodicite` snapshotée | SQL, TRG (TR-82) | |
| INV-124 | `ca_encaisse = Σ montant_retenu` des lignes `retenu` ; source XOR `reglement_id`/`facture_id` (avoir) ; un règlement ou un avoir compté une seule fois par période | SQL, TRG (TR-84), CK-08 | |
| INV-125 | Période verrouillée jamais réécrite : seuls `statut` et `updated_at` changent ; tout événement postérieur crée une ligne `urssaf_corrections` et passe la période à `a_verifier` ; sortie par ligne `resolution` | TRG (TR-82, TR-85), SVC | T-17, T-18 |
| INV-126 | Détails et encaissements figés au verrouillage ; `calcul_snapshot` permet de reproduire le calcul avec la version réglementaire de l'époque | TRG (TR-83) | T-18 |
| INV-127 | Aucune déclaration officielle automatique ; `ecart = montant_declare − (cotisations + cfp)` fixé à la déclaration | SVC, SQL | |

## L. Import de `import-v6.json` (contrat d'entrée V6)

Flux : sauvegarde JSON V2 → **convertisseur externe** → `import-v6.json` → **import V6**. Les invariants ci-dessous ne concernent que l'étape 2 (validation et import par V6). Les règles de transformation V2 sont sorties de ce registre : voir le journal (règles transférées au futur `docs/migration/convertisseur-v2-vers-import-v6.md`).

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-130 | Aucune donnée d'import supprimée en silence : ce que le fichier déclare `non_importe` est conservé dans `import_anomalies` ; `import_anomalies` jamais supprimée (seuls `statut` et `traite_at` évoluent) ; le fichier source n'est jamais modifié | TRG (TR-90), SVC | T-21 |
| INV-131 | Aucune règle métier n'est exemptée pour les données importées. Seule exception : format, préfixe et année du `numero` des devis, factures et PV `origine='import'` (numéro déjà remis au client) ; non vide, unique et immuable (TR-01) | SQL (CHECK conditionnés par `origine`), TRG | T-23 |
| INV-133 | Fin d'import : comptages, Σ `total_ht` des factures actives et Σ `reste_du` déclarés dans `controles` = valeurs recalculées par V6 ; tout écart, ou tout échec de CK-01 à CK-12, annule l'import | CK-12, SVC | T-16 |
| INV-134 | Le contrat d'import n'accepte aucune garantie ; les garanties naissent uniquement de la facturation V6 ; `garanties.bc_ligne_id` et `facture_declenchement_id` sont NOT NULL sans exception ; une garantie n'est jamais recalculée | SQL, SVC | |
| INV-135 | Compteurs : le convertisseur récupère les compteurs historiques compatibles ; ils sont transmis dans `import-v6.json` (`sequences`) ; V6 initialise `numerotation_sequences` et `sequence_high_water` à partir de ces valeurs ; un numéro déjà attribué n'est jamais réutilisé ; un saut de numéro est acceptable | SVC, CK-02 | T-22 |
| INV-136 | `origine` ∈ (`v6`, `import`) ; `origine='v6'` ⇒ `legacy_id`, `legacy_data` et `legacy_numero` NULL ; `legacy_numero` seulement s'il diffère de `numero` (clients et BC) ; `legacy_id` = `ref` de l'objet dans le fichier ; aucune colonne `migration_id` | SQL | |
| INV-153 | Lecteur strict de `import-v6.json` : rejet total si JSON invalide, `format`/`contrat_version` inconnus, clé ou bloc inconnu, `ref` dupliqué ou introuvable, énumération ou précision décimale invalide, violation d'un CHECK ou d'un trigger ; jamais de réparation ni de tolérance côté V6 | SVC, test | T-21 |
| INV-154 | Import en deux temps (validation sans écriture, puis transaction unique, tout ou rien) et seulement sur base métier vide | SVC, test | T-21, T-23 |
| INV-161 | Le contrat d'import n'accepte aucune donnée URSSAF ; le profil URSSAF est saisi au premier lancement ; aucune période n'est calculée avant | SVC | |
| INV-163 | Une anomalie `a_verifier` du fichier crée un enregistrement `import_anomalies` lié à l'objet importé ; le tableau de bord affiche le bandeau tant qu'il en existe au statut `a_traiter` ; une facture importée non réglée est une facture ordinaire (facturation, reste dû, CA engagé ; ni CA encaissé ni URSSAF sans règlement saisi) (D-19) | SVC, CK-06, test | T-16 |
| INV-164 | Ordre de recalcul du service financier : factures actives → facturation nette → montant restant → avancement → état 100 % → `date_100_facture` → reste dû du solde → `termine`/`en_cours` → CA engagé ; jamais de cache intermédiaire incohérent | SVC, CK-06 | |
| INV-165 | Deux catégories seulement dans V6 : `a_verifier` (objet importé à contrôler) et `non_importe` (donnée non représentable, conservée) ; les avertissements purement informatifs restent dans le rapport du convertisseur | SVC | |
| INV-166 | Le catalogue par défaut V6 exclut ELE-008 (prise RJ45 Cat6) ; un document historique qui la contient la conserve par snapshot, `prestation_id NULL` | SVC | |
| INV-167 | Les tests d'intégrité T-01 à T-20 (modèle §13.2) sont couverts avant le passage au DDL | test | T-01 à T-20 |
| INV-168 | Avant le gel, aucune fonction ne référence une ligne de BC (`bc_lignes.id`), hors `facture_lignes.bc_ligne_id` en `RESTRICT` ; toute nouvelle fonction qui en aurait besoin exige d'abord de rétablir des identifiants stables (décision D-20) | SVC, revue | |
| INV-169 | Le fichier d'import ne porte que des faits saisis : caches du BC, `frozen_at`, états dérivés et garanties ne sont jamais lus du fichier ; V6 les recalcule (§3.7) et pose le gel par TR-15 | SVC, CK-06 | T-21 |
| INV-170 | Deux périmètres de tests : tests du convertisseur (`TC-xx`, hors V6) et tests de validation/import V6 (T-16, T-21 à T-23) ; aucun test V6 ne lit un fichier V2 | test | T-16, T-21, T-22, T-23 |

## M. Sauvegarde, restauration, licence

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-140 | Sauvegarde par API Backup SQLite ou `VACUUM INTO`, jamais copie brute en WAL ; le fichier ne contient que la base métier | SVC, test | |
| INV-141 | Restauration : validation, `user_version` ≤ supporté (refus sinon), migrations sur copie, `integrity_check`, `foreign_key_check`, sauvegarde de sécurité, remplacement atomique, contrôles post-restauration | SVC, test | |
| INV-142 | Une restauration ne modifie jamais le mot de passe local, la licence, l'identifiant d'installation, les racines ni le dossier de travail | SVC, test | T-04, T-05, T-06 |
| INV-143 | Sauvegarde de sécurité avant restauration ; avant un changement de dossier, sauvegarde proposée dans l'ancien dossier, sans copie automatique | SVC | |
| INV-144 | Le JSON est un export, jamais un format de restauration V6 ; une sauvegarde JSON V2 n'est pas restaurable dans V6 : elle est une entrée du convertisseur externe, qui produit `import-v6.json` ; V6 ne lit jamais le format V2 | SVC | T-21 |
| INV-150 | Licence hors base métier ; vérification trimestrielle ; 15 jours de grâce ; ensuite consultation et exports seuls | SVC, test | |
| INV-151 | Secrets (clé de licence, jetons Gmail) dans le coffre système, jamais dans la base métier ; mot de passe local jamais en clair | SVC | |
| INV-152 | E-mails toujours manuels ; jamais de faux envoi | SVC | |
| INV-171 | Le compte local est créé obligatoirement au premier démarrage : `identifiant` unique non vide et mot de passe (`mot_de_passe_hash` argon2id, NOT NULL) ; `nom` et `prenom` facultatifs ; tant que le compte n'existe pas, seul l'écran de création est accessible | SQL (NOT NULL, UNIQUE, CHECK), SVC, test | T-25 |
| INV-172 | Le DDL de `machine.db` ne crée aucune ligne : les singletons `id=1` sont créés par le service d'initialisation avec `INSERT OR IGNORE` (jamais d'écrasement) ; préférences de sauvegarde par défaut : automatique activée, 30 minutes, sauvegarde à la fermeture activée, `derniere_sauvegarde_*` NULL ; `machine.db` ne contient aucun trigger | SVC, test | T-25 |

---

## Journal des retraits et modifications

| Date | INV | Changement | Motif | Décision |
|---|---|---|---|---|
| 2026-09-30 | INV-15 | Modifié : réarrondi à la migration remplacé par rejet de tout montant hors précision | V6 ne réarrondit plus ; l'arrondi V2 est fait par le convertisseur | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-20 | Modifié : format contrôlé sans exception sauf devis/factures/PV importés | exemptions d'origine supprimées | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-25 | Modifié : initialisation du high-water à l'import ajoutée | INV-135 remplacé | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-25 | Modifié (V3.7) : « high-water abaissé » au démarrage normal **supprimé** ; `max_attribue` ne diminue jamais, prochain numéro = `max_attribue` + 1, trou accepté et journalisé ; restauration : `max_attribue` relevé aussi | L'ancienne règle pouvait réattribuer un numéro déjà attribué avant un incident | Correction demandée par Rémy (D-27) |
| 2026-09-30 | INV-27 | Modifié : « numéros V2 jamais transformés » limité aux devis, factures, PV ; BC et codes clients au format V6 | D-01 et E-09 | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-54 | Modifié : exemption « migration » supprimée | aucune exemption | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-110 / INV-111 | Modifié : acteur et événement `migration` renommés `import` | vocabulaire de l'import | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-130 | Modifié : quarantaine et rapport de migration remplacés par `import_anomalies` (TR-90) | D-22 | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-131 | Modifié : principe général d'exemptions par `origine='migration'` supprimé ; reste une exemption unique (format du `numero` historique) | D-24 (validée 2026-09-30) | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-133 | Modifié : contrôle « reste dû V6 = reste dû V2 » remplacé par les totaux de contrôle du fichier ; `resteAPayer` V2 ne concerne plus V6 | le calcul du reste dû V2 est une règle du convertisseur | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-134 | Modifié : « la migration n'en crée aucune » remplacé par « le contrat n'accepte aucune garantie » ; NOT NULL sans exception | D-16, D-23 | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-135 | **Remplacé** — ancien énoncé : « Compteurs V2 jamais importés (incohérents, sans année) ; séquences V6 vides après migration » | Compteurs récupérés par le convertisseur et transmis dans `sequences` ; V6 initialise ses séquences ; saut acceptable, réutilisation interdite | D-26 (brief du 2026-09-30) |
| 2026-09-30 | INV-136 | Modifié : `migration_id` supprimé ; `origine` ∈ (`v6`,`import`) ; `legacy_*` NULL si `origine='v6'` | D-23 (validée 2026-09-30) | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-144 | **Réécrit** — ancien énoncé : « JSON = export, pas format de restauration ; l'import des sauvegardes V2 JSON reste possible via la migration (base vide uniquement) » | Le JSON V2 n'est pas un format de restauration V6 ; c'est une entrée du convertisseur | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-153 | Modifié : lecteur V2 tolérant remplacé par lecteur strict du contrat `import-v6.json` | V6 ne lit plus la V2 (D-25) | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-154 | Modifié : import V2 → import de `import-v6.json` | même règle, autre entrée | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-161 | Modifié : « profil URSSAF non créé par la migration » → « le contrat n'accepte aucune donnée URSSAF » ; la comparaison des taux V2 passe au convertisseur | périmètre V6/convertisseur | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-163 | Modifié : règle V2 (facture sans statut) → mécanisme `a_verifier` du contrat et bandeau V6 | la production de l'anomalie est une règle du convertisseur | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-165 | Modifié : avertissement/quarantaine → `a_verifier` / `non_importe` | D-22 | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-169, INV-170 | **Ajoutés** | Valeurs dérivées jamais lues du fichier ; séparation des tests convertisseur / V6 | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-132 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « Paiement unique V2 (`Reglee` + `datePaiement`) → un règlement `encaissement` (mode `autre`) ; `Reglee` sans date → quarantaine ; client déduit non présent en base → `a_rattacher` (rapprochement exact normalisé uniquement) ; `prestation_id` NULL si la référence est absente du catalogue importé » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-155 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « Catalogue V2 : réparation des colonnes décalées seulement si le motif est exact ; en-tête importé et préfixe inconnu → quarantaine ; unités normalisées (D-13) » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-156 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « Client déduit d'un devis V2 : clé nom+prénom normalisée, e-mails compatibles, sinon deux clients ; création en `a_rattacher` ; aucun fuzzy » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-157 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « BC reconstruit uniquement pour un devis `accepte` ; `date_acceptation` estimée (D-15) avec avertissement ; `nFacture`/`nAcompte`/`nBC` ne font que confirmer `refDevis` » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-158 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « Factures V2 : types `acompte`/`solde` seuls ; autre type ou statut non vide inconnu → quarantaine ; acompte = 1 ligne `synthese` ; solde = lignes `prestation` + 1 ligne `deduction` ; `montantHT` fait foi » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-159 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « Montants V2 : totaux recalculés selon les règles V6 pour les devis non acceptés ; factures reprises à `montantHT` ; fraction de centime → HALF_UP + original en `legacy_data` » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-160 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « PV V2 sans BC (`refDevis` absent ou devis non accepté) → quarantaine ; numéro V2 conservé » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | INV-162 | **Retiré** de V6, règle **transférée au convertisseur** — énoncé d'origine à reprendre : « Snapshot entreprise des documents importés reconstitué depuis `entreprise` V2, avertissement unique au rapport » | Règle de transformation purement V2, sans objet dans SQLite | Migration V2 externalisée (D-21, E-09) |
| 2026-09-30 | D-13 à D-19 (modèle §15) | Règles de transformation V2 transférées au convertisseur (unités, `date_acceptation` estimée, statut inconnu, facture sans statut, garanties non recréées) ; côté V6 : liste fermée des unités, aucune garantie importée, mécanisme `a_verifier` | Les décisions restent valides ; leur exécution change de composant | Migration V2 externalisée (D-21, E-09) |
| 2026-10-01 | INV-171, INV-172 | **Ajoutés** (V3.8) | Compte local obligatoire avec identifiant ; initialisation des singletons de `machine.db` par le service ; défauts de sauvegarde | D-28, D-29, D-30 (réponse de Rémy, 2026-10-01) |
| 2026-10-01 | INV-25, INV-106 | Confirmés : garde **SVC** (aucun trigger dans `machine.db`) | Les triggers proposés dans le premier jet de `machine/001_initial.sql` sont supprimés | D-30 |

## Contrôle de non-régression (à exécuter à chaque nouvelle version du modèle)

1. Extraire tous les `INV-xx` cités dans le modèle ; chacun doit exister ici.
2. Vérifier que chaque INV de ce registre est encore cité dans le modèle (sinon : ligne dans le journal).
3. Vérifier que chaque INV a un test nommé `test_INV_xx` dans la suite de tests SQL/domaine.
4. Rejouer les cas chiffrés C-01 à C-20.
5. Vérifier qu'aucun INV de la section L ne décrit un « lecteur V2 » dans V6 : toute règle V2 vit dans le document du convertisseur.
