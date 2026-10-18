# Charte graphique BATORYA Essentiel V6

**Version : 0.6**  
**Statut : En construction — référence graphique de travail**  
**Périmètre : BATORYA Essentiel V6**  
**Référence visuelle :** `docs/conception/references-ui/Prototype_mistral_ui-ux-modern.html` — prototype Mistral « Azur »

> Cette charte définit exclusivement les principes graphiques de BATORYA Essentiel V6 : direction artistique, palette, typographie, surfaces, formes, composants visuels, iconographie et mouvement. Elle ne spécifie ni les parcours, ni la navigation fonctionnelle, ni les règles métier, ni l'architecture technique. Ces sujets relèvent de documents distincts.

---

## 1. Objet, périmètre et statut

Cette charte formalise le langage visuel à préserver lors de la conception puis de l'implémentation de BATORYA Essentiel V6, en thème clair et sombre.

Elle vise à :
- donner à BATORYA une identité visuelle cohérente, reconnaissable et professionnelle ;
- centraliser les choix graphiques partagés ;
- maintenir une lecture confortable pendant de longues sessions ;
- éviter la dérive vers des styles différents selon les écrans ou les composants ;
- distinguer les principes graphiques retenus des valeurs encore à éprouver.

Elle ne constitue pas un système de design exhaustif. Les valeurs relevées dans le prototype sont des références de départ ; elles pourront être ajustées après vérification sur des écrans représentatifs, sans perdre la direction artistique validée.

### 1.1. Versionnement

- **0.x** : construction et validation progressive de la charte ;
- **1.0** : première référence graphique stabilisée pour l'implémentation V6 ;
- après 1.0 : toute évolution de fond est tracée dans l'historique.

### 1.2. Hiérarchie des références graphiques

Pour les choix graphiques :
1. la présente charte définit les principes communs formalisés ;
2. le prototype Mistral « Azur » illustre la direction visuelle actuelle et constitue la référence de travail ;
3. les autres prototypes servent à l'historique, à l'inspiration ou à la comparaison, sauf validation explicite ultérieure.

La charte doit être mise à jour si une décision graphique est validée et que le prototype ou les règles écrites ne la reflètent plus.

---

## 2. Direction artistique

### 2.1. Intention

BATORYA Essentiel doit présenter une interface :
- moderne, élégante et professionnelle ;
- distinctive sans extravagance ;
- confortable à regarder et à utiliser sur la durée ;
- claire, hiérarchisée et visuellement apaisée ;
- suffisamment vivante pour ne pas ressembler à un logiciel de gestion traditionnel ;
- cohérente en thème clair comme en thème sombre.

La direction « Azur » associe **verre dépoli, profondeur douce et nuances bleu glacier**. Les surfaces translucides, les ombres diffuses et les accents bleus créent une impression de légèreté et de profondeur. Ces effets doivent rester maîtrisés : ils servent la composition et la séparation visuelle, jamais l'ornement gratuit.

### 2.2. Principes de composition

- Privilégier une hiérarchie nette, des espacements cohérents et des contrastes lisibles.
- Utiliser les surfaces translucides et le flou pour créer une profondeur subtile.
- Employer les ombres avec mesure, en distinguant les surfaces qui semblent flotter du fond.
- Utiliser le bleu comme couleur d'accent principale, sans colorer inutilement toutes les zones.
- Préserver des fonds calmes pour que les contenus et les données restent prioritaires.
- Éviter les dégradés saturés, les halos trop intenses, les contours lourds et les accumulations d'effets.
- Ne pas appliquer systématiquement le verre dépoli à chaque composant : le contraste entre surfaces vitrées et surfaces opaques participe à la hiérarchie.
- Éviter les combinaisons chromatiques ou les animations agressives susceptibles de fatiguer visuellement.

### 2.3. Identité graphique

La personnalité visuelle repose sur l'association de :
- fonds gris bleuté et atmosphères bleu glacier ;
- surfaces blanches ou bleu nuit semi-transparentes ;
- reflets et bordures clairs très subtils ;
- ombres étagées et diffuses ;
- géométrie arrondie mais maîtrisée ;
- typographie contemporaine, différenciée selon l'usage ;
- bleu vif pour les actions et les repères importants.

