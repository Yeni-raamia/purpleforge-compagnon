"""Connexion à la base de données SQLite.

SQLModel est la bibliothèque qui fait le pont entre Python et SQLite.
Le fichier purpleforge.db sera créé automatiquement dans le dossier du projet.
"""

from sqlmodel import SQLModel, create_engine, Session

# Chemin de la base SQLite (fichier local, zéro configuration).
# Le préfixe "sqlite:///" signifie "base de données dans un fichier local".
DATABASE_URL = "sqlite:///purpleforge.db"

# Le moteur (engine) gère les connexions à la base.
# echo=True affiche les requêtes SQL dans le terminal — utile pour déboguer.
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Crée la base et toutes les tables au démarrage de l'appli.

    Cette fonction lit tous les modèles importés (SQLModel)
    et crée les tables correspondantes si elles n'existent pas encore.
    En Phase 0, aucun modèle n'est encore défini : elle ne fait rien de visible,
    mais la base SQLite est bien créée.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """Fournit une session de base de données à chaque requête.

    On utilisera cette fonction dès la Phase 1 pour lire/écrire en base.
    """
    with Session(engine) as session:
        yield session
