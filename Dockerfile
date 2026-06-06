# --- Image de base ---
# On part d'une image Python officielle allégée (slim).
FROM python:3.12-slim

# Dossier de travail dans le conteneur.
WORKDIR /app

# On copie d'abord le fichier de dépendances seul (optimisation : Docker met en cache
# cette couche tant que requirements.txt ne change pas, ce qui accélère les rebuilds).
COPY requirements.txt .

# On installe les dépendances sans cache pip (garde l'image légère).
RUN pip install --no-cache-dir -r requirements.txt

# On copie ensuite tout le code de l'appli.
COPY . .

# Port exposé par l'appli.
EXPOSE 8000

# Commande lancée au démarrage du conteneur.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
