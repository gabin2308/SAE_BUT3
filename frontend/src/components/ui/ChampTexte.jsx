// src/components/ui/ChampTexte.jsx
// Champ du storyboard : libellé au-dessus, icône à gauche, œil à droite pour les mots de passe.
import { useId, useState } from "react";
import { IconeOeil, IconeOeilBarre } from "./Icones";

export default function ChampTexte({
  label,
  icone,
  type = "text",
  erreur,
  className = "",
  ...props
}) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  const estMotDePasse = type === "password";

  return (
    <div className={className}>
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
          type={estMotDePasse && visible ? "text" : type}
          aria-invalid={erreur ? "true" : undefined}
          aria-describedby={erreur ? `${id}-erreur` : undefined}
          className={`w-full rounded-lg border bg-white py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 ${
            icone ? "pl-10" : "pl-3"
          } ${estMotDePasse ? "pr-11" : "pr-3"} ${
            erreur ? "border-red-500" : "border-slate-300"
          }`}
          {...props}
        />
        {estMotDePasse && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
            aria-pressed={visible}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-slate-500 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
          >
            {visible ? <IconeOeilBarre /> : <IconeOeil />}
          </button>
        )}
      </div>
      {erreur && (
        <p id={`${id}-erreur`} className="mt-1 text-sm text-red-600">
          {erreur}
        </p>
      )}
    </div>
  );
}