import requests
from datetime import datetime
from time import strftime


def Data_Extraction(client, content_list, number_posts, number_comments):
    # I am looping through the latest "Hot" submissions on the Investing Reddit thread. I have limited the results to 10.
    for submission in client.subreddit("wallstreetbets").hot(
            limit=number_posts):  # Alternatively use .rising() to list the submissions rising in popularity
        if "Formal posting guidelines" in submission.title or "Daily Advice" in submission.title or submission.author is None:  # Skip the first guidelines posts
            continue
        content_list.append({"text": submission.title + submission.selftext, "user": submission.author.name, "upvotes": submission.score, "datetime": datetime.utcfromtimestamp(submission.created_utc).strftime('%Y%m%d %H:%M:%S')})
        count = 0

        # This is a Reddit API wrapper specific instruction, which tells the wrapper to not load further comments, when fetching
        # Comment replies from reddit response trees.
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            # Skip welcoming comment or comments that have no name, due to the user being deleted
            if "welcome to /r/investing." in str(comment.body) or comment.author is None:
                continue
            if count >= number_comments:  # Limit the amount of comments taken from each submission to 5
                break
            content_list.append({"text": comment.body, "user": comment.author.name, "upvotes": comment.score, "datetime": datetime.utcfromtimestamp(comment.created_utc).strftime('%Y%m%d %H:%M:%S')})
            count += 1


def Clean_Data(content_list, dictionary):
    # We need to replace all blank spaces with %20, in order for the API to accept our input. The space is a reserved character
    # in this specific API, similar to URLs, which is why it needs to be "percent encoded" to its byte value in ASCII
    for index, content in enumerate(content_list):
        cleaned_content = content["text"].replace(" ", "%20").replace("\r", "%20").replace("\n", "%20").replace("\"", "").replace("\'", "")
        content["text"].replace("\r", "").replace("\n", "").replace("\"", "").replace("\'", "")
        row = {"id": index + 1, "user": content["user"], "companies": {}, "data": {"raw_data": content["text"], "input_data": "text=" + cleaned_content}, "sentiment": {"upvotes": content["upvotes"]}, "datetime": content["datetime"]}
        dictionary.append(row)
        print(row)


def Entity_Recognition(dictionary, org_url, headers, company_search_api, company_search_sk):
    for index, piece in enumerate(dictionary):
        response = requests.request("POST", org_url, data=piece["data"]["input_data"].encode('utf-8'), headers=headers).json()
        companies = {}
        if not response["result"]:
            continue
        for entity in response["result"]:
            if "ORG" == entity.split("/")[1] or "GPE" == entity.split("/")[1]:  # If the recognized entity is an organization, it is extracted and saved
                company = entity.split("/")[0]
                company.replace(".", "").replace("!", "").replace("?", "").replace(",", "")
                print(company)

                # PART 4: TRANSFORM ENTITIES TO STOCK TICKERS

                # Some of the organizations identified by the former entity recognition API are provided as company names. In order to
                # search for these companies with the IEX API in the next step, we need the stock tickers. We make an API call to
                # financialmodelingprep.com/api/v3/search?, which allows us 250 API calls a day for free. We try to limit our use by only calling the API
                # if the found org name is longer than 4 chars and thus likely not a stock ticker.

                if len(company) > 4:  # Im ONLY looking at all identified entities over the maximum stock ticker length.
                    try:
                        # Request data from company recognition api to see if we can get a ticker
                        search_url = company_search_api + company.replace(" ", "%20") + "&limit=1&apikey=" + company_search_sk
                        identified_data = requests.get(search_url).json()

                        # If the api finds a ticker, we update the company name in the JSON dictionary
                        company_ticker = identified_data[0]["symbol"]
                        companies.update({company_ticker: {}})

                    except:
                        # If the api does not find the ticker, we dont add the entity to the list of companies in the JSON dictionary
                        continue
                else:
                    # If we believe that it is the ticker, add it.
                    companies.update({company: {}})

        dictionary[index]["companies"] = companies  # Saving the JSON  output from the GET request to the entity recognition api


def Sentiment_Analysis(dictionary, sentiment_url, headers):
    # Since the JSON structure was created before with IDs allocated by ascending index,
    # it does not need to be sorted
    for index, piece in enumerate(dictionary):
        if dictionary[index]["companies"] is not None:
            response = requests.request("POST", sentiment_url, data=piece["data"]["input_data"].encode('utf-8'),
                                        headers=headers)
            dictionary[index]["sentiment"].update(
                response.json())  # Saving the JSON Object output from the GET request to the sentiment api


def Stock_Data_Lookup(dictionary, client, iex_sk):
    for index, entry in enumerate(dictionary):
        for company_index, company in enumerate(entry["companies"]):

            try:
                company_data = client.company(symbol=company)  # Get company information (worth 1 api call)
                performance_data = client.keyStats(symbol=company)  # Get stock performance data (worth 5 api calls)
                quote_data = client.quote(symbol=company)  # Get quote data (worth 1 api call)
                dictionary[index]["companies"][company].update({"companyName": company_data["companyName"], "industry": company_data["industry"], "sector": company_data["sector"], "description": company_data["description"], "country": company_data["country"], "performance": {"symbol": company_data["symbol"], "price": quote_data["latestPrice"], "marketcap": quote_data["marketCap"], "24HourReturn": quote_data["changePercent"], "5DayReturn": performance_data["day5ChangePercent"], "30DayReturn": performance_data["day30ChangePercent"], "ytdReturn": performance_data["ytdChangePercent"], "lastUpdate": strftime("%Y%m%d %H:%M:%S")}})
                print(company)
            except Exception as e:
                print(e)
                dictionary[index]["companies"][company].update({"companyName": None})  # Setting the value of companies to zero that couldn't be found allows us to filter these out later on.


