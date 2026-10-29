// src/pages/publiques/Connexion.jsx  (écran 4 du storyboard)
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthLayout from "../../components/layouts/AuthLayout";
import AuthCard from "../../components/ui/AuthCard";
import Logo from "../../components/ui/Logo";
import ChampTexte from "../../components/ui/ChampTexte";
import { IconeEnveloppe, IconeCadenas } from "../../components/ui/Icones";
import { useAuth } from "../../context/AuthContext";
import { utilisateurService } from "../../services/utilisateurService";
import { isValidEmail } from "../../utils/validators";

const MESSAGES = {
  compte_non_active:
    "Votre compte n’est pas encore activé. Cliquez sur le lien reçu par email.",
  identifiants_invalides: "Email ou mot de passe incorrect.",
  trop_de_tentatives: "Trop de tentatives. Réessayez dans une minute.",
};

// Le backend renvoie { detail } sans code : on déduit le cas depuis le statut HTTP.
// 403 = compte non activé (à confirmer : AccesRefuseError levée par authentifier()).
function deduireCode(res) {
  if (res?.code === "compte_non_active" || res?.status === 403) return "compte_non_active";
  if (res?.status === 429) return "trop_de_tentatives";
  if (res?.status === 401) return "identifiants_invalides";
  return res?.code ?? "erreur";
}
const MESSAGE_PAR_DEFAUT = "Connexion impossible pour le moment. Réessayez dans un instant.";

export default function Connexion() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const destination = location.state?.from?.pathname ?? "/accueil";

  // Message de succès transmis par une autre page (ex. mot de passe modifié)
  const [messageSucces] = useState(() => location.state?.message ?? null);

  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreurs, setErreurs] = useState({});
  const [codeErreur, setCodeErreur] = useState(null);
  const [messageErreur, setMessageErreur] = useState(null);
  const [envoi, setEnvoi] = useState(false);
  const [renvoi, setRenvoi] = useState(null); // null | "envoi" | "ok" | "erreur"

  const soumettre = async (e) => {
    e.preventDefault();
    const nouvelles = {};
    if (!isValidEmail(email)) nouvelles.email = "Entrez une adresse email valide.";
    if (!motDePasse) nouvelles.motDePasse = "Entrez votre mot de passe.";
    setErreurs(nouvelles);
    setCodeErreur(null);
    setMessageErreur(null);
    setRenvoi(null);
    if (Object.keys(nouvelles).length) return;

    setEnvoi(true);
    // login ne lève pas : il renvoie { success: true } ou { error, status, code }
    const res = await login(email.trim(), motDePasse);
    if (res?.success) {
      navigate(destination, { replace: true });
    } else {
      setCodeErreur(deduireCode(res));
      setMessageErreur(typeof res?.error === "string" ? res.error : null);
    }
    setEnvoi(false);
  };

  const renvoyerEmail = async () => {
    setRenvoi("envoi");
    try {
      await utilisateurService.renvoyerActivation(email.trim());
      setRenvoi("ok");
    } catch {
      setRenvoi("erreur");
    }
  };

  return (
    <AuthLayout>
      <AuthCard>
        <div className="flex justify-center">
          <Logo />
        </div>
        <h1 className="mt-6 text-center text-2xl font-bold text-slate-900">Se connecter</h1>
        <p className="mt-2 text-center text-sm text-slate-600">
          Bon retour ! Connectez-vous pour accéder à votre compte.
        </p>

        {messageSucces && (
          <p
            role="status"
            className="mt-5 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800"
          >
            {messageSucces}
          </p>
        )}

        <div aria-live="polite">
          {codeErreur && (
            <div
              role="alert"
              className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800"
            >
              <p>{MESSAGES[codeErreur] ?? messageErreur ?? MESSAGE_PAR_DEFAUT}</p>
              {codeErreur === "compte_non_active" && (
                <button
                  type="button"
                  onClick={renvoyerEmail}
                  disabled={renvoi === "envoi" || !isValidEmail(email)}
                  className="mt-2 font-medium text-blue-700 hover:underline disabled:opacity-50"
                >
                  Renvoyer l’email
                </button>
              )}
            </div>
          )}
          {renvoi === "ok" && (
            <p className="mt-3 text-sm text-green-700">
              Si ce compte existe, un nouvel email d’activation vient d’être envoyé.
            </p>
          )}
          {renvoi === "erreur" && (
            <p className="mt-3 text-sm text-red-700">
              L’envoi a échoué. Réessayez dans un instant.
            </p>
          )}
        </div>

        <form onSubmit={soumettre} noValidate className="mt-6 space-y-4">
          <ChampTexte
            label="Email"
            type="email"
            icone={<IconeEnveloppe />}
            placeholder="exemple@email.com"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            erreur={erreurs.email}
          />
          <ChampTexte
            label="Mot de passe"
            type="password"
            icone={<IconeCadenas />}
            placeholder="Votre mot de passe"
            autoComplete="current-password"
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            erreur={erreurs.motDePasse}
          />

          <div className="text-right">
            <Link to="/mot-de-passe-oublie" className="text-sm text-blue-600 hover:underline">
              Mot de passe oublié ?
            </Link>
          </div>

          <button
            type="submit"
            disabled={envoi}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:opacity-60"
          >
            {envoi ? "Connexion…" : "Se connecter"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          Vous n’avez pas de compte ?{" "}
          <Link to="/inscription" className="text-blue-600 hover:underline">
            Créer un compte
          </Link>
        </p>
      </AuthCard>
    </AuthLayout>
  );
}