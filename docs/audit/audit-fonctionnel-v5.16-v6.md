Audit fonctionnel V5.16 → BATORYA V6

Statut : Audit clôturé
Version de référence : BATORYA V5.16
Cible : BATORYA V6 – Essentiel

⸻

1. Objet du document

Cet audit a pour objectif de vérifier que la conception fonctionnelle de BATORYA V6 a bien pris en compte les règles métier, comportements et fonctionnalités utiles présents dans BATORYA V5.16.

L’objectif n’est pas de déterminer quelles parties du code V5.16 peuvent être réutilisées.

BATORYA V6 fait l’objet d’une reconstruction complète, avec une architecture, un modèle de données et une séparation des responsabilités nouveaux.

Le V5.16 constitue donc une source de référence fonctionnelle, tandis que le CDC V6 constitue la référence pour l’implémentation future.

⸻

2. Méthode d’audit

L’analyse a été réalisée en confrontant :

* les fonctionnalités réellement présentes dans V5.16 ;
* les règles métier observées dans le fonctionnement des modules ;
* les décisions fonctionnelles prises lors de la conception du V6 ;
* le CDC V6 consolidé.

Pour chaque domaine, les fonctionnalités ont été classées selon quatre catégories :

* Conservé : comportement ou règle métier repris dans V6 ;
* Évolué : comportement V5 conservé mais modifié ou renforcé ;
* Abandonné : fonctionnalité volontairement supprimée du périmètre V6 ;
* Remplacé : fonctionnalité conservée dans son objectif mais entièrement reconstruite selon une nouvelle logique.

⸻

3. Synthèse par domaine

3.1 Catalogue de prestations

V5.16

Le catalogue contient les prestations prédéfinies utilisées pour constituer les devis.

L’audit du catalogue réel a permis d’identifier 205 prestations prédéfinies.

Certaines incohérences existent dans le modèle V5 :

* coexistence de categorie et corps ;
* unités non uniformisées ;
* prix stockés sous forme numérique flottante ;
* gestion des garanties intégrée directement aux prestations ;
* suppression physique des prestations.

La prestation ELE-008 – prise RJ45 Cat6 a été identifiée comme une prestation spécifique et non comme une catégorie « Cat6 ».

Décision V6

Remplacé.

Le catalogue V6 sera reconstruit proprement à partir du catalogue réel V5.16.

Les données utiles sont conservées, mais le modèle sera normalisé.

La prestation Cat6 identifiée comme ELE-008 est supprimée du catalogue V6.

Les prix seront traités avec une représentation décimale exacte.

Les prestations utilisées historiquement ne devront pas être détruites de manière à casser les documents existants.

Les garanties par prestation sont conservées comme information métier, mais leurs échéances ne sont pas considérées comme une vérité juridique.

⸻

3.2 Clients

V5.16

Le client possède notamment :

* code ;
* nom ;
* prénom ;
* adresse ;
* téléphone ;
* email ;
* notes.

Les documents conservent également une copie des informations client utilisées lors de leur création.

Le code client est indépendant de la numérotation des documents.

Décision V6

Conservé et renforcé.

Les clients deviennent de véritables entités référencées par identifiant.

Les documents conservent leur propre snapshot des informations nécessaires à leur historique.

Le rattachement fonctionnel repose sur clientId et non sur le nom du client.

Les codes clients restent distincts de la convention de numérotation des documents :

CLI-001

⸻

4. Devis

V5.16

Le devis permet notamment :

* sélection d’un client ;
* saisie de prestations du catalogue ;
* lignes libres ;
* quantités ;
* unités ;
* prix ;
* remises ;
* type de prestation ;
* acompte ;
* validité ;
* objet ;
* adresse de chantier ;
* notes ;
* rappel ;
* statut ;
* création d’un BC lors de l’acceptation.

Les lignes de devis conservent les informations de la prestation au moment de leur utilisation.

Le V5 utilise notamment la numérotation :

DEV-00001

Décision V6

Évolué et reconstruit.

Le principe fonctionnel est conservé, mais le modèle de données est entièrement reconstruit.

