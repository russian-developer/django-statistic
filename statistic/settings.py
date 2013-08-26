from django.conf import settings

RELATIVE_FOR_YEAR = getattr(settings, 'RELATIVE_FOR_YEAR', 1)
RELATIVE_FOR_MONTH = getattr(settings, 'RELATIVE_FOR_MONTH', 3)
RELATIVE_FOR_WEEK = getattr(settings, 'RELATIVE_FOR_WEEK', 2)

