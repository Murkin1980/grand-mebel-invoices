# -*- coding: utf-8 -*-
"""
Модуль для работы с ЭСФ (Электронные Счета-Фактуры)
Интеграция с ИС ЭСФ через SOAP API
"""
import os
import datetime
from dataclasses import dataclass, field
from typing import List, Optional
from lxml import etree

NS = {
    'esf': 'esf',
    'inv': 'abstractInvoice.esf',
}

@dataclass
class Participant:
    """Участник сделки (продавец/покупатель)"""
    bin_iin: str
    name: str
    address: str
    bank_account: str = ""
    bank_name: str = ""
    bik: str = ""
    is_resident: bool = True
    
    def to_xml(self, tag: str) -> etree.Element:
        elem = etree.Element(tag)
        if self.is_resident:
            elem.set('type', '1')  # БИН
        else:
            elem.set('type', '2')  # ИИН
        
        # БИН/ИИН
        bin_elem = etree.SubElement(elem, ' Bin')
        bin_elem.text = self.bin_iin
        
        # Наименование
        name_elem = etree.SubElement(elem, 'Name')
        name_elem.text = self.name
        
        # Адрес
        addr_elem = etree.SubElement(elem, 'Address')
        elem_elem = etree.SubElement(addr_elem, 'Country')
        elem_elem.text = 'KZ'
        city_elem = etree.SubElement(addr_elem, 'City')
        city_elem.text = self.address
        
        # Банковские реквизиты
        if self.bank_account:
            bank_elem = etree.SubElement(elem, 'Bank')
            iik_elem = etree.SubElement(bank_elem, 'IIK')
            iik_elem.text = self.bank_account
            if self.bank_name:
                name_elem = etree.SubElement(bank_elem, 'Name')
                name_elem.text = self.bank_name
            if self.bik:
                bik_elem = etree.SubElement(bank_elem, 'BIC')
                bik_elem.text = self.bik
        
        return elem


@dataclass
class InvoiceItem:
    """Позиция в счете-фактуре"""
    name: str
    unit_code: str = "166"  # Штука по умолчанию
    unit_name: str = "Штука"
    quantity: float = 1.0
    price: float = 0.0
    tax_rate: float = 0.0  # Ставка НДС (0, 12, 20)
    excise_sum: float = 0.0  # Сумма акциза
    country_code: str = "KZ"  # Код страны происхождения
    
    @property
    def total_without_tax(self) -> float:
        """Сумма без НДС"""
        return self.quantity * self.price
    
    @property
    def tax_sum(self) -> float:
        """Сумма НДС"""
        return self.total_without_tax * (self.tax_rate / 100)
    
    @property
    def total_with_tax(self) -> float:
        """Сумма с НДС"""
        return self.total_without_tax + self.tax_sum
    
    def to_xml(self, idx: int) -> etree.Element:
        elem = etree.Element('Contents')
        elem.set('num', str(idx))
        
        # Наименование товара
        name_elem = etree.SubElement(elem, 'Name')
        name_elem.text = self.name
        
        # Единица измерения
        unit_elem = etree.SubElement(elem, 'UnitOfMeasure')
        unit_elem.set('code', self.unit_code)
        unit_elem.set('value', self.unit_name)
        
        # Количество
        qty_elem = etree.SubElement(elem, 'Quantity')
        qty_elem.text = str(self.quantity)
        
        # Цена без НДС
        price_elem = etree.SubElement(elem, 'PriceWithoutVAT')
        price_elem.text = f"{self.price:.2f}"
        
        # Ставка НДС
        tax_elem = etree.SubElement(elem, 'VATRate')
        tax_elem.text = str(self.tax_rate)
        
        # Сумма НДС
        tax_sum_elem = etree.SubElement(elem, 'VATSum')
        tax_sum_elem.text = f"{self.tax_sum:.2f}"
        
        # Сумма с НДС
        total_elem = etree.SubElement(elem, 'TotalWithVAT')
        total_elem.text = f"{self.total_with_tax:.2f}"
        
        return elem


