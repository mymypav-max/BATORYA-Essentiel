# BATORYA Essentiel

**Modèle métier V6**

Produit : BATORYA Essentiel
Version : V6
Statut : Modèle métier — **mis à jour le 2026-10-03, alignements Dépenses du 2026-10-04 (en relecture)** : intègre les arbitrages Q1–Q27 et A–D (errata E-10 à E-20, invariants INV-179 à INV-196) et les règles de la tranche Dépenses (cadrage 005, invariants INV-197 à INV-201) ; aligné sur le modèle de données SQLite **V3.13 (en relecture)**, le registre des invariants (v9) et les errata E-01 à E-20. Les passages dont le **mécanisme technique** reste à concevoir (exécution, remise détaillée) sont signalés comme tels et renvoient aux propositions techniques PT-xx du modèle de données §19 (PT-1 est tranché, PT-21 validé sur le principe).
Périmètre : Micro-entrepreneur BTP — prestations de services — franchise en base de TVA

⸻

## 1. Principe général

BATORYA Essentiel est organisé autour du dossier commercial et opérationnel, dont le **Bon de commande (BC)** constitue l'élément central après acceptation d'un devis.

Le modèle métier suit globalement cette chaîne :

Client → Devis → Bon de commande → Facturation → Règlements

À cette chaîne principale s'ajoutent :

* prestations du catalogue ;
* dépenses ;
* planification ;
* notes ;
* PV ;
* garanties ;
* analyses ;
* URSSAF ;
* documents ;
* historique.

Les objets métier sont indépendants des écrans qui les manipulent. Aucune interface ne doit devenir propriétaire des données ou des règles métier.

Ce document est la référence des **règles métier**. Il ne recopie pas le schéma SQLite : les tables, types, contraintes et triggers sont dans le modèle de données SQLite V3.13 (en relecture), et chaque règle importante y porte un identifiant d'invariant (`INV-xx`) défini dans `invariants.md`. Les écarts décidés par rapport au CDC gelé sont tracés dans `cdc-errata-v6.md`.

⸻

## 2. Règles transverses

### 2.1 Montants

* Tous les montants sont des **décimaux exacts** ; aucun nombre flottant n'est utilisé pour un montant.
* L'arrondi est **HALF_UP** (demi vers le haut en valeur absolue : 0,125 → 0,13 ; −0,125 → −0,13), et il est appliqué **une seule fois par ligne**.
* Les montants commerciaux finaux (totaux, acomptes, factures, règlements, dépenses) ont exactement **2 décimales**.
* La précision est **libre** uniquement là où elle est prévue : quantité, prix unitaire, remise « montant » de ligne, taux. Les pourcentages saisis ont 2 décimales.
* Aucune perte silencieuse de précision historique : une valeur historique qui ne tient pas dans la précision prévue n'est jamais tronquée en silence.
* Une valeur **négative** est conservée lorsqu'elle est mathématiquement et métier légitime : ligne de déduction d'une facture, CA encaissé d'une période URSSAF (après avoirs ou remboursements), écart de déclaration, base de calcul URSSAF et montant retenu d'un événement négatif. Partout ailleurs, un montant est positif ou nul.

### 2.2 Numérotation

Convention uniforme `TRI-00001-yy` (trigramme, compteur sur 5 chiffres, année sur 2 chiffres), compteur remis à 1 chaque année :

| Objet | Numéro |
|---|---|
| Devis | DEV-00001-26 |
| Bon de commande | BCD-00001-26 |
| Facture (situation, solde) | FAC-00001-26 |
| Acompte | ACP-00001-26 |
| Avoir | AVO-00001-26 |
| PV de réception | PVR-00001-26 |
| Levée de réserves | PVR-00001-26-01, PVR-00001-26-02… |
| Dépense | DEP-00001-26 |
| Client | CLI-0001 |
| Fournisseur | FOU-0001 |

