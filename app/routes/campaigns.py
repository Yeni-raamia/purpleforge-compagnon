"""Routes liées aux campagnes purple team.

Toutes les routes sont protégées par require_user.
L'utilisateur connecté est passé dans le contexte des templates
pour afficher son nom dans la navigation.
"""

import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_user
from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.models.user import User
from app.services.attack import get_matrix
from app.services.coverage import compute_coverage

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", response_class=HTMLResponse)
def list_campaigns(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page principale : liste toutes les campagnes + formulaire de création."""
    campaigns = session.exec(
        select(Campaign).order_by(Campaign.created_at.desc())
    ).all()
    return templates.TemplateResponse(
        request,
        "campaigns/list.html",
        {"campaigns": campaigns, "current_user": current_user},
    )


@router.post("/", response_class=HTMLResponse)
def create_campaign(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Reçoit le formulaire de création et enregistre la campagne."""
    campaign = Campaign(name=name.strip(), description=description.strip())
    session.add(campaign)
    session.commit()
    return RedirectResponse(url="/campaigns/", status_code=303)


@router.get("/{campaign_id}", response_class=HTMLResponse)
def campaign_detail(
    campaign_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de détail d'une campagne : ses techniques + leur statut."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return templates.TemplateResponse(
            request, "404.html", {"message": "Campagne introuvable.", "current_user": current_user}, status_code=404
        )

    techniques = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.campaign_id == campaign_id)
        .order_by(TechniqueEntry.played_at.desc())
    ).all()

    return templates.TemplateResponse(
        request,
        "campaigns/detail.html",
        {"campaign": campaign, "techniques": techniques, "current_user": current_user},
    )


@router.get("/{campaign_id}/matrix", response_class=HTMLResponse)
def campaign_matrix(
    campaign_id: int,
    request: Request,
    tactic: str = "",
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de la matrice ATT&CK : affiche les techniques par tactique."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return templates.TemplateResponse(
            request, "404.html", {"message": "Campagne introuvable.", "current_user": current_user}, status_code=404
        )

    added = session.exec(
        select(TechniqueEntry).where(TechniqueEntry.campaign_id == campaign_id)
    ).all()
    existing_ids = {t.attack_id for t in added}

    matrix = get_matrix()
    active_tactic = tactic or (matrix[0]["shortname"] if matrix else "")

    return templates.TemplateResponse(
        request,
        "campaigns/matrix.html",
        {
            "campaign": campaign,
            "matrix": matrix,
            "active_tactic": active_tactic,
            "existing_ids": existing_ids,
            "current_user": current_user,
        },
    )


@router.post("/{campaign_id}/techniques", response_class=HTMLResponse)
def add_technique(
    campaign_id: int,
    attack_id: str = Form(...),
    name: str = Form(...),
    tactic: str = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Ajoute une technique à la campagne (HTMX — fragment HTML)."""
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

    return HTMLResponse('<span class="status-badge status-badge--ok added-badge">✓ Ajoutée</span>')


@router.get("/{campaign_id}/coverage", response_class=HTMLResponse)
def campaign_coverage(
    campaign_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de couverture : statistiques de détection et carte par tactique."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return templates.TemplateResponse(
            request, "404.html", {"message": "Campagne introuvable.", "current_user": current_user}, status_code=404
        )

    coverage = compute_coverage(campaign_id, session)

    return templates.TemplateResponse(
        request,
        "campaigns/coverage.html",
        {"campaign": campaign, "coverage": coverage, "current_user": current_user},
    )


@router.get("/{campaign_id}/export")
def campaign_export(
    campaign_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Exporte la campagne au format ATT&CK Navigator layer (JSON téléchargeable)."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return Response(status_code=404)

    techniques = session.exec(
        select(TechniqueEntry).where(TechniqueEntry.campaign_id == campaign_id)
    ).all()

    COLOR_MAP = {
        "detecte":      "#2e7d32",
        "a_construire": "#e65100",
        "non_detecte":  "#b71c1c",
    }

    techniques_layer = []
    for t in techniques:
        techniques_layer.append({
            "techniqueID": t.attack_id,
            "tactic":      t.tactic,
            "color":       COLOR_MAP.get(t.status.value, "#ffffff"),
            "comment":     t.blue_note or "",
            "enabled":     True,
            "score":       0,
            "metadata":    [],
        })

    layer = {
        "name":        campaign.name,
        "versions": {
            "attack":    "14",
            "navigator": "4.9",
            "layer":     "4.5",
        },
        "domain":      "enterprise-attack",
        "description": campaign.description or f"Campagne PurpleForge : {campaign.name}",
        "filters": {
            "platforms": [
                "Windows", "Linux", "macOS",
                "Network", "PRE", "Containers",
                "Office 365", "SaaS", "Google Workspace",
                "IaaS", "Azure AD",
            ]
        },
        "sorting":      0,
        "layout": {
            "layout":               "side",
            "aggregateFunction":    "average",
            "showID":               True,
            "showName":             True,
            "showAggregateScores":  False,
            "countUnscored":        False,
        },
        "hideDisabled": False,
        "techniques":   techniques_layer,
        "gradient": {
            "colors":   ["#ff6666ff", "#ffe766ff", "#8ec843ff"],
            "minValue": 0,
            "maxValue": 100,
        },
        "legendItems": [
            {"label": "Détecté",      "color": "#2e7d32"},
            {"label": "À construire", "color": "#e65100"},
            {"label": "Non détecté",  "color": "#b71c1c"},
        ],
        "metadata":  [],
        "links":     [],
        "showTacticRowBackground":       False,
        "tacticRowBackground":           "#dddddd",
        "selectTechniquesAcrossTactics": True,
        "selectSubtechniquesWithParent": False,
    }

    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "-"
        for c in campaign.name.lower()
    ).strip("-")
    filename = f"purpleforge-{safe_name}-navigator.json"

    return Response(
        content=json.dumps(layer, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
