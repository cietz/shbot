"""
🦈 SharkClub Discord Bot - Mini-games Cog
Roleta, Lootbox e Raspadinha
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timezone

from database.queries import UserQueries, BadgeQueries, RewardQueries, MissionQueries
from utils.embeds import SharkEmbeds
from utils.xp_calculator import XPCalculator
from utils.cooldowns import CooldownManager
import config


# ═══════════════════════════════════════════════════════════════
# VIEW COM BOTÕES PARA MINIGAMES
# ═══════════════════════════════════════════════════════════════

class MinigamesView(discord.ui.View):
    """View persistente com botões para minigames"""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)  # Persistente
        self.bot = bot
    
    @discord.ui.button(
        label="🎰 Roleta",
        style=discord.ButtonStyle.danger,
        custom_id="minigames_roleta",
        row=0
    )
    async def roleta_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Executa a roleta via botão"""
        minigames_cog = self.bot.get_cog('MinigamesCog')
        if minigames_cog:
            await minigames_cog._execute_roleta(interaction)
        else:
            await interaction.response.send_message("❌ Erro ao carregar minigame.", ephemeral=True)
    
    @discord.ui.button(
        label="📦 Lootbox",
        style=discord.ButtonStyle.primary,
        custom_id="minigames_lootbox",
        row=0
    )
    async def lootbox_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Abre lootbox via botão"""
        minigames_cog = self.bot.get_cog('MinigamesCog')
        if minigames_cog:
            await minigames_cog._execute_lootbox(interaction)
        else:
            await interaction.response.send_message("❌ Erro ao carregar minigame.", ephemeral=True)
    
    @discord.ui.button(
        label="🎟️ Raspadinha",
        style=discord.ButtonStyle.success,
        custom_id="minigames_raspadinha",
        row=0
    )
    async def raspadinha_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Executa raspadinha via botão"""
        minigames_cog = self.bot.get_cog('MinigamesCog')
        if minigames_cog:
            await minigames_cog._execute_raspadinha(interaction)
        else:
            await interaction.response.send_message("❌ Erro ao carregar minigame.", ephemeral=True)


