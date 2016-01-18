# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import six

from .node import Node
from .lib.utils import un_camel, un_camel_id


class ListNode(Node):
    """
    ListNode's are used to store list of field sets.
    Their DB representation look like list of dicts:

    .. code-block:: python

        class Student(Model):
            class Lectures(ListNode):
                name = field.String()
                code = field.String(required=False)

        st = Student()
        st.Lectures(name="Math101", code='M1')
        st.Lectures(name="Math102", code='M2')
        st.clean_value()
        {
            'deleted': False,
            'timestamp': None
            'lectures': [
                {'code': 'M1', 'name': 'Math101'},
                {'code': 'M2', 'name': 'Math102'},
            ]
        }



    Notes:
        - Currently we disregard the ordering when updating items of a ListNode

    """

    # HASH_BY = '' # calculate __hash__ value by field defined here
    _TYPE = 'ListNode'

    def __init__(self, **kwargs):
        self._is_item = False
        self._from_db = False
        self.values = []
        self.node_stack = []
        self.node_dict = {}
        super(ListNode, self).__init__(**kwargs)
        self._data = []

    def _load_data(self, data, from_db=False):
        """
        Stores the data at self._data, actual object creation done at _generate_instances()
        """
        self._data = data[:]
        self._from_db = from_db

    def _generate_instances(self):
        """
        ListNode item generator. Will be used by __iter__ and __getitem__
        Yields:
            ListNode items (instances)
        """
        for node in self.node_stack:
            yield node
        while self._data:
            yield self._make_instance(self._data.pop(0))

    def _make_instance(self, node_data):
        """
        create a ListNode instance from node_data

        :param dict node_data:
        :return: ListNode item
        """
        node_data['from_db'] = self._from_db
        clone = self.__call__(**node_data)
        clone.container = self
        clone._is_item = True
        for name in self._nodes:
            _name = un_camel(name)
            if _name in node_data:  # check for partial data
                getattr(clone, name)._load_data(node_data[_name])
        _key = clone._get_linked_model_key()
        if _key:
            self.node_dict[_key] = clone
        return clone

    def _get_linked_model_key(self):
        """
        only one linked model can represent a listnode instance,
        return's the first linked models key if exists otherwise None

        :return: None | str
        """
        for lnk in self.get_links():
            return getattr(self, lnk['field']).key

    def clean_value(self):
        """
        Populates json serialization ready data.
        This is the method used to serialize and store the object data in to DB

        Returns:
            List of dicts.
        """
        result = []
        for mdl in self:
            result.append(super(ListNode, mdl).clean_value())
        return result

    def __repr__(self):
        """
        This works for two different object:
            - Main ListNode object
            - Items of the node (like instance of a class)
                which created on iteration of main object
        Returns:
            String representation of object.
        """
        if not self._is_item:
            return [obj for obj in self[:10]].__repr__()
        else:
            try:
                u = six.text_type(self)
            except (UnicodeEncodeError, UnicodeDecodeError):
                u = '[Bad Unicode data]'
            return six.text_type('<%s: %s>' % (self.__class__.__name__, u))

    # def __hash__(self):
    #     if self.HASH_BY:
    #         return hash(getattr(self, self.HASH_BY))

    def add(self, **kwargs):
        """
        Stores node data without creating an instance of it.
        This is more efficient if node instance is not required.

        Args:
            kwargs: attributes of the ListNode
        """
        self._data.append(kwargs)

    def __call__(self, **kwargs):
        """
        Stores created instance in node_stack and returns it's reference to callee
        """
        kwargs['_root_node'] = self._root_node
        clone = self.__class__(**kwargs)
        # clone._root_node = self._root_node
        clone._is_item = True
        self.node_stack.append(clone)
        _key = clone._get_linked_model_key()
        if _key:
            self.node_dict[_key] = clone
        return clone

    def clear(self):
        """
        Clear outs the list node.
        """
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack = []
        self._data = []

    def __contains__(self, item):
        if self._data:
            return any([d[un_camel_id(item.__class__.__name__)] == item.key for d in self._data])
        else:
            return item.key in self.node_dict

    def __len__(self):
        return len(self._data or self.node_stack)

    def __getitem__(self, index):
        return list(self._generate_instances()).__getitem__(index)

    def __iter__(self):
        return self._generate_instances()

    def __setitem__(self, key, value):
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack[key] = value

    def __delitem__(self, obj):
        if self._is_item:
            raise TypeError("This an item of the parent ListNode")
        self.node_stack.remove(obj)

    def remove(self):
        """
        Removes this item from ListNode.

        Note:
            Parent object should be explicitly saved.
        """
        if not self._is_item:
            raise TypeError("A ListNode cannot be deleted")
        self.container.node_stack.remove(self)
