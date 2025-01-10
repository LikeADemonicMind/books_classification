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

## 🚀 Lancer le Projet

Pour exécuter le projet, utilisez les commandes suivantes dans votre terminal (avec l'environnement activé) :
```bash
nohup uvicorn api_lm_svc:app --host 0.0.0.0 --port 29000 &
nohup uvicorn app:asgi_app --host 0.0.0.0 --port 8000 &
```
