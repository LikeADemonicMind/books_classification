import pytest
import base64
from httpx import AsyncClient
from dotenv import load_dotenv
import os

load_dotenv()

# Configurer les identifiants pour HTTP Basic Auth
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

# Ajouter l'entête Authorization pour chaque requête
AUTH_HEADER = {
    "Authorization": "Basic " + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
}

# Base URL correcte
BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.asyncio
async def test_index():
    """
    Teste l'accès à la page principale.
    """
    async with AsyncClient(base_url=BASE_URL, timeout=30) as client:
        response = await client.get("/", headers=AUTH_HEADER)
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text  # Vérifie que la réponse est une page HTML
    assert '<html lang="fr">' in response.text  # Vérifie que la langue est définie


@pytest.mark.asyncio
async def test_capture():
    """
    Teste la capture d'une image (POST /capture).
    """
    dummy_image = "data:image/jpeg;base64," + base64.b64encode(b"dummy_image_data").decode()
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/capture", data={"image": dummy_image}, headers=AUTH_HEADER)
    assert response.status_code in [302, 307]


@pytest.mark.asyncio
async def test_processing():
    """
    Teste l'affichage de la page de traitement.
    """
    timestamp = "dummy_timestamp"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(f"/processing/{timestamp}", headers=AUTH_HEADER)
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Traitement en cours" in response.text


@pytest.mark.asyncio
async def test_process_data():
    """
    Teste le traitement des données.
    """
    timestamp = "dummy_timestamp"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(f"/process_data/{timestamp}", headers=AUTH_HEADER)
    assert response.status_code in [200, 302, 307]


@pytest.mark.asyncio
async def test_result_get():
    """
    Teste l'affichage de la page de résultat (GET /result/<timestamp>).
    """
    timestamp = "dummy_timestamp"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(f"/result/{timestamp}", headers=AUTH_HEADER)
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Résultat" in response.text


@pytest.mark.asyncio
async def test_result_post():
    """
    Teste l'envoi d'un feedback via POST /result/<timestamp>.
    """
    timestamp = "dummy_timestamp"
    feedback = "positive feedback"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(f"/result/{timestamp}", data={"feedback": feedback}, headers=AUTH_HEADER)
    assert response.status_code in [302, 307]


@pytest.mark.asyncio
async def test_unauthorized_access():
    """
    Teste l'accès non autorisé à l'application sans les identifiants.
    """
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/")
    assert response.status_code == 401
    assert response.json()["error"] == "Accès non autorisé. Veuillez vérifier vos identifiants."
