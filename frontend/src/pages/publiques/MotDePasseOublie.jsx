import { useState } from "react";
import { Link } from "react-router-dom";
import AuthLayout from "../../components/layouts/AuthLayout";
import AuthCard from "../../components/ui/AuthCard";
import Logo from "../../components/ui/Logo";
import ChampTexte from "../../components/ui/ChampTexte";
import { IconeEnveloppe } from "../../components/ui/Icones";
import { LienBouton } from "../../components/ui/Button";
import { utilisateurService } from "../../services/utilisateurService";
import { lireErreurs } from "../../utils/erreurs";
import { isValidEmail } from "../../utils/validators";

export default function MotDePasseOublie() {
  const [email, setEmail] = useState("");
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(false);
  const [envoye, setEnvoye] = useState(false);

  async function soumettre(e) {
    e.preventDefault();
    setErreur("");
    if (!isValidEmail(email)) {
      setErreur("Saisissez une adresse email valide.");
      return;
    }
    setChargement(true);
    try {
      await utilisateurService.motDePasseOublie(email.trim());
      setEnvoye(true);
    } catch (error) {
      setErreur(lireErreurs(error).global);
    } finally {
      setChargement(false);
    }
  }

  // Écran 6 : même message que l'adresse existe ou non
  if (envoye) {
    return (
      <AuthLayout>
        <AuthCard>
          <h1 className="text-center text-2xl font-bold text-slate-900">
            Un lien vous a été envoyé
          </h1>
          <p className="mt-3 text-center text-sm text-slate-600">
            Si un compte existe avec cette adresse email, vous recevrez un lien de
            réinitialisation dans les prochaines minutes.
          </p>
          <LienBouton to="/connexion" className="mt-6 w-full">
            Retour à la connexion
          </LienBouton>
        </AuthCard>
      </AuthLayout>
    );
  }

  // Écran 5
  return (
    <AuthLayout>
      <AuthCard>
        <div className="flex justify-center"><Logo /></div>
        <h1 className="mt-6 text-center text-2xl font-bold text-slate-900">
          Réinitialiser votre mot de passe
        </h1>
        <p className="mt-2 text-center text-sm text-slate-600">
          Entrez votre adresse email et nous vous enverrons un lien pour
          réinitialiser votre mot de passe.
        </p>

        {erreur && (
          <div role="alert" className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            {erreur}
          </div>
        )}

        <form onSubmit={soumettre} noValidate className="mt-6 space-y-4">
          <ChampTexte
            label="Email"
            type="email"
            icone={<IconeEnveloppe />}
            placeholder="exemple@email.com"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            type="submit"
            disabled={chargement}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {chargement ? "Envoi…" : "Envoyer le lien"}
          </button>
          <Link to="/connexion" className="block text-center text-sm text-blue-600 hover:underline">
            Retour à la connexion
          </Link>
        </form>
      </AuthCard>
    </AuthLayout>
  );
}