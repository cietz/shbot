"""
🦈 SharkClub Discord Bot - Cooldown Manager
Sistema de gerenciamento de cooldowns
"""

from datetime import datetime, timezone, timedelta
from typing import Tuple
from database.queries import CooldownQueries


class CooldownManager:
    """Gerencia cooldowns de ações"""
    
    # Tipos de ações e seus cooldowns em segundos (FREE)
    COOLDOWN_TYPES = {
        'checkin': 20 * 3600,       # 20 horas
        'roulette': 24 * 3600,      # 24 horas
        'scratch': 7 * 24 * 3600,   # 7 dias (1 por semana)
        'message_xp': 60,           # 1 minuto
        'voice_xp': 300,            # 5 minutos
    }
    
    # Cooldowns reduzidos para VIPs
    VIP_COOLDOWN_TYPES = {
        'checkin': 16 * 3600,       # 16 horas (VIP)
        'roulette': 20 * 3600,      # 20 horas (VIP) - Free: 24h
        'scratch': 5 * 24 * 3600,   # 5 dias (VIP) - Free: 7 dias
        'message_xp': 60,           # igual
        'voice_xp': 300,            # igual
    }
    
    @staticmethod
    def check(user_id: int, action: str, override_seconds: int = None, is_vip: bool = False) -> Tuple[bool, int]:
        """
        Verifica se ação pode ser executada.
        Retorna (pode_executar, segundos_restantes)
        
        Args:
            user_id: ID do usuário
            action: Tipo de ação
            override_seconds: Cooldown customizado (ignora COOLDOWN_TYPES se fornecido)
            is_vip: Se True, usa cooldowns VIP reduzidos
        """
        if override_seconds is not None:
            cooldown_seconds = override_seconds
        elif is_vip and action in CooldownManager.VIP_COOLDOWN_TYPES:
            cooldown_seconds = CooldownManager.VIP_COOLDOWN_TYPES.get(action, 0)
        else:
            cooldown_seconds = CooldownManager.COOLDOWN_TYPES.get(action, 0)
        return CooldownQueries.check_cooldown(user_id, action, cooldown_seconds)
    
    @staticmethod
    def set(user_id: int, action: str) -> None:
        """Define cooldown para uma ação"""
        CooldownQueries.set_cooldown(user_id, action)
    
    @staticmethod
    def format_remaining(seconds: int) -> str:
        """Formata tempo restante para exibição"""
        if seconds <= 0:
            return "Disponível!"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            return f"{days}d {hours}h {minutes}min"
        elif hours > 0:
            return f"{hours}h {minutes}min"
        else:
            return f"{minutes}min"
    
    @staticmethod
    def get_next_available(user_id: int, action: str) -> datetime:
        """Retorna quando a ação estará disponível"""
        can_execute, remaining = CooldownManager.check(user_id, action)
        
        if can_execute:
            return datetime.now(timezone.utc)
        
        return datetime.now(timezone.utc) + timedelta(seconds=remaining)
