"""Routes liées aux techniques d'une campagne.

Gère :
- GET  /campaigns/{id}/techniques/{tech_id}/sigma  → fragment HTMX : règles Sigma
- GET  /campaigns/{id}/techniques/{tech_id}/wazuh  → téléchargement XML Wazuh
- POST /campaigns/{id}/techniques/{tech_id}        → fragment HTMX : carte mise à jour
"""

from fastapi import APIRouter, Depends, Form, Query, Request, Response as FastResponse
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_user
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.models.user import User
from app.services.sigma import get_rules_for_technique
from app.services.wazuh import sigma_yaml_to_wazuh_xml

router = APIRouter(prefix="/campaigns", tags=["techniques"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/{campaign_id}/techniques/{tech_id}/sigma", response_class=HTMLResponse)
def get_sigma_rules(
    campaign_id: int,
    tech_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Retourne un fragment HTML avec les règles Sigma pour cette technique.

    Appelé par HTMX au clic sur « Voir les détections ».
    Premier appel : déclenche le téléchargement SigmaHQ (~30s).
    Appels suivants : instantanés (cache local).
    """
    technique = session.get(TechniqueEntry, tech_id)
    if not technique or technique.campaign_id != campaign_id:
        return HTMLResponse("<p>Technique introuvable.</p>", status_code=404)

    rules = get_rules_for_technique(technique.attack_id)

    return templates.TemplateResponse(
        request,
        "campaigns/partials/sigma_rules.html",
        {"technique": technique, "rules": rules, "campaign_id": campaign_id},
    )


@router.get("/{campaign_id}/techniques/{tech_id}/wazuh")
def export_wazuh_rule(
    campaign_id: int,
    tech_id: int,
    rule_idx: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Convertit la règle Sigma n°rule_idx en XML Wazuh et la retourne en téléchargement.

    La conversion est best-effort : métadonnées et champs Windows courants
    sont traduits fidèlement ; les champs exotiques tombent sur full_log.
    À vérifier avant déploiement en production.
    """
    technique = session.get(TechniqueEntry, tech_id)
    if not technique or technique.campaign_id != campaign_id:
        return Response(status_code=404)

    rules = get_rules_for_technique(technique.attack_id)
    if not rules or rule_idx >= len(rules):
        return Response(
            content="<!-- Aucune règle Sigma disponible pour cette technique -->",
            media_type="application/xml",
            status_code=404,
        )

    rule = rules[rule_idx]
    xml_content = sigma_yaml_to_wazuh_xml(rule["yaml_content"], technique.attack_id)

    safe_id  = technique.attack_id.replace(".", "_").upper()
    filename = f"wazuh_{safe_id}_{rule_idx}.xml"

    xml_bytes = xml_content.encode("utf-8")
    return Response(
        content=xml_bytes,
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{campaign_id}/techniques/{tech_id}/remediation")
def update_remediation(
    campaign_id: int,
    tech_id: int,
    request: Request,
    assignee:     str = Form(""),
    deadline:     str = Form(""),
    remed_status: str = Form("en_cours"),
    board: int = Query(default=0),   # ?board=1 → redirect vers le board
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Met à jour les champs de remédiation.

    - Sans ?board=1 : retourne un feedback HTML inline (HTMX depuis la carte).
    - Avec ?board=1  : redirige vers la page de remédiation (formulaire board).
    """
    technique = session.get(TechniqueEntry, tech_id)
    if not technique or technique.campaign_id != campaign_id:
        return HTMLResponse("Introuvable.", status_code=404)

    technique.remediation_assignee = assignee.strip()
    technique.remediation_deadline = deadline.strip()
    valid = {"en_cours", "bloque", "termine"}
    technique.remediation_status = remed_status if remed_status in valid else "en_cours"

    session.add(technique)
    session.commit()

    if board:
        return RedirectResponse(
            url=f"/campaigns/{campaign_id}/remediation", status_code=303
        )

    return HTMLResponse(
        '<span style="color:#16a34a; font-weight:700; font-size:.82rem;">✓ Sauvegardé</span>'
    )


@router.post("/{campaign_id}/techniques/{tech_id}", response_class=HTMLResponse)
def update_technique(
    campaign_id: int,
    tech_id: int,
    request: Request,
    status: str = Form(...),
    blue_note: str = Form(""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Met à jour le statut et la note blue team d'une technique.

    Retourne un fragment HTML (carte mise à jour) remplacé par HTMX.
    """
    technique = session.get(TechniqueEntry, tech_id)
    if not technique or technique.campaign_id != campaign_id:
        return HTMLResponse("<p>Technique introuvable.</p>", status_code=404)

    try:
        technique.status = TechniqueStatus(status)
    except ValueError:
        pass
    technique.blue_note = blue_note.strip()

    session.add(technique)
    session.commit()
    session.refresh(technique)

    return templates.TemplateResponse(
        request,
        "campaigns/partials/technique_card.html",
        {"technique": technique, "campaign_id": campaign_id},
    )
