"""Connexion à la base de données SQLite.

SQLModel est la bibliothèque qui fait le pont entre Python et SQLite.
Le fichier purpleforge.db sera créé automatiquement dans le dossier du projet.
"""

import sqlite3

from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///purpleforge.db"

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Crée la base et toutes les tables au démarrage de l'appli."""
    SQLModel.metadata.create_all(engine)
    _run_migrations()


def _run_migrations() -> None:
    """Ajoute les colonnes manquantes sur une base existante.

    SQLModel/SQLAlchemy ne fait pas de migrations automatiques (ALTER TABLE).
    Cette fonction comble le manque de façon simple, sans Alembic.
    Chaque bloc try/except est idempotent : il échoue silencieusement si la
    colonne existe déjà.
    """
    with sqlite3.connect("purpleforge.db") as conn:
        # Phase 6 — colonne tags sur Campaign (groupes ATT&CK / APT)
        try:
            conn.execute("ALTER TABLE campaign ADD COLUMN tags TEXT DEFAULT ''")
            conn.commit()
        except sqlite3.OperationalError:
            pass   # colonne déjà présente


def get_session():
    """Fournit une session de base de données à chaque requête."""
    with Session(engine) as session:
        yield session
