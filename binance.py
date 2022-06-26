import asyncio
import time
import json
import aiohttp
import gspread
from pathlib import Path
from oauth2client.service_account import ServiceAccountCredentials

class CurrencyCell(object):

    def __init__(self, pay_type: str, sheet_url: str, cell: str, native_currency: str = "RUB", currency: str = "USDT", \
                 filepath: str = "./scopes1.json"):
        # это банк, который нас интерсует
        self.pay_type = pay_type
        # ссылка на документ
        self.sheet_url = sheet_url
        # ячейка, куда нужно вставить результат
        self.cell = cell

    ####################################################

        # родная валюта (по умолчанию рубли)
        self.native_currency = native_currency
        # нужная валюта
        self.currency = currency
        # путь до файла с настройками
        self.api_creds = Path(filepath)


    def __str__(self):
        return f"Currency {self.currency} in {self.pay_type} in cell {self.cell}"


    async def scrape_currency(self) -> str:
        """Эта функция вытаскивает нужный курс"""
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        payload = {
            "page": 1,
            "rows": 10,
            # банк, который нас интересует - список
            "payTypes": [self.pay_type],
            "publisherType": None,
            "asset": self.currency, # USDT
            "tradeType":"BUY",
            "fiat": self.native_currency
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                json = await response.json()
                # самый первый курс
                if isinstance(None, type(json)):
                    raise ValueError("Кажется, что такого банка нет.")

                currency = json["data"][0]["adv"]["price"]
                return currency

    def save_in_sheet(self, currency: str):

        scope = ('https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive')

        # api_creds = json.load(open(self.api_creds, encoding="utf8"))
        # учётные данные из .json файла от Google
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.api_creds, scope)
        auth = gspread.authorize(credentials)
        wb = auth.open_by_url(self.sheet_url).sheet1
        wb.update(self.cell, currency)

async def main():
    settings = json.load(open("settings1.json", encoding="utf8"))
    sheet_url = settings["url"]
    api_creds = settings["api_creds"]


    active_cell = CurrencyCell(pay_type="QIWI", sheet_url=sheet_url, cell="B14", filepath=api_creds)
    currency = await active_cell.scrape_currency()
    active_cell.save_in_sheet(currency)
    print(f"{active_cell} записана")
    await asyncio.sleep(5)

    active_cell = CurrencyCell(pay_type="Tinkoff", sheet_url=sheet_url, cell="B15", currency="BTC", filepath=api_creds)
    currency = await active_cell.scrape_currency()
    active_cell.save_in_sheet(currency)
    print(f"{active_cell} записана")
    await asyncio.sleep(5)

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as error:
            print("Что-то пошло не так...")
            print(error)
        finally:
            time.sleep(60)







