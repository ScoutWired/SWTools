import os
import nextcord
from nextcord import Intents
from nextcord.ext import commands
import requests
import chat_exporter
import io
import json
from nextcord.ext import application_checks
from translate import Translator


class ClientSettings(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_views_added = False

    async def on_ready(self):
        if not self.persistent_views_added:
            self.add_view(CreateTicket(client))
            self.add_view(TicketSettings())
            self.persistent_views_added = True
        print("Persistent views added")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("  ████████ ██       ██   ██████████   ███████     ███████   ██        ████████")
        print(" ██░░░░░░ ░██      ░██  ░░░░░██░░░   ██░░░░░██   ██░░░░░██ ░██       ██░░░░░░ ")
        print("░██       ░██   █  ░██      ░██     ██     ░░██ ██     ░░██░██      ░██       ")
        print("░█████████░██  ███ ░██      ░██    ░██      ░██░██      ░██░██      ░█████████")
        print("░░░░░░░░██░██ ██░██░██      ░██    ░██      ░██░██      ░██░██      ░░░░░░░░██")
        print("       ░██░████ ░░████      ░██    ░░██     ██ ░░██     ██ ░██             ░██")
        print(" ████████ ░██░   ░░░██      ░██     ░░███████   ░░███████  ░████████ ████████ ")
        print("░░░░░░░░  ░░       ░░       ░░       ░░░░░░░     ░░░░░░░   ░░░░░░░░ ░░░░░░░░")
        print("Version ~ 1.0.0 | Designed, Programmed & Maintained By AlpineVR & SW Tech Team")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(f"Logged in as {self.user} (ID: {self.user.id})")

intents = Intents.all()

with open('config.json') as config_file:
    data = json.load(config_file)

token = data['token']
prefix = data['prefix']
role = data['supportRole']
ticketCategory = data['ticketCategory']
logChannel = data['logChannel']
title = data['title']
desc = data['desc']

client = ClientSettings(command_prefix=prefix, intents=intents)

#-------------------------------------------------------------------COMMANDS-------------------------------------------------------------------

@client.slash_command(description="Generate a transcript for any channel")
async def transcript(interaction: nextcord.Interaction):
    guild = client.get_guild(data["guildId"])
    support_role = nextcord.utils.get(guild.roles, id=data['supportRole'])
    
    if support_role in interaction.user.roles:
        await interaction.response.send_message("Your transcript is now being generated. A link will be sent here once it is finished generating. Depending on the size of the channel transcripts can take up to 3 minutes to generate...")
        channel_handler = chat_exporter.AttachmentToDiscordChannelHandler(
            channel=client.get_channel(data['attachments']),
        )
    
        transcript = await chat_exporter.export(
            interaction.channel,
            bot=client,
            attachment_handler=channel_handler,
        )
    
        if transcript is None:
            return
    
        transcript_file = nextcord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.html",
        )
    
        UPLOAD_FOLDER = "temp"
        file_path = os.path.join(UPLOAD_FOLDER, "temp.html")
    
        with open(file_path, 'wb') as f:
            content = transcript_file.fp.read()
            f.write(content)
        response = requests.post('http://127.0.0.1:4000/uploads', files={'file': open(file_path, 'rb')})
            
        if(response.text is not None):
            code_name = response.text  # Get the code name from the response
            print(response.text)
            await interaction.channel.send(f"Transcript Generated Sucessfully... Complain to alpine if its broken.")
            await interaction.channel.send(f"https://tickets.scoutwired.org/uploads/{response.text}.html")
        else:
            print('File upload failed!')
            await interaction.channel.send(f"Your transcript has been generated sucessfully! Attached is the transcript, To view it download it and then open it using your web browser! Thanks for using the Studio Transcript System!", file=transcript_file)
    else:
        await interaction.response.send_message("You do not have the required permission to perfom this command :(")
        
#-------------------------------------------------------------------TICKET---------------------------------------------------------------
class AddUser(nextcord.ui.Modal):
    def __init__(self, channel):
        super().__init__(
            "Add User To Ticket",
            timeout=300,
        )
        self.channel = channel
        
        self.user = nextcord.ui.TextInput(label="User ID", min_length=2, max_length=30, required=True, placeholder="User ID (NUMBER)")
        self.add_item(self.user)
    async def callback(self, interaction: nextcord.Interaction) -> None:
        user = await interaction.guild.query_members(user_ids=[self.user.value]) # list of members with userid
        user = user[0]
        if user is None:
            return await interaction.send(f"Invalid User ID, Make sure the user is in this guild!")
        overwrite = nextcord.PermissionOverwrite()
        overwrite.read_messages = True
        await self.channel.set_permissions(user, overwrite=overwrite)
        await interaction.send(f"{user.mention} has been added to this ticket.")

