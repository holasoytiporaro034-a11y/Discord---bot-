import discord
from discord import app_commands
import os
import logging
import json
from datetime import timedelta, datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Falta la variable de entorno DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ─── CONFIGURACIÓN COMPARTIDA (config.py) ─────────────────────────────────────
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from config import (
    welcome_configs, save_welcome,
    verify_configs,  save_verify,
    logs_configs,    save_logs,
)


# ─── HELPER: enviar log de moderación ─────────────────────────────────────────
async def send_log(guild: discord.Guild, action: str, target: discord.Member,
                   moderator: discord.Member, reason: str = "", extra: str = ""):
    gid = str(guild.id)
    if gid not in logs_configs:
        return
    ch_id = logs_configs[gid].get("channel_id")
    if not ch_id:
        return
    channel = guild.get_channel(int(ch_id))
    if not channel:
        return

    colors = {
        "🔨 Ban":      discord.Color.red(),
        "👢 Kick":     discord.Color.orange(),
        "🔇 Mute":     discord.Color.yellow(),
        "🔊 Unmute":   discord.Color.green(),
        "🗑️ Purge":    discord.Color.blurple(),
        "✅ Verificado": discord.Color.green(),
    }
    embed = discord.Embed(
        title=action,
        color=colors.get(action, discord.Color.greyple()),
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Usuario", value=f"{target.mention} (`{target.id}`)", inline=False)
    embed.add_field(name="Moderador", value=moderator.mention, inline=True)
    if reason:
        embed.add_field(name="Razón", value=reason, inline=True)
    if extra:
        embed.add_field(name="Detalle", value=extra, inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text=f"ID: {target.id}")
    try:
        await channel.send(embed=embed)
    except Exception as e:
        logger.warning(f"No se pudo enviar log: {e}")


# ─── BOTÓN DE VERIFICACIÓN (persistente) ──────────────────────────────────────
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Verificarme",
        style=discord.ButtonStyle.success,
        custom_id="randoom_verify_button"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        gid = str(interaction.guild_id)
        if gid not in verify_configs:
            return await interaction.response.send_message(
                "❌ El sistema de verificación no está configurado.", ephemeral=True
            )
        cfg     = verify_configs[gid]
        role_id = int(cfg["role_id"])
        role    = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message(
                "❌ El rol de verificación ya no existe. Pide a un admin que lo reconfigue.", ephemeral=True
            )
        if role in interaction.user.roles:
            return await interaction.response.send_message(
                "✅ Ya tienes el rol de verificado.", ephemeral=True
            )
        await interaction.user.add_roles(role, reason="Verificación en el servidor")
        await interaction.response.send_message(
            f"✅ ¡Verificado! Se te asignó el rol **{role.name}**.", ephemeral=True
        )
        await send_log(
            interaction.guild, "✅ Verificado",
            interaction.user, interaction.user,
            extra=f"Rol asignado: {role.name}"
        )


# ─── EVENTOS ──────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    client.add_view(VerifyView())   # registrar vista persistente para reinicios
    await tree.sync()
    logger.info(f"Bot conectado como {client.user}")


@client.event
async def on_member_join(member):
    gid = str(member.guild.id)
    if gid not in welcome_configs:
        return
    cfg        = welcome_configs[gid]
    channel_id = cfg.get("channel_id")
    message    = cfg.get("message", "")
    dm_message = cfg.get("dm_message", "")
    if channel_id and message:
        channel = member.guild.get_channel(int(channel_id))
        if channel:
            await channel.send(message.replace("{user}", member.mention))
    if dm_message:
        try:
            await member.send(dm_message.replace("{user}", member.display_name))
        except Exception:
            pass


# ─── PING ─────────────────────────────────────────────────────────────────────
@tree.command(name="ping", description="Muestra la latencia del bot")
async def ping(interaction: discord.Interaction):
    latencia = round(client.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latencia: **{latencia}ms**")


# ─── HOLA ─────────────────────────────────────────────────────────────────────
@tree.command(name="hola", description="El bot te saluda")
async def hola(interaction: discord.Interaction):
    await interaction.response.send_message(f"¡Hola, **{interaction.user.display_name}**!")


# ─── AYUDA ────────────────────────────────────────────────────────────────────
@tree.command(name="ayuda", description="Muestra todos los comandos disponibles")
async def ayuda(interaction: discord.Interaction):
    embed = discord.Embed(title="📋 Comandos — RANDOOM SUPPORT", color=discord.Color.blurple())
    embed.add_field(
        name="⚙️ General",
        value="`/ping` `/hola` `/ayuda`",
        inline=False
    )
    embed.add_field(
        name="🛡️ Moderación",
        value=(
            "`/ban @usuario [razón]`\n"
            "`/kick @usuario [razón]`\n"
            "`/mute @usuario [minutos]`\n"
            "`/purge [cantidad]`"
        ),
        inline=False
    )
    embed.add_field(
        name="📢 Mensajes",
        value=(
            "`/mensaje #canal [texto]`\n"
            "`/embed #canal [título] [desc] [color] [footer]`\n"
            "`/imagen #canal [url] [título]`\n"
            "`/embed_imagen #canal [título] [desc] [url] [footer] [color]`"
        ),
        inline=False
    )
    embed.add_field(
        name="👋 Bienvenidas",
        value="`/bienvenida #canal [mensaje] [dm]`",
        inline=False
    )
    embed.add_field(
        name="🔐 Verificación",
        value="`/setverify #canal @rol [mensaje]` — Configura verificación con botón\n`/quitarverify` — Elimina la verificación",
        inline=False
    )
    embed.add_field(
        name="📋 Logs",
        value="`/setlogs #canal` — Canal de logs de moderación\n`/quitarlogs` — Desactiva los logs",
        inline=False
    )
    embed.set_footer(text="Solo admins pueden usar comandos de configuración.")
    await interaction.response.send_message(embed=embed)


# ─── PURGE ────────────────────────────────────────────────────────────────────
@tree.command(name="purge", description="Elimina mensajes del canal actual")
@app_commands.describe(cantidad="Cantidad de mensajes a eliminar (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, cantidad: int):
    if cantidad < 1 or cantidad > 100:
        return await interaction.response.send_message(
            "❌ Especifica entre **1** y **100** mensajes.", ephemeral=True
        )
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=cantidad)
    await interaction.followup.send(
        f"✅ Se eliminaron **{len(deleted)}** mensajes.", ephemeral=True
    )
    await send_log(
        interaction.guild, "🗑️ Purge",
        interaction.user, interaction.user,
        extra=f"{len(deleted)} mensajes eliminados en {interaction.channel.mention}"
    )


# ─── KICK ─────────────────────────────────────────────────────────────────────
@tree.command(name="kick", description="Expulsa a un miembro del servidor")
@app_commands.describe(usuario="Miembro a expulsar", razon="Razón de la expulsión")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón"):
    if usuario == interaction.user:
        return await interaction.response.send_message("❌ No puedes expulsarte a ti mismo.", ephemeral=True)
    if usuario.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            "❌ No puedes expulsar a alguien con igual o mayor rango.", ephemeral=True
        )
    await usuario.kick(reason=razon)
    embed = discord.Embed(title="👢 Miembro expulsado", color=discord.Color.orange())
    embed.add_field(name="Usuario", value=f"{usuario} (`{usuario.id}`)", inline=False)
    embed.add_field(name="Razón", value=razon, inline=False)
    embed.add_field(name="Moderador", value=interaction.user.mention, inline=False)
    embed.set_thumbnail(url=usuario.display_avatar.url)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, "👢 Kick", usuario, interaction.user, reason=razon)


