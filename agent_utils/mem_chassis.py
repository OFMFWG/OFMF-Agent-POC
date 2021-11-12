# Copyright Notice:
# Copyright 2016-2019 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

# get_Chassis_instance()

import copy
from flask import json

_CHASSIS_TEMPLATE = \
    {
        "@odata.id": "{rb}Chassis/{id}",
        "@odata.type": "#Chassis.1.0.0.Chassis",
        "Id": "{id}",
        "Name": "Memory Node",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },

    "Manufacturer": "Contoso",
    "Model": "Contoso Memory Node",
    "SerialNumber": "<SerialNumber>",
    "PowerState": "On",
    "IndicatorLED": "Off",
    "ChassisType": "Sled",
    "MediaControllers": {
        "@odata.id": "{rb}Chassis/{id}/MediaControllers"
    },
    "MemoryDomains": {
        "@odata.id": "{rb}Chassis/{id}/MemoryDomains"
    },
    "Links": {
        "ManagedBy": [
            {
                "@odata.id": "{rb}Managers/1"
            }
        ],
        "ManagersInChassis": [
            {
                "@odata.id": "{rb}Managers/1"
            }
        ]
      }
    }


def get_Chassis_instance(wildcards):
    
    """
    Instantiates and formats the template

    Arguments:
        wildcard - A dictionary of wildcards strings and their repalcement values
    """
    c = copy.deepcopy(_CHASSIS_TEMPLATE)
    d = json.dumps(c)
    g = d.replace('{id}', 'NUv')
    g = g.replace('{rb}', 'NUb')
    g = g.replace('{{', '~~!')
    g = g.replace('}}', '!!~')
    g = g.replace('{', '~!')
    g = g.replace('}', '!~')
    g = g.replace('NUv', '{id}')
    g = g.replace('NUb', '{rb}')
    g = g.format(**wildcards)
    g = g.replace('~~!', '{{')
    g = g.replace('!!~', '}}')
    g = g.replace('~!', '{')
    g = g.replace('!~', '}')
    return json.loads(g)

