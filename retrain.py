import os
import time
import json
import joblib
import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sentence_transformers import SentenceTransformer
import requests
from dotenv import load_dotenv

load_dotenv()


# Fonction pour sauvegarder le score actuel
def save_current_model_score(score, filepath="model_score.json"):
    with open(filepath, "w") as f:
        json.dump({"balanced_accuracy": score}, f)


# Fonction pour charger le score actuel
def load_current_model_score(filepath="model_score.json"):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            return data["balanced_accuracy"]
    except FileNotFoundError:
        return 0.0  # Si aucun score précédent n'existe, retourner 0.0


# Fonction pour log les résultats de Grid Search
def log_results(params_tested, best_params, val_score, test_score, confusion_matrix, is_replaced, filepath="training_logs.csv"):
    if not os.path.exists(filepath):
        # Créer le fichier et ajouter l'en-tête
        pd.DataFrame(columns=["date", "params_tested", "best_params", "val_score", "test_score", "confusion_matrix", "is_replaced"]).to_csv(filepath, index=False)
    
    # Ajouter une ligne de log
    log_entry = pd.DataFrame(
        {
            "date": [time.strftime("%Y-%m-%d %H:%M:%S")],
            "params_tested": [json.dumps(params_tested)],  # Liste des paramètres testés
            "best_params": [json.dumps(best_params)],
            "val_score": [val_score],
            "test_score": [test_score],
            "confusion_matrix": [json.dumps(confusion_matrix.tolist())],  # Sauvegarder la matrice sous forme de JSON
            "is_replaced": [is_replaced]  # Indique si le modèle a été remplacé
        }
    )
    log_entry.to_csv(filepath, mode='a', index=False, header=False)


# Fonction pour récupérer les données via l'API
def fetch_data_from_api(base_url, endpoint, username, password):
    response = requests.get(f"{base_url}{endpoint}", auth=(username, password))
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        raise Exception(f"Erreur lors de la récupération des données : {response.status_code} - {response.text}")


# Fonction pour charger les IDs du jeu de test
def load_test_ids(filepath="test_ids.pkl"):
    return set(joblib.load(filepath))


# Fonction pour transformer les descriptions en embeddings
def generate_embeddings(sentences, model):
    return model.encode(sentences.tolist())


# Fonction pour entraîner le modèle avec Grid Search
def perform_grid_search(
    X_train, y_train_encoded, X_test, y_test_encoded, label_encoder,
    current_model_path, score_filepath="model_score.json"
):
    # Charger le score du modèle actuel
    current_balanced_accuracy = load_current_model_score(score_filepath)
    print(f"Current balanced accuracy score: {current_balanced_accuracy}")

    # Paramètres de recherche
    param_grid = {
        'C': [0.1, 1, 10, 100],  # Paramètre de régularisation
        'kernel': ['linear', 'rbf', 'poly'],  # Type de noyau
        'gamma': ['scale', 'auto'],  # Coefficient pour les noyaux RBF, poly et sigmoid
    }
    
    # Initialiser le modèle et la Grid Search
    svc = SVC(probability=True, random_state=42, class_weight="balanced")
    grid_search = GridSearchCV(svc, param_grid, scoring='balanced_accuracy', cv=5, verbose=2, n_jobs=-1)
    
    # Entraîner la Grid Search
    grid_search.fit(X_train, y_train_encoded)
    
    # Meilleurs hyperparamètres et score
    best_params = grid_search.best_params_
    best_val_score = grid_search.best_score_
    print(f"Best parameters: {best_params}")
    print(f"Best balanced accuracy score (validation): {best_val_score}")
    
    # Tester sur le jeu de test
    best_model = grid_search.best_estimator_
    y_test_pred = best_model.predict(X_test)
    test_score = balanced_accuracy_score(y_test_encoded, y_test_pred)

    # Calculer la matrice de confusion
    cm = confusion_matrix(y_test_encoded, y_test_pred)
    print(f"Test balanced accuracy score: {test_score}")
    print(f"Confusion Matrix:\n{cm}")
    
    # Vérifier si le score dépasse celui de l'ancien modèle
    is_replaced = False
    if test_score > current_balanced_accuracy:
        print("Nouveau modèle accepté. Sauvegarde en cours...")
        joblib.dump(best_model, current_model_path)
        joblib.dump(label_encoder, "label_encoder.pkl")
        save_current_model_score(test_score, score_filepath)
        is_replaced = True
    else:
        print("Nouveau modèle rejeté. L'ancien modèle est conservé.")
    
    # Log des résultats, y compris la matrice de confusion et si le modèle a été remplacé
    log_results(param_grid, best_params, best_val_score, test_score, cm, is_replaced)

    return best_params, best_val_score, test_score


# Script principal
if __name__ == "__main__":
    # Configuration
    API_BASE_URL = "http://127.0.0.1:5000"
    API_ENDPOINT = "/books"
    USERNAME = os.getenv("ADMIN_USERNAME")
    PASSWORD = os.getenv("ADMIN_PASSWORD")
    TEST_IDS_FILE = "test_ids.pkl"
    MODEL_PATH = "svc_model.pkl"
    SCORE_FILE = "model_score.json"

    # Charger le modèle d'embeddding
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Récupérer les données
    books_df = fetch_data_from_api(API_BASE_URL, API_ENDPOINT, USERNAME, PASSWORD)

    # Charger les IDs du jeu de test
    test_ids = load_test_ids(TEST_IDS_FILE)

    # Séparer les données en test et entraîment
    train_data = books_df[~books_df["id"].isin(test_ids)]
    test_data = books_df[books_df["id"].isin(test_ids)]
    print(len(test_data))
    X_train_raw = train_data["description"]
    y_train = train_data["genre"]
    X_test_raw = test_data["description"]
    y_test = test_data["genre"]

    # Encoder les labels
    label_encoder = LabelEncoder()
    y_train_encoded = label_encoder.fit_transform(y_train)
    y_test_encoded = label_encoder.transform(y_test)

    # Générer les embeddings
    print("Génération des embeddings pour l'entraîment...")
    X_train = generate_embeddings(X_train_raw, embedding_model)
    print("Génération des embeddings pour le test...")
    X_test = generate_embeddings(X_test_raw, embedding_model)

    # Entraîner le modèle avec Grid Search
    perform_grid_search(X_train, y_train_encoded, X_test, y_test_encoded, label_encoder, MODEL_PATH, SCORE_FILE)
