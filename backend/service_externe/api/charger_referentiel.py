"""Charge pays + aéroports depuis OurAirports (0 requête Ignav)."""
import csv
import io

import psycopg2
import requests

from app.settings import settings

BASE = "https://davidmegginson.github.io/ourairports-data/"


def lire_csv(nom):
    rep = requests.get(BASE + nom, timeout=60)
    rep.raise_for_status()
    return csv.DictReader(io.StringIO(rep.text))


def main():
    conn = psycopg2.connect(settings.dsn)
    with conn, conn.cursor() as cur:
        # 1. Pays (avant les aéroports, à cause de la clé étrangère)
        pays = {r["code"]: r["name"] for r in lire_csv("countries.csv") if len(r["code"]) == 2}
        for code, nom in pays.items():
            cur.execute(
                "INSERT INTO pays (code_pays, nom) VALUES (%s, %s) "
                "ON CONFLICT (code_pays) DO UPDATE SET nom = EXCLUDED.nom", (code, nom))
        print(f"{len(pays)} pays")

        # 2. Aéroports ayant un code IATA (dédoublonnés)
        aeroports = {}
        for r in lire_csv("airports.csv"):
            iata = r["iata_code"].strip()
            if len(iata) == 3 and r["iso_country"] in pays:
                aeroports[iata] = r
        for iata, r in aeroports.items():
            cur.execute(
                """INSERT INTO aeroports (code_iata, nom, ville, code_pays, latitude, longitude)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (code_iata) DO UPDATE
                      SET nom = EXCLUDED.nom, ville = EXCLUDED.ville,
                          code_pays = EXCLUDED.code_pays,
                          latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude""",
                (iata, r["name"], r["municipality"] or None, r["iso_country"],
                 float(r["latitude_deg"]), float(r["longitude_deg"])))
        print(f"{len(aeroports)} aéroports")
    conn.close()


if __name__ == "__main__":
    main()