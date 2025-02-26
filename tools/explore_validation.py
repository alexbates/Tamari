# This script validates the URLs found in Explore text files.
# The purpose is to ensure that parsing of ingredients and instructions is successful
# for every URL.
# To use, place explore-all-randomized.txt in same directory as this python script.

import requests, cloudscraper
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time

# List of WPRM sites
wprm_sites = [
    "wellplated.com", "fedandfit.com", "damndelicious.net", "recipetineats.com", "skinnytaste.com",
    "therecipecritic.com", "spendwithpennies.com", "bellyfull.net", "iheartnaptime.net", "daringgourmet.com",
    "lifemadesweeter.com", "iambaker.net", "tastesoflizzyt.com", "thebestblogrecipes.com",
    "favfamilyrecipes.com", "feelgoodfoodie.net", "vegrecipesofindia.com", "theseasonedmom.com",
    "keviniscooking.com", "isabeleats.com", "bakerbynature.com", "minimalistbaker.com",
    "dinneratthezoo.com", "lecremedelacrumb.com", "gonnawantseconds.com", "lilluna.com", "joyfoodsunshine.com",
    "paleorunningmomma.com", "themediterraneandish.com", "deliciousasitlooks.com", "thestayathomechef.com",
    "barefeetinthekitchen.com", "addapinch.com", "thecafesucrefarine.com", "iamhomesteader.com",
    "handletheheat.com", "sipandfeast.com", "askchefdennis.com", "noracooks.com", "greedygirlgourmet.com",
    "thereciperebel.com"
]

