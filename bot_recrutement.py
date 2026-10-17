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
STAFF_CHANNEL_ID = 1557463296326639666  # Ton salon staff principal (#candidatures-recues)
CATEGORY_CANDIDATURES_ID = 1557463296326639666  # Catégorie où créer les salons privés de candidature

# ID de ton rôle Staff (laisse 0 si tu veux autoriser uniquement les Administrateurs)
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

    # Nom du salon
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

    # Récupération de la catégorie configurée
    category = guild.get_channel(CATEGORY_CANDIDATURES_ID)

    # Permissions du salon : PRIVÉ POUR LE STAFF UNIQUEMENT (Le candidat n'a PAS accès)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }

    # Accès au rôle Staff si défini
    if STAFF_ROLE_ID != 0:
      staff_role = guild.get_role(STAFF_ROLE_ID)
      if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        )

    try:
      # Création du salon privé sous la catégorie
      new_channel = await guild.create_text_channel(
          name=channel_name, category=category, overwrites=overwrites
      )

      # Construction de l'embed
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
          name="Disponibilités", value=self.disponibilites.value,
