from psycopg2.extensions import make_dsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Debug / dev
    DEBUG: bool = True
    ENV: str = "development"  # "production" sur Render : active le flag secure des cookies

    # Sécurité : sans valeur par défaut, l'appli refuse de démarrer si elles manquent
    JWT_SECRET: str
    totp_encryption_key: str
    
    # Production (Render) : une seule URL
    database_url: str | None = None

    # Développement : paramètres séparés
    postgres_host: str
    postgres_port: int
    postgres_name: str 
    postgres_user: str 
    postgres_password: str 

    # Emails (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    notify_email: str | None = None 
    smtp_from_name: str = ""
    smtp_timeout: int = 10  # secondes

    # Contact Equipes : formulaire public, sans compte
    contact_email_equipe: str
    
    # Front et invitations
    frontend_url: str # port par défaut de Vite

    # API
    ignav_api_key: str | None = None  # clé d'API pour Ignav (si activée)
    dossier_json: str | None = None  # chemin vers le dossier contenant les fichiers JSON (si activé)
    
    @property
    def dsn(self) -> str:
        """DATABASE_URL si définie (prod), sinon DSN construit depuis DB_* (dev)."""
        if self.database_url:
            return self.database_url
        return make_dsn(
            host=self.postgres_host,
            port=self.postgres_port,
            dbname=self.postgres_name,
            user=self.postgres_user,
            password=self.postgres_password,
        )


settings = Settings()