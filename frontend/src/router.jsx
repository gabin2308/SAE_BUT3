// src/router.jsx
import { createBrowserRouter, Outlet } from "react-router-dom";
import { ROLES } from "./constants/roles";
import UtilisateurLayout from "./components/layouts/UtilisateurLayout";
import RequireAuth from "./components/RequireAuth";
import RootRedirect from "./components/RootRedirect";

import Accroche from "./pages/publiques/Accroche";
import MotDePasseOublie from "./pages/publiques/MotDePasseOublie";
import NouveauMotDePasse from "./pages/publiques/NouveauMotDePasse";
import Connexion from "./pages/authentification/Connexion";
import Inscription from "./pages/authentification/Inscription";
import VerificationEmail from "./pages/authentification/VerificationEmail";
import ActivationCompte from "./pages/authentification/ActivationCompte";

import Accueil from "./pages/utilisateur/Accueil"; // à ranger plus tard dans pages/utilisateur/

// UtilisateurLayout reçoit `children` : cet adaptateur lui fournit la page de la route active.
function LayoutUtilisateur() {
  return (
    <UtilisateurLayout>
      <Outlet />
    </UtilisateurLayout>
  );
}

const erreurPage = (
  <p className="p-8 text-red-600" role="alert">
    Une erreur est survenue dans cette page (voir la console du navigateur).
  </p>
);

export default createBrowserRouter([
  // Routes publiques
  { path: "/", element: <Accroche />, errorElement: erreurPage },
  { path: "/connexion", element: <Connexion /> },
  { path: "/inscription", element: <Inscription /> },
  { path: "/mot-de-passe-oublie", element: <MotDePasseOublie /> },
  { path: "/reinitialisation", element: <NouveauMotDePasse /> }, // lien email : ?jeton=...

  // Activation du compte depuis le lien reçu par email : ?jeton=...
  { path: "/verification-email", element: <VerificationEmail /> },
  { path: "/activation", element: <ActivationCompte /> },

  // Routes protégées (tous rôles), avec en-tête et pied de page
  {
    element: <RequireAuth />,
    errorElement: erreurPage,
    children: [
      {
        element: <LayoutUtilisateur />,
        children: [
          { path: "/accueil", element: <Accueil /> },
          // À venir :
          // { path: "/resultats", element: <Resultats /> },        // US12, US14, US15
          // { path: "/vols/:id", element: <FicheVol /> },          // US20
          // { path: "/favoris", element: <Favoris /> },            // US16
          // { path: "/historique", element: <Historique /> },      // US19
          // { path: "/mon-compte", element: <MonCompte /> },       // US24
        ],
      },
    ],
  },

  // Espace évaluateur (US26, US29 à US31), à ajouter au fur et à mesure :
  // {
  //   element: <RequireAuth roles={[ROLES.EVALUATEUR]} />,
  //   children: [{ element: <LayoutUtilisateur />, children: [
  //     { path: "/evaluateur", element: <TableauDeBord /> },
  //   ]}],
  // },

  { path: "*", element: <RootRedirect /> },
]);