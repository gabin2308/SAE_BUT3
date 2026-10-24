# Fonctionnalités à développer, dans l'ordre

Projet de recommandation de vols : 8 étapes, du socle technique à la comparaison des approches. Les numéros US renvoient au document des user stories.

## Ordre de développement

| Étape | Fonctionnalité | Stories | Lot |
| --- | --- | --- | --- |
| **0. Socle** | Dépôt Git et numérotation sémantique | US38 | 1 |
|  | Docker compose (PostgreSQL + pgvector, Flask, React), schema.sql, .env.example | US37 | 1 |
| **1. Données** | Scripts d'ingestion (pays, aéroports, prix de vols Travelpayouts) | US33 | 1 |
|  | Conservation des JSON bruts et ingestion rejouable sans doublons | US34 | 1 |
|  | Module de simulation des vols hors catalogue | US35 | 1 |
| **2. Compte** | Inscription avec consentements | US1 | 1 |
|  | Email d'activation du compte | US2 | 1 |
|  | Connexion et déconnexion (JWT) | US3 | 1 |
|  | Mot de passe oublié | US4 | 1 |
| **3. Accueil et recherche** | Page d'accroche publique | US7 | 1 |
|  | Accueil avec message de bienvenue et description | US8 | 1 |
|  | Module de recherche (départ manuel, destination, dates, budget) | US9 | 1 |
| **4. Résultats (approche A)** | Embeddings des vols et classement par similarité (pgvector) | US12 | 1 |
|  | Page de résultats, modification des paramètres, filtres et tri | US14, US15 | 1 |
|  | Mesure du temps de recommandation (côté évaluateur) | US26 | 1 |
| **5. Personnalisation** | Page de préférences facultatives à la première connexion | US5 | 2 |
|  | Localisation avec consentement et saisie manuelle de secours | US10, US11 | 2 |
|  | Enregistrement des interactions (vues, favoris, avis, « Réserver ») | US22 | 2 |
|  | Favoris et avis pertinent ou non | US16, US17 | 2 |
|  | Mise à jour du profil à la connexion suivante | US23 | 2 |
| **6. Fiche et compte** | Fiche d'un vol et bouton « Réserver » | US20, US21 | 2 |
|  | Explication simple d'une recommandation | US18 | 2 |
|  | Historique des recherches | US19 | 2 |
|  | Mon compte : profil, préférences, consentements, suppression | US6, US24, US25 | 2 |
| **7. Approche B** | Utilisateurs et interactions simulés | US36 | 2 |
|  | Filtrage collaboratif kNN vol-vol | US27 | 3 |
|  | Mélange A et B (alpha selon les interactions) | US28 | 3 |
| **8. Comparaison et finitions** | Comparaison côté à côte de A et B | US29 | 3 |
|  | Dashboard évaluateur (temps, complexité, ressources) | US30 | 3 |
|  | Qualité : precision@k et NDCG | US31 | 3 |
|  | Compte de démonstration | US32 | 3 |
|  | Nom, logo, slogan, licence | US39 | 3 |

## Règles de conduite

- Ne pas commencer l'approche B avant que l'approche A soit intégrée de bout en bout (étape 4 terminée).
- Mesurer le temps de chaque recommandation dès la première version.
- Relire chaque fonctionnalité à deux, pour que tout le monde sache l'expliquer à l'oral.
