# Cadrage fonctionnel de Léon — BATORYA Essentiel V6

**Statut :** document de travail — décisions de cadrage consolidées  
**Périmètre :** BATORYA Essentiel V6 exclusivement  
**Version :** V1 — cadrage initial

## 1. Objet et périmètre

Léon est l’assistant intégré à BATORYA Essentiel V6. Il accompagne l’utilisateur dans la compréhension et l’utilisation de l’application ainsi que dans ses opérations métier quotidiennes.

Léon doit fonctionner localement, sans dépendre d’un modèle d’IA distant pour assurer ses fonctions. Ce document centralise les décisions validées et les axes de conception avant la définition détaillée des intents et de l’architecture. Il ne remplace pas les documents structurants de BATORYA V6 et ne vaut pas validation des choix techniques encore à étudier.

Les décisions historiques issues de versions antérieures de Léon sont des références d’expérience uniquement ; elles ne sont pas automatiquement reconduites dans V6.

## 2. Mission fonctionnelle

La mission retenue correspond à l’option C : un guide et un assistant métier avec accompagnement actif.

Léon doit pouvoir :
- comprendre les demandes formulées en langage naturel ;
- expliquer les fonctionnalités et les règles métier de BATORYA ;
- aider l’utilisateur à comprendre les informations présentes à l’écran ;
- analyser les données auxquelles il est autorisé à accéder ;
- guider l’utilisateur dans la réalisation d’une opération ;
- aider à préparer une opération, par exemple un devis, sans l’exécuter lui-même ;
- accompagner l’utilisateur lorsqu’il navigue entre plusieurs écrans pour résoudre un même problème.

Cette mission constitue la cible fonctionnelle. Elle ne signifie pas que toutes les capacités seront disponibles dès la première version ni qu’un modèle local puissant devra être imposé si ses performances sont insuffisantes. La priorité est de construire un Léon utile, fiable et fluide, compatible avec les contraintes d’un fonctionnement local.

## 3. Limites fonctionnelles de la V1

### 3.1 Capacités autorisées

La V1 couvre les deux premiers niveaux de capacité.

**Niveau 1 — Comprendre et conseiller**
- Répondre aux questions sur BATORYA.
- Expliquer les fonctionnalités et les règles métier.
- Aider à interpréter les informations accessibles.
- Analyser une situation à partir de données vérifiées.
- Proposer des explications et des prochaines étapes.

**Niveau 2 — Préparer et guider**
- Aider à préparer un devis ou une autre opération.
- Indiquer les informations nécessaires.
- Présenter une trame ou une proposition que l’utilisateur pourra reporter lui-même dans BATORYA.
- Guider l’utilisateur dans les étapes et les champs de l’application.

### 3.2 Capacités exclues

La V1 ne permet pas à Léon d’effectuer des modifications métier. Il ne doit notamment pas :
- créer ou modifier un document dans BATORYA ;
- enregistrer un règlement ;
- changer un statut ;
- valider ou supprimer une donnée ;
- déclencher une opération métier ;
- remplir automatiquement des champs métier ;
- enregistrer un brouillon dans la base de données.

Cette restriction doit être garantie par les capacités techniques réellement exposées à Léon, et pas uniquement par une consigne adressée au modèle. Léon ne doit pas disposer d’un accès direct en écriture à SQLite.

## 4. Fiabilité et dialogue

Léon ne doit ni inventer des informations ni présenter une supposition comme un fait. Il doit :
1. répondre directement lorsque l’intention est suffisamment claire et que les informations nécessaires sont disponibles ;
2. exploiter le contexte de BATORYA pour éviter les questions inutiles ;
3. identifier les informations réellement manquantes ;
4. poser une ou plusieurs questions ciblées lorsque cela est nécessaire, en regroupant les questions liées lorsque c’est possible ;
5. distinguer les faits vérifiés, les hypothèses explicitement présentées comme telles et les informations inconnues ;
6. reconnaître ses limites lorsqu’il ne peut pas établir une réponse fiable ;
7. ne pas inventer une cause, une règle métier, une donnée ou une fonctionnalité pour éviter de demander une précision.

L’objectif n’est pas de maximiser le nombre de questions posées, mais d’obtenir une compréhension correcte avec le minimum d’échanges nécessaires.

