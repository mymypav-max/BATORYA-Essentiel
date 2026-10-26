# Cycle de vie de la conversation — Léon V1

**Statut :** décisions fonctionnelles arbitrées le 27 octobre 2026 ; spécification technique à poursuivre  
**Périmètre :** BATORYA Essentiel V6 — Léon V1 uniquement  
**Nature :** spécification fonctionnelle ; aucune implémentation applicative n'est décrite comme existante  
**Document de référence :** ce document remplace les propositions antérieures contradictoires sur le cycle de vie de la conversation.

## 1. Objectif et principes

Ce document définit le démarrage, la continuité, l'annulation, l'expiration et la suppression d'une conversation de Léon V1.

Principes retenus :

- Léon est un assistant local, sollicité explicitement. L'ouverture du panneau ou la navigation dans BATORYA ne déclenche aucune inférence.
- Une seule génération peut être active à la fois.
- La mémoire conversationnelle est temporaire et conservée en RAM uniquement.
- La fermeture du panneau n'est pas la fermeture de la conversation.
- La fermeture complète de BATORYA met fin à la conversation.
- La mémoire conversationnelle, les connaissances documentées et les données métier sont trois catégories séparées.
- Léon reste en lecture seule côté métier : aucune création, modification, suppression, validation ou autre action métier.

## 2. Démarrage et continuité

### 2.1 Ouverture et fermeture du panneau

- Ouvrir le panneau Léon ne lance pas le modèle et ne démarre aucune génération.
- Fermer le panneau ne supprime pas la conversation et n'interrompt pas une génération en cours.
- Une génération continue en arrière-plan lorsque le panneau est fermé.
- À la réouverture, l'utilisateur retrouve l'état de la conversation tant qu'elle n'a pas expiré et que BATORYA n'est pas fermé.

### 2.2 Une réponse terminée n'est pas une conversation terminée

La fin d'une génération libère Léon pour une nouvelle demande. Elle n'efface ni l'historique ni le contexte conversationnel. La conversation reste disponible jusqu'à l'expiration, à une réinitialisation explicite ou à la fermeture complète de BATORYA.

### 2.3 Contexte utilisé par Léon

Pour la V1, Léon ne reçoit pas automatiquement le contexte de la page ou de l'écran affiché. Il s'appuie sur le message de l'utilisateur, les connaissances documentées et, lorsque la demande le nécessite, des données métier fournies ponctuellement par un mécanisme autorisé en lecture seule.

Les services et données métier accessibles ne sont pas exhaustivement définis dans ce document. Ils seront précisés à mesure que BATORYA sera conçu et implémenté. Si une donnée requise n'est pas disponible, Léon le signale et ne la devine pas.

## 3. Gestion d'une génération

### 3.1 Un seul message en traitement

Pendant que Léon génère une réponse, la saisie et l'envoi d'un nouveau message sont bloqués. Aucun message n'est placé en file d'attente et aucune génération concurrente n'est lancée.

Si l'utilisateur veut envoyer une autre demande avant la fin, il doit d'abord annuler la génération en cours.

### 3.2 Annulation volontaire

L'utilisateur peut arrêter explicitement une génération. Après l'annulation :

1. la génération est réellement interrompue ;
2. les ressources mobilisées par cette génération sont libérées ;
3. la partie de réponse déjà produite reste visible et porte la mention « Réponse interrompue » ;
4. cette réponse partielle reste dans le contexte de la conversation active ;
5. l'utilisateur peut envoyer une nouvelle demande.

Léon peut s'appuyer sur la réponse partielle pour interpréter la demande suivante. Il doit la traiter comme incomplète, jamais comme une réponse terminée ou comme une information métier vérifiée. Si la nouvelle demande est ambiguë, il demande une précision plutôt que de supposer.

### 3.3 Délai maximal de génération

