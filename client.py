# -*- coding: cp1250 -*-
"""
Napisao Marin Obranovic.

Scripta provjerava i izbacuje kategoriju i podrucni ured osigurane osobe!

"""
import os
from threading import Thread
import pythoncom, pyHook
import string
import mechanize
from bs4 import BeautifulSoup
import datetime
import sqlite3
import socket

# variable ---------------------
prijasnji = ""
title, title1, keys, keylength = '', '', '', 9
url = "http://www.hzzo-net.hr/statos_MBO.htm"
podrucni = "004", "010", "018", "026", "034", "037", "040", "060", "065", "072", "078", "079", "080", "082", "083", "088", "090", "091", "100", "114"
#variable end -----------------------


def screen_show(event_code, mbo, kat=None, pod=None,osn=None, iz=0, update=None):
    izvor =["Internet", "Baza"]
    event_error_url= "Problem sa hzzo-om!! mbo: " + mbo + "\n\n"
    event_error_mbo= "Pogresan MBO!! " + str(mbo)
    event_success = "\n\n\n\n\nTrazeni MBO:    | " + str(mbo) + "\n\nKategorija:	| " + str(kat) + "\n\nPodrucni:	| " + str(pod) + "\n\n\n\n\n\nOsnova:         | " + str(osn) + "\n\nIzvor:          | " + izvor[iz]+ "\n\nzadnji update:	| " + str(update)
    event_error_opcenito ="""MBO problem ?? \n\n\n\nvrijeme: """ + str(datetime.datetime.now())+ """
                            \n\nMBO nije tocan ili nema osiguranje... Provjeriti jos jednom MBO
                            \n\n{{{  """ + str(mbo) + """   }}}}"""
    event_dic = {"1":event_error_url, "2":event_error_mbo, "3":event_success, "4":event_error_opcenito}
    print event_dic[event_code]

def obrada(value, mbo):
    os.system("cls")
    if(len(value[0])==1):
        screen_show(value[0], mbo)
    elif(len(value[0])>1):
        podatak = string.split(value[0], "@")
        screen_show(podatak[0], podatak[1], podatak[2], podatak[3], podatak[4], int(podatak[5]), podatak[6])

def client_za_podatke(value):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.sendto(str(value), ("192.168.1.131", 8666))
    data = conn.recvfrom(200)
    conn.close()
    obrada(data, value)



def keys_collecting(event):
    global title, title1, keys, keylength, prijasnji
    try:
        title = event.WindowName
        keys = keys + chr(event.Ascii)
        keys = keys.replace('', '[BS]')
        keys = keys.replace(' ?', '?')
        if(keys[len(keys)-1]=="q"):
            t = Thread(target=client_za_podatke, args=("00"+prijasnji,))
            t.start()
            keys = keys[0:len(keys)-1]
        #for ured in podrucni :
        #    if ured == keys:
        #        keys = ""
        if unicode(keys).isnumeric() == False:
            keys = ""
        if len(keys) == keylength:
            prijasnji = keys
            t = Thread(target=client_za_podatke, args=(keys,))
            t.start()
            keys, title, title1 = '', '', ''
        return True
    except Exception as inst:
        keys = ""
        print(inst)
        return True





hm = pyHook.HookManager()
hm.KeyDown = keys_collecting
hm.HookKeyboard()
pythoncom.PumpMessages()
