// src/hooks/usePermissions.js
import { useMemo } from "react";
import { useAuth } from "../context/AuthContext";
import { ROLES } from "../constants/roles";

// Affichage uniquement : la vraie protection reste côté backend.
export const usePermissions = () => {
  const { user } = useAuth();
  const role = user?.role ?? null;

  return useMemo(
    () => ({
      role,
      isUtilisateur: role === ROLES.UTILISATEUR,
      isEvaluateur: role === ROLES.EVALUATEUR,
      // hasRole("utilisateur", "evaluateur") pour les gardes de route
      hasRole: (...roles) => role !== null && roles.includes(role),
    }),
    [role]
  );
};