# Tamari

Tamari is a fully-featured recipe manager web application built using Python and the Flask Framework. 

![GitHub repo size](https://img.shields.io/github/repo-size/alexbates/Tamari?style=plastic)
![GitHub language count](https://img.shields.io/github/languages/count/alexbates/Tamari?style=plastic)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) 
![GitHub last commit](https://img.shields.io/github/last-commit/alexbates/Tamari?color=red&style=plastic)

![Tamari Screenshot](https://bates.gg/mockup-tamari-min.png)

## Live Demo

Try it out at https://demo.tamariapp.com

Some functionality is disabled and data is deleted every 20 minutes.

## Features
- **Create User Accounts.** Login with an email and password. If configured on the instance, account passwords can be reset by sending a reset request to the email associated with your account.
- **Store, View, Search, and Share Recipes.** For a single recipe, you can save a title, category, description, time estimates, servings, URL, ingredients, instructions, and a photo. If you don’t upload a photo, Tamari will assign a random cooking-themed placeholder. On the detail page for a recipe, you can click to cross off completed ingredients and instruction steps while you are cooking. Search-as-you-type functionality enables you to find the recipe you are looking for as quickly as possible. Recipes are only visible while logged in by default, however you can make a recipe public and share the URL with anyone.
- **Organize.** Mark recipes as Favorites for easy access. Assign categories to recipes and browse by category.
- **Explore.** Browse and search a collection of over 36,000 recipes from three recipe sharing websites (more coming soon!). When you browse a recipe in Explore, Tamari will fetch and parse the relevant data from the URL without requiring you to visit the webpage. Import a recipe into My Recipes with the click of a button.
- **Make Shopping Lists.** Make a shopping list for each store you shop at. Add all ingredients for a specific recipe to a shopping list with the click of a button. Click an item on a shopping list to mark it as completed.
- **Plan Meals.** Use the Meal Planner to keep on top of what you plan to cook for the week. The Schedule button can assign a recipe being viewed to a date up to 30 days in advance.
- **Customize.** Choose to display large photos to show off your recipes to friends, or smaller photos to fit more recipes on the screen. Sort recipes by title or by date added. Select between four account profile pictures. Set an accent color that applies to most buttons and many elements throughout the app. For a Tamari instance, some configuration options can be customized such as recipes per page and dynamic loading of images.
- **Access on any Device.** Tamari is designed to function well on any desktop, laptop, tablet, or smartphone.

## Installing with Docker 🐳
This creates a 'tamaristorage' volume for persistent storage.
```
docker run -d --restart=always -p 4888:4888 -v tamaristorage:/app --name tamari alexbates/tamari:0.4
```
Tamari is now running! Go to http://localhost:4888

### Alternative Command with Mail Settings
Use this command instead if you wish to enable password reset requests via email. Replace variables with settings for an email account you control.
```
docker run -d -e MAIL_SERVER=mail.example.com -e MAIL_PORT=587 -e MAIL_USE_TLS=1 -e MAIL_USERNAME=youremail@example.com -e MAIL_PASSWORD=yourpassword --restart=always -p 4888:4888 -v tamaristorage:/app --name tamari alexbates/tamari:0.4
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

### Start Tamari Automatically at System Boot
Make start script executable (must be in Tamari directory)
```
sudo chmod u+x start.sh
```
Create Systemd service
```
sudo nano /etc/systemd/system/tamari.service
```
Paste This (You must change “USERNAME”)
```
[Unit]
Description=Tamari Recipe Manager
After=syslog.target network.target

[Service]
Type=simple
WorkingDirectory=/home/USERNAME/Tamari
ExecStart=/home/USERNAME/Tamari/start.sh
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
```
Start the Systemd service
```
sudo systemctl enable tamari.service
sudo systemctl start tamari.service
```

### Access Tamari from behind a reverse proxy
Here is a sample Nginx config (/etc/nginx/conf.d/default.conf).
```
server {
	listen 80;
	server_name tamari.example.com;
	return 301 https://tamari.example.com$request_uri;
}
server {
	listen 443 ssl;
	server_name tamari.example.com;
	ssl on;
	
	location / {
		proxy_pass		http://127.0.0.1:4888;
		proxy_set_header Host $http_host;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-Proto $scheme;
		add_header 'Content-Security-Policy' 'upgrade-insecure-requests';
		proxy_redirect http://$http_host/ https://$http_host/;
	}
	ssl_certificate /etc/ssl/certs/tamari.example.com/fullchain.pem;
	ssl_certificate_key /etc/ssl/certs/tamari.example.com/privkey.pem;
}
```
This forces SSL, causes Flask url_for to build urls using subdomain instead of localhost, and prevents http resources from being blocked by browsers. An SSL certificate for your domain is required. 

### Configure Mail Settings (Optional)
Configure to enable password reset requests via email. If login username is not the same as your email address, you need to configure 'ADMIN' in config.py.
```
source venv/bin/activate
export MAIL_SERVER=mail.example.com
export MAIL_PORT=587
export MAIL_USE_TLS=1
export MAIL_USERNAME=youremail@example.com
export MAIL_PASSWORD=yourpassword
```

## Backups

Please make backups of your data. All user data is stored in the following database file and directory.
```
Tamari/app/app.db
Tamari/app/recipe-photos
```
For Docker, if using tamaristorage volume, files may be mounted at the following locations.
```
/var/lib/docker/volumes/tamaristorage/_data/app.db
/var/lib/docker/volumes/tamaristorage/_data/recipe-photos
```