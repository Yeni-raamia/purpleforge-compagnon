"""Service Sigma : retrouve les règles de détection SigmaHQ pour un identifiant ATT&CK.

Fonctionnement :
1. Premier appel → télécharge les règles SigmaHQ (~30 Mo) dans data/.
2. Extrait uniquement les fichiers YAML de règles, construit un index ATT&CK → règles.
3. Appels suivants → lit l'index local (instantané).
"""

import io
import json
import logging
import zipfile
from pathlib import Path

import requests
import yaml

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
SIGMA_RULES_DIR = DATA_DIR / "sigma_rules"
SIGMA_INDEX_FILE = DATA_DIR / "sigma_index.json"

# Archive ZIP de la branche principale du dépôt SigmaHQ.
SIGMA_ZIP_URL = "https://github.com/SigmaHQ/sigma/archive/refs/heads/master.zip"

# Cache mémoire de l'index : chargé une seule fois par démarrage.
_index_cache: dict | None = None


def is_sigma_ready() -> bool:
    """Vrai si l'index Sigma est disponible localement."""
    return SIGMA_INDEX_FILE.exists()


def _download_and_index() -> None:
    """Télécharge les règles SigmaHQ et construit l'index ATT&CK → règles.

    Bloquant (première fois seulement). La progression s'affiche dans le terminal.
    """
    if is_sigma_ready():
        return

    DATA_DIR.mkdir(exist_ok=True)
    SIGMA_RULES_DIR.mkdir(exist_ok=True)

    print("[Sigma] Première ouverture : téléchargement des règles SigmaHQ (~30 Mo)…")
    print("[Sigma] Le navigateur attend — c'est normal, une seule fois.")

    response = requests.get(SIGMA_ZIP_URL, stream=True, timeout=300)
    response.raise_for_status()

    # On accumule le ZIP en mémoire (30 Mo, acceptable) pour l'extraire.
    zip_bytes = io.BytesIO()
    for chunk in response.iter_content(chunk_size=65_536):
        zip_bytes.write(chunk)
    zip_bytes.seek(0)

    print("[Sigma] Téléchargement terminé. Indexation en cours…")

    # Index : identifiant ATT&CK → liste de noms de fichiers de règles.
    index: dict[str, list[str]] = {}
    saved = 0

    with zipfile.ZipFile(zip_bytes) as zf:
        # On ne garde que les fichiers YAML dans les dossiers de règles.
        rule_entries = [
            name for name in zf.namelist()
            if name.endswith(".yml")
            and ("/rules/" in name or "/rules-threat-hunting/" in name)
        ]

        for entry in rule_entries:
            try:
                content = zf.read(entry).decode("utf-8", errors="replace")
                rule = yaml.safe_load(content)
                if not isinstance(rule, dict):
                    continue

                # Extraire les tags ATT&CK (ex. "attack.t1003.001").
                tags = rule.get("tags") or []
                attack_ids = []
                for tag in tags:
                    tag_lower = str(tag).lower()
                    # On filtre les tags techniques : attack.t + chiffre
                    if (
                        tag_lower.startswith("attack.t")
                        and len(tag_lower) > 8
                        and tag_lower[8].isdigit()
                    ):
                        # Normalisation → "T1003.001"
                        attack_ids.append(tag_lower[7:].upper())

                if not attack_ids:
                    continue

                # Sauvegarde du fichier YAML localement.
                filename = Path(entry).name
                local_path = SIGMA_RULES_DIR / filename
                local_path.write_text(content, encoding="utf-8")
                saved += 1

                # Mise à jour de l'index.
                for aid in attack_ids:
                    index.setdefault(aid, [])
                    if filename not in index[aid]:
                        index[aid].append(filename)

            except Exception:
                continue  # on ignore les fichiers malformés

    # Sauvegarde de l'index.
    SIGMA_INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[Sigma] Index prêt : {len(index)} techniques, {saved} règles sauvegardées.")


def _load_index() -> dict:
    """Charge l'index depuis le fichier JSON (avec cache mémoire)."""
    global _index_cache
    if _index_cache is None:
        _download_and_index()
        _index_cache = json.loads(SIGMA_INDEX_FILE.read_text(encoding="utf-8"))
    return _index_cache


def _format_logsource(logsource: dict) -> str:
    """Transforme le bloc logsource YAML en texte lisible pour l'interface."""
    if not logsource:
        return "Non spécifié"
    parts = []
    if "product" in logsource:
        parts.append(logsource["product"].capitalize())
    if "category" in logsource:
        parts.append(f"catégorie : {logsource['category']}")
    if "service" in logsource:
        parts.append(f"service : {logsource['service']}")
    return " — ".join(parts)


def get_rules_for_technique(attack_id: str) -> list[dict]:
    """Retourne la liste des règles Sigma pour un identifiant ATT&CK.

    Args:
        attack_id : identifiant ATT&CK, ex. « T1003.001 » ou « T1003 ».

    Returns:
        Liste de dicts contenant :
        - title         : titre de la règle
        - description   : description courte
        - required_logs : logs nécessaires (texte lisible)
        - level         : niveau (informational / low / medium / high / critical)
        - yaml_content  : contenu brut YAML (pour copier-coller)
    """
    index = _load_index()
    filenames = index.get(attack_id.upper(), [])

    rules = []
    for filename in filenames[:8]:   # on affiche au maximum 8 règles
        path = SIGMA_RULES_DIR / filename
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
            rule = yaml.safe_load(content)
            if not isinstance(rule, dict):
                continue

            logsource = rule.get("logsource") or {}
            rules.append({
                "title": rule.get("title", filename),
                "description": (rule.get("description") or "")[:300],
                "required_logs": _format_logsource(logsource),
                "level": rule.get("level", ""),
                "yaml_content": content,
            })
        except Exception:
            continue

    return rules