class ClaimTicket(nextcord.ui.Modal):
    def __init__(self, channel):
        super().__init__(
            "Claim The Ticket",
            timeout=300,
        )
        self.channel = channel
        self.support_message = nextcord.ui.TextInput(label="Message", min_length=2, max_length=50, required=True, placeholder="Support Welcome Message")
        self.add_item(self.support_message)
    async def callback(self, interaction: nextcord.Interaction) -> None:
        user = interaction.user
        has_staff_role = any(role.name == "Staff" for role in user.roles)
        if has_staff_role:
            await interaction.send(embed=nextcord.Embed(description=f"{user.mention} has claimed this ticket.\nTheir Support Message: \n\n`{self.support_message.value}`"))
        else:
            await interaction.send(f"Sorry, {user.mention}, you need the 'Staff' role to claim this ticket.")
    
class RemoveUser(nextcord.ui.Modal):
    def __init__(self, channel):
        super().__init__(
            "Remove User From Ticket",
            timeout=300,
        )
        self.channel = channel
        self.user = nextcord.ui.TextInput(label="User ID", min_length=2, max_length=30, required=True, placeholder="User ID (NUMBER)")
        self.add_item(self.user)
    async def callback(self, interaction: nextcord.Interaction) -> None:
        user = interaction.guild.get_member(int(self.user.value))
        if user is None:
            return await interaction.send(f"Invalid User ID, Make sure the user is in this guild!")
        overwrite = nextcord.PermissionOverwrite()
        overwrite.read_messages = False
        await self.channel.set_permissions(user, overwrite=overwrite)
        await interaction.send(f"{user.mention} has been removed from this ticket.")

class CreateTicket(nextcord.ui.View):
    def __init__(self, client):
        super().__init__(timeout=None)
        self.client = client

    @nextcord.ui.button(label="Create Ticket", style=nextcord.ButtonStyle.blurple, custom_id="create_ticket:blurple")
    async def create_ticket(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Read the current ticket number from the file
        with open('ticket_counter.txt', 'r') as file:
            ticket_number = int(file.read().strip())
        
        # Increment the ticket number
        ticket_number += 1
        
        # Format the ticket number with leading zeros
        formatted_ticket_number = str(ticket_number).zfill(5)
        
        # Use the formatted ticket number to name the new ticket channel
        channel_name = f"ticket-{formatted_ticket_number}"
        
        # Send an ephemeral message to indicate the ticket creation process
        msg = await interaction.response.send_message("Creating ticket...", ephemeral=True)
        
        user = interaction.user

        if role:
            overwrites = {
                interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True),
                interaction.guild.get_role(role): nextcord.PermissionOverwrite(read_messages=True),
            }
        else:
            overwrites = {
                interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True),
            }
        
        channel = await interaction.guild.create_text_channel(channel_name, overwrites=overwrites, category=interaction.guild.get_channel(ticketCategory))
        
        # Send a follow-up message that can be edited
        await msg.edit(f"Channel sucessfully created! {channel.mention}")
        
        # Save the updated ticket number back to the file
        with open('ticket_counter.txt', 'w') as file:
            file.write(str(ticket_number))
        
        embed = nextcord.Embed(title="Ticket Opened", description=f"{interaction.user.mention} created a ticket! Click one of the buttons below to change the ticket settings!")
        log_channel = interaction.guild.get_channel(logChannel)
        embed2 = nextcord.Embed(title="Ticket Opened", description=f"Ticket Owner: {interaction.user.mention}\nTicket Name: `{channel.name}`\nChannel ID: `{channel.id}`", color=nextcord.Colour.green(), timestamp=nextcord.utils.utcnow())
        await log_channel.send(embed=embed2)
        overwrite = nextcord.PermissionOverwrite()
        overwrite.read_messages = True
        await channel.send(embed=embed, view=TicketSettings())
        await channel.set_permissions(user, overwrite=overwrite)

