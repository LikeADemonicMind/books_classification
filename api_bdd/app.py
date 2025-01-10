from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os 

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

# Initialiser l'application FastAPI
app = FastAPI(
    title="Books API",
    description="Une API REST pour gérer les données de livres avec authentification simple",
    version="1.0.0",
)

# Configuration Basic Auth
security = HTTPBasic()
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Vérification des identifiants
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Connexion PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password=DB_PASSWORD,
            host="db.boiayreqovzmageqecos.supabase.co",
            port="5432"
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion à la base de données : {str(e)}")

# Modèle de données pour les livres
class Book(BaseModel):
    id: int
    title: str
    description: str
    genre: str

@app.get("/", summary="Bienvenue")
def home():
    return {"message": "Bienvenue sur l'API Books REST. Consultez /docs pour plus d'informations!"}

@app.get("/books", response_model=List[Book], summary="Récupérer tous les livres")
def get_books(username: str = Depends(authenticate)):
    try:
        # Connexion à la base de données
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Exécuter la requête pour récupérer tous les livres
        query = "SELECT id, title, description, genre FROM books_table;"
        cur.execute(query)
        books = cur.fetchall()
        
        # Fermer les connexions
        cur.close()
        conn.close()
        
        # Retourner les résultats
        return books
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")
