import os
from datetime import timedelta


class BaseConfig:
    # --- Ogólne ---
    SECRET_KEY          = os.environ["SECRET_KEY"]
    FRONTEND_URL        = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # --- Baza danych ---
    SQLALCHEMY_DATABASE_URI     = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS   = {
        "pool_pre_ping": True,       # odtwarza połączenia po restarcie DB
        "pool_recycle":  300,        # recykl co 5 minut
        "pool_size":     10,
        "max_overflow":  20,
    }

    # --- JWT ---
    JWT_SECRET_KEY              = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES    = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES   = timedelta(days=30)
    JWT_TOKEN_LOCATION          = ["headers", "cookies"]
    JWT_COOKIE_SECURE           = True
    JWT_COOKIE_CSRF_PROTECT     = True

    # --- Redis / Sesje ---
    REDIS_URL                   = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SESSION_TYPE                = "redis"
    SESSION_PERMANENT           = False
    SESSION_USE_SIGNER          = True
    PERMANENT_SESSION_LIFETIME  = timedelta(days=7)

    # --- Mail ---
    MAIL_SERVER                 = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT                   = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS                = True
    MAIL_USERNAME               = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD               = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER         = os.getenv("MAIL_DEFAULT_SENDER", "noreply@example.com")

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URL       = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATELIMIT_DEFAULT           = "200 per day;50 per hour"

    # --- CORS ---
    CORS_ORIGINS                = [FRONTEND_URL]
    CORS_SUPPORTS_CREDENTIALS   = True


class DevelopmentConfig(BaseConfig):
    DEBUG                               = True
    JWT_COOKIE_SECURE                   = False   # HTTP w dev
    JWT_COOKIE_CSRF_PROTECT             = False
    SQLALCHEMY_ECHO                     = False   # True = loguj każde zapytanie SQL
    RATELIMIT_ENABLED                   = False   # wyłącz limity w dev


class ProductionConfig(BaseConfig):
    DEBUG                               = False
    PROPAGATE_EXCEPTIONS                = True
    SQLALCHEMY_ENGINE_OPTIONS           = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size":    20,
        "max_overflow": 40,
    }


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
