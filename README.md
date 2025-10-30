# Tamari

Tamari is a fully-featured recipe manager web application built using Python and the Flask Framework. 

![GitHub repo size](https://img.shields.io/github/repo-size/alexbates/Tamari?style=plastic)
![GitHub language count](https://img.shields.io/github/languages/count/alexbates/Tamari?style=plastic)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) 
![GitHub last commit](https://img.shields.io/github/last-commit/alexbates/Tamari?color=red&style=plastic)

![Tamari Screenshot](https://tamariapp.com/images/tamari-cover-photo-copy.png)

## Live Demo and Public Instance

Try it out at https://app.tamariapp.com

Create your own account or sign in with the demo credentials.

## Features
- **Create User Accounts.** Login with an email and password. If enabled, easily reset forgotten passwords via email.
- **Store, View, Search, and Share Recipes.** For a single recipe, you can save a title, category, description, time estimates, servings, URL, nutrition info, ingredients, instructions, and a photo. If no photo is uploaded, a random cooking-themed placeholder is assigned. Mark off completed ingredients on the recipe detail page for seamless cooking. Quickly find recipes with real-time "search-as-you-type" functionality. Recipes are only visible while logged in by default, however you can make a recipe public and share the URL with anyone.
- **Organize.** Mark recipes as Favorites for quick access. Categorize recipes and browse by category.
- **Explore.** Browse and search a collection of over 107,000 recipes from 50 recipe sharing websites. Import a recipe into "My Recipes" with one click.
- **Create Shopping Lists.** Organize shopping lists for each store. Add all ingredients from a recipe to a shopping list with one click. Check off items as you shop. Scan barcodes to add list items.
- **Plan Meals.** Plan your meals for the week using the Meal Planner. Assign recipes to specific dates up to 30 days in advance.
- **Customize.** Choose to display large photos to show off your recipes to friends, or smaller photos to fit more recipes on the screen. Sort recipes by title or date added. Switch between light and dark themes. Pick from four profile pictures and customize your account's accent color. Configure instance-wide settings like recipes per page or dynamic image loading.
- **REST API.** Access a comprehensive API to manage recipes, shopping lists, and meal plans programmatically.
- **Access on any Device.** Enjoy a seamless experience on desktops, laptops, tablets, and smartphones.

## Installing with Docker 🐳
This creates a 'tamariappdata' volume for persistent storage.
```
docker run -d --restart=always -p 4888:4888 -v tamariappdata:/app/appdata --name tamari alexbates/tamari:1.4
```
You can also pull ghcr.io/alexbates/tamari:latest or alexbates/tamari:latest.

Tamari is now running! Go to http://localhost:4888

### Alternative Command with Mail Settings
Use this command instead if you wish to enable password reset requests via email. Replace variables with settings for an email account you control.
```
docker run -d -e MAIL_SERVER=mail.example.com -e MAIL_PORT=587 -e MAIL_USE_TLS=1 -e MAIL_USERNAME=youremail@example.com -e MAIL_PASSWORD=yourpassword --restart=always -p 4888:4888 -v tamariappdata:/app/appdata --name tamari alexbates/tamari:1.4
```

## Manual Installation

### Instructions for Debian 12 and Ubuntu 24.10
This uses a virtual environment to ensure that dependencies don't interfere with other software on your system.
```
sudo apt install python3 python3-venv git
sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev libpangocairo-1.0-0
git clone https://github.com/alexbates/Tamari
cd Tamari
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db init
flask db migrate -m "Initial"
flask db upgrade
export FLASK_APP=tamari.py
gunicorn -b 0.0.0.0:4888 -w 4 app:app
```
Tamari is now running! Go to http://localhost:4888

## Documentation
For more information regarding usage, installation, and upgrading, check out the documentation at https://tamariapp.com/docs/

## Backups
Please make backups of your data to prevent data loss. Details about the location of user data can be found at https://tamariapp.com/docs/backups/

## Contribute
Have ideas for new features, improvements, or found a bug? Feel free to open an issue! I am looking for ways to improve the app, and your feedback is appreciated.

![Mobile Screenshots](https://tamariapp.com/images/mobile-screenshots.png)