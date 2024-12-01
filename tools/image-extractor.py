# This code converts "url;title" text files to "url;title;imageurl" format
# Used for Tamari V0.6 Explore improvments

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests, time

# Use custom headers with page requests to prevent request blocking
headers = {
    'User-Agent': UserAgent().random,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Open text file with "url;title" format
# Encoding is specified to avoid UnicodeDecodeErrors 
readfile = open('justapinch-all-1.txt', "r", encoding="utf-8")
filelines = readfile.readlines()
# Original text file is read into a multidimensional array
lines = []
for line in filelines:
    x = line.split(";")
    newline = [x[0], x[1]]
    lines.append(newline)
readfile.close()
# Create blank text file that will have "url;title;imageurl" format
newfile = open('justapinch-all-1-picture.txt', "w")
# Count variable is used for outputting progress
count = 1
for line in lines:
    # 16 second timeout and exception handling for page requests
    try:
        page = requests.get(line[0], timeout=16, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
    except:
        soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
    photo_1 = soup.find('meta',attrs={"property": "og:image"})
    if photo_1:
        photo = photo_1['content']
    else:
        photo = ''
    # Original text file has line break at end of title, we need to remove that
    line1 = line[1].replace("\n","")
    newline = line[0] + ";" + line1 + ";" + photo + "\n"
    newfile.write(newline)
    # Output lines completed, effectively a progress bar
    print("Lines completed: " + str(count) + " / " + str(len(lines)))
    count += 1
    # 5 second delay between page requests
    time.sleep(5)
newfile.close()
