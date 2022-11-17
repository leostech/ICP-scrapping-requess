import codecs
import configparser
import sys
import threading
from requests.adapters import Retry, HTTPAdapter
import playsound
from Requester import Requester2
from anticaptchaofficial.recaptchav3proxyless import *


def read_proxies(PATH):
    global proxies
    proxies = []
    with open(PATH, "r") as file:
        lines = file.readlines()
        for line in lines:
            split = line.replace("\n", "").split(":")
            proxies.append({'https': f"http://{split[2]}:{split[3]}@{split[0]}:{split[1]}/"})
    global proxy_quantity
    proxy_quantity = len(proxies)


def read_conf(section, key, config):
    try:
        return config[section][key]
    except:
        return None


def read_mails(PATH):
    if not config_mailed:
        with open(PATH, "r") as file:
            mails = file.readlines()
        global mail_quantity
        mail_quantity = len(mails)
        return mails
    else:
        return [mail]


# Path of mails file
MAIL_PATH = "./mail.txt"
# Path of proxies file
PROXY_PATH = "./proxies.txt"

#API_TELEGRAM = "5728961320:AAFXRnj9Sz5HHyucbrn61HxWvON8yVDypH4" # demobot
#chat_id = 870418576 # demobot

config = configparser.ConfigParser()
config.read_file(codecs.open("config.ini", "r", "utf8"))
proxy_counter = 1
mail_counter = 1
read_proxies(PROXY_PATH)
city = read_conf('INFO', 'PROVINCIAS', config)
document_type = read_conf('INFO', 'TIPO_DOCUMENTO', config)
document_data = read_conf('INFO', 'DOCUMENTO_DATA', config)
document_person = read_conf('INFO', 'DOCUMENTO_PERSON', config)
residence_end_date = read_conf('INFO', 'END_DATE_RESIDENCE', config)
motivo = read_conf('INFO', 'OBSERVACIONES', config)
phone = read_conf('INFO', 'TELEFON', config)
office = read_conf('INFO', 'POLICIA_RECOGIDA_SEDE_ID', config)
nation_id = read_conf('INFO', 'NATION value id', config)
dob = read_conf('INFO', 'DATE_OF_BIRTH', config)
mail = read_conf('INFO', 'E-MAIL', config)
frequency = read_conf('INFO', 'FREQUENCY', config)
tramite_0 = -1 if read_conf('INFO', 'tramite[0]', config) == '' or read_conf('INFO', 'tramite[0]', config) is None else read_conf('INFO', 'tramite[0]', config)
tramite_1 = -1 if read_conf('INFO', 'tramite[1]', config) == '' or read_conf('INFO', 'tramite[1]', config) is None else read_conf('INFO', 'tramite[1]', config)

if mail is not None and mail != '':
    config_mailed = True
else:
    config_mailed = False
mails = read_mails(MAIL_PATH)

data = {'city': city, 'document_type': document_type, 'document_person': document_person,
        'document_data': document_data, 'residence_end_date': residence_end_date,
        'phone': phone, 'nation_id': nation_id, 'dob': dob, 'mail': mails[0],
        'tramite_0': tramite_0, 'tramite_1': tramite_1, 'proxy': proxies[0],
        'office': office, 'motivo': motivo, 'frequency': frequency}

rs = Requester2(data, proxies, mails)
#raise Exception('ok')
booked = False
while not booked:
    if getattr(rs, 'phone', None) and not rs.config_phoned:
        #clear previous used number
        rs.cancel_number(rs.phone['id'])

    result = rs.drive()
    if result == "SESSION_EXPIRED" or result == "CHANGE_PROXY" or result == "ERROR" or result is None:
        print("changing the proxy ({})".format(result))
        rs.data['proxy'] = proxies[proxy_counter]
        
        rs.init_session()
        
        proxy_counter = 0 if proxy_counter == proxy_quantity-1 else proxy_counter + 1
        if not config_mailed:
            print("changing the mail")
            rs.data['mail'] = mails[mail_counter]
            mail_counter = 0 if mail_counter == mail_quantity - 1 else mail_counter + 1
    elif result is not None:
        print("Booking")
        if rs.book(result['response'], result['TABLE_PAGE']):
            print("BOOKED")
            threading.Thread(target=playsound.playsound, args=["./alarm.wav"]).start()
            tramit = tramite_1 if tramite_1 != -1 else tramite_0
            text = "There is an available visit on %s -- %s\n%s\n%s\n%s\n%s\n%s" % (rs.data['city'], tramit, rs.data['code'], rs.data['document_person'],
                                                                                rs.phone['number'], rs.data['date'], rs.data['time'])
            rs.send_telegram_message(text)
            print(rs.data['document_person'])
            booked = True
            sys.exit()
            #break
        print("Couldn't book. Trying Again.")
        