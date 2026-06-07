"""Service de tableau de bord — statistiques globales sur toutes les campagnes.

Agrège les données de toutes les campagnes pour la vue d'ensemble :
- Compteurs globaux (campagnes, techniques, taux de détection)
- Résumé par campagne (pour la liste triée)
- Tactiques les plus jouées
"""

from datetime import date
from sqlmodel import Session, select

from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.services.coverage import TACTIC_DISPLAY_NAMES


def compute_dashboard(session: Session) -> dict:
    """Retourne toutes les statistiques pour le tableau de bord.

    Format :
    {
      "nb_campaigns": int,
      "nb_techniques": int,
      "global_pct_detecte": int (0-100),
      "global_counts": {"detecte": N, "a_construire": N, "non_detecte": N},
      "campaigns": [
        {
          "campaign": Campaign,
          "total": int,
          "counts": {...},
          "pct_detecte": int,
        },
        ...
      ],
      "top_tactics": [
        {"name": str, "count": int},
        ...
      ],
    }
    """
    # ── Toutes les campagnes (récentes en premier) ─────────────────────────
    campaigns = session.exec(
        select(Campaign).order_by(Campaign.created_at.desc())
    ).all()

    # ── Toutes les techniques (une seule requête) ──────────────────────────
    all_techniques = session.exec(select(TechniqueEntry)).all()

    # Index des techniques par campagne_id.
    tech_by_campaign: dict[int, list[TechniqueEntry]] = {}
    for t in all_techniques:
        tech_by_campaign.setdefault(t.campaign_id, []).append(t)

    # ── Compteurs globaux ─────────────────────────────────────────────────
    global_counts = {"detecte": 0, "a_construire": 0, "non_detecte": 0}
    for t in all_techniques:
        global_counts[t.status.value] = global_counts.get(t.status.value, 0) + 1

    nb_total = len(all_techniques)
    global_pct = round(global_counts["detecte"] * 100 / nb_total) if nb_total > 0 else 0

    # ── Résumé par campagne ───────────────────────────────────────────────
    campaigns_summary = []
    for c in campaigns:
        techs = tech_by_campaign.get(c.id, [])
        total = len(techs)
        counts = {"detecte": 0, "a_construire": 0, "non_detecte": 0}
        for t in techs:
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        pct = round(counts["detecte"] * 100 / total) if total > 0 else 0
        campaigns_summary.append({
            "campaign": c,
            "total": total,
            "counts": counts,
            "pct_detecte": pct,
        })

    # ── Top tactiques (les plus représentées toutes campagnes confondues) ──
    tactic_counts: dict[str, int] = {}
    for t in all_techniques:
        tactic_counts[t.tactic] = tactic_counts.get(t.tactic, 0) + 1

    top_tactics = sorted(
        [
            {
                "shortname": tactic,
                "name": TACTIC_DISPLAY_NAMES.get(tactic, tactic.replace("-", " ").title()),
                "count": count,
            }
            for tactic, count in tactic_counts.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )[:6]  # Top 6

    # ── Remédiatins en retard (deadline dépassée, pas encore terminée) ────
    today_iso = date.today().isoformat()
    camp_by_id = {c.id: c for c in campaigns}   # accès O(1)
    overdue = []
    for t in all_techniques:
        if (
            t.status.value == "a_construire"
            and t.remediation_deadline
            and t.remediation_deadline < today_iso
            and t.remediation_status != "termine"
        ):
            camp = camp_by_id.get(t.campaign_id)
            try:
                days = (date.today() - date.fromisoformat(t.remediation_deadline)).days
            except ValueError:
                days = 0
            overdue.append({
                "technique":     t,
                "campaign_name": camp.name if camp else "?",
                "campaign_id":   t.campaign_id,
                "days_overdue":  days,
            })

    # Les plus en retard en premier
    overdue.sort(key=lambda x: x["days_overdue"], reverse=True)

    return {
        "nb_campaigns":          len(campaigns),
        "nb_techniques":         nb_total,
        "global_pct_detecte":    global_pct,
        "global_counts":         global_counts,
        "campaigns":             campaigns_summary,
        "top_tactics":           top_tactics,
        "overdue_remediations":  overdue[:10],   # max 10 alertes
    }
