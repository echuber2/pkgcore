# Copyright: 2005 Gentoo Foundation
# License: GPL2
# $Id: mappings.py 2284 2005-11-10 00:35:50Z ferringb $

from itertools import imap, chain
import UserDict


def _munchValues(key, value):
	return key + '/' + value


class FrozenIndexableSequence(object):

	"""Strange hybrid of a dynamically-generated dict and a sequence.

	__getitem__, items, iteritems, keys, iterkeys and __contains__
	work as if this is a dict, with all values sequences. Valid keys
	and values are determined by a pair of functions passed in on
	construction.

	__len__ and __iter__ work as if this is a sequence generated by:
	for key in self.iterkeys():
		for val in self[key]:
			yield self.returnIterFunc(key, val)
	where returnIterFunc defaults to a function returning "key + '/' + val".
	"""
	
	def __init__(
		self, get_keys, get_values, recursive=False, returnEmpty=False, 
		returnIterFunc=_munchValues):
		"""Initialize.

		get_keys is a no-argument function returning a sequence of keys.
		get_values is a function taking a key, returning a sequence of values.
		get_values must raise KeyError on receiving a key not in get_keys or
		weirdness ensues.
		recursive disables some caching if True. TODO clarify.
		returnEmpty makes iteration also return keys with no values.
		returnIterFunc is a function taking a key and value. Its return value
		is what iteration returns. Defaults to returning "key + '/' + value".
		"""
		self._get_keys = get_keys
		self._get_values = get_values
		self._cache = {}
		self._cache_complete = False
		self._cache_can_be_complete = not recursive
		self._return_empty = returnEmpty
		self._returnFunc = returnIterFunc

	def __getitem__(self, key):
		if not (self._cache_complete or self._cache.has_key(key)):
			self._cache[key] = self._get_values(key)
		return self._cache[key]

	def keys(self):
		return list(self.iterkeys())

	def __contains__(self, key):
		try:	
			self[key]
			return True
		except KeyError:
			return False

	def iterkeys(self):
		if self._cache_complete:
			return self._cache.iterkeys()
		else:
			return chain(self._cache.iterkeys(), self._gen_keys())

	def __len__(self):
		count = 0
		for x in self.__iter__(disable_return=True):
			count += 1
		return count

	def _gen_keys(self):
		for key in self._get_keys():
			if key not in self._cache:
				self._cache[key] = self._get_values(key)
				yield key
		self._cache_complete = self._cache_can_be_complete
		return

	def __iter__(self, disable_return=False):
		if disable_return:
			def func(key, val):
				return key, val
		else:
			func = self._returnFunc
			
		for key, value in self.iteritems():
			if len(value) == 0:
				if self._return_empty:
					yield key
			else:
				for x in value:
					yield func(key, x)

	def items(self):
		return list(self.iteritems())

	def iteritems(self):
		if self._cache_complete:
			for key, value in self._cache.iteritems():
				yield key, value
			return
		for key in self._cache.keys():
			yield key, self[key]
		for key in self._gen_keys():
			yield key, self[key]


class ModifiableIndexableSequence(FrozenIndexableSequence):

	"""This class is broken. Fix it before you use it."""
	
	def __init__(
		self, get_keys, get_values, delfunc, updatefunc, recursive=False,
		returnEmpty=False, returnIterFunc=None):
		raise Exception('I am broken. Do not use me.')
		FrozenIndexableSequence.__init__(
			self, get_keys, get_values, recursive, returnEmpty,
			returnIterFunc)
		self._cache_can_be_complete = False
		self._del_func = delfunc
		self._update_func = updatefunc

	def __delitem__(self, key):
		if not key in self:
			raise KeyError(key)
		return self._del_func(key)

	def __setitem__(self, key, value):
		if not key in self:
			raise KeyError(key)
		return self._update_func(key, value)
	

# TODO get rid of this, reliant on portage.repository.prototype cleanups, and portage.config.central
def IndexableSequence(
	get_keys, get_values, recursive=False, returnEmpty=False, 
	returnIterFunc=_munchValues, modifiable=False, delfunc=None,
	updatefunc=None):
	if modifiable:
		if delfunc is None or updatefunc is None:
			raise ValueError('need delfunc and updatefunc for modifiable')
		return ModifiableIndexableSequence(
			get_keys, get_values, delfunc, updatefunc, recursive, returnEmpty,
			returnIterFunc)
	else:
		return FrozenIndexableSequence(
			get_keys, get_values, recursive, returnEmpty, returnIterFunc)
	

class LazyValDict(UserDict.DictMixin):
	"""
	given a function to get keys, and to look up the val for those keys, it'll 
	lazy load key definitions, and values as requested
	"""
	def __init__(self, get_keys_func, get_val_func):
		"""
		get_keys_func is a callable that is JIT called with no args	 returns a tuple of keys, or is a list
		get_val_func is a callable that is JIT called with the key requested
		"""
		if not callable(get_val_func):
			raise TypeError("get_val_func isn't a callable")
		if callable(get_keys_func):
			self.__keys_func = get_keys_func
		else:
			try:
				self.__keys = set(get_keys_func)
				self.__keys_func = None
			except TypeError:
				raise TypeError("get_keys_func isn't iterable nor is it callable")
		self.__val_func = get_val_func
		self.__vals = {}


	def __setitem__(self, key, value):
		raise AttributeError


	def __delitem__(self, key):
		raise AttributeError


	def __getitem__(self, key):
		if self.__keys_func != None:
			self.__keys = set(self.__keys_func())
			self.__keys_func = None
		if key in self.__vals:
			return self.__vals[key]
		if key in self.__keys:
			v = self.__vals[key] = self.__val_func(key)
			return v
		raise KeyError(key)


	def keys(self):
		if self.__keys_func != None:
			self.__keys = set(self.__keys_func())
			self.__keys_func = None
		return list(self.__keys)


	def __contains__(self, key):
		if self.__keys_func != None:
			self.__keys = set(self.__keys_func())
			self.__keys_func = None
		return key in self.__keys

	has_key = __contains__


