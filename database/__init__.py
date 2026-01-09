"""
🦈 SharkClub Discord Bot - Database Package
"""
from .connection import get_supabase, init_database
from .queries import (
    UserQueries, 
    BadgeQueries, 
    MissionQueries, 
    RewardQueries,
    DailyProgressQueries,
    EventQueries
)

__all__ = [
    'get_supabase',
    'init_database', 
    'UserQueries',
    'BadgeQueries',
    'MissionQueries',
    'RewardQueries',
    'DailyProgressQueries',
    'EventQueries'
]

