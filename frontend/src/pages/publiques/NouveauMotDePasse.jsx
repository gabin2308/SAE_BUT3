// src/pages/publiques/NouveauMotDePasse.jsx
// Écran 7 : lien reçu par email, /reinitialisation?jeton=...
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import AuthLayout from "../../components/layouts/AuthLayout";
import AuthCard from "../../components/ui/AuthCard";
import Logo from "../../components/ui/Logo";
import ChampTexte from "../../components/ui/ChampTexte";
import { IconeCadenas } from "../../components/ui/Icones";
import { utilisateurService } from "../../services/utilisateurService";
import { lireErreurs } from "../../utils/erreurs";
import { getPasswordStrengthErrors, motsDePasseIdentiques } from "../../utils/validators";

function BoiteErreur({ children }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      {children}
    </div>
  );
}

export default function NouveauMotDePasse() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  // Le jeton est gardé en mémoire dès le premier rendu (accepte aussi ?token=)
  const [jeton] = useState(() => params.get("jeton") ?? params.get("token"));

  const [nouveau, setNouveau] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [erreurs, setErreurs] = useState({});
  const [erreurGlobale, setErreurGlobale] = useState("");
  const [chargement, setChargement] = useState(false);

  // Retire le jeton de la barre d'adresse (historique, en-tête Referer)
  useEffect(() => {
    if (jeton) navigate("/reinitialisation", { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function soumettre(e) {
    e.preventDefault();
    const err = {};
    const mdp = getPasswordStrengthErrors(nouveau);
    if (mdp.length) err.nouveau = mdp.join(" ");
    if (!motsDePasseIdentiques(nouveau, confirmation)) {
      err.confirmation = "Les mots de passe ne correspondent pas.";
    }
    setErreurs(err);
    setErreurGlobale("");
    if (Object.keys(err).length) return;

    setChargement(true);
    try {
      await utilisateurService.reinitialiserMotDePasse(jeton, nouveau);
      navigate("/connexion", {
        replace: true,
        state: { message: "Mot de passe modifié. Vous pouvez vous connecter." },
      });
    } catch (error) {
      setErreurGlobale(
        lireErreurs(error).global || "Ce lien n'est plus valable. Demandez-en un nouveau."
      );
    } finally {
      setChargement(false);
    }
  }

  // Lien sans jeton (ou page rechargée après nettoyage de l'URL)
  if (!jeton) {
    return (
      <AuthLayout>
        <AuthCard>
          <h1 className="text-center text-2xl font-bold text-slate-900">Lien incomplet</h1>
          <div className="mt-5 space-y-4 text-center">
            <BoiteErreur>
              Ce lien de réinitialisation est incomplet. Ouvrez le lien reçu par email.
            </BoiteErreur>
            <Link to="/mot-de-passe-oublie" className="block text-sm text-blue-600 hover:underline">
              Demander un nouveau lien
            </Link>
          </div>
        </AuthCard>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <AuthCard>
        <div className="flex justify-center">
          <Logo />
        </div>
        <h1 className="mt-6 text-center text-2xl font-bold text-slate-900">Nouveau mot de passe</h1>
        <p className="mt-2 text-center text-sm text-slate-600">
          Choisissez un nouveau mot de passe pour sécuriser votre compte.
        </p>

        {erreurGlobale && (
          <div className="mt-5 space-y-2">
            <BoiteErreur>{erreurGlobale}</BoiteErreur>
            <Link to="/mot-de-passe-oublie" className="block text-sm text-blue-600 hover:underline">
              Demander un nouveau lien
            </Link>
          </div>
        )}

        <form onSubmit={soumettre} noValidate className="mt-6 space-y-4">
          <ChampTexte
            label="Nouveau mot de passe"
            type="password"
            icone={<IconeCadenas />}
            placeholder="Votre nouveau mot de passe"
            autoComplete="new-password"
            value={nouveau}
            onChange={(e) => setNouveau(e.target.value)}
            erreur={erreurs.nouveau}
          />
          <ChampTexte
            label="Confirmez le mot de passe"
            type="password"
            icone={<IconeCadenas />}
            placeholder="Confirmez votre mot de passe"
            autoComplete="new-password"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            erreur={erreurs.confirmation}
          />
          <button
            type="submit"
            disabled={chargement}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:opacity-60"
          >
            {chargement ? "Enregistrement…" : "Réinitialiser le mot de passe"}
          </button>
        </form>
      </AuthCard>
    </AuthLayout>
  );
}