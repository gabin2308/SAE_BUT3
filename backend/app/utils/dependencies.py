"""
Assemblage central des DAO et Services (composition root).

Chaque DAO et Service n'est instancié qu'UNE SEULE FOIS ici, puis
réutilisé partout ailleurs (controllers, auth.py) par simple import.
"""

from app.models.utilisateur.UtilisateurDAO import UtilisateurDAO
from app.models.jeton.JetonDAO import JetonDAO
from app.models.token_revoque.TokenRevoqueDAO import TokenRevoqueDAO
from app.models.email.EmailServiceDAO import EmailEnvoyeDAO
from app.models.aeroport.AeroportDAO import AeroportDAO
from app.models.pays.PaysDAO import PaysDAO
from app.services.UtilisateurService import UtilisateurService
from app.services.AuthentificationService import AuthService
from app.services.AeroportService import AeroportService
from app.services.PaysService import PaysService

# ----------------------------------------------------------------------------
# DAO : une instance chacun, sans état (chaque appel passe par le pool de
# connexions), donc sans risque à partager. Le pool doit être initialisé
# (init_db_pool) au démarrage de l'appli, avant la première requête.
# ----------------------------------------------------------------------------
utilisateur_dao = UtilisateurDAO()
jeton_dao = JetonDAO()
token_revoque_dao = TokenRevoqueDAO()
email_dao = EmailEnvoyeDAO()
aeroport_dao = AeroportDAO()
pays_dao = PaysDAO()

# ----------------------------------------------------------------------------
# Services :
#  - UtilisateurService : comptes (inscription, activation par jeton email,
#    réinitialisation du mot de passe, profil, consentements). L'envoi d'email
#    est un appel direct à backend/smtp_email.py, sans injection.
#  - AuthService : sessions (connexion, JWT, rafraîchissement, révocation).
#  - AeroportService / PaysService : référentiel en lecture seule (US9, US10).
# ----------------------------------------------------------------------------
utilisateur_service = UtilisateurService(utilisateur_dao=utilisateur_dao, jeton_dao=jeton_dao)
auth_service = AuthService(utilisateur_dao=utilisateur_dao, token_revoque_dao=token_revoque_dao)
aeroport_service = AeroportService(aeroport_dao=aeroport_dao)
pays_service = PaysService(pays_dao=pays_dao)