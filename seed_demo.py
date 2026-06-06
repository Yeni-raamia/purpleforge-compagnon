"""Peuplement de la base avec des données fictives de démonstration.

Usage (depuis purpleforge/) :
    python seed_demo.py

Ce script crée 4 campagnes réalistes avec leurs techniques et statuts.
Il ne supprime pas les données existantes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlmodel import Session
from app.database import engine, create_db_and_tables
from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus

# ─── Données fictives ──────────────────────────────────────────────────────────

CAMPAIGNS = [
    {
        "name": "Red Team Q1 2025 — Intrusion APT28",
        "description": (
            "Simulation d'une intrusion APT28 ciblant l'infrastructure Active Directory "
            "et la messagerie. Premier exercice de l'année — nombreuses lacunes identifiées."
        ),
        "tags": "APT28, Fancy Bear",
        "techniques": [
            # Initial Access
            {
                "attack_id": "T1566", "name": "Phishing",
                "tactic": "initial-access", "status": "detecte",
                "blue_note": "Détecté par Microsoft Defender for Office 365 — règle anti-phishing "
                             "déclenchée sur 3 emails piégés. Temps de détection : 11 min.",
            },
            {
                "attack_id": "T1190", "name": "Exploit Public-Facing Application",
                "tactic": "initial-access", "status": "non_detecte",
                "blue_note": "",
            },
            # Execution
            {
                "attack_id": "T1059", "name": "Command and Scripting Interpreter",
                "tactic": "execution", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1053", "name": "Scheduled Task/Job",
                "tactic": "execution", "status": "a_construire",
                "blue_note": "Activité visible dans les logs Windows (Event ID 4698) "
                             "mais aucune alerte déclenchée. Règle Sigma à créer.",
            },
            # Persistence
            {
                "attack_id": "T1547", "name": "Boot or Logon Autostart Execution",
                "tactic": "persistence", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1136", "name": "Create Account",
                "tactic": "persistence", "status": "detecte",
                "blue_note": "Wazuh a déclenché une alerte sur la création du compte svc_backup$ "
                             "hors des plages de maintenance. Escalade SOC en 7 min.",
            },
            {
                "attack_id": "T1098", "name": "Account Manipulation",
                "tactic": "persistence", "status": "non_detecte",
                "blue_note": "",
            },
            # Defense Evasion
            {
                "attack_id": "T1027", "name": "Obfuscated Files or Information",
                "tactic": "defense-evasion", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1562", "name": "Impair Defenses",
                "tactic": "defense-evasion", "status": "a_construire",
                "blue_note": "Désactivation de Windows Defender visible en logs mais "
                             "sans corrélation ni alerte. Règle à implémenter.",
            },
            {
                "attack_id": "T1055", "name": "Process Injection",
                "tactic": "defense-evasion", "status": "non_detecte",
                "blue_note": "",
            },
            # Credential Access
            {
                "attack_id": "T1003", "name": "OS Credential Dumping",
                "tactic": "credential-access", "status": "a_construire",
                "blue_note": "Accès à lsass.exe tracé par Sysmon (Event ID 10) "
                             "mais aucune alerte. Règle à implémenter sur le processus cible.",
            },
            {
                "attack_id": "T1110", "name": "Brute Force",
                "tactic": "credential-access", "status": "detecte",
                "blue_note": "Fail2ban a bloqué l'IP source après 15 tentatives SMB "
                             "échouées en moins de 2 min.",
            },
            # Discovery
            {
                "attack_id": "T1082", "name": "System Information Discovery",
                "tactic": "discovery", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1046", "name": "Network Service Discovery",
                "tactic": "discovery", "status": "non_detecte",
                "blue_note": "",
            },
            # Lateral Movement
            {
                "attack_id": "T1021", "name": "Remote Services",
                "tactic": "lateral-movement", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1570", "name": "Lateral Tool Transfer",
                "tactic": "lateral-movement", "status": "non_detecte",
                "blue_note": "",
            },
            # Collection
            {
                "attack_id": "T1560", "name": "Archive Collected Data",
                "tactic": "collection", "status": "non_detecte",
                "blue_note": "",
            },
            # Exfiltration
            {
                "attack_id": "T1048", "name": "Exfiltration Over Alternative Protocol",
                "tactic": "exfiltration", "status": "non_detecte",
                "blue_note": "",
            },
        ],
    },
    {
        "name": "Red Team Q2 2025 — Ransomware LockBit",
        "description": (
            "Simulation d'une attaque ransomware de type LockBit sur le SI bureautique. "
            "Focus sur la progression post-intrusion et l'impact. Taux de détection en hausse vs Q1."
        ),
        "tags": "LockBit, Ransomware",
        "techniques": [
            # Initial Access
            {
                "attack_id": "T1566", "name": "Phishing",
                "tactic": "initial-access", "status": "detecte",
                "blue_note": "Sandbox email opérationnelle — URLs malveillantes détonées et "
                             "bloquées. Règle mise à jour depuis Q1 : couverture 97 %.",
            },
            {
                "attack_id": "T1078", "name": "Valid Accounts",
                "tactic": "initial-access", "status": "non_detecte",
                "blue_note": "",
            },
            # Execution
            {
                "attack_id": "T1059", "name": "Command and Scripting Interpreter",
                "tactic": "execution", "status": "detecte",
                "blue_note": "Règle Sigma déployée depuis Q1 — PowerShell encodé (-enc) "
                             "détecté via Wazuh en 3 min.",
            },
            {
                "attack_id": "T1053", "name": "Scheduled Task/Job",
                "tactic": "execution", "status": "detecte",
                "blue_note": "Nouvelle règle Wazuh sur Event ID 4698 opérationnelle — "
                             "alerte déclenchée en 4 min. Amélioration vs Q1.",
            },
            # Persistence
            {
                "attack_id": "T1547", "name": "Boot or Logon Autostart Execution",
                "tactic": "persistence", "status": "a_construire",
                "blue_note": "Clé Run détectée dans les logs Sysmon mais sans alerte "
                             "corrélée côté SIEM. À finaliser.",
            },
            {
                "attack_id": "T1543", "name": "Create or Modify System Process",
                "tactic": "persistence", "status": "non_detecte",
                "blue_note": "",
            },
            # Defense Evasion
            {
                "attack_id": "T1027", "name": "Obfuscated Files or Information",
                "tactic": "defense-evasion", "status": "a_construire",
                "blue_note": "Détecté manuellement lors de l'analyse post-exercice. "
                             "Règle YARA à créer et déployer sur les endpoints.",
            },
            {
                "attack_id": "T1562", "name": "Impair Defenses",
                "tactic": "defense-evasion", "status": "detecte",
                "blue_note": "Alerte sur net stop wscsvc — corrélation SIEM fonctionnelle "
                             "après fix Q1. Temps de détection : 6 min.",
            },
            {
                "attack_id": "T1112", "name": "Modify Registry",
                "tactic": "defense-evasion", "status": "non_detecte",
                "blue_note": "",
            },
            # Credential Access
            {
                "attack_id": "T1003", "name": "OS Credential Dumping",
                "tactic": "credential-access", "status": "detecte",
                "blue_note": "Crowdstrike a bloqué la tentative de dump lsass — "
                             "alerte critique générée et ticket ouvert automatiquement.",
            },
            {
                "attack_id": "T1110", "name": "Brute Force",
                "tactic": "credential-access", "status": "detecte",
                "blue_note": "Politique de verrouillage AD opérationnelle (5 tentatives / 30 min). "
                             "Compte verrouillé et alerte SOC en 1 min 30.",
            },
            # Discovery
            {
                "attack_id": "T1082", "name": "System Information Discovery",
                "tactic": "discovery", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1083", "name": "File and Directory Discovery",
                "tactic": "discovery", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1046", "name": "Network Service Discovery",
                "tactic": "discovery", "status": "a_construire",
                "blue_note": "Scan nmap interne visible dans les logs firewall "
                             "mais sans règle de corrélation côté SIEM.",
            },
            # Lateral Movement
            {
                "attack_id": "T1021", "name": "Remote Services",
                "tactic": "lateral-movement", "status": "a_construire",
                "blue_note": "Connexion RDP inter-serveur tracée dans les logs "
                             "mais non alertée. Règle conditionnelle à affiner.",
            },
            {
                "attack_id": "T1570", "name": "Lateral Tool Transfer",
                "tactic": "lateral-movement", "status": "non_detecte",
                "blue_note": "",
            },
            # Collection
            {
                "attack_id": "T1560", "name": "Archive Collected Data",
                "tactic": "collection", "status": "non_detecte",
                "blue_note": "",
            },
            # Command & Control
            {
                "attack_id": "T1071", "name": "Application Layer Protocol",
                "tactic": "command-and-control", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1105", "name": "Ingress Tool Transfer",
                "tactic": "command-and-control", "status": "non_detecte",
                "blue_note": "",
            },
            # Impact
            {
                "attack_id": "T1486", "name": "Data Encrypted for Impact",
                "tactic": "impact", "status": "a_construire",
                "blue_note": "Chiffrement simulé détecté en post-mortem via logs VSS "
                             "mais aucune alerte temps réel. Honeypot à déployer.",
            },
            {
                "attack_id": "T1489", "name": "Service Stop",
                "tactic": "impact", "status": "detecte",
                "blue_note": "Arrêt des services SQL Server détecté et alerté par "
                             "le monitoring Zabbix en 2 min.",
            },
        ],
    },
    {
        "name": "Exercice Phishing & Accès Initial — FIN7",
        "description": (
            "Campagne centrée sur les techniques d'accès initial et de persistance "
            "caractéristiques du groupe FIN7. Bon taux de détection sur l'accès initial."
        ),
        "tags": "FIN7, Carbanak, Spearphishing",
        "techniques": [
            # Initial Access
            {
                "attack_id": "T1566", "name": "Phishing",
                "tactic": "initial-access", "status": "detecte",
                "blue_note": "Sandbox email opérationnelle — URLs malveillantes détonées et bloquées. "
                             "Formation utilisateurs : taux de clic simulé en baisse (8 % vs 22 % an dernier).",
            },
            {
                "attack_id": "T1190", "name": "Exploit Public-Facing Application",
                "tactic": "initial-access", "status": "detecte",
                "blue_note": "WAF Cloudflare a bloqué l'exploit SQLi sur le portail RH. "
                             "Règle de détection validée.",
            },
            {
                "attack_id": "T1078", "name": "Valid Accounts",
                "tactic": "initial-access", "status": "non_detecte",
                "blue_note": "",
            },
            # Execution
            {
                "attack_id": "T1059", "name": "Command and Scripting Interpreter",
                "tactic": "execution", "status": "detecte",
                "blue_note": "PowerShell CLM actif sur les postes standards — "
                             "exécution bloquée. Alerte Defender en 1 min.",
            },
            {
                "attack_id": "T1204", "name": "User Execution",
                "tactic": "execution", "status": "a_construire",
                "blue_note": "Macro Word exécutée sans alerte sur 2 postes non durcis. "
                             "Politique macro Office à renforcer + règle de détection à créer.",
            },
            # Persistence
            {
                "attack_id": "T1547", "name": "Boot or Logon Autostart Execution",
                "tactic": "persistence", "status": "detecte",
                "blue_note": "Sysmon + règle Wazuh sur création de clés Run — "
                             "alerte déclenchée en 2 min.",
            },
            {
                "attack_id": "T1136", "name": "Create Account",
                "tactic": "persistence", "status": "detecte",
                "blue_note": "SOC alerté immédiatement sur la création d'un compte admin local. "
                             "Ticket P1 ouvert et compte désactivé en 5 min.",
            },
            # Defense Evasion
            {
                "attack_id": "T1027", "name": "Obfuscated Files or Information",
                "tactic": "defense-evasion", "status": "detecte",
                "blue_note": "Règle YARA déployée — payload obfusqué détecté "
                             "à l'écriture disque par Crowdstrike.",
            },
            {
                "attack_id": "T1055", "name": "Process Injection",
                "tactic": "defense-evasion", "status": "a_construire",
                "blue_note": "Injection dans explorer.exe non détectée. "
                             "ETW logging à renforcer sur les processus critiques.",
            },
            # Credential Access
            {
                "attack_id": "T1110", "name": "Brute Force",
                "tactic": "credential-access", "status": "detecte",
                "blue_note": "MFA enforced sur tous les comptes — attaque bloquée "
                             "malgré credentials valides obtenus par phishing.",
            },
            # Discovery
            {
                "attack_id": "T1082", "name": "System Information Discovery",
                "tactic": "discovery", "status": "non_detecte",
                "blue_note": "",
            },
            # Command & Control
            {
                "attack_id": "T1071", "name": "Application Layer Protocol",
                "tactic": "command-and-control", "status": "a_construire",
                "blue_note": "Beacon C2 HTTPS non détecté par le proxy. "
                             "Inspection SSL à activer sur le flux sortant.",
            },
            {
                "attack_id": "T1105", "name": "Ingress Tool Transfer",
                "tactic": "command-and-control", "status": "non_detecte",
                "blue_note": "",
            },
        ],
    },
    {
        "name": "Purple Team — Mouvement Latéral Q3 2025",
        "description": (
            "Exercice focalisé sur le mouvement latéral et l'élévation de privilèges. "
            "Scénario post-compromission initiale simulant APT29. "
            "Meilleur résultat sur credential access grâce aux actions Q1/Q2."
        ),
        "tags": "APT29, Cozy Bear",
        "techniques": [
            # Privilege Escalation
            {
                "attack_id": "T1134", "name": "Access Token Manipulation",
                "tactic": "privilege-escalation", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1055", "name": "Process Injection",
                "tactic": "privilege-escalation", "status": "a_construire",
                "blue_note": "Injection détectée via Sysmon Event ID 8 (CreateRemoteThread) "
                             "mais aucune alerte corrélée côté SIEM.",
            },
            {
                "attack_id": "T1078", "name": "Valid Accounts",
                "tactic": "privilege-escalation", "status": "detecte",
                "blue_note": "Utilisation d'un compte de service détectée hors plage horaire "
                             "habituelle — alerte UBA (User Behavior Analytics) déclenchée.",
            },
            # Defense Evasion
            {
                "attack_id": "T1027", "name": "Obfuscated Files or Information",
                "tactic": "defense-evasion", "status": "detecte",
                "blue_note": "Crowdstrike Falcon détecte le payload obfusqué "
                             "et le met en quarantaine automatiquement.",
            },
            {
                "attack_id": "T1574", "name": "Hijack Execution Flow",
                "tactic": "defense-evasion", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1562", "name": "Impair Defenses",
                "tactic": "defense-evasion", "status": "detecte",
                "blue_note": "Tentative de désactivation d'ETW détectée par Crowdstrike "
                             "et bloquée automatiquement.",
            },
            # Credential Access
            {
                "attack_id": "T1003", "name": "OS Credential Dumping",
                "tactic": "credential-access", "status": "detecte",
                "blue_note": "Credential Guard activé sur tous les DC — "
                             "dump lsass bloqué. Alerte générée en 30 sec.",
            },
            {
                "attack_id": "T1558", "name": "Steal or Forge Kerberos Tickets",
                "tactic": "credential-access", "status": "a_construire",
                "blue_note": "Kerberoasting non détecté. "
                             "Règle sur les demandes TGS anormales (volume + compte service) à créer.",
            },
            {
                "attack_id": "T1552", "name": "Unsecured Credentials",
                "tactic": "credential-access", "status": "non_detecte",
                "blue_note": "",
            },
            # Discovery
            {
                "attack_id": "T1087", "name": "Account Discovery",
                "tactic": "discovery", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1069", "name": "Permission Groups Discovery",
                "tactic": "discovery", "status": "non_detecte",
                "blue_note": "",
            },
            {
                "attack_id": "T1046", "name": "Network Service Discovery",
                "tactic": "discovery", "status": "detecte",
                "blue_note": "Scan interne détecté par NDR Darktrace — "
                             "alerte « Unusual Port Scanning Activity » en 8 min.",
            },
            # Lateral Movement
            {
                "attack_id": "T1021", "name": "Remote Services",
                "tactic": "lateral-movement", "status": "detecte",
                "blue_note": "PAM CyberArk — connexion RDP depuis un poste non habituel "
                             "bloquée et alertée en 3 min.",
            },
            {
                "attack_id": "T1550", "name": "Use Alternate Authentication Material",
                "tactic": "lateral-movement", "status": "non_detecte",
                "blue_note": "Pass-the-Hash non détecté. "
                             "Règle sur authentification NTLM cross-segment à créer.",
            },
            {
                "attack_id": "T1570", "name": "Lateral Tool Transfer",
                "tactic": "lateral-movement", "status": "a_construire",
                "blue_note": "Transfert d'outil via SMB visible dans les logs "
                             "mais sans règle de corrélation SIEM.",
            },
            # Collection
            {
                "attack_id": "T1005", "name": "Data from Local System",
                "tactic": "collection", "status": "non_detecte",
                "blue_note": "",
            },
            # Command & Control
            {
                "attack_id": "T1071", "name": "Application Layer Protocol",
                "tactic": "command-and-control", "status": "a_construire",
                "blue_note": "Tunnel DNS détecté manuellement lors de l'analyse post-exercice. "
                             "Règle de détection DNS-over-HTTPS anormal à déployer.",
            },
        ],
    },
]


def main():
    print("\n=== PurpleForge - Peuplement demo ===\n")

    create_db_and_tables()

    with Session(engine) as session:
        for camp_data in CAMPAIGNS:
            # Création de la campagne
            campaign = Campaign(
                name=camp_data["name"],
                description=camp_data["description"],
                tags=camp_data["tags"],
            )
            session.add(campaign)
            session.commit()
            session.refresh(campaign)

            # Ajout des techniques
            for t in camp_data["techniques"]:
                entry = TechniqueEntry(
                    campaign_id=campaign.id,
                    attack_id=t["attack_id"],
                    name=t["name"],
                    tactic=t["tactic"],
                    status=TechniqueStatus(t["status"]),
                    blue_note=t["blue_note"] or None,
                )
                session.add(entry)

            session.commit()

            total = len(camp_data["techniques"])
            nb_d  = sum(1 for t in camp_data["techniques"] if t["status"] == "detecte")
            nb_a  = sum(1 for t in camp_data["techniques"] if t["status"] == "a_construire")
            nb_n  = sum(1 for t in camp_data["techniques"] if t["status"] == "non_detecte")
            pct   = round(nb_d * 100 / total) if total else 0

            print(f"  [OK] [{campaign.id:>2}] {campaign.name}")
            print(f"       {total} techniques : {nb_d} detectees ({pct}%)"
                  f" / {nb_a} a construire / {nb_n} non detectees")

    print("\n  4 campagnes creees avec succes.")
    print("  Relance le serveur puis ouvre http://127.0.0.1:8080\n")


if __name__ == "__main__":
    main()
