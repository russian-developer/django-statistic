from django.conf import settings
import operator
from random import shuffle as _shuffle
from itertools import chain
from django.db import models
from django.db.models import Q, Sum
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


TOTAL = 0
YEAR = 1
MONTH = 2
WEEK = 3


class StatisticManager(models.Manager):

    STATISTIC_TEMPLATE = {
        'total': None,
        'year': None,
        'month': None,
        'week': None,
    }

    def _get_imprecise_filter(self, filter_type):
        result = []
        if filter_type == TOTAL:
            result.append(Q(year=None, month=None, week=None))
        if filter_type == YEAR:
            for year in range(self._year-settings.RELATIVE_FOR_YEAR, self._year):
                result.append(Q(year=year, month=None, week=None))
        if filter_type == MONTH:
            point_date = date.today() + relativedelta(months=-settings.RELATIVE_FOR_MONTH)
            months = range((self._year - point_date.year) * 12 + self._month - point_date.month)
            for i in months:
                result.append(Q(year=point_date.year, month=point_date.month))
                point_date = point_date + relativedelta(months=+1)
        if filter_type == WEEK:
            point_date = date.today() + relativedelta(weeks=-settings.RELATIVE_FOR_WEEK)
            weeks = range((self._year - point_date.year) * 52 + self._week - point_date.timetuple().tm_yday / 7)
            for i in weeks:
                result.append(Q(year=point_date.year, month=point_date.month, week=point_date.timetuple().tm_yday / 7))
                point_date = point_date + relativedelta(weeks=+1)
        return result


    def _increment(self, **filter):
        queryset = self.get_query_set()
        try:
            obj = queryset.get(**filter)
            obj.count += 1
        except queryset.model.DoesNotExist:
            obj = queryset.model(**filter)
        obj.save()
        return obj

    @property
    def _year(self):
        return date.today().year

    @property
    def _month(self):
        return date.today().month

    @property
    def _week(self):
        return date.today().timetuple().tm_yday / 7

    def is_relative(self, userdate, relative_type):
        current_date = date.today()
        if relative_type == YEAR:
            return (current_date + relativedelta(years=-settings.RELATIVE_FOR_YEAR)) < userdate < (current_date + relativedelta(years=+settings.RELATIVE_FOR_YEAR))
        if relative_type == MONTH:
            return (current_date + relativedelta(months=-settings.RELATIVE_FOR_MONTH)) < userdate < (current_date + relativedelta(months=+settings.RELATIVE_FOR_MONTH))
        if relative_type == WEEK:
            return (current_date + relativedelta(weeks=-settings.RELATIVE_FOR_WEEK)) < userdate < (current_date + relativedelta(weeks=+settings.RELATIVE_FOR_WEEK))

    def add(self, object):
        object_type = ContentType.objects.get_for_model(object)
        queryset = self.get_query_set()

        # total_statistic
        self._increment(
                content_type=object_type,
                object_id=object.id,
                year=None,
                month=None,
                week=None,
        )

        # Statistic for year
        self._increment(
                content_type=object_type,
                object_id=object.id,
                year=self._year,
                month=None,
                week=None,
        )

        # Statistic for year and month
        self._increment(
                content_type=object_type,
                object_id=object.id,
                year=self._year,
                month=self._month,
                week=None,
        )

        # Statistic for year, month and week
        self._increment(
                content_type=object_type,
                object_id=object.id,
                year=self._year,
                month=self._month,
                week=self._week,
        )

    def get_statistic_for_object(self, object):
        object_type = ContentType.objects.get_for_model(object)
        queryset = self.get_query_set().filter(content_type=object_type, object_id=object.id)
        result = self.STATISTIC_TEMPLATE.copy()

        try:
            result['total'] = queryset.get(year=None)
        except queryset.model.DoesNotExist:
            return queryset.none()
        else:
            result['year'] = queryset \
                .filter(reduce(operator.or_, self._get_imprecise_filter(YEAR))) \
                .aggregate(total_count=models.Sum('count'))['total_count']
            result['month'] = queryset \
                .filter(reduce(operator.or_, self._get_imprecise_filter(MONTH))) \
                .aggregate(total_count=models.Sum('count'))['total_count']
            result['week'] = queryset \
                .filter(reduce(operator.or_, self._get_imprecise_filter(WEEK))) \
                .aggregate(total_count=models.Sum('count'))['total_count']
        return result

    def get_statistic_for_model(self, model, limit=50):
        """

        :param model: model cls
        :param limit: int, limit of total returned objects in ranges
        :return: dict of periods
            Total TOP
            TOP for year
            TOP for month
            TOP for week
        """
        def dict_to_queryset(object_list):
            if object_list:
                return model.objects.filter(pk__in=map(lambda f: f['object_id'], object_list))
            return model.objects.none()

        object_type = ContentType.objects.get_for_model(model)
        queryset = self.get_query_set() \
            .values('object_id') \
            .filter(content_type=object_type) \
            .annotate(count_sum=Sum('count')) \
            .order_by('-count_sum')
        result = self.STATISTIC_TEMPLATE.copy()
        result['total'] = dict_to_queryset(
            queryset.filter(reduce(operator.or_, self._get_imprecise_filter(TOTAL)))[:limit]
        )
        result['year'] = dict_to_queryset(
            queryset.filter(reduce(operator.or_, self._get_imprecise_filter(YEAR)))[:limit]
        )
        result['month'] = dict_to_queryset(
            queryset.filter(reduce(operator.or_, self._get_imprecise_filter(MONTH)))[:limit]
        )
        result['week'] = dict_to_queryset(
            queryset.filter(reduce(operator.or_, self._get_imprecise_filter(WEEK)))[:limit]
        )
        return result

    def get_statistic_for_models(self, models, limit=100, shuffle=True):
        """

        -> example of usage:
        -> from myapp.models import MyModel
        -> from myotherapp.models import MyOtherModel
        -> from statistic.models import Statistic
        -> Statistic.objects.get_statistic_for_models([MyModel, MyOtherModel], limit=50, shuffle=True)
        <- [<MyModel: MyModel object>, <MyOtherModel: MyOtherModel object>, <MyModel: MyModel object>, ...]

        :param models: [model_cls_A, model_cls_B]
        :param limit: int, limit of total returned objects
        :param shuffle:  bool
        :return: list of objects
        """
        assert isinstance(models, list), '`models` must be list of models cls'
        statistic = \
            list(
                chain(
                    map(
                        lambda model: self.get_statistic_for_model(model, limit=limit/len(models)),
                        models
                    )
                )
            )
        if shuffle:
            _shuffle(statistic)
        return statistic



class Statistic(models.Model):
    '''
    1) Total statistic (empty year, month, week)
    2) Statistic for year (empty all exclude year)
    3) Statistic for year and month (empty all exclude year and month)
    4) Statistic for year, month and week
    '''
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    count = models.PositiveIntegerField(default=1)

    year = models.IntegerField(db_index=True, null=True, blank=True)
    month = models.IntegerField(db_index=True, null=True, blank=True)
    week = models.IntegerField(db_index=True, null=True, blank=True)

    objects = StatisticManager()

    @property
    def statistic_type(self):
        if not self.year and not self.month and not self.week:
            return TOTAL
        if self.year and not self.month and not self.week:
            return YEAR
        if self.year and self.month and not self.week:
            return MONTH
        if self.year and self.month and self.week:
            return WEEK
        raise Exception('Invalid statistic object')

    class Meta:
        unique_together = ('content_type', 'object_id', 'year', 'month', 'week')