L'identité ne dépend pas d'un effet isolé. Elle doit rester reconnaissable même lorsque le flou ou les ombres sont absents, notamment pour préserver la lisibilité et les performances.

---

## 3. Typographie

Le prototype « Azur » déclare trois familles complémentaires.

| Usage | Famille | Rôle |
|---|---|---|
| Titres, grands chiffres éditoriaux et éléments de marque provisoires | **Outfit** | Donner une personnalité moderne et des titres expressifs sans excès |
| Interface, navigation, libellés, formulaires et texte courant | **Manrope** | Assurer une lecture fluide et une tonalité contemporaine |
| Données chiffrées, références, codes et informations tabulaires | **JetBrains Mono** | Distinguer les données techniques et stabiliser leur alignement |

### 3.1. Hiérarchie typographique

- Outfit est la famille de titre ; elle doit rester lisible et ne pas être utilisée systématiquement pour les longs paragraphes.
- Manrope constitue la base de lecture de l'interface.
- JetBrains Mono est réservée aux données et repères pour lesquels une largeur régulière apporte un bénéfice.
- Les graisses doivent être utilisées pour établir une hiérarchie claire, sans multiplier les niveaux.
- Les capitales espacées conviennent aux petites catégories et métadonnées ; elles ne doivent pas devenir le style du texte courant.
- Les montants et nombres comparables doivent privilégier les chiffres tabulaires lorsque cela améliore leur alignement.
- La typographie doit conserver un contraste suffisant entre titres, texte secondaire et métadonnées.

Le prototype utilise une taille de texte de base proche de **14,5 px** avec un interlignage de **1,55**. Ces valeurs sont indicatives et devront être testées à l'échelle réelle de l'application, notamment sur les longues sessions et les écrans denses.

### 3.2. Distribution locale des polices

Le prototype charge les familles depuis Google Fonts. L'application finale étant conçue pour fonctionner localement et hors ligne, **l'affichage ne doit pas dépendre d'un accès réseau pour charger les polices**.

Avant l'implémentation :
- vérifier les licences et les conditions de distribution ;
- privilégier l'intégration locale des fichiers de police si elle est compatible avec les licences ;
- définir des piles de repli cohérentes.

Piles de repli observées :
- Outfit : `"Segoe UI", ui-sans-serif, system-ui, sans-serif` ;
- Manrope : `"Segoe UI", ui-sans-serif, system-ui, -apple-system, sans-serif` ;
- JetBrains Mono : `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`.

---

## 4. Palette — thème clair

Les valeurs ci-dessous sont reprises des tokens CSS du prototype Mistral « Azur ». Les couleurs transparentes sont intentionnelles : leur rendu dépend de la surface située derrière elles.

| Token / rôle | Valeur | Usage graphique |
|---|---|---|
| Fond principal (`--paper`) | `#F2F5F9` | Fond général gris bleuté très clair |
| Surface (`--sheet`) | `rgba(255,255,255,.62)` | Surface claire semi-transparente |
| Voile secondaire (`--wash`) | `rgba(47,109,235,.08)` | Fond secondaire et survol discret |
| Voile renforcé (`--wash-2`) | `rgba(47,109,235,.15)` | Accent de fond un peu plus visible |
| Filet principal (`--rule`) | `rgba(30,64,120,.16)` | Bordures et séparateurs |
| Filet discret (`--rule-2`) | `rgba(30,64,120,.10)` | Séparateurs peu présents |
| Encre principale (`--ink`) | `#1B2A41` | Texte principal bleu marine |
| Encre secondaire (`--ink-2`) | `#4A5A74` | Texte secondaire |
| Encre tertiaire (`--ink-3`) | `#7E8DA3` | Métadonnées et indications discrètes |
| Texte sur encre (`--on-ink`) | `#FFFFFF` | Texte contrasté sur une surface sombre |
| Bleu principal (`--acc`) | `#2F6BEB` | Accent, actions et repères importants |
| Bleu clair (`--acc-2`) | `#5B9BF5` | Nuance secondaire et dégradés d'accent |
| Voile bleu (`--acc-wash`) | `rgba(47,107,235,.13)` | Sélection et accent en arrière-plan |
| Texte sur accent (`--acc-ink`) | `#FFFFFF` | Texte sur accent bleu |
| Rouge fonctionnel (`--red`) | `#DE4D62` | Erreur ou état négatif |
| Fond rouge (`--red-wash`) | `rgba(222,77,98,.12)` | Fond d'état négatif |
| Vert fonctionnel (`--green`) | `#0E9A76` | Confirmation positive |
| Fond vert (`--green-wash`) | `rgba(14,154,118,.13)` | Fond d'état positif |
| Ambre fonctionnel (`--amber`) | `#C5851F` | Avertissement |
| Fond ambre (`--amber-wash`) | `rgba(197,133,31,.14)` | Fond d'avertissement |
| Surface documentaire (`--doc`) | `#FFFFFF` | Support documentaire clair |
| Encre documentaire (`--doc-ink`) | `#1B2A41` | Texte documentaire |
| Filet documentaire (`--doc-rule`) | `#E2E8F1` | Séparateurs documentaires |

