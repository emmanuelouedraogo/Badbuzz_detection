# Bad Buzz Detection 🧠✨

Ce projet est une application web d'analyse de sentiments qui utilise un modèle de deep learning (Bidirectional GRU) pour classifier un texte en **Positif** ou **Négatif**.

L'application est composée de deux parties :
1.  Une **API backend (Flask)** qui sert le modèle de machine learning.
2.  Une **interface utilisateur frontend (Streamlit)** qui permet d'interagir avec l'API.



## 🏛️ Architecture

-   **Frontend** : Streamlit - Fournit une interface web interactive et moderne.
-   **Backend** : Flask - Une micro-framework web pour exposer le modèle via une API REST.
-   **Modèle ML** : Un modèle Keras (`.keras`) entraîné pour l'analyse de sentiments.
-   **Serveur de Production** : Gunicorn - Un serveur WSGI pour exécuter l'application Flask en production.
-   **Hébergement** : Azure App Service - Pour le déploiement cloud de l'API.

## 🚀 Installation Locale

Suivez ces étapes pour lancer le projet sur votre machine locale.

### Prérequis

-   Python 3.8+
-   Git

### 1. Cloner le dépôt

```bash
git clone <url-du-depot>
cd badbuzz_detection
```

### 2. Créer un environnement virtuel

Il est fortement recommandé d'utiliser un environnement virtuel.

```bash
# Windows
python -m venv badbuzzenv
badbuzzenv\Scripts\activate

# macOS / Linux
python3 -m venv badbuzzenv
source badbuzzenv/bin/activate
```

### 3. Installer les dépendances

Installez toutes les bibliothèques nécessaires à partir du fichier `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 4. Placer les fichiers du modèle

Assurez-vous que votre modèle et votre tokenizer sont placés correctement dans le projet :

```
badbuzz_detection/
├── saved_model/
│   └── best_gensim_bidirectional_gru_en_model.keras  <-- VOTRE MODÈLE ICI
├── tokenizer.pickle                                  <-- VOTRE TOKENIZER ICI
├── app.py
└── streamlit_app.py
```

## ▶️ Lancement de l'application

Vous devez lancer deux processus dans deux terminaux distincts.

### 1. Lancer l'API Flask

Dans le premier terminal (avec l'environnement virtuel activé) :

```bash
python app.py
```

Le serveur démarrera sur `http://127.0.0.1:5000`. Vous devriez voir les logs indiquant que le modèle et le tokenizer ont été chargés.

### 2. Lancer l'interface Streamlit

Dans un second terminal (avec l'environnement virtuel activé) :

```bash
streamlit run streamlit_app.py
```

Votre navigateur devrait s'ouvrir automatiquement sur l'interface de l'application.

## ☁️ Déploiement sur Azure App Service

L'API Flask est conçue pour être déployée sur des services cloud comme Azure App Service.

1.  **Préparation** : Assurez-vous que `gunicorn` est dans `requirements.txt`.
2.  **Création des ressources** : Utilisez Azure CLI pour créer un Groupe de Ressources, un Plan App Service et une Web App.
3.  **Configuration** : Configurez la commande de démarrage de l'application sur Azure :
    ```bash
    az webapp config set --resource-group <rg-name> --name <app-name> --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
    ```
4.  **Déploiement** : Déployez le code via Git local en "pushant" sur le remote Azure.
    ```bash
    git push azure main
    ```

## 📝 Documentation de l'API

### Endpoint de prédiction

-   **URL** : `/predict`
-   **Méthode** : `POST`
-   **Description** : Analyse le sentiment du texte fourni.

#### Requête
-   **Headers** : `Content-Type: application/json`
-   **Body** (raw JSON) :
  ```json
  {
    "text": "This was a fantastic experience!"
  }
  ```

#### Réponse (Succès)
-   **Code** : `200 OK`
-   **Body** :
  ```json
  {
    "prediction": "Positive",
    "confidence_score": 0.0123
  }
  ```
  *Note : Le `confidence_score` est le score brut du modèle. Un score proche de 0 est "Positif", un score proche de 1 est "Négatif".*
