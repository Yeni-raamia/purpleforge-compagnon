"""Modèle utilisateur pour l'authentification multi-équipe.

Un User représente un membre de l'équipe purple team.
Le premier utilisateur créé est automatiquement administrateur.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id:              Optional[int] = Field(default=None, primary_key=True)
    username:        str           = Field(index=True, unique=True, max_length=50)
    display_name:    str           = Field(default="", max_length=100)
    hashed_password: str
    is_admin:        bool          = Field(default=False)
    created_at:      datetime      = Field(default_factory=datetime.utcnow)
