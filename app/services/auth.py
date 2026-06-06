"""Service d'authentification — hachage, vérification et validation de mots de passe.

Utilise bcrypt directement (sans passlib) pour éviter les problèmes
de compatibilité entre passlib et bcrypt >= 4.0.
"""

import re
import bcrypt


def hash_password(plain: str) -> str:
    """Retourne le hash bcrypt d'un mot de passe en clair."""
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Retourne True si le mot de passe en clair correspond au hash stocké."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def validate_password_strength(password: str) -> list[str]:
    """Vérifie la robustesse d'un mot de passe.

    Retourne une liste de messages d'erreur (vide = mot de passe valide).

    Règles :
    - Au moins 12 caractères
    - Au moins 1 lettre majuscule
    - Au moins 1 lettre minuscule
    - Au moins 1 chiffre
    - Au moins 1 caractère spécial (tout ce qui n'est pas alphanumérique)
    """
    errors: list[str] = []

    if len(password) < 12:
        errors.append("au moins 12 caractères")
    if not re.search(r"[A-Z]", password):
        errors.append("au moins une majuscule (A–Z)")
    if not re.search(r"[a-z]", password):
        errors.append("au moins une minuscule (a–z)")
    if not re.search(r"\d", password):
        errors.append("au moins un chiffre (0–9)")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("au moins un caractère spécial (!@#$%^&*…)")

    return errors
