django-statistic
=========================

Statistic for models

Install
-------

For install you can use pip:
```
pip install django-statistic
```

Usage
-------

models.py

```
from django.db import models

class Authors(models.Model):
    first_name = ....
    last_name = ....
  
class Books(models.Model):
    title = ....
    author = models.ManyToManyField(Author)
```

views.py

```
from statistic import Statistic
from models import Authors, Books


def my_view(request):
    book = Books.objects.get(...)

    # Put object in statistic table
    Statistic.objects.add(book)
    
    # Get statistic for object
    statistic_for_object = Statistic.objects.get_statistic_for_object(book)
    
    # Get statistic for model
    statistic_for_model = Statistic.objects.get_statistic_for_model(Books, limit=50)
    
    # Get statistic for models
    statistic_for_models = Statistic.objects.get_statistic_for_model([Authors, Books], limit=50, shuffle=True)
```
    
settings.py

```
RELATIVE_FOR_YEAR = 1 # Get relative year (Today is 2013, example get: 2012, 2013)
RELATIVE_FOR_MONTH = 3 # Get relative month (Today is 1'th January, example get: 2012.11, 2012.12, 2013.1)
RELATIVE_FOR_WEEK = 2 # Get relative week (Today is 13'th week of year, example get: 11, 12, 13 week of year)
```

Note
-------

For big data, you must use cache/crontab.