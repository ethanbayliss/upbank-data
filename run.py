#imports
import conf
import requests
import json
from datetime import datetime, timedelta

#conf
conf.load("config.json")

#constants
UP_API_ENDPOINT = "https://api.up.com.au/api/v1"
YNAB_API_ENDPOINT = "https://api.youneedabudget.com/v1"

#creds
UP_CREDS_HEADER = {"Authorization": "Bearer {}".format(conf.get("upbankApiKey"))}
YNAB_CREDS_HEADER = {"Authorization": "Bearer {}".format(conf.get("ynabAccessToken"))}

def main():
    #Main function ran on script startup
    if not testYnabApi():
        print("YNAB API connection failed, please check your config file")
        exit(1)
    if not testUpbankApi():
        print("YNAB API connection failed, please check your config file")
        exit(1)

    bankAccounts = getUpAccounts()

    for account in bankAccounts:
        #print(account)
        getTransactions(account)


def testUpbankApi():
    #Make a call to up bank's API and parse result to determine if key is correct
    apiStatus = False

    resp = requests.get("{}/util/ping".format(UP_API_ENDPOINT),headers=UP_CREDS_HEADER)

    if resp.status_code == 200:
        print("Up Bank Connected: {}".format(json.loads(resp.content)["meta"]["statusEmoji"]))
        apiStatus = True
    if resp.status_code != 200:
        print("Up Bank connection failed: GET /util/ping {}".format(resp.status_code))
    return apiStatus

def testYnabApi():
    #Make a call to YNAB API to test key
    apiStatus = False

    resp = requests.get("{}/budgets".format(YNAB_API_ENDPOINT),headers=YNAB_CREDS_HEADER)

    if resp.status_code == 200:
        apiStatus = True
        print("Found YNAB Budgets: ")
        for budget in json.loads(resp.content)["data"]["budgets"]:
            print("\t{}".format(budget["name"]))
    if resp.status_code != 200:
        print("YNAB connection failed: GET /budgets {}".format(resp.status_code))
    return apiStatus

def getUpAccounts():
    #Get a list of all up bank accounts aka savers
    resp = requests.get("{}/accounts".format(UP_API_ENDPOINT),headers=UP_CREDS_HEADER)

    if resp.status_code == 200:
        print("Found Up Bank Accounts: ")
        for account in json.loads(resp.content)["data"]:
            print("\t{}".format(account["attributes"]["displayName"]))
    if resp.status_code != 200:
        print("Up Bank connection failed: GET /accounts {}".format(resp.status_code))
    return json.loads(resp.content)["data"]

def getTransactions(bankAccounts):
    #Get past x days of transactions from the cheque account
    transactions = []
    filteredTransactions = []

    for account in bankAccounts:
        print(account)
        if account["attributes"]["accountType"] == "TRANSACTIONAL":
            chequeAccount = account
            break

    resp = requests.get(chequeAccount["relationships"]["transactions"]["links"]["related"],headers=UP_CREDS_HEADER)
    transactions = json.loads(resp.content)["data"]

    for transaction in transactions:
        if datetime.fromisoformat(transaction["createdAt"]) >= (datetime.now() + timedelta(days=-30)):
            print(transaction["attributes"]["amount"]["value"])

    print(json.loads(resp.content))

    return filteredTransactions

if __name__ == "__main__":
    main()