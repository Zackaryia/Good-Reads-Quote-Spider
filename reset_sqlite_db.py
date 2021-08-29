
# # # # # # # # # # #

# Resets SQLite DB. #

# # # # # # # # # # #

import os
if os.path.isfile('./quotes.db'): #if the database already exists then remove it to have a freash start
    os.remove("quotes.db")


import sqlite3

conn = sqlite3.connect('quotes.db')

c = conn.cursor()

c.execute("""CREATE TABLE quotes (
    quote_string text,
    author text,
    tags text,
    likes int,
    tweet_link text,
    link text
)""")

c.execute("""CREATE TABLE scraped_tags (
    tag text,
    ammount_of_quotes int
)""")

c.execute("""CREATE TABLE to_scrape_tags (
    tag text
)""")


with open('inspirational_tags.txt', 'r') as inspirational_tags_file:
    inspirational_tags = inspirational_tags_file.readlines()

for inspirational_tag in inspirational_tags:
    c.execute("INSERT INTO to_scrape_tags VALUES (?)", (inspirational_tag.strip(),))


conn.commit()

conn.close()


"""		self.quote_string = quote_string
		self.author = author
		self.tags = tags
		self.likes = likes
		self.link = link
"""

#c.execute("INSERT INTO quotes VALUES ('when life gives', 'me', '[\"inspirational\", \"cool\"]', 10000, 'https://lmao.com/')")
#c.execute("INSERT INTO quotes VALUES (?, ?, ?, ?, ?)", ('when life gives', 'me', '[\"inspirational\", \"cool\"]', 10000, 'https://lmao.com/'))
# c.execute("INSERT INTO quotes VALUES (:quote_text, :author, :tags, :likes, :link)", {"quote_text": "when life gives", "author": "me", "tags": "[\"inspirational\", \"cool\"]", "likes": 10000, "link": "https://lmao.com/"})


#c.execute("select * from quotes")

# c.execute("select * from quotes where link='https://lmao.com/'")
# c.execute("select * from quotes where link=?", ("https://lmao.com/"))
# c.execute("select * from quotes where link=':link'", {"link": "https://lmao.com/"})

# c.execute("select * from quotes")
# print(c.fetchall().__len__())