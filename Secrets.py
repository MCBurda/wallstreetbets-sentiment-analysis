import praw
import pyEX

# ------- Authentication Information fro APIs ---------

# I am using the PRAW wrapper for the Reddit developer API, which provides me with simplified methods to access the different
# functionalities of the Reddit API. The wrapper also times the API calls for me, in order for me not to break the allowed call limits.
# Documentation: https://praw.readthedocs.io/
# Register your app with Reddit: https://www.reddit.com/prefs/apps
reddit = praw.Reddit(
    client_id="INSERT OWN CLIENT ID FROM REDDIT",
    client_secret="INSERT OWN CLEINT SECRET",
    user_agent="INSERT OWN USER AGENT"
)

# TextAnalysis API Information for sentiment analysis and entity recognition: https://rapidapi.com/textanalysis/api/textanalysis
sentiment_url = "https://textanalysis.p.rapidapi.com/pattern-sentiment-analysis"
org_url = "https://textanalysis.p.rapidapi.com/spacy-named-entity-recognition-ner"
headers = {
    'x-rapidapi-host': "textanalysis.p.rapidapi.com",
    'x-rapidapi-key': "ENTER OWN SECRET",
    'content-type': "application/x-www-form-urlencoded"
    }

# Financial Modelling Prep API for ticker recognition
company_search_api = "https://financialmodelingprep.com/api/v3/search?query="
company_search_sk = "ENTER OWN SECRET"

# IEX API
# IEX is an American stock exchange that offers a free API to retrieve company data based on the ticker symbol
# I installed a free library for IEX's API called PyEx, since it handles caching for us, allowing us to save API requests and latency
iex_pk = "ENTER OWN PUBLIC KEY "
iex_sk = "ENTER OWN SECRET KEY"
iex_api = "https://cloud.iexapis.com/"

IEX_client = pyEX.Client(api_token=iex_sk, version='v1', api_limit=5)

# ---------- END OF AUTH INFO ----------------------
