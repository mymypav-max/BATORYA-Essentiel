BATORYA Essentiel V6

Cahier des charges fonctionnel et architectural définitif

Version : V6 — CDC gelé

⸻

1. Objet du projet

BATORYA V6 est une application desktop locale destinée aux micro-entrepreneurs du BTP exerçant une activité de prestation de services, relevant du régime micro-entrepreneur et n’étant pas assujettis à la TVA dans le cadre couvert par BATORYA Essentiel.

BATORYA centralise notamment :

* clients ;
* catalogue de prestations ;
* devis ;
* BC ;
* facturation ;
* règlements ;
* planification ;
* PV ;
* garanties ;
* notes ;
* dépenses ;
* suivi URSSAF ;
* analyses de gestion ;
* documents PDF ;
* sauvegardes ;
* paramètres ;
* licence et mises à jour.

BATORYA est un outil de gestion et d’assistance, et non un logiciel comptable ou un service administratif officiel.

⸻

2. Périmètre BATORYA Essentiel

Inclus

Le périmètre V6 couvre exclusivement :

* micro-entrepreneur ;
* activité de prestation de services ;
* secteur BTP ;
* absence de gestion de TVA ;
* gestion locale des données ;
* devis ;
* BC ;
* factures ;
* règlements ;
* avoirs ;
* clients ;
* catalogue ;
* planification ;
* PV ;
* garanties ;
* notes ;
* dépenses ;
* suivi URSSAF ;
* analyses de gestion ;
* documents ;
* sauvegardes ;
* licence ;
* mises à jour logicielles ;
* mises à jour des références réglementaires.

Exclus

Ne font pas partie de BATORYA Essentiel V6 :

* BATORYA Entreprise ;
* gestion de salariés ;
* pointage salarié ;
* gestion de paie ;
* TVA ;
* gestion générale des régimes fiscaux ;
* BNC ;
* comptabilité complète ;
* rapprochement bancaire ;
* télétransmission URSSAF ;
* déclaration URSSAF automatique ;
* gestion automatique des emails ;
* gestion des échéances fournisseurs ;
* gestion du paiement des dépenses ;
* avenants ;
* gestion de chantier indépendante du BC ;
* compte utilisateur en ligne ;
* stockage cloud des données métier ;
* Google Drive ;
* banque connectée.

⸻

3. Principes fonctionnels

BATORYA V6 doit rester :

* simple ;
* local ;
* utilisable hors connexion ;
* cohérent ;
* traçable ;
* prévisible ;
* non intrusif.

BATORYA reste utilisable hors connexion, sauf restriction temporaire liée à la validation de licence, conformément au chapitre 41.

Les opérations importantes doivent être atomiques et ne jamais laisser une donnée dans un état incohérent.

BATORYA doit distinguer clairement :

* donnée ;
* calcul ;
* information ;
* estimation ;
* alerte ;
* règle réglementaire.

Aucune donnée ne doit être inventée automatiquement lorsqu’elle n’est pas disponible.

⸻

4. Architecture technique

La V6 est une nouvelle implémentation basée sur :

* Tauri 2 ;
* React ;
* TypeScript ;
* Vite ;
* SQLite.

Architecture logique :

Interface → services applicatifs → règles métier → repositories → SQLite

Les composants ne doivent pas accéder directement aux données d’un autre module.

Les commandes natives Tauri doivent rester limitées et contrôlées.

Le renderer ne doit pas disposer d’un accès arbitraire au système de fichiers.

⸻

5. Stockage des données

SQLite constitue la source de vérité des données métier.

Les données métier ne sont pas stockées dans le dossier de travail.

Le changement du dossier de travail ne doit donc :

* ni déplacer SQLite ;
* ni modifier les données métier ;
* ni nécessiter une migration des données.

Le dossier de travail concerne principalement le stockage des documents générés et des sauvegardes.

⸻

6. Gestion monétaire

Les montants monétaires sont manipulés avec une représentation décimale exacte. SQLite ne doit pas utiliser REAL comme représentation exacte d’un montant.

BATORYA utilise une représentation décimale fiable, avec stockage canonique en texte décimal et calcul via une bibliothèque décimale adaptée.

Les calculs intermédiaires conservent leur précision et aucun arrondi prématuré n’est effectué.

Les montants commerciaux finaux (totaux, acomptes, factures, règlements, dépenses) sont à 2 décimales. L’arrondi est HALF_UP et intervient une seule fois par ligne ; le total est obtenu par somme des lignes arrondies, moins la remise globale arrondie.

