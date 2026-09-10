# ══════════════════════════════════════════════════════════════════════════════
# ██████╗  ██████╗ ████████╗    ██████╗ ██████╗ ███████╗    ███╗   ███╗███╗   ███╗██╗
# ██╔══██╗██╔═══██╗╚══██╔══╝    ██╔══██╗██╔══██╗██╔════╝    ████╗ ████║████╗ ████║██║
# ██████╔╝██║   ██║   ██║       ██████╔╝██║  ██║█████╗      ██╔████╔██║██╔████╔██║██║
# ██╔══██╗██║   ██║   ██║       ██╔══██╗██║  ██║██╔══╝      ██║╚██╔╝██║██║╚██╔╝██║██║
# ██████╔╝╚██████╔╝   ██║       ██████╔╝██████╔╝███████╗    ██║ ╚═╝ ██║██║ ╚═╝ ██║██║
# ╚═════╝  ╚═════╝    ╚═╝       ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# Bot Discord pour le BDE MMI Mafia - Université d'Artois
# Ce fichier contient TOUTES les fonctionnalités du bot, organisées par feature
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════════════
# IMPORTS & CONFIGURATION GLOBALE
# ══════════════════════════════════════════════════════════════════════════════════════

import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
import random
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import asyncio
import datetime

# Chargement des variables d'environnement (.env)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_BDE = os.getenv("EMAIL_BDE")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ID du serveur Discord
GUILD_ID = 1412342194639212657

# Configuration des intents Discord (permissions du bot)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True  # Requis pour les vocaux temporaires

# Création de l'instance du bot
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Appelé au démarrage du bot pour sync les commandes et enregistrer les vues persistantes"""
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        # Enregistrement des vues persistantes (boutons qui fonctionnent après redémarrage)
        self.add_view(ReglementView())
        self.add_view(VerificationView())
        self.add_view(VerificationCodeView(user_id=0))
        self.add_view(MMIMenu())
        self.add_view(ClassSelectView("mmi1", ROLE_MMI1_CLASSES))
        self.add_view(SpeSelectView("mmi2"))
        self.add_view(SpeSelectView("mmi3"))
        self.add_view(AncienSpeView())
        self.add_view(SummerMMIView())
        self.add_view(TicketMenuView())
        self.add_view(DemandeMenuView())
        self.add_view(MinecraftRoleView())
        self.add_view(SquadraView())
        self.add_view(SquadraAleatoireView())

        # Démarrage de la tâche planifiée qui vérifie chaque jour si la rotation
        # annuelle des promos (début juillet) doit être déclenchée
        if not verifier_rotation_annuelle.is_running():
            verifier_rotation_annuelle.start()

bot = MyBot()

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    print(f"Bot connecté : {bot.user} ✅")











# ══════════════════════════════════════════════════════════════════════════════════════
# ███████╗███████╗████████╗██╗   ██╗██████╗     ██████╗ ███████╗ ██████╗ ██╗     ███████╗
# ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗    ██╔══██╗██╔════╝██╔════╝ ██║     ██╔════╝
# ███████╗█████╗     ██║   ██║   ██║██████╔╝    ██████╔╝█████╗  ██║  ███╗██║     █████╗  
# ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝     ██╔══██╗██╔══╝  ██║   ██║██║     ██╔══╝  
# ███████║███████╗   ██║   ╚██████╔╝██║         ██║  ██║███████╗╚██████╔╝███████╗███████╗
# ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝         ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 1 : ACCEPTATION DU RÈGLEMENT
# 
# Ordre chronologique :
# 1. Admin tape /setup_regle
# 2. Le bot envoie le règlement complet (en 3 messages)
# 3. L'utilisateur clique sur "Accepter" ou "Refuser"
# 4. Si accepté → Rôle Membre attribué
# 5. Si refusé → Kick du serveur
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION ET IDS
# ──────────────────────────────────────────────────────────────────────────────────────

# ID du rôle "Membre" (attribué après acceptation du règlement)
ROLE_MEMBRE_ID = 1460271345102487675

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : COMMANDE ADMIN (/setup_regle) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_regle")
@app_commands.checks.has_permissions(administrator=True)
async def setup_regle(interaction: discord.Interaction):
    """Crée le message d'acceptation du règlement dans le salon actuel"""
    
    # Le règlement est trop long pour un seul message Discord (limite 2000 caractères)
    # Il est donc découpé en 3 parties
    
    partie1 = (
        "**📜 RÈGLEMENT DE LA MAFIA – BDE MMI**\n"
        "\n**PRINCIPES FONDAMENTAUX**\n"
        "\n**ART. 1er**\n"
        "La Mafia est une organisation « familiale », fondée sur la créativité, l'expression et le partage des savoir-faire.\n"
        "Le pouvoir appartient au peuple, qui l'exerce collectivement dans les formes et dans les limites du présent Règlement.\n"
        
        "\n**ART. 2**\n"
        "La Mafia reconnaît et garantit les droits fondamentaux de chaque membre, comme individu et comme membre de formations sociales où s'exerce sa personnalité, et exige l'accomplissement des devoirs de solidarité, de respect, de fraternité et d'entraide auxquels il ne peut être dérogé.\n"
        
        "\n**ART. 3**\n"
        "Tous les membres ont une même dignité sociale et sont égaux devant l'administration de la Mafia, sans distinction de sexe, de race, de langue, de religion, d'opinions, de compétences, de parcours ou de conditions personnelles et sociales.\n"
        "Il appartient à la Mafia d'éliminer les comportements, pratiques ou obstacles qui, en limitant de fait la liberté, l'égalité ou le bien-être des membres, entravent le plein développement de la personne humaine et la participation effective de tous les membres de la Mafia.\n"
        
        "\n**ART. 4**\n"
        "La Mafia reconnaît à tous les membres le droit de créer, de s'exprimer, d'expérimenter, de participer à la vie du serveur et surtout de s'amuser, et crée les conditions nécessaires pour rendre ces droits effectifs.\n"
        "Tout membre a le droit de partager ses créations, selon ses possibilités et selon son choix, par ses créations, ses compétences ou son engagement, au progrès créatif, technique, culturel ou collectif de la communauté.\n"
        "‎"
    )
    
    partie2 = (
        "\n**ART. 5**\n"
        "La Mafia, une et indivisible, reconnaît et favorise les initiatives étudiantes, créatives et collaboratives; réalise, dans les espaces, rôles et projets qui dépendent de la Mafia, la plus large décentralisation de l'organisation; adapte les principes et les méthodes de son règlement aux exigences de l'autonomie des membres, du travail en groupe et de la diversité des parcours au sein de la formation MMI.\n"

        "\n**ART. 6**\n"
        "La Mafia protège par des normes particulières les minorités.\n"

        "\n**ART. 7**\n"
        "La Mafia et les instances pédagogiques de la formation MMI sont, chacune dans leur rôle, indépendantes et respectées.\n"
        "Le fonctionnement du serveur n'a pas vocation à se substituer aux règles officielles de la formation, mais à les compléter par un cadre d'échange, d'entraide et d'expérimentation.\n"
        "Toute collaboration ou adaptation des règles s'effectue dans le respect mutuel et n'exige pas de procédure de révision du présent règlement fondamental.\n"
        
        "\n**ART. 8**\n"
        "Tous les sujets et activités sur le serveur sont libres et ont le droit de s'organiser selon leurs propres statuts tant qu'ils ne nuisent pas aux autres membres ni au bon fonctionnement du serveur.\n"
        "‎"
    )
    
    partie3 = (
        "\n**ART. 9**\n"
        "La Mafia favorise le développement de la créativité et des compétences graphiques et techniques.\n"
        "Elle protège le patrimoine historique et artistique de la MMI contre la montée en puissance de l'armée italienne (AI).\n"

        "\n**ART. 10**\n"
        "L'ordre des Associés de la Mafia se conforme aux règles du droit inter-serveur généralement reconnues.\n"
        "La condition juridique de l'extra-muro est autorisée par la loi, conformément aux normes et au respect de ce traité.\n"
        "L'extra-muro, auquel l'exercice effectif des libertés garanties par la Mafia, a droit d'asile sur le serveur de la Mafia, dans les conditions fixées par la loi.\n"
        "L'expulsion d'un extra-muro pour des délits ou toute infraction au règlement est admise.\n"
        
        "\n**ART. 11**\n"
        "La Mafia répudie le harcèlement, les injures et toute forme de comportement toxique en tant qu'instruments d'atteinte à la liberté, à la dignité et à la créativité des membres, ainsi que comme modes de résolution des conflits; elle consent, dans des conditions de respect et de réciprocité avec d'autres serveurs étudiants ou communautés créatives, aux règles nécessaires à un ordre garantissant un espace sain, inclusif et collaboratif; elle soutient et favorise les initiatives collectives, inter-serveurs ou associatives poursuivant ces objectifs.\n"
        
        "\n**ART. 12**\n"
        "L'emblème de la Mafia est constitué d'une inscription « MAFIA » dorée soulignée par deux feuilles de laurier, le tout accompagné des inscriptions gravées dans le marbre « MMXXVI - MMXXVII » et « MMI », nous rappelant ce qui nous relie toutes et tous.\n"
        
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Clique sur le bouton ci-dessous pour **accepter** le règlement et rejoindre le serveur."
        "‎"
    )
    
    # Envoi des 3 parties
    await interaction.channel.send(partie1)
    await interaction.channel.send(partie2)
    await interaction.channel.send(partie3, view=ReglementView())  # View sur le dernier message
    
    await interaction.response.send_message("✅  Message de règlement envoyé.", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : VIEWS - BOUTONS D'ACCEPTATION/REFUS
# ──────────────────────────────────────────────────────────────────────────────────────

class ReglementView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistant (pas de timeout)

    @discord.ui.button(
        label="J'accepte le règlement",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="accept_reglement"  # ID unique pour la persistance
    )
    async def accept(self, interaction: discord.Interaction, button: Button):
        """Bouton d'acceptation du règlement"""
        role = interaction.guild.get_role(ROLE_MEMBRE_ID)

        # Vérifier si l'utilisateur a déjà le rôle
        if role in interaction.user.roles:
            await interaction.response.send_message(
                "Tu as déjà accepté le règlement 👍",
                ephemeral=True
            )
            return

        # Attribuer le rôle Membre
        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            "✅  Règlement accepté. Bienvenue sur le serveur !",
            ephemeral=True
        )

    @discord.ui.button(
        label="Refuser",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="refuse_reglement"
    )
    async def refuse(self, interaction: discord.Interaction, button: Button):
        """Bouton de refus du règlement → expulsion du serveur"""
        await interaction.response.send_message(
            "Ciao bella 👋 Reviens quand tu seras d'humeur,\n"
            "mais sache que la Mafia n'oublie jamais...",
            ephemeral=True
        )
        await interaction.guild.kick(
            interaction.user,
            reason="Règlement refusé"
        )











