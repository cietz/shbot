"""
🦈 SharkClub Discord Bot - Check-in Cog
Sistema de check-in diário e streak com diferenciação FREE/VIP
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta

from database.queries import UserQueries, BadgeQueries, MissionQueries, DailyProgressQueries, RewardQueries
from utils.embeds import SharkEmbeds
from utils.xp_calculator import XPCalculator
from utils.cooldowns import CooldownManager
import config


# ═══════════════════════════════════════════════════════════════
# VIEW COM BOTÃO PARA CHECK-IN
# ═══════════════════════════════════════════════════════════════

class CheckinView(discord.ui.View):
    """View persistente com botão de check-in"""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)  # Persistente
        self.bot = bot
    
    @discord.ui.button(
        label="📅 Check-in Diário",
        style=discord.ButtonStyle.success,
        custom_id="checkin_daily",
        row=1
    )
    async def checkin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Realiza check-in via botão"""
        checkin_cog = self.bot.get_cog('CheckinCog')
        if checkin_cog:
            await checkin_cog._execute_checkin(interaction)
        else:
            await interaction.response.send_message("❌ Erro ao carregar check-in.", ephemeral=True)


class CheckinCog(commands.Cog):
    """Sistema de check-in diário"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Envia painel de check-in no canal apropriado"""
        import asyncio
        await asyncio.sleep(6)  # Aguarda setup de canais
        
        for guild in self.bot.guilds:
            await self._send_checkin_panel(guild)
    
    async def _send_checkin_panel(self, guild: discord.Guild):
        """Envia painel de check-in no canal de check-in"""
        # Busca o canal pelo ID fixo
        channel = self.bot.get_channel(config.CHANNEL_IDS.get("checkin"))
        
        if not channel:
            print(f"⚠️ Canal de check-in não encontrado (ID: {config.CHANNEL_IDS.get('checkin')})")
            return
        
        # Cria embed do painel
        embed = discord.Embed(
            title="📅 Check-in Diário SharkClub",
            description="Clique no botão abaixo para fazer seu check-in!\n\n"
                       "🔥 **Streaks** - Ganhe bônus por dias consecutivos\n"
                       "⭐ **XP Extra** - VIPs ganham mais XP\n"
                       "🎁 **Marcos** - Recompensas especiais em 7, 14 e 30 dias!",
            color=config.EMBED_COLOR_SUCCESS
        )
        embed.set_footer(text="🦈 SharkClub - Faça check-in todo dia!")
        
        # Cria view com botão
        view = CheckinView(self.bot)
        
        # Tenta encontrar mensagem existente
        try:
            async for message in channel.history(limit=10):
                if message.author == self.bot.user and message.embeds:
                    first_embed = message.embeds[0]
                    if first_embed.title and "Check-in" in first_embed.title:
                        await message.edit(embed=embed, view=view)
                        print(f"✅ Painel de check-in atualizado em {channel.name}")
                        return
            
            # Envia nova mensagem
            await channel.send(embed=embed, view=view)
            print(f"✅ Painel de check-in enviado para {channel.name}")
        except discord.Forbidden:
            print(f"❌ Sem permissão para enviar no canal {channel.name}")
        except Exception as e:
            print(f"❌ Erro ao enviar painel de check-in: {e}")
    
    @app_commands.command(name="admin-setup-checkin", description="[ADMIN] Reenviar o painel de check-in")
    async def admin_setup_checkin(self, interaction: discord.Interaction):
        """[ADMIN] Reenvia o painel de check-in no canal configurado"""
        # Verifica admin no DB
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        if not user_data.get('is_admin', False):
             await interaction.response.send_message("❌ Apenas administradores do bot podem usar este comando.", ephemeral=True)
             return

        await interaction.response.defer(ephemeral=True)
        await self._send_checkin_panel(interaction.guild)
        await interaction.followup.send("✅ Painel de check-in reenviado!", ephemeral=True)

    # Método interno para execução via botão
    async def _execute_checkin(self, interaction: discord.Interaction):
        """Executa check-in (usado por comando e botão)"""
        await self.checkin.callback(self, interaction)
    

    
    def get_cooldown_hours(self, is_vip: bool) -> int:
        """Retorna o cooldown de check-in baseado no status VIP"""
        return config.VIP_CHECKIN_COOLDOWN_HOURS if is_vip else config.FREE_CHECKIN_COOLDOWN_HOURS
    
    def get_base_xp(self, is_vip: bool) -> int:
        """Retorna o XP base de check-in baseado no status VIP"""
        return config.VIP_CHECKIN_XP if is_vip else config.FREE_CHECKIN_XP
    
    def check_streak_milestone(self, streak: int) -> dict:
        """Verifica se atingiu um marco de streak e retorna as recompensas"""
        if streak in config.STREAK_MILESTONES:
            return config.STREAK_MILESTONES[streak]
        return None
    
    @app_commands.command(name="checkin", description="Faça seu check-in diário e ganhe XP!")
    async def checkin(self, interaction: discord.Interaction):
        """Realiza o check-in diário"""
        # Defer para evitar timeout (resposta ephemeral)
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        username = interaction.user.display_name

        
        # Busca ou cria usuário
        user_data = UserQueries.get_or_create_user(user_id, username)
        is_vip = user_data.get('is_vip', False)
        
        # Determina cooldown baseado no VIP
        cooldown_hours = self.get_cooldown_hours(is_vip)
        cooldown_seconds = cooldown_hours * 3600
        
        # Verifica cooldown (ninguém ignora)
        can_checkin, remaining = CooldownManager.check(user_id, 'checkin', cooldown_seconds)
        
        if not can_checkin:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            embed = SharkEmbeds.checkin_cooldown(hours, minutes)
            # Cooldown é ephemeral para não poluir o chat
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Calcula streak
        last_checkin = user_data.get('last_checkin')
        current_streak = user_data.get('current_streak', 0)
        
        if last_checkin:
            # Converte para datetime se necessário
            if isinstance(last_checkin, str):
                last_checkin = datetime.fromisoformat(last_checkin.replace('Z', '+00:00'))
            
            # Verifica se perdeu o streak
            now = datetime.now(timezone.utc)
            hours_since_checkin = (now - last_checkin).total_seconds() / 3600
            
            if hours_since_checkin > config.STREAK_RESET_HOURS:
                # Reset de streak
                new_streak = 1
            else:
                # Continua streak
                new_streak = current_streak + 1
        else:
            # Primeiro check-in
            new_streak = 1
        
        # Calcula XP base (VIP ganha mais)
        base_xp = self.get_base_xp(is_vip)
        
        # Adiciona bônus de streak
        streak_bonus = new_streak * config.STREAK_XP_BONUS_PER_DAY
        xp_earned = base_xp + streak_bonus
        
        # Aplica multiplicador VIP se aplicável
        if is_vip:
            xp_earned = int(xp_earned * config.VIP_XP_MULTIPLIER)
        
        # Verifica se tem multiplicador de booster ativo
        booster = UserQueries.get_active_booster(user_id)
        if booster:
            xp_earned = int(xp_earned * booster['multiplier'])
        
        # Atualiza banco de dados
        old_xp = user_data.get('xp', 0)
        updated_user = UserQueries.update_checkin(user_id, new_streak, xp_earned)
        new_xp = old_xp + xp_earned
        
        # Marca check-in no progresso diário
        DailyProgressQueries.mark_checkin_done(user_id)
        
        # Define cooldown
        CooldownManager.set(user_id, 'checkin')
        
        # ═══════════════════════════════════════════════════════════════
        # GERAÇÃO AUTOMÁTICA DE MISSÕES NO CHECK-IN
        # ═══════════════════════════════════════════════════════════════
        
        # Busca missões ativas do usuário
        daily_missions = MissionQueries.get_active_missions(user_id, 'daily')
        weekly_missions = MissionQueries.get_active_missions(user_id, 'weekly')
        secret_missions = MissionQueries.get_active_missions(user_id, 'secret')
        
        # Se não tem missões diárias, tenta gerar
        if not daily_missions:
            missions_cog = self.bot.get_cog('MissionsCog')
            if missions_cog:
                daily_missions = await missions_cog.generate_daily_missions(user_id)
                print(f"📋 Geradas {len(daily_missions)} missões diárias para {username} via check-in")
        
        # Se não tem missões semanais, tenta gerar
        if not weekly_missions:
            missions_cog = self.bot.get_cog('MissionsCog')
            if missions_cog:
                weekly_missions = await missions_cog.generate_weekly_missions(user_id)
                print(f"📆 Geradas {len(weekly_missions)} missões semanais para {username} via check-in")
        
        # Se é VIP e não tem missões secretas, tenta gerar
        if is_vip and not secret_missions:
            missions_cog = self.bot.get_cog('MissionsCog')
            if missions_cog:
                secret_missions = await missions_cog.generate_secret_missions(user_id)
                if secret_missions:
                    print(f"⭐ Geradas {len(secret_missions)} missões secretas VIP para {username} via check-in")
        
        # Atualiza missão de check-in (se existir)
        for mission in daily_missions:
            if mission.get('mission_id') == 'daily_checkin' and mission.get('status') == 'active':
                new_progress = mission.get('progress', 0) + 1
                target = mission.get('target', 1)
                
                if new_progress >= target:
                    MissionQueries.complete_mission(mission['id'])
                    mission_xp = mission.get('xp_reward', 0)
                    UserQueries.update_xp(user_id, mission_xp)
                else:
                    MissionQueries.update_mission_progress(mission['id'], new_progress)
                break
        
        # Verifica level up
        leveled_up, old_level, new_level = XPCalculator.check_level_up(old_xp, new_xp)
        
        # Log para debug
        print(f"📊 Check-in: old_xp={old_xp}, new_xp={new_xp}, old_level={old_level}, new_level={new_level}, leveled_up={leveled_up}")
        
        # Concede badge de nível se subiu
        if leveled_up:
            print(f"🎉 {username} subiu de nível! {old_level} -> {new_level}")
            badge_name = XPCalculator.get_badge_name(new_level)
            BadgeQueries.award_badge(user_id, badge_name, 'level')
            
            # Atribui cargo automaticamente
            auto_setup_cog = self.bot.get_cog('AutoSetupCog')
            print(f"🔧 AutoSetupCog encontrado: {auto_setup_cog is not None}")
            if auto_setup_cog and interaction.guild:
                print(f"✅ Atribuindo cargo nível {new_level} para {username}")
                await auto_setup_cog.assign_level_role(interaction.user, new_level)
                # Envia notificação no canal de level-ups
                await auto_setup_cog.send_level_up_notification(
                    interaction.guild, interaction.user, old_level, new_level
                )
            else:
                print(f"❌ Não foi possível atribuir cargo: cog={auto_setup_cog}, guild={interaction.guild}")
        
        # Verifica se atingiu marco de streak
        milestone = self.check_streak_milestone(new_streak)
        milestone_rewards = None
        
        if milestone:
            milestone_rewards = milestone.copy()
            
            # Dá XP extra do marco
            UserQueries.update_xp(user_id, milestone['xp'])
            
            # Dá moedas do marco
            UserQueries.update_coins(user_id, milestone['coins'])
            
            # Dá badge do marco
            if 'badge' in milestone:
                BadgeQueries.award_badge(user_id, milestone['badge'], 'streak')
            
            # Dá lootbox se aplicável
            if milestone.get('lootbox'):
                RewardQueries.add_reward(user_id, 'mystery_box', 1)
            
            # Ativa booster se aplicável
            if 'booster' in milestone:
                booster_info = milestone['booster']
                duration_seconds = booster_info['duration_hours'] * 3600
                UserQueries.set_multiplier(user_id, booster_info['multiplier'], duration_seconds)
        
        # Cria embed de resposta
        embed = self.create_checkin_embed(
            interaction.user,
            xp_earned,
            new_streak,
            new_xp,
            is_vip,
            new_level if leveled_up else None,
            milestone_rewards
        )
        
        # Responde ephemeralmente (visível apenas para o user)
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Se subiu de nível, envia embed de level up também (ephemeral)
        if leveled_up:
            level_up_embed = SharkEmbeds.level_up(interaction.user, old_level, new_level)
            await interaction.followup.send(embed=level_up_embed, ephemeral=True)
    
    def create_checkin_embed(self, user: discord.User, xp_earned: int, streak: int, 
                             total_xp: int, is_vip: bool, new_level: int = None,
                             milestone_rewards: dict = None) -> discord.Embed:
        """Cria embed de check-in com informações VIP"""
        
        # Cor baseada no status VIP
        color = config.EMBED_COLOR_VIP if is_vip else config.EMBED_COLOR_SUCCESS
        status_emoji = config.EMOJI_VIP if is_vip else config.EMOJI_FREE
        
        embed = discord.Embed(
            title=f"{config.EMOJI_CHECKIN} Check-in Realizado! {status_emoji}",
            description=f"Bem-vindo de volta, **{user.display_name}**!",
            color=color
        )
        
        embed.add_field(
            name=f"{config.EMOJI_XP} XP Ganho",
            value=f"+{xp_earned} XP",
            inline=True
        )
        
        embed.add_field(
            name=f"{config.EMOJI_STREAK} Streak",
            value=f"🔥 {streak} dias",
            inline=True
        )
        
        embed.add_field(
            name="📊 XP Total",
            value=f"{total_xp:,}",
            inline=True
        )
        
        # Se é VIP, mostra bônus
        if is_vip:
            embed.add_field(
                name=f"{config.EMOJI_VIP} Bônus VIP Aplicados",
                value=f"• XP Base: {config.VIP_CHECKIN_XP}\n• Multiplicador: {config.VIP_XP_MULTIPLIER}x",
                inline=False
            )
        
        # Se atingiu marco de streak
        if milestone_rewards:
            rewards_text = f"**{milestone_rewards['name']}**\n"
            rewards_text += f"🎁 +{milestone_rewards['xp']} XP\n"
            rewards_text += f"🪙 +{milestone_rewards['coins']} Moedas\n"
            
            if milestone_rewards.get('badge'):
                rewards_text += f"🏅 Badge: {milestone_rewards['badge']}\n"
            
            if milestone_rewards.get('lootbox'):
                rewards_text += f"📦 +1 Caixa Misteriosa!\n"
            
            if 'booster' in milestone_rewards:
                booster = milestone_rewards['booster']
                rewards_text += f"🚀 Booster {booster['multiplier']}x por {booster['duration_hours']}h!"
            
            embed.add_field(
                name="🎉 MARCO DE STREAK!",
                value=rewards_text,
                inline=False
            )
            embed.color = config.EMBED_COLOR_GOLD
        
        # Level up
        if new_level:
            embed.add_field(
                name="🎉 LEVEL UP!",
                value=f"Você alcançou o **Nível {new_level}**!\n{XPCalculator.get_badge_name(new_level)}",
                inline=False
            )
            embed.color = config.EMBED_COLOR_GOLD
        
        # Próximo marco de streak
        next_milestones = [7, 14, 30]
        for m in next_milestones:
            if streak < m:
                days_until = m - streak
                embed.set_footer(text=f"🔥 Faltam {days_until} dias para o marco de {m} dias!")
                break
        else:
            embed.set_footer(text="🦈 Você é um verdadeiro Tubarão Frenético!")
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        return embed
    
    @app_commands.command(name="progresso", description="Ver seu progresso diário")
    async def progresso(self, interaction: discord.Interaction):
        """Mostra o progresso diário do usuário"""
        user_id = interaction.user.id
        username = interaction.user.display_name
        
        # Garante que usuário existe
        UserQueries.get_or_create_user(user_id, username)
        
        # Busca resumo diário
        summary = DailyProgressQueries.get_user_daily_summary(user_id)
        is_vip = summary['is_vip']
        
        # Cor baseada no status
        color = config.EMBED_COLOR_VIP if is_vip else config.EMBED_COLOR_PRIMARY
        status_emoji = config.EMOJI_VIP if is_vip else config.EMOJI_FREE
        
        embed = discord.Embed(
            title=f"📋 Progresso Diário {status_emoji}",
            description=f"**{username}** - {'VIP' if is_vip else 'Free'}",
            color=color
        )
        
        # Check-in
        checkin_status = "✅ Feito" if summary['checkin_done'] else "⬜ Pendente"
        embed.add_field(
            name="📅 Check-in Diário",
            value=checkin_status,
            inline=True
        )
        
        # Tempo Online
        if is_vip and config.FASTPASS_SKIPS_ONLINE_TIME:
            online_status = f"{config.EMOJI_FASTPASS} FastPass"
        else:
            online_pct = summary['online_progress_percent']
            online_bar = self.create_progress_bar(online_pct)
            online_status = f"{online_bar}\n{summary['online_minutes']}/{summary['online_required']} min"
            if summary['online_completed']:
                online_status = f"✅ Completo\n{summary['online_minutes']} min"
        
        embed.add_field(
            name="⏰ Tempo Online",
            value=online_status,
            inline=True
        )
        
        # Mensagens no Chat
        if is_vip and config.FASTPASS_SKIPS_CHAT_INTERACTION:
            chat_status = f"{config.EMOJI_FASTPASS} FastPass"
        else:
            if summary['messages_required'] == 0:
                chat_status = "✅ Sem requisito"
            else:
                chat_pct = summary['chat_progress_percent']
                chat_bar = self.create_progress_bar(chat_pct)
                chat_status = f"{chat_bar}\n{summary['messages_count']}/{summary['messages_required']} msgs"
                if summary['chat_completed']:
                    chat_status = f"✅ Completo\n{summary['messages_count']} msgs"
        
        embed.add_field(
            name="💬 Interação no Chat",
            value=chat_status,
            inline=True
        )
        
        # FastPass info para VIP
        if is_vip and summary['fastpass_active']:
            embed.add_field(
                name=f"{config.EMOJI_FASTPASS} FastPass Ativo",
                value="Você pula requisitos de tempo online e chat!",
                inline=False
            )
        
        # Dicas
        if not is_vip:
            embed.add_field(
                name="💡 Dica",
                value="VIPs têm requisitos reduzidos com FastPass!",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="🦈 SharkClub - Sistema de Gamificação")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def create_progress_bar(self, percent: int) -> str:
        """Cria uma barra de progresso visual"""
        filled = int(percent / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty + f" {percent}%"


async def setup(bot: commands.Bot):
    await bot.add_cog(CheckinCog(bot))
