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
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
import random
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import asyncio

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











# ══════════════════════════════════════════════════════════════════════════════════════
# ███████╗███████╗████████╗██╗   ██╗██████╗     ██████╗ ███████╗ ██████╗ ██╗     ███████╗
# ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗    ██╔══██╗██╔════╝██╔════╝ ██║     ██╔════╝
# ███████╗█████╗     ██║   ██║   ██║██████╔╝    ██████╔╝█████╗  ██║  ███╗██║     █████╗  
# ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝     ██╔══██╗██╔══╝  ██║   ██║██║     ██╔══╝  
# ███████║███████╗   ██║   ╚██████╔╝██║         ██║  ██║███████╗╚██████╔╝███████╗███████╗
# ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝         ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝
# ══════════════════════════════════════════════════════════════════════════════════════
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
        await interaction.response.send_message(
            "Regarde tes messages privés pour continuer la vérification  📩",
            ephemeral=True
        )
        await interaction.user.send(
            "**Vérification Étudiante – Université d'Artois**\n\n"
            "Merci d'envoyer ton **adresse mail universitaire** :\n"
            "prenom_nom@ens.univ-artois.fr"
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

# Rôles MMI2 : Classes (ACTUELLEMENT UTILISÉES - UTILISÉES DE SEPTEMBRE À FÉVRIER)
ROLE_MMI2_CLASSES = [
    (1459156766204891253, "MMI2 A1"),
    (1459156833506820199, "MMI2 A2"),
    (1459156886774480927, "MMI2 B1"),
    (1459156940893720699, "MMI2 B2"),
    (1459157008522674320, "MMI2 C")
]

# Rôles MMI2 : Spécialités (NON UTILISÉES ACTUELLEMENT - UTILISÉES DE MARS À JUIN)
# Nouvelles appellations : Stratégie, Création, Développement Web
ROLE_MMI2_SPES = [
    (1459159992849662125, "MMI2 - STRAT1"),
    (1459242224402305045, "MMI2 - STRAT2"),
    (1459159792646881418, "MMI2 - CREA1"),
    (1459242366555914418, "MMI2 - CREA2"),
    (1459160080657289361, "MMI2 - DWEB")
]

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
# Anciennes appellations : COM, MUL, WEB
ROLE_ANCIEN_SPES = [
    (1459772225937998001, "COM"),
    (1459772322029375646, "MUL"),
    (1459770233765101800, "WEB")
]

# ──────────────────────────────────────────────────────────────────────────────────────
# SECTION 1 : COMMANDE ADMIN (/setup_mmi) - PREMIÈRE ACTION
# ──────────────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_mmi")
@app_commands.checks.has_permissions(administrator=True)
async def setup_mmi(interaction: discord.Interaction):
    """Crée le menu de sélection MMI dans le salon configuré"""
    channel = bot.get_channel(CHANNEL_MMI_ID)
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
            await interaction.response.send_message(
                "✅  Promo sélectionnée. Maintenant choisis ta **classe**.",
                view=ClassSelectView("mmi1", ROLE_MMI1_CLASSES),
                ephemeral=True
            )
        elif promo == ROLE_PROMOS[1][0]:  # MMI2
            await interaction.response.send_message(
                "✅  Promo sélectionnée. Maintenant choisis ta **classe**.",
                view=ClassSelectView("mmi2", ROLE_MMI2_CLASSES),
                ephemeral=True
            )
        elif promo == ROLE_PROMOS[2][0]:  # MMI3
            await interaction.response.send_message(
                "✅  Promo sélectionnée.",
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

        await interaction.response.send_message(
            "✅  Classe sélectionnée.",
            ephemeral=True
        )


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
# SECTION 7 : COMMANDE VACANCES D'ÉTÉ (SÉLECTION POUR LA RENTRÉE DE SEPTEMBRE)
# ──────────────────────────────────────────────────────────────────────────────────────
#
# Commande indépendante, utilisée uniquement pendant les vacances d'été.
# Ne modifie ni ne remplace /setup_mmi : c'est un menu séparé, posté à part.
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


@bot.tree.command(name="setup_mmi_vac")
@app_commands.checks.has_permissions(administrator=True)
async def setup_mmi_vac(interaction: discord.Interaction):
    """Crée le menu de sélection MMI spécifique aux vacances d'été"""
    channel = bot.get_channel(CHANNEL_MMI_ID)
    await channel.send(
        "À la rentrée de septembre, dans quelle promotion seras-tu ?",
        view=SummerMMIView()
    )
    await interaction.response.send_message("Menu MMI vacances créé.", ephemeral=True)











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
