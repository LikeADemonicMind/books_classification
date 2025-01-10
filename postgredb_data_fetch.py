import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

def fetch_books_from_postgres(genres, limit=1000):
    """
    Récupère les derniers livres pour chaque genre depuis la base PostgreSQL.

    :param genres: Liste des genres à récupérer.
    :param limit: Nombre maximum de livres par genre.
    :return: DataFrame contenant les livres récupérés.
    """
    # Connexion à la base PostgreSQL
    conn = psycopg2.connect(
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT")
    )
    cur = conn.cursor()

    all_books = []

    for genre in genres:
        print(f"Récupération des livres pour le genre : {genre}")

        # Requête SQL pour récupérer les derniers livres par genre
        query = f"""
        SELECT b.title, b.description, g.genre, a.name AS author
        FROM books_infos b
        JOIN genres g ON b.genre_id = g.id
        JOIN book_authors ba ON b.id = ba.book_id
        JOIN authors a ON ba.author_id = a.id
        WHERE g.genre = %s AND b.description IS NOT NULL
        ORDER BY b.id DESC
        LIMIT %s
        """
        cur.execute(query, (genre, limit))
        rows = cur.fetchall()

        # Convertir les résultats en DataFrame
        if rows:
            df = pd.DataFrame(rows, columns=["title", "description", "genre", "author"])
            all_books.append(df)
        else:
            print(f"Aucun livre trouvé pour le genre : {genre}")

    cur.close()
    conn.close()

    if all_books:
        return pd.concat(all_books, ignore_index=True)
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    # Liste des catégories prioritaires
    priorities = ["Romance", "Fantasy", "Nonfiction", "Thriller", "Science Fiction"]

    # Récupérer les livres depuis PostgreSQL
    books_data = fetch_books_from_postgres(priorities, limit=1000)

    # Sauvegarder les résultats dans un fichier CSV
    if not books_data.empty:
        books_data.to_csv("postgres_filtered_books_by_genre.csv", index=False, encoding="utf-8")
        print("Filtered books by genre saved to 'postgres_filtered_books_by_genre.csv'")
    else:
        print("Aucun livre récupéré pour les genres spécifiés.")
