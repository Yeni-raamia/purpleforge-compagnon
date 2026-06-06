# On importe les modèles ici dans le bon ordre.
# C'est important : SQLModel doit les "voir" avant que create_all() soit appelé,
# sinon il ne saurait pas quelles tables créer.
from app.models.user import User                                   # noqa: F401  ← en premier (pas de FK vers les autres)
from app.models.campaign import Campaign                           # noqa: F401
from app.models.technique import TechniqueEntry, TechniqueStatus  # noqa: F401
