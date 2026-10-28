// src/components/layouts/AuthLayout.jsx
// Coquille des écrans d'accès (connexion, inscription, activation, mot de passe oublié…) :
// fond bleu très clair, contenu centré, sans navigation. Chaque page fournit sa propre carte
// (le logo est dans la carte, ou en bas pour « Compte activé »).
export default function AuthLayout({ children }) {
  return (
    <div className="flex min-h-screen flex-col bg-blue-50 font-sans text-slate-900 antialiased">
      <a
        href="#contenu"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:border-2 focus:border-blue-600 focus:bg-white focus:p-3"
      >
        Aller au contenu principal
      </a>

      <main
        id="contenu"
        className="flex flex-1 items-center justify-center px-4 py-10 sm:px-6"
      >
        <div className="w-full max-w-md">{children}</div>
      </main>

      <footer className="px-4 py-6 text-center text-sm text-slate-600">
        © {new Date().getFullYear()} SkyRecom
      </footer>
    </div>
  );
}