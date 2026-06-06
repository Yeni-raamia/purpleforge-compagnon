"""Tests de fumée (smoke tests) — Phase 0.

Un "test de fumée" vérifie juste que l'essentiel fonctionne,
sans tester les détails. Comme allumer une ampoule pour vérifier
qu'il y a du courant, avant de vérifier chaque prise.
"""

from app.main import app
from app.database import engine, create_db_and_tables


def test_app_is_created():
    """L'appli FastAPI existe et a le bon titre."""
    assert app is not None
    assert app.title == "PurpleForge Compagnon"


def test_home_route_exists():
    """La route '/' est bien déclarée."""
    routes = [r.path for r in app.routes]
    assert "/" in routes


def test_database_engine():
    """Le moteur SQLite se crée sans erreur."""
    assert engine is not None


def test_create_db_and_tables():
    """La fonction d'init de la base s'exécute sans erreur."""
    # Ne doit pas lever d'exception.
    create_db_and_tables()
