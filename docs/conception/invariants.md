# BATORYA Essentiel V6 — Registre des invariants

Version du registre : 1 (rattaché au modèle SQLite V3.5)
Statut : **pièce obligatoire du modèle de données**

## Mode d'emploi

- Un invariant (**INV-xx**) est une règle métier ou technique déjà validée. Son numéro est **stable** : il n'est jamais réutilisé ni renuméroté. Les numéros absents de la séquence (trous entre sections) sont **réservés** : ils ne sont jamais attribués rétroactivement, une nouvelle règle reçoit le numéro suivant le plus élevé (INV-153, …).
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
| INV-15 | Migration : montant final à plus de 2 décimales → valeur V6 arrondie, valeur d'origine dans `legacy_data`, anomalie au rapport | SVC, CK | |

## C. Numérotation

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-20 | Formats V6 : `CLI-0001`, `FOU-0001`, `DEV|BCD|FAC|ACP|AVO|PVR|DEP-00001-yy`, levée `PVR-00001-yy-01` ; `yy` = année de la date métier ; contrôle de format seulement si `origine='v6'` | SQL | |
| INV-21 | Séquence unique par `(type_objet, annee)` ; `annee=0` pour CLI/FOU ; situation et solde partagent FAC ; ACP et AVO séparés | SQL | |
| INV-22 | Attribution atomique dans la transaction de création ; numéro jamais réattribué ; erreur explicite au plafond (99 999 / 9 999) ; `dernier_numero` ne diminue jamais | SVC, TRG (TR-95), SQL | T-20 |
| INV-23 | `numero` immuable ; l'année (yy) de la date de numérotation ne change jamais ; `date_creation` devis/BC immuable | TRG (TR-01) | |
| INV-24 | ACP, FAC, AVO : `date_emission` ≥ dernière date de la séquence (pas pour DEV, BCD, PVR, DEP) | TRG (TR-02) | |
| INV-25 | `sequence_high_water` (machine.db) : après restauration, séquence = max(restaurée, high-water) ; au démarrage normal, high-water > séquence = crash → high-water abaissé | SVC, test | C-18 |
| INV-26 | Suffixe PV de levée = max + 1 par PV d'origine, dans la transaction | TRG (TR-41), SQL | |
| INV-27 | Numéros historiques V2 conservés tels quels ; jamais transformés en numéros V6 | SVC, CK-01 | |

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
| INV-54 | `Σ facture_lignes.montant_ht = factures.total_ht` (exemption : migration) | SVC, CK-05 | C-08, T-19 |
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
| INV-110 | `historique` est append-only (aucun UPDATE/DELETE) ; gel, émission, règlement, annulation, remboursement, avoir, passage/retour de Terminé, garantie, rattachement, URSSAF, migration, restauration y sont tracés | TRG (TR-60), SVC | |
| INV-111 | `historique.type_entite` et `type_evenement` sont des énumérations fermées ; acteur `utilisateur`, `systeme` ou `migration` | SQL | |

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

