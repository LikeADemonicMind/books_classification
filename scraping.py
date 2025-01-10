import os
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

# Charger les identifiants Goodreads depuis le fichier .env
load_dotenv()
GOODREADS_EMAIL = os.getenv("GOODREADS_EMAIL")
GOODREADS_PASSWORD = os.getenv("GOODREADS_PASSWORD")

def setup_driver():
    """Configurer et retourner un driver Selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode sans tête pour plus de rapidité
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver

def login_to_goodreads(driver):
    """Connecter à Goodreads via Selenium."""
    driver.get("https://www.goodreads.com/user/sign_in")
    try:
        # Cliquer sur 'Sign in with email'
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in with email')]"))
        ).click()

        # Remplir le formulaire de connexion
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ap_email")))
        driver.find_element(By.ID, "ap_email").send_keys(GOODREADS_EMAIL)
        driver.find_element(By.ID, "ap_password").send_keys(GOODREADS_PASSWORD)
        driver.find_element(By.ID, "ap_password").submit()

        # Attendre la connexion réussie
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "siteHeader__personal")))
        print("Connexion réussie à Goodreads.")
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        driver.quit()

def get_book_links(driver, genre_url):
    """Récupérer tous les liens des livres depuis une page."""
    driver.get(genre_url)
    book_links = []
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".coverWrapper a")))
        links = driver.find_elements(By.CSS_SELECTOR, ".coverWrapper a")
        for link in links:
            book_links.append(link.get_attribute("href"))
    except Exception as e:
        print(f"Erreur lors de la récupération des liens : {e}")
    print(f"{len(book_links)} liens récupérés.")
    return book_links

def get_book_details(driver, book_url):
    """Récupérer le titre et la description d'un livre."""
    try:
        driver.get(book_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # Récupérer le titre
        title_element = driver.find_element(By.CSS_SELECTOR, 'h1[data-testid="bookTitle"]')
        title = title_element.text.strip() if title_element else "Titre non trouvé"

        # Récupérer la description
        try:
            description_element = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="description"]')
            description = description_element.text.strip()
        except:
            description = "Description non trouvée"

        print(f"Récupéré : {title}")
        return {"title": title, "description": description, "link": book_url}

    except Exception as e:
        print(f"Erreur lors de la récupération des détails pour {book_url}: {e}")
        return {"title": "Erreur", "description": "Erreur", "link": book_url}

def scrape_genre(genre, max_books=10):
    """Scraper les nouvelles sorties pour un genre donné."""
    driver = setup_driver()
    login_to_goodreads(driver)

    genre_url = f"https://www.goodreads.com/genres/new_releases/{genre}"
    print(f"--- Scraping des livres pour le genre : {genre} ---")
    book_links = get_book_links(driver, genre_url)

    books_data = []
    for i, book_url in enumerate(book_links[:max_books]):
        print(f"[{i+1}/{len(book_links[:max_books])}] Récupération des détails...")
        book_details = get_book_details(driver, book_url)
        book_details["genre"] = genre
        books_data.append(book_details)
        time.sleep(random.uniform(2, 4))  # Pause aléatoire pour éviter le blocage

    driver.quit()
    return books_data

if __name__ == "__main__":
    genres = ["romance", "fantasy", "non-fiction", "science-fiction", "thriller"]
    max_books_per_genre = 1  # Nombre de livres à récupérer par genre
    all_books = []

    for genre in genres:
        books = scrape_genre(genre, max_books=max_books_per_genre)
        all_books.extend(books)

    # Sauvegarder les résultats dans un fichier CSV
    df = pd.DataFrame(all_books)
    df['genre'] = df['genre'].replace({
    'non-fiction': 'nonfiction',
    'science-fiction': 'science fiction'
    })
    df.to_csv("goodreads_new_releases.csv", index=False)
    print("Scraping terminé. Données sauvegardées dans 'goodreads_new_releases.csv'.")
