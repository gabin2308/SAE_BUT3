# User stories – Recommandation de vols (v2)

Groupe « Les Orques tactiques » – SAÉ BUT3 5.Real.01

## 1. Périmètre

Application web découplée (Flask, React, PostgreSQL + pgvector, Docker) qui **recommande des vols uniquement**. Le train, le bus, les hébergements, la météo et la fidélité sont retirés. Deux approches de recommandation sont comparées dans un tableau de bord (A : filtrage par contenu à base d'embeddings des vols ; B : filtrage collaboratif par contenu).

## 2. Parcours

1. **Page d'accroche** publique : logo, slogan, description, boutons « Créer un compte » et « Se connecter ».
2. **Inscription** : nom, prénom, email, mot de passe, consentements, politique d'utilisation. Un email de confirmation active le compte.
3. **Connexion** : email et mot de passe, avec « mot de passe oublié ».
4. **Première connexion** : page de préférences facultatives (passable), puis accueil.
5. **Accueil** : message de bienvenue, description de l'application et module de recherche (pays, ville, aéroport, budget et autres informations).
6. **Résultats** (autre page) : vols classés par l'algorithme, favoris, modification des paramètres, filtres et tri.
7. **Fiche d'un vol** : informations complètes et lien de réservation.

## 3. Hypothèses retenues (à valider avec le groupe)

- **Consentements** : une case obligatoire (politique d'utilisation et confidentialité, non pré-cochée) et deux facultatives (personnalisation, localisation).
- **Préférences** : aéroport de départ habituel, budget approximatif, escales acceptées, compagnies préférées, bagage.
- **Recherche** : départ, destination, dates, aller simple ou aller-retour, passagers, budget max.
- **Activation** : lien valable 24 h avec renvoi possible ; lien de mot de passe oublié valable 1 h.
- **Données** : catalogue de 10 à 15 routes (prix Travelpayouts), simulation marquée « simulée » pour les autres.

## 4. Lots

| Lot | Objectif | Contenu |
| --- | --- | --- |
| **Lot 1** | Cœur | Compte, connexion, accueil, recherche, résultats, approche A, temps de réponse, ingestion, Docker et Git |
| **Lot 2** | Personnalisation | Préférences, localisation, favoris, avis, historique, fiche d'un vol, Mon compte, mise à jour du profil, utilisateurs simulés |
| **Lot 3** | Comparaison et finitions | Approche B, mélange, dashboard, qualité, compte de démonstration, identité du projet |

## 5. User stories

### Epic 1 : Compte et accès

| ID | Lot | Story |
| --- | --- | --- |
| **US1** | 1 | En tant que visiteur, je crée un compte (nom, prénom, email, mot de passe) en acceptant la politique d'utilisation et en choisissant mes consentements (personnalisation, localisation), afin d'accéder à l'application. |
| **US2** | 1 | En tant que nouvel inscrit, je reçois un email de confirmation avec un lien d'activation (valable 24 h, renvoi possible), afin de valider mon adresse et d'activer mon compte. |
| **US3** | 1 | En tant qu'utilisateur, je me connecte avec mon email et mon mot de passe, et je me déconnecte, afin de protéger mon compte. |
| **US4** | 1 | En tant qu'utilisateur, je réinitialise mon mot de passe grâce à un lien reçu par email si je l'ai oublié. |

### Epic 2 : Préférences

| ID | Lot | Story |
| --- | --- | --- |
| **US5** | 2 | En tant que nouvel utilisateur, à ma première connexion, je renseigne si je le souhaite mes préférences (aéroport habituel, budget, escales, compagnies, bagage) ou je passe cette étape, afin d'obtenir des recommandations adaptées dès le départ. |
| **US6** | 2 | En tant qu'utilisateur, je modifie mes préférences à tout moment depuis « Mon compte ». |

### Epic 3 : Page d'accroche, accueil et recherche

| ID | Lot | Story |
| --- | --- | --- |
| **US7** | 1 | En tant que visiteur, je découvre une page d'accroche (logo, slogan, description) avec des boutons d'inscription et de connexion, afin de comprendre l'intérêt de l'application. |
| **US8** | 1 | En tant qu'utilisateur connecté, j'arrive sur un accueil avec un message de bienvenue et la description de l'application, afin de me repérer. |
| **US9** | 1 | En tant qu'utilisateur, je lance une recherche de vols depuis l'accueil (pays, ville, aéroport, dates, passagers, budget et autres informations utiles), afin de trouver un vol. |
| **US10** | 2 | En tant qu'utilisateur, je peux utiliser ma position, après une explication et mon accord au clic, pour que l'application me propose l'aéroport le plus proche, que je confirme ou change. |
| **US11** | 2 | En tant qu'utilisateur, si je refuse la position ou si elle échoue, je continue avec la saisie manuelle sans être bloqué. |

### Epic 4 : Résultats

| ID | Lot | Story |
| --- | --- | --- |
| **US12** | 1 | En tant qu'utilisateur, je vois sur une page dédiée les vols classés selon mon profil, afin de savoir lesquels choisir. |
| **US13** | 1 | En tant qu'utilisateur, j'obtiens mes résultats rapidement, sans attente excessive. |
| **US14** | 1 | En tant qu'utilisateur, je modifie mes paramètres de recherche depuis la page de résultats, sans repasser par l'accueil, et la liste se met à jour. |
| **US15** | 1 | En tant qu'utilisateur, je filtre et trie les résultats (prix, durée, escales, compagnie), afin d'affiner ma recherche. |
| **US16** | 2 | En tant qu'utilisateur, j'ajoute un vol en favori et je le retrouve plus tard, afin de le comparer. |
| **US17** | 2 | En tant qu'utilisateur, j'indique si un résultat est pertinent ou non, afin d'améliorer mes recommandations. |
| **US18** | 2 | En tant qu'utilisateur, je vois en une phrase simple pourquoi un vol m'est proposé (par exemple « moins cher que la moyenne »), afin de comprendre le classement. |
| **US19** | 2 | En tant qu'utilisateur, je consulte l'historique de mes recherches et je les relance. |

### Epic 5 : Fiche d'un vol

| ID | Lot | Story |
| --- | --- | --- |
| **US20** | 2 | En tant qu'utilisateur, je clique sur un résultat pour accéder à ses informations complètes (horaires, compagnie, escales, bagage, prix), afin de décider. |
| **US21** | 2 | En tant qu'utilisateur, je clique sur « Réserver » pour ouvrir le site de la compagnie ou de l'agence dans un nouvel onglet ; ce clic est enregistré comme un signal fort pour mon profil. |

### Epic 6 : Personnalisation

| ID | Lot | Story |
| --- | --- | --- |
| **US22** | 2 | En tant qu'utilisateur, mes actions (recherches, vues, favoris, avis, clics sur « Réserver ») sont enregistrées afin d'alimenter mon profil. |
| **US23** | 2 | En tant qu'utilisateur, à ma connexion suivante, mon profil est mis à jour à partir de mes actions et mes recommandations s'adaptent. |

### Epic 7 : Mon compte

| ID | Lot | Story |
| --- | --- | --- |
| **US24** | 2 | En tant qu'utilisateur, depuis « Mon compte », je consulte et modifie mon profil, je retire mes consentements, et je retrouve mes favoris et mon historique. |
| **US25** | 2 | En tant qu'utilisateur, je supprime mon lieu de départ et mon compte, ce qui supprime mes données, afin de garder la maîtrise de mes données. |

### Epic 8 : Comparaison et performance (évaluateur)

| ID | Lot | Story |
| --- | --- | --- |
| **US26** | 1 | En tant qu'évaluateur, je vois le temps de réponse de chaque recommandation afin de mesurer la performance. |
| **US27** | 3 | En tant qu'utilisateur, je vois aussi des vols appréciés par des utilisateurs au profil proche du mien. |
| **US28** | 3 | En tant qu'utilisateur, mes résultats combinent les deux approches, la part de B augmentant avec le nombre de mes interactions. |
| **US29** | 3 | En tant qu'évaluateur, je vois côte à côte les résultats des approches A et B, avec les vols communs et divergents mis en évidence. |
| **US30** | 3 | En tant qu'évaluateur, je vois un tableau de bord comparant A et B (temps min, max et moyen, complexité, ressources, énergie estimée). |
| **US31** | 3 | En tant qu'évaluateur, je vois la qualité de chaque approche sur l'historique (precision@k et NDCG, dernière offre choisie masquée). |
| **US32** | 3 | En tant qu'évaluateur, je me connecte avec un compte de démonstration dont l'historique est déjà rempli. |

### Epic 9 : Données et socle technique

| ID | Lot | Story |
| --- | --- | --- |
| **US33** | 1 | En tant qu'équipe, nous lançons un script d'ingestion par source (pays, aéroports, prix de vols) afin de remplir la base. |
| **US34** | 1 | En tant qu'équipe, nous conservons les JSON bruts et rejouons l'ingestion sans doublons. |
| **US35** | 1 | En tant qu'équipe, nous générons les données manquantes (vols hors catalogue) et les marquons « simulée ». |
| **US36** | 2 | En tant qu'équipe, nous générons des utilisateurs et interactions fictifs à partir de profils types, afin d'évaluer les approches et de gérer le démarrage à froid. |
| **US37** | 1 | En tant qu'équipe, nous lançons tout le projet avec « docker compose up ». |
| **US38** | 1 | En tant qu'équipe, nous versionnons avec Git et une numérotation sémantique (v0.1.0). |
| **US39** | 3 | En tant qu'équipe, nous donnons au projet un nom, un logo, un slogan et une licence open source justifiée. |

## 6. Sources de données conservées

- **Pays** : data.gouv.fr (liste des pays).
- **Aéroports** : OurAirports ou données de référence Travelpayouts (coordonnées, codes IATA).
- **Prix de vols** : Travelpayouts (cache, certaines routes seulement).
- **Simulation** : module `simulation/` pour les routes absentes, marquées « simulée ».

Retirés : SNCF, Navitia, GTFS BlaBlaBus, OpenStreetMap, Open-Météo.

## 7. Approches de recommandation

Le projet compare deux approches, A (embeddings sur le contenu des vols) et B (filtrage collaboratif, avec l'algorithme kNN proposé). La formulation exacte de B est à confirmer avec le groupe.

### Approche A : embeddings sur le contenu des vols

- Chaque vol devient un vecteur (embedding) construit à partir de ses caractéristiques : prix, durée, escales, compagnie, bagage, ramenés entre 0 et 1.
- Le profil de l'utilisateur est aussi un vecteur : la moyenne des vols qu'il a vus, mis en favori ou réservés, ou ses préférences s'il est nouveau.
- Les vols sont classés par similarité cosinus avec ce profil, calculée dans pgvector.
- **Force** : fonctionne dès la première connexion, rapide, explicable. **Limite** : ne propose que des vols qui ressemblent à ce que l'utilisateur connaît déjà.

### Approche B : filtrage collaboratif

- Elle ignore les caractéristiques des vols et s'appuie sur le comportement des utilisateurs : vues, favoris, avis, clics sur « Réserver ».
- Principe : les vols appréciés par des utilisateurs qui ont les mêmes goûts que moi me seront probablement utiles.
- **Force** : fait découvrir des vols inattendus. **Limite** : inefficace pour un nouvel utilisateur et demande beaucoup d'utilisateurs, d'où les utilisateurs simulés (US36).

### Algorithme kNN pour l'approche B

kNN (*k nearest neighbors*) signifie les k plus proches voisins : on cherche les k éléments les plus proches de celui qui nous intéresse, puis on s'appuie sur eux. Version proposée, vol-vol (*item-based*) :

1. Construire la matrice utilisateurs × vols : chaque interaction reçoit un poids (un clic sur « Réserver » compte plus qu'une simple vue).
2. Calculer la similarité cosinus entre chaque paire de vols : deux vols sont proches s'ils plaisent aux mêmes utilisateurs.
3. Pour chaque vol apprécié par l'utilisateur, retenir ses k voisins les plus proches.
4. Additionner les similarités, retirer les vols déjà vus, puis classer.

Le choix de k se règle sur l'historique avec precision@k et NDCG : un k petit (3 à 5) est précis mais sensible au bruit, un k grand (20 à 50) est plus stable mais moins personnalisé. La variante utilisateur-utilisateur (*user-based*) cherche à la place les k utilisateurs les plus proches et recommande ce qu'ils ont aimé.

### Comparaison

| Critère | A : embeddings (contenu) | B : kNN (collaboratif) |
| --- | --- | --- |
| Données utilisées | Caractéristiques des vols | Interactions des utilisateurs |
| Nouvel utilisateur | Fonctionne dès le départ | Peu efficace |
| Nouveau vol | Fonctionne dès le départ | Sans interaction, peu recommandé |
| Explication | « Ressemble à vos vols » | « Aimé par des utilisateurs proches » |
| Calcul | Similarité vectorielle (pgvector) | Matrice de similarités entre vols |

### Mélange

Score final = (1 − alpha) × A + alpha × B, où alpha augmente avec le nombre d'interactions de l'utilisateur : A domine au début, B prend le relais avec l'historique.
