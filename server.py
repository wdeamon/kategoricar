# -*- coding: cp1250 -*-
import socket
from threading import Thread
import sqlite3
from bs4 import BeautifulSoup
import datetime
import os
import mechanize
import string


#################################
##konfiguracija
#################################
url = "http://www.hzzo-net.hr/statos_MBO.htm"
serverIP = "192.168.1.131"
port = 8666
#################################

def dataObrada(mbo, kategorija, osnova, podrucni):
    try:
        con = sqlite3.connect("kategoricar.db")
        cursor = con.cursor()
        cursor.execute("select kategorija, mbo, counter from testTable where mbo = :Mbo ", {"Mbo":str(mbo)})
        podaci = cursor.fetchall()
        if (podaci != []):
            cursor.execute("update testTable set counter = :Counter where mbo= :Mbo ", {"Mbo":str(mbo), "Counter":podaci[0][2]+1})
            con.commit()
        else:
    #provjera na netu
            cursor.execute("insert into testTable values(?,?,?,?,?,?)", (mbo, kategorija, datetime.datetime.now(), 0, osnova, podrucni))
            con.commit()
        con.close()
    except:
          pass

def scraping(html, uneseni_mbo):
    global keys
    try:
            soup = BeautifulSoup(html)
            text = soup.get_text()
            text = unicode(string.strip(text))
            if not string.find(text, "Nema podataka") == -1:
                    return 2
                    keys= ""
            else:
                    kategorija = text[string.find(text,"Osnova:")-2:string.find(text,"Osnova:")]
                    kategorija = kategorija[1]
                    text=string.strip(text)
                    osnova = text[string.find(text,"Osnova:")+10:string.find(text,"Osnova:")+15]
                    podrucni = string.split(text, "DOPUNSKO OSIGURANJE")
                    podrucni = podrucni[0][len(podrucni[0])-6:len(podrucni[0])]
                    podrucni = string.strip(podrucni)
                    if len(podrucni) == 1:
                        podrucni = "00" + podrucni
                    elif len(podrucni) == 2:
                	podrucni = "0" + podrucni
                    dataObrada(uneseni_mbo, kategorija, osnova, podrucni)
                    data = str("@"+ uneseni_mbo + "@" + kategorija + "@" + podrucni + "@" + osnova + "@" + str(0) + "@" + str(datetime.datetime.now()))
                    return "3"+data
    except:
		return 4




def Ubazi(mbo):
    con = sqlite3.connect("kategoricar.db")
    cursor = con.cursor()
    cursor.execute("select mbo, kategorija from testTable where mbo = :Mbo", {"Mbo":mbo})
    data = cursor.fetchone()
    try:
        if(data == "[]" or data[1]== "Null"):
            return True
    except:
        return True
    return False

def destilator(poruka):
	global url
	try:
            if (len(poruka)==11):
                poruka = poruka[2:11]
                br = mechanize.Browser()
                br.set_handle_robots(False) # ignore robots
                br.open(url, timeout=8.0)
                br.select_form(name="isktr")
                br["upmbo"] = poruka
                br["answer"]="11111"
                res = br.submit()
                content = res.read()
                podatak = scraping(content, poruka)
                br.close()
                if len(str(podatak))==1:
                    return podatak
                podatak1= string.split(podatak, "@")
                con = sqlite3.connect("kategoricar.db")
                cursor = con.cursor()
                cursor.execute("update testTable set kategorija=:Kate, podrucni=:Pon, osnova=:Osn, zadnjiUpdate=:Up where mbo= :Mbo ", {"Mbo":str(poruka), "Kate":podatak1[2], "Pon":podatak1[3], "Osn":podatak1[4], "Up":podatak1[6]})
                con.commit()
                return podatak
            elif(Ubazi(poruka) ):
                br = mechanize.Browser()
                br.set_handle_robots(False) # ignore robots
                br.open(url, timeout=8.0)
                br.select_form(name="isktr")
                br["upmbo"] = poruka
                br["answer"]="11111"
                res = br.submit()
                content = res.read()
                podatak = scraping(content, poruka)
                br.close()
                return podatak
            else:
                con = sqlite3.connect("kategoricar.db")
                cursor = con.cursor()
                cursor.execute("select kategorija, podrucni, osnova, zadnjiUpdate from testTable where mbo = :Mbo", {"Mbo":poruka})
                data = cursor.fetchone()
                data = str("@"+ poruka + "@" + data[0] + "@" + data[1] + "@" + data[2] + "@" + str(1) + "@" + data[3])
                return "3"+data

	except Exception as inst:
            dataObrada(poruka, "Null", "Null", "Null")
            print("Pogreska na serveru! MBO:" + poruka)
            return 1



def slanje(conn,addr, data):
	conn.sendto(str(destilator(data)), addr)


if __name__ == "__main__":
	conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	conn.bind((serverIP, port))
	while True:
		data, addr = conn.recvfrom(1024)
		print("Podaci(" + data + ") primljeni! IP:" + str(addr))
		t = Thread(target=slanje, args=(conn, addr, data))
		t.start()
	conn.close()
