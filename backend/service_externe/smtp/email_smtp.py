# service_externe/smtp_email.py
import html
import logging
import smtplib
import ssl
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from app.models.email.EmailServiceDAO import EmailEnvoyeDAO
from app.settings import settings

_SMTP_HOST = settings.smtp_host
_SMTP_PORT = settings.smtp_port
_SMTP_USER = settings.smtp_user
_SMTP_PASSWORD = settings.smtp_password
_SMTP_FROM_NAME = settings.smtp_from_name
_SMTP_TIMEOUT = settings.smtp_timeout

_PARIS = ZoneInfo("Europe/Paris")
_NOM_APPLI = "Recommandation de vols"

_journal_dao = EmailEnvoyeDAO()


def _send(type_email: str, to_email: str, subject: str, html_body: str) -> bool:
    """
    Envoie un email via SMTP et journalise le résultat dans email_envoye.
    Ne lève jamais d'exception : une panne d'envoi ne doit pas faire échouer
    l'opération métier appelante (l'utilisateur peut redemander l'email).

    Timeout explicite : sans lui, un hébergeur qui laisse la connexion
    "pendre" sans répondre bloquerait le thread indéfiniment.

    to_email et subject ne viennent jamais d'une saisie brute : l'email est
    celui d'un compte déjà validé (EmailStr) et le sujet est fixe, ce qui
    exclut l'injection d'en-têtes.
    """
    erreur = None
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{_SMTP_FROM_NAME} <{_SMTP_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=_SMTP_TIMEOUT) as server:
            # Contexte par défaut : vérifie le certificat du serveur SMTP
            server.starttls(context=ssl.create_default_context())
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.sendmail(_SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        erreur = str(e)[:500]
        logging.error(f"Échec envoi email à {to_email}: {e}")

    # On journalise le sujet, jamais le corps : il contient le lien secret.
    try:
        _journal_dao.journaliser(
            type_email, to_email, subject, "echec" if erreur else "envoye", erreur
        )
    except Exception:
        logging.exception("Impossible de journaliser l'email dans email_envoye")

    return erreur is None


def _send_async(type_email: str, to_email: str, subject: str, html_body: str) -> None:
    """
    Lance _send() dans un thread daemon, pour ne jamais bloquer la requête
    HTTP sur un appel SMTP lent. daemon=True : le thread ne retarde pas
    l'arrêt du process.
    """
    thread = threading.Thread(
        target=_send,
        args=(type_email, to_email, subject, html_body),
        daemon=True,
    )
    thread.start()


def envoyer_email_activation(
    destinataire: str, prenom: str, lien: str, expire_le: datetime
) -> None:
    """
    Envoie le lien d'activation de compte, de façon non bloquante.
    Ne retourne rien et ne lève jamais : le compte existe en base même si
    l'email échoue (voir email_envoye, puis « renvoyer l'email »).
    """
    expire = expire_le.astimezone(_PARIS).strftime("%d/%m/%Y à %H:%M")

    html_body = f"""
        <p>Bonjour {html.escape(prenom)},</p>
        <p>Bienvenue sur la plateforme « {html.escape(_NOM_APPLI)} ».
           Pour activer votre compte, confirmez votre adresse email.</p>
        <p><a href="{html.escape(lien, quote=True)}">Cliquez ici pour activer votre compte</a></p>
        <p>Ce lien est personnel et expire le {expire} (heure de Paris).
           Après ce délai, vous pourrez en demander un nouveau.
           Si vous n'avez pas créé de compte, ignorez simplement cet email.</p>
    """

    _send_async(
        type_email="activation",
        to_email=destinataire,
        subject=f"Activez votre compte — {_NOM_APPLI}",
        html_body=html_body,
    )


def envoyer_email_reinitialisation(
    destinataire: str, prenom: str, lien: str, expire_le: datetime
) -> None:
    """
    Envoie le lien de réinitialisation du mot de passe, de façon non bloquante.
    Ne retourne rien et ne lève jamais : l'utilisateur peut refaire une demande.
    """
    expire = expire_le.astimezone(_PARIS).strftime("%d/%m/%Y à %H:%M")

    html_body = f"""
        <p>Bonjour {html.escape(prenom)},</p>
        <p>Une demande de réinitialisation de mot de passe a été faite pour votre compte.</p>
        <p><a href="{html.escape(lien, quote=True)}">Cliquez ici pour choisir un nouveau mot de passe</a></p>
        <p>Ce lien est personnel et expire le {expire} (heure de Paris).
           Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet email :
           votre mot de passe actuel reste valable.</p>
    """

    _send_async(
        type_email="reinitialisation_mdp",
        to_email=destinataire,
        subject=f"Réinitialisation de votre mot de passe — {_NOM_APPLI}",
        html_body=html_body,
    )