from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient
from sqlmodel import Session
from .. import dependencies
from ..config import Settings
from ..dependencies import get_session
from ..main import app
import jwt
import pytest

AUDIENCE = "https://api.test"


@pytest.fixture(name="signing_key", scope="module")
def signing_key_fixture():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(name="auth_client")
def auth_client_fixture(
    session: Session, users, signing_key, tmp_path: Path, monkeypatch
):
    """A client that validates real tokens against a throwaway certificate."""
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(signing_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(signing_key, hashes.SHA256())
    )
    cert_path = tmp_path / "cert.pem"
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    settings = Settings(
        auth0_certificate_url=str(cert_path), auth0_audience=[AUDIENCE]
    )
    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_token(signing_key, issued_in=0, expires_in=3600, **claims):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "auth0|1",
        "aud": AUDIENCE,
        "iat": now + timedelta(seconds=issued_in),
        "exp": now + timedelta(seconds=expires_in),
        **claims,
    }
    return jwt.encode(payload, signing_key, algorithm="RS256")


def get_me(client: TestClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    return client.get("/users/me", headers=headers)


def test_valid_token(auth_client, signing_key):
    response = get_me(auth_client, make_token(signing_key))
    assert response.status_code == 200
    assert response.json()["auth0_id"] == "auth0|1"


def test_token_issued_slightly_in_the_future_is_accepted(
    auth_client, signing_key
):
    # Auth0's clock a few seconds ahead of the server's.
    response = get_me(auth_client, make_token(signing_key, issued_in=3))
    assert response.status_code == 200


@pytest.mark.parametrize(
    "token_args",
    [
        {"issued_in": 120},
        {"expires_in": -120},
        {"aud": "https://other.api"},
        {"sub": "auth0|unknown"},
    ],
    ids=["not-yet-valid", "expired", "wrong-audience", "unknown-user"],
)
def test_invalid_token_is_unauthorized(auth_client, signing_key, token_args):
    response = get_me(auth_client, make_token(signing_key, **token_args))
    assert response.status_code == 401


def test_token_signed_by_another_key_is_unauthorized(auth_client):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    response = get_me(auth_client, make_token(other_key))
    assert response.status_code == 401


def test_malformed_token_is_unauthorized(auth_client):
    response = get_me(auth_client, "not-a-jwt")
    assert response.status_code == 401
