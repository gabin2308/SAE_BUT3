// src/pages/publiques/VerificationEmail.jsx  (écran 3 du storyboard)
// Affichée après l'inscription : l'email arrive par navigate(..., { state: { email } }).
import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import AuthLayout from "../../components/layouts/AuthLayout";
import AuthCard from "../../components/ui/AuthCard";
import { IconeEnveloppe } from "../../components/ui/Icones";
import { utilisateurService } from "../../services/utilisateurService";

export default function VerificationEmail() {
  const { state } = useLocation();
  const email = state?.email;
  const [statut, setStatut] = useState(null); // null | "envoi" | "ok" | message d'erreur

  // Arrivée directe sur l'URL (rechargement, lien partagé) : rien à afficher
  if (!email) return <Navigate to="/connexion" replace />;

  const renvoyer = async () => {
    setStatut("envoi");
    try {
      await utilisateurService.renvoyerActivation(email);
      setStatut("ok");
    } catch (err) {
      setStatut(err?.message || "L’envoi a échoué. Réessayez dans un instant.");
    }
  };

  return (
    <AuthLayout>
      <AuthCard className="text-center">
        <div className="relative mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-blue-50 text-blue-600">
          <span className="scale-150">
            <IconeEnveloppe />
          </span>
          <span
            aria-hidden="true"
            className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500 text-white"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="m5 12 5 5 9-10" />
            </svg>
          </span>
        </div>

        <h1 className="mt-6 text-2xl font-bold text-slate-900">Vérifiez votre boîte mail</h1>
        <p className="mt-3 text-sm text-slate-700">
          Nous venons de vous envoyer un lien de confirmation à l’adresse{" "}
          <strong className="break-all">{email}</strong>.
        </p>
        <p className="mt-3 text-sm text-slate-700">
          Ce lien est valable 24 heures. Si vous ne le recevez pas, vous pouvez demander un
          nouvel envoi.
        </p>

        <div aria-live="polite" className="mt-4 min-h-5 text-sm">
          {statut === "ok" && (
            <p className="text-green-700">Un nouvel email vient d’être envoyé.</p>
          )}
          {statut && statut !== "ok" && statut !== "envoi" && (
            <p role="alert" className="text-red-700">{statut}</p>
          )}
        </div>

        <button
          type="button"
          onClick={renvoyer}
          disabled={statut === "envoi"}
          className="mt-2 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:opacity-60"
        >
          {statut === "envoi" ? "Envoi…" : "Renvoyer l’email"}
        </button>

        <p className="mt-5 text-sm">
          <Link to="/connexion" className="text-blue-600 hover:underline">
            Retour à la page de connexion
          </Link>
        </p>
      </AuthCard>
    </AuthLayout>
  );
}