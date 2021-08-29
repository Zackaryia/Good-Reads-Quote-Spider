from bs4 import BeautifulSoup
import requests, json, os
from time import sleep, time
from helper import *
import sqlite3
from tqdm import tqdm

# Cooldown between requesting pages from goodreads.com, sometimes you will be ratelimited and forced to wait 60 seconds to recieve a web page if you request pages too frequently.
cooldown_between_page_scrapes = 0

# Cache webpages on disc, Only recomended if you are bugtesting / developing, if you are trying to run a full scrape of good reads turn this off and reset the database.
cache = False




conn = sqlite3.connect('quotes.db')

c = conn.cursor()

def add_tag_to_scrape(tag, commit_changes = True):
	c.execute("select * from to_scrape_tags where tag=?", (tag,))
	if c.fetchone() == None: #checks if quote is already in DB
		c.execute("select * from scraped_tags where tag=?", (tag,))
		if c.fetchone() == None: #checks if quote is already in DB
			c.execute("INSERT INTO to_scrape_tags VALUES (?)", (tag,))
			if commit_changes:
				conn.commit()
			return "Interted into DB"
		else:
			return "looks like its already in the scraped database"
	return "Looks like its already in the DB"

def give_a_to_scrape_tag(list_all_of_them=False):
	c.execute("select * from to_scrape_tags")
	if list_all_of_them:
		return c.fetchall()
	else:
		return c.fetchone()[0]

def set_tag_as_scraped(tag, ammount_of_quotes, commit_changes=True):
	print(tag)
	c.execute(f"SELECT * from scraped_tags WHERE tag=?", (tag,)) 
	if c.fetchone() == None: #checks if quote is already in DB
		c.execute("select * from to_scrape_tags where tag=?", (tag,))
		if c.fetchone() == None: #checks if quote is already in DB
			raise ValueError("It looks like this variable isnt in either database")
		else:
			c.execute("INSERT INTO scraped_tags VALUES (?, ?)", (tag, ammount_of_quotes))
			c.execute("DELETE from to_scrape_tags WHERE tag=?", (tag,))
			if commit_changes:
				conn.commit()

		return "Interted into DB"
	return "Looks like its already in the DB"



class quote:
	def __init__(self, quote_string, author, tags, likes, link):

		self.quote_string = quote_string # IN DATABASE THIS IS CALLED QUOTE TEXT
		self.author = author
		self.tags = json.dumps(tags).replace('"', ':') #Because SQLite does not support lists the tags are formatted as a string the replace is to make it easier to search the DB
		self.likes = likes
		self.tweet_link = None
		self.link = link

	def add_to_db(self, commit_changes=True):
		c.execute("select * from quotes where link=?", (self.link,))
		if c.fetchone() == None: #checks if quote is already in DB
			c.execute("INSERT INTO quotes VALUES (:quote_string, :author, :tags, :likes, :tweet_link, :link)", self.toJSON())
			if commit_changes:
				conn.commit()
			return "Interted into DB"
		return "Looks like its already in the DB"

	def toJSON(self): #for json serialization
		return json.loads(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True))


def get_tag_quotes(tag):
	if cache:
		if not os.path.isdir(f"./quotes_files/{tag}"):
			os.mkdir(f"./quotes_files/{tag}")

	r = requests.get("https://www.goodreads.com/quotes/tag/"+tag)
	webpage_soup = BeautifulSoup(r.content, 'html.parser')

	
	try: # if there isnt enough quotes to make multiple pages this will fail because there will be no bottom arrow to switch between pages, So I will just set the total ammount of pages to 1
		total_amount_of_pages = int(webpage_soup.find(style="float: right;").contents[1].contents[-3].text)
	except:
		total_amount_of_pages = 1

	ammount_of_quotes = int(webpage_soup.find(class_='leftContainer').contents[1].find(class_='smallText').text.split(' ')[-1].strip().replace(',', ''))
	print(ammount_of_quotes)

	set_tag_as_scraped(tag, ammount_of_quotes, commit_changes=False)

		
	for page_number in tqdm(range(total_amount_of_pages)): # Iterates through all the pages of quotes
		page_number += 1 # because Good Reads indexes from 1 and python indexes from 0

		if cache:
			html_data = ""
			if os.path.isfile(f'./quotes_files/{tag}/{page_number}.html'):
				with open(f'./quotes_files/{tag}/{page_number}.html', 'r') as quote_file:
					html_data = quote_file.read()			
			else:
				html_data = requests.get(f"https://www.goodreads.com/quotes/tag/{tag}?page={page_number}").content
				with open(f'./quotes_files/{tag}/{page_number}.html', 'w') as quote_file:
					quote_file.write(html_data.decode('utf-8'))			
		else:
			html_data = requests.get(f"https://www.goodreads.com/quotes/tag/{tag}?page={page_number}").content

		
		webpage_soup = BeautifulSoup(html_data, 'html.parser')

		unparsed_quotes = webpage_soup.find_all(class_='quote mediumText')

		for unparsed_quote in unparsed_quotes:
			quote_text, author = unparsed_quote.find(class_="quoteDetails").find(class_="quoteText").text.split("―", 1) # get text and author
			tags = [tag.strip() for tag in unparsed_quote.find(class_="quoteFooter").find(class_="greyText smallText left").text.split(':')[1].split(",")] # tags
			link = "https://www.goodreads.com"+unparsed_quote.find(class_="quoteFooter").find(class_="right").find('a').get('href') # link_to_quote
			likes = int(unparsed_quote.find(class_="quoteFooter").find(class_="right").find('a').text.split(" ")[0]) # likes

			author = author.split(',')[0]
			quote_text, author = quote_text.strip(), author.strip()
			
			quote(quote_text, author, tags, likes, link).add_to_db(commit_changes=False)
			
			for tag_to_be_scraped in tags: #adding the tags to the lists of scraped and unscraped tags (the  spider part)
				add_tag_to_scrape(tag_to_be_scraped, commit_changes=False)

		
		current_page_time = time()
		last_page_time = current_page_time
		sleep(cooldown_between_page_scrapes)

	
try:
	while True:
		tag_to_scrape = give_a_to_scrape_tag()
		get_tag_quotes(tag_to_scrape)
		conn.commit()
finally:
	conn.close()
