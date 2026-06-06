"""Utilitaire de réinitialisation de mot de passe.

Utilisation (depuis le dossier purpleforge/) :
    python reset_password.py

Ce script :
  1. Affiche les utilisateurs existants
  2. Demande un identifiant
  3. Demande un nouveau mot de passe
  4. Met à jour la base de données
"""

import sqlite3
import getpass
import sys

try:
    import bcrypt
except ImportError:
    print("❌ Module bcrypt introuvable. Lance : pip install bcrypt")
    sys.exit(1)

DB_PATH = "purpleforge.db"


def main():
    print("\n╔══════════════════════════════════════════╗")
    print("║  PurpleForge — Réinitialisation de MDP   ║")
    print("╚══════════════════════════════════════════╝\n")

    # ── Vérification que la base existe ──────────────────────────────────
    try:
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
    except Exception as e:
        print(f"❌ Impossible d'ouvrir la base : {e}")
        print("   Lance ce script depuis le dossier purpleforge/ (là où se trouve purpleforge.db)")
        sys.exit(1)

    # ── Liste des utilisateurs ──────────────────────────────────────────
    cur.execute("SELECT id, username, display_name, is_admin FROM user")
    rows = cur.fetchall()

    if not rows:
        print("❌ Aucun utilisateur trouvé dans la base.")
        print("   Vérifie que tu es dans le bon dossier (purpleforge/).")
        conn.close()
        sys.exit(1)

    print("Utilisateurs existants :")
    for uid, username, display_name, is_admin in rows:
        role = "admin" if is_admin else "utilisateur"
        print(f"  [{uid}] {username}  ({display_name or '—'})  · {role}")

    # ── Saisie de l'identifiant ─────────────────────────────────────────
    print()
    username = input("Identifiant à modifier : ").strip()

    cur.execute("SELECT id FROM user WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        print(f"❌ Utilisateur « {username} » introuvable.")
        conn.close()
        sys.exit(1)

    user_id = row[0]

    # ── Nouveau mot de passe ────────────────────────────────────────────
    print("\nNouveau mot de passe (la saisie est masquée) :")
    new_pwd = getpass.getpass("  Nouveau MDP  : ")
    confirm = getpass.getpass("  Confirmer   : ")

    if new_pwd != confirm:
        print("❌ Les mots de passe ne correspondent pas.")
        conn.close()
        sys.exit(1)

    if len(new_pwd) < 8:
        print("❌ Mot de passe trop court (minimum 8 caractères).")
        conn.close()
        sys.exit(1)

    # ── Hachage & mise à jour ───────────────────────────────────────────
    hashed = bcrypt.hashpw(new_pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute("UPDATE user SET hashed_password = ? WHERE id = ?", (hashed, user_id))
    conn.commit()
    conn.close()

    print(f"\n✅ Mot de passe de « {username} » mis à jour avec succès.")
    print("   Tu peux maintenant te connecter sur http://127.0.0.1:8080/login\n")


if __name__ == "__main__":
    main()
