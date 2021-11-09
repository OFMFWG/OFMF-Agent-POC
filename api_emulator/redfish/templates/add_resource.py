# Copyright Notice:
# Copyright 2017-2019 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

# Example z_add_resource_instance() body template
#  will need to append memory resource descriptions to memory[] list

import copy
import strgen
import json

_TEMPLATE = \
{
    "fabric_uuid": "{fab_uuid}",
    "resource":
        {
               "producer":   "{prod_cuuid}",
               "consumers": [],
               "resources": [
                 {
                   "class_uuid": "{class_uuid}",
                   "instance_uuid": "???",
                   "flags": "{flags_int}",
                   "class": "{class_int}",
                   "memory": [
                   ]
                 }
               ]
        }
}

def z_add_resource_instance(wildcards):
    """
    Instantiate and format the template

    Arguments:
        wildcard - A dictionary of wildcards strings and their repalcement values

    """
    c = copy.deepcopy(_TEMPLATE)
    d = json.dumps(c)
    g = d.replace('{fab_uuid}', 'NUv')
    g = g.replace('{prod_cuuid}', 'NUb')
    g = g.replace('{class_uuid}', 'NUd')
    g = g.replace('{flags_int}', 'NUf')
    g = g.replace('{class_int}', 'NUg')
    g = g.replace('{{', '~~!')
    g = g.replace('}}', '!!~')
    g = g.replace('{', '~!')
    g = g.replace('}', '!~')
    g = g.replace('NUv', '{fab_uuid}')
    g = g.replace('NUb', '{prod_cuuid}')
    g = g.replace('NUd', '{class_uuid}')
    g = g.replace('NUf', '{flags_int}')
    g = g.replace('NUg', '{class_int}')
    g = g.format(**wildcards)
    g = g.replace('~~!', '{{')
    g = g.replace('!!~', '}}')
    g = g.replace('~!', '{')
    g = g.replace('!~', '}')
    return json.loads(g)

