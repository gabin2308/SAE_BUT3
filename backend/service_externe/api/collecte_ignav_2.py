"""
Collecte des vols Ignav -> PostgreSQL (schema.sql)

Usage :
    python collecte_ignav.py collecter   # appelle l'API, stocke le JSON brut, normalise
    python collecte_ignav.py rejouer     # re-normalise les JSON bruts non traités (0 requête API)
    python collecte_ignav.py importer    # charge en base les fichiers JSON du dossier data/raw (0 requête API)

Chaque réponse de l'API est aussi enregistrée dans un fichier JSON (dossier data/raw,
modifiable avec la variable DOSSIER_JSON).

Variables d'environnement :
    IGNAV_API_KEY   clé API Ignav
    DATABASE_URL    ex. postgresql://user:mdp@localhost:5432/sae

Dépendances : pip install requests psycopg2-binary
"""
import hashlib
import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import psycopg2
import requests
from psycopg2.extras import Json

from dotenv import load_dotenv
load_dotenv()

BASE_URL = "https://ignav.com"
API_KEY = os.environ.get("IGNAV_API_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DOSSIER_JSON = Path(os.environ.get("DOSSIER_JSON", "data/raw"))

# --- À adapter ---------------------------------------------------------------
DEPARTS = ["CDG"]
DESTINATIONS = [
    "LHR", "FRA", "MAD", "FCO", "BCN", "AMS", "LIS", "BRU", "ZRH", "VIE", "CPH", "ATH",
    "IST", "DUB", "JFK", "YUL", "DXB", "CMN", "ALG", "TUN", "DSS", "ABJ", "DLA", "NBO",
    "BKK", "HND", "GRU",
]
ROUTES = [(o, d) for o in DEPARTS for d in DESTINATIONS if o != d]
DECALAGES_JOURS = [21, 45, 90]            # départs dans 21, 45 et 90 jours
DUREE_SEJOUR = 7                          # jours entre aller et retour (aller-retour)
TYPES = ["aller_simple","aller_retour"]                  # ajoute "aller_retour" pour des trajets retour
MAX_REQUETES = 800                        # plafond de requêtes API par lancement
# Quota : 1 000 requêtes gratuites au total. Chaque requête renvoie ~10 itinéraires.
# Ici : 135 routes x 3 dates = 405 requêtes d'aller simple, soit ~4 000 vols.
# -----------------------------------------------------------------------------


def appeler_api(chemin, corps, tentatives=4):
    """POST JSON avec nouvelle tentative (erreurs réseau et HTTP 424)."""
    for essai in range(tentatives):
        try:
            rep = requests.post(
                BASE_URL + chemin,
                json=corps,
                headers={"X-Api-Key": API_KEY},
                timeout=60,
            )
        except requests.RequestException:
            rep = None
        if rep is not None and rep.status_code == 200:
            return rep.json()
        if rep is not None and rep.status_code not in (424, 429, 500, 502, 503):
            raise RuntimeError(f"Erreur API {rep.status_code} : {rep.text[:300]}")
        time.sleep(2 ** essai)
    raise RuntimeError(f"Échec après {tentatives} tentatives : {chemin} {corps}")


def sauver_json(type_req, donnees):
    """Enregistre la réponse brute dans un fichier JSON horodaté."""
    DOSSIER_JSON.mkdir(parents=True, exist_ok=True)
    horodatage = donnees["observed_at"][:19].replace(":", "").replace("-", "")
    nom = (f"{type_req}_{donnees['origin']}-{donnees['destination']}_"
           f"{donnees['departure_date']}_{horodatage}.json")
    with open(DOSSIER_JSON / nom, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)


def calculer_signature(itineraire):
    """SHA-256 des segments (compagnie | numéro | départ UTC), aller puis retour."""
    morceaux = []
    for sens in ("outbound", "inbound"):
        for seg in (itineraire.get(sens) or {}).get("segments", []):
            morceaux.append(f"{sens}|{seg['marketing_carrier_code']}|"
                            f"{seg['flight_number']}|{seg['departure_time_utc']}")
    return hashlib.sha256("#".join(morceaux).encode()).hexdigest()


def assurer_aeroports(cur, donnees):
    """Évite les erreurs de clé étrangère : crée les aéroports manquants
    (nom = code IATA), à enrichir ensuite avec OurAirports."""
    codes = {donnees["origin"], donnees["destination"]}
    for it in donnees["itineraries"]:
        for sens in ("outbound", "inbound"):
            for seg in (it.get(sens) or {}).get("segments", []):
                codes.add(seg["departure_airport"])
                codes.add(seg["arrival_airport"])
    for code in codes:
        cur.execute(
            "INSERT INTO aeroports (code_iata, nom) VALUES (%s, %s) "
            "ON CONFLICT (code_iata) DO NOTHING", (code, code))


def inserer_segments(cur, vol_id, trajet, sens):
    for ordre, s in enumerate(trajet["segments"], start=1):
        cur.execute(
            """INSERT INTO segments_vol
               (vol_id, sens, ordre, code_compagnie, numero_vol, compagnie_operante, avion,
                aeroport_depart, depart_local, fuseau_depart, depart_utc,
                aeroport_arrivee, arrivee_locale, fuseau_arrivee, arrivee_utc, duree_min)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (vol_id, sens, ordre, s["marketing_carrier_code"], s["flight_number"],
             s["operating_carrier_name"], s.get("aircraft"),
             s["departure_airport"], s["departure_time_local"], s["departure_timezone"],
             s["departure_time_utc"],
             s["arrival_airport"], s["arrival_time_local"], s["arrival_timezone"],
             s["arrival_time_utc"], s["duration_minutes"]))


def normaliser(cur, ingestion_id, donnees):
    """Insère (ou met à jour le prix de) chaque itinéraire. Retourne (nouveaux, mis_a_jour)."""
    assurer_aeroports(cur, donnees)
    nouveaux = maj = 0
    for it in donnees["itineraries"]:
        aller = it["outbound"]
        retour = it.get("inbound")
        cur.execute(
            """INSERT INTO vols
               (signature, ignav_id, ingestion_id, origine, destination, date_depart,
                date_retour, aller_retour, prix, devise, statut_prix, classe, auto_transfert,
                compagnie_aller, duree_aller_min, escales_aller,
                compagnie_retour, duree_retour_min, escales_retour, observe_le)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (signature) DO UPDATE
                  SET prix = EXCLUDED.prix, ignav_id = EXCLUDED.ignav_id,
                      statut_prix = EXCLUDED.statut_prix, observe_le = EXCLUDED.observe_le
               RETURNING id, (xmax = 0) AS insere""",
            (calculer_signature(it), it["ignav_id"], ingestion_id,
             donnees["origin"], donnees["destination"], donnees["departure_date"],
             donnees.get("return_date"), retour is not None,
             it["price"]["amount"], it["price"]["currency"], it["price"].get("status"),
             it.get("cabin_class", "economy"), it.get("requires_self_transfer", False),
             aller["carrier"], aller["duration_minutes"], len(aller["segments"]) - 1,
             retour["carrier"] if retour else None,
             retour["duration_minutes"] if retour else None,
             len(retour["segments"]) - 1 if retour else None,
             donnees["observed_at"]))
        vol_id, insere = cur.fetchone()
        if insere:
            nouveaux += 1
            inserer_segments(cur, vol_id, aller, "aller")
            if retour:
                inserer_segments(cur, vol_id, retour, "retour")
        else:
            maj += 1
    return nouveaux, maj


def stocker_brut(cur, type_req, donnees):
    cur.execute(
        """INSERT INTO ingestions_brutes
           (type, origine, destination, date_depart, date_retour, observe_le,
            nb_itineraires, payload)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (type_req, donnees["origin"], donnees["destination"], donnees["departure_date"],
         donnees.get("return_date"), donnees["observed_at"],
         len(donnees["itineraries"]), Json(donnees)))
    return cur.fetchone()[0]


def deja_collecte(cur, type_req, origine, destination, depart):
    """Évite de consommer du quota pour une recherche déjà faite dans les dernières 24 h."""
    cur.execute(
        """SELECT 1 FROM ingestions_brutes
           WHERE type = %s AND origine = %s AND destination = %s AND date_depart = %s
             AND observe_le > NOW() - INTERVAL '24 hours' LIMIT 1""",
        (type_req, origine, destination, depart))
    return cur.fetchone() is not None


def collecter():
    conn = psycopg2.connect(DATABASE_URL)
    nb_requetes = 0
    for decalage in DECALAGES_JOURS:
        depart = date.today() + timedelta(days=decalage)
        retour = depart + timedelta(days=DUREE_SEJOUR)
        for origine, destination in ROUTES:
            for type_req in TYPES:
                if nb_requetes >= MAX_REQUETES:
                    print(f"Plafond de {MAX_REQUETES} requêtes atteint, arrêt.")
                    conn.close()
                    return
                with conn, conn.cursor() as cur:
                    if deja_collecte(cur, type_req, origine, destination, depart):
                        continue
                corps = {"origin": origine, "destination": destination,
                         "departure_date": depart.isoformat()}
                if type_req == "aller_simple":
                    chemin = "/api/fares/one-way"
                else:
                    chemin = "/api/fares/round-trip"
                    corps["return_date"] = retour.isoformat()
                try:
                    donnees = appeler_api(chemin, corps)
                    nb_requetes += 1
                    sauver_json(type_req, donnees)
                    with conn, conn.cursor() as cur:   # une transaction par requête
                        ingestion_id = stocker_brut(cur, type_req, donnees)
                        n, m = normaliser(cur, ingestion_id, donnees)
                        cur.execute("UPDATE ingestions_brutes SET traite = TRUE WHERE id = %s",
                                    (ingestion_id,))
                    print(f"[{nb_requetes}] {origine}->{destination} {depart} {type_req}: "
                          f"+{n} nouveaux, {m} mis à jour")
                except Exception as e:  # on continue avec la route suivante
                    print(f"ERREUR {origine}->{destination} {depart} {type_req}: {e}")
    print(f"Terminé : {nb_requetes} requêtes API utilisées.")
    conn.close()


def rejouer():
    conn = psycopg2.connect(DATABASE_URL)
    with conn, conn.cursor() as cur:
        cur.execute("SELECT id, payload FROM ingestions_brutes WHERE traite = FALSE ORDER BY observe_le")
        for ingestion_id, payload in cur.fetchall():
            n, m = normaliser(cur, ingestion_id, payload)
            cur.execute("UPDATE ingestions_brutes SET traite = TRUE WHERE id = %s", (ingestion_id,))
            print(f"{ingestion_id}: +{n} nouveaux, {m} mis à jour")
    conn.close()


def importer():
    """Charge en base les fichiers JSON du dossier (sans appeler l'API)."""
    conn = psycopg2.connect(DATABASE_URL)
    for fichier in sorted(DOSSIER_JSON.glob("*.json")):
        with open(fichier, encoding="utf-8") as f:
            donnees = json.load(f)
        type_req = "aller_retour" if donnees.get("return_date") else "aller_simple"
        with conn, conn.cursor() as cur:
            ingestion_id = stocker_brut(cur, type_req, donnees)
            n, m = normaliser(cur, ingestion_id, donnees)
            cur.execute("UPDATE ingestions_brutes SET traite = TRUE WHERE id = %s", (ingestion_id,))
        print(f"{fichier.name}: +{n} nouveaux, {m} mis à jour")
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("collecter", "rejouer", "importer"):
        sys.exit(__doc__)
    if not DATABASE_URL or (sys.argv[1] == "collecter" and not API_KEY):
        sys.exit("Définis DATABASE_URL (et IGNAV_API_KEY pour collecter).")
    {"collecter": collecter, "rejouer": rejouer, "importer": importer}[sys.argv[1]]()