Une génération ne doit pas pouvoir tourner indéfiniment. Un délai maximal sera défini à partir des essais du modèle local sur le matériel cible ; aucune durée chiffrée n'est fixée à ce stade.

En cas de dépassement :

- la génération est arrêtée ;
- les ressources sont libérées ;
- la réponse partielle reste visible avec la mention « Réponse interrompue » ;
- le contexte conversationnel est conservé tant qu'il n'a pas expiré ;
- l'utilisateur peut réessayer.

### 3.4 Erreur technique

Si le moteur local échoue pendant la génération :

- Léon signale l'échec technique ;
- la réponse partielle reste visible avec une indication d'échec technique ;
- le contexte conversationnel reste disponible jusqu'à son expiration ;
- les ressources de génération sont libérées ;
- aucune relance automatique n'est effectuée.

Une réponse partielle, interrompue ou affectée par une erreur ne doit jamais être présentée comme complète.

## 4. Expiration après 30 minutes

### 4.1 Règle de délai

La conversation expire après 30 minutes d'inactivité. Le délai est établi à partir de l'événement pertinent le plus récent : la réception du dernier message de l'utilisateur ou la fin de la dernière génération.

La génération en cours n'est pas interrompue par le seul écoulement du délai de mémoire. À la fin de la génération — réponse terminée, annulation, dépassement du délai maximal ou erreur — le délai d'inactivité est recalculé à partir de l'événement le plus récent.

Les événements suivants ne réinitialisent pas le délai : ouvrir ou fermer le panneau Léon, naviguer dans BATORYA, changer de module, laisser l'application ouverte ou effectuer un traitement interne. La fermeture du panneau n'efface pas la conversation.

### 4.2 Nettoyage effectif

L'expiration doit être appliquée par deux mécanismes complémentaires :

1. un nettoyage automatique après le délai ;
2. une vérification de l'expiration avant toute nouvelle interaction transmise au modèle.

Si le nettoyage automatique a été retardé, la vérification préalable doit effacer le contexte expiré avant qu'il puisse être réutilisé.

À l'expiration :

- l'historique visible disparaît du panneau, même si celui-ci reste ouvert ;
- le contexte conversationnel temporaire est effacé ;
- Léon revient à son état initial ;
- la prochaine demande démarre silencieusement une nouvelle conversation ;
- aucun avertissement préalable ou message d'expiration n'est affiché.

L'ancienne conversation ne doit pas être reconstruite à partir de suppositions. Les connaissances documentées ne sont pas effacées. L'expiration de la conversation ne supprime ni ne modifie les données métier de BATORYA.

## 5. Nouvelle conversation demandée par l'utilisateur

Une action « Nouvelle conversation » permet de repartir de zéro sans attendre l'expiration.

- Si la conversation est vide, l'action s'exécute immédiatement, sans confirmation.
- Si des messages existent, une confirmation est demandée.
- Si l'utilisateur annule la confirmation, la conversation reste inchangée et une génération en cours continue.
- Si l'utilisateur confirme, toute génération en cours est annulée, puis l'historique et le contexte temporaire sont effacés.
- La nouvelle conversation est affichée vierge et prête à recevoir un message.

Aucun résumé n'est généré automatiquement avant l'effacement. L'action ne supprime ni les connaissances documentées ni les données métier.

## 6. Fermeture complète de BATORYA

La fermeture complète de BATORYA met immédiatement fin à la conversation :

- toute génération en cours est interrompue ;
- le moteur est arrêté proprement et les ressources sont libérées ;
- l'historique et le contexte conversationnel ne sont pas sauvegardés sur disque ;
- la conversation n'est pas restaurée au prochain lancement.

La fermeture de l'application est prioritaire : BATORYA n'attend pas la fin d'une génération qui ne sera pas conservée.

## 7. Séparation des informations

### 7.1 Mémoire conversationnelle

