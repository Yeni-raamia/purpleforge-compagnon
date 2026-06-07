"""Tests des routes HTTP — PurpleForge Compagnon.

Chaque classe regroupe les tests d'un domaine fonctionnel :
  - Campagnes  : liste, détail, édition, suppression, exports, pagination
  - Techniques : ajout, mise à jour (statut + notes), suppression, remédiation
  - Dashboard  : vue globale, board kanban global, stats remédiation
  - Cas limites : pages inconnues, paramètres hors-bornes, statuts invalides

Toutes les routes nécessitent un utilisateur connecté ; le client de test
injecte un utilisateur fictif via app.dependency_overrides (conftest.py).
Les données de test sont créées dans la base SQLite en mémoire partagée
par la session de tests.
"""

import json
import pytest

from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus


# ══════════════════════════════════════════════════════════════════════════════
# Campagnes — liste & création
# ══════════════════════════════════════════════════════════════════════════════

class TestCampaignList:
    """Tests sur GET /campaigns/ et POST /campaigns/ (création)."""

    def test_list_200(self, client):
        """La liste des campagnes est accessible et renvoie 200."""
        r = client.get("/campaigns/")
        assert r.status_code == 200

    def test_list_contient_html(self, client):
        """La réponse est bien du HTML contenant un mot clé attendu."""
        r = client.get("/campaigns/")
        assert "campagne" in r.text.lower() or "PurpleForge" in r.text

    def test_create_campaign_redirige(self, client):
        """Créer une campagne soumet le formulaire et suit la redirection."""
        r = client.post(
            "/campaigns/",
            data={"name": "Campagne Smoke", "description": "", "tags": ""},
        )
        # Le TestClient de Starlette suit les redirections → 200 final
        assert r.status_code == 200

    def test_campaign_creee_apparait_dans_liste(self, client):
        """La campagne nouvellement créée est visible dans la liste."""
        client.post(
            "/campaigns/",
            data={"name": "Campagne Visible XYZ", "description": "", "tags": ""},
        )
        r = client.get("/campaigns/")
        assert "Campagne Visible XYZ" in r.text

    def test_create_campaign_normalise_tags(self, client):
        """Les tags avec point-virgule sont normalisés (pas d'erreur 500)."""
        r = client.post(
            "/campaigns/",
            data={"name": "Campagne Tags Semi", "description": "", "tags": "APT28 ; APT29"},
        )
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# Campagnes — page de détail
# ══════════════════════════════════════════════════════════════════════════════

class TestCampaignDetail:
    """Tests sur GET /campaigns/{id} (détail + pagination)."""

    def test_detail_200(self, client, sample_campaign):
        """La page de détail d'une campagne existante renvoie 200."""
        r = client.get(f"/campaigns/{sample_campaign.id}")
        assert r.status_code == 200

    def test_detail_affiche_nom_campagne(self, client, sample_campaign):
        """Le nom de la campagne est présent dans la réponse HTML."""
        r = client.get(f"/campaigns/{sample_campaign.id}")
        assert sample_campaign.name in r.text

    def test_detail_affiche_tags(self, client, sample_campaign):
        """Les tags de la campagne sont affichés."""
        r = client.get(f"/campaigns/{sample_campaign.id}")
        assert "APT28" in r.text

    def test_detail_404_campagne_inconnue(self, client):
        """Une campagne inexistante renvoie 404."""
        r = client.get("/campaigns/999999")
        assert r.status_code == 404

    def test_pagination_page1(self, client, sample_campaign):
        """?page=1 renvoie la première page sans erreur."""
        r = client.get(f"/campaigns/{sample_campaign.id}?page=1")
        assert r.status_code == 200

    def test_pagination_page_hors_bornes_haute(self, client, sample_campaign):
        """Une page très grande est ramenée à la dernière page valide (200)."""
        r = client.get(f"/campaigns/{sample_campaign.id}?page=9999")
        assert r.status_code == 200

    def test_pagination_page_negative_clamped(self, client, sample_campaign):
        """Un numéro de page négatif est ramené à 1 (200)."""
        r = client.get(f"/campaigns/{sample_campaign.id}?page=-3")
        assert r.status_code == 200

    def test_pagination_page_zero_clamped(self, client, sample_campaign):
        """page=0 est ramené à 1 (200)."""
        r = client.get(f"/campaigns/{sample_campaign.id}?page=0")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# Campagnes — édition & suppression
