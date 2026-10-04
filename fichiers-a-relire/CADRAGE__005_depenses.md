# BATORYA Essentiel V6 — Cadrage de la tranche 005 « Dépenses » — version finale du 2026-10-04 (arbitrages complémentaires intégrés)

**Mise à jour 2026-10-04 (arbitrages complémentaires, derniers points ouverts levés)** : sont définitivement validés **TR-102** (trigger SQL inclus, point T-1), **DV-4 à DV-12** et **C-1**, en plus de DV-1 à DV-3 (versionnement des migrations, mécanisme d'annulation, annulation irréversible). **Il ne reste aucune décision métier à valider avant l'écriture du SQL** ; subsistent uniquement des **alignements documentaires** à effectuer ultérieurement (§6 et §9.2), qui ne sont pas des décisions. Le document suit le plan en neuf sections demandé (correspondance en tête de la section 1). La tranche 005 reste la tranche **métier Dépenses** (`005_depenses.sql`, rang 5) ; M-A et M-B sont des **correctives** (`005a`, `005b`, rangs 6 et 7) qui s'exécutent avant 006 et ne renumérotent aucune tranche.

**Statut** : cadrage **en relecture**, à valider avant toute écriture de `005_depenses.sql` et de `test_005_depenses.py`. Aucune migration, aucun test, aucun code, aucun trigger réel, aucun fichier officiel (`docs/**`), aucune convention, aucun modèle V3.13 et aucun CDC n'ont été créés ou modifiés par cette révision.
**Périmètre** : BATORYA **Essentiel** uniquement. Rien de BATORYA Entreprise, rien de Léon, rien des tranches 006 et suivantes.
**Base** : dépôt `mymypav-max/BATORYA-Essentiel`, migrations 001–004 et tests 001–004 **inchangés** ; copies de travail `MAJ__*` de `fichiers-a-relire/` (modèle SQLite **V3.13**, invariants INV-179 à INV-196, errata E-10 à E-20, décisions D-40 à D-55) comme référence documentaire de travail.
**Fichier** : cette version est la copie de travail `MAJ__CADRAGE__005_depenses.md` ; elle remplace la première version (`CADRAGE__005_depenses.md`, conservée telle quelle), dont le corps reposait sur des hypothèses caduques (§6).

**Classement utilisé partout** (colonne « Nature », exclusivement ces cinq valeurs) :

| Nature | Sens |
|---|---|
| **Règle documentée** | énoncée par un document V6 (CDC, errata, Métier, Modèle, invariants, audit de conservation validé) ou par une migration existante |
| **Décision validée** | décision explicite de Rémy (arbitrages du 2026-10-03 et du 2026-10-04), pas encore reportée dans les documents officiels ; elle **prévaut** sur un document antérieur qui la contredit, l'écart étant signalé (§6) |
| **Déduction technique** | conséquence SQL/SQLite ou de service d'une règle documentée ou d'une décision validée ; aucune règle métier nouvelle |
| **Proposition** | choix de conception de ma part, non décidé par le métier |
| **Décision restant à valider** | point que ni les sources ni les décisions ne tranchent ; **aucune règle n'est créée par déduction**. *À ce jour, aucune décision de cette nature ne subsiste dans ce cadrage.* |

**Hiérarchie respectée** : 1. décisions validées ; 2. invariants ; 3. modèle SQLite V6 ; 4. modèle métier V6 ; 5. CDC et conventions ; 6. déductions techniques clairement identifiées. Aucune décision validée n'est rouverte ; lorsqu'une source de rang inférieur ou égal la contredit ou la laisse incomplète, le point est signalé au §6 et non masqué.

Légende : « Modèle » = modèle SQLite V3.13 (copie de travail) ; « Métier » = modèle métier V6 ; « INV » = invariants ; « D-xx », « C-xx », « T-xx », « TR-xx », « CK-xx », « PT-xx » = identifiants du Modèle ; « Audit conservation » = `AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES` (D1 à D6, validées).

---

## 1. Cadrage métier de Dépenses

**Plan (correspondance avec les neuf sections demandées)** : 1 Cadrage métier · 2 Modèle de données proposé · 3 Relations et règles de rattachement · 4 Liste des invariants · 5 Répartition SQL / triggers / services / CK-13 · 6 Points ambigus ou contradictoires · 7 Structure de `005_depenses.sql` · 8 Structure de `test_005_depenses.py` · 9 Décisions nécessitant validation. Annexes : A tableau de synthèse, B recherche documentaire, C impact documentaire.

### 1.1 Finalité et périmètre

**Dépenses = suivi économique des achats et charges de l'activité et de leur impact sur les chantiers/BC, par rapport à ce qui a été vendu** (*Décision validée*, 2026-10-04 ; cohérent avec CDC §28 : « les dépenses servent aux analyses de gestion et de marge »).

Ce n'est **pas** : un module de facturation fournisseurs, de gestion d'échéances fournisseurs, de paiement fournisseurs, une comptabilité complète, ni un sous-module de TVA. Le périmètre n'est pas élargi : pas de date de facture, d'échéance ni de paiement ; pas de workflow ni de rapprochement de facture fournisseur ; pas de taux, montant de TVA ni TTC.

### 1.2 Synthèse de la tranche

| Sujet | Contenu de la tranche |
|---|---|
| Tables | **1** : `depenses` (catégories dans 001, fournisseurs dans 002, BC dans 004). **Aucune** table d'historique générique |
| Triggers | **3** : TR-01 (numéro et année immuables), TR-101 (garde de suppression, INV-06), TR-102 (dépense annulée totalement immuable) — **TR-102 : règle et trigger SQL validés** (§5), complétés par un contrôle de service. Aucun trigger inter-tables, aucun trigger sur les tables des tranches précédentes |
| Index | **4** (Modèle §9) : `bc_id`, `fournisseur_id`, `categorie_id`, `date_depense` |
| Dépense globale / rattachée | les deux existent ; le rattachement se corrige (changement de BC, détachement, rattachement ultérieur) tant que la dépense est active |
| BC annulé | une dépense peut y être **créée** et **rattachée ultérieurement** ; aucune règle des 30 jours ni confirmation sur un BC annulé |
| Annulation | `cancelled_at` + `motif_annulation`, **sans `statut`** ; **irréversible** ; dépense annulée **totalement immuable** (service + trigger TR-102) ; exclue des calculs actifs ; conservée et consultable |
| Fournisseur | **facultatif**, par identifiant, **sans statut ni archivage** (E-12, INV-183) ; modifiable sur une dépense active |
| Catégorie | obligatoire ; une catégorie **inactive** n'est pas sélectionnable pour une nouvelle dépense ni comme cible d'une correction ; le lien historique d'une dépense existante est conservé (service, aucune contrainte SQL inter-table) |
| Date | **une seule date métier** : `date_depense`, date métier attribuée à la dépense par l'utilisateur ; initialisée par défaut à la date du jour, mais pouvant être renseignée a posteriori ; distincte de `created_at` (donnée technique de création) ; aucune date de facture, d'échéance ni de paiement |
| Montant | un seul `montant`, **HT**, D2 (centime exact), strictement positif ; **aucune TVA** |
| Import | **aucun** : `depenses` et `fournisseurs` sont des blocs refusés de `import-v6.json` (Modèle §10.3, D-23) ; ni `origine`, ni `legacy_*` |
| Numérotation | `DEP-nnnnn-yy`, `yy` = année de `date_depense`, mécanisme **PT-1 tranché** ; aucun doublon > absence de trou ; numéro jamais réutilisé |
| Conservation | une dépense numérotée n'est **jamais supprimée** (INV-06, INV-193) ; garde DELETE en base |
| Contrôles CK | **aucun nouveau CK** ; CK-01, CK-02, CK-03 couvrent `depenses` ; CK-10 à étendre (libellé) ; CK-13 et CK-14 non concernés |
| Place dans la chaîne | `005_depenses.sql` = rang 5 ; `005a` (M-A) et `005b` (M-B) viennent après et avant 006 (DV-1) |

### 1.3 Décisions validées intégrées (arbitrage complémentaire du 2026-10-04)

| Réf. | Décision validée | Effet sur le cadrage |
|---|---|---|
| **TR-102** (T-1) | Une dépense annulée est **totalement immuable** : aucun UPDATE, y compris fournisseur, BC, rattachement/détachement, montant, date, motif d'annulation, `updated_at` et **toute autre colonne métier ou technique** de la ligne. Le **service** interdit ces modifications ; le **trigger SQL TR-102 est validé** comme barrière SQLite complémentaire. Objet, numéro DEP, données et rattachement conservés ; annulation irréversible. Aucun autre mécanisme d'historisation spécifique | §5.2 (règle / service / trigger) ; INV-197 proposé |
| **DV-4** | Une dépense annulée est conservée physiquement mais **exclue des calculs métier actifs** : totaux de dépenses, marges, analyses économiques, indicateurs actifs ; elle reste consultable dans l'historique ; ce n'est pas une suppression | aucun SQL ; filtre des requêtes d'analyse (service) ; INV-200 proposé |
| **DV-5** | Une dépense **active** peut être corrigée, notamment : fournisseur, détachement d'un BC, rattachement à un BC, changement de BC, passage globale ↔ rattachée. Toute nouvelle opération de rattachement est contrôlée **selon les règles applicables au moment de l'opération** ; un déplacement BC → BC est permis si les règles du nouveau BC sont respectées | §3 ; INV-198 proposé |
| **DV-6** | Une dépense peut être **créée directement** avec un BC annulé et **rattachée ultérieurement** à un BC annulé (achats anticipés avant l'annulation du client). Le BC annulé reste un conteneur historique et économique ; « annulé » n'est pas une interdiction absolue | §3 ; étend D5/INV-188 (§6, C-R) |
| **DV-7** | La règle des 30 jours après `date_100_facture` concerne les **BC non annulés** (rattachement normal jusqu'à 30 jours calendaires, confirmation explicite au-delà, aucun délai maximal). **BC annulé : aucun délai, aucune confirmation tardive**. Exception **spécifique aux BC annulés**, à documenter comme telle ; règle de **service**, jamais un CHECK | §3 ; INV-199 proposé ; modifie la portée d'INV-103 (§6, C-S) |
| **DV-8** + **DV-12** | Le module n'est pas un suivi de facturation fournisseurs : **une seule date métier `date_depense`** = date métier attribuée à la dépense par l'utilisateur ; initialisée par défaut à la date du jour, mais pouvant être renseignée a posteriori. Elle n'est **pas** définie comme « la date à laquelle la dépense est saisie ». `created_at` est la donnée technique de création, jamais une seconde date métier. Pas de `date_facture`. La numérotation annuelle utilise la date métier. Une fois le numéro DEP attribué, il n'est jamais réutilisé ni rendu incohérent avec son année : si une correction exigeait une autre année, on **n'écrit pas** le numéro de nouveau ; on applique les règles générales de conservation/correction (annulation puis nouvel objet) ; **aucune procédure de renumérotation** | §1.5.7 ; INV-201 proposé |
| **DV-11** | Une catégorie **inactive** n'est pas sélectionnable pour une **nouvelle** dépense. Dépense existante : si sa catégorie devient inactive, le **lien historique est conservé**, la dépense reste consultable, **aucune modification automatique** ; lors d'un changement vers une autre catégorie, la **catégorie cible doit être active**. Règle de **service** ; aucune contrainte SQL inter-table (convention : un contrôle qui compare plusieurs tables n'est jamais un CHECK ni un trigger de miroir) | §1.5.4 ; §5.1 |
| **C-1** | **Aucune confirmation des 30 jours** si le BC reste identique : la règle concerne le **rattachement** à un BC, pas toute modification d'une dépense. BC A → BC B : règles du BC B évaluées ; globale → BC : règles du BC cible évaluées ; BC → globale : détachement autorisé pour une dépense active | §1.5.3 ; §3.2 |
| **DV-9** | Un seul `montant`, **HT**, précision au centime, strictement positif ; aucun taux, montant de TVA ni TTC ; aucun calcul fiscal ; montants exacts, aucun flottant | §2 ; libellé « HT » à aligner (§6, C-Q) |
| **DV-10** | La traçabilité repose sur les **données propres de la dépense** : numéro DEP, date, fournisseur, BC éventuel, montant, `created_at`/`updated_at`, `cancelled_at`, `motif_annulation`. Une dépense annulée reste présente. **Aucune** table générique d'historique, **aucune** architecture de journalisation propre aux dépenses | §2, §5 ; l'événement d'historique éventuel relève du mécanisme V6 existant (`historique`, PT-15), hors 005 |
| DV-1 à DV-3 | Voir §9.1 (tranchées le matin du 2026-10-04) : place de 005 dans la chaîne (rang 5, `005a`/`005b` après), `cancelled_at` + `motif_annulation` sans `statut`, annulation irréversible | §7, §9 |

### 1.4 Règles documentées et décidées (base de la tranche)

| # | Règle | Nature | Source |
|---|---|---|---|
| R1 | Une dépense est une charge enregistrée, pour l'analyse de gestion et de marge ; elle ne réduit **jamais** le CA URSSAF | Règle documentée | CDC §28 ; Métier §17, §18 ; INV-100, INV-120 |
| R2 | Une dépense est **globale** (sans BC) ou **rattachée à un BC** | Règle documentée | CDC §28 ; Métier §18 ; Modèle §4.12 |
| R3 | Fournisseur **facultatif** (« lorsque nécessaire »), référencé **par identifiant** | Règle documentée | CDC §28 ; Métier §18, §19 ; INV-100 |
| R4 | Aucune gestion du paiement : ni statut payé/non payé, ni échéance, ni règlement fournisseur, ni dépenses à payer | Règle documentée | CDC §28 (hors périmètre) ; Métier §18 ; INV-100 |
| R5 | `montant` : « montant réellement payé », franchise de TVA, 2 décimales exactes (D2), jamais `0.00`, jamais négatif ; **libellé « HT » imposé par la décision DV-9 (R29)** : voir §6, C-Q | Règle documentée | Métier §2.1, §18 ; Modèle §2.3, §4.12 ; INV-11, INV-14 |
| R6 | **Plus de fournisseur archivé** : tout fournisseur reste sélectionnable pour une nouvelle dépense | Règle documentée | Métier §17, §19 ; E-12 ; INV-100, INV-183 |
| R7 | Un fournisseur est **conservé définitivement** : code immuable, aucune suppression, aucun archivage ni statut | Règle documentée | INV-183 ; Métier §19 ; D-43 |
| R8 | **Règle des 30 jours (pour un BC non annulé ; exception BC annulé : R27)** : à compter de `date_100_facture`, rattachement normal pendant 30 jours calendaires ; ensuite **confirmation simple** (« clôturé depuis X jours », X = jours écoulés − 30, C-22 : 45 jours → 15) ; ni déblocage, ni délai maximal ; **règle de service, aucun trigger** | Règle documentée | CDC §15 ; Métier §17 ; Modèle §4.12 (`date_du_jour > date_100_facture + 30 jours`), D-31, C-21, C-22 ; INV-103 |
| R9 | La clôture des dépenses n'affecte ni le statut financier du BC, ni son historique, ni les dépenses déjà rattachées ; le BC n'expose que `date_100_facture` | Règle documentée | Modèle §3.5 |
| R10 | Numéro `DEP-00001-yy`, séquence `DEP`, `yy` = année de **`date_depense`** ; **jamais attribué deux fois** ; trou accepté et jamais récupéré ; plafond 99 999 ; pas de chronologie continue (TR-02 ne concerne pas DEP) | Règle documentée | Modèle §6 ; Métier §2.2 ; INV-20, INV-22, INV-24, INV-179 ; D-54 |
| R11 | `numero` immuable ; `date_depense` modifiable **tant que l'année (yy) ne change pas** ; sinon : annulation puis nouvelle saisie (le numéro n'est jamais réécrit ni rendu incohérent avec son année ; **aucune procédure de renumérotation**) | Règle documentée | Modèle §4.12, §6, §8 (TR-01) ; INV-23 |
| R12 | Borne d'année **2001–2099** de `date_depense` : contrôle du **service**, jamais un CHECK | Règle documentée | INV-177 ; D-38 |
| R13 | Catégorie obligatoire (liste de référence modifiable : ordre, **état actif**) | Règle documentée | Modèle §4.3, §4.12 ; D-12, D-18 ; Métier §4.2 |
| R14 | Pièce jointe facultative : `piece_jointe_chemin` et `piece_jointe_racine_id`, « les deux ou aucun » ; chemins relatifs à une racine identifiée | Règle documentée | Modèle §4.12 ; INV-106 |
| R15 | `description` obligatoire ; `notes` facultatif ; dates de création et de modification | Règle documentée | Modèle §4.12 ; Métier §18 |
| R16 | Une dépense **corrigeable** pour erreur de saisie, **annulable** lorsqu'elle ne doit plus participer aux calculs ; une dépense annulée reste en base avec numéro, historique et relations, exclue des totaux et calculs opérationnels concernés (liste générale : DV-4, R24) ; **aucune suppression d'une dépense numérotée** | Règle documentée | E-19 ; INV-193 ; INV-06 ; D-50 ; Audit conservation D5 ; Métier §2.4, §18 |
| R17 | **Une dépense peut être créée sur un BC annulé et y rester liée** (création et maintien du lien ; le rattachement ultérieur est étendu par R26) | Règle documentée | Audit conservation D5, §7.1 n°4 ; INV-188, INV-100, INV-193 ; Métier §18 ; CDC §28 (E-19) |
| R18 | `depenses` **n'est pas importable** (bloc refusé de `import-v6.json`) | Règle documentée | Modèle §10.3 ; D-23 ; en-tête de `002_fournisseurs.sql` |
| R19 | FK en `RESTRICT` par défaut, jamais de `ON UPDATE`, `id` AUTOINCREMENT, tables `STRICT`, `recursive_triggers=ON`, `INSERT OR REPLACE` interdit par convention | Règle documentée | Modèle §1, §2.1 ; INV-04, INV-05, INV-07 ; D-39 |
| R20 | Index `depenses(bc_id)`, `(fournisseur_id)`, `(categorie_id)`, `(date_depense)` | Règle documentée | Modèle §9 |
| R21 | TR-01 couvre explicitement les dépenses (« `numero` immuable ; année de la date de numérotation immuable ») | Règle documentée | Modèle §8 |
| R22 | L'annulation d'un objet annulable est tracée (« date et motif ») ; l'annulation d'une dépense est un événement tracé de l'historique **par le mécanisme V6 existant** (aucune journalisation propre aux dépenses : R30) | Règle documentée | Métier §2.4, §26 (événements tracés) ; INV-110, INV-194 |
| R23 | **Dépense annulée = totalement immuable** : aucun UPDATE — ni fournisseur, BC, rattachement/détachement, montant, date, motif, `updated_at`, ni **aucune autre colonne métier ou technique** ; interdit par le **service** et par le **trigger TR-102** ; numéro DEP, données et rattachement conservés ; **annulation irréversible**, aucune réactivation ; une nouvelle saisie est un nouvel objet avec un nouveau numéro | **Décision validée** (TR-102 / T-1, DV-3, 2026-10-04) | Arbitrage Dépenses ; INV-179 |
| R24 | Une dépense annulée est **exclue des calculs métier actifs** (totaux de dépenses, marges, analyses économiques, indicateurs actifs), **conservée physiquement** et **consultable dans l'historique** ; ce n'est pas une suppression | **Décision validée** (DV-4) | Arbitrage Dépenses ; INV-193 |
| R25 | Une dépense **active** peut être corrigée, notamment : fournisseur, détachement, rattachement, changement de BC, globale ↔ rattachée ; tout **nouveau rattachement** est contrôlé selon les règles applicables **au moment de l'opération** ; BC → BC permis si les règles du nouveau BC sont respectées | **Décision validée** (DV-5) | Arbitrage Dépenses |
| R26 | Une dépense peut être **créée directement avec un BC annulé** et **rattachée ultérieurement à un BC annulé** (achats anticipés avant l'annulation du client) ; le BC annulé reste un conteneur historique et économique | **Décision validée** (DV-6) | Arbitrage Dépenses ; étend R17 |
| R27 | La règle des 30 jours ne vise que les **BC non annulés** ; pour un **BC annulé** : aucun délai, aucune confirmation tardive, rattachement sans cette restriction (**exception métier spécifique aux BC annulés**) ; règle de service | **Décision validée** (DV-7) | Arbitrage Dépenses ; limite R8, INV-103 |
| R28 | **Une seule date métier** : `date_depense` = date métier attribuée à la dépense par l'utilisateur ; initialisée par défaut à la date du jour, mais pouvant être renseignée a posteriori ; **distincte de `created_at`** (donnée technique de création) ; ni `date_facture`, ni échéance, ni date de paiement | **Décision validée** (DV-8, DV-12) | Arbitrage Dépenses |
| R29 | `montant` : **un seul**, **HT**, au centime, strictement positif ; aucun taux/montant de TVA, aucun TTC, aucun calcul fiscal ; décimal exact, jamais de flottant | **Décision validée** (DV-9) ; Règle documentée (D2, INV-11, INV-14) | Arbitrage Dépenses ; Modèle §4.12 |
| R30 | **Traçabilité** par les données propres de la dépense (numéro, date, fournisseur, BC, montant, `created_at`/`updated_at`, `cancelled_at`, `motif_annulation`) ; dépense annulée présente ; **aucune table générique d'historique, aucune journalisation spécifique aux dépenses** | **Décision validée** (DV-10) | Arbitrage Dépenses ; INV-110, INV-194 (mécanisme V6, hors 005) |
| R31 | **Catégorie inactive** : non sélectionnable pour une nouvelle dépense ; pour une dépense existante, lien historique conservé, dépense consultable, aucune modification automatique ; changement de catégorie ⇒ catégorie cible active ; règle de service, aucune contrainte SQL inter-table | **Décision validée** (DV-11) | Arbitrage Dépenses ; conventions §9 |
| R32 | **Modification sans changement de BC** : aucune vérification du délai de rattachement ; la règle des 30 jours ne concerne que le rattachement (BC A → BC B, globale → BC) | **Décision validée** (C-1) | Arbitrage Dépenses ; INV-103 |

### 1.5 Revue thématique

#### 1.5.1 Dépense globale et dépense rattachée à un BC

| Question | Conclusion | Nature | Source |
|---|---|---|---|
| Dépense **globale** (`bc_id` NULL) | autorisée ; numéro identique (DEP) ; aucune règle propre : la règle des 30 jours porte sur le rattachement à un BC | Règle documentée | R2, R8 ; INV-103 |
| Dépense **rattachée à un BC** (`bc_id` renseigné) | autorisée, y compris à un BC annulé (R26) ; relation facultative, `ON DELETE RESTRICT` | Règle documentée ; Décision validée (BC annulé) | R2, R26 ; §3 |
| Passer de globale à rattachée, de rattachée à globale, changer de BC | **permis** pour une dépense **active** ; chaque nouveau rattachement est contrôlé au moment de l'opération | Décision validée | R25 (DV-5) |
| Prise en compte dans les analyses (globales ou par BC) | analyses calculées, jamais stockées, **hors tranche** ; une dépense **active** y entre, une dépense **annulée** non (R24). *Le détail de chaque indicateur relève des analyses (Métier §17), pas de 005* | Décision validée (principe) ; Déduction technique | R24 |

#### 1.5.2 BC annulé

Les cas sont désormais tranchés ; il ne reste ni « sans règle » ni option ouverte. Le BC annulé reste un **conteneur historique et économique** : « annulé » n'est pas interprété comme une interdiction absolue de rattachement de dépenses (R26).

| Question | Conclusion | Nature | Source |
|---|---|---|---|
| Créer une **nouvelle** dépense avec un BC annulé | **autorisé** | Règle documentée ; Décision validée | Audit conservation D5 ; INV-188 ; R26 |
| Rattacher une dépense **existante** (globale ou d'un autre BC) à un BC **déjà annulé** | **autorisé** (achats anticipés avant l'annulation du client) | **Décision validée** | R26 (DV-6) |
| Une dépense déjà rattachée quand le BC **devient** annulé | reste rattachée ; l'annulation du BC ne modifie aucune dépense (aucun trigger de 001–004 ne touche `depenses` ; pas de cascade) | Règle documentée ; Déduction technique | INV-188, INV-193 ; 004 |
| Une dépense **annulée** peut rester liée à un BC annulé | oui (et elle est immuable : elle ne peut plus être détachée ni déplacée) | Règle documentée ; Décision validée (immutabilité) | INV-193 ; R23 |
| Détacher une dépense **active** d'un BC annulé, ou la déplacer vers un autre BC | **permis** (règles du BC cible respectées) | **Décision validée** | R25 |
| Modifier (montant, description, catégorie…) une dépense **active** liée à un BC annulé | aucune restriction (INV-173 ne gèle que les données commerciales du **BC**) | Déduction technique | INV-173 ; R25 |
| **30 jours** sur un BC annulé | **aucun délai, aucune confirmation**, même si `date_100_facture` est non NULL (annulation avec solde actif possible, E-15) | **Décision validée** | R27 (DV-7) |

**Correction conservée d'une erreur de la première version** : « un BC annulé a en principe `date_100_facture` NULL (annulation avec solde actif interdite, D-05 / INV-44) » est faux ; D-05 est **remplacée** (D-46, E-15). Le point est sans conséquence depuis DV-7 : le BC annulé est exempté quelle que soit `date_100_facture`.

#### 1.5.3 Règle des 30 jours (BC non annulé)

| Sujet | Conclusion | Nature | Source |
|---|---|---|---|
| Portée | **BC non annulés** uniquement ; BC annulé : exception (1.5.2) | Décision validée | R27 |
| Rattachement normal | jusqu'à **30 jours calendaires** après `date_100_facture` | Règle documentée | R8 ; C-21 |
| Au-delà | **confirmation explicite** (« clôturé depuis X jours », X = jours écoulés − 30, C-22 : 45 jours → 15) | Règle documentée | R8 ; C-22 |
| Délai maximal | **aucun** ; une confirmation positive permet le rattachement sans limite | Règle documentée | INV-103 |
| Point de départ | `date_100_facture` du BC comparée au **jour courant local** à la date de l'opération (pas à `date_depense`) | Règle documentée | R8 ; Modèle §2.2 |
| Nature de la règle | **règle de service**, jamais un CHECK, jamais un trigger | Décision validée ; Règle documentée | R27 ; INV-103 (SVC) |
| Opérations visées | création avec BC ; rattachement ultérieur ; **changement de BC** (contrôle sur le **BC cible** seulement, au moment de l'opération) | Décision validée | R25 |
| Modification d'une dépense déjà rattachée **sans changer de BC** (montant, description…) | ce n'est pas un nouveau rattachement : **aucune confirmation, aucune nouvelle vérification du délai** (exemple : dépense au BC A, montant modifié, BC A inchangé) | **Décision validée** (C-1) | R32 ; INV-103 (« nouveau rattachement ») |
| `termine`, « gelé » | `termine` : même règle (c'est `date_100_facture` qui compte) ; « gelé » : aucun effet | Déduction technique | D-31 ; 004 ; PT-8 |

#### 1.5.4 Modification d'une dépense active

| Question | Conclusion | Nature | Source |
|---|---|---|---|
| Principe | une dépense **active** est corrigeable (erreur de saisie) | Règle documentée | R16 ; INV-193 |
| Fournisseur | modifiable : changer, retirer (`NULL`), ajouter | **Décision validée** | R25 |
| BC | rattacher, détacher, changer ; globale ↔ rattachée ; contrôle au moment de l'opération | **Décision validée** | R25 |
| Montant, description, catégorie, notes, pièce jointe | modifiables : aucune restriction documentée, la liste de DV-5 est donnée « notamment » | Déduction technique | R25 ; Modèle §4.12 |
| `date_depense` | modifiable **tant que l'année (yy) ne change pas** ; sinon : annulation puis nouvelle saisie ; le sens de la date : 1.5.7 | Règle documentée | R11 ; INV-23 |
| `numero` | **immuable** (TR-01) | Règle documentée | INV-23 |
| Catégorie inactive | **non sélectionnable** pour une nouvelle dépense ; dépense existante dont la catégorie devient inactive : lien conservé, dépense consultable, aucune modification automatique ; changement de catégorie : la **catégorie cible doit être active** | **Décision validée** (DV-11) ; contrôle de **service** | R31 ; conventions §9 (aucun CHECK ni trigger inter-tables) |
| Dépense **annulée** | aucune modification (1.5.5) | Décision validée | R23 |

#### 1.5.5 Annulation, immutabilité et exclusion des calculs

| Sujet | Conclusion | Nature | Source |
|---|---|---|---|
| Mécanisme | `cancelled_at` + `motif_annulation`, annulation ⇔ `cancelled_at IS NOT NULL` ; **pas de `statut`** ; UTC millisecondes ; motif obligatoire et non vide ; deux colonnes cohérentes (toutes deux NULL ou toutes deux renseignées) | Décision validée | DV-2 ; même logique que les règlements (INV-70) |
| Irréversibilité | annulation **irréversible**, aucune réactivation | Décision validée | R23 (DV-3 option A) |
| Immutabilité totale | après annulation : aucun UPDATE métier, **y compris** fournisseur, BC, détachement, rattachement, montant, date, motif et `updated_at` isolé ; l'objet, son numéro DEP, ses données et son rattachement sont conservés | **Décision validée** | R23 (TR-102) |
| Trois niveaux | règle métier (R23) ; contrôle de service (refus explicite) ; trigger SQL **TR-102** | voir §5 | §5 |
| Nouvelle saisie après annulation | **nouvel objet**, **nouveau numéro** (INV-179 : un numéro n'est jamais attribué deux fois) ; trou accepté | Règle documentée | R11, INV-179 |
| Exclusion des calculs actifs | totaux de dépenses, marges, analyses économiques, indicateurs actifs ; **filtre `cancelled_at IS NULL`** des requêtes d'analyse | Décision validée (principe) ; Déduction technique (filtre) | R24 (DV-4) |
| Conservation et consultation | la dépense annulée reste en base et **consultable dans l'historique** (liste des dépenses avec leur annulation) | Décision validée | R24 |
| Totaux stockés | **aucun** (aucune colonne de cache sur `bons_commande`) : la règle d'exclusion ne produit donc aucun SQL | Déduction technique | Modèle §4.12 |
| Suppression physique | **jamais** | Règle documentée | INV-06, INV-193 |
| Archivage | n'existe pas pour une dépense (l'annulation en tient lieu) | Déduction technique | INV-183 |
| Annulation d'une dépense **déjà annulée** | refusée (l'annulation est une opération unique) | Déduction technique | R23 |
| Dépense créée **déjà annulée** | non prévue : une dépense naît active ; contrôle au **service** (aucun trigger `BEFORE INSERT` proposé) | Proposition | R23 |

#### 1.5.6 Fournisseur

| Question | Conclusion | Nature | Source |
|---|---|---|---|
| Obligatoire ? | **Non** : `fournisseur_id` NULL admis | Règle documentée | R3 |
| Utilisable pour une dépense | **tout fournisseur existant** ; ni archive, ni statut, ni réactivation | Règle documentée | R6, R7 ; E-12 ; INV-183 |
| Changer ou retirer le fournisseur d'une dépense active | **autorisé** | **Décision validée** | R25 |
| Dépense annulée | fournisseur figé (R23) | Décision validée | R23 |
| Modification des données du fournisseur | autorisée ; la dépense référence l'identifiant et présente les données **courantes** (aucune copie du nom) | Règle documentée ; Déduction technique | INV-183, INV-100 |
| Suppression physique du fournisseur | **interdite** ; garde SQL côté dépenses : FK `RESTRICT` ; la garde sur `fournisseurs` (TR-97, PT-4) relève de la corrective M-A, pas de 005 | Règle documentée ; Proposition (PT-4, hors 005) | INV-183, INV-05 |

**Contradiction avec la migration 002 (immuable)** : `fournisseurs.statut` (`actif`/`archive`, NOT NULL) existe encore. Il disparaîtra par la corrective M-A (`005a`, PT-3, contenu en proposition) : suppression de l'index `idx_fournisseurs_statut` puis de la colonne, **sans reconstruction de `fournisseurs`**. **Conséquence pour 005** : le DDL, les triggers et les tests de `depenses` ne lisent, ne testent et ne présupposent **jamais** `fournisseurs.statut` (les fixtures fournissent la valeur imposée par 002 sans la commenter).

#### 1.5.7 Date métier unique

| Notion | Conclusion | Nature | Source |
|---|---|---|---|
| `date_depense` | **seule date métier** de la dépense : date métier attribuée à la dépense par l'utilisateur ; initialisée par défaut à la date du jour, mais pouvant être renseignée a posteriori ; date réelle `YYYY-MM-DD` (`GLOB` + `date(x) IS x`), NOT NULL ; borne 2001–2099 au **service** | Décision validée (sens, DV-8 et DV-12) ; Règle documentée (format, borne) | R28 ; INV-10, INV-177 |
| Année du numéro | année de `date_depense` | Règle documentée | R10 ; Métier §2.2 |
| Date de facture fournisseur | **aucune colonne** (à ne pas confondre avec `date_100_facture`, colonne du BC) | Décision validée | R28 |
| Échéance, date de paiement | **exclues** | Règle documentée ; Décision validée | R4, R28 |
| `created_at` / `updated_at` | **données techniques** (création et modification de la ligne, TS UTC) : jamais des dates métier ; `date_depense` n'est **pas** « la date de saisie » et n'est jamais déduite d'un timestamp | Règle documentée ; Décision validée | Modèle §2.2 ; INV-10 ; R28 |
| Date d'annulation | `cancelled_at` (TS UTC, millisecondes) | Décision validée | DV-2 |
| Cohérence `date_depense` ↔ dates du BC | aucune règle ⇒ **aucun contrôle** en 005 | Déduction technique | R28 |
| Point de départ des 30 jours | `date_100_facture` du BC, pas `date_depense` | Règle documentée | R8 |
| Saisie **a posteriori** | **autorisée** : la date est proposée par défaut (jour courant, local) et l'utilisateur peut la renseigner a posteriori ; la correction ultérieure suit R11 (même année) | **Décision validée** (DV-12) | R28, R11 |
| Numéro DEP et année | l'année du numéro est celle de `date_depense` à l'attribution ; le numéro n'est **jamais réutilisé ni rendu incohérent** avec son année (TR-01 + CHECK) ; si une correction exigeait une autre année : **annulation puis nouvel objet**, sans renumérotation | Règle documentée ; Décision validée | R10, R11 ; INV-23, INV-179 |

#### 1.5.8 Montant HT, sans TVA

| Sujet | Conclusion | Nature | Source |
|---|---|---|---|
| Colonne | **une seule** : `montant`, D2, TEXT canonique ; aucun `REAL` | Règle documentée | R5 ; INV-11 |
| Base | exprimé en **HT** ; aucun taux, aucun montant de TVA, aucun TTC, aucune ventilation, aucun workflow ni calcul fiscal | **Décision validée** | R29 (DV-9) |
| Positif | `0.00` refusé ; négatif refusé (les négatifs autorisés par INV-14 excluent les dépenses) | Règle documentée | Modèle §4.12 ; INV-14 |
| Précision | 2 décimales saisies, conservées exactes ; aucun calcul ni arrondi à l'écriture | Déduction technique | INV-11 |
| Sommes (totaux, marges) | calculées par le service, **hors tranche**, en centimes entiers, jamais en flottant | Déduction technique | INV-11 ; Métier §17 |
| Avoir fournisseur, remboursement reçu | **non représentables** : limite connue, confirmée par « strictement positif » | Décision validée | R29 |
| Modèles de TVA d'autres domaines (factures, devis) | **non recopiés** | Décision validée | R29 |
| Libellé | les documents disent « montant réellement payé (franchise de TVA) » ; la décision dit « HT » : alignement des libellés à faire | voir §6 | §6, C-Q |

#### 1.5.9 Cycle de vie

| Étape | Conclusion | Nature | Source |
|---|---|---|---|
| Création | une dépense naît **numérotée et active** ; aucun brouillon, aucune validation, aucun statut | Déduction technique | INV-180/185 ; INV-100 |
| Correction | autorisée tant que la dépense est active (1.5.4) | Règle documentée ; Décision validée | R16, R25 |
| Annulation | opération unique, motif obligatoire, irréversible (1.5.5) | Décision validée | R23 |
| Après annulation | immuable, conservée, exclue des calculs actifs, consultable | Décision validée | R23, R24 |
| Suppression | jamais | Règle documentée | INV-06 |

Conséquences de l'absence de statut : **conservation** — rien ne peut disparaître (garde DELETE, annulation non destructrice) ; **correction** — une erreur courante se corrige par modification ; une erreur d'**année** ou une dépense à ne plus compter se règle par **annulation puis nouvelle saisie** (R11), ce qui consomme un numéro (trou accepté, jamais réutilisé).

#### 1.5.10 Numérotation `DEP-nnnnn-yy` (cohérence avec PT-1)

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

#### 1.5.11 Import V6 (confirmé : aucun import de dépenses)

| Sujet | Conclusion | Nature | Source |
|---|---|---|---|
| Blocs `depenses` et `fournisseurs` dans `import-v6.json` | **refusés** (« La V2 ne les fournit pas » ; ouvrir un bloc = nouvelle `contrat_version`) | Règle documentée | Modèle §10.3 ; D-23 ; en-tête de 002 |
| BLOC-IMP sur `depenses` | **retiré** : aucun `origine`, aucun `legacy_id`, aucun `legacy_data`, aucun `legacy_numero` | Règle documentée | D-23 |
| `import_anomalies` pour des dépenses | aucune | Déduction technique | §10.3 |
| Numéros DEP importés | sans objet | Déduction technique | §10.3 |
| Convertisseur V2 → V6 | **hors périmètre** de la tranche | Règle documentée | périmètre du brief |
| Format d'import de dépenses | **aucun n'est proposé** ; les dépenses sont **hors import** (règle documentaire confirmée : aucune décision contraire dans l'arbitrage du 2026-10-04) | Règle documentée | D-23 ; Modèle §10.3 |

Note technique (sans conséquence tant que l'import reste exclu) : introduire plus tard `origine`/`legacy_*` avec leurs CHECK de table obligerait à reconstruire `depenses` (SQLite ne permet pas d'ajouter un CHECK de table par `ALTER`) et exigerait aussi un bloc `fournisseurs` — **Déduction technique**.

#### 1.5.12 Conservation définitive des dépenses numérotées

| Principe validé | Application à la dépense | Nature | Source |
|---|---|---|---|
| Un objet à numéro définitif n'est pas supprimé physiquement | une dépense est numérotée dès sa création : **jamais supprimée**, annulée ou non | Règle documentée | INV-06, INV-193 ; Audit conservation D1, D5 |
| Le numéro n'est jamais réutilisé | séquence + high-water + `UNIQUE` ; l'annulation ne libère rien | Règle documentée | INV-06, INV-22, INV-179 |
| L'annulation conserve l'objet | `cancelled_at` / `motif_annulation`, relations (BC, fournisseur, catégorie) et pièce jointe non supprimées ; la dépense annulée est de plus **immuable** (R23) ; le fichier de la pièce jointe est conservé | Règle documentée (objet, relations) ; Décision validée (immutabilité) ; Déduction technique (fichier) | INV-193 ; R23 |
| Suppression seulement des objets non définitifs | aucune dépense n'est « non définitive » | Déduction technique | INV-06 |
| Contournement par `INSERT OR REPLACE` | refusé **par la garde DELETE** avec `recursive_triggers=ON` ; **non protégé** si le réglage est OFF (convention INV-07) — constaté sur prototype (SQLite 3.45.1) : DELETE refusé dans les deux cas, REPLACE refusé seulement avec ON | Déduction technique | INV-07 ; Modèle §1, §4.19 |

La première version (A-4) constatait qu'un REPLACE contournait TR-01 faute de garde DELETE ; **la garde DELETE, désormais exigée par INV-06, supprime ce contournement** (réglage actif).

---
## 2. Modèle de données proposé (esquisse, non destinée à être copiée telle quelle)

| Colonne | Type | Contraintes | Nature | Source |
|---|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | Règle documentée | INV-04 |
| `numero` | TEXT | NOT NULL UNIQUE ; `GLOB 'DEP-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'` | Règle documentée | INV-20, R10 |
| `fournisseur_id` | INTEGER | NULL ; FK → `fournisseurs(id)` ON DELETE RESTRICT | Règle documentée | R3 |
| `bc_id` | INTEGER | NULL ; FK → `bons_commande(id)` ON DELETE RESTRICT | Règle documentée | R2 |
| `date_depense` | TEXT (D) | NOT NULL ; `GLOB` aaaa-mm-jj et `date(x) IS x` ; **aucune borne d'année** ; **seule date métier** (attribuée par l'utilisateur, défaut = jour, a posteriori possible ; distincte de `created_at`) | Règle documentée (format) ; Décision validée (sens, DV-8, DV-12) | INV-10, INV-177, R28 |
| `montant` | TEXT (D2) | NOT NULL ; motif D2 ; `<> '0.00'` ; **HT**, un seul montant | Règle documentée (D2) ; Décision validée (HT, DV-9) | R5, R29 |
| `categorie_id` | INTEGER | NOT NULL ; FK → `categories_depenses(id)` ON DELETE RESTRICT | Règle documentée | R13 |
| `description` | TEXT | NOT NULL ; `<> ''` (le non-vide : convention de nommage des autres tables) | Règle documentée (NOT NULL) ; Déduction technique (`<> ''`) | R15 |
| `piece_jointe_chemin` | TEXT | NULL ; si présent `<> ''` | Règle documentée | R14 |
| `piece_jointe_racine_id` | INTEGER | NULL ; sans FK | Déduction technique | R14 |
| `notes` | TEXT | NULL | Règle documentée | R15 |
| `cancelled_at` | TEXT (TS) | NULL ; GLOB TS UTC millisecondes (classes `[0-9]`, mêmes que 003/004) | **Décision validée** (DV-2) | R16, R22 |
| `motif_annulation` | TEXT | NULL ; `<> ''` si présent | **Décision validée** (DV-2) | R22 |
| `created_at`, `updated_at` | TEXT (TS) | NOT NULL ; défaut instant UTC ms ; `GLOB` ; **données techniques** (non métier) | Règle documentée | Modèle §2.2 |

CHECK de table : `substr(numero,11,2) = substr(date_depense,3,2)` (Déduction technique) ; `(piece_jointe_chemin IS NULL) = (piece_jointe_racine_id IS NULL)` (Règle documentée) ; `(cancelled_at IS NULL) = (motif_annulation IS NULL)` (Décision validée, DV-2).

**Absent volontairement** (décisions DV-8 à DV-10) : `statut` ; `origine`, `legacy_id`, `legacy_data`, `legacy_numero` ; `taux_tva`, `montant_tva`, `montant_ttc` ; `date_facture`, `date_echeance`, `date_paiement` ; toute table ou colonne d'historique des modifications (pas de `created_by`, de `modified_*` ni de journal propre) ; `frozen_at` ; toute colonne de cache sur `bons_commande` (aucun total des dépenses stocké) ; borne 2001–2099 ; contrôle fournisseur/catégorie/BC annulé/30 jours (service).

Triggers : **TR-01** `tr_01_depenses_numero_immuable` (`BEFORE UPDATE OF numero, date_depense`, `WHEN NEW.numero IS NOT OLD.numero OR substr(NEW.date_depense,3,2) IS NOT substr(OLD.date_depense,3,2)`, message `INV-23: …`) ; **TR-101** (numéro proposé, le premier libre après TR-100) `BEFORE DELETE ON depenses` : `RAISE(ABORT, 'INV-06: …')` ; **TR-102** (**validé**, T-1 ; §5) `BEFORE UPDATE ON depenses` (sans liste de colonnes) `WHEN OLD.cancelled_at IS NOT NULL` : `RAISE(ABORT, …)` — refuse **tout** UPDATE d'une dépense déjà annulée, y compris `updated_at` isolé et tout retour de `cancelled_at` à NULL. L'annulation elle-même (`OLD.cancelled_at IS NULL`) n'est pas visée. Les trois triggers sont **locaux à une ligne**.

Index : `idx_depenses_bc_id`, `idx_depenses_fournisseur_id`, `idx_depenses_categorie_id`, `idx_depenses_date_depense` ; aucune table d'historique créée par 005 ; hors tranche : `historique`, `documents`, factures, règlements, garanties, PV, planning, URSSAF.

---
## 3. Relations et règles de rattachement

### 3.1 Relations et intégrité

| Relation | Cardinalité | FK / ON DELETE / ON UPDATE | Unicité | Index | Modification ou suppression du parent | Nature |
|---|---|---|---|---|---|---|
| Dépense → Fournisseur | facultative (NULL) | `REFERENCES fournisseurs(id) ON DELETE RESTRICT` ; aucun `ON UPDATE` | non | `idx_depenses_fournisseur_id` | données modifiables sans effet ; suppression interdite (FK, INV-183) | Règle documentée |
| Dépense → BC | facultative (NULL) | `REFERENCES bons_commande(id) ON DELETE RESTRICT` ; aucun `ON UPDATE` | non | `idx_depenses_bc_id` | annulation du BC sans effet ; suppression du BC impossible (TR-19) | Règle documentée |
| Dépense → Catégorie | obligatoire | `REFERENCES categories_depenses(id) ON DELETE RESTRICT` ; aucun `ON UPDATE` | non | `idx_depenses_categorie_id` | une catégorie utilisée n'est pas supprimée ; elle est désactivée (`actif`) | Règle documentée (RESTRICT) ; Déduction technique (désactivation) |
| Pièce jointe → racine de stockage | facultative, liée à `piece_jointe_chemin` | **aucune FK** : `machine.db` est une base distincte (référence logique, comme `documents.racine_stockage_id`) ; contrôlée par CK-10 | non | — | racine « non localisable » après restauration sur une autre machine | Déduction technique ; Proposition (extension de CK-10) |
| Dépense → `historique` | aucun lien SQL | polymorphe (`type_entite = 'depense'`, existence : CK-09) ; table `historique` hors tranche | — | — | — | Règle documentée |
| Dépense → URSSAF, client, document | **aucune** | — | — | — | le client d'un BC n'est pas copié sur la dépense | Règle documentée (INV-120, D-34) |

Aucun `CASCADE`, aucun `SET NULL`, aucun `ON UPDATE`. Index supplémentaire sur `numero` : inutile (l'`UNIQUE` en crée un).

### 3.2 Règles de rattachement d'une dépense à un BC

*Toutes sont des règles de **service** (aucun trigger inter-tables, aucun CHECK). Le contrôle porte sur le BC **cible**, à l'instant de l'opération.*

| Opération | Règle | Nature | Source |
|---|---|---|---|
| Création **sans** BC (dépense globale) | libre | Règle documentée | R2 |
| Création avec un BC **non annulé** (`date_100_facture` NULL ou ≤ 30 jours) | libre, sans confirmation | Règle documentée | R8 ; C-21 |
| Création avec un BC **non annulé** clôturé depuis plus de 30 jours | **confirmation explicite** (« clôturé depuis X jours »), aucun délai maximal | Règle documentée | R8 ; C-22 ; INV-103 |
| Création avec un BC **annulé** | libre : **aucun délai, aucune confirmation** | Décision validée | R26, R27 (DV-6, DV-7) |
| **Rattachement ultérieur** d'une dépense globale à un BC non annulé | mêmes règles que la création (30 jours, confirmation) | Décision validée | R25 (DV-5) |
| **Rattachement ultérieur** à un BC **annulé** | libre, sans délai ni confirmation | Décision validée | R26, R27 |
| **Changement de BC** (BC 1 → BC 2) | contrôle du **BC 2** au moment de l'opération ; aucun contrôle sur le BC 1 d'origine (aucune règle) | Décision validée (BC 2) ; Déduction technique (BC 1) | R25 |
| **Détachement** (→ dépense globale) | permis ; aucun contrôle | Décision validée | R25 |
| Modification d'une dépense déjà rattachée **sans changer de BC** | pas un nouveau rattachement : aucune confirmation, aucune nouvelle vérification du délai | **Décision validée** | R32 (C-1) |
| Toute opération sur une dépense **annulée** | **refusée** (immutabilité totale) | Décision validée | R23 (TR-102) |
| Passage du BC à `annule` après le rattachement | n'affecte aucune dépense ; le lien reste | Règle documentée | INV-188, INV-193 |
| Suppression du BC | impossible (TR-19) | Règle documentée | INV-174, D-35 |

### 3.3 États du BC (vérifiés séparément, sans transposition depuis devis ou factures)

Les statuts réels du BC (004, CHECK) sont `en_cours`, `termine`, `annule`. Le **gel** n'est pas un statut ; le « gel commercial » est **supprimé** en V3.13 (Métier ; PT-8) et `frozen_at` est appelé à être adapté.

| État du BC | Nouvelle dépense / nouveau rattachement | Nature | Source |
|---|---|---|---|
| `en_cours`, `date_100_facture` NULL | libre | Règle documentée | R8 |
| `en_cours`, 100 % facturé depuis ≤ 30 jours | libre, sans confirmation | Règle documentée | C-21, INV-103 |
| `en_cours`, 100 % facturé depuis > 30 jours | confirmation simple (« clôturé depuis X jours ») | Règle documentée | C-22, D-31 |
| `termine` | la règle porte sur `date_100_facture` (toujours renseignée, CHECK de 004), non sur le statut : **même règle, aucune règle propre à `termine`** | Déduction technique | D-31 ; 004 |
| « gelé » | **aucun effet** ; aucune règle de dépense ne dépend de `frozen_at` (PT-8). Une dépense n'écrit rien dans `bons_commande` | Déduction technique | Métier (gel supprimé) ; PT-8 ; 004 |
| `annule` | création et rattachement **libres**, sans 30 jours ni confirmation ; le lien se conserve | Décision validée | R26, R27 |

Rien n'est repris des règles propres aux devis (verrouillage) ou aux factures (avoirs, TR-16).

| Évènement sur le BC | Effet sur les dépenses rattachées | Nature | Source |
|---|---|---|---|
| régénération des lignes / modification du devis | aucun (`bons_commande.id` stable) | Déduction technique | 004 |
| annulation du BC | aucun (conservation, pas de cascade) | Règle documentée | INV-188 |
| passage `termine` ↔ `en_cours` | aucun | Déduction technique | D-31, R9 |
| suppression du BC | impossible (TR-19) | Règle documentée | INV-174, D-35 |

---

## 4. Liste des invariants

### 4.1 Invariants existants applicables à Dépenses (non modifiés)

| INV | Contenu utile à Dépenses | Garde |
|---|---|---|
| INV-04 | `id` AUTOINCREMENT, jamais réutilisé | SQL |
| INV-05 | FK `ON DELETE RESTRICT` par défaut, aucun `ON UPDATE` | SQL |
| INV-06 | aucune suppression physique d'un objet numéroté (DEP inclus) ; annulation ne libère pas le numéro | SQL, TRG (TR-101 proposé) |
| INV-07 | `recursive_triggers=ON` ; `INSERT OR REPLACE` interdit | convention, test |
| INV-10, INV-11, INV-14 | dates réelles ; décimaux exacts D2 ; montants positifs hors cas listés | SQL |
| INV-20, INV-22, INV-23, INV-25, INV-179 | format, unicité, immuabilité du numéro et de son année ; high-water ; jamais attribué deux fois | SQL, TRG (TR-01), SVC |
| INV-100 | fournisseur par identifiant, BC optionnel (BC annulé admis), ni paiement ni échéance, corrigeable puis annulable | SQL, SVC |
| INV-103 | 30 jours + confirmation, sans délai maximal | SVC (**portée précisée par INV-199 proposé**) |
| INV-106 | chemins relatifs à une racine identifiée | SVC |
| INV-110, INV-194 | historique métier utile (mécanisme V6, hors 005) | TRG (TR-60), SVC |
| INV-120 | une dépense ne réduit jamais le CA URSSAF | calcul URSSAF |
| INV-173, INV-188 | BC annulé : conservé avec ses dépenses ; une dépense peut y être créée ou y rester liée | TRG, SVC |
| INV-177 | borne d'année 2001–2099 (service) | SVC |
| INV-183 | fournisseurs conservés, sans statut | SQL, TRG (PT-4) |
| INV-193 | dépense corrigeable puis annulable ; annulée : conservée, exclue des calculs, liée au BC annulé possible | SVC |

### 4.2 Invariants proposés pour les décisions du 2026-10-04 (**Propositions** ; numéros provisoires INV-197 à INV-201, `invariants.md` non modifié)

Chaque invariant exige, selon le registre, une garde et un test du même nom (`test_INV_xxx`).

| INV proposé | Énoncé | Origine | Garde | Test |
|---|---|---|---|---|
| **INV-197** | Une dépense annulée est **totalement immuable** : aucun UPDATE, sur aucune colonne métier ou technique (`updated_at` inclus) ; l'annulation est irréversible ; objet, numéro, données et rattachement conservés | Décision validée (TR-102 / T-1, DV-3) | **TR-102** (validé) + SVC | `test_INV_197_*` (005) |
| **INV-198** | Une dépense **active** est corrigeable (fournisseur, détachement, rattachement, changement de BC, globale ↔ rattachée) ; tout nouveau rattachement est contrôlé selon les règles applicables au moment de l'opération | Décision validée (DV-5) | SVC | service (hors 005) ; 005 : le SQL accepte ces `UPDATE` sur une dépense active |
| **INV-199** | La règle des 30 jours + confirmation ne s'applique qu'aux **BC non annulés** ; pour un BC annulé : aucun délai ni confirmation, création et rattachement ultérieur libres | Décision validée (DV-6, DV-7) | SVC | service (hors 005) ; 005 : le SQL accepte la création et le rattachement vers un BC annulé |
| **INV-200** | Une dépense annulée est conservée physiquement, **exclue des calculs actifs** (totaux, marges, analyses économiques, indicateurs actifs) et consultable dans l'historique | Décision validée (DV-4) | SVC (requêtes d'analyse) | service (hors 005) |
| **INV-201** | Une dépense n'a qu'**une date métier**, `date_depense` (attribuée par l'utilisateur, par défaut le jour, a posteriori possible) ; aucune date de facture, d'échéance ou de paiement ; `created_at` est une donnée technique | Décision validée (DV-8, DV-12) | SQL (absence de colonnes) ; SVC | `test_INV_201_*` (005) : absence de colonnes |

Les règles DV-11 (catégorie inactive) et C-1 (pas de confirmation si le BC reste identique) sont des règles de **service** sans invariant SQL propre ; elles pourront être rattachées à INV-198 / INV-199 lors de l'intégration. Intégrations documentaires associées (à reporter à la validation du modèle, annexe C) : INV-103 (portée), INV-188 et Métier §18 (rattachement ultérieur), journal du registre.

---

## 5. Répartition SQL / triggers / services / CK-13

### 5.1 Couche de chaque règle

| Règle | CHECK / UNIQUE / FK | Trigger | Service | Contrôle | Nature |
|---|---|---|---|---|---|
| Format, unicité du numéro | CHECK GLOB + UNIQUE | — | attribution PT-1 | CK-01, CK-02 | Règle documentée |
| Année du numéro = année de `date_depense` | CHECK `substr` | TR-01 (message INV-23) | — | CK-01 | Règle documentée ; Déduction technique |
| `numero` et année immuables | — | **TR-01** | — | — | Règle documentée (R21) |
| Dates réelles | CHECK GLOB + `date(x) IS x` | — | — | — | Règle documentée |
| Borne 2001–2099 | **jamais un CHECK** | — | oui (création, modification) | — | Règle documentée |
| Une seule date métier, aucune `date_facture`/échéance/paiement | absence de colonnes | — | — | — | Décision validée (DV-8) |
| `montant` D2, > 0, HT, sans TVA | CHECK ; absence de colonnes TVA/TTC | — | saisie à 2 décimales | — | Règle documentée (D2) ; Décision validée (HT, DV-9) |
| Pièce jointe : les deux ou aucun | CHECK | — | stockage du fichier | CK-10 (étendu) | Règle documentée |
| Existence des parents | FK RESTRICT | — | — | CK-03 | Règle documentée |
| **Suppression interdite** (y compris `INSERT OR REPLACE`) | — | **BEFORE DELETE** (TR-101 proposé) | — | — | Règle documentée (principe) ; Proposition (trigger) |
| Annulation : date et motif ensemble ; motif non vide ; format TS | CHECK | — | motif demandé ; annulation unique | — | Décision validée (DV-2) |
| **Dépense annulée immuable et irréversible** | — | **TR-102** (validé) | refus explicite ; aucune réactivation | — | Décision validée (règle, service et trigger : T-1) — détail ci-dessous |
| Correction d'une dépense active (fournisseur, BC, détachement, rattachement, globale ↔ rattachée) | aucune restriction SQL | — (hors TR-01 et TR-102) | oui, contrôle du rattachement ; **aucun** contrôle de délai si le BC est inchangé | — | Décision validée (DV-5, C-1) |
| 30 jours + confirmation (BC non annulé) | — | **non** | oui | — | Règle documentée ; Décision validée (portée, DV-7) |
| Exception BC annulé (aucun délai, aucune confirmation) | — | **non** | oui | — | Décision validée (DV-6, DV-7) |
| Création / rattachement ultérieur vers un BC annulé | aucune restriction SQL | — | autorisé | — | Décision validée (DV-6) |
| Exclusion des dépenses annulées des calculs actifs | — | — | requêtes d'analyse (`cancelled_at IS NULL`) | — | Décision validée (DV-4) |
| Catégorie inactive : non sélectionnable (nouvelle dépense, catégorie cible d'une correction) ; lien historique conservé | **aucune** (pas de CHECK ni de trigger inter-tables) | non | oui | — | Décision validée (DV-11) |
| Dépense ne réduit pas le CA URSSAF | — | — | calcul URSSAF | — | Règle documentée |
| Journalisation spécifique aux dépenses | **aucune** | — | mécanisme V6 `historique` (hors 005) | CK-09 (hors 005) | Décision validée (DV-10) |
| Import | **aucun** | — | — | CK-12 sans objet | Règle documentée |

**Aucune règle complexe ni inter-tables n'est convertie en trigger** : 30 jours, BC annulé, rattachement, catégorie inactive, cohérence date ↔ BC restent au service. Les trois triggers sont **locaux à une ligne** (TR-01 comme pour devis et BC ; TR-101 comme TR-19 / TR-90 / TR-96 ; TR-102 comme le verrou des règlements, INV-70 / TR-32).

### 5.2 Immutabilité d'une dépense annulée : règle, service, trigger

| Niveau | Contenu | Nature |
|---|---|---|
| **Règle métier** | une dépense annulée est totalement immuable et l'annulation irréversible (R23) ; aucune colonne, métier ou technique (`updated_at` inclus), ne change ; l'objet, son numéro DEP, ses données et son rattachement sont conservés | **Décision validée** |
| **Contrôle de service** | le service refuse, avec un message métier explicite, toute modification, tout rattachement ou détachement, tout changement de fournisseur, de montant, de date ou de motif, et toute tentative de réactivation ou de nouvelle annulation d'une dépense annulée ; l'annulation est une opération unique avec motif obligatoire | **Décision validée** (le service doit interdire ces modifications) ; message métier : Déduction technique |
| **Trigger SQL TR-102** | `BEFORE UPDATE ON depenses WHEN OLD.cancelled_at IS NOT NULL` → `RAISE(ABORT, …)` ; sans liste de colonnes (couvre `updated_at` isolé et le retour de `cancelled_at` à NULL) ; l'annulation (`OLD.cancelled_at IS NULL`) passe ; DELETE reste refusé par TR-101 (donc aussi `INSERT OR REPLACE` avec `recursive_triggers=ON`) | **Décision validée** (T-1) : barrière SQLite complémentaire au service |

*Portée* : le trigger est la seule mécanique SQL ajoutée pour cette règle ; il ne crée aucun historique (aucune table, aucune colonne de journal : DV-10). Précédent : règlements immuables (INV-70, TR-32) ; trigger local à une ligne. *Non retenu* : un contrôle supplémentaire garantissant qu'à l'instant de l'annulation les colonnes métier restent inchangées (hors périmètre de la décision ; le service et ses tests le couvrent).

### 5.3 Contrôles `CK-xx`

**Contrôles existants (CK-01, 02, 03, 10, 13, 14) — conclusion explicite : aucun nouveau CK n'est nécessaire.** Déduction technique : l'annulation ne stocke aucun total dénormalisé ; l'exclusion des dépenses annulées des calculs actifs est un filtre de requête, pas un contrôle d'intégrité.

| Contrôle | Couvre `depenses` ? | Action |
|---|---|---|
| CK-01 numéros uniques et conformes au format V6 | oui (aucune exemption d'origine pour DEP) | citer `depenses` explicitement dans la requête |
| CK-02 séquences ≥ max des numéros V6 | oui ; l'année est lue dans le numéro (`yy`), la séquence est `(DEP, yy)` | idem |
| CK-03 (`foreign_key_check`) | oui, générique | aucune |
| CK-09 existence des `entite_id` polymorphes | oui dès que `historique` existe (hors tranche) | aucune |
| CK-10 racines connues | **libellé limité aux « racines de documents »** | étendre aux pièces jointes de dépenses (précision documentaire, **Proposition**) |
| CK-13 (devis ↔ BC) | non concerné | aucune |
| CK-14 (rattachement multi-devis) | non concerné | si un CK de dépenses était un jour voulu : **CK-16**, jamais CK-14 |

---
## 6. Points ambigus ou contradictoires trouvés dans les documents

*Les points C-A à C-O sont les corrections apportées à la première version ; C-P à C-X sont les points relevés lors de l'intégration des arbitrages du 2026-10-04. **Aucune décision validée n'est rouverte, et aucun de ces points n'est une nouvelle décision** : les décisions correspondantes sont déjà prises ; ce sont des **alignements documentaires à effectuer ultérieurement**, sans correction des documents normatifs à ce stade. Les cinq alignements retenus : (1) INV-103 sans exception explicite pour les BC annulés (C-S) ; (2) INV-188 / CDC : portée du rattachement à un BC annulé (C-R) ; (3) Métier §18 / Modèle §4.12 : « montant réellement payé » contre « montant HT » (C-Q) ; (4) définition de `date_depense` (C-U) ; (5) intégration ultérieure d'INV-197 à INV-201 (C-X).*

| # | Constat | Nature | Traitement |
|---|---|---|---|
| C-A | Q2 « dépense sur BC annulé : aucune règle » | caduque | tranchée (R17, R25, R26, R27) |
| C-B | « fournisseur archivé / actif » (R6, R7, §3.1) | caduque | supprimée (E-12, INV-183) |
| C-C | « aucune annulation, suppression permise » (Q3, INV-181 proposé) | caduque | annulation (DV-2, irréversible DV-3) ; suppression interdite ; garde DELETE |
| C-D | « A-4 : REPLACE contourne TR-01 » | traité | garde DELETE ; test documenté |
| C-E | « annulation d'un BC avec solde actif interdite (D-05) » | caduque | D-05 remplacée (D-46, E-15) |
| C-F | Numéros INV-179 à INV-182 proposés pour Dépenses | déjà attribués | nouvelles règles de Dépenses : **INV-197 et suivants** |
| C-G | « CK-14 de cohérence des dépenses » | collision | CK-14 est le rattachement multi-devis ; éventuel CK de dépenses : CK-16 ; non proposé |
| C-H | « Base `548f61f`, 9 décisions » | périmé | base actualisée ; DV-1 à DV-10 |
| C-I | « Dépense globale entre dans les analyses » | non documenté | retiré |
| C-J | Catégorie inactive, sens de `date_depense` : présentés comme propositions de règle | silence | sens de la date tranché (DV-8) ; catégorie inactive : DV-11 |
| C-K | T-30 réservé à la tranche dans la première version | collision | T-30 = numérotation en V3.13 ; numéro à réattribuer |
| C-L | Migration 002 contient encore `fournisseurs.statut` | contradiction migration/documents | traitée par la corrective M-A (`005a`, PT-3), hors 005 ; 005 n'y touche pas (§1.5.6) |
| C-M | DV-1 de la version précédente : recommandation « (b) M-A et M-B d'abord, Dépenses ensuite », mention d'une migration `005_corrections_v313` et d'un « numéro de fichier de 005 dépendant de DV-1 » | **contredit** la décision V-1 à V-5 (2026-10-04) | corrigé : 005 = Dépenses (rang 5) ; M-A/M-B = `005a`/`005b` (rangs 6 et 7), avant 006 ; aucune tranche renumérotée |
| C-N | Risque annoncé : « reconstruction de `fournisseurs` avec FK entrante `RESTRICT` » et « montage le plus fragile de SQLite » | **surévalué / inexact** | `fournisseurs` ne se reconstruit pas (`DROP INDEX` puis `DROP COLUMN`) ; le vrai cas est la reconstruction de `bons_commande` par M-B, référencée par `depenses.bc_id` : couverte par le protocole de reconstruction (conventions §5) |
| C-O | DV-2 « Proposition (PT-14) » et DV-3 « Décision à valider » dans les tableaux de la version précédente | **périmé** | DV-2 et DV-3 (option A) validées le 2026-10-04 ; natures mises à jour |
| C-P | Version précédente : DV-4 à DV-10 « Décision à valider » (effets de l'annulation, champs corrigeables, BC annulé, 30 jours, sens de la date, limites, historique), TR-102 « conditionnel », « liste des calculs à définir » | **périmé** | décisions validées le 2026-10-04 (R23 à R30) ; TR-102 retenu en proposition ; restent DV-11 et DV-12 |
| C-Q | **Libellé du montant** : Métier §18 et Modèle §4.12 disent « montant réellement payé (franchise de TVA) » ; la décision DV-9 dit « **HT** », sans TVA ni TTC | **contradiction de libellé, non de structure** : pour une entreprise en franchise, la TVA d'achat n'est pas récupérable et le « réellement payé » est un montant toutes taxes ; « HT » ne le dit pas | **non masquée, non rouverte** : aucune incidence SQL (un seul `montant` D2) ; la décision prévaut ; le libellé de l'interface et des documents (Métier §18, Modèle §4.12) est à aligner à la validation du modèle, en précisant ce que « HT » désigne pour la dépense saisie |
| C-R | **Rattachement ultérieur à un BC annulé** : D5, INV-188, Métier §18, CDC §28 et Modèle §4.12 disent « créée sur un BC annulé et y rester liée » ; l'Audit conservation §7.3 n°4 laissait le rattachement ultérieur à ce cadrage | **extension** | DV-6 l'autorise ; les textes sont à compléter (« créée ou rattachée ultérieurement ») |
| C-S | **Règle des 30 jours sans exception** : INV-103, Modèle §4.12 (« `date_du_jour > date_100_facture + 30 jours` »), CDC §15, C-21/C-22 sont énoncés sans exclure le BC annulé | **contradiction apparente** avec DV-7 | DV-7 prévaut : exception **spécifique aux BC annulés**, à documenter comme telle dans INV-103, Modèle §4.12 et CDC §15 ; l'Audit conservation §7.3 n°5 est ainsi tranché |
| C-T | **« Liste des calculs à définir (PT-14) »** dans Métier §18, Modèle §4.12, INV-193, E-19 | **lacune comblée au niveau général** | DV-4 fixe le principe (totaux, marges, analyses économiques, indicateurs actifs) ; le détail indicateur par indicateur relève des analyses (hors 005) |
| C-U | **Définition de `date_depense`** : le Modèle §4.12, le Métier §18 et les invariants parlent d'une « date » sans la définir (et du « montant réellement payé ») ; une première formulation du cadrage la disait « date de saisie/enregistrement » | **définition à aligner** | **tranchée (DV-12)** : date métier attribuée par l'utilisateur, par défaut le jour, renseignable a posteriori, **distincte de `created_at`** ; formulation erronée supprimée du cadrage ; la définition est à reporter dans le Modèle §4.12 et le Métier §18 (alignement documentaire, §9.2) |
| C-V | **Traçabilité** : DV-10 exclut toute journalisation propre aux dépenses ; Métier §2.4/§26, INV-110 et INV-194 disent que l'annulation d'une dépense est un événement tracé de l'historique | **compatible sous une condition** | l'événement relève du mécanisme V6 existant (`historique`, TR-60, énumération PT-15), **hors 005** ; 005 ne crée aucune table ni colonne de journal. « Consultable dans l'historique » (DV-4) est lu comme : la dépense annulée reste visible dans les consultations et son annulation dans l'historique V6 |
| C-W | **Immutabilité totale vs trigger** : l'ancien cadrage laissait en suspens le sort d'un `updated_at` isolé sur une dépense annulée | **résolu** | refus total (R23) ; TR-102 sans liste blanche |
| C-X | **Intégration des invariants proposés** INV-197 à INV-201 (§4.2) et des règles de service R31 (DV-11) et R32 (C-1) | **alignement ultérieur** | à intégrer à `invariants.md` à la validation du modèle ; `invariants.md` non modifié ici |


Statuts documentaires périmés à corriger hors de ce cadrage (annexe C) : en-têtes de `docs/README.md` et d'`invariants.md` (« V3.12 non validée »), `modèle-métier` (renvois V3.10/V3.11), `conventions-techniques` §4/§5/§7 (001–003 seulement), Modèle §4.12 (« sera déterminé lors de la conception de la tranche Dépenses »), ligne vide du tableau §17.1 avant 004.

---

## 7. Proposition de structure de `005_depenses.sql` (à n'écrire qu'après validation)

`PRAGMA user_version` (rang 5) posé par le runner **dans la transaction de la migration, avant son `COMMIT`** (conventions §5) ; ni `BEGIN/COMMIT` ni `PRAGMA` dans le fichier ; aucune ligne insérée ; aucune reconstruction de table ; en-tête citant le **modèle V3.13 validé**. Ordre : (1) en-tête (références Modèle §2, §3.5, §4.12, §6, §8, §9, §10.3, §17.1 ; INV-04, 05, 06, 10, 11, 14, 20 à 23, 100, 103, 177, 188, 193 et INV-197 à 201 une fois intégrés ; D-12, D-18, D-23, D-31, D-38, D-39, D-50, D-55 ; PT-1, PT-14) ; (2) table `depenses` STRICT (colonnes du §2 : aucune colonne de TVA, de facture, d'échéance, de paiement, d'historique) ; (3) **TR-01, TR-101 et TR-102** ; (4) quatre index. **Fichier `005_depenses.sql`, tranche métier de rang 5 (DV-1).**

---

## 8. Proposition de structure de `test_005_depenses.py`

Test à numéroter dans le Modèle §13.3 (T-43 est le dernier numéro attribué : prendre le prochain numéro libre). Connexion : `foreign_keys=ON`, `recursive_triggers=ON` posés explicitement, chaîne **001 → 005** appliquée (rangs 1 à 5 ; le test pose `user_version = 5`, qui est ici à la fois le rang et le numéro) ; noms `test_INV_xx_…`. Les tests 003/004 vérifiant l'absence de `depenses` ne sont pas touchés. Les règles de **service** (30 jours, confirmation, borne d'année, rattachement à un BC annulé, catégorie active) se testent côté Rust : **hors de cette tranche** ; ici, uniquement les **faits SQL** (ce que la base accepte et refuse).

| Groupe | Contenu | Tests (estim.) |
|---|---|---|
| Structure | `PRAGMA recursive_triggers` actif ; 1 table `STRICT`, colonnes exactes (types, NOT NULL, défauts) ; aucune ligne ; 3 triggers (noms : TR-01, TR-101, TR-102) ; 4 index (noms, colonnes, plan de requête qui les utilise) ; `foreign_key_check` vide ; **absence** de `statut`, `origine`, `legacy_*`, TVA/TTC, `date_facture`, `date_echeance`, `date_paiement`, colonnes de journal, `frozen_at` ; tables 001–004 inchangées | 9 |
| Création | dépense minimale ; globale ; avec fournisseur ; avec BC `en_cours` ; avec pièce jointe ; défauts `created_at`/`updated_at` ; annulation absente à la création | 7 |
| Numérotation | format `GLOB` explicite ; année = année de `date_depense` (et non l'année courante) ; séquence `DEP` par année ; plafond 99 999 ; `annee = 0` refusé pour `DEP` ; TR-95/TR-96 inchangés ; **numéro non réutilisé après annulation** ; **trou toléré** par la base ; `UNIQUE(numero)` ; deux attributions → deux numéros | 10 |
| TR-01 | `numero` immuable ; changement d'année refusé (message `INV-23`) ; changement de jour dans la même année accepté ; chaque opérande du `WHEN` isolé ; autres colonnes modifiables | 8 |
| Garde DELETE | `DELETE` refusé (dépense active, annulée, globale, rattachée) ; message `INV-06` ; `INSERT OR REPLACE` par `id` et par `numero` refusés avec `recursive_triggers=ON` ; témoin documenté avec OFF ; aucune ligne perdue | 7 |
| Annulation | `cancelled_at`/`motif_annulation` ensemble ou aucun ; motif vide refusé ; format TS ; l'annulation d'une dépense active est acceptée (une seule fois) ; une dépense annulée conserve `numero`, `bc_id`, `fournisseur_id`, `categorie_id` | 6 |
| **TR-102 (dépense annulée immuable)** | `UPDATE` refusé pour **chaque** colonne métier et technique (fournisseur, BC, détachement, rattachement, catégorie, montant, date, description, notes, pièce jointe, `created_at`) ; `updated_at` **isolé** refusé ; `cancelled_at` → NULL refusé ; `motif_annulation` modifié refusé ; l'annulation d'une dépense active passe ; `DELETE` et `INSERT OR REPLACE` d'une dépense annulée refusés ; TR-01 et TR-102 coexistent | 10 |
| Dates | calendrier exhaustif (bissextiles, 30/31 jours) ; `date(x) IS x` ; années 1900, 2000, 2100 acceptées par le SQL (règle de service) ; date antérieure au jour de création acceptée (saisie a posteriori, DV-12) ; aucune colonne `date_facture` | 6 |
| Montants HT / précision | D2 valides (`0.01`, `1250.50`, valeur maximale raisonnable) ; invalides (`0.00`, `1.5`, `-1.00`, `1a.00`, `1.2.50`, `01.00`, `1e2`, espaces, `""`, NULL, float) ; **texte conservé octet pour octet** (`0.10`, `0.30`) ; somme en centimes entiers exacte (`0.10 + 0.20 = 0.30`) ; aucune colonne TVA | 8 |
| Textes et pièce jointe | `description` vide/NULL ; chemin vide ; chemin sans racine et inversement ; les deux ou aucun | 5 |
| FK | `fournisseur_id`, `bc_id`, `categorie_id` inexistants refusés ; suppression d'un fournisseur / d'une catégorie / d'un BC référencés refusée (RESTRICT, TR-19) ; aucun `ON UPDATE` ; une catégorie **inactive** est acceptée par le SQL (la règle DV-11 est au service) | 7 |
| Fournisseur | NULL accepté ; tout fournisseur existant accepté ; changement et retrait du fournisseur d'une dépense **active** acceptés ; **aucun test ne lit ni n'asserte `fournisseurs.statut`** ; modification des données du fournisseur sans effet sur la dépense | 5 |
| BC (faits SQL) | `en_cours` ; `en_cours` 100 % depuis 20 et 45 jours ; `termine` ; **`annule` : création acceptée, rattachement ultérieur accepté, lien conservé** (DV-6) ; annulation du BC (UPDATE légitime) sans effet sur ses dépenses ; la création n'écrit rien dans `bons_commande` ; changement/détachement de `bc_id` d'une dépense **active** acceptés par le SQL (la règle est au service) | 9 |
| Dépense globale | création ; rattachement ultérieur et détachement d'une dépense **active** acceptés par le SQL (règle de service : DV-5) | 3 |
| Modification | colonnes modifiables hors `numero`/année ; `updated_at` (valeur fournie par le service) ; TR-01 reste actif | 3 |
| Import | **aucun test de bloc** (blocs refusés) : seulement l'absence de `origine`/`legacy_*` et d'`import_anomalies` de dépense | 2 |
| Identifiants décalés | clients, fournisseurs, catégories, BC, dépenses avec des `id` tous différents pour détecter une confusion de colonnes | 3 |
| Contrôles de restauration | requêtes CK-01/02/03 (et CK-10 étendu) : doublon de numéro, séquence en retard, FK orpheline, racine inconnue | 5 |
| **Total estimé** | | **≈ 113** |

**Campagne de mutation (conventions §7.1), au niveau de rigueur de 004** — objectif : **0 survivant non qualifié**. Mutants génériques : suppression ou inversion de chaque CHECK ; chaque jeton des motifs `GLOB` (positions, classes, `NOT GLOB`) ; `IN` ↔ `NOT IN` ; chaque `NOT NULL` ; chaque `UNIQUE` ; chaque FK (`RESTRICT` → `CASCADE`/`SET NULL`/`NO ACTION`/absente) ; `IS`/`IS NOT` ↔ `=`/`<>` (pièges `NULL`) ; `OLD`/`NEW` ; `date(x) IS x`. Mutants propres à 005 : confusion d'identifiants entre colonnes ; chaque opérande du `WHEN` de TR-01 ; `UPDATE OF` incomplet ; offsets de `substr` du numéro (11,2) et de la date (3,2) ; conjoncts D2 (jeu de caractères, double point, zéros de tête, `0.00`, signe) ; « les deux ou aucun » de la pièce jointe et de l'annulation ; **suppression du trigger DELETE**, `BEFORE` ↔ `AFTER`, message ; **TR-102** : condition `WHEN` inversée ou supprimée (annulation bloquée, ou dépense annulée modifiable), `UPDATE OF` avec liste de colonnes (laisse passer `updated_at` isolé), opérande `OLD`/`NEW` échangé ; index supprimé ou colonne modifiée (plan de requête) ; **trigger absent + `recursive_triggers=OFF`** (REPLACE) ; mutation de l'ordre 001 → 005. Survivants attendus à qualifier (mêmes classes qu'en 004) : `GLOB` de date redondant avec `date(x) IS x` ; clause « année » de TR-01 redondante avec le CHECK `substr` quand `numero` est inchangé (tuée seulement par le message `INV-23`) ; `BEFORE` ↔ `AFTER` avec `RAISE(ABORT)` (équivalent, y compris pour TR-102) ; disjonctions laissant passer `NULL`.

---
## 9. Liste des décisions nécessitant validation

### 9.1 Décisions déjà validées (ne pas rouvrir)

| # | Décision | Nature | Date | Effet |
|---|---|---|---|---|
| **DV-1** | Versionnement et place de 005 : ordre métier réservé 001 → 010 ; `005_depenses.sql` = tranche métier de **rang 5** ; M-A et M-B = **correctives** `005a_corrections_v313.sql` (rang 6) et `005b_bc_multi_devis.sql` (rang 7), après 005 et avant 006, **sans renumérotation** ; `user_version` = rang (après 005 : 5) ; base à `user_version = 4` → 005 puis 005a, 005b, 006 ; runner et protocole de reconstruction = chantier technique distinct (V-1 à V-5, D-55) | Décision validée | 2026-10-04 | nom et rang du fichier ; aucune reconstruction dans 005 |
| **DV-2** | Annulation : `cancelled_at` + `motif_annulation`, **sans `statut`** ; UTC millisecondes ; motif obligatoire et non vide ; deux colonnes cohérentes | Décision validée | 2026-10-04 | 2 colonnes, CHECK de cohérence et de format |
| **DV-3** | Option A : annulation irréversible, aucune réactivation, aucune modification métier ; nouvelle dépense = nouvel objet, nouveau numéro | Décision validée | 2026-10-04 | TR-102 |
| **TR-102** (T-1) | Dépense annulée totalement immuable (toute colonne, `updated_at` inclus) ; interdit par le service **et** par le trigger SQL TR-102 (validé) | Décision validée | 2026-10-04 | TR-102 ; §5.2 |
| **DV-4** | Dépense annulée exclue des calculs métier actifs, conservée, consultable | Décision validée | 2026-10-04 | service ; INV-200 proposé |
| **DV-5** | Dépense active corrigeable (fournisseur, détachement, rattachement, changement de BC, globale ↔ rattachée) ; contrôle au moment de l'opération | Décision validée | 2026-10-04 | service ; INV-198 proposé |
| **DV-6** | Création directe et rattachement ultérieur autorisés avec un BC annulé | Décision validée | 2026-10-04 | service ; INV-199 proposé |
| **DV-7** | 30 jours : BC non annulés seulement ; BC annulé sans délai ni confirmation ; règle de service | Décision validée | 2026-10-04 | service ; INV-199 proposé |
| **DV-8** | Une seule date métier `date_depense` ; pas de `date_facture` ; `created_at` technique | Décision validée | 2026-10-04 | INV-201 proposé |
| **DV-12** | `date_depense` = date métier attribuée à la dépense par l'utilisateur ; initialisée par défaut à la date du jour, mais pouvant être renseignée a posteriori ; distincte de `created_at` ; numéro DEP jamais réutilisé ni rendu incohérent avec son année ; changement d'année incompatible ⇒ annulation puis nouvel objet, sans renumérotation | Décision validée | 2026-10-04 | INV-201 proposé ; service |
| **DV-9** | Un `montant` HT, centime, strictement positif ; aucune TVA | Décision validée | 2026-10-04 | CHECK, absence de colonnes |
| **DV-10** | Traçabilité par les données propres ; aucune table d'historique générique ni journalisation propre | Décision validée | 2026-10-04 | aucune table, aucune colonne de journal |
| **DV-11** | Catégorie inactive non sélectionnable (nouvelle dépense, catégorie cible d'une correction) ; lien historique conservé ; aucune modification automatique ; règle de service sans contrainte SQL inter-table | Décision validée | 2026-10-04 | service |
| **C-1** | Aucune confirmation des 30 jours si le BC reste identique ; BC A → B et globale → BC : règles du BC cible ; BC → globale permis (dépense active) | Décision validée | 2026-10-04 | service |

**Non soumis à décision** (déjà documentés ou décidés) : import exclu (D-23, §10.3) ; suppression interdite (INV-06) ; fournisseur sans statut (E-12) ; format et année du numéro ; mécanisme PT-1 ; TVA absente.

### 9.2 Décisions restant à valider

**Aucune.** T-1, DV-11, DV-12 et C-1 ne sont plus des points ouverts ; le relevé des sources n'a fait apparaître **aucune décision métier bloquante** pour écrire `005_depenses.sql`. Rien n'a été ajouté artificiellement.

**Alignements documentaires à effectuer ultérieurement (ce ne sont pas des décisions, les décisions correspondantes étant prises ; les documents normatifs ne sont pas corrigés à ce stade)** :

| # | Alignement | Documents | Point du §6 |
|---|---|---|---|
| 1 | INV-103 : exception explicite pour les BC annulés | `invariants.md`, Modèle §4.12, CDC §15 | C-S |
| 2 | INV-188 / CDC : portée du rattachement à un BC annulé (création **et** rattachement ultérieur) | `invariants.md`, CDC §28, Métier §18, Modèle §4.12 | C-R |
| 3 | « Montant réellement payé » (Métier §18, Modèle §4.12) contre « montant HT » | Métier §18, Modèle §4.12 | C-Q |
| 4 | Définition de `date_depense` | Modèle §4.12, Métier §18 | C-U |
| 5 | Intégration d'INV-197 à INV-201 (et rattachement de R31, R32) | `invariants.md` | C-X |

Restent aussi, comme tâches documentaires déjà signalées (annexe C) : liste générale des calculs exclus (C-T), énumération PT-15 des événements d'historique (C-V).

**Cadrage 005 prêt pour validation finale avant implémentation SQL.**

---

## Annexe A — Tableau de synthèse

| Sujet | Conclusion | Nature | Source | Action |
|---|---|---|---|---|
| Finalité de Dépenses | suivi économique des achats/charges et de leur impact sur chantiers/BC ; ni facturation, ni échéances, ni paiements fournisseurs, ni comptabilité complète, ni TVA | Décision validée | arbitrage 2026-10-04 | — |
| Dépense globale | autorisée ; sans règle propre | Règle documentée | CDC §28 ; R2 | — |
| Dépense rattachée à un BC | autorisée ; FK RESTRICT | Règle documentée | R2 | — |
| Création sur BC annulé | autorisée | Règle documentée ; Décision validée | Audit D5 ; INV-188 ; R26 | test SQL positif |
| Rattachement ultérieur à un BC annulé | autorisé | Décision validée | DV-6 | test SQL positif ; service |
| Détacher / changer de BC (dépense active) | autorisé ; contrôle du BC cible au moment de l'opération | Décision validée | DV-5 | service |
| Passer globale ↔ rattachée | autorisé (dépense active) | Décision validée | DV-5 | service |
| 30 jours, BC non annulé | rattachement normal ≤ 30 jours, confirmation au-delà, aucun délai maximal | Règle documentée | R8 ; INV-103 | service |
| 30 jours, BC annulé | **aucun délai, aucune confirmation** (exception spécifique) | Décision validée | DV-7 | service ; INV-103 à compléter |
| Modifier une dépense active (y compris liée à un BC annulé) | autorisé, sauf `numero` et année de la date | Décision validée ; Déduction technique | DV-5 ; INV-173 | — |
| Dépense annulée | **totalement immuable**, irréversible | Décision validée | TR-102 / DV-3 | règle + service + TR-102 |
| TR-102 | trigger `BEFORE UPDATE` sur dépense annulée (toute colonne) + contrôle de service | Décision validée | T-1 ; §5.2 | écrire dans 005 |
| Exclusion des calculs actifs | totaux, marges, analyses économiques, indicateurs actifs | Décision validée | DV-4 | requêtes d'analyse |
| Fournisseur facultatif, par identifiant | oui | Règle documentée | CDC §28 ; INV-100 | — |
| Fournisseur actif / archivé | n'existe plus | Règle documentée | E-12 ; INV-183 | règle retirée |
| Changer / retirer le fournisseur (dépense active) | autorisé | Décision validée | DV-5 | — |
| Suppression du fournisseur | interdite ; FK RESTRICT ; garde PT-4 hors 005 | Règle documentée ; Proposition | INV-183 | M-A |
| `fournisseurs.statut` dans 002 | contradiction, traitée par la corrective M-A (`005a`) | Déduction technique | 002 ; PT-3 | aucune dans 005 |
| Date métier | **unique** : `date_depense`, date métier attribuée par l'utilisateur (défaut = jour, a posteriori possible) | Décision validée | DV-8, DV-12 | INV-201 proposé |
| `date_facture`, échéance, paiement | absents | Décision validée | DV-8 ; R4 | — |
| Saisie a posteriori de `date_depense` | autorisée ; défaut = date du jour ; distincte de `created_at` | Décision validée | DV-12 | service |
| `created_at` | donnée technique de création (non métier) | Règle documentée ; Décision validée | Modèle §2.2 ; DV-12 | — |
| Date d'annulation | `cancelled_at` | Décision validée | DV-2 | aucune |
| Montant | un seul, HT, D2, > 0, sans TVA | Règle documentée ; Décision validée | Modèle §4.12 ; DV-9 | CHECK |
| Libellé du montant | « réellement payé » vs « HT » | voir §6 | C-Q | alignement documentaire |
| Précision, arrondi, somme | exacts, sans calcul à l'écriture | Déduction technique | INV-11 | tests |
| Avoir fournisseur / négatif | non représentable | Décision validée ; Règle documentée | DV-9 ; INV-14 | — |
| Statut | aucun | Déduction technique | INV-100 | — |
| Annulation (colonnes) | `cancelled_at` + `motif_annulation`, sans `statut` | Décision validée | DV-2 | CHECK |
| Suppression physique | interdite | Règle documentée | INV-06 ; INV-193 | garde DELETE (TR-101, Proposition) |
| Traçabilité | colonnes propres ; aucune table d'historique ; événement d'historique via le mécanisme V6 | Décision validée ; Règle documentée | DV-10 ; INV-110 | — |
| Numérotation : année | `date_depense` | Règle documentée | Modèle §6 | — |
| Numérotation : attribution | à la création, PT-1 | Règle documentée ; Déduction technique | §11.4 | — |
| Numérotation : doublons, trous, réutilisation | aucun doublon > trou ; jamais réutilisé | Règle documentée | INV-22, INV-179 | — |
| Import | exclu (règle confirmée), aucun `origine` ni `legacy_*` | Règle documentée | §10.3 ; D-23 | — |
| Relations / ON DELETE | RESTRICT partout, aucun ON UPDATE | Règle documentée | INV-05 | — |
| Index | 4 | Règle documentée | Modèle §9 | — |
| CK-01, 02, 03 | couvrent `depenses` | Déduction technique | §14 | citer `depenses` |
| CK-10 | à étendre aux pièces jointes de dépenses | Proposition | §14 | doc |
| CK-13, CK-14 | non concernés ; aucun nouveau CK | Déduction technique | §14 | — |
| Triggers inter-tables | aucun | Déduction technique | D-36, INV-103 | — |
| Catégorie inactive | non sélectionnable pour une nouvelle dépense ou comme cible ; lien historique conservé | Décision validée | DV-11 | service (aucun SQL) |
| Modification sans changement de BC | aucune vérification des 30 jours | Décision validée | C-1 | service |
| Ordre et rang des migrations | `005_depenses` = rang 5 ; `005a`/`005b` rangs 6 et 7 ; `006_facturation` = rang 8 | Décision validée | Modèle §17.1 ; conventions §5 ; D-55 | — |
| Tests / mutation | ≈ 113 tests, campagne niveau 004 | Proposition | conventions §7.1 | après validation |

---

## Annexe B — Recherche documentaire

Termes interrogés : *dépense, DEP-, fournisseur, TVA, franchise, supprim\*, annul\*, 30 jours, date_100_facture, clôtur\*, import, legacy, origine, archiv\*, restauration, CK-, TR-, INV-100, INV-103, INV-177, INV-188, INV-193, D5, E-12, E-15, E-19, PT-14, rattach\*, immuable, HT, date_depense*. Sources : CDC §2, §15, §17, §28, §29 (+ amendements E-15, E-19) ; Métier §2.1, §2.2, §2.4, §4.2, §17, §18, §19 ; Modèle §2.2, §2.3, §3.5, §4.3, §4.4, §4.12, §6, §8, §9, §10.3, §11.4, §13.1 (C-21, C-22), §14, §15 (D-12, D-18, D-23, D-31, D-38, D-39, D-43, D-46, D-50, D-54), §17.1, §19 (PT-1, PT-3, PT-4, PT-8, PT-14) ; INV-04 à 07, 10, 11, 14, 20 à 25, 43 à 45, 100, 103, 106, 110, 120, 173, 177, 183, 188, 193 ; Audit conservation D1 à D6, §7 ; migrations 001 (`categories_depenses`, `numerotation_sequences` — `DEP` déjà dans la liste fermée), 002 (en-tête, `statut`), 004 (`date_100_facture`, statuts, TR-12/13/14/17/19, TR-96) ; tests 001–004 (aucun test de dépense).

## Annexe C — Impact documentaire (à reporter ; **rien n'a été modifié dans `docs/**`**, ni dans le modèle V3.13, les conventions ou le CDC**)

| Fichier | Correction nécessaire |
|---|---|
| Modèle SQLite → **V3.13 validé** | §4.12 : retirer « sera déterminé lors de la conception de la tranche Dépenses », consigner DV-1 à DV-12 et C-1 (tranchés), l'exception des 30 jours pour BC annulé, le rattachement ultérieur, la date unique et sa définition (DV-12), la catégorie inactive (DV-11), le libellé « HT » (C-Q), la liste générale des calculs exclus (PT-14, C-T) ; §4.19 : précisions de DDL de la migration Dépenses ; §8 : TR-101 et TR-102 ; §13.3 : numéro de test libre ; §14 : CK-01, 02, 03, 10 ; §15 : décisions ; §17.1 : ligne Dépenses (rang 5) — l'ordre et la chaîne sont déjà portés par la copie de travail V3.13 (D-55) ; la ligne vide du tableau est corrigée dans cette copie |
| `invariants.md` | INV-197 à INV-201 (propositions, §4.2) ; **INV-103** : portée aux BC non annulés ; INV-197 à INV-201 et règles de service R31, R32 ; **INV-188** : « créée ou rattachée ultérieurement » ; journal ; statut de la version |
| `modèle-métier-V6.md` | §18 : sens de `date_depense` (DV-8), libellé du montant (C-Q), règles de rattachement et exception BC annulé (DV-5 à DV-7), immutabilité d'une dépense annulée ; §17 : exclusion des dépenses annulées ; en-tête |
| `conventions-techniques-v6.md` | §5 : chaîne ordonnée et protocole déjà portés par la copie de travail 0.6 ; §7 : ajouter `test_004` (liste restée à 001–003) et, plus tard, `test_005_depenses.py` ; §4 : ajouter la migration Dépenses à sa livraison |
| `docs/README.md` | statut de la V3.13 |
| `cdc-fonctionnel-architectural-v6.md` | §15 / §28 : formulation « depuis X jours » ; exception BC annulé et rattachement ultérieur (DV-6, DV-7) |

---

**Risque** : les cinq alignements documentaires (§9.2) n'ont aucune incidence SQL, mais, tant qu'INV-103, INV-188, le libellé « montant réellement payé » et la définition de `date_depense` ne sont pas alignés, un lecteur des documents normatifs verra encore l'ancienne règle (30 jours sans exception, « date » non définie) ; les écrans et les messages de service devront suivre le cadrage, pas les anciens textes.
**Micro-amélioration** : traiter les cinq alignements dans une seule passe lors du passage du modèle à V3.13 validé, avant d'écrire `005_depenses.sql`, pour que l'en-tête de la migration cite des documents cohérents.
