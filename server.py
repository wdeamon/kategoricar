# -*- coding: cp1250 -*-
import socket
import threading
import string
import datetime
import time
import sqlite3
import os
import json

from bs4 import BeautifulSoup
import mechanize



# ##############
#configuration#
#############################################
url = "http://www.hzzo-net.hr/statos_MBO.htm"
serverPort = 8666
logPort = 8667
updaterPort = 8668
serverIP = "192.168.1.131"
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
        con = sqlite3.connect("kategoricar.db")
        cursor = con.cursor()
        cursor.execute("select kategorija, mbo, counter from testTable where mbo = :Mbo ", {"Mbo": data["mbo"]})
        podaci = cursor.fetchall()
        if (podaci != []):
            cursor.execute("update testTable set counter = :Counter where mbo= :Mbo ",
                           {"Mbo": data["mbo"], "Counter": podaci[0][2] + 1})
            con.commit()
        else:
            #provjera na netu
            cursor.execute("insert into testTable values(?,?,?,?,?,?)", (
            data["mbo"], data["kategorija"], datetime.datetime.now(), 0, data["osnova"], data["podrucni"]))
            con.commit()
        con.close()
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
    con = sqlite3.connect("kategoricar.db")
    cursor = con.cursor()
    cursor.execute("select mbo, kategorija from testTable where mbo = :Mbo", {"Mbo": mbo})
    data = cursor.fetchone()
    con.close()
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
            br = mechanize.Browser()
            br.set_handle_robots(False)  # ignore robots
            br.open(url, timeout=8.0)
            br.select_form(name="isktr")
            br["upmbo"] = data["mbo"]
            br["answer"] = "11111"
            res = br.submit()
            content = res.read()
            data = scraping(content, data)
            br.close()
            if data["errorCode"] != "0":
                if data["vrstaZahtjeva"] == "2":
                    return data["errorCode"]
                return data
            con = sqlite3.connect("kategoricar.db")
            cursor = con.cursor()
            cursor.execute(
                "update testTable set kategorija=:Kate, podrucni=:Pon, osnova=:Osn, zadnjiUpdate=:Up where mbo= :Mbo ",
                {"Mbo": data["mbo"], "Kate": data["kategorija"], "Pon": data["podrucni"], "Osn": data["osnova"],
                 "Up": data["updateTime"]})
            con.commit()
            if data["vrstaZahtjeva"] == "2":
                return data["errorCode"]
            return data
        elif (ubazi(data["mbo"])):
            br = mechanize.Browser()
            br.set_handle_robots(False)  # ignore robots
            br.open(url, timeout=8.0)
            br.select_form(name="isktr")
            br["upmbo"] = data["mbo"]
            br["answer"] = "11111"
            res = br.submit()
            content = res.read()
            podatak = scraping(content, data)
            br.close()
            return podatak
        else:
            con = sqlite3.connect("kategoricar.db")
            cursor = con.cursor()
            cursor.execute("select kategorija, podrucni, osnova, zadnjiUpdate from testTable where mbo = :Mbo",
                           {"Mbo": data["mbo"]})
            data_baza = cursor.fetchone()
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
        data = json.loads(data)
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
    file_name = datetime.date.isoformat(datetime.date.today()) + ".txt"
    datoteka = open(file_name, "a")
    datoteka.write(value)
    datoteka.close()
       


def updater_thread():
    updater_con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    updater_con.bind((serverIP, updaterPort))
    rjecnik = {"mbo": "143520838", "kategorija": "A", "podrucni": "004", "osnova": "00112", "brojPristupa": "0",
               "errorCode": "0", "updateTime": "14", "vrstaZahtjeva": "2", "izvor": "0"}
    data = 0
    a = []
    while 1:
        con = sqlite3.connect("kategoricar.db")
        cursor = con.cursor()
        cursor.execute("select  mbo  from testTable where kategorija='Null'")
        podatak = cursor.fetchall()
        for y in range(len(podatak)):
            a.append(podatak[y][0])
        if a != "[]":
            while (a != "[]"):
                for x in range(20):
                    rjecnik["mbo"] = a[x]
                    updater_con.sendto(json.dumps(rjecnik), (serverIP, serverPort))
                    data, addr = updater_con.recvfrom(1024)
                    timer(15)
                    if data == "1":  # if there is server problems break and wait better times
                        break
                    if data == "3":  # if there is error with mbo try 3 more times, if there is everytime every delete it from database
                        for y in range(2):
                            updater_con.sendto(str(json.dumps(rjecnik)), (serverIP, serverPort))
                            data, addr = updater_con.recvfrom(1024)
                            timer(15)
                            if data == "0":
                                break
                        if data == "1":
                            break
                        if data == "3":
                            cursor.execute("delete from testTable where mbo=:Mbo", {"Mbo": a[x]})
                            con.commit()

                    data = 0
                    del a[x]
                    timer(15)
                if data == "1":
                    break

        if data != "1":
            cursor.execute(
                "select mbo  from testTable where julianday('now') - julianday(zadnjiUpdate)>30 and kategorija = 'F' or kategorija = 'A' limit 260")
            podatak = cursor.fetchall()
            for y in range(len(podatak)):
                a.append(podatak[y][0])
            if a != "[]":
                while (a != "[]"):
                    for x in range(20):
                        rjecnik["mbo"] = a[x]
                        updater_con.sendto(str(json.dumps(rjecnik)), (serverIP, serverPort))
                        data, addr = updater_con.recvfrom(1024)
                        timer(15)
                        if data == "1":  # if there is server problems break and wait better times
                            break
                        if data == "3":  # if there is error with mbo try 3 more times, if there is everytime error delete it from database
                            for y in range(2):
                                updater_con.sendto(str(json.dumps(rjecnik)), (serverIP, serverPort))
                                data, addr = updater_con.recvfrom(1024)
                                if data == "0":
                                    break
                                timer(15)
                            if data == "1":
                                break
                            if data == "3":
                                cursor.execute("delete from testTable where mbo=:Mbo", {"Mbo": a[x]})
                                con.commit()

                        data = 0
                        del a[x]
                        timer(15)
                    if data == "1":
                        break

        timer(216000)


if __name__ == "__main__":
    while 1:
        #starting server thread
        tekst = str(threading.enumerate())
        if string.find(tekst, "server") == -1:
            cunt = threading.Thread(target=server_thread, name="server")
            cunt.start()


        #starting log thread
        #if string.find(tekst, "log") == -1:
        #    cunt = threading.Thread(target=log_thread, name="log")
        #    cunt.start()

        #starting updater thread
        #if string.find(tekst, "updater") == -1:
        #    cunt = threading.Thread(target=updater_thread, name="updater")
        #    cunt.start()
        timer(30)
#enter code for checks and so on