### 4.1. Atmosphère bleu glacier

Le prototype déclare plusieurs halos radiaux diffus, positionnés autour de la surface principale, dans des nuances de bleu, de cyan et de bleu lavande. Ils composent une atmosphère légère plutôt qu'un dégradé uniforme.

Principes d'usage :
- garder les halos peu saturés et très diffus ;
- éviter qu'ils nuisent au contraste du texte ou aux couleurs d'état ;
- conserver un fond lisible lorsque les effets de fond ne sont pas disponibles ;
- ne pas transformer chaque carte ou panneau en dégradé décoratif.

### 4.2. Ombres et transparence

Ombre principale observée :

```css
0 1px 2px rgba(27,42,65,.06),
0 14px 36px -14px rgba(27,42,65,.22)
```

Ombre flottante observée :

```css
0 10px 26px -10px rgba(27,42,65,.18),
0 28px 64px -28px rgba(37,107,220,.30)
```

Surface vitrée observée : `rgba(255,255,255,.60)`.  
Bordure claire de surface vitrée : `rgba(255,255,255,.70)`.

Ces valeurs constituent une référence visuelle, pas une obligation de les appliquer à chaque élément.

---

## 5. Palette — thème sombre

Le thème sombre conserve l'identité bleu glacier, mais utilise des fonds bleu nuit, des surfaces translucides profondes et des accents plus lumineux. Il ne doit pas être produit par inversion mécanique du thème clair.

| Token / rôle | Valeur | Usage graphique |
|---|---|---|
| Fond principal (`--paper`) | `#0C1422` | Fond bleu nuit |
| Surface (`--sheet`) | `rgba(20,32,54,.62)` | Surface sombre semi-transparente |
| Voile secondaire (`--wash`) | `rgba(140,180,255,.09)` | Surface secondaire |
| Voile renforcé (`--wash-2`) | `rgba(140,180,255,.15)` | Accent de fond plus visible |
| Filet principal (`--rule`) | `rgba(160,190,235,.20)` | Bordures et séparateurs |
| Filet discret (`--rule-2`) | `rgba(160,190,235,.11)` | Séparateurs discrets |
| Encre principale (`--ink`) | `#EAF0F9` | Texte principal clair |
| Encre secondaire (`--ink-2`) | `#B4C2D9` | Texte secondaire |
| Encre tertiaire (`--ink-3`) | `#8494AE` | Métadonnées |
| Texte sur encre (`--on-ink`) | `#0C1422` | Texte sur élément clair |
| Bleu principal (`--acc`) | `#6BA6FF` | Accent et états importants |
| Bleu clair (`--acc-2`) | `#93C2FF` | Accent secondaire |
| Voile bleu (`--acc-wash`) | `rgba(107,166,255,.16)` | Sélection et accent en arrière-plan |
| Texte sur accent (`--acc-ink`) | `#0A1830` | Texte sur accent bleu |
| Rouge fonctionnel (`--red`) | `#FF8296` | Erreur ou état négatif |
| Fond rouge (`--red-wash`) | `rgba(255,130,150,.14)` | Fond d'état négatif |
| Vert fonctionnel (`--green`) | `#4AD9A4` | Confirmation positive |
| Fond vert (`--green-wash`) | `rgba(74,217,164,.13)` | Fond d'état positif |
| Ambre fonctionnel (`--amber`) | `#EFC276` | Avertissement |
| Fond ambre (`--amber-wash`) | `rgba(239,194,118,.14)` | Fond d'avertissement |
| Surface documentaire (`--doc`) | `#F2F5FA` | Support documentaire clair |
| Encre documentaire (`--doc-ink`) | `#1B2A41` | Texte documentaire |
| Filet documentaire (`--doc-rule`) | `#D5DEEC` | Séparateurs documentaires |

