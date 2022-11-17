from datetime import datetime
import json
import base64
import io
import os
import random
import sys
import threading
import asyncio
import time
from PIL import Image
from anticaptchaofficial.recaptchav3proxyless import recaptchaV3Proxyless
import capmonstercloudclient
from capmonstercloudclient.requests import ImageToTextRequest
from capmonstercloudclient import CapMonsterClient, ClientOptions
import traceback
import requests
import urllib3
import telegram
from bs4 import BeautifulSoup
import logging
import playsound
from requests.adapters import Retry, HTTPAdapter
from requests.auth import HTTPProxyAuth
from smsactivate import SmsActivate

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
logger = logging.getLogger("my_logger")
handler = logging.FileHandler("logs.log", encoding="utf-8")
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s : \n************\n %(message)s\n**********\n')
handler.setFormatter(formatter)
logger.addHandler(handler)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
base_url = "https://icp.administracionelectronica.gob.es/"
API_SMSACTIVATE = '55bAe70cfdfe4b973A22767b83ddb6bf'
API_CAPMONSTER = "b7a01275c66483da242ab99fd85b6bfb"
API_ANTIGATE = "efd9ecc5500bea27960da5e89e7fe9cc"
API_TELEGRAM = "1210117443:AAG4x2MuE8ecu5SsAmpcg0EyyxUJaIMt5F4" # bot
#Chat ID For Telegram
chat_id = "-343257230" # bot

SMSA = SmsActivate(API_SMSACTIVATE)

