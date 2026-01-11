import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
import random
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# ================== CHARGEMENT ENV ==================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_BDE = os.getenv("EMAIL_BDE")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ================== CONFIG SERVEUR ==================
GUILD_ID = 1412342194639212657
CHANNEL_ROLES_ID = 1413971250958696520
CHANNEL_MMI_ID = 1459358436859838648

# ================== ROLES ET CLASSES ==================
ROLE_ETUDIANT_ID = 1412384279371055185
ROLE_MMI_ID = 1412385271214899240

ROLE_PROMOS = [
    (1459145017128914945, "MMI1"),
    (1459149695409586341, "MMI2"),
    (1459149685993373707, "MMI3"),
    (1459772466129010862, "Ancien")
]

ROLE_MMI1_CLASSES = [
    (1459149991216939230, "MMI1 A1"),
    (1459150875854635028, "MMI1 A2"),
    (1459150952740159650, "MMI1 A3"),
    (1459151029470761042, "MMI1 B1"),
    (1459151085079105730, "MMI1 B2"),
    (1459151141706268686, "MMI1 B3"),
    (1459151199575216235, "MMI1 C1")
]

ROLE_MMI2_CLASSES = [
    (1459156766204891253, "MMI2 A1"),
    (1459156833506820199, "MMI2 A2"),
    (1459156886774480927, "MMI2 B1"),
    (1459156940893720699, "MMI2 B2"),
    (1459157008522674320, "MMI2 C1")
]

ROLE_MMI2_SPES = [
    (1459159992849662125, "COM2"),
    (1459242224402305045, "COM2"),
    (1459159792646881418, "MUL1"),
    (1459242366555914418, "MUL2"),
    (1459160080657289361, "WEB")
]

ROLE_MMI3_CLASSES = [
    (1459157221110841427, "MMI3 A1"),
    (1459157304061726843, "MMI3 A2"),
    (1459157361615962268, "MMI3 B1"),
    (1459157446621794334, "MMI3 B2"),
    (1459157500262613093, "MMI3 C1")
]

ROLE_ANCIEN_SPES = [
    (1459772225937998001, "COM"),
    (1459772322029375646, "MUL"),
    (1459770233765101800, "WEB")
]

# ================== CONFIG MAIL ==================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ================== STOCKAGE TEMPORAIRE ==================
codes_temp = {}
mails_temp = {}
decisions_mmi = {}
promo_selection = {}
class_selection = {}
spe_selection = {}

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ================== BOT ==================
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user} ✅")

# ================== FONCTION ENVOI MAIL ==================
async def envoyer_code(email_dest, user_id):
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
        f"Si tu n’as pas demandé ce code, ignore ce mail."
    )

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_BDE, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Erreur SMTP: {e}")
        return False

# ================== VIEWS VERIFICATION ==================
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
        await interaction.response.send_message(
            "Regarde tes messages privés pour continuer la vérification 📩",
            ephemeral=True
        )
        try:
            await interaction.user.send(
                "**Vérification Étudiante – Université d'Artois**\n\n"
                "Merci d’envoyer ton **adresse mail universitaire** :\n"
                "prenom_nom@ens.univ-artois.fr"
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "Impossible de t’envoyer un DM. Active les messages privés du serveur.",
                ephemeral=True
            )

class VerificationCodeView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="🔄 Renvoyer le code", style=discord.ButtonStyle.secondary)
    async def resend(self, interaction: discord.Interaction, button: Button):
        if self.user_id not in mails_temp:
            await interaction.response.send_message("❌ Aucun mail enregistré.", ephemeral=True)
            return
        success = await envoyer_code(mails_temp[self.user_id], self.user_id)
        await interaction.response.send_message(
            "✅ Nouveau code envoyé." if success else "❌ Impossible d’envoyer le code.", ephemeral=True
        )

    @discord.ui.button(label="✏️ Modifier le mail", style=discord.ButtonStyle.danger)
    async def change(self, interaction: discord.Interaction, button: Button):
        codes_temp.pop(self.user_id, None)
        mails_temp.pop(self.user_id, None)
        await interaction.user.send(
            "**Modification de ton mail universitaire**\n\n"
            "Merci d’envoyer ton **nouveau mail universitaire** :\n"
            "prenom_nom@ens.univ-artois.fr"
        )
        await interaction.response.send_message("Flux réinitialisé.", ephemeral=True)

