"""Service de recherche globale.

Recherche dans toutes les campagnes et techniques :
- Nom de campagne
- ATT&CK ID (ex : T1003, T1003.001)
- Nom de technique
- Notes blue team
- Tags APT

Retourne des résultats groupés par campagne, triés par pertinence.
"""

from sqlmodel import Session, select, or_

from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry


MAX_RESULTS = 60   # limite totale pour éviter les pages interminables


def search(query: str, session: Session) -> dict:
    """Effectue la recherche et retourne les résultats groupés.

    Format retourné :
    {
      "query": str,
      "total": int,
      "campaign_hits": [
        {
          "campaign": Campaign,
          "techniques": [TechniqueEntry, ...],   # techniques qui matchent
          "campaign_match": bool,                 # le nom/tag de la campagne matche aussi
        },
        ...
      ]
    }
    """
    q = query.strip()
    if len(q) < 2:
        return {"query": q, "total": 0, "campaign_hits": []}

    pattern = f"%{q}%"

    # ── Campagnes dont le nom ou les tags correspondent ────────────────────
    matching_campaigns = session.exec(
        select(Campaign).where(
            or_(
                Campaign.name.ilike(pattern),
                Campaign.description.ilike(pattern),
                Campaign.tags.ilike(pattern),
            )
        ).order_by(Campaign.created_at.desc())
    ).all()
    matching_campaign_ids = {c.id for c in matching_campaigns}

    # ── Techniques qui correspondent ───────────────────────────────────────
    matching_techniques = session.exec(
        select(TechniqueEntry).where(
            or_(
                TechniqueEntry.attack_id.ilike(pattern),
                TechniqueEntry.name.ilike(pattern),
                TechniqueEntry.blue_note.ilike(pattern),
                TechniqueEntry.tactic.ilike(pattern),
            )
        ).limit(MAX_RESULTS)
    ).all()

    # ── Regroupement par campagne ──────────────────────────────────────────
    # On charge toutes les campagnes concernées d'un coup.
    all_campaign_ids = matching_campaign_ids | {t.campaign_id for t in matching_techniques}

    if not all_campaign_ids:
        return {"query": q, "total": 0, "campaign_hits": []}

    all_campaigns = {
        c.id: c
        for c in session.exec(
            select(Campaign).where(Campaign.id.in_(list(all_campaign_ids)))
        ).all()
    }

    # Index des techniques par campagne.
    techs_by_campaign: dict[int, list[TechniqueEntry]] = {}
    for t in matching_techniques:
        techs_by_campaign.setdefault(t.campaign_id, []).append(t)

    # Assemblage final — campagnes triées par nombre de résultats décroissant.
    hits = []
    seen = set()
    for campaign_id in sorted(
        all_campaign_ids,
        key=lambda cid: len(techs_by_campaign.get(cid, [])),
        reverse=True,
    ):
        if campaign_id in seen or campaign_id not in all_campaigns:
            continue
        seen.add(campaign_id)
        hits.append({
            "campaign":       all_campaigns[campaign_id],
            "techniques":     techs_by_campaign.get(campaign_id, []),
            "campaign_match": campaign_id in matching_campaign_ids,
        })

    total = sum(
        (1 if h["campaign_match"] else 0) + len(h["techniques"])
        for h in hits
    )

    return {"query": q, "total": total, "campaign_hits": hits}


def highlight(text: str, query: str, max_len: int = 120) -> str:
    """Retourne un extrait du texte avec le terme de recherche en contexte.

    Trouve la première occurrence (insensible à la casse) et retourne
    les caractères autour pour donner du contexte.
    """
    if not text or not query:
        return text[:max_len] if text else ""

    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:max_len] + ("…" if len(text) > max_len else "")

    # On centre l'extrait autour de la correspondance.
    start = max(0, idx - 40)
    end   = min(len(text), idx + len(query) + 80)
    snippet = ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")
    return snippet
