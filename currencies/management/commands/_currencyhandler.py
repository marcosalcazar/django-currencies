# -*- coding: utf-8 -*-
import os
import json
from decimal import Decimal

class BaseHandler(object):
    """
    Base Currency Handler implements helpers:
    _dir
    info(), warn()
    get_currencysymbol(code) - should be overridden
    ratechangebase(Decimal, current_base, new_base)

    Public API required:
    endpoint
    get_allcurrencycodes()
    get_currencyname(code)

    Optional - do not implement:
    get_info(code):
    get_ratefactor(base, code)
    get_ratetimestamp(base, code)
    """
    # For caching downloaded currency data
    _dir = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, print_info, print_warn):
        """Save the message stream functions"""
        self.info = print_info
        self.warn = print_warn

    _symbols = None
    def get_currencysymbol(self, code):
        """Retrieve the currency symbol from the local file"""
        if not self._symbols:
            symbolpath = os.path.join(self._dir, 'currencies.json')
            with open(symbolpath) as df:
                self._symbols = json.load(df)
        return self._symbols.get(code)

    _multiplier = None
    def ratechangebase(self, ratefactor, current_base, new_base):
        """
        Local helper function for changing currency base, returns new rate in new base
        Defaults to ROUND_HALF_EVEN
        """
        if not self._multiplier:
            self.warn("CurrencyHandler: changing base ourselves")
            # Check the current base is 1
            if Decimal(1) != self.get_ratefactor(current_base, current_base):
                raise RuntimeError("CurrencyHandler: current baserate: %s not 1" % current_base)
            self._multiplier = Decimal(1) / self.get_ratefactor(current_base, new_base)
        return (ratefactor * self._multiplier).quantize(Decimal(".0001"))
