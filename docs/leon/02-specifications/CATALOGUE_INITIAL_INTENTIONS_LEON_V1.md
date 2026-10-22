# Catalogue initial des intentions de Léon — BATORYA Essentiel V6

**Statut :** première proposition de travail, non validée comme taxonomie définitive  
**Périmètre :** Léon V1 — BATORYA Essentiel V6 uniquement  
**Objet :** fournir un premier catalogue testable d'intentions utilisateur, dérivé du périmètre V6 et du cadrage de Léon, sans définir l'architecture de classification.

## 1. Autorité documentaire et règles de lecture

Ce catalogue est subordonné aux documents de référence BATORYA V6. Il ne modifie ni le périmètre métier, ni les règles métier, ni les invariants.

Ordre de référence à appliquer en cas de divergence :
1. [CDC fonctionnel et architectural V6.1](../../specifications/cdc-fonctionnel-architectural-v6.md) ;
2. modèle métier V6 et invariants validés ;
3. décisions et errata intégrés au CDC V6.1, à consulter pour la traçabilité ;
4. [Cadrage fonctionnel de Léon V1](../01-cadrage/CADRAGE_FONCTIONNEL_LEON_V1.md), pour les capacités et limites de l'assistant ;
5. le présent catalogue, qui constitue une proposition de taxonomie et d'exemples, non une autorité métier.

Les documents V5 ne constituent pas une source automatique d'intentions V6. Une règle ou une capacité ne doit pas être déduite de son existence historique.

### Statuts utilisés

- **Établi par les sources V6** : le domaine, la fonctionnalité ou la règle est explicitement prévu par les documents de référence.
- **Proposé pour Léon** : la famille, l'intention ou son regroupement est une hypothèse de conception à tester ; cela ne signifie pas que sa taxonomie est validée.
- **À vérifier** : les frontières ou données accessibles dépendent d'une vérification documentaire ou d'un contrat applicatif encore à définir.

La présence d'une intention dans ce catalogue ne garantit pas que Léon puisse déjà répondre à toutes ses formulations. Il faut que les informations nécessaires soient documentées et accessibles par un mécanisme autorisé.

## 2. Principes de classification

1. Classer selon **l'objectif de l'utilisateur**, pas uniquement selon les mots employés, l'écran courant ou le type de document mentionné.
2. Une demande reçoit une **famille principale**. Une ou plusieurs familles secondaires peuvent être ajoutées si la réponse exige réellement plusieurs domaines. Ne créer pas une nouvelle famille pour chaque combinaison.
3. Les familles transversales décrivent le type d'aide demandé ; les familles métier fournissent le domaine de connaissances et les règles applicables.
4. Le guidage est une famille transversale dédiée. Il coordonne les étapes ; le domaine métier reste l'autorité sur les prérequis et les règles propres à l'opération.
5. La navigation courante et la mémoire conversationnelle sont deux contextes distincts. Changer d'écran ne doit pas effacer automatiquement l'objectif conversationnel.
6. Les données métier et les règles vérifiées de BATORYA sont l'autorité. Le modèle ne doit inventer ni données, ni règles, ni capacités.
7. La récupération de données est ponctuelle et limitée au besoin, via des services applicatifs contrôlés en lecture seule. Léon ne reçoit pas un accès libre à SQLite ou au système de fichiers.
8. **Limite impérative de Léon V1 : aucune écriture métier.** Léon ne crée, ne modifie, ne supprime, ne valide ni n'enregistre aucun objet ou brouillon métier ; il n'enregistre aucun règlement, ne change aucun statut et ne déclenche aucune opération métier. Il peut expliquer et guider l'utilisateur qui effectue lui-même l'opération.
9. Ne poser une question que si une information manquante ou une ambiguïté empêche une réponse fiable ou change substantiellement la réponse.
10. Les exemples sont représentatifs, pas exhaustifs. Ils ne doivent pas être interprétés comme une promesse d'action ou de disponibilité des données.

### Champs du catalogue

Pour chaque intention, les tableaux donnent :
- **Objectif / exemples** : le résultat recherché et des formulations naturelles possibles ;
- **Données** : les informations nécessaires à une réponse fiable ;
- **Lecture** : si une récupération ciblée est probablement requise ;
- **Clarification** : quand demander une précision ;
- **Frontière** : les intentions voisines à ne pas confondre.

« Lecture conditionnelle » signifie que Léon doit vérifier si le contexte courant suffit ; sinon, il peut demander une récupération autorisée. Le catalogue ne définit pas encore les noms ni les contrats des services.

## 3. Familles transversales

Les familles transversales sont une taxonomie proposée pour Léon. Leur besoin général est cohérent avec le cadrage fonctionnel ; les IDs et frontières restent à valider sur un corpus.

