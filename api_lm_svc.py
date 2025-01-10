from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
import time
import pandas as pd
from sentence_transformers import SentenceTransformer
import joblib
from starlette.middleware.wsgi import WSGIMiddleware
from dashboard import app as dash_app
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
with open("api.pid", "w") as pid_file:
    pid_file.write(str(os.getpid()))

load_dotenv()

# Définir l'application et l'authentification
app = FastAPI()
security = HTTPBasic()


# Définir les entrées du modèle
class BookSummary(BaseModel):
    summary: str


# Intégration du tableau de bord Dash
app.mount("/dashboard", WSGIMiddleware(dash_app.server))

# Charger les modèles
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
classification_model = joblib.load("svc_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Fichier de logs pour les prédictions et les entraînements
LOG_FILE = "predictions_log.csv"
TRAINING_LOG_FILE = "training_logs.csv"

# Utilisateur et mot de passe par défaut
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return credentials


# Initialiser les fichiers CSV si nécessaire
def initialize_file(filepath, headers):
    try:
        if not os.path.exists(filepath):
            pd.DataFrame(columns=headers).to_csv(filepath, index=False)
    except Exception as e:
        print(f"Erreur lors de l'initialisation de {filepath} : {e}")


initialize_file(LOG_FILE, ["timestamp", "input_summary", "predicted_genre", "elapsed_time", "error"])
initialize_file(TRAINING_LOG_FILE, ["date", "params_tested", "best_params", "val_score", "test_score", "confusion_matrix", "replaced_model"])


# Fonction d'enregistrement des logs de prédiction
def log_prediction(summary, predicted_genre, elapsed_time, error=None):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_summary": summary,
        "predicted_genre": predicted_genre,
        "elapsed_time": round(elapsed_time, 2),
        "error": error,
    }
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as log_file:
        pd.DataFrame([log_entry]).to_csv(log_file, header=False, index=False)


# Endpoint pour prédire un genre
@app.post("/predict_genre/")
async def predict_genre(book: BookSummary, credentials: HTTPBasicCredentials = Depends(authenticate)):
    start_time = time.time()
    try:
        # Vérifier si le résumé est vide
        if not book.summary.strip():
            raise HTTPException(status_code=400, detail="Le résumé ne peut pas être vide.")

        # Générer l'embedding pour le résumé
        embedding = embedding_model.encode([book.summary])

        # Prédire le genre
        genre_encoded = classification_model.predict(embedding)[0]

        # Convertir l'encodage en genre lisible
        predicted_genre = label_encoder.inverse_transform([genre_encoded])[0]

        elapsed_time = time.time() - start_time

        # Ajouter aux logs
        log_prediction(
            summary=book.summary,
            predicted_genre=predicted_genre,
            elapsed_time=elapsed_time,
        )

        return {"predicted_genre": predicted_genre, "elapsed_time": f"{elapsed_time:.2f}s"}

    except HTTPException as e:
        # Renvoyer les erreurs HTTP telles quelles
        raise e
    except Exception as e:
        elapsed_time = time.time() - start_time

        # Ajouter l'erreur aux logs
        log_prediction(
            summary=book.summary,
            predicted_genre=None,
            elapsed_time=elapsed_time,
            error=str(e),
        )

        # Retourner une exception HTTP avec le détail de l'erreur
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")


# Fonction pour charger les logs d'entraînement
def load_training_logs():
    try:
        logs = pd.read_csv(TRAINING_LOG_FILE)
        logs["date"] = pd.to_datetime(logs["date"])  # Assurez-vous que la colonne "date" est en datetime
        return logs
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fichier de logs d'entraînement introuvable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des logs d'entraînement : {e}")


# Générer une matrice de confusion et la convertir en base64
def generate_confusion_matrix_image_from_log(confusion_matrix_str):
    try:
        # Convertir la chaîne JSON en matrice
        cm = json.loads(confusion_matrix_str)
        plt.figure(figsize=(10, 7))
        sns.heatmap(cm, annot=True, fmt="d", cmap="YlGnBu")
        plt.xlabel("Predicted Labels")
        plt.ylabel("True Labels")
        plt.title("Confusion Matrix")
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close()
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de la matrice de confusion : {e}")


@app.get("/training_logs_visual", response_class=HTMLResponse)
def display_training_logs(date: str = Query(None, description="Filtrer par date (YYYY-MM-DD)")):
    logs = load_training_logs()

    # Trier les logs par date décroissante
    logs = logs.sort_values(by="date", ascending=False)

    if date:
        logs = logs[logs["date"].dt.strftime("%Y-%m-%d").str.contains(date)]
        if logs.empty:
            raise HTTPException(status_code=404, detail="Aucun log trouvé pour cette date.")

    rows = []
    for _, log in logs.iterrows():
        # Déterminer le statut à partir de `is_replaced`
        status = "Accepté" if log["is_replaced"] else "Rejeté"
        status_color = "green" if status == "Accepté" else "red"

        # Générer l'image de la matrice de confusion avec un lien cliquable
        if "confusion_matrix" in log and pd.notna(log["confusion_matrix"]):
            confusion_matrix_img = (
                f'<a href="data:image/png;base64,{generate_confusion_matrix_image_from_log(log["confusion_matrix"])}" '
                f'target="_blank">'
                f'<img src="data:image/png;base64,{generate_confusion_matrix_image_from_log(log["confusion_matrix"])}" '
                f'width="200" alt="Confusion Matrix" />'
                f'</a>'
            )
        else:
            confusion_matrix_img = "N/A"

        row = f"""
        <div class="log">
            <div class="log-box">
                <h3>Date: {log["date"].strftime('%Y-%m-%d')}</h3>
                <p><strong>Parameters Tested:</strong> {log["params_tested"]}</p>
                <p><strong>Best Parameters:</strong> {log["best_params"]}</p>
                <p><strong>Validation Score:</strong> {log["val_score"]:.4f}</p>
                <p><strong>Test Score:</strong> {log["test_score"]:.4f}</p>
                <p><strong>Status:</strong> <span style="color: {status_color};">{status}</span></p>
            </div>
            <div class="matrix">{confusion_matrix_img}</div>
        </div>
        """
        rows.append(row)

    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    margin: 0;
                    padding: 20px;
                }}
                .log {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding: 15px;
                    border-radius: 10px;
                    background-color: #ffffff;
                    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .log-box {{
                    width: 60%;
                }}
                .matrix {{
                    width: 35%;
                    text-align: center;
                }}
                h3 {{
                    margin: 0 0 10px;
                    color: #333;
                }}
                p {{
                    margin: 5px 0;
                    color: #555;
                }}
                span {{
                    font-weight: bold;
                }}
                img {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 5px;
                    background-color: #f9f9f9;
                }}
                a {{
                    text-decoration: none;
                }}
                a:hover img {{
                    box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.3);
                }}
            </style>
        </head>
        <body>
            <h1>Training Logs</h1>
            {''.join(rows)}
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ps aux | grep uvicorn
