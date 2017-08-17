# -*- coding: utf-8 -*-
"""Provides budget_flight object."""

from __future__ import absolute_import
from .. import t1types
from ..entity import Entity
from ..errors import ClientError


class BudgetFlight(Entity):
    """BudgetFlight entity."""
    collection = 'budget_flights'
    resource = 'budget_flight'
    _relations = {
        'campaign',
    }
    _pull = {
        'campaign_id': int,
        'created_on': t1types.strpt,
        'id': int,
        'name': None,
        'updated_on': t1types.strpt,
        'version': int,
        'currency_code': None,
        "zone_name": None,
        "is_relevant": t1types.int_to_bool,
        'start_date': t1types.strpt,
        'end_date': t1types.strpt,
        "total_budget": float,
    }
    _push = _pull.copy()

    _readonly = Entity._readonly | {'campaign_id', 'zone_name', 'is_relevant', 'currency_code'}

    def __init__(self, session, properties=None, **kwargs):
        super(BudgetFlight, self).__init__(session, properties, **kwargs)

    def save(self, data=None, url=None):
        try:
            self.__getattr__('campaign_id')
        except AttributeError:
            raise ClientError('Campaign ID not given')
        url = 'campaigns/{}/'.format(self.campaign_id) + self._construct_url()
        print(url)

        if data is None:
            data = self._properties.copy()

        super(BudgetFlight, self).save(data=data, url=url)
