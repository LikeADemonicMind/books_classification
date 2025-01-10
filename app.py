import os
import json
import time
import cv2
import pytesseract
import base64
import requests
from flask import Flask, render_template, jsonify, redirect, url_for, request
from flask_httpauth import HTTPBasicAuth
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from asgiref.wsgi import WsgiToAsgi
import flask_monitoringdashboard as dashboard
import logging
from logging.handlers import SMTPHandler
from dotenv import load_dotenv
load_dotenv()
# Configuration
LOG_FILE = "feedback_logs.json"
IMAGES_DIR = "images"
API_URL = "http://127.0.0.1:29000/predict_genre/"
API_USERNAME = os.getenv("ADMIN_USERNAME")  # Identifiant pour l'API
API_PASSWORD = os.getenv("ADMIN_PASSWORD")  # Mot de passe pour l'API

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as file:
        json.dump([], file)

with open("app.pid", "w") as pid_file:
    pid_file.write(str(os.getpid()))

# Initialisation
app = Flask(__name__)
auth = HTTPBasicAuth()

# Utilisateurs autorisés pour l'application Flask
users_json = os.getenv("USERS")
users = json.loads(users_json) if users_json else {}

logger = logging.getLogger('flask_app')
logger.setLevel(logging.ERROR)  # Log uniquement les erreurs critiques

# Configuration de l'alerte email
mail_handler = SMTPHandler(
    mailhost=(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))),  # SMTP server and port
    fromaddr=os.getenv("SMTP_FROM"),  # Sender email address
    toaddrs=[os.getenv("SMTP_TO")],  # List of recipient email addresses
    subject='[ALERTE Flask] Une erreur critique est survenue',  # Email subject
    credentials=(os.getenv("SMTP_FROM"), os.getenv("SMTP_PASSWORD")),  # Gmail login credentials
    secure=()  # Enable secure connection
)
mail_handler.setLevel(logging.ERROR)  # Envoie des e-mails pour les erreurs de niveau ERROR et supérieur
  

logger.addHandler(mail_handler)


@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None


@auth.error_handler
def unauthorized():
    return jsonify({"error": "Accès non autorisé. Veuillez vérifier vos identifiants."}), 401


# Fonction pour traduire du français vers l'anglais
def translate(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        translated = model.generate(**inputs)
    translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True)
    return translated_text[0] if translated_text else ""


# Fonction pour sauvegarder les logs dans un fichier JSON
def save_log(new_log):
    with open(LOG_FILE, "r") as file:
        logs = json.load(file)

    for log in logs:
        if log["timestamp"] == new_log["timestamp"]:
            log.update(new_log)
            break
    else:
        logs.append(new_log)

    with open(LOG_FILE, "w") as file:
        json.dump(logs, file, indent=4)


# Appeler l'API avec authentification
def call_api(summary):
    try:
        response = requests.post(
            API_URL,
            json={"summary": summary},
            auth=(API_USERNAME, API_PASSWORD)  # Ajouter l'authentification ici
        )
        response.raise_for_status()
        return response.json().get("predicted_genre", "Genre inconnu")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API : {e}")
        return "Erreur API"
    

@app.errorhandler(500)
def handle_500_error(e):
    logger.error('Erreur 500 détectée', exc_info=e)  # Log l'erreur avec les détails
    return "Erreur interne", 500


@app.errorhandler(Exception)
def handle_generic_error(e):
    logger.error('Erreur inattendue détectée', exc_info=e)  # Log toutes les autres exceptions
    return "Une erreur est survenue", 500


@app.route("/")
@auth.login_required
def index():
    return render_template("index.html")


@app.route("/cause_error")
def cause_error():
    1 / 0


@app.route("/capture", methods=["POST"])
@auth.login_required
def capture():
    image_data = request.form["image"]
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)
    timestamp = str(time.time_ns())
    image_path = os.path.join(IMAGES_DIR, f"{timestamp}.jpg")

    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    save_log({
        "timestamp": timestamp,
        "image_path": image_path,
        "ocr_text": None,
        "translated_text": None,
        "predicted_genre": None,
        "feedback": None,
    })

    return redirect(url_for("processing", timestamp=timestamp))


@app.route("/processing/<timestamp>")
@auth.login_required
def processing(timestamp):
    return render_template("processing.html", timestamp=timestamp)


@app.route("/process_data/<timestamp>")
@auth.login_required
def process_data(timestamp):
    image_path = os.path.join(IMAGES_DIR, f"{timestamp}.jpg")
    if not os.path.exists(image_path):
        return redirect(url_for("result", timestamp=timestamp))

    frame = cv2.imread(image_path)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    ocr_text = pytesseract.image_to_string(thresh, lang="fra").strip()
    if not ocr_text:
        ocr_text = "Erreur : Aucun texte détecté."

    try:
        translated_text = translate(ocr_text)
    except Exception as e:
        print(f"Erreur lors de la traduction : {e}")
        translated_text = "Erreur de traduction."

    predicted_genre = call_api(translated_text)

    save_log({
        "timestamp": timestamp,
        "image_path": image_path,
        "ocr_text": ocr_text,
        "translated_text": translated_text,
        "predicted_genre": predicted_genre,
        "feedback": None,
    })

    return redirect(url_for("result", timestamp=timestamp))


@app.route("/result/<timestamp>", methods=["GET", "POST"])
@auth.login_required
def result(timestamp):
    image_path = os.path.join(IMAGES_DIR, f"{timestamp}.jpg")
    with open(LOG_FILE, "r") as file:
        logs = json.load(file)
    log = max(
        (log for log in logs if log["timestamp"] == timestamp),
        key=lambda x: (x["ocr_text"] is not None, x["translated_text"] is not None, x["predicted_genre"] is not None),
        default=None
    )

    if request.method == "POST":
        feedback = request.form.get("feedback")
        if log:
            log["feedback"] = feedback
            with open(LOG_FILE, "w") as file:
                json.dump(logs, file, indent=4)
        return redirect(url_for("index"))

    return render_template(
        "result.html",
        genre=log["predicted_genre"] if log else "N/A",
        ocr_text=log["ocr_text"] if log else "N/A",
        translated_text=log["translated_text"] if log else "N/A",
        image_path=image_path if log else None,
        timestamp=timestamp
    )


dashboard.bind(app)
asgi_app = WsgiToAsgi(app)
if __name__ == "__main__":
    model_name = "Helsinki-NLP/opus-mt-fr-en"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    app.run(host="0.0.0.0", port=8000, debug=False)
