# PurpleForge Compagnon — Instructions pour Claude Code

> Document à envoyer à Claude Code au démarrage du projet. Il décrit **quoi** construire, **comment**, et **dans quel ordre**. À garder à la racine du dépôt sous le nom `CLAUDE.md` pour que Claude Code le lise automatiquement.

---

## 0. À lire en premier (consignes de collaboration)

Je suis **débutante en Python** (et en PowerShell). Merci de :

1. **Expliquer chaque étape** avant de coder : ce qu'on va faire et pourquoi.
2. Avancer **par petits incréments testables**, jamais 10 fichiers d'un coup.
3. **Commenter le code en français**, simplement.
4. Après chaque morceau, me dire **comment le lancer et le vérifier** (commande exacte).
5. Si un choix technique se présente, me proposer **une option recommandée** et l'expliquer en une phrase, plutôt que de me noyer dans les alternatives.
6. Privilégier la **simplicité** à l'élégance. Pas de magie, pas d'abstractions prématurées.

---

## 0bis. Exigence de design et d'expérience utilisateur (NON NÉGOCIABLE)

Le design des pages et l'expérience utilisateur sont une **exigence forte**, au même niveau que le bon fonctionnement. Un outil puissant mais moche ou confus ne sera pas adopté. Concrètement :

- **Soigner chaque écran** : mise en page claire, hiérarchie visuelle, espacements généreux, cohérence partout.
- **Respecter la charte graphique (section 8)** sur toutes les pages, sans exception.
- **Navigation intuitive** : on doit comprendre où on est et quoi faire sans réfléchir.
- **Responsive** : lisible sur grand écran comme sur petit.
- **Accessibilité** : contrastes suffisants, libellés clairs, jamais la couleur seule pour porter une information.
- **Feedback** : chaque action donne un retour visuel (chargement, succès, erreur), facile avec HTMX.
- **Finition** : aucune page brute non stylée ; même les états vides et les messages d'erreur sont soignés.

Avant de me livrer un écran, demande-toi : « est-ce que je serais fière de le montrer à un pair ou à la communauté ? » Si non, on le peaufine.

---

## 1. Le projet en une phrase

PurpleForge Compagnon est un **outil web open-source de purple teaming** : il prend en entrée les techniques d'attaque jouées par une red team (référentiel **MITRE ATT&CK**) et produit en sortie des **règles de détection Sigma**, la liste des **logs nécessaires**, et une **carte de couverture** collaborative entre red et blue team.

**Boucle de valeur :** TTP joué → détection suggérée → testée/déployée → couverture mise à jour, partagée.

---

## 2. Stack technique (imposée)

| Couche | Choix | Remarque |
|---|---|---|
| Langage | **Python 3.11+** | un seul langage pour tout le projet |
| Backend / API | **FastAPI** | doc auto, moderne, pédagogique |
| Serveur | **Uvicorn** | serveur ASGI de dev |
| Frontend | **HTMX + Jinja2** | pas de framework JS, tout reste en Python |
| Templates | Jinja2 (fournis par FastAPI) | |
| Base de données | **SQLite** (puis PostgreSQL) | SQLite = zéro config pour démarrer |
| ORM | **SQLModel** | écrit par l'auteur de FastAPI, simple pour débuter |
| Données ATT&CK | **mitreattack-python** | charge le référentiel MITRE |
| Règles de détection | **pySigma** + dépôt **SigmaHQ** | standards du domaine |
| Conteneurisation | **Docker** + docker-compose | installation en une commande |
| Tests | **pytest** | tests simples dès le MVP |

> Important : **ne pas introduire React, Vue, ni de build front JavaScript.** L'interactivité passe uniquement par HTMX.

---

## 3. Architecture cible

```
[ Navigateur ]
      |  (HTML + HTMX)
      v
[ FastAPI (Python) ] --- templates Jinja2
      |
      +-- services/        logique métier
      |     |-- attack.py   (données MITRE ATT&CK)
      |     |-- sigma.py    (suggestion de règles Sigma)
      |     |-- coverage.py (calcul de la couverture)
      |
      +-- models/          tables SQLModel
      |
      v
[ SQLite -> PostgreSQL ]
```

Un seul service backend. **Pas de microservices.**

---

## 4. Structure du dépôt (à créer en Phase 0)

```
purpleforge-compagnon/
├── CLAUDE.md                 # ce document
├── README.md
├── LICENSE                   # MIT
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .gitignore
├── app/
│   ├── main.py               # point d'entrée FastAPI
│   ├── database.py           # connexion + init SQLite
│   ├── models/
│   │   ├── campaign.py
│   │   ├── technique.py
│   │   └── detection.py
│   ├── services/
│   │   ├── attack.py
│   │   ├── sigma.py
│   │   └── coverage.py
│   ├── routes/
│   │   ├── campaigns.py
│   │   └── techniques.py
│   ├── templates/            # Jinja2 (.html)
│   │   ├── base.html
│   │   ├── campaign.html
│   │   └── partials/         # fragments HTMX
│   └── static/
│       └── style.css         # charte graphique (section 8)
├── data/                     # données ATT&CK, règles Sigma (cache local)
└── tests/
    └── test_smoke.py
```

---

## 5. Modèle de données (MVP)

Trois entités principales :

**Campaign** — un engagement purple team.
- `id`, `name`, `description`, `created_at`

