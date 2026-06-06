# PurpleForge Compagnon

Outil web open-source de **purple teaming** : il prend en entrée les techniques
d'attaque jouées par une red team (référentiel MITRE ATT&CK) et produit en sortie
des règles de détection Sigma, la liste des logs nécessaires, et une carte de
couverture collaborative.

**Boucle de valeur :** TTP joué → détection suggérée → testée/déployée → couverture mise à jour.

## Stack

- **Python 3.11+** / **FastAPI** / **Uvicorn**
- **HTMX + Jinja2** (pas de framework JS)
- **SQLite** → PostgreSQL
- **Docker**

## Installation (développement local)

### Prérequis
- Python 3.11 ou supérieur
- Git

### Lancer l'appli

```bash
git clone <url-du-depot>
cd purpleforge

# Créer et activer l'environnement isolé
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate        # Mac / Linux

# Installer les dépendances
pip install -r requirements.txt

# Démarrer le serveur
uvicorn app.main:app --reload
```

Ouvrir **http://127.0.0.1:8000** dans le navigateur.

## Installation via Docker

```bash
docker-compose up
```

Ouvrir **http://localhost:8000**.

## Licence

MIT — voir [LICENSE](LICENSE).
