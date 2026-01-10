"""
🦈 SharkClub Discord Bot - Shop Cog
Loja de itens com SHARK COINS + Sistema de Agendamento de Calls
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime, timezone, timedelta

from database.queries import UserQueries, ShopQueries
from utils.embeds import SharkEmbeds
import config


def generate_date_options():
    """Gera opções de datas para os próximos 7 dias"""
    options = []
    today = datetime.now()
    
    # Dias da semana em português
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    for i in range(7):  # Apenas 7 dias
        date = today + timedelta(days=i)
        dia_semana = dias_semana[date.weekday()]
        mes = meses[date.month - 1]
        
        if i == 0:
            label = f"Hoje ({dia_semana}, {date.day} {mes})"
        elif i == 1:
            label = f"Amanhã ({dia_semana}, {date.day} {mes})"
        else:
            label = f"{dia_semana}, {date.day} {mes}"
        
        options.append(discord.SelectOption(
            label=label,
            value=date.strftime('%Y-%m-%d'),
            emoji="📅"
        ))
    
    return options


def generate_time_options():
    """Gera opções de horários (9:00 às 21:00, intervalos de 1h)"""
    options = []
    
    # Horários principais (13 opções)
    for hour in range(9, 22):
        time_str = f"{hour:02d}:00"
        
        # Emojis baseados no período
        if hour < 12:
            emoji = "🌅"  # Manhã
        elif hour < 18:
            emoji = "☀️"  # Tarde
        else:
            emoji = "🌙"  # Noite
        
        options.append(discord.SelectOption(
            label=time_str,
            value=time_str,
            emoji=emoji
        ))
    
    return options



class DateSelect(discord.ui.Select):
    """Select menu para escolher a data"""
    
    def __init__(self):
        options = generate_date_options()
        super().__init__(
            placeholder="📅 Escolha a data...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        self.view.selected_date = self.values[0]
        await interaction.response.defer()
        await self.view.check_and_confirm(interaction)


class TimeSelect(discord.ui.Select):
    """Select menu para escolher o horário"""
    
    def __init__(self):
        options = generate_time_options()
        super().__init__(
            placeholder="⏰ Escolha o horário...",
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        self.view.selected_time = self.values[0]
        await interaction.response.defer()
        await self.view.check_and_confirm(interaction)


class ScheduleCallView(discord.ui.View):
    """View com Select menus para agendar data e horário da call"""
    
    def __init__(self, purchase_id: int, buyer_id: int, target_id: int, guild_id: int, bot: commands.Bot):
        super().__init__(timeout=300)  # 5 minutos
        self.purchase_id = purchase_id
        self.buyer_id = buyer_id
        self.target_id = target_id
        self.guild_id = guild_id
        self.bot = bot
        self.selected_date = None
        self.selected_time = None
        self.confirmed = False
        
        # Adiciona os selects
        self.add_item(DateSelect())
        self.add_item(TimeSelect())
    
    async def check_and_confirm(self, interaction: discord.Interaction):
        """Verifica se data e hora foram selecionadas e confirma"""
        if not self.selected_date or not self.selected_time or self.confirmed:
            return
        
        self.confirmed = True
        
        # Parseia a data e hora
        date_parts = self.selected_date.split('-')
        time_parts = self.selected_time.split(':')
        
        scheduled_dt = datetime(
            year=int(date_parts[0]),
            month=int(date_parts[1]),
            day=int(date_parts[2]),
            hour=int(time_parts[0]),
            minute=int(time_parts[1])
        )
        
        # Formata para exibição
        data_str = scheduled_dt.strftime('%d/%m/%Y')
        hora_str = scheduled_dt.strftime('%H:%M')
        
        # Atualiza status e data agendada
        ShopQueries.update_purchase_schedule(self.purchase_id, 'scheduled', scheduled_dt.isoformat())
        
        # Busca o servidor
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            await interaction.followup.send("❌ Servidor não encontrado!", ephemeral=True)
            return
        
        # Busca os membros
        buyer = guild.get_member(self.buyer_id)
        target = guild.get_member(self.target_id)
        
        if not buyer or not target:
            await interaction.followup.send("❌ Usuários não encontrados no servidor!", ephemeral=True)
            return
        
        # Cria canal de voz com permissões especiais
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=True,
                connect=False,
                speak=False
            ),
            buyer: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                stream=True
            ),
            target: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                stream=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True
            )
        }
        
        channel_name = f"📞 Call #{self.purchase_id} - {data_str} {hora_str}"
        
        try:
            category = discord.utils.get(guild.categories, name="📞 Calls Agendadas")
            if not category:
                category = await guild.create_category(
                    name="📞 Calls Agendadas",
                    overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True)}
                )
            
            voice_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Call agendada #{self.purchase_id}"
            )
            
            ShopQueries.update_purchase_channel(self.purchase_id, voice_channel.id)
            
            # Desabilita os selects
            for child in self.children:
                child.disabled = True
            
            await interaction.message.edit(
                content=f"✅ **Call agendada com sucesso!**\n\n"
                       f"📅 **Data:** {data_str}\n"
                       f"⏰ **Horário:** {hora_str}\n"
                       f"🎙️ **Canal:** {voice_channel.mention}\n\n"
                       f"Apenas você e <@{self.buyer_id}> podem entrar!",
                view=self
            )
            
            # Notifica o comprador
            try:
                buyer_user = await self.bot.fetch_user(self.buyer_id)
                await buyer_user.send(
                    f"🎉 **Sua call foi agendada!**\n\n"
                    f"📅 **Data:** {data_str}\n"
                    f"⏰ **Horário:** {hora_str}\n"
                    f"👤 **Com:** {interaction.user.display_name}\n"
                    f"🏠 **Servidor:** {guild.name}\n\n"
                    f"Um canal de voz exclusivo foi criado para vocês!"
                )
            except:
                pass
            
            # Envia relatório público no canal de reports
            try:
                # Busca canal de reports pelo ID fixo
                reports_channel_id = config.CHANNEL_IDS.get("calls_marcadas")
                reports_channel = self.bot.get_channel(reports_channel_id)
                
                # Fallback: Tenta fetch se get retornar None (pode não estar no cache)
                if not reports_channel:
                    try:
                        reports_channel = await self.bot.fetch_channel(reports_channel_id)
                    except Exception as e:
                        print(f"❌ Erro ao fazer fetch do canal {reports_channel_id}: {e}")
                
                if reports_channel:
                    print(f"📢 Enviando relatório para canal: {reports_channel.name} ({reports_channel.id})")
                    report_embed = discord.Embed(
                        title="📞 Nova Call Agendada!",
                        description=f"Uma call foi comprada e agendada com sucesso!",
                        color=config.EMBED_COLOR_SUCCESS
                    )
                    report_embed.add_field(
                        name="👤 Comprador",
                        value=f"<@{self.buyer_id}>",
                        inline=True
                    )
                    report_embed.add_field(
                        name="🎯 Expert",
                        value=f"<@{self.target_id}>",
                        inline=True
                    )
                    report_embed.add_field(
                        name="📅 Agendamento",
                        value=f"{data_str} às {hora_str}",
                        inline=True
                    )
                    report_embed.set_footer(text=f"Call #{self.purchase_id} | 🦈 SharkClub Shop")
                    await reports_channel.send(embed=report_embed)
                else:
                    print(f"⚠️ Canal de reports de call não encontrado (ID: {reports_channel_id})")
            except Exception as e:
                print(f"❌ Erro ao enviar relatório de call: {e}")
                
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para criar canais!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)



class CallResponseView(discord.ui.View):
    """View com botões para aceitar/recusar pedido de call"""
    
    def __init__(self, purchase_id: int, buyer_id: int, target_id: int, guild_id: int, bot: commands.Bot = None):
        super().__init__(timeout=None)  # Persistente
        self.purchase_id = purchase_id
        self.buyer_id = buyer_id
        self.target_id = target_id
        self.guild_id = guild_id
        self.bot = bot
        
        # Cria custom_ids dinâmicos com os dados
        accept_id = f"call_accept:{purchase_id}:{buyer_id}:{target_id}:{guild_id}"
        decline_id = f"call_decline:{purchase_id}:{buyer_id}:{target_id}:{guild_id}"
        
        # Remove botões padrão e adiciona novos
        self.clear_items()
        
        accept_btn = discord.ui.Button(
            label="✅ Aceitar e Agendar",
            style=discord.ButtonStyle.success,
            custom_id=accept_id
        )
        decline_btn = discord.ui.Button(
            label="❌ Recusar",
            style=discord.ButtonStyle.danger,
            custom_id=decline_id
        )
        
        self.add_item(accept_btn)
        self.add_item(decline_btn)


class PersistentCallButtons(discord.ui.View):
    """View persistente para botões de call - registrada no bot"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="✅ Aceitar e Agendar", style=discord.ButtonStyle.success, custom_id="call_accept_btn")
    async def accept_placeholder(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Este é apenas placeholder, a lógica real está no listener
        pass
    
    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="call_decline_btn")
    async def decline_placeholder(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


class ShopCog(commands.Cog):
    """Loja de itens com SHARK COINS"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Listener para tratar botões persistentes"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get('custom_id', '')
        print(f"[SHOP] Interação recebida: {custom_id}")  # Debug
        
        # Verifica se é um botão de call
        if custom_id.startswith('call_accept:'):
            print(f"[SHOP] Processando aceitar call")  # Debug
            await self.handle_accept_call(interaction, custom_id)
        elif custom_id.startswith('call_decline:'):
            print(f"[SHOP] Processando recusar call")  # Debug
            await self.handle_decline_call(interaction, custom_id)

    
    async def handle_accept_call(self, interaction: discord.Interaction, custom_id: str):
        """Lida com aceitar call"""
        try:
            parts = custom_id.split(':')
            purchase_id = int(parts[1])
            buyer_id = int(parts[2])
            target_id = int(parts[3])
            guild_id = int(parts[4])
            print(f"[SHOP] Dados: purchase={purchase_id}, buyer={buyer_id}, target={target_id}, guild={guild_id}")
        except Exception as e:
            print(f"[SHOP] Erro ao parsear: {e}")
            await interaction.response.send_message("❌ Erro ao processar!", ephemeral=True)
            return
        
        if interaction.user.id != target_id:
            await interaction.response.send_message("❌ Apenas a pessoa solicitada pode responder!", ephemeral=True)
            return
        
        try:
            # Desabilita botões na mensagem original
            view = discord.ui.View()
            accept_btn = discord.ui.Button(label="✅ Aceitar e Agendar", style=discord.ButtonStyle.success, disabled=True)
            decline_btn = discord.ui.Button(label="❌ Recusar", style=discord.ButtonStyle.danger, disabled=True)
            view.add_item(accept_btn)
            view.add_item(decline_btn)
            
            await interaction.response.edit_message(view=view)
            print("[SHOP] Botões desabilitados com sucesso")
            
            # Envia view de agendamento
            schedule_view = ScheduleCallView(
                purchase_id=purchase_id,
                buyer_id=buyer_id,
                target_id=target_id,
                guild_id=guild_id,
                bot=self.bot
            )
            
            await interaction.followup.send(
                "📅 **Escolha a data e horário da call:**\n\n"
                "Selecione abaixo quando você pode atender.",
                view=schedule_view
            )
            print("[SHOP] View de agendamento enviada")
        except Exception as e:
            print(f"[SHOP] Erro: {e}")
            import traceback
            traceback.print_exc()

    
    async def handle_decline_call(self, interaction: discord.Interaction, custom_id: str):
        """Lida com recusar call"""
        try:
            parts = custom_id.split(':')
            purchase_id = int(parts[1])
            buyer_id = int(parts[2])
            target_id = int(parts[3])
        except:
            await interaction.response.send_message("❌ Erro ao processar!", ephemeral=True)
            return
        
        if interaction.user.id != target_id:
            await interaction.response.send_message("❌ Apenas a pessoa solicitada pode responder!", ephemeral=True)
            return
        
        # Atualiza status
        ShopQueries.update_purchase_status(purchase_id, 'declined')
        
        # Busca a compra e devolve moedas
        purchase = ShopQueries.get_purchase(purchase_id)
        price_paid = 0
        if purchase:
            price_paid = purchase.get('price_paid', 0)
            UserQueries.update_coins(buyer_id, price_paid)
        
        # Desabilita botões
        view = discord.ui.View()
        accept_btn = discord.ui.Button(label="✅ Aceitar e Agendar", style=discord.ButtonStyle.success, disabled=True)
        decline_btn = discord.ui.Button(label="❌ Recusar", style=discord.ButtonStyle.danger, disabled=True)
        view.add_item(accept_btn)
        view.add_item(decline_btn)
        
        await interaction.response.edit_message(view=view)
        
        await interaction.followup.send(
            f"❌ Você **recusou** a call com <@{buyer_id}>.\n"
            f"As moedas foram devolvidas ao comprador.",
            ephemeral=True
        )
        
        # Notifica o comprador
        try:
            buyer = await self.bot.fetch_user(buyer_id)
            await buyer.send(
                f"😔 {interaction.user.display_name} **recusou** seu pedido de call.\n"
                f"💰 Suas **{price_paid} SHARK COINS** foram devolvidas!"
            )
        except:
            pass

    
    @app_commands.command(name="loja", description="Ver a loja de itens do SharkClub")
    async def loja(self, interaction: discord.Interaction):
        """Exibe a loja com todos os itens disponíveis"""
        await interaction.response.defer(ephemeral=True)
        
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        coins = user_data.get('coins', 0)
        is_vip = user_data.get('is_vip', False)
        
        # Define cor baseado no VIP
        embed_color = config.EMBED_COLOR_VIP if is_vip else config.EMBED_COLOR_PRIMARY
        
        embed = discord.Embed(
            title=f"{config.EMOJI_SHOP} Loja SharkClub",
            description=f"Gaste suas SHARK COINS em itens especiais!\n\n"
                       f"💰 **Seu saldo:** {coins:,} {config.EMOJI_COINS}",
            color=embed_color
        )
        
        # Lista todos os itens
        for item_id, item in config.SHOP_ITEMS.items():
            price = item['price_vip'] if is_vip else item['price_free']
            discount_text = ""
            
            if is_vip and item['price_vip'] < item['price_free']:
                discount = int((1 - item['price_vip'] / item['price_free']) * 100)
                discount_text = f" ~~{item['price_free']}~~ (-{discount}% VIP)"
            
            can_afford = "✅" if coins >= price else "❌"
            
            embed.add_field(
                name=f"{item['emoji']} {item['name']}",
                value=f"{item['description']}\n"
                      f"💰 **{price:,}** {config.EMOJI_COINS}{discount_text}\n"
                      f"{can_afford} Use `/comprar {item_id}`",
                inline=False
            )
        
        # Dica VIP
        if not is_vip:
            embed.add_field(
                name="💡 Dica",
                value=f"Usuários {config.EMOJI_VIP} VIP têm desconto em todos os itens!",
                inline=False
            )
        
        embed.set_footer(text="🦈 SharkClub Shop")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="comprar", description="Comprar um item da loja")
    @app_commands.describe(
        item="Item que deseja comprar",
        membro="Membro para quem você quer solicitar a call (obrigatório para call_expert)"
    )
    @app_commands.choices(item=[
        app_commands.Choice(name="📞 Call com Expert (1000 coins)", value="call_expert"),
    ])
    async def comprar(self, interaction: discord.Interaction, item: str, membro: Optional[discord.Member] = None):
        """Compra um item da loja"""
        await interaction.response.defer(ephemeral=True)
        
        # Verifica se o item existe
        if item not in config.SHOP_ITEMS:
            await interaction.followup.send("❌ Item não encontrado na loja!", ephemeral=True)
            return
        
        shop_item = config.SHOP_ITEMS[item]
        
        # Para call_expert, precisa escolher um membro
        if shop_item.get('requires_target') and not membro:
            await interaction.followup.send(
                f"❌ Você precisa escolher um membro para solicitar a call!\n"
                f"Use: `/comprar {item} @membro`",
                ephemeral=True
            )
            return
        
        # Não pode comprar call consigo mesmo
        if membro and membro.id == interaction.user.id:
            await interaction.followup.send("❌ Você não pode solicitar uma call consigo mesmo!", ephemeral=True)
            return
        
        # Não pode comprar call com bot
        if membro and membro.bot:
            await interaction.followup.send("❌ Você não pode solicitar uma call com um bot!", ephemeral=True)
            return
        
        # Busca dados do usuário
        user_data = UserQueries.get_or_create_user(interaction.user.id, interaction.user.display_name)
        coins = user_data.get('coins', 0)
        is_vip = user_data.get('is_vip', False)
        
        # Calcula preço
        price = shop_item['price_vip'] if is_vip else shop_item['price_free']
        
        # Verifica saldo
        if coins < price:
            await interaction.followup.send(
                f"❌ Saldo insuficiente!\n"
                f"💰 Você tem: **{coins:,}** {config.EMOJI_COINS}\n"
                f"💸 Preço: **{price:,}** {config.EMOJI_COINS}\n"
                f"📉 Faltam: **{price - coins:,}** {config.EMOJI_COINS}",
                ephemeral=True
            )
            return
        
        # Desconta moedas
        UserQueries.update_coins(interaction.user.id, -price)
        
        # Registra compra
        purchase = ShopQueries.create_purchase(
            buyer_id=interaction.user.id,
            item_id=item,
            target_id=membro.id if membro else None,
            price_paid=price,
            guild_id=interaction.guild.id if interaction.guild else None
        )
        
        if not purchase:
            # Devolve moedas se falhou
            UserQueries.update_coins(interaction.user.id, price)
            await interaction.followup.send("❌ Erro ao processar a compra. Tente novamente.", ephemeral=True)
            return
        
        # Para call_expert, envia DM para o membro escolhido
        if item == "call_expert" and membro:
            try:
                # Cria embed para o membro
                dm_embed = discord.Embed(
                    title=f"📞 Pedido de Call!",
                    description=f"**{interaction.user.display_name}** quer fazer uma call com você!",
                    color=config.EMBED_COLOR_PRIMARY
                )
                
                dm_embed.add_field(
                    name="👤 Solicitante",
                    value=f"{interaction.user.mention}\n({interaction.user.display_name})",
                    inline=True
                )
                
                dm_embed.add_field(
                    name="🏠 Servidor",
                    value=interaction.guild.name if interaction.guild else "Desconhecido",
                    inline=True
                )
                
                dm_embed.add_field(
                    name="⏰ Tempo limite",
                    value=f"Responda em até {config.CALL_REQUEST_EXPIRY_HOURS}h",
                    inline=False
                )
                
                dm_embed.add_field(
                    name="📅 Agendamento",
                    value="Ao aceitar, você escolherá a data e hora.\nUm canal de voz exclusivo será criado!",
                    inline=False
                )
                
                dm_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                dm_embed.set_footer(text=f"ID da compra: #{purchase['id']}")
                
                # Cria view com botões
                view = CallResponseView(
                    purchase_id=purchase['id'],
                    buyer_id=interaction.user.id,
                    target_id=membro.id,
                    guild_id=interaction.guild.id if interaction.guild else 0,
                    bot=self.bot
                )
                
                # Envia DM
                await membro.send(embed=dm_embed, view=view)
                
                # Confirma para o comprador
                success_embed = discord.Embed(
                    title="✅ Compra realizada!",
                    description=f"Você comprou: **{shop_item['name']}**",
                    color=config.EMBED_COLOR_SUCCESS
                )
                
                success_embed.add_field(
                    name="💰 Valor pago",
                    value=f"**{price:,}** {config.EMOJI_COINS}",
                    inline=True
                )
                
                success_embed.add_field(
                    name="👤 Solicitado para",
                    value=membro.mention,
                    inline=True
                )
                
                success_embed.add_field(
                    name="📋 Status",
                    value=f"{config.CALL_STATUS['pending']['emoji']} Aguardando resposta...\n"
                          f"Quando aceito, a pessoa escolherá data/hora.\n"
                          f"Se recusado, suas moedas serão devolvidas.",
                    inline=False
                )
                
                success_embed.set_footer(text=f"ID da compra: #{purchase['id']}")
                
                await interaction.followup.send(embed=success_embed, ephemeral=True)
                
            except discord.Forbidden:
                # Não conseguiu enviar DM - devolve moedas
                UserQueries.update_coins(interaction.user.id, price)
                ShopQueries.update_purchase_status(purchase['id'], 'expired')
                
                await interaction.followup.send(
                    f"❌ Não foi possível enviar mensagem para {membro.mention}!\n"
                    f"Provavelmente as DMs estão desativadas.\n"
                    f"💰 Suas **{price:,} SHARK COINS** foram devolvidas.",
                    ephemeral=True
                )
    
    @app_commands.command(name="pedidos", description="Ver pedidos de call pendentes para você")
    async def pedidos(self, interaction: discord.Interaction):
        """Lista pedidos de call pendentes para o usuário"""
        await interaction.response.defer(ephemeral=True)
        
        pending = ShopQueries.get_pending_calls_for_user(interaction.user.id)
        
        if not pending:
            await interaction.followup.send(
                "📭 Você não tem pedidos de call pendentes!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📞 Pedidos de Call Pendentes",
            description=f"Você tem **{len(pending)}** pedido(s) aguardando resposta.",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        for purchase in pending[:10]:  # Máximo 10
            buyer_id = purchase.get('buyer_id')
            created_at = purchase.get('created_at', 'Desconhecido')
            purchase_id = purchase.get('id')
            
            embed.add_field(
                name=f"#{purchase_id}",
                value=f"👤 Solicitante: <@{buyer_id}>\n"
                      f"📅 Data: {created_at[:10] if created_at else 'N/A'}",
                inline=False
            )
        
        embed.set_footer(text="Responda via DM do bot ou use /aceitar ou /recusar")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="aceitar", description="Aceitar um pedido de call")
    @app_commands.describe(id="ID do pedido de call")
    async def aceitar(self, interaction: discord.Interaction, id: int):
        """Aceita um pedido de call pelo ID"""
        purchase = ShopQueries.get_purchase(id)
        
        if not purchase:
            await interaction.response.send_message("❌ Pedido não encontrado!", ephemeral=True)
            return
        
        if purchase.get('target_id') != interaction.user.id:
            await interaction.response.send_message("❌ Este pedido não é para você!", ephemeral=True)
            return
        
        if purchase.get('status') != 'pending':
            await interaction.response.send_message(
                f"❌ Este pedido já foi {purchase.get('status', 'processado')}!",
                ephemeral=True
            )
            return
        
        # Envia view de agendamento com dropdowns
        guild_id = purchase.get('guild_id') or (interaction.guild.id if interaction.guild else 0)
        schedule_view = ScheduleCallView(
            purchase_id=id,
            buyer_id=purchase.get('buyer_id'),
            target_id=interaction.user.id,
            guild_id=guild_id,
            bot=self.bot
        )
        
        await interaction.response.send_message(
            "📅 **Escolha a data e horário da call:**\n\n"
            "Selecione abaixo quando você pode atender.",
            view=schedule_view,
            ephemeral=True
        )

    
    @app_commands.command(name="recusar", description="Recusar um pedido de call")
    @app_commands.describe(id="ID do pedido de call")
    async def recusar(self, interaction: discord.Interaction, id: int):
        """Recusa um pedido de call pelo ID"""
        await interaction.response.defer(ephemeral=True)
        
        purchase = ShopQueries.get_purchase(id)
        
        if not purchase:
            await interaction.followup.send("❌ Pedido não encontrado!", ephemeral=True)
            return
        
        if purchase.get('target_id') != interaction.user.id:
            await interaction.followup.send("❌ Este pedido não é para você!", ephemeral=True)
            return
        
        if purchase.get('status') != 'pending':
            await interaction.followup.send(
                f"❌ Este pedido já foi {purchase.get('status', 'processado')}!",
                ephemeral=True
            )
            return
        
        # Recusa e devolve moedas
        ShopQueries.update_purchase_status(id, 'declined')
        
        price_paid = purchase.get('price_paid', 0)
        buyer_id = purchase.get('buyer_id')
        UserQueries.update_coins(buyer_id, price_paid)
        
        await interaction.followup.send(
            f"❌ Você **recusou** a call com <@{buyer_id}>.\n"
            f"As moedas foram devolvidas ao comprador.",
            ephemeral=True
        )
        
        # Notifica comprador
        try:
            buyer = await self.bot.fetch_user(buyer_id)
            await buyer.send(
                f"😔 **{interaction.user.display_name}** recusou seu pedido de call (#{id}).\n"
                f"💰 Suas **{price_paid} SHARK COINS** foram devolvidas!"
            )
        except:
            pass
    
    @app_commands.command(name="compras", description="Ver seu histórico de compras")
    async def compras(self, interaction: discord.Interaction):
        """Lista o histórico de compras do usuário"""
        await interaction.response.defer(ephemeral=True)
        
        purchases = ShopQueries.get_user_purchases(interaction.user.id, limit=10)
        
        if not purchases:
            await interaction.followup.send(
                "📭 Você ainda não fez nenhuma compra!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🛒 Seu Histórico de Compras",
            description=f"Mostrando as últimas **{len(purchases)}** compras.",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        for purchase in purchases:
            item_id = purchase.get('item_id', 'unknown')
            item = config.SHOP_ITEMS.get(item_id, {'name': item_id, 'emoji': '📦'})
            status_key = purchase.get('status', 'pending')
            status = config.CALL_STATUS.get(status_key, {'emoji': '❓', 'name': status_key})
            price = purchase.get('price_paid', 0)
            created = purchase.get('created_at', '')[:10]
            target_id = purchase.get('target_id')
            scheduled_at = purchase.get('scheduled_at')
            
            target_text = f" → <@{target_id}>" if target_id else ""
            schedule_text = ""
            if scheduled_at:
                try:
                    sched_dt = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
                    schedule_text = f"\n📅 Agendado: {sched_dt.strftime('%d/%m/%Y %H:%M')}"
                except:
                    pass
            
            embed.add_field(
                name=f"{item['emoji']} {item['name']}",
                value=f"{status['emoji']} {status['name']}{target_text}{schedule_text}\n"
                      f"💰 {price:,} coins | 📅 {created}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="admin-test-report", description="[ADMIN] Testar envio de report de call no canal fixo")
    async def admin_test_report(self, interaction: discord.Interaction):
        """Teste de envio para o canal de reports"""
        from database.queries import UserQueries
        # Verifica admin rapido
        user_data = UserQueries.get_user(interaction.user.id)
        if not user_data or not user_data.get('is_admin'):
            await interaction.response.send_message("❌ Apenas admins.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        channel_id = config.CHANNEL_IDS.get("calls_marcadas")
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(channel_id)
            
            if not channel:
                await interaction.followup.send(f"❌ Canal ID {channel_id} não encontrado!", ephemeral=True)
                return
                
            await channel.send(f"🧪 Teste de relatório de call. Canal correto: {channel.name} ({channel.id})")
            await interaction.followup.send(f"✅ Mensagem enviada para {channel.mention}", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao testar canal: {e}", ephemeral=True)
    
    @app_commands.command(name="calls", description="Ver suas calls agendadas")
    async def calls(self, interaction: discord.Interaction):
        """Lista calls agendadas do usuário"""
        await interaction.response.defer(ephemeral=True)
        
        # Busca calls onde o usuário é comprador ou alvo
        scheduled = ShopQueries.get_scheduled_calls_for_user(interaction.user.id)
        
        if not scheduled:
            await interaction.followup.send(
                "📭 Você não tem calls agendadas!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📅 Suas Calls Agendadas",
            description=f"Você tem **{len(scheduled)}** call(s) agendada(s).",
            color=config.EMBED_COLOR_PRIMARY
        )
        
        for call in scheduled[:10]:
            purchase_id = call.get('id')
            buyer_id = call.get('buyer_id')
            target_id = call.get('target_id')
            scheduled_at = call.get('scheduled_at')
            channel_id = call.get('channel_id')
            
            # Determina quem é a outra pessoa
            other_id = target_id if buyer_id == interaction.user.id else buyer_id
            
            schedule_str = "Não definido"
            if scheduled_at:
                try:
                    sched_dt = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
                    schedule_str = sched_dt.strftime('%d/%m/%Y às %H:%M')
                except:
                    pass
            
            channel_text = f"<#{channel_id}>" if channel_id else "Não criado"
            
            embed.add_field(
                name=f"📞 Call #{purchase_id}",
                value=f"👤 Com: <@{other_id}>\n"
                      f"📅 {schedule_str}\n"
                      f"🎙️ Canal: {channel_text}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
