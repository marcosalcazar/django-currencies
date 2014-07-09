from django.http import HttpResponseRedirect
from currencies.models import Currency
from currencies.signals import currency_changed


def set_currency(request):
    if request.method == 'POST':
        currency_code = request.POST.get('currency', None)
        next = request.POST.get('next', None)
    else:
        currency_code = request.GET.get('currency', None)
        next = request.GET.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'
    response = HttpResponseRedirect(next)
    if currency_code:
        currency = Currency.objects.get(code=currency_code)
        currency_id = currency.id
        if hasattr(request, 'session'):
            request.session['currency_id'] = currency_id
        else:
            response.set_cookie('currency_id', currency_id)
    currency_changed.send(sender=set_currency,
                          currency=currency,
                          user=request.user)
    return response
