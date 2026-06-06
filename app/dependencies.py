"""Dépendances FastAPI partagées — gestion de l'authentification.

require_user  : injecte l'utilisateur connecté dans une route protégée.
require_admin : idem, mais réservé aux administrateurs.

Les deux lèvent NotAuthenticated / NotAdmin, capturées par les
gestionnaires d'exceptions enregistrés dans main.py.
"""

from fastapi import Depends
from fastapi.requests import Request
from sqlmodel import Session

from app.database import get_session
from app.models.user import User


# ── Exceptions personnalisées (plus propres que HTTPException pour les redirects) ──

class NotAuthenticated(Exception):
    """Levée quand l'utilisateur n'est pas connecté."""


class NotAdmin(Exception):
    """Levée quand l'utilisateur est connecté mais n'est pas administrateur."""


# ── Dépendances injectables dans les routes ────────────────────────────────────

def require_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """Retourne l'utilisateur connecté, ou lève NotAuthenticated.

    FastAPI injecte cette dépendance dans toute route qui la déclare.
    Le gestionnaire d'exceptions dans main.py se charge de la redirection.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise NotAuthenticated()

    user = session.get(User, user_id)
    if not user:
        # Session obsolète (utilisateur supprimé depuis la dernière connexion).
        request.session.clear()
        raise NotAuthenticated()

    return user


def require_admin(user: User = Depends(require_user)) -> User:
    """Retourne l'utilisateur SI il est administrateur, sinon lève NotAdmin."""
    if not user.is_admin:
        raise NotAdmin()
    return user
