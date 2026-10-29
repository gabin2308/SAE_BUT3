// src/utils/erreurs.js

const MESSAGE_PAR_DEFAUT = "Une erreur est survenue. Veuillez réessayer.";

function aplatir(valeur) {
  if (!valeur) return [];
  if (typeof valeur === "string") return [valeur];
  if (Array.isArray(valeur)) return valeur.flatMap(aplatir);
  if (typeof valeur === "object") return Object.values(valeur).flatMap(aplatir);
  return [String(valeur)];
}

/**
 * Retourne { global: "message général", champs: { email: "...", ... } }
 */
export function lireErreurs(erreur) {
  // Serveur injoignable
  if (erreur?.request && !erreur?.response) {
    return { global: "Impossible de contacter le serveur.", champs: {} };
  }

  const data = erreur?.response?.data;

  // Erreurs par champ : { errors: { email: ["..."] } } ou { email: ["..."] }
  const brut = data?.errors ?? data?.erreurs;
  const champs = {};
  if (brut && typeof brut === "object" && !Array.isArray(brut)) {
    for (const [nom, msgs] of Object.entries(brut)) {
      const premier = aplatir(msgs)[0];
      if (premier) champs[nom] = premier;
    }
  }

  // Message global
  const global =
    aplatir(data?.message)[0] ??
    aplatir(data?.detail)[0] ??
    aplatir(data?.error)[0] ??
    aplatir(data?.erreur)[0] ??
    Object.values(champs)[0] ??
    erreur?.message ??
    MESSAGE_PAR_DEFAUT;

  return { global, champs };
}