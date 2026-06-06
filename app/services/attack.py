"""Service ATT&CK : charge et expose le référentiel MITRE ATT&CK Enterprise.

Fonctionnement :
1. Première utilisation → télécharge le fichier STIX (~50 Mo) dans data/.
2. Appels suivants → lit le fichier local (cache mémoire après premier parse).
"""

import json
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Emplacement du fichier de données local (ignoré par git via .gitignore).
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "enterprise-attack.json"

# URL du référentiel ATT&CK Enterprise sur GitHub MITRE (version 14.1).
# On utilise le format STIX 2.1 officiel.
ATTACK_URL = (
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data"
    "/master/enterprise-attack/enterprise-attack-14.1.json"
)

# Ordre canonique des 14 tactiques ATT&CK Enterprise.
TACTIC_ORDER = [
    "reconnaissance",
    "resource-development",
    "initial-access",
    "execution",
    "persistence",
    "privilege-escalation",
    "defense-evasion",
    "credential-access",
    "discovery",
    "lateral-movement",
    "collection",
    "command-and-control",
    "exfiltration",
    "impact",
]

# Cache mémoire : on parse le JSON une seule fois par démarrage de serveur.
_matrix_cache: list | None = None


def is_data_ready() -> bool:
    """Vrai si le fichier STIX est présent et complet (> 1 Mo)."""
    return DATA_FILE.exists() and DATA_FILE.stat().st_size > 1_000_000


def _download_if_needed() -> None:
    """Télécharge le fichier STIX ATT&CK si absent. Bloquant, mais une seule fois."""
    if is_data_ready():
        return

    DATA_DIR.mkdir(exist_ok=True)
    print("[ATT&CK] Première ouverture : téléchargement des données (~50 Mo)…")
    print("[ATT&CK] Le navigateur attend — c'est normal, ça ne se passe qu'une fois.")
    logger.info("Téléchargement des données ATT&CK Enterprise en cours…")

    response = requests.get(ATTACK_URL, stream=True, timeout=180)
    response.raise_for_status()

    with open(DATA_FILE, "wb") as f:
        for chunk in response.iter_content(chunk_size=65_536):
            f.write(chunk)

    print("[ATT&CK] Téléchargement terminé.")
    logger.info("Données ATT&CK téléchargées et mises en cache dans data/.")


def _get_attack_id(obj: dict) -> str:
    """Extrait l'identifiant ATT&CK (ex. T1003.001) depuis les références externes."""
    for ref in obj.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id", "")
    return ""


def _get_tactic_shortnames(obj: dict) -> list[str]:
    """Retourne les noms courts de tactique (kill-chain) d'une technique."""
    return [
        phase["phase_name"]
        for phase in obj.get("kill_chain_phases", [])
        if phase.get("kill_chain_name") == "mitre-attack"
    ]


def get_matrix() -> list[dict]:
    """Retourne la matrice ATT&CK Enterprise : liste ordonnée de tactiques + techniques.

    Format :
    [
      {
        "shortname": "credential-access",
        "name": "Credential Access",
        "techniques": [
          {"attack_id": "T1003", "name": "OS Credential Dumping", "is_sub": False},
          {"attack_id": "T1003.001", "name": "LSASS Memory", "is_sub": True},
          ...
        ]
      },
      ...
    ]
    """
    global _matrix_cache
    if _matrix_cache is not None:
        return _matrix_cache

    _download_if_needed()

    print("[ATT&CK] Chargement et indexation du référentiel…")
    with open(DATA_FILE, encoding="utf-8") as f:
        stix = json.load(f)

    objects = stix.get("objects", [])

    # Construction de l'index des tactiques.
    tactic_map: dict[str, dict] = {}
    for obj in objects:
        if obj.get("type") != "x-mitre-tactic":
            continue
        # Note : le nouveau format MITRE utilise x_mitre_shortname (underscores).
        shortname = obj.get("x_mitre_shortname", "")
        if not shortname:
            continue
        tactic_map[shortname] = {
            "shortname": shortname,
            "name": obj.get("name", shortname),
            "techniques": [],
        }

    # Parcours des techniques (on exclut les révoquées et dépréciées).
    for obj in objects:
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        # Garder uniquement les techniques du domaine enterprise-attack.
        if "enterprise-attack" not in obj.get("x_mitre_domains", []):
            continue

        attack_id = _get_attack_id(obj)
        if not attack_id:
            continue

        technique = {
            "attack_id": attack_id,
            "name": obj.get("name", ""),
            "is_sub": obj.get("x_mitre_is_subtechnique", "." in attack_id),
        }

        # Une technique peut appartenir à plusieurs tactiques.
        for shortname in _get_tactic_shortnames(obj):
            if shortname in tactic_map:
                tactic_map[shortname]["techniques"].append(technique)

    # Tri par identifiant ATT&CK dans chaque tactique.
    for tactic in tactic_map.values():
        tactic["techniques"].sort(key=lambda t: t["attack_id"])

    # On retourne les tactiques dans l'ordre canonique ATT&CK.
    _matrix_cache = [
        tactic_map[sn] for sn in TACTIC_ORDER if sn in tactic_map
    ]
    print(f"[ATT&CK] Matrice prête : {len(_matrix_cache)} tactiques indexées.")
    return _matrix_cache
