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
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "innovdiaspora"
    db_user: str = "postgres"
    db_password: str = ""

    # Emails (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    notify_email: str | None = None 
    smtp_from_name: str = "Journée de l'innovation"
    smtp_timeout: int = 10  # secondes

    # Contact Equipes : formulaire public, sans compte
    contact_email_equipe: str = ""
    
    # Front et invitations
    frontend_url: str = "http://localhost:5173"  # port par défaut de Vite
    invitation_validite_jours: int = 7


    depot_validation_heures: int = 48
    suivi_validite_jours: int = 365

    @property
    def url_validation_depot(self) -> str:
        return f"{self.frontend_url.rstrip('/')}/validation"  # route front à adapter

    @property
    def url_suivi(self) -> str:
        return f"{self.frontend_url.rstrip('/')}/suivi"  # route front à adapter

    @property
    def dsn(self) -> str:
        """DATABASE_URL si définie (prod), sinon DSN construit depuis DB_* (dev)."""
        if self.database_url:
            return self.database_url
        return make_dsn(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
        )

    @property
    def url_activation(self) -> str:
        return f"{self.frontend_url.rstrip('/')}/activation"  # route front à adapter


settings = Settings()