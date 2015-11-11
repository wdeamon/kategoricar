# -*- coding: cp1250 -*-
import socket
import threading
import string
import datetime
import time
import sqlite3
import os
import json

from imports.sqlwork import sqlWork
from imports.htmlgetter import hzzoHtmlGetter
from bs4 import BeautifulSoup




# ##############
#configuration#
#############################################

serverPort = 8666
logPort = 8667
updaterPort = 8668
serverIP = "localhost"
##############################################

def timer(timeout):
    #time in secunds!!
    now = time.time()
    future = now + timeout
    while (True):
        if time.time() > future:
            break


def dataObrada(data):
    try:
	sql = sqlWork()
        podaci = sql.returnData("select kategorija, mbo, counter from testTable where mbo = %s" % data["mbo"])
        if (podaci != []):
	    sql.updateData(mbo=data[mbo], counter=podaci[0][2])
	    sql.commitData()
        else:
            #provjera na netu
	    sql.insertData(mbo=data["mbo"], kategorija=data["kategorija"], osnova=data["osnova"], areacode=data["podrucni"])
	    sql.commitData()
    except:
        pass


def scraping(html, data):
    try:
        soup = BeautifulSoup(html)
        text = soup.get_text()
        text = unicode(string.strip(text))
        if not string.find(text, "Nema podataka") == -1:
            data["errorCode"] = "3"
            return data
        else:
            kategorija = text[string.find(text, "Osnova:") - 2:string.find(text, "Osnova:")]
            data["kategorija"] = kategorija[1]
            text = string.strip(text)
            data["osnova"] = text[string.find(text, "Osnova:") + 10:string.find(text, "Osnova:") + 15]
            podrucni = string.split(text, "DOPUNSKO OSIGURANJE")
            podrucni = podrucni[0][len(podrucni[0]) - 6:len(podrucni[0])]
            data["podrucni"] = string.strip(podrucni)
            if len(data["podrucni"]) == 1:
                data["podrucni"] = "00" + str(data["podrucni"])
            elif len(data["podrucni"]) == 2:
                data["podrucni"] = "0" + str(data["podrucni"])
            dataObrada(data)
            data["izvor"] = "1"
            data["updateTime"] = str(datetime.datetime.now())
            return data
    except Exception as inst:
        data["errorCode"] = "1"
        print str(inst)
        return data


def ubazi(mbo):
    data = sqlWork().returnData("select mbo, kategorija from testTable where mbo = %s" % mbo)
    try:    
	data = data[0]
    except:
	pass
    try:
        if (data == "[]" or data[1] == "Null"):
            return True
    except:
        return True
    return False


def destilator(data):
    global url
    
    try:
    	if (data["vrstaZahtjeva"] == "1" or data["vrstaZahtjeva"] == "2"):	
		content = hzzoHtmlGetter().getHtml(data["mbo"])
        	data = scraping(content, data)
        	if data["errorCode"] != 0:
            		return data
		sql = sqlWork()
		sql.updateData(mbo=data["mbo"], kategorija=data["kategorija"], areacode=data["podrucni"], osnova=data["osnova"])
		sql.commitData()
        	return data
    	elif (ubazi(data["mbo"])):
        	content = hzzoHtmlGetter().getHtml(data["mbo"])
        	podatak = scraping(content, data)
		sql = sqlWork()
		sql.updateData(mbo=podatak["mbo"], kategorija=podatak["kategorija"], areacode=podatak["podrucni"],osnova=podatak["osnova"])
		sql.commitData()
        	return podatak
    	else:
		data_baza = sqlWork().returnData("select kategorija, podrucni, osnova, zadnjiUpdate from testTable where mbo = %s" % data["mbo"])            
		data_baza = data_baza[0]
        	data["kategorija"] = data_baza[0]
        	data["podrucni"] = data_baza[1]
        	data["osnova"] = data_baza[2]
        	data["izvor"] = "1"
        	data["updateTime"] = data_baza[3]
        	return data

    except Exception as inst:
        dataObrada(data)
        #log :: progreska u obradi podataka
        #print("Pogreska na serveru! MBO:" + poruka)
        print  "ispis data"
        print str(inst)
        data["errorCode"] = "1"
        if data["vrstaZahtjeva"] == "2":
            return data["errorCode"]
        return data


def slanje(conn, addr, data):
    conn.sendto(json.dumps(destilator(data)), addr)


def server_thread():
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.bind((serverIP, serverPort))
    while 1:
        data, addr = conn.recvfrom(2048)
        data = json.loads(data)
        try:
            data["errorCode"] = 0
        except:
            data = json.loads(data)
        #here goes code for logs!!
        #print("Podaci(" + data["mbo"] + ") primljeni! IP:" + str(addr))
        t = threading.Thread(target=slanje, args=(conn, addr, data))
        t.start()
    conn.close()


def log_thread(value):
	pass
	#hmm tu jos moram staviti kako se spremati log.

       


def updater_thread():
#    updater_con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    updater_con.bind((serverIP, updaterPort))
#    rjecnik = {"mbo": "143520838", "kategorija": "A", "podrucni": "004", "osnova": "00112", "brojPristupa": "0",
#              "errorCode": "0", "updateTime": "14", "vrstaZahtjeva": "2", "izvor": "0"}
    pass
    # prima mbo po mbo i provjerava. U slučaju da se dogode tri pogreške briši mbo iz baze 



if __name__ == "__main__":
    #treba procijeniti dali je taj while potreban ... mislim da ce se maknuti jer samo stvara teren na procesor
    while 1:
        #starting server thread
        tekst = str(threading.enumerate())
        if string.find(tekst, "server") == -1:
            MainThread = threading.Thread(target=server_thread, name="server")
            MainThread.start()


        #starting log thread
        #if string.find(tekst, "log") == -1:
        #    LogThread = threading.Thread(target=log_thread, name="log")
        #    LogThread.start()

        #starting updater thread
        #if string.find(tekst, "updater") == -1:
        #    UpdateThread = threading.Thread(target=updater_thread, name="updater")
        #    UpdateThread.start()
        timer(30)
#enter code for checks and so on