Les lignes deviennent des snapshots structurés.

Le devis possède un clientId en plus de son snapshot client.

Les statuts sont normalisés.

La suppression est soumise aux règles d’historique.

La numérotation devient :

DEV-00001-26

L’acceptation d’un devis entraîne la création structurée et idempotente d’un véritable BC.

La date d’acceptation est conservée comme événement métier.

⸻

5. Bons de commande

V5.16

Le BC V5.16 est principalement un prolongement du devis accepté.

Il n’est pas véritablement modélisé comme une entité indépendante.

La numérotation historique est :

BC-0001-26

Le statut dépend largement de la facturation.

Il n’existe pas de véritable mécanisme de cancellation structuré.

Décision V6

Évolution structurelle majeure.

Le BC devient une véritable entité centrale du dossier.

Il possède son propre cycle de vie.

Le vocabulaire fonctionnel reste BC, mais sa numérotation devient :

BCD-00001-26

Le cycle normal est :

En cours → Terminé

Le BC devient Terminé uniquement lorsque la facture de solde est entièrement réglée.

Le BC peut être annulé uniquement lorsque les conditions définies dans le CDC sont respectées.

Une Situation émise bloque la cancellation directe du BC.

Un montant encaissé bloque également la cancellation directe.

Un BC annulé est conservé dans l’historique.

⸻

6. Facturation

V5.16

Le système distingue :

* acompte ;
* situation ;
* solde ;
* avoir ;
* ancien type technique complete.

Les factures sont liées aux devis.

Les situations utilisent une logique de progression cumulée permettant de déterminer le montant supplémentaire à facturer.

Les factures possèdent un montant restant à payer et un statut.

Décision V6

Reconstruit entièrement.

Le principe métier est conservé, mais le modèle V5 n’est pas repris.

Le type complete disparaît.

La facturation V6 repose sur :

* Acompte ;
* Situation ;
* Solde ;
* Avoir.

Une facture finale est toujours une facture de solde, y compris lorsqu’aucun acompte ou aucune situation n’a précédé.

La logique des situations et de la progression est conservée.

Les documents utilisent la convention :

* FAC-00001-26
* ACP-00001-26
* AVO-00001-26

⸻

7. Règlements

V5.16

Le règlement d’une facture repose essentiellement sur :

* une date de paiement ;
* un mode de paiement ;
* un statut ;
* un reste à payer.

Une facture est essentiellement marquée comme réglée en une seule opération.

Décision V6

Évolution fonctionnelle majeure.

Le règlement devient une entité indépendante.

Une facture peut recevoir plusieurs règlements.

Chaque règlement contient notamment :

* date ;
* montant ;
* mode de paiement.

Modes prévus :

* espèces ;
* chèque ;
* virement ;
* carte ;
* autre.

Le reste à payer est calculé automatiquement.

Les états sont dérivés des règlements :

* En attente ;
* Partiellement réglée ;
* Réglée ;
* En retard ;
* Annulée.

« En retard » est transversal et peut donc concerner une facture partiellement réglée.

Aucune réconciliation bancaire automatique n’est prévue.

⸻

8. Avoirs

V5.16

L’avoir est conservé comme document historique et référence une facture d’origine.

Le V5 permet notamment des avoirs partiels.

Décision V6

Conservé et renforcé.

L’avoir devient un document autonome, avec son propre numéro :

AVO-00001-26

Une facture déjà payée ne doit pas être simplement supprimée ou annulée.

L’avoir constitue le mécanisme approprié pour les corrections financières concernées.

L’impact de l’avoir ou d’un remboursement sur le calcul URSSAF est déterminé par la version du référentiel réglementaire applicable à la période.

⸻

9. Dépenses

V5.16

Les dépenses peuvent être :

* globales ;
* associées à un BC ;
* associées à un fournisseur ;
* accompagnées d’une pièce ou d’une note.

Le V5 possède également une logique de paiement des dépenses.

Décision V6

Conservé pour l’analyse, simplifié fonctionnellement.

Les dépenses restent indépendantes ou rattachées à un BC.

