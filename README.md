# Projet de Classification de Livres

Ce projet utilise des modèles de traitement du langage naturel (NLP) pour classer les résumés de livres en fonction de leur genre. Il s'appuie sur `Flask` pour l'API, `Sentence Transformers` pour les embeddings, et inclut une interface utilisateur simple pour capturer les données et afficher les résultats.

---

## 📦 Installation

Pour utiliser ce projet, suivez ces étapes :

### 1. Cloner le dépôt
Clonez le répertoire en local :
```bash
git clone https://github.com/LikeADemonicMind/books_classification
cd books_classification
```

### 2. Créer un environnement virtuel
Créez un nouvel environnement virtuel pour isoler les dépendances et activez le ensuite. 

### 3. Installer les dépendances
pip install -r requirements.txt

## ⚙️ Configuration

Avant de démarrer l'application, configurez les variables d'environnement nécessaires :
Créer un fichier .env à la racine du projet en complétant les informations suivantes :
```env
GOODREADS_EMAIL=
GOODREADS_PASSWORD=
# Informations de connexion à la base de données PostgreSQL
PGHOST=dpg-ctenl8tds78s73dhlg9g-a.frankfurt-postgres.render.com         # Adresse du serveur PostgreSQL (ou domaine si hébergé)
PGPORT=5432               # Port utilisé par PostgreSQL (par défaut : 5432)
PGDATABASE=books_database_5p5t # Nom de la base de données que vous utilisez
PGUSER=books_database_5p5t_user          # Nom de l'utilisateur PostgreSQL
PGPASSWORD=  # Mot de passe de l'utilisateur PostgreSQL
ADMIN_USERNAME=
ADMIN_PASSWORD=
USERS={"username": "password"}
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM=
SMTP_PASSWORD=
SMTP_TO=
GOOGLE_API_KEY=
URI_MONGO_DB=
```


## Structure du projet

Voici une description des principaux fichiers et répertoires du projet :

### Fichiers principaux
- `README.md` : Documentation principale du projet.
- `requirements.txt` : Liste des dépendances nécessaires pour exécuter le projet.
- `app.py` : Script principal pour lancer l'application Flask.
- `api_lm_svc.py` : API exposant le modèle d'intelligence artificielle pour les prédictions.
- `dashboard.py` : Configuration et gestion du tableau de bord de monitoring Flask.
- `ci_cd_pipeline.py` : Script pour gérer la chaîne d'intégration et de livraison continues.
- `retrain.py` : Script pour réentraîner le modèle avec de nouvelles données.
- `script_maitre.py` : Script pour lancer tous les scripts de gestion de données ainsi que le script pour réentraîner le modèle d'intelligence artificielle.

### Données et modèles
- `feedback_logs.json` : Fichier journal des retours utilisateur (feedback loop).
- `training_logs.csv` : Historique des réentraînements du modèle.
- `model_score.json` : Score du modèle actuellement en service.
- `svc_model.pkl` : Modèle SVC entraîné pour la prédiction des genres.
- `label_encoder.pkl` : Encodeur des labels de genres.

### Scripts de gestion des données
- `csv_kaggle.py` : Script pour traiter les données CSV récupérées de Kaggle.
- `google_books_api_fetch.py` : Script pour collecter des données via l'API Google Books.
- `mongodb_data_fetch.py` : Script pour récupérer des données depuis MongoDB.
- `postgredb_data_fetch.py` : Script pour récupérer des données depuis PostgreSQL.
- `scraping.py` : Script pour collecter des données via du web scraping.


### Fichiers journaux
- `output.log` et `debug.log` : Journaux d'exécution et de débogage.
- `predictions_log.csv` : Historique des prédictions effectuées.
- `nohup.out` : Fichier de sortie des commandes exécutées en arrière-plan.

### Tests
- `test_api.py` : Tests pour vérifier le bon fonctionnement de l'API.
- `test_app.py` : Tests pour l'application Flask.
- `test_ids.pkl` : Identifiants des données de test pour assurer une cohérence lors des réentraînements.

### Répertoires
- `__pycache__/` : Répertoire contenant les fichiers Python compilés.
- `assets/` : Répertoire pour les ressources additionnelles (images, styles, etc.).
- `images/` : Répertoire contenant les images utilisées par l'application ou générées.
- `static/` : Fichiers statiques (CSS, JavaScript, etc.) pour l'application Flask.
- `templates/` : Modèles HTML pour l'application Flask.

### Divers
- `flask_monitoringdashboard.db` : Base de données pour le monitoring de l'application.
- `app.pid` et `api.pid` : Fichiers contenant les identifiants des processus pour redémarrer les services.

## 🚀 Lancer le Projet

Pour exécuter le projet, utilisez les commandes suivantes dans votre terminal (avec l'environnement activé) :
```bash
nohup uvicorn api_lm_svc:app --host 0.0.0.0 --port 29000 &
nohup uvicorn app:asgi_app --host 0.0.0.0 --port 8000 &
```
### Accès à l'application sur téléphone
Pour accéder à l'application sur un téléphone, vous pouvez utiliser [ngrok](https://ngrok.com) pour exposer localement votre serveur Flask. Après avoir lancé l'application en local, exécutez la commande suivante :

```bash
ngrok http 8000
```
Cela générera une URL publique que vous pourrez utiliser pour accéder à l'application depuis n'importe quel appareil connecté.