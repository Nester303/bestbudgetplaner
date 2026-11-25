from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
import redis as redis_module

db      = SQLAlchemy()
migrate = Migrate()
jwt     = JWTManager()
mail    = Mail()
cors    = CORS()
sess    = Session()
limiter = Limiter(key_func=get_remote_address)

redis_client = None


def init_redis(app):
    global redis_client
    url = app.config["REDIS_URL"]

    redis_client = redis_module.from_url(url, decode_responses=True)

    # Flask-Session
    app.config["SESSION_TYPE"]         = "redis"
    app.config["SESSION_REDIS"]        = redis_module.from_url(url, decode_responses=False)
    app.config["SESSION_PERMANENT"]    = False
    app.config["SESSION_USE_SIGNER"]   = True

    # Flask-Limiter — musi być przed init_app
    app.config["RATELIMIT_STORAGE_URI"] = url

    return redis_client