class ProtectedDict(UserDict.DictMixin):
	"""
	given an initial dict, this wraps that dict storing changes in a secondary dict, protecting
	the underlying dict from changes
	"""
	__slots__=("orig","new","blacklist")

	def __init__(self, orig):
		self.orig = orig
		self.new = {}
		self.blacklist = {}


	def __setitem__(self, key, val):
		self.new[key] = val
		if key in self.blacklist:
			del self.blacklist[key]


	def __getitem__(self, key):
		if key in self.new:
			return self.new[key]
		if key in self.blacklist:
			raise KeyError(key)
		return self.orig[key]


	def __delitem__(self, key):
		if key in self.new:
			del self.new[key]
			return
		elif key in self.orig:
			if key not in self.blacklist:
				self.blacklist[key] = True
				return
		raise KeyError(key)
			

	def __iter__(self):
		for k in self.new.iterkeys():
			yield k
		for k in self.orig.iterkeys():
			if k not in self.blacklist and k not in self.new:
				yield k


	def keys(self):
		return list(self.__iter__())


	def has_key(self, key):
		return key in self.new or (key not in self.blacklist and key in self.orig)


class Unchangable(Exception):
	def __init__(self, key):	self.key = key
	def __str__(self):			return "key '%s' is unchangable" % self.key


class InvertedContains(set):
	"""negate the __contains__ return from a set
	mainly useful in conjuection with LimitedChangeSet for converting from blacklist to whitelist
	"""
	def __contains__(self, key):
		return not set.__contains__(self, key)

class LimitedChangeSet(object):
	"""
	set that supports limited changes, specifically deleting/adding a key only once per commit, 
	optionally blocking changes to certain keys.
	"""
	_removed	= 0
	_added		= 1

	def __init__(self, initial_keys, unchangable_keys=None):
		self.__new = set(initial_keys)
		if unchangable_keys == None:
			self.__blacklist = []
		else:
			if isinstance(unchangable_keys, (list, tuple)):
				unchangable_keys = set(unchangable_keys)
			self.__blacklist = unchangable_keys
		self.__changed = set()
		self.__change_order = []
		self.__orig = frozenset(self.__new)

	def add(self, key):
		if key in self.__changed or key in self.__blacklist:
			# it's been del'd already once upon a time.
			raise Unchangable(key)

		self.__new.add(key)
		self.__changed.add(key)
		self.__change_order.append((self._added, key))

	def remove(self, key):
		if key in self.__changed or key in self.__blacklist:
			raise Unchangable(key)
		
		if key in self.__new:
			self.__new.remove(key)
		self.__changed.add(key)
		self.__change_order.append((self._removed, key))

	def __contains__(self, key):
		return key in self.__new

	def changes_count(self):
		return len(self.__change_order)

	def commit(self):
		self.__orig = frozenset(self.__new)
		self.__changed.clear()
		self.__change_order = []

	def rollback(self, point=0):
		l = self.changes_count()
		if point < 0 or point > l:
			raise TypeError("%s point must be >=0 and <= changes_count()" % point)
		while l > point:
			change, key = self.__change_order.pop(-1)
			self.__changed.remove(key)
			if change == self._removed:
				self.__new.add(key)
			else:
				self.__new.remove(key)					
			l -= 1

	def __str__(self):
		return str(self.__new).replace("set(","LimitedChangeSet(", 1)

	def __iter__(self):
		return iter(self.__new)

	def __len__(self):
		return len(self.__new)


class ImmutableDict(dict):
	"""Immutable Dict, non changable after instantiating"""

	def __delitem__(self, *args):
		raise TypeError("non modifiable")

	__setitem__ = __delitem__
	clear = __delitem__
	update = __delitem__
	pop = __delitem__
	popitem = __delitem__
	setdefault = __delitem__
	
	def __hash__(self):
		k = self.items()
		k.sort(lambda x, y: cmp(x[0], y[0]))
		return hash(tuple(k))
	
	__delattr__ = __setitem__
	__setattr__ = __setitem__

class IndeterminantDict(dict):
	"""A wrapped dict with a constant dict, and a fallback function to pull keys"""
	def __init__(self, pull_func, starter_dict=None):
		if starter_dict is None:
			self.__initial = {}
		else:
			self.__initial = starter_dict
		self.__pull = pull_func
		
	def __getitem__(self, key):
		if key in self.starter_dict:
			return self.starter_dict[key]
		else:
			return self.__pull(key)

	def __hash__(self):
		raise TypeError("non hashable")
	
	def __delitem__(self, *args):
		raise TypeError("non modifiable")

	clear = update = pop = popitem = setdefault = __setitem__ = __delitem__
	__delattr__ = __setattr__ = __iter__ = keys = values = __len__ = __delitem__
	
