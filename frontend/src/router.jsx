import { createBrowserRouter } from "react-router-dom";
import RequireAuth from "./components/RequireAuth";
import RootRedirect from "./components/RootRedirect";
import Accueil from "./pages/publiques/Accueil";
import Connexion from "./pages/authentification/Connexion";
import Inscription from "./pages/authentification/Inscription";
import VerificationEmail from "./pages/authentification/VerificationEmail";
import ActivationCompte from "./pages/authentification/ActivationCompte";
export default createBrowserRouter([
  // Routes publiques
  { path: "/connexion", element: <Connexion /> },
  { path: "/inscription", element: <Inscription /> },

  // Activation du compte depuis le lien reçu par email
  {path: "/verification-email", element: <VerificationEmail /> },
  { path: "/activation", element: <ActivationCompte /> },

  // Routes protégées
  {
    element: <RequireAuth />,
    children: [{ path: "/accueil", element: <Accueil /> }],
  },

  { path: "/", element: <RootRedirect /> },
  { path: "*", element: <RootRedirect /> },
]);