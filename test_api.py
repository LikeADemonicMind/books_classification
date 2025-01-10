import pytest
from httpx import AsyncClient
from base64 import b64encode
from dotenv import load_dotenv
import os

load_dotenv()

username = os.getenv("ADMIN_USERNAME")
password = os.getenv("ADMIN_PASSWORD")

# Définir la base URL de l'API
BASE_URL = "http://127.0.0.1:29000"

# Encodage des informations d'authentification
AUTH_HEADER = {
    "Authorization": "Basic " + b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
}


@pytest.mark.asyncio
async def test_predict_genre_valid():
    """
    Teste une prédiction valide avec un résumé fourni.
    """
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/predict_genre/",
            json={"summary": "A fascinating tale of adventure and mystery."},
            headers=AUTH_HEADER
        )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_genre" in data
    assert "elapsed_time" in data


@pytest.mark.asyncio
async def test_predict_genre_invalid():
    """
    Teste le cas d'un résumé vide, ce qui doit retourner une erreur 400.
    """
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/predict_genre/",
            json={"summary": ""},
            headers=AUTH_HEADER
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Le résumé ne peut pas être vide."


@pytest.mark.asyncio
async def test_predict_genre_unauthenticated():
    """
    Teste le cas où une requête est envoyée sans authentification.
    """
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/predict_genre/",
            json={"summary": "Test summary"}
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_predict_genre_wrong_authentication():
    """
    Teste le cas où l'authentification est incorrecte.
    """
    wrong_auth_header = {
        "Authorization": "Basic " + b64encode(b"wrong:credentials").decode("utf-8")
    }
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/predict_genre/",
            json={"summary": "Test summary"},
            headers=wrong_auth_header
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_predict_genre_missing_field():
    """
    Teste le cas où le champ "summary" est manquant dans la requête.
    """
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/predict_genre/",
            json={},
            headers=AUTH_HEADER
        )
    assert response.status_code == 422  # Erreur de validation FastAPI
    assert "detail" in response.json()
    assert response.json()["detail"][0]["loc"] == ["body", "summary"]
