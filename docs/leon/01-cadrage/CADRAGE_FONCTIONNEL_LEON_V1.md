Cadrage fonctionnel de Léon — BATORYA Essentiel V6

Statut : document de travail — décisions de cadrage consolidées
Périmètre : BATORYA Essentiel V6 exclusivement
Version : V1 — cadrage initial
Objet : centraliser les décisions validées et les axes de conception avant la définition détaillée des intents et de l’architecture de Léon.

⸻

1. Objet et périmètre

Léon est l’assistant intégré à BATORYA Essentiel V6. Il doit accompagner l’utilisateur dans la compréhension et l’utilisation de l’application, ainsi que dans ses opérations métier quotidiennes.

Léon doit fonctionner localement, sans dépendre d’un modèle d’IA distant pour assurer ses fonctions.

Ce document constitue une référence de travail pour la conception de Léon. Il ne remplace pas les documents structurants de BATORYA V6 et ne vaut pas validation des choix techniques qui restent à étudier.

Les décisions historiques issues de versions antérieures de Léon constituent uniquement des références d’expérience. Elles ne sont pas automatiquement reconduites dans V6.

2. Mission fonctionnelle retenue

La mission retenue correspond à l’option C : un guide et un assistant métier avec accompagnement actif.

Léon doit pouvoir :

* comprendre les demandes formulées en langage naturel ;
* expliquer les fonctionnalités et les règles métier de BATORYA ;
* aider l’utilisateur à comprendre les informations présentes à l’écran ;
* analyser les données auxquelles il est autorisé à accéder ;
* guider l’utilisateur dans la réalisation d’une opération ;
* aider à préparer une opération, par exemple un devis, sans l’exécuter lui-même ;
* accompagner l’utilisateur lorsque celui-ci navigue entre plusieurs écrans pour résoudre un même problème.

La mission C constitue la cible fonctionnelle. Elle ne signifie pas que toutes les capacités devront être disponibles dès la première version, ni qu’un modèle local puissant devra être imposé si ses performances sont insuffisantes.

La priorité est de construire un Léon utile, fiable et fluide, compatible avec les contraintes d’un fonctionnement local.

3. Limites fonctionnelles de la V1

3.1 Capacités autorisées

La V1 couvre les deux premiers niveaux de capacité.

Niveau 1 — Comprendre et conseiller

* Répondre aux questions sur BATORYA.
* Expliquer les fonctionnalités et les règles métier.
* Aider à interpréter les informations accessibles.
* Analyser une situation à partir de données vérifiées.
* Proposer des explications et des prochaines étapes.

Niveau 2 — Préparer et guider

* Aider à préparer un devis ou une autre opération.
* Indiquer les informations nécessaires.
* Présenter une trame ou une proposition que l’utilisateur pourra reporter lui-même dans BATORYA.
* Guider l’utilisateur dans les étapes et les champs de l’application.

3.2 Capacités exclues

La V1 ne permet pas à Léon d’effectuer des modifications métier.

Il ne doit notamment pas :

* créer ou modifier un document dans BATORYA ;
* enregistrer un règlement ;
* changer un statut ;
* valider ou supprimer une donnée ;
* déclencher une opération métier ;
* remplir automatiquement des champs métier ;
* enregistrer un brouillon dans la base de données.

Cette restriction doit être garantie par les capacités techniques réellement exposées à Léon, et pas uniquement par une consigne adressée au modèle.

Léon doit accéder aux données métier par des mécanismes contrôlés, en lecture seule. Il ne doit pas disposer d’un accès direct en écriture à SQLite.

4. Fiabilité et clarification maîtrisée

Léon ne doit ni inventer des informations, ni présenter une supposition comme un fait.

Il doit :

1. Répondre directement lorsque l’intention est suffisamment claire et que les informations nécessaires sont disponibles.
2. Exploiter le contexte de BATORYA pour éviter les questions inutiles.
3. Identifier les informations réellement manquantes.
4. Poser une ou plusieurs questions ciblées lorsque cela est nécessaire, en regroupant les questions liées lorsque c’est possible.
5. Distinguer les faits vérifiés, les hypothèses explicitement présentées comme telles et les informations inconnues.
6. Reconnaître ses limites lorsqu’il ne peut pas établir une réponse fiable.
7. Ne pas inventer une cause, une règle métier, une donnée ou une fonctionnalité pour éviter de demander une précision.

L’objectif n’est pas de maximiser le nombre de questions posées, mais d’obtenir une compréhension correcte avec le minimum d’échanges nécessaires.

Conséquence pour la conception des intents

Les intents devront être définis de façon à exploiter :

