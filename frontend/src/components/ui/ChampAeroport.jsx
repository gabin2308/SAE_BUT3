// src/components/ui/ChampAeroport.jsx
// Autocomplétion d'aéroport (US9) : appel à partir de 2 caractères, délai de 250 ms,
// requête précédente annulée, navigation clavier (pattern ARIA combobox).
import { useEffect, useId, useState } from "react";
import { aeroportService } from "../../services/aeroportService";

const DELAI_MS = 250;
const MIN_CARACTERES = 2;

export default function ChampAeroport({
  label,
  icone,
  value,            // aéroport choisi, ou null
  onChange,         // (aeroport | null) => void
  erreur,
  placeholder = "Ville, aéroport ou pays",
  className = "",
  ...props
}) {
  const id = useId();
  const listeId = `${id}-liste`;

  const [texte, setTexte] = useState(value?.libelle ?? "");
  const [options, setOptions] = useState([]);
  const [ouvert, setOuvert] = useState(false);
  const [actif, setActif] = useState(-1);
  const [chargement, setChargement] = useState(false);
  const [echecReseau, setEchecReseau] = useState(false);

  // Valeur imposée de l'extérieur (préremplissage, relance d'une recherche)
  useEffect(() => {
    if (value) setTexte(value.libelle);
  }, [value]);

  // Recherche avec délai ; le cleanup annule le minuteur et la requête en cours
  useEffect(() => {
    const q = texte.trim();
    if (value || q.length < MIN_CARACTERES) {
      setOptions([]);
      setChargement(false);
      return;
    }
    const ctrl = new AbortController();
    const minuteur = setTimeout(async () => {
      setChargement(true);
      setEchecReseau(false);
      try {
        const res = await aeroportService.rechercher(q, { signal: ctrl.signal });
        setOptions(res);
        setActif(-1);
      } catch {
        if (ctrl.signal.aborted) return; // annulée volontairement
        setOptions([]);
        setEchecReseau(true);
      } finally {
        if (!ctrl.signal.aborted) setChargement(false);
      }
    }, DELAI_MS);
    return () => {
      clearTimeout(minuteur);
      ctrl.abort();
    };
  }, [texte, value]);

  const saisir = (e) => {
    setTexte(e.target.value);
    setOuvert(true);
    if (value) onChange(null); // il retape : l'ancien choix n'est plus valable
  };

  const choisir = (aeroport) => {
    setTexte(aeroport.libelle);
    setOuvert(false);
    setOptions([]);
    onChange(aeroport);
  };

  const toucheClavier = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOuvert(true);
      setActif((i) => Math.min(i + 1, options.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActif((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && ouvert && actif >= 0 && options[actif]) {
      e.preventDefault(); // ne soumet pas le formulaire
      choisir(options[actif]);
    } else if (e.key === "Escape") {
      setOuvert(false);
    }
  };

  const afficherListe = ouvert && !value && texte.trim().length >= MIN_CARACTERES;

  return (
    <div className={`relative ${className}`}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-800">
        {label}
      </label>
      <div className="relative">
        {icone && (
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
            {icone}
          </span>
        )}
        <input
          id={id}
          type="text"
          role="combobox"
          autoComplete="off"
          aria-expanded={afficherListe}
          aria-controls={listeId}
          aria-autocomplete="list"
          aria-activedescendant={actif >= 0 ? `${id}-opt-${actif}` : undefined}
          aria-invalid={erreur ? "true" : undefined}
          aria-describedby={erreur ? `${id}-erreur` : undefined}
          placeholder={placeholder}
          value={texte}
          onChange={saisir}
          onFocus={() => setOuvert(true)}
          onBlur={() => setOuvert(false)}
          onKeyDown={toucheClavier}
          className={`w-full rounded-lg border bg-white py-2.5 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 ${
            icone ? "pl-10" : "pl-3"
          } ${erreur ? "border-red-500" : "border-slate-300"}`}
          {...props}
        />
      </div>

      {afficherListe && (
        <ul
          id={listeId}
          role="listbox"
          aria-label={`Suggestions : ${label}`}
          className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
        >
          {options.map((a, i) => (
            <li
              key={a.code_iata}
              id={`${id}-opt-${i}`}
              role="option"
              aria-selected={i === actif}
              // mousedown (et non click) : se produit avant le blur de l'input
              onMouseDown={(e) => {
                e.preventDefault();
                choisir(a);
              }}
              onMouseEnter={() => setActif(i)}
              className={`cursor-pointer px-3 py-2 text-sm ${
                i === actif ? "bg-blue-50 text-blue-900" : "text-slate-800"
              }`}
            >
              <span className="font-medium">{a.libelle}</span>
              {a.nom && a.nom !== a.ville && (
                <span className="block text-xs text-slate-500">{a.nom}</span>
              )}
            </li>
          ))}
          {!chargement && !echecReseau && options.length === 0 && (
            <li role="presentation" className="px-3 py-2 text-sm text-slate-500">
              Aucun aéroport trouvé.
            </li>
          )}
          {chargement && (
            <li role="presentation" className="px-3 py-2 text-sm text-slate-500">
              Recherche…
            </li>
          )}
          {echecReseau && (
            <li role="presentation" className="px-3 py-2 text-sm text-red-600">
              Recherche impossible pour le moment.
            </li>
          )}
        </ul>
      )}

      {erreur && (
        <p id={`${id}-erreur`} className="mt-1 text-sm text-red-600">
          {erreur}
        </p>
      )}
    </div>
  );
}