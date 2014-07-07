from currencies.models import Currency


def currencies(request):
    currencies = Currency.objects.all()

    if not request.session.get('currency_id'):
        request.session['currency_id'] = Currency.objects.get(is_default__exact=True).id

    return {
        'CURRENCIES': currencies,
        'CURRENCY': Currency.objects.get(pk=request.session['currency_id'])
    }