# ─── BAN ──────────────────────────────────────────────────────────────────────
@tree.command(name="ban", description="Banea a un miembro del servidor")
@app_commands.describe(usuario="Miembro a banear", razon="Razón del ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón"):
    if usuario == interaction.user:
        return await interaction.response.send_message("❌ No puedes banearte a ti mismo.", ephemeral=True)
    if usuario.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            "❌ No puedes banear a alguien con igual o mayor rango.", ephemeral=True
        )
    await usuario.ban(reason=razon, delete_message_days=0)
    embed = discord.Embed(title="🔨 Miembro baneado", color=discord.Color.red())
    embed.add_field(name="Usuario", value=f"{usuario} (`{usuario.id}`)", inline=False)
    embed.add_field(name="Razón", value=razon, inline=False)
    embed.add_field(name="Moderador", value=interaction.user.mention, inline=False)
    embed.set_thumbnail(url=usuario.display_avatar.url)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, "🔨 Ban", usuario, interaction.user, reason=razon)


# ─── MUTE ─────────────────────────────────────────────────────────────────────
@tree.command(name="mute", description="Silencia a un miembro con timeout")
@app_commands.describe(
    usuario="Miembro a silenciar",
    minutos="Duración en minutos (máx 40320 = 4 semanas)"
)
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, usuario: discord.Member, minutos: int = 10):
    if minutos < 1 or minutos > 40320:
        return await interaction.response.send_message(
            "❌ El tiempo debe estar entre **1** y **40320** minutos.", ephemeral=True
        )
    if usuario.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            "❌ No puedes silenciar a alguien con igual o mayor rango.", ephemeral=True
        )
    until = datetime.now(timezone.utc) + timedelta(minutes=minutos)
    await usuario.timeout(until, reason=f"Silenciado por {interaction.user}")
    embed = discord.Embed(title="🔇 Miembro silenciado", color=discord.Color.yellow())
    embed.add_field(name="Usuario", value=f"{usuario} (`{usuario.id}`)", inline=False)
    embed.add_field(name="Duración", value=f"**{minutos}** minuto(s)", inline=False)
    embed.add_field(name="Moderador", value=interaction.user.mention, inline=False)
    embed.set_thumbnail(url=usuario.display_avatar.url)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, "🔇 Mute", usuario, interaction.user,
                   extra=f"Duración: {minutos} minuto(s)")