Ombre principale observée :

```css
0 1px 1px rgba(0,0,0,.4),
0 18px 46px -12px rgba(0,0,0,.7)
```

Ombre flottante observée :

```css
0 10px 26px -10px rgba(0,0,0,.5),
0 30px 70px -28px rgba(0,0,0,.8)
```

Surface vitrée observée : `rgba(24,36,60,.58)`.  
Bordure claire subtile : `rgba(255,255,255,.12)`.

Les couleurs fonctionnelles doivent rester réservées aux états qui les justifient. Vérifier le contraste réel de chaque combinaison pendant la conception des composants.

---

## 6. Surfaces, verre dépoli et profondeur

### 6.1. Surfaces vitrées

Le verre dépoli est un marqueur important de la direction « Azur ». Le prototype combine :
- une couleur de surface translucide ;
- un flou d'arrière-plan ;
- une légère saturation des couleurs derrière la surface ;
- une bordure discrète ;
- une ombre douce lorsque la surface doit sembler élevée.

Référence CSS du prototype : `blur(16px) saturate(1.5)`.

Le rendu doit rester subtil. Une surface vitrée doit permettre de distinguer clairement le contenu qu'elle porte et ne doit pas créer de bruit visuel avec des fonds trop contrastés.

### 6.2. Hiérarchie des surfaces

Le système graphique peut combiner :
- le fond général avec son atmosphère bleu glacier ;
- des surfaces principales translucides ;
- des surfaces opaques lorsque le contraste ou la lisibilité le demande ;
- des surfaces secondaires légèrement teintées ;
- des surfaces flottantes avec une ombre plus marquée.

Toutes les surfaces ne doivent pas avoir le même niveau de transparence, de flou ou d'ombre. Leur différence doit contribuer à la hiérarchie visuelle.

### 6.3. Bordures et reflets

- Préférer des bordures fines et peu contrastées.
- Sur les surfaces vitrées claires, un reflet clair peut renforcer subtilement le contour.
- En thème sombre, privilégier une bordure claire très transparente.
- Éviter les contours épais ou très lumineux qui donneraient un aspect néon.
- Ne pas utiliser une bordure comme seul moyen de signaler un état important.

### 6.4. Compatibilité et sobriété

La lisibilité ne doit pas dépendre du flou d'arrière-plan. Lorsque cet effet n'est pas disponible ou doit être réduit, le fond et la bordure doivent suffire à distinguer la surface. Les ombres et les effets translucides doivent rester modérés pour ne pas nuire à la performance ou au confort visuel.

---

## 7. Formes, dimensions et espacement

| Élément | Valeur observée dans le prototype | Statut |
|---|---:|---|
| Rayon commun (`--r`) | 12 px | Référence visuelle à éprouver |
| Hauteur de ligne confortable (`--row`) | 48 px | Référence visuelle à éprouver |
| Hauteur de ligne compacte | 38 px | Variante visuelle du prototype |
| Largeur de marge de page (`--marg`) | 240 px | Dimension de composition du prototype |
| Hauteur de barre supérieure | 64 px | Dimension de composition du prototype |
| Flou de surface (`--blur`) | 16 px | Référence visuelle |
| Focus visible | 2 px, décalage de 2 px | Référence d'accessibilité visuelle |

Les valeurs de composition ci-dessus ne définissent pas la structure fonctionnelle de l'application. Elles servent à reproduire et à tester le langage visuel du prototype.

