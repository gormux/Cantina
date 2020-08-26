import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "9OLWxND4cklfzh42o83j4K4iuopO"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir}/cantina.sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = "plokij"
    APP_CONFIG = None
