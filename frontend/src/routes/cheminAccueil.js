// Page d'accueil après connexion, selon le rôle.
import { ROLES } from "../constants/roles";

export function cheminAccueil(role) {
  switch (role) {

    case ROLES.UTILISATEUR:
    case ROLES.EVALUATEUR:
    default:
      return "/accueil";
  }
}