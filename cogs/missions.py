"""
🦈 SharkClub Discord Bot - Missions Cog
Sistema de missões diárias, semanais e secretas
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import random
import asyncio

from database.queries import UserQueries, MissionQueries, RewardQueries, ActivityQueries
from utils.embeds import SharkEmbeds
from utils.xp_calculator import XPCalculator
import config


# ═══════════════════════════════════════════════════════════════
# VIEW COM BOTÃO PARA MISSÕES PESSOAIS
# ═══════════════════════════════════════════════════════════════

class MissionsView(discord.ui.View):
    """View persistente com botão para ver missões pessoais"""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)  # Persistente
        self.bot = bot
    
    @discord.ui.button(
        label="📋 Minhas Missões",
        style=discord.ButtonStyle.primary,
        custom_id="missions_view_personal"
    )
    async def view_missions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostra missões pessoais do usuário"""
        await interaction.response.defer(ephemeral=True)
        
        missions_cog = self.bot.get_cog('MissionsCog')
        if not missions_cog:
            await interaction.followup.send("❌ Erro ao carregar missões.", ephemeral=True)
            return
        
        user_id = interaction.user.id
        
        # Garante que usuário existe
        UserQueries.get_or_create_user(user_id, interaction.user.display_name)
        
        # Busca missões ativas
        daily = MissionQueries.get_active_missions(user_id, 'daily')
        weekly = MissionQueries.get_active_missions(user_id, 'weekly')
        secret = MissionQueries.get_active_missions(user_id, 'secret')
        
        # Se não tem missões diárias, gera novas
        if not daily:
            daily = await missions_cog.generate_daily_missions(user_id)
        
        # Se não tem missões semanais, gera novas
        if not weekly:
            weekly = await missions_cog.generate_weekly_missions(user_id)
        
        # Se é VIP e não tem missões secretas, gera novas
        if UserQueries.is_vip(user_id) and not secret:
            secret = await missions_cog.generate_secret_missions(user_id)
        
        # Cria embed customizado
        embed = missions_cog.create_missions_embed(daily, weekly, secret)
        
        await interaction.followup.send(embed=embed, ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# VIEW PERSISTENTE DO BOTÃO "AJUDOU" PARA THREADS
# ═══════════════════════════════════════════════════════════════

class ThreadHelpedButtonView(discord.ui.View):
    """View persistente com botão 'Ajudou' enviada em threads de ajuda"""
    
    def __init__(self, thread_owner_id: int):
        super().__init__(timeout=None)  # Persistente
        self.thread_owner_id = thread_owner_id
    
    @discord.ui.button(
        label="🤝 Ajudou!",
        style=discord.ButtonStyle.success,
        custom_id="thread_helped_button"
    )
    async def helped_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Registra que o criador da thread ajudou o usuário que clicou"""
        await interaction.response.defer(ephemeral=True)
        
        clicker_id = interaction.user.id
        
        # Extrai o thread_owner_id do custom_id da mensagem (armazenado no embed)
        # Primeiro tenta pegar do embed da mensagem
        thread_owner_id = None
        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            if embed.footer and embed.footer.text:
                # O formato é: "ID: <user_id>"
                try:
                    footer_text = embed.footer.text
                    if "ID:" in footer_text:
                        thread_owner_id = int(footer_text.split("ID:")[1].strip())
                except:
                    pass
        
        if not thread_owner_id:
            await interaction.followup.send(
                "❌ Não foi possível identificar o criador da thread.", 
                ephemeral=True
            )
            return
        
        # Validações
        if clicker_id == thread_owner_id:
            await interaction.followup.send(
                "❌ Você não pode marcar você mesmo como ajudante!",
                ephemeral=True
            )
            return
        
        # Pega o membro que criou a thread (o helper)
        helper = interaction.guild.get_member(thread_owner_id)
        if not helper:
            try:
                helper = await interaction.guild.fetch_member(thread_owner_id)
            except:
                await interaction.followup.send(
                    "❌ O criador da thread não foi encontrado no servidor.",
                    ephemeral=True
                )
                return
        
        if helper.bot:
            await interaction.followup.send(
                "❌ Você não pode marcar um bot como ajudante!",
                ephemeral=True
            )
            return
        
        # Garante que o helper existe no banco
        UserQueries.get_or_create_user(thread_owner_id, helper.display_name)
        
        # Busca missões semanais do helper
        weekly_missions = MissionQueries.get_active_missions(thread_owner_id, 'weekly')
        
        # Se não tem missões semanais, cria automaticamente (via cog)
        missions_cog = interaction.client.get_cog('MissionsCog')
        if not weekly_missions and missions_cog:
            weekly_missions = await missions_cog.generate_weekly_missions(thread_owner_id)
        
        # Registra a ajuda no activity_log (para missão secreta 2)
        try:
            unique_helped = ActivityQueries.get_unique_helped_members(thread_owner_id, days=7)
            if clicker_id not in unique_helped:
                ActivityQueries.log_help_activity(thread_owner_id, clicker_id)
        except Exception as e:
            print(f"⚠️ Erro ao registrar ajuda: {e}")
        
        # Procura pela missão mentor_fantasma
        mentor_mission = next((m for m in weekly_missions if m.get('mission_id') == 'mentor_fantasma'), None)
        
        if not mentor_mission:
            await interaction.followup.send(
                f"✅ Obrigado! Sua ajuda foi registrada para {helper.mention}!",
                ephemeral=True
            )
            # Ainda verifica missão secreta VIP
            if UserQueries.is_vip(thread_owner_id) and missions_cog:
                await missions_cog._check_help_mission(thread_owner_id, clicker_id)
            return
        
        if mentor_mission.get('status') == 'completed':
            embed = discord.Embed(
                title="✅ Obrigado!",
                description=f"Sua ajuda foi registrada!\n{helper.mention} já completou a missão **Mentor Fantasma** esta semana! 🎉",
                color=config.EMBED_COLOR_SUCCESS
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            # Mesmo com missão semanal completa, ainda verifica missão secreta VIP
            if UserQueries.is_vip(thread_owner_id) and missions_cog:
                await missions_cog._check_help_mission(thread_owner_id, clicker_id)
            return
        
        # Avança o progresso da missão
        new_progress = mentor_mission.get('progress', 0) + 1
        target = mentor_mission.get('target', 2)
        
        if new_progress >= target:
            # Completa a missão
            MissionQueries.complete_mission(mentor_mission['id'])
            xp_reward = config.WEEKLY_MISSIONS.get('mentor_fantasma', {}).get('xp_reward', 100)
            coins_reward = config.WEEKLY_MISSIONS.get('mentor_fantasma', {}).get('coins_reward', 10)
            UserQueries.update_xp(thread_owner_id, xp_reward)
            UserQueries.update_coins(thread_owner_id, coins_reward)
            
            embed = discord.Embed(
                title="🎉 Missão Completa!",
                description=f"Você confirmou que {helper.mention} te ajudou!\n\n"
                           f"**{helper.display_name}** completou a missão **Mentor Fantasma**! 🎯\n"
                           f"**Recompensas:** +{xp_reward} XP | +{coins_reward} 🪙",
                color=config.EMBED_COLOR_SUCCESS
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Atualiza progresso
            MissionQueries.update_mission_progress(mentor_mission['id'], new_progress)
            
            embed = discord.Embed(
                title="✅ Ajuda Registrada!",
                description=f"Você confirmou que {helper.mention} te ajudou!\n\n"
                           f"**Progresso da missão Mentor Fantasma:** {new_progress}/{target}",
                color=config.EMBED_COLOR_SUCCESS
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Verifica missão secreta 2 para VIPs
        if UserQueries.is_vip(thread_owner_id) and missions_cog:
            await missions_cog._check_help_mission(thread_owner_id, clicker_id)


class MissionsCog(commands.Cog):
    """Sistema de missões"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._missions_message_id = None  # ID da mensagem das missões no canal
        # Tracking de tempo em voz para recompensas passivas
        self.voice_join_times: Dict[int, datetime] = {}  # user_id -> timestamp de entrada
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Envia painel de missões no canal apropriado e registra Views persistentes"""
        await asyncio.sleep(7)  # Aguarda setup
        
        # Registra a View persistente do botão "Ajudou" para threads
        # Usa ID 0 como placeholder - o ID real é extraído do embed footer
        self.bot.add_view(ThreadHelpedButtonView(thread_owner_id=0))
        print("✅ View persistente do botão 'Ajudou!' registrada")
        
        for guild in self.bot.guilds:
            await self._send_missions_panel(guild)
    

    async def _send_missions_panel(self, guild: discord.Guild, force_new: bool = False):
        """Envia ou atualiza painel de missões no canal de missões"""
        # Busca o canal pelo ID fixo
        channel_id = config.CHANNEL_IDS.get("missoes")
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            msg = f"⚠️ Canal de missões não encontrado (ID: {channel_id})"
            print(msg)
            return False, msg
        
        # Cria embed do painel
        embed = discord.Embed(
            title="📋 Missões SharkClub",
            description="Clique no botão abaixo para ver suas missões!\n\n"
                       "📅 **Missões Diárias** - Renovam todo dia\n"
                       "📆 **Missões Semanais** - 5 missões por semana\n"
                       "⭐ **Missões Secretas** - Exclusivo VIP",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_footer(text="🦈 SharkClub - Complete missões para ganhar XP e coins!")
        
        # Cria view com botão
        view = MissionsView(self.bot)
        
        # Tenta encontrar mensagem existente
        try:
            if not force_new:
                async for message in channel.history(limit=10):
                    if message.author == self.bot.user and message.embeds:
                        first_embed = message.embeds[0]
                        if first_embed.title and "Missões" in first_embed.title:
                            await message.edit(embed=embed, view=view)
                            msg = f"✅ Painel de missões atualizado em {channel.name}"
                            print(msg)
                            return True, msg
            
            # Envia nova mensagem
            await channel.send(embed=embed, view=view)
            msg = f"✅ Painel de missões enviado para {channel.name}"
            print(msg)
            return True, msg
            
        except discord.Forbidden:
            msg = f"❌ Sem permissão para enviar no canal {channel.name}"
            print(msg)
            return False, msg
        except Exception as e:
            msg = f"❌ Erro ao enviar painel de missões: {e}"
            print(msg)
            return False, msg
    
    @app_commands.command(name="admin-setup-missoes", description="[ADMIN] Reenviar o painel de missões")
    async def admin_setup_missoes(self, interaction: discord.Interaction):
        """[ADMIN] Reenvia o painel de missões no canal configurado"""
        # Verifica admin no DB
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        if not user_data.get('is_admin', False):
             await interaction.response.send_message("❌ Apenas administradores do bot podem usar este comando.", ephemeral=True)
             return

        await interaction.response.defer(ephemeral=True)
        # Força envio de nova mensagem
        success, msg = await self._send_missions_panel(interaction.guild, force_new=True)
        
        if success:
            await interaction.followup.send(f"{msg}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Falha: {msg}", ephemeral=True)

    @app_commands.command(name="admin-setup-ajudou", description="[ADMIN] Envia painel 'Ajudou' no canal atual")
    @app_commands.describe(membro="O membro que criou o conteúdo/post que ajuda outros")
    async def admin_setup_ajudou(self, interaction: discord.Interaction, membro: discord.Member):
        """[ADMIN] Envia o painel com botão 'Ajudou' no canal atual, atribuindo ao membro especificado"""
        # Verifica admin no DB
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        if not user_data.get('is_admin', False):
            await interaction.response.send_message("❌ Apenas administradores do bot podem usar este comando.", ephemeral=True)
            return
        
        # Validações
        if membro.bot:
            await interaction.response.send_message("❌ Você não pode selecionar um bot!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        helper_id = membro.id
        
        # Cria embed com instruções
        embed = discord.Embed(
            title="🤝 Esta informação te ajudou?",
            description=f"Se o conteúdo deste post foi útil para você, clique no botão abaixo!\n\n"
                       f"**Autor:** {membro.mention}\n"
                       f"O autor receberá progresso na missão **Mentor Fantasma**.",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_footer(text=f"ID: {helper_id}")  # Armazena o ID do helper no footer
        
        # Cria view com botão
        view = ThreadHelpedButtonView(thread_owner_id=helper_id)
        
        try:
            await interaction.channel.send(embed=embed, view=view)
            await interaction.followup.send(f"✅ Painel 'Ajudou' enviado com sucesso! Atribuído a {membro.mention}", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para enviar no canal.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {e}", ephemeral=True)

    def cog_unload(self):
        self.check_weekly_reset.cancel()
    
    @commands.Cog.listener()
    async def on_ready_missions_gen(self):
        """Inicia verificação de reset semanal e gera missões"""
        if not self.check_weekly_reset.is_running():
            self.check_weekly_reset.start()
        
        # Aguarda um pouco para garantir que os canais estão configurados
        await asyncio.sleep(8)
        
        # Para cada servidor - apenas gera missões
        for guild in self.bot.guilds:
            # Gera missões semanais para todos os membros automaticamente
            await self.generate_weekly_missions_for_all(guild)
    
    async def generate_weekly_missions_for_all(self, guild: discord.Guild):
        """Gera missões semanais para todos os membros do servidor que ainda não têm (OTIMIZADO)"""
        from datetime import timedelta
        
        # 1. Busca todos os user_ids que JÁ têm missões semanais (1 query)
        users_with_missions = MissionQueries.get_users_with_active_weekly_missions()
        
        # 2. Busca todos os usuários que já existem no banco de dados
        existing_users = UserQueries.get_all_user_ids()
        
        # 3. Filtra membros que precisam de missões E que já existem no banco
        members_needing_missions = [
            m for m in guild.members 
            if not m.bot and m.id not in users_with_missions and m.id in existing_users
        ]
        
        if not members_needing_missions:
            return
        
        # 4. Calcula data de expiração (próximo domingo 23:59)
        now = datetime.now(timezone.utc)
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        expires_at = (now + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59)
        expires_at_iso = expires_at.isoformat()
        
        # 5. Prepara batch de missões para todos os membros (sem chamada individual ao banco)
        all_missions = []
        for member in members_needing_missions:
            # Adiciona as 5 missões semanais para este membro
            for mission_id, mission_data in config.WEEKLY_MISSIONS.items():
                all_missions.append({
                    'user_id': member.id,
                    'mission_id': mission_id,
                    'mission_type': 'weekly',
                    'status': 'active',
                    'progress': 0,
                    'target': mission_data['target'],
                    'xp_reward': mission_data['xp_reward'],
                    'expires_at': expires_at_iso,
                })
        
        # 6. Insere todas as missões de uma vez (1 query)
        if all_missions:
            created = MissionQueries.create_missions_batch(all_missions)
            
            if created > 0:
                print(f"📋 {created} missões semanais criadas para {len(members_needing_missions)} membros em {guild.name}")

    
    @tasks.loop(hours=1)
    async def check_weekly_reset(self):
        """Verifica se é hora de resetar missões semanais (segunda-feira 00:00)"""
        now = datetime.now(timezone.utc)
        # Segunda-feira = 0
        if now.weekday() == 0 and now.hour == 0:
            print("🔄 Resetando missões semanais...")
            # Expira todas as missões semanais antigas
            MissionQueries.expire_old_missions('weekly')
            
            # Gera novas missões para todos e atualiza o canal
            for guild in self.bot.guilds:
                await self.generate_weekly_missions_for_all(guild)
                await self.send_missions_to_channel(guild)
    
    async def send_missions_to_channel(self, guild: discord.Guild):
        """Envia ou atualiza embed de missões semanais no canal 📋-missoes-🦈"""
        # Busca o canal de missões (prioriza canais do bot com 🦈)
        channel = None
        fallback_channel = None
        
        for ch in guild.text_channels:
            if "missoes" in ch.name.lower() or "missões" in ch.name.lower():
                # Prioriza canais do bot (terminam com 🦈)
                if "🦈" in ch.name:
                    channel = ch
                    break
                # Guarda fallback caso não encontre o canal com 🦈
                if fallback_channel is None:
                    fallback_channel = ch
        
        # Se não encontrou canal com 🦈, usa o fallback
        if channel is None:
            channel = fallback_channel
        
        if not channel:
            print(f"⚠️ Canal de missões não encontrado em {guild.name}")
            return
        
        # Cria embed das missões semanais
        embed = self.create_weekly_missions_channel_embed()
        
        # Cria view com botão
        view = MissionsView(self.bot)
        
        # Tenta encontrar a mensagem existente no canal (nas últimas 10 mensagens)
        try:
            async for message in channel.history(limit=10):
                if message.author == self.bot.user and message.embeds:
                    first_embed = message.embeds[0]
                    if first_embed.title and "Missões Semanais" in first_embed.title:
                        # Atualiza a mensagem existente
                        await message.edit(embed=embed, view=view)
                        print(f"✅ Missões atualizadas no canal {channel.name}")
                        return
            
            # Se não encontrou, envia nova mensagem com botão
            await channel.send(embed=embed, view=view)
            print(f"✅ Missões enviadas para o canal {channel.name}")
            
        except discord.Forbidden:
            print(f"❌ Sem permissão para enviar no canal {channel.name}")
        except Exception as e:
            print(f"❌ Erro ao enviar missões: {e}")
    
    def create_weekly_missions_channel_embed(self) -> discord.Embed:
        """Cria embed formatado das missões semanais para o canal"""
        embed = discord.Embed(
            title="📆 Missões Semanais SharkClub",
            description="Complete as missões abaixo para ganhar **XP** e **Shark Coins**!\n"
                       "Use `/missoes` para ver seu progresso pessoal.",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        # Adiciona cada missão
        for mission_id, mission_data in config.WEEKLY_MISSIONS.items():
            emoji = mission_data.get('emoji', '📋')
            name = mission_data.get('name', mission_id)
            description = mission_data.get('description', '')
            objective = mission_data.get('objective', '')
            xp = mission_data.get('xp_reward', 100)
            coins = mission_data.get('coins_reward', 10)
            target = mission_data.get('target', 1)
            
            field_value = f"{description}\n"
            field_value += f"**Objetivo:** {objective} ({target}x)\n"
            field_value += f"**Recompensa:** +{xp} XP | +{coins} 🪙"
            
            embed.add_field(
                name=f"{emoji} {name}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text="💡 Use /missoes para ver seu progresso | Reseta toda segunda-feira")
        embed.timestamp = datetime.now(timezone.utc)
        
        return embed
    
    @app_commands.command(name="missoes", description="Ver suas missões ativas")
    async def missoes(self, interaction: discord.Interaction):
        """Lista missões do usuário"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        
        # Garante que usuário existe
        UserQueries.get_or_create_user(user_id, interaction.user.display_name)
        
        # Busca missões ativas
        daily = MissionQueries.get_active_missions(user_id, 'daily')
        weekly = MissionQueries.get_active_missions(user_id, 'weekly')
        secret = MissionQueries.get_active_missions(user_id, 'secret')
        
        # Se não tem missões diárias, gera novas
        if not daily:
            daily = await self.generate_daily_missions(user_id)
        
        # Se não tem missões semanais, gera novas
        if not weekly:
            weekly = await self.generate_weekly_missions(user_id)
        
        # Se é VIP e não tem missões secretas, gera novas
        if UserQueries.is_vip(user_id) and not secret:
            secret = await self.generate_secret_missions(user_id)
        
        # Cria embed customizado
        embed = self.create_missions_embed(daily, weekly, secret)
        
        # Missões são pessoais
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    def create_missions_embed(self, daily: list, weekly: list, secret: list) -> discord.Embed:
        """Cria embed de missões formatado"""
        embed = discord.Embed(
            title="📋 Suas Missões",
            description="Complete missões para ganhar XP!",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        # Missões Diárias
        if daily:
            daily_text = ""
            for m in daily:
                progress = m.get('progress', 0)
                target = m.get('target', 1)
                status = "✅" if m.get('status') == 'completed' else f"{progress}/{target}"
                mission_info = self.get_mission_info(m.get('mission_id'), 'daily')
                name = mission_info.get('name', m.get('mission_id'))
                xp = m.get('xp_reward', 0)
                daily_text += f"• **{name}** [{status}] → +{xp} XP\n"
            embed.add_field(name="📅 Missões Diárias", value=daily_text or "Nenhuma", inline=False)
        
        # Missões Semanais
        if weekly:
            weekly_text = ""
            for m in weekly:
                progress = m.get('progress', 0)
                target = m.get('target', 1)
                status = "✅" if m.get('status') == 'completed' else f"{progress}/{target}"
                mission_info = self.get_mission_info(m.get('mission_id'), 'weekly')
                emoji = mission_info.get('emoji', '📋')
                name = mission_info.get('name', m.get('mission_id'))
                xp = m.get('xp_reward', 0)
                weekly_text += f"{emoji} **{name}** [{status}] → +{xp} XP\n"
            embed.add_field(name="📆 Missões Semanais", value=weekly_text or "Nenhuma", inline=False)
        else:
            embed.add_field(name="📆 Missões Semanais", value="Use `/missoes` para gerar!", inline=False)
        
        # Missões Secretas (apenas para VIPs)
        if secret:
            secret_text = ""
            for m in secret:
                progress = m.get('progress', 0)
                target = m.get('target', 1)
                status = "✅" if m.get('status') == 'completed' else f"{progress}/{target}"
                mission_info = self.get_mission_info(m.get('mission_id'), 'secret')
                name = mission_info.get('name', '???')
                xp = m.get('xp_reward', 0)
                secret_text += f"⭐ **{name}** [{status}] → +{xp} XP\n"
            embed.add_field(name="⭐ Missões Secretas VIP", value=secret_text, inline=False)
        
        embed.set_footer(text="💡 Dica: Complete missões para subir de nível mais rápido!")
        return embed
    
    def get_mission_info(self, mission_id: str, mission_type: str) -> dict:
        """Retorna informações de uma missão do config"""
        if mission_type == 'weekly':
            return config.WEEKLY_MISSIONS.get(mission_id, {'name': mission_id})
        elif mission_type == 'daily':
            return config.DAILY_MISSIONS_TEMPLATES.get(mission_id, {'name': mission_id})
        elif mission_type == 'secret':
            return config.SECRET_MISSIONS.get(mission_id, {'name': mission_id})
        return {'name': mission_id}
    
    async def generate_daily_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Gera missões diárias para o usuário"""
        missions = []
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        # Seleciona missões aleatórias do config
        available = list(config.DAILY_MISSIONS_TEMPLATES.items())
        selected = random.sample(available, min(config.DAILY_MISSIONS_COUNT, len(available)))
        
        for mission_id, mission_data in selected:
            result = MissionQueries.create_mission(
                user_id=user_id,
                mission_id=mission_id,
                mission_type='daily',
                target=mission_data['target'],
                xp_reward=mission_data['xp_reward'],
                expires_at=expires_at
            )
            if result:
                missions.append(result)
        
        return missions
    
    async def generate_weekly_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Gera missões semanais para o usuário (as 5 do config)"""
        missions = []
        # Expira no próximo domingo às 23:59
        now = datetime.now(timezone.utc)
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7  # Se hoje é domingo, próxima semana
        expires_at = now + timedelta(days=days_until_sunday)
        expires_at = expires_at.replace(hour=23, minute=59, second=59)
        
        # Cria todas as 5 missões semanais
        for mission_id, mission_data in config.WEEKLY_MISSIONS.items():
            result = MissionQueries.create_mission(
                user_id=user_id,
                mission_id=mission_id,
                mission_type='weekly',
                target=mission_data['target'],
                xp_reward=mission_data['xp_reward'],
                expires_at=expires_at
            )
            if result:
                missions.append(result)
        
        print(f"📋 Criadas {len(missions)} missões semanais para user {user_id}")
        return missions
    
    async def generate_secret_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Gera missões secretas para usuários VIP"""
        # Verifica se o usuário é VIP
        if not UserQueries.is_vip(user_id):
            return []
        
        missions = []
        # Expira no próximo domingo às 23:59 (junto com as semanais)
        now = datetime.now(timezone.utc)
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        expires_at = now + timedelta(days=days_until_sunday)
        expires_at = expires_at.replace(hour=23, minute=59, second=59)
        
        # Verifica se já tem missões secretas ativas
        existing_secret = MissionQueries.get_active_missions(user_id, 'secret')
        existing_ids = [m.get('mission_id') for m in existing_secret]
        
        # Cria missões secretas que ainda não existem
        for mission_id, mission_data in config.SECRET_MISSIONS.items():
            if mission_id in existing_ids:
                continue  # Já tem essa missão
            
            result = MissionQueries.create_mission(
                user_id=user_id,
                mission_id=mission_id,
                mission_type='secret',
                target=mission_data['target'],
                xp_reward=mission_data['xp_reward'],
                expires_at=expires_at
            )
            if result:
                missions.append(result)
        
        if missions:
            print(f"⭐ Criadas {len(missions)} missões secretas VIP para user {user_id}")
        return missions
    
    @app_commands.command(name="missao-info", description="Ver detalhes de uma missão")
    @app_commands.describe(missao_id="ID da missão")
    async def missao_info(self, interaction: discord.Interaction, missao_id: str):
        """Mostra detalhes de uma missão específica"""
        # Busca definição da missão
        all_missions = DAILY_MISSIONS + WEEKLY_MISSIONS + SECRET_MISSIONS
        mission_def = next((m for m in all_missions if m['id'] == missao_id), None)
        
        if not mission_def:
            embed = discord.Embed(
                title="❌ Missão não encontrada",
                description=f"Não foi possível encontrar a missão `{missao_id}`",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Determina tipo
        if mission_def in DAILY_MISSIONS:
            mission_type = "📅 Diária"
            type_color = config.EMBED_COLOR_PRIMARY
        elif mission_def in WEEKLY_MISSIONS:
            mission_type = "📆 Semanal"
            type_color = config.EMBED_COLOR_SUCCESS
        else:
            mission_type = "⭐ Secreta"
            type_color = config.EMBED_COLOR_LEGENDARY
        
        embed = discord.Embed(
            title=f"{config.EMOJI_MISSION} {mission_def['name']}",
            description=mission_def['desc'],
            color=type_color
        )
        
        embed.add_field(name="Tipo", value=mission_type, inline=True)
        embed.add_field(name="Objetivo", value=f"{mission_def['target']}x", inline=True)
        embed.add_field(name="Recompensa", value=f"+{mission_def['xp']} XP", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listener para progresso de missões baseado em mensagens"""
        if message.author.bot:
            return
        
        user_id = message.author.id
        channel_id = message.channel.id if message.channel else 0
        
        # Registra atividade do usuário (para missão secreta 1)
        try:
            ActivityQueries.log_activity(user_id, channel_id, 'chat', message.id)
        except Exception as e:
            print(f"⚠️ Erro ao registrar atividade: {e}")
        
        # Busca missões de chat ativas
        daily_missions = MissionQueries.get_active_missions(user_id, 'daily')
        
        for mission in daily_missions:
            if mission.get('mission_id') == 'daily_messages' and mission.get('status') == 'active':
                new_progress = mission.get('progress', 0) + 1
                target = mission.get('target', 5)
                
                if new_progress >= target:
                    # Completa missão
                    MissionQueries.complete_mission(mission['id'])
                    # Dá o XP
                    xp_reward = mission.get('xp_reward', 0)
                    UserQueries.update_xp(user_id, xp_reward)
                else:
                    # Atualiza progresso
                    MissionQueries.update_mission_progress(mission['id'], new_progress)
        
        # Verifica missão secreta 1: Atividade Consistente (apenas VIPs)
        if UserQueries.is_vip(user_id):
            await self._check_activity_streak_mission(user_id)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Listener para progresso de missões e recompensas passivas de voz"""
        # Ignora bots
        if member.bot:
            return
        
        user_id = member.id
        
        # ═══════════════════════════════════════════════════════════════
        # RECOMPENSAS PASSIVAS DE VOZ - Tracking de tempo
        # ═══════════════════════════════════════════════════════════════
        
        # Usuário ENTROU em um canal de voz
        if before.channel is None and after.channel is not None:
            # Registra timestamp de entrada para recompensas passivas
            # APENAS no servidor SharkClub
            SHARKCLUB_GUILD_ID = 1296246117843079248
            if member.guild.id == SHARKCLUB_GUILD_ID:
                self.voice_join_times[user_id] = datetime.now(timezone.utc)
            
            channel_id = after.channel.id if after.channel else 0
            
            # Registra atividade de voz (para missão secreta 1)
            try:
                ActivityQueries.log_activity(user_id, channel_id, 'call')
            except Exception as e:
                print(f"⚠️ Erro ao registrar atividade de voz: {e}")
            
            # Busca missões diárias ativas
            daily_missions = MissionQueries.get_active_missions(user_id, 'daily')
            
            for mission in daily_missions:
                mission_id = mission.get('mission_id')
                
                # Missão: Entrar em calls (daily_voice_join)
                if mission_id == 'daily_voice_join' and mission.get('status') == 'active':
                    new_progress = mission.get('progress', 0) + 1
                    target = mission.get('target', 2)
                    
                    if new_progress >= target:
                        MissionQueries.complete_mission(mission['id'])
                        xp_reward = mission.get('xp_reward', 0)
                        UserQueries.update_xp(user_id, xp_reward)
                    else:
                        MissionQueries.update_mission_progress(mission['id'], new_progress)
                
                # Missão: Participar de call (daily_voice) - completa ao entrar
                if mission_id == 'daily_voice' and mission.get('status') == 'active':
                    new_progress = mission.get('progress', 0) + 1
                    target = mission.get('target', 1)
                    
                    if new_progress >= target:
                        MissionQueries.complete_mission(mission['id'])
                        xp_reward = mission.get('xp_reward', 0)
                        UserQueries.update_xp(user_id, xp_reward)
                    else:
                        MissionQueries.update_mission_progress(mission['id'], new_progress)
            
            # Busca missões semanais ativas
            weekly_missions = MissionQueries.get_active_missions(user_id, 'weekly')
            
            for mission in weekly_missions:
                mission_id = mission.get('mission_id')
                
                # Missão Semanal: Caçada da Semana (participar de calls nervosas)
                if mission_id == 'cacada_semana' and mission.get('status') == 'active':
                    new_progress = mission.get('progress', 0) + 1
                    target = mission.get('target', 2)
                    
                    if new_progress >= target:
                        MissionQueries.complete_mission(mission['id'])
                        xp_reward = mission.get('xp_reward', 0)
                        coins_reward = config.WEEKLY_MISSIONS.get('cacada_semana', {}).get('coins_reward', 10)
                        UserQueries.update_xp(user_id, xp_reward)
                        UserQueries.update_coins(user_id, coins_reward)
                        print(f"🏆 {member.display_name} completou: Caçada da Semana!")
                    else:
                        MissionQueries.update_mission_progress(mission['id'], new_progress)
            
            # Verifica missão secreta 1: Atividade Consistente (apenas VIPs)
            if UserQueries.is_vip(user_id):
                await self._check_activity_streak_mission(user_id)
        
        # Usuário SAIU de um canal de voz
        elif before.channel is not None and after.channel is None:
            # Calcula tempo em call e dá recompensas passivas
            # APENAS no servidor SharkClub
            SHARKCLUB_GUILD_ID = 1296246117843079248
            if member.guild.id != SHARKCLUB_GUILD_ID:
                # Remove tracking se estava sendo rastreado
                self.voice_join_times.pop(user_id, None)
                return
            
            if user_id in self.voice_join_times:
                join_time = self.voice_join_times.pop(user_id)
                now = datetime.now(timezone.utc)
                duration = now - join_time
                minutes_in_call = duration.total_seconds() / 60
                
                # Verifica se ficou tempo suficiente para ganhar recompensa
                required_minutes = config.VOICE_PASSIVE_MINUTES
                if minutes_in_call >= required_minutes:
                    # Calcula quantas vezes completou 1 hora (sem acumular mais de 1x por sessão)
                    # Para simplicidade, dá 1x a recompensa por sessão de 1h+
                    xp_reward = config.VOICE_PASSIVE_XP
                    coins_reward = config.VOICE_PASSIVE_COINS
                    
                    # Garante que usuário existe
                    UserQueries.get_or_create_user(user_id, member.display_name)
                    
                    # Dá as recompensas
                    UserQueries.update_xp(user_id, xp_reward)
                    UserQueries.update_coins(user_id, coins_reward)
                    
                    print(f"🎤 {member.display_name} ganhou +{xp_reward} XP e +{coins_reward} coins por {int(minutes_in_call)} min em call!")
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Listener para progresso de missões baseado em reações"""
        # Ignora reações de bots
        if payload.member and payload.member.bot:
            return
        
        user_id = payload.user_id
        
        # Busca missões de reação ativas
        daily_missions = MissionQueries.get_active_missions(user_id, 'daily')
        
        for mission in daily_missions:
            if mission.get('mission_id') == 'daily_react' and mission.get('status') == 'active':
                new_progress = mission.get('progress', 0) + 1
                target = mission.get('target', 3)
                
                if new_progress >= target:
                    MissionQueries.complete_mission(mission['id'])
                    xp_reward = mission.get('xp_reward', 0)
                    UserQueries.update_xp(user_id, xp_reward)
                else:
                    MissionQueries.update_mission_progress(mission['id'], new_progress)
                break  # Só uma missão de react por vez
    
    @app_commands.command(name="missoes-semanais", description="[ADMIN] Ver as 5 missões semanais disponíveis")
    async def missoes_semanais(self, interaction: discord.Interaction):
        """Lista todas as missões semanais disponíveis (apenas admins do DB)"""
        # Verificação via Banco de Dados
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        
        # Verifica se é admin no banco OU se tem permissão de administrador no Discord (opcional, mas seguro manter ambos ou só DB)
        # O usuário pediu "verifique o banco", então vamos priorizar o banco.
        if not user_data.get('is_admin', False):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Este comando é restrito a **administradores do bot**.\n\nSe você é um admin, peça para ser adicionado no painel.",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📆 Missões Semanais SharkClub",
            description="Complete missões para ganhar XP e coins!\nUse o botão **📋 Minhas Missões** para ver seu progresso.",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        for mission_id, mission_data in config.WEEKLY_MISSIONS.items():
            emoji = mission_data.get('emoji', '📋')
            name = mission_data.get('name', mission_id)
            description = mission_data.get('description', '')
            xp = mission_data.get('xp_reward', 100)
            coins = mission_data.get('coins_reward', 10)
            
            embed.add_field(
                name=f"{emoji} {name}",
                value=f"{description}\n**Recompensa:** +{xp} XP | +{coins} 🪙",
                inline=False
            )
        
        embed.set_footer(text="💡 Dica: Complete todas as 5 missões para maximizar seus ganhos!")
        await interaction.response.send_message(embed=embed)
    

    


    @app_commands.command(name="ajudou", description="Reportar que um membro te ajudou com dúvidas")
    @app_commands.describe(membro="O membro que te ajudou")
    async def ajudou(self, interaction: discord.Interaction, membro: discord.Member):
        """Comando para usuário reportar que outro membro o ajudou"""
        await interaction.response.defer()
        
        # Verifica se o comando está sendo usado no canal correto
        channel_name = interaction.channel.name.lower() if interaction.channel else ""
        if "ajudou" not in channel_name:
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description="Este comando só pode ser usado no canal **🤝-ajudou-🦈**!",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Validações básicas
        if membro.bot:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você não pode marcar um bot como ajudante!",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if membro.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você não pode marcar você mesmo como ajudante!",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        helper_id = membro.id
        
        # Garante que o helper existe no banco
        UserQueries.get_or_create_user(helper_id, membro.display_name)
        
        # Busca missões semanais do helper
        weekly_missions = MissionQueries.get_active_missions(helper_id, 'weekly')
        
        # Se não tem missões semanais, cria automaticamente
        if not weekly_missions:
            weekly_missions = await self.generate_weekly_missions(helper_id)
        
        # Registra a ajuda no activity_log (para missão secreta 2)
        try:
            # Verifica se esse par já foi registrado esta semana para evitar duplicatas
            unique_helped = ActivityQueries.get_unique_helped_members(helper_id, days=7)
            if interaction.user.id not in unique_helped:
                ActivityQueries.log_help_activity(helper_id, interaction.user.id)
        except Exception as e:
            print(f"⚠️ Erro ao registrar ajuda: {e}")
        
        # Procura pela missão mentor_fantasma
        mentor_mission = next((m for m in weekly_missions if m.get('mission_id') == 'mentor_fantasma'), None)
        
        if not mentor_mission:
            # Isso não deveria acontecer, mas por segurança
            embed = discord.Embed(
                title="⚠️ Erro ao carregar missão",
                description="Ocorreu um erro ao carregar a missão. Tente novamente.",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if mentor_mission.get('status') == 'completed':
            embed = discord.Embed(
                title="✅ Obrigado!",
                description=f"Sua ajuda foi registrada!\n{membro.mention} já completou a missão **Mentor Fantasma** esta semana! 🎉",
                color=config.EMBED_COLOR_SUCCESS
            )
            await interaction.followup.send(embed=embed)
            # Mesmo com missão semanal completa, ainda verifica missão secreta VIP
            if UserQueries.is_vip(helper_id):
                await self._check_help_mission(helper_id, interaction.user.id)
            return
        
        # Avança o progresso da missão
        new_progress = mentor_mission.get('progress', 0) + 1
        target = mentor_mission.get('target', 2)
        
        if new_progress >= target:
            # Completa a missão
            MissionQueries.complete_mission(mentor_mission['id'])
            xp_reward = config.WEEKLY_MISSIONS.get('mentor_fantasma', {}).get('xp_reward', 100)
            coins_reward = config.WEEKLY_MISSIONS.get('mentor_fantasma', {}).get('coins_reward', 10)
            UserQueries.update_xp(helper_id, xp_reward)
            UserQueries.update_coins(helper_id, coins_reward)
            
            embed = discord.Embed(
                title="🎉 Missão Completa!",
                description=f"**{interaction.user.display_name}** confirmou que {membro.mention} o(a) ajudou!\n\n"
                           f"**{membro.display_name}** completou a missão **Mentor Fantasma**! 🎯",
                color=config.EMBED_COLOR_SUCCESS
            )
            embed.add_field(name="Recompensas", value=f"+{xp_reward} XP | +{coins_reward} 🪙")
            embed.set_footer(text="Use /ajudou para agradecer quem te ajuda!")
        else:
            # Atualiza progresso
            MissionQueries.update_mission_progress(mentor_mission['id'], new_progress)
            
            embed = discord.Embed(
                title="🤝 Ajuda Registrada!",
                description=f"**{interaction.user.display_name}** confirmou que {membro.mention} o(a) ajudou!\n\n"
                           f"**Progresso da missão Mentor Fantasma:** {new_progress}/{target}",
                color=config.EMBED_COLOR_PRIMARY
            )
            embed.set_footer(text="Use /ajudou para agradecer quem te ajuda!")
        
        await interaction.followup.send(embed=embed)
        
        # Verifica missão secreta 2 para VIPs
        if UserQueries.is_vip(helper_id):
            await self._check_help_mission(helper_id, interaction.user.id)
    
    async def _check_activity_streak_mission(self, user_id: int):
        """
        Verifica e atualiza progresso da missão secreta 'Atividade Consistente'.
        Chamado após qualquer atividade (mensagem, call, post).
        """
        # Busca missão secreta ativa
        secret_missions = MissionQueries.get_active_missions(user_id, 'secret')
        activity_mission = next((m for m in secret_missions if m.get('mission_id') == 'secreta_1'), None)
        
        if not activity_mission or activity_mission.get('status') == 'completed':
            return
        
        # Calcula dias consecutivos de atividade
        consecutive_days = ActivityQueries.get_consecutive_activity_days(user_id)
        target = activity_mission.get('target', 5)
        
        # Atualiza progresso apenas se aumentou
        current_progress = activity_mission.get('progress', 0)
        if consecutive_days > current_progress:
            if consecutive_days >= target:
                # Completa a missão!
                MissionQueries.complete_mission(activity_mission['id'])
                xp_reward = activity_mission.get('xp_reward', 50)
                UserQueries.update_xp(user_id, xp_reward)
                print(f"⭐ User {user_id} completou missão secreta: Atividade Consistente! +{xp_reward} XP")
            else:
                MissionQueries.update_mission_progress(activity_mission['id'], consecutive_days)
    
    async def _check_help_mission(self, helper_id: int, helped_member_id: int):
        """
        Verifica e atualiza progresso da missão secreta 'Mentor da Comunidade'.
        Chamado após cada /ajudou.
        """
        # Busca missão secreta ativa
        secret_missions = MissionQueries.get_active_missions(helper_id, 'secret')
        help_mission = next((m for m in secret_missions if m.get('mission_id') == 'secreta_2'), None)
        
        if not help_mission or help_mission.get('status') == 'completed':
            return
        
        # Conta membros únicos ajudados
        unique_helped = ActivityQueries.get_unique_helped_members(helper_id, days=7)
        unique_count = len(unique_helped)
        target = help_mission.get('target', 3)
        
        # Atualiza progresso
        current_progress = help_mission.get('progress', 0)
        if unique_count > current_progress:
            if unique_count >= target:
                # Completa a missão!
                MissionQueries.complete_mission(help_mission['id'])
                xp_reward = help_mission.get('xp_reward', 50)
                UserQueries.update_xp(helper_id, xp_reward)
                print(f"⭐ User {helper_id} completou missão secreta: Mentor da Comunidade! +{xp_reward} XP")
            else:
                MissionQueries.update_mission_progress(help_mission['id'], unique_count)


async def setup(bot: commands.Bot):
    await bot.add_cog(MissionsCog(bot))