### 7.1. Géométrie

- Privilégier les rayons arrondis de manière cohérente.
- Réserver les très grands rayons aux composants qui s'y prêtent, comme certains boutons, filtres ou champs.
- Éviter le mélange de formes très anguleuses et de capsules sans logique visuelle.
- Maintenir des espacements réguliers entre les groupes d'éléments.
- Ne pas réduire les zones de lecture au seul motif de conserver davantage d'informations à l'écran.

---

## 8. Principes graphiques des composants

Cette section décrit uniquement leur apparence. Elle ne spécifie ni les actions, ni les états métier, ni le comportement de navigation.

### 8.1. Boutons

Le prototype emploie notamment :
- **primaire** : dégradé bleu, texte contrasté, sans bordure lourde et avec une ombre d'accent discrète ;
- **secondaire** : surface translucide, bordure légère et texte principal ;
- **discret** : fond transparent, qui se teinte légèrement au survol ;
- **destructif** : accent rouge réservé à l'action ou à l'état concerné.

Les boutons sont généralement arrondis en capsule. La hauteur standard observée est de 38 px, avec une variante compacte de 30 px. Ces mesures sont des références de prototype à vérifier sur les écrans réels.

### 8.2. Champs et formulaires

Le prototype utilise des champs légèrement teintés, arrondis, avec une bordure discrète au repos et un accent bleu au focus.

Références visuelles :
- fond secondaire légèrement teinté ;
- hauteur de champ proche de 40 px ;
- rayon de 12 px ;
- focus bleu avec un halo fin et discret ;
- fond et contour rouges pour l'erreur ;
- libellés en Manrope, généralement en petites capitales espacées.

Le style doit rester calme et suffisamment contrasté. Les fonds de champs ne doivent pas se confondre avec ceux des surfaces environnantes.

### 8.3. Sélecteurs, filtres et contrôles segmentés

- Les sélecteurs et filtres utilisent des formes arrondies et des fonds légers.
- L'élément actif se distingue par un fond bleu translucide et le texte d'accent.
- Les contrôles segmentés peuvent utiliser une surface intérieure claire ou translucide pour marquer la sélection.
- Les transitions de couleur et de fond restent courtes et discrètes.

### 8.4. Listes et tableaux

- Préférer des séparateurs fins plutôt que des bordures épaisses autour de chaque cellule.
- Utiliser les fonds de survol avec parcimonie.
- Maintenir une hiérarchie typographique claire entre en-têtes, contenu et métadonnées.
- Aligner les nombres et montants pour faciliter la comparaison.
- Utiliser JetBrains Mono et les chiffres tabulaires lorsque cela améliore la lecture.
- Réserver les couleurs fonctionnelles aux états qui le justifient.
- Conserver des lignes confortables et une variante compacte lorsque la densité de données le demande.

### 8.5. Cartes, panneaux et surfaces flottantes

Les cartes peuvent utiliser une surface vitrée, une bordure discrète et une ombre douce. L'intensité dépend de leur importance visuelle :
- surface de contenu ordinaire : contraste et ombre modérés ;
- panneau secondaire : relief faible ;
- élément flottant : ombre plus prononcée, sans halo excessif.

Toutes les sections ne doivent pas être enfermées dans des cartes. La composition doit alterner les surfaces et les espaces libres pour conserver une lecture aérée.

### 8.6. Badges et états colorés

Les états positifs, négatifs et d'avertissement utilisent respectivement les familles vert, rouge et ambre. Les fonds associés sont translucides et peu saturés.

- Ne pas utiliser ces couleurs à des fins purement décoratives.
- Ne pas communiquer une information uniquement par la couleur.
- Maintenir une lisibilité suffisante en thème clair et sombre.
- Éviter d'afficher simultanément trop de badges ou d'accents concurrents.

### 8.7. Focus et accessibilité visuelle

Le prototype utilise un focus visible de 2 px avec un décalage de 2 px, porté par la couleur d'accent. Le focus doit rester perceptible et ne peut pas être supprimé pour des raisons esthétiques.

