# Charte graphique BATORYA V6

**Version : 0.5**  
**Statut : En construction — référence de conception**  
**Périmètre : BATORYA Essentiel V6**  
**Prototype de référence :** `docs/conception/references-ui/prototype_claude_ui-uxV3.html`

> Document de référence graphique de BATORYA Essentiel V6. Cette version aligne la charte sur le prototype UI/UX V3 actuellement retenu. Elle distingue les choix visibles dans le prototype, les règles communes à appliquer et les éléments qui restent à concevoir. Elle ne définit pas l'architecture fonctionnelle de l'application.

---

## 1. Objet et statut de la charte

Cette charte décrit le langage visuel à utiliser pour concevoir puis implémenter l'interface de BATORYA Essentiel V6, en modes clair et sombre.

Elle vise à :
- maintenir une identité visuelle cohérente dans l'application ;
- fournir des références graphiques réutilisables plutôt que des styles propres à chaque écran ;
- distinguer les décisions observables dans le prototype des règles encore à valider ;
- permettre une déclinaison claire, sombre et, à terme, automatique.

La charte ne spécifie ni les fonctions métier, ni les règles de navigation, ni l'architecture du Shell. La présence d'un élément dans un prototype ne suffit pas à figer son comportement fonctionnel.

### 1.1. Versionnement

- **0.x** : construction et validation progressive de la charte ;
- **1.0** : première référence graphique considérée comme stable pour l'implémentation V6 ;
- après 1.0 : toute évolution est tracée dans l'historique.

Toute modification de fond doit entraîner une mise à jour de l'indice et de l'historique. Les versions antérieures restent consultables dans Git.

### 1.2. Hiérarchie des références graphiques

Pour la conception graphique :
1. la présente charte décrit les règles communes validées ;
2. le prototype UI/UX V3 illustre leur application et sert de référence visuelle actuelle ;
3. les autres fichiers de référence servent à l'inspiration ou à la comparaison, sauf validation explicite ultérieure.

Si une valeur précise du prototype diffère d'une ancienne règle de cette charte, les anciennes valeurs décrivant la palette, la typographie ou les formes ne doivent pas être conservées par simple inertie : la version 0.5 prend pour base le prototype V3.

---

## 2. Direction artistique

### 2.1. Intention

L'interface BATORYA Essentiel doit être :
- professionnelle, contemporaine et lisible ;
- éditoriale et structurée, sans apparence de logiciel de gestion traditionnel ;
- sobre, avec une hiérarchie nette et des détails graphiques maîtrisés ;
- dense lorsque le travail le demande, sans sacrifier la lecture ;
- cohérente en clair comme en sombre.

Le langage visuel du prototype V3 repose sur l'association **papier, encre et outremer** : fonds neutres légèrement chauds, texte très contrasté, bleu outremer pour l'action et les états actifs, filets fins et typographie à caractère éditorial.

### 2.2. Principes de composition

- Préférer la hiérarchie typographique, l'alignement, les espacements et les filets à une multiplication des cartes et des encadrements.
- Utiliser les surfaces élevées ou les ombres uniquement lorsqu'elles apportent une séparation utile.
- Réserver la couleur d'accent aux actions, aux états actifs et aux informations qui la justifient.
- Éviter les dégradés décoratifs, halos lumineux, effets vitrés et accents orange hérités des anciens prototypes lorsqu'ils ne figurent pas dans la direction V3.
- Ne pas généraliser les choix d'un écran à toute l'application sans vérifier leur cohérence avec le système graphique.

### 2.3. Densité et rythme

Le prototype expose une hauteur de ligne de référence de **48 px** pour la densité confort et une variante compacte de **38 px**. Ce sont des valeurs de prototype, pas encore une décision exhaustive pour tous les composants.

La densité doit rester adaptée à la tâche : les tableaux et listes peuvent être plus compacts que les formulaires ou les écrans d'accueil. Le comportement responsive et le choix définitif de densité restent à valider.

---

## 3. Typographie

Le prototype V3 utilise trois familles complémentaires.