### T1 — Aide et connaissances BATORYA

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-T01 | Expliquer une fonctionnalité : « À quoi sert le Gantt ? », « Comment fonctionne le catalogue ? » | Documentation V6 validée sur la fonctionnalité | Non si la documentation suffit | Préciser la fonctionnalité si plusieurs sont possibles. Si l'utilisateur demande où la trouver, T2 est secondaire. |
| LI-T02 | Expliquer un concept métier : « Quelle est la différence entre un devis et un BC ? » | Définitions et relations métier validées | Non si la règle est documentée | Si la question porte sur un objet réel, ajouter la famille métier concernée. |
| LI-T03 | Expliquer une règle générale : « Quand un devis est-il gelé ? » | Règle métier V6 et éventuelles conditions | En principe non ; lecture si la question concerne un cas concret | Ne pas confondre explication générale et diagnostic d'un devis précis (T3 + M3/M4). |

### T2 — Navigation et orientation

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-T04 | Trouver une fonctionnalité : « Où se trouve le suivi des garanties ? » | Structure de navigation V6 documentée | Non | Si la demande vise une garantie précise, ajouter M10. |
| LI-T05 | Trouver un objet ou une information : « Où retrouver mon dernier devis ? » | Type d'objet, et éventuellement identifiant ou période | Lecture conditionnelle si l'utilisateur demande de retrouver l'objet, plutôt que son emplacement | T2 porte sur l'orientation ; rechercher réellement le devis mobilise M3. |
| LI-T06 | Comprendre l'écran courant : « Qu'est-ce que je peux consulter ici ? » | Contexte de navigation fiable et documentation de l'écran | Non si le contexte et la documentation suffisent | Ne pas supposer le contenu d'un formulaire ni déduire des champs non transmis. |

### T3 — Compréhension et diagnostic d'une situation

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-T07 | Expliquer un état ou un résultat observé : « Pourquoi ce BC est-il encore en cours ? » | Objet identifié, données courantes pertinentes et règle métier applicable | Oui si les données ne sont pas déjà dans le contexte fiable | Si plusieurs BC sont possibles, demander lequel. Le domaine métier concerné est secondaire ou fournit les faits. |
| LI-T08 | Analyser un écart : « Pourquoi le CA encaissé diffère-t-il du montant facturé ? » | Période, valeurs sources et définitions des indicateurs | Oui, potentiellement plusieurs domaines | Ne pas assimiler facturation et encaissements ; M11 peut être principal, M5 secondaire. |
| LI-T09 | Comprendre une anomalie apparente : « Pourquoi cette garantie n'apparaît-elle pas ? » | Objet concerné, événements métier pertinents et règle de génération | Oui | Ne pas affirmer une cause sans vérification. M10 est le domaine source ; T3 caractérise l'objectif diagnostique. |
| LI-T10 | Déterminer ce qui manque pour expliquer un blocage : « Pourquoi ne puis-je pas faire cette opération ? » | Opération visée, objet et prérequis métier documentés | Lecture conditionnelle | Demander l'opération ou l'objet si indéterminé. T4 peut ensuite guider, sans exécuter l'opération. |

### T4 — Guidage et accompagnement d'une opération

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-T11 | Guider un parcours : « Guide-moi pour préparer un devis. » | Objectif, étapes et prérequis validés du domaine concerné | Lecture conditionnelle | Le domaine métier fournit les règles. Léon décrit les étapes ; il ne remplit pas et n'enregistre pas le devis. |
| LI-T12 | Préparer l'utilisateur avant une opération : « Quelles informations me faut-il avant de facturer ? » | Règles et données requises pour l'opération ciblée | Oui si les prérequis dépendent d'un objet précis | Si l'opération est vague, demander laquelle. Ne pas confondre préparation et exécution. |
| LI-T13 | Reprendre un parcours après navigation : « Je suis revenu au BC, on en était où ? » | Objectif conversationnel conservé, contexte courant actualisé et faits déjà vérifiés | Lecture conditionnelle | Ne pas remplacer l'objectif initial par le seul écran actif ; si le contexte conversationnel a expiré, signaler la limite. |
| LI-T14 | Comparer les prochaines étapes possibles : « Que dois-je vérifier ensuite ? » | Objectif connu et étapes autorisées/documentées | Lecture conditionnelle | Recommander seulement des étapes étayées par les règles V6 ; ne pas lancer d'action métier. |

### T5 — Fonctionnement et limites de Léon

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-T15 | Expliquer une capacité : « Peux-tu analyser mes factures impayées ? » | Capacités réellement disponibles et données accessibles | Vérifier la disponibilité des données si la question inclut une analyse concrète | Distinguer capacité prévue et capacité effectivement disponible dans la version actuelle. |
| LI-T16 | Expliquer une limite d'action : « Peux-tu enregistrer ce règlement ? » | Règles de capacité V1 | Non | Répondre clairement que Léon ne l'enregistre pas ; il peut guider l'utilisateur pour qu'il le fasse lui-même. |
| LI-T17 | Expliquer l'accès aux données et la confidentialité : « Est-ce que tu vois toutes mes données ? » | Contrat de contexte et d'accès validé | Non, sauf question portant sur un accès concret | Ne pas prétendre à un accès général à SQLite, aux fichiers ou aux données non fournies. |