Les quantités, prix unitaires et remises en valeur peuvent conserver une précision libre lorsqu’elle est prévue par le modèle. Les pourcentages saisis utilisent 2 décimales.

Aucune perte silencieuse de précision n’est autorisée. Pour l’import historique, V6 ne réarrondit pas les données : le convertisseur externe produit un import-v6.json conforme à la précision attendue, et un fichier hors précision est rejeté par l’import V6.

⸻

7. Entreprise et profil utilisateur

Identité de l’entreprise

Les paramètres d’entreprise comprennent notamment :

* nom et prénom de l’entrepreneur ;
* entrepreneur individuel / EI lorsque nécessaire ;
* nom commercial éventuel ;
* adresse ;
* téléphone ;
* adresse email ;
* SIREN ;
* SIRET ;
* autres informations d’identification utiles ;
* coordonnées bancaires éventuellement affichées sur les documents.

Les coordonnées bancaires sont facultatives.

Profil local

BATORYA peut disposer d’un profil local permettant notamment :

* affichage du nom de l’utilisateur ;
* mot de passe local ;
* identification visuelle de l’utilisateur.

Il n’existe pas de compte utilisateur en ligne ni de système complexe de rôles.

Le mot de passe n’est jamais stocké en clair.

Mot de passe oublié

En cas de blocage lié à un mot de passe oublié :

* BATORYA ne récupère pas le mot de passe ;
* l’utilisateur contacte le support BATORYA ;
* le support peut générer une procédure de déblocage ;
* le mécanisme repose sur un code/token temporaire lié à l’installation ;
* aucune donnée métier n’est transmise au support ;
* après validation, l’utilisateur peut définir un nouveau mot de passe.

⸻

8. Paramètres généraux

Le module Paramètres regroupe uniquement les réglages réellement généraux.

Paramètres commerciaux

* délai de paiement par défaut ;
* modes de paiement proposés ;
* mention commerciale standard ;
* conditions particulières standard.

Ces valeurs servent de préremplissage mais peuvent être adaptées lorsque cela est autorisé.

Les mentions légalement obligatoires ne peuvent pas être supprimées simplement par préférence utilisateur.

Sauvegardes

Le module permet :

* activation/désactivation des sauvegardes automatiques ;
* fréquence lorsque nécessaire ;
* sauvegarde manuelle ;
* affichage/ouverture du dossier de sauvegarde ;
* affichage du dernier état de sauvegarde.

Le moteur de sauvegarde est centralisé.

Gmail

Le module permet :

* connexion du compte Gmail ;
* déconnexion ;
* affichage de l’état de connexion ;
* affichage du compte utilisé ;
* test de connexion.

Les emails sont toujours envoyés manuellement.

Services BATORYA

Le module affiche notamment :

* état de licence ;
* dernière vérification ;
* version installée ;
* disponibilité éventuelle d’une mise à jour ;
* version du référentiel réglementaire ;
* dernière communication réussie.

Les paramètres URSSAF ne sont pas dupliqués dans ce module.

⸻

9. Dossier de travail et documents

L’utilisateur choisit un dossier de travail local.

Ce dossier sert principalement de racine de stockage documentaire.

Modifier le dossier de travail :

* ne déplace pas SQLite ;
* ne modifie pas les données métier ;
* ne copie pas automatiquement les anciens documents ;
* fait simplement utiliser le nouveau chemin pour les futurs documents.

Les anciens fichiers restent dans leur ancien emplacement.

Sauvegarde lors du changement de dossier

Lors d’un changement de dossier de travail, BATORYA propose une sauvegarde immédiate avant le changement.

Cette sauvegarde reste dans l’ancien dossier avec les sauvegardes existantes.

Aucune copie automatique des anciennes sauvegardes vers le nouveau dossier n’est effectuée.

⸻

10. Structure documentaire

Les documents sont classés par année.

Structure générale :

Dossier de travail/
├── 2026/
│   ├── Devis/
│   │   ├── En_attente/
│   │   ├── Accepte/
│   │   ├── Refuse/
│   │   └── Annule/
│   ├── Factures/
│   │   ├── Acomptes/
│   │   ├── Situations/
│   │   ├── Soldes/
│   │   └── Avoirs/
│   └── PV/
└── Sauvegardes/

Le BC n’est pas un document généré et ne possède donc pas de dossier documentaire.

