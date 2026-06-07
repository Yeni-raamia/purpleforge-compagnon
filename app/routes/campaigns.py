"""Routes liées aux campagnes purple team.

Toutes les routes sont protégées par require_user.
L'utilisateur connecté est passé dans le contexte des templates
pour afficher son nom dans la navigation.
"""

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_user
from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.models.user import User
from app.data.apt_templates import APT_TEMPLATES, APT_BY_SLUG
from app.services.attack import get_matrix
from app.services.coverage import compute_coverage, TACTIC_DISPLAY_NAMES, TACTIC_ORDER

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Groupes ATT&CK suggérés pour l'autocomplete
APT_SUGGESTIONS = [
    "APT28", "APT29", "APT41", "APT32", "APT38",
    "Lazarus", "Sandworm", "Turla", "Cozy Bear", "Fancy Bear",
    "FIN7", "FIN11", "Carbanak", "Equation Group",
    "UNC2452", "ALPHV", "LockBit", "Conti", "REvil",
]


def _normalize_tags(raw: str) -> str:
    """Normalise une liste de tags : sépare par virgule, déduplique, trie."""
    parts = [t.strip() for t in raw.replace(";", ",").split(",") if t.strip()]
    seen, unique = set(), []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return ", ".join(unique)


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

    # Stats par campagne pour les mini-rings et les pills
    all_techs = session.exec(select(TechniqueEntry)).all()
    tech_by_camp: dict[int, list] = {}
    for t in all_techs:
        tech_by_camp.setdefault(t.campaign_id, []).append(t)

    campaigns_stats = []
    for c in campaigns:
        techs = tech_by_camp.get(c.id, [])
        total = len(techs)
        counts = {"detecte": 0, "a_construire": 0, "non_detecte": 0}
        for t in techs:
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        pct = round(counts["detecte"] * 100 / total) if total > 0 else 0
        campaigns_stats.append({
            "campaign":    c,
            "total":       total,
            "counts":      counts,
            "pct_detecte": pct,
        })

    return templates.TemplateResponse(
        request,
        "campaigns/list.html",
        {
            "campaigns":       campaigns,
            "campaigns_stats": campaigns_stats,
            "nb_campaigns":    len(campaigns),
            "nb_techniques":   len(all_techs),
            "current_user":    current_user,
        },
    )


