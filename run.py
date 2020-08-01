#imports
import conf
import requests
import json

#conf
conf.load("config.json")

#constants
UP_API_ENDPOINT = "https://api.up.com.au/api/v1"

#creds
UP_CREDS_HEADER = {"Authorization": "Bearer {}".format(conf.get("upbankApiKey"))}

#curl https://api.up.com.au/api/v1/util/ping \
#  -H "Authorization: Bearer $your_access_token"

def main():
    """Main function ran on script startup"""
    testUpbankApi()

def testUpbankApi():
    """Make a call to up bank's API and parse result to determine if key is correct"""
    resp = requests.get("{}/util/ping".format(UP_API_ENDPOINT),headers=UP_CREDS_HEADER)
    if resp.status_code == 200:
        print("Up Bank Connected: {}".format(json.loads(resp.content)["meta"]["statusEmoji"]))
    if resp.status_code != 200:
        print("Up Bank connection failed: GET /util/ping {}".format(resp.status_code))

def testYnabApi():
    """Make a call to YNAB API to test key"""

if __name__ == "__main__":
    main()