Le PV est un document généré et possède son propre dossier annuel.

⸻

11. Catalogue des prestations

Le catalogue constitue la base des prestations proposées dans les devis.

Le catalogue V6 doit reprendre le catalogue réel validé de V5.16.

Le catalogue réel de référence contient 205 prestations prédéfinies. Après suppression de ELE-008, le catalogue par défaut V6 comporte donc 204 prestations.

La liste doit être récupérée depuis le catalogue réel audité, et non reconstruite manuellement.

Garanties

Les garanties peuvent être gérées depuis le catalogue de prestations.

Une prestation peut disposer d’un ou plusieurs types de garantie par défaut.

Les garanties sont notamment :

* parfait achèvement : 1 an ;
* biennale : 2 ans ;
* décennale : 10 ans.

Les règles de garantie sont conservées dans les snapshots des documents historiques.

Suppression de Cat6

Cat6 n’est pas une catégorie.

Il s’agit d’une prestation spécifique :

ELE-008 — F+P prise RJ45 Cat6 avec câblage

Cette prestation doit être supprimée du catalogue V6.

⸻

12. Clients

Les clients constituent un référentiel indépendant.

Ils peuvent être utilisés par :

* devis ;
* BC ;
* factures ;
* planification ;
* PV ;
* garanties ;
* notes ;
* analyses.

Les documents historiques conservent les informations nécessaires à leur propre cohérence même si la fiche client évolue ensuite.

⸻

13. Devis

Le devis est le document commercial préalable à l’acceptation d’une prestation.

Chaque devis possède notamment :

* numéro ;
* client ;
* date ;
* lignes de prestations ;
* quantités ;
* prix ;
* conditions ;
* mentions nécessaires ;
* statut ;
* historique.

Numérotation : préfixe DEV.

États

Le devis peut notamment être :

* en attente ;
* accepté ;
* refusé ;
* annulé.

Classement PDF

Les PDF sont déplacés selon leur état :

* Devis/En_attente
* Devis/Accepte
* Devis/Refuse
* Devis/Annule

⸻

14. Modification d’un devis accepté

Un devis accepté reste modifiable tant qu’il n’est pas gelé.

Le gel est irréversible et intervient au premier événement suivant :
* encaissement actif, même partiel, d’un acompte ;
* émission d’une situation ;
* émission d’un solde.

Un acompte émis mais non encaissé ne gèle pas le devis ni le BC.

Lorsqu’un devis accepté non gelé est modifié :
* l’historique est conservé ;
* le BC associé est régénéré dans la même transaction ;
* les snapshots, lignes, garanties de lignes et montant contractuel du BC restent cohérents ;
* tout acompte émis mais non encaissé est annulé automatiquement dans la même transaction.

Un devis refusé ou annulé est immuable.

Après le gel :
* le devis et le BC sont figés sur leurs éléments commerciaux structurants ;
* les lignes, garanties de lignes, remises, acompte prévu, client, chantier, snapshots et montant contractuel ne sont plus modifiables.

Les travaux supplémentaires ne donnent pas lieu à un avenant dans Essentiel.

Ils nécessitent :

nouveau devis → acceptation → nouveau BC indépendant.

⸻

15. BC — Dossier central

Le BC est le point central du workflow BATORYA.

Il remplace toute notion fonctionnelle d’« Affaire ».

Le BC peut correspondre, dans le langage courant, à un chantier ou une affaire, mais BATORYA ne crée pas une entité fonctionnelle distincte.

Le BC relie notamment :

* client ;
* devis accepté ;
* facturation ;
* règlements ;
* planification ;
* notes ;
* PV ;
* garanties.

Les dépenses peuvent être globales ou rattachées à un BC.

⸻

16. Création et cycle de vie du BC

Lorsqu’un devis est accepté :

* le BC est créé automatiquement ;
* la création est atomique ;
* l’opération est idempotente ;
* aucun double BC ne doit être créé pour le même devis accepté.

Le BC démarre à l’état :

En cours

Le statut métier n’est pas librement modifiable par l’utilisateur.

Passage à Terminé

Le BC devient **Terminé** si et seulement si :
* un solde actif existe ;
* la somme des restes dus des factures actives hors avoir est nulle.

Un solde à 0 € ne suffit pas s’il reste un acompte ou une situation dû.

