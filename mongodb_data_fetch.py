import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()
def fetch_books_from_mongodb_by_genre(uri, db_name, collection_name, genre, limit=1000):
    """
    Récupère les derniers documents correspondant à un genre spécifique depuis MongoDB.

    :param uri: URI de connexion MongoDB.
    :param db_name: Nom de la base de données MongoDB.
    :param collection_name: Nom de la collection MongoDB.
    :param genre: Genre à filtrer.
    :param limit: Nombre maximum de documents à récupérer pour le genre.
    :return: DataFrame contenant les documents récupérés pour le genre.
    """
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    # Requête MongoDB pour filtrer par un genre spécifique
    query = {"genre": genre}
    print(query)
    cursor = collection.find(query).sort("_id", -1).limit(limit)

    # Convertir les documents en DataFrame
    books = list(cursor)
    if books:
        return pd.DataFrame(books)
    else:
        print(f"Aucun document trouvé pour le genre : {genre}")
        return pd.DataFrame()

if __name__ == "__main__":
    # URI de connexion MongoDB
    uri = os.getenv("URI_MONGO_DB")
    db_name = "books_db"
    collection_name = "books_collection"  # Remplacez par le nom réel de votre collection

    # Liste des catégories prioritaires
    priorities = ["Romance", "Fantasy", "Nonfiction", "Thriller", "Science Fiction"]

    all_books = []

    # Récupérer 1000 documents pour chaque genre
    for genre in priorities:
        print(f"Récupération des documents pour le genre : {genre}")
        genre_books = fetch_books_from_mongodb_by_genre(uri, db_name, collection_name, genre, limit=1000)
        if not genre_books.empty:
            all_books.append(genre_books)

    # Combiner toutes les données et sauvegarder dans un fichier CSV
    if all_books:
        combined_books = pd.concat(all_books, ignore_index=True)
        combined_books = combined_books.rename(columns={'desc': 'description'})
        combined_books.to_csv("mongodb_filtered_books_by_genre.csv", index=False, encoding="utf-8")
        print("Filtered books by genre saved to 'mongodb_filtered_books_by_genre.csv'")
    else:
        print("Aucun livre récupéré pour les genres spécifiés.")
