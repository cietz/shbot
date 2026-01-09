"""
🦈 SharkClub Discord Bot - Notifications Cog
Processa notificações pendentes do Dashboard e envia DMs aos usuários
"""

import discord
from discord.ext import commands, tasks
import config
from database.queries import NotificationQueries


class NotificationsCog(commands.Cog):
    """Processa notificações do Dashboard"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.process_notifications.start()
    
    def cog_unload(self):
        self.process_notifications.cancel()
    
    @tasks.loop(seconds=30)
    async def process_notifications(self):
        """Processa notificações pendentes a cada 30 segundos"""
        try:
            notifications = NotificationQueries.get_pending_notifications(limit=10)
            
            for notif in notifications:
                await self.send_notification(notif)
                
        except Exception as e:
            print(f"⚠️ Erro ao processar notificações: {e}")
    
    @process_notifications.before_loop
    async def before_process_notifications(self):
        await self.bot.wait_until_ready()
    
    async def send_notification(self, notif: dict):
        """Envia notificação para o usuário via DM"""
        try:
            user_id = notif.get('user_id')
            user = await self.bot.fetch_user(user_id)
            
            if not user:
                NotificationQueries.mark_as_failed(notif['id'], "Usuário não encontrado")
                return
            
            # Cria embed da notificação
            xp_reward = notif.get('xp_reward', 0)
            coins_reward = notif.get('coins_reward', 0)
            
            # Monta descrição com recompensas
            description = notif.get('message', '')
            
            embed = discord.Embed(
                title=notif.get('title', '📬 Notificação'),
                description=description,
                color=config.EMBED_COLOR_SUCCESS
            )
            
            embed.set_footer(text="🦈 SharkClub")
            
            # Tenta enviar DM
            try:
                await user.send(embed=embed)
                NotificationQueries.mark_as_sent(notif['id'])
                print(f"✅ Notificação enviada para {user.name} (ID: {user_id})")
            except discord.Forbidden:
                # Usuário bloqueou DMs
                NotificationQueries.mark_as_failed(notif['id'], "DMs desabilitadas")
                print(f"⚠️ Não foi possível enviar DM para {user_id} - DMs bloqueadas")
            except Exception as dm_error:
                NotificationQueries.mark_as_failed(notif['id'], str(dm_error))
                print(f"⚠️ Erro ao enviar DM para {user_id}: {dm_error}")
                
        except Exception as e:
            NotificationQueries.mark_as_failed(notif['id'], str(e))
            print(f"⚠️ Erro ao processar notificação {notif.get('id')}: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(NotificationsCog(bot))