Le passage à Terminé est dérivé du service métier et n’est pas librement saisi par l’utilisateur. Une annulation de règlement ou d’avoir peut faire revenir le BC à En cours lorsque les conditions de Terminé ne sont plus réunies.

⸻

17. Annulation du BC

L’annulation du BC est possible uniquement dans les conditions prévues.

Aucun travail facturé en situation

Si aucune Situation n’a été émise et qu’aucun paiement n’a été encaissé :

* le BC peut être annulé selon les règles applicables ;
* si un acompte impayé existe, il est annulé avec le BC.

Situation émise

Si une Situation a été émise, le BC ne peut plus être annulé directement, même si cette Situation est encore impayée.

Une Situation matérialise un avancement de travaux déjà commencé.

Paiement encaissé

Une fois qu’un paiement a été encaissé :

l’annulation directe du BC est interdite.

Une facture déjà payée n’est pas supprimée.

Elle est traitée par le mécanisme de facturation approprié, notamment par avoir.

Conséquences de l’annulation

Lorsqu’un BC peut légalement être annulé :

* le devis passe à Annulé ;
* son PDF est placé dans Devis/Annule ;
* le BC reste conservé ;
* la facture d’acompte annulée reste conservée lorsqu’elle existe ;
* aucune nouvelle opération de facturation ne peut être effectuée sur ce BC.

⸻

18. Facturation

BATORYA V6 gère quatre types fonctionnels :

* Acompte
* Situation
* Solde
* Avoir

Le type technique historique `complete` n’est pas conservé comme type métier V6.

Solde

La facture finale est toujours une facture de solde.

Même lorsqu’aucune facture préalable n’existe, la facture finale est de type Solde.

Acompte

Préfixe :

ACP

Les numéros V6 suivent la convention uniforme définie par le modèle : DEV, BCD, FAC, ACP, AVO, PVR, DEP suivis du compteur sur 5 chiffres et de l’année sur 2 chiffres.

Les devis, factures, acomptes, situations, soldes, avoirs et PV importés peuvent conserver leur numéro historique lorsqu’il a déjà été remis au client. Les BC et codes clients/fournisseurs importés utilisent les formats V6.

⸻

19. Séquence de facturation

La séquence fonctionnelle permet notamment :

* acompte ;
* situations ;
* solde ;
* avoir.

Plusieurs situations peuvent être émises.

Le solde clôture la facturation commerciale du BC.

Les situations et les soldes partagent la même séquence FAC. Les numéros ne sont pas configurables manuellement et un numéro déjà attribué n’est jamais réutilisé ; les trous de numérotation sont acceptables.

Les factures historiques restent conservées.

⸻

20. Règlements

Une facture peut recevoir plusieurs règlements.

Chaque règlement comporte :

* date ;
* montant ;
* mode de paiement.

Modes notamment :

* espèces ;
* chèque ;
* virement ;
* carte ;
* autre.

Une facture n’est considérée comme totalement réglée que lorsque la totalité du montant dû a effectivement été enregistrée.

Un paiement partiel laisse apparaître le solde restant.

BATORYA ne réalise pas de rapprochement bancaire.

⸻

21. États des factures

Les états fonctionnels sont :

* En attente : aucun paiement ;
* Partiellement réglée : paiement(s) enregistré(s), solde restant ;
* Réglée : solde à zéro ;
* En retard : échéance dépassée avec un solde restant ;
* Annulée.

En retard est un indicateur transversal.

Une facture peut donc être :

Partiellement réglée — En retard

L’état de paiement et l’information d’échéance ne sont pas artificiellement exclusifs.

⸻

22. Avoirs

Un avoir constitue le mécanisme de correction ou de restitution après facturation lorsque cela est nécessaire.

Une facture payée n’est pas supprimée.

Elle reste dans l’historique et l’avoir constitue un document distinct.

L’avoir doit conserver :

* son origine ;
* son montant ;
* sa date ;
* son lien avec le document concerné ;
* son historique.

Le traitement d’un avoir ou remboursement dans le calcul du CA pris en compte pour l’URSSAF est défini par le référentiel réglementaire versionné.

BATORYA ne code pas cette règle en dur.

Le moteur applique la règle correspondant à la version réglementaire applicable à la période concernée.

⸻

23. PV et réception

Le PV est facultatif.

Il n’est jamais obligatoire pour terminer le workflow d’un BC.

Une réception peut être :

* sans réserve ;
* avec réserves.

Le PV original est immuable.

Une levée de réserves constitue un second PV autonome.