Les intents devront tenir compte des formulations naturelles possibles, de l’écran et du module actifs, de l’objet éventuellement consulté, des informations déjà établies dans la conversation, des données indispensables, des ambiguïtés connues et des conditions permettant de répondre ou imposant une clarification. La qualité de compréhension et la limitation des clarifications inutiles devront être vérifiées par des tests. Le catalogue d’intents sera construit progressivement, au rythme du développement de BATORYA V6 ; il ne doit pas être figé prématurément.

## 5. Contexte fourni par BATORYA

### 5.1 Construction à la demande

Le contexte nécessaire est construit au moment où l’utilisateur sollicite Léon. Aucun traitement IA ne doit être lancé en arrière-plan lorsque l’utilisateur ne fait pas appel à lui. La navigation dans BATORYA ne doit pas, à elle seule, déclencher un traitement IA.

Il n’est pas nécessaire de transmettre en permanence le contexte de l’application au modèle ni de charger systématiquement toutes les données métier. Le contexte est constitué en fonction de la demande et des informations nécessaires pour y répondre.

### 5.2 Contexte courant

Le contexte courant décrit la situation présente de l’utilisateur dans BATORYA. Il pourra comprendre, selon leur disponibilité et leur utilité :
- le chapitre ou module actif ;
- l’écran courant ;
- l’onglet ou l’étape active ;
- l’objet consulté ou sélectionné ;
- les informations de navigation utiles à l’interprétation de la demande.

Ces éléments sont une base de conception, pas une obligation de transmettre systématiquement tous les champs. Le contrat minimal exact reste à définir. BATORYA doit fournir les informations de navigation qu’il connaît de manière fiable ; Léon ne doit pas devoir les déduire uniquement de la formulation de l’utilisateur.

Lorsqu’un objet métier est pertinent, BATORYA peut transmettre une référence permettant de l’identifier sans ambiguïté, par exemple un client, un devis, une facture ou un règlement. Cette référence ne signifie pas que Léon connaît toutes les données associées. Si aucun objet n’est sélectionné, Léon ne doit pas en inventer un ni supposer que la demande concerne un objet particulier.

Le contexte courant doit correspondre à la situation réelle au moment où une nouvelle demande est traitée. Son actualisation est indépendante du traitement par le modèle.

### 5.3 Récupération ciblée des données métier

Le contexte courant ne doit pas contenir systématiquement toutes les données métier. Lorsqu’une demande nécessite des informations complémentaires, BATORYA peut les récupérer par l’intermédiaire de services applicatifs autorisés, en lecture seule.

Exemples :
- rechercher un client dans le carnet clients ;
- vérifier le statut d’un devis ;
- consulter les échéances d’une facture ;
- récupérer les informations nécessaires à l’explication d’un blocage métier.

La récupération doit être limitée aux informations utiles à la demande. Léon ne doit pas recevoir une fiche complète ou un ensemble de données métier simplement parce qu’il pourrait éventuellement en avoir besoin. Les accès doivent respecter les règles métier et les autorisations de BATORYA.

Une information absente du contexte immédiat ne doit pas être considérée automatiquement comme inexistante dans BATORYA. Si elle est accessible, une récupération ciblée peut être effectuée. Si elle ne peut pas être vérifiée, Léon doit le signaler.

### 5.4 Autorité des informations

Les données métier et les règles vérifiées de BATORYA constituent les références factuelles. Le modèle IA ne doit pas remplacer une règle métier par une supposition ni présenter une interprétation comme un résultat officiellement établi par BATORYA. Les informations factuelles et les calculs doivent provenir de BATORYA ou de sources explicitement reconnues.

## 6. Continuité conversationnelle

### 6.1 Contexte de la demande et mémoire conversationnelle

Le contexte conversationnel conserve les éléments nécessaires à la continuité du dialogue, lorsque ceux-ci sont utiles :
- la demande initiale et l’objectif poursuivi ;
- les précisions fournies par l’utilisateur ;
- les informations déjà vérifiées ;
- les questions et réponses précédentes pertinentes ;
- la progression de la résolution ;
- les références aux objets métier concernés.

Le contenu exact et le format technique de cette mémoire restent à concevoir. Le contexte conversationnel ne doit pas être confondu avec l’écran courant.

