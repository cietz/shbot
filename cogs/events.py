"""
🦈 SharkClub Discord Bot - Events Cog
Sistema de eventos e lives com presença X2 para VIPs
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
from typing import Optional

from database.queries import UserQueries, EventQueries
from utils.embeds import SharkEmbeds
import config

# Timezone brasileiro (UTC-3)
BR_TIMEZONE = timezone(timedelta(hours=-3))


class EventsCog(commands.Cog):
    """Sistema de eventos e lives"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def cog_unload(self):
        """Cancela tasks ao descarregar cog"""
        self.auto_close_events.cancel()
        self.announce_new_events.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Inicia task de auto-fechamento de eventos"""
        if not self.auto_close_events.is_running():
            self.auto_close_events.start()
            print("✅ Task de auto-fechamento de eventos iniciada")
            
        if not self.announce_new_events.is_running():
            self.announce_new_events.start()
            print("✅ Task de anúncios automáticos iniciada")
    
    @tasks.loop(seconds=15)
    async def auto_close_events(self):
        """Verifica eventos que passaram do horário e os encerra automaticamente. Também atualiza status."""
        try:
            events = EventQueries.get_active_events()
            now = datetime.now(timezone.utc)
            
            for event in events:
                end_time = event.get('end_time') or event.get('ends_at')
                start_time = event.get('start_time') or event.get('starts_at')
                
                # Converte string ISO para datetime
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                # Verifica encerramento
                if end_time and end_time <= now:
                    EventQueries.close_event(event['id'])
                    print(f"🔒 Evento #{event['id']} '{event['event_name']}' encerrado automaticamente")
                    
                    # Atualiza mensagem final
                    if event.get('message_id') and event.get('channel_id'):
                        channel = self.bot.get_channel(int(event['channel_id']))
                        if channel:
                            await self.update_event_announcement(channel.guild, event)
                    continue

                # Atualiza status (Em Breve -> Ativo) e contadores
                if event.get('message_id') and event.get('channel_id'):
                    try:
                        channel = self.bot.get_channel(int(event['channel_id']))
                        if channel:
                            await self.update_event_announcement(channel.guild, event)
                    except Exception as e:
                        # Ignora erros de update pontuais
                        pass
                        
        except Exception as e:
            print(f"⚠️ Erro ao verificar auto-fechamento de eventos: {e}")

    @tasks.loop(seconds=15)
    async def announce_new_events(self):
        """Verifica novos eventos criados na dashboard e os anuncia"""
        try:
            # Busca canal fixo de eventos
            channel_id = config.CHANNEL_IDS.get("eventos")
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                # Silencioso para não spammar logs se não configurado
                return
            
            # Busca eventos não anunciados
            new_events = EventQueries.get_unannounced_events()
            
            if not new_events:
                return
                
            for event in new_events:
                try:
                    # Cria embed
                    embed = self.create_event_announcement_embed(event, [])
                    
                    # Envia para o canal
                    message = await channel.send(embed=embed)
                    
                    # Atualiza BD com message_id
                    EventQueries.update_event_message(event['id'], message.id, channel.id)
                    print(f"📢 Novo evento anunciado: {event['event_name']}")
                    
                except Exception as ex:
                    print(f"❌ Erro ao anunciar evento {event['id']}: {ex}")
                    
        except Exception as e:
            print(f"⚠️ Erro na task de anúncios: {e}")
    
    def is_admin():
        """Decorator para verificar permissão de admin"""
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    def create_event_announcement_embed(self, event: dict, presences: list) -> discord.Embed:
        """Cria embed do anúncio de evento com lista de participantes"""
        tipo_emoji = {
            'live': '🎬',
            'event': '🎪',
            'workshop': '📚'
        }
        emoji = tipo_emoji.get(event.get('event_type', 'event'), '🎪')
        
        # Converte horários
        start_time = event.get('starts_at') or event.get('start_time')
        end_time = event.get('ends_at') or event.get('end_time')
        
        now = datetime.now(timezone.utc)
        
        # Converte strings para datetime
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
        is_future = start_time and start_time > now
        is_ended = end_time and end_time <= now
        
        if is_future:
            status_text = "⏳ Em Breve!"
            desc_text = f"Prepare-se! O evento começará <t:{int(start_time.timestamp())}:R>."
            color = config.EMBED_COLOR_WARNING
        elif is_ended:
            status_text = "🔒 Encerrado"
            desc_text = "Este evento já foi finalizado."
            color = config.EMBED_COLOR_ERROR
        else:
            status_text = "🟢 Ao Vivo / Ativo"
            desc_text = "Evento em andamento! Participe agora!"
            color = config.EMBED_COLOR_SUCCESS
            
        custom_desc = event.get('description')
        if custom_desc:
            desc_text = f"{custom_desc}\n\n{desc_text}"
        
        embed = discord.Embed(
            title=f"{emoji} {event['event_name']} | {status_text}",
            description=desc_text,
            color=color
        )
        
        # Datas
        if start_time:
            embed.add_field(name="⏰ Início", value=f"<t:{int(start_time.timestamp())}:f>", inline=True)
        if end_time:
            embed.add_field(name="🏁 Término", value=f"<t:{int(end_time.timestamp())}:f>", inline=True)
        
        embed.add_field(name="⭐ Recompensa XP", value=f"+{event['xp_reward']} XP", inline=True)
        embed.add_field(name="🪙 Moedas", value=f"+{event['coins_reward']}", inline=True)
        embed.add_field(name=f"{config.EMOJI_VIP} Bônus VIP", value="Recompensas X2!", inline=True)
        
        # Lista de participantes
        if presences:
            participants_text = ""
            for i, p in enumerate(presences[:15], 1):
                participants_text += f"{i}. <@{p['user_id']}>\n"
            if len(presences) > 15:
                participants_text += f"\n_...e mais {len(presences) - 15} participantes_"
            embed.add_field(name=f"👥 Participantes ({len(presences)})", value=participants_text, inline=False)
        else:
            embed.add_field(name="👥 Participantes", value="_Nenhum ainda - seja o primeiro!_", inline=False)
        
        if not is_ended:
            cmd_text = f"Use o comando `/presenca` para confirmar!"
            if is_future:
                cmd_text = "Aguarde o início para marcar presença!"
            
            embed.add_field(
                name="📝 Como participar",
                value=cmd_text,
                inline=False
            )
        
        embed.set_footer(text=f"🆔 Evento #{event['id']} | 🦈 SharkClub")
        return embed
    
    async def update_event_announcement(self, guild: discord.Guild, event: dict):
        """Atualiza o embed do anúncio do evento com a lista atualizada de participantes"""
        try:
            # Pega message_id e channel_id do evento
            message_id = event.get('message_id')
            channel_id = event.get('channel_id')
            
            if not message_id or not channel_id:
                return  # Evento não tem anúncio salvo
            
            # Busca o canal
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return
            
            # Busca a mensagem
            try:
                message = await channel.fetch_message(int(message_id))
            except:
                return  # Mensagem não encontrada
            
            # Busca presenças atualizadas
            presences = EventQueries.get_event_presences(event['id'])
            
            # Cria embed atualizado
            new_embed = self.create_event_announcement_embed(event, presences)
            
            # Edita a mensagem
            await message.edit(embed=new_embed)
        except Exception as e:
            print(f"⚠️ Erro ao atualizar anúncio: {e}")
            
    # ═══════════════════════════════════════════════════════════════
    # COMANDOS DE USUÁRIO - MARCAR PRESENÇA
    # ═══════════════════════════════════════════════════════════════
    
    @app_commands.command(name="presenca", description="Marcar presença no evento/live atual")
    async def presenca(self, interaction: discord.Interaction):
        """Marca presença no evento ativo (detecta automaticamente)"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        username = interaction.user.display_name
        
        # Busca eventos ativos
        events = EventQueries.get_active_events()
        
        if not events:
            embed = discord.Embed(
                title="⚠️ Nenhum Evento Ativo",
                description="Não há nenhum evento acontecendo no momento.\nFique atento aos anúncios!",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verifica qual evento está acontecendo AGORA (baseado em horário brasileiro)
        from datetime import timedelta
        now = datetime.now(timezone.utc) - timedelta(hours=3)  # Ajusta para horário BR
        
        active_event = None
        for event in events:
            # Verifica se o evento tem horário definido e se está dentro do período
            start_time = event.get('starts_at') or event.get('start_time')
            end_time = event.get('ends_at') or event.get('end_time')
            
            if start_time and end_time:
                # Converte strings ISO para datetime se necessário
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                # Ajusta para horário BR
                start_br = start_time - timedelta(hours=3) if start_time.tzinfo else start_time
                end_br = end_time - timedelta(hours=3) if end_time.tzinfo else end_time
                now_naive = now.replace(tzinfo=None) if now.tzinfo else now
                start_naive = start_br.replace(tzinfo=None) if hasattr(start_br, 'tzinfo') and start_br.tzinfo else start_br
                end_naive = end_br.replace(tzinfo=None) if hasattr(end_br, 'tzinfo') and end_br.tzinfo else end_br
                
                if start_naive <= now_naive <= end_naive:
                    active_event = event
                    break
            else:
                # Se não tem horário definido, considera ativo (comportamento legado)
                active_event = event
                break
        
        if not active_event:
            embed = discord.Embed(
                title="⏰ Fora do Horário",
                description="Não há nenhum evento acontecendo **agora**.\n\nUse `/eventos` para ver os próximos eventos!",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        event = active_event
        
        # Busca ou cria usuário
        user_data = UserQueries.get_or_create_user(user_id, username)
        is_vip = user_data.get('is_vip', False)
        
        # Marca presença
        presence = EventQueries.mark_presence(event['id'], user_id, is_vip)
        
        if not presence:
            embed = discord.Embed(
                title="✅ Presença Já Marcada",
                description=f"Você já marcou presença no evento **{event['event_name']}**.",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Dá as recompensas ao usuário
        xp_earned = presence.get('xp_earned', 0)
        coins_earned = presence.get('coins_earned', 0)
        multiplier = presence.get('presence_multiplier', 1)
        
        UserQueries.update_xp(user_id, xp_earned)
        UserQueries.update_coins(user_id, coins_earned)
        
        # Cria embed de sucesso (ephemeral)
        color = config.EMBED_COLOR_VIP if is_vip else config.EMBED_COLOR_SUCCESS
        status_emoji = config.EMOJI_VIP if is_vip else config.EMOJI_FREE
        
        embed = discord.Embed(
            title=f"✅ Presença Confirmada! {status_emoji}",
            description=f"Você está participando do evento **{event['event_name']}**!",
            color=color
        )
        
        embed.add_field(name="⭐ XP Ganho", value=f"+{xp_earned} XP", inline=True)
        embed.add_field(name="🪙 Moedas", value=f"+{coins_earned}", inline=True)
        
        if is_vip and multiplier > 1:
            embed.add_field(
                name=f"{config.EMOJI_VIP} Bônus VIP!",
                value=f"Presença X{multiplier}! Recompensas dobradas!",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="🦈 SharkClub - Sistema de Eventos")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Atualiza o embed do anúncio dinamicamente
        await self.update_event_announcement(interaction.guild, event)
    
    @app_commands.command(name="eventos", description="Ver eventos ativos disponíveis")
    async def eventos(self, interaction: discord.Interaction):
        """Lista eventos ativos para o usuário"""
        events = EventQueries.get_active_events()
        
        # Verifica status VIP do usuário
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        is_vip = user_data.get('is_vip', False)
        
        color = config.EMBED_COLOR_VIP if is_vip else config.EMBED_COLOR_PRIMARY
        
        embed = discord.Embed(
            title=f"{config.EMOJI_EVENT} Eventos Disponíveis",
            color=color
        )
        
        if events:
            for event in events[:5]:
                # Verifica se usuário já marcou presença
                presences = EventQueries.get_event_presences(event['id'])
                user_presence = next((p for p in presences if p['user_id'] == interaction.user.id), None)
                
                status = "✅ Presença marcada" if user_presence else "⬜ Aguardando presença"
                
                # Multiplicador VIP
                if is_vip:
                    xp_show = event['xp_reward'] * config.VIP_EVENT_PRESENCE_MULTIPLIER
                    coins_show = event['coins_reward'] * config.VIP_EVENT_PRESENCE_MULTIPLIER
                    reward_text = f"⭐ {xp_show} XP | 🪙 {coins_show} moedas ({config.EMOJI_VIP} X2)"
                else:
                    reward_text = f"⭐ {event['xp_reward']} XP | 🪙 {event['coins_reward']} moedas"
                
                embed.add_field(
                    name=f"🆔 {event['id']} - {event['event_name']}",
                    value=f"{reward_text}\n{status}",
                    inline=False
                )
            
            embed.set_footer(text="Use /presenca ID para marcar sua presença!")
        else:
            embed.description = "Nenhum evento ativo no momento.\nFique atento aos anúncios!"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="minhas-presencas", description="Ver suas presenças em eventos")
    async def minhas_presencas(self, interaction: discord.Interaction):
        """Mostra histórico de presenças do usuário"""
        user_id = interaction.user.id
        
        presences = EventQueries.get_user_event_presences(user_id, days=30)
        total_xp = EventQueries.get_user_total_event_xp(user_id)
        
        embed = discord.Embed(
            title=f"{config.EMOJI_EVENT} Suas Presenças em Eventos",
            description=f"Últimos 30 dias",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        if presences:
            for p in presences[:10]:
                event = EventQueries.get_event(p['event_id'])
                event_name = event['event_name'] if event else f"Evento #{p['event_id']}"
                
                multiplier_text = f" ({config.EMOJI_VIP} X{p['presence_multiplier']})" if p['presence_multiplier'] > 1 else ""
                
                embed.add_field(
                    name=event_name,
                    value=f"⭐ {p['xp_earned']} XP | 🪙 {p['coins_earned']} moedas{multiplier_text}",
                    inline=True
                )
            
            embed.add_field(
                name="📊 Total de XP em Eventos",
                value=f"**{total_xp:,}** XP",
                inline=False
            )
        else:
            embed.description = "Você ainda não marcou presença em nenhum evento.\nUse `/eventos` para ver os eventos disponíveis!"
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Total: {len(presences)} presença(s)")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    



async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
