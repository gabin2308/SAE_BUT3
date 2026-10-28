import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthLayout from "../../components/layouts/AuthLayout";
import AuthCard from "../../components/ui/AuthCard";
import { utilisateurService } from "../../services/utilisateurService";

export default function ActivationCompte() {
  const [searchParams] = useSearchParams();
  const jeton = searchParams.get("jeton");

  const [statut, setStatut] = useState("chargement");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!jeton) {
      setStatut("erreur");
      setMessage("Le lien d'activation est invalide : aucun jeton fourni.");
      return;
    }

    let annule = false;

    async function activerCompte() {
      try {
        await utilisateurService.activerCompte(jeton);

        if (!annule) {
          setStatut("succes");
          setMessage("Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.");
        }
      } catch (erreur) {
        if (!annule) {
          setStatut("erreur");
          setMessage(
            erreur?.message ||
              "Le lien d'activation est invalide ou a expiré. Vous pouvez demander un nouveau lien."
          );
        }
      }
    }

    activerCompte();

    return () => {
      annule = true;
    };
  }, [jeton]);

  return (
    <AuthLayout>
      <AuthCard className="text-center">
        <h1 className="text-2xl font-bold text-slate-900">
          Activation du compte
        </h1>

        <div aria-live="polite" className="mt-4 text-sm">
          {statut === "chargement" && (
            <p>Activation de votre compte en cours...</p>
          )}

          {statut === "succes" && (
            <p className="text-green-700">{message}</p>
          )}

          {statut === "erreur" && (
            <p role="alert" className="text-red-700">{message}</p>
          )}
        </div>

        {statut === "succes" && (
          <Link
            to="/connexion"
            className="mt-6 inline-block rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Se connecter
          </Link>
        )}

        {statut === "erreur" && (
          <Link
            to="/connexion"
            className="mt-6 inline-block text-blue-600 hover:underline"
          >
            Retour à la connexion
          </Link>
        )}
      </AuthCard>
    </AuthLayout>
  );
}