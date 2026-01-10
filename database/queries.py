"""
🦈 SharkClub Discord Bot - Database Queries
Queries para interação com Supabase
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from .connection import get_supabase


class UserQueries:
    """Queries relacionadas a usuários"""
    
    @staticmethod
    def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """Busca usuário pelo ID do Discord"""
        client = get_supabase()
        result = client.table('users').select('*').eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_user(user_id: int, username: str) -> Dict[str, Any]:
        """Cria novo usuário"""
        client = get_supabase()
        data = {
            'user_id': user_id,
            'username': username,
            'xp': 0,
            'level': 1,
            'current_streak': 0,
            'longest_streak': 0,
            'coins': 0,
            'xp_multiplier': 1.0,
            'is_vip': False,
        }
        result = client.table('users').insert(data).execute()
        return result.data[0] if result.data else data
    
    @staticmethod
    def get_or_create_user(user_id: int, username: str) -> Dict[str, Any]:
        """Busca usuário ou cria se não existir"""
        user = UserQueries.get_user(user_id)
        if not user:
            user = UserQueries.create_user(user_id, username)
        return user
    
    @staticmethod
    def update_xp(user_id: int, xp_amount: int, new_level: Optional[int] = None, apply_booster: bool = True) -> Dict[str, Any]:
        """Atualiza XP do usuário. Se apply_booster=True, aplica multiplicador ativo."""
        client = get_supabase()
        
        # Busca usuário atual
        user = UserQueries.get_user(user_id)
        if not user:
            return None
        
        # Aplica multiplicador se booster ativo
        final_xp = xp_amount
        if apply_booster and xp_amount > 0:
            booster = UserQueries.get_active_booster(user_id)
            if booster:
                final_xp = int(xp_amount * booster['multiplier'])
        
        new_xp = user['xp'] + final_xp
        
        # Se não foi passado um level, calcula automaticamente
        if new_level is None:
            from utils.xp_calculator import XPCalculator
            new_level = XPCalculator.get_level_from_xp(new_xp)
        
        update_data = {
            'xp': max(0, new_xp),
            'level': new_level  # Sempre atualiza o nível
        }
        
        result = client.table('users').update(update_data).eq('user_id', user_id).execute()
        
        # Retorna dados com info do XP ganho (para mostrar ao usuário)
        if result.data:
            result.data[0]['xp_gained'] = final_xp
            result.data[0]['xp_base'] = xp_amount
            result.data[0]['booster_applied'] = final_xp > xp_amount
        
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_checkin(user_id: int, new_streak: int, xp_earned: int) -> Dict[str, Any]:
        """Atualiza check-in e streak"""
        client = get_supabase()
        user = UserQueries.get_user(user_id)
        
        if not user:
            return None
        
        # Aplica multiplicador se booster ativo
        final_xp = xp_earned
        booster = UserQueries.get_active_booster(user_id)
        if booster and xp_earned > 0:
            final_xp = int(xp_earned * booster['multiplier'])
        
        new_xp = user['xp'] + final_xp
        longest = max(user.get('longest_streak', 0), new_streak)
        
        # Calcula o novo nível baseado no XP total
        from utils.xp_calculator import XPCalculator
        new_level = XPCalculator.get_level_from_xp(new_xp)
        
        update_data = {
            'xp': new_xp,
            'level': new_level,  # Sempre atualiza o nível
            'current_streak': new_streak,
            'longest_streak': longest,
            'last_checkin': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('users').update(update_data).eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_coins(user_id: int, coins_amount: int) -> Dict[str, Any]:
        """Atualiza moedas do usuário"""
        client = get_supabase()
        user = UserQueries.get_user(user_id)
        
        if not user:
            return None
        
        new_coins = max(0, user.get('coins', 0) + coins_amount)
        result = client.table('users').update({'coins': new_coins}).eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def set_multiplier(user_id: int, multiplier: float, duration_seconds: int) -> Dict[str, Any]:
        """Define multiplicador de XP temporário"""
        client = get_supabase()
        expires_at = datetime.now(timezone.utc).timestamp() + duration_seconds
        
        update_data = {
            'xp_multiplier': multiplier,
            'multiplier_expires_at': datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
        }
        
        result = client.table('users').update(update_data).eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_active_booster(user_id: int) -> Dict[str, Any]:
        """Verifica se o usuário tem booster ativo e retorna info"""
        user = UserQueries.get_user(user_id)
        if not user:
            return None
        
        multiplier = user.get('xp_multiplier', 1.0)
        expires_at_str = user.get('multiplier_expires_at')
        
        if not expires_at_str or multiplier <= 1.0:
            return None
        
        # Converte string ISO para datetime
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            if expires_at > now:
                remaining_seconds = int((expires_at - now).total_seconds())
                return {
                    'multiplier': multiplier,
                    'expires_at': expires_at,
                    'remaining_seconds': remaining_seconds,
                    'remaining_minutes': remaining_seconds // 60,
                }
            else:
                # Booster expirou, limpa
                client = get_supabase()
                client.table('users').update({
                    'xp_multiplier': 1.0,
                    'multiplier_expires_at': None
                }).eq('user_id', user_id).execute()
                return None
        except:
            return None
    
    @staticmethod
    def get_all_users() -> List[Dict[str, Any]]:
        """Busca todos os usuários de uma vez (para operações em lote)"""
        client = get_supabase()
        result = client.table('users').select('user_id, level, username').execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_all_user_ids() -> set:
        """Retorna set de todos os user_ids cadastrados no banco (otimizado para lookup)"""
        client = get_supabase()
        result = client.table('users').select('user_id').execute()
        return set(u['user_id'] for u in (result.data or []))
    
    @staticmethod
    def get_top_users(limit: int = 10, order_by: str = 'xp') -> List[Dict[str, Any]]:
        """Busca top usuários por XP ou outro campo"""
        client = get_supabase()
        result = client.table('users').select('*').order(order_by, desc=True).limit(limit).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_user_rank(user_id: int) -> int:
        """Retorna a posição do usuário no ranking de XP"""
        client = get_supabase()
        user = UserQueries.get_user(user_id)
        
        if not user:
            return 0
        
        # Conta quantos usuários têm mais XP
        result = client.table('users').select('user_id', count='exact').gt('xp', user['xp']).execute()
        return (result.count or 0) + 1
    
    # ═══════════════════════════════════════════════════════════════
    # SISTEMA VIP
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def is_vip(user_id: int) -> bool:
        """Verifica se o usuário é VIP (ativo)"""
        user = UserQueries.get_user(user_id)
        if not user:
            return False
        
        is_vip = user.get('is_vip', False)
        if not is_vip:
            return False
        
        # Verifica se VIP expirou
        vip_expires_at_str = user.get('vip_expires_at')
        if vip_expires_at_str:
            try:
                vip_expires_at = datetime.fromisoformat(vip_expires_at_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                
                if vip_expires_at < now:
                    # VIP expirou, remove o status
                    client = get_supabase()
                    client.table('users').update({
                        'is_vip': False,
                        'vip_expires_at': None
                    }).eq('user_id', user_id).execute()
                    return False
            except:
                pass
        
        return True
    
    @staticmethod
    def get_vip_info(user_id: int) -> Optional[Dict[str, Any]]:
        """Retorna informações detalhadas do VIP do usuário"""
        user = UserQueries.get_user(user_id)
        if not user:
            return None
        
        is_vip = UserQueries.is_vip(user_id)
        
        result = {
            'is_vip': is_vip,
            'vip_type': 'vip' if is_vip else 'free',
            'expires_at': None,
            'remaining_days': None,
            'is_permanent': False,
        }
        
        if is_vip:
            vip_expires_at_str = user.get('vip_expires_at')
            if vip_expires_at_str:
                try:
                    vip_expires_at = datetime.fromisoformat(vip_expires_at_str.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    remaining = vip_expires_at - now
                    result['expires_at'] = vip_expires_at
                    result['remaining_days'] = remaining.days
                except:
                    pass
            else:
                result['is_permanent'] = True
        
        return result
    
    @staticmethod
    def set_vip(user_id: int, duration_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Define usuário como VIP.
        duration_days: número de dias (None = permanente)
        """
        client = get_supabase()
        
        update_data = {'is_vip': True}
        
        if duration_days is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
            update_data['vip_expires_at'] = expires_at.isoformat()
        else:
            update_data['vip_expires_at'] = None  # Permanente
        
        result = client.table('users').update(update_data).eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def remove_vip(user_id: int) -> Dict[str, Any]:
        """Remove status VIP do usuário"""
        client = get_supabase()
        update_data = {
            'is_vip': False,
            'vip_expires_at': None
        }
        result = client.table('users').update(update_data).eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_all_vips() -> List[Dict[str, Any]]:
        """Retorna lista de todos os usuários VIP ativos"""
        client = get_supabase()
        result = client.table('users').select('*').eq('is_vip', True).execute()
        
        # Filtra apenas VIPs válidos (não expirados)
        vips = []
        for user in (result.data or []):
            vip_expires_at_str = user.get('vip_expires_at')
            if vip_expires_at_str:
                try:
                    vip_expires_at = datetime.fromisoformat(vip_expires_at_str.replace('Z', '+00:00'))
                    if vip_expires_at < datetime.now(timezone.utc):
                        continue  # VIP expirado
                except:
                    pass
            vips.append(user)
        
        return vips


