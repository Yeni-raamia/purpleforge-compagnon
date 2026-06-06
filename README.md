# PurpleForge Compagnon

> Outil web open-source de **purple teaming** : prend en entrée les techniques ATT&CK
> jouées par une red team, et produit des règles de détection Sigma, la liste des logs
> nécessaires, et une carte de couverture collaborative.

**Boucle de valeur :**
```
TTP joué → Sigma suggéré → règle testée & déployée → couverture mise à jour
```

---

## Fonctionnalités

| Écran | Ce que ça fait |
|---|---|
| **Campagnes** | Créer une session de purple team, voir l'historique |
| **Matrice ATT&CK** | Parcourir les 14 tactiques, ajouter les techniques jouées en un clic |
| **Fiche technique** | Statut (non détecté / à construire / détecté), note blue team, règles Sigma automatiques |
| **Couverture** | Barre de progression par statut, carte visuelle technique par technique |
| **Export Navigator** | Fichier `.json` importable sur [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) |

---

## Installation locale (Windows / Mac / Linux)

### Prérequis

- [Python 3.12+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/<votre-org>/purpleforge.git
cd purpleforge

# 2. Créer et activer l'environnement virtuel
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Mac / Linux
# source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Démarrer le serveur
uvicorn app.main:app --reload
```

Ouvrir **http://127.0.0.1:8000** dans le navigateur.

> **Premier démarrage :** l'appli télécharge automatiquement deux jeux de données :
> - Données ATT&CK Enterprise (MITRE STIX, ~40 Mo) — environ 30–60 secondes
> - Règles Sigma de SigmaHQ (~30 Mo, 2 900+ règles) — environ 30–60 secondes
>
> Ces téléchargements n'ont lieu qu'**une seule fois** ; les données sont mises en cache
> dans le dossier `data/`. Les démarrages suivants sont instantanés.

---

## Installation via Docker

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Démarrer en une commande

```bash
docker compose up
```

Ouvrir **http://localhost:8000**.

Pour arrêter :
```bash
docker compose down
```

> La base de données (`purpleforge.db`) et les données ATT&CK/Sigma (`data/`) sont
> stockées dans des volumes Docker et survivent aux redémarrages.

---

## Utilisation rapide

### 1. Créer une campagne

Sur la page d'accueil → **Voir les campagnes** → remplir le formulaire « Nouvelle campagne ».

### 2. Ajouter des techniques

Dans la campagne → **Ouvrir la matrice ATT&CK** → choisir une tactique → cliquer sur
**+ Ajouter** pour chaque technique jouée lors de l'exercice.

### 3. Qualifier les détections

Revenir sur la page de la campagne → chaque technique a :
- Un **statut** : `Non détectée` / `À construire` / `Détectée`
- Une **note blue team** (règle déployée, ticket SIEM, commentaire…)
- Un bouton **Règles Sigma** : affiche jusqu'à 8 règles SigmaHQ correspondantes avec
  les logs requis et le contenu YAML

### 4. Consulter la couverture

**Voir la couverture** → barre empilée vert/orange/rouge + carte de toutes les techniques
par tactique.

### 5. Exporter vers ATT&CK Navigator

**⬇ Exporter Navigator** → fichier `.json` à glisser sur
[attack-navigator](https://mitre-attack.github.io/attack-navigator/) pour une vue matricielle.

---

## Architecture

```
purpleforge/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── database.py              # Moteur SQLite + session
│   ├── models/
│   │   ├── campaign.py          # Modèle Campaign
│   │   └── technique.py         # Modèle TechniqueEntry (statut, note, tactic…)
│   ├── routes/
│   │   ├── campaigns.py         # Routes /campaigns/*
│   │   └── techniques.py        # Routes update statut + Sigma
│   ├── services/
│   │   ├── attack.py            # Téléchargement + parsing MITRE ATT&CK
│   │   ├── sigma.py             # Téléchargement + indexation règles Sigma
│   │   └── coverage.py          # Calcul des statistiques de couverture
│   ├── templates/               # Gabarits Jinja2 (HTML)
│   └── static/                  # style.css
├── data/                        # Données ATT&CK + Sigma (gitignorées)
├── tests/
│   └── test_smoke.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Stack technique

| Couche | Technologie |
|---|---|
| Framework web | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Rendu HTML | [Jinja2](https://jinja.palletsprojects.com/) |
| Interactivité front | [HTMX](https://htmx.org/) (pas de JS framework) |
| Base de données | [SQLite](https://www.sqlite.org/) via [SQLModel](https://sqlmodel.tiangolo.com/) |
| Données ATT&CK | [MITRE ATT&CK STIX 2.1](https://github.com/mitre-attack/attack-stix-data) |
| Règles de détection | [SigmaHQ](https://github.com/SigmaHQ/sigma) |

---

## Données téléchargées automatiquement

| Source | Taille | Fréquence |
|---|---|---|
| `attack-stix-data` (MITRE GitHub) | ~40 Mo | 1 fois, mis en cache dans `data/` |
| `sigma` (SigmaHQ GitHub) | ~30 Mo | 1 fois, mis en cache dans `data/` |

Pour forcer un re-téléchargement, supprimer les fichiers correspondants dans `data/`.

---

## Tests

```bash
pytest tests/ -v
```

4 tests de fumée couvrent : démarrage de l'appli, route d'accueil, moteur de base de
données, création des tables.

---

## Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Licence

MIT — voir [LICENSE](LICENSE).