Le second PV référence le PV initial et ne modifie jamais le document original.

Numérotation

Le numéro du PV initial est réutilisé avec suffixe :

* PVR-00001-26
* PVR-00001-26-01
* PVR-00001-26-02

La levée de réserves ne modifie pas le suivi interne des garanties.

⸻

24. Garanties

BATORYA suit trois catégories :

* parfait achèvement ;
* biennale ;
* décennale.

Le suivi des garanties est un suivi interne BATORYA.

Déclenchement

Le suivi interne démarre lorsque le BC atteint :

100 % facturé

Il ne dépend pas :

* du paiement du solde ;
* de la réception ;
* de l’existence d’un PV ;
* de la présence de réserves ;
* de la levée des réserves.

Cela est distinct du passage du BC à Terminé : les garanties sont déclenchées par le franchissement de 100 % facturé, alors que Terminé dépend du solde actif et de l’absence de reste dû sur les factures actives hors avoir.

Date de garantie

La date affichée dans BATORYA est une date de suivi interne.

Elle doit être identifiée dans l’interface comme telle, par exemple :

« Suivi interne BATORYA — date indicative »

Elle ne constitue pas une détermination juridique du point de départ d’une garantie légale.

⸻

25. Consultation des garanties

Les garanties ne constituent pas un module métier autonome. Leur configuration est gérée directement depuis le Catalogue des prestations.

Le suivi des garanties générées est consultable depuis le BC concerné et les vues de suivi nécessaires à l’interface. Il présente notamment :
* BC ;
* client ;
* prestation ;
* type de garantie ;
* date de début du suivi interne ;
* date d’échéance ;
* état dérivé.

L’interface affiche « Suivi interne BATORYA — date indicative ». Aucun affichage ne doit présenter cette date comme une détermination juridique du point de départ d’une garantie légale.

⸻

26. Planification

Le module s’appelle **Planification** et comporte deux onglets : **Calendrier** et **Gantt**.

Calendrier :
* événements typés : intervention, travaux, rendez-vous client, réunion, appel, administratif, congé, indisponibilité, autre ;
* une intervention ou des travaux sont obligatoirement rattachés à un BC ;
* congé et indisponibilité ne sont jamais rattachés à un BC ;
* les autres types peuvent être rattachés ou non à un BC ;
* les événements peuvent être sur journée entière ou avec horaires.

Gantt :
* il est dédié aux BC ;
* il utilise les dates de début et de fin du BC ;
* un BC sans dates n’a pas de barre ;
* il ne constitue pas une gestion de chantier indépendante du BC.

La Planification est facultative et n’a aucune autorité sur le cycle de vie du BC. Une intervention planifiée ne rend pas un BC actif ou terminé.

Aucune synchronisation Outlook ou Google n’est prévue en V6. Les jours ouvrés et jours fériés français sont pris en compte.

⸻

27. Notes

Les notes sont des informations internes rattachées à un BC.

Une note comporte :

* texte libre ;
* date de création ;
* date de modification.

Elle peut être :

* modifiée ;
* supprimée.

Il n’existe pas dans V6 de moteur de tâches ou de workflow de rappel associé aux notes.

⸻

28. Dépenses

BATORYA permet d’enregistrer des dépenses afin d’alimenter les analyses de gestion.

Une dépense peut être :

* globale ;
* rattachée à un BC.

Une dépense peut être associée à un fournisseur lorsque nécessaire.

Les dépenses ne réduisent jamais directement le CA utilisé pour le calcul URSSAF.

Hors périmètre

BATORYA V6 ne gère pas :

* le paiement des dépenses ;
* les dépenses à payer ;
* les échéanciers fournisseurs ;
* un workflow de règlement fournisseur.

Les dépenses servent uniquement aux analyses comptables et de marge.

⸻

29. Analyse comptable et marge

La comptabilité de BATORYA est une couche d’analyse.

BATORYA ne crée pas un second moteur comptable parallèle.

Les analyses peuvent utiliser :

* facturation ;
* règlements ;
* dépenses ;
* BC ;
* clients ;
* périodes.

Les calculs de marge doivent distinguer les recettes et les charges sans confondre cette analyse avec la base réglementaire URSSAF.

⸻

30. Module URSSAF — principe

Le module URSSAF constitue une assistance au suivi déclaratif.

BATORYA :

* calcule ;
* estime ;
* historise ;
* alerte ;
* aide l’utilisateur à préparer sa déclaration.

