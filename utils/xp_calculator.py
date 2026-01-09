"""
🦈 SharkClub Discord Bot - XP Calculator
Cálculos de XP, níveis e progressão
"""

from typing import Tuple, Optional
import config


class XPCalculator:
    """Gerencia cálculos de XP e níveis"""
    
    @staticmethod
    def get_level_from_xp(xp: int) -> int:
        """Calcula o nível baseado no XP total"""
        level = 1
        for lvl, required_xp in sorted(config.XP_PER_LEVEL.items()):
            if xp >= required_xp:
                level = lvl
            else:
                break
        return level
    
    @staticmethod
    def get_xp_for_level(level: int) -> int:
        """Retorna XP necessário para alcançar determinado nível"""
        return config.XP_PER_LEVEL.get(level, 0)
    
    @staticmethod
    def get_xp_for_next_level(current_level: int) -> int:
        """Retorna XP necessário para o próximo nível"""
        next_level = min(current_level + 1, 10)
        return config.XP_PER_LEVEL.get(next_level, config.XP_PER_LEVEL[10])
    
    @staticmethod
    def get_level_progress(xp: int, level: int) -> Tuple[int, int, float]:
        """
        Calcula progresso dentro do nível atual.
        Retorna (xp_atual_no_nivel, xp_total_para_nivel, percentual)
        """
        current_level_xp = config.XP_PER_LEVEL.get(level, 0)
        next_level_xp = config.XP_PER_LEVEL.get(level + 1, config.XP_PER_LEVEL[10])
        
        # Se já é nível máximo
        if level >= 10:
            return xp - current_level_xp, 0, 1.0
        
        xp_in_level = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        percentage = xp_in_level / xp_needed if xp_needed > 0 else 1.0
        
        return xp_in_level, xp_needed, min(percentage, 1.0)
    
    @staticmethod
    def check_level_up(old_xp: int, new_xp: int) -> Tuple[bool, int, int]:
        """
        Verifica se houve level up.
        Retorna (subiu_de_nivel, nivel_antigo, nivel_novo)
        """
        old_level = XPCalculator.get_level_from_xp(old_xp)
        new_level = XPCalculator.get_level_from_xp(new_xp)
        
        return new_level > old_level, old_level, new_level
    
    @staticmethod
    def get_badge_name(level: int) -> str:
        """Retorna nome da insígnia para determinado nível"""
        return config.BADGE_NAMES.get(level, config.BADGE_NAMES[1])
    
    @staticmethod
    def get_badge_description(level: int) -> str:
        """Retorna descrição da insígnia para determinado nível"""
        return config.BADGE_DESCRIPTIONS.get(level, config.BADGE_DESCRIPTIONS[1])
    
    @staticmethod
    def calculate_checkin_xp(streak: int) -> int:
        """Calcula XP do check-in baseado no streak"""
        base_xp = config.CHECKIN_BASE_XP
        bonus = config.CHECKIN_STREAK_BONUS * streak
        return min(base_xp + bonus, config.CHECKIN_MAX_XP)
    
    @staticmethod
    def apply_multiplier(xp: int, multiplier: float) -> int:
        """Aplica multiplicador de XP"""
        return int(xp * multiplier)
    
    @staticmethod
    def generate_progress_bar(percentage: float, length: int = 10) -> str:
        """Gera barra de progresso visual"""
        filled = int(percentage * length)
        empty = length - filled
        
        bar = "█" * filled + "░" * empty
        return f"[{bar}]"
    
    @staticmethod
    def format_xp(xp: int) -> str:
        """Formata XP para exibição (ex: 1.5K, 2.3M)"""
        if xp >= 1_000_000:
            return f"{xp / 1_000_000:.1f}M"
        elif xp >= 1_000:
            return f"{xp / 1_000:.1f}K"
        return str(xp)
    
    @staticmethod
    def get_cargo_name(level: int) -> str:
        """Retorna nome do cargo para determinado nível"""
        return config.CARGO_NAMES.get(level, config.CARGO_NAMES[1])
    
    @staticmethod
    def get_cargo_emoji(level: int) -> str:
        """Retorna emoji do cargo para determinado nível"""
        return config.CARGO_EMOJIS.get(level, config.CARGO_EMOJIS[1])
    
    @staticmethod
    def get_cargo_color(level: int) -> int:
        """Retorna cor do cargo para determinado nível"""
        return config.CARGO_COLORS.get(level, config.CARGO_COLORS[1])
    
    @staticmethod
    def get_level_info(level: int) -> dict:
        """Retorna informações completas do nível"""
        return {
            'level': level,
            'cargo_name': config.CARGO_NAMES.get(level, ''),
            'badge_name': config.BADGE_NAMES.get(level, ''),
            'description': config.BADGE_DESCRIPTIONS.get(level, ''),
            'emoji': config.CARGO_EMOJIS.get(level, ''),
            'color': config.CARGO_COLORS.get(level, 0x808080),
            'xp_required': config.XP_PER_LEVEL.get(level, 0),
            'xp_next': config.XP_PER_LEVEL.get(level + 1, 30000),
        }
    
    @staticmethod
    def get_xp_to_next_level(xp: int, level: int) -> int:
        """Retorna quanto XP falta para o próximo nível"""
        if level >= 10:
            return 0
        next_level_xp = config.XP_PER_LEVEL.get(level + 1, 30000)
        return max(0, next_level_xp - xp)
    
    @staticmethod
    def get_all_levels_info() -> list:
        """Retorna lista com informações de todos os níveis"""
        levels = []
        for level in range(1, 11):
            info = XPCalculator.get_level_info(level)
            levels.append(info)
        return levels

