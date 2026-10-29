import { Link } from "react-router-dom";

const base =
  "inline-flex items-center justify-center rounded-lg px-5 py-3 text-sm font-semibold transition " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:opacity-60";

const variantes = {
  primary: "bg-brand-500 text-white hover:bg-brand-600",
  outline: "border border-white/70 bg-[#0a2a5e]/30 text-white backdrop-blur-sm hover:bg-[#0a2a5e]/50",
};

export default function Button({ variant = "primary", loading = false, className = "", children, ...props }) {
  return (
    <button {...props} disabled={loading || props.disabled}
      className={`${base} ${variantes[variant]} ${className}`}>
      {loading ? "Patientez…" : children}
    </button>
  );
}

export function LienBouton({ to, variant = "primary", className = "", ...props }) {
  return <Link to={to} className={`${base} ${variantes[variant]} ${className}`} {...props} />;
}
