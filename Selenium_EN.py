from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import time
import asyncio
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

options = Options()
options.add_argument("--headless")          
options.add_argument("--disable-gpu")       
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

def speech_tab():
    driver.switch_to.new_window()
    driver.get("https://huggingface.co/spaces/Plachta/VITS-Umamusume-voice-synthesizer")
    time.sleep(5)
    driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
    time.sleep(0.3)
    character_box = driver.find_element(By.CSS_SELECTOR, 'input[aria-label="character"]')
    character_box.clear()
    character_box.send_keys("Rice Shower")
    
    character_box.send_keys(Keys.RETURN)
    

def OpenTabs():
    
    driver.get("http://127.0.0.1:7860/")
    chat_setting = driver.find_element(By.CSS_SELECTOR, "label[class='svelte-1mhtq7j selected']")
    chat_setting.click()
    driver.switch_to.new_window()
    driver.get("https://kanjikana.com/en/tools/translator/en/ja")
    driver.switch_to.new_window()
    driver.get('https://www.romajidesu.com/translator')
    speech_tab()


    
def Chat(name, prompt):
    
    web_ui = driver.window_handles[0]
    driver.switch_to.window(web_ui)
    input_box = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder='Send a message']")
    input_box.send_keys(f'{name}: {prompt}')
    input_box.send_keys(Keys.RETURN)
    time.sleep(5)

    
    asyncio.run_coroutine_threadsafe(Translate(), bot.loop)

async def Translate():
    elements = driver.find_elements(By.CSS_SELECTOR, ".message[data-raw]")
    latest = elements[-1]
    message_bot = latest.get_attribute("data-raw")
    print(message_bot)

    japanese = driver.window_handles[1]
    romanji = driver.window_handles[2]

    driver.switch_to.window(japanese)
    jp_text_box = driver.find_element(By.CSS_SELECTOR, "#input")
    jp_text_box.clear()
    jp_text_box.send_keys(message_bot)
    jp_translate_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    jp_translate_button.click()
    await asyncio.sleep(5)

    japanese_box = driver.find_elements(By.CSS_SELECTOR, "div[data-furigana='false']")
    print("")

    japanese_text_list = [el.text for el in japanese_box if el.text.strip()]
    japanese_text = "".join(japanese_text_list)
    print(japanese_text)


    driver.switch_to.window(romanji)
    romanji_text_box = driver.find_element(By.CSS_SELECTOR, "#japanese_input")
    romanji_text_box.clear()
    romanji_text_box.send_keys(japanese_text)
    romanji_translate_button = driver.find_element(By.CSS_SELECTOR, "input[value='Translate Now']")
    romanji_translate_button.click()
    spans = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#res_romaji span"))
    )

    
    romanji_tokens = [span.text.strip() for span in spans if span.text.strip()]
    romanji_line = " ".join(romanji_tokens)
    
    

    if romanji_line.strip():
        await send_to_discord(romanji_line, message_bot)
    else:
        print("No romanji output yet, skipping send_to_discord")
    romanji_text_box = driver.find_element(By.CSS_SELECTOR, "#japanese_input")
    romanji_text_box.clear()
    time.sleep(0.2)

    romanji_translate_button = driver.find_element(By.CSS_SELECTOR, "input[value='Translate Now']")
    romanji_translate_button.click()
    driver.refresh()

    await speech(japanese_text)



async def speech(japanese_text):
    Speech_tab = driver.window_handles[-1]
    driver.switch_to.window(Speech_tab)
    driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
    text_box = driver.find_element(By.CSS_SELECTOR, 'textarea[data-testid="textbox"]')
    text_box.clear()
    
    text_box.send_keys(japanese_text)
    
    generate_btn = driver.find_element(By.CSS_SELECTOR, "#component-24")
    generate_btn.click()
    wait = WebDriverWait(driver, 20)
    play_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.play-pause-button")))
    time.sleep(1.5)
    play_btn.click()
    time.sleep(15)
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    speech_tab()



OpenTabs()
driver.switch_to.window(driver.window_handles[0])

dump_channel_id = 1445758792485568525
scrape_channel_id = 1154013995011940365


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log',encoding= 'utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix = '!', intents=intents)

pipeline_lock = asyncio.Lock()

@bot.event
async def on_ready():
    print("We good!")
    bot.loop.create_task(pipeline_loop())

last_processed_id = None

async def pipeline_loop():
    global last_processed_id
    await bot.wait_until_ready()
    channel = bot.get_channel(scrape_channel_id)

    while not bot.is_closed():
        async with pipeline_lock:
            async for msg in channel.history(limit=1):
                latest_msg = msg

            if latest_msg and latest_msg.id != last_processed_id:
                if latest_msg.author != bot.user and latest_msg.author.name != 'Scripty Transcriptions':
                    user_input = latest_msg.content
                    print(f'Pipeline run on latest: {latest_msg.author}: {user_input}')
                    Chat(latest_msg.author, user_input)
                    
                    last_processed_id = latest_msg.id

        
        await asyncio.sleep(2)

async def send_to_discord(romanji_line: str, message_bot: str):


    dump_channel = bot.get_channel(dump_channel_id)

    if dump_channel:
        
        if romanji_line:
            await dump_channel.send(romanji_line)
        
        if message_bot:
            await dump_channel.send(message_bot)

bot.run(token, log_handler = handler , log_level = logging.DEBUG)