# ══════════════════════════════════════════════════════════════════════════════

class TestCampaignEdition:
    """Tests sur POST /campaigns/{id}/edit."""

    def test_edit_persiste_nouveau_nom(self, client, sample_campaign):
        """L'édition d'une campagne met à jour le nom affiché."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/edit",
            data={"name": "Campagne Renommée OK", "description": "Nouvelle desc", "tags": "APT41"},
        )
        assert r.status_code == 200
        assert "Campagne Renommée OK" in r.text

    def test_edit_campagne_inconnue_redirige(self, client):
        """Éditer une campagne inexistante redirige proprement (200 après redirect)."""
        r = client.post(
            "/campaigns/999998/edit",
            data={"name": "X", "description": "", "tags": ""},
        )
        assert r.status_code == 200


class TestCampaignSuppression:
    """Tests sur POST /campaigns/{id}/delete."""

    def test_delete_campagne_redirige(self, client, db_session):
        """Supprimer une campagne suit la redirection vers la liste (200)."""
        # Campagne dédiée à ce test pour ne pas perturber sample_campaign
        c = Campaign(name="À Supprimer Maintenant", description="", tags="")
        db_session.add(c)
        db_session.commit()
        db_session.refresh(c)

        r = client.post(f"/campaigns/{c.id}/delete")
        assert r.status_code == 200  # après redirection vers /campaigns/

    def test_delete_campagne_inconnue_redirige(self, client):
        """Supprimer une campagne inexistante redirige sans erreur."""
        r = client.post("/campaigns/999997/delete")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# Campagnes — pages secondaires
# ══════════════════════════════════════════════════════════════════════════════

class TestCampaignCoverage:
    def test_coverage_200(self, client, sample_campaign):
        r = client.get(f"/campaigns/{sample_campaign.id}/coverage")
        assert r.status_code == 200

    def test_coverage_404_campagne_inconnue(self, client):
        r = client.get("/campaigns/999999/coverage")
        assert r.status_code == 404


class TestCampaignPrint:
    def test_print_200(self, client, sample_campaign):
        r = client.get(f"/campaigns/{sample_campaign.id}/print")
        assert r.status_code == 200


class TestCampaignTemplates:
    def test_templates_200(self, client):
        """La galerie de templates APT renvoie 200."""
        r = client.get("/campaigns/templates")
        assert r.status_code == 200

    def test_templates_contient_apt(self, client):
        """La page des templates mentionne au moins un nom d'APT connu."""
        r = client.get("/campaigns/templates")
        # Au moins un groupe connu est présent dans la page
        assert any(g in r.text for g in ["APT28", "APT29", "Lazarus", "Sandworm"])


class TestCampaignCompare:
    def test_compare_sans_selection_200(self, client):
        """La page de comparaison sans paramètres renvoie 200."""
        r = client.get("/campaigns/compare")
        assert r.status_code == 200

    def test_compare_meme_campagne_affiche_erreur(self, client, sample_campaign):
        """Comparer une campagne à elle-même affiche un message d'erreur."""
        cid = sample_campaign.id
        r = client.get(f"/campaigns/compare?a={cid}&b={cid}")
        assert r.status_code == 200
        # Le message "différentes" fait partie de l'erreur retournée
        assert "différentes" in r.text

    def test_compare_campagne_inconnue_affiche_erreur(self, client, sample_campaign):
        """Comparer avec une campagne inexistante affiche un message d'erreur."""
        r = client.get(f"/campaigns/compare?a={sample_campaign.id}&b=999999")
        assert r.status_code == 200
        assert "introuvable" in r.text.lower()


class TestCampaignImport:
    def test_import_page_200(self, client):
        """La page d'import renvoie 200."""
        r = client.get("/campaigns/import")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# Campagnes — exports
# ══════════════════════════════════════════════════════════════════════════════