* les formulations naturelles possibles ;
* l’écran et le module actifs ;
* l’objet éventuellement consulté ;
* les informations déjà établies dans la conversation ;
* les informations indispensables pour traiter la demande ;
* les ambiguïtés connues et les questions de clarification pertinentes ;
* les conditions qui permettent de répondre directement ou qui imposent de demander une précision.

La qualité de la compréhension et la limitation des clarifications inutiles devront être vérifiées par des tests.

5. Sobriété des ressources et fonctionnement local

Léon doit être conçu pour fonctionner localement et préserver la fluidité de BATORYA sur des configurations matérielles courantes.

Le choix de la mission C ne doit pas imposer un modèle trop lourd ou des exigences de calcul incompatibles avec une expérience fluide.

Les principes suivants sont retenus :

* Aucun traitement IA de Léon en arrière-plan lorsque l’utilisateur ne le sollicite pas.
* Aucun lancement systématique du modèle pour suivre la navigation dans BATORYA.
* Aucun traitement inutile lorsque Léon n’est pas sollicité.
* Recours au mécanisme le plus léger adapté à la demande.
* Utilisation possible de règles déterministes et de recherches ciblées lorsque celles-ci suffisent.
* Mesure des performances réelles avant de fixer les exigences définitives du modèle local.

Si la mission complète s’avère trop coûteuse ou trop lente, le périmètre fonctionnel ou les exigences devront être revus à la baisse plutôt que de compromettre la fluidité et la viabilité du projet.

Le suivi de navigation, la gestion du contexte et le traitement par le modèle sont des mécanismes distincts. La mise à jour du contexte courant ne doit pas, à elle seule, déclencher une analyse IA.

6. Construction du contexte à la demande

Le contexte de Léon est construit au moment où l’utilisateur le sollicite.

Il n’est pas nécessaire de transmettre en permanence le contexte de l’application au modèle ni de charger systématiquement toutes les données métier.

Le contexte est constitué en fonction de la demande et des informations nécessaires pour y répondre.

6.1 Contexte immédiat

Le contexte minimal pourra notamment comprendre :

* le message de l’utilisateur ;
* le chapitre ou module actif ;
* l’écran et, si pertinent, l’onglet actif ;
* l’objet consulté ou sélectionné, lorsqu’il existe et qu’il est pertinent ;
* les informations de navigation nécessaires à la compréhension de la demande.

Le contenu exact du contexte minimal reste à spécifier.

6.2 Données métier complémentaires

Les données métier complémentaires ne sont récupérées que lorsque la demande le justifie.

Exemples :

* statut d’un devis ;
* échéance d’une facture ;
* informations nécessaires à la recherche d’un client ;
* motifs de blocage établis par les règles métier ;
* autres informations pertinentes pour la demande.

Ces données doivent provenir de sources contrôlées et être accessibles en lecture seule.

Une information absente du contexte immédiat ne doit pas être considérée automatiquement comme inexistante dans BATORYA. Si elle est accessible, une récupération ciblée peut être effectuée. Si elle ne peut pas être vérifiée, Léon doit le signaler.

7. Contexte courant et continuité conversationnelle

Deux dimensions doivent être distinguées.

7.1 Contexte courant

Le contexte courant décrit la situation présente dans BATORYA :

* module actif ;
* écran actif ;
* onglet pertinent ;
* objet actuellement consulté ou sélectionné ;
* informations utiles à la demande actuelle.

Il évolue avec la navigation de l’utilisateur.

Lorsque Léon est sollicité, BATORYA doit lui transmettre le contexte courant correspondant à la situation réelle au moment de la demande.

7.2 Contexte de la demande et mémoire conversationnelle

Le contexte conversationnel conserve les éléments nécessaires à la continuité du dialogue :

* demande initiale et objectif poursuivi ;
* éléments déjà établis ;
* questions et réponses précédentes pertinentes ;
* progression de la résolution ;
* références nécessaires aux échanges antérieurs.

Il ne doit pas être confondu avec l’écran courant.

7.3 Changement de module ou d’écran

Un changement d’écran ou de module ne doit pas annuler automatiquement une demande, interrompre le fil de discussion ou effacer la mémoire conversationnelle.

Léon doit pouvoir prendre en compte le nouvel écran tout en poursuivant la demande initiale lorsque la navigation s’inscrit dans sa résolution.

Exemple :

L’utilisateur se trouve à la première étape de création d’un devis et ne trouve pas un client pourtant enregistré. Il sollicite Léon, puis ouvre le carnet clients avant que Léon ait terminé sa réponse.

Léon doit alors :

1. conserver la demande initiale : retrouver le client manquant dans la création du devis ;
2. prendre en compte le changement de module vers le carnet clients ;
3. poursuivre l’accompagnement en utilisant le nouveau contexte si celui-ci aide à résoudre le problème ;
4. conserver le fil de discussion et son objectif ;
5. ne pas confondre le nouvel écran avec la demande initiale.