@router.post("/", response_class=HTMLResponse)
def create_campaign(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Reçoit le formulaire de création et enregistre la campagne."""
    campaign = Campaign(
        name=name.strip(),
        description=description.strip(),
        tags=_normalize_tags(tags),
    )
    session.add(campaign)
    session.commit()
    return RedirectResponse(url="/campaigns/", status_code=303)


@router.get("/templates", response_class=HTMLResponse)
def list_templates(
    request: Request,
    current_user: User = Depends(require_user),
):
    """Page des templates APT : grille de profils d'attaquants connus."""
    return templates.TemplateResponse(
        request,
        "campaigns/templates.html",
        {"apt_templates": APT_TEMPLATES, "current_user": current_user},
    )


@router.post("/from-template/{slug}", response_class=HTMLResponse)
def create_from_template(
    slug: str,
    request: Request,
    campaign_name: str = Form(""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Crée une nouvelle campagne pré-remplie depuis un profil APT."""
    profile = APT_BY_SLUG.get(slug)
    if not profile:
        return RedirectResponse(url="/campaigns/templates", status_code=303)

    name = campaign_name.strip() or f"Simulation {profile['name']}"
    tags = ", ".join([profile["name"]] + profile["aliases"][:2])

    campaign = Campaign(
        name=name,
        description=(
            f"Campagne générée depuis le profil {profile['name']} "
            f"({', '.join(profile['aliases'][:2])}). "
            f"Origine : {profile['origin']}. "
            f"Motivations : {', '.join(profile['motivation'])}."
        ),
        tags=_normalize_tags(tags),
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    # Ajout des techniques du profil, toutes en statut "non_detecte"
    for t in profile["techniques"]:
        session.add(TechniqueEntry(
            campaign_id=campaign.id,
            attack_id=t["attack_id"],
            name=t["name"],
            tactic=t["tactic"],
            status=TechniqueStatus.non_detecte,
            blue_note=None,
        ))

    session.commit()
    return RedirectResponse(url=f"/campaigns/{campaign.id}", status_code=303)


@router.get("/compare", response_class=HTMLResponse)
def compare_campaigns(
    request: Request,
    a: int = 0,
    b: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de comparaison de deux campagnes : delta de détection technique par technique."""
    all_campaigns = session.exec(
        select(Campaign).order_by(Campaign.created_at.desc())
    ).all()

    ctx_base = {
        "campaigns":   all_campaigns,
        "camp_a_id":   a,
        "camp_b_id":   b,
        "comparison":  None,
        "camp_a":      None,
        "camp_b":      None,
        "error":       None,
        "current_user": current_user,
    }

    # Pas encore de sélection, ou même campagne choisie deux fois
    if not a or not b:
        return templates.TemplateResponse(request, "campaigns/compare.html", ctx_base)

    if a == b:
        ctx_base["error"] = "Sélectionne deux campagnes différentes."
        return templates.TemplateResponse(request, "campaigns/compare.html", ctx_base)

    camp_a = session.get(Campaign, a)
    camp_b = session.get(Campaign, b)
    if not camp_a or not camp_b:
        ctx_base["error"] = "L'une des campagnes est introuvable."
        return templates.TemplateResponse(request, "campaigns/compare.html", ctx_base)

    # ── Chargement des techniques ──────────────────────────────────────────
    techs_a = {t.attack_id: t for t in session.exec(
        select(TechniqueEntry).where(TechniqueEntry.campaign_id == a)
    ).all()}
    techs_b = {t.attack_id: t for t in session.exec(
        select(TechniqueEntry).where(TechniqueEntry.campaign_id == b)
    ).all()}

    STATUS_SCORE = {"detecte": 2, "a_construire": 1, "non_detecte": 0}

    # ── Construction des lignes de comparaison ─────────────────────────────
    rows = []
    for attack_id in sorted(set(techs_a) | set(techs_b)):
        ta = techs_a.get(attack_id)
        tb = techs_b.get(attack_id)

        status_a = ta.status.value if ta else None
        status_b = tb.status.value if tb else None

        if status_a is None:
            delta = "nouveau"
        elif status_b is None:
            delta = "supprime"
        elif STATUS_SCORE[status_b] > STATUS_SCORE[status_a]:
            delta = "ameliore"
        elif STATUS_SCORE[status_b] < STATUS_SCORE[status_a]:
            delta = "regressee"
        else:
            delta = "stable"

        rows.append({
            "attack_id": attack_id,
            "name":      (ta or tb).name,
            "tactic":    (ta or tb).tactic,
            "status_a":  status_a,
            "status_b":  status_b,
            "delta":     delta,
        })

    # Tri par ordre tactique canonique puis par identifiant ATT&CK
    tactic_idx = {t: i for i, t in enumerate(TACTIC_ORDER)}
    rows.sort(key=lambda r: (tactic_idx.get(r["tactic"], 99), r["attack_id"]))

    # ── Statistiques globales ──────────────────────────────────────────────
    def _pct(techs):
        if not techs:
            return 0
        det = sum(1 for t in techs.values() if t.status.value == "detecte")
        return round(det * 100 / len(techs))

    score_a = _pct(techs_a)
    score_b = _pct(techs_b)

    comparison = {
        "rows":          rows,
        "score_a":       score_a,
        "score_b":       score_b,
        "delta_score":   score_b - score_a,
        "nb_ameliore":   sum(1 for r in rows if r["delta"] == "ameliore"),
        "nb_regressee":  sum(1 for r in rows if r["delta"] == "regressee"),
        "nb_stable":     sum(1 for r in rows if r["delta"] == "stable"),
        "nb_nouveau":    sum(1 for r in rows if r["delta"] == "nouveau"),
        "nb_supprime":   sum(1 for r in rows if r["delta"] == "supprime"),
        "total":         len(rows),
    }

    return templates.TemplateResponse(
        request,
        "campaigns/compare.html",
        {
            **ctx_base,
            "camp_a":     camp_a,
            "camp_b":     camp_b,
            "comparison": comparison,
        },
    )


@router.get("/import", response_class=HTMLResponse)
def import_campaign_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    """Page d'import : affiche le formulaire de dépôt de fichier JSON."""
    return templates.TemplateResponse(
        request,
        "campaigns/import.html",
        {"current_user": current_user},
    )


@router.post("/import", response_class=HTMLResponse)
async def import_campaign_post(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Traite le fichier JSON PurpleForge et crée la campagne importée."""
    # 1. Lecture et décodage
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return templates.TemplateResponse(
            request,
            "campaigns/import.html",
            {"error": f"Fichier JSON invalide : {exc}", "current_user": current_user},
            status_code=400,
        )

    # 2. Validation minimale du format
    if "campaign" not in data or "techniques" not in data:
        return templates.TemplateResponse(
            request,
            "campaigns/import.html",
            {
                "error": (
                    "Format non reconnu. Utilise un fichier exporté "
                    "depuis PurpleForge (bouton « ⬇ JSON PurpleForge »)."
                ),
                "current_user": current_user,
            },
            status_code=400,
        )

    camp_data  = data["campaign"]
    techs_data = data.get("techniques", [])

    # 3. Création de la campagne
    raw_name = (camp_data.get("name") or "Campagne importée").strip()
    campaign = Campaign(
        name        = f"{raw_name} (importée)",
        description = (camp_data.get("description") or "").strip(),
        tags        = _normalize_tags(camp_data.get("tags") or ""),
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    # 4. Import des techniques (lignes incomplètes ignorées silencieusement)
    valid_statuses = {s.value for s in TechniqueStatus}
    for t in techs_data:
        attack_id = (t.get("attack_id") or "").strip()
        name      = (t.get("name")      or "").strip()
        tactic    = (t.get("tactic")    or "").strip()
        if not attack_id or not name or not tactic:
            continue

        status_val = (t.get("status") or "non_detecte").strip()
        if status_val not in valid_statuses:
            status_val = "non_detecte"

        session.add(TechniqueEntry(
            campaign_id = campaign.id,
            attack_id   = attack_id,
            name        = name,
            tactic      = tactic,
            status      = TechniqueStatus(status_val),
            blue_note   = (t.get("blue_note") or "").strip() or None,
        ))

    session.commit()

    return RedirectResponse(url=f"/campaigns/{campaign.id}", status_code=303)


@router.get("/{campaign_id}", response_class=HTMLResponse)
def campaign_detail(
    campaign_id: int,
    request: Request,
    page: int = 1,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de détail d'une campagne : ses techniques + leur statut.

    Supporte la pagination via ?page=N (20 techniques par page).
    """
    PER_PAGE = 20

    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return templates.TemplateResponse(
            request, "404.html", {"message": "Campagne introuvable.", "current_user": current_user}, status_code=404
        )

    all_techniques = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.campaign_id == campaign_id)
        .order_by(TechniqueEntry.played_at.desc())
    ).all()

    # Stats globales pour le hero (toutes techniques, pas seulement la page)
    total = len(all_techniques)
    counts = {"detecte": 0, "a_construire": 0, "non_detecte": 0}
    for t in all_techniques:
        counts[t.status.value] = counts.get(t.status.value, 0) + 1
    pct_detecte = round(counts["detecte"] * 100 / total) if total > 0 else 0

    # Pagination
    page = max(1, page)
    nb_pages  = max(1, -(-total // PER_PAGE))   # division entière au plafond
    page      = min(page, nb_pages)
    offset    = (page - 1) * PER_PAGE
    techniques = all_techniques[offset : offset + PER_PAGE]

    return templates.TemplateResponse(
        request,
        "campaigns/detail.html",
        {
            "campaign":    campaign,
            "techniques":  techniques,
            "total":       total,
            "counts":      counts,
            "pct_detecte": pct_detecte,
            "page":        page,
            "nb_pages":    nb_pages,
            "per_page":    PER_PAGE,
            "current_user": current_user,
        },
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


@router.get("/{campaign_id}/remediation", response_class=HTMLResponse)
def campaign_remediation(
    campaign_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Board de suivi de remédiation : toutes les techniques À construire, en 3 colonnes."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return templates.TemplateResponse(
            request, "404.html",
            {"message": "Campagne introuvable.", "current_user": current_user},
            status_code=404,
        )

    # Récupère uniquement les techniques "à construire"
    a_construire = session.exec(
        select(TechniqueEntry)
        .where(
            TechniqueEntry.campaign_id == campaign_id,
            TechniqueEntry.status == TechniqueStatus.a_construire,
        )
        .order_by(TechniqueEntry.attack_id)
    ).all()

    # Groupement par statut de remédiation
    board = {
        "en_cours": [t for t in a_construire if t.remediation_status == "en_cours"],
        "bloque":   [t for t in a_construire if t.remediation_status == "bloque"],
        "termine":  [t for t in a_construire if t.remediation_status == "termine"],
    }

    from datetime import date as _date
    return templates.TemplateResponse(
        request,
        "campaigns/remediation.html",
        {
            "campaign":    campaign,
            "board":       board,
            "total":       len(a_construire),
            "today":       _date.today().isoformat(),
            "current_user": current_user,
        },
    )


@router.get("/{campaign_id}/export/json")
def campaign_export_json(
    campaign_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Exporte la campagne au format JSON natif PurpleForge (réimportable)."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return Response(status_code=404)

    techniques = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.campaign_id == campaign_id)
        .order_by(TechniqueEntry.tactic, TechniqueEntry.attack_id)
    ).all()

    payload = {
        "purpleforge_version": "1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "campaign": {
            "name":        campaign.name,
            "description": campaign.description or "",
            "tags":        campaign.tags or "",
        },
        "techniques": [
            {
                "attack_id": t.attack_id,
                "name":      t.name,
                "tactic":    t.tactic,
                "status":    t.status.value,
                "blue_note": t.blue_note or "",
            }
            for t in techniques
        ],
    }

    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "-"
        for c in campaign.name.lower()
    ).strip("-")
    filename = f"purpleforge-{safe_name}.json"

    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{campaign_id}/export/csv")
def campaign_export_csv(
    campaign_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Exporte la campagne au format CSV (compatible tableur)."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return Response(status_code=404)

    techniques = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.campaign_id == campaign_id)
        .order_by(TechniqueEntry.tactic, TechniqueEntry.attack_id)
    ).all()

    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow(["attack_id", "name", "tactic", "status", "blue_note"])
    for t in techniques:
        writer.writerow([
            t.attack_id,
            t.name,
            t.tactic,
            t.status.value,
            t.blue_note or "",
        ])

    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "-"
        for c in campaign.name.lower()
    ).strip("-")
    filename = f"purpleforge-{safe_name}.csv"

    return Response(
        content=buf.getvalue().encode("utf-8-sig"),   # BOM pour Excel
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{campaign_id}/edit", response_class=HTMLResponse)
def edit_campaign(
    campaign_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Met à jour le nom, la description et les tags d'une campagne."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return RedirectResponse(url="/campaigns/", status_code=303)

    campaign.name        = name.strip() or campaign.name
    campaign.description = description.strip()
    campaign.tags        = _normalize_tags(tags)
    session.add(campaign)
    session.commit()

    return RedirectResponse(url=f"/campaigns/{campaign_id}", status_code=303)


@router.get("/{campaign_id}/remediation/export/csv")
def export_remediation_csv(
    campaign_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Export CSV du suivi de remédiation d'une campagne."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return Response(status_code=404)

    techniques = session.exec(
        select(TechniqueEntry)
        .where(
            TechniqueEntry.campaign_id == campaign_id,
            TechniqueEntry.status == TechniqueStatus.a_construire,
        )
        .order_by(TechniqueEntry.attack_id)
    ).all()

    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "attack_id", "nom", "tactique", "responsable",
        "deadline", "avancement", "campagne",
    ])
    STATUS_FR = {"en_cours": "En cours", "bloque": "Bloqué", "termine": "Terminé"}
    for t in techniques:
        writer.writerow([
            t.attack_id, t.name, t.tactic,
            t.remediation_assignee or "",
            t.remediation_deadline  or "",
            STATUS_FR.get(t.remediation_status, t.remediation_status),
            campaign.name,
        ])

    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in campaign.name.lower()).strip("-")
    return Response(
        content=buf.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="remediation-{safe}.csv"'},
    )