# ═══════════════════════════════════════════════════════════════════════
# ███████╗███████╗████████╗██╗   ██╗██████╗     ███████╗████████╗██╗   ██╗
# ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗    ██╔════╝╚══██╔══╝██║   ██║
# ███████╗█████╗     ██║   ██║   ██║██████╔╝    █████╗     ██║   ██║   ██║
# ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝     ██╔══╝     ██║   ██║   ██║
# ███████║███████╗   ██║   ╚██████╔╝██║         ███████╗   ██║   ╚██████╔╝
# ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝         ╚══════╝   ╚═╝    ╚═════╝ 
# ═══════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 2 : VÉRIFICATION ÉTUDIANTE (RÔLE ÉTUDIANT)
#
# Ordre chronologique :
# 1. Admin tape /setup_etu
# 2. Le bot envoie un message avec un bouton "Vérification Étudiante"
# 3. L'utilisateur clique → reçoit un DM
# 4. L'utilisateur envoie son mail @ens.univ-artois.fr en DM
# 5. Le bot envoie un code à 6 chiffres par mail
# 6. L'utilisateur renvoie le code en DM
# 7. Si code correct → Rôle Étudiant attribué
# 8. Le bot demande si l'utilisateur est en MMI
# 9. Si oui → Rôle MMI attribué
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION ET IDS
# ──────────────────────────────────────────────────────────────────────────────────────

# IDs nécessaires pour cette fonctionnalité
CHANNEL_ROLES_ID = 1413971250958696520  # Salon où sera posté le message de vérification
ROLE_ETUDIANT_ID = 1412384279371055185  # Rôle attribué après vérification
ROLE_MMI_ID = 1412385271214899240        # Rôle MMI (si l'étudiant est en MMI)

# Stockage temporaire pour la vérification
codes_temp = {}  # {user_id: code}
mails_temp = {}  # {user_id: email}
waiting_mmi_response = set()  # IDs des users qui attendent de répondre OUI/NON pour MMI

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : COMMANDE ADMIN (/setup_etu) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_etu")
@app_commands.checks.has_permissions(administrator=True)
async def setup_etu(interaction: discord.Interaction):
    """Crée le message de vérification étudiante"""
    channel = bot.get_channel(CHANNEL_ROLES_ID)
    await channel.send(
        "**Vérification Étudiante – Université d'Artois** 🎓\n\n"
        "⚠️  Cette vérification est uniquement destinée aux étudiants de l'IUT de Lens.\n"
        "Si tu n'es pas étudiant à l'IUT de Lens, cette vérification ne te concerne pas.\n\n"
        "Clique sur le bouton ci-dessous pour commencer la vérification.",
        view=VerificationView()
    )
    await interaction.response.send_message("✅  Message de vérification envoyé.", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : VIEWS - BOUTON DE VÉRIFICATION
# ──────────────────────────────────────────────────────────────────────────────────────

class VerificationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Vérification Étudiante",
        style=discord.ButtonStyle.primary,
        emoji="🎓",
        custom_id="verif_etudiant"
    )
    async def start_verif(self, interaction: discord.Interaction, button: Button):
        """Démarre le processus de vérification en DM"""
        try:
            await interaction.user.send(
                "**Vérification Étudiante – Université d'Artois**\n\n"
                "Merci d'envoyer ton **adresse mail universitaire** :\n"
                "prenom_nom@ens.univ-artois.fr"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌  Je n'arrive pas à t'envoyer de message privé.\n\n"
                "Va dans **Paramètres du serveur** (clic droit sur le nom du serveur en haut à gauche) "
                "→ **Paramètres de confidentialité** → active **\"Autoriser les messages privés\"**, "
                "puis reclique sur ce bouton.\n\n"
                "Tu pourras redésactiver cette option une fois la vérification terminée.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Regarde tes messages privés pour continuer la vérification  📩",
            ephemeral=True
        )

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 3 : VIEWS - BOUTONS DE CODE
# ──────────────────────────────────────────────────────────────────────────────────────

class VerificationCodeView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(
        label="🔄 Renvoyer le code",
        style=discord.ButtonStyle.secondary,
        custom_id="verif_resend_code"
    )
    async def resend(self, interaction: discord.Interaction, button: Button):
        """Renvoie le code de vérification par mail"""
        if self.user_id not in mails_temp:
            await interaction.response.send_message(
                "❌  Session expirée, recommence la vérification.",
                ephemeral=True
            )
            return

        success = await envoyer_code(mails_temp[self.user_id], self.user_id)
        await interaction.response.send_message(
            "✅  Nouveau code envoyé." if success else "❌  Impossible d'envoyer le code.",
            ephemeral=True
        )

    @discord.ui.button(
        label="✏️ Modifier le mail",
        style=discord.ButtonStyle.danger,
        custom_id="verif_change_mail"
    )
    async def change(self, interaction: discord.Interaction, button: Button):
        """Permet de modifier l'adresse mail saisie"""
        codes_temp.pop(self.user_id, None)
        mails_temp.pop(self.user_id, None)

        await interaction.user.send(
            "**Modification de ton mail universitaire**\n\n"
            "Merci d'envoyer ton **nouveau mail universitaire** :\n"
            "prenom_nom@ens.univ-artois.fr"
        )
        await interaction.response.send_message(
            "Flux réinitialisé.",
            ephemeral=True
        )

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 4 : FONCTIONS - ENVOI DE MAIL
# ──────────────────────────────────────────────────────────────────────────────────────

def envoyer_mail_sync(msg):
    """Version synchrone de l'envoi SMTP (appelée dans un thread séparé)"""
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_BDE, EMAIL_PASSWORD)
        smtp.send_message(msg)

async def envoyer_code(email_dest, user_id):
    """Génère un code à 6 chiffres et l'envoie par mail sans bloquer le bot"""
    code = str(random.randint(100000, 999999))
    codes_temp[user_id] = code
    mails_temp[user_id] = email_dest

    msg = EmailMessage()
    msg["Subject"] = "Code de vérification Étudiante 🎓"
    msg["From"] = f"BDE MMI Mafia <{EMAIL_BDE}>"
    msg["To"] = email_dest
    msg.set_content(
        f"Bonjour,\n\n"
        f"Voici ton code de vérification pour le serveur Discord du BDE MMI Mafia : {code}\n\n"
        f"Si tu n'as pas demandé ce code, ignore ce mail."
    )

    loop = asyncio.get_running_loop()

    try:
        # Exécution dans un thread pour ne pas bloquer le bot
        await loop.run_in_executor(None, envoyer_mail_sync, msg)
        print("✅ Mail envoyé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur envoi mail : {e}")
        return False

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 5 : NOTE - ÉVÉNEMENT UNIFIÉ
# ──────────────────────────────────────────────────────────────────────────────────────
# La gestion des messages (ETU + TICKETS) est centralisée dans une seule fonction on_message
# placée en bas du fichier pour la clarté de l'organisation.
# Voir : "GESTION UNIFIÉE DES MESSAGES" avant le bot.run(TOKEN)








# ══════════════════════════════════════════════════════════════════════════════════════
# ███████╗███████╗████████╗██╗   ██╗██████╗     ███╗   ███╗███╗   ███╗██╗
# ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗    ████╗ ████║████╗ ████║██║
# ███████╗█████╗     ██║   ██║   ██║██████╔╝    ██╔████╔██║██╔████╔██║██║
# ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝     ██║╚██╔╝██║██║╚██╔╝██║██║
# ███████║███████╗   ██║   ╚██████╔╝██║         ██║ ╚═╝ ██║██║ ╚═╝ ██║██║
# ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝         ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 3 : ATTRIBUTION DES RÔLES MMI (PROMO/CLASSE/SPÉ)
#
# Ordre chronologique :
# 1. Admin tape /setup_mmi
# 2. Le bot envoie un menu de sélection des promos
# 3. L'utilisateur choisit sa promo (MMI1, MMI2, MMI3, Ancien)
# 4. Le bot demande la classe (pour MMI1) ou la spécialité (pour MMI2/MMI3/Ancien)
# 5. L'utilisateur choisit → rôles attribués
#
# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION ET DÉFINITION DES RÔLES MMI
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Cette section définit TOUS les rôles disponibles pour les étudiants MMI.
# Les rôles sont organisés par année et spécialité.
#
# ATTENTION : Ne pas toucher aux noms de classes et spécialités !
# Ils correspondent exactement aux rôles Discord configurés sur le serveur.
#
# STRUCTURE DES RÔLES MMI :
# ─────────────────────────────────────────────────────────────────────────────
# MMI1 : Classes uniquement (A1, A2, B1, B2, C1, C2, D)
# MMI2 : Classes ET spécialités (STRAT1, STRAT2, CREA1, CREA2, DWEB)
#        ⚠️ ROLE_MMI2_CLASSES existe mais n'est PAS utilisé actuellement
#        ⚠️ Les MMI2 choisissent directement leur spécialité (comme MMI3)
#        ⚠️ Les classes MMI2 sont conservées pour usage futur (rentrée suivante)
# MMI3 : Spécialités uniquement (COM1, COM2, MUL1, MUL2, WEB)
# Ancien : Spécialités anciennes (COM, MUL, WEB)
# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════════════

# ID du salon où sera posté le menu MMI
CHANNEL_MMI_ID = 1459358436859838648

# Rôles de promos (niveau d'année)
ROLE_PROMOS = [
    (1459145017128914945, "MMI1"),
    (1459149695409586341, "MMI2"),
    (1459149685993373707, "MMI3"),
    (1459772466129010862, "Ancien")
]

# Rôles MMI1 : Classes uniquement
ROLE_MMI1_CLASSES = [
    (1459149991216939230, "MMI1 A1"),
    (1459150875854635028, "MMI1 A2"),
    (1459150952740159650, "MMI1 B1"),
    (1459151029470761042, "MMI1 B2"),
    (1459151085079105730, "MMI1 C1"),
    (1459151141706268686, "MMI1 C2"),
    (1459151199575216235, "MMI1 D")
]

# Rôles MMI2 : Classes (groupe TD/TP) - UTILISÉES DE SEPTEMBRE À DÉCEMBRE (S3)
ROLE_MMI2_CLASSES = [
    (1459156766204891253, "MMI2 A1"),
    (1459156833506820199, "MMI2 A2"),
    (1459156886774480927, "MMI2 B1"),
    (1459156940893720699, "MMI2 B2"),
    (1459157008522674320, "MMI2 C")
]

# Rôles MMI2 : Spécialités - UTILISÉES DE JANVIER À JUIN (S4, après les SAE de début janvier)
# Nouvelles appellations : Stratégie, Création, Développement Web
ROLE_MMI2_SPES = [
    (1459159992849662125, "MMI2 - STRAT1"),
    (1459242224402305045, "MMI2 - STRAT2"),
    (1459159792646881418, "MMI2 - CREA1"),
    (1459242366555914418, "MMI2 - CREA2"),
    (1459160080657289361, "MMI2 - DWEB")
]

