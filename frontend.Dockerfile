# --- Stage 1: Builder ---
# Cette étape installe les dépendances Python dans un environnement temporaire.
FROM python:3.12-slim AS builder

WORKDIR /app

# Mettre à jour pip
RUN pip install --upgrade pip

# Copier uniquement le fichier des dépendances pour profiter du cache Docker.
COPY requirements-frontend.txt .

# Installer les dépendances en désactivant le cache pour réduire la taille de la couche.
RUN pip install --no-cache-dir -r requirements-frontend.txt


# --- Stage 2: Final Image ---
# Cette étape construit l'image de production finale, légère et sécurisée.
FROM python:3.12-slim

# Créer un utilisateur et un groupe non-root pour l'application
# L'option -m crée le répertoire personnel de l'utilisateur (/home/appuser),
# ce qui est essentiel pour que les applications puissent y écrire des fichiers de configuration.
RUN groupadd -r appgroup && useradd -r -m -g appgroup -s /bin/bash appuser

WORKDIR /app

# Copier les paquets Python installés depuis l'étape "builder".
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copier les exécutables (comme 'streamlit') depuis l'étape de build.
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code de l'application
COPY streamlit_app.py .

# Donner la propriété du répertoire à notre utilisateur non-root
RUN chown -R appuser:appgroup /app

# Changer d'utilisateur pour ne pas exécuter en tant que root
USER appuser

# Exposer le port sur lequel l'application écoute
EXPOSE 8501

# Commande pour démarrer le serveur Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]