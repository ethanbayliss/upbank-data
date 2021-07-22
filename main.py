#!/usr/bin/python3

#imports
import conf
import requests
import json
from datetime import datetime, timedelta
import pytz

#conf
conf.load("config.json")

#constants
UP_API_ENDPOINT = "https://api.up.com.au/api/v1"
TIME_NOW = pytz.timezone("Australia/Perth").localize(datetime.now())

#creds
UP_CREDS_HEADER = {"Authorization": "Bearer {}".format(conf.get("upbankApiKey"))}

def main():
    #Main function ran on script startup
    if not testUpbankApi():
        print("YNAB API connection failed, please check your config file")
        exit(1)

    bankAccounts = getUpAccounts()

    #Get cheque account
    for account in bankAccounts:
        if account["attributes"]["accountType"] == "TRANSACTIONAL":
            chequeAccount = account
            break

    printCsv(getTransactions(chequeAccount, -1),bankAccounts)
    

def printCsv(transactions,bankAccounts):
    print("id,accountId,accountName,description,rawText,createdAt,value,parentCategory,category,transferAccountId,transferAccount")
    for transaction in transactions:
        print("{},{},{},{},{},{},{}".format(
            transaction["id"],
            transaction['relationships']['account']['data']['id'],
            getAccountName(bankAccounts,transaction['relationships']['account']['data']['id']),
            transaction["attributes"]["description"],
            transaction['attributes']['rawText'],
            transaction["attributes"]["createdAt"],
            transaction["attributes"]["amount"]["value"],
        ),
        end="")

        if(transaction['relationships']['category']['data']):
            print(",{},{}".format(
                transaction['relationships']['parentCategory']['data']['id'],
                transaction['relationships']['category']['data']['id'],
            ),
            end="")
        else:
            if(transaction['relationships']['transferAccount']['data']):
                print(",transfer,transfer",end="")
            else:
                print(",,",end="")

        if(transaction['relationships']['transferAccount']['data']):
            print(",{},{}".format(
                transaction['relationships']['transferAccount']['data']['id'],
                getAccountName(bankAccounts,transaction['relationships']['transferAccount']['data']['id']),
            ),
            end="")
        else:
            print(",,",end="")

        print()

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

def getUpAccounts():
    #Get a list of all up bank accounts aka savers
    resp = requests.get("{}/accounts".format(UP_API_ENDPOINT),headers=UP_CREDS_HEADER)
    accounts = []

    if resp.status_code == 200:
        print("Found Up Bank Accounts: ")
        for account in json.loads(resp.content)["data"]:
            print("\t{}".format(account["attributes"]["displayName"]))
            accounts.append(account)
    if resp.status_code != 200:
        print("Up Bank connection failed: GET /accounts {}".format(resp.status_code))
    
    return accounts

def getTransactions(account, daysFrom):
    #Get past x days of transactions from the cheque account, -1 gets all
    transactions = []

    nextTransactionPage = account["relationships"]["transactions"]["links"]["related"]
    while True:
        resp = requests.get(nextTransactionPage,headers=UP_CREDS_HEADER)

        for transaction in json.loads(resp.content)["data"]:
            transactions.append(transaction)
        
        #If the transactions list has no more items, stop getting more transactions
        if json.loads(resp.content)["links"]["next"] is None:
            break

        #If the first transaction in the list is before a certain date, stop getting more transactions
        if daysFrom != -1:
            if datetime.fromisoformat(json.loads(resp.content)["data"][0]["attributes"]["createdAt"]) < TIME_NOW + timedelta(days=-daysFrom):
                break

        nextTransactionPage = json.loads(resp.content)["links"]["next"]

    return removeOldTransactions(transactions, daysFrom)

def removeOldTransactions(transactions, daysFrom):
    filteredTransactions = []

    if daysFrom == -1:
        filteredTransactions = transactions
    else:
        for transaction in transactions:
            if datetime.fromisoformat(transaction["attributes"]["createdAt"]) >= TIME_NOW + timedelta(days=-daysFrom):
                filteredTransactions.append(transaction)

    return filteredTransactions

def getAccountName(bankAccounts,accountId):
    for account in bankAccounts:
        if account["id"] == accountId:
            return account["attributes"]["displayName"]

if __name__ == "__main__":
    main()