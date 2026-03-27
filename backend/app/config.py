import os
from datetime import timedelta


class BaseConfig:
    SECRET_KEY               = os.environ["SECRET_KEY"]
    FRONTEND_URL             = os.getenv("FRONTEND_URL", "http://localhost:3000")

    SQLALCHEMY_DATABASE_URI        = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS      = {
        "pool_pre_ping": True,
        "pool_recycle":  300,
        "pool_size":     10,
        "max_overflow":  20,
    }

    JWT_SECRET_KEY           = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES= timedelta(days=30)
    JWT_TOKEN_LOCATION       = ["headers", "cookies"]
    JWT_COOKIE_SECURE        = True
    JWT_COOKIE_CSRF_PROTECT  = True

    REDIS_URL                = os.getenv("REDIS_URL", "redis://redis:6379/0")
    SESSION_TYPE             = "redis"
    SESSION_PERMANENT        = False

    MAIL_SERVER              = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT                = int(os.getenv("MAIL_PORT", 25))
    MAIL_USE_TLS  = False
    MAIL_USE_SSL  = False
    MAIL_USERNAME            = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD            = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER      = os.getenv("MAIL_DEFAULT_SENDER", "noreply@bestbudgetplaner.pl")

    CORS_ORIGINS             = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

class DevelopmentConfig(BaseConfig):
    DEBUG                    = True
    JWT_COOKIE_SECURE        = False
    JWT_COOKIE_CSRF_PROTECT  = False


class ProductionConfig(BaseConfig):
    DEBUG                    = False
    JWT_COOKIE_CSRF_PROTECT  = False
    JWT_TOKEN_LOCATION       = ["headers"]

class TestingConfig(BaseConfig):
    TESTING                  = True
    DEBUG                    = True
    SQLALCHEMY_DATABASE_URI  = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    JWT_COOKIE_SECURE        = False
    JWT_COOKIE_CSRF_PROTECT  = False
    SECRET_KEY               = os.getenv("SECRET_KEY", "test-secret")
    JWT_SECRET_KEY           = os.getenv("JWT_SECRET_KEY", "test-jwt-secret")


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     ProductionConfig,
}
