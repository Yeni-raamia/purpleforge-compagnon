# ─── Étape 1 : image de base Python légère ───────────────────────────────────
# python:3.12-slim = Python 3.12 sans les outils de build (image ~60 Mo).
FROM python:3.12-slim

# ─── Dossier de travail à l'intérieur du conteneur ───────────────────────────
WORKDIR /app

# ─── Dépendances Python ───────────────────────────────────────────────────────
# On copie d'abord requirements.txt seul (couche Docker mise en cache si
# requirements.txt n'a pas changé, ce qui accélère les rebuilds).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Code de l'application ────────────────────────────────────────────────────
COPY app/ app/

# ─── Dossier data/ persistant (ATT&CK + Sigma téléchargés au 1er démarrage) ──
# Le volume sera monté depuis docker-compose.yml pour survivre aux redémarrages.
RUN mkdir -p data

# ─── Port exposé ──────────────────────────────────────────────────────────────
EXPOSE 8000

# ─── Commande de démarrage ────────────────────────────────────────────────────
# --host 0.0.0.0 = accessible depuis l'extérieur du conteneur.
# --workers 1    = un seul worker (cache ATT&CK en mémoire partagé).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
