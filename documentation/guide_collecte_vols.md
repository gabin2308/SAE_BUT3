# Guide : base de vols et collecte Ignav

Projet SAÉ « Recommandation de vols » (BUT3 5.Real.01). Ce guide regroupe les commandes et les remarques de la mise en place : base PostgreSQL + pgvector dans Docker, collecte des données de l'API Ignav, vérifications.

## 1. Fichiers du dossier de travail

```
Données/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── schema.sql
├── collecte_ignav.py
├── .venv/              (environnement Python)
└── data/raw/           (JSON bruts de l'API)
```

### `.env` (ne jamais commiter)

```
POSTGRES_USER=sae
POSTGRES_PASSWORD=motdepasse
POSTGRES_DB=sae
DATABASE_URL=postgresql://sae:motdepasse@localhost:5433/sae
IGNAV_API_KEY=ta_cle_ici
DOSSIER_JSON=data/raw
```

### `.env.example` (à commiter, valeurs factices)

Même contenu que `.env`, avec des valeurs d'exemple, pour que le groupe sache quoi renseigner.

### `.gitignore`

```
.env
.venv/
data/raw/
```

### `docker-compose.yml`

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    env_file: .env
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./schema.sql:/docker-entrypoint-initdb.d/01-schema.sql

volumes:
  pgdata:
```

Le port `5433` côté machine évite le conflit avec un PostgreSQL local déjà sur le `5432`. Dans `DATABASE_URL`, utilise donc `localhost:5433`.

## 2. Démarrer la base (Docker)

```bash
docker compose up -d
docker compose ps
docker compose logs db | tail -30
docker compose exec db psql -U sae -d sae -c "\dt"
```

- `schema.sql` crée **18 tables**, 3 vues et des triggers.
- Au premier lancement, attends la ligne `database system is ready to accept connections` avant de lancer `psql`.
- `schema.sql` ne s'exécute **qu'à la première création** de la base. Après une modification du schéma, recrée tout (**efface les données**) :

```bash
docker compose down -v
docker compose up -d
```

### Arrêter / relancer sans perdre les données

```bash
docker compose stop
docker compose start
```

## 3. Environnement Python

Ubuntu protège son Python système (erreur `externally-managed-environment`) : utilise un environnement virtuel.

```bash
sudo apt install python3-full python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install requests psycopg2-binary python-dotenv
```

- À chaque nouveau terminal : `source .venv/bin/activate`.
- Le script lit le `.env` grâce à ces deux lignes en haut de `collecte_ignav.py` :

```python
from dotenv import load_dotenv
load_dotenv()
```

## 4. Les trois commandes du script

```bash
python collecte_ignav.py collecter   # appelle l'API, enregistre le fichier JSON ET la base
python collecte_ignav.py importer    # charge en base tous les .json du dossier data/raw (0 requête API)
python collecte_ignav.py rejouer     # re-normalise les JSON bruts non traités de la base (0 requête API)
```

### Quelle fonction stocke le JSON ?

| Fonction | Rôle |
| --- | --- |
| `sauver_json(type_req, donnees)` | enregistre la réponse dans un **fichier** `data/raw/*.json` |
| `stocker_brut(cur, type_req, donnees)` | enregistre la réponse dans la **base** (`ingestions_brutes.payload`, type JSONB) |
| `normaliser(cur, ingestion_id, donnees)` | remplit `vols` et `segments_vol` à partir du JSON |
| `importer()` | relit les fichiers JSON et les envoie en base |
| `rejouer()` | relit les JSON stockés en base et les re-normalise |

### Que devient un JSON dans la base ?

| Dans le JSON | Table |
| --- | --- |
| Le fichier entier | `ingestions_brutes` (1 ligne par appel) |
| Chaque élément de `itineraries` | `vols` |
| Chaque élément de `segments` | `segments_vol` |
| Les codes d'aéroports | `aeroports` (créés avec le code comme nom) |

## 5. Envoyer un JSON neuf en base

### Cas 1 : depuis l'API

```bash
source .venv/bin/activate
python collecte_ignav.py collecter
```

Règle d'abord `DEPARTS`, `DESTINATIONS`, `DECALAGES_JOURS`, `TYPES` et `MAX_REQUETES` en haut du script. La fonction `deja_collecte` saute une recherche déjà faite dans les dernières 24 h (pour ne pas gaspiller de quota). Pour en refaire une sur la même route et la même date : change la date (autre décalage), attends 24 h, ou supprime la ligne correspondante de `ingestions_brutes`.

### Cas 2 : tu as déjà un fichier JSON

1. Enregistre-le dans `data/raw/` avec l'extension `.json`. Il doit être complet : `origin`, `destination`, `departure_date`, `itineraries`, `observed_at`.
2. Lance :

```bash
python collecte_ignav.py importer
```

Attention : `importer` relit **tous** les fichiers du dossier. Les vols déjà connus sont mis à jour (prix) sans doublon, mais chaque passage ajoute une ligne dans `ingestions_brutes`. Pour n'envoyer que le nouveau fichier, déplace les anciens dans `data/raw/archive/` (les sous-dossiers ne sont pas lus).

## 6. Vérifier dans la base

```bash
# Comptages
docker compose exec db psql -U sae -d sae -c "SELECT (SELECT COUNT(*) FROM vols) AS vols, (SELECT COUNT(*) FROM segments_vol) AS segments, (SELECT COUNT(*) FROM ingestions_brutes) AS bruts, (SELECT COUNT(*) FROM aeroports) AS aeroports;"

# Les vols
docker compose exec db psql -U sae -d sae -c "SELECT origine, destination, prix, devise, compagnie_aller, duree_aller_min, escales_aller FROM vols ORDER BY prix;"

# Les segments
docker compose exec db psql -U sae -d sae -c "SELECT numero_vol, aeroport_depart, depart_local, aeroport_arrivee, arrivee_locale FROM segments_vol ORDER BY depart_local;"

# Les JSON bruts
docker compose exec db psql -U sae -d sae -c "SELECT type, origine, destination, nb_itineraires, traite FROM ingestions_brutes;"
```

Test anti-doublons : relance `importer` ; il doit afficher `+0 nouveaux, N mis à jour`, et les comptes de `vols` et `segments_vol` ne changent pas.

Session interactive : `docker compose exec db psql -U sae -d sae`, puis `\dt` (tables), `\q` (quitter).

## 7. Jeu de données pour démarrer

Un petit jeu réaliste suffit pour développer l'approche A. Exemple (environ 72 requêtes, 500 à 800 vols) :

- `DEPARTS = ["CDG"]`
- une douzaine de destinations variées : Europe proche (LHR, FRA, MAD, FCO), Maghreb (ALG, CMN), long-courrier (JFK, DXB, DSS), quelques autres
- `DECALAGES_JOURS = [21, 45, 90]`
- `TYPES = ["aller_simple", "aller_retour"]`

Ensuite :

1. Charger `pays` (data.gouv.fr) et enrichir `aeroports` avec OurAirports (noms, villes, pays, coordonnées), nécessaires pour la recherche par pays ou ville (US9).
2. Générer des vols simulés (US35) pour les routes absentes, avec une graine fixe, marqués `simulee = TRUE`.
3. Calculer les embeddings (prix, durée, escales, compagnie, bagage, ramenés entre 0 et 1) dans `vols.embedding`.
4. Poursuivre avec l'ordre de développement : compte, accueil et recherche, résultats (approche A).

## 8. Remarques importantes

- **Quota Ignav** : 1 000 requêtes gratuites au total, puis 2 $ les 1 000. Chaque requête renvoie environ 10 itinéraires. Les requêtes échouées ne sont pas facturées. Le plafond `MAX_REQUETES` protège contre un dépassement accidentel. Garde une réserve pour les liens de réservation (appelés au clic sur « Réserver », US21).
- **Fraîcheur des prix** : la FAQ d'Ignav déconseille de garder les résultats en cache plus de quelques heures. Pour la SAÉ, affiche « prix relevé le… » (colonne `observe_le`) et relance la collecte avant une démonstration.
- **Bagage** : aucune information de bagage dans les JSON de l'échantillon. `vols.bagage_inclus` reste donc `NULL`. À décider avec le groupe : le simuler, ou retirer ce critère de l'embedding (et passer `vector(5)` à `vector(4)`).
- **Devise** : les prix sont en USD. Décide si tu convertis en EUR ou si tu affiches en USD.
- **Escales** : non fournies par l'API. Elles se calculent : nombre de segments d'un sens moins 1.
- **Anti-doublons** : l'unicité repose sur `vols.signature` (SHA-256 de compagnie, numéro de vol et départ UTC de chaque segment), pas sur `ignav_id`, dont on ne sait pas s'il reste stable. Si le vol existe, seul le prix est mis à jour.
- **Aéroports** : le script crée les aéroports manquants avec le code IATA comme nom, pour éviter les erreurs de clé étrangère. À enrichir ensuite avec OurAirports.
- **Noms de champs de la requête** (`origin`, `destination`, `departure_date`, `return_date`) et en-tête d'authentification (`X-Api-Key`, ou `Authorization: Bearer`) : déduits de la doc, à confirmer dans la page « One-Way Fares » ou le playground d'Ignav en cas d'erreur 4xx.
- **Sécurité** : la clé API et le mot de passe restent dans `.env`, jamais dans le code ni sur Git.
- **Suppression de compte (US25)** : toutes les tables qui référencent `utilisateurs` ont `ON DELETE CASCADE`. Les mesures de `executions_recommandation` sont conservées (l'utilisateur passe à `NULL`).

## 9. Dépannage (erreurs rencontrées)

| Erreur | Cause | Solution |
| --- | --- | --- |
| `failed to resolve reference ... i/o timeout` (Docker) | DNS de Docker | Ajouter `{"dns": ["8.8.8.8", "1.1.1.1"]}` dans `/etc/docker/daemon.json`, puis `sudo systemctl restart docker` |
| `Bind for 127.0.0.1:5432 failed: port is already allocated` | Un PostgreSQL local occupe le port | Mapper `"5433:5432"` et utiliser le port 5433 dans `DATABASE_URL` |
| `psql: ... No such file or directory` juste après le démarrage | La base n'est pas encore prête | Attendre, vérifier `docker compose logs db` |
| `externally-managed-environment` (pip) | Python système protégé | Utiliser un `venv` (section 3) |
| Le script affiche seulement l'aide | Ancienne version du script, ou mauvaise commande | Remplacer le fichier ; vérifier avec `grep importer collecte_ignav.py` |
| `JSONDecodeError: Expecting value: line 1 column 1` | Fichier JSON vide | Remplir le fichier (`wc -c fichier.json` doit être > 0) ou le supprimer |
| `importer` n'affiche rien | `data/raw/` vide ou introuvable | `ls data/raw` ; lancer la commande depuis le dossier `Données` |
