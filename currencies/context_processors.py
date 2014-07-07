from currencies.models import Currency


def currencies(request):
    currencies = Currency.objects.all()
    currencies_active = Currency.objects.filter(is_active=True).all()
    if not request.session.get('currency_id'):
        request.session['currency_id'] = Currency.objects.get(is_default__exact=True).id

    return {
        'CURRENCIES': currencies,
        'CURRENCIES_ACTIVE': currencies_active,
        'CURRENCY': Currency.objects.get(pk=request.session['currency_id'])
    }
