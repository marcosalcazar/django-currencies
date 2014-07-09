import django.dispatch


currency_changed = django.dispatch.Signal(providing_args=["currency",
                                                          "user"])