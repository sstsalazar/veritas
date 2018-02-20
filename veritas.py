#! /usr/bin/python3

from  astrofetch import AstroFetch
from solarechoes import SolarEchoes
from solarechoes import Message
import csv2fits
import urllib.error
import json, os, subprocess

#Variables
veritasConfig     = "config/VERITAS.json"
filesInput        = "./data/files"
csvFiles          = "./data/src"
fitsOutput        = "./data/fits"
solarechoesConfig = "config/solarechoes.json"
fetchVeritas      = "git checkout veritas/DoNotTouch_MachineAtWork -- data/src"
veritasData       = []

#Functions
def dataAcquisition():
    if not os.scandir(filesInput):
        try:
            with open(veritasConfig) as configFile:
                config = json.load(configFile)
                fetcher = AstroFetch.AstroFetch(config["source"], config["sections"])
                fetcher.scrap()
                fetcher.fetch(filesInput)
                fetcher.print_results(filesInput)
                fetcher.print_logs(filesInput)
                return fetcher
        except urllib.error.URLError:
            print("Error accessing the URL!")
        subprocess.run(fetchVeritas.split())


def dataConversion():
    #pwd = os.getcwd()
    #print("Current Dir: {}".format(pwd))
    #access_path(csvFiles)
    #print("Current Dir: {}".format( os.getcwd()))
    for file in os.scandir(csvFiles):
        if file.is_file() and "csv" in file.name:
            print("Processing:{}".format(file.name) )
            #subprocess.run(["python2","csv2fits.py",csvFiles+"/"+file.name, fitsOutput+"/"+file.name.replace("csv","fits")])
            csv2fits.main(csvFiles+"/"+file.name, fitsOutput+"/"+file.name.replace("csv","fits"))
    #access_path(pwd)
def dataAggregation():
    from astropy.table import Table
    for rawCSV in os.scandir(csvFiles):
        if rawCSV.is_file() and "csv" in rawCSV.name:
            tab = Table.read(csvFiles+"/"+rawCSV.name, format='ascii.ecsv')
            veritasData.append(tab.meta)
    AstroFetch.AstroFetch.print_json(veritasData,"data/veritas.json")

def notifier():
    with open(solarechoesConfig) as configFile:
        config = json.load(configFile)
        messager = SolarEchoes.SolarEchoes(config["settings"], config["contacts"])
        return messager

def errorNotifications(notifier,data):
    if data:
        for entry in data.fetcher.log:
            if entry["Status"] == "ERROR":
                print(entry)
                subject = "[VERITAS] Error acquiring data"
                body = "Failed do acquire: {}".format(entry["File"])
                message(subject,body)
                notifier.send_notification(message)

def access_path( path):
    """
    Verifies if the current proccess is in the path desired and if not changes the current working directory to it
    """
    if os.getcwd() != path:
        try:
            os.chdir(path)
        except FileNotFoundError:
            print("Directory {} is not accessible!".format(path))

if __name__ == "__main__":
    notifier = notifier()
    data = dataAcquisition()
    errorNotifications( notifier, data )
    dataConversion()
    dataAggregation()
