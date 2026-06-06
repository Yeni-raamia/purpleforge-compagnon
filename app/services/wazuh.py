"""Service de conversion Sigma YAML → Wazuh XML.

Convertit une règle Sigma (format SigmaHQ YAML) en règle Wazuh XML
prête à déposer dans /var/ossec/etc/rules/local_rules.xml.

Principe :
  - Les métadonnées (niveau, MITRE, description) sont converties fidèlement.
  - Les champs de détection sont traduits "best-effort" : les champs Windows
    courants sont mappés vers leurs équivalents Wazuh (win.eventdata.*,
    win.system.*), les autres vers full_log.
  - Les conditions complexes (AND/OR multi-selection) sont simplifiées :
    on prend les 4 premiers champs détectés.

Aucune dépendance externe (utilise PyYAML déjà installé).
"""

import hashlib
import re
import xml.sax.saxutils as saxutils

import yaml

# ─── Mapping champs Sigma courants → champs Wazuh JSON ──────────────────────
FIELD_MAP: dict[str, str] = {
    # Windows — Sysmon / EventLog
    "commandline":        "win.eventdata.commandLine",
    "image":              "win.eventdata.image",
    "parentimage":        "win.eventdata.parentImage",
    "sourceimage":        "win.eventdata.sourceImage",
    "targetimage":        "win.eventdata.targetImage",
    "targetfilename":     "win.eventdata.targetFileName",
    "targetprocessname":  "win.eventdata.targetProcessName",
    "processname":        "win.eventdata.processName",
    "originalfilename":   "win.eventdata.originalFileName",
    "description":        "win.eventdata.description",
    "product":            "win.eventdata.product",
    "company":            "win.eventdata.company",
    "integritylevel":     "win.eventdata.integrityLevel",
    "eventid":            "win.system.eventID",
    "channel":            "win.system.channel",
    "computername":       "win.system.computer",
    "user":               "win.eventdata.user",
    "username":           "win.eventdata.user",
    "subjectusername":    "win.eventdata.subjectUserName",
    "targetusername":     "win.eventdata.targetUserName",
    "logontype":          "win.eventdata.logonType",
    "destinationport":    "win.eventdata.destinationPort",
    "destinationip":      "win.eventdata.destinationIp",
    "sourceport":         "win.eventdata.sourcePort",
    "sourceip":           "win.eventdata.sourceIp",
    "queriedname":        "win.eventdata.queriedName",
    "queryname":          "win.eventdata.queryName",
    "imagepath":          "win.eventdata.imagePath",
    "servicename":        "win.eventdata.serviceName",
    "targetobject":       "win.eventdata.targetObject",
    "details":            "win.eventdata.details",
    "objectname":         "win.eventdata.objectName",
    "objecttype":         "win.eventdata.objectType",
    "accessmask":         "win.eventdata.accessMask",
    "grantedaccess":      "win.eventdata.grantedAccess",
    "calltrace":          "win.eventdata.callTrace",
    "hashes":             "win.eventdata.hashes",
    "signature":          "win.eventdata.signature",
    "signaturedesc":      "win.eventdata.signatureDesc",
    "signed":             "win.eventdata.signed",
    "rulesname":          "win.eventdata.rulesName",
    # Linux / auditd
    "comm":               "audit.command",
    "exe":                "audit.exe",
    "key":                "audit.key",
    "syscall":            "audit.syscall",
    "auid":               "audit.auid",
    "uid":                "audit.uid",
    # Réseau
    "dst_ip":             "data.dstip",
    "src_ip":             "data.srcip",
    "dst_port":           "data.dstport",
    "src_port":           "data.srcport",
    "method":             "data.method",
    "url":                "data.url",
    # Générique (fallback)
    "keywords":           "full_log",
    "msg":                "full_log",
}

# ─── Mapping niveau Sigma → niveau Wazuh (0–15) ──────────────────────────────
LEVEL_MAP: dict[str, int] = {
    "critical":      15,
    "high":          12,
    "medium":        10,
    "low":            6,
    "informational":  3,
}


def _field_name(sigma_field: str) -> str:
    """Traduit un champ Sigma (avec éventuel modifier) en champ Wazuh."""
    base = sigma_field.split("|")[0].strip().lower()
    return FIELD_MAP.get(base, "full_log")


def _extract_modifier(sigma_key: str) -> str:
    """Retourne le premier modifier d'un champ Sigma : 'contains', 're', etc."""
    parts = sigma_key.split("|")
    return parts[1].lower() if len(parts) > 1 else "contains"


def _values_to_pcre2(values: list, modifier: str) -> str:
    """Convertit une liste de valeurs Sigma en expression pcre2."""
    patterns = []
    for v in values:
        v = str(v)
        if modifier == "re":
            # Déjà une regex, on l'utilise telle quelle.
            patterns.append(v)
        elif modifier == "endswith":
            patterns.append(re.escape(v.rstrip("*")) + "$")
        elif modifier == "startswith":
            patterns.append("^" + re.escape(v.lstrip("*")))
        else:
            # contains / default : les jokers * deviennent .*
            patterns.append(re.escape(v).replace(r"\*", ".*"))
    return "|".join(p for p in patterns if p)


def _parse_selection(selection: dict) -> list[tuple[str, str]]:
    """Extrait des paires (wazuh_field, pcre2_pattern) depuis une selection."""
    results = []
    if not isinstance(selection, dict):
        return results

    for key, val in selection.items():
        modifier = _extract_modifier(key)
        wazuh_field = _field_name(key)

        vals = val if isinstance(val, list) else [val]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue

        pattern = _values_to_pcre2(vals, modifier)
        if pattern:
            # (?i) = insensibilité à la casse, standard Wazuh pcre2.
            results.append((wazuh_field, f"(?i)(?:{pattern})"))

    return results