# ──────────────────────────────────────────────────────────────────────────────────────
# PÉRIODES DE L'ANNÉE POUR LES MMI2 (3ᵉ période, en plus des vacances d'été)
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Les MMI2 sont le seul niveau dont le rôle de groupe change en cours d'année scolaire :
# - Septembre à décembre (S3) : rôles de CLASSE (ROLE_MMI2_CLASSES)
# - Janvier à juin (S4)       : rôles de SPÉCIALITÉ (ROLE_MMI2_SPES)
#
# MMI1 garde toujours ses classes, MMI3 garde toujours ses spécialités : rien à faire
# pour eux en cours d'année.
# ──────────────────────────────────────────────────────────────────────────────────────

# Mois où les MMI2 utilisent leur rôle de CLASSE
MOIS_MMI2_CLASSES = [9, 10, 11, 12]

# Mois où les MMI2 utilisent leur rôle de SPÉCIALITÉ
MOIS_MMI2_SPE = [1, 2, 3, 4, 5, 6]

# Nombre de jours, en septembre, considérés comme le "début de la rentrée" : pendant
# cette fenêtre, le message affiché après le choix de la classe précise que l'on peut
# laisser le choix en suspens si on ne connaît pas encore sa classe. Passé ce délai
# (octobre), tout le monde est censé connaître sa classe, donc le message redevient standard.
JOUR_LIMITE_RENTREE = 14

# Rôles MMI3 : Spécialités uniquement
# Nouvelles appellations : Stratégie, Création, Développement Web
ROLE_MMI3_SPES = [
    (1459157221110841427, "MMI3 - STRAT1"),
    (1459157304061726843, "MMI3 - STRAT2"),
    (1459157361615962268, "MMI3 - CREA1"),
    (1459157446621794334, "MMI3 - CREA2"),
    (1459157500262613093, "MMI3 - DWEB")
]

# Rôles Anciens : Spécialités de fin d'études
# Anciennes appellations : COM, CREA, WEB
ROLE_ANCIEN_SPES = [
    (1459772225937998001, "COM"),
    (1459772322029375646, "CREA"),
    (1459770233765101800, "WEB")
]

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : COMMANDE ADMIN (/setup_mmi) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Cette commande unique s'adapte automatiquement à la période de l'année :
# - En juillet et en août (vacances d'été, cf. MOIS_VACANCES_MMI un peu plus bas) :
#   affiche le menu léger "rentrée de septembre" (SummerMMIView), sans demande de
#   classe/groupe précis puisque les étudiants ne le connaissent pas encore.
# - Le reste de l'année (rentrée de septembre à fin d'année scolaire) :
#   affiche le menu complet habituel (MMIMenu), avec classe/spécialité.
#
# Un futur BDE n'a donc besoin de retenir qu'UNE seule commande, /setup_mmi, quelle
# que soit la période à laquelle il l'utilise. Si les mois de vacances changent un
# jour, il suffit de modifier la liste MOIS_VACANCES_MMI.
# ──────────────────────────────────────────────────────────────────────────────────────

# Mois pendant lesquels /setup_mmi bascule automatiquement en mode "vacances d'été"
# 7 = juillet, 8 = août
MOIS_VACANCES_MMI = [7, 8]

@bot.tree.command(name="setup_mmi")
@app_commands.checks.has_permissions(administrator=True)
async def setup_mmi(interaction: discord.Interaction):
    """Crée le menu de sélection MMI dans le salon configuré.
    Le menu affiché dépend automatiquement du mois en cours
    (voir MOIS_VACANCES_MMI)."""
    channel = bot.get_channel(CHANNEL_MMI_ID)
    mois_actuel = datetime.date.today().month

    if mois_actuel in MOIS_VACANCES_MMI:
        # Mode vacances d'été : menu léger pour la rentrée de septembre
        await channel.send(
            "À la rentrée de septembre, dans quelle promotion seras-tu ?",
            view=SummerMMIView()
        )
    else:
        # Mode normal : menu complet promo + classe/spécialité
        role = interaction.guild.get_role(ROLE_MMI_ID)
        await channel.send(
            f"\n**Obtention des rôles {role.mention}**\n"
            "Pour commencer, tu es en quelle année de BUT ?",
            view=MMIMenu()
        )

    await interaction.response.send_message("✅  Menu MMI créé.", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : FONCTIONS UTILITAIRES
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Fonction utilitaire : Suppression de plusieurs rôles en une fois
# ──────────────────────────────────────────────────────────────────────────────────────

async def remove_roles(member, role_ids):
    """Supprime tous les rôles de la liste fournie que le membre possède"""
    roles = [member.guild.get_role(rid) for rid in role_ids]
    roles = [r for r in roles if r and r in member.roles]
    if roles:
        await member.remove_roles(*roles)

#
# Fonctions utilitaires : Détection de la période de l'année (pour les MMI2 et la rentrée)
# ──────────────────────────────────────────────────────────────────────────────────────

def mmi2_utilise_classes():
    """True de septembre à décembre : les MMI2 choisissent/ont leur classe (groupe TD/TP).
    False de janvier à juin : les MMI2 choisissent/ont leur spécialité."""
    return datetime.date.today().month in MOIS_MMI2_CLASSES


def en_debut_septembre():
    """True uniquement pendant les JOUR_LIMITE_RENTREE premiers jours de septembre
    (période de rentrée où la classe n'est pas encore forcément connue)."""
    aujourdhui = datetime.date.today()
    return aujourdhui.month == 9 and aujourdhui.day <= JOUR_LIMITE_RENTREE

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 3 : SÉLECTION DE LA PROMO (Menu principal)
# ──────────────────────────────────────────────────────────────────────────────────────

class PromoSelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Choisis ta promo",
            options=[discord.SelectOption(label=n, value=str(i)) for i, n in ROLE_PROMOS],
            custom_id="promo_select"
        )

    async def callback(self, interaction):
        # ⚠️ NE PAS SUPPRIMER CE MESSAGE
        # Ce select correspond au message de setup MMI (message racine).
        # Il doit rester visible en permanence pour que les users puissent choisir leur promo.
        # La suppression ici casserait tout le système.
        # await interaction.message.delete()  ❌ INTERDIT ICI

        member = interaction.user
        promo = int(self.values[0])

        # Supprimer toutes les promos, classes et spé existantes
        await remove_roles(member, [r[0] for r in ROLE_PROMOS])
        await remove_roles(member,
            [r[0] for r in ROLE_MMI1_CLASSES]
            + [r[0] for r in ROLE_MMI2_CLASSES]
            + [r[0] for r in ROLE_MMI2_SPES]
            + [r[0] for r in ROLE_MMI3_SPES]
            + [r[0] for r in ROLE_ANCIEN_SPES]
        )

        # Attribuer le rôle de promo choisi
        await member.add_roles(interaction.guild.get_role(promo))

        # Rediriger vers le menu approprié selon la promo
        if promo == ROLE_PROMOS[3][0]:  # Ancien
            await interaction.response.send_message(
                "✅  Ah, un ancien !? C'était quoi ta **spécialité de 3ème année** ?",
                view=AncienSpeView(),
                ephemeral=True
            )
        elif promo == ROLE_PROMOS[0][0]:  # MMI1
            # MMI1 garde toujours des classes, quelle que soit la période de l'année.
            if en_debut_septembre():
                message = (
                    "✅  C'est la rentrée ! Sélectionne ta nouvelle **classe** "
                    "(si tu ne la connais pas encore, laisse en suspens et reviens plus tard)."
                )
            else:
                message = "✅  Promo sélectionnée. Maintenant choisis ta **classe**."

            await interaction.response.send_message(
                message,
                view=ClassSelectView("mmi1", ROLE_MMI1_CLASSES),
                ephemeral=True
            )
        elif promo == ROLE_PROMOS[1][0]:  # MMI2
            # MMI2 change de groupe en cours d'année : groupe TD/TP de septembre à
            # décembre, puis groupe de spécialité (STRAT/CREA/DWEB) de janvier à juin.
            # Les deux sont appelés "classe" côté étudiant, donc le message ne change pas.
            if mmi2_utilise_classes():
                vue_mmi2 = ClassSelectView("mmi2", ROLE_MMI2_CLASSES)
            else:
                vue_mmi2 = SpeSelectView("mmi2")

            if en_debut_septembre():
                message = (
                    "✅  C'est la rentrée ! Sélectionne ta nouvelle **classe** "
                    "(si tu ne la connais pas encore, laisse en suspens et reviens plus tard)."
                )
            else:
                message = "✅  Promo sélectionnée. Maintenant choisis ta **classe**."

            await interaction.response.send_message(message, view=vue_mmi2, ephemeral=True)
        elif promo == ROLE_PROMOS[2][0]:  # MMI3
            if en_debut_septembre():
                message = (
                    "✅  C'est la rentrée ! Sélectionne ta nouvelle **classe** "
                    "(si tu ne la connais pas encore, laisse en suspens et reviens plus tard)."
                )
            else:
                message = "✅  Promo sélectionnée. Maintenant choisis ta **classe**."

            await interaction.response.send_message(
                message,
                view=SpeSelectView("mmi3"),
                ephemeral=True
            )


