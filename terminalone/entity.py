# -*- coding: utf-8 -*-
"""Provides base object for T1 data classes.

Python library for interacting with the T1 API. Uses third-party module Requests
(http://docs.python-requests.org/en/latest/) to get and post data, and ElementTree
to parse it.
"""

from __future__ import absolute_import, division
from datetime import datetime
import warnings
from .connection import Connection
from .errors import ClientError
from .vendor.six import six


class Entity(Connection):
	"""Superclass for all the various T1 entities.

	Implements methods for data validation and saving to T1. Entity and its
	subclasses should not be instantiated directly; instead, an instance of
	T1 should instantiate these classes, passing in the proper session, etc.
	"""
	_readonly = {'id', 'build_date', 'created_on',
					'_type', # _type is used because "type" is taken by T1User.
					'updated_on', 'last_modified'}
	_readonly_update = set()
	def __init__(self, session, properties=None, **kwargs):
		"""Passes session to underlying connection and validates properties passed in.

		Entity, or any class deriving from it, should never be instantiated directly.
		`T1` class should, with session information, instantiate the relevant
		subclass.
		:param session: requests.Session to be used
		:param properties: dict of entity properties
		:param kwargs: additional kwargs to pass to Connection
		"""

		# __setattr__ is overridden below. So, to set self.properties as an empty
		# dict, we need to use the built-in __setattr__ method; thus, super()
		super(Entity, self).__init__(create_session=False, **kwargs)
		super(Entity, self).__setattr__('session', session)
		if properties is None:
			super(Entity, self).__setattr__('properties', {})
			return
		# This block will only execute if properties is given
		for attr, val in six.iteritems(properties):
			if self._pull.get(attr) is not None:
				properties[attr] = self._pull[attr](val)
		super(Entity, self).__setattr__('properties', properties)

	def __repr__(self):
		return '{cname}({props})'.format(
			cname=type(self).__name__,
			props=', '.join(
				'{key}={value!r}'.format(key=key, value=value)
				for key, value in six.iteritems(self.properties)
			)
		)

	def __getitem__(self, attribute):
		"""DEPRECATED way of retrieving properties like with dictionary"""
		warnings.warn(('Accessing entity like a dictionary will be deprecated; '
							'please discontinue use.'),
						DeprecationWarning, stacklevel=2)
		if attribute in self.properties:
			return self.properties[attribute]
		else:
			raise AttributeError(attribute)

	def __setitem__(self, attribute, value):
		"""DEPRECATED way of setting properties like with dictionary"""
		warnings.warn(('Accessing entity like a dictionary will be deprecated; '
							'please discontinue use.'),
						DeprecationWarning, stacklevel=2)
		self.properties[attribute] = self._pull[attribute](value)

	def __getattr__(self, attribute):
		if attribute in self.properties:
			return self.properties[attribute]
		else:
			raise AttributeError(attribute)
	def __setattr__(self, attribute, value):
		if self._pull.get(attribute) is not None:
			self.properties[attribute] = self._pull[attribute](value)
		else:
			self.properties[attribute] = value

	def __getstate__(self):
		"""Custom pickling. TODO"""
		return super(Entity, self).__getstate__()
	def __setstate__(self, state):
		"""Custom unpickling. TODO"""
		return super(Entity, self).__setstate__(state)

	@staticmethod
	def _int_to_bool(value):
		return bool(int(value))

	@staticmethod
	def _none_to_empty(val):
		if val is None:
			return ""
		return val

	@staticmethod
	def _enum(all_vars, default):
		def get_value(test_value):
			if test_value in all_vars:
				return test_value
			else:
				return default
		return get_value

	@staticmethod
	def _default_empty(default):
		def get_value(test_value):
			if test_value:
				return test_value
			else:
				return default
		return get_value

	@staticmethod
	def _strpt(ti):
		if isinstance(ti, datetime):
			return ti
		return datetime.strptime(ti, "%Y-%m-%dT%H:%M:%S")

	@staticmethod
	def _strft(ti):
		return ti.strftime("%Y-%m-%dT%H:%M:%S")

	@staticmethod
	def _valid_id(id_):
		try:
			myid = int(id_)
		except (ValueError, TypeError):
			return False
		if myid < 1:
			return False
		return True

	def _validate_read(self, data):
		for key, value in six.iteritems(data):
			if key in self._pull:
				data[key] = self._pull[key](value)
		return data

	def _validate_write(self, data):
		update = 'id' in self.properties
		if 'version' not in data and update:
			data['version'] = self.version
		for key, value in six.iteritems(data.copy()):
			if key in self._readonly or key in self._relations:
				del data[key]
			elif update and key in self._readonly_update:
				del data[key]
			else:
				if self._push.get(key) is not None:
					data[key] = self._push[key](value)
				else:
					data[key] = value
		return data

	def _update_self(self, entity):
		for key, value in six.iteritems(entity):
			setattr(self, key, value)

	def set(self, properties):
		for attr, value in six.iteritems(properties):
			setattr(self, attr, value)

	def save(self, data=None):
		if self.properties.get('id'):
			url = '/'.join([self.api_base, self.collection, str(self.id)])
		else:
			url = '/'.join([self.api_base, self.collection])
		if data is not None:
			data = self._validate_write(data)
		else:
			data = self._validate_write(self.properties)
		entity, __ = self._post(url, data=data)
		self._update_self(next(iter(entity)))

	def update(self, *args, **kwargs):
		return self.save(*args, **kwargs)

	def history(self):
		if not self.properties.get('id'):
			raise ClientError('Entity ID not given')
		url  = '/'.join([self.api_base, self.collection, str(self.id), 'history'])
		history, __ = self._get(url)
		return history

class SubEntity(Entity):
	def save(self, data=None):
		if self.properties.get('id'):
			url = '/'.join([self.api_base, self.parent, self.parent_id,
							self.collection, self.id])
		else:
			url = '/'.join([self.api_base, self.parent,
							self.parent_id, self.collection])
		if data is not None:
			data = self._validate_write(data)
		else:
			data = self._validate_write(self.properties)
		entity = self._post(url, data=data)[0][0]
		self._update_self(entity)