## 4. Familles métier

Les domaines métier ci-dessous sont présents dans le périmètre V6. Leur regroupement en familles d'intentions reste une proposition. Les services de lecture cités sont des besoins d'information, pas des APIs déjà existantes.

### M1 — Clients

**Ancrage V6 :** les clients forment un référentiel indépendant ; les documents historiques conservent leurs propres snapshots.  
**Frontière :** une demande sur les informations du client relève de M1 ; une demande sur le contenu ou l'état d'un devis relève de M3, même si le devis est lié à ce client.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M01 | Rechercher un client : « Retrouve Martin Dupont. » | Critères de recherche disponibles | Oui, sauf résultat déjà fourni dans le contexte | Si plusieurs résultats sont plausibles, demander de choisir ; ne pas sélectionner arbitrairement. |
| LI-M02 | Consulter une fiche client : « Quelles coordonnées ai-je pour ce client ? » | Référence client et champs accessibles | Oui | Identifier le client si absent ou ambigu. Ne pas exposer des données non nécessaires. |
| LI-M03 | Comprendre l'historique lié à un client : « Quels documents sont associés à ce client ? » | Client identifié et références de documents accessibles | Oui, potentiellement plusieurs domaines | Distinguer l'historique du client des snapshots historiques propres aux documents. |

### M2 — Catalogue des prestations

**Ancrage V6 :** le catalogue constitue la base des prestations proposées dans les devis ; les lignes de devis conservent leur photographie commerciale et restent autonomes par rapport aux évolutions du catalogue. Les garanties par défaut se configurent au niveau des prestations.  
**Frontière :** rechercher une prestation relève de M2 ; comprendre comment elle est utilisée dans un devis précis peut ajouter M3.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M04 | Rechercher une prestation : « As-tu une prestation pour poser une prise RJ45 ? » | Catalogue V6 réel et critères de recherche | Oui | Clarifier le besoin seulement si les résultats sont trop ambigus. Ne jamais reconstruire ou inventer une prestation absente du catalogue. |
| LI-M05 | Consulter les caractéristiques d'une prestation : « Quelle est la désignation et l'unité de cette prestation ? » | Prestation identifiée et champs validés | Oui | Distinguer la prestation catalogue de la ligne snapshot d'un ancien devis. |
| LI-M06 | Comprendre les garanties par défaut d'une prestation : « Quelles garanties sont associées à cette prestation ? » | Configuration de garanties du catalogue | Oui | Expliquer qu'il s'agit de valeurs par défaut ; pour une garantie déjà générée, utiliser M10 et les snapshots concernés. |

### M3 — Devis

**Ancrage V6 :** le devis est le document commercial préalable à l'acceptation ; un devis accepté peut être modifiable tant qu'il n'est pas gelé. Le catalogue ne modifie pas rétroactivement les lignes déjà utilisées.  
**Frontière :** le devis reste distinct du BC créé à l'acceptation ; la facturation relève de M5.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M07 | Rechercher ou consulter un devis : « Retrouve le devis de Dupont. » | Critères de recherche, client éventuel, références de devis | Oui | Si plusieurs devis correspondent, demander une période, un numéro ou un autre critère. |
| LI-M08 | Expliquer le statut ou le cycle de vie d'un devis : « Pourquoi ce devis est-il accepté mais non modifiable ? » | Devis identifié, état, gel et événements déclencheurs pertinents | Oui | Si le cas est concret, diagnostic T3 en complément ; ne pas déduire le gel d'un seul statut. |
| LI-M09 | Expliquer le calcul ou le contenu d'un devis : « Comment arrive-t-on à ce total ? » | Lignes, quantités, prix, remises et règle de calcul | Oui | Ne pas recalculer à partir d'informations partielles ni utiliser de calcul flottant approximatif. |
| LI-M10 | Préparer un devis sans l'exécuter : « Aide-moi à préparer le devis pour ces travaux. » | Besoin exprimé, catalogue et informations nécessaires au parcours | Oui, selon le besoin | T4 coordonne le guidage ; M2 fournit les prestations. Léon ne crée ni ne sauvegarde de devis et ne remplit aucun champ. |

### M4 — Bons de commande (BC)

