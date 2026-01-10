"""
🦈 SharkClub Discord Bot - Activity & Evaluation Cog
Sistema de monitoramento de atividade e avaliação de membros com estrelas e comentários
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional, List

from database.queries import UserQueries, ActivityQueries, EvaluationQueries, CooldownQueries
from utils.embeds import SharkEmbeds
import config


# ═══════════════════════════════════════════════════════════════
# MODAL PARA AVALIAÇÃO COM COMENTÁRIO
# ═══════════════════════════════════════════════════════════════

class EvaluationModal(discord.ui.Modal):
    """Modal para escrever comentário da avaliação"""
    
    def __init__(self, target: discord.Member, stars: int):
        super().__init__(title=f"Avaliar {target.display_name}")
        self.target = target
        self.stars = stars
        
        self.comment = discord.ui.TextInput(
            label="Seu comentário",
            placeholder="Escreva sua opinião sobre esse membro...",
            min_length=config.EVALUATION_COMMENT_MIN_LENGTH,
            max_length=config.EVALUATION_COMMENT_MAX_LENGTH,
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.comment)
    
    async def on_submit(self, interaction: discord.Interaction):
        evaluator = interaction.user
        comment_text = self.comment.value.strip()
        
        # Busca dados de estrelas
        star_data = config.EVALUATION_STARS.get(self.stars, config.EVALUATION_STARS[3])
        xp_reward = star_data['xp']
        
        # Garante que ambos usuários existem
        UserQueries.get_or_create_user(self.target.id, self.target.display_name)
        UserQueries.get_or_create_user(evaluator.id, evaluator.display_name)
        
        # Cria a avaliação no banco
        EvaluationQueries.create_evaluation(
            evaluator_id=evaluator.id,
            target_id=self.target.id,
            stars=self.stars,
            comment=comment_text,
            xp_given=xp_reward
        )
        
        # Busca XP atual antes
        target_data = UserQueries.get_user(self.target.id)
        old_xp = target_data.get('xp', 0) if target_data else 0
        
        # Dá XP para o avaliado
        UserQueries.update_xp(self.target.id, xp_reward)
        new_xp = old_xp + xp_reward
        
        # Dá XP bônus para quem avaliou
        UserQueries.update_xp(evaluator.id, config.EVALUATOR_XP_BONUS)
        
        # Verifica level up e atribui cargo
        bot = interaction.client
        auto_setup = bot.get_cog('AutoSetupCog')
        if auto_setup and interaction.guild:
            await auto_setup.handle_xp_gain(interaction.guild, self.target, old_xp, new_xp)
        
        # Busca média atualizada
        stats = EvaluationQueries.get_average_stars(self.target.id)
        
        # Cria embed PÚBLICO da avaliação
        embed = discord.Embed(
            title=f"{star_data['emoji']} Nova Avaliação!",
            description=f"**{evaluator.display_name}** avaliou **{self.target.display_name}**",
            color=star_data['color']
        )
        
        embed.add_field(
            name="⭐ Nota",
            value=f"{star_data['emoji']} ({self.stars}/5 - {star_data['label']})",
            inline=True
        )
        
        embed.add_field(
            name="🎁 XP Ganho",
            value=f"+{xp_reward} XP",
            inline=True
        )
        
        embed.add_field(
            name="💬 Comentário",
            value=f"*\"{comment_text}\"*",
            inline=False
        )
        
        embed.add_field(
            name="📊 Média Geral",
            value=f"⭐ {stats['average']} ({stats['count']} avaliações)",
            inline=False
        )
        
        embed.set_thumbnail(url=self.target.display_avatar.url)
        embed.set_footer(text=f"Avaliado por {evaluator.display_name}", icon_url=evaluator.display_avatar.url)
        embed.timestamp = datetime.now(timezone.utc)
        
        # Envia para o canal de avaliações
        sent_to_channel = False
        if auto_setup and interaction.guild:
            sent_to_channel = await auto_setup.send_evaluation_to_channel(interaction.guild, embed)
        
        # Responde ao usuário (ephemeral)
        if sent_to_channel:
            confirm_embed = discord.Embed(
                title="✅ Avaliação Enviada!",
                description=f"Sua avaliação de **{self.target.display_name}** foi publicada no canal de avaliações!\n\n"
                           f"Você ganhou **+{config.EVALUATOR_XP_BONUS} XP** por avaliar.",
                color=config.EMBED_COLOR_SUCCESS
            )
        else:
            confirm_embed = discord.Embed(
                title="✅ Avaliação Registrada!",
                description=f"Sua avaliação de **{self.target.display_name}** foi salva!\n\n"
                           f"Você ganhou **+{config.EVALUATOR_XP_BONUS} XP** por avaliar.",
                color=config.EMBED_COLOR_SUCCESS
            )
        
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# VIEW COM BOTÕES DE ESTRELAS
# ═══════════════════════════════════════════════════════════════

class StarButton(discord.ui.Button):
    """Botão de estrela individual"""
    
    def __init__(self, stars: int, target: discord.Member):
        star_data = config.EVALUATION_STARS.get(stars, {})
        label = f"{stars}⭐ {star_data.get('label', '')}"
        
        # Define cor baseada nas estrelas
        if stars <= 2:
            style = discord.ButtonStyle.danger
        elif stars == 3:
            style = discord.ButtonStyle.secondary
        else:
            style = discord.ButtonStyle.success
        
        super().__init__(label=label, style=style, custom_id=f"star_{stars}")
        self.stars = stars
        self.target = target
    
    async def callback(self, interaction: discord.Interaction):
        # Abre o modal para escrever comentário
        modal = EvaluationModal(self.target, self.stars)
        await interaction.response.send_modal(modal)


class EvaluationStarsView(discord.ui.View):
    """View com botões para selecionar estrelas"""
    
    def __init__(self, target: discord.Member, evaluator: discord.Member):
        super().__init__(timeout=300)  # 5 minutos
        self.target = target
        self.evaluator = evaluator
        
        # Adiciona botões de 1 a 5 estrelas
        for stars in range(1, 6):
            self.add_item(StarButton(stars, target))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Garante que apenas o avaliador original pode usar os botões"""
        if interaction.user.id != self.evaluator.id:
            await interaction.response.send_message(
                "❌ Apenas quem iniciou a avaliação pode escolher a nota!",
                ephemeral=True
            )
            return False
        return True