* Les situations et les soldes partagent la même séquence `FAC`. Les codes client et fournisseur n'ont pas d'année.
* L'année d'un numéro est celle de la date métier du document (**validation** du devis, création du BC, émission de la facture, réception du PV, date de la dépense) et ne change jamais.
* **Un numéro définitif n'est jamais attribué deux fois (priorité absolue).** Un numéro peut être consommé sans objet si un crash ou un rollback survient pendant la finalisation (exemple : `DEV-00041` existe, `DEV-00042` n'existe pas, `DEV-00043` est attribué ensuite) : ce trou est acceptable et **n'est jamais récupéré**. Est interdit : `DEV-00042` attribué à un premier objet puis réattribué à un autre. Après attribution, un numéro n'est jamais réattribué, même après annulation de l'objet, restauration ou incident. Le dernier numéro attribué est mémorisé hors de la base métier pour qu'une restauration ou un incident ne ramène pas un compteur en arrière ; **le mécanisme technique (réservation du numéro committée avant la création de l'objet, double garde compteur + mémoire hors base métier) est tranché le 2026-10-03** (modèle de données §11.4, PT-1) ; sa seule limite est la restauration d'une base ancienne combinée à la perte de la mémoire des numéros.
* Un **devis brouillon** n'a pas de numéro et n'en consomme pas ; il le reçoit à sa validation. Il n'existe pas de facture brouillon.
* Factures, acomptes et avoirs suivent une chronologie continue : la date d'émission n'est jamais antérieure à la dernière date de la séquence.
* Les numéros ne sont pas configurables manuellement.

### 2.3 Snapshots et immutabilité

Un document conserve ses propres copies (snapshots) des informations client, entreprise et chantier, ainsi que de ses lignes. Une modification ultérieure du catalogue, d'un client ou des paramètres ne modifie jamais un document existant.

### 2.4 Conservation plutôt que suppression

* Tout objet portant un numéro définitif est **conservé** : il n'est jamais supprimé. Seul un objet sans numéro (le devis brouillon) peut être supprimé.
* Un document émis, un règlement, une garantie, un PV ou un événement d'historique n'est jamais supprimé pour corriger une erreur : il est annulé (date et motif) lorsque l'objet est annulable (devis, BC, dépense, règlement), ou corrigé par un document opposé. **Une facture validée n'est jamais annulée** : son erreur se corrige par un **avoir**.
* Les clients et fournisseurs sont conservés définitivement (§ 3, § 19).
* Les dérivés (états, reste à payer, CA) sont calculés, jamais saisis.
* Une relation historique ne change jamais silencieusement de cible (références stables).

⸻


## 3. Client

Le Client représente le donneur d'ordre.

**Données principales**

* identifiant interne ;
* code client (`CLI-0001`) ;
* nom, prénom ;
* adresse, code postal et ville ;
* téléphone, email ;
* notes ;
* dates de création et de modification.

Le code client est indépendant de la numérotation des documents.

**Conservation permanente (aucun statut)**

Un client est créé, modifié, conservé. Une fois son code attribué, il ne peut **pas être supprimé** et son code est **immuable**. Il n'existe ni archivage, ni désarchivage, ni statut actif/inactif, ni suppression logique, ni statut « à rattacher », ni mécanisme de réactivation. L'interface peut filtrer, rechercher et masquer par défaut un client sans activité récente ; ce n'est pas un état persistant.

**Règles**

* Un devis, un BC et une facture référencent toujours un client par identifiant (et portent en plus leur snapshot documentaire) ; le nom n'est jamais une clé.
* Un client nouveau est créé explicitement ; il n'est jamais créé implicitement à partir d'un nom saisi dans un document.
* Le client d'un document ne change jamais après coup (plus de « rattachement de client »). Un client issu de l'import dont l'identité est ambiguë est traité à l'import (modèle de données PT-3), jamais par un statut.

**Relations**

Un client peut posséder plusieurs devis, plusieurs BC et plusieurs factures.

⸻


## 4. Catalogue

### 4.1 Prestation

Une Prestation représente un élément commercial réutilisable dans les devis.

**Données principales**

* identifiant ;
* référence (code prestation) ;
* désignation, description ;
* catégorie (liste de référence) ;
* unité : `u`, `ens`, `ml`, `m2`, `m3` ;
* prix unitaire HT (précision libre) ;
* type de prestation : fourniture, pose, fourniture et pose ;
* garanties par défaut (un ou plusieurs types) ;
* actif / inactif.

**Règles**

* Une prestation n'est jamais la source historique d'un document existant : ses informations sont copiées dans la ligne du devis.
* Une prestation utilisée est désactivée, jamais supprimée.
* Le catalogue par défaut compte 204 prestations (catalogue de référence moins ELE-008, prestation « prise RJ45 Cat6 » supprimée). Il est chargé uniquement lors d'une nouvelle installation.
* Les garanties se configurent depuis la prestation du catalogue ; il n'existe pas de module « Garanties » séparé.

### 4.2 Catégories

Les catégories de prestations et les catégories de dépenses sont des listes de référence modifiables par l'utilisateur, avec leur ordre d'affichage et leur état actif.

⸻

## 5. Devis

Le Devis représente une proposition commerciale adressée à un client.

**Données principales**

* identifiant ;
* numéro (`DEV-00001-26`), **attribué à la validation** ;
* client et snapshots (client, entreprise, chantier) ;
* date de création, date de validité ;
* date d'acceptation, date de refus ;
* objet, notes ;
* lignes ;
* remise globale (aucune, pourcentage ou montant) ;
* acompte prévu (aucun, pourcentage ou montant) ;
* total HT ;
* statut, annulation (date et motif) ;
* devis d'origine éventuel (devis supplémentaire, PT-7) ;
* dates de création et de modification.

**Statuts**

* **Brouillon** ;
* En attente ;
* Accepté ;
* Refusé ;
* Annulé.

L'expiration de la validité est un état dérivé, jamais stocké.

**Règles (validées)**

* **Brouillon** : devis persistant, **sans numéro définitif**, librement modifiable (lignes, garanties de ligne, remises, snapshots), **supprimable physiquement tant qu'il n'a jamais été finalisé**. La suppression d'un brouillon ne consomme aucun numéro et emporte ses lignes. C'est le seul devis supprimable.
* **Finalisation du brouillon** : le devis reçoit son numéro définitif `DEV-xxxxx-YY`, consommé définitivement, et passe à **En attente**.
* **En attente** : le devis est **numéroté et reste modifiable** (le client peut demander des ajustements). Son numéro ne change jamais ; une modification ne crée pas de nouveau numéro de devis. Les modifications passent par le système de **révisions** (ci-dessous).
* **Accepté** : le devis et sa dernière version sont **verrouillés** — aucune modification directe (lignes, garanties de ligne, remises, acompte prévu, client, chantier, snapshots, total). Seuls évoluent son statut, les dates et motifs liés au statut. Un devis accepté engage les parties (art. 1193 du Code civil et documentation DGCCRF, vérifiés par Rémy) ; **il n'existe aucun module « avenant »** : une évolution du périmètre passe par un **nouveau devis**, accepté puis rattachable au même BC (§ 7).
* **Refusé** : conservé avec son numéro et **verrouillé** ; peut être **rouvert** (`refuse → en_attente`), le numéro restant identique ; une fois En attente, il est de nouveau modifiable. Le refus et la réouverture sont tracés dans l'historique. **Annulé** : terminal.

**Révisions de devis** *(règles validées le 2026-10-03 ; stockage : PT-21, validé sur le principe)*
* Le devis initial est la **version initiale** : ce n'est **pas** une « révision 0 » et aucune « Révision 0 » n'apparaît dans l'interface ni dans les documents. Les révisions commencent à **Révision 1** : version initiale → Révision 1 → Révision 2 → Révision 3… Elles s'affichent « `DEV-00042` — Révision 1 » ; le numéro `DEV-00042` reste strictement identique pendant toute la vie du devis.
* Une révision est une **nouvelle version complète** du devis, et non chaque modification élémentaire : aucune révision par frappe ni par modification de ligne.
* **Toute modification du contenu présenté au client ou ayant un impact quantitatif ou financier** (lignes, quantités, prix, remises, descriptions, prestations, garanties présentées, notes imprimées…) engage une phase de révision : BATORYA demande confirmation, l'utilisateur travaille sur la révision, puis valide la nouvelle version. Une modification purement technique, sans impact sur le contenu présenté, ne crée pas artificiellement de révision. Les **notes** présentées au client font partie de la révision.
* **Révision abandonnée** : une révision commencée mais jamais validée ne devient pas une version historique ; aucun numéro de révision n'est consommé ; le devis revient exactement à sa dernière version validée. Une phase de révision **sans modification significative** est refusée ou abandonnée. Un **refus ou une annulation** du devis pendant une révision abandonne la révision non validée.
* Une nouvelle révision part **toujours de la dernière version validée** ; reprendre une ancienne révision comme base n'est pas prévu à ce stade.
* À l'acceptation, la **dernière version validée** devient la version contractuelle de référence. Pendant une révision en cours, elle reste la référence : les documents et restitutions représentant le devis validé l'utilisent, et l'interface distingue clairement la version validée de la version en cours de modification.
* Après la finalisation, le **client du devis ne change plus** : changer de client exige un nouveau devis.

* La **date de création** est distincte de la **date d'acceptation** ; la date de validité reste modifiable tant que le devis n'est pas accepté, puis suit le verrouillage du contenu contractuel.
* Un devis accepté peut créer un nouveau BC ou rejoindre un BC existant éligible (§ 7), de façon idempotente (un devis n'appartient qu'à un seul BC).
* Un devis rattaché à un BC ne peut quitter « Accepté » que si ce BC est annulé ; **l'annulation d'un BC n'annule pas automatiquement ses devis**.
* Un devis à 0,00 € ne peut pas être accepté.
* Aucune notion de suppression d'un devis numéroté : un devis finalisé reste en base, quel que soit son statut.

**Relations**

Un devis appartient à un client, possède plusieurs lignes, peut appartenir à un BC, et peut être associé à des factures par l'intermédiaire du BC.

⸻


## 6. Ligne de devis

La LigneDevis est une photographie commerciale de la prestation au moment de son utilisation.

**Données**

* ordre ;
* référence de la prestation et identifiant de prestation ;
* désignation, description ;
* quantité, unité, prix unitaire HT ;
* remise de ligne (aucune, pourcentage, montant total de la ligne) ;
* type de prestation ;
* garanties de ligne (snapshots) ;
* montant calculé.

**Règles**

* Une ligne peut venir du catalogue (identifiant de prestation renseigné) ou être une **saisie libre** (identifiant de prestation vide). Il n'existe ni pseudo-prestation ni type de ligne « libre ».
* La référence de prestation saisie est conservée sur la ligne même si la prestation est ensuite désactivée.
* Le montant de ligne est `arrondi(quantité × prix − remise)`, avec un seul arrondi par ligne ; le total HT du devis est la somme des lignes moins la remise globale.
* La ligne reste autonome : une suppression ou une modification du catalogue ne la modifie jamais.

⸻

## 7. Bon de commande

Le BC est le dossier métier central après acceptation du devis. Il ne s'agit pas d'un simple état du devis.

**Données principales**

* identifiant ;
* numéro (`BCD-00001-26`) ;
* **devis rattachés** (un BC peut regrouper plusieurs devis acceptés du même client ; chaque devis reste identifiable ; devis d'origine = premier devis) ;
* client et snapshots (client, entreprise, chantier) ;
* date de création (jour d'enregistrement du BC) et date d'acceptation (celle du devis d'origine) ;
* dates de début et de fin éventuelles (utilisées par le Gantt) ;
* lignes copiées des devis rattachés ; la remise globale et l'acompte prévu restent portés par chaque devis ;
* **montant contractuel HT** (somme des devis rattachés) ;
* **facturation cumulée** (facturation nette) ;
* **avancement** (facturation nette / contractuel ; 100 % dès qu'un solde actif existe) ;
* date du 100 % facturé ;
* état, date de passage à Terminé ;
* annulation (date et motif) ;
* dates de création et de modification.

L'avancement mesure la facturation, jamais l'avancement physique du chantier (voir § 8, couche d'exécution). Facturation cumulée, avancement, date du 100 %, état et date de passage à Terminé sont recalculés par un seul service financier, à partir des factures et des règlements, dans la même transaction que l'opération.

**États**

* En cours ;
* Terminé ;
* Annulé.

**Règles**

* À sa création : **En cours**.
* **Plusieurs devis sur un BC** : un devis accepté du même client peut être rattaché à un BC existant **tant que la facture de solde n'a pas été rédigée/validée**. Un acompte déjà émis ou une ou plusieurs situations déjà émises **ne ferment pas** le BC ; plusieurs devis acceptés peuvent donc le rejoindre. Dès que le solde est rédigé/validé, le BC est clôturé commercialement : aucun nouveau devis ne peut lui être rattaché, et **un avoir ultérieur sur le solde ne le rouvre pas** (un nouveau BC est nécessaire). Un BC annulé ne peut pas recevoir de nouveau devis. Le rattachement copie les lignes et garanties de ligne du devis dans le BC ; les documents déjà émis ne sont pas modifiés.
* Le contenu contractuel du BC n'est **jamais réécrit rétroactivement** ; seul l'ajout d'un devis l'augmente.
* **Terminé** ⇔ un **solde actif** existe **et** la somme des restes dus des factures actives (hors avoirs) est nulle. Un solde à 0 € ne suffit pas tant qu'un acompte ou une situation reste dû. Un avoir n'est pas un encaissement ; il intervient par la réduction du reste dû.
* Le BC repasse En cours si un règlement est annulé ou si un avoir intervient et que la condition n'est plus remplie.
* **Annulation** : possible **quel que soit l'état de la facturation** (motif obligatoire). Le BC annulé est **conservé** avec son numéro, **ses devis (non annulés automatiquement)**, ses factures, règlements, avoirs, dépenses et son historique. Il ne peut plus poursuivre son cycle commercial normal : ni nouvel acompte, ni nouvelle situation, ni nouveau solde, ni nouveau devis rattaché. Les corrections de documents existants (avoir, règlement) restent possibles. Un BC annulé est terminal et ne participe plus au CA engagé.
* Un BC n'est jamais supprimé.
* Le BC n'est pas un document PDF autonome.

⸻


## 8. Lignes du BC, exécution et remise globale

**Lignes du BC**

Les lignes du BC sont une copie des lignes des devis rattachés (mêmes données, plus la référence de la ligne de devis d'origine). La copie est faite à la création du BC ou au rattachement d'un devis ; elles ne sont ensuite ni modifiées ni supprimées. Il n'y a plus de synchronisation avec le devis : le devis validé étant verrouillé, la cohérence est stable. Aucune facture ne référence une ligne du BC avant la première facture.

**Plus de « gel commercial »**

L'ancien mécanisme de gel (devis et BC modifiables jusqu'au premier encaissement d'acompte, à la première situation ou au solde, avec annulation automatique de l'acompte non réglé) est **supprimé** : le devis accepté est verrouillé (le devis En attente reste modifiable par révisions) et le contenu contractuel du BC est stable dès sa création. Le sort technique de la colonne `frozen_at` est une proposition (PT-8).

**Exécution (couche distincte du contractuel) — principes validés, schéma À CONCEVOIR**

* Le devis accepté reste contractuellement inchangé. BATORYA ne suit pas l'avancement physique automatiquement : l'utilisateur renseigne l'état réel connu.
* Une ligne peut être réalisée, partiellement réalisée par quantité, totalement abandonnée, ou voir une quantité ou un prix unitaire d'exécution différent du contractuel lorsque le métier le justifie.
* L'exécution distingue au minimum : contractuel, exécuté, abandonné, restant, facturé, payé.
* La partie abandonnée n'est plus à réaliser ni à facturer et reste visible historiquement ; si elle avait été facturée, la correction passe par un avoir. Une augmentation de périmètre passe par un nouveau devis.
* Le schéma de cette couche, les bornes de prix ou de quantité et la formule de la « base facturable » sont **à concevoir** (PT-12) : aucune table n'existe encore.

**Remise globale — principe validé, formule À CONCEVOIR**

La remise globale est attachée au contrat initial et n'est jamais recalculée sur le devis. En cas d'exécution partielle, elle est répartie **au prorata de la valeur exécutée/facturée**. Exemple : contractuel 10 000 €, remise 1 000 € (net 9 000 €), abandon 2 000 € → exécuté 8 000 €, remise affectée 800 €, net exécuté 7 200 € ; le devis reste à 10 000 € avec sa remise de 1 000 €. C'est une règle métier BATORYA (pratique comparable aux logiciels BTP), non une obligation légale. La formule détaillée et ses cas particuliers sont à concevoir (PT-13).

⸻

## 9. Verrouillage des documents

Aucun document n'évolue par un « gel » progressif :

* le **devis accepté** est verrouillé (§ 5) ;
* le **contenu contractuel du BC** est stable dès sa création (§ 7, § 8) ;
* la **facture validée** est immuable (§ 10) ;
* seuls évoluent les statuts, annulations et recalculs de caches prévus par chaque section.

⸻


## 10. Facture

La Facture représente un document de facturation **validé** : il n'existe **pas de brouillon persistant**. La facture est créée, numérotée et validée en une seule opération ; l'abandon d'une préparation avant validation ne crée aucun objet ; le numéro n'est attribué qu'à la validation.

**Types**

* Acompte ;
* Situation ;
* Solde ;
* Avoir.

Il n'existe pas de type `complete` en V6.

**Données principales**

* identifiant ;
* numéro ;
* type ;
* BC (le ou les devis sont accessibles par le BC) ;
* pour un acompte : le devis d'origine (un acompte par devis, PT-10) ;
* client et snapshots (client, entreprise, chantier) ;
* objet ;
* date d'émission ;
* date d'échéance (absente pour un avoir) ;
* lignes ;
* montant HT ;
* pour une situation : numéro d'ordre, mode de saisie (pourcentage ou montant), valeur saisie, avancement, montant HT facturé, valeurs figées (PT-11) ;
* pour un avoir : facture d'origine et motif ;
* date de création.

**Règles**

* Aucun statut n'est stocké : l'état de paiement est dérivé (§ 16). Aucune TVA (franchise en base).
* La date d'échéance = date d'émission + délai de paiement du snapshot entreprise.
* **Une facture validée est immuable**, jamais supprimée ni simplement éditée, et **jamais annulée**. Toute correction passe par un **avoir** (ou, selon le cas, un document correctif).
* Un **avoir total** permet l'émission d'une nouvelle facture du même type, avec un **nouveau numéro** ; la facture initiale et son avoir restent dans l'historique. L'unicité « une seule facture active du type » est reformulée en conséquence (mécanisme : PT-9).
* Numéros : `ACP-…` pour les acomptes, `AVO-…` pour les avoirs, `FAC-…` pour les situations et les soldes.
* La somme des lignes est égale au montant HT de la facture.
* Un règlement correspond à **une seule facture** ; un virement couvrant plusieurs factures est réparti explicitement par facture.

⸻


## 11. Ligne de facture

La LigneFacture est une photographie des éléments facturés. Elle ne dépend plus du catalogue ni du devis après émission.

**Données**

* ordre ;
* référence de prestation éventuelle ;
* désignation, description ;
* quantité, unité, prix ;
* remise ;
* type de ligne : **prestation**, **synthèse**, **déduction** ;
* montant ;
* référence éventuelle à la ligne de BC d'origine.

**Composition**

* acompte : une ligne de synthèse ;
* situation : une ligne de synthèse (le cumul et le déjà-facturé restent sur la facture) ;
* solde : les lignes de prestation du BC, puis des lignes de déduction (facturation antérieure, remise globale) ;
* avoir : lignes positives.

Une ligne de déduction est la seule ligne dont le montant est négatif.

⸻

## 12. Situation

Une Situation est une facture de type Situation, avec des informations permettant de représenter la progression facturée.

**Règles métier (validées)**

* La situation est **globale au BC** : elle porte sur l'ensemble du périmètre contractuel actuellement accepté (tous les devis rattachés).
* Elle est saisie **en pourcentage ou en montant**. Sont conservés : le mode de saisie, la valeur saisie, l'avancement calculé et le montant HT facturé ; ces données sont **figées** après validation.
* La cohérence se raisonne en **montants cumulés** : acomptes et facturations antérieures sont pris en compte, aucune double facturation.
* La facturation nette après la situation ne dépasse jamais le montant contractuel.
* Une situation atteignant 100 % n'existe pas : la facture finale est un **Solde**.
* Une situation ne peut plus être émise dès qu'un solde actif existe, ni sur un BC annulé.
* Une situation ne s'annule pas : sa correction passe par un avoir.

*Pour le pourcentage* : montant = `arrondi(contractuel × cumul % / 100) − facturation nette antérieure` (formule inchangée). *Ce que désigne exactement la valeur « montant » en mode montant (cumul ou montant de la période) est à concevoir (PT-11).*

⸻


## 13. Solde

Le Solde est **toujours le document final** de facturation du BC, y compris lorsqu'aucun acompte ni aucune situation ne l'a précédé.

* Montant du solde = montant contractuel − facturation nette avant le solde (en cas d'exécution : composition à concevoir, PT-12). Il est **positif ou nul** : un **solde à 0 €** est autorisé.
* Un seul solde actif par BC ; après un **avoir total** sur le solde, une nouvelle facture de solde peut être émise (nouveau numéro).
* Dès qu'un solde actif existe : plus d'acompte, plus de situation, **plus de nouveau devis rattaché au BC**, et **aucun avoir ne rouvre le BC** à de nouveaux devis.
* « 100 % facturé » signifie la **présence d'un solde actif**.
* L'émission du solde déclenche la création des garanties (§ 24).

⸻


## 14. Avoir

L'Avoir est une facture de type spécifique qui corrige financièrement une facturation existante.

**Données spécifiques**

* facture d'origine (acompte, situation ou solde, du même BC) ;
* motif (obligatoire) ;
* montant et lignes ;
* remboursements éventuels (règlements de type remboursement).

**Règles**

* L'avoir ne détruit ni ne modifie jamais la facture d'origine, qui reste dans l'historique. Une facture payée n'est jamais supprimée pour corriger une erreur.
* Le total des avoirs d'une facture ne dépasse pas son montant.
* Tous les avoirs réduisent la facturation nette. Avant le solde, un avoir sur acompte ou situation libère donc un montant refacturable ; après un solde actif, il ne rouvre pas le BC à de nouveaux devis. Un **avoir total** autorise une nouvelle facture du même type (nouveau numéro).
* **Un avoir n'est pas annulable** ; la correction d'un avoir erroné est à concevoir (PT-9).
* Un avoir absorbe la dette non encaissée de sa facture d'origine, puis constitue un **crédit** remboursable.
* Son impact sur le calcul URSSAF est déterminé par le référentiel réglementaire applicable.

⸻

## 15. Règlement

Le Règlement est une entité indépendante.

**Données**

* identifiant ;
* facture concernée ;
* **type** : encaissement ou remboursement ;
* date de l'événement ;
* montant (positif, non nul) ;
* mode : espèces, chèque, virement, carte, autre ;
* référence, note éventuelles ;
* annulation (date et motif) ;
* date de création.

**Règles**

* Une facture peut posséder **plusieurs règlements**.
* Un encaissement porte sur une facture active qui n'est pas un avoir et ne peut dépasser le reste dû. Un remboursement porte sur un **avoir** actif et ne peut dépasser le crédit disponible.
* Un règlement n'est jamais supprimé ni modifié : il peut être annulé une seule fois (date, motif). L'annulation d'un encaissement est refusée si elle rend le crédit inférieur aux remboursements actifs.
* Pour une facture hors avoir de montant M :
  * encaissé = somme des encaissements actifs ;
  * absorbé par avoirs = min(somme des avoirs, max(0, M − encaissé)) ;
  * **reste dû** = max(0, M − encaissé − absorbé) ;
  * **crédit** = somme des avoirs − absorbé − somme des remboursements actifs (jamais négatif).
* Le reste à payer est calculé et non saisi.

⸻

## 16. États dérivés

Jamais persistés.

**Facture hors avoir**

* **Entièrement créditée** si un ou plusieurs avoirs couvrent la totalité de son montant (état dérivé, définition exacte : PT-9) ;
* sinon **Réglée** si son reste dû est nul (y compris un solde à 0 € ou une dette couverte par avoirs) ;
* sinon **Partiellement réglée** si des encaissements existent ;
* sinon **En attente**.

**En retard** est un indicateur transversal : facture non entièrement créditée, reste dû positif et échéance dépassée. Une facture peut être Partiellement réglée **et** En retard.

**Avoir** : crédit disponible, ou soldé. Un avoir n'est jamais « en retard ».

**Garantie** : à surveiller ou échue (§ 24).

⸻

## 17. CA et analyses

BATORYA ne devient pas un logiciel comptable complet. Les analyses exploitent les modules métier ; aucune valeur d'analyse n'est stockée.

* **CA encaissé réel** : somme des encaissements nets des remboursements ;
* **CA engagé** : pour les BC **En cours** uniquement (un BC annulé ou terminé n'y figure pas), `max(0, (contractuel − avoirs) − (encaissements − remboursements))` ;
* **CA prévisionnel** : distinct des deux précédents.

Les dépenses servent à l'analyse de marge ; elles ne réduisent jamais le CA servant au calcul URSSAF.

Il n'existe plus de fournisseur archivé : tout fournisseur reste sélectionnable pour une nouvelle dépense.

Lorsqu'un BC atteint 100 % facturé, les dépenses peuvent encore lui être rattachées normalement pendant 30 jours calendaires à compter de `date_100_facture`. Après ce délai, le BC est considéré comme clôturé pour les nouvelles dépenses. BATORYA affiche alors une confirmation simple indiquant depuis combien de jours le BC est clôturé ; si l'utilisateur confirme, la dépense est rattachée. Il n'existe ni procédure de déblocage, ni autorisation supplémentaire, ni délai maximal de rattachement tardif. Cette règle ne s'applique pas à un BC annulé : aucun délai ni confirmation, même si `date_100_facture` est renseignée. Une modification de dépense qui conserve le même BC n'est pas un nouveau rattachement.

⸻

## 18. Dépense

La Dépense représente une charge enregistrée par l'entreprise.

**Données**

* identifiant ;
* numéro (`DEP-00001-26`) ;
* date de la dépense (`date_depense`) : date métier attribuée à la dépense par l'utilisateur ; proposée par défaut avec la date du jour, elle peut être une date antérieure correspondant à la date métier réelle de la dépense ; distincte de la date de création technique ;
* montant HT de la dépense : montant économique unique, **strictement positif** (supérieur à zéro), exact au centime ; sans TVA ni montant TTC ;
* catégorie (liste de référence) ;
* description ;
* fournisseur éventuel ;
* BC éventuel ;
* pièce jointe éventuelle ;
* notes ;
* dates de création et de modification.

**Règles**

* Une dépense est **globale** ou rattachée à un BC.
* Aucune gestion du paiement fournisseur en V6 : ni statut payé / non payé, ni échéance, ni règlement fournisseur.
* **Correction et annulation** : une dépense active peut être corrigée (erreur de saisie) ; elle peut être **annulée** lorsqu'elle ne doit plus participer aux calculs métier. Une dépense annulée reste en base avec son numéro, son historique et ses relations (BC, fournisseur, catégorie) ; elle est exclue des **calculs actifs** — totaux de dépenses, marges, analyses économiques et indicateurs actifs (principe validé, INV-200) — et reste consultable dans l'historique. Les formules détaillées de chaque analyse ne sont pas spécifiées ici (PT-14). Une dépense numérotée n'est jamais supprimée. L'annulation n'est pas un statut de paiement.
* Une dépense peut être créée sur un BC annulé, lui être rattachée ultérieurement ou y rester liée : aucun délai ni confirmation de rattachement tardif pour un BC annulé.
* `date_depense` est la seule date métier de la dépense : ni date de facture, ni échéance, ni date de paiement. Sa correction ne peut pas changer l'année du numéro ; si c'était nécessaire, la dépense est annulée puis ressaisie sous un nouveau numéro (jamais de renumérotation).

⸻

## 19. Fournisseur

Le Fournisseur est une entité indépendante.

**Données**

* identifiant ;
* code (`FOU-0001`) ;
* nom / raison sociale ;
* coordonnées ;
* notes ;

* dates de création et de modification.

Une dépense référence le fournisseur par identifiant. Comme un client, un fournisseur est **conservé définitivement** : code immuable, aucune suppression, aucun archivage ni statut, aucune réactivation.

⸻

## 20. Planification

Le module s'appelle **Planification** (et non « Planning ») et comporte deux onglets : **Calendrier** et **Gantt**.

**Calendrier**

Événements typés : intervention, travaux, rendez-vous client, réunion, appel, administratif, congé, indisponibilité, autre. Un événement a un titre, des dates de début et de fin (journée entière ou avec horaires), un lieu et une description.

* `intervention` et `travaux` sont **obligatoirement rattachés à un BC** ;
* `congé` et `indisponibilité` n'ont **jamais** de BC ;
* les autres types peuvent être rattachés ou non à un BC.

**Gantt**

Le Gantt est lié aux dates de début et de fin du BC ; un BC sans dates n'a pas de barre. Il ne constitue pas une gestion de chantier indépendante du BC.

**Règles**

* La planification n'a **aucune autorité sur le cycle de vie du BC** : une intervention planifiée ne rend pas un BC actif ou terminé.
* Les jours ouvrés et les jours fériés français sont pris en compte.
* Aucune synchronisation avec Outlook ou Google en V6.

⸻

## 21. Note

La Note est une information interne libre rattachée à un BC.

**Données** : identifiant, BC concerné, contenu, dates de création et de modification.

Un BC peut avoir plusieurs notes, modifiables et supprimables. Les notes ne constituent pas un système de tâches et n'affectent aucun montant.

⸻

## 22. PV de réception

Le PV représente un événement documentaire de réception.

**Données**

* identifiant ;
* numéro (`PVR-00001-26`) ;
* BC ;
* date de réception ;
* type : réception sans réserve, réception avec réserves, levée de réserves ;
* snapshots (chantier, client, entreprise) ;
* observations, réserves ;
* PV d'origine et suffixe (levée de réserves) ;
* date de création.

**Règles**

* Le PV est **facultatif** : il ne conditionne ni le solde, ni l'état Terminé, ni les garanties. Plusieurs PV initiaux par BC ne sont pas interdits.
* Les réserves sont renseignées si et seulement si la réception est avec réserves.
* Un PV est **immuable dès son émission** (ni modification, ni suppression).

⸻

## 23. Levée de réserves

La levée de réserves n'est pas une modification du PV initial : elle crée un **nouveau PV**.

* Le nouveau PV référence le PV d'origine, qui doit être une réception avec réserves **du même BC**. Une levée ne porte jamais sur une levée.
* Son numéro est celui du PV d'origine suivi d'un suffixe sur 2 chiffres, en séquence par PV d'origine : `PVR-00001-26`, puis `PVR-00001-26-01`, `PVR-00001-26-02`.
* Le PV d'origine reste inchangé. La levée ne modifie pas la date de début du suivi interne des garanties.

⸻

## 24. Garantie

La Garantie représente le suivi interne d'une obligation de garantie associée à une prestation du BC.

**Configuration et snapshots**

* Les garanties se configurent par prestation dans le Catalogue (un ou plusieurs types) ; ces valeurs sont des défauts.
* Elles sont copiées (snapshot) sur les lignes de devis puis de BC (à la création du BC ou au rattachement d'un devis) ; une modification du catalogue ne change jamais une garantie existante.
* **Principe inchangé** : une ligne de devis modifiée (brouillon) suit le principe de garantie existant ; une ligne **entièrement supprimée** n'existe plus, et sa garantie liée non plus. Aucun nouveau système de garantie n'est créé.

**Données d'une garantie générée**

* BC et ligne de BC concernée ;
* type de garantie : parfait achèvement (1 an), biennale (2 ans), décennale (10 ans) ;
* date de déclenchement ;
* date de fin de suivi ;
* facture de déclenchement (le solde).

**Règle de déclenchement V6**

Les garanties sont générées **à l'émission du solde actif** (franchissement de 100 % facturé). Elles ne dépendent pas :

* du PV ;
* de la réception ;
* des réserves ni de leur levée ;
* du **paiement** du solde.

La date de déclenchement est la date d'émission de ce solde ; la création est idempotente (la première date est conservée) ; une garantie n'est ni modifiée ni supprimée, même si un avoir (y compris total) est émis sur le solde ou si un règlement intervient. Tout devis rattaché au BC l'ayant été avant la rédaction du solde, toutes les lignes du BC existent à ce moment. Aucune garantie n'est recréée automatiquement à partir de données historiques importées.

Le suivi est **indicatif** : l'interface affiche toujours « Suivi interne BATORYA — date indicative ». L'état (à surveiller avant la fin du suivi, échue après) est dérivé.

⸻

## 25. Document

Le Document représente la matérialisation PDF d'un objet métier.

* **SQLite = source de vérité** ; le PDF est une représentation générée à partir des données métier.
* Types : devis, acompte, situation, solde, avoir, PV. Le BC n'est pas un document autonome.
* Une régénération crée une **nouvelle version** ; le contenu d'un document n'est jamais supprimé.
* Un document est localisé par un dossier de travail (racine de stockage) et un chemin relatif, avec une empreinte du contenu. Un document dont la racine est inconnue de la machine courante est « non localisable » et propose un remappage.

⸻

## 26. Historique

L'Historique représente les événements métier significatifs ; il est **append-only** et indépendant de l'interface.

Événements tracés (historique métier utile : quoi, quand, avant/après lorsque pertinent, pourquoi lorsque nécessaire, qui lorsque l'information existe ; aucune journalisation de chaque frappe) : création, **validation** (finalisation du devis), modification (devis brouillon), **révisions de devis** (création, validation, abandon), acceptation, refus, **réouverture d'un devis**, annulation (devis, BC, dépense), **rattachement d'un devis à un BC**, événements d'exécution significatifs, émission, règlement et annulation de règlement, remboursement, avoir, passage à Terminé et retour à En cours, déclenchement de garantie, déclaration et correction URSSAF, import de données historiques, restauration. *(Supprimés : gel, annulation automatique d'un acompte, rattachement d'un client. Liste exacte : PT-15.)*

L'acteur d'un événement est l'utilisateur, le système ou l'import.

⸻

## 27. URSSAF

L'URSSAF n'est pas une propriété du BC ou de la facture : c'est un domaine transversal exploitant les encaissements.

**Données et règles**

* **Profil** : date de début d'activité, périodicité (mensuelle ou trimestrielle), ACRE. Il est saisi par l'utilisateur et conservé par versions (une ligne par changement).
* **Périodes déclaratives** : CA encaissé, cotisations estimées, CFP, statut (à déclarer, déclarée, à vérifier). Une période à CA nul existe ; la première peut être partielle.
* **CA encaissé** : somme des événements retenus (encaissements, et avoirs ou remboursements selon le référentiel). Une facture émise n'est pas du CA encaissé ; un paiement partiel compte à hauteur du montant encaissé.
* **Verrouillage** : une période déclarée est verrouillée ; seul son statut peut alors évoluer.
* **Corrections** : un événement postérieur touchant une période verrouillée ne modifie pas la période ; il crée une **correction** tracée et la période passe « à vérifier » jusqu'à résolution.
* **Reproductibilité** : chaque période conserve le détail de son calcul et la version du référentiel utilisée.
* Les événements négatifs (avoirs, remboursements) sont traités selon le référentiel applicable.
* Aucune déclaration officielle automatique.

Principe : un règlement constitue l'événement financier qui détermine l'encaissement.

⸻

## 28. Référentiel réglementaire

Le référentiel réglementaire est une composante distincte, propre à chaque période.

* Chaque version est identifiable, avec sa date de début d'effet.
* Les versions sont **append-only** : la date de début d'effet est strictement croissante, une nouvelle version s'applique aux périodes dont le début est postérieur, et les versions anciennes restent conservées pour reproduire les calculs historiques.
* Une version future peut être importée avant son entrée en vigueur.
* Il est distribué par les Services BATORYA.

⸻

## 29. Paramètres entreprise

Les paramètres de l'entreprise ne sont pas une entité commerciale : ils représentent la configuration professionnelle utilisée par les différents services.

Ils comprennent notamment :

* identité (forme juridique, nom, prénom, nom commercial) ;
* coordonnées ;
* informations administratives (SIREN, SIRET, autres identifiants) ;
* informations bancaires facultatives, affichées sur les documents uniquement si l'utilisateur le choisit ;
* paramètres commerciaux : délai de paiement (0 à 60 jours), modes de règlement par défaut, mentions et conditions commerciales ;
* paramètres de sauvegarde, configuration Gmail, Services BATORYA, dossier de travail ;
* profil utilisateur.

Les valeurs courantes ne reconstruisent jamais un document historique (snapshots). Les mentions légales obligatoires ne peuvent pas être retirées par paramétrage. Les paramètres URSSAF restent dans leur domaine dédié.

⸻

## 30. Utilisateur local

BATORYA Essentiel est une application locale. Le compte local est créé obligatoirement au premier démarrage, avec un identifiant et un mot de passe (nom et prénom facultatifs) ; tant qu'il n'existe pas, seul l'écran de création du compte est accessible. Le profil sert à identifier l'utilisateur local, protéger l'accès et gérer le mot de passe local (conservé sous forme de hachage, jamais en clair). Il n'existe pas de comptes distants ni de rôles.

⸻

## 31. Sauvegarde, restauration et import de données historiques

### 31.1 Données métier et données machine

* **Base métier** (SQLite) : sauvegardée et restaurée.
* **Données machine** (base séparée, jamais sauvegardée ni restaurée) : utilisateur local et mot de passe, licence, identifiant d'installation, dossiers de stockage, préférences de sauvegarde, état Gmail, **mémoire des derniers numéros attribués (high-water)**.
* Les secrets (clé de licence, jetons Gmail) sont dans le coffre du système d'exploitation.

### 31.2 Sauvegarde

* Sauvegarde **SQLite** cohérente (manuelle, automatique, à la fermeture), par un seul moteur. Par défaut : sauvegarde automatique activée toutes les 30 minutes et sauvegarde à chaque fermeture activée.
* **Export JSON** : consultation et archivage uniquement ; ce n'est pas un format de restauration.

### 31.3 Restauration

Restauration **validée et atomique** : validation du fichier, refus si la version du schéma est supérieure à celle supportée, migrations de schéma sur une copie, contrôles d'intégrité, **sauvegarde de sécurité** de la base courante avant remplacement, remplacement atomique, contrôles après restauration.

Une restauration ne modifie jamais le mot de passe local, la licence, l'identifiant d'installation ni le dossier de travail. Après restauration, aucun numéro déjà attribué n'est réutilisé (§ 2.2).

### 31.4 Import de données historiques

BATORYA V6 n'embarque **aucune migration de l'ancien format V2**. La seule reprise de données historiques prévue suit le flux :

JSON V2 → convertisseur externe → `import-v6.json` → import V6

* Le convertisseur externe porte les particularités de la V2 ; V6 n'adapte pas son modèle à la V2.
* L'import V6 n'accepte qu'un fichier `import-v6.json` conforme (lecteur strict), en deux temps (validation sans écriture, puis transaction unique), **uniquement sur une base métier vide**.
* Toutes les règles métier s'appliquent aux données importées. La seule exception est la conservation du numéro historique des devis, factures et PV importés, déjà remis aux clients.
* Les valeurs dérivées (état du BC, avancement) sont recalculées par V6.
* Les compteurs historiques compatibles initialisent la numérotation V6 ; un saut de numéro est acceptable.
* Les éléments à contrôler sont signalés à l'utilisateur (bandeau) jusqu'à traitement ; les données non représentables sont conservées pour consultation.

⸻

## 32. Licence et services distants

La licence est séparée du domaine métier : elle représente l'autorisation d'utilisation de BATORYA Essentiel sur une machine donnée et est contrôlée par les **Services BATORYA**.

* Les données métier restent **100 % locales** ; le service distant est limité à la licence, aux mises à jour et aux référentiels réglementaires. La licence ne contient ni ne transmet jamais de données commerciales.
* Aucune dépendance réseau pour le fonctionnement métier courant.
* Vérification trimestrielle ; en cas d'échec, **15 jours** de grâce en usage complet ; ensuite, consultation et exports seuls (création, modification, suppression et facturation bloquées). Une vérification réussie rétablit tout. Il n'y a pas d'autre cas de verrouillage.

⸻

## 33. Email et rapports d'erreur

* Un service d'envoi d'e-mails central (EmailService) s'appuie sur **Gmail, facultatif**.
* L'envoi d'un PDF (devis, facture, autre document) est toujours **manuel**, déclenché par l'utilisateur ; aucun envoi automatique, et jamais de faux envoi si Gmail n'est pas configuré ou si l'envoi échoue.
* Le **rapport d'erreur** est généré sans table métier, copiable ou enregistrable, et envoyé manuellement.

⸻

## 34. Vue d'ensemble des relations

```
CLIENT
   │
   ├── DEVIS
   │      │
   │      └── LIGNES DEVIS (+ garanties de ligne)
   │
   └── BC  (regroupe un ou plusieurs devis acceptés ; un devis appartient à un seul BC)
          │
          ├── LIGNES BC (+ garanties de ligne)
          │
          ├── FACTURES (acompte, situation, solde, avoir)
          │      │
          │      ├── LIGNES FACTURE
          │      └── RÈGLEMENTS (encaissements, remboursements)
          │
          ├── DÉPENSES
          ├── PLANIFICATION (Calendrier ; le Gantt lit les dates du BC)
          ├── NOTES
          ├── PV
          │      └── LEVÉES DE RÉSERVES
          └── GARANTIES (générées au solde actif)

En parallèle :

CATALOGUE
   │
   └── PRESTATIONS (+ garanties par défaut)
          └── copiées comme snapshots dans les lignes de devis
FOURNISSEUR
   └── DÉPENSES
RÈGLEMENTS
   └── URSSAF ── PÉRIODES DÉCLARATIVES ── CORRECTIONS
RÉFÉRENTIEL RÉGLEMENTAIRE
   └── URSSAF
PARAMÈTRES ENTREPRISE
   ├── DOCUMENTS / PDF
   ├── EMAIL
   └── SERVICES BATORYA
HISTORIQUE (transversal)
```

⸻

## 35. Règle d'architecture fondamentale

Aucune entité métier ne doit connaître l'implémentation technique de la persistance. Le domaine métier ne dépend :

* ni de SQLite ;
* ni de React ;
* ni de Tauri ;
* ni du système de fichiers ;
* ni de l'interface graphique.

Les relations définies ici sont traduites en repositories et en tables SQLite (modèle de données SQLite V3.13, en relecture).

⸻

## 36. Règles d'intégrité majeures

Le modèle V6 garantit notamment que :

1. un document conserve son historique après modification du catalogue, des paramètres ou du référentiel (snapshots) ;
2. un devis accepté crée un BC ou rejoint un BC existant éligible, et n'appartient qu'à un seul BC ; un BC peut regrouper plusieurs devis tant que sa facture de solde n'a pas été rédigée/validée ;
3. un BC est Terminé seulement si un solde actif existe et que le reste dû des factures actives (hors avoirs) est nul ;
4. un devis accepté est verrouillé (le devis En attente reste modifiable par révisions) ; le contenu contractuel du BC est stable ; un devis brouillon, jamais finalisé, est le seul devis supprimable ;
5. une facture validée n'est ni supprimée, ni annulée, ni éditée : l'avoir corrige ; il n'y a pas de facture brouillon ;
6. un BC peut être annulé quel que soit l'état de la facturation ; il est alors conservé avec ses devis (non annulés automatiquement), factures, règlements, dépenses et historique, et ne reçoit plus de nouveau document commercial ;
7. le solde est toujours la facture finale ; un solde à 0 € est autorisé ; aucune situation, aucun acompte et aucun nouveau devis après un solde actif ;
8. une facture peut recevoir plusieurs règlements ; un règlement correspond à une seule facture ; le reste à payer est calculé, jamais saisi ; un encaissement ne dépasse pas le reste dû ;

9. une facture payée ne disparaît jamais pour corriger une erreur : l'avoir corrige ;
10. un avoir conserve la référence de la facture concernée ; le total des avoirs ne dépasse pas l'origine ; un remboursement ne dépasse pas le crédit ;
11. un BC annulé n'est plus comptabilisé dans le CA engagé ; une dépense annulée est exclue des calculs opérationnels concernés ;
12. les garanties sont générées à l'émission du solde actif, indépendamment du paiement et du PV, et ne sont jamais recalculées ;
13. un PV émis ne peut plus être modifié ; une levée de réserves crée un nouveau PV ;
14. les calculs URSSAF utilisent les encaissements réels ; une période verrouillée n'est corrigée que par le mécanisme de correction ;
15. les versions réglementaires historiques restent reproductibles ;
16. les montants sont manipulés avec une précision décimale exacte, arrondis HALF_UP une fois par ligne ;
17. un numéro définitif n'est jamais attribué deux fois ; un trou après crash ou rollback est acceptable et n'est jamais récupéré ; clients et fournisseurs sont conservés définitivement ;
18. les données métier restent locales ; aucune fonctionnalité distante n'est nécessaire au fonctionnement normal ;
19. SQLite est la source de vérité ; les PDF, exports et sauvegardes en sont dérivés ;
20. la seule reprise de données historiques passe par un `import-v6.json` conforme, sur base vide, en transaction unique.

⸻

## 37. Statut de ce document

Ce document est le modèle métier de BATORYA Essentiel V6. Il est aligné sur :

* le modèle de données SQLite V6 (V3.13, en relecture) ;
* le registre des invariants (`invariants.md`, version 7) ;
* les errata au CDC gelé (`cdc-errata-v6.md`, E-01 à E-20).

**Hors périmètre d'Essentiel V6** : le **pointage salarié** relève de BATORYA Entreprise et n'est ni conçu ni préparé ici (INV-195). **Non tranchés (propositions techniques)** : schéma d'exécution et formule de remise (PT-12, PT-13), définition technique de « facture active » (PT-9). Le mécanisme du numéro et du high-water (PT-1) est tranché le 2026-10-03 et le stockage des révisions de devis (PT-21) est validé sur le principe.

Il ne définit pas les tables SQLite, les types SQL, les index, les repositories, les services TypeScript, les composants React ni les commandes Tauri : ces éléments relèvent des documents techniques correspondants.
