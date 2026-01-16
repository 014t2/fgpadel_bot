import discord
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
from scraper import obtener_torneos  # Importamos tu lógica de scraping

# 1. Cargar configuración
load_dotenv()
# Obtener el token y el ID del servidor del .env
TOKEN = os.getenv('DISCORD_TOKEN')
ID_SERVIDOR = int(os.getenv('GUILD_ID'))

# --- CONFIGURACIÓN PERSONALIZADA ---
ID_MI_SERVIDOR = ID_SERVIDOR  
CAT_ACTIVOS = "🏆 Torneos Activos"
CAT_ARCHIVO = "📁 Archivo Torneos"

# 2. Configurar el bot e Intents
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True # Necesario para leer comandos como !check

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    for guild in bot.guilds:
        print(f"🟢 Conectado al servidor: {guild.name} ({guild.id})")
    if not actualizar_torneos.is_running():
        actualizar_torneos.start()


# 3. Tarea automática (se ejecuta cada 24 horas)
@tasks.loop(hours=168)
async def actualizar_torneos():
    guild = bot.get_guild(ID_MI_SERVIDOR)
    
    if guild is None:
        print(f"❌ No se encontró el servidor con ID {ID_MI_SERVIDOR}. ¿Está el bot dentro?")
        return

    print("🔍 Revisando torneos en FGPadel...")

    # Asegurar que las categorías existen
    cat_activos = discord.utils.get(guild.categories, name=CAT_ACTIVOS)
    cat_archivo = discord.utils.get(guild.categories, name=CAT_ARCHIVO)

    if not cat_activos: cat_activos = await guild.create_category(CAT_ACTIVOS)
    if not cat_archivo: cat_archivo = await guild.create_category(CAT_ARCHIVO)

    # Obtener lista de torneos del scraper
    lista_torneos = obtener_torneos()
    print(f"DEBUG: El scraper ha devuelto {len(lista_torneos)} torneos.")
    for torneo in lista_torneos:
        # Generar nombre limpio para Discord
        nombre_canal = torneo['nombre'].lower().replace(" ", "-")
        # Eliminar caracteres especiales que no sean letras o guiones
        nombre_canal = "".join(e for e in nombre_canal if e.isalnum() or e == "-")[:90]
        
        print(f"DEBUG: Procesando torneo: {nombre_canal} | Finalizado: {torneo['finalizado']}")

        canal_existente = discord.utils.get(guild.channels, name=nombre_canal)

        if torneo['finalizado']:
            if canal_existente:
                if canal_existente.category != cat_archivo:
                    await canal_existente.edit(category=cat_archivo)
                    await canal_existente.set_permissions(guild.default_role, send_messages=False)
                    print(f"📦 Archivado: {nombre_canal}")
            else:
                # Si el torneo está finalizado pero NO existe el canal, lo creamos directamente en archivo
                await guild.create_text_channel(nombre_canal, category=cat_archivo)
                canal_nuevo = discord.utils.get(guild.channels, name=nombre_canal)
                await canal_nuevo.set_permissions(guild.default_role, send_messages=False)
                print(f"✨ Creado directamente en archivo: {nombre_canal}")
        else:
            if not canal_existente:
                await guild.create_text_channel(nombre_canal, category=cat_activos)
                print(f"✨ Creado: {nombre_canal}")

@bot.command()
async def check(ctx):
    """Comando manual para no esperar 24 horas"""
    if ctx.guild.id != ID_MI_SERVIDOR:
        return
    await ctx.send("⏳ Procesando actualización de torneos...")
    await actualizar_torneos()
    await ctx.send("✅ ¡Proceso completado!")

bot.run(TOKEN)