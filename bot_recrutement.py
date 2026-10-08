from datetime import datetime, timedelta
import os
import threading
import discord
from discord import app_commands
from discord.ui import Button, Modal, TextInput, View
from flask import Flask

# ===============================================
# CONFIGURATION
# ===============================================
STAFF_CHANNEL_ID = (
    1557463296326639666  # Ton salon staff/admin enregistré
)
GUILD_ID = discord.Object(
    id=1222994281334177842
)  # Ton serveur Discord SPM
# ===============================================


class CandidatureModal(Modal, title="Candidature SPM"):
  nom_age = TextInput(
      label="Nom, Prénom & Âge",
      placeholder="ex: Morcamp Yoan, 50 ans",
  )
  experience = TextInput(
      label="Expérience en simracing (LMU, etc.)",
      placeholder="Décris ton parcours...",
      style=discord.TextStyle.paragraph,
  )
  motivations = TextInput(
      label="Pourquoi rejoindre Stinger Performance ?",
      placeholder="Tes motivations...",
      style=discord.TextStyle.paragraph,
  )

  async def on_submit(self, interaction: discord.Interaction):
    staff_channel = interaction.guild.get_channel(STAFF_CHANNEL_ID)

    embed = discord.Embed(
        title="📥 Nouvelle Candidature SPM",
        color=discord.Color.from_rgb(114, 13, 148),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(
        name="Candidat", value=interaction.user.mention, inline=False
    )
    embed.add_field(
        name="Nom, Prénom & Âge", value=self.nom_age.value, inline=False
    )
    embed.add_field(
        name="Expérience", value=self.experience.value, inline=False
    )
    embed.add_field(
        name="Motivations", value=self.motivations.value, inline=False
    )

    if staff_channel:
      await staff_channel.send(embed=embed)
      await interaction.response.send_message(
          "✅ Ta candidature a bien été envoyée au staff de Stinger"
          " Performance Motorsport ! Nous allons l'étudier rapidement.",
          ephemeral=True,
      )
    else:
      await interaction.response.send_message(
          "❌ Erreur : Le salon staff est introuvable. Contacte un administrateur"
          " directement.",
          ephemeral=True,
      )


class RecrutementView(View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="Postuler chez SPM",
      style=discord.ButtonStyle.primary,
      custom_id="btn_postuler_spm",
  )
  async def postuler(
      self, interaction: discord.Interaction, button: discord.Button
  ):
    await interaction.response.send_modal(CandidatureModal())


class MyClient(discord.Client):

  def __init__(self):
    super().__init__(intents=discord.Intents.default())
    self.tree = app_commands.CommandTree(self)

  async def setup_hook(self):
    self.add_view(RecrutementView())
    await self.tree.sync(guild=GUILD_ID)
    print("Commandes synchronisées et vue persistante enregistrée.")


client = MyClient()


@client.event
async def on_ready():
  print(f"Connecté en tant que {client.user} (ID: {client.user.id})")
  print("Le bot est prêt et opérationnel !")


@client.tree.command(
    name="deploy_recrutement",
    description="Poste le message et le bouton de recrutement SPM",
    guild=GUILD_ID,
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_recrutement(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Déploiement du message de recrutement en cours...", ephemeral=True
  )

  embed = discord.Embed(
      title="Stinger Performance Motorsport - Recrutement",
      description=(
          "**Recrutements / Candidatures**\n\n"
          "Pilotes, la Stinger Performance Motorsport recrute de nouveaux"
          " talents pour renforcer ses équipages en endurance (LMU) ! 🏎️ 🏁"
          " 🏆\n"
          "Avant d'ouvrir votre dossier de candidature, assurez-vous de"
          " correspondre à nos attentes et critères de sélection :\n"
          "🎯 **Le Profil Recherché :**\n"
          "• **Présence & Régularité :** Être présent régulièrement aux"
          " sessions d'entraînement et disponible pour les courses.\n"
          "• **Mentalité :** Esprit d'équipe irréprochable, bonne humeur et"
          " détente hors piste, mais focus et rigueur une fois en course.\n"
          "• **Investissement :** S'impliquer activement dans la vie de"
          " l'équipe, la préparation des courses et le partage"
          " d'expériences.\n"
          "• **Période d'essai :** Toute intégration validée sera suivie"
          " d'une période d'essai d'un mois afin de s'assurer de la bonne"
          " cohésion avec l'équipe.\n"
          "📋 **Prérequis :**\n"
          "• **Driver Ranking :** S1\n"
          "• **Safety Ranking :** P1\n"
          "❌ **Si vous ne remplissez pas ces critères, merci de ne pas"
          " envoyer de demande.**\n\n"
          "💬 **Comment postuler ?**\n"
          "Si vous avez le profil et l'envie de porter nos couleurs, cliquez"
          " sur le bouton ci-dessous pour lancer votre candidature.\n"
          "Pour le moment 3 places de disponibles.\n"
          '*"BEE FAST, STING HARD"*\n'
      ),
      color=discord.Color.from_rgb(114, 13, 148),
  )

  await interaction.channel.send(embed=embed, view=RecrutementView())


# ===============================================
# CONFIGURATION SERVEUR WEB (FLASK) POUR RENDER
# ===============================================
app = Flask("")


@app.route("/")
def home():
  return "Bot SPM Recrutement est en ligne !"


def run_discord():
  token = os.getenv("DISCORD_TOKEN")
  if not token:
    print("Erreur : Le token Discord est introuvable dans les variables d'env.")
    return
  client.run(token)


# Lancement automatique du thread Discord dès que Gunicorn charge le fichier
if not any(t.name == "DiscordThread" for t in threading.enumerate()):
  discord_thread = threading.Thread(
      target=run_discord, name="DiscordThread", daemon=True
  )
  discord_thread.start()