# ================== HANDLER DM ==================
@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = message.author.id
    content = message.content.strip().lower()

    # --- Vérification code ---
    if user_id in codes_temp:
        if content == codes_temp[user_id]:
            guild = bot.get_guild(GUILD_ID)
            member = guild.get_member(user_id)
            await member.add_roles(guild.get_role(ROLE_ETUDIANT_ID))
            codes_temp.pop(user_id)
            mails_temp.pop(user_id)
            await message.channel.send("✅ Vérification réussie ! Rôle Étudiant attribué.")
            await message.channel.send("Es-tu un étudiant en BUT MMI (ancien compris)?", view=PostVerificationMMI(user_id))
        else:
            await message.channel.send("❌ Code incorrect, réessaie.", view=VerificationCodeView(user_id))
        return

    # --- Vérification format mail ---
    if not content.endswith("@ens.univ-artois.fr"):
        await message.channel.send("❌ Adresse invalide. Envoie un mail **@ens.univ-artois.fr**")
        return

    success = await envoyer_code(content, user_id)
    if success:
        await message.channel.send("✅ Code envoyé par mail. Réponds avec le code reçu.", view=VerificationCodeView(user_id))
    else:
        await message.channel.send("❌ Impossible d’envoyer le code.")

# ================== POST-VERIF MMI ==================
class PostVerificationMMI(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Oui", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: Button):
        if self.user_id in decisions_mmi:
            await interaction.response.send_message("❌ Choix déjà fait.", ephemeral=True)
            return
        member = interaction.guild.get_member(self.user_id)
        await member.add_roles(interaction.guild.get_role(ROLE_MMI_ID))
        decisions_mmi[self.user_id] = True
        await interaction.response.send_message("✅ Rôle MMI attribué.", ephemeral=True)

    @discord.ui.button(label="Non", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: Button):
        if self.user_id in decisions_mmi:
            await interaction.response.send_message("❌ Choix déjà fait.", ephemeral=True)
            return
        decisions_mmi[self.user_id] = False
        await interaction.response.send_message("Merci pour ta réponse.", ephemeral=True)

# ================== MENU MMI ==================
async def check_mmi(interaction):
    if ROLE_MMI_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("❌ Réservé aux MMI.", ephemeral=True)
        return False
    return True

async def remove_roles(member, ids):
    for rid in ids:
        role = member.guild.get_role(rid)
        if role and role in member.roles:
            await member.remove_roles(role)

class PromoSelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Choisis ta promo",
            options=[
                discord.SelectOption(label=name, value=str(rid)) for rid, name in ROLE_PROMOS
            ]
        )

    async def callback(self, interaction):
        selected = int(self.values[0])
        member = interaction.user
        promo_selection[member.id] = selected

        # Supprime toutes promos/classes/spés existantes
        await remove_roles(
            member,
            [rid for rid, _ in ROLE_PROMOS]
            + [rid for rid, _ in ROLE_MMI1_CLASSES]
            + [rid for rid, _ in ROLE_MMI2_CLASSES]
            + [rid for rid, _ in ROLE_MMI2_SPES]
            + [rid for rid, _ in ROLE_MMI3_CLASSES]
            + [rid for rid, _ in ROLE_ANCIEN_SPES]
        )

        # Ajoute le rôle promo sélectionné
        await member.add_roles(interaction.guild.get_role(selected))

        # Lance la suite selon promo
        if selected == ROLE_PROMOS[3][0]:  # Ancien
            # Directement dans la View, pas besoin d'une autre classe
            await interaction.response.send_message(
                "✅ Ah, un ancien !? C'était quoi ta **spécialité de 3ème année** ?",
                view=View(timeout=None).add_item(SpeSelectAncien()),
                ephemeral=True
            )
        elif selected == ROLE_PROMOS[0][0]:  # MMI1
            await interaction.response.send_message(
                "✅ Promo sélectionnée. Maintenant choisis ta **classe**.",
                view=ClassSelectView("mmi1"),
                ephemeral=True
            )
        elif selected == ROLE_PROMOS[1][0]:  # MMI2
            await interaction.response.send_message(
                "✅ Promo sélectionnée. Maintenant choisis ta **classe**.",
                view=ClassSelectView("mmi2"),
                ephemeral=True
            )
        elif selected == ROLE_PROMOS[2][0]:  # MMI3
            await interaction.response.send_message(
                "✅ Promo sélectionnée. Maintenant choisis ta **classe**.",
                view=ClassSelectView("mmi3"),
                ephemeral=True
            )

