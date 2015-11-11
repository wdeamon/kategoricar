# -*- coding: cp1250 -*-
"""
Napisao Marin Obranovic.

Scripta provjerava i izbacuje kategoriju i podrucni ured osigurane osobe!

"""
import os
from threading import Thread
import string
import datetime
import socket
import json

import pythoncom
import pyHook


# variable ---------------------
ServerPort = 8666
ServerIP = "localhost"
prijasnji = ""
title, title1, keys, keylength = '', '', '', 9
url = "http://www.hzzo-net.hr/statos_MBO.htm"
podrucni = "004", "010", "018", "026", "034", "037", "040", "060", "065", "072", "078", "079", "080", "082", "083", "088", "090", "091", "100", "114"
rjecnik = {"mbo": "11111111", "kategorija": "0", "podrucni": "0", "osnova": "0", "brojPristupa": "0", "errorCode": "0",
           "updateTime": "0", "vrstaZahtjeva": "1", "izvor": "0"}
# variable end -----------------------


def screen_show(event_code, data):
    izvor = ["Baza", "Internet"]
    event_error_url = "Problem sa hzzo-om!! mbo: " + data["mbo"] + "\n\n"
    event_error_mbo = "Pogresan MBO/ nema osiguranje!! " + data["mbo"]
    event_success = "\n\n\n\n\nTrazeni MBO:    | " + data["mbo"] + "\n\nKategorija:	| " + data[
        "kategorija"] + "\n\nPodrucni:	| " + data["podrucni"] + "\n\n\n\n\n\nOsnova:         | " + data[
                        "osnova"] + "\n\nIzvor:          | " + izvor[int(data["izvor"])] + "\n\nzadnji update:	| " + data["updateTime"]
    event_error_opcenito = """MBO problem ?? \n\n\n\nvrijeme: """ + str(datetime.datetime.now()) + """
                            \n\nMBO nije tocan ili nema osiguranje... Provjeriti jos jednom MBO
                            \n\n{{{  """ + str(data["mbo"]) + """   }}}}"""
    event_dic = {"1": event_error_url, "3": event_error_mbo, "0": event_success, "2": event_error_opcenito}
    print event_dic[event_code]


def obrada(value):
    os.system("cls")
    # ErrorCodes
    #now every time we will have at least some data ... so we need to be careful

    if (len(value["errorCode"]) != "0"):
        screen_show(value["errorCode"], value)
    elif (value["errorCode"] == "0"):
        screen_show("0", value)


def client_za_podatke(value):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.sendto(json.dumps(value), (ServerIP, ServerPort))
    data,addr = conn.recvfrom(2048)
    conn.close()
    obrada(json.loads(data))


def keys_collecting(event):
    global title, title1, keys, keylength, prijasnji, rjecnik
    try:
        title = event.WindowName
        keys = keys + chr(event.Ascii)
        keys = keys.replace('', '[BS]')
        keys = keys.replace(' ?', '?')
        if (keys[len(keys) - 1] == "q"):
            rjecnik["vrstaZahtjeva"] = "1"
            rjecnik["mbo"] = prijasnji
            t = Thread(target=client_za_podatke, args=(json.dumps(rjecnik),))
            t.start()
            keys = keys[0:len(keys) - 1]
    #for ured in podrucni :
    #    if ured == keys:
    #        keys = ""
        if unicode(keys).isnumeric() == False:
            keys = ""
        if len(keys) == keylength:
            prijasnji = keys
            rjecnik["mbo"] = keys
            rjecnik["vrstaZahtjeva"] = "0"
            t = Thread(target=client_za_podatke, args=(json.dumps(rjecnik),))
            t.start()
            keys, title, title1 = '', '', ''
        return True
    except Exception as inst:
        keys = ""
        print(inst)
        return True

#1. greska servera
#2. pogreska u podacima
#3. krivi mbo/ nema podataka
#0. nema greske
#
#0. normalni zahtjev
#1. kompletna provjera
#2. update
hm = pyHook.HookManager()
hm.KeyDown = keys_collecting
hm.HookKeyboard()
pythoncom.PumpMessages()
