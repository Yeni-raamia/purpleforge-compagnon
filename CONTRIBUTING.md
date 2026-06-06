# Guide de contribution — PurpleForge Compagnon

Merci de l'intérêt ! Ce guide explique comment contribuer de façon simple et efficace.

---

## Avant de commencer

- Vérifie que [Python 3.12+](https://www.python.org/) et
  [Git](https://git-scm.com/) sont installés.
- Lis le [README](README.md) pour comprendre l'appli et la stack.
- Parcours les [issues ouvertes](../../issues) : quelqu'un travaille peut-être déjà
  sur ce que tu veux faire.

---

## Mise en place de l'environnement de développement

```bash
git clone https://github.com/<votre-org>/purpleforge.git
cd purpleforge

python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## Soumettre une contribution

### 1. Forker et créer une branche

```bash
git checkout -b feat/nom-de-ma-fonctionnalite
# ou
git checkout -b fix/description-du-bug
```

### 2. Développer

Quelques règles pour que la review se passe bien :

| Règle | Détail |
|---|---|
| **Un seul objectif par PR** | Sépare les corrections de bugs et les nouvelles fonctionnalités |
| **Tests** | Ajoute au moins un test de fumée dans `tests/` si tu touches du code Python |
| **Commentaires en français** | Les commentaires dans le code sont en français (cohérence du projet) |
| **Pas de dépendances surprises** | Si tu as besoin d'une nouvelle lib, justifie-la dans la PR |
| **HTML valide** | Vérifie que les templates Jinja2 se rendent sans erreur |

### 3. Lancer les tests

```bash
pytest tests/ -v
```

Tous les tests doivent passer avant de soumettre.

### 4. Pousser et ouvrir une Pull Request

```bash
git push origin feat/nom-de-ma-fonctionnalite
```

Sur GitHub → **New Pull Request** → décris ce que tu as fait et pourquoi.

---

## Structure du code

```
app/routes/       → une route = une URL + sa logique
app/services/     → logique métier (ATT&CK, Sigma, couverture)
app/models/       → schémas de base de données (SQLModel)
app/templates/    → HTML (Jinja2)
app/static/       → style.css (une seule feuille de styles)
tests/            → tests pytest
```

**Convention de nommage :**
- Fichiers et variables : `snake_case`
- Classes SQLModel : `PascalCase`
- Routes : préfixe `/campaigns/`, `/techniques/`

---

## Signaler un bug

Ouvre une [issue](../../issues/new) avec :
1. Les étapes pour reproduire le bug
2. Le message d'erreur complet (logs uvicorn si applicable)
3. Ton OS et ta version de Python

---

## Proposer une fonctionnalité

Ouvre une [issue](../../issues/new) avec le label `enhancement` et décris :
1. Le problème que ça résout (pour quel type d'utilisateur)
2. La solution envisagée
3. Les alternatives que tu as considérées

---

## Code de conduite

Ce projet adopte le [Contributor Covenant](https://www.contributor-covenant.org/fr/).
En résumé : sois respectueux·se et constructif·ve.
