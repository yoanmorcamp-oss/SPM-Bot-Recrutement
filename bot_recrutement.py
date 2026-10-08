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
STAFF_CHANNEL_ID = 1557463296326639666
# ===============================================


class CandidatureModal(Modal, title="Candidature SPM"):

  def __init__(self):
    super().__init__()

  nom_age = TextInput(
      label="Nom, Prénom & Âge",
      placeholder="ex: Morcamp Yoan, 50 ans",
      required=True,
  )
  experience = TextInput(
      label="Expérience en simracing (LMU, etc.)",
      placeholder="Ton parcours, iRating/Driver Ranking...",
      style=discord.TextStyle.paragraph,
      required=True,
  )
  vehicules = TextInput(
      label="Classes maîtrisées (Hypercar, LMP2, LMGT3)",
      placeholder="Quelles catégories tu pilotes le mieux ?",
      required=True,
  )
  disponibilites = TextInput(
      label="Disponibilités & Présence",
      placeholder="Tes jours d'entraînement, dispo courses...",
      required=True,
  )
  motivations = TextInput(
      label="Pourquoi rejoindre Stinger Performance ?",
      placeholder="Tes motivations et ton état d'esprit...",
      style=discord.TextStyle.paragraph,
      required=True,
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
        name="Classes maîtrisées", value=self.vehicules.value, inline=False
    )
    embed.add_field(
        name="Disponibilités", value=self.disponibilites.value, inline=False
    )
    embed.add_field(
        name="Motivations", value=self.motivations.value, inline=False
    )

    if staff_channel:
      await staff_channel.send(
          embed=embed, view=StaffDecisionView(interaction.user)
      )
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


class StaffDecisionView(View):

  def __init__(self, candidate: discord.User):
    super().__init__(timeout=None)
    self.candidate = candidate

  @discord.ui.button(
      label="✅ Accepter",
      style=discord.ButtonStyle.success,
      custom_id="btn_accept_candidature",
  )
  async def accepter(
      self, interaction: discord.Interaction, button: discord.Button
  ):
    for child in self.children:
      child.disabled = True
    await interaction.message.edit(view=self)

    today = datetime.now()
    end_date = today + timedelta(days=30)
    date_today_str = today.strftime("%d/%m/%Y")
    date_end_str = end_date.strftime("%d/%m/%Y")

    embed_accept = discord.Embed(
        title="🎉 Félicitations ! Candidature retenue - SPM",
        description=(
            "Bonjour !\n\nLe staff de la **Stinger Performance Motorsport** a"
            " examiné ta candidature avec attention et a le plaisir de"
            " t'annoncer qu'elle est **validée** !\n\n"
            "🏎️ **Début de ta période d'essai :**\n"
            f"Ta période d'essai officielle d'un mois commence dès aujourd'hui"
            f" (**{date_today_str}**) et se terminera le **{date_end_str}**.\n"
            "C'est l'occasion de partager nos sessions d'entraînement, de"
            " trouver tes repères en piste et de confirmer notre belle cohésion"
            " d'équipe.\n\n"
            "Bienvenue à bord et **BEE FAST, STING HARD** 🐝 !"
        ),
        color=discord.Color.green(),
    )

    try:
      await self.candidate.send(embed=embed_accept)
    except discord.HTTPException:
      pass

    await interaction.response.send_message(
        f"✅ Candidature de {self.candidate.mention} acceptée. Le candidat a"
        " reçu son embed de validation en MP.",
        ephemeral=True,
    )

  @discord.ui.button(
      label="❌ Refuser",
      style=discord.ButtonStyle.danger,
      custom_id="btn_refuse_candidature",
  )
  async def refuser(
      self, interaction: discord.Interaction, button: discord.Button
  ):
    for child in self.children:
      child.disabled = True
    await interaction.message.edit(view=self)

    embed_refuse = discord.Embed(
        title="Mise à jour concernant ta candidature - SPM",
        description=(
            "Bonjour,\n\nNous te remercions pour l'intérêt que tu portes à la"
            " **Stinger Performance Motorsport**.\n"
            "Après étude de ton profil, nous ne pouvons malheureusement pas"
            " donner suite à ta candidature pour le moment.\n\n"
            "Nous te souhaitons une excellente continuation sur les pistes !"
        ),
        color=discord.Color.red(),
    )

    try:
      await self.candidate.send(embed=embed_refuse)
    except discord.HTTPException:
      pass

    await interaction.response.send_message(
        f"❌ Candidature de {self.candidate.mention} refusée. Le candidat a"
        " reçu son embed de refus en MP.",
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
    # Envoi direct du modal pour éviter le timeout de 3 secondes de Discord
    await interaction.response.send_modal(CandidatureModal())


class MyClient(discord.Client):

  def __init__(self):
    super().__init__(intents=discord.Intents.default())
    self.tree = app_commands.CommandTree(self)

  async def setup_hook(self):
    # Enregistrement persistant des vues pour qu'elles fonctionnent même après un redémarrage du bot
    self.add_view(RecrutementView())
    self.add_view(
        StaffDecisionView(None)
    )  # Permet de garder les boutons staff actifs
    await self.tree.sync()
    print("Commandes synchronisées et vues persistantes enregistrées.")


client = MyClient()


@client.event
async def on_ready():
  print(f"Connecté en tant que {client.user} (ID: {client.user.id})")
  print("Le bot est prêt et opérationnel !")


@client.tree.command(
    name="deploy_recrutement",
    description="Poste le message et le bouton de recrutement SPM",
)
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
# CONFIGURATION SERVEUR WEB (FLASK) & GUNICORN
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


if not any(t.name == "DiscordThread" for t in threading.enumerate()):
  discord_thread = threading.Thread(
      target=run_discord, name="DiscordThread", daemon=True
  )
  discord_thread.start()
