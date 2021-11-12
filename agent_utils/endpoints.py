#
# Copyright (c) 2017-2021, The Storage Networking Industry Association.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of The Storage Networking Industry Association (SNIA) nor
# the names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#  THE POSSIBILITY OF SUCH DAMAGE.
#

# get_Endpoints_instance()

import copy
from flask import json

_TEMPLATE = \
{
  "@Redfish.Copyright": "Copyright 2014-2021 SNIA. All rights reserved.",
  "@odata.id": "{rb}Fabrics/{f_id}/Endpoints/{ep_id}",
  "@odata.type": "#Endpoint.v1_0_0.Endpoint",
  "Description": "INVALID",
  "Id": "{ep_id}",
  "Name": "INVALID",
  "EndpointProtocol": "GenZ",
  "Status": {
    "State": "Enabled",
    "Health": "OK"
  },

  "ConnectedEntities": [
        {
            "EntityType": "INVALID",
            "GenZ": {
                "GCID": {
                    "CID": "ZZZZ",
                    "SID": "ZZZ"
                },
                "AccessKey": "ZZZZZZ"
            },
            "EntityLink": {
                "@odata.id": "INVALID"
            }
        }
    ],
   "Links": {
        "Connections": [
        ]
    }
}


def get_Endpoints_instance(wildcards):
    """
    Instantiates and formats the template

    Arguments:
        wildcard - A dictionary of wildcards strings and their repalcement values
    """
    c = copy.deepcopy(_TEMPLATE)
    d = json.dumps(c)
    g = d.replace('{ep_id}', 'NUv')
    g = g.replace('{rb}', 'NUb')
    g = g.replace('{f_id}', 'NUs')
    g = g.replace('{{', '~~!')
    g = g.replace('}}', '!!~')
    g = g.replace('{', '~!')
    g = g.replace('}', '!~')
    g = g.replace('NUv', '{ep_id}')
    g = g.replace('NUb', '{rb}')
    g = g.replace('NUs', '{f_id}')
    g = g.format(**wildcards)
    g = g.replace('~~!', '{{')
    g = g.replace('!!~', '}}')
    g = g.replace('~!', '{')
    g = g.replace('!~', '}')
    return json.loads(g)
