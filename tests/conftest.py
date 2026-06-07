"""Configuration pytest — fixtures partagées pour tous les tests PurpleForge.

Approche :
- Base de données SQLite en mémoire isolée par session de test
- Injection de dépendances FastAPI : get_session et require_user sont remplacés
  afin de ne pas toucher la vraie base ni d'avoir besoin d'être connecté.
- Un TestClient synchrone (httpx) est fourni prêt à l'emploi.
"""

import pytest
from sqlmodel import SQLModel, Session, create_engine, StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session
from app.dependencies import require_user
from app.models.user import User
from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus


# ─── Base de données de test (en mémoire, isolée) ────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """Moteur SQLite en mémoire partagé pour toute la session de tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_engine):
    """Session de base ouverte pour chaque test, avec rollback automatique."""
    with Session(test_engine) as session:
        yield session


# ─── Utilisateur de test ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_user():
    """Utilisateur fictif injecté à la place de la vraie authentification."""
    return User(
        id=1,
        username="testuser",
        display_name="Test User",
        hashed_password="hashed",
        is_admin=True,
    )


# ─── Client HTTP de test (authentifié) ───────────────────────────────────────

@pytest.fixture
def client(db_session, test_user):
    """TestClient avec dépendances remplacées (DB + auth)."""

    def _override_session():
        yield db_session

    def _override_user():
        return test_user

    app.dependency_overrides[get_session]  = _override_session
    app.dependency_overrides[require_user] = _override_user

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


# ─── Données de test ─────────────────────────────────────────────────────────

@pytest.fixture
def sample_campaign(db_session) -> Campaign:
    """Campagne de test persistée dans la DB de test."""
    camp = Campaign(name="Campagne Test", description="Test", tags="APT28")
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp


@pytest.fixture
def sample_technique(db_session, sample_campaign) -> TechniqueEntry:
    """Technique de test liée à la campagne de test."""
    tech = TechniqueEntry(
        campaign_id=sample_campaign.id,
        attack_id="T1059",
        name="Command and Scripting Interpreter",
        tactic="execution",
        status=TechniqueStatus.non_detecte,
        blue_note="",
        red_note="",
    )
    db_session.add(tech)
    db_session.commit()
    db_session.refresh(tech)
    return tech
