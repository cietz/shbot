"""
🦈 SharkClub Discord Bot
Bot de gamificação para Discord focado em engajamento saudável
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import threading

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

class SharkBot(commands.Bot):
    """Bot principal do SharkClub"""
    
    def __init__(self):
        super().__init__(
            command_prefix='!',  # Prefix para comandos legacy (não usado)
            intents=intents,
            application_id=os.getenv('DISCORD_APP_ID')
        )
        self.initial_extensions = [
            'cogs.auto_setup',  # Deve ser carregado primeiro para setup automático
            'cogs.profile',
            'cogs.checkin',
            'cogs.minigames',
            'cogs.ranking',
            'cogs.missions',

            'cogs.activity',
            'cogs.events',
            'cogs.shop',
            'cogs.notifications',  # Processa notificações do Dashboard
        ]
    
    async def setup_hook(self):
        """Configuração inicial do bot"""
        print("🦈 Iniciando SharkClub Bot...")
        
        # Carrega cogs
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"   ✅ Carregado: {ext}")
            except Exception as e:
                print(f"   ❌ Erro ao carregar {ext}: {e}")
    
    async def on_ready(self):
        """Evento quando o bot está pronto"""
        print("🔄 Sincronizando comandos...")
        
        # Sincroniza comandos APENAS por servidor (sem duplicação global)
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"   ✅ Comandos sincronizados para: {guild.name}")
            except Exception as e:
                print(f"   ❌ Erro ao sincronizar para {guild.name}: {e}")
        
        print(f"\n{'='*50}")
        print(f"🦈 SharkClub Bot Online!")
        print(f"   Logado como: {self.user.name}")
        print(f"   ID: {self.user.id}")
        print(f"   Servidores: {len(self.guilds)}")
        print(f"{'='*50}\n")
        
        # Define status do bot
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="o oceano do tráfego 🌊"
            )
        )
    
    async def on_guild_join(self, guild: discord.Guild):
        """Evento quando o bot entra em um servidor"""
        print(f"🎉 Entrou no servidor: {guild.name} (ID: {guild.id})")
    
    async def on_command_error(self, ctx, error):
        """Handler global de erros para comandos prefix"""
        if isinstance(error, commands.CommandNotFound):
            return
        print(f"❌ Erro: {error}")


async def setup_global_error_handler(bot: commands.Bot):
    """Configura handler de erro global para slash commands"""
    
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handler global de erros para slash commands"""
        error_msg = str(error)
        print(f"❌ Erro no comando /{interaction.command.name if interaction.command else 'unknown'}: {error_msg}")
        
        # Tenta responder com erro
        try:
            embed = discord.Embed(
                title="❌ Ocorreu um erro",
                description=f"Houve um problema ao executar o comando.\n\n```{error_msg[:200]}```",
                color=0xFF0000
            )
            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass  # Se falhar em responder, ignora


async def main():
    """Função principal"""
    # Verifica token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN não encontrado no .env!")
        print("   Copie .env.example para .env e configure o token.")
        return
    
    # Inicializa banco de dados
    from database.connection import init_database
    db_ok = await init_database()
    
    if not db_ok:
        print("\n⚠️  IMPORTANTE: Configure as tabelas no Supabase!")
        print("   Execute o SQL disponível em database/connection.py")
        print("   no SQL Editor do Supabase Dashboard.\n")
    
    # Inicia a Dashboard em thread separada
    def run_dashboard():
        try:
            from dashboard.app import app
            dashboard_port = int(os.getenv('DASHBOARD_PORT', 5000))
            print(f"🌐 Dashboard iniciando na porta {dashboard_port}...")
            # Desabilita logs do werkzeug para não poluir console
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            app.run(host='0.0.0.0', port=dashboard_port, debug=False, use_reloader=False)
        except Exception as e:
            print(f"❌ Erro ao iniciar Dashboard: {e}")
    
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    print("✅ Dashboard thread iniciada!")
    
    # Inicia o bot
    bot = SharkBot()
    
    # Configura handler de erro global
    await setup_global_error_handler(bot)
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Token inválido! Verifique seu DISCORD_TOKEN no .env")
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