Le fournisseur est référencé par identifiant et non par simple nom texte.

La gestion du paiement des dépenses est volontairement supprimée du V6 :

* pas de statut payé/non payé ;
* pas de règlement fournisseur ;
* pas de gestion d’échéance fournisseur ;
* pas de workflow de paiement.

La dépense reste une donnée d’analyse comptable et de marge.

Numérotation :

DEP-00001-26

⸻

10. Fournisseurs

V5.16

Le fournisseur constitue un carnet indépendant utilisé notamment pour les dépenses.

Décision V6

Conservé et restructuré.

Le fournisseur devient une entité indépendante.

Les relations avec les dépenses reposent sur un identifiant stable.

Les fournisseurs historiques ne doivent pas être supprimés lorsqu’ils sont nécessaires à l’historique.

Numérotation :

FOU-001

⸻

11. Planning

V5.16

Le planning permet notamment de représenter les interventions liées aux devis/BC.

La logique existante prend en compte les jours ouvrés et les jours fériés français.

Décision V6

Évolué.

Le planning V6 couvre deux familles :

1. événements liés aux BC ;
2. événements généraux de l’entreprise.

Les événements généraux peuvent notamment concerner :

* congés ;
* indisponibilités ;
* rendez-vous ;
* autres événements internes.

Le planning ne modifie pas le statut du BC.

Les règles de calcul des jours ouvrés et jours fériés pertinentes sont conservées.

⸻

12. PV de réception

V5.16

Le PV est un objet distinct du devis/BC.

Décision V6

Évolué et restructuré.

Le PV est facultatif.

Il peut constater :

* une réception sans réserve ;
* une réception avec réserves.

Le PV initial devient immuable après émission.

La levée de réserves fait l’objet d’un second PV autonome.

La numérotation est :

PVR-00001-26

Les PV de levée de réserves reprennent le numéro du PV d’origine avec suffixe :

PVR-00001-26-01

puis :

PVR-00001-26-02

La levée des réserves ne modifie pas la date de début du suivi interne des garanties.

Les PV sont stockés sous :

2026/PV/

⸻

13. Garanties

V5.16

Le V5 associe les garanties aux prestations et possède une logique de suivi basée sur la réception/PV.

Décision V6

Règle métier volontairement modifiée.

Le suivi interne BATORYA commence lorsque le BC atteint 100 % facturé, indépendamment :

* du PV ;
* de la réception ;
* des réserves ;
* de la levée des réserves ;
* du paiement final.

Les garanties suivies sont :

* parfait achèvement : 1 an ;
* biennale : 2 ans ;
* décennale : 10 ans.

Ce calcul constitue un suivi interne indicatif BATORYA et ne constitue pas une détermination juridique du point de départ des garanties.

Le caractère indicatif doit être explicitement visible dans l’interface.

⸻

14. Notes

V5.16

Le système possède des notes rattachées au contexte du dossier.

Décision V6

Conservé et amélioré.

Le BC peut comporter plusieurs notes internes :

* contenu ;
* date de création ;
* date de modification.

Les notes peuvent être modifiées ou supprimées.

Elles ne constituent pas un système de tâches ou de workflow.

⸻

15. URSSAF

V5.16

Le V5 contient déjà des éléments de calcul et de suivi URSSAF.

Décision V6

Entièrement restructuré et déjà validé dans le CDC.

Le périmètre est strictement celui de BATORYA Essentiel :

* micro-entrepreneur ;
* BTP ;
* prestations de services ;
* franchise en base de TVA.

Les calculs reposent sur le CA encaissé et non sur les factures émises.

Les paiements partiels sont pris en compte à hauteur du montant réellement encaissé.

Les périodes déclaratives sont conservées historiquement.

Les règles réglementaires sont versionnées.

Le référentiel réglementaire peut être mis à jour via les Services BATORYA.

Les anciennes versions restent disponibles pour permettre la reproduction des calculs historiques.

Aucune déclaration officielle automatique n’est effectuée.

⸻

16. Comptabilité et analyse

V5.16