# ================== CLASS & SPE VIEWS ==================
class ClassSelect(Select):
    def __init__(self, promo):
        self.promo = promo
        if promo == "mmi1":
            options = [discord.SelectOption(label=name, value=str(rid)) for rid, name in ROLE_MMI1_CLASSES]
        elif promo == "mmi2":
            options = [discord.SelectOption(label=name, value=str(rid)) for rid, name in ROLE_MMI2_CLASSES]
        else:
            options = [discord.SelectOption(label=name, value=str(rid)) for rid, name in ROLE_MMI3_CLASSES]
        super().__init__(placeholder="Choisis ta classe", options=options)

    async def callback(self, interaction):
        member = interaction.user
        class_id = int(self.values[0])
        await member.add_roles(interaction.guild.get_role(class_id))
        class_selection[member.id] = class_id

        if self.promo == "mmi2":
            await interaction.response.send_message(
                "✅ Classe sélectionnée. Maintenant choisis ta **spécialité**.",
                view=SpeSelectView(),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "✅ Classe sélectionnée.",
                ephemeral=True
            )

class SpeSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, value=str(rid)) for rid, name in ROLE_MMI2_SPES]
        super().__init__(placeholder="Choisis ta spécialité", options=options)

    async def callback(self, interaction):
        member = interaction.user
        spe_id = int(self.values[0])
        await member.add_roles(interaction.guild.get_role(spe_id))
        spe_selection[member.id] = spe_id
        await interaction.response.send_message(
            "✅ Spécialité sélectionnée.",
            ephemeral=True
        )

class SpeSelectAncien(Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, value=str(rid)) for rid, name in ROLE_ANCIEN_SPES]
        super().__init__(placeholder="Indique ta spécialité de fin d'études", options=options)

    async def callback(self, interaction):
        member = interaction.user
        spe_id = int(self.values[0])
        await member.add_roles(interaction.guild.get_role(spe_id))
        spe_selection[member.id] = spe_id
        await interaction.response.send_message(
            "✅ Spécialité sélectionnée.",
            ephemeral=True
        )

class ClassSelectView(View):
    def __init__(self, promo):
        super().__init__(timeout=None)
        self.add_item(ClassSelect(promo))

class SpeSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SpeSelect())

# ================== COMMANDES ADMIN ==================
@bot.tree.command(name="setup_etu")
@app_commands.checks.has_permissions(administrator=True)
async def setup_etu(interaction: discord.Interaction):
    channel = bot.get_channel(CHANNEL_ROLES_ID)
    guild = interaction.guild
    role = guild.get_role(ROLE_ETUDIANT_ID)
    await channel.send(
        f"\n**Obtention du rôle {role.mention}**\n"
        "Clique sur le bouton ci-dessous pour faire la **vérification étudiante** 🎓",
        view=VerificationView()
    )
    await interaction.response.send_message("Message créé.", ephemeral=True)

@bot.tree.command(name="setup_mmi")
@app_commands.checks.has_permissions(administrator=True)
async def setup_mmi(interaction: discord.Interaction):
    channel = bot.get_channel(CHANNEL_MMI_ID)
    guild = interaction.guild
    role = guild.get_role(ROLE_MMI_ID)
    # Message public pour tout le monde
    await channel.send(
        f"\n**Obtention des rôles {role.mention}**\n"
        "Pour commencer, tu es en quelle année de BUT ?",
        view=MMIMenu()
    )
    await interaction.response.send_message("Menu MMI créé.", ephemeral=True)

# ================== MMIMENU ==================
class MMIMenu(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PromoSelect())

# ================== RUN ==================
bot.run(TOKEN)

