# Copyright Notice:
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

import json
import copy
import requests

def runResetTopo(service_URI):

    headers = {'Content-type':'application/json', 'Accept':'text/plain'}

    print(service_URI)
    postID="/redfish/v1/resettopology"
    print(service_URI+postID)
    r = requests.delete(service_URI+postID, headers=headers)
    print(r)
    print(r.text)

    return
