"""Profils d'attaquants connus — données statiques pour les templates de campagnes.

Chaque profil contient :
  - slug        : identifiant URL (ex. "apt28")
  - name        : nom principal du groupe
  - aliases     : autres noms connus
  - origin      : pays d'origine (texte)
  - flag        : emoji drapeau
  - motivation  : liste de motivations (espionnage, financier, destructif…)
  - description : courte présentation
  - techniques  : liste de dicts {attack_id, name, tactic}

Sources : MITRE ATT&CK, CISA, Mandiant, Crowdstrike.
"""

APT_TEMPLATES: list[dict] = [
    {
        "slug":        "apt28",
        "name":        "APT28",
        "aliases":     ["Fancy Bear", "Sofacy", "STRONTIUM"],
        "origin":      "Russie",
        "flag":        "RU",
        "motivation":  ["Espionnage", "Influence"],
        "description": (
            "Groupe lié au renseignement militaire russe (GRU). Cible les gouvernements, "
            "l'OTAN, les partis politiques et les médias. Connu pour l'opération Cloud Hopper "
            "et les ingérences électorales."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1190", "name": "Exploit Public-Facing Application",    "tactic": "initial-access"},
            {"attack_id": "T1078", "name": "Valid Accounts",                        "tactic": "initial-access"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1053", "name": "Scheduled Task/Job",                   "tactic": "execution"},
            {"attack_id": "T1547", "name": "Boot or Logon Autostart Execution",    "tactic": "persistence"},
            {"attack_id": "T1098", "name": "Account Manipulation",                 "tactic": "persistence"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1055", "name": "Process Injection",                    "tactic": "defense-evasion"},
            {"attack_id": "T1562", "name": "Impair Defenses",                      "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1110", "name": "Brute Force",                          "tactic": "credential-access"},
            {"attack_id": "T1082", "name": "System Information Discovery",         "tactic": "discovery"},
            {"attack_id": "T1016", "name": "System Network Configuration Discovery","tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1570", "name": "Lateral Tool Transfer",                "tactic": "lateral-movement"},
            {"attack_id": "T1071", "name": "Application Layer Protocol",           "tactic": "command-and-control"},
            {"attack_id": "T1048", "name": "Exfiltration Over Alternative Protocol","tactic": "exfiltration"},
        ],
    },
    {
        "slug":        "apt29",
        "name":        "APT29",
        "aliases":     ["Cozy Bear", "Midnight Blizzard", "Nobelium"],
        "origin":      "Russie",
        "flag":        "RU",
        "motivation":  ["Espionnage"],
        "description": (
            "Groupe lié au renseignement extérieur russe (SVR). Opérations très discrètes, "
            "longue persistence. Responsable du piratage de SolarWinds (2020) et de l'intrusion "
            "dans les serveurs du Comité National Démocrate."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1195", "name": "Supply Chain Compromise",              "tactic": "initial-access"},
            {"attack_id": "T1078", "name": "Valid Accounts",                       "tactic": "initial-access"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1106", "name": "Native API",                           "tactic": "execution"},
            {"attack_id": "T1547", "name": "Boot or Logon Autostart Execution",    "tactic": "persistence"},
            {"attack_id": "T1098", "name": "Account Manipulation",                 "tactic": "persistence"},
            {"attack_id": "T1134", "name": "Access Token Manipulation",            "tactic": "defense-evasion"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1562", "name": "Impair Defenses",                      "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1558", "name": "Steal or Forge Kerberos Tickets",      "tactic": "credential-access"},
            {"attack_id": "T1087", "name": "Account Discovery",                    "tactic": "discovery"},
            {"attack_id": "T1069", "name": "Permission Groups Discovery",           "tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1550", "name": "Use Alternate Authentication Material","tactic": "lateral-movement"},
            {"attack_id": "T1071", "name": "Application Layer Protocol",           "tactic": "command-and-control"},
            {"attack_id": "T1102", "name": "Web Service",                          "tactic": "command-and-control"},
            {"attack_id": "T1041", "name": "Exfiltration Over C2 Channel",         "tactic": "exfiltration"},
        ],
    },
    {
        "slug":        "apt41",
        "name":        "APT41",
        "aliases":     ["Double Dragon", "Winnti", "Barium"],
        "origin":      "Chine",
        "flag":        "CN",
        "motivation":  ["Espionnage", "Financier"],
        "description": (
            "Groupe unique à double casquette : espionnage étatique chinois ET cybercriminalité "
            "financière. Cible la santé, les télécoms, les jeux vidéo et la supply chain logicielle."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1190", "name": "Exploit Public-Facing Application",    "tactic": "initial-access"},
            {"attack_id": "T1195", "name": "Supply Chain Compromise",              "tactic": "initial-access"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1053", "name": "Scheduled Task/Job",                   "tactic": "execution"},
            {"attack_id": "T1547", "name": "Boot or Logon Autostart Execution",    "tactic": "persistence"},
            {"attack_id": "T1078", "name": "Valid Accounts",                       "tactic": "persistence"},
            {"attack_id": "T1574", "name": "Hijack Execution Flow",                "tactic": "defense-evasion"},
            {"attack_id": "T1036", "name": "Masquerading",                         "tactic": "defense-evasion"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1558", "name": "Steal or Forge Kerberos Tickets",      "tactic": "credential-access"},
            {"attack_id": "T1087", "name": "Account Discovery",                    "tactic": "discovery"},
            {"attack_id": "T1046", "name": "Network Service Discovery",            "tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1570", "name": "Lateral Tool Transfer",                "tactic": "lateral-movement"},
            {"attack_id": "T1071", "name": "Application Layer Protocol",           "tactic": "command-and-control"},
            {"attack_id": "T1048", "name": "Exfiltration Over Alternative Protocol","tactic": "exfiltration"},
        ],
    },
    {
        "slug":        "lazarus",
        "name":        "Lazarus Group",
        "aliases":     ["Hidden Cobra", "Guardians of Peace", "Zinc"],
        "origin":      "Corée du Nord",
        "flag":        "KP",
        "motivation":  ["Financier", "Espionnage", "Destructif"],
        "description": (
            "Groupe lié à la Corée du Nord (RGB). Mène des opérations financières massives "
            "(vol de cryptomonnaies, attaques bancaires SWIFT) et des sabotages. "
            "Responsable de WannaCry (2017) et du vol de 1,5 Md$ en crypto."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1190", "name": "Exploit Public-Facing Application",    "tactic": "initial-access"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1204", "name": "User Execution",                       "tactic": "execution"},
            {"attack_id": "T1547", "name": "Boot or Logon Autostart Execution",    "tactic": "persistence"},
            {"attack_id": "T1543", "name": "Create or Modify System Process",      "tactic": "persistence"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1036", "name": "Masquerading",                         "tactic": "defense-evasion"},
            {"attack_id": "T1055", "name": "Process Injection",                    "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1082", "name": "System Information Discovery",         "tactic": "discovery"},
            {"attack_id": "T1083", "name": "File and Directory Discovery",         "tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1570", "name": "Lateral Tool Transfer",                "tactic": "lateral-movement"},
            {"attack_id": "T1105", "name": "Ingress Tool Transfer",                "tactic": "command-and-control"},
            {"attack_id": "T1071", "name": "Application Layer Protocol",           "tactic": "command-and-control"},
            {"attack_id": "T1486", "name": "Data Encrypted for Impact",            "tactic": "impact"},
            {"attack_id": "T1529", "name": "System Shutdown/Reboot",               "tactic": "impact"},
        ],
    },
    {
        "slug":        "fin7",
        "name":        "FIN7",
        "aliases":     ["Carbanak", "Navigator Group", "ITG14"],
        "origin":      "Europe de l'Est",
        "flag":        "EU",
        "motivation":  ["Financier"],
        "description": (
            "Groupe cybercriminel très organisé, ciblant la restauration, le commerce de détail "
            "et l'hôtellerie pour voler des données de cartes bancaires. Opère des campagnes "
            "de spearphishing très ciblées avec des documents Office piégés."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1204", "name": "User Execution",                       "tactic": "execution"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1547", "name": "Boot or Logon Autostart Execution",    "tactic": "persistence"},
            {"attack_id": "T1136", "name": "Create Account",                       "tactic": "persistence"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1055", "name": "Process Injection",                    "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1082", "name": "System Information Discovery",         "tactic": "discovery"},
            {"attack_id": "T1083", "name": "File and Directory Discovery",         "tactic": "discovery"},
            {"attack_id": "T1057", "name": "Process Discovery",                    "tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1560", "name": "Archive Collected Data",               "tactic": "collection"},
            {"attack_id": "T1113", "name": "Screen Capture",                       "tactic": "collection"},
            {"attack_id": "T1071", "name": "Application Layer Protocol",           "tactic": "command-and-control"},
            {"attack_id": "T1048", "name": "Exfiltration Over Alternative Protocol","tactic": "exfiltration"},
        ],
    },
    {
        "slug":        "lockbit",
        "name":        "LockBit",
        "aliases":     ["LockBit 3.0", "ABCD Group"],
        "origin":      "International",
        "flag":        "INT",
        "motivation":  ["Financier", "Ransomware"],
        "description": (
            "L'un des groupes ransomware les plus actifs et dommageables depuis 2019. "
            "Opère en Ransomware-as-a-Service (RaaS). Cible tous les secteurs, "
            "avec une forte présence dans la santé, l'industrie et les collectivités."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1190", "name": "Exploit Public-Facing Application",    "tactic": "initial-access"},
            {"attack_id": "T1078", "name": "Valid Accounts",                       "tactic": "initial-access"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1053", "name": "Scheduled Task/Job",                   "tactic": "execution"},
            {"attack_id": "T1547", "name": "Boot or Logon Autostart Execution",    "tactic": "persistence"},
            {"attack_id": "T1562", "name": "Impair Defenses",                      "tactic": "defense-evasion"},
            {"attack_id": "T1112", "name": "Modify Registry",                      "tactic": "defense-evasion"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1110", "name": "Brute Force",                          "tactic": "credential-access"},
            {"attack_id": "T1082", "name": "System Information Discovery",         "tactic": "discovery"},
            {"attack_id": "T1046", "name": "Network Service Discovery",            "tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1570", "name": "Lateral Tool Transfer",                "tactic": "lateral-movement"},
            {"attack_id": "T1560", "name": "Archive Collected Data",               "tactic": "collection"},
            {"attack_id": "T1486", "name": "Data Encrypted for Impact",            "tactic": "impact"},
            {"attack_id": "T1489", "name": "Service Stop",                         "tactic": "impact"},
            {"attack_id": "T1490", "name": "Inhibit System Recovery",              "tactic": "impact"},
        ],
    },
    {
        "slug":        "sandworm",
        "name":        "Sandworm",
        "aliases":     ["Voodoo Bear", "BlackEnergy", "Seashell Blizzard"],
        "origin":      "Russie",
        "flag":        "RU",
        "motivation":  ["Destructif", "Espionnage"],
        "description": (
            "Unité 74455 du GRU russe, spécialisée dans les attaques destructives "
            "sur les infrastructures critiques. Responsable des coupures électriques "
            "en Ukraine (2015-2016), NotPetya (2017) et des attaques sur les JO de Pyeongchang."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1190", "name": "Exploit Public-Facing Application",    "tactic": "initial-access"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1072", "name": "Software Deployment Tools",            "tactic": "execution"},
            {"attack_id": "T1543", "name": "Create or Modify System Process",      "tactic": "persistence"},
            {"attack_id": "T1562", "name": "Impair Defenses",                      "tactic": "defense-evasion"},
            {"attack_id": "T1036", "name": "Masquerading",                         "tactic": "defense-evasion"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1046", "name": "Network Service Discovery",            "tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1570", "name": "Lateral Tool Transfer",                "tactic": "lateral-movement"},
            {"attack_id": "T1485", "name": "Data Destruction",                     "tactic": "impact"},
            {"attack_id": "T1486", "name": "Data Encrypted for Impact",            "tactic": "impact"},
            {"attack_id": "T1489", "name": "Service Stop",                         "tactic": "impact"},
            {"attack_id": "T1490", "name": "Inhibit System Recovery",              "tactic": "impact"},
            {"attack_id": "T1529", "name": "System Shutdown/Reboot",               "tactic": "impact"},
        ],
    },
    {
        "slug":        "turla",
        "name":        "Turla",
        "aliases":     ["Snake", "Uroburos", "Waterbug", "Secret Blizzard"],
        "origin":      "Russie",
        "flag":        "RU",
        "motivation":  ["Espionnage"],
        "description": (
            "L'un des groupes APT les plus sophistiqués et les plus anciens (actif depuis 2004). "
            "Lié au FSB russe. Réputé pour ses techniques de persistance très avancées, "
            "l'utilisation de satellites pour son C2, et ses malwares Snake/Uroburos."
        ),
        "techniques": [
            {"attack_id": "T1566", "name": "Phishing",                            "tactic": "initial-access"},
            {"attack_id": "T1190", "name": "Exploit Public-Facing Application",    "tactic": "initial-access"},
            {"attack_id": "T1059", "name": "Command and Scripting Interpreter",    "tactic": "execution"},
            {"attack_id": "T1547", "name": "Boot or Logon Autostart Execution",    "tactic": "persistence"},
            {"attack_id": "T1098", "name": "Account Manipulation",                 "tactic": "persistence"},
            {"attack_id": "T1027", "name": "Obfuscated Files or Information",      "tactic": "defense-evasion"},
            {"attack_id": "T1055", "name": "Process Injection",                    "tactic": "defense-evasion"},
            {"attack_id": "T1562", "name": "Impair Defenses",                      "tactic": "defense-evasion"},
            {"attack_id": "T1003", "name": "OS Credential Dumping",                "tactic": "credential-access"},
            {"attack_id": "T1552", "name": "Unsecured Credentials",                "tactic": "credential-access"},
            {"attack_id": "T1082", "name": "System Information Discovery",         "tactic": "discovery"},
            {"attack_id": "T1016", "name": "System Network Configuration Discovery","tactic": "discovery"},
            {"attack_id": "T1021", "name": "Remote Services",                      "tactic": "lateral-movement"},
            {"attack_id": "T1102", "name": "Web Service",                          "tactic": "command-and-control"},
            {"attack_id": "T1071", "name": "Application Layer Protocol",           "tactic": "command-and-control"},
            {"attack_id": "T1048", "name": "Exfiltration Over Alternative Protocol","tactic": "exfiltration"},
        ],
    },
]

# Index par slug pour accès rapide
APT_BY_SLUG: dict[str, dict] = {t["slug"]: t for t in APT_TEMPLATES}

# Couleurs par motivation (pour les badges)
MOTIVATION_COLORS: dict[str, str] = {
    "Espionnage":  "#7B2FBE",
    "Financier":   "#D97706",
    "Destructif":  "#DC2626",
    "Ransomware":  "#B91C1C",
    "Influence":   "#2563EB",
}