# ─── BIENVENIDA ───────────────────────────────────────────────────────────────
@tree.command(name="bienvenida", description="Configura el mensaje de bienvenida automática")
@app_commands.describe(
    canal="Canal donde se enviarán las bienvenidas",
    mensaje="Mensaje en el canal (usa {user} para mencionar)",
    dm="Mensaje privado al nuevo miembro (opcional)"
)
@app_commands.checks.has_permissions(manage_guild=True)
async def bienvenida(interaction: discord.Interaction, canal: discord.TextChannel,
                     mensaje: str, dm: str = ""):
    gid = str(interaction.guild_id)
    welcome_configs[gid] = {"channel_id": str(canal.id), "message": mensaje, "dm_message": dm}
    save_welcome(welcome_configs)
    embed = discord.Embed(title="✅ Bienvenida configurada", color=discord.Color.green())
    embed.add_field(name="Canal", value=canal.mention, inline=False)
    embed.add_field(name="Mensaje", value=mensaje, inline=False)
    if dm:
        embed.add_field(name="DM", value=dm, inline=False)
    embed.set_footer(text="Usa {user} para mencionar al nuevo miembro.")
    await interaction.response.send_message(embed=embed)


# ─── SETVERIFY ────────────────────────────────────────────────────────────────
@tree.command(name="setverify", description="Configura el sistema de verificación con botón")
@app_commands.describe(
    canal="Canal donde aparecerá el botón de verificación",
    rol="Rol que se asignará al verificarse",
    mensaje="Texto del mensaje de verificación (opcional)"
)
@app_commands.checks.has_permissions(manage_guild=True)
async def setverify(interaction: discord.Interaction, canal: discord.TextChannel,
                    rol: discord.Role, mensaje: str = "Haz clic en el botón para verificarte y acceder al servidor."):
    gid = str(interaction.guild_id)
    verify_configs[gid] = {
        "channel_id": str(canal.id),
        "role_id":    str(rol.id),
        "message":    mensaje
    }
    save_verify(verify_configs)

    emb = discord.Embed(
        title="🔐 Verificación",
        description=mensaje,
        color=0x3CFFA0
    )
    emb.set_footer(text="Pulsa el botón para obtener acceso al servidor.")
    await canal.send(embed=emb, view=VerifyView())

    reply = discord.Embed(title="✅ Verificación configurada", color=discord.Color.green())
    reply.add_field(name="Canal", value=canal.mention, inline=True)
    reply.add_field(name="Rol",   value=rol.mention,   inline=True)
    reply.add_field(name="Mensaje", value=mensaje,     inline=False)
    await interaction.response.send_message(embed=reply)


# ─── QUITARVERIFY ─────────────────────────────────────────────────────────────
@tree.command(name="quitarverify", description="Desactiva el sistema de verificación")
@app_commands.checks.has_permissions(manage_guild=True)
async def quitarverify(interaction: discord.Interaction):
    gid = str(interaction.guild_id)
    if gid in verify_configs:
        del verify_configs[gid]
        save_verify(verify_configs)
    await interaction.response.send_message("✅ Sistema de verificación desactivado.", ephemeral=True)


# ─── SETLOGS ──────────────────────────────────────────────────────────────────
@tree.command(name="setlogs", description="Configura el canal de logs de moderación")
@app_commands.describe(canal="Canal donde se registrarán las acciones de moderación")
@app_commands.checks.has_permissions(manage_guild=True)
async def setlogs(interaction: discord.Interaction, canal: discord.TextChannel):
    gid = str(interaction.guild_id)
    logs_configs[gid] = {"channel_id": str(canal.id)}
    save_logs(logs_configs)
    embed = discord.Embed(title="✅ Canal de logs configurado", color=discord.Color.green())
    embed.add_field(name="Canal", value=canal.mention, inline=False)
    embed.add_field(
        name="Se registrarán",
        value="🔨 Bans · 👢 Kicks · 🔇 Mutes · 🗑️ Purges · ✅ Verificaciones",
        inline=False
    )
    await interaction.response.send_message(embed=embed)