Elle contient temporairement les messages et les éléments nécessaires à la continuité de l'échange, notamment les précisions de l'utilisateur et les réponses partielles. Elle est conservée en RAM uniquement, puis effacée à l'expiration, à la réinitialisation ou à la fermeture complète de BATORYA.

### 7.2 Connaissances documentées

Les explications sur le fonctionnement de BATORYA, son vocabulaire, ses procédures et ses règles métier validées sont conservées dans une documentation locale versionnée. Elles ne sont pas supprimées à la fin d'une conversation.

### 7.3 Données métier

Léon ne suppose pas connaître les données propres à l'utilisateur. Une lecture métier autorisée n'est effectuée que si la demande l'exige et si un mécanisme de lecture existe. Les calculs ou vérifications métier doivent s'appuyer sur les résultats fiables fournis par BATORYA.

Les données lues peuvent être utilisées dans le contexte de la conversation active lorsque c'est nécessaire, mais ne constituent pas une mémoire personnelle persistante de Léon. Aucun cache métier indépendant entre conversations n'est prévu pour V1. Une donnée susceptible d'avoir changé doit être vérifiée à nouveau avant d'être présentée comme actuelle.

## 8. Critères d'acceptation fonctionnels

La conception et les tests devront vérifier que :

- ouvrir le panneau ne déclenche pas de génération ;
- fermer le panneau n'annule pas la génération et ne supprime pas la conversation ;
- la saisie et l'envoi sont bloqués pendant une génération ;
- l'utilisateur peut annuler une génération et envoyer ensuite un nouveau message ;
- une réponse partielle annulée reste visible, marquée « Réponse interrompue » et utilisable comme contexte incomplet ;
- une erreur technique est signalée, la réponse partielle est conservée et aucune relance automatique n'a lieu ;
- le dépassement du délai maximal interrompt la génération et conserve la réponse partielle ;
- la mémoire expire après 30 minutes selon la règle définie ;
- l'expiration efface l'historique affiché et le contexte, sans avertissement ;
- toute interaction vérifie l'expiration avant d'utiliser le contexte ;
- « Nouvelle conversation » demande confirmation uniquement si des messages existent ;
- confirmer une nouvelle conversation annule toute génération en cours et efface l'ancien contexte ;
- fermer BATORYA interrompt immédiatement la génération et aucune conversation n'est restaurée au redémarrage ;
- les connaissances documentées et les données métier restent séparées de la mémoire conversationnelle ;
- aucune écriture métier n'est possible depuis Léon.

## 9. Évolutions futures — hors périmètre V1

**Confidentialité des traces résiduelles du système d'exploitation**

Pour une version ultérieure, étudier les moyens de limiter les traces résiduelles des conversations pouvant résulter du fonctionnement du système d'exploitation ou des outils de diagnostic, notamment :

- fichier d'échange ou pagination mémoire ;
- dumps mémoire et rapports de plantage ;
- journaux techniques et diagnostics ;
- autres mécanismes de stockage temporaire susceptibles de contenir des fragments de conversation.

Cette étude devra définir les protections réalistes, leurs limites, leurs effets sur les performances et les moyens de les tester. Elle ne doit pas conduire à promettre un effacement physique absolu. Ce sujet est explicitement hors périmètre de Léon V1.

## 10. Points techniques restant à spécifier

Les règles fonctionnelles ci-dessus sont retenues. Les éléments suivants restent à définir avant implémentation :

1. le délai maximal de génération, mesuré sur le matériel cible ;
2. le mécanisme d'arrêt effectif du moteur local et de libération des ressources ;
3. le mécanisme technique de temporisation, de nettoyage automatique et de vérification avant interaction ;
4. le format et le budget de la mémoire conversationnelle en RAM ;
5. les services de lecture métier autorisés, au fur et à mesure de l'implémentation de BATORYA ;
6. les tests de non-restauration après fermeture et de non-réutilisation d'un contexte expiré.

Aucun code, schéma SQLite ou règle métier n'est modifié par cette spécification.