def Identify_Database(cursor):
    # Retrieving a list of all existing databases in the local MySQL DB
    cursor.execute("SELECT name FROM master.dbo.sysdatabases")
    data = cursor.fetchall()

    # Check if our destination database already exists ("redditscrapeDB")
    if data is not None:
        if "redditscrapeDB" in str(data):  # The previous fetchall() cursor method returns tuples containing the names of all databases in the MySQL server
            print("redditscrapeDB exists in the local MySQL database.")
        else:
            print("redditscrapeDB does not exist in the local MySQL database and will be created.")
            cursor.execute("CREATE DATABASE redditscrapeDB")
            cursor.execute(
                "CREATE TABLE redditscrapeDB.dbo.tickers( Ticker nvarchar(8) NOT NULL, Price float, Marketcap bigint, [24HourReturn] float, [5DayReturn] float, [30DayReturn] float, YtdReturn float, LastUpdate datetime, PRIMARY KEY (Ticker))")
            cursor.execute(
                "CREATE TABLE redditscrapeDB.dbo.companies( Id int Identity(1,1) NOT NULL, Name nvarchar(255) NOT NULL, Industry nvarchar(255), Sector nvarchar(255), Country nvarchar(255), Description nvarchar(max), Ticker nvarchar(8) NOT NULL, PRIMARY KEY(Id), FOREIGN KEY (Ticker) REFERENCES tickers(Ticker))")
            cursor.execute(
                "CREATE TABLE redditscrapeDB.dbo.comments( Ticker nvarchar(8) NOT NULL, Username nvarchar(255) NOT NULL, Posttime datetime NOT NULL, Comment nvarchar(max) NOT NULL, Upvotes int NOT NULL, Polarity float NOT NULL, Subjectivity float NOT NULL, PRIMARY KEY(Ticker, Username, Posttime), FOREIGN KEY(Ticker) REFERENCES tickers(Ticker))")

    else:  # If no databases could be found, there must be a database error.
        print("There was a database error. List of all existing databases could not be retrieved.")


def Insert_Data(dictionary, cursor):
    for index, text in enumerate(dictionary):
        if not text["companies"]:  # Skipping comments/posts with no companies mentioned in them
            print("No firms in id: " + str(text["id"]))
            continue

        for company in text["companies"]:
            company_values = list(dictionary[index]["companies"][company].values())
            if company_values[0] is None:  # The first company value is the firm name. If this is None, then we couldnt find data on the firm and should skip it
                print("None")
                continue
            print(company_values)

            # Check if the found ticker already exists in our database
            cursor.execute("SELECT * FROM redditscrapeDB.dbo.tickers WHERE Ticker = ?", (company_values[5]["symbol"]))
            data = cursor.fetchall()
            if len(data) != 0:  # If a ticker with the symbol was found, update its market values
                print("updating financials")
                cursor.execute(
                    "UPDATE redditscrapeDB.dbo.tickers SET Price = ?, Marketcap = ?, [24HourReturn] = ?, [5DayReturn] = ?, [30DayReturn] = ?, YtdReturn = ?, LastUpdate = ? WHERE Ticker = ?",
                    (company_values[5]["price"], company_values[5]["marketcap"], company_values[5]["24HourReturn"],
                     company_values[5]["5DayReturn"], company_values[5]["30DayReturn"], company_values[5]["ytdReturn"],
                     company_values[5]["lastUpdate"], company_values[5]["symbol"]))
            else:  # If not, insert the new ticker and all values
                cursor.execute(
                    "INSERT INTO redditscrapeDB.dbo.tickers (Ticker, Price, Marketcap, [24HourReturn], [5DayReturn], [30DayReturn], YtdReturn, LastUpdate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (company_values[5]["symbol"], company_values[5]["price"], company_values[5]["marketcap"],
                     company_values[5]["24HourReturn"], company_values[5]["5DayReturn"],
                     company_values[5]["30DayReturn"],
                     company_values[5]["ytdReturn"], company_values[5]["lastUpdate"]))
                # If the ticker doesn't exist, then by the logic of the SQL table, the company can't either, because the company ticker cannot be NULL
                cursor.execute(
                    "INSERT INTO redditscrapeDB.dbo.companies (Name, Industry, Sector, Country, Description, Ticker) VALUES (?, ?, ?, ?, ?, ?)",
                    (company_values[0], company_values[1], company_values[2], company_values[4], company_values[3],
                     company_values[5]["symbol"]))

            # Check if the found comment already exists in our database
            cursor.execute(
                "SELECT * FROM redditscrapeDB.dbo.comments WHERE (Ticker = ? AND Username = ? AND Posttime = ?)",
                (company_values[5]["symbol"], dictionary[index]["user"], dictionary[index]["datetime"]))
            data = cursor.fetchall()
            if len(data) != 0:  # If a ticker with the symbol was found, update its market values
                print("updating comment")
                cursor.execute(
                    "UPDATE redditscrapeDB.dbo.comments SET Upvotes = ? WHERE (Ticker = ? AND Username = ? AND Posttime = ?)",
                    (
                    dictionary[index]["sentiment"]["upvotes"], company_values[5]["symbol"], dictionary[index]["user"],
                    dictionary[index]["datetime"]))
                continue
            else:
                cursor.execute(
                    "INSERT INTO redditscrapeDB.dbo.comments (Ticker, Username, Posttime, Comment, Upvotes, Polarity, Subjectivity) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (company_values[5]["symbol"], dictionary[index]["user"], dictionary[index]["datetime"],
                     dictionary[index]["data"]["raw_data"], dictionary[index]["sentiment"]["upvotes"],
                     dictionary[index]["sentiment"]["Polarity"], dictionary[index]["sentiment"]["Subjectivity"]))


