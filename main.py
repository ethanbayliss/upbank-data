#!/usr/bin/python3

#imports
import conf
import requests
import json
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import csv
import io

#conf
conf.load("config.json")

#constants
UP_API_ENDPOINT = "https://api.up.com.au/api/v1"
TIME_NOW = pytz.timezone(conf.get("TIMEZONE")).localize(datetime.now())
TZ = pytz.timezone(conf.get("TIMEZONE"))
#DEBUG = not __debug__
DEBUG = False

#creds
UP_CREDS_HEADER = {"Authorization": "Bearer {}".format(conf.get("UP_API_KEY"))}

def main():
    #Main function ran on script startup
    if not testUpbankApi():
        exit(10)

    bankAccounts = getUpAccounts()

    # #Get cheque account
    # for account in bankAccounts:
    #     if account['attributes']['displayName'] == 'Spending':
    #         printCsv(getTransactions(account, 30),bankAccounts)
    #         break

    days = int(input("Enter how many days of transactions to grab: "))

    print("Getting {} days of transactions".format(days))

    for account in bankAccounts:
        saveCsv(getTransactions(account, days), account)

def saveCsv(transactions,account):
    output = open("data/{}.csv".format(account['attributes']['displayName']), "w", encoding="utf-8")
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(["Date","Payee","Memo","Amount"])
    for transaction in transactions:
        writer.writerow([
            parser.parse(transaction["attributes"]["createdAt"]).strftime('%d-%m-%Y'),
            transaction["attributes"]["description"],
            "{}: {}".format(
                parser.parse(transaction['attributes']['createdAt']).astimezone(TZ).strftime('%I:%M%p'),
                transaction['attributes']['rawText'],
            ),
            transaction["attributes"]["amount"]["value"],
        ])

def printCsv(transactions,bankAccounts):
    print("Date,Payee,Memo,Amount")
    for transaction in transactions:
        print("{},{},{},{}".format(
            parser.parse(transaction["attributes"]["createdAt"]).strftime('%d-%m-%Y'),
            transaction["attributes"]["description"],
            "Imported: " + TIME_NOW.strftime('%d-%m-%Y'),
            transaction["attributes"]["amount"]["value"],
        ))

def testUpbankApi():
    '''
    Make a call to up bank's API and parse result to determine if key is correct
    '''
    apiStatus = False

    resp = requests.get("{}/util/ping".format(UP_API_ENDPOINT),headers=UP_CREDS_HEADER)

    if resp.status_code == 200:
        if DEBUG: print("Up Bank Connected: {}".format(json.loads(resp.content)["meta"]["statusEmoji"]))
        apiStatus = True
    if resp.status_code != 200:
        print("Up Bank connection failed: GET /util/ping {}".format(resp.status_code))
        raise ValueError("Up Bank credentials may be wrong. Move the config-template.json template to config.json and replace the U API credential")
    
    return apiStatus

def getUpAccounts():
    #Get a list of all up bank accounts aka savers
    resp = requests.get("{}/accounts".format(UP_API_ENDPOINT),headers=UP_CREDS_HEADER)
    accounts = []

    if resp.status_code == 200:
        if DEBUG: print("Found Up Bank Accounts: ")
        for account in json.loads(resp.content)["data"]:
            if DEBUG: print("\t{}".format(account["attributes"]["displayName"]))
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
