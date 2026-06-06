"""Routes liées aux campagnes purple team.

Une "route" = une URL + ce qu'on fait quand on la visite.
Ici on gère : lister les campagnes, en créer une nouvelle,
et afficher le détail d'une campagne.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.services.attack import get_matrix

# Le routeur regroupe toutes les routes de ce fichier.
# On lui donne un préfixe : toutes les URLs commenceront par /campaigns.
router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Même dossier de templates que dans main.py.
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", response_class=HTMLResponse)
def list_campaigns(request: Request, session: Session = Depends(get_session)):
    """Page principale : liste toutes les campagnes + formulaire de création."""
    # On récupère toutes les campagnes, triées de la plus récente à la plus ancienne.
    campaigns = session.exec(
        select(Campaign).order_by(Campaign.created_at.desc())
    ).all()
    return templates.TemplateResponse(
        request, "campaigns/list.html", {"campaigns": campaigns}
    )


@router.post("/", response_class=HTMLResponse)
def create_campaign(
    request: Request,
    name: str = Form(...),           # Form(...) = champ obligatoire du formulaire HTML
    description: str = Form(""),     # champ optionnel, vide par défaut
    session: Session = Depends(get_session),
):
    """Reçoit le formulaire de création et enregistre la campagne."""
    # On crée l'objet Campaign et on l'enregistre en base.
    campaign = Campaign(name=name.strip(), description=description.strip())
    session.add(campaign)
    session.commit()
    # Après création, on redirige vers la liste (évite les doubles soumissions).
    return RedirectResponse(url="/campaigns/", status_code=303)


@router.get("/{campaign_id}", response_class=HTMLResponse)
def campaign_detail(
    campaign_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    """Page de détail d'une campagne : ses techniques + leur statut."""
    # On charge la campagne (ou renvoie 404 si elle n'existe pas).
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return templates.TemplateResponse(
            request, "404.html", {"message": "Campagne introuvable."}, status_code=404
        )

    # On récupère toutes les techniques liées à cette campagne.
    techniques = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.campaign_id == campaign_id)
        .order_by(TechniqueEntry.played_at.desc())
    ).all()

    return templates.TemplateResponse(
        request,
        "campaigns/detail.html",
        {"campaign": campaign, "techniques": techniques},
    )


@router.get("/{campaign_id}/matrix", response_class=HTMLResponse)
def campaign_matrix(
    campaign_id: int,
    request: Request,
    tactic: str = "",                   # tactique active (passée en paramètre URL)
    session: Session = Depends(get_session),
):
    """Page de la matrice ATT&CK : affiche les techniques par tactique.

    Première ouverture : télécharge les données MITRE (~50 Mo, ~30s).
    Appels suivants : instantanés (cache local + mémoire).
    """
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return templates.TemplateResponse(
            request, "404.html", {"message": "Campagne introuvable."}, status_code=404
        )

    # Identifiants des techniques déjà ajoutées (pour les marquer dans la matrice).
    added = session.exec(
        select(TechniqueEntry).where(TechniqueEntry.campaign_id == campaign_id)
    ).all()
    existing_ids = {t.attack_id for t in added}

    # Chargement de la matrice ATT&CK (téléchargement si nécessaire).
    matrix = get_matrix()

    # Tactique active : celle passée en URL, ou la première par défaut.
    active_tactic = tactic or (matrix[0]["shortname"] if matrix else "")

    return templates.TemplateResponse(
        request,
        "campaigns/matrix.html",
        {
            "campaign": campaign,
            "matrix": matrix,
            "active_tactic": active_tactic,
            "existing_ids": existing_ids,
        },
    )


@router.post("/{campaign_id}/techniques", response_class=HTMLResponse)
def add_technique(
    campaign_id: int,
    attack_id: str = Form(...),
    name: str = Form(...),
    tactic: str = Form(...),
    session: Session = Depends(get_session),
):
    """Ajoute une technique à la campagne (appelé par HTMX — retourne un fragment HTML).

    Si la technique est déjà dans la campagne, on ne la duplique pas.
    Dans les deux cas, on retourne un badge « ✓ Ajouté » qui remplace le bouton.
    """
    # Vérification : la technique est-elle déjà dans cette campagne ?
    existing = session.exec(
        select(TechniqueEntry).where(
            TechniqueEntry.campaign_id == campaign_id,
            TechniqueEntry.attack_id == attack_id,
        )
    ).first()

    if not existing:
        new_technique = TechniqueEntry(
            campaign_id=campaign_id,
            attack_id=attack_id,
            name=name,
            tactic=tactic,
            status=TechniqueStatus.non_detecte,
        )
        session.add(new_technique)
        session.commit()

    # HTMX remplacera le formulaire « Ajouter » par ce badge.
    return HTMLResponse('<span class="status-badge status-badge--ok added-badge">✓ Ajoutée</span>')
