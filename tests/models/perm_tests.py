# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from pyoko import Model, field


class Person(Model):
    name = field.String(index=True)
    section = field.String(index=True)
    phone = field.String(index=True)

    def row_level_access(self, current):
        if not current.has_permission("access_to_other_sections"):
            self.objects = self.objects.filter(section=current.user.section)

    META = {
        'field_permissions': {
            # fields will be filtered out if current user
            # doesnt have the required permissions.
            'can_see_phone_number': ['phone']
        },
    }


class MockContext(object):
    def __init__(self, **kwargs):
        self.perms = {
            'can_see_phone_number': True,
            'access_to_other_sections': True,
        }
        self.perms.update(kwargs)
        self.user = type('', (), {})
        self.user.section = 'Section_A'

    def has_permission(self, perm):
        return self.perms[perm]

    def grant(self, perm):
        self.perms[perm] = True

    def restrict(self, perm):
        self.perms[perm] = False