class Requester2:
    
    def init_session(self):
        #print('new session with proxies')
        self.session = requests.Session()
        self.session.headers.clear()
        retry = Retry(total=5, backoff_factor=1)
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.update_proxy()
        self.update_email()

    def update_proxy(self):
        self.proxyNum = self.proxyNum + 1 if self.proxyNum+1 < len(self.proxies) else 0
        self.data['proxy'] = self.proxies[self.proxyNum]
        self.session.proxies.update(self.data['proxy'])
        #print(self.data['proxy']['https'])

    def update_email(self, ):
        self.emailNum = random.randint(0, len(self.emailsList) - 1)
        self.data['mail'] = self.emailsList[self.emailNum]

    def __init__(self, data, _proxies, _emails):
        self.data = data
        self.keyword = None
        self.userNum = random.randint(0, len(UAGENTS)-1)
        self.proxyNum = 0
        self.proxies = _proxies
        self.emailNum = 0
        self.emailsList = _emails

        self.init_session()
        
        self.data['city_id'], self.data['city_url'] = self.get_city_id()
        if self.data['phone'] is not None and self.data['phone'] != '':
            self.config_phoned = True
        else:
            self.config_phoned = False

    def sessreq(self, *args, **kwargs):
        url = kwargs.get('url') or args[1]
        #print('TO URL {}'.format(url))
        try:
            r = self.session.request(*args, **kwargs)
        except:
            time.sleep(3)
            r = self.session.request(*args, **kwargs)
        if '<html><head><title>Request Rejected</title></head><body>The requested URL was rejected. Please consult with your administrator.' in r.text:
            raise Exception('Request Rejected on {}'.format(url))
        if 'Se ha producido un error en el sistema' in r.text:
            raise Exception('Se ha producido un error en el sistema on {}'.format(url))
        #if 'En este momento no hay citas disponibles' in r.text:
            #raise Exception('En este momento no hay citas disponibles on {}'.format(url))
        return r
            
    def get_city_id(self):
        url = base_url + "icpplus/index.html"
        headers = get_headers('index', self.session, self.userNum, cookify=False)
        var = {
            'User-Agent': 'Chrome',
        }
        response = self.sessreq("GET", headers=headers, url=url, verify=False,
                                        timeout=30)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        options = soup.find("select").find_all("option")
        for i in range(1, len(options)):
            city = options[i].text
            id = options[i]['value'].split("=")[1].split("&")[0]
            url = options[i]['value']
            if city == self.data['city']:
                return id, url

    # Returns portadaForm fields and tramite selection
    def query_city(self, city_url):
        url = '{}/{}'.format(base_url, city_url
                            )
        headers = get_headers('citar', self.session, self.userNum, cookify=False)
        
        response = self.sessreq("GET", url=url, headers=headers, verify=False, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")
        portada_inputs = soup.find("form", attrs={'id': "portadaForm"}).find_all("input")
        portada = {}
        for portada_input in portada_inputs:
            if portada_input['type'] == "hidden" and portada_input['value'] and portada_input['value'] != "":
                portada['key1'] = portada_input['name']
                portada['value1'] = portada_input['value']
            elif portada_input['type'] == "hidden":
                portada['key2'] = portada_input['name']
        
        self.keyword = city_url.split('/')[1]
        
        return {'portada': portada, 'url': url}


    def acInfo(self, key1, value1, key2, referer):
        url = base_url + f"{self.keyword}/acInfo"
        payload = f'{key2}=&{key1}={value1}&sede=99&tramiteGrupo%5B0%5D={self.data["tramite_0"]}&tramiteGrupo%5B1%5D={self.data["tramite_1"]}'
        headers = get_headers('acInfo', self.session, self.userNum,)
        headers['Referer'] = referer
        response = self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")
        inputs = soup.find_all("input")
        hiddens = {}
        for input in inputs:
            if input['type'] == 'button' and input['id'] == "btnEntrar":
                hidden_inputs = soup.find("form", attrs={'name': 'info', 'action': 'acEntrada'}).find_all("input",
                                                                                                          attrs={
                                                                                                              'type': 'hidden'})
                for hidden_input in hidden_inputs:
                    if hidden_input['value'] and hidden_input['value'] != '':
                        hiddens['key1'] = hidden_input['name']
                        hiddens['value1'] = hidden_input['value']
                    else:
                        hiddens['key2'] = hidden_input['name']
                return self.skip_entrance(hiddens['key1'], hiddens['key2'], hiddens['value1'])
        return response

    # Called By self.acInfo
    def skip_entrance(self, key1, key2, value1):
        url = base_url + f"{self.keyword}/acEntrada"
        payload = f'{key2}=&{key1}={value1}'
        headers = get_headers('acEntrada', self.session, self.userNum)
        response = self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
        return response

    def send_telegram_message(self, message):
        bot = telegram.Bot(API_TELEGRAM)
        bot.send_message(text=message, chat_id=chat_id)
        del bot

    def login(self, key1, key2, value1, nation_required, birth_date_required, end_date_required):
        url = base_url + f"{self.keyword}/acValidarEntrada"
        payload = {
            key2: '',
            key1: value1,
            'rdbTipoDoc': self.data['document_type'],
            'txtIdCitado': self.data['document_data'],
            'txtDesCitado': self.data['document_person']}
        headers = get_headers('acValidarEntrada', self.session, self.userNum)
        {
            'User-Agent': 'Chrome',
            'Referer': base_url + "acEntrada"
        }
        payload['txtPaisNac'] = self.data['nation_id'] if nation_required else None
        payload['txtAnnoCitado'] = self.data['dob'] if birth_date_required else None
        payload['txtFecha'] = self.data['residence_end_date'] if end_date_required else None
        response = self.sessreq("POST", url, headers=headers, data=self.filter_none(payload), verify=False,
                                        timeout=30)
        return response

    def filter_none(self, d):
        return {k:v for k,v in d.items() if v is not None}

    def demand_appointment(self, key1, key2, value1):
        url = base_url + f"{self.keyword}/acCitar"
        payload = f'{key2}=&{key1}={value1}'
        headers = get_headers('acCitar', self.session, self.userNum)
        response = self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
        return response

    def select_office(self, key1, key2, value1, idSede):
        time.sleep(1)
        url = base_url + f"{self.keyword}/acVerFormulario"
        payload = f'{key1}={value1}&{key2}=&idSede={idSede}'
        headers = get_headers('acVerFormulario', self.session, self.userNum)
        response = self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
        return response

    def _get_hidden_pl(self, r_text, soup_form_filter, first=False):
        '''soup_form_filter dict like {'name' : 'procedimientos'}'''
        soup = BeautifulSoup(r_text, 'html.parser')
        elems = soup.find('form', soup_form_filter).find_all('input', {'type' : 'hidden'})
        if first:
            elems = elems[:first]
        payload = {elem['name'] : elem['value'] for elem in elems if elem.get('name')}
        #return payload
        for k,v in payload.items():
            if v == '':
                key2 = k
            else:
                key1=k
                value1=v
        return key1, key2, value1    

    def get_phone(self):
        if self.config_phoned:
            return {'id': 1, 'number': self.data['phone']}
        else:
            print('getting phone')
            r = SMSA.get_number(country=56, service='ot')
            SMSA.set_status(1, r[0])
            print('phone is {}'.format(r[1][2:]))
            return {'id' : r[0], 'number' : r[1][2:]}

    @staticmethod
    def get_sms(smsa_mobile_id):
        while True:
            msg = SMSA.get_status(smsa_mobile_id)
            if 'STATUS_OK' in msg:
                code = msg.split('DEBE INTRODUCIR EL CODIGO ')[1][:5]
                return int(code)
            time.sleep(1)

    @staticmethod
    def cancel_number(smsa_mobile_id):
        print("discarding phone number")
        if smsa_mobile_id not in [None, 1]:
            SMSA.set_status(8, smsa_mobile_id)     


    def see_appointments(self, key1, key2, value1, phone, mail, motivo_required):
        url = base_url + f"{self.keyword}/acOfertarCita"
        payload = f'{key1}={value1}&{key2}=&txtTelefonoCitado={phone}&txtMailCitado={mail}&emailDOS={mail}'
        headers = get_headers('acOfertarCita', self.session, self.userNum)
        if motivo_required:
            payload += f'&txtObservaciones={self.data["motivo"]}'
        #print(payload)    
        response = self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
        return response

    def reload(self, key1, key2, value1):
        url = base_url + f"{self.keyword}/acOfertarCita"

        payload = f'{key1}={value1}&{key2}=&txtHora=00%3A00&vista=&recargarCaptcha=&txtCaptcha='
        headers = get_headers('acOfertarCita', self.session, self.userNum)
        response = self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
        return response

    def verificate(self, key1, key2, value1, recaptcha, captcha, hora, cita_id):
        url = base_url + f"{self.keyword}/acVerificarCita"
        #print(self, key1, key2, value1, recaptcha, captcha, hora, cita_id)
        payload = f'{key2}=&{key1}={value1}&rdbCita={cita_id}&txtHora={hora}&vista=&reCAPTCHA_site_key={recaptcha["site-key"]}' \
                  f'&action={recaptcha["action"]}&g-recaptcha-response={recaptcha["response"]}&txtCaptcha={captcha}'
        headers = get_headers('acVerificarCita', self.session, self.userNum)
        #print(payload)
        response = self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
        return response

    def check_ip(self):
        url = 'https://ifconfig.me/all.json'
        response = self.sessreq("GET", url)
        print(f'You real IP: {response.text}')

    def drive(self):

        response = ""
        sentences = ["En este momento no hay citas disponibles.",
                     "Lo sentimos, pero usted ha superado"]
        while True:
            time.sleep(5)
            self.init_session()
            print(self.data['proxy']['https'])
            print(self.data['mail'])

            self.check_ip()

            print(self.session.proxies)
            
            try:
                print("Querying the city")
                info = self.query_city(self.data['city_url'])
                time.sleep(random.uniform(0.3, 2))
                response = self.acInfo(info['portada']['key1'], info['portada']['value1'], info['portada']['key2'], info['url'])                  
                soup = BeautifulSoup(response.text, "html.parser")
                nation_required = bool(soup.find("select", attrs={'id': 'txtPaisNac'}))
                dob_required = bool(soup.find("input", attrs={'id': 'txtAnnoCitado'}))
                residence_required = bool(soup.find("input", attrs={'id': 'txtFecha'}))

                if 'Se ha producido un error inesperado.' in response.text:
                    print('Se ha producido un error inesperado.')

                #key1, key2, value1 = self.find_inputs(soup.find("form", attrs={'id': 'citadoForm'}))
                key1, key2, value1 = self._get_hidden_pl(response.text, {'id' : 'citadoForm'}, first=2)

                print("Logging in")
                time.sleep(random.uniform(0.3, 2))
                response = self.login(key1, key2, value1, nation_required, dob_required, residence_required)
                soup = BeautifulSoup(response.text, "html.parser")
                #key1, key2, value1 = self.find_inputs(form)
                key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'procedimientos'})

                print("Demanding Appointment")
                time.sleep(random.uniform(0.3, 2))
                response = self.demand_appointment(key1, key2, value1)
                soup = BeautifulSoup(response.text, "html.parser")
                #form = soup.find("form", attrs={'name': 'procedimientos'})
                #print(response.text)

                if sentences[1] in response.text:
                    print("Person Already Have Visit")
                    self.send_telegram_message(
                        f"{self.data['document_data']} {self.data['document_person']} Already Have Visit")

                    os._exit(1)
                elif not sentences[0] in response.text:
                    try:
                        #key1, key2, value1 = self.find_inputs(form)
                        key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'procedimientos'})
                        if self.data['office'] not in [None, '']:
                            idSede = self.data['office']
                        else:
                            opts = soup.find("select", attrs={'id': 'idSede'}).find_all(
                                lambda elem: elem.name == 'option' and 'Seleccionar' not in elem.text
                            )
                            idSede = opts[random.randint(0, len(opts)-1)]['value']

                        print("Selecting Office")
                        time.sleep(random.uniform(0.3, 2))
                        response = self.select_office(key1, key2, value1, idSede)

                        if sentences[1] in response.text:
                            print("Person Already Have Visit")
                            self.send_telegram_message(
                                f"{self.data['document_data']} {self.data['document_person']} Already Have Visit")

                            os._exit(1)

                        if sentences[0] not in response.text:
                            soup = BeautifulSoup(response.text, "html.parser")
                            try:
                                #form = soup.find("form", attrs={'name': 'procedimientos'})
                                #key1, key2, value1 = self.find_inputs(form)
                                key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'procedimientos'}, first=2)
                            except:
                                print('except')
                                #key1, key2, value1 = self.find_inputs(soup.find("form", attrs={'name': 'info'})) ?
                                key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'info'})

                            print("Listing Appointments.")
                            motivo_required = bool(soup.find("textarea", attrs={'id': "txtObservaciones"}))
                            self.phone = self.get_phone()
                            self.generate_captcha()
                            time.sleep(random.uniform(0.3, 2))
                            response = self.see_appointments(key1, key2, value1, self.phone['number'], self.data['mail'],
                                                             motivo_required)
                            soup = BeautifulSoup(response.text, "html.parser")
                            if sentences[1] in response.text:
                                print("Person Already Have Visit")
                                self.send_telegram_message(f"{self.data['document_data']} {self.data['document_person']} Already Have Visit")
                                self.cancel_number(self.phone['id'])
                                os._exit(1)
                            if sentences[0] not in soup.text:
                                form = soup.find("form", attrs={'name': 'procedimientos'})
                                key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'procedimientos'}, first=2)

                                slots = form.select('div[id*="cita_"]')
                                table = form.find("table", attrs={'id': 'VistaMapa_Datatable'})
                                if table and "LIBRE" in table.text:
                                    logger.error(response.text)
                                    return {'response': response, 'TABLE_PAGE': True}
                                if len(slots) == 0:
                                    continue
                                logger.error(response.text)
                                return {'response': response, 'TABLE_PAGE': False}
                            else:
                                self.cancel_number(self.phone['id'])
                                #logger.error(form.text.strip())
                                time.sleep(float(self.data['frequency']))
                                print("Not available Visits")
                                return "CHANGE_PROXY"
                        else:
                            #logger.error(form.text.strip())
                            time.sleep(float(self.data['frequency']))
                            print("Not available Visits")
                            return "CHANGE_PROXY"
                    except KeyboardInterrupt:
                        print("Bye")
                        os._exit(1)
                    except:
                        print(traceback.print_exc())
                        try:
                            if "sesión" in response.text:
                                print("Session expired or IP banned")
                                return "SESSION_EXPIRED"
                            elif "in a given amount of time." in response.text:
                                print("BANNED")
                                return "SESSION_EXPIRED"
                        except KeyboardInterrupt:
                            print("Bye")
                            os._exit(1)
                        except:
                            print(traceback.print_exc())
                            print("ERROR")
                            return "ERROR"
                        break
                else:
                    print("En este momento no hay citas disponibles.")
                    logger.error(soup.find("form", attrs={'name': 'procedimientos'}).text.strip())
                    time.sleep(float(self.data['frequency']))
                    if getattr(self, 'phone', None) and not self.config_phoned:
                        self.cancel_number(self.phone['id'])

            except KeyboardInterrupt:
                print("Bye")
                os._exit(1)
            except:
                try:
                    if "sesión" in response.text:
                        print("Session expired or IP banned ({})".format(len(response.text)))
                        return "SESSION_EXPIRED"
                    elif "in a given amount of time." in response.text:
                        print("BANNED ({})".format(len(response.text)))
                        return "SESSION_EXPIRED"
                except KeyboardInterrupt:
                    print("Bye")
                    os._exit(1)
                except Exception as e:
                    print("ERROR")
                    return "ERROR"
                finally:
                    print(traceback.print_exc())
                break

    def verificar_table_paged(self, key1, key2, value1, cita_id, recaptcha, captcha):
        url = base_url + f"{self.keyword}/acVerificarCita"
        payload = f'{key1}={value1}&{key2}=&txtIdCita={cita_id}&reCAPTCHA_site_key={recaptcha["site-key"]}&action={recaptcha["action"]}&g-recaptcha-response={recaptcha["response"]}&txtCaptcha={captcha}'
        headers = get_headers('acVerificarCita', self.session, self.userNum)
        return self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)

    def book_table_paged(self, _response):
        r = _response
        try:
            soup = BeautifulSoup(_response.text, "html.parser")
            form = soup.find("form", attrs={'name': 'procedimientos'})
            #key1, key2, value1 = self self.find_inputs(form)
            key1, key2, value1 = self._get_hidden_pl(_response.text, {'name': 'procedimientos'}, first=2)
            btns = form.find("table", attrs={'id': 'VistaMapa_Datatable'}).find_all("a", attrs={'role': 'button'})
            libre_btns = [btn for btn in btns if "LIBRE"==btn.text]
            index = random.randint(0, len(libre_btns)-1)
            btn_id = libre_btns[index]['id'].split("O")[1]
            try:
                captcha_image = soup.find("img", attrs={'alt': 'captcha'})['src']
                print("Solving Captcha")
                captcha_answer = self.captcha_solver(captcha_image)
            except Exception as e:
                captcha_answer = ''
            try:
                recaptcha_site_key = soup.find("input", attrs={'id': 'reCAPTCHA_site_key'})['value']
                if recaptcha_site_key == None:
                    return self.book_table_paged(self, _response)
                action = soup.find("input", attrs={'id': 'action'})['value']
                print("Solving Recaptcha v3")
                #recaptcha_answer = self.solve_recaptcha(recaptcha_site_key, action)
                recaptcha_answer = self.solve_recapthcaV3_capmonster(recaptcha_site_key, action)
                recaptcha = {'site-key': recaptcha_site_key, 'action': action, 'response': recaptcha_answer}
            except Exception as e:
                recaptcha_answer = ''
                recaptcha = {'site-key': '', 'action': '', 'response': recaptcha_answer}
            response = self.verificar_table_paged(key1, key2, value1, btn_id, recaptcha, captcha_answer)
            soup = BeautifulSoup(response.text, "html.parser")
            form = soup.find("form", attrs={'name': 'procedimientos'})
            #key1, key2, value1 = self.find_inputs(form)


            key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'procedimientos'}, first=2)



            sms_input = soup.find("input", attrs={'id': 'txtCodigoVerificacion'})
            if sms_input is not None:
                if not self.config_phoned:
                    print("Waiting for SMS")
                    self.send_telegram_message("Waiting for the sms.")
                    sms = self.get_sms(self.phone['id'])
                    print("Got the SMS")
                    print("Code: ", sms)
                else:
                    threading.Thread(target=playsound.playsound, args=["./alarm.wav"]).start()
                    self.send_telegram_message("Please Enter the SMS Code.")
                    sms = input("Enter the SMS: ")
                response = self.grabar_cita(key1, key2, value1, sms)
            else:
                print("No SMS\nConfirming")
                response = self.grabar_cita(key1, key2, value1, None)
                if not self.config_phoned:
                    self.cancel_number(self.phone['id'])
            if "Justificante de cita" in response.text:
                soup = BeautifulSoup(response.text, "html.parser")
                form = soup.find("form", attrs={'name': 'procedimientos'})
                self.data['code'] = form.find("span", attrs={"id": "justificanteFinal"}).text
                divs = form.find_all("div", attrs={'class': 'fld'})
                for div in divs:
                    if "CITADO" in div.text:
                        self.data['citado'] = div.find_all_next("span")[1].text
                    elif "Día de la cita" in div.text:
                        self.data['date'] = div.find_all_next("span")[1].text
                    elif "Hora cita" in div.text:
                        self.data['time'] = div.find_all_next("span")[1].text
                return True
            else:
                return False
        except:
            print(traceback.print_exc())
            return False

    def book(self, response, table_paged):
        if table_paged:
            return self.book_table_paged(response)
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            form = soup.find("form", attrs={'name': 'procedimientos'})
            #key1, key2, value1 = self.find_inputs(form)
            key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'procedimientos'}, first=2)

            citas = form.find("div", attrs={'class': 'mf-layout--row'}).find_all("div")
            cita_index = random.randint(0, len(citas) - 1)
            cita = citas[cita_index]
            cita_hora = cita.find_all("span")[-1].text.replace(":", "%3A")
            cita_id = cita_index + 1
            try:
                captcha_image = soup.find("img", attrs={'alt': 'captcha'})['src']
                print("Solving Captcha book")
                captcha_answer = self.captcha_solver(captcha_image)
            except Exception as e:
                captcha_answer = ''
            try:
                recaptcha_site_key = soup.find("input", attrs={'id': 'reCAPTCHA_site_key'})['value']
                action = soup.find("input", attrs={'id': 'action'})['value']
                print("Solving Recaptcha v3 book")
                #recaptcha_answer = self.solve_recaptcha(recaptcha_site_key, action)
                recaptcha_answer = self.solve_recapthcaV3_capmonster(recaptcha_site_key, action)
                recaptcha = {'site-key': recaptcha_site_key, 'action': action, 'response': recaptcha_answer}
            except:
                recaptcha_answer = ''
                recaptcha = {'site-key': '', 'action': '', 'response': recaptcha_answer}
            response = self.verificate(key1, key2, value1, recaptcha, captcha_answer, cita_hora, cita_id)
            soup = BeautifulSoup(response.text, "html.parser")
            form = soup.find("form", attrs={'name': 'procedimientos'})
            key1, key2, value1 = self._get_hidden_pl(response.text, {'name': 'procedimientos'}, first=2)
            sms_input = soup.find("input", attrs={'id': 'txtCodigoVerificacion'})
            if sms_input is not None:
                if not self.config_phoned:
                    print("Waiting for SMS")
                    self.send_telegram_message("Waiting for the SMS")
                    sms = self.get_sms(self.phone['id'])
                    print("Got the SMS")
                    print("Code: ", sms)
                else:
                    threading.Thread(target=playsound.playsound, args=["./alarm.wav"]).start()
                    sms = input("Enter the SMS: ")
                    self.send_telegram_message("Please Enter the SMS Code.")
                response = self.grabar_cita(key1, key2, value1, sms)
            else:
                print("No SMS\nConfirming")
                response = self.grabar_cita(key1, key2, value1, None)
                if not self.config_phoned:
                    self.cancel_number(self.phone['id'])

            if "Justificante de cita" in response.text:
                soup = BeautifulSoup(response.text, "html.parser")
                form = soup.find("form", attrs={'name': 'procedimientos'})
                self.data['code'] = form.find("span", attrs={"id": "justificanteFinal"}).text
                divs = form.find_all("div", attrs={'class': 'fld'})
                for div in divs:
                    if "CITADO" in div.text:
                        self.data['citado'] = div.find_all("span")[1].text
                    elif "Día de la cita" in div.text:
                        self.data['date'] = div.find_all("span")[1].text
                    elif "Hora cita" in div.text:
                        self.data['time'] = div.find_all("span")[1].text
                return True
            else:
                return False
        except:
            print(traceback.print_exc())
            return False

    def captcha_solver(self, img_src):
        b64 = img_src.split("base64,")[1]
        with open("captcha.png", "wb") as file:
            file.write(base64.decodebytes(bytes(b64, encoding="utf8")))
        answer = self.solve_captcha("captcha.png")
        return answer

    def solve_captcha(self, b64):
        try:
            client_options = ClientOptions(api_key=API_CAPMONSTER)
            cap_monster_client = CapMonsterClient(options=client_options)
            with open(b64, "rb") as f:
                by = f.read()
            image = Image.open(io.BytesIO(by))
            pixels = image.load()
            for y in range(image.size[1]):
                for x in range(image.size[0]):
                    if pixels[x, y][3] < 255:
                        pixels[x, y] = (255, 255, 255, 255)
            image = image.resize((201, 50))
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            image_request = ImageToTextRequest(image_bytes=(image_bytes.getvalue()))
            nums = 3
            sync_start = time.time()
            sync_responses = asyncio.run(self.solve_captcha_sync(nums, image_request, cap_monster_client))
            print(f'average execution time sync {1 / ((time.time() - sync_start) / nums):0.2f} '
                  f'resp/sec\nsolution: {sync_responses[0]}')
            return sync_responses[0]['text']
        except requests.exceptions.ReadTimeout as ex:
            print(traceback.print_exc())
            self.solve_captcha(b64)

        except Exception as ex:
            print(traceback.print_exc())

    def solve_recapthcaV3_capmonster(self, site_key, _action):
        try:
            url = "https://icp.administracionelectronica.gob.es/icpplus/acOfertarCita"
            client_options = ClientOptions(api_key=API_CAPMONSTER)
            cap_monster_client = CapMonsterClient(options=client_options)
            recaptcha3request = capmonstercloudclient.requests.RecaptchaV3ProxylessRequest(websiteUrl=url,
                                                                                           websiteKey=site_key,
                                                                                           pageAction=_action,
                                                                                           min_score=0.8)
            sync_start = time.time()
            sync_responses = asyncio.run(self.solve_captcha_sync(3, recaptcha3request, cap_monster_client))

            print(f'average execution time sync {1 / ((time.time() - sync_start) / 3):0.2f} ' \
                  f'resp/sec\nsolution: {sync_responses[0]}')
            return sync_responses
        except:
            return ''

    def solve_recaptcha(self, site_key, action):
        try:
            url = "https://icp.administracionelectronica.gob.es/icpplus/acOfertarCita"
            solver = recaptchaV3Proxyless()
            solver.set_verbose(1)
            solver.set_key(API_ANTIGATE)
            solver.set_website_url(url)
            solver.set_website_key(site_key)
            solver.set_page_action(action)
            solver.set_min_score(0.9)
            return solver.solve_and_return_solution()
        except:
            return ''

    async def solve_captcha_sync(self, num_requests, captchaRequest, cap_monster_client):
        return [await cap_monster_client.solve_captcha(captchaRequest) for _ in range(num_requests)]

    def generate_captcha(self):
        url = "https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfBEb8UAAAAAC3Tj2jbBeAapky_TfXoNbzeBhJN&co" \
              "=aHR0cHM6Ly9pY3AuYWRtaW5pc3RyYWNpb25lbGVjdHJvbmljYS5nb2IuZXM6NDQz&hl=es&v=vP4jQKq0YJFzU6e21-BGy3GP" \
              "&size=invisible"
        headers = {
            'referer': 'https://icp.administracionelectronica.gob.es/',
            'User-Agent': 'Chrome'
        }
        self.sessreq("GET", url, headers=headers)

    def grabar_cita(self, key1, key2, value1, sms):
        url = base_url + f"{self.keyword}/acGrabarCita"

        if sms is not None:
            payload = f'{key1}={value1}&{key2}=&txtCodigoVerificacion={sms}&chkTotal=1&enviarCorreo=on'
        else:
            payload = f'{key1}={value1}&{key2}=&chkTotal=1&enviarCorreo=on'
        headers = get_headers('acGrabarCita', self.session, self.userNum)
        return self.sessreq("POST", url, headers=headers, data=payload, verify=False, timeout=30)
    
UAGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 YaBrowser/21.8.1.468 Yowser/2.5 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0',
    'Mozilla/5.0 (X11; CrOS x86_64 14440.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4807.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14467.0.2022) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4838.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14469.7.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.13 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14455.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4827.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14469.11.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.17 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14436.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4803.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14475.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4840.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14469.3.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.9 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14471.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4840.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14388.37.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.9 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14409.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4829.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14395.0.2021) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4765.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14469.8.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.14 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14484.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4840.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14450.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4817.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14473.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4840.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14324.72.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.91 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14454.0.2022) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4824.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14453.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4816.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14447.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4815.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14477.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4840.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14476.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4840.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14469.8.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.9 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.67.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.67.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.69.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.82 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14695.25.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.22 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.57.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.64 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.89.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.84.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.93 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14469.59.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.91.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.55 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14695.23.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.20 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14695.36.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.36 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.41.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.26 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14695.11.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.6 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.67.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14685.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.4992.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.69.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.82 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14682.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.16 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14695.9.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.5 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14574.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4937.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14388.52.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14716.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5002.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14268.81.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14469.41.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.48 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14388.61.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14695.37.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.37 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.51.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.32 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.92.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.56 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.43.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.54 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14505.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4870.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.16.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.25 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.28.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.44 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14543.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4918.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.11.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.6 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14588.31.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.19 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.13 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14658.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.4975.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14695.25.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5002.0 Safari/537.36'
]
        
