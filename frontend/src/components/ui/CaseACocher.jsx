// src/components/ui/CaseACocher.jsx
import { useId } from "react";

export default function CaseACocher({ children, erreur, className = "", ...props }) {
  const id = useId();
  return (
    <div className={className}>
      <div className="flex items-start gap-2.5">
        <input
          id={id}
          type="checkbox"
          aria-invalid={erreur ? "true" : undefined}
          aria-describedby={erreur ? `${id}-erreur` : undefined}
          className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-blue-600 focus:ring-2 focus:ring-blue-600"
          {...props}
        />
        <label htmlFor={id} className="text-sm leading-snug text-slate-700">
          {children}
        </label>
      </div>
      {erreur && (
        <p id={`${id}-erreur`} className="mt-1 pl-6 text-sm text-red-600">
          {erreur}
        </p>
      )}
    </div>
  );
}