# ─── QUITARLOGS ───────────────────────────────────────────────────────────────
@tree.command(name="quitarlogs", description="Desactiva el canal de logs de moderación")
@app_commands.checks.has_permissions(manage_guild=True)
async def quitarlogs(interaction: discord.Interaction):
    gid = str(interaction.guild_id)
    if gid in logs_configs:
        del logs_configs[gid]
        save_logs(logs_configs)
    await interaction.response.send_message("✅ Logs de moderación desactivados.", ephemeral=True)


# ─── MENSAJE ──────────────────────────────────────────────────────────────────
@tree.command(name="mensaje", description="Envía un mensaje en un canal como el bot")
@app_commands.describe(canal="Canal donde enviar el mensaje", texto="Texto del mensaje")
@app_commands.checks.has_permissions(manage_messages=True)
async def mensaje(interaction: discord.Interaction, canal: discord.TextChannel, texto: str):
    await canal.send(texto)
    await interaction.response.send_message(f"✅ Mensaje enviado en {canal.mention}", ephemeral=True)


# ─── EMBED ────────────────────────────────────────────────────────────────────
@tree.command(name="embed", description="Envía un embed en un canal")
@app_commands.describe(
    canal="Canal destino", titulo="Título", descripcion="Descripción",
    color="Color hex sin # (ej: ff5733)", footer="Footer (opcional)"
)
@app_commands.checks.has_permissions(manage_messages=True)
async def embed_cmd(interaction: discord.Interaction, canal: discord.TextChannel,
                    titulo: str, descripcion: str, color: str = "3cffa0", footer: str = ""):
    try:
        color_int = int(color.lstrip("#"), 16)
    except ValueError:
        color_int = 0x3CFFA0
    emb = discord.Embed(title=titulo, description=descripcion, color=color_int)
    if footer:
        emb.set_footer(text=footer)
    await canal.send(embed=emb)
    await interaction.response.send_message(f"✅ Embed enviado en {canal.mention}", ephemeral=True)


# ─── IMAGEN ───────────────────────────────────────────────────────────────────
@tree.command(name="imagen", description="Envía una imagen desde URL en un canal")
@app_commands.describe(canal="Canal destino", url="URL directa de la imagen", titulo="Título (opcional)")
@app_commands.checks.has_permissions(manage_messages=True)
async def imagen(interaction: discord.Interaction, canal: discord.TextChannel,
                 url: str, titulo: str = ""):
    emb = discord.Embed(color=0x3CFFA0)
    if titulo:
        emb.title = titulo
    emb.set_image(url=url)
    await canal.send(embed=emb)
    await interaction.response.send_message(f"✅ Imagen enviada en {canal.mention}", ephemeral=True)


# ─── EMBED CON IMAGEN ─────────────────────────────────────────────────────────
@tree.command(name="embed_imagen", description="Embed completo con imagen URL y footer")
@app_commands.describe(
    canal="Canal destino", titulo="Título", descripcion="Descripción",
    imagen_url="URL de la imagen", footer="Footer (opcional)", color="Color hex sin #"
)
@app_commands.checks.has_permissions(manage_messages=True)
async def embed_imagen(interaction: discord.Interaction, canal: discord.TextChannel,
                       titulo: str, descripcion: str, imagen_url: str,
                       footer: str = "", color: str = "3cffa0"):
    try:
        color_int = int(color.lstrip("#"), 16)
    except ValueError:
        color_int = 0x3CFFA0
    emb = discord.Embed(title=titulo, description=descripcion, color=color_int)
    emb.set_image(url=imagen_url)
    if footer:
        emb.set_footer(text=footer)
    await canal.send(embed=emb)
    await interaction.response.send_message(
        f"✅ Embed con imagen enviado en {canal.mention}", ephemeral=True
    )


# ─── MANEJADOR DE ERRORES ─────────────────────────────────────────────────────
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ No tienes permisos para usar este comando.", ephemeral=True
        )
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message(
            "❌ El bot no tiene los permisos necesarios.", ephemeral=True
        )
    else:
        logger.error(f"Error en comando: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocurrió un error inesperado.", ephemeral=True)


if __name__ == "__main__":
    client.run(TOKEN, reconnect=True)
