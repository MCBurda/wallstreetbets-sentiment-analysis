import pyodbc
import DataProcessing
import Secrets

print("The script has started. It will take 5-10 minutes to run through, when given 40 posts and 20 comments each.")

# ------------- PART 1: INFO EXTRACTION ---------------

content_list = []  # List for storing Reddit titles & comments
number_posts = 60  # You can change this value for more or less posts. Do not exceed 20, since API costs are expensive
number_comments = 15  # You can change this value for more or less comments. Do not exceed 20, since API costs are expensive


# We start by extracting the data from Reddit by passing the reddit client and a list to our extraction function
print("Starting Extraction...")
DataProcessing.Data_Extraction(Secrets.reddit, content_list, number_posts, number_comments)


# -------------- PART 2: TEXT CLEANING --------------------

JSON_Struct = []  # We create a JSON object to store all data that will eventually end up in our SQL database

# We now pass our list of extracted content to the data cleaning function, which will clean it and return a dictionary with all our database values
print("Starting Cleaning...")
DataProcessing.Clean_Data(content_list, JSON_Struct)


# -------------- PART 3: ENTITY RECOGNITION ------------------

# We iterate through the each Reddit text snippet and try to find companies (ORG) or Geo-Political Entities (GPE) named in them, then extract those
print("Starting Entity Recognition...")
DataProcessing.Entity_Recognition(JSON_Struct, Secrets.org_url, Secrets.headers, Secrets.company_search_api, Secrets.company_search_sk)


# -------------- PART 5: SENTIMENT ANALYSIS -------------------

# For each identified Organization (ORG) or Geo-Political Organization (GPE), we identify the sentiment of the comment or post
print("Starting Sentiment Analysis...")
DataProcessing.Sentiment_Analysis(JSON_Struct, Secrets.sentiment_url, Secrets.headers)


# -------------- PART 6: COMPANY DATA FETCH FROM IEX -----------------

# Each identified stock ticker is now fed into the IEX API to find its historical returns
print("Starting Stock Data Lookup...")
DataProcessing.Stock_Data_Lookup(JSON_Struct, Secrets.IEX_client, Secrets.iex_sk)

print("----------------- Printing the dictionary of extracted data ------------------------")
print(JSON_Struct)


# ------------ PART 7: INSERT INTO MySQL Database ------------

conn = None  # We set the connection to None initially, in order to test if our connection attempt is successful
try:
    conn = pyodbc.connect("Driver={SQL Server};"
                          "Server=DESKTOP-LRHJDUA\SQLEXPRESS;"
                          "Trusted_Connection=yes;"
                          "Uid=auth_window;")
    print('Connected to SQL Server Successfully')

except:
    print('Connection failed to SQL Server')

if conn is not None: # Here we test if our connection attempt worked. If it did and the connection is not none and we enable autocommit, which
    # means that each SQL command committed is treated as one transaction against the database and cannot be rolled back --> https://en.wikipedia.org/wiki/Autocommit
    conn.autocommit = True

# Connect to database
cursor = conn.cursor()

DataProcessing.Identify_Database(cursor)


# Insert individual titles and comments that contain a company into the database
DataProcessing.Insert_Data(JSON_Struct, cursor)

# If all goes well, this will show
print("Script executed successfully!")