| Usage | Famille déclarée dans le prototype | Rôle |
|---|---|---|
| Titres éditoriaux, grands titres et certains libellés de marque | **Source Serif 4** | Donner du caractère et établir la hiérarchie |
| Interface, formulaires, navigation et texte courant | **Instrument Sans** | Lisibilité et neutralité fonctionnelle |
| Données, nombres, repères et informations tabulaires | **DM Mono** | Alignement visuel et distinction des données |

### 3.1. Hiérarchie typographique

- Les titres principaux utilisent la sérif avec une graisse mesurée ; l'italique peut servir d'accent éditorial ponctuel.
- Le texte courant utilise la sans-sérif.
- Les données chiffrées et repères courts peuvent utiliser la monospace, notamment avec des chiffres tabulaires.
- Les petites étiquettes en capitales et à espacement augmenté sont réservées aux métadonnées ou aux catégories, pas au texte courant.
- La hiérarchie doit d'abord reposer sur la taille, la graisse, l'espacement et le contraste, et non sur la multiplication des couleurs.

Les tailles typographiques complètes ne sont pas encore figées. Elles seront documentées avec les composants correspondants.

### 3.2. Disponibilité des polices

Le HTML de référence charge ces familles depuis Google Fonts. **L'application finale ne doit pas dépendre d'un accès réseau pour afficher sa typographie**, compte tenu de son fonctionnement local et hors ligne.

Avant l'implémentation, vérifier les licences et la possibilité de distribuer les fichiers de police avec l'application. Si ces familles ne peuvent pas être embarquées, définir une solution de repli cohérente. Cette charte ne prescrit pas de téléchargement distant à l'exécution.

Piles de repli déclarées par le prototype :
- sérif : `ui-serif, Georgia, "Times New Roman", serif` ;
- sans-sérif : `ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif` ;
- monospace : `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`.

---

## 4. Palette — mode clair

Les valeurs ci-dessous sont reprises des tokens CSS du prototype V3. Elles constituent la base graphique de cette version de la charte.

| Token / rôle | Valeur | Usage |
|---|---|---|
| Papier / fond principal (`--paper`) | `#F6F6F2` | Fond général clair, légèrement chaud |
| Surface (`--sheet`) | `#FFFFFF` | Surface de contenu |
| Voile secondaire (`--wash`) | `#EEEEE8` | Survols et surfaces secondaires |
| Voile renforcé (`--wash-2`) | `#E7E7E0` | Niveau secondaire plus marqué |
| Filet principal (`--rule`) | `#D6D6CC` | Séparateurs et bordures |
| Filet discret (`--rule-2`) | `#E6E6DE` | Séparateurs peu présents |
| Encre principale (`--ink`) | `#14161B` | Texte principal et éléments forts |
| Encre secondaire (`--ink-2`) | `#43464E` | Texte secondaire |
| Encre tertiaire (`--ink-3`) | `#6C6F77` | Métadonnées et indications discrètes |
| Texte sur encre (`--on-ink`) | `#F6F6F2` | Contraste sur surface encre |
| Bleu outremer (`--blue`) | `#2B38D0` | Action principale, focus et état actif |
| Bleu outremer renforcé (`--blue-2`) | `#1E29A8` | Survol de l'action bleue |
| Voile bleu (`--blue-wash`) | `#E6E8FA` | Sélection ou état bleu en arrière-plan |
| Texte sur bleu (`--blue-ink`) | `#FFFFFF` | Texte sur accent bleu |
| Rouge fonctionnel (`--red`) | `#C23B24` | Erreur ou action destructive |
| Fond rouge (`--red-wash`) | `#F7E1DB` | Fond d'état d'erreur |
| Vert fonctionnel (`--green`) | `#287047` | Confirmation positive |
| Fond vert (`--green-wash`) | `#DDEDE2` | Fond d'état positif |
| Ambre fonctionnel (`--amber`) | `#9E6B0B` | Avertissement |
| Fond ambre (`--amber-wash`) | `#F4E9CF` | Fond d'avertissement |
| Surface documentaire (`--doc`) | `#FFFFFF` | Surface de document |
| Encre documentaire (`--doc-ink`) | `#14161B` | Texte sur document |
| Filet documentaire (`--doc-rule`) | `#E3E3DA` | Séparateurs sur document |

