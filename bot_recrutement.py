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
STAFF_CHANNEL_ID = 1557463296326639666  # Ton salon staff
# ID de la catégorie où créer les salons (laisse None si tu veux les créer à la racine)
CATEGORY_CANDIDATURES_ID = None

# OPTIONNEL : Si tu veux cibler un rôle staff précis par son ID, remplace 0 par son ID.
# Si tu laisses 0, seuls les administrateurs du serveur pourront valider/refuser.
STAFF_ROLE_ID = 0
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
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    user = interaction.user

    safe_name = (
        user.name.lower()
        .replace(" ", "-")
        .replace("#", "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    if not safe_name:
      safe_name = f"candidat-{user.id}"
    channel_name = f"candidature-{safe_name}"

    category = (
        guild.get_channel(CATEGORY_CANDIDATURES_ID)
        if CATEGORY_CANDIDATURES_ID
        else None
    )

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }

    try:
      new_channel = await guild.create_text_channel(
          name=channel_name, category=category, overwrites=overwrites
      )

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

      await new_channel.send(
          content=(
              f"Bienvenue {user.mention} ! Voici ton espace de candidature"
              " privé. Le staff de la Stinger Performance Motorsport étudiera"
              " ton dossier ici."
          ),
          embed=embed,
          view=StaffDecisionView(user, new_channel),
      )

      staff_channel = guild.get_channel(STAFF_CHANNEL_ID)
      if staff_channel:
        await staff_channel.send(
            content=(
                f"🔔 **Nouvelle candidature créée :** {new_channel.mention}"
            ),
            embed=embed,
        )

      await interaction.followup.send(
          f"✅ Ta candidature a été enregistrée ! Un salon privé a été créé"
          f" : {new_channel.mention}",
          ephemeral=True,
      )

    except Exception as e:
      print(f"Erreur création salon candidature : {e}")
      await interaction.followup.send(
          "❌ Une erreur s'est produite lors de la création du salon."
          " Contacte un membre du staff.",
          ephemeral=True,
      )


class StaffDecisionView(View):

  def __init__(self, candidate: discord.User, channel: discord.TextChannel):
    super().__init__(timeout=None)
    self.candidate = candidate
    self.channel = channel

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    is_admin = (
        interaction.user.guild_permissions.administrator
        if hasattr(interaction.user, "guild_permissions")
        else False
    )
    has_role = (
        any(role.id == STAFF_ROLE_ID for role in interaction.user.roles)
        if STAFF_ROLE_ID != 0 and hasattr(interaction.user, "roles")
        else False
    )

    if not (is_admin or has_role):
      await interaction.response.send_message(
          "⛔ Seuls les administrateurs ou membres du staff peuvent valider ou"
          " refuser une candidature !",
          ephemeral=True,
      )
      return False
    return True

  @discord.ui.button(
      label="✅ Accepter",
      style=discord.ButtonStyle.success,
      custom_id="btn_accept_candidature_v3",
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
            "Bienvenue à bord et **BEE FAST, STING HARD** 🐝 !"
        ),
        color=discord.Color.green(),
    )

    try:
      await self.candidate.send(embed=embed_accept)
    except discord.HTTPException:
      pass

    await interaction.response.send_message(
        "✅ Candidature validée. Notification envoyée en MP au candidat.",
        ephemeral=True,
    )
    await self.channel.send(
        "🔒 **Candidature acceptée par le staff !** Ce salon peut désormais"
        " être archivé ou supprimé."
    )

  @discord.ui.button(
      label="❌ Refuser",
      style=discord.ButtonStyle.danger,
      custom_id="btn_refuse_candidature_v3",
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
        "❌ Candidature refusée. Notification envoyée en MP au candidat.",
        ephemeral=True,
    )
    await self.channel.send(
        "🔒 **Candidature refusée par le staff.** Ce salon peut être supprimé."
    )


class RecrutementView(View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="Postuler chez SPM",
      style=discord.ButtonStyle.primary,
      custom_id="btn_postuler_spm_v3",
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
