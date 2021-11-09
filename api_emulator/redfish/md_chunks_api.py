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

# c_memory_api.py

import json, os
import traceback
import logging
import shutil
import copy

import g
import urllib3

from flask import jsonify, request
from flask_restful import Resource
from api_emulator.utils import update_collections_json, create_path, get_json_data, create_and_patch_object, delete_object, patch_object, put_object, delete_collection, create_collection
from .constants import *
from .templates.md_chunks import get_MDChunks_instance

members =[]
member_ids = []
config = {}
INTERNAL_ERROR = 500

# the following is temporary hack
AGENT_DB_FILE = "./agentDB.json"
agentDB ={}

# MemoryDomainAPI API
class MDChunksAPI(Resource):
    def __init__(self, **kwargs):
        logging.info('MDChunksAPI init called')
        self.root = PATHS['Root']
        self.chassis = PATHS['Chassis']['path']
        self.memory_domains = PATHS['Chassis']['memory_domain']
        self.md_chunks = PATHS['Chassis']['md_chunks']
        global agentDB

        # hack to get the agentDB
        with open(AGENT_DB_FILE, "r") as file_json:
            agentDB=json.load(file_json)
        file_json.close()


    # HTTP GET
    def get(self, chassis, memory_domain, md_chunks):
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks, 'index.json')
        #return get_json_data (path)
        return 501
    


    # HTTP POST
    # - Agent parses POST of MemoryChunk
    # - Updates the agentDB for provider node (the fabricAdapter or MediaController) memory resources
    # - evaluates if Zephyr needs to take any action
    # 
    def post(self, chassis, memory_domain, md_chunks):
        logging.info('MDChunksAPI POST called')
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks)
        collection_path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, 'index.json')

        try:
            global config
            tmpMemChunk={}
            if request.data: 
                config= json.loads(request.data)
            #  find the nodeID of the endpoint that sources the memory chunk
            #  a memory chunk may have only ONE sourcing endpoint in PoC
            ep_id = config["Links"]["Endpoints"][0]["@odata.id"].split("/")[-1]
            nodeID = agentDB["endpt_xref"][ep_id]
            numaID = 1  # PoC default, only value allowed
            #  extract the details of the mem chunk
            print("source node for mem chunk is ",nodeID)
            chunkSize=(config["MemoryChunkSizeMiB"])*(2**20)
            chunkStart=(config["AddressRangeOffsetMiB"])*(2**20)
            memClass=config["Oem"]["class"]
            md_index=agentDB["nodes"][nodeID]["zephyrNodeIDs"]["md_index"]
            daxCount=agentDB["fabricIDs"]["daxCount"]
            memType=1
            # retrieve existing chunks from this source, may be empty list
            tmpList=copy.deepcopy(agentDB["nodes"][nodeID]["nodeProperties"]["memchunks"])
            for index, item in enumerate(tmpList):
                if item["start"] == chunkStart:
                    print("ooops, chunk already exists on this node")
                    resp = 409
                    return resp


            if memClass == 2:
                class_uuid="f147276b-c2c1-431e-91af-3031d0039768"
                memFlags= numaID*(2**16) + (daxCount+1)*(2**8) + int(md_index)
            else:
                class_uuid="3cb8d3bd-51ba-4586-835f-3548789dd906"
                memFlags= 0

            # create the rest of the mem chunk details for agentDB
            ro_rkey = 0  
            rw_rkey = 0
            instance_uuid = "???"     # not used in PoC

            tmpMemChunk["@odata.id"] = config["@odata.id"]
            tmpMemChunk["class_uuid"] = class_uuid
            tmpMemChunk["instance_uuid"] = instance_uuid
            tmpMemChunk["flags"] = memFlags
            tmpMemChunk["class"] = memClass
            tmpMemChunk["type"] = memType
            tmpMemChunk["start"] = chunkStart
            tmpMemChunk["length"] = chunkSize
            tmpMemChunk["ro_rkey"] = ro_rkey
            tmpMemChunk["rw_rkey"] = rw_rkey

            if (chunkStart + chunkSize) > agentDB["nodes"][nodeID]["zephyrNodeIDs"]["max_data"] :
                print("ooops, chunk exceeds node capacity")
                resp = 500

            # add the memory chunk to agentDB
            agentDB["nodes"][nodeID]["nodeProperties"]["memchunks"].append(tmpMemChunk)
            agentDB["fabricIDs"]["daxCount"] = daxCount + 1     
            print(json.dumps(tmpMemChunk, indent=4))
            # write the DB back to the file

            with open(AGENT_DB_FILE, "w") as file_json:
                json.dump(agentDB,file_json, indent=4)
            file_json.close()

            resp = config, 200

        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('MDChunksAPI POST exit')
        return resp

    '''
    # HTTP POST
    # - Create the resource (since URI variables are available)
    # - Update the members and members.id lists
    # - Attach the APIs of subordinate resources (do this only once)
    # - Finally, create an instance of the subordiante resources
    def post(self, chassis, memory_domain, md_chunks):
        logging.info('MDChunksAPI POST called')
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks)
        collection_path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, 'index.json')

        # Check if collection exists:
        if not os.path.exists(collection_path):
            MDChunksCollectionAPI.post (self, chassis, memory_domain)

        if md_chunks in members:
            resp = 404
            return resp
        try:
            global config
            wildcards = {'c_id':chassis, 'md_id': memory_domain, 'mc_id': md_chunks, 'rb': g.rest_base}
            config=get_MDChunks_instance(wildcards)
            config = create_and_patch_object (config, members, member_ids, path, collection_path)

            # Create sub-collections:
            resp = config, 200

        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('MDChunksAPI POST exit')
        return resp
    '''
    # HTTP PATCH
    def patch(self, chassis, memory_domain, md_chunks):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks, 'index.json')
        patch_object(path)
        #return self.get(chassis, memory_domain)
        return 501

    # HTTP PUT
    def put(self, chassis, memory_domain, md_chunks):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks, 'index.json')
        put_object(path)
        #return self.get(chassis, memory_domain)
        return 501

    # HTTP DELETE
    def delete(self, chassis, memory_domain, md_chunks):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks)
        base_path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks)
        #return delete_object(path, base_path)
        return 501


# MemoryDomains Collection API
class MDChunksCollectionAPI(Resource):

    def __init__(self):
        self.root = PATHS['Root']
        self.chassis = PATHS['Chassis']['path']
        self.memory_domains = PATHS['Chassis']['memory_domain']
        self.md_chunks = PATHS['Chassis']['md_chunks']

    def get(self, chassis, memory_domain):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, 'index.json')
        return get_json_data (path)

    def verify(self, config):
        # TODO: Implement a method to verify that the POST body is valid
        return True,{}

    # HTTP POST Collection
    def post(self, chassis, memory_domain):
        self.root = PATHS['Root']
        self.chassis = PATHS['Chassis']['path']
        self.memory_domains = PATHS['Chassis']['memory_domain']

        logging.info('MDChunksCollectionAPI POST called')

        if memory_domain in members:
            resp = 404
            return resp

        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks)
        return create_collection (path, 'MemoryChunk')

    # HTTP PUT
    def put(self, chassis, memory_domain):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, 'index.json')
        put_object(path)
        return self.get(chassis)

    # HTTP DELETE
    def delete(self, chassis, memory_domain):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks)
        base_path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain)
        return delete_collection(path, base_path)
