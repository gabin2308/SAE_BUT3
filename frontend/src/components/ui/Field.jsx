import { useState } from "react";
import { IconeOeil, IconeOeilBarre } from "./Icones";

export default function Field({ label, icon: Icon, type = "text", error, id, ...props }) {
  const [visible, setVisible] = useState(false);
  const estMdp = type === "password";
  const inputId = id ?? props.name;

  return (
    <div>
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-sm font-semibold text-ink">{label}</label>
      )}
      <div className={`flex items-center gap-2 rounded-lg border bg-white px-3 focus-within:ring-2 focus-within:ring-brand-500/30 ${
        error ? "border-red-400" : "border-slate-200 focus-within:border-brand-500"}`}>
        {Icon && <Icon className="h-5 w-5 shrink-0 text-slate-400" />}
        <input id={inputId} type={estMdp && visible ? "text" : type} aria-invalid={!!error}
          className="w-full bg-transparent py-3 text-sm text-ink outline-none placeholder:text-slate-400"
          {...props} />
        {estMdp && (
          <button type="button" onClick={() => setVisible((v) => !v)}
            aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
            className="text-slate-400 hover:text-slate-600">
            {visible ? <IconeOeilBarre className="h-5 w-5" /> : <IconeOeil className="h-5 w-5" />}
          </button>
        )}
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
