"""Service d'authentification — hachage et vérification de mots de passe.

Utilise bcrypt directement (sans passlib) pour éviter les problèmes
de compatibilité entre passlib et bcrypt >= 4.0.
"""

import bcrypt


def hash_password(plain: str) -> str:
    """Retourne le hash bcrypt d'un mot de passe en clair."""
    # bcrypt.gensalt() génère un sel aléatoire (coût par défaut : 12).
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Retourne True si le mot de passe en clair correspond au hash stocké."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