class MinigamesCog(commands.Cog):
    """Mini-games do SharkClub"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Envia painel de minigames no canal apropriado"""
        import asyncio
        await asyncio.sleep(3)  # Aguarda setup de canais
        
        for guild in self.bot.guilds:
            await self._send_minigames_panel(guild)
    
    async def _send_minigames_panel(self, guild: discord.Guild):
        """Envia ou atualiza painel de minigames no canal"""
        # Busca o canal de minigames
        channel = None
        for ch in guild.text_channels:
            if "minigames" in ch.name.lower() or "minigame" in ch.name.lower():
                if "🦈" in ch.name:
                    channel = ch
                    break
                channel = ch
        
        if not channel:
            return
        
        # Cria embed do painel
        embed = discord.Embed(
            title="🎮 Mini-Games SharkClub",
            description="Clique nos botões abaixo para jogar!\n\n"
                       "🎰 **Roleta** - 1x por dia (VIPs: cooldown reduzido)\n"
                       "📦 **Lootbox** - Ganhe com 7 dias de streak\n"
                       "🎟️ **Raspadinha** - 1x por semana",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_footer(text="🦈 SharkClub - Boa sorte!")
        
        # Cria view com botões
        from cogs.checkin import CheckinView
        
        # View combinada com check-in + minigames
        class CombinedView(discord.ui.View):
            def __init__(view_self, bot):
                super().__init__(timeout=None)
                # Adiciona botões do CheckinView
                checkin_view = CheckinView(bot)
                for item in checkin_view.children:
                    view_self.add_item(item)
                # Adiciona botões do MinigamesView
                minigames_view = MinigamesView(bot)
                for item in minigames_view.children:
                    view_self.add_item(item)
        
        view = CombinedView(self.bot)
        
        # Tenta encontrar mensagem existente
        try:
            async for message in channel.history(limit=10):
                if message.author == self.bot.user and message.embeds:
                    first_embed = message.embeds[0]
                    if first_embed.title and "Mini-Games" in first_embed.title:
                        await message.edit(embed=embed, view=view)
                        print(f"✅ Painel de minigames atualizado em {channel.name}")
                        return
            
            # Envia nova mensagem
            await channel.send(embed=embed, view=view)
            print(f"✅ Painel de minigames enviado para {channel.name}")
        except discord.Forbidden:
            print(f"❌ Sem permissão para enviar no canal {channel.name}")
        except Exception as e:
            print(f"❌ Erro ao enviar painel de minigames: {e}")
    
    # Métodos internos para execução via botão
    async def _execute_roleta(self, interaction: discord.Interaction):
        """Executa roleta (usado por comando e botão)"""
        await self.roleta.callback(self, interaction)
    
    async def _execute_lootbox(self, interaction: discord.Interaction):
        """Executa lootbox (usado por comando e botão)"""
        await self.lootbox.callback(self, interaction)
    
    async def _execute_raspadinha(self, interaction: discord.Interaction):
        """Executa raspadinha (usado por comando e botão)"""
        await self.raspadinha.callback(self, interaction)
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Verifica se o usuário é admin (ignora cooldowns)"""
        return interaction.user.guild_permissions.administrator
    
    def weighted_choice(self, items: list) -> dict:
        """Escolhe item baseado em peso"""
        weights = [item.get('weight', 1) for item in items]
        return random.choices(items, weights=weights, k=1)[0]
    
    def spin_slots(self) -> tuple:
        """Gira os slots e retorna os 3 símbolos"""
        slots = []
        for _ in range(3):
            symbol = self.weighted_choice(config.SHARK_SLOTS)
            slots.append(symbol['emoji'])
        return tuple(slots)
    
    def get_slot_visual_result(self, slots: tuple) -> str:
        """Retorna tipo visual do resultado (jackpot/pair/lose)"""
        s1, s2, s3 = slots
        if s1 == s2 == s3:
            return "jackpot"
        if s1 == s2 or s2 == s3 or s1 == s3:
            return "pair"
        return "lose"
    
    def update_minigame_mission(self, user_id: int):
        """Atualiza progresso da missão de minigame"""
        daily_missions = MissionQueries.get_active_missions(user_id, 'daily')
        
        for mission in daily_missions:
            if mission.get('mission_id') == 'daily_minigame' and mission.get('status') == 'active':
                new_progress = mission.get('progress', 0) + 1
                target = mission.get('target', 1)
                
                if new_progress >= target:
                    MissionQueries.complete_mission(mission['id'])
                    xp_reward = mission.get('xp_reward', 0)
                    UserQueries.update_xp(user_id, xp_reward)
                else:
                    MissionQueries.update_mission_progress(mission['id'], new_progress)
                break  # Só uma missão por vez
    
    async def process_xp_with_levelup(self, interaction: discord.Interaction, user_id: int, xp_amount: int) -> dict:
        """
        Processa ganho de XP e verifica level up automaticamente.
        Retorna informações sobre o XP ganho e level up.
        """
        # Busca XP antes
        user_data = UserQueries.get_user(user_id)
        old_xp = user_data.get('xp', 0) if user_data else 0
        
        # Aplica XP
        result = UserQueries.update_xp(user_id, xp_amount)
        xp_gained = xp_amount
        booster_applied = False
        if result:
            xp_gained = result.get('xp_gained', xp_amount)
            booster_applied = result.get('booster_applied', False)
        
        new_xp = old_xp + xp_gained
        
        # Verifica level up
        auto_setup = self.bot.get_cog('AutoSetupCog')
        levelup_result = None
        if auto_setup and interaction.guild:
            member = interaction.guild.get_member(user_id)
            if member:
                levelup_result = await auto_setup.handle_xp_gain(interaction.guild, member, old_xp, new_xp)
        
        return {
            'xp_gained': xp_gained,
            'xp_base': xp_amount,
            'booster_applied': booster_applied,
            'leveled_up': levelup_result.get('leveled_up', False) if levelup_result else False,
            'new_level': levelup_result.get('new_level', 1) if levelup_result else 1,
        }
    
    @app_commands.command(name="roleta", description="🦈 Gire a Roleta Shark! (1x por dia)")
    async def roleta(self, interaction: discord.Interaction):
        """Roleta Shark - 1 gratuito por dia, tickets extras via eventos!"""
        user_id = interaction.user.id
        
        # Busca dados do usuário primeiro para verificar VIP
        user_data = UserQueries.get_or_create_user(user_id, interaction.user.display_name)
        is_vip = user_data.get('is_vip', False)
        
        # Verifica cooldown diário (24h FREE, 20h VIP)
        can_spin, remaining = CooldownManager.check(user_id, 'roulette', is_vip=is_vip)
        
        # Verifica se tem ticket extra
        reward = RewardQueries.get_reward(user_id, 'roulette_ticket')
        has_ticket = reward and reward.get('available_count', 0) > 0
        
        # Precisa cooldown liberado OU ticket extra
        if not can_spin and not has_ticket:
            remaining_text = CooldownManager.format_remaining(remaining)
            vip_tip = "" if is_vip else "\n👑 **VIPs têm cooldown reduzido!**"
            embed = discord.Embed(
                title="🎰 Roleta em Cooldown",
                description=f"Você já usou seu giro gratuito de hoje!\n\n"
                           f"**Próximo giro em:** {remaining_text}\n"
                           f"**Dica:** Participe de eventos para ganhar tickets extras!{vip_tip}",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Animação inicial
        await interaction.response.defer(ephemeral=True)
        
        # Decide se usa ticket ou cooldown gratuito
        used_ticket = False
        if has_ticket:
            # Usa ticket extra (não afeta cooldown gratuito)
            RewardQueries.use_reward(user_id, 'roulette_ticket')
            used_ticket = True
        else:
            # Usa o gratuito diário - seta cooldown
            CooldownManager.set(user_id, 'roulette')
        
        # Gira slots para efeito visual
        slots = self.spin_slots()
        visual_result = self.get_slot_visual_result(slots)
        
        # SORTEIA PRÊMIO baseado nas probabilidades da ROULETTE_PRIZES
        prize = self.weighted_choice(config.ROULETTE_PRIZES)
        
        # Aplica prêmios conforme o tipo
        xp_gained = 0
        xp_base = 0
        coins_gained = 0
        booster_text = ""
        badge_text = ""
        booster_applied = False
        
        if prize.get('type') == 'xp':
            xp_base = prize.get('xp', 0)
            xp_result = await self.process_xp_with_levelup(interaction, user_id, xp_base)
            xp_gained = xp_result['xp_gained']
            booster_applied = xp_result['booster_applied']
        
        elif prize.get('type') == 'booster':
            booster = prize.get('booster', 2.0)
            duration = prize.get('booster_duration', 3600)
            UserQueries.set_multiplier(user_id, booster, duration)
            booster_text = f"🚀 **Booster {booster}x XP** ({duration // 60} min)"
        
        elif prize.get('type') == 'badge_coins':
            badge = prize.get('badge')
            coins_base = prize.get('coins', 5)
            # VIPs ganham o dobro de moedas
            coins_gained = int(coins_base * config.VIP_COINS_MULTIPLIER) if is_vip else coins_base
            if badge:
                BadgeQueries.award_badge(user_id, badge, 'special')
                badge_text = f"🏅 **Insígnia: {badge}**"
            UserQueries.update_coins(user_id, coins_gained)
        
        elif prize.get('type') == 'rare_coin':
            coins_base = prize.get('coins', 10)
            # VIPs ganham o dobro de moedas
            coins_gained = int(coins_base * config.VIP_COINS_MULTIPLIER) if is_vip else coins_base
            UserQueries.update_coins(user_id, coins_gained)
        
        # Determina cor e título baseado no prêmio
        prize_type = prize.get('type', 'xp')
        if prize_type == 'rare_coin':
            color = config.EMBED_COLOR_LEGENDARY
            title = "🎰 💎 MOEDA RARA! 💎"
        elif prize_type == 'badge_coins':
            color = config.EMBED_COLOR_GOLD
            title = "🎰 🏅 PRÊMIO ESPECIAL!"
        elif prize_type == 'booster':
            color = config.EMBED_COLOR_SUCCESS
            title = "🎰 🚀 BOOSTER ATIVADO!"
        else:
            color = config.EMBED_COLOR_SUCCESS if xp_gained > 50 else config.EMBED_COLOR_PRIMARY
            title = "🎰 Resultado da Roleta!"
        
        # Pega o símbolo mais relevante para o GIF
        if slots[0] == slots[1] == slots[2]:
            winning_symbol = slots[0]
        elif slots[0] == slots[1]:
            winning_symbol = slots[0]
        elif slots[1] == slots[2]:
            winning_symbol = slots[1]
        else:
            winning_symbol = slots[0]
        
        gif_url = config.SLOT_SYMBOL_GIFS.get(winning_symbol, config.SLOT_RESULT_GIFS.get("pair"))
        
        # Monta texto de recompensas
        rewards_text = ""
        if xp_gained > 0:
            if booster_applied:
                rewards_text += f"⭐ **+{xp_gained} XP** 🚀 _(Booster {xp_base}→{xp_gained})_\n"
            else:
                rewards_text += f"⭐ **+{xp_gained} XP**\n"
        if coins_gained > 0:
            rewards_text += f"🪙 **+{coins_gained} SHARK COINS**\n"
        if booster_text:
            rewards_text += f"{booster_text}\n"
        if badge_text:
            rewards_text += f"{badge_text}\n"
        
        if not rewards_text:
            rewards_text = "🌟 Boa sorte na próxima!"
        
        # Criar embed
        embed = discord.Embed(
            title=title,
            description=f"**{interaction.user.display_name}** girou a roleta!",
            color=color
        )
        
        embed.set_thumbnail(url=gif_url)
        
        embed.add_field(
            name="🎰 Animação",
            value=f"## ▸ {slots[0]} ▸ {slots[1]} ▸ {slots[2]} ◂",
            inline=False
        )
        
        embed.add_field(
            name=f"🎁 {prize.get('emoji', '🎁')} {prize.get('name', 'Prêmio')}",
            value=rewards_text,
            inline=False
        )
        
        embed.set_image(url=gif_url)
        embed.set_footer(text=f"🦈 SharkClub Roleta | Próximo giro em 24h")
        
        # Atualiza missão de minigame
        self.update_minigame_mission(user_id)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="lootbox", description="📦 Abra sua Lootbox! (Ganhe com 7 dias de streak)")
    async def lootbox(self, interaction: discord.Interaction):
        """Lootbox - Prêmios especiais para membros dedicados"""
        user_id = interaction.user.id
        
        # Verifica se tem lootbox disponível
        reward = RewardQueries.get_reward(user_id, 'lootbox')
        
        if not reward or reward.get('available_count', 0) <= 0:
            embed = discord.Embed(
                title="📦 Sem Lootboxes",
                description="Você não tem Lootboxes disponíveis!\n\n"
                           "**Como conseguir:**\n"
                           "• 🔥 7 dias de login seguidos\n"
                           "• 🎙️ Participar de calls de voz\n"
                           "• 📋 Completar missões semanais\n"
                           "• 🏆 Eventos especiais",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Usa a lootbox
        RewardQueries.use_reward(user_id, 'lootbox')
        
        # Garante que usuário existe e verifica VIP
        user_data = UserQueries.get_or_create_user(user_id, interaction.user.display_name)
        is_vip = user_data.get('is_vip', False)
        
        # Sorteia prêmio
        prize = self.weighted_choice(config.LOOTBOX_PRIZES)
        
        # Aplica prêmios conforme o tipo
        rewards = []
        color = config.EMBED_COLOR_SUCCESS
        
        if prize.get('type') == 'xp':
            xp_base = random.randint(prize.get('xp_min', 100), prize.get('xp_max', 500))
            result = UserQueries.update_xp(user_id, xp_base)
            if result and result.get('booster_applied'):
                xp_final = result.get('xp_gained', xp_base)
                rewards.append(f"⭐ **+{xp_final} XP** 🚀 _(Booster {xp_base}→{xp_final})_")
            else:
                rewards.append(f"⭐ **+{xp_base} XP**")
        
        elif prize.get('type') == 'coins':
            coins_base = prize.get('coins', 5)
            # VIPs ganham o dobro de moedas
            coins = int(coins_base * config.VIP_COINS_MULTIPLIER) if is_vip else coins_base
            UserQueries.update_coins(user_id, coins)
            vip_bonus = " 👑" if is_vip and coins > coins_base else ""
            rewards.append(f"🪙 **+{coins} SHARK COINS**{vip_bonus}")
            color = config.EMBED_COLOR_GOLD
        
        elif prize.get('type') == 'special_role':
            role_name = prize.get('role', 'rei_raspadinha')
            rewards.append(f"👑 **Cargo: REI DA RASPADINHA!**")
            rewards.append(f"🎙️ **Acesso: Call PV com Admin**")
            color = config.EMBED_COLOR_GOLD
            
            # Atribui o cargo especial
            auto_setup_cog = self.bot.get_cog('AutoSetupCog')
            if auto_setup_cog and interaction.guild:
                special_role = await auto_setup_cog.get_or_create_role(
                    interaction.guild,
                    name="👑 Rei da Raspadinha",
                    color=discord.Color.gold(),
                    hoist=True,
                    reason="SharkClub - Prêmio Lootbox"
                )
                if special_role:
                    try:
                        await interaction.user.add_roles(special_role, reason="Ganhou na Lootbox!")
                        print(f"👑 {interaction.user.display_name} ganhou cargo Rei da Raspadinha!")
                    except Exception as e:
                        print(f"❌ Erro ao dar cargo especial: {e}")
        
        elif prize.get('type') == 'legendary_badge':
            badge = prize.get('badge', 'lootbox_legend')
            BadgeQueries.award_badge(user_id, badge, 'legendary')
            rewards.append(f"🏆 **Insígnia Lendária: {badge}**")
            color = config.EMBED_COLOR_LEGENDARY
        
        # Chance de pular 1 nível (2%)
        if random.randint(1, 100) <= config.LOOTBOX_SKIP_LEVEL_CHANCE:
            # Sobe 1 nível
            current_level = user_data.get('level', 1)
            if current_level < 10:
                # Adiciona XP suficiente para próximo nível (sem booster)
                next_level_xp = config.XP_PER_LEVEL.get(current_level + 1, 0)
                current_xp = user_data.get('xp', 0)
                xp_needed = max(0, next_level_xp - current_xp + 1)
                UserQueries.update_xp(user_id, xp_needed, apply_booster=False)
                rewards.append(f"🚀 **SUBIU 1 NÍVEL!**")
                color = config.EMBED_COLOR_LEGENDARY
        
        # Cria embed
        embed = discord.Embed(
            title=f"📦 {prize.get('emoji', '🎁')} {prize.get('name', 'Lootbox')}",
            description=f"**{interaction.user.display_name}** abriu uma Lootbox!",
            color=color
        )
        
        embed.add_field(
            name="🎁 Recompensas",
            value="\n".join(rewards) if rewards else "Boa sorte!",
            inline=False
        )
        
        # GIF de abertura
        embed.set_image(url="https://media1.tenor.com/m/vSC90LPLbZoAAAAC/mystery-box.gif")
        embed.set_footer(text="🦈 SharkClub Lootbox")
        
        # Atualiza missão de minigame
        self.update_minigame_mission(user_id)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="raspadinha", description="🎟️ Use um ticket de Raspadinha Shark! (1x por semana)")
    async def raspadinha(self, interaction: discord.Interaction):
        """Raspadinha Shark - 1 gratuito por semana, tickets extras via lootbox!"""
        user_id = interaction.user.id
        
        # Busca dados do usuário primeiro para verificar VIP
        user_data = UserQueries.get_or_create_user(user_id, interaction.user.display_name)
        is_vip = user_data.get('is_vip', False)
        
        # Verifica cooldown semanal (7 dias FREE, 5 dias VIP)
        can_scratch, remaining = CooldownManager.check(user_id, 'scratch', is_vip=is_vip)
        
        # Verifica se tem ticket extra
        reward = RewardQueries.get_reward(user_id, 'scratch_ticket')
        has_ticket = reward and reward.get('available_count', 0) > 0
        
        # Precisa cooldown liberado OU ticket extra
        if not can_scratch and not has_ticket:
            remaining_text = CooldownManager.format_remaining(remaining)
            vip_tip = "" if is_vip else "\n👑 **VIPs têm cooldown reduzido!**"
            embed = discord.Embed(
                title="🎟️ Sem Tickets",
                description=f"Você já usou sua raspadinha gratuita da semana!\n\n"
                           f"**Próximo gratuito em:** {remaining_text}\n"
                           f"**Ou:** Abra lootboxes para ganhar tickets extras!{vip_tip}",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Decide se usa ticket ou cooldown gratuito
        if has_ticket:
            # Usa ticket extra (não afeta cooldown gratuito)
            RewardQueries.use_reward(user_id, 'scratch_ticket')
        else:
            # Usa o gratuito semanal - seta cooldown
            CooldownManager.set(user_id, 'scratch')
        
        # Sorteia resultado
        result = self.weighted_choice(config.SCRATCH_PRIZES)
        
        # Aplica XP (com booster se ativo)
        xp_base = result.get('xp', 0)
        update_result = UserQueries.update_xp(user_id, xp_base)
        xp_final = xp_base
        booster_applied = False
        if update_result:
            xp_final = update_result.get('xp_gained', xp_base)
            booster_applied = update_result.get('booster_applied', False)
        
        # Se for Jackpot, dá badge especial
        badge_text = ""
        if result.get('special_badge'):
            BadgeQueries.award_badge(user_id, result['special_badge'], 'special')
            badge_text = f"\n🏅 **Insígnia: {result['special_badge']}**"
        
        # Determina cor baseado no prêmio (usa xp_base para determinar tier)
        if xp_base >= 500:
            color = config.EMBED_COLOR_LEGENDARY
            title = "🎟️ 🦈 JACKPOT MEGALODON! 🦈"
        elif xp_base >= 150:
            color = config.EMBED_COLOR_GOLD
            title = "🎟️ 🏆 Prêmio Grande!"
        elif xp_base >= 80:
            color = config.EMBED_COLOR_SUCCESS
            title = "🎟️ 🎟️ Prêmio Médio!"
        elif xp_base >= 30:
            color = config.EMBED_COLOR_PRIMARY
            title = "🎟️ 🎫 Pequeno Prêmio!"
        else:
            color = config.EMBED_COLOR_WARNING
            title = "🎟️ 😢 Que pena..."
        
        # Monta texto do XP
        if booster_applied:
            xp_text = f"⭐ **+{xp_final} XP** 🚀 _(Booster {xp_base}→{xp_final})_{badge_text}"
        else:
            xp_text = f"⭐ **+{xp_final} XP**{badge_text}"
        
        # Cria embed personalizado
        embed = discord.Embed(
            title=title,
            description=f"**{interaction.user.display_name}** raspou um ticket!",
            color=color
        )
        
        embed.add_field(
            name=f"{result.get('emoji', '🎁')} {result.get('name', 'Resultado')}",
            value=xp_text,
            inline=False
        )
        
        # GIF da raspadinha
        embed.set_image(url=config.SCRATCH_GIF)
        embed.set_footer(text="🦈 SharkClub Raspadinha")
        
        # Atualiza missão de minigame
        self.update_minigame_mission(user_id)
        
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MinigamesCog(bot))