BATORYA ne transmet jamais automatiquement une déclaration officielle à l’URSSAF.

L’utilisateur reste responsable de sa déclaration.

⸻

31. Profil réglementaire URSSAF

Le profil cible est fixe :

* statut : Micro-entrepreneur ;
* secteur : Travaux BTP ;
* activité : Prestation de services ;
* date de début d’activité ;
* périodicité : mensuelle ou trimestrielle ;
* ACRE : oui/non.

Les autres paramètres sont dérivés des données réglementaires.

La date de début d’activité est une donnée essentielle.

Elle ne doit pas être confondue avec une simple date de création de l’entreprise.

⸻

32. CA encaissé

Le CA utilisé pour le suivi URSSAF repose sur les sommes effectivement encaissées, avec application des règles réglementaires versionnées relatives notamment aux avoirs et remboursements.

Ainsi :

* facture émise mais impayée → aucun CA encaissé ;
* paiement partiel → seul le montant effectivement reçu est pris en compte ;
* plusieurs paiements → chacun est affecté à sa date réelle ;
* acompte payé → pris en compte à la date de réception ;
* une même facture peut contribuer à plusieurs périodes ;
* un avoir ou remboursement est traité selon la règle portée par le référentiel réglementaire applicable.

Le CA encaissé est distinct du montant facturé.

⸻

33. CA engagé et CA prévisionnel

BATORYA distingue :

CA encaissé

Sommes réellement reçues.

CA engagé

Montant des devis acceptés mais pas encore totalement encaissés.

Un BC annulé est automatiquement retiré du CA engagé.

Il ne doit plus être pris en compte dans les alertes de seuil ou projections utilisant le CA engagé.

Son historique reste conservé.

CA prévisionnel

Projection future construite à partir des données connues, notamment le CA engagé et les éléments planifiés disponibles.

Ces deux indicateurs ne doivent jamais être présentés comme du CA encaissé.

Seul le CA effectivement reçu constitue le CA réalisé pour le suivi URSSAF.

⸻

34. Périodes URSSAF

Les périodes sont :

Mensuelles

Du premier au dernier jour du mois.

Trimestrielles

Trimestres civils.

Chaque paiement est affecté à la période correspondant à sa date réelle de réception.

Si l’activité débute en cours de mois ou de trimestre, la première période est partielle.

Le calcul porte uniquement sur la période réellement concernée.

Une période sans encaissement existe néanmoins et doit être déclarée.

⸻

35. Déclarations

Pour chaque période, BATORYA conserve notamment :

* période ;
* CA encaissé calculé ;
* contributions estimées ;
* CFP ;
* autres éléments réglementaires applicables ;
* montant effectivement déclaré par l’utilisateur ;
* date réelle de déclaration ;
* statut ;
* différence entre estimation et déclaration ;
* version du référentiel réglementaire.

États notamment :

* À déclarer ;
* Déclarée ;
* À vérifier.

BATORYA ne marque jamais automatiquement une déclaration comme officiellement réalisée.

⸻

36. Historique et corrections

Une période déclarée ne doit jamais être silencieusement réécrite.

Si une donnée postérieure modifie une situation historique :

* l’ancienne valeur est conservée ;
* la nouvelle valeur est identifiée ;
* l’écart est affiché ;
* une anomalie/correction est créée ;
* la période originale reste traçable.

Les calculs historiques doivent rester reproductibles avec la version réglementaire utilisée à l’époque.

⸻

37. ACRE et CFP

ACRE

L’utilisateur indique s’il bénéficie de l’ACRE.

BATORYA détermine les règles applicables à partir :

* de la date de début d’activité ;
* de la période ;
* du référentiel réglementaire.

La transition vers les règles normales est automatique.

L’historique conserve la règle réellement appliquée.

CFP

La CFP est traitée séparément des contributions sociales.

Son applicabilité et son taux proviennent du référentiel réglementaire.

Elle apparaît séparément dans les calculs et l’historique.

Versement libératoire

Hors périmètre V6.

⸻

38. Seuils et alertes

BATORYA surveille le seuil réglementaire applicable.

Le module distingue :

* CA encaissé réel ;
* CA engagé ;
* CA prévisionnel.

Le seuil peut faire l’objet d’une alerte prévisionnelle.

Exemple :

* marge restante avant seuil : 3 000 € ;
* devis accepté : 10 000 € ;
* BATORYA signale l’exposition.