class MMIMenu(View):
    """View principale contenant le sélecteur de promo"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PromoSelect())

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 4 : SÉLECTION DE LA CLASSE (MMI1 uniquement)
# ──────────────────────────────────────────────────────────────────────────────────────

class ClassSelect(Select):
    def __init__(self, promo, roles):
        self.roles = roles
        super().__init__(
            placeholder="Choisis ta classe",
            options=[discord.SelectOption(label=n, value=str(i)) for i, n in roles],
            custom_id=f"class_{promo}"
        )
        self.promo = promo

    async def callback(self, interaction):
        # Ce message peut être supprimé car c'est un message éphémère individuel
        try:
            await interaction.message.delete()
        except:
            pass

        member = interaction.user

        await remove_roles(member, [r[0] for r in self.roles])
        await member.add_roles(interaction.guild.get_role(int(self.values[0])))

        # Rappel spécifique aux MMI2 : en janvier, la classe laisse place à la spécialité
        if self.promo == "mmi2" and mmi2_utilise_classes():
            message = (
                "✅  Classe sélectionnée. En janvier, lors du passage aux groupes de "
                "spécialité, reviens sur ce menu pour choisir ta nouvelle classe."
            )
        else:
            message = "✅  Classe sélectionnée."

        await interaction.response.send_message(message, ephemeral=True)


class ClassSelectView(View):
    """View pour la sélection de classe (MMI1 ou MMI2)"""
    def __init__(self, promo, roles):
        super().__init__(timeout=None)
        self.add_item(ClassSelect(promo, roles))

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 5 : SÉLECTION DE LA SPÉCIALITÉ (MMI2, MMI3)
# ──────────────────────────────────────────────────────────────────────────────────────

class SpeSelect(Select):
    def __init__(self, promo):
        if promo == "mmi2":
            roles = ROLE_MMI2_SPES
            placeholder = "Choisis ta classe"
        elif promo == "mmi3":
            roles = ROLE_MMI3_SPES
            placeholder = "Choisis ta classe"
        
        super().__init__(
            placeholder=placeholder,
            options=[discord.SelectOption(label=n, value=str(i)) for i, n in roles],
            custom_id=f"spe_{promo}"
        )
        self.promo = promo

    async def callback(self, interaction):
        # Ce message peut être supprimé car c'est un message éphémère individuel
        try:
            await interaction.message.delete()
        except:
            pass

        member = interaction.user

        # Supprimer anciennes spés
        if self.promo == "mmi2":
            await remove_roles(member, [r[0] for r in ROLE_MMI2_SPES])
        elif self.promo == "mmi3":
            await remove_roles(member, [r[0] for r in ROLE_MMI3_SPES])

        await member.add_roles(interaction.guild.get_role(int(self.values[0])))

        await interaction.response.send_message(
            "✅  Classe sélectionnée.",
            ephemeral=True
        )


class SpeSelectView(View):
    """View pour la sélection de spécialité (MMI2, MMI3)"""
    def __init__(self, promo):
        super().__init__(timeout=None)
        self.add_item(SpeSelect(promo))

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 6 : SÉLECTION DE LA SPÉCIALITÉ (ANCIENS)
# ──────────────────────────────────────────────────────────────────────────────────────

class AncienSpeSelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Indique ta spécialité de fin d'études",
            options=[discord.SelectOption(label=n, value=str(i)) for i, n in ROLE_ANCIEN_SPES],
            custom_id="ancien_spe"
        )

    async def callback(self, interaction):
        try:
            await interaction.message.delete()
        except:
            pass

        member = interaction.user

        await remove_roles(member, [r[0] for r in ROLE_ANCIEN_SPES])
        await member.add_roles(interaction.guild.get_role(int(self.values[0])))

        await interaction.response.send_message(
            "✅  Spécialité sélectionnée.",
            ephemeral=True
        )


class AncienSpeView(View):
    """View pour la sélection de spécialité (Anciens)"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(AncienSpeSelect())

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 7 : MODE VACANCES D'ÉTÉ (SÉLECTION POUR LA RENTRÉE DE SEPTEMBRE)
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Ces vues sont utilisées automatiquement par /setup_mmi lorsque la commande est
# exécutée pendant les mois listés dans MOIS_VACANCES_MMI (voir Section 1 plus haut).
# Il n'y a plus de commande séparée : tout passe par /setup_mmi.
#
# Pendant l'été, les étudiants savent déjà dans quelle promotion ils seront à la
# rentrée de septembre, mais ne connaissent pas encore leur futur groupe TD/TP.
#
# Cas par promotion :
# - MMI1  : rôle de promo uniquement
# - MMI2  : rôle de promo uniquement
# - MMI3  : rôle de promo uniquement (pas de spécialité demandée à ce stade)
# - Ancien : rôle de promo, puis choix de la spécialité de fin d'études
#            (réutilise AncienSpeView, déjà existant)
# ──────────────────────────────────────────────────────────────────────────────────────

# Rôles de promos utilisés pour la sélection "rentrée de septembre"
ROLE_PROMOS_VAC = [
    (1459145017128914945, "MMI1 (redoublant ou nouveau)"),
    (1459149695409586341, "MMI2"),
    (1459149685993373707, "MMI3"),
    (1459772466129010862, "Ancien")
]

class SummerPromoSelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Choisis ta promotion pour la rentrée",
            options=[discord.SelectOption(label=n, value=str(i)) for i, n in ROLE_PROMOS_VAC],
            custom_id="promo_vac_select"
        )

    async def callback(self, interaction):
        member = interaction.user
        promo = int(self.values[0])

        # Supprimer toutes les promos, classes et spés existantes
        await remove_roles(member, [r[0] for r in ROLE_PROMOS])
        await remove_roles(member,
            [r[0] for r in ROLE_MMI1_CLASSES]
            + [r[0] for r in ROLE_MMI2_CLASSES]
            + [r[0] for r in ROLE_MMI2_SPES]
            + [r[0] for r in ROLE_MMI3_SPES]
            + [r[0] for r in ROLE_ANCIEN_SPES]
        )

        # Attribuer le rôle de promo choisi pour la rentrée
        await member.add_roles(interaction.guild.get_role(promo))

        if promo == ROLE_PROMOS_VAC[3][0]:  # Ancien
            await interaction.response.send_message(
                "Promotion pour la rentrée sélectionnée. Quelle était ta spécialité ?",
                view=AncienSpeView(),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Promotion pour la rentrée sélectionnée.",
                ephemeral=True
            )


class SummerMMIView(View):
    """View principale pour la sélection de promo pendant les vacances"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SummerPromoSelect())












# ══════════════════════════════════════════════════════════════════════════════════════
# ███████╗███████╗████████╗██╗   ██╗██████╗     ████████╗██╗ ██████╗██╗  ██╗███████╗████████╗███████╗
# ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗    ╚══██╔══╝██║██╔════╝██║ ██╔╝██╔════╝╚══██╔══╝██╔════╝
# ███████╗█████╗     ██║   ██║   ██║██████╔╝       ██║   ██║██║     █████╔╝ █████╗     ██║   ███████╗
# ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝        ██║   ██║██║     ██╔═██╗ ██╔══╝     ██║   ╚════██║
# ███████║███████╗   ██║   ╚██████╔╝██║            ██║   ██║╚██████╗██║  ██╗███████╗   ██║   ███████║
# ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝            ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 4 : SYSTÈME DE TICKETS (PLAINTES + DEMANDES)
#
# Ordre chronologique :
# 1. Admin tape /setup_tickets (pour plaintes) ou /setup_demandes (pour suggestions)
# 2. Le bot envoie un message avec un bouton dans le salon approprié
# 3. L'utilisateur clique sur le bouton
# 4. Un formulaire Modal s'ouvre
# 5. L'utilisateur remplit le formulaire et valide
# 6. Le ticket est envoyé en DM à l'admin configuré (avec embed + bouton de réponse)
# 7. L'admin peut cliquer sur "Répondre au ticket" pour envoyer une réponse à l'utilisateur
# 
# FONCTIONNALITÉS SPÉCIALES :
# - Les messages normaux dans ces salons sont automatiquement supprimés
# - Seuls les admins peuvent écrire normalement dans ces salons
# - Chaque ticket a un ID unique (#1, #2, #3...)
# - L'utilisateur reçoit une confirmation avec le numéro de son ticket
#
# ══════════════════════════════════════════════════════════════════════════════════════

# Configuration des salons
CHANNEL_TICKETS_ID = 1464012851235651604   # Salon pour les plaintes
CHANNEL_DEMANDES_ID = 1415236565755756624  # Salon pour les suggestions

# ID de l'admin qui reçoit les tickets en DM
ADMIN_ID = 692758779808448593

# Compteur de tickets (global, partagé entre plaintes et demandes)
ticket_counter = 0

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : COMMANDES ADMIN (/setup_tickets et /setup_demandes) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_tickets")
@app_commands.checks.has_permissions(administrator=True)
async def setup_tickets(interaction: discord.Interaction):
    """Crée le menu des plaintes dans le salon configuré"""
    channel = bot.get_channel(CHANNEL_TICKETS_ID)
    await channel.send(
        "**🚨 SIGNALEMENT DE PLAINTES – BDE MMI MAFIA**\n\n"
        "Tu as observé un **comportement inapproprié** sur le serveur ?\n"
        "Utilise le bouton ci-dessous pour signaler une plainte de manière confidentielle.\n\n"
        "⚠️  Types de plaintes : harcèlement, spam, comportement toxique, non-respect du règlement, etc.\n\n"
        "Ton signalement sera traité avec sérieux et confidentialité.",
        view=TicketMenuView()
    )
    await interaction.response.send_message("✅  Menu des plaintes créé.", ephemeral=True)
                                            
@bot.tree.command(name="setup_demandes")
@app_commands.checks.has_permissions(administrator=True)
async def setup_demandes(interaction: discord.Interaction):
    """Crée le menu des demandes dans le salon configuré"""
    channel = bot.get_channel(CHANNEL_DEMANDES_ID)
    await channel.send(
        "**💡 DEMANDES D'AJOUT & SUGGESTIONS – BDE MMI MAFIA**\n\n"
        "Tu as une **idée** pour améliorer le serveur ?\n"
        "Utilise le bouton ci-dessous pour soumettre ta suggestion !\n\n"
        "💡  Types de demandes : nouveau salon, événement, fonctionnalité, activité, partenariat, etc.\n\n"
        "Toutes les suggestions sont étudiées par l'équipe du BDE.",
        view=DemandeMenuView()
    )
    await interaction.response.send_message("✅  Menu des demandes créé.", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : NOTE - ÉVÉNEMENT UNIFIÉ
# ──────────────────────────────────────────────────────────────────────────────────────
# La gestion automatique des messages (modération TICKETS) est centralisée dans la
# fonction on_message unique placée en bas du fichier.
# Voir : "GESTION UNIFIÉE DES MESSAGES" avant le bot.run(TOKEN)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : VIEWS AVEC LES BOUTONS DE DÉCLENCHEMENT
# ──────────────────────────────────────────────────────────────────────────────────────

class TicketMenuView(View):
    """View avec le bouton pour ouvrir une plainte"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ouvrir une plainte",
        style=discord.ButtonStyle.danger,
        emoji="⚠️",
        custom_id="ticket_plainte"
    )
    async def plainte_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PlainteModal())