class TestCampaignExports:
    """Tests sur les endpoints d'export (JSON Navigator, JSON PurpleForge, CSV)."""

    def test_export_navigator_json(self, client, sample_campaign):
        """L'export Navigator JSON renvoie du JSON avec les clés attendues."""
        r = client.get(f"/campaigns/{sample_campaign.id}/export")
        assert r.status_code == 200
        data = json.loads(r.content)
        assert "techniques" in data
        assert "domain" in data
        assert data["domain"] == "enterprise-attack"

    def test_export_navigator_json_nom_campagne(self, client, sample_campaign):
        """L'export Navigator JSON contient le nom de la campagne."""
        r = client.get(f"/campaigns/{sample_campaign.id}/export")
        data = json.loads(r.content)
        assert data["name"] == sample_campaign.name

    def test_export_purpleforge_json(self, client, sample_campaign):
        """L'export JSON PurpleForge contient les clés campaign + techniques."""
        r = client.get(f"/campaigns/{sample_campaign.id}/export/json")
        assert r.status_code == 200
        data = json.loads(r.content)
        assert "campaign" in data
        assert "techniques" in data
        assert "purpleforge_version" in data

    def test_export_purpleforge_json_contient_nom(self, client, sample_campaign):
        """Le JSON PurpleForge contient le nom exact de la campagne."""
        r = client.get(f"/campaigns/{sample_campaign.id}/export/json")
        data = json.loads(r.content)
        assert data["campaign"]["name"] == sample_campaign.name

    def test_export_purpleforge_json_contient_technique(self, client, sample_campaign, sample_technique):
        """Le JSON PurpleForge contient bien la technique de test."""
        r = client.get(f"/campaigns/{sample_campaign.id}/export/json")
        data = json.loads(r.content)
        attack_ids = [t["attack_id"] for t in data["techniques"]]
        assert sample_technique.attack_id in attack_ids

    def test_export_csv(self, client, sample_campaign):
        """L'export CSV renvoie du contenu texte avec les bons en-têtes."""
        r = client.get(f"/campaigns/{sample_campaign.id}/export/csv")
        assert r.status_code == 200
        # En-têtes obligatoires
        assert "attack_id" in r.text
        assert "name" in r.text
        assert "tactic" in r.text
        assert "status" in r.text

    def test_export_csv_contient_technique(self, client, sample_campaign, sample_technique):
        """Le CSV contient bien la technique de test."""
        r = client.get(f"/campaigns/{sample_campaign.id}/export/csv")
        assert sample_technique.attack_id in r.text


# ══════════════════════════════════════════════════════════════════════════════
# Campagnes — remédiation par campagne
# ══════════════════════════════════════════════════════════════════════════════

class TestCampaignRemediation:
    """Tests sur le board de remédiation d'une campagne spécifique."""

    def test_remediation_200(self, client, sample_campaign):
        r = client.get(f"/campaigns/{sample_campaign.id}/remediation")
        assert r.status_code == 200

    def test_remediation_404_campagne_inconnue(self, client):
        r = client.get("/campaigns/999999/remediation")
        assert r.status_code == 404

    def test_remediation_export_csv(self, client, sample_campaign):
        """L'export CSV de remédiation renvoie du CSV avec les bons en-têtes."""
        r = client.get(f"/campaigns/{sample_campaign.id}/remediation/export/csv")
        assert r.status_code == 200
        assert "attack_id" in r.text
        assert "campagne" in r.text.lower()

    def test_remediation_print(self, client, sample_campaign):
        """La page d'impression remédiation renvoie 200."""
        r = client.get(f"/campaigns/{sample_campaign.id}/remediation/print")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# Techniques — ajout & mise à jour
# ══════════════════════════════════════════════════════════════════════════════

class TestTechniqueAjout:
    """Tests sur POST /campaigns/{id}/techniques (ajout depuis la matrice)."""

    def test_ajout_retourne_badge(self, client, sample_campaign):
        """Ajouter une technique retourne un badge HTML 'Ajoutée'."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques",
            data={
                "attack_id": "T1078",
                "name": "Valid Accounts",
                "tactic": "initial-access",
            },
        )
        assert r.status_code == 200
        assert "Ajoutée" in r.text

    def test_ajout_deux_fois_idempotent(self, client, sample_campaign):
        """Ajouter la même technique deux fois ne provoque pas d'erreur."""
        data = {
            "attack_id": "T1055",
            "name": "Process Injection",
            "tactic": "privilege-escalation",
        }
        r1 = client.post(f"/campaigns/{sample_campaign.id}/techniques", data=data)
        r2 = client.post(f"/campaigns/{sample_campaign.id}/techniques", data=data)
        assert r1.status_code == 200
        assert r2.status_code == 200