@router.get("/{campaign_id}/remediation/print", response_class=HTMLResponse)
def print_remediation(
    campaign_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page d'impression PDF du suivi de remédiation d'une campagne."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return RedirectResponse(url="/campaigns/", status_code=303)

    techniques = session.exec(
        select(TechniqueEntry)
        .where(
            TechniqueEntry.campaign_id == campaign_id,
            TechniqueEntry.status == TechniqueStatus.a_construire,
        )
        .order_by(TechniqueEntry.attack_id)
    ).all()

    from datetime import date as _date
    today = _date.today().isoformat()
    total = len(techniques)
    nb_termine = sum(1 for t in techniques if t.remediation_status == "termine")
    pct_done   = round(nb_termine * 100 / total) if total > 0 else 0

    return templates.TemplateResponse(
        request,
        "remediation_print.html",
        {
            "campaign":   campaign,
            "techniques": techniques,
            "total":      total,
            "nb_termine": nb_termine,
            "pct_done":   pct_done,
            "today":      today,
            "now":        datetime.now(timezone.utc).strftime("%d/%m/%Y à %H:%M UTC"),
            "global":     False,
            "camp_by_id": {},
        },
    )


@router.post("/{campaign_id}/delete", response_class=HTMLResponse)
def delete_campaign(
    campaign_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Supprime définitivement une campagne et toutes ses techniques.

    Redirige vers la liste des campagnes après suppression.
    """
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return RedirectResponse(url="/campaigns/", status_code=303)

    # Supprimer d'abord toutes les techniques liées (intégrité référentielle)
    techniques = session.exec(
        select(TechniqueEntry).where(TechniqueEntry.campaign_id == campaign_id)
    ).all()
    for t in techniques:
        session.delete(t)

    session.delete(campaign)
    session.commit()

    return RedirectResponse(url="/campaigns/", status_code=303)


@router.get("/{campaign_id}/print", response_class=HTMLResponse)
def campaign_print(
    campaign_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page d'impression / export PDF du rapport de campagne.

    Retourne un HTML autonome optimisé pour l'impression.
    L'utilisateur utilise Ctrl+P → Enregistrer en PDF dans son navigateur.
    """
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return RedirectResponse(url="/campaigns/", status_code=303)

    # Récupération des techniques avec regroupement par tactique.
    techniques = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.campaign_id == campaign_id)
        .order_by(TechniqueEntry.attack_id)
    ).all()

    total = len(techniques)
    counts = {"detecte": 0, "a_construire": 0, "non_detecte": 0}
    for t in techniques:
        counts[t.status.value] = counts.get(t.status.value, 0) + 1
    pct_detecte = round(counts["detecte"] * 100 / total) if total > 0 else 0

    # Regroupement par tactique (ordre canonique ATT&CK).
    by_shortname: dict[str, list] = {}
    for t in techniques:
        by_shortname.setdefault(t.tactic, []).append(t)

    by_tactic = []
    seen: set[str] = set()
    for shortname in TACTIC_ORDER:
        if shortname in by_shortname:
            by_tactic.append({
                "shortname": shortname,
                "name": TACTIC_DISPLAY_NAMES.get(shortname, shortname.replace("-", " ").title()),
                "techniques": by_shortname[shortname],
            })
            seen.add(shortname)
    for shortname, techs in by_shortname.items():
        if shortname not in seen:
            by_tactic.append({
                "shortname": shortname,
                "name": shortname.replace("-", " ").title(),
                "techniques": techs,
            })

    now = datetime.now(timezone.utc).strftime("%d/%m/%Y à %H:%M UTC")

    return templates.TemplateResponse(
        request,
        "campaigns/print.html",
        {
            "campaign":    campaign,
            "total":       total,
            "counts":      counts,
            "pct_detecte": pct_detecte,
            "by_tactic":   by_tactic,
            "now":         now,
        },
    )