### 6.2 Navigation sans perte du fil

Un changement d’écran ou de module ne doit pas annuler automatiquement une demande, interrompre le fil de discussion ou effacer la mémoire conversationnelle. Léon doit pouvoir prendre en compte le nouvel écran tout en poursuivant la demande initiale lorsque la navigation s’inscrit dans sa résolution.

**Exemple : recherche d’un client lors de la création d’un devis**
1. L’utilisateur commence la création d’un devis et indique à Léon qu’il ne trouve pas un client pourtant enregistré.
2. Avant que Léon ait terminé sa réponse, l’utilisateur ouvre le carnet clients.
3. Léon conserve l’objectif initial — retrouver le client pour poursuivre le devis — et actualise le contexte courant pour tenir compte du carnet clients.
4. Léon poursuit l’accompagnement à partir du nouvel écran si les informations disponibles le permettent, sans confondre cet écran avec la demande initiale.

Le changement de module ne doit pas être interprété comme une nouvelle conversation. Une clarification n’est nécessaire que si une ambiguïté réelle empêche de poursuivre correctement.

### 6.3 Références à des éléments précédents

Lorsqu’une nouvelle demande fait référence à un élément précédent, Léon doit exploiter le contexte conversationnel si celui-ci permet d’identifier cet élément de façon suffisamment fiable. Si plusieurs interprétations restent possibles et conduisent à des réponses différentes, Léon doit poser une question ciblée. Il ne doit ni oublier systématiquement le contexte précédent ni supposer qu’une référence est certaine lorsqu’elle ne l’est pas.

## 7. Expiration de la mémoire conversationnelle

Le principe d’une expiration après **30 minutes d’inactivité** est retenu pour la V1. Cette durée correspond à une période d’inactivité avant expiration du contexte conversationnel ; elle ne constitue ni une durée maximale de traitement d’une demande ni une durée de maintien du modèle en mémoire vive.

Principes retenus :
- le contexte conversationnel est conservé pendant la période d’inactivité définie ;
- une navigation dans BATORYA ne remet pas automatiquement le délai à zéro et ne supprime pas le fil de discussion ;
- le contexte courant est actualisé indépendamment de la mémoire conversationnelle ;
- une nouvelle interaction pertinente permet de poursuivre le fil de discussion ;
- après expiration, Léon ne doit pas prétendre disposer d’éléments conversationnels qui ne sont plus conservés ;
- il pourra demander à l’utilisateur de rappeler les éléments nécessaires à la reprise de la demande.

L’expiration de la mémoire conversationnelle ne doit pas être confondue avec la suppression des données métier de BATORYA.

**Points restant à préciser :** le point de départ exact du délai, les interactions qui le renouvellent, le traitement des demandes encore en cours, les données conservées après expiration et les modalités de reprise d’une demande dont le contexte n’est plus disponible.

## 8. Confidentialité, accès et séparation des responsabilités

Le contexte transmis à Léon doit être limité aux informations nécessaires à la demande. Léon ne doit pas :
- disposer d’un accès libre à la base SQLite ;
- parcourir librement les fichiers de l’ordinateur ;
- recevoir systématiquement toutes les données d’un client ou d’un document ;
- utiliser des données qui ne sont pas disponibles dans le contexte ou accessibles par un mécanisme autorisé ;
- effectuer une opération d’écriture métier.

Les mécanismes techniques doivent garantir ces limites indépendamment du comportement du modèle.

**BATORYA est responsable de :**
- connaître l’écran et le module actifs ;
- identifier le contexte de navigation ;
- fournir les informations autorisées et nécessaires ;
- récupérer les données métier complémentaires par des services contrôlés ;
- garantir l’absence de capacité d’écriture métier exposée à Léon.

**Léon est responsable de :**
- interpréter la demande ;
- exploiter le contexte fourni ;
- déterminer si les informations disponibles suffisent ;
- produire une explication ou une proposition ;
- demander une clarification lorsqu’elle est nécessaire ;
- signaler les limites de sa réponse.

Les modalités précises de stockage, de protection et de suppression du contexte conversationnel restent à définir.

## 9. Fonctionnement local et sobriété des ressources