### 4.1. Ombres et voile

Ombre déclarée par le prototype :

```css
0 1px 1px rgba(20,22,27,.04),
0 12px 32px -12px rgba(20,22,27,.18)
```

Voile d'arrière-plan déclaré : `rgba(20,22,27,.28)`.

Ces valeurs sont des références à appliquer avec discernement, pas une autorisation à ombrer chaque élément. La composition privilégie les filets et le contraste entre surfaces.

---

## 5. Palette — mode sombre

Le mode sombre est une déclinaison de la même identité. Il ne doit pas être obtenu par inversion mécanique des couleurs du mode clair.

| Token / rôle | Valeur | Usage |
|---|---|---|
| Papier / fond principal (`--paper`) | `#0E1016` | Fond général sombre |
| Surface (`--sheet`) | `#151821` | Surface principale |
| Voile secondaire (`--wash`) | `#191D27` | Surface secondaire et survol |
| Voile renforcé (`--wash-2`) | `#212634` | Niveau secondaire plus marqué |
| Filet principal (`--rule`) | `#2A2F3D` | Bordures et séparateurs |
| Filet discret (`--rule-2`) | `#1F2330` | Séparateurs discrets |
| Encre principale (`--ink`) | `#E8E6DF` | Texte principal |
| Encre secondaire (`--ink-2`) | `#B8B7B1` | Texte secondaire |
| Encre tertiaire (`--ink-3`) | `#8A8D96` | Métadonnées |
| Texte sur encre (`--on-ink`) | `#0E1016` | Texte sur élément clair |
| Bleu outremer (`--blue`) | `#8F9CFF` | Accent et état actif |
| Bleu outremer renforcé (`--blue-2`) | `#AAB4FF` | Survol ou accent renforcé |
| Voile bleu (`--blue-wash`) | `rgba(143,156,255,.12)` | Sélection bleue discrète |
| Texte sur bleu (`--blue-ink`) | `#0B0E1E` | Texte sur accent bleu |
| Rouge fonctionnel (`--red`) | `#F0897A` | Erreur ou action destructive |
| Fond rouge (`--red-wash`) | `rgba(240,137,122,.13)` | Fond d'erreur |
| Vert fonctionnel (`--green`) | `#7DC79A` | Confirmation positive |
| Fond vert (`--green-wash`) | `rgba(125,199,154,.12)` | Fond d'état positif |
| Ambre fonctionnel (`--amber`) | `#E0B460` | Avertissement |
| Fond ambre (`--amber-wash`) | `rgba(224,180,96,.12)` | Fond d'avertissement |
| Surface documentaire (`--doc`) | `#EAE8E1` | Surface de document |
| Encre documentaire (`--doc-ink`) | `#14161B` | Texte sur document |
| Filet documentaire (`--doc-rule`) | `#CFCDC4` | Séparateurs sur document |

Ombre déclarée par le prototype :

```css
0 1px 1px rgba(0,0,0,.3),
0 16px 40px -12px rgba(0,0,0,.6)
```

Voile d'arrière-plan déclaré : `rgba(0,0,0,.5)`.

Les couleurs fonctionnelles du thème sombre ne doivent pas être utilisées comme décoration. Vérifier le contraste des textes et états lors de la réalisation des composants.

---

## 6. Surfaces, filets et profondeur

### 6.1. Fonds et surfaces

- Le fond clair est `#F6F6F2`, pas le gris bleuté des anciens prototypes.
- Les surfaces de contenu sont principalement blanches en thème clair et bleu-noir très sombre en thème sombre.
- Les surfaces secondaires utilisent les tokens `--wash` et `--wash-2`.
- Les documents peuvent utiliser les tokens dédiés `--doc`, `--doc-ink` et `--doc-rule`.

### 6.2. Filets

Les filets fins constituent un élément structurant du style V3. Ils séparent les zones et établissent la hiérarchie sans enfermer systématiquement le contenu dans des cartes.

