"""
🦈 SharkClub Discord Bot - Ranking Cog
Sistema de rankings e leaderboards
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from database.queries import UserQueries
from utils.embeds import SharkEmbeds
import config


class RankingCog(commands.Cog):
    """Sistema de rankings"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="ranking", description="Ver o ranking do servidor")
    @app_commands.describe(categoria="Tipo de ranking")
    @app_commands.choices(categoria=[
        app_commands.Choice(name="XP Total", value="xp"),
        app_commands.Choice(name="Nível", value="level"),
        app_commands.Choice(name="Streak", value="current_streak"),
    ])
    async def ranking(self, interaction: discord.Interaction, categoria: Optional[str] = "xp"):
        """Mostra ranking do servidor"""
        order_field = categoria or "xp"
        
        # Títulos por categoria
        titles = {
            "xp": "🏆 Ranking de XP",
            "level": "📊 Ranking de Níveis",
            "current_streak": "🔥 Ranking de Streaks",
        }
        
        # Busca top 10
        top_users = UserQueries.get_top_users(limit=10, order_by=order_field)
        
        # Cria embed
        embed = SharkEmbeds.ranking(top_users, titles.get(order_field, "Ranking"))
        
        # Adiciona posição do usuário se não estiver no top 10
        user_rank = UserQueries.get_user_rank(interaction.user.id)
        if user_rank > 10:
            user_data = UserQueries.get_user(interaction.user.id)
            if user_data:
                value = user_data.get(order_field, 0)
                embed.add_field(
                    name="📍 Sua Posição",
                    value=f"#{user_rank} - {value}",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="Ver o Hall da Fama")
    async def leaderboard(self, interaction: discord.Interaction):
        """Hall da Fama do servidor"""
        embed = discord.Embed(
            title="🏆 Hall da Fama - SharkClub",
            description="Os maiores predadores do oceano do tráfego!",
            color=config.EMBED_COLOR_GOLD
        )
        
        # Top 3 por XP
        top_xp = UserQueries.get_top_users(limit=3, order_by='xp')
        if top_xp:
            medals = ["🥇", "🥈", "🥉"]
            xp_text = ""
            for i, u in enumerate(top_xp):
                xp_text += f"{medals[i]} **{u.get('username', 'Usuário')}** - Lv.{u.get('level', 1)} ({u.get('xp', 0):,} XP)\n"
            embed.add_field(name="⭐ Top XP", value=xp_text, inline=False)
        
        # Top 3 por Streak
        top_streak = UserQueries.get_top_users(limit=3, order_by='longest_streak')
        if top_streak:
            medals = ["🥇", "🥈", "🥉"]
            streak_text = ""
            for i, u in enumerate(top_streak):
                streak_text += f"{medals[i]} **{u.get('username', 'Usuário')}** - {u.get('longest_streak', 0)} dias\n"
            embed.add_field(name="🔥 Maiores Streaks", value=streak_text, inline=False)
        
        # Estatísticas gerais (simplificado)
        all_users = UserQueries.get_top_users(limit=1000, order_by='xp')
        total_users = len(all_users)
        total_xp = sum(u.get('xp', 0) for u in all_users)
        
        embed.add_field(
            name="📊 Estatísticas do Servidor",
            value=f"👥 {total_users} membros ativos\n⭐ {total_xp:,} XP total",
            inline=False
        )
        
        embed.set_footer(text="Continue participando para entrar no Hall da Fama!")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(RankingCog(bot))
