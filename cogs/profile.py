"""
🦈 SharkClub Discord Bot - Profile Cog
Comandos de perfil, badges e streak
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from database.queries import UserQueries, BadgeQueries
from utils.embeds import SharkEmbeds
from utils.xp_calculator import XPCalculator
import config


class ProfileCog(commands.Cog):
    """Comandos relacionados ao perfil do usuário"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="perfil", description="Ver seu perfil ou de outro membro")
    @app_commands.describe(membro="Membro para ver o perfil (opcional)")
    async def perfil(self, interaction: discord.Interaction, membro: Optional[discord.Member] = None):
        """Exibe o perfil do usuário"""
        await interaction.response.defer(ephemeral=True)
        
        target = membro or interaction.user
        is_self = target.id == interaction.user.id
        
        # Busca ou cria usuário
        user_data = UserQueries.get_or_create_user(target.id, target.display_name)
        
        # Busca ranking e badges
        rank = UserQueries.get_user_rank(target.id)
        badges = BadgeQueries.get_user_badges(target.id)
        
        # Cria embed
        embed = SharkEmbeds.profile(target, user_data, rank, badges)
        
        # Responde
        await interaction.followup.send(embed=embed, ephemeral=is_self)
    
    @app_commands.command(name="badges", description="Ver todas as insígnias disponíveis")
    async def badges(self, interaction: discord.Interaction):
        """Lista todas as insígnias do sistema"""
        embed = discord.Embed(
            title=f"{config.EMOJI_BADGE} Insígnias do SharkClub",
            description="Suba de nível para desbloquear novas insígnias!",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        # Insígnias de nível
        badges_text = ""
        for level in range(1, 11):
            badge_name = XPCalculator.get_badge_name(level)
            badge_desc = XPCalculator.get_badge_description(level)
            xp_needed = config.XP_PER_LEVEL[level]
            badges_text += f"**Lv.{level}** {badge_name}\n└ {badge_desc} ({xp_needed:,} XP)\n"
        
        embed.add_field(
            name="📊 Insígnias de Nível",
            value=badges_text,
            inline=False
        )
        
        # Busca insígnias do usuário
        user_badges = BadgeQueries.get_user_badges(interaction.user.id)
        if user_badges:
            owned = [b.get('badge_name', '') for b in user_badges]
            embed.add_field(
                name=f"✅ Suas Insígnias ({len(user_badges)})",
                value=" ".join(owned) or "Nenhuma",
                inline=False
            )
        
        embed.set_footer(text="Continue participando para ganhar insígnias especiais!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="streak", description="Ver seu streak de check-in")
    async def streak(self, interaction: discord.Interaction):
        """Mostra informações de streak do usuário"""
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        
        current = user_data.get('current_streak', 0)
        longest = user_data.get('longest_streak', 0)
        
        # Determina status do streak
        if current >= longest and current > 0:
            status = "🏆 Recorde atual!"
        elif current > 0:
            status = f"🎯 Faltam {longest - current} dias para o recorde"
        else:
            status = "💤 Faça check-in para iniciar!"
        
        embed = discord.Embed(
            title=f"{config.EMOJI_STREAK} Streak de {interaction.user.display_name}",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        # Barra de progresso visual
        flames = "🔥" * min(current, 10) if current > 0 else "❄️"
        
        embed.add_field(
            name="Streak Atual",
            value=f"**{current}** dias\n{flames}",
            inline=True
        )
        
        embed.add_field(
            name="Recorde",
            value=f"**{longest}** dias\n👑",
            inline=True
        )
        
        embed.add_field(
            name="Status",
            value=status,
            inline=False
        )
        
        # Recompensas por manter streak
        embed.add_field(
            name="💰 Bônus por Streak",
            value=f"+{config.CHECKIN_STREAK_BONUS} XP por dia de streak\nMáximo: {config.CHECKIN_MAX_XP} XP/check-in",
            inline=False
        )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="O streak reseta após 72h sem check-in")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="saldo", description="Ver seu XP, moedas e nível atual")
    async def saldo(self, interaction: discord.Interaction):
        """Mostra saldo rápido do usuário"""
        await interaction.response.defer(ephemeral=True)
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        
        xp = user_data.get('xp', 0)
        level = user_data.get('level', 1)
        coins = user_data.get('coins', 0)
        streak = user_data.get('current_streak', 0)
        is_vip = user_data.get('is_vip', False)
        
        # Calcula XP para próximo nível
        next_level = level + 1
        if next_level <= 10:
            xp_needed = config.XP_PER_LEVEL.get(next_level, 99999)
            xp_progress = xp - config.XP_PER_LEVEL.get(level, 0)
            xp_to_next = xp_needed - config.XP_PER_LEVEL.get(level, 0)
            progress_percent = min(100, int((xp_progress / xp_to_next) * 100)) if xp_to_next > 0 else 100
        else:
            xp_needed = 0
            progress_percent = 100
        
        # Barra de progresso visual
        filled = int(progress_percent / 10)
        progress_bar = "█" * filled + "░" * (10 - filled)
        
        # Badge atual
        badge_name = XPCalculator.get_badge_name(level)
        
        # Define cor baseado no VIP
        embed_color = config.EMBED_COLOR_VIP if is_vip else config.EMBED_COLOR_PRIMARY
        title_emoji = config.EMOJI_VIP if is_vip else "💰"
        
        embed = discord.Embed(
            title=f"{title_emoji} Saldo de {interaction.user.display_name}",
            color=embed_color
        )
        
        # Status VIP/Free
        if is_vip:
            vip_status = f"{config.EMOJI_VIP} VIP"
            vip_expires_at = user_data.get('vip_expires_at')
            if vip_expires_at:
                try:
                    from datetime import datetime, timezone
                    expires_dt = datetime.fromisoformat(vip_expires_at.replace('Z', '+00:00'))
                    remaining = (expires_dt - datetime.now(timezone.utc)).days
                    vip_status += f" ({remaining}d)"
                except:
                    pass
            else:
                vip_status += " ♾️"
        else:
            vip_status = f"{config.EMOJI_FREE} Free"
        
        embed.add_field(
            name="📋 Status",
            value=f"**{vip_status}**",
            inline=True
        )
        
        embed.add_field(
            name="📊 Nível",
            value=f"**{level}** {badge_name}",
            inline=True
        )
        
        embed.add_field(
            name="⭐ XP",
            value=f"**{xp:,}**",
            inline=True
        )
        
        embed.add_field(
            name="🪙 Moedas",
            value=f"**{coins:,}**",
            inline=True
        )
        
        embed.add_field(
            name="🔥 Streak",
            value=f"**{streak}** dias",
            inline=True
        )
        
        if next_level <= 10:
            embed.add_field(
                name=f"📈 Progresso para Lv.{next_level}",
                value=f"`{progress_bar}` {progress_percent}%\n{xp:,} / {xp_needed:,} XP",
                inline=False
            )
        else:
            embed.add_field(
                name="👑 Nível Máximo!",
                value="Você alcançou o nível máximo!",
                inline=False
            )
        
        # Verifica booster ativo
        booster = UserQueries.get_active_booster(interaction.user.id)
        if booster:
            remaining_min = booster['remaining_minutes']
            remaining_sec = booster['remaining_seconds'] % 60
            embed.add_field(
                name="🚀 BOOSTER ATIVO!",
                value=f"**{booster['multiplier']}x XP** por mais **{remaining_min}min {remaining_sec}s**",
                inline=False
            )
        
        # Bônus VIP
        if is_vip:
            embed.add_field(
                name="⚡ Bônus VIP",
                value=f"{config.VIP_XP_MULTIPLIER}x XP | {int(config.VIP_COINS_MULTIPLIER)}x Moedas",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="🦈 SharkClub")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="vip", description="Ver seu status VIP e benefícios disponíveis")
    async def vip(self, interaction: discord.Interaction):
        """Mostra status VIP e benefícios"""
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        is_vip = user_data.get('is_vip', False)
        
        if is_vip:
            # Usuário VIP
            embed = discord.Embed(
                title=f"{config.EMOJI_VIP} Você é VIP!",
                description="Aproveite todos os benefícios exclusivos!",
                color=config.EMBED_COLOR_VIP
            )
            
            # Status do VIP
            vip_expires_at = user_data.get('vip_expires_at')
            if vip_expires_at:
                try:
                    from datetime import datetime, timezone
                    expires_dt = datetime.fromisoformat(vip_expires_at.replace('Z', '+00:00'))
                    remaining = (expires_dt - datetime.now(timezone.utc)).days
                    status_text = f"⏰ Expira em **{remaining}** dias"
                except:
                    status_text = "⏰ VIP Temporário"
            else:
                status_text = "♾️ VIP **Permanente**"
            
            embed.add_field(
                name="📋 Status",
                value=status_text,
                inline=False
            )
            
            # Lista benefícios ativos
            benefits_text = "\n".join([f"✅ {b}" for b in config.VIP_BENEFITS])
            embed.add_field(
                name="🎁 Seus Benefícios Ativos",
                value=benefits_text,
                inline=False
            )
            
        else:
            # Usuário Free
            embed = discord.Embed(
                title=f"{config.EMOJI_FREE} Você é um usuário Free",
                description="Desbloqueie benefícios exclusivos com o VIP!",
                color=config.VIP_STATUS['free']['color']
            )
            
            # Lista benefícios disponíveis
            benefits_text = "\n".join([f"🔒 {b}" for b in config.VIP_BENEFITS])
            embed.add_field(
                name="🎁 Benefícios VIP Disponíveis",
                value=benefits_text,
                inline=False
            )
            
            embed.add_field(
                name="💡 Como obter VIP?",
                value="Entre em contato com a administração para adquirir o VIP!",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="🦈 SharkClub VIP System")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="niveis", description="Ver tabela de níveis e cargos")
    async def niveis(self, interaction: discord.Interaction):
        """Mostra a tabela completa de níveis e progressão"""
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        current_level = user_data.get('level', 1)
        current_xp = user_data.get('xp', 0)
        
        embed = discord.Embed(
            title="🏴‍☠️ Níveis e Cargos do SharkClub",
            description="Ganhe XP para subir de nível e desbloquear cargos!",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        # Lista todos os níveis
        levels_text = ""
        for level in range(1, 11):
            emoji = config.CARGO_EMOJIS.get(level, "")
            name = config.CARGO_NAMES.get(level, f"Nível {level}")
            xp_min = config.XP_PER_LEVEL.get(level, 0)
            xp_max = config.XP_PER_LEVEL.get(level + 1, 30000) if level < 10 else 30000
            
            # Marca o nível atual
            if level == current_level:
                marker = "➡️ "
                line = f"**{marker}{emoji} {name}** ({xp_min:,}-{xp_max:,} XP) 👈 Você está aqui!\n"
            elif level < current_level:
                marker = "✅ "
                line = f"{marker}{emoji} ~~{name}~~ (Conquistado!)\n"
            else:
                marker = "🔒 "
                line = f"{marker}{emoji} {name} ({xp_min:,}-{xp_max:,} XP)\n"
            
            levels_text += line
        
        embed.add_field(
            name="📋 Progressão de Níveis",
            value=levels_text,
            inline=False
        )
        
        # Progresso atual
        xp_to_next = XPCalculator.get_xp_to_next_level(current_xp, current_level)
        if current_level < 10:
            embed.add_field(
                name="📊 Seu Progresso",
                value=f"**Nível Atual:** {current_level} - {config.CARGO_NAMES.get(current_level)}\n"
                      f"**XP Atual:** {current_xp:,}\n"
                      f"**Falta para próximo nível:** {xp_to_next:,} XP",
                inline=False
            )
        else:
            embed.add_field(
                name="👑 Nível Máximo!",
                value=f"Parabéns! Você é **{config.CARGO_NAMES[10]}**!\nXP Total: {current_xp:,}",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="🦈 SharkClub - Sistema de Progressão")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))

