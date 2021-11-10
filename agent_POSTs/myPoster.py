# Copyright Notice:
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

import json
import copy
import requests

def runPOSTer(infile,service_URI):
    postFile=""
    with open(infile,"r") as file_json:
        fileList = json.load(file_json)
    file_json.close()

    headers = {'Content-type':'application/json', 'Accept':'text/plain'}

    print(service_URI)
    for index, postName in enumerate(fileList):
        print("POST file is ",postName)
        postFile = postName
        with open(postFile,"r") as file_json:
            data = json.load(file_json)
        file_json.close()
        postID=data["@odata.id"]
        print(postID)
        print(data)
        r = requests.post(service_URI+postID, data=json.dumps(data), headers=headers)
        print(r)
        print(r.text)

    return