HEADERS = {
    'index' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'icp.administracionelectronica.gob.es',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    
    'citar' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'icp.administracionelectronica.gob.es',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acInfo' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        #'Content-Length': '167',
        'Content-Type': 'application/x-www-form-urlencoded',
        #'Cookie': 'JSESSIONID=9107E6E0F073E7FFF3AD31A83309F092.appdmzgal3_19023_icpplus',#; TS01df4168=01a3cd4c04f4faf3f9a6f48a8248c67e67edbf63d8ef6ea425db065e5802fff7c3297ac4efa32bd90ceecefd2879babcd651832876a96e432dccd1f22c9ed3b3001cf68eb9; f5_cspm=1234; dtCookie=v_4_srv_4_sn_2526BE3505DAADE47A4FDF47A9B7D6B3_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666907764393NMC65IHM9M8H0GC9R37MEDKDHUPKL4BO; __utma=129963284.834944477.1666907767.1666907767.1666907767.1; __utmc=129963284; __utmz=129963284.1666907767.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); TS00000000076=083a28b6b8ab2800696e2cb258725c7958fa48ed7a5bcbff4a95bbda6a6700240c8ffa86de2b5c4c28aed942786e4f4a08de9bcd1809d00096bfc3376eb542fc6ae9915aa5f01898e5f5fe563a95bff418f3d459e228b27d5f30ae7c2b7cbab947c962243b15b899dc4fdf3d7f119c6b8853d543bec1bd64f16eb233b6e8a287e035af1dd8f09707a291c35a623164d19a27c27cb89135c6d48ed3673c70e5b45b004405a7b48125bb9e1831f8fb64c5187a97e1a0f958f048916880bf76ef47d8478f0789d868ed43b4896507acc0b2649e5b028d98adbeb706db869e6ca8569b53ff8f7738a1fd5b4a3c315f32e1d3cc419728400820a639aa30f62a37fa578b62b05f4a97c986; TSPD_101_DID=083a28b6b8ab2800696e2cb258725c7958fa48ed7a5bcbff4a95bbda6a6700240c8ffa86de2b5c4c28aed942786e4f4a08de9bcd1806380064d87661f1f609a1216b919cdc3edbc513bd7ddbba3b3851720868ca6948f0bbc6de236ea34b9036fb4dd7ae92071544e3127c569b571477; TSPD_101=083a28b6b8ab28004dd9180b1aed7008c46b53aa2c06bac074c8e292b001badaf9bf8a4811eb4d42dbbf6821b2e5f0890889fcad75051800172a5ecf164b99a772b2ab1b0f4bdd01d9ba1ca193434d91; __utmb=129963284.12.10.1666907767; TSf1e2d148077=083a28b6b8ab28001db77cde3181b5c28f2705cd7aea240ec8f2af852cf85088e6ff7c2af2c700b80ce4519fe8be01cf087c17bbb71720008869a0c180109815d94699046aa7e2b781d59bee7ede29fa7d893c39d450c6a4; TS01629f81=01a3cd4c04743455bcd4048d93e5702a56333923657b650adbe32ddf693cdaf1638e70041c821c3c7802866a7ad37a4b3956f5a342597c69dfa506e2377cd4d3d75e730bc2e0dc40a043a96ed7c01abf182275c14d4c9b406d0898d3b0324e29774efadbd1; dtLatC=335; rxvt=1666910930465|1666907764395; TSf1e2d148029=083a28b6b8ab2800466a76429b7dfea56c90df1a63563292fba688f4ab2bbda4f226111f0089813ec187436a412bda5a; TSb5dce861027=083a28b6b8ab20007846d8b5e72a154364cca30ce523b059ecda37b43809c9f7d5297403871c85930859b5dd3f113000785aad643345dee7599efcf3adc27c5bf0a71146180f2fd55348e4d710531416a3c5e320cb993f25961a942d9297efe2; dtPC=4$108986781_901h-vCMOPPMAUSCVETUMOIBMMRBFKQPKTUIFB-0e0; dtSa=true%7CC%7C-1%7CAceptar%7C-%7C1666909133651%7C108986781_901%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2Fcitar%3Fp%3D49%26locale%3Des%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/citar?p=49&locale=es',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acEntrada' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '111',
        'Content-Type': 'application/x-www-form-urlencoded',
        #'Cookie': 'JSESSIONID=9107E6E0F073E7FFF3AD31A83309F092.appdmzgal3_19023_icpplus; TS01df4168=01a3cd4c04f4faf3f9a6f48a8248c67e67edbf63d8ef6ea425db065e5802fff7c3297ac4efa32bd90ceecefd2879babcd651832876a96e432dccd1f22c9ed3b3001cf68eb9; f5_cspm=1234; dtCookie=v_4_srv_4_sn_2526BE3505DAADE47A4FDF47A9B7D6B3_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666907764393NMC65IHM9M8H0GC9R37MEDKDHUPKL4BO; __utma=129963284.834944477.1666907767.1666907767.1666907767.1; __utmc=129963284; __utmz=129963284.1666907767.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); TSPD_101=083a28b6b8ab28004dd9180b1aed7008c46b53aa2c06bac074c8e292b001badaf9bf8a4811eb4d42dbbf6821b2e5f0890889fcad75051800172a5ecf164b99a772b2ab1b0f4bdd01d9ba1ca193434d91; TS01629f81=01a3cd4c04743455bcd4048d93e5702a56333923657b650adbe32ddf693cdaf1638e70041c821c3c7802866a7ad37a4b3956f5a342597c69dfa506e2377cd4d3d75e730bc2e0dc40a043a96ed7c01abf182275c14d4c9b406d0898d3b0324e29774efadbd1; dtLatC=2; TS00000000076=083a28b6b8ab2800c09f17b24281d9a586cc219613920bfe1f5c5c6330de20cd2af1c9d6cf1abb9da18b9795f436d49b08a5c77beb09d000a70b8a529ba964446ae9915aa5f01898e5f5fe563a95bff4dc0972e187b63cc2026e05ba4d62d49acfc8c132a8c24541eee9375caccd8b9e41d1c58183db821c7ecfa083ca8343afae90927e779a828309898cd8d3e272c00fd6c6a8230145784d6973b66ce3279db81354e58969b912aa975a7358dbfcb76f3eec27dfd0f005e3da446bf1f575240aa457e19700843f6c7bef445d84be0eae2b988d99209fd5c559a5bb097afb99ee36b2c91a4bae470e27ceb4d77f0f44ef117cebed616bf3d7e1633ff3af98fae88dd59e32270c95; TSb5dce861027=083a28b6b8ab20005112ca85aa0b9c4f9bbde616a6f733f41787230dc94911a27ea59de9bb6d611e0836364e80113000b36fdaa353461c3c5d9e9b93620a11d4c98a0f7bae4157f1771febb9da6f1e8320b9266fb3d06138e7ef42c5d19b3e7b; TSPD_101_DID=083a28b6b8ab2800c09f17b24281d9a586cc219613920bfe1f5c5c6330de20cd2af1c9d6cf1abb9da18b9795f436d49b08a5c77beb0638001bc8aedd9217b66b407e47eef825ac313b865b9193a1d8656a5ca1a1af8c343d92102fa8ac4cd8e84edf90b605a2d29c72c587e99edca595; TSf1e2d148077=083a28b6b8ab2800376c21e817446bd44990b7004f953dda373c65d6c3dfa41aa5173ee443b8a6c73644012be33c49fb08008b6b51172000d064317d532c03f9d94699046aa7e2b7d10f7ac4ff66fd22e9b659717070a395; dtPC=4$108842481_727h-vRRUHKPBEOBDAVPRWKHAFPCKOIHGLSHQM-0e0; rxvt=1666912735544|1666910935544; dtSa=true%7CC%7C-1%7CEntrar%7C-%7C1666911045940%7C109134041_226%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2FacInfo%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/acInfo',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acValidarEntrada' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '3150',
        #'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundary1bwfoXBoWJ9910Vm',
        #'Cookie': 'JSESSIONID=9107E6E0F073E7FFF3AD31A83309F092.appdmzgal3_19023_icpplus; TS01df4168=01a3cd4c04f4faf3f9a6f48a8248c67e67edbf63d8ef6ea425db065e5802fff7c3297ac4efa32bd90ceecefd2879babcd651832876a96e432dccd1f22c9ed3b3001cf68eb9; f5_cspm=1234; dtCookie=v_4_srv_4_sn_2526BE3505DAADE47A4FDF47A9B7D6B3_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666907764393NMC65IHM9M8H0GC9R37MEDKDHUPKL4BO; __utmc=129963284; __utmz=129963284.1666907767.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); TS01629f81=01a3cd4c0431371f91038d037702b8a222d35d7192746ddd54c2b7b4f7d49a93527c2ea7defde13d669967ae2cf1beacd76254fe629322c4f245a6c0f18f5557836d6edf7c11309f0d7f637ee7ea0a17e90defee90d9415978da450e9b5ba877d7c47bb1dc; dtLatC=549; __utma=129963284.834944477.1666907767.1666907767.1666911048.2; __utmt=1; __utmb=129963284.1.10.1666911048; TS00000000076=083a28b6b8ab28002359e4cf9a51e436faa3dc2df36ae4f49b445d1f1a5b35fb2899a2a432409263abc33208430a1a3808d63607b109d000ad624cdd113dca773cbc27f4aac0604c5323da16f551951f63c6fb5ed00774c80b28740b997c6cfa6aa2d2e820cba58b59d656d939504a258aa8409859ad8cbd12bd2d7a933039fed9581c7dd0f2e4ddae1244823ff7e73b5fd76fa40db20180b8dfa15040dcf415b97cf0974ebff40bcf61e857a3cb44fded183dcb3698ed16e3051995677ecdd1737b53ae24b50d4febbb20fb5f93893d0b15df0a9317e6390dd9523ef091d6093d2fc564cc07bfdf90dbd44f917407fbdaf8c392b8d25e823d4e4b5b223ba3b32417a44eee4605f6; dtPC=4$111047514_965h-vRRUHKPBEOBDAVPRWKHAFPCKOIHGLSHQM-0e0; TSPD_101_DID=083a28b6b8ab28002359e4cf9a51e436faa3dc2df36ae4f49b445d1f1a5b35fb2899a2a432409263abc33208430a1a3808d63607b1063800d911da128ae82676645ce00fd6206d407cc98d17489f25d114fea101f7c613b42758e7aa57ce1ceef1a0236b07d5b058afacdfaafa6946a7; TSPD_101=083a28b6b8ab28003cc6448265f7ac1822807003c5225265e85d50ceb48363218c74a12bac27a0e12242b9d122849e58081b3aa8b2051800c6df6aab884f904e72b2ab1b0f4bdd01d9ba1ca193434d91; TSb5dce861027=083a28b6b8ab2000762e6f3bbe173f4b0b7181c957f2d9f53234d06d1807cf6c76f0deaec439f1df087979ac0f113000872738295bc22756a4aaa286a3e15d6f6111af4ed18ab732c3b38204a6ce1d807893fade727055c4c61b38ab259f2cf8; TSf1e2d148077=083a28b6b8ab2800a9eec6b85c15305276b83bd351199a5fbb9194fff7c8a36231d4695c69dbdb17adda1a47063adbdf08b1eaacd9172000d0dcdd4f52700d93d94699046aa7e2b7ccafae7cd9f0916b79bf713fa83f72ee; rxvt=1666913000717|1666910935544; dtSa=true%7CC%7C-1%7CAceptar%7C-%7C1666911514596%7C111047514_965%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2FacEntrada%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/acEntrada',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acCitar' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '111',
        'Content-Type': 'application/x-www-form-urlencoded',
        #'Cookie': 'f5_cspm=1234; JSESSIONID=E3E30E05CDD357947842CF48C33DBB5F.appdmzgal3_19023_icpplus; TS01df4168=01a3cd4c0426e05a170f056714a1e4b0bd51634c2def6ea425db065e5802fff7c3297ac4efa32bd90ceecefd2879babcd6518328761ec72bdd84f629269cac3fe27ccbe8c1; dtCookie=v_4_srv_4_sn_2526BE3505DAADE47A4FDF47A9B7D6B3_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666907764393NMC65IHM9M8H0GC9R37MEDKDHUPKL4BO; __utmc=129963284; __utmz=129963284.1666907767.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utma=129963284.834944477.1666907767.1666911048.1666915283.3; __utmt=1; TSPD_101=083a28b6b8ab2800bd42173a413ed0b669aad70c6d3e65a5c848ce99ec013ac0a0573832476f884ec571f787e1fdb50a0837a83d0a0518006f57d217b6104fa472b2ab1b0f4bdd01d9ba1ca193434d91; TS01629f81=01a3cd4c042662ee23fa1132bca47ccd06e0a5928291fe7931104d5a257c3143c13849e1a4c666bbaaf39831ae17fc8fe45cb0bf7829e1a2ad9a1d8fd210190e0b68c4cf033f906fd90d2a85d04bd2c84c694663564004a5243acae6d1f3408cf6c0136589; dtLatC=11768; __utmb=129963284.10.10.1666915283; rxvt=1666917404819|1666914645452; dtPC=4$115601839_623h-vCMWKHAGFVKCKREPHCBSKREWJPHWRDICA-0e0; TSf1e2d148077=083a28b6b8ab2800c1a4c4306c730f920a1cb1673e29391a97a18575d1d0adf0d86ebe0c7110e4eb451d6bb48ce4246108c0814607172000033d2928b207064408f16b7823624fabafd6d8ccc2829efbe531d61e269bfb76; TS00000000076=083a28b6b8ab28008d27389dcce896f606cf6feacd94440a2fa2326934d4541a1f0fdba03a273ecbe055cba2d56a6d3408c21af71209d00055be3c89fa108a18347f4459f2c5944c09d8952ea3f317a1c41ad3600e78339afb40599866cd963c01f032900c8b41b230ca60cb7aa11393755221cefff88f3b94c824edfb211b68b89b7ef125e9f6717961c9ffec1bc13ecb5d3d4eed0498b4edb73291d48c3d51ee02d3d005feaccb31c3d9b6d68d6f8c46264fd920c740cdf82d8540db20a22b75f75d4a8e306fd4aaacafbcfe17e6cba50bac2f76e4f1eab75ed1253cb75c70db2df0166d5dba709a31fb2b79d91e27213283c6446654caf83cd89313e6e5e5a5aefd5497bcd5f1; TSb5dce861027=083a28b6b8ab20003d3d969ac74e890c8f50861a58aeebf299efd5f91cd0298b903ec0bf205a660208298f2d21113000f43d139294e3c5edc101287b48c0e5b0dc255d079b3eca7414d1b561e9e49c9565599194a9b8fa6fd701c4fa19165c14; TSPD_101_DID=083a28b6b8ab28008d27389dcce896f606cf6feacd94440a2fa2326934d4541a1f0fdba03a273ecbe055cba2d56a6d3408c21af712063800fccc2993ec9831b9d7bd598c43c07cde57e6fa043842e702f157bd6e085af9d9fa34a73f75e5b830a5e5e27a93ca32ba5aaac86e5c4de027; viewed_cookie_policy=yes; dtSa=true%7CC%7C-1%7CSolicitar%20Cita%7C-%7C1666915865426%7C115601839_623%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2FacValidarEntrada%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/acValidarEntrada',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acVerFormulario' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '120',
        'Content-Type': 'application/x-www-form-urlencoded',
        # 'Cookie': 'f5_cspm=1234; JSESSIONID=E3E30E05CDD357947842CF48C33DBB5F.appdmzgal3_19023_icpplus; TS01df4168=01a3cd4c0426e05a170f056714a1e4b0bd51634c2def6ea425db065e5802fff7c3297ac4efa32bd90ceecefd2879babcd6518328761ec72bdd84f629269cac3fe27ccbe8c1; dtCookie=v_4_srv_4_sn_2526BE3505DAADE47A4FDF47A9B7D6B3_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666907764393NMC65IHM9M8H0GC9R37MEDKDHUPKL4BO; __utmc=129963284; __utmz=129963284.1666907767.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utma=129963284.834944477.1666907767.1666911048.1666915283.3; TS01629f81=01a3cd4c042662ee23fa1132bca47ccd06e0a5928291fe7931104d5a257c3143c13849e1a4c666bbaaf39831ae17fc8fe45cb0bf7829e1a2ad9a1d8fd210190e0b68c4cf033f906fd90d2a85d04bd2c84c694663564004a5243acae6d1f3408cf6c0136589; TS00000000076=083a28b6b8ab28008d27389dcce896f606cf6feacd94440a2fa2326934d4541a1f0fdba03a273ecbe055cba2d56a6d3408c21af71209d00055be3c89fa108a18347f4459f2c5944c09d8952ea3f317a1c41ad3600e78339afb40599866cd963c01f032900c8b41b230ca60cb7aa11393755221cefff88f3b94c824edfb211b68b89b7ef125e9f6717961c9ffec1bc13ecb5d3d4eed0498b4edb73291d48c3d51ee02d3d005feaccb31c3d9b6d68d6f8c46264fd920c740cdf82d8540db20a22b75f75d4a8e306fd4aaacafbcfe17e6cba50bac2f76e4f1eab75ed1253cb75c70db2df0166d5dba709a31fb2b79d91e27213283c6446654caf83cd89313e6e5e5a5aefd5497bcd5f1; TSPD_101_DID=083a28b6b8ab28008d27389dcce896f606cf6feacd94440a2fa2326934d4541a1f0fdba03a273ecbe055cba2d56a6d3408c21af712063800fccc2993ec9831b9d7bd598c43c07cde57e6fa043842e702f157bd6e085af9d9fa34a73f75e5b830a5e5e27a93ca32ba5aaac86e5c4de027; viewed_cookie_policy=yes; dtLatC=303; __utmb=129963284.11.10.1666915283; rxvt=1666917668101|1666914645452; dtPC=4$115866387_524h-vCMWKHAGFVKCKREPHCBSKREWJPHWRDICA-0e0; TSPD_101=083a28b6b8ab2800d4629bcc5fcf641936218fe588982df7c42d416f2164f919fda1d025cacd03782d7f528546a1de830828cff3b90518000c86144987d3a2d27d8a60c8ee437eccf60d418ef8fa8c4a; TSb5dce861027=083a28b6b8ab20002a35f4624a563878668c5aad9aaef22e29a8868a0d57a0e689b8725647e5ec8708f1fa8c00113000448af0f3c56ff61c925e49417712af0affe971ec9c8bbd6e5d7768d5fbccb383d69e0142999eb94b66c9cb3e7bbc918c; TSf1e2d148077=083a28b6b8ab28004fdb96887b61c686cc84d9d53832847b7d9d6d017f72173d2fc897e8fb2f8e5c8378c0be8e58aef608334c7164172000ef33e4a393ef72da08f16b7823624fabcbc16ec59970375f2b3d78daf76d2cab; dtSa=true%7CC%7C-1%7CSiguiente%7C-%7C1666916319255%7C115866387_524%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2FacCitar%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/acCitar',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acOfertarCita' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '295',
        'Content-Type': 'application/x-www-form-urlencoded',
        #'Cookie': 'f5_cspm=1234; JSESSIONID=E3E30E05CDD357947842CF48C33DBB5F.appdmzgal3_19023_icpplus; TS01df4168=01a3cd4c0426e05a170f056714a1e4b0bd51634c2def6ea425db065e5802fff7c3297ac4efa32bd90ceecefd2879babcd6518328761ec72bdd84f629269cac3fe27ccbe8c1; dtCookie=v_4_srv_4_sn_2526BE3505DAADE47A4FDF47A9B7D6B3_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666907764393NMC65IHM9M8H0GC9R37MEDKDHUPKL4BO; __utmc=129963284; __utmz=129963284.1666907767.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utma=129963284.834944477.1666907767.1666911048.1666915283.3; viewed_cookie_policy=yes; TS01629f81=01a3cd4c049a3567444e1950da3021196e2b1e96eace4a4405b30ac4c2d578dfc5050a347a7c694b8d034499dbb58393538bc80203f4a6b8c20424b4179546b94c916e87eeca4edf2f2a4c653a06fd7c00bb045f8d205941561ebff70760a53cbf1abeb86f; TSPD_101=083a28b6b8ab280015e88e981a6c427cd6b7fb323c28a323b07939e6b1dcf913c12e515548ca94a2b0ef6e699d4f3b4308e09f6fb80518004d21fb0850061e6572b2ab1b0f4bdd01d9ba1ca193434d91; dtLatC=316; __utmb=129963284.12.10.1666915283; dtPC=4$116320360_564h-vCMWKHAGFVKCKREPHCBSKREWJPHWRDICA-0e0; TS00000000076=083a28b6b8ab2800df7082dfe314347c6a4fd80116f0e22660ad857cd99d13474bf575f91d41fad6209228528f6c05f6085738158c09d0005512a94cc3b2d9ba347f4459f2c5944c09d8952ea3f317a1c41ad3600e78339afb40599866cd963c01f032900c8b41b230ca60cb7aa11393755221cefff88f3b94c824edfb211b68b89b7ef125e9f6717961c9ffec1bc13ecb5d3d4eed0498b4f68df51cd8983b5b47af03dae0ed990180ac5175b3bc651e35bf5f940260b63f88517be864a12695bf78f3b1b9c986958ae9abe47b4050ddfcfa975b3bc83034a6b846fa555718205ebf8ffede1f83b3e7a6b2c7c6981c95fa744e0dfe6711223d19e58e04af6c724877bbd333a4e32c; TSb5dce861027=083a28b6b8ab20009738569887973279657545b390453fc4cd36c7ceb1944737bda95f36b5cf39e6084c576ecc11300014e5276a09a95c81e902c168aaec3b37d4737db5188cb6b2ab1b4a71fc4a42a9b9b841af229211ec7638dd1e6596326c; TSPD_101_DID=083a28b6b8ab2800df7082dfe314347c6a4fd80116f0e22660ad857cd99d13474bf575f91d41fad6209228528f6c05f6085738158c063800f19c6bd2e81e5d9032572f9367457c4473db0b2894bdb60cd051eb693a594a8bcf04221a5032cf382f83575d88dbe59a35bc23afc0714fc3; TSf1e2d148077=083a28b6b8ab28006d68d72387232c57b584a58dc2d28e8724379c459f6b20b51dedcb3b1cdbe36852e7cb971fcfd6e70867051c7f1720001e7ccc586ee1f10808f16b7823624fab2a4eb5d61664f532b153e65a3a6003a4; rxvt=1666918837640|1666914645452; dtSa=true%7CC%7C-1%7CSiguiente%7C-%7C1666917057162%7C116320360_564%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2FacVerFormulario%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/acVerFormulario',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acVerificarCita' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        #'Content-Length': '873',
        'Content-Type': 'application/x-www-form-urlencoded',
        #'Cookie': 'f5_cspm=1234; JSESSIONID=AF86C169F10B62C2F4EB4A9A6ED2FE6B.appdmzgal3_19023_icpplus; TS01df4168=01a3cd4c04e8477efe44efc79ce80cede651b93f62b1bd3eada264c0c0211311d5ed3194ceff6fcacc590c4bfc6a6fb81ecee3c6289ff2aefbf83c63ac00b16b32abc1a7e1; dtCookie=v_4_srv_4_sn_6D7EA802D29485984E66B8879A10241B_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666988924680UDCBHMF2S67F0I08CD3625UGH04CPT72; __utmc=129963284; __utmz=129963284.1666988926.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utma=129963284.311966744.1666988926.1666988926.1666991676.2; __utmt=1; TS00000000076=083a28b6b8ab280033a832af8ebfacc4b571b5c81205389eae653e6354d1a54a2cd3040ee07be17fd1ef8efe491e3baf08b680222509d0006ec66ca010d8d8ba01dc69a2a45fb00d6f9aa1f5d04472ea1d00dbfc611a2931bcd018ff4b4ea059e52ad713a0fb3796132b9aba15481b7e79c6cc5a835261ae82170bb35c18f88b5bd2324afa6db6b81f1e3320a2a453af4b0ba44b6df04c7b707fd4031ea5c298586688d09420a85ce5360b1982d07f008bf4acecefc18950e6450aa77b6444751247e2de8f16dd06eab3a73936ce0f86d19852e1f13c686c0cd0d231058fd3acdeeb88c7cfe87d1a38a2c9479d71b550361f3dac96b98a48af388207d5a993f7758f3b448109dbc3; TSPD_101_DID=083a28b6b8ab280033a832af8ebfacc4b571b5c81205389eae653e6354d1a54a2cd3040ee07be17fd1ef8efe491e3baf08b6802225063800d49428a8c544747eacdbd46e661ba32a0fd5b0ec74b4929329d5c6fd0c1cd4eca78000c473e2c4acfa566987614cdfac18c30839b40659d5; TSPD_101=083a28b6b8ab2800b7d835cb3c87c79a96d58f407b144c7ff290f846699a1eab49322982339b6f0000d1478645977bac08e44c4ae8051800a23f17c0a183126472b2ab1b0f4bdd01d9ba1ca193434d91; TS01629f81=01a3cd4c04219ac777ebe3a05f0cd50f5c2e61cf2d1a3340b648656f015c86d340e561966c0628a97085208beeadd57edce9765ed8dde3d13be8055bbd83477d43924f9f22bf8e2da3c151510e6003350e193fd47d660fe7af20a0d79b41ec60ee9dafb727; dtLatC=2; __utmb=129963284.7.10.1666991676; rxvt=1666993649530|1666991231008; dtPC=4$191845567_138h-vCPRPEKICKGWQROIFDRHKMPMCSDVCOWLA-0e0; TSf1e2d148077=083a28b6b8ab2800482c611339af7d840866bf10955bd4f18b6a15db4594fceec06710622f0ae8c1fe54537bf196254908bbf6461b1720000080887736c8b4e4654420e553b3533c9313f803198d0672b13715143478987f; TSf1e2d148029=083a28b6b8ab2800a41335edf775657199ab631eb4c824d38d292adc5c09705620e607103e1880641d45e7620c3d9346; TSb5dce861027=083a28b6b8ab200050bb5aef8dc2a96515ad5a2a5fcc3475dc978a75510f42cdb268c3be2d906c0c0818a79239113000d382aeb6dff5802c36c01f49c1e6f4d0f11cd035a52a9d6affe0a6b9a2076d8ab7f282dba4dcfda433ac452aac1b92fd; dtSa=true%7CC%7C-1%7CSiguiente%7C-%7C1666991851168%7C191845567_138%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2FacOfertarCita%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/acOfertarCita',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    },
    'acGrabarCita' : {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,es;q=0.5',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Length': '166',
        'Content-Type': 'application/x-www-form-urlencoded',
        #'Cookie': 'JSESSIONID=1CD9A33624169E30E4D5DA8617F08CF3.appdmzmol1_19024_icpplus; f5_cspm=1234; TS01df4168=01a3cd4c04ce2ce1c9c54bc363ac56d4f381126d0ded1b8336d9b058a009b77dce5ba6a668d3c2fb34611b75807c4e85e85f6d6252499eb732844b3bc6f1bc737b66ac23f669ca8192ac07ee9c3de1079e43cc96970c5a066c8878a640b4721077714c0ac9; dtCookie=v_4_srv_3_sn_7931D155263390B687C24B46851DE5A9_perc_100000_ol_0_mul_1_app-3Afc0be45c7c7075ff_0; rxVisitor=1666989279184NVP142BG83N6A0QICPOH3HE640C6E184; __utmc=129963284; __utmz=129963284.1666989282.3.2.utmcsr=localhost8888|utmccn=(referral)|utmcmd=referral|utmcct=/; __utma=129963284.1469496881.1666883304.1666989282.1666992707.4; __utmt=1; TS00000000076=083a28b6b8ab280055f8cd62c6160760a0d293e91352dd6c342cea94a9665a4ab7dd1e63c017a2eedabb133203c8c4aa0896f351f809d0001d15d00196da5f9ae67cdc1edfb8f8e254eb02fca46d2cd79f544e7143d239e5aae656cce68f7ee34f79e7cb83f070abfb3108ef044e9bd3c47eeb41e9fa29a640ad9f0e166d966991df25aaed02c2012c04cf15b2dc0fc9567bcc16312697e4a25a21b28f21edf83c04a136596842866b8d8aebd11c40947066ea9e5d5b53999b59bf1f1d4aa5985075075c2ab4a2518a1cfaa5e0771a12f35a0a45d9f3aa05c190b7b2eb3bced9a1bb8cc56dea012b2ddf433e1f15243999e2b2b3dd7e077d7b2aad769c6b4c5870ea8bcbe717d6df; TSPD_101_DID=083a28b6b8ab280055f8cd62c6160760a0d293e91352dd6c342cea94a9665a4ab7dd1e63c017a2eedabb133203c8c4aa0896f351f8063800113fe2145d884e2b2edf24ac17c630320d76321c5cff57338716c4fd3a749161de76b60e34dc726941d7bc88f962a78e0f202018f5e80451; TSPD_101=083a28b6b8ab28007938b7cc1b456e728c7409bb39c40f44dacee18fab94da6bfba76b9eaebd7e33298d49810d76f2530809f809b4051800f0dbe02344cfdb0272b2ab1b0f4bdd01d9ba1ca193434d91; TS01629f81=01a3cd4c0477ddfbf6b7474d4bcb30050d5ca5f732ed1b8336d9b058a009b77dce5ba6a668d3c2fb34611b75807c4e85e85f6d6252499eb732844b3bc6f1bc737b66ac23f6b3e5f549e7b20d9a5757f59b4ccf9c29337db0890f17d5055da9af863d1485ca; dtLatC=2; __utmb=129963284.16.10.1666992707; rxvt=1666994749836|1666991083008; dtPC=3$192948670_937h-vHFKHVVMHREVSUKQTQAWFRAMSWHDCURPM-0e0; TSf1e2d148077=083a28b6b8ab2800e2ee5a8dbaf19f1eeda237a434bf5943ce94b5f5eade1aa59141aaddecaa03ce09da6a03c6e5469808bcf76bd21720001046727341fcd5d2654420e553b3533c3bb9349290ad0e0ec082970a055f59b5; TSb5dce861027=083a28b6b8ab2000fdb06641896acea77de49b6585c53af044cce6b00921c470c609597e77de16c40884630ece113000f060264a93fd2d90237f951c3a99de7c3b98f275a4b99b81358dac33cb69a8f8b5e0080a56f85cf823a54f49115e8d73; dtSa=true%7CC%7C-1%7CConfirmar%7C-%7C1666993000465%7C192948670_937%7Chttps%3A%2F%2Ficp.administracionelectronica.gob.es%2Ficpplus%2FacVerificarCita%7C%7C%7C%7C',
        'Host': 'icp.administracionelectronica.gob.es',
        'Origin': 'https//icp.administracionelectronica.gob.es',
        'Referer': 'https//icp.administracionelectronica.gob.es/icpplus/acVerificarCita',
        'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52'
    }
}

def get_headers(header_name, session, num, cookify=True):
    header = HEADERS[header_name]
    header['User-Agent'] = UAGENTS[num]
    h = header
    if cookify:
        h['Cookie'] = 'JSESSIONID={}'.format(session.cookies['JSESSIONID'])
    return h    