**Ancrage V6 :** le BC est le dossier métier central après acceptation du devis ; il relie notamment client, devis, facturation, règlements, planification, notes, PV et garanties. Son état est dérivé de règles métier, et non librement saisi.  
**Frontière :** le BC n'est pas un PDF autonome ni une gestion de chantier indépendante.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M11 | Rechercher ou consulter un BC : « Retrouve le BC de ce chantier. » | Critères et référence de BC, client ou devis éventuel | Oui | Ne pas traiter « chantier » comme une entité indépendante du BC. |
| LI-M12 | Expliquer l'état ou l'avancement facturé d'un BC : « Pourquoi le BC est-il terminé ? » | BC, factures actives, règlements, avoirs et règles de recalcul pertinentes | Oui | L'avancement mesure la facturation, pas l'avancement physique des travaux. T3 peut qualifier la demande. |
| LI-M13 | Comprendre les liens d'un BC : « Quels devis, factures et PV sont rattachés à ce BC ? » | BC identifié et références des objets associés | Oui | Les objets restent sous la responsabilité de leur domaine métier respectif. |

### M5 — Facturation, règlements et avoirs

**Ancrage V6 :** les types de factures comprennent acompte, situation, solde et avoir ; les règlements sont des entités distinctes ; les avoirs corrigent financièrement une facture sans supprimer l'historique d'origine. Le CA encaissé est fondé sur les encaissements et remboursements selon le référentiel réglementaire applicable.  
**Frontière :** facturé n'est pas encaissé ; un avoir n'est ni un encaissement ni une réouverture automatique de la facturation. Les questions de synthèse de gestion peuvent mobiliser M11.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M14 | Rechercher ou consulter une facture : « Retrouve la dernière facture de ce BC. » | BC/client, type, période ou numéro si nécessaire | Oui | Préciser le BC ou la période si plusieurs résultats. |
| LI-M15 | Comprendre un type ou un état de facture : « Quelle différence entre une situation et un solde ? » | Type de facture et règles V6 | Non pour une explication générale ; oui pour un cas précis | Ne pas confondre type de facture, état de paiement et indicateur « en retard ». |
| LI-M16 | Expliquer le reste dû : « Combien reste-t-il à payer sur cette facture ? » | Montant, encaissements actifs, avoirs actifs, remboursements et annulations pertinents | Oui | Le reste dû est calculé, jamais supposé. Identifier la facture si ambiguë. |
| LI-M17 | Comprendre les règlements : « Quels paiements ont été enregistrés pour cette facture ? » | Facture et règlements actifs/historiques pertinents | Oui | Léon peut consulter et expliquer, jamais enregistrer, modifier ou annuler un règlement. |
| LI-M18 | Comprendre un avoir ou un remboursement : « Pourquoi cet avoir laisse-t-il encore un crédit ? » | Facture d'origine, avoirs, encaissements, remboursements et règle applicable | Oui | Si l'impact URSSAF est demandé, ajouter M12 et/ou M13 ; ne pas inventer le traitement réglementaire. |
| LI-M19 | Comprendre les factures impayées ou en retard : « Quelles factures ont un reste dû et dépassent l'échéance ? » | Factures actives, échéances, règlements et soldes calculés | Oui | L'indicateur de retard peut coexister avec un paiement partiel. Si l'utilisateur demande une synthèse globale, M11 peut être secondaire. |

### M6 — Planification

**Ancrage V6 :** le module Planification comprend Calendrier et Gantt. Les interventions/travaux sont rattachés à un BC ; congés et indisponibilités ne le sont pas. La planification n'a pas autorité sur le cycle de vie du BC.  
**Frontière :** pas de synchronisation Google/Outlook ni de gestion autonome de chantier dans le périmètre V6.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M20 | Consulter les événements d'une période : « Qu'ai-je de prévu vendredi ? » | Période, fuseau/horaires pertinents et événements accessibles | Oui | Demander la date si « vendredi » ne peut pas être résolu de façon fiable. |
| LI-M21 | Comprendre un événement ou son rattachement : « À quel BC correspond cette intervention ? » | Événement identifié et référence BC éventuelle | Oui | Ne pas déduire un rattachement si absent. |
| LI-M22 | Comprendre les dates d'un BC dans le Gantt : « Pourquoi ce BC n'apparaît-il pas dans le Gantt ? » | BC, dates de début/fin et règles du Gantt | Oui | Un BC sans dates n'a pas de barre ; ne pas assimiler la planification à un statut métier. |

### M7 — Notes

**Ancrage V6 :** une note est une information libre interne rattachée à un BC ; il n'existe pas de moteur de tâches ou de rappels associé.  
**Frontière :** une note n'est pas une tâche ni un workflow.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M23 | Retrouver ou consulter les notes d'un BC : « Quelles notes ai-je prises sur ce BC ? » | BC identifié et notes accessibles | Oui | Si plusieurs BC sont possibles, demander lequel. |
| LI-M24 | Expliquer la portée d'une note : « Cette note déclenche-t-elle un rappel ? » | Fonctionnement documenté des notes | Non | Expliquer qu'une note ne crée pas, à elle seule, une tâche ou un rappel automatique. Léon ne modifie pas la note. |

### M8 — Dépenses et fournisseurs