class BadgeQueries:
    """Queries relacionadas a insígnias"""
    
    @staticmethod
    def get_user_badges(user_id: int) -> List[Dict[str, Any]]:
        """Busca todas as insígnias do usuário"""
        client = get_supabase()
        result = client.table('badges').select('*').eq('user_id', user_id).execute()
        return result.data if result.data else []
    
    @staticmethod
    def has_badge(user_id: int, badge_name: str) -> bool:
        """Verifica se usuário tem determinada insígnia"""
        client = get_supabase()
        result = client.table('badges').select('id').eq('user_id', user_id).eq('badge_name', badge_name).execute()
        return len(result.data) > 0 if result.data else False
    
    @staticmethod
    def award_badge(user_id: int, badge_name: str, badge_type: str = 'permanent', 
                    expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Concede insígnia ao usuário"""
        client = get_supabase()
        
        # Verifica se já tem a badge
        if BadgeQueries.has_badge(user_id, badge_name):
            return None
        
        data = {
            'user_id': user_id,
            'badge_name': badge_name,
            'badge_type': badge_type,
            'is_temporary': expires_at is not None,
            'expires_at': expires_at.isoformat() if expires_at else None,
        }
        
        result = client.table('badges').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def remove_badge(user_id: int, badge_name: str) -> bool:
        """Remove insígnia do usuário"""
        client = get_supabase()
        result = client.table('badges').delete().eq('user_id', user_id).eq('badge_name', badge_name).execute()
        return True


class MissionQueries:
    """Queries relacionadas a missões"""
    
    @staticmethod
    def get_active_missions(user_id: int, mission_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca missões ativas do usuário"""
        client = get_supabase()
        query = client.table('missions').select('*').eq('user_id', user_id).eq('status', 'active')
        
        if mission_type:
            query = query.eq('mission_type', mission_type)
        
        result = query.execute()
        return result.data if result.data else []
    
    @staticmethod
    def create_mission(user_id: int, mission_id: str, mission_type: str, 
                       target: int, xp_reward: int, expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Cria nova missão para o usuário"""
        client = get_supabase()
        
        data = {
            'user_id': user_id,
            'mission_id': mission_id,
            'mission_type': mission_type,
            'status': 'active',
            'progress': 0,
            'target': target,
            'xp_reward': xp_reward,
            'expires_at': expires_at.isoformat() if expires_at else None,
        }
        
        result = client.table('missions').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_mission_progress(mission_db_id: int, progress: int) -> Dict[str, Any]:
        """Atualiza progresso da missão"""
        client = get_supabase()
        result = client.table('missions').update({'progress': progress}).eq('id', mission_db_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def complete_mission(mission_db_id: int) -> Dict[str, Any]:
        """Marca missão como completa"""
        client = get_supabase()
        update_data = {
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('missions').update(update_data).eq('id', mission_db_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def expire_old_missions(mission_type: str = None):
        """Expira missões antigas (ativas com expires_at no passado)"""
        client = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        
        query = client.table('missions').update({'status': 'expired'}).eq('status', 'active').lt('expires_at', now)
        
        if mission_type:
            query = query.eq('mission_type', mission_type)
        
        result = query.execute()
        count = len(result.data) if result.data else 0
        if count > 0:
            print(f"⏰ {count} missões {mission_type or 'todas'} expiradas")
        return count
    
    @staticmethod
    def get_users_with_active_weekly_missions() -> set:
        """Retorna set de user_ids que já têm missões semanais ativas (busca em lote)"""
        client = get_supabase()
        result = client.table('missions').select('user_id').eq('status', 'active').eq('mission_type', 'weekly').execute()
        return set(m['user_id'] for m in (result.data or []))
    
    @staticmethod
    def create_missions_batch(missions_data: List[Dict[str, Any]]) -> int:
        """Cria múltiplas missões de uma vez (batch insert)"""
        if not missions_data:
            return 0
        client = get_supabase()
        result = client.table('missions').insert(missions_data).execute()
        return len(result.data) if result.data else 0


class RewardQueries:
    """Queries relacionadas a recompensas (caixas, tickets, etc)"""
    
    @staticmethod
    def get_reward(user_id: int, reward_type: str) -> Optional[Dict[str, Any]]:
        """Busca recompensa específica do usuário"""
        client = get_supabase()
        result = client.table('rewards').select('*').eq('user_id', user_id).eq('reward_type', reward_type).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def add_reward(user_id: int, reward_type: str, count: int = 1) -> Dict[str, Any]:
        """Adiciona recompensa ao usuário"""
        client = get_supabase()
        existing = RewardQueries.get_reward(user_id, reward_type)
        
        if existing:
            new_count = existing.get('available_count', 0) + count
            result = client.table('rewards').update({'available_count': new_count}).eq('id', existing['id']).execute()
        else:
            data = {
                'user_id': user_id,
                'reward_type': reward_type,
                'available_count': count,
            }
            result = client.table('rewards').insert(data).execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    def use_reward(user_id: int, reward_type: str) -> bool:
        """Usa uma recompensa (decrementa contador)"""
        client = get_supabase()
        existing = RewardQueries.get_reward(user_id, reward_type)
        
        if not existing or existing.get('available_count', 0) <= 0:
            return False
        
        new_count = existing['available_count'] - 1
        update_data = {
            'available_count': new_count,
            'last_used': datetime.now(timezone.utc).isoformat(),
        }
        client.table('rewards').update(update_data).eq('id', existing['id']).execute()
        return True


class CooldownQueries:
    """Queries relacionadas a cooldowns"""
    
    @staticmethod
    def get_cooldown(user_id: int, action_type: str) -> Optional[datetime]:
        """Retorna quando foi a última vez que a ação foi executada"""
        client = get_supabase()
        result = client.table('cooldowns').select('last_used').eq('user_id', user_id).eq('action_type', action_type).execute()
        
        if result.data and result.data[0].get('last_used'):
            return datetime.fromisoformat(result.data[0]['last_used'].replace('Z', '+00:00'))
        return None
    
    @staticmethod
    def set_cooldown(user_id: int, action_type: str) -> None:
        """Define cooldown para uma ação"""
        client = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        
        # Tenta atualizar, se não existir insere
        existing = client.table('cooldowns').select('id').eq('user_id', user_id).eq('action_type', action_type).execute()
        
        if existing.data:
            client.table('cooldowns').update({'last_used': now}).eq('user_id', user_id).eq('action_type', action_type).execute()
        else:
            client.table('cooldowns').insert({
                'user_id': user_id,
                'action_type': action_type,
                'last_used': now,
            }).execute()
    
    @staticmethod
    def check_cooldown(user_id: int, action_type: str, cooldown_seconds: int) -> tuple[bool, int]:
        """
        Verifica se ação está em cooldown.
        Retorna (can_execute, remaining_seconds)
        """
        last_used = CooldownQueries.get_cooldown(user_id, action_type)
        
        if not last_used:
            return True, 0
        
        now = datetime.now(timezone.utc)
        elapsed = (now - last_used).total_seconds()
        remaining = cooldown_seconds - elapsed
        
        if remaining <= 0:
            return True, 0
        
        return False, int(remaining)


class ActivityQueries:
    """Queries relacionadas ao monitoramento de atividade"""
    
    @staticmethod
    def log_activity(user_id: int, channel_id: int, activity_type: str, message_id: int = None) -> Dict[str, Any]:
        """Registra uma atividade do usuário"""
        client = get_supabase()
        data = {
            'user_id': user_id,
            'channel_id': channel_id,
            'activity_type': activity_type,  # 'post', 'comment', 'reaction'
            'message_id': message_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('activity_log').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_user_activity(user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Busca atividades do usuário nos últimos X dias"""
        client = get_supabase()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = client.table('activity_log').select('*').eq('user_id', user_id).gte('created_at', from_date).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_channel_activity_stats(channel_id: int, days: int = 7) -> Dict[str, int]:
        """Estatísticas de atividade de um canal"""
        client = get_supabase()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        result = client.table('activity_log').select('activity_type').eq('channel_id', channel_id).gte('created_at', from_date).execute()
        
        stats = {'posts': 0, 'comments': 0, 'reactions': 0, 'total': 0}
        if result.data:
            for item in result.data:
                activity_type = item.get('activity_type', '')
                if activity_type == 'post':
                    stats['posts'] += 1
                elif activity_type == 'comment':
                    stats['comments'] += 1
                elif activity_type == 'reaction':
                    stats['reactions'] += 1
                stats['total'] += 1
        
        return stats
    
    @staticmethod
    def get_user_activity_stats(user_id: int, days: int = 7) -> Dict[str, int]:
        """Estatísticas de atividade de um usuário"""
        client = get_supabase()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        result = client.table('activity_log').select('activity_type').eq('user_id', user_id).gte('created_at', from_date).execute()
        
        stats = {'posts': 0, 'comments': 0, 'reactions': 0, 'total': 0}
        if result.data:
            for item in result.data:
                activity_type = item.get('activity_type', '')
                if activity_type == 'post':
                    stats['posts'] += 1
                elif activity_type == 'comment':
                    stats['comments'] += 1
                elif activity_type == 'reaction':
                    stats['reactions'] += 1
                stats['total'] += 1
        
        return stats
    
    @staticmethod
    def get_top_active_users(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna os usuários mais ativos nos últimos X dias"""
        client = get_supabase()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Busca todas as atividades e agrupa por usuário
        result = client.table('activity_log').select('user_id').gte('created_at', from_date).execute()
        
        if not result.data:
            return []
        
        # Conta atividades por usuário
        user_counts = {}
        for item in result.data:
            user_id = item.get('user_id')
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        # Ordena e limita
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'user_id': user_id, 'activity_count': count} for user_id, count in sorted_users]
    
    @staticmethod
    def get_consecutive_activity_days(user_id: int) -> int:
        """
        Calcula quantos dias consecutivos o usuário teve atividade.
        Considera chat, call ou post como atividade válida.
        """
        client = get_supabase()
        
        # Busca atividades dos últimos 30 dias
        from_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        result = client.table('activity_log').select('created_at').eq('user_id', user_id).gte('created_at', from_date).order('created_at', desc=True).execute()
        
        if not result.data:
            return 0
        
        # Extrai datas únicas (apenas o dia)
        activity_dates = set()
        for item in result.data:
            created_at = item.get('created_at', '')
            if created_at:
                # Extrai apenas a data (YYYY-MM-DD)
                date_str = created_at[:10]
                activity_dates.add(date_str)
        
        if not activity_dates:
            return 0
        
        # Ordena as datas em ordem decrescente
        sorted_dates = sorted(activity_dates, reverse=True)
        
        # Conta dias consecutivos a partir de hoje
        today = datetime.now(timezone.utc).date()
        consecutive = 0
        
        for i, date_str in enumerate(sorted_dates):
            expected_date = today - timedelta(days=i)
            if date_str == expected_date.isoformat():
                consecutive += 1
            else:
                break
        
        return consecutive
    
    @staticmethod
    def get_unique_helped_members(helper_id: int, days: int = 7) -> List[int]:
        """
        Retorna lista de IDs de membros únicos que o helper ajudou nos últimos X dias.
        Usa a tabela de evaluations para rastrear ajudas.
        """
        client = get_supabase()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Busca avaliações onde o helper foi o alvo (quem recebeu o /ajudou)
        # ou usa activity_log com tipo 'help'
        result = client.table('activity_log').select('message_id').eq('user_id', helper_id).eq('activity_type', 'help').gte('created_at', from_date).execute()
        
        if not result.data:
            return []
        
        # message_id é usado para armazenar o ID do membro que foi ajudado
        unique_members = set()
        for item in result.data:
            member_id = item.get('message_id')
            if member_id:
                unique_members.add(member_id)
        
        return list(unique_members)
    
    @staticmethod
    def log_help_activity(helper_id: int, helped_member_id: int) -> Dict[str, Any]:
        """
        Registra quando um membro ajudou outro.
        Usa message_id para armazenar o ID do membro ajudado.
        """
        client = get_supabase()
        data = {
            'user_id': helper_id,
            'channel_id': 0,  # Não associado a um canal específico
            'activity_type': 'help',
            'message_id': helped_member_id,  # ID do membro que foi ajudado
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('activity_log').insert(data).execute()
        return result.data[0] if result.data else None


class EvaluationQueries:
    """Queries relacionadas ao sistema de avaliação de membros com estrelas e comentários"""
    
    @staticmethod
    def create_evaluation(evaluator_id: int, target_id: int, stars: int, 
                          comment: str, xp_given: int = 0) -> Dict[str, Any]:
        """Cria uma avaliação com estrelas e comentário"""
        client = get_supabase()
        data = {
            'evaluator_id': evaluator_id,
            'target_id': target_id,
            'stars': stars,
            'comment': comment,
            'xp_given': xp_given,
            'evaluation_type': f'{stars}_stars',  # Mantém compatibilidade
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('evaluations').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_user_evaluations_received(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca avaliações recebidas pelo usuário (mais recentes primeiro)"""
        client = get_supabase()
        result = client.table('evaluations').select('*').eq('target_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_user_evaluations_given(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca avaliações dadas pelo usuário"""
        client = get_supabase()
        result = client.table('evaluations').select('*').eq('evaluator_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_average_stars(user_id: int) -> Dict[str, Any]:
        """Calcula a média de estrelas recebidas pelo usuário"""
        evaluations = EvaluationQueries.get_user_evaluations_received(user_id, limit=1000)
        
        if not evaluations:
            return {'average': 0.0, 'count': 0, 'total_xp': 0}
        
        total_stars = sum(e.get('stars', 0) for e in evaluations)
        total_xp = sum(e.get('xp_given', 0) for e in evaluations)
        count = len(evaluations)
        average = round(total_stars / count, 1) if count > 0 else 0.0
        
        return {
            'average': average,
            'count': count,
            'total_xp': total_xp,
        }
    
    @staticmethod
    def get_evaluation_stats(user_id: int) -> Dict[str, Any]:
        """Estatísticas de avaliação de um usuário"""
        received = EvaluationQueries.get_user_evaluations_received(user_id, limit=1000)
        given = EvaluationQueries.get_user_evaluations_given(user_id, limit=1000)
        
        # Conta por quantidade de estrelas
        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_xp = 0
        for eval in received:
            stars = eval.get('stars', 0)
            if stars in star_counts:
                star_counts[stars] += 1
            total_xp += eval.get('xp_given', 0)
        
        # Calcula média
        total_stars = sum(e.get('stars', 0) for e in received)
        average = round(total_stars / len(received), 1) if received else 0.0
        
        return {
            'received_count': len(received),
            'given_count': len(given),
            'total_xp_from_evals': total_xp,
            'star_breakdown': star_counts,
            'average_stars': average,
        }
    
    @staticmethod
    def can_evaluate(evaluator_id: int, target_id: int, cooldown_hours: int = 24) -> bool:
        """Verifica se o avaliador pode avaliar o alvo (cooldown)"""
        client = get_supabase()
        cooldown_time = (datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)).isoformat()
        
        result = client.table('evaluations').select('id').eq('evaluator_id', evaluator_id).eq('target_id', target_id).gte('created_at', cooldown_time).execute()
        
        return not result.data or len(result.data) == 0
    
    @staticmethod
    def get_top_evaluated(days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna os membros mais bem avaliados (por média de estrelas)"""
        client = get_supabase()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        result = client.table('evaluations').select('target_id, xp_given, stars').gte('created_at', from_date).execute()
        
        if not result.data:
            return []
        
        # Agrupa por usuário
        user_data = {}
        for item in result.data:
            target_id = item.get('target_id')
            xp = item.get('xp_given', 0)
            stars = item.get('stars', 0)
            
            if target_id not in user_data:
                user_data[target_id] = {'xp': 0, 'stars': 0, 'count': 0}
            
            user_data[target_id]['xp'] += xp
            user_data[target_id]['stars'] += stars
            user_data[target_id]['count'] += 1
        
        # Calcula médias e ordena
        results = []
        for user_id, data in user_data.items():
            avg_stars = round(data['stars'] / data['count'], 1) if data['count'] > 0 else 0
            results.append({
                'user_id': user_id,
                'total_xp': data['xp'],
                'eval_count': data['count'],
                'average_stars': avg_stars,
            })
        
        # Ordena por média de estrelas (depois por quantidade)
        sorted_results = sorted(results, key=lambda x: (x['average_stars'], x['eval_count']), reverse=True)[:limit]
        return sorted_results


class DailyProgressQueries:
    """Queries relacionadas ao progresso diário do usuário"""
    
    @staticmethod
    def get_today_progress(user_id: int) -> Optional[Dict[str, Any]]:
        """Retorna o progresso do usuário para hoje"""
        client = get_supabase()
        today = datetime.now(timezone.utc).date().isoformat()
        result = client.table('daily_progress').select('*').eq('user_id', user_id).eq('date', today).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_or_create_today_progress(user_id: int) -> Dict[str, Any]:
        """Retorna ou cria o progresso do usuário para hoje"""
        client = get_supabase()
        today = datetime.now(timezone.utc).date().isoformat()
        
        existing = DailyProgressQueries.get_today_progress(user_id)
        if existing:
            return existing
        
        # Cria novo registro
        data = {
            'user_id': user_id,
            'date': today,
            'online_minutes': 0,
            'online_completed': False,
            'online_reward_claimed': False,
            'messages_count': 0,
            'chat_completed': False,
            'chat_reward_claimed': False,
            'checkin_done': False,
        }
        result = client.table('daily_progress').insert(data).execute()
        return result.data[0] if result.data else data
    
    @staticmethod
    def add_online_time(user_id: int, minutes: int = 1) -> Dict[str, Any]:
        """Adiciona tempo online ao usuário"""
        client = get_supabase()
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        
        new_minutes = progress.get('online_minutes', 0) + minutes
        update_data = {
            'online_minutes': new_minutes,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('daily_progress').update(update_data).eq('id', progress['id']).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def complete_online_requirement(user_id: int) -> Dict[str, Any]:
        """Marca o requisito de tempo online como completo"""
        client = get_supabase()
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        
        update_data = {
            'online_completed': True,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('daily_progress').update(update_data).eq('id', progress['id']).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def claim_online_reward(user_id: int) -> Dict[str, Any]:
        """Marca a recompensa de tempo online como recebida"""
        client = get_supabase()
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        
        update_data = {
            'online_reward_claimed': True,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('daily_progress').update(update_data).eq('id', progress['id']).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def add_message(user_id: int) -> Dict[str, Any]:
        """Adiciona uma mensagem ao contador diário"""
        client = get_supabase()
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        
        new_count = progress.get('messages_count', 0) + 1
        update_data = {
            'messages_count': new_count,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('daily_progress').update(update_data).eq('id', progress['id']).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def complete_chat_requirement(user_id: int) -> Dict[str, Any]:
        """Marca o requisito de chat como completo"""
        client = get_supabase()
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        
        update_data = {
            'chat_completed': True,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('daily_progress').update(update_data).eq('id', progress['id']).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def claim_chat_reward(user_id: int) -> Dict[str, Any]:
        """Marca a recompensa de chat como recebida"""
        client = get_supabase()
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        
        update_data = {
            'chat_reward_claimed': True,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('daily_progress').update(update_data).eq('id', progress['id']).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def mark_checkin_done(user_id: int) -> Dict[str, Any]:
        """Marca o check-in como feito"""
        client = get_supabase()
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        
        update_data = {
            'checkin_done': True,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
        
        result = client.table('daily_progress').update(update_data).eq('id', progress['id']).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_user_daily_summary(user_id: int) -> Dict[str, Any]:
        """Retorna resumo do dia para o usuário"""
        progress = DailyProgressQueries.get_or_create_today_progress(user_id)
        is_vip = UserQueries.is_vip(user_id)
        
        import config
        
        # Requisitos baseados no status VIP
        online_required = config.VIP_DAILY_ONLINE_MINUTES if is_vip else config.FREE_DAILY_ONLINE_MINUTES
        messages_required = config.VIP_DAILY_MESSAGES if is_vip else config.FREE_DAILY_MESSAGES
        
        return {
            'is_vip': is_vip,
            # Tempo Online
            'online_minutes': progress.get('online_minutes', 0),
            'online_required': online_required,
            'online_completed': progress.get('online_completed', False),
            'online_progress_percent': min(100, int((progress.get('online_minutes', 0) / online_required) * 100)) if online_required > 0 else 100,
            # Mensagens
            'messages_count': progress.get('messages_count', 0),
            'messages_required': messages_required,
            'chat_completed': progress.get('chat_completed', False),
            'chat_progress_percent': min(100, int((progress.get('messages_count', 0) / messages_required) * 100)) if messages_required > 0 else 100,
            # Check-in
            'checkin_done': progress.get('checkin_done', False),
            # FastPass (VIP)
            'fastpass_active': is_vip and config.FASTPASS_ENABLED,
        }


class EventQueries:
    """Queries relacionadas a eventos e presenças"""
    
    @staticmethod
    def create_event(name: str, event_type: str, xp_reward: int, coins_reward: int, 
                     description: str = None, created_by: int = None) -> Dict[str, Any]:
        """Cria um novo evento"""
        client = get_supabase()
        data = {
            'event_name': name,
            'event_type': event_type,
            'description': description,
            'xp_reward': xp_reward,
            'coins_reward': coins_reward,
            'is_active': True,
            'created_by': created_by,
            'starts_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('events').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_active_events() -> List[Dict[str, Any]]:
        """Retorna todos os eventos ativos"""
        client = get_supabase()
        result = client.table('events').select('*').eq('is_active', True).order('created_at', desc=True).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_unannounced_events() -> List[Dict[str, Any]]:
        """Busca eventos ativos não anunciados"""
        client = get_supabase()
        # Busca eventos ativos onde message_id é null
        result = client.table('events').select('*').eq('is_active', True).is_('message_id', 'null').execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_event(event_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um evento pelo ID"""
        client = get_supabase()
        result = client.table('events').select('*').eq('id', event_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def end_event(event_id: int) -> Dict[str, Any]:
        """Finaliza um evento"""
        client = get_supabase()
        update_data = {
            'is_active': False,
            'ends_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('events').update(update_data).eq('id', event_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def close_event(event_id: int) -> Dict[str, Any]:
        """Alias para end_event - encerra um evento automaticamente"""
        return EventQueries.end_event(event_id)
    
    @staticmethod
    def update_event_message(event_id: int, message_id: int, channel_id: int) -> bool:
        """Salva o ID da mensagem de anúncio do evento"""
        client = get_supabase()
        try:
            update_data = {
                'message_id': str(message_id),
                'channel_id': str(channel_id),
            }
            client.table('events').update(update_data).eq('id', event_id).execute()
            return True
        except:
            return False
    
    @staticmethod
    def mark_presence(event_id: int, user_id: int, is_vip: bool = False) -> Dict[str, Any]:
        """Marca presença de um usuário em um evento"""
        client = get_supabase()
        
        # Verifica se já marcou presença
        existing = client.table('event_presence').select('id').eq('event_id', event_id).eq('user_id', user_id).execute()
        if existing.data:
            return None  # Já marcou presença
        
        # Busca o evento para pegar as recompensas
        event = EventQueries.get_event(event_id)
        if not event:
            return None
        
        import config
        
        # Multiplicador baseado no VIP
        multiplier = config.VIP_EVENT_PRESENCE_MULTIPLIER if is_vip else config.FREE_EVENT_PRESENCE_MULTIPLIER
        
        xp_earned = event.get('xp_reward', config.EVENT_PRESENCE_BASE_XP) * multiplier
        coins_earned = event.get('coins_reward', config.EVENT_PRESENCE_BASE_COINS) * multiplier
        
        data = {
            'event_id': event_id,
            'user_id': user_id,
            'presence_multiplier': multiplier,
            'xp_earned': xp_earned,
            'coins_earned': coins_earned,
        }
        
        result = client.table('event_presence').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_event_presences(event_id: int) -> List[Dict[str, Any]]:
        """Retorna todas as presenças de um evento"""
        client = get_supabase()
        result = client.table('event_presence').select('*').eq('event_id', event_id).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_user_event_presences(user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Retorna presenças do usuário nos últimos X dias"""
        client = get_supabase()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = client.table('event_presence').select('*').eq('user_id', user_id).gte('marked_at', from_date).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_user_total_event_xp(user_id: int) -> int:
        """Retorna o XP total ganho em eventos pelo usuário"""
        presences = EventQueries.get_user_event_presences(user_id, days=365)
        return sum(p.get('xp_earned', 0) for p in presences)


class ShopQueries:
    """Queries relacionadas à loja e compras"""
    
    @staticmethod
    def create_purchase(buyer_id: int, item_id: str, target_id: int = None, 
                       price_paid: int = 0, guild_id: int = None) -> Dict[str, Any]:
        """Cria uma nova compra na loja"""
        client = get_supabase()
        data = {
            'buyer_id': buyer_id,
            'item_id': item_id,
            'target_id': target_id,
            'price_paid': price_paid,
            'guild_id': guild_id,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('shop_purchases').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_purchase(purchase_id: int) -> Optional[Dict[str, Any]]:
        """Busca uma compra pelo ID"""
        client = get_supabase()
        result = client.table('shop_purchases').select('*').eq('id', purchase_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_pending_calls_for_user(target_id: int) -> List[Dict[str, Any]]:
        """Busca pedidos de call pendentes para um usuário"""
        client = get_supabase()
        result = client.table('shop_purchases').select('*').eq('target_id', target_id).eq('status', 'pending').eq('item_id', 'call_expert').order('created_at', desc=True).execute()
        return result.data if result.data else []
    
    @staticmethod
    def get_user_purchases(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca histórico de compras do usuário"""
        client = get_supabase()
        result = client.table('shop_purchases').select('*').eq('buyer_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return result.data if result.data else []
    
    @staticmethod
    def update_purchase_status(purchase_id: int, status: str) -> Dict[str, Any]:
        """Atualiza o status de uma compra"""
        client = get_supabase()
        update_data = {
            'status': status,
            'resolved_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('shop_purchases').update(update_data).eq('id', purchase_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_purchase_schedule(purchase_id: int, status: str, scheduled_at: str) -> Dict[str, Any]:
        """Atualiza o agendamento de uma compra"""
        client = get_supabase()
        update_data = {
            'status': status,
            'scheduled_at': scheduled_at,
            'resolved_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('shop_purchases').update(update_data).eq('id', purchase_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_purchase_channel(purchase_id: int, channel_id: int) -> Dict[str, Any]:
        """Atualiza o canal de voz da call"""
        client = get_supabase()
        update_data = {
            'channel_id': str(channel_id),
        }
        result = client.table('shop_purchases').update(update_data).eq('id', purchase_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_scheduled_calls_for_user(user_id: int) -> List[Dict[str, Any]]:
        """Busca calls agendadas onde o usuário é comprador ou alvo"""
        client = get_supabase()
        
        # Busca como comprador
        as_buyer = client.table('shop_purchases').select('*').eq('buyer_id', user_id).eq('status', 'scheduled').eq('item_id', 'call_expert').order('scheduled_at', desc=False).execute()
        
        # Busca como alvo
        as_target = client.table('shop_purchases').select('*').eq('target_id', user_id).eq('status', 'scheduled').eq('item_id', 'call_expert').order('scheduled_at', desc=False).execute()
        
        # Combina e remove duplicatas
        all_calls = (as_buyer.data or []) + (as_target.data or [])
        seen_ids = set()
        unique_calls = []
        for call in all_calls:
            if call['id'] not in seen_ids:
                seen_ids.add(call['id'])
                unique_calls.append(call)
        
        return sorted(unique_calls, key=lambda x: x.get('scheduled_at', ''))
    
    @staticmethod
    def get_all_pending_calls() -> List[Dict[str, Any]]:
        """Busca todos os pedidos de call pendentes"""
        client = get_supabase()
        result = client.table('shop_purchases').select('*').eq('status', 'pending').eq('item_id', 'call_expert').order('created_at', desc=True).execute()
        return result.data if result.data else []
    
    @staticmethod
    def expire_old_calls(hours: int = 48) -> int:
        """Expira pedidos de call antigos e retorna quantidade expirada"""
        client = get_supabase()
        expiry_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        result = client.table('shop_purchases').update({
            'status': 'expired',
            'resolved_at': datetime.now(timezone.utc).isoformat(),
        }).eq('status', 'pending').eq('item_id', 'call_expert').lt('created_at', expiry_time).execute()
        
        return len(result.data) if result.data else 0


class NotificationQueries:
    """Queries relacionadas a notificações pendentes (Dashboard -> Bot)"""
    
    @staticmethod
    def create_notification(user_id: int, notification_type: str, title: str, message: str, 
                            xp_reward: int = 0, coins_reward: int = 0) -> Dict[str, Any]:
        """Cria uma notificação pendente para o bot enviar"""
        client = get_supabase()
        data = {
            'user_id': user_id,
            'notification_type': notification_type,  # 'mission_complete', 'reward', 'admin_message'
            'title': title,
            'message': message,
            'xp_reward': xp_reward,
            'coins_reward': coins_reward,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        result = client.table('notifications').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_pending_notifications(limit: int = 10) -> List[Dict[str, Any]]:
        """Busca notificações pendentes para o bot enviar"""
        client = get_supabase()
        result = client.table('notifications').select('*').eq('status', 'pending').order('created_at', desc=False).limit(limit).execute()
        return result.data if result.data else []
    
    @staticmethod
    def mark_as_sent(notification_id: int) -> bool:
        """Marca notificação como enviada"""
        client = get_supabase()
        client.table('notifications').update({
            'status': 'sent',
            'sent_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', notification_id).execute()
        return True
    
    @staticmethod
    def mark_as_failed(notification_id: int, error_msg: str = None) -> bool:
        """Marca notificação como falha"""
        client = get_supabase()
        client.table('notifications').update({
            'status': 'failed',
            'error': error_msg,
        }).eq('id', notification_id).execute()
        return True