class TestTechniqueMiseAJour:
    """Tests sur POST /campaigns/{id}/techniques/{tid} (mise à jour statut/notes)."""

    def test_update_statut_detecte(self, client, sample_campaign, sample_technique):
        """Passer une technique en 'détecté' retourne un fragment HTML."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}",
            data={"status": "detecte", "blue_note": "Règle Sigma active", "red_note": ""},
        )
        assert r.status_code == 200
        assert sample_technique.attack_id in r.text

    def test_update_statut_a_construire(self, client, sample_campaign, sample_technique):
        """Passer en 'à construire' retourne le fragment mis à jour."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}",
            data={"status": "a_construire", "blue_note": "", "red_note": ""},
        )
        assert r.status_code == 200

    def test_update_red_note(self, client, sample_campaign, sample_technique):
        """La note red team est acceptée sans erreur."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}",
            data={
                "status": "non_detecte",
                "blue_note": "",
                "red_note": "Exécution confirmée via PowerShell",
            },
        )
        assert r.status_code == 200

    def test_update_statut_inconnu_ignore(self, client, sample_campaign, sample_technique):
        """Un statut inconnu ne provoque pas d'erreur 500 (silencieusement ignoré)."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}",
            data={"status": "inexistant_xyz", "blue_note": "", "red_note": ""},
        )
        assert r.status_code == 200

    def test_update_mauvais_campaign_id_404(self, client, sample_technique):
        """Modifier une technique avec un campaign_id erroné retourne 404."""
        r = client.post(
            f"/campaigns/999999/techniques/{sample_technique.id}",
            data={"status": "detecte", "blue_note": "", "red_note": ""},
        )
        assert r.status_code == 404


class TestTechniqueSuppression:
    """Tests sur POST /campaigns/{id}/techniques/{tid}/delete."""

    def test_delete_retourne_chaine_vide(self, client, sample_campaign, db_session):
        """Supprimer une technique retourne une réponse vide (HTMX outerHTML)."""
        # Technique dédiée à ce test
        tech = TechniqueEntry(
            campaign_id=sample_campaign.id,
            attack_id="T1070",
            name="Indicator Removal",
            tactic="defense-evasion",
            status=TechniqueStatus.non_detecte,
            blue_note="",
            red_note="",
        )
        db_session.add(tech)
        db_session.commit()
        db_session.refresh(tech)

        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{tech.id}/delete"
        )
        assert r.status_code == 200
        assert r.text.strip() == ""  # La carte disparaît de l'interface HTMX

    def test_delete_mauvais_campaign_id_404(self, client, sample_technique):
        """Supprimer avec un campaign_id erroné retourne 404."""
        r = client.post(
            f"/campaigns/999999/techniques/{sample_technique.id}/delete"
        )
        assert r.status_code == 404

    def test_delete_technique_inexistante_404(self, client, sample_campaign):
        """Supprimer une technique inexistante retourne 404."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/999999/delete"
        )
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# Techniques — remédiation
# ══════════════════════════════════════════════════════════════════════════════

class TestTechniqueRemediation:
    """Tests sur POST /campaigns/{id}/techniques/{tid}/remediation."""

    def test_inline_retourne_feedback(self, client, sample_campaign, sample_technique):
        """Sans ?board, la mise à jour retourne un feedback HTML inline."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}/remediation",
            data={
                "assignee": "alice@soc.local",
                "deadline": "2025-12-31",
                "remed_status": "en_cours",
            },
        )
        assert r.status_code == 200
        assert "Sauvegardé" in r.text

    def test_board1_redirige_vers_board_campagne(self, client, sample_campaign, sample_technique):
        """?board=1 redirige vers le board de remédiation de la campagne."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}/remediation?board=1",
            data={"assignee": "bob", "deadline": "", "remed_status": "termine"},
        )
        # Après redirection /campaigns/{id}/remediation → 200
        assert r.status_code == 200

    def test_board2_redirige_vers_board_global(self, client, sample_campaign, sample_technique):
        """?board=2 redirige vers le board de remédiation global."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}/remediation?board=2",
            data={"assignee": "", "deadline": "", "remed_status": "bloque"},
        )
        # Après redirection /remediation → 200
        assert r.status_code == 200

    def test_statut_invalide_corrige_en_en_cours(self, client, sample_campaign, sample_technique, db_session):
        """Un statut remédiation invalide est silencieusement corrigé en 'en_cours'."""
        r = client.post(
            f"/campaigns/{sample_campaign.id}/techniques/{sample_technique.id}/remediation",
            data={"assignee": "", "deadline": "", "remed_status": "valeur_inconnue"},
        )
        assert r.status_code == 200
        # Rechargement depuis la base pour vérifier la valeur persistée
        db_session.refresh(sample_technique)
        assert sample_technique.remediation_status == "en_cours"

    def test_remediation_mauvais_campaign_id_404(self, client, sample_technique):
        """Mettre à jour la remédiation avec un campaign_id erroné retourne 404."""
        r = client.post(
            f"/campaigns/999999/techniques/{sample_technique.id}/remediation",
            data={"assignee": "", "deadline": "", "remed_status": "en_cours"},
        )
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class TestDashboard:
    """Tests sur GET /dashboard."""

    def test_dashboard_200(self, client):
        r = client.get("/dashboard")
        assert r.status_code == 200

    def test_dashboard_contient_html(self, client):
        """La page contient du contenu lié à PurpleForge."""
        r = client.get("/dashboard")
        assert "PurpleForge" in r.text or "campagne" in r.text.lower()


