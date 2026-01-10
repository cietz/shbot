
"""
🦈 SharkClub Discord Bot - Ranking Cog
Sistema de leaderboard diário automático
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone, time
import config
from database.queries import UserQueries

# Horário que o leaderboard será postado (10:00 da manhã BRT = 13:00 UTC)
LEADERBOARD_TIME = time(hour=13, minute=0, second=0)

class RankingCog(commands.Cog):
    """Sistema de Ranking Diário"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def cog_unload(self):
        """Cancela tasks ao descarregar cog"""
        self.daily_leaderboard.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Inicia task de ranking diário"""
        if not self.daily_leaderboard.is_running():
            print("⏳ Iniciando agendador de Ranking Diário...")
            self.daily_leaderboard.start()
            print("✅ Ranking Diário agendado para 10:00 BRT")
    
    @tasks.loop(time=LEADERBOARD_TIME)
    async def daily_leaderboard(self):
        """Task que roda todos os dias para postar o ranking"""
        await self.post_leaderboard()
    
    async def post_leaderboard(self):
        """Lógica principal de postagem do leaderboard"""
        print("📊 Gerando Leaderboard Diário...")
        
        try:
            # Busca canal de ranking
            channel_id = config.CHANNEL_IDS.get("ranking")
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                # Tenta fetch se não estiver no cache
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except:
                    print(f"⚠️ Canal de Ranking não encontrado (ID: {channel_id})")
                    return
            
            # Busca top 10 usuários
            top_users = UserQueries.get_top_users(limit=10)
            
            if not top_users:
                print("⚠️ Nenhum usuário encontrado para o ranking.")
                return

            # Cria Embed
            embed = discord.Embed(
                title="🏆 LEADERBOARD DIÁRIO | SHARK CLUB 🦈",
                description="Os maiores predadores do oceano hoje!",
                color=config.EMBED_COLOR_GOLD
            )
            embed.set_thumbnail(url="https://media1.tenor.com/m/v8hVDs0LSIoAAAAd/shark-attack.gif")
            
            leaderboard_text = ""
            for i, user in enumerate(top_users, 1):
                user_id = user['user_id']
                xp = user['xp']
                level = user.get('level', 1)
                
                # Medalhas para top 3
                if i == 1:
                    rank_icon = "🥇"
                elif i == 2:
                    rank_icon = "🥈"
                elif i == 3:
                    rank_icon = "🥉"
                else:
                    rank_icon = f"**#{i}**"
                
                # Tenta pegar nome do usuário no Discord
                try:
                    # Tenta pegar do cache primeiro
                    member = channel.guild.get_member(user_id)
                    if not member:
                        member = await channel.guild.fetch_member(user_id)
                    username = member.display_name
                except:
                    username = user.get('username', f"Tubarão #{user_id}")
                
                # Formatação da linha
                leaderboard_text += f"{rank_icon} **{username}** • Nível {level} • `{xp:,} XP`\n"

            embed.add_field(name="🔥 TOP 10 MAIS EXPERIENTES", value=leaderboard_text, inline=False)
            
            embed.set_footer(text="Continue interagindo para subir no ranking! 🚀")
            embed.timestamp = datetime.now(timezone.utc)
            
            # Limpa mensagens antigas do bot no canal (opcional, para manter limpo, mas perigoso se deletar msg errada)
            # Vamos apenas enviar a nova mensagem por enquanto para ser seguro.
            
            await channel.send(embed=embed)
            print("✅ Leaderboard Diário postado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao postar Leaderboard: {e}")

    def is_admin():
        """Decorator para verificar permissão de admin"""
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    @app_commands.command(name="admin-force-leaderboard", description="[ADMIN] Forçar postagem do leaderboard agora")
    @is_admin()
    async def force_leaderboard(self, interaction: discord.Interaction):
        """Comando manual para testar o leaderboard"""
        await interaction.response.defer(ephemeral=True)
        await self.post_leaderboard()
        await interaction.followup.send("✅ Leaderboard disparado manualmente!", ephemeral=True)

    @force_leaderboard.error
    async def admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("❌ Apenas admins podem usar este comando.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RankingCog(bot))