# Site-specific parsing logic
def parse_recipe(url, retries=0):
    headers = {
        'User-Agent': UserAgent().random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    for attempt in range(retries + 1):
        try:
            # Fetch the page
            print(f"Fetching {url} (Attempt {attempt + 1}/{retries + 1})...")
            ingredients, instructions = [], []
            if "cookinglsl.com" in url or "lanascooking.com" in url:
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = get_wprm_ingredients(soup)
                instructions = get_wprm_instructions(soup)
            elif "justapinch.com" in url:
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = []
                ingredients_1 = soup.find('ul', {'id': 'recipe-ingredients-list'})
                if ingredients_1:
                    ingredients_2 = soup.find_all('li',class_='x-checkable')
                    for ingredient in ingredients_2:
                        ing_amount_1 = ingredient.find('div',class_='text-blue-ribbon text-wrap text-right font-weight-bold mr-2')
                        ing_amount = ing_amount_1.text
                        ing_amount = ing_amount.strip()
                        ing_item_1 = ingredient.find('div',class_='ml-1')
                        ing_item = ing_item_1.text
                        ingred = ing_amount + ' ' + ing_item
                        ingred = ingred.strip()
                        ingredients.append(ingred)
                instructions = []
                instructions_1 = soup.find('ul', {'id': 'recipe-preparation'})
                if instructions_1:
                    instructions_2 = soup.find_all('div',class_='card-body p-0 py-1')
                    for instruction in instructions_2:
                        instr_1 = instruction.find('div',class_='flex-fill recipe-direction rcp-ugc-block')
                        instr = instr_1.text
                        instr = instr.strip()
                        instructions.append(instr)
            elif "pinchofyum.com" in url:
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = []
                ingredients_1 = soup.find_all('li',attrs={'data-tr-ingredient-checkbox': True})
                if ingredients_1:
                    for ingredient in ingredients_1:
                        ingred = ingredient.text
                        ingred = ingred.strip()
                        ingredients.append(ingred)
                instructions = []
                instructions_1 = soup.find('div',class_='tasty-recipes-instructions')
                if instructions_1:
                    instructions_2 = instructions_1.find_all('li')
                    for instruction in instructions_2:
                        instr = instruction.text
                        instr = instr.strip()
                        instructions.append(instr)
            elif "tasty.co" in url:
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = []
                ingredients_1 = soup.find('div',class_='ingredients__section')
                if ingredients_1:
                    ingredients_2 = ingredients_1.find_all('li',class_='ingredient')
                    for ingredient in ingredients_2:
                        ingred = ingredient.text
                        ingred = ingred.strip()
                        ingredients.append(ingred)
                instructions = []
                instructions_1 = soup.find('ol',class_='prep-steps')
                if instructions_1:
                    instructions_2 = instructions_1.find_all('li')
                    for instruction in instructions_2:
                        instr = instruction.text
                        instr = instr.strip()
                        instructions.append(instr)
            elif "food52.com" in url:
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = []
                ingredients_1 = soup.find('div',class_='recipe__list--ingredients')
                if ingredients_1:
                    ingredients_2 = ingredients_1.find_all('li')
                    for ingredient in ingredients_2:
                        ingred = ingredient.text
                        ingred = ingred.replace('\n\n', ' ').replace('\n', ' ')
                        ingred = ingred.strip()
                        ingredients.append(ingred)
                instructions = []
                instructions_1 = soup.find('div',class_='recipe__list--steps')
                if instructions_1:
                    instructions_2 = instructions_1.find_all('li',class_='recipe__list-step')
                    for instruction in instructions_2:
                        instr = instruction.text
                        instr = instr.strip()
                        instructions.append(instr)
            elif "tasteofhome.com" in url:
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = []
                ingredients_1 = soup.find('ul',class_='recipe-ingredients__list')
                if ingredients_1:
                    ingredients_2 = ingredients_1.find_all('li')
                    for ingredient in ingredients_2:
                        ingred = ingredient.text
                        ingred = ingred.strip()
                        ingredients.append(ingred)
                instructions = []
                instructions_1 = soup.find('ol',class_='recipe-directions__list')
                if instructions_1:
                    instructions_2 = instructions_1.find_all('li')
                    for instruction in instructions_2:
                        instr = instruction.text
                        instr = instr.strip()
                        instructions.append(instr)
            elif "taste.com.au" in url:
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = []
                ingredients_1 = soup.find('div',class_='recipe-ingredients-section')
                if ingredients_1:
                    ingredients_2 = ingredients_1.find_all('div',class_='ingredient-description')
                    for ingredient in ingredients_2:
                        ingred = ingredient.text
                        ingred = ingred.strip()
                        ingredients.append(ingred)
                instructions = []
                instructions_1 = soup.find('ul',class_='recipe-method-steps')
                if instructions_1:
                    instructions_2 = instructions_1.find_all('div',class_='recipe-method-step-content')
                    for instruction in instructions_2:
                        instr = instruction.text
                        instr = instr.strip()
                        instructions.append(instr)
            elif "easypeasyfoodie.com" in url:
                scraper = cloudscraper.create_scraper()
                page = scraper.get(url, timeout=16)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                instructions = []
                # Find the main container for instructions
                instructions_container = soup.find('div', class_='wprm-recipe-instructions-container')
                if instructions_container:
                    # Find all instruction groups within the container
                    instruction_groups = instructions_container.find_all('div', class_='wprm-recipe-instruction-group')
                    
                    for group in instruction_groups:
                        # Find all instruction list items within the group
                        instruction_steps = group.find_all('li', class_='wprm-recipe-instruction')
                        
                        for step in instruction_steps:
                            # Extract the instruction text
                            instruction_text = step.find('div', class_='wprm-recipe-instruction-text')
                            
                            if instruction_text:
                                # If there are nested <span> tags, extract their text
                                span = instruction_text.find('span')
                                if span:
                                    instructions.append(span.text.strip())
                                else:
                                    instructions.append(instruction_text.text.strip())
            elif "damndelicious.net" in url:
                scraper = cloudscraper.create_scraper()
                page = scraper.get(url, timeout=16)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = get_wprm_ingredients(soup)
                instructions = get_wprm_instructions(soup)
            elif any(link in url for link in wprm_sites):
                page = requests.get(url, timeout=16, headers=headers)
                # UNCOMMENT FOR DEBUGGING
                #print("PAGE: " + page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                ingredients = get_wprm_ingredients(soup)
                instructions = get_wprm_instructions(soup)
            else:
                ingredients, instructions = [], []
                
                
            # If both ingredients and instructions are found, return them
            if ingredients and instructions:
                return ingredients, instructions
                
        except Exception as e:
            print(f"Error fetching URL: {url}, Error: {e}")

        # Delay between retries
        if attempt < retries:
            delay = 10 + (5 * attempt)  # 10 seconds for the first retry, 15 for the second
            print(f"Retrying after {delay} seconds...")
            time.sleep(delay)

    # Return empty lists if parsing fails
    return [], []

# Helper functions for parsing
def get_wprm_ingredients(soup):
    ingredients = []
    ingredients_1 = soup.find('div', class_='wprm-recipe-ingredients-container')
    if ingredients_1:
        ingredients_2 = ingredients_1.find_all('li', class_='wprm-recipe-ingredient')
        for ingredient in ingredients_2:
            ingred = ingredient.text.replace("\n", " ").replace("▢", "").strip()
            ingredients.append(ingred)
    return ingredients

def get_wprm_instructions(soup):
    instructions = []
    instructions_1 = soup.find('div', class_='wprm-recipe-instructions-container')
    if instructions_1:
        instructions_2 = instructions_1.find_all('div', class_='wprm-recipe-instruction-group')
        for group in instructions_2:
            instructions_h4 = group.find('li')
            if instructions_h4:
                content = str(instructions_h4.contents[0]).replace("<strong>", "").replace("</strong>", "")
                instructions.append(content.strip())
            inst_steps = group.find_all('div', class_='wprm-recipe-instruction-text')
            inst_steps_2 = inst_steps.find('span')
            for step in inst_steps_2:
                instructions.append(step.text.strip())
    return instructions

# Main function to process the file
def process_file(input_file, valid_file, invalid_file):
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(valid_file, "w", encoding="utf-8") as valid_out, \
         open(invalid_file, "w", encoding="utf-8") as invalid_out:

        for line_number, line in enumerate(infile, 1):
            try:
                parts = line.strip().split(";")
                if len(parts) < 3:  # Ensure URL, title, and image are present
                    invalid_out.write(line)
                    continue

                url, title, image = parts[0], parts[1], parts[2]
            
                # Add delay before processing each URL
                time.sleep(3)
                ingredients, instructions = parse_recipe(url)
                # UNCOMMENT FOR DEBUGGING
                #print("Ingredients: " + str(ingredients))
                #print("Instructions: " + str(instructions))
                if ingredients and instructions:
                    valid_out.write(line)  # Write valid line as is
                else:
                    invalid_out.write(line)  # Write invalid line as is
            except Exception as e:
                invalid_out.write(line)
                print(f"Error processing line {line_number}: {e}")

# File paths
input_file = "explore-all-randomized-v1.0.txt"
valid_file = "valid.txt"
invalid_file = "invalid.txt"

# Process the file
process_file(input_file, valid_file, invalid_file)
