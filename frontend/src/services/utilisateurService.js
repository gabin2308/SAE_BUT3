// src/services/utilisateurService.js
// Miroir du UtilisateurController (préfixe /utilisateurs). api.js préfixe déjà "/api".
// Connexion, rafraîchissement, /auth/moi, déconnexion et changement de mot de passe
// restent dans authService.js.
import { apiFetch } from "./api";

const BASE = "/utilisateurs";

export const utilisateurService = {
  // ─────────────────────────────────────────
  // ROUTES PUBLIQUES (pas de cookie, pas de CSRF)
  // ─────────────────────────────────────────

  // US1 : le compte est créé inactif, aucune session n'est ouverte.
  // La politique de confidentialité est obligatoire côté interface uniquement :
  // le backend ne reçoit que les deux consentements facultatifs.
  inscription: async ({
    nom,
    prenom,
    email,
    mot_de_passe,
    consentement_politique,
    consentement_personnalisation = false,
    consentement_localisation = false,
  }) => {
    return await apiFetch(`${BASE}/inscription`, {
      method: "POST",
      body: JSON.stringify({
        nom,
        prenom,
        email,
        mot_de_passe,
        consentement_politique,
        consentement_personnalisation,
        consentement_localisation,
      }),
    });
  },

  // US2 : lien reçu par email (/activation?token=...). Envoyé en POST pour qu'un
  // scanner d'emails qui suit le lien ne consomme pas le jeton.
  activerCompte: async (jeton) => {
    return await apiFetch(`${BASE}/activation`, {
      method: "POST",
      body: JSON.stringify({ jeton }),
    });
  },

  // Réponse identique que l'email existe ou non.
  renvoyerActivation: async (email) => {
    return await apiFetch(`${BASE}/activation/renvoyer`, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  // US4 : réponse identique que l'email existe ou non (pas de fuite d'information).
  motDePasseOublie: async (email) => {
    return await apiFetch(`${BASE}/mot-de-passe-oublie`, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  reinitialiserMotDePasse: async (jeton, nouveau_mot_de_passe) => {
    return await apiFetch(`${BASE}/reinitialisation`, {
      method: "POST",
      body: JSON.stringify({ jeton, nouveau_mot_de_passe }),
    });
  },

  // ─────────────────────────────────────────
  // ROUTES AUTHENTIFIÉES (cookie + CSRF géré par apiFetch)
  // ─────────────────────────────────────────

  // Seuls les champs présents dans `champs` sont modifiés (exclude_unset côté backend).
  // Renvoie l'utilisateur à jour : à passer à mettreAJourUser() du AuthContext.
  modifierProfil: async (champs) => {
    return await apiFetch(`${BASE}/moi`, {
      method: "PATCH",
      body: JSON.stringify(champs),
    });
  },

  lireConsentements: async () => {
    return await apiFetch(`${BASE}/moi/consentements`);
  },

  // type : le nom du consentement attendu par le backend (ex. "personnalisation",
  // "localisation") ; accorde : booléen. Renvoie tous les consentements à jour.
  modifierConsentement: async (type, accorde) => {
    return await apiFetch(`${BASE}/moi/consentements`, {
      method: "PUT",
      body: JSON.stringify({ type, accorde }),
    });
  },

  terminerOnboarding: async () => {
    return await apiFetch(`${BASE}/moi/onboarding`, { method: "POST" });
  },
};