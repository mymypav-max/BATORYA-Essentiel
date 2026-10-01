# BATORYA Essentiel

**Modèle métier V6**

Produit : BATORYA Essentiel
Version : V6
Statut : Modèle métier — mis à jour le 2026-10-01, aligné sur le modèle de données SQLite V3.10, le registre des invariants (v4) et les errata E-01 à E-09
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

Ce document est la référence des **règles métier**. Il ne recopie pas le schéma SQLite : les tables, types, contraintes et triggers sont dans le modèle de données SQLite V3.10, et chaque règle importante y porte un identifiant d'invariant (`INV-xx`) défini dans `invariants.md`. Les écarts décidés par rapport au CDC gelé sont tracés dans `cdc-errata-v6.md`.

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
* L'année d'un numéro est celle de la date métier du document (création du devis et du BC, émission de la facture, réception du PV, date de la dépense) et ne change jamais.
* **Un numéro déjà attribué n'est jamais réutilisé ; un trou de numérotation est acceptable.** Le dernier numéro attribué est mémorisé hors de la base métier, pour qu'une restauration ou un incident ne puisse pas ramener un compteur en arrière.
* Factures, acomptes et avoirs suivent une chronologie continue : la date d'émission n'est jamais antérieure à la dernière date de la séquence.
* Les numéros ne sont pas configurables manuellement.

### 2.3 Snapshots et immutabilité

Un document conserve ses propres copies (snapshots) des informations client, entreprise et chantier, ainsi que de ses lignes. Une modification ultérieure du catalogue, d'un client ou des paramètres ne modifie jamais un document existant.

### 2.4 Annulation plutôt que suppression

Un document émis, un règlement, une garantie, un PV ou un événement d'historique n'est jamais supprimé pour corriger une erreur : il est annulé (date et motif) ou corrigé par un document opposé (avoir). Les dérivés (états, reste à payer, CA) sont calculés, jamais saisis.

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
* statut ;
* dates de création et de modification.

Le code client est indépendant de la numérotation des documents.

**Statuts**

* **actif** ;
* **archivé** : un client ayant un historique n'est jamais supprimé ;
* **à rattacher** : statut réservé à un client issu de l'import de données historiques, en attente de rattachement à un client existant. Le rattachement réaffecte les documents concernés, est tracé dans l'historique et ne modifie pas les snapshots. C'est la seule modification de client autorisée sur un document gelé.

**Règles**

* Un devis, un BC et une facture référencent toujours un client par identifiant (et portent en plus leur snapshot documentaire) ; le nom n'est jamais une clé.
* Un client nouveau est créé explicitement ; il n'est jamais créé implicitement à partir d'un nom saisi dans un document.

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
* numéro (`DEV-00001-26`) ;
* client et snapshots (client, entreprise, chantier) ;
* date de création, date de validité ;
* date d'acceptation, date de refus ;
* objet, notes ;
* lignes ;
* remise globale (aucune, pourcentage ou montant) ;
* acompte prévu (aucun, pourcentage ou montant) ;
* total HT ;
* statut, gel, annulation (date et motif) ;
* dates de création et de modification.

**Statuts**

* En attente ;
* Accepté ;
* Refusé ;
* Annulé.

L'expiration de la validité est un état dérivé, jamais stocké.

**Règles**

* La **date de création** est distincte de la **date d'acceptation** ; la date de création est immuable, la date de validité reste modifiable.
* Un devis est modifiable s'il est En attente, ou Accepté et **non gelé**. Un devis Refusé ou Annulé est immuable.
* Le devis est le **seul point d'édition** : toute modification d'un devis accepté non gelé régénère le BC correspondant (lignes, garanties de lignes, montant contractuel, snapshots).
* Un devis accepté produit **un seul BC**, de façon idempotente.

**Relations**