BATORYA ne bloque jamais :

* la création d’un devis ;
* l’acceptation d’un devis ;
* la création d’un BC ;
* la facturation.

L’utilisateur conserve entièrement sa décision.

⸻

39. Référentiel réglementaire

Les paramètres réglementaires sont séparés du code applicatif.

Chaque version possède :

* identifiant/version ;
* date d’effet ;
* données réglementaires concernées ;
* règles nécessaires au traitement des différents cas réglementaires, notamment les avoirs et remboursements lorsqu’ils ont un impact sur le CA.

Les versions historiques sont conservées.

Une nouvelle version réglementaire téléchargée remplace les paramètres précédents, y compris lorsqu’une valeur avait été modifiée manuellement auparavant.

La nouvelle version devient la référence applicable selon sa date d’effet.

Les anciennes versions restent disponibles pour les calculs historiques.

Une nouvelle version future peut être téléchargée avant son entrée en vigueur.

Si une donnée réglementaire nécessaire est absente :

* BATORYA avertit ;
* ne fabrique aucune valeur ;
* ne bloque pas inutilement l’application.

⸻

40. Services BATORYA

Le service distant BATORYA possède trois fonctions principales :

1. Licence
2. Mises à jour logicielles
3. Références réglementaires

Le service ne reçoit pas les données métier de l’utilisateur.

Les données métier restent locales.

Une indisponibilité du service distant ne doit jamais bloquer BATORYA immédiatement.

Les communications distantes sont explicitement limitées aux fonctions prévues.

⸻

41. Licence et changement d’ordinateur

La licence est liée à l’ordinateur / installation.

La vérification de licence intervient tous les trois mois.

En cas d’échec de vérification :

« La licence de BATORYA n’a pas pu être vérifiée. Vous disposez de 15 jours pour connecter cet ordinateur à Internet afin de vérifier la validité de votre licence. »

Pendant les 15 jours :

* utilisation complète.

Après expiration :

* consultation autorisée ;
* exports autorisés ;
* création interdite ;
* modification interdite ;
* suppression interdite ;
* opérations de facturation interdites.

Une vérification réussie rétablit immédiatement le fonctionnement normal.

Changement d’ordinateur

En cas de changement d’ordinateur :

* l’utilisateur contacte le support BATORYA ;
* le support génère une nouvelle clé de licence spécifique au nouvel ordinateur ;
* l’ancienne clé devient invalide.

Il n’existe pas de procédure automatique de migration de licence entre deux ordinateurs.

⸻

42. Sauvegardes, restauration et import historique

Sauvegardes

Lors de la première sauvegarde, BATORYA crée :
Dossier de travail/
└── Sauvegardes/

Les sauvegardes officielles sont des sauvegardes cohérentes de la **base SQLite métier**. Le JSON est un export de consultation/archivage et n’est pas un format de restauration V6.

Le moteur est commun aux :
* sauvegardes automatiques ;
* sauvegardes manuelles ;
* sauvegarde à la fermeture lorsque configurée.

Lors d’un changement de dossier de travail, la sauvegarde immédiate proposée avant le changement est réalisée dans l’ancien dossier, afin de conserver une sauvegarde de sécurité avant la modification du chemin documentaire.

Import historique V2

V6 ne lit jamais directement le JSON V2. La reprise suit exclusivement le flux :

**JSON V2 → convertisseur externe → import-v6.json → import V6**

Le convertisseur externe porte les règles de transformation, normalisation et compatibilité propres à la V2. V6 ne contient aucune logique d’adaptation à la structure V2.

L’import V6 :
* accepte uniquement un import-v6.json conforme à son contrat ;
* effectue une validation complète sans écriture, puis un import en transaction unique ;
* est prévu uniquement sur une base métier vide ;
* applique les règles métier V6 normales ;
* ne lit jamais les états dérivés, caches du BC ou frozen_at fournis par le fichier ;
* recalcule les valeurs dérivées selon les règles V6 ;
* conserve uniquement l’exception prévue pour le numéro historique des devis, factures et PV déjà remis aux clients ;
* initialise les séquences V6 et le high-water à partir des compteurs historiques compatibles transmis par le convertisseur ;
* conserve les anomalies déclarées par le fichier dans import_anomalies, notamment a_verifier et non_importe, sans suppression silencieuse ;
* trace les objets importés avec origine import et, lorsque disponible, legacy_id, legacy_numero et legacy_data.