Le prototype utilise notamment une séparation double pour certains titres de page. Ce motif peut être réutilisé lorsqu'il correspond à la hiérarchie du contenu, sans devenir un ornement obligatoire.

### 6.3. Ombres

Les ombres sont secondaires. Elles servent à distinguer une surface réellement élevée ou un voile, pas à donner artificiellement du relief à chaque section. Les contours lourds, les ombres décoratives et les effets vitrés hérités des anciens prototypes ne sont pas la référence de cette direction artistique.

---

## 7. Formes et dimensions de référence

| Élément | Valeur observée dans le prototype V3 |
|---|---:|
| Rayon commun (`--r`) | 3 px |
| Hauteur de ligne confort (`--row`) | 48 px |
| Hauteur de ligne compacte | 38 px |
| Largeur de marge contextuelle (`--marg`) | 240 px |
| Hauteur de topbar du prototype | 64 px |

Ces valeurs décrivent la composition actuelle du prototype, pas une spécification fonctionnelle de la navigation ni une obligation d'appliquer ces dimensions à chaque écran. Les rayons et dimensions définitifs des composants restent à confirmer pendant la conception du système UI.

Le rayon de 3 px donne une géométrie plutôt nette. Les boutons, champs et surfaces ne doivent donc pas revenir automatiquement aux grandes formes arrondies des anciens prototypes.

---

## 8. Composants graphiques

### 8.1. Boutons

Le prototype V3 distingue notamment :
- **primaire** : fond bleu outremer, bordure de même couleur et texte contrasté ;
- **secondaire** : fond transparent et bordure encre ;
- **discret** : bordure neutre, avec fond secondaire au survol ;
- **destructif** : texte rouge et état de survol associé au rouge fonctionnel.

Les boutons sont compacts, rectilignes et utilisent le rayon commun du prototype. Le survol et l'activation doivent rester discrets. L'orange n'est plus l'accent principal de cette direction graphique.

### 8.2. Champs et formulaires

Le prototype métier utilise des champs à fond transparent et à soulignement fin plutôt que des champs systématiquement placés dans des capsules ou des rectangles fortement arrondis.

Références observées :
- hauteur de champ de 38 px ;
- libellé en petites capitales, avec espacement augmenté ;
- filet neutre au repos ;
- filet bleu au focus ;
- filet rouge pour l'état d'erreur ;
- fond transparent lorsque le contexte le permet.

Ces choix doivent être adaptés au contexte. Le prototype de connexion peut utiliser une présentation de formulaire différente si elle reste cohérente avec la palette, la typographie et la géométrie globale.

### 8.3. Navigation, onglets et commandes

Les contrôles de navigation du prototype sont sobres, sans fond permanent pour chaque entrée. L'état actif est principalement indiqué par le contraste, la couleur du repère et un filet bleu.

Cette observation décrit le prototype ; elle ne fige pas l'organisation définitive des chapitres, modules, onglets ou commandes de l'application.

### 8.4. Listes et tableaux

- Privilégier les alignements réguliers et les séparateurs fins.
- Aligner à droite les montants et nombres lorsque la lecture comparative l'exige.
- Utiliser les chiffres tabulaires pour stabiliser les colonnes numériques.
- Réserver les couleurs fonctionnelles aux états qui le nécessitent.
- Ne pas encadrer chaque ligne dans une carte.

Les composants complets de tableaux et de listes restent à définir au fil de la conception des écrans.

### 8.5. Focus et accessibilité

Le prototype définit un focus visible de 2 px avec décalage de 2 px, porté par la couleur d'accent du thème. Le focus clavier doit rester visible et ne peut pas être supprimé au seul motif esthétique.

Les états ne doivent pas dépendre exclusivement de la couleur : le contexte, le libellé, l'icône ou la forme doivent également permettre de comprendre l'état lorsque cela est nécessaire.

---

## 9. Iconographie et logo

### 9.1. Marque provisoire du prototype

Le prototype V3 utilise un signe provisoire composé d'un **B sérif dans un cadre fin**, accompagné d'un petit carré bleu décalé. Le mot-symbole « Batorya » est composé en sérif et la mention « Essentiel V6 » en monospace.

