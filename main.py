import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import aiohttp
import asyncio
from collections import deque
import logging
import time

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
ERROR_CHANNEL_ID = int(os.getenv("ERROR_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

request_queues = {}
server_requests = {}
processing_locks = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

async def get_api_link(content, type_):
    base_url = "http://hnode1.roverdev.xyz:27375/api/addlink"
    return f"{base_url}?url={content}"

async def process_next_request(guild_id):
    if guild_id not in processing_locks:
        processing_locks[guild_id] = asyncio.Lock()

    async with processing_locks[guild_id]:
        queue = request_queues.get(guild_id, deque())
        if queue:
            user_id, interaction, api_link, start_time = queue.popleft()
            server_requests[guild_id].add(user_id)

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_link) as resp:
                        data = await resp.json()

                bypassed_link = data.get("url") or data.get("result")
                time_taken = round((time.time() - start_time), 2)

                if bypassed_link:
                    embed = discord.Embed(
                        title="✅ | Bypass Successful!",
                        color=0x2ecc71
                    ).set_thumbnail(url=interaction.user.display_avatar.url)

                    embed.add_field(name="🔑 Bypassed Link:", value=f"```diff\n{bypassed_link}\n```", inline=False)
                    embed.add_field(name="⏱️ Time Taken:", value=f"```yaml\n{time_taken} seconds\n```", inline=True)
                    embed.add_field(name="📝 Requested by:", value=f"```yaml\n{interaction.user}\n```", inline=True)

                    log_channel = bot.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        await log_channel.send(embed=embed)

                else:
                    embed = discord.Embed(
                        title="❌ | Bypass Failed",
                        description="```diff\n- Unable to process.\n```",
                        color=0xff0000
                    )

                await interaction.followup.send(embed=embed, ephemeral=True)

            except Exception as e:
                logger.error(f"❌ Error: {e}")
                embed = discord.Embed(
                    title="❌ Error",
                    description="```API is down, please try again later.```",
                    color=0xff0000
                )
                err_chan = bot.get_channel(ERROR_CHANNEL_ID)
                if err_chan:
                    await err_chan.send(embed=embed)
                await interaction.followup.send(embed=embed, ephemeral=True)

            finally:
                server_requests[guild_id].remove(user_id)
                if queue:
                    await process_next_request(guild_id)

class LinkModal(discord.ui.Modal, title="Enter Your Link"):
    def __init__(self, type_):
        super().__init__(timeout=None)
        self.type_ = type_
        self.link_input = discord.ui.TextInput(
            label="Enter your link here",
            placeholder=f"Enter your {type_} link",
            custom_id="linkInput",
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.link_input)

    async def on_submit(self, interaction: discord.Interaction):
        link = self.link_input.value
        api_link = await get_api_link(link, self.type_)

        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild_id
        user_id = interaction.user.id

        if guild_id not in request_queues:
            request_queues[guild_id] = deque()
        if guild_id not in server_requests:
            server_requests[guild_id] = set()

        request_queues[guild_id].append((user_id, interaction, api_link, time.time()))
        if len(server_requests[guild_id]) == 0:
            await process_next_request(guild_id)

class ButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        buttons = [
            ("linkvertise", "Linkvertise", "<:Linkvertise:1266787483169849365>"),
            ("workink", "Work.ink", "<:Workink:1284411465872441426>"),
            ("fluxus", "Fluxus", "<:Fluxus:1273680261283971205>"),
            ("social_unlock", "SocialUnlock", "🔓"),
            ("lootlinks", "LootLinks", "🎮"),
            ("rekonise", "Rekonise", "<:evilBwaa:1267141351015977100>"),
            ("mediafire", "MediaFire", "<:mediafire1:1289437115230322729>"),
            ("boostink", "Boost.ink", "🚀"),
            ("pastebin", "Pastebin", "<:Pastebin:1289435860223262812>"),
            ("delta", "Delta", "<:Delta:1273669791093231697>"),
            ("codex", "Codex", "<:Codex:1273713250223259813>"),
            ("pastedrop", "PasteDrop", "<:hu0gwUZY_400x400:1289436319440699412>"),
            ("sub2unlock", "Sub2unlock", "<:Screenshot20240927025411:1288951814007554119>"),
            ("mboost", "MBoost", "⚡"),
            ("tinyurl", "TinyURL", "🔗"),
        ]
        for custom_id, label, emoji in buttons:
            self.add_item(ButtonHandler(custom_id, label, emoji))

class ButtonHandler(discord.ui.Button):
    def __init__(self, custom_id, label, emoji):
        super().__init__(label=label, custom_id=custom_id, emoji=emoji, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LinkModal(self.custom_id))

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="AA", url="https://www.twitch.tv/4levy_z1"))
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        logger.error(f"Sync error: {e}")
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.tree.command(name="setbypass", description="Send a bypass Embed ;>")
@app_commands.checks.has_permissions(administrator=True)
async def setbypass(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ | __Bypass Menu__",
        description="```Free Bypass\n\nSlow Update```",
        color=0xffffff
    )
    embed.set_image(url="https://media2.giphy.com/media/12wkaD1nh3XsFG/giphy.gif")
    await interaction.response.send_message(embed=embed, view=ButtonView())

bot.run(TOKEN)
