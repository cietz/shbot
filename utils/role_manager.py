"""
🦈 SharkClub Discord Bot - Role Manager
Sistema de gerenciamento de cargos baseado em níveis
"""

import discord
from typing import Optional, List
import config


class RoleManager:
    """Gerencia cargos de nível no Discord"""
    
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self._level_roles: dict = {}  # Cache de roles por nível
    
    async def get_or_create_level_role(self, level: int) -> Optional[discord.Role]:
        """Busca ou cria o cargo para um nível específico"""
        # Verifica se já existe no cache
        if level in self._level_roles:
            return self._level_roles[level]
        
        # Busca o ID configurado
        configured_id = config.DISCORD_ROLE_IDS.get(level)
        
        if configured_id:
            role = self.guild.get_role(configured_id)
            if role:
                self._level_roles[level] = role
                return role
        
        # Busca por nome
        cargo_name = config.CARGO_NAMES.get(level, f"Nível {level}")
        
        for role in self.guild.roles:
            if role.name == cargo_name:
                self._level_roles[level] = role
                return role
        
        # Se não encontrou e podemos criar
        try:
            color = discord.Color(config.CARGO_COLORS.get(level, 0x808080))
            new_role = await self.guild.create_role(
                name=cargo_name,
                color=color,
                reason=f"SharkClub - Cargo de nível {level}",
                hoist=True,  # Mostrar separadamente na lista de membros
                mentionable=False,
            )
            self._level_roles[level] = new_role
            print(f"✅ Cargo criado: {cargo_name}")
            return new_role
        except discord.Forbidden:
            print(f"❌ Sem permissão para criar cargo: {cargo_name}")
            return None
        except Exception as e:
            print(f"❌ Erro ao criar cargo {cargo_name}: {e}")
            return None
    
    async def update_member_role(self, member: discord.Member, new_level: int, old_level: int = None) -> dict:
        """
        Atualiza o cargo de um membro baseado no novo nível.
        Remove cargos de níveis anteriores e adiciona o novo.
        
        Retorna: {'success': bool, 'added': role, 'removed': [roles]}
        """
        result = {
            'success': False,
            'added': None,
            'removed': [],
            'error': None,
        }
        
        try:
            # Busca/cria o cargo do novo nível
            new_role = await self.get_or_create_level_role(new_level)
            
            if not new_role:
                result['error'] = "Não foi possível obter o cargo"
                return result
            
            # Lista de cargos de nível para remover
            roles_to_remove = []
            
            for level in range(1, 11):
                if level == new_level:
                    continue  # Não remove o cargo atual
                
                level_role = await self.get_or_create_level_role(level)
                if level_role and level_role in member.roles:
                    roles_to_remove.append(level_role)
            
            # Remove cargos antigos
            for role in roles_to_remove:
                try:
                    await member.remove_roles(role, reason=f"SharkClub - Subiu para nível {new_level}")
                    result['removed'].append(role)
                except:
                    pass
            
            # Adiciona novo cargo
            if new_role not in member.roles:
                await member.add_roles(new_role, reason=f"SharkClub - Alcançou nível {new_level}")
                result['added'] = new_role
            
            result['success'] = True
            return result
            
        except discord.Forbidden:
            result['error'] = "Bot sem permissão para gerenciar cargos"
            return result
        except Exception as e:
            result['error'] = str(e)
            return result
    
    async def sync_all_level_roles(self) -> List[discord.Role]:
        """Cria todos os cargos de nível se não existirem"""
        created = []
        
        for level in range(1, 11):
            role = await self.get_or_create_level_role(level)
            if role:
                created.append(role)
        
        return created
    
    def get_member_level_role(self, member: discord.Member) -> Optional[discord.Role]:
        """Retorna o cargo de nível atual do membro"""
        for level in range(10, 0, -1):  # Do maior para o menor
            cargo_name = config.CARGO_NAMES.get(level)
            for role in member.roles:
                if role.name == cargo_name:
                    return role
        return None
    
    def get_member_current_level_from_roles(self, member: discord.Member) -> int:
        """Retorna o nível do membro baseado nos cargos"""
        for level in range(10, 0, -1):
            cargo_name = config.CARGO_NAMES.get(level)
            for role in member.roles:
                if role.name == cargo_name:
                    return level
        return 1  # Padrão: nível 1