Le changement de contexte ne doit pas être interprété comme une nouvelle conversation. Une clarification n’est nécessaire que si une ambiguïté réelle empêche de poursuivre correctement.

8. Mémoire conversationnelle de 30 minutes

Le principe initial d’une mémoire conversationnelle de 30 minutes est retenu pour la V1.

La durée de 30 minutes correspond à une période d’inactivité avant expiration du contexte conversationnel, et non à une durée maximale de traitement d’une demande ni à la durée de chargement du modèle en mémoire vive.

Principes retenus :

* Le contexte conversationnel est conservé pendant la période d’inactivité définie.
* Une navigation dans BATORYA ne remet pas automatiquement le délai à zéro ni ne supprime le fil de discussion.
* Le contexte courant est actualisé indépendamment de la mémoire conversationnelle.
* Une nouvelle interaction pertinente permet de poursuivre le fil de discussion.
* Après expiration, Léon ne doit pas prétendre disposer des éléments du fil précédent si ceux-ci ne sont plus conservés.

Le point de départ exact, le renouvellement du délai, le traitement des demandes encore en cours et les modalités techniques d’expiration restent à préciser.

9. Séparation des responsabilités

Les principes d’architecture suivants sont retenus, sans préjuger de l’implémentation détaillée.

BATORYA est responsable de :

* connaître l’écran et le module actifs ;
* identifier le contexte de navigation ;
* fournir les informations autorisées et nécessaires ;
* récupérer les données métier complémentaires par des services contrôlés ;
* garantir l’absence de capacité d’écriture métier exposée à Léon.

Léon est responsable de :

* interpréter la demande ;
* exploiter le contexte qui lui est fourni ;
* déterminer si les informations disponibles suffisent ;
* produire une explication ou une proposition ;
* demander une clarification lorsqu’elle est nécessaire ;
* signaler les limites de sa réponse.

Le modèle local ne doit pas être la source d’autorité pour les données ou les règles métier. Les informations factuelles et les calculs doivent provenir de BATORYA ou de sources explicitement reconnues.

10. Décisions et points à approfondir

Décisions validées

* Mission de guide et d’assistant métier avec accompagnement actif.
* V1 limitée aux capacités de compréhension, conseil, analyse et préparation.
* Aucune modification métier ni opération d’écriture.
* Fiabilité prioritaire et interdiction d’inventer.
* Clarifications ciblées, sans questions superflues.
* Conception rigoureuse des intents pour améliorer la compréhension immédiate.
* Fonctionnement local et sobriété des ressources.
* Aucun traitement IA en arrière-plan lorsque Léon n’est pas sollicité.
* Contexte construit à la demande.
* Contexte courant actualisé indépendamment de la conversation.
* Continuité de la demande malgré les changements d’écran et de module.
* Mémoire conversationnelle avec expiration après 30 minutes d’inactivité.

Axes restant à concevoir

1. Définition précise du contexte minimal transmis pour chaque demande.
2. Liste des informations de navigation nécessaires.
3. Mécanisme contrôlé de récupération des données métier en lecture seule.
4. Format, contenu et limites de la mémoire conversationnelle.
5. Définition du délai de 30 minutes et de son renouvellement.
6. Gestion des demandes en cours pendant la navigation.
7. Politique de clarification et traitement des références ambiguës.
8. Familles d’intents, puis catalogue détaillé des intents.
9. Stratégie de sélection entre règles déterministes, recherche et modèle local.
10. Critères mesurables de fluidité, de consommation mémoire et de qualité des réponses.
11. Corpus de tests couvrant les changements d’écran, les demandes ambiguës, les données manquantes et la continuité conversationnelle.

Ces points ne doivent pas être considérés comme décidés tant qu’ils n’ont pas fait l’objet d’un cadrage explicite.

11. Ordre de travail recommandé

Pour limiter les retours en arrière et éviter une architecture prématurée, l’ordre de travail proposé est :

1. Valider le présent document de cadrage.
2. Définir le contrat de contexte minimal et ses mécanismes d’enrichissement.
3. Formaliser la mémoire conversationnelle et sa durée de vie.
4. Définir les familles d’intents à partir des usages réels de BATORYA.
5. Construire le catalogue des intents et les règles de clarification.
6. Étudier les solutions techniques locales compatibles avec les contraintes de performance.
7. Définir les tests de fiabilité, de continuité et de consommation de ressources.
8. Détailler l’architecture et préparer l’intégration dans BATORYA Essentiel V6.

⸻

Statut final : ce document consolide le cadrage fonctionnel établi à ce stade. Les décisions validées constituent le socle de conception de Léon V1 ; les éléments listés comme restant à concevoir devront être traités explicitement avant d’être considérés comme acquis.
