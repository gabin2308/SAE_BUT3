// src/services/authService.js
import { apiFetch, doRefresh } from "./api";

const BASE = "/auth"; // api.js préfixe déjà "/api"

export const authService = {

  // ─────────────────────────────────────────
  // CONNEXION (US3)
  // ─────────────────────────────────────────
  login: async (email, mot_de_passe) => {
    // Le backend renvoie { utilisateur, csrf_token } et pose access_token,
    // refresh_token (HttpOnly) et csrf_token (lisible) en cookies.
    return await apiFetch(`${BASE}/connexion`, {
      method: "POST",
      body: JSON.stringify({ email, mot_de_passe }),
    });
  },

  // ─────────────────────────────────────────
  // RAFRAÎCHISSEMENT DE SESSION
  // ─────────────────────────────────────────
  refresh: async () => {
    // Passe par doRefresh (une seule requête même si plusieurs appels
    // simultanés). Renvoie { utilisateur, csrf_token } : pas besoin d'appeler
    // me() ensuite.
    return await doRefresh();
  },

  // ─────────────────────────────────────────
  // PROFIL UTILISATEUR
  // ─────────────────────────────────────────
  me: async () => {
    return await apiFetch(`${BASE}/moi`);
  },

  // ─────────────────────────────────────────
  // MON COMPTE (US6, US25)
  // ─────────────────────────────────────────
  changePassword: async (ancien_mot_de_passe, nouveau_mot_de_passe) => {
    // Renvoie { utilisateur, csrf_token } : la session courante est réémise
    return await apiFetch(`${BASE}/changer-mot-de-passe`, {
      method: "POST",
      body: JSON.stringify({ ancien_mot_de_passe, nouveau_mot_de_passe }),
    });
  },

  // Supprime le compte et toutes les données personnelles (cascade côté base)
//   supprimerCompte: async (mot_de_passe) => {
//     return await apiFetch(`/compte/suppression`, {
//       method: "POST",
//       body: JSON.stringify({ mot_de_passe }),
//     });
//   },

  // ─────────────────────────────────────────
  // DÉCONNEXION (US3)
  // ─────────────────────────────────────────
  logout: async () => {
    try {
      await apiFetch(`${BASE}/deconnexion`, { method: "POST" });
    } catch {
      // Session déjà expirée ou serveur injoignable : AuthContext vide
      // quand même user. Le backend supprime les cookies via Set-Cookie.
    }
  },
};