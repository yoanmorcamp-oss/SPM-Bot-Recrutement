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
STAFF_CHANNEL_ID = 1557463296326639666  # Ton salon staff principal
# ID de la catégorie où les salons de candidature vont se créer (optionnel, mets l'ID ou laisse None)
CATEGORY_CANDIDATURES_ID = None
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
    # On accuse réception immédiatement pour éviter le timeout
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    user = interaction.user

    # Nettoyage du nom pour créer un salon propre (ex: candidature-yoan-morcamp)
    safe_name = (
        user.name.lower()
        .replace(" ", "-")
        .replace("#", "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    channel_name = f"candidature-{safe_name}"

    # Récupération de la catégorie si elle est définie
    category = (
        guild.get_channel(CATEGORY_CANDIDATURES_ID)
        if CATEGORY_CANDIDATURES_ID
        else None
    )

    # Définition des permissions du salon (Privé : visible uniquement par le staff et le candidat)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }

    # Si tu as un rôle Staff, tu peux aussi lui donner accès automatiquement (remplace par l'ID de ton rôle staff si besoin)
    # staff_role = guild.get_role(ID_ROLE_STAFF)
    # if staff_role:
    #     overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    try:
      # Création automatique du salon
      new_channel = await guild.create_text_channel(
          name=channel_name, category=category, overwrites=overwrites
      )

      # Construction de l'embed de candidature
      embed = discord.Embed(
          title=f"📥 Candidature de {user.display_name}",
          color=discord.Color.from_rgb(114, 13, 148),
          timestamp=datetime.utcnow(),
      )
      embed.add_field(name="Candidat", value=user.mention, inline=False)
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

      # Envoi de l'embed et des boutons de décision dans ce nouveau salon dédié
      await new_channel.send(
          content=(
              f"Bienvenue {user.mention} ! Voici ton espace de candidature"
              " dédié. Le staff va l'étudier très rapidement ici."
          ),
          embed=embed,
          view=StaffDecisionView(user, new_channel),
      )

      # Message de confirmation discret au candidat
      await interaction.followup.send(
          f"✅ Ta candidature a bien été envoyée ! Un salon privé a été créé"
          f" pour toi : {new_channel.mention}.",
          ephemeral=True,
      )

    except Exception as e:
      await interaction.followup.send(
          "❌ Une erreur est survenue lors de la création de ton salon de"
          " candidature. Contacte un admin.",
          ephemeral=True,
      )
      print(f"Erreur création salon : {e}")


class StaffDecisionView(View):

  def __init__(self, candidate: discord.User, channel: discord.TextChannel):
    super().__init__(timeout=None)
    self.candidate = candidate
    self.channel = channel

  @discord.ui.button(
      label="✅ Accepter",
      style=discord.ButtonStyle.success,
      custom_id="btn_accept_candidature_v2",
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
            f" (**{date_today_str}**) et se terminera le **{date_end_str}**.\n\n"
            "Bienvenue à bord et **BEE FAST, STING HARD** *{\n"
        ),
        color=discord.Color.green(),
    )

    try:
      await self.candidate.send(embed=embed_accept)
    except discord.HTTPException:
      pass

    await interaction.response.send_message(
        f"✅ Candidature acceptée. Le salon va être archivé/supprimé ou"
        " conservé selon vos préférences.",
        ephemeral=True,
    )
    await self.channel.send(
        "🔒 **Candidature validée !** Ce salon sera géré par le staff."
    )

  @discord.ui.button(
      label="❌ Refuser",
      style=discord.ButtonStyle.danger,
      custom_id="btn_refuse_candidature_v2",
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
        "❌ Candidature refusée.", ephemeral=True
    )
    await self.channel.send(
        "🔒 **Candidature refusée.** Le salon pourra être supprimé par le"
        " staff."
    )


class RecrutementView(View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="Postuler chez SPM",
      style=discord.ButtonStyle.primary,
      custom_id="btn_postuler_spm_unique_v2",
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
    await self.tree.sync()
    print("Vue persistante enregistrée et commandes synchronisées.")


client = MyClient()


@client.event
async def on_ready():
  print(f"Connecté en tant que {client.user} (ID: {client.user.id})")


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
          "Clique sur le bouton ci-dessous pour lancer ton questionnaire de"
          " candidature. Un salon privé sera automatiquement créé pour ton"
          " dossier !\n\n"
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
    return
  client.run(token)


if not any(t.name == "DiscordThread" for t in threading.enumerate()):
  discord_thread = threading.Thread(
      target=run_discord, name="DiscordThread", daemon=True
  )
  discord_thread.start()