class TicketSettings(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="Close Ticket", style=nextcord.ButtonStyle.red, custom_id="ticket_settings:red")
    async def close_ticket(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        
        channel_handler = chat_exporter.AttachmentToDiscordChannelHandler(
            channel=client.get_channel(data['attachments']),
        )

        transcript = await chat_exporter.export(
            interaction.channel,
            bot=client,
            attachment_handler=channel_handler,
        )

        if transcript is None:
            return

        transcript_file = nextcord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.html",
        )

        UPLOAD_FOLDER = "temp"
        file_path = os.path.join(UPLOAD_FOLDER, "temp.html")

        with open(file_path, 'wb') as f:
            content = transcript_file.fp.read()
            f.write(content)
        response = requests.post('http://127.0.0.1:4000/uploads', files={'file': open(file_path, 'rb')})

        log_channel = interaction.guild.get_channel(logChannel)

        if(response.text is not None):
            code_name = response.text  # Get the code name from the response
            print(response.text)
            await interaction.response.send_message("Ticket is being closed.", ephemeral=True)
            await interaction.channel.delete()
            embed = nextcord.Embed(title="Ticket Closed", description=f"Ticket Name: `{interaction.channel.name}`\nClosed By: `{interaction.user}`\nTranscript: [Click Here](https://tickets.scoutwired.org/uploads/{response.text}.html)", color=nextcord.Colour.red(), timestamp=nextcord.utils.utcnow())
            await log_channel.send(embed=embed)
        else:
            print('File upload failed!')
            await interaction.response.send_message("Ticket is being closed.", ephemeral=True)
            await interaction.channel.delete()
            await log_channel.send(f"Your ticket has been closed sucessfully! Attached is the transcript, To view it download it and then open it using your web browser!", file=transcript_file)
        

    @nextcord.ui.button(label="Add User", style=nextcord.ButtonStyle.green, custom_id="ticket_settings:green")
    async def add_user(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(AddUser(interaction.channel))
        
    @nextcord.ui.button(label="Claim", style=nextcord.ButtonStyle.blurple, custom_id="ticket_settings:claim")
    async def claim_ticket(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(ClaimTicket(interaction.channel))
        
    @nextcord.ui.button(label="Remove User", style=nextcord.ButtonStyle.grey, custom_id="ticket_settings:grey")
    async def remove_user(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(RemoveUser(interaction.channel))

@client.slash_command()
@application_checks.has_permissions(manage_channels=True)
async def setup(interaction: nextcord.Interaction):
    embed = nextcord.Embed(
        title = title,
        description = desc,
        color=nextcord.Colour(0x0f0f0f)
    )
    await interaction.response.send_message(embed=embed, view=CreateTicket(client))


# Expanded morse code library
morse_code_library = {
    'A': '.-',     'B': '-...',   'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.',   'G': '--.',    'H': '....', 'I': '..',   'J': '.---',
    'K': '-.-',    'L': '.-..',   'M': '--',   'N': '-.',   'O': '---',
    'P': '.--.',   'Q': '--.-',  'R': '.-.',   'S': '...',  'T': '-',
    'U': '..-',    'V': '...-',   'W': '.--',   'X': '-..-',  'Y': '-.--',
    'Z': '--..',   '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....',  '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '0': '-----',  ' ': '/',     ',': '--..--', '.': '.-.-.-', '?': '..--..',
    '!': '-.-.--', '/': '-..-.', '-': '-....-', '(': '-.--.', ')': '-.--.-',
    '&': '.-...',  ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.',
    '_': '..--.',  '"': '.-..-.', '$': '...-..', '@': '.--.-.', '#': '-.-.-.',
    '%': '---...', '^': '.-.--.', '~': '...-',   '<': '.--.-.', '>': '.--.--'
}

def text_to_morse(text):
    morse_output = ""
    for char in text.upper():
        if char in morse_code_library:
            morse_output += morse_code_library[char] + " "
    return morse_output.strip()

def morse_to_text(morse_code):
    reverse_library = {value: key for key, value in morse_code_library.items()}
    words = morse_code.split("  ")
    output = ""
    for word in words:
        letters = word.split()
        for letter in letters:
            if letter != "/":
                output += reverse_library[letter]
        output += " "
    return output.strip()
    
def translate_text(text, target_language):
    try:
        translator = Translator(to_lang=target_language)
        return translator.translate(text)
    except Exception as e:
        return f"Translation failed: {str(e)}"

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.slash_command(name='texttomorse', description='Convert text to morse code')
async def text_to_morse_command(interaction: nextcord.Interaction, text: str):
    morse_output = text_to_morse(text)
    await interaction.response.send_message(f'Morse Code: {morse_output}')

@client.slash_command(name='morsetotext', description='Convert morse code to text')
async def morse_to_text_command(interaction: nextcord.Interaction, morse_code: str):
    text_output = morse_to_text(morse_code)
    await interaction.response.send_message(f'Text: {text_output}')

@client.slash_command(name='translate', description='Translate text to another language')
async def translate_command(interaction: nextcord.Interaction, text: str, target_language: str):
    await interaction.response.defer()
    
    try:
        translated_text = translate_text(text, target_language)
        await interaction.followup.send(f"Translated: `{translated_text}`")
    except Exception as e:
        await interaction.followup.send(f"Translation failed: {str(e)}", ephemeral=True)


client.run(token)