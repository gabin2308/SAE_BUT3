// src/pages/authentification/ActivationCompte.jsx  (écran 8 du storyboard)
// Lien reçu par email : /activation?jeton=...
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthLayout from "../../components/layouts/AuthLayout";
import AuthCard from "../../components/ui/AuthCard";
import Logo from "../../components/ui/Logo";
import { utilisateurService } from "../../services/utilisateurService";

const MESSAGE_JETON_ABSENT = "Le lien d’activation est invalide : aucun jeton fourni.";
const MESSAGE_PAR_DEFAUT =
  "Le lien d’activation est invalide ou a expiré. Connectez-vous pour recevoir un nouveau lien.";

const boutonPrincipal =
  "mt-6 inline-flex w-full items-center justify-center rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2";

export default function ActivationCompte() {
  const [searchParams] = useSearchParams();
  const jeton = searchParams.get("jeton");

  const [statut, setStatut] = useState(jeton ? "chargement" : "erreur");
  const [message, setMessage] = useState(jeton ? "" : MESSAGE_JETON_ABSENT);

  // Le jeton ne sert qu'une fois : en développement, StrictMode exécute l'effet deux fois.
  // Cette référence empêche le second appel (qui échouerait et masquerait le succès).
  const lance = useRef(false);

  useEffect(() => {
    if (!jeton || lance.current) return;
    lance.current = true;

    utilisateurService
      .activerCompte(jeton)
      .then(() => setStatut("succes"))
      .catch((erreur) => {
        setMessage(erreur?.message || MESSAGE_PAR_DEFAUT);
        setStatut("erreur");
      });
  }, [jeton]);

  return (
    <AuthLayout>
      <AuthCard className="text-center">
        <div aria-live="polite">
          {statut === "chargement" && (
            <>
              <h1 className="text-2xl font-bold text-slate-900">Activation en cours…</h1>
              <p className="mt-3 text-sm text-slate-600">Merci de patienter quelques instants.</p>
            </>
          )}

          {statut === "succes" && (
            <>
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500 text-white">
                <svg viewBox="0 0 24 24" aria-hidden="true" className="h-9 w-9" fill="none"
                  stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m5 12 5 5 9-10" />
                </svg>
              </div>
              <h1 className="mt-6 text-2xl font-bold text-slate-900">Votre compte est activé !</h1>
              <p className="mt-3 text-sm text-slate-600">
                Félicitations, votre adresse email a bien été confirmée. Vous pouvez maintenant
                vous connecter et profiter de toutes les fonctionnalités de SkyRecom.
              </p>
              <Link to="/connexion" className={boutonPrincipal}>Se connecter</Link>
              <p className="mt-4 text-sm">
                <Link to="/" className="text-blue-600 hover:underline">Retour à l’accueil</Link>
              </p>
              <div className="mt-8 flex justify-center">
                <Logo />
              </div>
            </>
          )}

          {statut === "erreur" && (
            <>
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-500 text-white">
                <svg viewBox="0 0 24 24" aria-hidden="true" className="h-9 w-9" fill="none"
                  stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 6l12 12M18 6 6 18" />
                </svg>
              </div>
              <h1 className="mt-6 text-2xl font-bold text-slate-900">Activation impossible</h1>
              <p role="alert" className="mt-3 text-sm text-red-700">{message}</p>
              <Link to="/connexion" className={boutonPrincipal}>Retour à la connexion</Link>
              <p className="mt-4 text-sm">
                <Link to="/" className="text-blue-600 hover:underline">Retour à l’accueil</Link>
              </p>
            </>
          )}
        </div>
      </AuthCard>
    </AuthLayout>
  );
}