Les contrastes, les tailles de texte et la visibilité des états devront être vérifiés sur les composants réels, en clair comme en sombre.

---

## 9. Iconographie et identité de marque

### 9.1. Icônes

Le prototype utilise des icônes SVG au trait, simples, avec une épaisseur homogène d'environ 1,5 px et une taille courante de 16 px.

Principes :
- privilégier des icônes lisibles et peu détaillées ;
- conserver une épaisseur de trait homogène ;
- utiliser la couleur du texte ou de l'accent selon la hiérarchie ;
- éviter de mélanger sans raison des icônes pleines, des pictogrammes détaillés et des styles de trait différents.

La famille d'icônes définitive et l'ensemble de ses tailles restent à confirmer lors de la conception du système UI.

### 9.2. Marque provisoire du prototype

Le prototype « Azur » présente un signe provisoire : un **B dans un carré arrondi bleu en dégradé**, accompagné du mot-symbole Batorya. Ce signe illustre le prototype ; il ne constitue pas le logo définitif.

### 9.3. Logo définitif

La recherche d'un signe distinctif BATORYA reste un chantier séparé. Cette charte ne préjuge pas de la forme finale du logo.

Une fois le logo choisi, ses variantes devront être documentées : symbole seul, mot-symbole, versions claire et sombre, tailles minimales et règles d'utilisation sur les fonds de l'interface.

---

## 10. Animation et mouvement — principes visuels

L'animation doit renforcer la perception de qualité sans distraire ni fatiguer.

Références déclarées dans le prototype :
- courbe : `cubic-bezier(.22,.7,.2,1)` ;
- transitions courtes d'environ 150 ms ;
- apparition de contenu autour de 300 ms.

Principes :
- utiliser des transitions discrètes pour les changements de couleur, de fond et de relief ;
- éviter les déplacements amples, les rebonds et les effets spectaculaires ;
- ne pas multiplier les animations simultanées ;
- respecter la préférence de réduction des animations ;
- conserver la compréhension visuelle lorsque les animations sont réduites ou absentes.

Cette section fixe une tonalité de mouvement, pas les comportements fonctionnels qui déclenchent les animations.

---

## 11. Présentation graphique de l'écran d'entrée

L'écran de connexion et de premier accès doit utiliser le même langage visuel que le reste de BATORYA Essentiel :
- fond gris bleuté et atmosphère légère ;
- surfaces vitrées ou panneaux translucides lorsque cela sert la composition ;
- typographie Outfit et Manrope ;
- accent bleu et ombres douces ;
- contrastes et états de focus lisibles.

Cette charte décrit uniquement l'apparence. Les parcours de connexion, la création d'espace, les règles de sécurité et les étapes de démarrage doivent être spécifiés séparément.

---

## 12. Thèmes clair et sombre

Les deux thèmes sont des expressions de la même identité graphique.

### Thème clair
- fond gris bleuté `#F2F5F9` ;
- surfaces blanches translucides ;
- texte bleu marine ;
- accent bleu vif et bleu ciel ;
- ombres diffuses et reflets clairs.

### Thème sombre
- fond bleu nuit `#0C1422` ;
- surfaces bleu nuit translucides ;
- texte clair bleuté ;
- accent bleu lumineux ;
- bordures claires discrètes et ombres plus profondes.

Les composants doivent conserver une hiérarchie comparable dans les deux thèmes. Le thème sombre ne doit ni éblouir par des accents trop lumineux ni rendre les surfaces indiscernables. Les couleurs et transparences devront être vérifiées sur les fonds réellement utilisés.

La manière dont le thème est choisi ou mémorisé ne relève pas de cette charte graphique.

---

## 13. Tokens et centralisation des styles

Les valeurs graphiques communes doivent être centralisées dans des tokens plutôt que redéfinies arbitrairement dans chaque composant.