Léon doit préserver la fluidité de BATORYA sur des configurations matérielles courantes. La mission C ne doit pas imposer un modèle trop lourd ou des exigences de calcul incompatibles avec une expérience fluide.

Principes retenus :
- aucun traitement IA en arrière-plan lorsque l’utilisateur ne sollicite pas Léon ;
- aucune analyse IA permanente de l’écran ;
- aucune récupération systématique de l’ensemble des données métier ;
- aucun chargement de contexte inutile ;
- recours au mécanisme le plus léger adapté à la demande ;
- utilisation possible de règles déterministes et de recherches ciblées lorsque celles-ci suffisent ;
- séparation entre suivi de navigation, mémoire conversationnelle et traitement du modèle ;
- mesure des performances réelles avant de fixer les exigences définitives du modèle local.

Le maintien d’une mémoire conversationnelle ne doit pas entraîner un traitement continu du modèle. Si la mission complète s’avère trop coûteuse ou trop lente, le périmètre fonctionnel ou les exigences devront être revus plutôt que de compromettre la fluidité et la viabilité du projet.

## 10. Décisions validées

À ce stade, les décisions de cadrage suivantes sont considérées comme validées :
- mission de guide et d’assistant métier avec accompagnement actif ;
- V1 limitée à la compréhension, au conseil, à l’analyse, à la préparation et au guidage ;
- aucune modification métier ni opération d’écriture par Léon ;
- fiabilité prioritaire et interdiction d’inventer ;
- clarifications ciblées, sans questions superflues ;
- conception des intents visant une bonne compréhension et une réduction des clarifications inutiles ;
- fonctionnement local et sobriété des ressources ;
- aucun traitement IA en arrière-plan lorsque Léon n’est pas sollicité ;
- contexte construit à la demande ;
- contexte courant actualisé indépendamment de la conversation ;
- récupération ciblée des données métier par des mécanismes contrôlés en lecture seule ;
- continuité de la demande malgré les changements d’écran et de module ;
- mémoire conversationnelle avec expiration après 30 minutes d’inactivité ;
- autorité de BATORYA pour les données et règles métier.

## 11. Points restant à concevoir

Les éléments suivants ne sont pas considérés comme définitivement décidés :
1. définition précise des champs du contexte minimal et des informations de navigation nécessaires ;
2. mécanisme et catalogue des services de lecture exposés à Léon ;
3. format, contenu et limites de la mémoire conversationnelle ;
4. point de départ et renouvellement du délai de 30 minutes ;
5. traitement des demandes en cours pendant la navigation ;
6. comportement détaillé à l’expiration et modalités de reprise ;
7. politique de clarification et traitement des références ambiguës ;
8. familles d’intents, puis catalogue détaillé des intents ;
9. stratégie de sélection entre règles déterministes, recherche et modèle local ;
10. modalités de stockage, de protection et de suppression de la mémoire ;
11. critères mesurables de fluidité, de consommation mémoire et de qualité des réponses ;
12. corpus de tests couvrant les changements d’écran, les demandes ambiguës, les données manquantes, l’expiration et la continuité conversationnelle.

Ces points ne doivent pas être considérés comme décidés tant qu’ils n’ont pas fait l’objet d’un cadrage explicite. Les tests devront évoluer avec les fonctionnalités réellement disponibles dans BATORYA V6.

## 12. Ordre de travail recommandé

Pour limiter les retours en arrière et éviter une architecture prématurée, l’ordre de travail proposé est :
1. valider le présent document de cadrage ;
2. définir le contrat de contexte minimal et ses mécanismes d’enrichissement ;
3. formaliser la mémoire conversationnelle et son cycle de vie ;
4. définir les familles d’intents à partir des usages réels de BATORYA ;
5. construire le catalogue des intents et les règles de clarification ;
6. étudier les solutions techniques locales compatibles avec les contraintes de performance ;
7. définir les tests de fiabilité, de continuité et de consommation de ressources ;
8. détailler l’architecture et préparer l’intégration dans BATORYA Essentiel V6.

---

**Statut final :** ce document centralise le cadrage fonctionnel et les principes du contrat de contexte de Léon V1. Les décisions validées constituent le socle de conception ; les éléments listés comme restant à concevoir devront être traités explicitement avant d’être considérés comme acquis.
