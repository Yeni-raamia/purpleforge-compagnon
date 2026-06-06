"""Service de couverture : calcule les statistiques de détection d'une campagne.

Retourne : comptes par statut, pourcentages, et techniques groupées par tactique
dans l'ordre canonique ATT&CK, pour alimenter la page de couverture.
"""

from sqlmodel import Session, select

from app.models.technique import TechniqueEntry

# Ordre canonique des 14 tactiques ATT&CK Enterprise.
TACTIC_ORDER = [
    "reconnaissance", "resource-development", "initial-access", "execution",
    "persistence", "privilege-escalation", "defense-evasion", "credential-access",
    "discovery", "lateral-movement", "collection", "command-and-control",
    "exfiltration", "impact",
]

# Noms lisibles des tactiques (shortname → affichage).
TACTIC_DISPLAY_NAMES = {
    "reconnaissance": "Reconnaissance",
    "resource-development": "Resource Development",
    "initial-access": "Initial Access",
    "execution": "Execution",
    "persistence": "Persistence",
    "privilege-escalation": "Privilege Escalation",
    "defense-evasion": "Defense Evasion",
    "credential-access": "Credential Access",
    "discovery": "Discovery",
    "lateral-movement": "Lateral Movement",
    "collection": "Collection",
    "command-and-control": "Command and Control",
    "exfiltration": "Exfiltration",
    "impact": "Impact",
}


def compute_coverage(campaign_id: int, session: Session) -> dict:
    """Calcule et retourne les statistiques de couverture d'une campagne.

    Format retourné :
    {
      "total": int,
      "counts":      {"detecte": N, "a_construire": N, "non_detecte": N},
      "percentages": {"detecte": %, "a_construire": %, "non_detecte": %},
      "by_tactic": [
        {"shortname": "credential-access", "name": "Credential Access",
         "techniques": [TechniqueEntry, ...]},
        ...
      ],
    }
    """
    techniques = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.campaign_id == campaign_id)
        .order_by(TechniqueEntry.attack_id)
    ).all()

    total = len(techniques)

    # Comptage par statut.
    counts = {"detecte": 0, "a_construire": 0, "non_detecte": 0}
    for t in techniques:
        counts[t.status.value] = counts.get(t.status.value, 0) + 1

    # Calcul des pourcentages (arrondi à l'entier).
    def pct(n: int) -> int:
        return round(n * 100 / total) if total > 0 else 0

    percentages = {k: pct(v) for k, v in counts.items()}

    # Regroupement par tactique.
    by_shortname: dict[str, list] = {}
    for t in techniques:
        by_shortname.setdefault(t.tactic, []).append(t)

    # Ordonner selon l'ordre canonique ATT&CK.
    by_tactic = []
    seen = set()
    for shortname in TACTIC_ORDER:
        if shortname in by_shortname:
            by_tactic.append({
                "shortname": shortname,
                "name": TACTIC_DISPLAY_NAMES.get(shortname, shortname.replace("-", " ").title()),
                "techniques": by_shortname[shortname],
            })
            seen.add(shortname)
    # Tactiques hors ordre canonique (cas rare).
    for shortname, techs in by_shortname.items():
        if shortname not in seen:
            by_tactic.append({
                "shortname": shortname,
                "name": shortname.replace("-", " ").title(),
                "techniques": techs,
            })

    return {
        "total": total,
        "counts": counts,
        "percentages": percentages,
        "by_tactic": by_tactic,
    }