**Ancrage V6 :** une dépense peut être globale ou rattachée à un BC et associée à un fournisseur. Le fournisseur est un référentiel indépendant ; les fournisseurs archivés restent consultables pour l'historique. V6 ne gère ni paiement fournisseur ni échéancier fournisseur.  
**Frontière :** ne pas introduire de suivi « à payer » ou de workflow de règlement fournisseur.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M25 | Consulter ou rechercher une dépense : « Retrouve la dépense de matériel du mois dernier. » | Période, description, montant ou référence si disponible | Oui | Clarifier si plusieurs dépenses correspondent. |
| LI-M26 | Comprendre le rattachement ou les données d'une dépense : « Cette dépense est-elle rattachée à un BC ? » | Dépense et éventuelle référence BC/fournisseur | Oui | Une dépense peut être globale. Ne pas inférer un BC à partir du seul fournisseur. |
| LI-M27 | Rechercher ou consulter un fournisseur : « Quelles coordonnées ai-je pour ce fournisseur ? » | Fournisseur et champs disponibles | Oui | Si la question porte sur une dépense donnée, M8 reste la famille principale mais la sous-intention doit distinguer dépense et fournisseur. Ne pas proposer un fournisseur archivé comme sélectionnable pour une nouvelle dépense. |

### M9 — PV et réception

**Ancrage V6 :** le PV est facultatif, immuable après émission et ne conditionne ni le solde, ni l'état Terminé, ni le déclenchement des garanties. Une levée de réserves crée un nouveau PV qui référence l'original.  
**Frontière :** le PV et la garantie sont distincts ; la levée de réserves ne modifie pas le suivi interne des garanties.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M28 | Consulter un PV : « Retrouve le PV de réception de ce BC. » | BC, type/date ou numéro de PV | Oui | Plusieurs PV initiaux peuvent exister ; préciser lequel si nécessaire. |
| LI-M29 | Comprendre les réserves et leur levée : « Cette réserve a-t-elle fait l'objet d'une levée ? » | PV d'origine et PV de levée associés | Oui | Une levée est un nouveau PV ; ne pas la présenter comme une modification de l'original. |
| LI-M30 | Comprendre l'effet du PV sur le parcours : « Le PV est-il obligatoire pour terminer le BC ? » | Règles métier V6 | Non pour la règle générale | Le PV est facultatif ; ne pas confondre réception et génération des garanties. |

### M10 — Garanties

**Ancrage V6 :** les garanties sont configurées par prestation, copiées en snapshots sur les lignes de devis/BC et générées à l'émission du premier solde actif. Le suivi est interne et indicatif ; il ne constitue pas une détermination juridique du point de départ d'une garantie légale.  
**Frontière :** configuration par défaut du catalogue = M2 ; suivi d'une garantie générée = M10 ; PV = M9.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M31 | Consulter les garanties d'un BC : « Quelles garanties sont suivies pour ce BC ? » | BC, garanties générées et états dérivés | Oui | Identifier le BC si nécessaire. |
| LI-M32 | Comprendre la date ou l'état de suivi : « Pourquoi cette garantie est-elle échue ? » | Garantie, dates de suivi et règle de calcul | Oui | Toujours préciser « Suivi interne BATORYA — date indicative » ; ne pas donner une conclusion juridique. |
| LI-M33 | Comprendre le déclenchement d'une garantie : « Pourquoi la garantie existe-t-elle sans PV ? » | Facture de solde et données de garantie pertinentes | Oui pour un cas concret | Le déclenchement dépend du solde actif, pas du PV, de la réception ou du paiement du solde. |

### M11 — Analyses de gestion

**Ancrage V6 :** les analyses sont une couche de lecture des modules métier, pas un second moteur comptable. CA encaissé, CA engagé, CA prévisionnel et charges/marge ont des définitions distinctes.  
**Frontière :** les calculs doivent reposer sur les données et règles métier sources ; les indicateurs URSSAF ont leur propre base réglementaire.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M34 | Comprendre le CA encaissé, engagé ou prévisionnel : « Quelle différence entre ces trois montants ? » | Définitions validées et éventuellement période | Non pour les définitions ; oui pour les montants réels | Ne jamais présenter le CA engagé ou prévisionnel comme du CA encaissé. |
| LI-M35 | Consulter une analyse sur une période : « Quel est mon CA encaissé ce trimestre ? » | Période et sources de règlements/remboursements selon la définition applicable | Oui | Clarifier période ou indicateur si nécessaire. |
| LI-M36 | Comprendre une marge ou des charges : « Pourquoi ma marge a-t-elle baissé ? » | Recettes, dépenses, période et méthode de calcul disponible | Oui, potentiellement plusieurs domaines | Expliquer uniquement les facteurs vérifiables ; ne pas confondre marge d'analyse et résultat comptable complet. |

### M12 — URSSAF et suivi déclaratif

