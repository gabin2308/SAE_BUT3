// src/components/RequireAuth.jsx
// Garde de route : <Route element={<RequireAuth roles={["administrateur"]} />}>
// Affichage uniquement : la vraie protection reste côté backend.
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { usePermissions } from "../hooks/usePermissions";

export default function RequireAuth({ roles }) {
  const { user, loading } = useAuth();
  const { hasRole } = usePermissions();
  const location = useLocation();

  if (loading) {
    return (
      <p className="p-8 text-slate-600" role="status">
        Chargement…
      </p>
    );
  }

  if (!user) {
    return <Navigate to="/connexion" state={{ from: location }} replace />;
  }

  if (roles && !hasRole(...roles)) {
    return (
      <p className="p-8 font-semibold text-erreur" role="alert">
        Accès refusé : votre rôle ne permet pas de consulter cette page.
      </p>
    );
  }

  return <Outlet />;
}