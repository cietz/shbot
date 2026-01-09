"""
🦈 SharkClub Discord Bot - Embeds
Embeds formatados para Discord
"""

import discord
from typing import Optional, List, Dict, Any
from datetime import datetime
import config
from .xp_calculator import XPCalculator


class SharkEmbeds:
    """Cria embeds temáticos do SharkClub"""
    
    @staticmethod
    def profile(user: discord.User, data: Dict[str, Any], rank: int, badges: List[Dict[str, Any]]) -> discord.Embed:
        """Embed do perfil do usuário"""
        level = data.get('level', 1)
        xp = data.get('xp', 0)
        streak = data.get('current_streak', 0)
        coins = data.get('coins', 0)
        is_vip = data.get('is_vip', False)
        
        # Calcula progresso
        xp_in_level, xp_needed, percentage = XPCalculator.get_level_progress(xp, level)
        progress_bar = XPCalculator.generate_progress_bar(percentage)
        badge_name = XPCalculator.get_badge_name(level)
        
        # Define cor e título baseado no VIP
        if is_vip:
            embed_color = config.EMBED_COLOR_VIP
            title_prefix = f"{config.EMOJI_VIP} "
            vip_badge = config.VIP_PROFILE_BADGE
        else:
            embed_color = config.EMBED_COLOR_PRIMARY
            title_prefix = f"{config.EMOJI_SHARK} "
            vip_badge = ""
        
        embed = discord.Embed(
            title=f"{title_prefix}Perfil de {user.display_name}",
            color=embed_color
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Status VIP/Free
        if is_vip:
            vip_status = f"{config.EMOJI_VIP} **VIP**"
            vip_expires_at = data.get('vip_expires_at')
            if vip_expires_at:
                try:
                    from datetime import datetime, timezone
                    expires_dt = datetime.fromisoformat(vip_expires_at.replace('Z', '+00:00'))
                    remaining = (expires_dt - datetime.now(timezone.utc)).days
                    vip_status += f" ({remaining} dias)"
                except:
                    pass
            else:
                vip_status += " (Permanente ♾️)"
        else:
            vip_status = f"{config.EMOJI_FREE} Free"
        
        embed.add_field(
            name="📋 Status",
            value=vip_status,
            inline=True
        )
        
        # Nível e Badge
        embed.add_field(
            name=f"{config.EMOJI_LEVEL} Nível {level}",
            value=f"{badge_name}\n{XPCalculator.get_badge_description(level)}",
            inline=True
        )
        
        # Ranking (com emblema VIP)
        rank_display = f"#{rank}"
        if is_vip:
            rank_display = f"👑 #{rank}"
        
        embed.add_field(
            name="🏆 Ranking",
            value=rank_display,
            inline=True
        )
        
        # XP
        if level < 10:
            xp_text = f"{XPCalculator.format_xp(xp_in_level)}/{XPCalculator.format_xp(xp_needed)}"
        else:
            xp_text = f"{XPCalculator.format_xp(xp)} (MAX)"
        
        embed.add_field(
            name=f"{config.EMOJI_XP} Experiência",
            value=f"{progress_bar}\n{xp_text}",
            inline=True
        )
        
        # Streak
        embed.add_field(
            name=f"{config.EMOJI_STREAK} Streak",
            value=f"{streak} dias\nRecorde: {data.get('longest_streak', 0)} dias",
            inline=True
        )
        
        # Moedas
        embed.add_field(
            name=f"{config.EMOJI_COINS} Moedas",
            value=f"{coins:,}",
            inline=True
        )
        
        # Insígnias (com badge VIP se aplicável)
        badge_list = [b.get('badge_name', '') for b in badges[:5]] if badges else []
        if is_vip and vip_badge not in badge_list:
            badge_list.insert(0, vip_badge)
        
        if badge_list:
            badges_text = " ".join(badge_list) if badge_list else "Nenhuma"
            embed.add_field(
                name=f"{config.EMOJI_BADGE} Insígnias ({len(badges) + (1 if is_vip else 0)})",
                value=badges_text,
                inline=False
            )
        
        # Bônus VIP ativos
        if is_vip:
            embed.add_field(
                name="⚡ Bônus VIP Ativos",
                value=f"• {config.VIP_XP_MULTIPLIER}x XP\n• {int(config.VIP_COINS_MULTIPLIER)}x Moedas\n• Cooldowns Reduzidos",
                inline=False
            )
        
        embed.set_footer(text="SharkClub • Sistema de Gamificação")
        embed.timestamp = datetime.now()
        
        return embed
    
    @staticmethod
    def checkin_success(user: discord.User, xp_earned: int, streak: int, total_xp: int, new_level: Optional[int] = None) -> discord.Embed:
        """Embed de check-in bem-sucedido"""
        embed = discord.Embed(
            title=f"{config.EMOJI_CHECKIN} Check-in Realizado!",
            description=f"Bem-vindo de volta, **{user.display_name}**!",
            color=config.EMBED_COLOR_SUCCESS
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
            value=f"{XPCalculator.format_xp(total_xp)}",
            inline=True
        )
        
        if new_level:
            embed.add_field(
                name="🎉 LEVEL UP!",
                value=f"Você alcançou o **Nível {new_level}**!\n{XPCalculator.get_badge_name(new_level)}",
                inline=False
            )
            embed.color = config.EMBED_COLOR_GOLD
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Continue assim! Volte amanhã para manter seu streak.")
        
        return embed
    
    @staticmethod
    def checkin_cooldown(remaining_hours: int, remaining_minutes: int) -> discord.Embed:
        """Embed de cooldown do check-in"""
        embed = discord.Embed(
            title=f"{config.EMOJI_SHARK} Aguarde!",
            description=f"Você já fez check-in hoje.\nVolte em **{remaining_hours}h {remaining_minutes}min**.",
            color=config.EMBED_COLOR_WARNING
        )
        return embed
    
    @staticmethod
    def level_up(user: discord.User, old_level: int, new_level: int) -> discord.Embed:
        """Embed de level up"""
        embed = discord.Embed(
            title="🎉 LEVEL UP! 🎉",
            description=f"**{user.display_name}** subiu de nível!",
            color=config.EMBED_COLOR_GOLD
        )
        
        embed.add_field(
            name="Antes",
            value=f"Nível {old_level}\n{XPCalculator.get_badge_name(old_level)}",
            inline=True
        )
        
        embed.add_field(
            name="➡️",
            value="",
            inline=True
        )
        
        embed.add_field(
            name="Agora",
            value=f"Nível {new_level}\n{XPCalculator.get_badge_name(new_level)}",
            inline=True
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Parabéns pela conquista!")
        
        return embed
    
    @staticmethod
    def ranking(users: List[Dict[str, Any]], title: str = "Ranking de XP") -> discord.Embed:
        """Embed de ranking"""
        embed = discord.Embed(
            title=f"🏆 {title}",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        
        for i, user_data in enumerate(users[:10]):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            username = user_data.get('username', 'Usuário')
            xp = user_data.get('xp', 0)
            level = user_data.get('level', 1)
            
            lines.append(f"{medal} {username} • Lv.{level} • {XPCalculator.format_xp(xp)} XP")
        
        embed.description = "\n".join(lines) if lines else "Nenhum usuário encontrado."
        embed.set_footer(text="SharkClub Rankings")
        embed.timestamp = datetime.now()
        
        return embed
    
    @staticmethod
    def roulette_spin(user: discord.User, prize: Dict[str, Any], xp_before: int, xp_after: int) -> discord.Embed:
        """Embed do resultado da roleta"""
        embed = discord.Embed(
            title=f"🎰 Roleta da Fortuna Shark!",
            description=f"**{user.display_name}** girou a roleta...",
            color=config.EMBED_COLOR_GOLD
        )
        
        prize_emoji = prize.get('emoji', '🎁')
        prize_name = prize.get('name', 'Prêmio')
        prize_type = prize.get('type', 'xp')
        prize_value = prize.get('value', 0)
        
        if prize_type == 'xp':
            value_text = f"+{prize_value} XP"
        elif prize_type == 'coins':
            value_text = f"+{prize_value} moedas"
        elif prize_type == 'booster':
            duration = prize.get('duration', 3600) // 60
            value_text = f"{prize_value}x XP por {duration} minutos"
        else:
            value_text = prize_name
        
        embed.add_field(
            name=f"{prize_emoji} Prêmio",
            value=f"**{prize_name}**\n{value_text}",
            inline=False
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Volte amanhã para girar novamente!")
        
        return embed
    
    @staticmethod
    def mystery_box(user: discord.User, box_type: str, rewards: List[str]) -> discord.Embed:
        """Embed de abertura de caixa misteriosa"""
        box_config = config.MYSTERY_BOX_TYPES.get(box_type, config.MYSTERY_BOX_TYPES['normal'])
        
        embed = discord.Embed(
            title=f"{box_config['emoji']} {box_config['name']} Aberta!",
            description=f"**{user.display_name}** abriu uma caixa misteriosa!",
            color=config.EMBED_COLOR_LEGENDARY if box_type == 'legendary' else config.EMBED_COLOR_GOLD
        )
        
        rewards_text = "\n".join([f"• {r}" for r in rewards])
        embed.add_field(
            name="🎁 Recompensas",
            value=rewards_text,
            inline=False
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        return embed
    
    @staticmethod
    def scratch_card(user: discord.User, result: Dict[str, Any]) -> discord.Embed:
        """Embed de raspadinha"""
        is_jackpot = result.get('name') == 'Jackpot Megalodon'
        
        embed = discord.Embed(
            title=f"🎟️ Raspadinha Shark!",
            description=f"**{user.display_name}** raspou o cartão...",
            color=config.EMBED_COLOR_LEGENDARY if is_jackpot else config.EMBED_COLOR_PRIMARY
        )
        
        emoji = result.get('emoji', '🎫')
        name = result.get('name', 'Prêmio')
        xp = result.get('xp', 0)
        
        if is_jackpot:
            embed.add_field(
                name=f"{emoji} JACKPOT!!! {emoji}",
                value=f"**{name}**\n+{xp} XP\n🏅 Insígnia ultra rara desbloqueada!",
                inline=False
            )
        else:
            embed.add_field(
                name=f"{emoji} Resultado",
                value=f"**{name}**\n+{xp} XP",
                inline=False
            )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Novo ticket disponível em 3 dias de presença!")
        
        return embed
    
    @staticmethod
    def missions(daily: List[Dict], weekly: List[Dict], secret: List[Dict]) -> discord.Embed:
        """Embed de missões"""
        embed = discord.Embed(
            title=f"{config.EMOJI_MISSION} Suas Missões",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        # Missões Diárias
        if daily:
            daily_text = ""
            for m in daily:
                status = "✅" if m.get('status') == 'completed' else "⬜"
                progress = f"{m.get('progress', 0)}/{m.get('target', 1)}"
                daily_text += f"{status} {m.get('mission_id')} [{progress}] (+{m.get('xp_reward', 0)} XP)\n"
            embed.add_field(name="📅 Diárias", value=daily_text or "Nenhuma", inline=False)
        
        # Missões Semanais
        if weekly:
            weekly_text = ""
            for m in weekly:
                status = "✅" if m.get('status') == 'completed' else "⬜"
                progress = f"{m.get('progress', 0)}/{m.get('target', 1)}"
                weekly_text += f"{status} {m.get('mission_id')} [{progress}] (+{m.get('xp_reward', 0)} XP)\n"
            embed.add_field(name="📆 Semanais", value=weekly_text or "Nenhuma", inline=False)
        
        # Missões Secretas
        if secret:
            secret_text = ""
            for m in secret:
                status = "✅" if m.get('status') == 'completed' else "🔒"
                progress = f"{m.get('progress', 0)}/{m.get('target', 1)}"
                secret_text += f"{status} {m.get('mission_id')} [{progress}] (+{m.get('xp_reward', 0)} XP)\n"
            embed.add_field(name="⭐ Secretas", value=secret_text or "Complete todas as semanais!", inline=False)
        
        embed.set_footer(text="Use /missoes para ver detalhes")
        embed.timestamp = datetime.now()
        
        return embed
    
    @staticmethod
    def error(message: str) -> discord.Embed:
        """Embed de erro"""
        return discord.Embed(
            title="❌ Erro",
            description=message,
            color=config.EMBED_COLOR_ERROR
        )
    
    @staticmethod
    def success(title: str, message: str) -> discord.Embed:
        """Embed de sucesso"""
        return discord.Embed(
            title=f"✅ {title}",
            description=message,
            color=config.EMBED_COLOR_SUCCESS
        )