Un devis appartient à un client, possède plusieurs lignes, peut produire un BC, et peut être associé à des factures par l'intermédiaire du BC.

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
* devis d'origine (un seul BC par devis) ;
* client et snapshots (client, entreprise, chantier) ;
* date de création (= date d'acceptation) ;
* dates de début et de fin éventuelles (utilisées par le Gantt) ;
* lignes, remise et acompte prévus (copiés du devis) ;
* **montant contractuel HT** ;
* **facturation cumulée** (facturation nette) ;
* **avancement** (facturation nette / contractuel ; 100 % dès qu'un solde actif existe) ;
* date du 100 % facturé ;
* état, date de passage à Terminé ;
* gel, annulation (date et motif) ;
* dates de création et de modification.

L'avancement mesure la facturation, jamais l'avancement physique du chantier. Facturation cumulée, avancement, date du 100 %, état et date de passage à Terminé sont recalculés par un seul service financier, à partir des factures et des règlements, dans la même transaction que l'opération.

**États**

* En cours ;
* Terminé ;
* Annulé.

**Règles**

* À sa création : **En cours**.
* **Terminé** ⇔ un **solde actif** existe **et** la somme des restes dus des factures actives (hors avoirs) est nulle. Un solde à 0 € ne suffit pas tant qu'un acompte ou une situation reste dû. Un avoir n'est pas un encaissement ; il intervient par la réduction du reste dû.
* Le BC repasse En cours si un règlement ou un avoir est annulé et que la condition n'est plus remplie.
* **Annulation** : interdite directement dès qu'une facture autre qu'un acompte non réglé existe ; une situation émise (même annulée) l'interdit toujours ; un encaissement l'interdit. Un acompte non réglé est annulé avec le BC. La correction passe sinon par avoir ou annulation de facture.
* Un BC annulé reste conservé dans l'historique et ne participe plus au CA engagé.
* Le BC n'est pas un document PDF autonome.

⸻

## 8. Lignes du BC

Les lignes du BC sont une copie des lignes du devis (mêmes données, plus la référence de la ligne de devis d'origine).

* **Avant le gel**, elles sont **synchronisées** avec le devis : toute modification du devis les régénère dans la même transaction, avec leurs garanties de lignes et le montant contractuel.
* **Après le gel**, elles ne bougent plus.
* Aucune facture ne référence une ligne du BC avant le gel.

⸻

## 9. Gel commercial

Le gel fige la structure commerciale du devis **et** du BC. Il est posé dans la transaction de l'événement qui le provoque, au premier de :

1. le premier **encaissement actif**, même partiel, sur un acompte ;
2. l'émission d'une **situation** ;
3. l'émission du **solde**.

* Un acompte émis mais non encaissé **ne gèle pas**. Si le devis ou le BC est alors modifié, l'acompte non réglé est **annulé automatiquement** (acteur système) et peut être réémis.
* Le gel est **irréversible** ; l'annulation d'une facture ne dégèle pas.
* Une fois gelés, le devis et le BC n'acceptent plus que les changements de statut, d'annulation, de rattachement client et, pour le BC, les recalculs de caches et les dates de début et de fin.

⸻

## 10. Facture

La Facture représente un document de facturation **émis** : il n'existe pas de brouillon.

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
* BC (le devis est accessible par le BC) ;
* client et snapshots (client, entreprise, chantier) ;
* objet ;
* date d'émission ;
* date d'échéance (absente pour un avoir) ;
* lignes ;
* montant HT ;
* annulation (date et motif) ;
* pour une situation : numéro d'ordre, avancement cumulé, montant déjà facturé ;
* pour un avoir : facture d'origine et motif ;
* date de création.

**Règles**

* Aucun statut n'est stocké : l'état de paiement est dérivé (§ 16). Aucune TVA (franchise en base).
* La date d'échéance = date d'émission + délai de paiement du snapshot entreprise.
* Une facture émise est immuable, sauf son annulation (une seule fois) et le rattachement client.
* Numéros : `ACP-…` pour les acomptes, `AVO-…` pour les avoirs, `FAC-…` pour les situations et les soldes.
* La somme des lignes est égale au montant HT de la facture.

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

**Données spécifiques**

* numéro d'ordre de situation ;
* avancement cumulé (pourcentage) ;
* montant déjà facturé (facturation nette avant la situation).

**Règles**

* Montant de la situation = `arrondi(contractuel × cumul % / 100) − facturation nette antérieure`.
* La facturation nette après la situation ne dépasse jamais le montant contractuel.
* Une situation atteignant 100 % n'existe pas : la facture finale est un **Solde**.
* Une situation ne peut plus être émise dès qu'un solde actif existe.
* Une situation n'est annulable que si c'est la dernière situation active, sans solde postérieur, et sans encaissement actif ni avoir actif sur elle.

⸻

## 13. Solde

Le Solde est **toujours le document final** de facturation du BC, y compris lorsqu'aucun acompte ni aucune situation ne l'a précédé.

* Montant du solde = montant contractuel − facturation nette avant le solde. Il est **positif ou nul** : un **solde à 0 €** est autorisé (100 % déjà couvert par les acomptes et situations).
* Un seul solde actif par BC. Un solde annulé peut être réémis.
* Dès qu'un solde actif existe : plus d'acompte, plus de situation, et **aucun avoir ne rouvre la facturation** (aucun nouveau solde par avoir).
* « 100 % facturé » signifie la **présence d'un solde actif**.
* L'émission du solde déclenche la création des garanties (§ 24) et le gel.

⸻

## 14. Avoir

L'Avoir est une facture de type spécifique qui corrige financièrement une facturation existante.

**Données spécifiques**

* facture d'origine (acompte, situation ou solde, non annulée, du même BC) ;
* motif (obligatoire) ;
* montant et lignes ;
* remboursements éventuels (règlements de type remboursement).

**Règles**

* L'avoir ne détruit ni ne modifie jamais la facture d'origine, qui reste dans l'historique. Une facture payée n'est jamais supprimée pour corriger une erreur.
* Le total des avoirs actifs d'une facture ne dépasse pas son montant.
* Tous les avoirs actifs réduisent la facturation nette. Avant le solde, un avoir sur acompte ou situation libère donc un montant refacturable ; après un solde actif, il ne rouvre rien.
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
  * absorbé par avoirs = min(somme des avoirs actifs, max(0, M − encaissé)) ;
  * **reste dû** = max(0, M − encaissé − absorbé) ;
  * **crédit** = somme des avoirs actifs − absorbé − somme des remboursements actifs (jamais négatif).
* Le reste à payer est calculé et non saisi.

⸻

## 16. États dérivés

Jamais persistés.

**Facture hors avoir**

* **Annulée** si elle est annulée ;
* sinon **Réglée** si son reste dû est nul (y compris un solde à 0 € ou une dette couverte par avoirs) ;
* sinon **Partiellement réglée** si des encaissements existent ;
* sinon **En attente**.

**En retard** est un indicateur transversal : facture non annulée, reste dû positif et échéance dépassée. Une facture peut être Partiellement réglée **et** En retard.

**Avoir** : annulé, crédit disponible, ou soldé. Un avoir n'est jamais « en retard ».

**Garantie** : à surveiller ou échue (§ 24).

⸻

## 17. CA et analyses

BATORYA ne devient pas un logiciel comptable complet. Les analyses exploitent les modules métier ; aucune valeur d'analyse n'est stockée.

* **CA encaissé réel** : somme des encaissements nets des remboursements ;
* **CA engagé** : pour les BC **En cours** uniquement (un BC annulé ou terminé n'y figure pas), `max(0, (contractuel − avoirs actifs) − (encaissements − remboursements))` ;
* **CA prévisionnel** : distinct des deux précédents.

Les dépenses servent à l'analyse de marge ; elles ne réduisent jamais le CA servant au calcul URSSAF.

Un fournisseur archivé reste consultable pour l'historique mais ne peut pas être sélectionné pour une nouvelle dépense.

Lorsqu'un BC atteint 100 % facturé, les dépenses peuvent encore lui être rattachées normalement pendant 30 jours calendaires à compter de `date_100_facture`. Après ce délai, le BC est considéré comme clôturé pour les nouvelles dépenses. BATORYA affiche alors une confirmation simple indiquant depuis combien de jours le BC est clôturé ; si l'utilisateur confirme, la dépense est rattachée. Il n'existe ni procédure de déblocage, ni autorisation supplémentaire, ni délai maximal de rattachement tardif.

⸻

## 18. Dépense

La Dépense représente une charge enregistrée par l'entreprise.

**Données**

* identifiant ;
* numéro (`DEP-00001-26`) ;
* date ;
* montant réellement payé (franchise de TVA) ;
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

⸻

## 19. Fournisseur

Le Fournisseur est une entité indépendante.

**Données**

* identifiant ;
* code (`FOU-0001`) ;
* nom / raison sociale ;
* coordonnées ;
* notes ;
* statut (actif, archivé) ;
* dates de création et de modification.

Une dépense référence le fournisseur par identifiant. Un fournisseur ayant un historique est archivé, jamais supprimé.

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
* Elles sont copiées (snapshot) sur les lignes de devis puis de BC ; une modification du catalogue ne change jamais une garantie existante.

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

La date de déclenchement est la date d'émission de ce solde ; la création est idempotente (la première date est conservée) ; une garantie n'est ni modifiée ni supprimée, même si le solde est annulé ou si un avoir ou un règlement intervient. Aucune garantie n'est recréée automatiquement à partir de données historiques importées.

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

Événements tracés : création, modification, acceptation, refus, annulation, gel, émission, règlement et annulation de règlement, remboursement, avoir, passage à Terminé et retour à En cours, déclenchement de garantie, annulation automatique d'un acompte, rattachement d'un client, déclaration et correction URSSAF, import de données historiques, restauration.

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
* Les valeurs dérivées (état du BC, avancement, gel) sont recalculées par V6.
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
   └── BC  (un seul par devis)
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

Les relations définies ici sont traduites en repositories et en tables SQLite (modèle de données SQLite V3.10).

⸻

## 36. Règles d'intégrité majeures

Le modèle V6 garantit notamment que :

1. un document conserve son historique après modification du catalogue, des paramètres ou du référentiel (snapshots) ;
2. un devis accepté produit un BC de manière idempotente (un seul BC par devis) ;
3. un BC est Terminé seulement si un solde actif existe et que le reste dû des factures actives (hors avoirs) est nul ;
4. le devis et le BC sont gelés, irréversiblement, au premier encaissement actif d'un acompte, à l'émission d'une situation ou à l'émission du solde ;
5. un acompte non réglé est annulé automatiquement si le devis ou le BC est modifié avant le gel ;
6. un BC dont la facturation dépasse un acompte non réglé ne peut pas être annulé directement ; une situation émise (même annulée) l'interdit toujours ;
7. le solde est toujours la facture finale ; un solde à 0 € est autorisé ; aucune situation, aucun acompte et aucun nouvel avoir-solde après un solde actif ;
8. une facture peut recevoir plusieurs règlements ; le reste à payer est calculé, jamais saisi ; un encaissement ne dépasse pas le reste dû ;
9. une facture payée ne disparaît jamais pour corriger une erreur : l'avoir corrige ;
10. un avoir conserve la référence de la facture concernée ; le total des avoirs actifs ne dépasse pas l'origine ; un remboursement ne dépasse pas le crédit ;
11. un BC annulé n'est plus comptabilisé dans le CA engagé ;
12. les garanties sont générées à l'émission du solde actif, indépendamment du paiement et du PV, et ne sont jamais recalculées ;
13. un PV émis ne peut plus être modifié ; une levée de réserves crée un nouveau PV ;
14. les calculs URSSAF utilisent les encaissements réels ; une période verrouillée n'est corrigée que par le mécanisme de correction ;
15. les versions réglementaires historiques restent reproductibles ;
16. les montants sont manipulés avec une précision décimale exacte, arrondis HALF_UP une fois par ligne ;
17. un numéro attribué n'est jamais réutilisé, même après annulation, restauration ou incident ; un trou est acceptable ;
18. les données métier restent locales ; aucune fonctionnalité distante n'est nécessaire au fonctionnement normal ;
19. SQLite est la source de vérité ; les PDF, exports et sauvegardes en sont dérivés ;
20. la seule reprise de données historiques passe par un `import-v6.json` conforme, sur base vide, en transaction unique.

⸻

## 37. Statut de ce document

Ce document est le modèle métier de BATORYA Essentiel V6. Il est aligné sur :

* le modèle de données SQLite V6 (V3.10) ;
* le registre des invariants (`invariants.md`, version 3) ;
* les errata au CDC gelé (`cdc-errata-v6.md`, E-01 à E-09).

Il ne définit pas les tables SQLite, les types SQL, les index, les repositories, les services TypeScript, les composants React ni les commandes Tauri : ces éléments relèvent des documents techniques correspondants.
