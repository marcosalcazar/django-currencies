# -*- coding: utf-8 -*-
import sys, re, json
#from urllib2 import urlopen, HTTPError
# requires beautifulsoup4 and requests
from bs4 import BeautifulSoup as BS4
from requests import get, exceptions
from decimal import Decimal
from datetime import datetime

from ._currencyhandler import BaseHandler


class YahooHandler(BaseHandler):
    """
    Currency Handler implements public API:
    endpoint
    get_allcurrencycodes()
    get_currencyname(code)
    get_currencysymbol(code) - optional
    get_ratetimestamp(base, code)
    get_ratefactor(base, code)
    """
    endpoint = 'http://finance.yahoo.com'
    onerate_url = 'http://finance.yahoo.com/d/quotes.csv?s=%s%s=X&f=l1'
    full_url = 'http://uk.finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote;currency=true?view=basic&format=json&callback=YAHOO.Finance.CurrencyConverter.addConversionRates'
    ukbulk_url = 'http://uk.finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json'
    bulk_url = 'http://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json'
    currencies_url = 'http://finance.yahoo.com/currency-converter/'

    _currencies = None
    _rates = None
    _base = None

    @property
    def currencies(self):
        if not self._currencies:
            self._currencies = self.get_bulkcurrencies()
        return self._currencies

    @property
    def rates(self):
        if not self._rates:
            self._rates = self.get_bulkrates()
        return self._rates

    @property
    def base(self):
        if not self._base:
            self._base = self.get_baserate()
        return self._base

    def get_bulkcurrencies(self):
        """
        Get the supported currencies
        Scraped from a JSON object on the html page in javascript tag
        """
        start = r'YAHOO\.Finance\.CurrencyConverter\.addCurrencies\('
        _json = r'\[[^\]]*\]'
        try:
            resp = get(self.currencies_url)
            resp.raise_for_status()
        except exceptions.RequestException as e:
            raise RuntimeError(e)
        # Find the javascript that contains the json object
        soup = BS4(resp.text, 'html.parser')
        re_start = re.compile(start)
        jscript = soup.find('script', type='text/javascript', text=re_start).string

        # Separate the json object
        re_json = re.compile(_json)
        match = re_json.search(jscript)
        if match:
            json_str = match.group(0)
        else:
            raise RuntimeError("YahooFinance: Currency JSON object not found")

        # Parse the json object
        return json.loads(json_str)

    def get_bulkrates(self):
        """Get & format the rates dict"""
        try:
            resp = get(self.bulk_url)
            resp.raise_for_status()
        except exceptions.RequestException as e:
            raise RuntimeError(e)
        return resp.json()

    def get_singlerate(self, base, code):
        """Get a single rate, used as fallback"""
        try:
            url = self.onerate_url % (base, code)
            #rate = urllib2.urlopen(url).read().rstrip()
            resp = get(url)
            resp.raise_for_status()
        except exceptions.HTTPError:
            self.warn("YahooFinance: problem with %s" % url)
            return None
        rate = resp.text.rstrip()

        if rate == 'N/A':
            return None
        else:
            return Decimal(rate)

    def get_allcurrencycodes(self):
        """Return an iterable of 3 character ISO 4217 currency codes"""
        return (currency['shortname'] for currency in self.currencies)

    def get_currency(self, code):
        """Helper function"""
        for currency in self.currencies:
            if currency['shortname'] == code:
                return currency
        raise RuntimeError("YahooFinance: %s not found" % code)

    def get_currencyname(self, code):
        """Return the currency name from the code"""
        return self.get_currency(code)['longname']

    def get_currencysymbol(self, code):
        """Return the currency symbol from the code"""
        return self.get_currency(code)['symbol']

    def get_rate(self, code):
        """Helper function to access the rates structure"""
        rateslist = self.rates['list']['resources']
        for rate in rateslist:
            rateobj = rate['resource']['fields']
            if rateobj['symbol'].startswith(code):
                return rateobj
        raise RuntimeError("YahooFinance: %s not found" % code)

    def get_baserate(self):
        """Helper function to populate the base rate"""
        rateslist = self.rates['list']['resources']
        for rate in rateslist:
            rateobj = rate['resource']['fields']
            if rateobj['symbol'].partition('=')[0] == rateobj['name']:
                return rateobj['name']
        raise RuntimeError("YahooFinance: baserate not found")

    def get_ratetimestamp(self, base, code):
        """Return rate timestamp in datetime format or None"""
        try:
            ts = int(self.get_rate(code)['ts'])
        except RuntimeError:
            return None
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    # These YF currencies are reported differently with no base, but still appear to be based on USD
    # Gold, Copper, Palladium, Platinum, Silver
    _exceptions = ('XAU', 'XCP', 'XPD', 'XPT', 'XAG')
    def check_ratebase(self, rate):
        """Helper function"""
        split = rate['name'].partition('/')
        if split[1]:
            ratebase = split[0]
            if ratebase != self.base:
                raise RuntimeError("YahooFinance: %s has different base rate:\n%s" % (ratebase, rate))
        elif rate['name'] == self.base:
            pass
        elif rate['symbol'].partition('=')[0] not in self._exceptions:
            self.warn("YahooFinance: currency found with no base:\n%s" % rate)


    def get_ratefactor(self, base, code):
        """
        Return the Decimal currency exchange rate factor of 'code' compared to 1 'base' unit, or None
        Yahoo currently uses USD as base currency, but here we detect it with get_baserate
        """
        try:
            rate = self.get_rate(code)
        except RuntimeError:
            # fallback
            return self.get_singlerate(base, code)

        self.check_ratebase(rate)
        ratefactor = Decimal(rate['price'])

        if base == self.base:
            return ratefactor
        else:
            return self.ratechangebase(ratefactor, self.base, base)


def get_handle(print_info, print_warn):
    """
    Get a handle to the currency client and description string
    Passes helper functions for informational and warning messages
    """
    y = YahooHandler(print_info, print_warn)
    return y, y.endpoint

def get_allcurrencycodes(handle):
    return handle.get_allcurrencycodes()

def get_currencyname(handle, code):
    return handle.get_currencyname(code)



def get_ratetimestamp(handle, base, code):
    return handle.get_ratetimestamp(base, code)

def get_ratefactor(handle, base, code):
    return handle.get_ratefactor(base, code)

def remove_cache():
    pass