class DemandeMenuView(View):
    """View avec le bouton pour faire une demande"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Faire une demande",
        style=discord.ButtonStyle.primary,
        emoji="💡",
        custom_id="ticket_demande"
    )
    async def demande_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DemandeModal())

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 3 : SYSTÈME DE RÉPONSE AUX TICKETS
# ──────────────────────────────────────────────────────────────────────────────────────

class ReponseTicketView(View):
    """View avec le bouton de réponse (envoyé à l'admin avec le ticket)"""
    def __init__(self, user_id, ticket_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.ticket_id = ticket_id

    @discord.ui.button(
        label="Répondre au ticket",
        style=discord.ButtonStyle.success,
        emoji="📝"
    )
    async def repondre(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ReponseModal(self.user_id, self.ticket_id))


class ReponseModal(Modal, title="Répondre au ticket"):
    """Modal de réponse à un ticket"""
    reponse = TextInput(
        label="Ta réponse",
        placeholder="Écris ta réponse ici...",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )

    def __init__(self, user_id, ticket_id):
        super().__init__()
        self.user_id = user_id
        self.ticket_id = ticket_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user = await bot.fetch_user(self.user_id)
            
            # Créer l'embed de réponse
            embed = discord.Embed(
                title=f"📬 RÉPONSE À TON TICKET #{self.ticket_id}",
                description=self.reponse.value,
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="BDE MMI Mafia - Administration")
            
            # Envoyer la réponse à l'utilisateur
            await user.send(embed=embed)
            
            await interaction.response.send_message(
                f"✅  Réponse envoyée à {user.name} !",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌  Impossible d'envoyer la réponse : {e}",
                ephemeral=True
            )

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 4 : FORMULAIRE DE PLAINTE
# ──────────────────────────────────────────────────────────────────────────────────────

class PlainteModal(Modal, title="📢 Signaler une plainte"):
    """Formulaire de signalement d'une plainte"""
    sujet = TextInput(
        label="Sujet de la plainte",
        placeholder="Ex: Comportement inapproprié, spam, harcèlement...",
        max_length=100,
        required=True
    )
    
    description = TextInput(
        label="Description détaillée",
        placeholder="Décris la situation en détail (qui, quoi, où, quand)...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )
    
    personne_concernee = TextInput(
        label="Personne(s) concernée(s) (optionnel)",
        placeholder="Nom d'utilisateur Discord ou @mention",
        max_length=200,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1
        ticket_id = ticket_counter
        
        # Créer l'embed du ticket
        embed = discord.Embed(
            title=f"🚨 NOUVELLE PLAINTE #{ticket_id}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="📝 Sujet", value=self.sujet.value, inline=False)
        embed.add_field(name="📄 Description", value=self.description.value, inline=False)
        
        if self.personne_concernee.value:
            embed.add_field(name="👤 Personne(s) concernée(s)", value=self.personne_concernee.value, inline=False)
        
        embed.add_field(name="👤 Auteur", value=f"{interaction.user.mention} ({interaction.user.name})", inline=True)
        embed.add_field(name="🆔 ID Auteur", value=f"`{interaction.user.id}`", inline=True)
        embed.set_footer(text=f"Ticket #{ticket_id}", icon_url=interaction.user.display_avatar.url)

        # Envoyer le ticket à l'admin
        try:
            admin = await bot.fetch_user(ADMIN_ID)
            await admin.send(embed=embed, view=ReponseTicketView(interaction.user.id, ticket_id))
            print(f"✅ Plainte #{ticket_id} envoyée à l'admin")
        except Exception as e:
            print(f"❌ Impossible d'envoyer la plainte à l'admin : {e}")

        # Confirmer à l'utilisateur
        await interaction.response.send_message(
            f"✅  Ta plainte **#{ticket_id}** a été envoyée aux administrateurs.\n"
            "Elle sera traitée dans les plus brefs délais. Merci pour ton signalement.",
            ephemeral=True
        )

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 5 : FORMULAIRE DE DEMANDE/SUGGESTION
# ──────────────────────────────────────────────────────────────────────────────────────

class DemandeModal(Modal, title="💡 Demande d'ajout / Suggestion"):
    """Formulaire de demande d'ajout ou suggestion"""
    titre = TextInput(
        label="Titre de ta demande",
        placeholder="Ex: Nouveau salon, événement, fonctionnalité...",
        max_length=100,
        required=True
    )
    
    description = TextInput(
        label="Description de ta demande",
        placeholder="Décris ce que tu aimerais voir ajouté et comment ça fonctionnerait...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )
    
    justification = TextInput(
        label="Pourquoi c'est utile ? (optionnel)",
        placeholder="Explique en quoi c'est bénéfique pour la communauté...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1
        ticket_id = ticket_counter
        
        # Créer l'embed du ticket
        embed = discord.Embed(
            title=f"💡 NOUVELLE DEMANDE #{ticket_id}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="📝 Titre", value=self.titre.value, inline=False)
        embed.add_field(name="📄 Description", value=self.description.value, inline=False)
        
        if self.justification.value:
            embed.add_field(name="✨ Justification", value=self.justification.value, inline=False)
        
        embed.add_field(name="👤 Auteur", value=f"{interaction.user.mention} ({interaction.user.name})", inline=True)
        embed.add_field(name="🆔 ID Auteur", value=f"`{interaction.user.id}`", inline=True)
        embed.set_footer(text=f"Ticket #{ticket_id}", icon_url=interaction.user.display_avatar.url)

        # Envoyer le ticket à l'admin
        try:
            admin = await bot.fetch_user(ADMIN_ID)
            await admin.send(embed=embed, view=ReponseTicketView(interaction.user.id, ticket_id))
            print(f"✅ Demande #{ticket_id} envoyée à l'admin")
        except Exception as e:
            print(f"❌ Impossible d'envoyer la demande à l'admin : {e}")

        # Confirmer à l'utilisateur
        await interaction.response.send_message(
            f"✅  Ta demande **#{ticket_id}** a été envoyée aux administrateurs.\n"
            "Merci pour ta suggestion ! On va étudier ça 👍",
            ephemeral=True
        )











# ══════════════════════════════════════════════════════════════════════════════════════
# ██╗   ██╗ ██████╗  ██████╗ █████╗ ██╗   ██╗██╗  ██╗    ████████╗███████╗███╗   ███╗██████╗ 
# ██║   ██║██╔═══██╗██╔════╝██╔══██╗██║   ██║╚██╗██╔╝    ╚══██╔══╝██╔════╝████╗ ████║██╔══██╗
# ██║   ██║██║   ██║██║     ███████║██║   ██║ ╚███╔╝        ██║   █████╗  ██╔████╔██║██████╔╝
# ╚██╗ ██╔╝██║   ██║██║     ██╔══██║██║   ██║ ██╔██╗        ██║   ██╔══╝  ██║╚██╔╝██║██╔═══╝ 
#  ╚████╔╝ ╚██████╔╝╚██████╗██║  ██║╚██████╔╝██╔╝ ██╗       ██║   ███████╗██║ ╚═╝ ██║██║     
#   ╚═══╝   ╚═════╝  ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝       ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝     
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 5 : SALONS VOCAUX TEMPORAIRES
#
# PRINCIPE DE FONCTIONNEMENT :
# 1. Un utilisateur rejoint un salon "HUB" (point d'entrée)
# 2. Le bot crée automatiquement un nouveau salon vocal dans la bonne catégorie
# 3. L'utilisateur est déplacé dans ce nouveau salon
# 4. Le créateur du salon obtient des permissions de gestion (renommer, kick)
# 5. Quand le salon devient vide, il est automatiquement supprimé
#
# DEUX TYPES DE VOCAUX TEMPORAIRES :
# ─────────────────────────────────────────────────────────────────────────────────────
# TYPE 1 : VOCAUX RÉVISION (thème études/travail)
#   - Hub d'entrée : HUB_VOCAL_MMI
#   - Catégorie de destination : CATEGORIE_MMI
#   - Noms : Squadra Passione, Squadra Innovazione, Squadra della Visione, etc.
#
# TYPE 2 : VOCAUX GAMING (thème jeux/détente)
#   - Hub d'entrée : HUB_VOCAL_GENERAL
#   - Catégorie de destination : CATEGORIE_GENERAL
#   - Noms : Squadra del Divertimento, Squadra d'Onore, Squadra Furia, etc.
# ─────────────────────────────────────────────────────────────────────────────────────
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION ET IDS
# ──────────────────────────────────────────────────────────────────────────────────────

# TYPE 1 : Vocaux Révision (thème MMI/Études)
HUB_VOCAL_MMI = 1463811448093540467     # Salon hub "Créer un vocal révision"
CATEGORIE_MMI = 1412395265662390354     # Catégorie où seront créés les vocaux

# TYPE 2 : Vocaux Gaming (thème Général/Jeux)
HUB_VOCAL_GENERAL = 1463811324986261600  # Salon hub "Créer un vocal gaming"
CATEGORIE_GENERAL = 1412345763484139532  # Catégorie où seront créés les vocaux

# Noms pour les vocaux de type RÉVISION (thème italien/motivation)
NOMS_VOCAUX_MMI = [
    "📚 Squadra Passione",           # L'équipe passion
    "📚 Squadra Innovazione",        # L'équipe innovation
    "📚 Squadra della Visione",      # L'équipe de la vision
    "📚 Squadra Dedizione",          # L'équipe dévouement
    "📚 Squadra per l'Eccellenza",   # L'équipe pour l'excellence
    "📚 Squadra Precisione",         # L'équipe précision
    "📚 Squadra Ingegno",            # L'équipe ingéniosité
    "📚 Squadra Maestria",           # L'équipe maîtrise
    "📚 Squadra del Progresso",      # L'équipe du progrès
    "📚 Squadra Sapere"              # L'équipe savoir
]

# Noms pour les vocaux de type GAMING (thème italien/combat)
NOMS_VOCAUX_GENERAL = [
    "🎮 Squadra del Divertimento",   # L'équipe du divertissement
    "🎮 Squadra Determinazione",     # L'équipe détermination
    "🎮 Squadra d'Onore",            # L'équipe d'honneur
    "🎮 Squadra Coraggio",           # L'équipe courage
    "🎮 Squadra di Strategia",       # L'équipe de stratégie
    "🎮 Squadra Forza",              # L'équipe force
    "🎮 Squadra per la Fratellanza", # L'équipe pour la fraternité
    "🎮 Squadra Furia",              # L'équipe furie
    "🎮 Squadra Gloria",             # L'équipe gloire
    "🎮 Squadra per la Conquista"    # L'équipe pour la conquête
]

# Dictionnaire de tracking des vocaux temporaires
temp_voice_channels = {}  # {channel_id: creator_id}

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : ÉVÉNEMENT - GESTION DES ÉTATS VOCAUX
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.event
async def on_voice_state_update(member, before, after):
    """
    Événement déclenché quand un utilisateur change d'état vocal
    (rejoint/quitte un salon, mute/unmute, etc.)
    """
    
    # Ignorer les bots
    if member.bot:
        return
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PARTIE 1 : CRÉATION D'UN VOCAL TEMPORAIRE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Vérifier si l'utilisateur a rejoint un salon hub
    if after.channel and after.channel.id in [HUB_VOCAL_MMI, HUB_VOCAL_GENERAL]:
        
        # Déterminer le type de vocal à créer (Révision ou Gaming)
        if after.channel.id == HUB_VOCAL_MMI:
            category_id = CATEGORIE_MMI
            noms = NOMS_VOCAUX_MMI
        else:
            category_id = CATEGORIE_GENERAL
            noms = NOMS_VOCAUX_GENERAL
        
        guild = member.guild
        category = guild.get_channel(category_id)
        
        # Choisir un nom aléatoire dans la liste appropriée
        nom_vocal = random.choice(noms)
        
        # Créer le nouveau salon vocal
        new_channel = await guild.create_voice_channel(
            name=nom_vocal,
            category=category,
            reason=f"Vocal temporaire créé par {member.name}"
        )
        
        # Donner les permissions de gestion au créateur du salon
        await new_channel.set_permissions(
            member,
            manage_channels=True,   # Peut renommer le salon
            move_members=True,      # Peut expulser des membres
            manage_permissions=False # Ne peut pas modifier les permissions
        )
        
        # Enregistrer le salon dans le dictionnaire de tracking
        temp_voice_channels[new_channel.id] = member.id
        
        # Déplacer le membre dans le nouveau salon
        await member.move_to(new_channel)
        
        print(f"✅ Vocal temporaire créé : {nom_vocal} par {member.name}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PARTIE 2 : SUPPRESSION AUTOMATIQUE D'UN VOCAL VIDE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Vérifier si l'utilisateur a quitté un salon temporaire
    if before.channel and before.channel.id in temp_voice_channels:
        
        # Vérifier si le salon est maintenant vide
        if len(before.channel.members) == 0:
            channel_id = before.channel.id
            channel = before.channel
            
            # Supprimer le salon
            await channel.delete(reason="Salon vocal temporaire vide")
            
            # Retirer du dictionnaire de tracking
            temp_voice_channels.pop(channel_id, None)
            
            print(f"🗑️ Vocal temporaire supprimé : {channel.name}")




















# ══════════════════════════════════════════════════════════════════════════════════════
# ███████╗███████╗████████╗██╗   ██╗██████╗     ██████╗ ███████╗███████╗███████╗ █████╗ ██╗   ██╗██╗  ██╗
# ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗    ██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██║   ██║╚██╗██╔╝
# ███████╗█████╗     ██║   ██║   ██║██████╔╝    ██████╔╝█████╗  ███████╗█████╗  ███████║██║   ██║ ╚███╔╝ 
# ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝     ██╔══██╗██╔══╝  ╚════██║██╔══╝  ██╔══██║██║   ██║ ██╔██╗ 
# ███████║███████╗   ██║   ╚██████╔╝██║         ██║  ██║███████╗███████║███████╗██║  ██║╚██████╔╝██╔╝ ██╗
# ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝         ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 6 : RÉSEAUX SOCIAUX (LINKTREE)
#
# Ordre chronologique :
# 1. Admin tape /setup_reseaux
# 2. Le bot envoie un embed avec un bouton de lien vers le Linktree
# 3. L'utilisateur clique → redirigé directement vers le Linktree (aucune interaction avec le bot)
#
# Note : le bouton est un bouton de lien Discord (style "link"), il n'a pas de custom_id
# et ne déclenche aucune interaction côté bot. Il n'a donc pas besoin d'être enregistré
# comme vue persistante dans setup_hook.
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────────────

LINKTREE_URL = "https://linktree-mmimafia.vercel.app/?utm_source=ig&utm_medium=social&utm_content=link_in_bio&fbclid=PAb21jcATA7CNleHRuA2FlbQIxMQBzcnRjBmFwcF9pZA81NjcwNjczNDMzNTI0MjcAAaegeBY8a0wK4Us2fDB2jBhOOvUBzB_RuaPeD0IIb-fG1foloWqjJm2b9Foq4Q_aem_KmhMDaAs0pMCoXYhtyDuvg"

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : COMMANDE ADMIN (/setup_reseaux) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_reseaux")
@app_commands.checks.has_permissions(administrator=True)
async def setup_reseaux(interaction: discord.Interaction):
    """Crée le message de redirection vers tous les réseaux sociaux du BDE"""
    embed = discord.Embed(
        title="Tous nos réseaux",
        description=(
            "Retrouve la Mafia MMI là où on est présents : Discord, Instagram, et le reste de nos réseaux.\n\n"
            "Un seul lien, mais tout au même endroit."
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="BDE MMI Mafia")

    await interaction.channel.send(embed=embed, view=ReseauxView())
    await interaction.response.send_message("✅  Message des réseaux envoyé.", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : VIEW - BOUTON DE LIEN VERS LE LINKTREE
# ──────────────────────────────────────────────────────────────────────────────────────

class ReseauxView(View):
    """View avec le bouton de lien vers le Linktree"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(
            label="Tous nos réseaux",
            style=discord.ButtonStyle.link,
            url=LINKTREE_URL,
            emoji="🔗"
        ))

















# ══════════════════════════════════════════════════════════════════════════════════════
# ███████╗███████╗████████╗██╗   ██╗██████╗     ███╗   ███╗ ██████╗
# ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗    ████╗ ████║██╔════╝
# ███████╗█████╗     ██║   ██║   ██║██████╔╝    ██╔████╔██║██║     
# ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝     ██║╚██╔╝██║██║     
# ███████║███████╗   ██║   ╚██████╔╝██║         ██║ ╚═╝ ██║╚██████╗
# ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝         ╚═╝     ╚═╝ ╚═════╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 7 : RÔLE MINECRAFT (ACCÈS À LA CATÉGORIE MINECRAFT)
#
# Ordre chronologique :
# 1. Admin tape /setup_mc
# 2. Le bot envoie un message dans le salon des rôles (même salon que /setup_etu)
# 3. L'utilisateur clique sur "Obtenir le rôle" → rôle Minecraft attribué
# 4. L'utilisateur peut cliquer sur "Retirer le rôle" à tout moment pour le retirer lui-même
#
# Le rôle Minecraft donne accès à la catégorie Minecraft du serveur. Le message reste
# volontairement général (pas de mention d'un serveur à venir), pour rester valable
# aussi bien avant qu'après la sortie du serveur Minecraft.
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION ET IDS
# ──────────────────────────────────────────────────────────────────────────────────────

# Rôle donnant accès à la catégorie Minecraft
ROLE_MINECRAFT_ID = 1439864603763802153

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : COMMANDE ADMIN (/setup_mc) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_mc")
@app_commands.checks.has_permissions(administrator=True)
async def setup_mc(interaction: discord.Interaction):
    """Crée le message d'obtention du rôle Minecraft dans le salon des rôles"""
    channel = bot.get_channel(CHANNEL_ROLES_ID)
    await channel.send(
        "**Catégorie Minecraft – BDE MMI Mafia**\n\n"
        "Ce rôle donne accès à la catégorie Minecraft du serveur : discussions, "
        "annonces, sondages et salons dédiés à tout ce qui touche au Minecraft de la Mafia MMI.\n\n"
        "Clique sur le bouton ci-dessous pour obtenir le rôle. Tu peux le retirer "
        "toi-même à tout moment si ça ne t'intéresse plus.",
        view=MinecraftRoleView()
    )
    await interaction.response.send_message("✅  Message Minecraft envoyé.", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : VIEW - BOUTONS D'ATTRIBUTION / RETRAIT DU RÔLE
# ──────────────────────────────────────────────────────────────────────────────────────

class MinecraftRoleView(View):
    """View avec les boutons d'obtention et de retrait du rôle Minecraft"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Obtenir le rôle Minecraft",
        style=discord.ButtonStyle.success,
        emoji="🎮",
        custom_id="mc_role_add"
    )
    async def add_role(self, interaction: discord.Interaction, button: Button):
        """Attribue le rôle Minecraft"""
        role = interaction.guild.get_role(ROLE_MINECRAFT_ID)

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "Tu as déjà le rôle Minecraft 👍",
                ephemeral=True
            )
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            "✅  Rôle Minecraft attribué. Tu as maintenant accès à la catégorie.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Retirer le rôle Minecraft",
        style=discord.ButtonStyle.danger,
        emoji="🚫",
        custom_id="mc_role_remove"
    )
    async def remove_role(self, interaction: discord.Interaction, button: Button):
        """Retire le rôle Minecraft"""
        role = interaction.guild.get_role(ROLE_MINECRAFT_ID)

        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "Tu n'as pas le rôle Minecraft.",
                ephemeral=True
            )
            return

        await interaction.user.remove_roles(role)
        await interaction.response.send_message(
            "✅  Rôle Minecraft retiré.",
            ephemeral=True
        )

















# ══════════════════════════════════════════════════════════════════════════════════════
# ██████╗  ██████╗ ████████╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
# ██╔══██╗██╔═══██╗╚══██╔══╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
# ██████╔╝██║   ██║   ██║   ███████║   ██║   ██║██║   ██║██╔██╗ ██║
# ██╔══██╗██║   ██║   ██║   ██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
# ██║  ██║╚██████╔╝   ██║   ██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
# ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 8 : ROTATION ANNUELLE AUTOMATIQUE DES PROMOS (DÉBUT JUILLET)
#
# Principe de fonctionnement :
# 1. Une tâche planifiée tourne en arrière-plan et se réveille une fois par jour
# 2. Si on est dans les premiers jours de juillet ET que la rotation n'a pas encore
#    été faite cette année-là, elle se déclenche automatiquement
# 3. Pour chaque membre du serveur :
#    - Tous les rôles de classe/spécialité (MMI1, MMI2, MMI3) sont retirés
#    - MMI1 → MMI2, MMI2 → MMI3, MMI3 → Ancien (les Anciens ne bougent plus, ils
#      gardent leur spécialité de fin d'études)
# 4. Tous les salons de classe (promo/TD/TP) listés dans CHANNELS_A_VIDER sont vidés
# 5. L'année de la dernière exécution est mémorisée en mémoire (aucun fichier, aucune
#    variable d'environnement) pour éviter de rejouer tout ça deux fois la même année.
#    Cette mémoire est remise à zéro à chaque redémarrage du bot : si le bot redémarre
#    PILE dans les JOUR_LIMITE_ROTATION premiers jours de juillet après avoir déjà
#    tourné cette année-là, la rotation pourrait se redéclencher. Risque volontairement
#    accepté pour ne pas complexifier avec un fichier ou le .env.
#
# Un membre qui a redoublé (ou qui s'est trompé) peut corriger sa situation lui-même,
# à tout moment, simplement en resélectionnant sa vraie promo via /setup_mmi : la
# suppression des rôles conflictuels est déjà gérée par PromoSelect.callback.
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────────────

# Nombre de jours, en juillet, pendant lesquels la tâche planifiée est autorisée à
# déclencher la rotation si elle ne l'a pas encore fait cette année (sert de filet de
# sécurité si le bot était éteint le 1er juillet)
JOUR_LIMITE_ROTATION = 5

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : SAUVEGARDE DE L'ÉTAT (ÉVITER LES DOUBLONS)
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Mémorisation en mémoire uniquement (pas de fichier ni de .env) : l'année de la
# dernière rotation est remise à zéro à chaque redémarrage du bot. Le seul risque est
# que la rotation se redéclenche si le bot redémarre PILE pendant les JOUR_LIMITE_ROTATION
# premiers jours de juillet après avoir déjà tourné cette année-là. Risque jugé
# suffisamment faible pour éviter la complexité d'un fichier ou d'une variable d'env.
# ──────────────────────────────────────────────────────────────────────────────────────

_derniere_rotation_annee = 0


def lire_derniere_rotation():
    """Lit l'année de la dernière rotation annuelle effectuée (0 si jamais exécutée
    depuis le dernier démarrage du bot)"""
    return _derniere_rotation_annee


def ecrire_derniere_rotation(annee):
    """Enregistre en mémoire l'année de la rotation annuelle qui vient d'être effectuée"""
    global _derniere_rotation_annee
    _derniere_rotation_annee = annee

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : FONCTION PRINCIPALE - ROTATION DES PROMOS
# ──────────────────────────────────────────────────────────────────────────────────────

async def effectuer_rotation_annuelle():
    """Fait avancer tous les membres d'une promotion et retire les rôles de
    classe/spécialité devenus obsolètes. Appelée automatiquement début juillet."""
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("❌ Rotation annuelle : serveur introuvable")
        return

    role_mmi1 = guild.get_role(ROLE_PROMOS[0][0])
    role_mmi2 = guild.get_role(ROLE_PROMOS[1][0])
    role_mmi3 = guild.get_role(ROLE_PROMOS[2][0])
    role_ancien = guild.get_role(ROLE_PROMOS[3][0])

    # Tous les rôles de classe/spécialité à nettoyer (les spés des Anciens sont
    # volontairement conservées : elles représentent leur spécialité de fin d'études)
    roles_classes_et_spes = (
        [r[0] for r in ROLE_MMI1_CLASSES]
        + [r[0] for r in ROLE_MMI2_CLASSES]
        + [r[0] for r in ROLE_MMI2_SPES]
        + [r[0] for r in ROLE_MMI3_SPES]
    )

    membres_deplaces = 0

    for member in guild.members:
        if member.bot:
            continue

        await remove_roles(member, roles_classes_et_spes)

        if role_mmi1 in member.roles:
            await member.remove_roles(role_mmi1)
            await member.add_roles(role_mmi2)
            membres_deplaces += 1
        elif role_mmi2 in member.roles:
            await member.remove_roles(role_mmi2)
            await member.add_roles(role_mmi3)
            membres_deplaces += 1
        elif role_mmi3 in member.roles:
            await member.remove_roles(role_mmi3)
            await member.add_roles(role_ancien)
            membres_deplaces += 1

    print(f"✅ Rotation annuelle effectuée : {membres_deplaces} membre(s) déplacé(s) de promo")

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2.5 : VIDAGE DES SALONS DE CLASSE (PROMO/TD/TP)
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Note : Discord ne permet la suppression "en masse" (rapide) que pour les messages de
# moins de 14 jours. Pour les messages plus anciens, discord.py bascule automatiquement
# sur une suppression message par message (beaucoup plus lente et soumise aux limites de
# l'API). Sur des salons actifs depuis un an, le vidage complet peut donc prendre du
# temps - c'est normal, il ne faut pas s'inquiéter si ça dure plusieurs minutes.
# ──────────────────────────────────────────────────────────────────────────────────────

# Salons de classe (promo/TD/TP) à vider intégralement chaque début juillet
CHANNELS_A_VIDER = [
    1415235848118734900,
    1460210497868795964,
    1460210687963041814,
    1460210913364934782,
    1460211064464474257,
    1460211141404917822,
    1460211194106216541,
    1460212958410834054,
    1460211506229543063,
    1460211641248387154,
    1460212300236591165,
    1459175254625620000,
    1460630973212524760,
    1460631121954869371,
    1460631623489028177,
    1460631718447808522,
    1460631801302220862,
    1460631861997863069,
    1460631953811312765,
    1460635160247799909,
    1460635045856411901,
    1460635533788053516,
    1459175371340644495,
    1460635975985270849,
    1460636030054043941,
    1460636081509892364,
    1460636397676527697,
    1460636483861086300,
    1460636570028605665,
    1460637078025928869
]


async def vider_salons_de_classe():
    """Vide intégralement tous les salons de classe (promo/TD/TP) listés dans
    CHANNELS_A_VIDER. Appelée automatiquement début juillet, en même temps que la
    rotation annuelle des promos."""
    total_supprime = 0

    for channel_id in CHANNELS_A_VIDER:
        channel = bot.get_channel(channel_id)
        if channel is None:
            print(f"❌ Salon introuvable pour le vidage : {channel_id}")
            continue

        try:
            supprimes = await channel.purge(limit=None)
            total_supprime += len(supprimes)
        except discord.Forbidden:
            print(f"❌ Permissions insuffisantes pour vider le salon {channel.name} ({channel_id})")
        except Exception as e:
            print(f"❌ Erreur lors du vidage du salon {channel_id} : {e}")

    print(f"✅ Salons de classe vidés : {total_supprime} message(s) supprimé(s) au total")

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 3 : TÂCHE PLANIFIÉE - VÉRIFICATION QUOTIDIENNE
# ──────────────────────────────────────────────────────────────────────────────────────

@tasks.loop(hours=24)
async def verifier_rotation_annuelle():
    """Vérifie une fois par jour si on est début juillet et si la rotation annuelle
    n'a pas déjà été effectuée cette année ; si besoin, déclenche automatiquement la
    rotation des promos ET le vidage des salons de classe"""
    aujourdhui = datetime.date.today()

    if aujourdhui.month == 7 and aujourdhui.day <= JOUR_LIMITE_ROTATION:
        if lire_derniere_rotation() != aujourdhui.year:
            await effectuer_rotation_annuelle()
            await vider_salons_de_classe()
            ecrire_derniere_rotation(aujourdhui.year)


@verifier_rotation_annuelle.before_loop
async def avant_verification_rotation():
    """Attend que le bot soit complètement connecté avant de démarrer les vérifications"""
    await bot.wait_until_ready()

















# ══════════════════════════════════════════════════════════════════════════════════════
# ███████╗ ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗  █████╗ 
# ██╔════╝██╔═══██╗██║   ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗
# ███████╗██║   ██║██║   ██║███████║██║  ██║██████╔╝███████║
# ╚════██║██║▄▄ ██║██║   ██║██╔══██║██║  ██║██╔══██╗██╔══██║
# ███████║╚██████╔╝╚██████╔╝██║  ██║██████╔╝██║  ██║██║  ██║
# ╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# FONCTIONNALITÉ 9 : ÉQUIPES DE COULEUR (INTÉ)
#
# Concept :
# Pour l'intégration, chaque étudiant MMI1/MMI2 est tiré au sort dans une équipe de
# couleur en amphi (en physique, IRL). Deux commandes permettent de gérer ça en Discord.
#
# /setup_squadra : poste le menu de sélection dans le salon où la commande est tapée
# (pas de salon fixe), pour pouvoir le poster séparément dans le salon des MMI1 pendant
# leur CM d'annonce, puis plus tard dans celui des MMI2, sans que les MMI2 n'y aient
# accès avant l'heure (et inversement).
#
# /setup_squadra_absents : poste un bouton qui attribue aléatoirement une équipe à tous
# les MMI1/MMI2 n'en ayant pas encore (absents le jour du tirage, ou indécis), en
# respectant les places encore disponibles par équipe et par niveau.
#
# Règles communes aux deux commandes :
# - Réservé aux MMI1 et MMI2 (vérifié via leurs rôles de promo)
# - Choix définitif : impossible de changer d'équipe soi-même une fois choisie, pour
#   éviter de tricher sur le tirage au sort fait en physique
# - Chaque équipe a un quota : 11 MMI1 et 8 MMI2, sauf la Squadra Verte qui n'a que
#   7 MMI2 (voir CAPACITE_SQUADRA_MMI1 / CAPACITE_SQUADRA_MMI2_DEFAUT / EXCEPTIONS).
#   Une fois le quota atteint pour un niveau donné, l'équipe n'est plus proposable à
#   ce niveau (mais reste ouverte à l'autre niveau si son quota n'est pas encore atteint).
#
# Les noms des rôles ("Squadra Rouge", etc.) peuvent changer plus tard : le code se
# base uniquement sur l'ID du rôle, jamais sur son nom affiché.
#
# ══════════════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 0 : CONFIGURATION ET IDS
# ──────────────────────────────────────────────────────────────────────────────────────

# Rôles d'équipe de couleur pour l'inté (nom affiché indicatif, seul l'ID compte)
ROLE_SQUADRA = [
    (1546395504357675078, "Noire"),
    (1546191049041641522, "Rouge"),
    (1546397998768980020, "Orange"),
    (1546396082336956496, "Jaune"),
    (1546397884193447947, "Verte"),
    (1546395829546254386, "Bleue"),
    (1546395985130033182, "Violette"),
    (1546396136233762907, "Rose")
]

# Quota MMI1 : identique pour toutes les équipes
CAPACITE_SQUADRA_MMI1 = 11

# Quota MMI2 : 8 par défaut, sauf la Squadra Verte qui n'en compte que 7
CAPACITE_SQUADRA_MMI2_DEFAUT = 8
CAPACITE_SQUADRA_MMI2_EXCEPTIONS = {
    1546397884193447947: 7,  # Squadra Verte
}

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : FONCTIONS UTILITAIRES - QUOTAS PAR ÉQUIPE
# ──────────────────────────────────────────────────────────────────────────────────────

def capacite_squadra(role_squadra_id, promo):
    """Retourne le quota d'une équipe pour un niveau donné ('mmi1' ou 'mmi2')"""
    if promo == "mmi1":
        return CAPACITE_SQUADRA_MMI1
    return CAPACITE_SQUADRA_MMI2_EXCEPTIONS.get(role_squadra_id, CAPACITE_SQUADRA_MMI2_DEFAUT)


def compter_membres_squadra(guild, role_squadra_id, role_niveau_id):
    """Compte les membres ayant à la fois le rôle d'équipe et le rôle de niveau
    (MMI1 ou MMI2) donnés"""
    role_squadra = guild.get_role(role_squadra_id)
    role_niveau = guild.get_role(role_niveau_id)
    if role_squadra is None or role_niveau is None:
        return 0
    return sum(1 for m in guild.members if role_squadra in m.roles and role_niveau in m.roles)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 2 : COMMANDE ADMIN (/setup_squadra) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_squadra")
@app_commands.checks.has_permissions(administrator=True)
async def setup_squadra(interaction: discord.Interaction):
    """Crée le menu de sélection d'équipe (inté) dans le salon où la commande est tapée.
    Permet de poster ce menu séparément dans le salon des MMI1 puis, plus tard, dans
    celui des MMI2, pour que chaque promo n'y ait accès qu'au bon moment (pendant leur
    propre CM d'annonce)."""
    await interaction.channel.send(
        "**Équipes de l'intégration**\n\n"
        "Tu as été tiré au sort dans une équipe en amphi ? Sélectionne-la ci-dessous.\n"
        "⚠️  Ce choix est définitif : tu ne pourras plus le changer toi-même ensuite.\n\n"
        "Réservé aux MMI1 et MMI2.",
        view=SquadraView()
    )
    await interaction.response.send_message("✅  Menu des équipes envoyé dans ce salon.", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 3 : VIEW - SÉLECTION DE L'ÉQUIPE
# ──────────────────────────────────────────────────────────────────────────────────────

class SquadraSelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Choisis ton équipe (celle tirée en amphi)",
            options=[discord.SelectOption(label=f"Squadra {n}", value=str(i)) for i, n in ROLE_SQUADRA],
            custom_id="squadra_select"
        )

    async def callback(self, interaction: discord.Interaction):
        # ⚠️ NE PAS SUPPRIMER CE MESSAGE
        # Ce select correspond au message racine partagé par tout le monde, comme le
        # PromoSelect de /setup_mmi : il doit rester visible en permanence.

        member = interaction.user
        guild = interaction.guild

        role_mmi1 = guild.get_role(ROLE_PROMOS[0][0])
        role_mmi2 = guild.get_role(ROLE_PROMOS[1][0])

        # Vérification : réservé aux MMI1 et MMI2
        if role_mmi1 in member.roles:
            promo = "mmi1"
            role_niveau = role_mmi1
        elif role_mmi2 in member.roles:
            promo = "mmi2"
            role_niveau = role_mmi2
        else:
            await interaction.response.send_message(
                "❌  Cette sélection est réservée aux MMI1 et MMI2. "
                "Choisis d'abord ta promo via /setup_mmi.",
                ephemeral=True
            )
            return

        # Choix définitif : impossible de changer d'équipe une fois qu'elle est attribuée
        roles_squadra_existants = [guild.get_role(r[0]) for r in ROLE_SQUADRA]
        if any(r in member.roles for r in roles_squadra_existants if r is not None):
            await interaction.response.send_message(
                "❌  Tu as déjà une équipe, impossible d'en changer toi-même.",
                ephemeral=True
            )
            return

        role_squadra_id = int(self.values[0])
        role_squadra = guild.get_role(role_squadra_id)

        # Vérification du quota restant pour cette équipe, à ce niveau
        quota = capacite_squadra(role_squadra_id, promo)
        deja_present = compter_membres_squadra(guild, role_squadra_id, role_niveau.id)

        if deja_present >= quota:
            await interaction.response.send_message(
                f"❌  Cette équipe est déjà complète pour les "
                f"{'MMI1' if promo == 'mmi1' else 'MMI2'}. Choisis-en une autre.",
                ephemeral=True
            )
            return

        await member.add_roles(role_squadra)
        await interaction.response.send_message(
            f"✅  Équipe **{role_squadra.name}** attribuée. C'est définitif, tu ne pourras plus en changer toi-même.",
            ephemeral=True
        )


class SquadraView(View):
    """View principale contenant le sélecteur d'équipe (message unique, partagé par tous)"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SquadraSelect())

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 4 : COMMANDE ADMIN (/setup_squadra_absents) - ATTRIBUTION ALÉATOIRE
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Pour les MMI1/MMI2 absents le jour du tirage au sort en amphi (ou qui n'ont
# simplement pas encore fait leur choix), cette commande poste un bouton permettant
# d'attribuer automatiquement une équipe à tous ceux qui n'en ont pas encore, en
# respectant les places encore disponibles dans chaque équipe (voir capacite_squadra
# et compter_membres_squadra définies plus haut).
#
# L'attribution est aléatoire mais contrainte : elle ne peut jamais faire dépasser le
# quota d'une équipe pour un niveau donné. S'il n'y a plus assez de places pour tout le
# monde (plus d'absents que de places libres), les membres restants ne reçoivent rien
# et sont signalés dans le message de résultat.
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_squadra_absents")
@app_commands.checks.has_permissions(administrator=True)
async def setup_squadra_absents(interaction: discord.Interaction):
    """Poste, dans le salon où la commande est tapée, un bouton pour attribuer
    aléatoirement une équipe aux MMI1/MMI2 qui n'en ont pas encore"""
    await interaction.channel.send(
        "**Attribution aléatoire des équipes restantes**\n\n"
        "Ce bouton attribue automatiquement une équipe aux MMI1 et MMI2 qui n'en ont "
        "pas encore, en respectant les places encore disponibles dans chaque équipe.",
        view=SquadraAleatoireView()
    )
    await interaction.response.send_message("✅  Message d'attribution aléatoire envoyé.", ephemeral=True)


class SquadraAleatoireView(View):
    """View avec le bouton d'attribution aléatoire des équipes restantes"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Attribuer les équipes aux absents",
        style=discord.ButtonStyle.primary,
        emoji="🎲",
        custom_id="squadra_attribution_alea"
    )
    async def attribuer(self, interaction: discord.Interaction, button: Button):
        """Tire au sort une équipe pour chaque MMI1/MMI2 n'en ayant pas encore,
        en respectant les places restantes par équipe et par niveau"""
        # Double sécurité : seul un admin peut déclencher l'attribution, même si le
        # bouton reste visible pour tout le monde une fois posté
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌  Seuls les administrateurs peuvent utiliser ce bouton.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        guild = interaction.guild
        role_mmi1 = guild.get_role(ROLE_PROMOS[0][0])
        role_mmi2 = guild.get_role(ROLE_PROMOS[1][0])
        roles_squadra_existants = [guild.get_role(r[0]) for r in ROLE_SQUADRA]

        resultats = []

        for promo, role_niveau, libelle_niveau in [
            ("mmi1", role_mmi1, "MMI1"),
            ("mmi2", role_mmi2, "MMI2"),
        ]:
            # Construction du "sac" des places encore libres : une entrée par place
            sac_places = []
            for role_squadra_id, _ in ROLE_SQUADRA:
                quota = capacite_squadra(role_squadra_id, promo)
                deja_present = compter_membres_squadra(guild, role_squadra_id, role_niveau.id)
                sac_places.extend([role_squadra_id] * max(0, quota - deja_present))

            random.shuffle(sac_places)

            # Membres de ce niveau n'ayant encore aucune équipe
            absents = [
                m for m in guild.members
                if role_niveau in m.roles
                and not any(r in m.roles for r in roles_squadra_existants if r is not None)
            ]
            random.shuffle(absents)

            nb_attribues = 0
            for membre in absents:
                if not sac_places:
                    break
                role_squadra = guild.get_role(sac_places.pop())
                await membre.add_roles(role_squadra)
                nb_attribues += 1

            nb_restants = len(absents) - nb_attribues
            resultats.append(f"{libelle_niveau} : {nb_attribues} équipe(s) attribuée(s), {nb_restants} en attente (plus de place libre)")

        await interaction.followup.send(
            "✅  Attribution terminée.\n" + "\n".join(resultats),
            ephemeral=True
        )











# ══════════════════════════════════════════════════════════════════════════════════════
# GESTION UNIFIÉE DES MESSAGES
# ══════════════════════════════════════════════════════════════════════════════════════
#
# Cette fonction centralise TOUS les traitements de messages du bot :
# 1. SYSTÈME ETU : Gestion de la vérification étudiante en DM
# 2. SYSTÈME TICKETS : Modération automatique des salons tickets/demandes
#
# Architecture :
# - Vérification anti-bot en premier
# - Branche ETU pour les DM (vérification email → code → MMI)
# - Branche TICKETS pour les salons modérés (suppression non-admin + avertissement)
# - Tout autre message est ignoré
#
# ══════════════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_message(message):
    """Gestion centralisée de TOUS les messages (ETU + TICKETS)"""
    
    # ✅ FILTRE ANTI-BOT (s'applique à tous les systèmes)
    if message.author.bot:
        return
    
    # ──────────────────────────────────────────────────────────────────────────────────────
    # BRANCHE 1 : SYSTÈME ETU (Vérification Étudiante)
    # ──────────────────────────────────────────────────────────────────────────────────────
    # Traitement des messages DM pour la vérification étudiante
    # Étapes : Email → Code par mail → Code valide → Question MMI
    
    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        content = message.content.strip()

        # ── Étape 3 : Réponse à la question "Es-tu en MMI ?" ──
        if user_id in waiting_mmi_response:
            if content.lower() in ["oui", "yes", "o", "y", "non", "no", "n"]:
                waiting_mmi_response.remove(user_id)
                
                if content.lower() in ["oui", "yes", "o", "y"]:
                    guild = bot.get_guild(GUILD_ID)
                    member = guild.get_member(user_id)
                    await member.add_roles(guild.get_role(ROLE_MMI_ID))
                    await message.channel.send("✅  Rôle MMI attribué.")
                else:
                    await message.channel.send("Merci pour ta réponse.")
            else:
                await message.channel.send("❌  Apprends à écrire, **OUI** ou **NON** !")
            return

        # ── Étape 2 : Vérification du code ──
        if user_id in codes_temp:
            if content == codes_temp[user_id]:
                guild = bot.get_guild(GUILD_ID)
                member = guild.get_member(user_id)
                await member.add_roles(guild.get_role(ROLE_ETUDIANT_ID))
                codes_temp.pop(user_id)
                mails_temp.pop(user_id)
                
                await message.channel.send("✅  Vérification réussie ! Rôle Étudiant attribué.")
                await message.channel.send("\n**Es-tu un étudiant en BUT MMI (anciens compris) ?**\nRéponds par **OUI** ou **NON**.")
                waiting_mmi_response.add(user_id)
            else:
                await message.channel.send(
                    "❌  Code incorrect, réessaie.",
                    view=VerificationCodeView(user_id)
                )
            return

        # ── Étape 1 : Réception de l'adresse mail ──
        if not content.endswith("@ens.univ-artois.fr"):
            await message.channel.send("❌  Adresse invalide. Envoie un mail **@ens.univ-artois.fr**")
            return

        success = await envoyer_code(content, user_id)
        if success:
            await message.channel.send(
                "✅  Code envoyé par mail. Réponds avec le code reçu.",
                view=VerificationCodeView(user_id)
            )
        else:
            await message.channel.send("❌  Impossible d'envoyer le code.")
        return
    
    # ──────────────────────────────────────────────────────────────────────────────────────
    # BRANCHE 2 : SYSTÈME TICKETS (Modération automatique)
    # ──────────────────────────────────────────────────────────────────────────────────────
    # Suppression automatique des messages non-admin dans les salons tickets/demandes
    
    if message.channel.id in [CHANNEL_TICKETS_ID, CHANNEL_DEMANDES_ID]:
        # Les admins peuvent écrire normalement
        if not message.author.guild_permissions.administrator:
            try:
                await message.delete()
                await message.author.send(
                    f"⚠️  Les messages dans ce salon sont automatiquement supprimés.\n"
                    f"Utilise le bouton pour {'ouvrir une plainte' if message.channel.id == CHANNEL_TICKETS_ID else 'faire une demande'} !"
                )
            except:
                pass
        return


# ══════════════════════════════════════════════════════════════════════════════════════
# ██████╗ ███████╗███╗   ███╗ █████╗ ██████╗ ██████╗  █████╗  ██████╗ ███████╗
# ██╔══██╗██╔════╝████╗ ████║██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝
# ██║  ██║█████╗  ██╔████╔██║███████║██████╔╝██████╔╝███████║██║  ███╗█████╗  
# ██║  ██║██╔══╝  ██║╚██╔╝██║██╔══██║██╔══██╗██╔══██╗██╔══██║██║   ██║██╔══╝  
# ██████╔╝███████╗██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██║██║  ██║╚██████╔╝███████╗
# ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
# ══════════════════════════════════════════════════════════════════════════════════════
#
# DÉMARRAGE DU BOT
#
# Cette ligne démarre le bot Discord avec le token fourni dans le fichier .env
# C'est la dernière instruction du fichier - tout le code précédent définit
# les fonctionnalités, cette ligne les active.
#
# ══════════════════════════════════════════════════════════════════════════════════════

bot.run(TOKEN)