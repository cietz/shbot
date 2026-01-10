
import discord
import os
from dotenv import load_dotenv
import asyncio
import config

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

class ChannelChecker(discord.Client):
    async def on_ready(self):
        print(f'Logado como {self.user} (ID: {self.user.id})')
        print('--- Verificando Canais ---')
        
        for name, channel_id in config.CHANNEL_IDS.items():
            channel = self.get_channel(channel_id)
            if channel:
                print(f"✅ Canal '{name}' encontrado: {channel.name} (ID: {channel.id})")
                permissions = channel.permissions_for(channel.guild.me)
                if permissions.send_messages and permissions.view_channel:
                     print(f"   - Permissões OK: Ler e Enviar")
                else:
                     print(f"   ❌ SEM PERMISSÃO DE ENVIAR/LER!")
            else:
                print(f"❌ Canal '{name}' NÃO ENCONTRADO (ID: {channel_id})")
        
        print('--- Fim da Verificação ---')
        await self.close()

intents = discord.Intents.default()
client = ChannelChecker(intents=intents)
client.run(TOKEN)
