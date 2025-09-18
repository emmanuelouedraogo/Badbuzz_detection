# --- Stage 1: Builder ---
# Cette étape installe les dépendances dans un environnement temporaire.
# Nous utilisons une image "slim" pour réduire la taille de base.
FROM python:3.12-slim AS builder

# Définir le répertoire de travail
WORKDIR /app

# Mettre à jour pip pour s'assurer d'avoir la dernière version
RUN pip install --upgrade pip

# Copier uniquement le fichier des dépendances pour profiter du cache Docker.
# Cette couche ne sera reconstruite que si requirements.txt change.
COPY requirements.txt .

# Installer les dépendances en désactivant le cache pip pour réduire la taille de la couche.
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final Image ---
# Cette étape construit l'image de production finale, légère et sécurisée.
FROM python:3.12-slim

# Installer curl, nécessaire pour le healthcheck dans docker-compose.
RUN apt-get update && apt-get install -y curl --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur et un groupe non-root pour l'application
RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/bash appuser

# Définir le répertoire de travail
WORKDIR /app

# Copier les paquets Python installés depuis l'étape "builder".
# C'est la magie du multi-stage : on ne récupère que le résultat, pas les couches de build.
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copier les exécutables (comme 'flask' et 'waitress-serve') depuis l'étape de build.
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code de l'application et le modèle de ML
COPY app.py .
COPY pipeline.joblib .

# Donner la propriété du répertoire à notre utilisateur non-root
RUN chown -R appuser:appgroup /app

# Changer d'utilisateur pour ne pas exécuter en tant que root
USER appuser

# Exposer le port sur lequel l'application écoute
EXPOSE 5000

# Commande pour démarrer le serveur de production Waitress
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]