Le système fournit différentes informations :

* chiffre d’affaires ;
* facturation ;
* encaissements ;
* dépenses ;
* marge ;
* devis acceptés restant à facturer.

Décision V6

Conservé comme couche d’analyse.

BATORYA ne devient pas un logiciel comptable complet.

Les analyses doivent exploiter les données des modules métier existants.

Trois niveaux de prévision sont distingués :

1. CA encaissé réel ;
2. CA engagé ;
3. CA prévisionnel.

Un BC annulé ne fait plus partie du CA engagé.

⸻

17. Documents et PDF

V5.16

Les PDF sont classés selon :

* année ;
* type de document ;
* statut.

Les structures existantes constituent une référence fonctionnelle satisfaisante.

Décision V6

Conservé fonctionnellement, reconstruit techniquement.

Structure V6 :

2026/
├── Devis/
│   ├── En_attente/
│   ├── Accepte/
│   ├── Refuse/
│   └── Annule/
│
├── Factures/
│   ├── Acomptes/
│   ├── Situations/
│   ├── Soldes/
│   └── Avoirs/
│
└── PV/

Les BC ne possèdent pas de dossier PDF propre puisqu’ils constituent un dossier métier et non un document PDF indépendant.

⸻

18. Sauvegardes et restauration

V5.16

Le V5 sauvegarde notamment :

* devis ;
* factures ;
* clients ;
* fournisseurs ;
* dépenses ;
* PV ;
* notes ;
* planning ;
* historique ;
* paramètres ;
* compteurs.

Une ancienne structure de sauvegarde V2 a également été identifiée.

Décision V6

Conservé et fortement sécurisé.

Le V6 possède :

* sauvegarde manuelle ;
* sauvegarde automatique ;
* sauvegarde à la fermeture ;
* restauration validée ;
* sauvegarde de sécurité avant restauration ;
* restauration atomique ;
* contrôle de cohérence.

Les anciennes sauvegardes V2 doivent pouvoir être migrées vers le V6.

La migration doit normaliser les anciennes structures sans perte silencieuse de données et produire un rapport de migration.

⸻

19. Paramètres

V5.16

Les paramètres regroupent notamment les informations de l’entreprise et plusieurs préférences.

Décision V6

Restructuré.

Les paramètres V6 distinguent notamment :

* identité professionnelle ;
* informations administratives ;
* coordonnées ;
* informations bancaires facultatives ;
* paramètres commerciaux ;
* sauvegardes ;
* Gmail ;
* Services BATORYA ;
* profil utilisateur ;
* dossier de travail.

Les paramètres URSSAF disposent de leur propre espace.

Les numéros de documents ne sont pas configurables manuellement dans les paramètres.

⸻

20. Email

V5.16

Le système permet notamment l’envoi manuel de documents par email.

Décision V6

Conservé.

Gmail reste le fournisseur prévu.

Les emails sont toujours déclenchés explicitement par l’utilisateur.

Aucun email automatique n’est prévu.

Cela concerne notamment :

* devis ;
* factures ;
* autres documents ;
* rapports d’erreur.

⸻

21. Licence et mises à jour

V5.16

Le V5 possède son propre mécanisme de licence et d’association à la machine.

Décision V6

Remplacé.

Le système devient :

Services BATORYA — Licence & mises à jour

Il assure :

* validation de licence ;
* association de machine ;
* mises à jour logicielles ;
* distribution du référentiel réglementaire.

La vérification de licence intervient trimestriellement.

Une période de grâce de 15 jours permet de reconnecter la machine.

Après expiration de cette période :

* consultation autorisée ;
* exports autorisés ;
* création/modification/suppression bloquées ;
* facturation bloquée.

Les données métier ne sont jamais transmises au service distant.

⸻

22. Google Drive

V5.16

Une intégration Google Drive est présente dans le V5.

Décision V6

Abandonné.

Google Drive ne fait pas partie du périmètre initial de BATORYA V6.

⸻

23. Historique

V5.16

Le système conserve différents événements liés aux opérations effectuées.

Décision V6

Conservé et restructuré.

