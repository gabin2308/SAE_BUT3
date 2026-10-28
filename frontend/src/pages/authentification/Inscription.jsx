// src/pages/publiques/Inscription.jsx  (écran 2 du storyboard)
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../../components/layouts/AuthLayout";
import AuthCard from "../../components/ui/AuthCard";
import Logo from "../../components/ui/Logo";
import ChampTexte from "../../components/ui/ChampTexte";
import CaseACocher from "../../components/ui/CaseACocher";
import { IconeEnveloppe, IconeCadenas, IconePersonne } from "../../components/ui/Icones";
import { utilisateurService } from "../../services/utilisateurService";
import {
  isValidEmail,
  isValidNom,
  getPasswordStrengthErrors,
  MAX_EMAIL_LEN,
  MAX_NOM_LEN,
  MAX_PASSWORD_LEN,
} from "../../utils/validators";

const CHAMPS_SERVEUR = ["nom", "prenom", "email", "mot_de_passe", "consentement_politique"];

export default function Inscription() {
  const navigate = useNavigate();
  const [valeurs, setValeurs] = useState({
    nom: "",
    prenom: "",
    email: "",
    mot_de_passe: "",
  });
  const [politique, setPolitique] = useState(false);
  const [personnalisation, setPersonnalisation] = useState(false);
  const [localisation, setLocalisation] = useState(false);
  const [erreurs, setErreurs] = useState({});
  const [erreurGlobale, setErreurGlobale] = useState(null);
  const [envoi, setEnvoi] = useState(false);

  const changer = (champ) => (e) =>
    setValeurs((v) => ({ ...v, [champ]: e.target.value }));

  const valider = () => {
    const e = {};
    if (!isValidNom(valeurs.nom)) e.nom = "Entrez votre nom (lettres, espaces, - et ’ uniquement).";
    if (!isValidNom(valeurs.prenom)) e.prenom = "Entrez votre prénom (lettres, espaces, - et ’ uniquement).";
    if (!isValidEmail(valeurs.email)) e.email = "Entrez une adresse email valide.";
    const mdp = getPasswordStrengthErrors(valeurs.mot_de_passe);
    if (mdp.length) e.mot_de_passe = `Mot de passe : ${mdp.join(" ").toLowerCase()}`;
    if (!politique) e.politique = "Vous devez accepter la politique pour créer un compte.";
    return e;
  };

  const soumettre = async (ev) => {
    ev.preventDefault();
    setErreurGlobale(null);
    const e = valider();
    setErreurs(e);
    if (Object.keys(e).length) return;

    setEnvoi(true);
    try {
      const email = valeurs.email.trim();
      await utilisateurService.inscription({
        nom: valeurs.nom.trim(),
        prenom: valeurs.prenom.trim(),
        email,
        mot_de_passe: valeurs.mot_de_passe,
        consentement_politique: politique,
        consentement_personnalisation: personnalisation,
        consentement_localisation: localisation,
      });
      navigate("/verification-email", { state: { email }, replace: true });
    } catch (err) {
      if (err?.status === 409) {
        setErreurs({ email: "Cette adresse email est déjà utilisée." });
      } else if (err?.champs && typeof err.champs === "object") {
        // { champ: [messages] } : on affiche le premier message sous chaque champ connu
        const parChamp = {};
        for (const [champ, msgs] of Object.entries(err.champs)) {
          const msg = [msgs].flat()[0];
          if (CHAMPS_SERVEUR.includes(champ) && msg) parChamp[champ] = String(msg);
        }
        if (Object.keys(parChamp).length) setErreurs(parChamp);
        else setErreurGlobale(err.message);
      } else {
        setErreurGlobale(err?.message || "Inscription impossible pour le moment. Réessayez.");
      }
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <AuthLayout>
      <AuthCard>
        <div className="flex justify-center">
          <Logo />
        </div>
        <h1 className="mt-6 text-center text-2xl font-bold text-slate-900">Créer un compte</h1>
        <p className="mt-2 text-center text-sm text-slate-600">
          Rejoignez notre communauté et commencez à trouver vos prochains voyages.
        </p>

        <div aria-live="polite">
          {erreurGlobale && (
            <p
              role="alert"
              className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800"
            >
              {erreurGlobale}
            </p>
          )}
        </div>

        <form onSubmit={soumettre} noValidate className="mt-6 space-y-4">
          <ChampTexte
            label="Nom"
            icone={<IconePersonne />}
            placeholder="Nom"
            autoComplete="family-name"
            maxLength={MAX_NOM_LEN}
            value={valeurs.nom}
            onChange={changer("nom")}
            erreur={erreurs.nom}
          />
          <ChampTexte
            label="Prénom"
            icone={<IconePersonne />}
            placeholder="Prénom"
            autoComplete="given-name"
            maxLength={MAX_NOM_LEN}
            value={valeurs.prenom}
            onChange={changer("prenom")}
            erreur={erreurs.prenom}
          />
          <ChampTexte
            label="Email"
            type="email"
            icone={<IconeEnveloppe />}
            placeholder="exemple@email.com"
            autoComplete="email"
            maxLength={MAX_EMAIL_LEN}
            value={valeurs.email}
            onChange={changer("email")}
            erreur={erreurs.email}
          />
          <ChampTexte
            label="Mot de passe"
            type="password"
            icone={<IconeCadenas />}
            placeholder="Mot de passe"
            autoComplete="new-password"
            maxLength={MAX_PASSWORD_LEN}
            value={valeurs.mot_de_passe}
            onChange={changer("mot_de_passe")}
            erreur={erreurs.mot_de_passe}
          />

          <div className="space-y-3 pt-1">
            <CaseACocher
              checked={politique}
              onChange={(e) => setPolitique(e.target.checked)}
              erreur={erreurs.politique || erreurs.consentement_politique}
            >
              J’accepte la{" "}
              <Link to="/politique-de-confidentialite" className="text-blue-600 hover:underline">
                politique d’utilisation et la confidentialité
              </Link>{" "}
              (obligatoire)
            </CaseACocher>
            <CaseACocher
              checked={personnalisation}
              onChange={(e) => setPersonnalisation(e.target.checked)}
            >
              Je souhaite recevoir des offres personnalisées (facultatif)
            </CaseACocher>
            <CaseACocher
              checked={localisation}
              onChange={(e) => setLocalisation(e.target.checked)}
            >
              J’accepte d’activer la localisation (facultatif)
            </CaseACocher>
          </div>

          <button
            type="submit"
            disabled={envoi}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:opacity-60"
          >
            {envoi ? "Création du compte…" : "S’inscrire"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          Vous avez déjà un compte ?{" "}
          <Link to="/connexion" className="text-blue-600 hover:underline">
            Se connecter
          </Link>
        </p>
      </AuthCard>
    </AuthLayout>
  );
}