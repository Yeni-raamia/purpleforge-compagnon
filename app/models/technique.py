"""Modèle TechniqueEntry — une technique ATT&CK jouée dans une campagne.

Chaque entrée représente une technique jouée par la red team,
avec son statut de détection et les notes des deux équipes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class TechniqueStatus(str, Enum):
    """Les trois états possibles d'une technique.

    On hérite de str pour que SQLite stocke la valeur texte
    (ex. 'detecte') et non un entier incompréhensible.
    """

    non_detecte = "non_detecte"   # la technique n'a pas été détectée
    a_construire = "a_construire" # une détection est à construire
    detecte = "detecte"           # la détection est en place


class TechniqueEntry(SQLModel, table=True):
    """Table 'techniqueentry' en base de données."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Lien vers la campagne parente (clé étrangère → table 'campaign').
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaign.id")

    # Identifiant ATT&CK officiel, ex. "T1003" ou "T1003.001".
    attack_id: str

    # Nom lisible de la technique, ex. "OS Credential Dumping".
    name: str

    # Tactique ATT&CK parente, ex. "Credential Access".
    tactic: str

    # Note de la red team : ce qu'elle a fait exactement.
    red_note: str = Field(default="")

    # Note de la blue team : observations, règle créée, log activé…
    blue_note: str = Field(default="")

    # Statut courant de la détection.
    status: TechniqueStatus = Field(default=TechniqueStatus.non_detecte)

    # Date à laquelle la technique a été jouée.
    played_at: datetime = Field(default_factory=datetime.utcnow)
