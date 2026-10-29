// src/components/layouts/UtilisateurLayout.jsx
// Coque des pages connectées : en-tête avec navigation et menu utilisateur,
// contenu, pied de page. Les pages publiques gardent AuthLayout.
import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import Logo from "../ui/Logo";
import { useAuth } from "../../context/AuthContext";

// Ajoute une entrée à mesure que les pages existent (une route par entrée).
const LIENS = [
  { to: "/accueil", label: "Accueil", end: true },
  // { to: "/favoris", label: "Favoris" },              // US16
  // { to: "/historique", label: "Historique" },        // US19
  // { to: "/mon-compte", label: "Mon compte" },        // US24
];

const LIENS_PIED = [
  { to: "/confidentialite", label: "Confidentialité" },
  { to: "/mentions-legales", label: "Mentions légales" },
];

const lienNav = ({ isActive }) =>
  `text-sm font-medium hover:text-blue-700 ${isActive ? "text-blue-700" : "text-slate-700"}`;

export default function UtilisateurLayout({ children }) {
  const { user, logout } = useAuth();
  const [menuOuvert, setMenuOuvert] = useState(false);
  const annee = new Date().getFullYear();

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900 antialiased">
      <a
        href="#contenu"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:border-2 focus:border-blue-600 focus:bg-white focus:p-3"
      >
        Aller au contenu principal
      </a>

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link to="/accueil" className="rounded-lg" aria-label="Accueil">
            <Logo />
          </Link>

          <nav className="hidden items-center gap-6 md:flex" aria-label="Navigation principale">
            {LIENS.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={lienNav}>
                {l.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden items-center gap-4 md:flex">
            <span className="text-sm text-slate-600">
              {user?.prenom} {user?.nom}
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              Se déconnecter
            </button>
          </div>

          <button
            type="button"
            onClick={() => setMenuOuvert((v) => !v)}
            aria-expanded={menuOuvert}
            aria-controls="menu-mobile"
            aria-label={menuOuvert ? "Fermer le menu" : "Ouvrir le menu"}
            className="inline-flex h-10 items-center justify-center rounded-lg border border-slate-300 px-3 text-slate-800 md:hidden"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d={menuOuvert ? "M6 6l12 12M18 6 6 18" : "M4 6h16M4 12h16M4 18h16"} />
            </svg>
          </button>
        </div>

        {menuOuvert && (
          <nav id="menu-mobile" className="border-t border-slate-200 px-4 py-3 md:hidden" aria-label="Navigation mobile">
            <ul className="flex flex-col">
              {LIENS.map((l) => (
                <li key={l.to}>
                  <NavLink
                    to={l.to}
                    end={l.end}
                    onClick={() => setMenuOuvert(false)}
                    className={(s) => `${lienNav(s)} flex min-h-11 items-center`}
                  >
                    {l.label}
                  </NavLink>
                </li>
              ))}
              <li className="mt-2 border-t border-slate-200 pt-3">
                <p className="mb-2 text-sm text-slate-600">
                  {user?.prenom} {user?.nom}
                </p>
                <button
                  type="button"
                  onClick={logout}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-800 hover:bg-slate-50"
                >
                  Se déconnecter
                </button>
              </li>
            </ul>
          </nav>
        )}
      </header>

      <main id="contenu" className="flex-1">
        {children}
      </main>

      <footer className="mt-12 border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-6 text-sm text-slate-600 sm:px-6 md:flex-row md:items-center md:justify-between">
          <p>© {annee} · Les Orques tactiques</p>
          <ul className="flex flex-wrap gap-x-5 gap-y-2">
            {LIENS_PIED.map((l) => (
              <li key={l.to}>
                <Link to={l.to} className="underline-offset-4 hover:underline">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </footer>
    </div>
  );
}