**Ancrage V6 :** le module calcule, estime, historise, alerte et aide à préparer la déclaration. Il ne transmet pas automatiquement une déclaration officielle. Le CA URSSAF est basé sur les encaissements et sur les règles réglementaires versionnées concernant notamment avoirs et remboursements.  
**Frontière :** le CA facturé, engagé ou prévisionnel n'est pas interchangeable avec le CA encaissé utilisé pour le suivi URSSAF.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M37 | Comprendre une période URSSAF : « Quelle période est concernée par ce montant ? » | Profil, périodicité et période de déclaration | Oui si l'utilisateur parle d'une période réelle | Clarifier la période si elle n'est pas identifiable. |
| LI-M38 | Comprendre un montant calculé ou estimé : « Comment ce montant a-t-il été calculé ? » | Encaissements, remboursements, période et version de règle applicable | Oui | Distinguer calcul, estimation et information réglementaire ; ne pas inventer un taux. |
| LI-M39 | Préparer la déclaration : « Aide-moi à vérifier les chiffres avant ma déclaration. » | Période et données calculées nécessaires | Oui | T4 peut guider la vérification ; l'utilisateur reste responsable de sa déclaration. Aucune télétransmission ni déclaration automatique. |

### M13 — Référentiel réglementaire

**Ancrage V6 :** les règles réglementaires sont versionnées ; le traitement de certains éléments, dont les avoirs/remboursements pour l'URSSAF, dépend de la règle applicable à la période. BATORYA expose la version du référentiel et permet des mises à jour de référence.  
**Frontière :** expliquer une règle versionnée relève de M13 ; expliquer un résultat URSSAF concret relève généralement de M12 avec M13 en soutien.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M40 | Expliquer une règle documentée : « Quelle règle s'applique à cette période ? » | Référentiel validé, version et date/période pertinente | Oui si la version applicable doit être identifiée | Si la date ou le cas est ambigu, demander la précision. Ne pas remplacer la règle par une connaissance générale non vérifiée. |
| LI-M41 | Identifier la version ou la provenance d'une règle : « Quelle version du référentiel est utilisée ? » | État de service/version du référentiel | Lecture conditionnelle | Distinguer version installée et version applicable à une période historique. |
| LI-M42 | Expliquer l'impact réglementaire d'un avoir/remboursement : « Comment cet avoir affecte-t-il mon CA URSSAF ? » | Avoir/remboursement, période et version de règle applicable | Oui | M12 est généralement la famille principale si l'objectif est le montant URSSAF ; M13 fournit la règle. |

### M14 — Documents PDF

**Ancrage V6 :** les PDF matérialisent des objets métier ; SQLite reste la source de vérité. Les types documentaires comprennent devis, acomptes, situations, soldes, avoirs et PV ; le BC n'est pas un document PDF autonome. Les documents sont localisés par racine de stockage et chemin relatif.  
**Frontière :** si la demande porte sur le sens métier du contenu, la famille métier source est principale ; M14 porte sur la recherche, la localisation ou la version du document.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M43 | Retrouver un PDF : « Où est le PDF de cette facture ? » | Objet métier identifié, métadonnées de document et état de localisation | Oui | Demander le type/numéro si plusieurs documents sont possibles. Ne pas parcourir librement le système de fichiers. |
| LI-M44 | Comprendre une version ou une localisation : « Pourquoi ce PDF est-il non localisable ? » | Référence du document, racine connue et chemin relatif | Oui | Ne pas prétendre que le document n'existe plus si seule sa localisation est inconnue. |
| LI-M45 | Comprendre quels objets ont un PDF : « Le BC a-t-il son propre PDF ? » | Règles documentaires V6 | Non pour la règle générale | Le BC n'est pas un PDF autonome ; les devis, factures et PV sont des types documentaires prévus. |

### M15 — Sauvegardes, restauration et import historique

**Ancrage V6 :** les sauvegardes sont locales et centralisées ; la base métier et machine.db sont distinctes. L'import historique utilise un convertisseur externe puis un import strict, avec validation et transaction, sans réparation implicite.  
**Frontière :** ne pas confondre la sauvegarde des données, la localisation des PDF et la correction d'une donnée métier.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M46 | Comprendre l'état d'une sauvegarde : « Quand la dernière sauvegarde a-t-elle réussi ? » | État de sauvegarde exposé par BATORYA | Oui si l'état n'est pas dans le contexte | Léon peut expliquer l'état ; il ne lance pas de sauvegarde. |
| LI-M47 | Comprendre la portée d'une restauration : « Est-ce que restaurer la base restaure aussi machine.db ? » | Règles validées de sauvegarde/restauration | Non pour la règle générale | Expliquer les limites précises ; ne déclencher aucune restauration. |
| LI-M48 | Comprendre une anomalie d'import historique : « Pourquoi cet élément n'a-t-il pas été importé ? » | Rapport d'import et anomalie vérifiée, si accessibles | Oui | Ne pas réparer, ignorer ou reclasser automatiquement l'anomalie ; proposer l'explication disponible et la voie de vérification documentée. |

