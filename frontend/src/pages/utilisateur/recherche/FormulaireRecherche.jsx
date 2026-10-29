// src/components/recherche/FormulaireRecherche.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ChampAeroport from "../../../components/ui/ChampAeroport";
import ChampTexte from "../../../components/ui/ChampTexte";

const aujourdhui = () => new Date().toISOString().slice(0, 10);

export default function FormulaireRecherche({ valeursInitiales = {} }) {
  const navigate = useNavigate();

  const [origine, setOrigine] = useState(valeursInitiales.origine ?? null);
  const [destination, setDestination] = useState(valeursInitiales.destination ?? null);
  const [allerRetour, setAllerRetour] = useState(valeursInitiales.allerRetour ?? true);
  const [dateDepart, setDateDepart] = useState(valeursInitiales.dateDepart ?? "");
  const [dateRetour, setDateRetour] = useState(valeursInitiales.dateRetour ?? "");
  const [passagers, setPassagers] = useState(valeursInitiales.passagers ?? 1);
  const [budget, setBudget] = useState(valeursInitiales.budget ?? "");
  const [erreurs, setErreurs] = useState({});

  const soumettre = (e) => {
    e.preventDefault();
    const err = {};
    if (!origine) err.origine = "Choisissez un aéroport de départ dans la liste.";
    if (!destination) err.destination = "Choisissez une destination dans la liste.";
    if (origine && destination && origine.code_iata === destination.code_iata) {
      err.destination = "La destination doit différer du départ.";
    }
    if (!dateDepart) err.dateDepart = "Indiquez la date de départ.";
    else if (dateDepart < aujourdhui()) err.dateDepart = "La date de départ est passée.";
    if (allerRetour) {
      if (!dateRetour) err.dateRetour = "Indiquez la date de retour.";
      else if (dateDepart && dateRetour < dateDepart) {
        err.dateRetour = "Le retour doit suivre le départ.";
      }
    }
    const nb = Number(passagers);
    if (!Number.isInteger(nb) || nb < 1 || nb > 9) err.passagers = "Entre 1 et 9 passagers.";
    if (budget !== "" && !(Number(budget) > 0)) err.budget = "Entrez un montant positif.";

    setErreurs(err);
    if (Object.keys(err).length) return;

    const params = new URLSearchParams({
      origine: origine.code_iata,
      destination: destination.code_iata,
      date_depart: dateDepart,
      aller_retour: allerRetour ? "1" : "0",
      passagers: String(nb),
    });
    if (allerRetour) params.set("date_retour", dateRetour);
    if (budget !== "") params.set("budget", String(Number(budget)));

    navigate(`/resultats?${params}`);
  };

  const choixType = (valeur, texte) => (
    <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-800">
      <input
        type="radio"
        name="type-trajet"
        checked={allerRetour === valeur}
        onChange={() => setAllerRetour(valeur)}
        className="h-4 w-4 accent-blue-600"
      />
      {texte}
    </label>
  );

  return (
    <form onSubmit={soumettre} noValidate className="space-y-5">
      <fieldset>
        <legend className="sr-only">Type de trajet</legend>
        <div className="flex gap-6">
          {choixType(true, "Aller-retour")}
          {choixType(false, "Aller simple")}
        </div>
      </fieldset>

      <div className="grid gap-4 md:grid-cols-2">
        <ChampAeroport label="Départ" value={origine} onChange={setOrigine} erreur={erreurs.origine} />
        <ChampAeroport label="Destination" value={destination} onChange={setDestination} erreur={erreurs.destination} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ChampTexte
          label="Date de départ"
          type="date"
          min={aujourdhui()}
          value={dateDepart}
          onChange={(e) => setDateDepart(e.target.value)}
          erreur={erreurs.dateDepart}
        />
        {allerRetour && (
          <ChampTexte
            label="Date de retour"
            type="date"
            min={dateDepart || aujourdhui()}
            value={dateRetour}
            onChange={(e) => setDateRetour(e.target.value)}
            erreur={erreurs.dateRetour}
          />
        )}
        <ChampTexte
          label="Passagers"
          type="number"
          min={1}
          max={9}
          value={passagers}
          onChange={(e) => setPassagers(e.target.value)}
          erreur={erreurs.passagers}
        />
        <ChampTexte
          label="Budget max (USD, facultatif)"
          type="number"
          min={1}
          placeholder="Ex. 600"
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
          erreur={erreurs.budget}
        />
      </div>

      <button
        type="submit"
        className="w-full rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 sm:w-auto"
      >
        Rechercher
      </button>
    </form>
  );
}