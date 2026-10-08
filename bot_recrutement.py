import discord
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from datetime import datetime, timedelta

# ==================== CONFIGURATION ====================
STAFF_CHANNEL_ID = 1557463296326639666  # Ton salon staff/admin enregistré
GUILD_ID = discord.Object(id=1222994281334177842)      # Ton serveur Discord SPM
# =======================================================

class CandidatureModal(Modal, title="Candidature SPM"):
    nom_age = TextInput(
        label="Nom, Prénom & Âge",
        placeholder="ex: Morcamp Yoan, 50 ans",
        style=discord.TextStyle.short,
        required=True,
        max_length=100
    )
    role_cat = TextInput(
        label="Catégorie / Rôle souhaité",
        placeholder="ex: Hypercar / GT3 / Graphiste",
        style=discord.TextStyle.short,
        required=True,
        max_length=100
    )
    niveau_exp = TextInput(
        label="Niveau & Expérience simracing",
        placeholder="ex: DR S1, SR P1, 2 ans d'endurance",
        style=discord.TextStyle.paragraph,
        required=True
    )
    disponibilites = TextInput(
        label="Disponibilités (entraînements/courses)",
        placeholder="ex: Soirs de semaine dès 21h / week-end",
        style=discord.TextStyle.paragraph,
        required=True
    )
    motivation = TextInput(
        label="Pourquoi rejoindre la SPM ?",
        placeholder="Quelles sont tes motivations ?",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        staff_channel = interaction.client.get_channel(STAFF_CHANNEL_ID)
        
        embed = discord.Embed(
            title="📥 Nouvelle candidature reçue !",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Nom, Prénom & Âge", value=self.nom_age.value, inline=False)
        embed.add_field(name="🏎️ Catégorie / Rôle", value=self.role_cat.value, inline=False)
        embed.add_field(name="📊 Niveau & Expérience", value=self.niveau_exp.value, inline=False)
        embed.add_field(name="📅 Disponibilités", value=self.disponibilites.value, inline=False)
        embed.add_field(name="💬 Motivations", value=self.motivation.value, inline=False)
        embed.set_footer(text=f"ID Candidat : {interaction.user.id} | Statut : En attente")

        if staff_channel:
            # On envoie l'embed avec les boutons de validation/refus pour le staff
            await staff_channel.send(embed=embed, view=StaffActionView(candidat_id=interaction.user.id))
        
        await interaction.response.send_message(
            "✅ **Candidature envoyée avec succès !** Le staff de la Stinger Performance Motorsport va l'étudier attentivement. À très vite !",
            ephemeral=True
        )

class StaffActionView(View):
    def __init__(self, candidat_id: int):
        super().__init__(timeout=None)
        self.candidat_id = candidat_id

    @discord.ui.button(label="Valider & Lancer l'essai", style=discord.ButtonStyle.success, custom_id="staff_accept", emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        candidat = guild.get_member(self.candidat_id)
        
        # Calcul de la fin de la période d'essai (30 jours)
        date_debut = datetime.now()
        date_fin = date_debut + timedelta(days=30)
        date_debut_str = date_debut.strftime("%d/%m/%Y")
        date_fin_str = date_fin.strftime("%d/%m/%Y")

        # 1. Mise à jour de l'embed dans le salon staff
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Candidature Validée - Période d'essai en cours"
        embed.add_field(
            name="🏁 Suivi de l'essai (1 mois)",
            value=f"• **Début :** {date_debut_str}\n• **Fin de l'essai :** {date_fin_str}\n• **Validé par :** {interaction.user.mention}",
            inline=False
        )
        embed.set_footer(text=f"ID Candidat : {self.candidat_id} | Statut : En période d'essai")

        # Désactivation des boutons après action
        for child in self.children:
            child.disabled = True

        await interaction.message.edit(embed=embed, view=self)

        # 2. Prévention du candidat en Message Privé (DM)
        if candidat:
            try:
                dm_embed = discord.Embed(
                    title="🎉 Félicitations ! Candidature retenue - SPM",
                    description=(
                        "Bonjour !\n\n"
                        "Le staff de la **Stinger Performance Motorsport** a examiné ta candidature avec attention et a le plaisir de t'annoncer qu'elle est **validée** !\n\n"
                        "🏎️ **Début de ta période d'essai :**\n"
                        f"Ta période d'essai officielle d'un mois commence dès aujourd'hui (**{date_debut_str}**) et se terminera le **{date_fin_str}**.\n"
                        "C'est l'occasion de partager nos sessions d'entraînement, de trouver tes repères en piste et de confirmer notre belle cohésion d'équipe.\n\n"
                        "Bienvenue à bord et **BEE FAST, STING HARD 🐝** !"
                    ),
                    color=discord.Color.green()
                )
                await candidat.send(embed=dm_embed)
            except discord.Forbidden:
                pass # Si le candidat a ses DM fermés

        await interaction.response.send_message(f"✅ Candidature validée avec succès. Le candidat a été prévenu et l'essai est programmé jusqu'au **{date_fin_str}**.", ephemeral=True)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger, custom_id="staff_refuse", emoji="❌")
    async def refuse_button(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        candidat = guild.get_member(self.candidat_id)

        # 1. Mise à jour de l'embed staff
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Candidature Refusée"
        embed.add_field(
            name="🚫 Décision",
            value=f"• **Refusé par :** {interaction.user.mention}\n• **Date :** {datetime.now().strftime('%d/%m/%Y')}",
            inline=False
        )
        embed.set_footer(text=f"ID Candidat : {self.candidat_id} | Statut : Refusé")

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(embed=embed, view=self)

        # 2. Prévention du candidat en DM
        if candidat:
            try:
                dm_embed = discord.Embed(
                    title="Mise à jour concernant ta candidature - SPM",
                    description=(
                        "Bonjour,\n\n"
                        "Nous te remercions pour l'intérêt que tu portes à la **Stinger Performance Motorsport**.\n"
                        "Après étude de ton profil, nous ne pouvons malheureusement pas donner suite à ta candidature pour le moment.\n\n"
                        "Nous te souhaitons une excellente continuation sur les pistes !"
                    ),
                    color=discord.Color.red()
                )
                await candidat.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        await interaction.response.send_message("❌ Candidature refusée. Le candidat a été notifié.", ephemeral=True)

class RecrutementView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Envoyer ma candidature", style=discord.ButtonStyle.primary, custom_id="spm_apply_button", emoji="📩")
    async def apply_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(CandidatureModal())

class SPMClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # Nécessaire pour retrouver le membre et lui envoyer un DM
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(RecrutementView())
        # Enregistrement persistant pour les boutons staff si le bot redémarre
        # (On peut créer une vue générique si besoin, mais ici le staff clique rapidement)

client = SPMClient()

@client.event
async def on_ready():
    client.tree.copy_global_to(guild=GUILD_ID)
    synced = await client.tree.sync(guild=GUILD_ID)
    print(f"Synchronisé {len(synced)} commande(s) sur le serveur SPM.")
    print(f"Connecté en tant que {client.user} (ID: {client.user.id})")
    print("Bot prêt et opérationnel !")

@client.tree.command(name="deploy_recrutement", description="Poste le message et le bouton de recrutement SPM")
@app_commands.checks.has_permissions(administrator=True)
async def deploy_recrutement(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Panel de recrutement déployé avec succès !", ephemeral=True)

    embed = discord.Embed(
        title="STINGER PERFORMANCE MOTORSPORT",
        description=(
            "**Recrutements / Candidatures**\n\n"
            "Pilotes, la Stinger Performance Motorsport recrute de nouveaux talents pour renforcer ses équipages en endurance (LMU) ! 🏎️ 🏁 🏆, et aussi un graphiste pour les communications et livrées.\n\n"
            "Avant d'ouvrir votre dossier de candidature, assurez-vous de correspondre à nos attentes et critères de sélection :\n\n"
            "🎯 **• Le Profil Recherché :**\n"
            "• **Présence & Régularité :** Être présent régulièrement aux sessions d'entraînement et disponible pour les courses.\n"
            "• **Mentalité :** Esprit d'équipe irréprochable, bonne humeur et détente hors piste, mais focus et rigueur une fois en course.\n"
            "• **Investissement :** S'impliquer activement dans la vie de l'équipe, la préparation des courses et le partage d'expériences.\n"
            "• **Période d'essai :** Toute intégration validée sera suivie d'une période d'essai d'un mois afin de s'assurer de la bonne cohésion avec l'équipe.\n\n"
            "📋 **• Prérequis :**\n"
            "• **Driver Ranking :** S1\n"
            "• **Safety Ranking :** P1\n\n"
            "❌ **Si vous ne remplissez pas ces critères, merci de ne pas envoyer de demande.**\n\n"
            "💬 **Comment postuler ?**\n"
            "Si vous avez le profil et l'envie de porter nos couleurs, cliquez sur le bouton ci-dessous pour lancer votre candidature.\n\n"
            "Pour le moment 3 places de disponibles.\n"
            "BEE FAST, STING HARD 🐝"
        ),
        color=discord.Color.from_rgb(114, 13, 148)
    )
    
    await interaction.channel.send(embed=embed, view=RecrutementView())

import os

token = os.getenv("DISCORD_TOKEN")
bot.run(token)