### M16 — Paramètres, licence et services BATORYA

**Ancrage V6 :** les paramètres généraux, l'état de licence, les mises à jour et la version du référentiel sont exposés par les services BATORYA. Les paramètres URSSAF ne sont pas dupliqués dans les paramètres généraux.  
**Frontière :** la capacité propre de Léon relève de T5 ; la règle réglementaire relève de M13.

| ID | Objectif et formulations possibles | Données nécessaires | Lecture | Clarification et frontières |
|---|---|---|---|---|
| LI-M49 | Comprendre un paramètre général : « À quoi sert le délai de paiement par défaut ? » | Documentation du paramètre et portée de son application | Non pour la règle générale ; oui pour un réglage concret | Léon explique mais ne modifie pas le paramètre. |
| LI-M50 | Comprendre l'état de licence ou une mise à jour : « Pourquoi certaines fonctions sont-elles limitées ? » | État de licence/service et règle d'accès applicable | Lecture conditionnelle | Ne pas affirmer une cause sans état vérifié ; T3 peut être secondaire pour le diagnostic. |
| LI-M51 | Comprendre les services locaux et l'état du service BATORYA : « Quelle version est installée ? » | État exposé par le service concerné | Oui si non présent dans le contexte | Ne pas déclencher de mise à jour, de communication distante ou d'action système. |

## 5. Cas de confusion à tester

Ces cas servent à vérifier que les intentions proches ne sont pas confondues. Ils ne définissent pas de mécanisme technique de classification.

| ID test | Formulation | Famille principale attendue | Famille secondaire possible | Confusion à éviter |
|---|---|---|---|---|
| TC-01 | « As-tu une prestation pour poser une prise RJ45 ? » | M2 Catalogue | — | Ne pas classer comme devis uniquement parce que les prestations sont utilisées dans les devis. |
| TC-02 | « Quelle prestation a été utilisée dans mon dernier devis ? » | M3 Devis | M2 Catalogue | La prestation est recherchée à partir du devis ; ne pas ignorer le document source. |
| TC-03 | « Pourquoi le BC est-il encore en cours ? » | T3 Diagnostic | M4 BC, M5 Facturation | Ne pas conclure à partir du seul statut affiché ; vérifier les conditions métier. |
| TC-04 | « Combien reste-t-il à payer sur cette facture ? » | M5 Facturation/règlements/avoirs | — | Ne pas répondre avec le montant initial de la facture sans tenir compte des encaissements et avoirs. |
| TC-05 | « Quel montant a été encaissé ce trimestre ? » | M11 Analyses ou M12 URSSAF selon l'objectif explicite | M5 Facturation/règlements/avoirs | Clarifier si l'utilisateur parle d'un indicateur de gestion ou de la base URSSAF lorsque cela change le calcul. |
| TC-06 | « Pourquoi cet avoir change-t-il le montant URSSAF ? » | M12 URSSAF | M13 Référentiel, M5 Facturation | Ne pas appliquer une règle non versionnée ou non vérifiée. |
| TC-07 | « Le PV est-il obligatoire pour déclencher les garanties ? » | M10 Garanties ou M9 PV selon l'objet de la question | L'autre famille | Ne pas confondre réception et déclenchement des garanties : le solde actif déclenche les garanties. |
| TC-08 | « Cette dépense est-elle liée à un fournisseur ? » | M8 Dépenses/fournisseurs | — | Ne pas inventer de relation si elle n'est pas enregistrée. |
| TC-09 | « Pourquoi ma marge a-t-elle baissé ? » | M11 Analyses | M8 Dépenses, M5 Facturation/règlements | L'analyse synthétise les sources mais ne remplace pas les règles de calcul métier. |
| TC-10 | « Quelle règle a servi à calculer le montant URSSAF de l'année dernière ? » | M13 Référentiel si la question porte sur la règle | M12 URSSAF | Ne pas confondre version installée actuellement et version applicable à la période historique. |
| TC-11 | « Pourquoi ce PDF est-il introuvable ? » | M14 Documents | M3/M5/M9 selon le type documentaire | « Non localisable » ne signifie pas automatiquement « supprimé ». |
| TC-12 | « Pourquoi cet élément de mon ancien fichier n'a-t-il pas été importé ? » | M15 Sauvegardes/import historique | Domaine métier source si identifiable | Ne pas réparer ou réimporter automatiquement ; consulter l'anomalie disponible. |
| TC-13 | « Guide-moi pour préparer un devis pour ce client. » | T4 Guidage | M1 Clients, M2 Catalogue, M3 Devis | T4 coordonne ; les domaines fournissent les données et règles. Aucune création ni saisie automatique. |
| TC-14 | « Peux-tu enregistrer le règlement que je viens de recevoir ? » | T5 Limites de Léon | M5 si l'utilisateur demande ensuite un guidage | Répondre que Léon ne peut pas l'enregistrer ; ne pas tenter une écriture. |
| TC-15 | « Où retrouver mes factures en retard ? » | T2 Navigation si la demande porte sur l'emplacement | M5 Facturation si l'utilisateur veut la liste réelle | Distinguer « où » de « lesquelles ». |
| TC-16 | « Je suis revenu sur le BC, on en était où ? » | T4 Guidage/continuité | M4 BC et famille(s) du parcours initial | Ne pas perdre l'objectif précédent au seul motif du changement d'écran. |

