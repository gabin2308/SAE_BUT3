
/**
 * Validateurs front : doivent rester alignés sur les validators Pydantic du backend.
 * Le backend reste l'autorité : ici, on ne fait que prévenir l'utilisateur plus tôt.
 */
const EMAIL_REGEX = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
const NOM_REGEX = /^[A-Za-zÀ-ÖØ-öø-ÿ'’ -]+$/;

export const MAX_EMAIL_LEN = 254;
export const MAX_NOM_LEN = 50;
export const MIN_PASSWORD_LEN = 8;
export const MAX_PASSWORD_LEN = 128;

export function isValidEmail(email) {
  if (typeof email !== "string") return false;
  const e = email.trim();
  return e.length > 0 && e.length <= MAX_EMAIL_LEN && EMAIL_REGEX.test(e);
}

/** Nom ou prénom : lettres (accents inclus), espaces, tirets et apostrophes. */
export function isValidNom(nom) {
  if (typeof nom !== "string") return false;
  const n = nom.trim();
  return n.length > 0 && n.length <= MAX_NOM_LEN && NOM_REGEX.test(n);
}

export function getPasswordStrengthErrors(mdp) {
  const e = [];
  if (typeof mdp !== "string") return ["Mot de passe invalide."];
  if (mdp.length < MIN_PASSWORD_LEN) e.push(`${MIN_PASSWORD_LEN} caractères minimum.`);
  if (mdp.length > MAX_PASSWORD_LEN) e.push(`${MAX_PASSWORD_LEN} caractères maximum.`);
  if (!/[A-Z]/.test(mdp)) e.push("Au moins une majuscule.");
  if (!/[0-9]/.test(mdp)) e.push("Au moins un chiffre.");
  if (!/[!@#$%^&*()\-_=+[\]{};:,.<>?/\\|`~"']/.test(mdp))
    e.push("Au moins un caractère spécial.");
  return e;
}

export const isValidPassword = (p) => getPasswordStrengthErrors(p).length === 0;

/** Confirmation du mot de passe (réinitialisation, changement). */
export const motsDePasseIdentiques = (a, b) => typeof a === "string" && a === b;