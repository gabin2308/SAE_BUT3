// src/pages/publiques/Accueil.jsx  (US8, US9)
import FormulaireRecherche from "./recherche/FormulaireRecherche";
import { useAuth } from "../../context/AuthContext";

export default function Accueil() {
  const { user } = useAuth();

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <h1 className="text-3xl font-bold text-slate-900">Bonjour {user.prenom}</h1>
        <p className="mt-3 max-w-2xl text-base text-slate-600">
          Trouvez le vol qui vous correspond. Indiquez votre trajet et votre budget :
          nous classons les vols selon votre profil et vos préférences.
        </p>
      </section>

      <section aria-labelledby="titre-recherche" className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 id="titre-recherche" className="text-lg font-semibold text-slate-900">
            Rechercher un vol
          </h2>
          <div className="mt-5">
            <FormulaireRecherche />
          </div>
        </div>
      </section>
    </>
  );
}