## 6. Clarification et réponse sûre

La classification ne dispense pas de vérifier que la demande est assez précise et que les données nécessaires sont accessibles.

Demander une précision notamment lorsque :
- plusieurs clients, devis, BC, factures ou périodes correspondent et que le choix change la réponse ;
- une période ou un indicateur n'est pas identifiable ;
- une formulation comme « ce document », « ce montant » ou « cette garantie » ne peut pas être reliée de façon fiable au contexte ;
- deux interprétations métier entraînent des calculs ou des conseils différents.

Ne pas demander une précision lorsque :
- l'intention et l'objet sont clairement identifiés ;
- la réponse est une règle générale documentée ;
- le contexte fiable ou une récupération ciblée autorisée suffit.

Si les données ne sont pas disponibles ou ne peuvent pas être vérifiées, Léon doit le dire explicitement. Il ne doit pas inventer un résultat, une règle, une cause ou une capacité pour compléter la réponse.

## 7. Points à vérifier avant validation du catalogue

Les points suivants restent ouverts ; le catalogue ne doit pas être considéré comme définitif avant leur résolution.

1. **Contrats de lecture accessibles à Léon :** les services applicatifs autorisés, leurs données de sortie et leurs erreurs ne sont pas définis par ce catalogue. Vérifier les contrats lors de la conception applicative, sans donner à Léon un accès direct à SQLite.
2. **Granularité des familles :** tester si les familles M8 (dépenses et fournisseurs), M13 (référentiel réglementaire) et M15 (sauvegardes/restauration/import) produisent des confusions. Les fusionner ou les séparer sur la base du corpus et des responsabilités métier, pas pour viser un nombre prédéterminé de familles.
3. **Analyses vs URSSAF :** les définitions des indicateurs, la base réglementaire et la version applicable doivent être respectées. Pour chaque exemple, vérifier si la demande est une analyse de gestion ou une préparation déclarative.
4. **Documents et historique :** confirmer quelles métadonnées de localisation, versions, sauvegardes et anomalies d'import seront réellement accessibles en lecture seule.
5. **Référentiel réglementaire :** vérifier comment la version applicable à une période historique peut être identifiée et exposée. Ne pas inférer ce contrat à partir de la seule présence d'une version installée.
6. **Contexte de navigation et mémoire conversationnelle :** le cadrage pose les principes, mais le contrat minimal exact et les modalités d'expiration/reprise restent à définir.
7. **Formulations et corpus :** les exemples actuels sont des cas initiaux rédigés pour la conception. Il faudra les enrichir avec des formulations variées, ambiguës, négatives et multi-domaines, puis mesurer les confusions.
8. **Vérification des versions de référence :** le CDC V6.1 se réfère aux décisions et au modèle SQLite V3.7 ; vérifier toute règle issue d'une version ultérieure du modèle qui serait encore en relecture avant de l'utiliser comme décision validée.
9. **Évolution du périmètre :** ajouter ou modifier une intention lorsque le comportement V6 correspondant est confirmé. Ne pas créer d'intention qui implique TVA, comptabilité complète, rapprochement bancaire, paiement fournisseur, télétransmission URSSAF, synchronisation Google/Outlook, gestion de salariés ou gestion autonome de chantier.
10. **Évaluation :** avant de choisir la stratégie technique de classification, établir un jeu de tests de référence et mesurer au minimum la famille principale, les familles secondaires justifiées, les demandes nécessitant une clarification et les réponses impossibles faute de données.

## 8. Critères de revue pour la prochaine version

La prochaine revue devra vérifier, pour chaque intention :
- qu'elle correspond à un objectif utilisateur distinct et utile ;
- qu'elle ne duplique pas une autre intention sous une formulation différente ;
- que ses frontières sont compréhensibles face aux intentions proches ;
- que les données nécessaires et les conditions de clarification sont identifiables ;
- qu'elle ne promet pas une donnée ou une action non disponible ;
- qu'elle respecte l'interdiction d'écriture métier de Léon V1 ;
- que les cas de test couvrent les confusions prévisibles ;
- que le domaine métier et la règle appliquée sont traçables vers les sources V6.

**Conclusion :** ce catalogue est une première base de test et de discussion. Il n'est ni une spécification technique, ni un catalogue définitivement validé, ni une autorisation d'implémenter les accès métier listés.
