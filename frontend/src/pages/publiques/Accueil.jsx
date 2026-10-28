// src/pages/Accueil.jsx — page protégée provisoire (tous rôles) (valide garde de route + déconnexion)
import AuthLayout from "../../components/layouts/AuthLayout";
import { useAuth } from "../../context/AuthContext";

export default function Accueil() {
  const { user, logout } = useAuth();

  return (
    <AuthLayout>
      <section className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <h1 className="text-3xl font-extrabold text-marine">Bonjour {user.prenom}</h1>
        <p className="mt-3 text-base text-slate-600">
          Rôle : <span className="font-semibold text-encre">{user.role}</span> · Second facteur :{" "}
          <span className="font-semibold text-encre">{user.totp_actif ? "actif" : "non activé"}</span>
        </p>
        <button
          type="button"
          onClick={logout}
          className="mt-8 inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-300 px-6 py-3 font-semibold text-marine hover:bg-slate-50"
        >
          Se déconnecter
        </button>
      </section>
    </AuthLayout>
  );
}