Les tokens présents dans le prototype comprennent notamment :
- fonds et surfaces : `--paper`, `--sheet`, `--wash`, `--wash-2` ;
- bordures : `--rule`, `--rule-2` ;
- texte : `--ink`, `--ink-2`, `--ink-3`, `--on-ink` ;
- accents : `--acc`, `--acc-2`, `--acc-wash`, `--acc-ink` ;
- états : `--red`, `--red-wash`, `--green`, `--green-wash`, `--amber`, `--amber-wash` ;
- documents : `--doc`, `--doc-ink`, `--doc-rule` ;
- profondeur : `--shadow`, `--float`, `--glass`, `--edge`, `--scrim`, `--aur` ;
- géométrie et mouvement : `--r`, `--row`, `--blur`, `--ease`.

Les noms peuvent évoluer pendant l'intégration technique à condition de conserver une correspondance explicite entre les tokens et leurs usages graphiques.

La centralisation est un principe de cohérence visuelle ; cette charte ne prescrit pas l'organisation des fichiers CSS ou des composants.

---

## 14. Éléments graphiques restant à définir ou à vérifier

Cette version aligne la charte sur le prototype « Azur », mais ne constitue pas encore un système de design complet.

Restent notamment à éprouver ou à documenter :
- l'échelle typographique complète et les tailles minimales ;
- l'échelle d'espacement ;
- les rayons et dimensions définitifs des composants ;
- les variantes complètes des boutons, champs, sélecteurs et cartes ;
- les tableaux et listes à forte densité ;
- les badges, alertes, modales, menus et infobulles ;
- les états vides et les traitements graphiques de chargement ;
- les contrastes en clair et en sombre ;
- le comportement visuel sur les tailles de fenêtre prises en charge ;
- les polices embarquées et leurs licences ;
- la famille d'icônes définitive ;
- le logo BATORYA définitif.

Ces points ne doivent pas être inventés pour compléter artificiellement la charte. Ils seront ajoutés au fur et à mesure de leur conception et de leur validation.

---

## 15. Règle de cohérence graphique

Toute nouvelle interface BATORYA Essentiel V6 doit préserver la direction artistique « Azur » et respecter les tokens partagés.

Lorsqu'un besoin graphique n'est pas couvert :
1. concevoir son apparence dans le contexte visuel où il sera utilisé ;
2. définir ses variantes en thème clair et sombre ;
3. vérifier lisibilité, contraste, densité et cohérence avec les composants existants ;
4. centraliser les nouveaux tokens ou règles réutilisables ;
5. compléter la charte et incrémenter sa version.

Une évolution graphique peut être proposée à partir d'un prototype ou d'un besoin métier. Elle doit toutefois être explicitement validée avant de devenir une règle commune.

---

## 16. Historique des versions

| Version | Date | Nature de l'évolution |
|---|---|---|
| 0.1 | 2026-10-05 | Création de la charte et formalisation des premiers principes graphiques des prototypes Login + Splash. |
| 0.2 | 2026-10-05 | Version intermédiaire ; détail des changements non consigné dans l'historique source. |
| 0.3 | 2026-10-09 | Documentation des comportements visuels des prototypes Login + Splash alors retenus. |
| 0.4 | 2026-10-09 | Mise à jour des palettes et tokens des anciens prototypes Login + Splash. |
| 0.5 | 2026-10-12 | Alignement temporaire de la référence graphique sur le prototype Claude V3 : palette papier/encre/outremer et typographie Source Serif 4 / Instrument Sans / DM Mono. |
| 0.6 | 2026-10-18 | Nouvelle référence graphique de travail : alignement sur le prototype Mistral « Azur », palette bleu glacier, surfaces vitrées, ombres douces, formes arrondies et typographie Outfit / Manrope / JetBrains Mono. Clarification du périmètre : charte strictement graphique, sans règles de navigation, de comportement métier ou d'architecture. |

---

## 17. Référence visuelle

### Prototype de référence actuel

`docs/conception/references-ui/Prototype_mistral_ui-ux-modern.html`

Le prototype sert de référence visuelle de travail. Il ne constitue pas à lui seul une spécification fonctionnelle ou une architecture technique.

Les autres fichiers présents dans `docs/conception/references-ui/` restent consultables comme références historiques ou sources d'inspiration, mais ne priment pas sur la présente charte pour les nouveaux travaux graphiques.

---

**Statut actuel :** charte graphique en construction.  
**Version courante : 0.6**