Aucune table migration_rapports, migration_quarantaine ou migration_id n’est utilisée.

Restauration

Avant restauration :
* une sauvegarde de sécurité de la base métier courante est réalisée ;
* le fichier est validé ;
* une version de schéma supérieure à celle supportée est refusée ;
* les migrations éventuelles sont effectuées sur une copie ;
* les contrôles d’intégrité sont exécutés ;
* le remplacement est atomique ;
* les contrôles post-restauration sont exécutés.

machine.db n’est jamais restaurée avec la base métier. Elle conserve notamment l’utilisateur local, la licence, l’identifiant d’installation, les dossiers de stockage, les préférences, Gmail et le high-water de numérotation.

Après restauration, max_attribue ne diminue jamais : le prochain numéro respecte le maximum entre le high-water de la machine et les numéros restaurés. Un numéro déjà attribué n’est donc jamais réutilisé.

⸻

43. Services transversaux, sécurité, erreurs et documents

DocumentService

Un service central gère :

* chemins ;
* classement ;
* déplacement ;
* existence ;
* génération des chemins documentaires.

PdfService

Le service PDF :

* utilise les données SQLite ;
* récupère les paramètres entreprise via les services applicatifs ;
* produit les documents selon les modèles BATORYA ;
* respecte le classement annuel.

Les PDF V5.16 validés servent de référence fonctionnelle.

EmailService

Les envois sont manuels.

Gmail est utilisé comme compte d’envoi.

BATORYA ne doit jamais prétendre avoir envoyé un email si le compte Gmail n’est pas configuré ou si l’envoi n’a pas réellement réussi.

ErrorService

Un service centralise les erreurs.

L’utilisateur peut ouvrir un rapport d’erreur contenant notamment :

* contexte ;
* erreur ;
* informations techniques utiles ;
* version BATORYA.

Le rapport peut être envoyé manuellement depuis Gmail au support :

batorya.app@outlook.fr

Si Gmail n’est pas configuré :

* aucun faux envoi ;
* possibilité de copier ou sauvegarder le rapport ;
* indication de la nécessité de configurer Gmail pour l’envoi.

Données et confidentialité

Les données métier restent locales.

Aucune donnée métier n’est envoyée automatiquement vers :

* Services BATORYA ;
* Gmail ;
* un serveur distant ;
* un système d’analyse externe.

Les communications distantes sont explicitement limitées aux fonctions prévues :

* licence ;
* mises à jour ;
* références réglementaires.

Cohérence et traçabilité

Les opérations sensibles doivent être :

* atomiques ;
* validées ;
* traçables ;
* réversibles lorsque le métier le permet.

Les documents historiques ne doivent jamais être modifiés silencieusement lorsqu’une nouvelle opération doit être créée.

⸻

Synthèse fonctionnelle finale

BATORYA Essentiel V6 est une application locale de gestion destinée exclusivement au micro-entrepreneur du BTP en prestation de services.

Le BC constitue le centre du workflow, sans devenir un document.

Le cycle principal est :

Client → Devis → Acceptation → BC → Facturation → Règlements → Terminé

avec les fonctions transversales :

* planification ;
* notes ;
* PV ;
* garanties ;
* dépenses ;
* analyses ;
* URSSAF ;
* documents ;
* sauvegardes.

Les principes structurants sont :

* données métier locales ;
* SQLite indépendant du dossier de travail ;
* précision monétaire conservée ;
* historique préservé ;
* absence de TVA ;
* absence d’avenants ;
* absence de comptabilité complète ;
* absence de gestion des paiements fournisseurs ;
* absence de télétransmission URSSAF ;
* assistance réglementaire versionnée ;
* licence et mises à jour via Services BATORYA ;
* aucune décision commerciale ou réglementaire automatisée à la place de l’utilisateur.

Le suivi interne des garanties démarre à 100 % facturé, indépendamment du paiement final et du statut Terminé.

Une Situation émise interdit l’annulation directe du BC, car elle matérialise un avancement de travaux commencé.

Le CA engagé exclut les BC annulés.

Le CA URSSAF repose sur les encaissements réels, avec traitement des avoirs et remboursements déterminé par le référentiel réglementaire versionné.

Le fonctionnement hors connexion demeure la règle, sous réserve du mécanisme de validation de licence.

Le changement de dossier de travail ne déplace jamais les données SQLite et propose une sauvegarde immédiate avant changement.
