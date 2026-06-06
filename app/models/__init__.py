# On importe les modèles ici dans le bon ordre.
# C'est important : SQLModel doit les "voir" avant que create_all() soit appelé,
# sinon il ne saurait pas quelles tables créer.
from app.models.campaign import Campaign           # noqa: F401
from app.models.technique import TechniqueEntry, TechniqueStatus  # noqa: F401
