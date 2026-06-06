"""Modèle Campaign — une session de purple teaming.

Chaque campagne regroupe un ensemble de techniques ATT&CK jouées
par la red team et les détections correspondantes de la blue team.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    """Table 'campaign' en base de données.

    table=True signifie : ce n'est pas juste une classe Python,
    c'est aussi une vraie table SQLite.
    """

    # Clé primaire : SQLite attribue l'id automatiquement (auto-incrément).
    id: Optional[int] = Field(default=None, primary_key=True)

    # Nom de la campagne (obligatoire, indexé pour des recherches rapides).
    name: str = Field(index=True)

    # Description libre (optionnelle, vide par défaut).
    description: str = Field(default="")

    # Date de création : remplie automatiquement à l'insertion.
    created_at: datetime = Field(default_factory=datetime.utcnow)
