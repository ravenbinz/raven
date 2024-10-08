import discord
from discord.ext import commands
import os
import asyncio

# Bot token and channel ID
TOKEN = 'MTI4NDQ4OTMyMjQxODE0NzM0OQ.GJi28s.gvEGMmXiCXBVdcZZHWRxO9eaOCLGFwcF1IAF_U'
CHANNEL_ID = 1276961272495214704  # Your channel ID
ROLE_ID = 1287843226002128926     # Role that can use the !search command

# Define your bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Cooldown dictionary for !rgen command (per user)
gen_cooldown = {}
# Global account generation count
global_generation_count = 0

# Check and remove accounts from a service file
def get_account(service):
    file_path = f"{service}.txt"
    try:
        with open(file_path, "r") as file:
            accounts = file.readlines()

        if accounts:
            account = accounts[0].strip()  # Get the first account
            # Remove the account from the file
            with open(file_path, "w") as file:
                file.writelines(accounts[1:])
            return account
        else:
            return None
    except FileNotFoundError:
        return None

# Command to generate accounts
@bot.command(name="rgen")
@commands.cooldown(1, 25, commands.BucketType.user)  # 25 seconds cooldown for !rgen command
async def generate_account(ctx, service: str):
    global global_generation_count

    if ctx.channel.id == CHANNEL_ID:
        # Cooldown check
        if ctx.author.id in gen_cooldown and gen_cooldown[ctx.author.id] > asyncio.get_event_loop().time():
            remaining_time = int(gen_cooldown[ctx.author.id] - asyncio.get_event_loop().time())
            cooldown_embed = discord.Embed(
                title="⏳ Cooldown",
                description=f"You are on cooldown. Please wait **{remaining_time} seconds** before generating another account.",
                color=discord.Color.red()
            )
            await ctx.send(embed=cooldown_embed)
            return

        # Get an account from the file
        account = get_account(service)

        if account:
            global_generation_count += 1  # Increment the global generation count
            gen_cooldown[ctx.author.id] = asyncio.get_event_loop().time() + 25  # Set user cooldown for 25 seconds

            # DM the user with the account
            await ctx.author.send(f"Here's your **{service}** account:\n`{account}`")

            # Send embed to the channel
            embed = discord.Embed(
                title="🎉 Success!",
                description=f"Successfully generated a **{service}** account, check your DMs!",
                color=discord.Color.green()
            )
            embed.add_field(name="🌍 **Global Generations:**", value=str(global_generation_count), inline=False)
            embed.add_field(name="🔓 **User Generations:**", value="1", inline=False)  # Can be expanded for user-specific counts
            await ctx.send(embed=embed)
        else:
            # No accounts available
            no_acc_embed = discord.Embed(
                title="❌ No Accounts",
                description=f"Sorry, no accounts are available for **{service}**.",
                color=discord.Color.red()
            )
            await ctx.send(embed=no_acc_embed)

    else:
        wrong_channel_embed = discord.Embed(
            title="⚠️ Command Restricted",
            description="This command can only be used in the specified channel.",
            color=discord.Color.red()
        )
        await ctx.send(embed=wrong_channel_embed)

# Function to search for accounts in search.txt based on domain
def search_accounts(domain):
    file_path = "search.txt"
    try:
        with open(file_path, "r") as file:
            accounts = file.readlines()

        # Filter accounts that contain the domain
        matching_accounts = [acc for acc in accounts if domain in acc]

        if len(matching_accounts) >= 50:
            # Get the first 50 matching accounts
            result_accounts = matching_accounts[:50]

            # Remove those accounts from the file
            with open(file_path, "w") as file:
                remaining_accounts = [acc for acc in accounts if acc not in result_accounts]
                file.writelines(remaining_accounts)

            # Save the found accounts to a new file
            output_file_path = f"{domain}_accounts.txt"
            with open(output_file_path, "w") as output_file:
                output_file.writelines(result_accounts)

            return output_file_path
        else:
            return None
    except FileNotFoundError:
        return None

# Command to search for accounts by domain (restricted to users with a specific role)
@bot.command(name="search")
@commands.has_role(ROLE_ID)  # Only users with this role can use the command
@commands.cooldown(1, 20, commands.BucketType.user)  # 20 seconds cooldown for search command
async def search_domain(ctx, domain: str):
    if ctx.channel.id == CHANNEL_ID:  # Check if the command is used in the right channel
        searching_embed = discord.Embed(
            title="🔍 Searching...",
            description=f"Searching for **{domain}** accounts. Please wait...",
            color=discord.Color.orange()
        )
        await ctx.send(embed=searching_embed)

        # Search for accounts containing the domain
        file_path = search_accounts(domain)

        if file_path:
            # Send the found accounts as a file to the user
            await ctx.author.send(f"Here are your **{domain}** accounts:", file=discord.File(file_path))

            success_embed = discord.Embed(
                title="💫 Search Complete!",
                description=f"Check your DMs for the **{domain}** accounts!",
                color=discord.Color.green()
            )
            await ctx.send(embed=success_embed)

            # Optionally, delete the file after sending
            os.remove(file_path)
        else:
            no_results_embed = discord.Embed(
                title="❌ No Accounts Found",
                description=f"Sorry, no accounts were found for **{domain}**, or there are fewer than 50 accounts.",
                color=discord.Color.red()
            )
            await ctx.send(embed=no_results_embed)
    else:
        wrong_channel_embed = discord.Embed(
            title="⚠️ Command Restricted",
            description="This command can only be used in the specified channel.",
            color=discord.Color.red()
        )
        await ctx.send(embed=wrong_channel_embed)

# Command to check the bot's ping
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)  # Convert latency to milliseconds
    ping_embed = discord.Embed(
        title="🏓 Pong!",
        description=f"BOT'S PING IS `{latency} MS`",
        color=discord.Color.green()
    )
    await ctx.send(embed=ping_embed)

# Command to show stock for all services
@bot.command(name="rstock")
async def stock(ctx):
    services = ["steam", "netflix", "crunchyroll", "hotmail", "disney"]
    stock_embed = discord.Embed(
        title="📦 Account Stock",
        color=discord.Color.blue()
    )

    for service in services:
        try:
            with open(f"{service}.txt", "r") as file:
                stock_count = len(file.readlines())
        except FileNotFoundError:
            stock_count = 0

        stock_embed.add_field(name=f"🔸 {service.capitalize()}:", value=f"{stock_count} accounts", inline=False)

    await ctx.send(embed=stock_embed)

# Error handler for command cooldowns
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Please wait {int(error.retry_after)} seconds before using the command again.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You don't have permission to use this command.")

# Run the bot
bot.run(TOKEN)
