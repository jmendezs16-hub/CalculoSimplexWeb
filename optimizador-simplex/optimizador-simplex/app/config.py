import os

from dotenv import load_dotenv


# Carga las variables del archivo .env del directorio desde el que se ejecuta la app.
load_dotenv()


def _cors_origins_from_env():
    value = os.getenv(
        "CORS_ORIGINS", os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    ).strip()
    if value == "*":
        return "*"
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = _cors_origins_from_env()


class DevelopmentConfig(Config):
    DEBUG = True
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "testing-only-secret"


class ProductionConfig(Config):
    DEBUG = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