Ce signe est une solution de prototypage et **n'est pas le logo définitif**. Il ne doit pas être présenté comme une identité de marque finalisée.

### 9.2. Chantier du logo définitif

La création d'un nouveau logo BATORYA adapté à cette direction graphique est un chantier distinct, à mener ultérieurement. Cette version de la charte ne préjuge pas de sa forme définitive.

Lorsqu'il sera conçu, le logo devra être évalué sur sa lisibilité, sa reconnaissance, son utilisation à petite taille, son rendu en clair et en sombre et sa capacité à être utilisé sans effets décoratifs obligatoires. La charte sera alors mise à jour avec les variantes et règles d'utilisation validées.

### 9.3. Icônes

Le prototype utilise des icônes SVG simples, au trait, avec une épaisseur de trait homogène. La famille définitive d'icônes et les règles de taille restent à confirmer.

Ne pas mélanger des icônes pleines, des pictogrammes très détaillés et des styles de trait différents sans raison fonctionnelle.

---

## 10. Animation et mouvement

L'animation doit aider à comprendre un changement d'état, pas ralentir l'usage.

### 10.1. Référence de mouvement

Le prototype déclare la courbe suivante :

```css
cubic-bezier(.22,.7,.2,1)
```

Il utilise notamment des transitions courtes d'environ 150 ms pour certains états et une apparition de contenu d'environ 300 ms. Ces valeurs constituent des références observées, pas des durées obligatoires pour tous les composants.

### 10.2. Principes

- Utiliser des transitions courtes pour les survols, focus et changements d'état simples.
- Réserver les animations plus longues aux changements de vue qui gagnent réellement en compréhension.
- Ne pas animer les données ou les contrôles sans bénéfice pour l'utilisateur.
- Respecter la préférence de réduction des animations du système. Lorsque la réduction est demandée, supprimer ou réduire fortement les mouvements non essentiels sans perdre l'information portée par l'état.

---

## 11. Écran de connexion et premier accès

Le point d'entrée doit être cohérent avec le langage graphique du prototype V3 : palette papier/encre/outremer, typographie éditoriale, filets fins et formes maîtrisées.

Le prototype présente les deux parcours **« Se connecter »** et **« Créer mon espace »** dans une même interface, avec les champs d'identification et de sécurité adaptés au parcours sélectionné. Il s'agit de la référence de conception actuelle pour cette entrée.

Les règles suivantes s'appliquent :
- conserver la cohérence avec la palette et la typographie générales ;
- distinguer clairement connexion et création d'espace ;
- rendre les libellés, erreurs, focus et actions compréhensibles ;
- adapter la mise en page aux largeurs d'écran réellement prises en charge ;
- ne pas considérer les interactions de démonstration du HTML comme une authentification fonctionnelle.

Le prototype peut contenir des transitions de démonstration ou un écran de démarrage. Leur présence ne fige ni la séquence technique de démarrage, ni le comportement de sécurité, ni les opérations métier. Ces aspects doivent être spécifiés séparément avant implémentation.

Les anciens prototypes Login + Splash basés sur le bleu glacier, les halos et l'orange ne sont plus la référence graphique courante. Ils peuvent rester dans le dépôt comme historique, mais ne doivent pas servir de base à de nouveaux écrans sans validation explicite.

---

## 12. Gestion des thèmes

Le système graphique doit permettre :
- **Automatique** : suivre la préférence clair/sombre du système d'exploitation ;
- **Clair** : forcer le thème clair ;
- **Sombre** : forcer le thème sombre.

La préférence système peut être détectée à l'aide de `prefers-color-scheme`. La valeur par défaut recommandée reste **Automatique**, sous réserve de validation lors de la conception des préférences utilisateur.

Le choix explicite de l'utilisateur devra être mémorisé localement. La charte décrit le rendu des thèmes ; elle ne fixe pas le mécanisme technique de stockage.

---

## 13. Tokens et centralisation

Les couleurs et valeurs communes doivent être centralisées dans des tokens de thème plutôt que redéfinies arbitrairement dans chaque composant.