# ══════════════════════════════════════════════════════════════════════════════
# Remédiation globale
# ══════════════════════════════════════════════════════════════════════════════

class TestRemediationGlobale:
    """Tests sur les routes /remediation (board global, stats, exports)."""

    def test_board_global_200(self, client):
        """Le board kanban global renvoie 200."""
        r = client.get("/remediation")
        assert r.status_code == 200

    def test_stats_remediation_200(self, client):
        """La page de statistiques de remédiation renvoie 200."""
        r = client.get("/remediation/stats")
        assert r.status_code == 200

    def test_export_csv_global_200(self, client):
        """L'export CSV global est accessible et renvoie du texte CSV."""
        r = client.get("/remediation/export/csv")
        assert r.status_code == 200
        assert "attack_id" in r.text

    def test_export_csv_global_entetes(self, client):
        """Le CSV global contient toutes les colonnes attendues."""
        r = client.get("/remediation/export/csv")
        assert "nom" in r.text.lower() or "attack_id" in r.text
        assert "campagne" in r.text.lower()

    def test_print_global_200(self, client):
        """La page d'impression PDF globale renvoie 200."""
        r = client.get("/remediation/print")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# Intégration — scénario de bout en bout
# ══════════════════════════════════════════════════════════════════════════════

class TestScenarioComplet:
    """Scénario de bout en bout : créer, peupler, vérifier, exporter, supprimer."""

    def test_cycle_complet(self, client, db_session):
        """
        Scénario : créer une campagne → ajouter une technique → mettre à jour
        le statut → vérifier l'export CSV → supprimer la technique → supprimer
        la campagne.
        """
        # 1. Créer une campagne
        r = client.post(
            "/campaigns/",
            data={"name": "Campagne E2E", "description": "Scénario complet", "tags": "FIN7"},
        )
        assert r.status_code == 200

        # 2. Retrouver l'ID de la campagne créée
        r_list = client.get("/campaigns/")
        assert "Campagne E2E" in r_list.text

        from sqlmodel import select
        camp = db_session.exec(
            select(Campaign).where(Campaign.name == "Campagne E2E")
        ).first()
        assert camp is not None
        cid = camp.id

        # 3. Ajouter une technique
        r_add = client.post(
            f"/campaigns/{cid}/techniques",
            data={"attack_id": "T1566", "name": "Phishing", "tactic": "initial-access"},
        )
        assert r_add.status_code == 200

        # 4. Récupérer l'ID de la technique créée
        tech = db_session.exec(
            select(TechniqueEntry).where(
                TechniqueEntry.campaign_id == cid,
                TechniqueEntry.attack_id == "T1566",
            )
        ).first()
        assert tech is not None
        tid = tech.id

        # 5. Mettre à jour son statut
        r_upd = client.post(
            f"/campaigns/{cid}/techniques/{tid}",
            data={"status": "detecte", "blue_note": "Règle Sigma #42", "red_note": ""},
        )
        assert r_upd.status_code == 200

        # 6. Vérifier l'export JSON
        r_json = client.get(f"/campaigns/{cid}/export/json")
        payload = json.loads(r_json.content)
        techs_in_export = {t["attack_id"]: t for t in payload["techniques"]}
        assert "T1566" in techs_in_export
        assert techs_in_export["T1566"]["status"] == "detecte"

        # 7. Supprimer la technique
        r_del = client.post(f"/campaigns/{cid}/techniques/{tid}/delete")
        assert r_del.status_code == 200

        # 8. Supprimer la campagne
        r_delc = client.post(f"/campaigns/{cid}/delete")
        assert r_delc.status_code == 200
