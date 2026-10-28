/* eslint-disable react-refresh/only-export-components */
// src/context/AuthContext.jsx
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { authService } from "../services/authService";
import { ApiError } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Au chargement : un seul appel. /auth/rafraichir valide la session (cookie
  // HttpOnly refresh_token), repose les cookies (dont le CSRF) et renvoie
  // déjà l'utilisateur : inutile d'appeler /auth/moi ensuite.
  useEffect(() => {
    let annule = false;
    (async () => {
      try {
        const data = await authService.refresh();
        if (!annule) setUser(data?.utilisateur ?? null);
      } catch {
        // Pas de session active : cas normal pour un visiteur non connecté
        if (!annule) setUser(null);
      } finally {
        if (!annule) setLoading(false);
      }
    })();
    return () => {
      annule = true;
    };
  }, []);

  // Session expirée détectée par apiFetch n'importe où dans l'appli
  useEffect(() => {
    const onExpire = () => setUser(null);
    window.addEventListener("auth:expired", onExpire);
    return () => window.removeEventListener("auth:expired", onExpire);
  }, []);

  const login = useCallback(async (email, motDePasse) => {
    try {
      const res = await authService.login(email, motDePasse);
      if (res?.utilisateur) {
        setUser(res.utilisateur);
        return { success: true };
      }
      return { error: "Identifiants invalides" };
    } catch (err) {
      // Message métier du backend si ApiError, sinon message générique
      const estApi = err instanceof ApiError;
      return {
        error: estApi
          ? err.message
          : "Une erreur est survenue. Réessayez plus tard.",
        status: estApi ? err.status : null,
        code: estApi ? err.code : null, // ex. "compte_non_active" : proposer le renvoi du lien (US2)
      };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
    }
  }, []);

  /** Re-synchronise l'utilisateur courant depuis le serveur */
  const refreshUser = useCallback(async () => {
    try {
      const data = await authService.me();
      setUser(data?.id ? data : null);
      return data;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  /** Met à jour user avec une réponse déjà reçue (changement de mot de passe, préférences) */
  const mettreAJourUser = useCallback((utilisateur) => {
    if (utilisateur?.id) setUser(utilisateur);
  }, []);

  /** US25 : supprime le compte, puis vide la session côté interface */
  const supprimerCompte = useCallback(async (motDePasse) => {
    await authService.supprimerCompte(motDePasse); // lève ApiError si mot de passe faux
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshUser, mettreAJourUser, supprimerCompte }),
    [user, loading, login, logout, refreshUser, mettreAJourUser, supprimerCompte]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth doit être utilisé à l'intérieur d'un <AuthProvider>");
  }
  return context;
};