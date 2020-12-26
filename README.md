# Wallstreetbets Sentiment Analysis

This project was created for the exam of the Business Data Processing and Business Intelligence course at Copenhagen Business School in Fall 2020.

This git repository contains the components of a data pipeline that I built, in order to fetch Reddit posts and their comments from the online stock trading forum r/wallstreetbets. The pipeline is comprised of the following steps:


STEP 1: The PRAW library for Reddit is used to fetch post titles, post bodies, and comments from the latest "hot" posts of r/wallstreetbets.

STEP 2: Each retrieved text snippet is cleaned and analyzed for company (ORGs or GPEs) mentions using a TextAnalysis API based on the Natural Language Toolkit library for Python (NLTK). 

STEP 3: Thereafter, each snippet containing a company mention is analyzed for sentiment with the TextAnalysis API and the results are saved (Polarity and Subjectivity are measured). 

STEP 4: The stock ticker corresponding to the company found in the Reddit post/comment is fed into the Financialmodellingprep API ( ). The result is the likely stock ticker associated with the company name. 

STEP 5: The stock ticker is used to query the IEX API for the historical return data, company profile, and latest stock quote of the company's stock.

STEP 6: The script checks for a local SQL database. If it doesn't exist, a new one is created. All the Reddit posts and comments that contained company mentions are fed into the database, consisting of three tables: Tickers, Companies, Comments.

STEP 7: The Tableau Workbook is connected to the SQL database and visualizes the results in a dashboard.


In this repository you will find:
- 3 linked Python files - RedditScrape.py (executes processing logic), DataProcessing.py (defines data processing functions), Secrets.py (APIs that I used with keys blended out)
- 1 Tablea workbook with the Dashboard and all base reports used in it to visualize the Reddit comment data
- 1 Tableau extract file called "redditscrapeDB"
- 1 Microsoft SQL Database file called "redditscrapeDB"

The final exam report is not included, due to it still being graded. Please reach out if you are interested in contributing to the project. 




