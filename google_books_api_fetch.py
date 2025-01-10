import requests
import time
import pandas as pd
from dotenv import load_dotenv
import os 

load_dotenv()
# Votre clé API Google Books
API_KEY = os.getenv("GOOGLE_API_KEY")

# Liste des genres
genres = ['Romance', 'Fantasy', 'Nonfiction', 'Thriller', 'Science Fiction']

# URL de base pour l'API Google Books
BASE_URL = "https://www.googleapis.com/books/v1/volumes"

# Fonction pour récupérer des livres pour un genre donné
def fetch_books_for_genre(genre, max_results=1000):
    books = []
    start_index = 0
    results_per_request = 40  # L'API autorise un maximum de 40 par requête

    while start_index < max_results:
        print(f"Fetching books for genre: {genre}, start_index: {start_index}")

        params = {
            "q": f"subject:{genre}",
            "startIndex": start_index,
            "maxResults": min(results_per_request, max_results - start_index),
            "key": API_KEY
        }

        response = requests.get(BASE_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                books.extend(data["items"])
                start_index += len(data["items"])
            else:
                print(f"No more books found for genre: {genre}")
                break
        else:
            print(f"Error fetching books for genre: {genre}, status code: {response.status_code}")
            break

        # Pause pour respecter les limites de l'API
        time.sleep(1)

    return books

if __name__ == "__main__":
    # Récupérer les livres pour chaque genre
    all_books = []

    for genre in genres:
        books = fetch_books_for_genre(genre)
        for book in books:
            book_info = {
                "genre": genre,
                "title": book["volumeInfo"].get("title", "No Title"),
                "description": book["volumeInfo"].get("description", "No Description"),
                "authors": ", ".join(book["volumeInfo"].get("authors", ["Unknown"])),
                "publishedDate": book["volumeInfo"].get("publishedDate", "Unknown")
            }
            all_books.append(book_info)

    # Sauvegarder les résultats dans un DataFrame
    df = pd.DataFrame(all_books)
    df = df[df.description != "No Description"]
    # Sauvegarder dans un fichier CSV
    df.to_csv("books_by_genre_api.csv", index=False, encoding="utf-8")
    print("Books saved to 'books_by_genre_api.csv'")
