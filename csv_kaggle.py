import os
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi

def download_kaggle_dataset(dataset, file_name):
    """
    Télécharge un fichier depuis un dataset Kaggle et extrait les données si nécessaire.

    :param dataset: Nom du dataset Kaggle (ex: 'mohamedbakhet/amazon-books-reviews').
    :param file_name: Nom du fichier à télécharger (ex: 'books_data.csv').
    """
    # Initialiser l'API Kaggle
    api = KaggleApi()
    api.authenticate()

    # Télécharger le fichier directement dans le répertoire courant
    print(f"Téléchargement du fichier {file_name} depuis le dataset {dataset}...")
    api.dataset_download_file(dataset, file_name, path=".")

    # Extraire le fichier si c'est un zip
    zip_path = f"{file_name}.zip"
    if os.path.exists(zip_path):
        print("Extraction du fichier zip...")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        os.remove(zip_path)
        print(f"Fichier extrait : {file_name}")
    else:
        print(f"Fichier téléchargé : {file_name}")

if __name__ == "__main__":
    # Spécifier le dataset et le fichier à télécharger
    dataset_name = "ishikajohari/best-books-10k-multi-genre-data"
    file_name = "goodreads_data.csv"

    # Télécharger et préparer les données
    download_kaggle_dataset(dataset_name, file_name)

    # Charger les données
    books_data = pd.read_csv(file_name)

    # Liste des catégories prioritaires
    priorities = ["Romance", "Fantasy", "Nonfiction", "Thriller", "Science Fiction"]

    # Fonction pour trouver la première catégorie prioritaire
    def extract_priority(genre_list, priorities):
        if isinstance(genre_list, str):
            # Convertir la chaîne en liste si nécessaire
            genre_list = eval(genre_list)
        # Chercher la première catégorie qui correspond
        for genre in genre_list:
            if genre in priorities:
                return genre
        return "Non classé"

    # Ajouter une nouvelle colonne avec la catégorie prioritaire
    books_data['genre'] = books_data['Genres'].apply(lambda x: extract_priority(x, priorities))
    books_data = books_data[books_data['genre'] != "Non classé"]
    books_data = books_data.dropna(subset=['Description'])
    books_data = books_data.rename(columns={'Description': 'description'})
    # Sauvegarder le fichier filtré
    books_data.to_csv("kaggle_books_data.csv", index=False, encoding="utf-8")
    os.remove(file_name)
    print("Books data filtered and saved to 'kaggle_books_data.csv'")
