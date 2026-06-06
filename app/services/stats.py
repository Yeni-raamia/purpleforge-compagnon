"""Service de calcul des statistiques globales.

Agrège les données de toutes les campagnes pour produire :
  - Évolution temporelle du taux de détection
  - Répartition par tactique (toutes campagnes confondues)
  - Top 10 des techniques les plus souvent non détectées
"""

from collections import defaultdict

from sqlmodel import Session, select

from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.services.coverage import TACTIC_ORDER, TACTIC_DISPLAY_NAMES


def compute_global_stats(session: Session) -> dict:
    """Calcule toutes les statistiques globales en une passe."""

    # ── 1. Toutes les campagnes triées par date ────────────────────────────
    campaigns = session.exec(
        select(Campaign).order_by(Campaign.created_at)
    ).all()

    # ── 2. Toutes les techniques ───────────────────────────────────────────
    all_entries = session.exec(select(TechniqueEntry)).all()

    # Index : campaign_id → liste de TechniqueEntry
    by_campaign: dict[int, list] = defaultdict(list)
    for t in all_entries:
        by_campaign[t.campaign_id].append(t)

    # ── 3. Évolution temporelle ────────────────────────────────────────────
    evolution = []
    for c in campaigns:
        techs = by_campaign.get(c.id, [])
        total = len(techs)
        nb_d  = sum(1 for t in techs if t.status == TechniqueStatus.detecte)
        nb_a  = sum(1 for t in techs if t.status == TechniqueStatus.a_construire)
        nb_n  = sum(1 for t in techs if t.status == TechniqueStatus.non_detecte)
        pct   = round(nb_d * 100 / total) if total else 0
        evolution.append({
            "campaign_id": c.id,
            "name":        c.name,
            "short_name":  c.name[:28] + "…" if len(c.name) > 30 else c.name,
            "date":        c.created_at.strftime("%d/%m/%Y"),
            "total":       total,
            "nb_detecte":  nb_d,
            "nb_construire": nb_a,
            "nb_non":      nb_n,
            "pct":         pct,
        })

    # ── 4. Répartition par tactique (toutes campagnes) ─────────────────────
    tactic_agg: dict[str, dict] = defaultdict(lambda: {"d": 0, "a": 0, "n": 0})
    for t in all_entries:
        key = t.tactic
        if t.status == TechniqueStatus.detecte:
            tactic_agg[key]["d"] += 1
        elif t.status == TechniqueStatus.a_construire:
            tactic_agg[key]["a"] += 1
        else:
            tactic_agg[key]["n"] += 1

    by_tactic = []
    for shortname in TACTIC_ORDER:
        if shortname not in tactic_agg:
            continue
        d = tactic_agg[shortname]
        total = d["d"] + d["a"] + d["n"]
        pct   = round(d["d"] * 100 / total) if total else 0
        by_tactic.append({
            "shortname":   shortname,
            "name":        TACTIC_DISPLAY_NAMES.get(shortname, shortname.replace("-", " ").title()),
            "detecte":     d["d"],
            "a_construire": d["a"],
            "non_detecte": d["n"],
            "total":       total,
            "pct":         pct,
        })

    # Tri : tactiques les moins couvertes en premier
    by_tactic_sorted = sorted(by_tactic, key=lambda x: x["pct"])

    # ── 5. Top 10 techniques non détectées ─────────────────────────────────
    tech_agg: dict[str, dict] = {}
    for t in all_entries:
        if t.status == TechniqueStatus.detecte:
            continue   # on ne compte que les non-couvertes
        key = t.attack_id
        if key not in tech_agg:
            tech_agg[key] = {
                "attack_id":   t.attack_id,
                "name":        t.name,
                "tactic":      t.tactic,
                "count":       0,
                "a_construire": 0,
                "non_detecte": 0,
            }
        tech_agg[key]["count"] += 1
        tech_agg[key][t.status.value] += 1

    top_non_detecte = sorted(
        tech_agg.values(),
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    # ── 6. Résumé global ───────────────────────────────────────────────────
    total_all  = len(all_entries)
    nb_det_all = sum(1 for t in all_entries if t.status == TechniqueStatus.detecte)
    global_pct = round(nb_det_all * 100 / total_all) if total_all else 0

    weakest_tactic = by_tactic_sorted[0] if by_tactic_sorted else None
    strongest_tactic = by_tactic_sorted[-1] if by_tactic_sorted else None

    return {
        "evolution":        evolution,
        "by_tactic":        by_tactic,           # ordre canonique (pour chart)
        "by_tactic_sorted": by_tactic_sorted,    # ordre croissant pct (pour liste)
        "top_non_detecte":  top_non_detecte,
        "nb_campaigns":     len(campaigns),
        "total_entries":    total_all,
        "global_pct":       global_pct,
        "weakest_tactic":   weakest_tactic,
        "strongest_tactic": strongest_tactic,
    }
