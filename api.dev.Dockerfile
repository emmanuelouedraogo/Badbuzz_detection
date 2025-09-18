# Utiliser une image Python slim comme base
FROM python:3.12

# Définir le répertoire de travail
WORKDIR /app

# Installer wget, nécessaire pour télécharger le modèle en développement
RUN apt-get update && apt-get install -y wget --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip
RUN pip install --upgrade pip

# Copier le fichier des dépendances et les installer
COPY requirements.txt .
RUN pip install -r requirements.txt

# Exposer le port
EXPOSE 5000

# La commande sera fournie par docker-compose.override.yml