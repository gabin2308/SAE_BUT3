// src/services/aeroportService.js
// Miroir de l'AeroportController (préfixe /aeroports). api.js préfixe déjà "/api".
import { apiFetch } from "./api";

const BASE = "/aeroports";

export const aeroportService = {
  // ─────────────────────────────────────────
  // ROUTES AUTHENTIFIÉES (cookie ; les GET n'ont pas de CSRF)
  // ─────────────────────────────────────────

  // Autocomplétion (US9). Renvoie [{ code_iata, nom, ville, code_pays, pays,
  // libelle, latitude, longitude }]. Le backend refuse q < 2 caractères (422) :
  // ne pas appeler avant. `signal` (AbortController) permet d'annuler la
  // requête précédente quand l'utilisateur continue de taper.
  rechercher: async (q, { limite = 10, signal } = {}) => {
    const params = new URLSearchParams({ q, limite: String(limite) });
    return await apiFetch(`${BASE}?${params}`, { signal });
  },

  // Liste des pays (≈ 250 lignes), pour une recherche par pays de destination.
  lireTousLesPays: async () => {
    return await apiFetch(`${BASE}/pays`);
  },
};