**TechniqueEntry** — une technique jouée dans une campagne.
- `id`, `campaign_id` (FK), `attack_id` (ex. `T1003.001`), `name`, `tactic`
- `red_note` (ce qu'a fait la red team), `played_at`
- `status` : `non_detecte` | `a_construire` | `detecte`
- `blue_note` (annotation de la blue team)

**DetectionSuggestion** — détection proposée pour une technique.
- `id`, `technique_entry_id` (FK), `sigma_title`, `sigma_yaml`
- `required_logs` (ex. « Sysmon Event ID 10 »), `source` (`sigmahq` | `genere`)

---

## 6. Périmètre du MVP (ce qu'on construit d'abord)

User stories à livrer, dans l'ordre :

1. **Créer une campagne** et la lister.
2. **Voir une matrice ATT&CK** (au moins les tactiques + techniques principales) et **ajouter une technique** à la campagne par un clic.
3. Pour une technique ajoutée, **afficher les règles Sigma suggérées** depuis SigmaHQ et les **logs nécessaires**.
4. **Changer le statut** d'une technique (non détecté / à construire / détecté) et **ajouter une note** blue team — sans recharger la page (HTMX).
5. **Carte de couverture** : vue d'ensemble colorée des techniques de la campagne par statut.
6. **Export** : un bouton qui produit un JSON compatible ATT&CK Navigator + un backlog des détections.

> Hors MVP (V2, ne pas commencer maintenant) : import Atomic Red Team / Caldera, parsing de rapport PDF, scorecard, connecteurs SIEM.

---

## 7. Plan de développement par phases

### Phase 0 — Fondations (commencer ici)
1. Créer la structure du dépôt (section 4) + `.gitignore` + `LICENSE` (MIT).
2. `requirements.txt` avec : fastapi, uvicorn, sqlmodel, jinja2, python-multipart, mitreattack-python, pysigma, pytest.
3. `app/main.py` : un FastAPI minimal qui sert une page « Hello » avec `base.html`.
4. `database.py` : créer la base SQLite et les tables au démarrage.
5. Dockerfile + docker-compose pour lancer en une commande.
6. **Vérification :** `uvicorn app.main:app --reload` affiche la page d'accueil.

### Phase 1 — Campagnes + techniques
1. Modèles `Campaign` et `TechniqueEntry`.
2. Routes : créer/lister une campagne ; page d'une campagne.
3. Charger les données ATT&CK via `services/attack.py` et afficher une matrice cliquable.
4. Ajouter une technique à une campagne (formulaire HTMX, sans rechargement).
5. **Vérification :** je peux créer « Campagne test », cliquer T1003.001, la voir apparaître.

### Phase 2 — Détections + couverture
1. `services/sigma.py` : pour un `attack_id`, retrouver les règles Sigma de SigmaHQ correspondantes + extraire les logs requis.
2. Afficher les suggestions sous la technique.
3. Boutons HTMX : changer le statut, enregistrer la note blue team.
4. `services/coverage.py` + page « carte de couverture » colorée.
5. Export JSON Navigator + backlog.
6. **Vérification :** le parcours complet de l'exemple Mimikatz/LSASS fonctionne de bout en bout.

### Phase 3 — Publication
README clair, captures d'écran, instructions d'installation Docker, licence MIT, guide de contribution.

---

## 8. Charte graphique (pour `static/style.css`)

Style **plat, épuré, sans ombres ni dégradés.**

| Usage | Couleur |
|---|---|
| Violet principal (accent, titres, en-têtes) | `#6A1B9A` |
| Violet foncé (accents secondaires) | `#4A148C` |
| Statut « Détecté » — fond / texte | `#E1F5EE` / `#085041` |
| Statut « Non détecté » — fond / texte | `#FCEBEB` / `#A32D2D` |
| Statut « À construire » — fond / texte | `#FAEEDA` / `#854F0B` |
| Red team — fond / texte | `#FBEAF0` / `#72243E` |
| Blue team — fond / texte | `#E6F1FB` / `#0C447C` |
| Texte principal | `#2C2C2A` |
| Texte secondaire | `#5A5A5A` |
| Bordures / séparateurs | `#CCCCCC` |

Règles :
- Police interface : **Arial / sans-serif**, deux graisses seulement (normale, semi-grasse).
- Police code et règles Sigma : **monospace**.
- Coins arrondis : **8 px** sur les éléments, **12 px** sur les cartes.
- Les statuts sont **toujours accompagnés du libellé texte** (jamais la couleur seule — accessibilité).
- Couleurs de rôle : rose = red team, bleu = blue team, violet = identité de l'appli.

---

## 9. Conventions de code

- Noms de variables et fonctions **en anglais**, commentaires **en français**.
- Fonctions courtes, une responsabilité par fonction.
- Pas de dépendance ajoutée sans me l'expliquer d'abord.
- Chaque nouvelle fonctionnalité s'accompagne d'**au moins un test pytest** simple.
- Secrets et config via variables d'environnement (jamais en dur dans le code).

---

## 10. Definition of done (MVP)

Le MVP est « fini » quand, sur une machine vierge :

1. `docker-compose up` lance l'application.
2. Je peux créer une campagne, y ajouter une technique ATT&CK par clic.
3. Je vois les règles Sigma suggérées et les logs nécessaires.
4. Je peux changer le statut et annoter sans recharger la page.
5. La carte de couverture reflète les statuts en couleur.
6. L'export JSON Navigator se télécharge.
7. `pytest` passe au vert.

---

## 11. Première demande à Claude Code

> « Commençons par la **Phase 0**. Explique-moi d'abord le rôle de chaque fichier qu'on va créer, puis génère la structure du dépôt, le `requirements.txt`, un `app/main.py` FastAPI minimal qui sert une page d'accueil avec Jinja2, et dis-moi la commande exacte pour la lancer et vérifier que ça marche. »
