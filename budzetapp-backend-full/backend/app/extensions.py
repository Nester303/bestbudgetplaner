"""
Rozszerzenia Flask inicjalizowane jako singletony — importuj stąd wszędzie.
Wzorzec application factory: init_app() wywoływany w create_app().
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
import redis

db      = SQLAlchemy()
migrate = Migrate()
jwt     = JWTManager()
mail    = Mail()
cors    = CORS()
limiter = Limiter(key_func=get_remote_address)
sess    = Session()

# Klient Redis (używany bezpośrednio w cache / pub-sub)
redis_client: redis.Redis | None = None


def init_redis(app):
    global redis_client
    redis_client = redis.from_url(
        app.config["REDIS_URL"],
        decode_responses=True,
    )
    return redis_client
