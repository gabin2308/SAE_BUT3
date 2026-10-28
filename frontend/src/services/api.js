// src/services/api.js
// Même origine grâce au proxy (Vite en dev, rewrites Vercel en prod) :
// les cookies HttpOnly fonctionnent sans CORS, et le cookie csrf_token posé par
// le backend (non HttpOnly) est lisible via document.cookie.
const BASE = "/api";

// ---------------------------------------------------------------------------
// CSRF (double-submit cookie) : le cookie est la seule source de vérité.
// Il est partagé entre onglets, donc toujours à jour après un refresh dans
// un autre onglet. Il expire en même temps que l'access token (30 min).
// ---------------------------------------------------------------------------
function lireCookie(nom) {
  const ligne = document.cookie.split("; ").find((r) => r.startsWith(`${nom}=`));
  return ligne ? decodeURIComponent(ligne.slice(nom.length + 1)) : null;
}

export function getCsrfToken() {
  return lireCookie("csrf_token");
}

// ---------------------------------------------------------------------------
// Erreurs : FastAPI renvoie {"detail": "texte"} ou, pour les 422 Pydantic,
// {"detail": [{loc, msg, type}, ...]}.
// ---------------------------------------------------------------------------
export class ApiError extends Error {
  constructor(message, { status, champs = null, code = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status; // 0 = serveur injoignable
    this.champs = champs; // { champ: [messages] } pour les erreurs de validation
    this.code = code; // ex. "compte_non_active" (connexion avant activation, US2)
  }
}

function lireErreur(parsed, status) {
  // Dépassement de quota (slowapi) : corps {"error": "..."} sans "detail"
  if (status === 429) {
    return new ApiError("Trop de tentatives. Réessayez dans une minute.", { status });
  }

  const code = parsed?.code ?? null;
  const detail = parsed?.detail;

  if (typeof detail === "string") return new ApiError(detail, { status, code });

  // 422 Pydantic : liste [{ loc, msg, type }]
  if (Array.isArray(detail)) {
    const champs = {};
    for (const d of detail) {
      const champ = String(d.loc?.[d.loc.length - 1] ?? "global");
      // Pydantic préfixe les ValueError des validators par "Value error, "
      const msg = String(d.msg ?? "").replace(/^Value error, /, "");
      (champs[champ] ??= []).push(msg);
    }
    const premier = Object.values(champs).flat()[0];
    return new ApiError(premier || "Données invalides", { status, champs, code });
  }

  // 400 ValidationError métier : { champ: [messages] }
  if (detail && typeof detail === "object") {
    const premier = Object.values(detail).flat()[0];
    return new ApiError(String(premier ?? "Données invalides"), {
      status,
      champs: detail,
      code,
    });
  }

  return new ApiError(`Erreur ${status}`, { status, code });
}

// Session expirée : on prévient AuthContext (qui remet user à null)
function sessionExpiree() {
  window.dispatchEvent(new Event("auth:expired"));
  return new ApiError("SESSION_EXPIRED", { status: 401 });
}

// Routes accessibles sans session : un 401 y est une vraie réponse métier
// (identifiants faux), et elles n'ont pas de cookie CSRF à présenter.
// methodes : quand elle est indiquée, la route n'est publique que pour ces méthodes.
// À ALIGNER avec les routes réelles du backend SkyRecom.
const ROUTES_PUBLIQUES = [
  { chemin: "/auth/connexion" },
  { chemin: "/auth/rafraichir" },
  { chemin: "/utilisateurs/inscription" },
  { chemin: "/utilisateurs/activation" }, // couvre aussi /activation/renvoyer
  { chemin: "/utilisateurs/mot-de-passe-oublie" },
  { chemin: "/utilisateurs/reinitialisation" },
];
const estPublique = (url, method) =>
  ROUTES_PUBLIQUES.some(
    (r) => url.startsWith(r.chemin) && (!r.methodes || r.methodes.includes(method))
  );

// Routes protégées où un 401 est une vraie réponse métier (mot de passe saisi
// incorrect), pas une session expirée. Elles exigent toujours le jeton CSRF.
const ROUTES_401_METIER = ["/auth/changer-mot-de-passe"];
const est401Metier = (url) => ROUTES_401_METIER.some((r) => url.startsWith(r));

const METHODES_ECRITURE = ["POST", "PUT", "PATCH", "DELETE"];

// Un seul /rafraichir à la fois (plusieurs 401 simultanés, ou StrictMode en dev)
let refreshPromise = null;

export function doRefresh() {
  if (!refreshPromise) {
    const csrf = getCsrfToken();
    refreshPromise = fetch(`${BASE}/auth/rafraichir`, {
      method: "POST",
      credentials: "include",
      headers: csrf ? { "X-CSRF-Token": csrf } : {},
    })
      .then(async (res) => {
        if (!res.ok) throw new Error("REFRESH_FAILED");
        // Le backend renvoie { utilisateur, csrf_token } et repose les cookies
        return res.json();
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

export async function apiFetch(url, options = {}, _retry = false) {
  const method = (
    options.method || (options.body ? "POST" : "GET")
  ).toUpperCase();
  const ecriture = METHODES_ECRITURE.includes(method);

  // Le cookie CSRF expire avec l'access token (30 min). S'il manque sur une
  // écriture protégée, on rafraîchit d'abord : sinon le serveur répondrait 403
  // (CSRF) au lieu de 401, et le refresh automatique ne se déclencherait pas.
  if (ecriture && !estPublique(url, method) && !getCsrfToken()) {
    try {
      await doRefresh();
    } catch {
      throw sessionExpiree();
    }
  }

  const csrf = getCsrfToken();
  const estFormData = options.body instanceof FormData;

  let response;
  try {
    response = await fetch(`${BASE}${url}`, {
      ...options,
      method,
      credentials: "include",
      headers: {
        ...(options.body && !estFormData && { "Content-Type": "application/json" }),
        ...(ecriture && csrf && { "X-CSRF-Token": csrf }),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError("Impossible de joindre le serveur. Vérifiez votre connexion.", {
      status: 0,
    });
  }

  if (response.status === 401 && !estPublique(url, method) && !est401Metier(url)) {
    if (_retry) throw sessionExpiree();
    try {
      await doRefresh();
    } catch {
      throw sessionExpiree();
    }
    return apiFetch(url, options, true);
  }

  if (!response.ok) {
    let parsed = null;
    try {
      parsed = await response.json();
    } catch {
      /* corps non JSON */
    }
    throw lireErreur(parsed, response.status);
  }

  if (response.status === 204) return null;
  return response.json();
}

// Raccourcis : api.post("/auth/connexion", { email, mot_de_passe })
export const api = {
  get: (url) => apiFetch(url),
  post: (url, body) =>
    apiFetch(url, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  put: (url, body) =>
    apiFetch(url, { method: "PUT", body: JSON.stringify(body) }),
  patch: (url, body) =>
    apiFetch(url, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (url) => apiFetch(url, { method: "DELETE" }),
};