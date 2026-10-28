// src/components/RootRedirect.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { cheminAccueil } from "../routes/cheminAccueil";

export default function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <p className="p-8 text-slate-600" role="status">
        Chargement…
      </p>
    );
  }
  return <Navigate to={user ? cheminAccueil(user.role) : "/"} replace />;
}