# ═══════════════════════════════════════════════════════════════
# VIEW COM SELETOR DE USUÁRIO (PARA PAINEL FIXO)
# ═══════════════════════════════════════════════════════════════

class UserSelectView(discord.ui.View):
    """View ephemeral com dropdown para selecionar usuário"""
    
    def __init__(self):
        super().__init__(timeout=60)
    
    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Selecione o membro para avaliar...", min_values=1, max_values=1)
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        target = select.values[0]
        
        # Não pode avaliar a si mesmo
        if target.id == interaction.user.id:
            await interaction.response.send_message("❌ Você não pode avaliar a si mesmo!", ephemeral=True)
            return
        
        # Não pode avaliar bots
        if target.bot:
            await interaction.response.send_message("❌ Você não pode avaliar bots!", ephemeral=True)
            return

        # Verifica cooldown
        can_eval = EvaluationQueries.can_evaluate(
            interaction.user.id, 
            target.id, 
            config.EVALUATION_COOLDOWN_HOURS
        )
        
        if not can_eval:
            await interaction.response.send_message(
                f"⏱️ Você já avaliou **{target.display_name}** recentemente. Tente novamente mais tarde.", 
                ephemeral=True
            )
            return

        # Busca média atual
        stats = EvaluationQueries.get_average_stars(target.id)
        
        embed = discord.Embed(
            title=f"⭐ Avaliar {target.display_name}",
            description="Escolha quantas estrelas dar para este membro:",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        if stats['count'] > 0:
            embed.add_field(name="Média Atual", value=f"⭐ {stats['average']} ({stats['count']} avaliações)")
            
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Abre view de estrelas (ephemeral também)
        view = EvaluationStarsView(target, interaction.user)
        # Editamos a mensagem original do seletor para virar a seleção de estrelas
        await interaction.response.edit_message(content=None, embed=embed, view=view)


class EvaluationPanelView(discord.ui.View):
    """View persistente do painel de avaliações"""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(
        label="Avaliar Alguém",
        style=discord.ButtonStyle.primary,
        emoji="⭐",
        custom_id="eval_panel_start"
    )
    async def start_evaluation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Inicia fluxo de avaliação"""
        view = UserSelectView()
        await interaction.response.send_message(
            "Selecione quem você quer avaliar:",
            view=view,
            ephemeral=True
        )


# ═══════════════════════════════════════════════════════════════
# COG PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class ActivityCog(commands.Cog):
    """Sistema de monitoramento de atividade e avaliações"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Verifica se o usuário é admin"""
        return interaction.user.guild_permissions.administrator
    
    # ═══════════════════════════════════════════════════════════════
    # MONITORAMENTO DE ATIVIDADE EM CANAIS ESPECÍFICOS
    # ═══════════════════════════════════════════════════════════════
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitora mensagens em canais específicos"""
        # Ignora bots
        if message.author.bot:
            return
        
        # Verifica se é um canal monitorado
        if message.channel.id not in config.MONITORED_CHANNELS:
            return
        
        user_id = message.author.id
        
        # Verifica cooldown
        can_xp, remaining = CooldownQueries.check_cooldown(user_id, 'monitored_activity', config.MONITORED_COOLDOWN)
        
        if not can_xp:
            return
        
        # Garante que usuário existe
        UserQueries.get_or_create_user(user_id, message.author.display_name)
        
        # Determina se é post (mensagem longa/original) ou comentário (resposta/curta)
        is_thread = isinstance(message.channel, discord.Thread)
        is_reply = message.reference is not None
        msg_length = len(message.content)
        
        if is_thread or is_reply or msg_length < 100:
            activity_type = 'comment'
            xp_reward = config.MONITORED_COMMENT_XP
        else:
            activity_type = 'post'
            xp_reward = config.MONITORED_POST_XP
        
        # Registra atividade
        ActivityQueries.log_activity(
            user_id=user_id,
            channel_id=message.channel.id,
            activity_type=activity_type,
            message_id=message.id
        )
        
        # Busca XP atual antes de dar
        user_data = UserQueries.get_user(user_id)
        old_xp = user_data.get('xp', 0) if user_data else 0
        
        # Dá XP
        UserQueries.update_xp(user_id, xp_reward)
        new_xp = old_xp + xp_reward
        
        # Verifica level up e atribui cargo
        auto_setup = self.bot.get_cog('AutoSetupCog')
        if auto_setup and message.guild:
            await auto_setup.handle_xp_gain(message.guild, message.author, old_xp, new_xp)
        
        # Seta cooldown
        CooldownQueries.set_cooldown(user_id, 'monitored_activity')
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Monitora reações em canais específicos"""
        # Verifica se é um canal monitorado
        if payload.channel_id not in config.MONITORED_CHANNELS:
            return
        
        # Ignora reações de bots
        if payload.member and payload.member.bot:
            return
        
        user_id = payload.user_id
        
        # Registra atividade (sem XP para reações, apenas tracking)
        ActivityQueries.log_activity(
            user_id=user_id,
            channel_id=payload.channel_id,
            activity_type='reaction',
            message_id=payload.message_id
        )
    
    # ═══════════════════════════════════════════════════════════════
    # COMANDOS DE AVALIAÇÃO COM ESTRELAS E COMENTÁRIOS
    # ═══════════════════════════════════════════════════════════════
    
    @app_commands.command(name="avaliar", description="Avaliar um membro da comunidade com estrelas e comentário")
    @app_commands.describe(membro="Membro que você deseja avaliar")
    async def avaliar(self, interaction: discord.Interaction, membro: discord.Member):
        """Avalia um membro da comunidade"""
        # Não pode avaliar a si mesmo
        if membro.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você não pode avaliar a si mesmo!",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Não pode avaliar bots
        if membro.bot:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você não pode avaliar bots!",
                color=config.EMBED_COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verifica cooldown
        can_eval = EvaluationQueries.can_evaluate(
            interaction.user.id, 
            membro.id, 
            config.EVALUATION_COOLDOWN_HOURS
        )
        
        if not can_eval:
            embed = discord.Embed(
                title="⏰ Aguarde",
                description=f"Você já avaliou **{membro.display_name}** nas últimas {config.EVALUATION_COOLDOWN_HOURS} horas.\n"
                           f"Tente novamente mais tarde!",
                color=config.EMBED_COLOR_WARNING
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Busca média atual do membro
        stats = EvaluationQueries.get_average_stars(membro.id)
        
        # Mostra embed com opções de avaliação
        embed = discord.Embed(
            title="⭐ Avaliar Membro",
            description=f"Escolha quantas estrelas dar para **{membro.display_name}**:\n\n"
                       f"Após escolher, você poderá escrever um comentário.",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        # Mostra média atual se houver avaliações
        if stats['count'] > 0:
            embed.add_field(
                name="📊 Avaliação Atual",
                value=f"⭐ **{stats['average']}** média ({stats['count']} avaliações)",
                inline=False
            )
        
        # Lista XP por estrela
        xp_info = ""
        for stars, data in config.EVALUATION_STARS.items():
            xp_info += f"{data['emoji']} **{data['label']}** → +{data['xp']} XP\n"
        embed.add_field(name="🎁 XP por Nota", value=xp_info, inline=False)
        
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text=f"Você também ganha +{config.EVALUATOR_XP_BONUS} XP por avaliar!")
        
        view = EvaluationStarsView(membro, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="avaliacoes", description="Ver avaliações de um membro")
    @app_commands.describe(membro="Membro para ver as avaliações (deixe vazio para ver as suas)")
    async def avaliacoes(self, interaction: discord.Interaction, membro: Optional[discord.Member] = None):
        """Mostra avaliações públicas de um membro"""
        target = membro or interaction.user
        
        # Busca avaliações recebidas
        evaluations = EvaluationQueries.get_user_evaluations_received(target.id, limit=10)
        stats = EvaluationQueries.get_average_stars(target.id)
        
        # Cria embed
        embed = discord.Embed(
            title=f"⭐ Avaliações de {target.display_name}",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Mostra média geral
        if stats['count'] > 0:
            # Gera visual de estrelas baseado na média
            avg = stats['average']
            full_stars = int(avg)
            star_visual = "⭐" * full_stars + "☆" * (5 - full_stars)
            
            embed.add_field(
                name="📊 Média Geral",
                value=f"{star_visual}\n**{avg}/5** ({stats['count']} avaliações)\n"
                      f"Total: **{stats['total_xp']:,}** XP ganhos",
                inline=False
            )
        else:
            embed.add_field(
                name="📊 Média Geral",
                value="Ainda não recebeu avaliações.",
                inline=False
            )
        
        # Lista últimas avaliações
        if evaluations:
            for i, eval in enumerate(evaluations[:5], 1):
                stars = eval.get('stars', 0)
                comment = eval.get('comment', 'Sem comentário')
                evaluator_id = eval.get('evaluator_id')
                created_at = eval.get('created_at', '')
                
                # Tenta buscar nome do avaliador
                try:
                    evaluator = await self.bot.fetch_user(evaluator_id)
                    evaluator_name = evaluator.display_name
                except:
                    evaluator_name = f"Usuário #{evaluator_id}"
                
                # Formata data
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = dt.strftime('%d/%m/%Y')
                except:
                    date_str = "Data desconhecida"
                
                star_data = config.EVALUATION_STARS.get(stars, {})
                star_emoji = star_data.get('emoji', '⭐' * stars)
                
                embed.add_field(
                    name=f"{star_emoji} por {evaluator_name} ({date_str})",
                    value=f"*\"{comment[:100]}{'...' if len(comment) > 100 else ''}\"*",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="minhas-avaliacoes", description="Ver estatísticas das suas avaliações")
    async def minhas_avaliacoes(self, interaction: discord.Interaction):
        """Mostra estatísticas de avaliações do usuário"""
        user_id = interaction.user.id
        
        stats = EvaluationQueries.get_evaluation_stats(user_id)
        
        embed = discord.Embed(
            title="📊 Suas Avaliações",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Média de estrelas
        if stats['average_stars'] > 0:
            avg = stats['average_stars']
            full_stars = int(avg)
            star_visual = "⭐" * full_stars + "☆" * (5 - full_stars)
            embed.add_field(
                name="⭐ Sua Média",
                value=f"{star_visual}\n**{avg}/5**",
                inline=True
            )
        
        embed.add_field(
            name="📥 Recebidas",
            value=f"**{stats['received_count']}** avaliações",
            inline=True
        )
        
        embed.add_field(
            name="📤 Dadas",
            value=f"**{stats['given_count']}** avaliações",
            inline=True
        )
        
        embed.add_field(
            name="🎁 XP de Avaliações",
            value=f"**{stats['total_xp_from_evals']:,}** XP",
            inline=True
        )
        
        # Breakdown por estrelas
        if stats['star_breakdown']:
            breakdown_text = ""
            for stars in range(5, 0, -1):  # De 5 a 1
                count = stats['star_breakdown'].get(stars, 0)
                if count > 0:
                    bar = "█" * min(count, 10)
                    breakdown_text += f"{'⭐' * stars}: {bar} **{count}**\n"
            
            if breakdown_text:
                embed.add_field(name="📈 Distribuição", value=breakdown_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="minha-atividade", description="Ver sua atividade nos canais monitorados")
    async def minha_atividade(self, interaction: discord.Interaction):
        """Mostra estatísticas de atividade do usuário"""
        user_id = interaction.user.id
        
        stats = ActivityQueries.get_user_activity_stats(user_id, days=7)
        
        embed = discord.Embed(
            title="📊 Sua Atividade (7 dias)",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        embed.add_field(
            name="📝 Posts",
            value=f"**{stats['posts']}**",
            inline=True
        )
        
        embed.add_field(
            name="💬 Comentários",
            value=f"**{stats['comments']}**",
            inline=True
        )
        
        embed.add_field(
            name="👍 Reações",
            value=f"**{stats['reactions']}**",
            inline=True
        )
        
        embed.add_field(
            name="📈 Total",
            value=f"**{stats['total']}** atividades",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ═══════════════════════════════════════════════════════════════
    # COMANDOS ADMIN
    # ═══════════════════════════════════════════════════════════════
    
    def is_admin_check():
        """Decorator para verificar permissão de admin"""
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)
    
    @app_commands.command(name="admin-atividade", description="[ADMIN] Ver estatísticas de atividade do servidor")
    @is_admin_check()
    async def admin_atividade(self, interaction: discord.Interaction, dias: int = 7):
        """Estatísticas de atividade do servidor"""
        await interaction.response.defer(ephemeral=True)
        
        # Top usuários ativos
        top_active = ActivityQueries.get_top_active_users(days=dias, limit=10)
        
        embed = discord.Embed(
            title=f"📊 Atividade do Servidor ({dias} dias)",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        if top_active:
            active_text = ""
            for i, user_data in enumerate(top_active, 1):
                user_id = user_data['user_id']
                count = user_data['activity_count']
                try:
                    member = await interaction.guild.fetch_member(user_id)
                    name = member.display_name
                except:
                    name = f"User {user_id}"
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
                active_text += f"{medal} **{name}** - {count} atividades\n"
            
            embed.add_field(name="🏆 Mais Ativos", value=active_text, inline=False)
        else:
            embed.add_field(name="🏆 Mais Ativos", value="Sem dados ainda", inline=False)
        
        # Canais monitorados
        if config.MONITORED_CHANNELS:
            channels_text = ""
            for channel_id in config.MONITORED_CHANNELS[:5]:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    stats = ActivityQueries.get_channel_activity_stats(channel_id, days=dias)
                    channels_text += f"#{channel.name}: **{stats['total']}** atividades\n"
            embed.add_field(name="📢 Canais Monitorados", value=channels_text or "Nenhum configurado", inline=False)
        else:
            embed.add_field(name="📢 Canais Monitorados", value="Nenhum configurado. Use `config.py` para adicionar.", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="admin-avaliacoes", description="[ADMIN] Ver top avaliados do servidor")
    @is_admin_check()
    async def admin_avaliacoes(self, interaction: discord.Interaction, dias: int = 30):
        """Top membros mais bem avaliados"""
        await interaction.response.defer(ephemeral=True)
        
        top_evaluated = EvaluationQueries.get_top_evaluated(days=dias, limit=10)
        
        embed = discord.Embed(
            title=f"⭐ Top Avaliados ({dias} dias)",
            color=config.EMBED_COLOR_GOLD
        )
        
        if top_evaluated:
            eval_text = ""
            for i, user_data in enumerate(top_evaluated, 1):
                user_id = user_data['user_id']
                avg_stars = user_data.get('average_stars', 0)
                eval_count = user_data['eval_count']
                
                try:
                    member = await interaction.guild.fetch_member(user_id)
                    name = member.display_name
                except:
                    name = f"User {user_id}"
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
                eval_text += f"{medal} **{name}** - ⭐ {avg_stars} média ({eval_count} avaliações)\n"
            
            embed.add_field(name="🏆 Mais Bem Avaliados", value=eval_text, inline=False)
        else:
            embed.add_field(name="🏆 Mais Bem Avaliados", value="Sem avaliações ainda", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="admin-add-canal", description="[ADMIN] Ver instruções para adicionar canal monitorado")
    @is_admin_check()
    async def admin_add_canal(self, interaction: discord.Interaction, canal: discord.TextChannel):
        """Instrução para adicionar canal à lista de monitorados"""
        embed = discord.Embed(
            title="📢 Adicionar Canal Monitorado",
            description=f"Para monitorar o canal **#{canal.name}**, adicione o ID no arquivo `config.py`:\n\n"
                       f"```python\nMONITORED_CHANNELS = [{canal.id}]\n```\n\n"
                       f"**ID do canal:** `{canal.id}`",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.add_field(
            name="📌 Nota",
            value="Após editar o arquivo, reinicie o bot para aplicar as mudanças.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="admin-setup-avaliacoes", description="[ADMIN] Enviar painel de avaliações fixo")
    @is_admin_check()
    async def admin_setup_avaliacoes(self, interaction: discord.Interaction):
        """Envia painel fixo de avaliações para o canal configurado"""
        await interaction.response.defer(ephemeral=True)
        
        channel_id = config.CHANNEL_IDS.get("avaliacoes")
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            await interaction.followup.send(f"❌ Canal de avaliações não encontrado (ID: {channel_id})", ephemeral=True)
            return

        embed = discord.Embed(
            title="⭐ Sistema de Avaliações",
            description="Reconheça membros que ajudaram você ou contribuíram para a comunidade!\n\n"
                       "**Como funciona:**\n"
                       "1. Clique no botão abaixo\n"
                       "2. Selecione o membro\n"
                       "3. Escolha a nota (1-5 estrelas)\n"
                       "4. Escreva um comentário\n\n"
                       "🏆 **Recompensas:** Tanto quem avalia quanto quem recebe ganha XP!",
            color=config.EMBED_COLOR_GOLD
        )
        embed.set_footer(text="SharkClub - Cultura de Reconhecimento")
        
        view = EvaluationPanelView(self.bot)
        
        # Envia nova mensagem (force new)
        await channel.send(embed=embed, view=view)
        
        await interaction.followup.send(f"✅ Painel de avaliações enviado para {channel.mention}!", ephemeral=True)

    @app_commands.command(name="admin-ver-atividade", description="[ADMIN] Ver atividade de um membro específico")
    @is_admin_check()
    async def admin_ver_atividade(self, interaction: discord.Interaction, membro: discord.Member, dias: int = 7):
        """Ver atividade detalhada de um membro"""
        stats = ActivityQueries.get_user_activity_stats(membro.id, days=dias)
        eval_stats = EvaluationQueries.get_evaluation_stats(membro.id)
        
        embed = discord.Embed(
            title=f"📊 Atividade de {membro.display_name}",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        
        # Atividade
        embed.add_field(
            name=f"📈 Atividade ({dias} dias)",
            value=f"📝 Posts: **{stats['posts']}**\n"
                  f"💬 Comentários: **{stats['comments']}**\n"
                  f"👍 Reações: **{stats['reactions']}**\n"
                  f"📊 Total: **{stats['total']}**",
            inline=True
        )
        
        # Avaliações
        embed.add_field(
            name="⭐ Avaliações",
            value=f"📥 Recebidas: **{eval_stats['received_count']}**\n"
                  f"📤 Dadas: **{eval_stats['given_count']}**\n"
                  f"⭐ Média: **{eval_stats['average_stars']}**\n"
                  f"🎁 XP de avaliações: **{eval_stats['total_xp_from_evals']}**",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Error handlers
    @admin_atividade.error
    @admin_avaliacoes.error
    @admin_add_canal.error
    @admin_ver_atividade.error
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


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityCog(bot))
