import os
import subprocess
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Configuration de la base PostgreSQL
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "e3Oji2ChrCZjLc43",
    "host": "db.boiayreqovzmageqecos.supabase.co",
    "port": "5432"
}

# Nom de la table PostgreSQL
TABLE_NAME = "books_table"

# Scripts à exécuter
SCRIPTS = [
    "google_books_api_fetch.py",
    "csv_kaggle.py",
    "mongodb_data_fetch.py",
    "postgredb_data_fetch.py",
    "scraping.py"
]

def execute_scripts(scripts):
    """
    Exécute chaque script dans la liste fournie.
    """
    for script in scripts:
        try:
            print(f"Exécution de {script}...")
            subprocess.run(["python", script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'exécution du script {script}: {e}")

def load_and_prepare_data(file_paths):
    """
    Charge les fichiers CSV produits par les scripts et prépare les données.
    """
    all_data = []
    for file_path in file_paths:
        if os.path.exists(file_path):
            print(f"Chargement des données depuis {file_path}...")
            df = pd.read_csv(file_path)

            # Mettre les genres en majuscules
            if "genre" in df.columns:
                df["genre"] = df["genre"].str.title()

            all_data.append(df)
        else:
            print(f"Fichier introuvable : {file_path}")

    # Combiner toutes les données
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def insert_data_into_postgres(df, table_name, db_config):
    """
    Insère les données dans PostgreSQL si elles n'existent pas déjà.
    """
    if df.empty:
        print("Aucune donnée à insérer.")
        return

    # Connexion à PostgreSQL
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    # Préparer les colonnes et les données pour l'insertion
    columns = ["title", "description", "genre"]
    values = [tuple(row) for row in df[columns].to_numpy()]

    # Requête SQL avec "ON CONFLICT" pour éviter les doublons
    insert_query = f"""
    INSERT INTO {table_name} ({', '.join(columns)}) 
    VALUES %s 
    ON CONFLICT (title) DO NOTHING;
    """

    try:
        # Insérer les données
        execute_values(cur, insert_query, values)
        conn.commit()
        print(f"Les données ont été insérées avec succès dans la table '{table_name}'.")
    except Exception as e:
        print(f"Erreur lors de l'insertion des données : {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def cleanup_csv_files(file_paths):
    """
    Supprime les fichiers CSV après leur traitement.
    """
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Fichier supprimé : {file_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {file_path} : {e}")

          

if __name__ == "__main__":
    
    # Étape 1 : Exécuter les 5 scripts
    execute_scripts(SCRIPTS)

    # Étape 2 : Charger et préparer les données des fichiers produits
    file_paths = [
        "books_by_genre_api.csv",
        "kaggle_books_data.csv",
        "mongodb_filtered_books_by_genre.csv",
        "postgres_filtered_books_by_genre.csv",
        "goodreads_new_releases.csv"
    ]
    combined_data = load_and_prepare_data(file_paths)

    # Étape 3 : Insérer les données dans PostgreSQL
    insert_data_into_postgres(combined_data, TABLE_NAME, DB_CONFIG)

    cleanup_csv_files(file_paths)

    print("Ingestion complète des données.")
    

    try:
        subprocess.run(
            ["python", "retrain.py"],
            check=True,
            cwd="."  # Répertoire où se trouve retrain.py
        )
        print("Script retrain.py exécuté avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de retrain.py : {e}")
    except FileNotFoundError:
        print("Le script retrain.py ou son répertoire n'a pas été trouvé.")