@dataclass
class Invoice:
    """Электронный Счет-Фактура (ЭСФ)"""
    invoice_number: str
    invoice_date: datetime.date
    
    # Продавец
    seller: Participant
    
    # Покупатель
    buyer: Participant
    
    # Данные об отгрузке
    shipment_date: datetime.date
    accept_date: Optional[datetime.date] = None
    
    # Договор
    contract_number: str = ""
    contract_date: Optional[datetime.date] = None
    
    # Позиции
    items: List[InvoiceItem] = field(default_factory=list)
    
    # Дополнительно
    invoice_type: int = 1  # 1 - исходящий
    currency: str = "KZT"
    
    # Для отправки в ЭСФ
    original_uuid: Optional[str] = None
    esf_id: Optional[int] = None
    esf_status: Optional[str] = None
    
    @property
    def total_without_tax(self) -> float:
        return sum(item.total_without_tax for item in self.items)
    
    @property
    def total_tax(self) -> float:
        return sum(item.tax_sum for item in self.items)
    
    @property
    def total_with_tax(self) -> float:
        return sum(item.total_with_tax for item in self.items)
    
    def to_xml(self) -> etree.Element:
        """Генерация XML документа ЭСФ"""
        root = etree.Element('Invoice')
        root.set('xmlns', 'esf')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        
        # Секция документа
        doc_elem = etree.SubElement(root, 'Document')
        
        # Регистрационный номер (присваивается ИС ЭСФ)
        if self.original_uuid:
            reg_num_elem = etree.SubElement(doc_elem, 'OriginalRegNumber')
            reg_num_elem.text = self.original_uuid
        
        # Номер счета-фактуры
        num_elem = etree.SubElement(doc_elem, 'InvoiceNumber')
        num_elem.text = self.invoice_number
        
        # Дата счета-фактуры
        date_elem = etree.SubElement(doc_elem, 'InvoiceDate')
        date_elem.text = self.invoice_date.strftime('%d.%m.%Y')
        
        # Тип счета-фактуры
        type_elem = etree.SubElement(doc_elem, 'InvoiceType')
        type_elem.text = str(self.invoice_type)
        
        # Продавец
        root.append(self.seller.to_xml('Seller'))
        
        # Покупатель
        root.append(self.buyer.to_xml('Buyer'))
        
        # Сведения об отгрузке
        shipment_elem = etree.SubElement(root, 'Shipment')
        date_ship_elem = etree.SubElement(shipment_elem, 'DateOfShipment')
        date_ship_elem.text = self.shipment_date.strftime('%d.%m.%Y')
        
        if self.accept_date:
            date_accept_elem = etree.SubElement(shipment_elem, 'DateOfAccept')
            date_accept_elem.text = self.accept_date.strftime('%d.%m.%Y')
        
        # Договор
        if self.contract_number:
            contract_elem = etree.SubElement(shipment_elem, 'Contract')
            contract_num_elem = etree.SubElement(contract_elem, 'ContractNumber')
            contract_num_elem.text = self.contract_number
            if self.contract_date:
                contract_date_elem = etree.SubElement(contract_elem, 'ContractDate')
                contract_date_elem.text = self.contract_date.strftime('%d.%m.%Y')
        
        # Валюта
        currency_elem = etree.SubElement(shipment_elem, 'Currency')
        currency_elem.set('code', self.currency)
        
        # Позиции
        contents_elem = etree.SubElement(root, 'Contents')
        for idx, item in enumerate(self.items, 1):
            contents_elem.append(item.to_xml(idx))
        
        # Итоги
        total_elem = etree.SubElement(root, 'Totals')
        total_without_tax_elem = etree.SubElement(total_elem, 'TotalSumWithoutVAT')
        total_without_tax_elem.text = f"{self.total_without_tax:.2f}"
        
        total_tax_elem = etree.SubElement(total_elem, 'TotalVATSum')
        total_tax_elem.text = f"{self.total_tax:.2f}"
        
        total_with_tax_elem = etree.SubElement(total_elem, 'TotalSum')
        total_with_tax_elem.text = f"{self.total_with_tax:.2f}"
        
        return root
    
    def to_xml_string(self) -> str:
        """Генерация XML строки"""
        root = self.to_xml()
        return etree.tostring(root, xml_declaration=True, encoding='UTF-8', pretty_print=True).decode('UTF-8')


def create_invoice_from_order(invoice_order) -> Invoice:
    """Создание ЭСФ из обычного счета на оплату"""
    seller = Participant(
        bin_iin='910226302322',
        name='ИП "ГРАНД МЕБЕЛЬ"',
        address='Казахстан, Аулиеагаш, МИКРОРАЙОН МАДЕНИЕТ, УЛИЦА ТАСБОЛАТ, дом 34',
        bank_account='KZ84722S000035000586',
        bank_name='АО «Kaspi Bank»',
        bik='CASPKZKA'
    )
    
    buyer = Participant(
        bin_iin=invoice_order.contractor.bin_iin,
        name=invoice_order.contractor.name,
        address=invoice_order.contractor.address
    )
    
    items = []
    for item in invoice_order.items:
        items.append(InvoiceItem(
            name=item.product.name,
            quantity=item.quantity,
            price=item.price,
            tax_rate=0  # Без НДС
        ))
    
    invoice = Invoice(
        invoice_number=f"ЭСФ-{invoice_order.number}",
        invoice_date=invoice_order.date,
        seller=seller,
        buyer=buyer,
        shipment_date=invoice_order.date,
        contract_number=invoice_order.contract_info if invoice_order.contract_info != 'Без договора' else ''
    )
    invoice.items = items
    
    return invoice
