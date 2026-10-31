from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rubanrose.models import Activite, Cagnotte, Organisation

PREFIXE = '[DÉMO]'
MOT_DE_PASSE = 'Demo2026!rose'
MENTION = "Organisation fictive créée uniquement pour la démonstration de la plateforme. "


class Command(BaseCommand):
    help = "Crée (ou supprime avec --supprimer) des données FICTIVES de démonstration."

    def add_arguments(self, parser):
        parser.add_argument(
            '--supprimer', action='store_true',
            help='Supprime toutes les données de démonstration.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['supprimer']:
            n, _ = User.objects.filter(username__startswith='demo_').delete()
            self.stdout.write(self.style.WARNING(f'{n} objet(s) de démonstration supprimé(s).'))
            return

        maintenant = timezone.now().replace(minute=0, second=0, microsecond=0)
        aujourdhui = timezone.localdate()

        def creer_org(username, nom, ville, zone, description, statut):
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=username, password=MOT_DE_PASSE,
                    email=f'{username}@example.org',
                )
            org, _ = Organisation.objects.get_or_create(
                user=user,
                defaults=dict(
                    nom=f'{PREFIXE} {nom}',
                    description=MENTION + description,
                    zone_intervention=zone,
                    ville=ville,
                    email_public=f'{username}@example.org',
                    telephone_public='+229 00 00 00 00',
                    statut_verification=statut,
                ),
            )
            return org

        org1 = creer_org(
            'demo_ruban', "Association Ruban d'Espoir", 'Cotonou',
            'Cotonou et environs',
            "Elle sert d'exemple pour présenter des actions de sensibilisation et de dépistage.",
            Organisation.Statut.APPROUVEE,
        )
        org2 = creer_org(
            'demo_solidarite', 'Collectif Solidarité Rose', 'Porto-Novo',
            'Département de l\'Ouémé',
            "Elle sert d'exemple pour présenter des actions d'accompagnement et de solidarité.",
            Organisation.Statut.APPROUVEE,
        )
        creer_org(
            'demo_attente', 'Réseau Femmes en Lumière', 'Parakou',
            'Département du Borgou',
            "Elle est volontairement en attente de vérification, pour tester l'administration.",
            Organisation.Statut.EN_ATTENTE,
        )

        def creer_activite(org, titre, categorie, lieu, jours, statut, description):
            Activite.objects.get_or_create(
                organisation=org, titre=f'{PREFIXE} {titre}',
                defaults=dict(
                    description=MENTION + description,
                    categorie=categorie, lieu=lieu,
                    date_debut=maintenant + timedelta(days=jours),
                    statut=statut,
                ),
            )

        P, A = Activite.Statut.PUBLIEE, Activite.Statut.EN_ATTENTE
        C = Activite.Categorie
        creer_activite(org1, 'Journée de sensibilisation', C.SENSIBILISATION,
                       'Place publique (exemple)', 10, P,
                       "Activité d'exemple : information du public sur la prévention.")
        creer_activite(org1, 'Matinée de dépistage', C.DEPISTAGE,
                       'Centre de santé (exemple)', 25, P,
                       "Activité d'exemple : consultation et orientation.")
        creer_activite(org1, 'Atelier en attente de validation', C.AUTRE,
                       'Salle communale (exemple)', 40, A,
                       "Activité d'exemple pour tester la validation par l'administrateur.")
        creer_activite(org2, 'Conférence sur la prévention', C.CONFERENCE,
                       'Salle de conférence (exemple)', 18, P,
                       "Activité d'exemple : échanges avec des professionnels.")
        creer_activite(org2, 'Groupe de parole', C.ACCOMPAGNEMENT,
                       'Local associatif (exemple)', -20, P,
                       "Activité passée d'exemple : accompagnement et écoute.")

        def creer_cagnotte(org, titre, objectif, statut, description):
            Cagnotte.objects.get_or_create(
                organisation=org, titre=f'{PREFIXE} {titre}',
                defaults=dict(
                    description=MENTION + description,
                    objectif_financier=objectif,
                    montant_collecte=None,  # aucune collecte réelle : on ne simule rien
                    date_debut=aujourdhui - timedelta(days=5),
                    date_fin=aujourdhui + timedelta(days=60),
                    informations_transparence=(
                        "Exemple fictif : utilisation prévue des fonds, responsables du suivi "
                        "et compte rendu public à la fin de la collecte."
                    ),
                    statut=statut,
                ),
            )

        creer_cagnotte(org1, 'Soutien aux dépistages gratuits', 500000,
                       Cagnotte.Statut.VALIDEE,
                       "Cagnotte d'exemple : financement fictif de journées de dépistage.")
        creer_cagnotte(org2, 'Kits de solidarité', 300000,
                       Cagnotte.Statut.VALIDEE,
                       "Cagnotte d'exemple : financement fictif de kits d'accompagnement.")
        creer_cagnotte(org1, 'Cagnotte en attente de validation', 200000,
                       Cagnotte.Statut.EN_ATTENTE,
                       "Cagnotte d'exemple pour tester la validation par l'administrateur.")

        self.stdout.write(self.style.SUCCESS('Données de démonstration créées.'))
        self.stdout.write(
            "Comptes de test (local uniquement) : demo_ruban, demo_solidarite, demo_attente\n"
            f"Mot de passe : {MOT_DE_PASSE}"
        )