## L. Migration

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-130 | Aucune donnée supprimée en silence ; rapport et quarantaine jamais supprimés ; sources jamais modifiées | TRG (TR-90), SVC | |
| INV-131 | Mode migration = exemptions conditionnées par `origine='migration'`, liste exhaustive (§10.3) ; unicités non exemptées ; écarts signalés par CK | SQL, TRG, CK | |
| INV-132 | Paiement unique V2 (`Reglee` + `datePaiement`) → un règlement `encaissement` (mode `autre`) ; `Reglee` sans date → quarantaine ; client déduit non présent en base → `a_rattacher` (rapprochement exact normalisé uniquement) ; `prestation_id` NULL si la référence est absente du catalogue importé | SVC, test | |
| INV-133 | Contrôle de fin de migration : reste dû V6 recalculé = reste dû V2 (0 si `Reglee`, sinon `montantHT`), écarts au rapport ; `resteAPayer` V2 jamais utilisé comme dette | CK-12 | T-16 |
| INV-134 | La V2 ne contient aucune garantie : la migration n'en crée aucune (D-16) ; le rapport liste les BC soldés concernés ; une garantie migrée éventuelle reste rattachée à un BC et jamais recalculée | SQL, SVC | |
| INV-135 | Compteurs V2 jamais importés (incohérents, sans année) ; séquences V6 vides après migration | SVC, CK-02 | |
| INV-136 | `origine='migration'` ⇔ `migration_id` renseigné ; `legacy_numero` seulement s'il diffère de `numero` | SQL | |
| INV-153 | Lecteur V2 tolérant : `data` et ses clés optionnels ; `version` `2.x` exigée ; clé inconnue conservée au rapport, jamais importée en silence | SVC, test | |
| INV-154 | Import V2 en deux temps (dry-run puis transaction unique, tout ou rien) et seulement sur base métier vide | SVC, test | |
| INV-155 | Catalogue V2 : réparation des colonnes décalées seulement si le motif est exact ; en-tête importé et préfixe inconnu → quarantaine ; unités normalisées (D-13) | SVC, test | |
| INV-156 | Client déduit d'un devis V2 : clé nom+prénom normalisée, e-mails compatibles, sinon deux clients ; création en `a_rattacher` ; aucun fuzzy | SVC, test | |
| INV-157 | BC reconstruit uniquement pour un devis `accepte` ; `date_acceptation` estimée (D-15) avec avertissement ; `nFacture`/`nAcompte`/`nBC` ne font que confirmer `refDevis` | SVC, test | |
| INV-158 | Factures V2 : types `acompte`/`solde` seuls ; autre type ou statut non vide inconnu → quarantaine ; acompte = 1 ligne `synthese` ; solde = lignes `prestation` + 1 ligne `deduction` ; `montantHT` fait foi | SVC, SQL | |
| INV-159 | Montants V2 : totaux recalculés selon les règles V6 pour les devis non acceptés ; factures reprises à `montantHT` ; fraction de centime → HALF_UP + original en `legacy_data` | SVC, CK-05 | |
| INV-160 | PV V2 sans BC (`refDevis` absent ou devis non accepté) → quarantaine ; numéro V2 conservé | SVC, test | |
| INV-161 | Profil URSSAF non créé par la migration ; taux V2 comparés au référentiel V6 (avertissement) ; aucune période calculée avant la saisie du profil | SVC | |
| INV-162 | Snapshot entreprise des documents importés reconstitué depuis `entreprise` V2, avertissement unique au rapport | SVC | |
| INV-163 | Facture V2 sans statut : importée non réglée, comptée dans facturation, reste dû et CA engagé, jamais dans CA encaissé ni URSSAF sans règlement saisi ; listée « À vérifier » et signalée par un bandeau du tableau de bord tant qu'elle n'est pas traitée (D-19) | SVC, CK-06, test | |
| INV-164 | Ordre de recalcul du service financier : factures actives → facturation nette → montant restant → avancement → état 100 % → `date_100_facture` → reste dû du solde → `termine`/`en_cours` → CA engagé ; jamais de cache intermédiaire incohérent | SVC, CK-06 | |
| INV-165 | Une anomalie informative est un avertissement au rapport de migration ; seule une donnée qui ne peut pas être représentée correctement part en quarantaine | SVC | |
| INV-166 | Le catalogue par défaut V6 exclut ELE-008 (prise RJ45 Cat6) ; un document historique qui la contient la conserve par snapshot, `prestation_id NULL` | SVC | |
| INV-167 | Les tests d'intégrité T-01 à T-20 (modèle §13.2) sont couverts avant le passage au DDL | test | T-01 à T-20 |

## M. Sauvegarde, restauration, licence

| INV | Énoncé | Garde | Cas |
|---|---|---|---|
| INV-140 | Sauvegarde par API Backup SQLite ou `VACUUM INTO`, jamais copie brute en WAL ; le fichier ne contient que la base métier | SVC, test | |
| INV-141 | Restauration : validation, `user_version` ≤ supporté (refus sinon), migrations sur copie, `integrity_check`, `foreign_key_check`, sauvegarde de sécurité, remplacement atomique, contrôles post-restauration | SVC, test | |
| INV-142 | Une restauration ne modifie jamais le mot de passe local, la licence, l'identifiant d'installation, les racines ni le dossier de travail | SVC, test | T-04, T-05, T-06 |
| INV-143 | Sauvegarde de sécurité avant restauration ; avant un changement de dossier, sauvegarde proposée dans l'ancien dossier, sans copie automatique | SVC | |
| INV-144 | JSON = export, pas format de restauration ; l'import des sauvegardes V2 JSON reste possible via la migration (base vide uniquement) | SVC | |
| INV-150 | Licence hors base métier ; vérification trimestrielle ; 15 jours de grâce ; ensuite consultation et exports seuls | SVC, test | |
| INV-151 | Secrets (clé de licence, jetons Gmail) dans le coffre système, jamais dans la base métier ; mot de passe local jamais en clair | SVC | |
| INV-152 | E-mails toujours manuels ; jamais de faux envoi | SVC | |

---

## Journal des retraits et modifications

| Date | INV | Changement | Motif | Décision |
|---|---|---|---|---|
| — | — | Aucun à ce jour | — | — |

## Contrôle de non-régression (à exécuter à chaque nouvelle version du modèle)

1. Extraire tous les `INV-xx` cités dans le modèle ; chacun doit exister ici.
2. Vérifier que chaque INV de ce registre est encore cité dans le modèle (sinon : ligne dans le journal).
3. Vérifier que chaque INV a un test nommé `test_INV_xx` dans la suite de tests SQL/domaine.
4. Rejouer les cas chiffrés C-01 à C-20.
