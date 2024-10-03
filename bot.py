import os
os.system("my-venv/bin/pip install nextcord setuptools googletrans==4.0.0-rc1 pycountry")
import nextcord
from nextcord.ext import commands
import re
from googletrans import Translator
import pycountry

# Load profanity list from a text file
def load_profanity_list(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"Failed to load profanity list: {str(e)}")
        return []

# Load the profanity list
profanity_list = load_profanity_list('swears.txt')

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

def contains_profanity(text):
    """ Check if the input text contains any profane words. """
    for word in profanity_list:
        if word.lower() in text.lower():
            return True
    return False

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

def get_language_code(language_name):
    """ Convert full language name to ISO code or return it if already an ISO code. """
    if len(language_name) == 2:  # Check if it's an ISO code
        return language_name.upper()  # ISO codes are uppercase
    try:
        # Search for the language by name
        lang = pycountry.languages.lookup(language_name)
        return lang.alpha_2
    except LookupError:
        return None

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.slash_command(name='texttomorse', description='Convert text to morse code')
async def text_to_morse_command(interaction: nextcord.Interaction, text: str):
    if contains_profanity(text):
        await interaction.response.send_message("Your input contains inappropriate language.", ephemeral=True)
        return
    
    morse_output = text_to_morse(text)
    await interaction.response.send_message(f'Morse Code: {morse_output}')

@bot.slash_command(name='morsetotext', description='Convert morse code to text')
async def morse_to_text_command(interaction: nextcord.Interaction, morse_code: str):
    if contains_profanity(morse_code):
        await interaction.response.send_message("Your input contains inappropriate language.", ephemeral=True)
        return
    
    text_output = morse_to_text(morse_code)
    await interaction.response.send_message(f'Text: {text_output}')

def translate_text(text, target_language):
    translators = [
        GoogleTranslator(source='auto', target=target_language),
        LibreTranslator(source='auto', target=target_language)
    ]

    for translator in translators:
        try:
            translation = translator.translate(text)
            return translation.text
        except Exception as e:
            print(f"Translation failed with {translator.__class__.__name__}: {str(e)}")

    raise ValueError("All translators failed")

@bot.slash_command(name='translate', description='Translate text to another language')
async def translate_command(interaction: nextcord.Interaction, text: str, target_language: str):
    if contains_profanity(text):
        await interaction.response.send_message("Your input contains inappropriate language.", ephemeral=True)
        return
    
    try:
        lang_code = get_language_code(target_language)
        
        if lang_code is None:
            raise ValueError("Invalid target language specified.")

        # Translate the text
        translated_text = translate_text(text, lang_code)
        await interaction.followup.send(f"Translated: `{translated_text}`")
    except ValueError as ve:
        await interaction.followup.send(f"Translation failed: {str(ve)}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred during translation: {str(e)}", ephemeral=True)


bot.run("haha, think im actually gonna post the token again like I've totally not accidentally done quite a few times... well not this time lol")
