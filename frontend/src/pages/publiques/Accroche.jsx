import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import Logo from "../../components/ui/Logo";
import { LienBouton } from "../../components/ui/Button";
import { useAuth } from "../../context/AuthContext";
import { cheminAccueil } from "../../routes/cheminAccueil";

// Écran 1 : page d'accroche publique (US7). Fichier autonome : le décor est défini plus bas.
// Fond : décor SVG par défaut ; dépose une photo dans public/hero.jpg pour la remplacer.
export default function Accroche() {
  const [photo, setPhoto] = useState(true);
  const { user, loading } = useAuth();

  if (loading) {
    return <p className="p-8 text-slate-600" role="status">Chargement…</p>;
  }
  if (user) {
    return <Navigate to={cheminAccueil(user.role)} replace />;
  }

  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden text-white">
      <DecorCiel className="absolute inset-0" />
      {photo && (
        <img src="/hero.jpg" alt="" onError={() => setPhoto(false)}
          className="absolute inset-0 h-full w-full object-cover" />
      )}
      

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between gap-2 px-4 py-4 sm:px-6 sm:py-5">
        <Logo clair className="[&_span:last-child]:text-lg sm:[&_span:last-child]:text-2xl" />
        <nav className="flex items-center gap-3 whitespace-nowrap text-xs sm:gap-4 sm:text-sm">
          <Link to="/connexion" className="hidden hover:underline sm:inline">Se connecter</Link>
          <Link to="/inscription"
            className="rounded-md border border-white/70 px-3 py-1.5 font-semibold hover:bg-white/10 sm:px-4 sm:py-2">
            Créer un compte
          </Link>
        </nav>
      </header>

      <section className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 pb-10 pt-[14vh]">
        <h1 className="max-w-xl text-4xl font-bold leading-tight sm:text-5xl">
          Trouvez le vol parfait,<br />selon vos envies
        </h1>
        <p className="mt-5 max-w-md text-base text-white/90">
          Des recommandations intelligentes pour découvrir les meilleurs vols, au meilleur prix.
        </p>
        <div className="mt-auto flex flex-wrap gap-3 pt-10 lg:mt-8 lg:pt-0">
          <LienBouton to="/inscription">Créer un compte</LienBouton>
          <LienBouton to="/connexion" variant="outline">Se connecter</LienBouton>
        </div>
      </section>
    </main>
  );
}

// ---------------------------------------------------------------------------
// Décor : ciel en dégradé (CSS) + aile d'avion et nuages (SVG), sans photo.
// Le ciel remplit tout l'écran ; l'aile reste ancrée en bas à droite, sans passer sous le texte.
// ---------------------------------------------------------------------------
function DecorCiel({ className = "" }) {
  return (
    <div aria-hidden="true"
      className={`bg-gradient-to-b from-[#0a2a5e] from-0% via-[#2d62ad] via-50% to-[#e3a083] to-100% ${className}`}>
      <svg viewBox="0 0 400 500" preserveAspectRatio="xMaxYMax meet"
        className="absolute bottom-0 right-0 h-[62%] w-full">
        <defs>
          <linearGradient id="aile" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#233f6b" />
            <stop offset="0.6" stopColor="#4a6f9f" />
            <stop offset="1" stopColor="#8fb0d6" />
          </linearGradient>
          <filter id="flou" x="-20%" y="-50%" width="140%" height="200%">
            <feGaussianBlur stdDeviation="9" />
          </filter>
        </defs>
        {/* aile et ailette */}
        <path d="M-10 242 C90 256 200 264 312 240 L346 178 C351 171 360 175 358 184 L338 266 C240 298 110 304 -10 298 Z"
          fill="url(#aile)" />
        <path d="M-10 242 C90 256 200 264 312 240 L346 178" fill="none"
          stroke="#cfe0f5" strokeOpacity="0.55" strokeWidth="1.5" />
        {/* volets et nervures, pour donner du relief à l'aile */}
        <g stroke="#cfe0f5" strokeOpacity="0.35" strokeWidth="1" fill="none">
          <path d="M40 262 C120 272 210 276 300 258" />
          <path d="M70 282 C140 290 220 292 320 276" />
          <path d="M120 250 L124 296 M200 254 L204 300 M270 246 L276 290" />
        </g>
        <path d="M-10 298 C110 304 240 298 338 266 L340 278 C240 316 110 322 -10 316 Z" fill="#162b4d" opacity="0.55" />
        {/* nuages */}
        <g filter="url(#flou)" opacity="0.85">
          <ellipse cx="70" cy="440" rx="140" ry="28" fill="#e9c4bf" />
          <ellipse cx="260" cy="458" rx="180" ry="32" fill="#f3c9b0" />
          <ellipse cx="380" cy="400" rx="90" ry="20" fill="#d9b3b8" opacity="0.8" />
          <ellipse cx="150" cy="350" rx="120" ry="14" fill="#9fb8d8" opacity="0.5" />
          <ellipse cx="200" cy="505" rx="260" ry="34" fill="#f3c9b0" />
        </g>
      </svg>
    </div>
  );
}
