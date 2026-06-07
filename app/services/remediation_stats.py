"""Service de statistiques de remédiation.

Calcule les métriques globales sur toutes les techniques « à construire » :
- Compteurs globaux et taux d'avancement
- Répartition par campagne, par responsable, par tactique
- Points chauds : en retard, sans responsable, sans deadline
"""

from datetime import date
from sqlmodel import Session, select

from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.services.coverage import TACTIC_DISPLAY_NAMES


def compute_remediation_stats(session: Session) -> dict:
    """Retourne toutes les statistiques de remédiation.

    Format :
    {
      "total": int,
      "nb_termine": int, "nb_en_cours": int, "nb_bloque": int,
      "pct_done": int (0-100),
      "nb_overdue": int,
      "nb_no_assignee": int,
      "nb_no_deadline": int,
      "by_campaign": [...],
      "by_assignee": [...],
      "by_tactic": [...],
      "max_camp": int,
      "max_assign": int,
      "max_tactic": int,
    }
    """
    today_iso = date.today().isoformat()

    # ── Toutes les techniques « à construire » ─────────────────────────
    a_construire = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.status == TechniqueStatus.a_construire)
    ).all()

    campaigns = session.exec(select(Campaign)).all()
    camp_by_id = {c.id: c for c in campaigns}

    # ── Compteurs globaux ──────────────────────────────────────────────
    total      = len(a_construire)
    nb_termine = sum(1 for t in a_construire if t.remediation_status == "termine")
    nb_cours   = sum(1 for t in a_construire if t.remediation_status == "en_cours")
    nb_bloque  = sum(1 for t in a_construire if t.remediation_status == "bloque")
    pct_done   = round(nb_termine * 100 / total) if total > 0 else 0

    # ── Points chauds (uniquement parmi les non-terminés) ─────────────
    non_done = [t for t in a_construire if t.remediation_status != "termine"]
    nb_overdue     = sum(1 for t in non_done if t.remediation_deadline and t.remediation_deadline < today_iso)
    nb_no_assignee = sum(1 for t in non_done if not t.remediation_assignee)
    nb_no_deadline = sum(1 for t in non_done if not t.remediation_deadline)

    # ── Par campagne ───────────────────────────────────────────────────
    camp_techs: dict[int, list] = {}
    for t in a_construire:
        camp_techs.setdefault(t.campaign_id, []).append(t)

    by_campaign = []
    for camp_id, techs in sorted(camp_techs.items(), key=lambda x: -len(x[1])):
        camp = camp_by_id.get(camp_id)
        if not camp:
            continue
        tot     = len(techs)
        done    = sum(1 for t in techs if t.remediation_status == "termine")
        cours   = sum(1 for t in techs if t.remediation_status == "en_cours")
        bloque  = sum(1 for t in techs if t.remediation_status == "bloque")
        overdue = sum(1 for t in techs
                      if t.remediation_deadline
                      and t.remediation_deadline < today_iso
                      and t.remediation_status != "termine")
        by_campaign.append({
            "campaign":   camp,
            "total":      tot,
            "nb_termine": done,
            "nb_en_cours": cours,
            "nb_bloque":  bloque,
            "nb_overdue": overdue,
            "pct_done":   round(done * 100 / tot) if tot > 0 else 0,
        })

    # ── Par responsable ────────────────────────────────────────────────
    assign_techs: dict[str, list] = {}
    for t in a_construire:
        key = t.remediation_assignee.strip() if t.remediation_assignee else "(non assigné)"
        assign_techs.setdefault(key, []).append(t)

    by_assignee = []
    for name, techs in sorted(assign_techs.items(), key=lambda x: -len(x[1])):
        tot    = len(techs)
        done   = sum(1 for t in techs if t.remediation_status == "termine")
        cours  = sum(1 for t in techs if t.remediation_status == "en_cours")
        bloque = sum(1 for t in techs if t.remediation_status == "bloque")
        by_assignee.append({
            "name":       name,
            "is_unknown": name == "(non assigné)",
            "total":      tot,
            "nb_termine": done,
            "nb_en_cours": cours,
            "nb_bloque":  bloque,
            "pct_done":   round(done * 100 / tot) if tot > 0 else 0,
        })

    # ── Par tactique (parmi les non-terminés) ──────────────────────────
    tactic_counts: dict[str, int] = {}
    for t in non_done:
        tactic_counts[t.tactic] = tactic_counts.get(t.tactic, 0) + 1

    by_tactic = sorted(
        [
            {
                "shortname": tactic,
                "name":  TACTIC_DISPLAY_NAMES.get(tactic, tactic.replace("-", " ").title()),
                "count": count,
            }
            for tactic, count in tactic_counts.items()
        ],
        key=lambda x: -x["count"],
    )

    return {
        "total":          total,
        "nb_termine":     nb_termine,
        "nb_en_cours":    nb_cours,
        "nb_bloque":      nb_bloque,
        "pct_done":       pct_done,
        "nb_overdue":     nb_overdue,
        "nb_no_assignee": nb_no_assignee,
        "nb_no_deadline": nb_no_deadline,
        "by_campaign":    by_campaign,
        "by_assignee":    by_assignee,
        "by_tactic":      by_tactic,
        "max_camp":       max((i["total"] for i in by_campaign), default=1),
        "max_assign":     max((i["total"] for i in by_assignee), default=1),
        "max_tactic":     max((i["count"] for i in by_tactic),   default=1),
    }
