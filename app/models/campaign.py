"""Modèle Campaign — une session de purple teaming.

Chaque campagne regroupe un ensemble de techniques ATT&CK jouées
par la red team et les détections correspondantes de la blue team.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    """Table 'campaign' en base de données."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Nom de la campagne (obligatoire, indexé pour des recherches rapides).
    name: str = Field(index=True)

    # Description libre (optionnelle).
    description: str = Field(default="")

    # Tags groupes d'attaquants : chaîne séparée par virgules (ex: "APT28, Lazarus").
    # Stocké en texte simple, parsé à l'affichage.
    tags: str = Field(default="")

    # Date de création.
    created_at: datetime = Field(default_factory=datetime.utcnow)
