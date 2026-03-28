# -*- coding: utf-8 -*-
"""
SOAP клиент для интеграции с ИС ЭСФ
"""
import os
import base64
import hashlib
from typing import Optional, Tuple
from datetime import datetime
from lxml import etree
import requests
from zeep import Client, Settings
from zeep.transports import Transport
from requests.auth import HTTPBasicAuth

class ESFClient:
    """Клиент для работы с ИС ЭСФ"""
    
    WSDL_URL = "https://ws.osvlad.kz/InvoiceService?WSDL"
    UPLOAD_WSDL_URL = "https://ws.osvlad.kz/UploadInvoiceService?WSDL"
    
    # Эндпоинты для разных операций
    INVOICE_SERVICE = "https://ws.osvlad.kz/InvoiceService"
    UPLOAD_SERVICE = "https://ws.osvlad.kz/UploadInvoiceService"
    SESSION_SERVICE = "https://ws.osvlad.kz/SessionService"
    
    def __init__(self, certificate_path: str, certificate_password: str, sender_bin: str):
        """
        Инициализация клиента
        
        Args:
            certificate_path: Путь к файлу ЭЦП (.p12)
            certificate_password: Пароль к ЭЦП
            sender_bin: БИН отправителя
        """
        self.certificate_path = certificate_path
        self.certificate_password = certificate_password
        self.sender_bin = sender_bin
        self.session_id: Optional[str] = None
        self._client = None
        
    def _load_certificate(self) -> Tuple[bytes, str]:
        """Загрузка сертификата из файла .p12"""
        import OpenSSL
        from OpenSSL import crypto
        
        with open(self.certificate_path, 'rb') as f:
            p12_data = f.read()
        
        p12 = crypto.load_pkcs12(p12_data, self.certificate_password)
        
        # PEM ключ
        pem_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
        # PEM сертификат
        pem_cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
        
        return pem_key, pem_cert
    
    def _sign_data(self, data: bytes) -> str:
        """Подписание данных ЭЦП"""
        from Crypto.Signature import pkcs1_15
        from Crypto.PublicKey import RSA
        import OpenSSL
        
        key, cert = self._load_certificate()
        
        # Загрузка ключа
        pkey = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        
        # Подписание
        signature = OpenSSL.crypto.sign(pkey, data, 'sha256')
        
        return base64.b64encode(signature).decode()
    
    def _get_x509_certificate(self) -> str:
        """Получение сертификата в формате PEM"""
        key, cert = self._load_certificate()
        return cert.decode()
    
    def create_session(self) -> str:
        """Создание сессии в ИС ЭСФ"""
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }
        
        body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <soap:Body>
        <ns2:CreateSession xmlns:ns2="esf">
            <ns2:request>
                <ns2:bin>{self.sender_bin}</ns2:bin>
                <ns2:signature>{self._sign_data(self.sender_bin.encode())}</ns2:signature>
                <ns2:x509Certificate>{self._get_x509_certificate()}</ns2:x509Certificate>
            </ns2:request>
        </ns2:CreateSession>
    </soap:Body>
</soap:Envelope>'''
        
        response = requests.post(
            self.SESSION_SERVICE,
            data=body.encode('utf-8'),
            headers=headers,
            verify=True
        )
        
        if response.status_code == 200:
            root = etree.fromstring(response.content)
            # Извлечение sessionId из ответа
            session_elem = root.find('.//{*}CreateSessionResponse/{*}sessionId')
            if session_elem is not None:
                self.session_id = session_elem.text
                return self.session_id
        
        raise Exception(f"Ошибка создания сессии: {response.status_code}")
    
    def close_session(self):
        """Закрытие сессии"""
        if not self.session_id:
            return
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }
        
        body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <ns2:CloseSession xmlns:ns2="esf">
            <ns2:sessionId>{self.session_id}</ns2:sessionId>
        </ns2:CloseSession>
    </soap:Body>
</soap:Envelope>'''
        
        requests.post(
            self.SESSION_SERVICE,
            data=body.encode('utf-8'),
            headers=headers
        )
        
        self.session_id = None
    
    def send_invoice(self, invoice_xml: str) -> dict:
        """
        Отправка счета-фактуры в ЭСФ
        
        Args:
            invoice_xml: XML документ счета-фактуры
            
        Returns:
            Словарь с результатом отправки
        """
        if not self.session_id:
            self.create_session()
        
        # Подписание документа
        invoice_bytes = invoice_xml.encode('utf-8')
        signature = self._sign_data(invoice_bytes)
        x509_cert = self._get_x509_certificate()
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }
        
        body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:ns2="esf">
    <soap:Body>
        <ns2:UploadInvoice>
            <ns2:request>
                <ns2:sessionId>{self.session_id}</ns2:sessionId>
                <ns2:invoice>
                    <ns2:invoice>
{invoice_xml}
                    </ns2:invoice>
                    <ns2:signature>{signature}</ns2:signature>
                    <ns2:x509Certificate>{x509_cert}</ns2:x509Certificate>
                </ns2:invoice>
            </ns2:request>
        </ns2:UploadInvoice>
    </soap:Body>
</soap:Envelope>'''
        
        response = requests.post(
            self.UPLOAD_SERVICE,
            data=body.encode('utf-8'),
            headers=headers,
            verify=True
        )
        
        if response.status_code == 200:
            root = etree.fromstring(response.content)
            # Парсинг ответа
            result = {
                'success': True,
                'response': response.content.decode('utf-8')
            }
            
            # Проверка на ошибки
            error_elem = root.find('.//{*}error')
            if error_elem is not None:
                result['success'] = False
                result['error'] = error_elem.text
            
            return result
        
        return {
            'success': False,
            'error': f'HTTP Error: {response.status_code}'
        }
    
    def get_invoice_status(self, invoice_id: int) -> dict:
        """Получение статуса счета-фактуры"""
        if not self.session_id:
            self.create_session()
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }
        
        body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:ns2="esf">
    <soap:Body>
        <ns2:GetInvoiceStatus>
            <ns2:request>
                <ns2:sessionId>{self.session_id}</ns2:sessionId>
                <ns2:idList>
                    <ns2:id>{invoice_id}</ns2:id>
                </ns2:idList>
            </ns2:request>
        </ns2:GetInvoiceStatus>
    </soap:Body>
</soap:Envelope>'''
        
        response = requests.post(
            self.INVOICE_SERVICE,
            data=body.encode('utf-8'),
            headers=headers
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'response': response.content.decode('utf-8')
            }
        
        return {
            'success': False,
            'error': f'HTTP Error: {response.status_code}'
        }


class MockESFClient:
    """Mock клиент для тестирования без реальной отправки"""
    
    def __init__(self, certificate_path: str = '', certificate_password: str = '', sender_bin: str = ''):
        self.certificate_path = certificate_path
        self.certificate_password = certificate_password
        self.sender_bin = sender_bin
        self.session_id = 'MOCK-SESSION-12345'
    
    def create_session(self) -> str:
        return self.session_id
    
    def close_session(self):
        pass
    
    def send_invoice(self, invoice_xml: str) -> dict:
        """Mock отправка - возвращает успех"""
        import uuid
        return {
            'success': True,
            'uuid': str(uuid.uuid4()),
            'message': 'Документ успешно зарегистрирован в ЭСФ (тестовый режим)',
            'response': 'MOCK_RESPONSE'
        }
    
    def get_invoice_status(self, invoice_id: int) -> dict:
        return {
            'success': True,
            'status': 'APPROVED',
            'message': 'Документ подтвержден'
        }