Les noms présents dans le prototype comprennent notamment :
- `--paper`, `--sheet`, `--wash`, `--wash-2` ;
- `--rule`, `--rule-2` ;
- `--ink`, `--ink-2`, `--ink-3`, `--on-ink` ;
- `--blue`, `--blue-2`, `--blue-wash`, `--blue-ink` ;
- `--red`, `--red-wash`, `--green`, `--green-wash`, `--amber`, `--amber-wash` ;
- `--doc`, `--doc-ink`, `--doc-rule`, `--shadow`, `--scrim`.

Ces noms décrivent les tokens du prototype. Ils peuvent être renommés pendant l'intégration, à condition de conserver une correspondance explicite entre tokens et usages.

> Un choix graphique partagé doit pouvoir être ajusté à un endroit central et se répercuter de façon cohérente dans l'interface.

La centralisation des tokens est une règle de conception. Elle ne prescrit pas à elle seule l'organisation des fichiers ou l'architecture technique de l'application.

---

## 14. Éléments restant à définir

Cette version 0.5 aligne la charte sur le prototype V3, mais ne constitue pas encore un système de design complet.

Restent notamment à confirmer ou concevoir :
- les tailles typographiques et l'échelle d'espacement complètes ;
- les dimensions et rayons définitifs des composants ;
- les règles responsive complètes ;
- les composants de navigation définitifs ;
- les variantes complètes de boutons, champs et sélecteurs ;
- les tableaux, badges, alertes, modales, menus et infobulles ;
- les états vides, de chargement, de succès, d'erreur et d'avertissement ;
- les règles d'accessibilité et de contraste à vérifier sur l'ensemble des composants ;
- la distribution locale et les licences des familles typographiques ;
- la famille d'icônes définitive ;
- le nouveau logo BATORYA ;
- les variantes et règles d'usage du logo une fois celui-ci validé.

Les éléments ci-dessus ne doivent pas être inventés simplement pour compléter la charte. Ils seront ajoutés lorsqu'ils auront été conçus et validés.

---

## 15. Règle de cohérence

Toute nouvelle interface BATORYA Essentiel V6 doit s'appuyer sur cette charte et sur le prototype V3 comme référence visuelle actuelle.

Lorsqu'un besoin nécessite une règle graphique qui n'est pas couverte :
1. concevoir le composant dans son contexte d'usage ;
2. définir les états nécessaires et leur rendu en clair et en sombre ;
3. vérifier la lisibilité, l'accessibilité et la cohérence avec les tokens ;
4. compléter la charte ;
5. incrémenter la version et renseigner l'historique.

La charte reste un document vivant. Elle ne doit pas devenir un catalogue de règles métier ou de décisions d'architecture.

---

## 16. Historique des versions

| Version | Date | Nature de l'évolution |
|---|---|---|
| 0.1 | 2026-10-05 | Création de la charte et formalisation des premiers principes graphiques des prototypes Login + Splash. |
| 0.2 | 2026-10-05 | Version intermédiaire ; détail des changements non consigné dans l'historique source. |
| 0.3 | 2026-10-09 | Documentation des comportements visuels des prototypes Login + Splash alors retenus. |
| 0.4 | 2026-10-09 | Mise à jour des palettes et tokens des anciens prototypes Login + Splash. |
| 0.5 | 2026-10-12 | Refonte de la référence graphique pour l'aligner sur le prototype UI/UX V3 : palette papier/encre/outremer, typographie Source Serif 4 / Instrument Sans / DM Mono, filets fins, géométrie compacte, mode sombre et statut provisoire du signe de marque. Correction des références obsolètes et de l'incohérence de version. |

---

## 17. Références

### Prototype de référence actuel

`docs/conception/references-ui/prototype_claude_ui-uxV3.html`

### Références antérieures

Les anciens fichiers Login + Splash présents dans `docs/conception/references-ui/` restent des références historiques. Ils ne priment pas sur le prototype V3 pour les nouveaux travaux graphiques.

Les autres références visuelles du dossier peuvent servir à l'inspiration et à la comparaison, mais ne remplacent pas les règles de la présente charte.

---

**Statut actuel :** charte en construction.  
**Version courante : 0.5**
