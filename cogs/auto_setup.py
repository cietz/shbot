"""
🦈 SharkClub Discord Bot - Auto Setup Cog
Sistema de configuração automática de cargos e canais
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing import Optional, Dict, List
import config


class AutoSetupCog(commands.Cog):
    """Sistema de configuração automática do servidor"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._level_roles: Dict[int, discord.Role] = {}  # Cache de roles por nível
        self._channels: Dict[str, discord.TextChannel] = {}  # Cache de canais
        self._setup_complete = False
    
    def cog_unload(self):
        """Para a task quando o cog é descarregado"""
        self.periodic_role_sync.cancel()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Executa setup automático quando o bot inicia"""
        print("🔧 Iniciando configuração automática...")
        
        for guild in self.bot.guilds:
            await self.setup_guild(guild)
        
        self._setup_complete = True
        print("✅ Configuração automática concluída!")
        
        # Inicia a task de sincronização periódica
        if not self.periodic_role_sync.is_running():
            self.periodic_role_sync.start()
            print("🔄 Task de sincronização periódica iniciada (a cada 5 min)")
    
    @tasks.loop(minutes=5)
    async def periodic_role_sync(self):
        """Sincroniza cargos de todos os membros periodicamente (apenas servidores pequenos)"""
        if not self._setup_complete:
            return
        
        for guild in self.bot.guilds:
            # Pula servidores grandes - cargos são sincronizados sob demanda
            member_count = len([m for m in guild.members if not m.bot])
            if member_count < 50:
                await self.auto_sync_member_roles(guild, silent=True)
    
    @periodic_role_sync.before_loop
    async def before_periodic_sync(self):
        """Aguarda o bot estar pronto antes de iniciar"""
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Configura o servidor quando o bot entra"""
        print(f"🆕 Bot adicionado ao servidor: {guild.name}")
        await self.setup_guild(guild)
    
    async def setup_guild(self, guild: discord.Guild):
        """Configura um servidor específico"""
        print(f"⚙️ Configurando servidor: {guild.name}")
        
        # 1. Criar cargos de nível
        await self.setup_level_roles(guild)
        
        # 2. Criar canais necessários
        await self.setup_channels(guild)
        
        # 3. Configurar permissões
        await self.setup_permissions(guild)
        
        # 4. Sincronizar cargos apenas para servidores pequenos (< 50 membros)
        # Para servidores grandes, os cargos são sincronizados sob demanda
        member_count = len([m for m in guild.members if not m.bot])
        if member_count < 50:
            await self.auto_sync_member_roles(guild)
        else:
            print(f"  ⏭️ Sincronização de cargos adiada (servidor grande: {member_count} membros)")
        
        print(f"✅ Servidor {guild.name} configurado!")
    
    async def auto_sync_member_roles(self, guild: discord.Guild, silent: bool = False):
        """Sincroniza cargos de nível de todos os membros automaticamente (OTIMIZADO)"""
        from database.queries import UserQueries
        
        if not silent:
            print(f"  🔄 Sincronizando cargos dos membros...")
        synced = 0
        
        # OTIMIZAÇÃO: Busca todos os usuários de uma vez (1 request em vez de N)
        all_users = UserQueries.get_all_users()
        user_levels = {u['user_id']: u.get('level', 1) for u in all_users}
        
        for member in guild.members:
            if member.bot:
                continue
            
            # Usa lookup no dicionário em vez de chamada HTTP
            level = user_levels.get(member.id)
            if level:
                # Verifica se já tem o cargo correto
                current_role = self.get_member_level_from_roles(member)
                if current_role != level:
                    success = await self.assign_level_role(member, level)
                    if success:
                        synced += 1
                        if not silent:
                            print(f"    ✅ {member.display_name} -> Nível {level}")
        
        if not silent:
            if synced > 0:
                print(f"  ✅ {synced} membros sincronizados!")
            else:
                print(f"  ✅ Todos os cargos já estão sincronizados!")
        elif synced > 0:
            print(f"🔄 Sync periódico: {synced} membros atualizados")
    
    def get_member_level_from_roles(self, member: discord.Member) -> int:
        """Retorna o nível do membro baseado nos cargos que tem"""
        for level in range(10, 0, -1):
            cargo_name = config.CARGO_NAMES.get(level)
            for role in member.roles:
                if role.name == cargo_name:
                    return level
        return 0  # Não tem nenhum cargo de nível
    
    # ═══════════════════════════════════════════════════════════════
    # SISTEMA DE CARGOS
    # ═══════════════════════════════════════════════════════════════
    
    async def setup_level_roles(self, guild: discord.Guild):
        """Cria todos os cargos de nível"""
        print("  📋 Configurando cargos de nível...")
        
        for level in range(1, 11):
            role = await self.get_or_create_level_role(guild, level)
            if role:
                self._level_roles[level] = role
        
        # Cargo VIP
        await self.get_or_create_role(
            guild, 
            name="👑 VIP",
            color=discord.Color(config.EMBED_COLOR_VIP),
            hoist=True,
            reason="SharkClub - Cargo VIP"
        )
        
        print("  ✅ Cargos de nível configurados!")
    
    async def get_or_create_level_role(self, guild: discord.Guild, level: int) -> Optional[discord.Role]:
        """Busca ou cria o cargo de um nível específico"""
        cargo_name = config.CARGO_NAMES.get(level, f"Nível {level}")
        cargo_color = discord.Color(config.CARGO_COLORS.get(level, 0x808080))
        
        # Verifica no cache
        if level in self._level_roles:
            if self._level_roles[level] in guild.roles:
                return self._level_roles[level]
        
        # Busca por nome
        for role in guild.roles:
            if role.name == cargo_name:
                self._level_roles[level] = role
                return role
        
        # Cria o cargo
        return await self.get_or_create_role(
            guild,
            name=cargo_name,
            color=cargo_color,
            hoist=True,
            reason=f"SharkClub - Cargo Nível {level}"
        )
    
    async def get_or_create_role(self, guild: discord.Guild, name: str, 
                                  color: discord.Color = None,
                                  hoist: bool = False,
                                  mentionable: bool = False,
                                  reason: str = None) -> Optional[discord.Role]:
        """Busca ou cria um cargo genérico"""
        # Busca por nome
        for role in guild.roles:
            if role.name == name:
                return role
        
        # Cria o cargo
        try:
            role = await guild.create_role(
                name=name,
                color=color or discord.Color.default(),
                hoist=hoist,
                mentionable=mentionable,
                reason=reason or "SharkClub Auto-Setup"
            )
            print(f"    ✅ Cargo criado: {name}")
            return role
        except discord.Forbidden:
            print(f"    ❌ Sem permissão para criar cargo: {name}")
            return None
        except Exception as e:
            print(f"    ❌ Erro ao criar cargo {name}: {e}")
            return None
    
    async def assign_level_role(self, member: discord.Member, new_level: int) -> bool:
        """Atribui cargo de nível a um membro (remove cargos anteriores)"""
        guild = member.guild
        
        try:
            # Remove todos os cargos de nível anteriores
            roles_to_remove = []
            for level in range(1, 11):
                if level != new_level:
                    role = await self.get_or_create_level_role(guild, level)
                    if role and role in member.roles:
                        roles_to_remove.append(role)
            
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"SharkClub - Subiu para nível {new_level}")
            
            # Adiciona o cargo do novo nível
            new_role = await self.get_or_create_level_role(guild, new_level)
            if new_role and new_role not in member.roles:
                await member.add_roles(new_role, reason=f"SharkClub - Alcançou nível {new_level}")
                return True
            
            return True
        except discord.Forbidden:
            print(f"❌ Sem permissão para atribuir cargo a {member.display_name}")
            return False
        except Exception as e:
            print(f"❌ Erro ao atribuir cargo: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # SISTEMA DE CANAIS (USANDO IDs FIXOS)
    # ═══════════════════════════════════════════════════════════════
    
    async def setup_channels(self, guild: discord.Guild):
        """Verifica canais fixos (não cria mais automaticamente)"""
        print("  📺 Verificando canais fixos...")
        
        # Usa os IDs fixos do config - não cria canais automaticamente
        import config
        for channel_name, channel_id in config.CHANNEL_IDS.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                self._channels[channel_name] = channel
                print(f"     ✓ Canal '{channel_name}' encontrado")
            else:
                print(f"     ⚠ Canal '{channel_name}' não encontrado (ID: {channel_id})")
        
        print("  ✅ Canais verificados!")
    
    async def get_or_create_category(self, guild: discord.Guild, name: str) -> Optional[discord.CategoryChannel]:
        """Busca ou cria uma categoria"""
        # Busca por nome
        for category in guild.categories:
            if category.name == name:
                return category
        
        # Não cria mais categorias automaticamente
        print(f"    ⚠ Categoria '{name}' não encontrada (Criação automática desativada)")
        return None
    
    async def get_or_create_text_channel(self, guild: discord.Guild, name: str,
                                          category: discord.CategoryChannel = None,
                                          topic: str = None) -> Optional[discord.TextChannel]:
        """Busca ou cria um canal de texto"""
        # Normaliza o nome para busca
        search_name = name.lower().replace(" ", "-")
        
        # Busca por nome
        for channel in guild.text_channels:
            if channel.name.lower() == search_name:
                return channel
        
        # Não cria mais canais automaticamente
        print(f"    ⚠ Canal '{name}' não encontrado (Criação automática desativada)")
        return None
    
    async def setup_permissions(self, guild: discord.Guild):
        """Configura permissões básicas"""
        print("  🔐 Configurando permissões...")
        # Permissões podem ser configuradas aqui conforme necessário
        print("  ✅ Permissões configuradas!")
    
    async def get_channel_by_name(self, guild: discord.Guild, name_contains: str) -> Optional[discord.TextChannel]:
        """Busca um canal que contenha o nome especificado"""
        search_term = name_contains.lower()
        
        # Primeiro verifica no cache
        for cached_name, channel in self._channels.items():
            if search_term in cached_name.lower():
                if channel in guild.text_channels:
                    return channel
        
        # Busca em todos os canais do servidor
        for channel in guild.text_channels:
            if search_term in channel.name.lower():
                return channel
        
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # COMANDOS DE ADMIN
    # ═══════════════════════════════════════════════════════════════
    
    def is_admin():
        """Decorator para verificar permissão de admin"""
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)
    
    @app_commands.command(name="setup", description="[ADMIN] Reconfigurar cargos e canais do bot")
    @is_admin()
    async def setup_command(self, interaction: discord.Interaction):
        """Reconfigura o servidor manualmente"""
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="⚙️ Reconfigurando servidor...",
            description="Isso pode levar alguns segundos.",
            color=config.EMBED_COLOR_PRIMARY
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        await self.setup_guild(interaction.guild)
        
        embed = discord.Embed(
            title="✅ Setup Completo!",
            description="Todos os cargos e canais foram verificados/criados.",
            color=config.EMBED_COLOR_SUCCESS
        )
        embed.add_field(
            name="📋 Cargos de Nível",
            value="\n".join([f"{config.CARGO_EMOJIS.get(l, '')} {config.CARGO_NAMES.get(l, '')}" for l in range(1, 11)]),
            inline=True
        )
        embed.add_field(
            name="📺 Canais Criados",
            value="• 📢-anuncios-shark\n• 🏆-ranking\n• 📋-missoes\n• 🎮-minigames\n• 🎪-eventos\n• 🔔-level-ups\n• ⭐-avaliacoes",
            inline=True
        )
        
        await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="sync-cargos", description="[ADMIN] Sincronizar cargos de todos os membros")
    @is_admin()
    async def sync_cargos(self, interaction: discord.Interaction):
        """Sincroniza cargos de nível de todos os membros"""
        await interaction.response.defer(ephemeral=True)
        
        from database.queries import UserQueries
        
        synced = 0
        errors = 0
        
        for member in interaction.guild.members:
            if member.bot:
                continue
            
            user_data = UserQueries.get_user(member.id)
            if user_data:
                level = user_data.get('level', 1)
                success = await self.assign_level_role(member, level)
                if success:
                    synced += 1
                else:
                    errors += 1
        
        embed = discord.Embed(
            title="✅ Sincronização Completa!",
            description=f"Cargos sincronizados para {synced} membros.",
            color=config.EMBED_COLOR_SUCCESS
        )
        if errors > 0:
            embed.add_field(name="⚠️ Erros", value=f"{errors} membros não puderam ser atualizados")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @setup_command.error
    @sync_cargos.error
    async def admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa ser administrador para usar este comando.",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            raise error
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS PARA OUTROS COGS
    # ═══════════════════════════════════════════════════════════════
    
    def get_channel(self, name: str) -> Optional[discord.TextChannel]:
        """Retorna canal do cache"""
        return self._channels.get(name)
    
    async def send_level_up_notification(self, guild: discord.Guild, member: discord.Member, 
                                          old_level: int, new_level: int):
        """Envia notificação de level up no canal apropriado"""
        channel_id = config.CHANNEL_IDS.get("level_ups")
        channel = guild.get_channel(channel_id)
        
        if not channel:
             print(f"⚠️ Canal de level-ups não encontrado (ID: {channel_id})")
             return
        
        if channel:
            cargo_name = config.CARGO_NAMES.get(new_level, f"Nível {new_level}")
            cargo_emoji = config.CARGO_EMOJIS.get(new_level, "🎉")
            
            embed = discord.Embed(
                title=f"🎉 LEVEL UP!",
                description=f"**{member.display_name}** subiu para o **Nível {new_level}**!\n\n"
                           f"Novo cargo: {cargo_emoji} **{cargo_name}**",
                color=discord.Color(config.CARGO_COLORS.get(new_level, 0xFFD700))
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            try:
                await channel.send(embed=embed)
            except:
                pass
    
    async def handle_xp_gain(self, guild: discord.Guild, member: discord.Member, 
                              old_xp: int, new_xp: int, old_level: int = None):
        """
        Método centralizado para lidar com ganho de XP.
        DEVE ser chamado por QUALQUER cog que dê XP ao usuário.
        Verifica level up e atribui cargo automaticamente.
        
        Args:
            guild: Servidor Discord
            member: Membro que ganhou XP
            old_xp: XP antes do ganho
            new_xp: XP depois do ganho
            old_level: Nível anterior (opcional, será calculado se não fornecido)
        
        Returns:
            dict com informações do resultado
        """
        from utils.xp_calculator import XPCalculator
        from database.queries import BadgeQueries
        
        # Calcula níveis
        if old_level is None:
            old_level = XPCalculator.get_level_from_xp(old_xp)
        new_level = XPCalculator.get_level_from_xp(new_xp)
        
        result = {
            'leveled_up': False,
            'old_level': old_level,
            'new_level': new_level,
            'role_assigned': False,
        }
        
        # Verifica se subiu de nível
        if new_level > old_level:
            result['leveled_up'] = True
            
            # Concede badge de nível
            badge_name = XPCalculator.get_badge_name(new_level)
            BadgeQueries.award_badge(member.id, badge_name, 'level')
            
            # Atribui cargo automaticamente
            success = await self.assign_level_role(member, new_level)
            result['role_assigned'] = success
            
            # Envia notificação no canal
            await self.send_level_up_notification(guild, member, old_level, new_level)
            
            print(f"🎉 {member.display_name} subiu para nível {new_level}!")
        
        return result
    
    async def get_evaluations_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """Retorna o canal de avaliações"""
        channel_id = config.CHANNEL_IDS.get("avaliacoes")
        channel = guild.get_channel(channel_id)
        
        if not channel:
            print(f"⚠️ Canal de avaliações não encontrado (ID: {channel_id})")
        
        return channel
    
    async def send_evaluation_to_channel(self, guild: discord.Guild, embed: discord.Embed):
        """Envia uma avaliação para o canal de avaliações"""
        channel = await self.get_evaluations_channel(guild)
        
        if channel:
            try:
                await channel.send(embed=embed)
                return True
            except:
                pass
        return False


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoSetupCog(bot))

