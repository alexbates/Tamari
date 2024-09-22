# Tamari

Tamari is a fully-featured recipe manager web application built using Python and the Flask Framework. 

![GitHub repo size](https://img.shields.io/github/repo-size/alexbates/Tamari?style=plastic)
![GitHub language count](https://img.shields.io/github/languages/count/alexbates/Tamari?style=plastic)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) 
![GitHub last commit](https://img.shields.io/github/last-commit/alexbates/Tamari?color=red&style=plastic)

![Tamari Screenshot](https://bates.gg/mockup-tamari.png)

## Live Demo and Public Instance

Try it out at https://app.tamariapp.com

Create your own account or sign in with the demo credentials.

## Features
- **Create User Accounts.** Login with an email and password. If configured on the instance, account passwords can be reset by sending a reset request to the email associated with your account.
- **Store, View, Search, and Share Recipes.** For a single recipe, you can save a title, category, description, time estimates, servings, URL, ingredients, instructions, and a photo. If you don’t upload a photo, Tamari will assign a random cooking-themed placeholder. On the detail page for a recipe, you can click to cross off completed ingredients and instruction steps while you are cooking. Search-as-you-type functionality enables you to find the recipe you are looking for as quickly as possible. Recipes are only visible while logged in by default, however you can make a recipe public and share the URL with anyone.
- **Organize.** Mark recipes as Favorites for easy access. Assign categories to recipes and browse by category.
- **Explore.** Browse and search a collection of over 109,000 recipes from 50 recipe sharing websites. When you browse a recipe in Explore, Tamari will fetch and parse the relevant data from the URL without requiring you to visit the webpage. Import a recipe into My Recipes with the click of a button.
- **Make Shopping Lists.** Make a shopping list for each store you shop at. Add all ingredients for a specific recipe to a shopping list with the click of a button. Click an item on a shopping list to mark it as completed.
- **Plan Meals.** Use the Meal Planner to keep on top of what you plan to cook for the week. The Schedule button can assign a recipe being viewed to a date up to 30 days in advance.
- **Customize.** Choose to display large photos to show off your recipes to friends, or smaller photos to fit more recipes on the screen. Sort recipes by title or by date added. Use the light or dark theme. Select between four account profile pictures. Set an accent color that applies to most buttons and many elements throughout the app. For a Tamari instance, some configuration options can be customized such as recipes per page and dynamic loading of images.
- **Access on any Device.** Tamari is designed to function well on any desktop, laptop, tablet, or smartphone.

## Installing with Docker 🐳
This creates a 'tamariappdata' volume for persistent storage.
```
docker run -d --restart=always -p 4888:4888 -v tamariappdata:/app/appdata --name tamari alexbates/tamari:0.9
```
Tamari is now running! Go to http://localhost:4888

### Alternative Command with Mail Settings
Use this command instead if you wish to enable password reset requests via email. Replace variables with settings for an email account you control.
```
docker run -d -e MAIL_SERVER=mail.example.com -e MAIL_PORT=587 -e MAIL_USE_TLS=1 -e MAIL_USERNAME=youremail@example.com -e MAIL_PASSWORD=yourpassword --restart=always -p 4888:4888 -v tamariappdata:/app/appdata --name tamari alexbates/tamari:0.9
```

## Manual Installation

### Install on Debian 11
Use a virtual environment to ensure that dependencies don't interfere with other software on your system.
```
sudo apt install python3 python3-venv git
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

Please make backups of your data. As of Version 0.5, all user data is stored in app/appdata. 
```
Tamari/app/appdata/app.db
Tamari/app/appdata/migrations
Tamari/app/appdata/recipe-photos
```
With Version 0.4, migrations directory is located at "Tamari/migrations" and recipe-photos is located at "Tamari/app/recipe-photos". app.db is found in either the Tamari or app directory.

For Docker, if using tamariappdata (previously tamaristorage) volume, files may be mounted at the following locations.
```
/var/lib/docker/volumes/tamariappdata/_data/app.db
/var/lib/docker/volumes/tamariappdata/_data/migrations
/var/lib/docker/volumes/tamariappdata/_data/recipe-photos
```