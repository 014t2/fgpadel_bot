import discord
import os
import re
from discord.ext import commands
from dotenv import load_dotenv
from scraper import obtener_torneos

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ID_SERVIDOR = int(os.getenv('GUILD_ID'))
ID_CANAL_LOGS = int(os.getenv('ID_CANAL_LOGS', 0))

CAT_ACTIVOS = "🏆 Torneos Activos"
CAT_ARCHIVO = "📁 Archivo Torneos"

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    await ejecutar_proceso_semanal()
    await bot.close()

async def ejecutar_proceso_semanal():
    guild = bot.get_guild(ID_SERVIDOR)
    if not guild: return

    cat_activos = discord.utils.get(guild.categories, name=CAT_ACTIVOS) or await guild.create_category(CAT_ACTIVOS)
    cat_archivo = discord.utils.get(guild.categories, name=CAT_ARCHIVO) or await guild.create_category(CAT_ARCHIVO)

    lista_torneos = obtener_torneos()
    creados, archivados = 0, 0

    for torneo in lista_torneos:
        # Limpieza de nombre para canal
        nombre_base = torneo['nombre'].lower().replace(" ", "-")
        nombre_canal = re.sub(r'[^a-z0-9-]', '', nombre_base)[:90]
        
        canal_existente = discord.utils.get(guild.channels, name=nombre_canal)

        if torneo['finalizado']:
            # MOVER A ARCHIVO: Si existe y no está ya allí
            if canal_existente and canal_existente.category.id != cat_archivo.id:
                await canal_existente.edit(category=cat_archivo)
                await canal_existente.set_permissions(guild.default_role, send_messages=False)
                print(f"📦 Archivado: {nombre_canal}")
                archivados += 1
        else:
            # MANTENER O CREAR EN ACTIVOS
            if not canal_existente:
                await guild.create_text_channel(nombre_canal, category=cat_activos)
                creados += 1
                print(f"✨ Creado: {nombre_canal}")
            elif canal_existente.category.id != cat_activos.id:
                # Si el torneo sigue activo pero estaba en archivo, lo devolvemos
                await canal_existente.edit(category=cat_activos)
                await canal_existente.set_permissions(guild.default_role, send_messages=True)
                print(f"🟢 Devuelto a activos: {nombre_canal}")

    if ID_CANAL_LOGS:
        canal_log = bot.get_channel(ID_CANAL_LOGS)
        if canal_log and (creados > 0 or archivados > 0):
            await canal_log.send(f"✅ **Actualización Realizada**\n✨ Torneos nuevos: {creados}\n📦 Torneos archivados: {archivados}")

if __name__ == "__main__":
    bot.run(TOKEN)