L’historique doit être exploitable sans dépendre de la structure interne des anciens modules.

Il doit notamment permettre de conserver les événements significatifs affectant les objets métier.

Les suppressions destructives sont remplacées autant que nécessaire par des mécanismes d’archivage, d’annulation ou de conservation historique.

⸻

24. Convention de numérotation V6

L’audit a également permis de constater que les conventions V5 sont hétérogènes.

La convention V6 est désormais uniformisée :

TRI-00001-26

avec :

* trigramme métier ;
* compteur sur 5 chiffres ;
* année sur 2 chiffres.

Correspondances validées :

Objet	Numéro
Devis	DEV-00001-26
Bon de commande	BCD-00001-26
Facture	FAC-00001-26
Acompte	ACP-00001-26
Avoir	AVO-00001-26
PV réception	PVR-00001-26
Dépense	DEP-00001-26

Les clients et fournisseurs conservent leurs propres codes :

* CLI-001
* FOU-001

Ils ne suivent pas la convention des documents.

⸻

25. Fonctionnalités volontairement abandonnées

L’audit confirme que les éléments suivants ne doivent pas être reproduits dans V6 :

* architecture V5 basée sur localStorage ;
* logique métier directement dans les modules UI ;
* ancien modèle de facture complete ;
* paiement unique des factures ;
* gestion du paiement des dépenses ;
* Google Drive ;
* ancienne logique de garantie basée sur le PV ;
* suppression physique non contrôlée des données historiques ;
* numérotations hétérogènes V5 ;
* gestion métier basée sur des noms texte lorsque des identifiants sont nécessaires ;
* stockage monétaire reposant sur des flottants ;
* dépendance à un backend pour les données métier.

Ces abandons sont des décisions de conception V6, et non des omissions de l’audit.

⸻

26. Points particuliers confirmés par l’audit

Plusieurs règles importantes ont été confirmées ou découvertes au cours de l’analyse :

* les Situations utilisent une logique de progression cumulée ;
* le règlement doit devenir une entité indépendante ;
* le BC doit devenir une véritable entité métier ;
* un BC annulé ne doit plus alimenter le CA engagé ;
* une Situation émise empêche la cancellation directe du BC ;
* un paiement encaissé empêche également cette cancellation ;
* une facture payée ne doit pas être supprimée pour corriger son montant ;
* l’avoir constitue le mécanisme approprié lorsque nécessaire ;
* le suivi interne des garanties démarre à 100 % facturé ;
* le PV et la garantie sont deux mécanismes distincts ;
* les documents doivent conserver les informations historiques nécessaires ;
* le fournisseur doit être référencé par identifiant ;
* les règles URSSAF dépendent d’un référentiel réglementaire versionné ;
* le dossier de travail est indépendant de la base SQLite ;
* le changement de dossier de travail ne déplace pas automatiquement les anciennes données ;
* une sauvegarde est proposée avant changement de dossier ;
* les anciennes sauvegardes V2 constituent une source de migration et non le modèle de données V6.

⸻

27. Conclusion de l’audit

L’audit fonctionnel de BATORYA V5.16 est considéré comme terminé.

Aucune fonctionnalité métier majeure de V5.16 n’a été identifiée comme absente du périmètre fonctionnel V6.

Les différences entre V5.16 et V6 correspondent principalement à :

* des reconstructions techniques ;
* des normalisations de données ;
* des renforcements de règles ;
* des corrections de comportements fragiles ;
* des évolutions fonctionnelles volontairement décidées ;
* des fonctionnalités explicitement sorties du périmètre.

Le code V5.16 ne constitue donc pas une base technique à refactoriser.

Il constitue une source de vérification fonctionnelle et de migration historique.

À compter de la clôture de cet audit :

Le CDC BATORYA V6 constitue la référence fonctionnelle.

La conception technique V6 peut être engagée indépendamment de l’architecture V5.16.

La prochaine étape est donc la définition du modèle de données SQLite, des entités métier, des relations et des services applicatifs, puis leur traduction dans l’architecture Tauri 2 + React + TypeScript.
