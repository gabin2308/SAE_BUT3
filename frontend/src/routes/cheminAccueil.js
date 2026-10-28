// Page d'accueil après connexion, selon le rôle.
import { ROLES } from "../constants/roles";

export function cheminAccueil(role) {
  switch (role) {

    case ROLES.UTILISATEUR:
    case ROLES.EVALUATEUR:
      return "/accueil"; // provisoire, jusqu'à la création de leurs espaces
    default:
      return "/connexion";
  }
}