def _logsource_to_decoder(product: str, category: str, service: str) -> str:
    """Retourne le decoder Wazuh à utiliser selon le logsource Sigma."""
    product  = (product  or "").lower()
    category = (category or "").lower()
    service  = (service  or "").lower()

    if product == "windows":
        sysmon_cats = {"process_creation", "file_event", "network_connection",
                       "image_load", "driver_load", "registry_event",
                       "registry_add", "registry_delete", "registry_rename",
                       "registry_set", "pipe_created", "raw_access_thread",
                       "process_access", "create_remote_thread"}
        if service == "sysmon" or category in sysmon_cats:
            return "windows-sysmon"
        if service == "security":
            return "windows-security"
        if service == "system":
            return "windows-system"
        if service == "application":
            return "windows-application"
        if service == "powershell":
            return "windows-powershell"
        return "windows-eventlog"

    if product == "linux":
        if service in ("auditd", "audit"):
            return "auditd"
        if service in ("auth", "sshd", "cron", "sudo"):
            return "syslog"
        return "syslog"

    if product in ("aws", "azure", "gcp", "m365", "okta", "github"):
        return "json"

    return ""


def sigma_yaml_to_wazuh_xml(yaml_content: str, fallback_attack_id: str = "") -> str:
    """Convertit une règle Sigma YAML en règle Wazuh XML (best-effort).

    Args:
        yaml_content:      Contenu YAML de la règle Sigma.
        fallback_attack_id: ATT&CK ID de secours si absent des tags.

    Returns:
        Chaîne XML valide pour /var/ossec/etc/rules/local_rules.xml.
    """
    # ── Lecture du YAML ────────────────────────────────────────────────────
    try:
        rule = yaml.safe_load(yaml_content) or {}
    except Exception:
        rule = {}

    title      = (rule.get("title") or "Sigma Rule").strip()
    level_str  = (rule.get("level") or "medium").lower()
    wazuh_lvl  = LEVEL_MAP.get(level_str, 10)

    # ── ATT&CK IDs depuis les tags Sigma ──────────────────────────────────
    attack_ids: list[str] = []
    for tag in (rule.get("tags") or []):
        if isinstance(tag, str) and tag.lower().startswith("attack.t"):
            tid = tag[7:].upper()   # "attack.t1003.001" → "T1003.001"
            if tid not in attack_ids:
                attack_ids.append(tid)
    if not attack_ids and fallback_attack_id:
        attack_ids = [fallback_attack_id.upper()]

    # ── Logsource → decoder Wazuh ─────────────────────────────────────────
    ls = rule.get("logsource") or {}
    decoded_as = _logsource_to_decoder(
        ls.get("product", ""),
        ls.get("category", ""),
        ls.get("service", ""),
    )

    # ── Detection → <field> elements (max 4 champs) ───────────────────────
    detection  = rule.get("detection") or {}
    field_pairs: list[tuple[str, str]] = []
    for sel_key, sel_val in detection.items():
        if sel_key == "condition":
            continue
        if isinstance(sel_val, dict):
            field_pairs.extend(_parse_selection(sel_val))
        if len(field_pairs) >= 4:
            break
    field_pairs = field_pairs[:4]

    # ── ID de règle pseudo-unique (plage locale 100000–109999) ────────────
    rule_id = 100000 + (int(hashlib.md5(title.encode()).hexdigest(), 16) % 9999)

    # ── Groupe Wazuh ──────────────────────────────────────────────────────
    group_parts = ["local", "attack"]
    for mid in attack_ids:
        group_parts.append(mid.lower().replace(".", "_"))
    group_str = ",".join(group_parts)

    # ── Escaping XML ──────────────────────────────────────────────────────
    safe_title = saxutils.escape(title)
    attack_sfx = f" ({', '.join(attack_ids)})" if attack_ids else ""

    # ── Assemblage du XML ─────────────────────────────────────────────────
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- ═══════════════════════════════════════════════════════════════ -->",
        "<!-- Règle générée automatiquement par PurpleForge Compagnon        -->",
        f"<!-- Sigma  : {saxutils.escape(title):<54} -->",
        f"<!-- Niveau : {level_str:<54} -->",
        "<!-- À déposer dans /var/ossec/etc/rules/local_rules.xml            -->",
        "<!-- Vérifier la correspondance des champs avant déploiement.       -->",
        "<!-- ═══════════════════════════════════════════════════════════════ -->",
        "",
        f'<group name="{group_str}">',
        "",
        f'  <rule id="{rule_id}" level="{wazuh_lvl}">',
    ]

    # Decoder
    if decoded_as:
        lines.append(f"    <decoded_as>{decoded_as}</decoded_as>")

    # Champs de détection
    for wf, pattern in field_pairs:
        safe_pat = saxutils.escape(pattern)
        lines.append(f'    <field name="{wf}" type="pcre2">{safe_pat}</field>')

    # Description + MITRE
    lines.append(f"    <description>{safe_title}{saxutils.escape(attack_sfx)}</description>")

    if attack_ids:
        lines.append("    <mitre>")
        for mid in attack_ids:
            lines.append(f"      <id>{mid}</id>")
        lines.append("    </mitre>")

    lines.extend([
        f"    <group>{group_str},</group>",
        "  </rule>",
        "",
        "</group>",
    ])

    return "\n".join(lines)
