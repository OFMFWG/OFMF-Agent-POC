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
#f_connections_api.py

import g
import json, os
import shutil
import requests

import traceback
import logging
import g
import urllib3
import copy

from flask import jsonify, request
from flask_restful import Resource
from api_emulator.utils import update_collections_json, create_path, get_json_data, create_and_patch_object, delete_object, patch_object, put_object, delete_collection, create_collection
from .constants import *
from .templates.connections import get_Connections_instance
from .templates.add_resource import z_add_resource_instance

members =[]
member_ids = []
config = {}
tmpStr=""
INTERNAL_ERROR = 500

# the following is temporary hack
AGENT_DB_FILE = "./agentDB.json"
agentDB ={}


# FabricsConnectionsAPI API
class FabricsConnectionsAPI(Resource):
    def __init__(self, **kwargs):
        logging.info('FabricsConnectionsAPI init called')
        self.root = PATHS['Root']
        self.fabrics = PATHS['Fabrics']['path']
        self.f_connections = PATHS['Fabrics']['f_connection']
        global agentDB

        # hack to get the agentDB
        with open(AGENT_DB_FILE, "r") as file_json:
            agentDB=json.load(file_json)
        file_json.close()

    # HTTP GET
    def get(self, fabric, f_connection):
        path = create_path(self.root, self.fabrics, fabric, self.f_connections, f_connection, 'index.json')
        #return get_json_data (path)
        return 501

    # HTTP POST
    # - Agent parses the connection and matches the connected resources
    #       to a producer, a consumer, and the proper memory chunk 
    #   and sends the add_resource request to the Zephyr fabric manager
    def post(self, fabric, f_connection):
        logging.info('FabricsConnectionsAPI POST called')
        path = create_path(self.root, self.fabrics, fabric, self.f_connections, f_connection)
        collection_path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, 'index.json')

        try:
            global config
            #  config will be the connection request from OFMF
            if request.data: 
                config= json.loads(request.data)
            
            connType = config["ConnectionType"]
            if connType != "Memory":
                print("ooops, not a memory resource connection -- exit")
                return
            print("connection passed in ", json.dumps(config,indent=4)) 
            fab_uuid = agentDB["fabricIDs"]["fab_uuid"]
            connID = config["Id"] 
            # only 1 memory chunk per connection allowed in PoC
            # find the MemoryChunk path
            tmpStr=config["MemoryChunkInfo"][0]["MemoryChunk"]["@odata.id"]
            # another hack 
            md_id = tmpStr.split("/")[6]
            mc_id= tmpStr.split("/")[-1]
            connURI = config["@odata.id"]
            tmpConn = {}
            tmpConn["@odata.id"] = connURI
            print("connection URI ",tmpConn)
            zephyrCMD_count = 0
            producers= copy.deepcopy(config["Links"]["TargetEndpoints"])
            consumers= copy.deepcopy(config["Links"]["InitiatorEndpoints"])
            print("consumers ",consumers)
            # for POC should only be one memory chunk but copy all just in case
            chunks= copy.deepcopy(config["MemoryChunkInfo"])
            print(chunks)

            # each producer(memory target) must have its own add_resource() call
            for p_index, p_item in enumerate(producers):
                # p_item is the list of producer (target) endpoints
                PchunkDetails = []
                p_nodeID=""
                p_endpt= p_item["@odata.id"].split("/")[-1]
                print("p_endpt ",p_endpt)
                p_nodeID = agentDB["endpt_xref"][p_endpt]
                p_cuuid = agentDB["nodes"][p_nodeID]["zephyrNodeIDs"]["id"]
                print("p_nodeID ",p_nodeID)
                print("p_cuuid ",p_cuuid)
                # get producer's memory resources which are used in this connection
                # all memoryChunks must be from same producer 
                # but could be more than one chunk available from the same producer
                p_Chunks=[]     # hence p_Chunks is a list
                p_Chunks=copy.deepcopy(agentDB["nodes"][p_nodeID]\
                        ["nodeProperties"]["memchunks"])
                print("p_Chunks ",json.dumps(p_Chunks,indent=4))
                # search all chunks mentioned in connection, for the link to this producer
                for con_ch_index, con_ch_item in enumerate(chunks):
                    print("connector chunk ", json.dumps(con_ch_item, indent=4))
                    conn_chunkURI=con_ch_item["MemoryChunk"]["@odata.id"]
                    print("connector chunk uri ", conn_chunkURI)
                    p_chunk_index = 0
                    for index, item in enumerate(p_Chunks):
                        p_chunkURI=p_Chunks[index]["@odata.id"]
                        print("producer chunk URI ",p_chunkURI)
                        if p_chunkURI == conn_chunkURI :
                            PchunkDetails.append(copy.deepcopy(p_Chunks[index]))
                            p_chunk_index = index  # have to save this for later

                if len(PchunkDetails) == 0:
                    print("producer not found ")
                    resp = 404
                    return resp

                #  now list all consumers of these memory chunks from this producer
                consumers_cuuid=[]
                for c_index, c_item in enumerate(consumers):
                    print("consumer check index ",c_index)
                    # need to build the list of consumers c_uuids
                    c_nodeID=""
                    c_endpt= c_item["@odata.id"].split("/")[-1]
                    print("c_endpt ",c_endpt)
                    c_nodeID = agentDB["endpt_xref"][c_endpt]
                    c_cuuid = agentDB["nodes"][c_nodeID]["zephyrNodeIDs"]["id"]
                    print("c_nodeID ",c_nodeID)
                    print("c_cuuid ",c_cuuid)
                    consumers_cuuid.append(c_cuuid)
                    #  add the connection to the consumer's node data
                    agentDB["nodes"][c_nodeID]["nodeProperties"]\
                        ["connections"].append(tmpConn)

                
                # ready to stuff the add_resource() template
                # right now, all producer memory uses the same flags, class, and class_uuid
                class_uuid=PchunkDetails[0]["class_uuid"]
                flags_int=PchunkDetails[0]["flags"]
                class_int=PchunkDetails[0]["class"]
                wildcards = { "fab_uuid":fab_uuid, "prod_cuuid":p_cuuid, \
                        "class_uuid":class_uuid, "flags_int":flags_int, \
                        "class_int":class_int}
                zephyr_body = copy.deepcopy(z_add_resource_instance(wildcards))
                # fix up some type() miss-alignments
                zephyr_body["resource"]["resources"][0]["flags"]= \
                        int(zephyr_body["resource"]["resources"][0]["flags"])
                zephyr_body["resource"]["resources"][0]["class"]= \
                        int(zephyr_body["resource"]["resources"][0]["class"])
                # add in the consumers
                zephyr_body["resource"]["consumers"] = copy.deepcopy(consumers_cuuid)
                # add in memory chunk details from producer's relevant memory chunks
                # there could be more than one chunk, but for now only one producer
                for index, item in enumerate(PchunkDetails):
                    tmpMemDetails = {}
                    tmpMemDetails["start"] = PchunkDetails[index]["start"]
                    tmpMemDetails["length"] = PchunkDetails[index]["length"]
                    tmpMemDetails["type"] = PchunkDetails[index]["type"]
                    tmpMemDetails["ro_rkey"] = PchunkDetails[index]["ro_rkey"]
                    tmpMemDetails["rw_rkey"] = PchunkDetails[index]["rw_rkey"]
                    zephyr_body["resource"]["resources"][0]["memory"].append(\
                            copy.deepcopy(tmpMemDetails))
                

                zAssigned_uuid = 'XXX'
                #  send the Zephyr command 
                #  we only send one chunk per connection, so only 1 memory resource involved
                if not "None" in g.ZEPHYR :
                    # try to reach Zephyr as defined
                    zephyr_response={}
                    zephyr_URI = g.ZEPHYR
                    postID= g.ZEPHYRADD
                    headers = {'Content-type':'application/json', 'Accept':'text/plain'}
                    r = requests.post(zephyr_URI+postID, data = json.dumps(zephyr_body),\
                            headers=headers)
                    zephyr_response = r.json()
                    z_resp=500
                    print(r)
                    # if successful;
                    if zephyr_response["callback"]["success"]:
                        #  retrieve the instance_uuid which Zephyr assigned to the chunk
                        zAssigned_uuid = zephyr_response["instance_uuids"][0]
                        z_resp=200
                        print(json.dumps(zephyr_body, indent=4))
                    else:
                        print("Zephyr did not report success")

                else:
                    # no Zephyr, 
                    print("could not find zephyr")
                    z_resp=200
                    
                # always create a record of the successful Zephyr command
                zephyr_body["resource"]["resources"][0]["instance_uuid"] =zAssigned_uuid
                if z_resp==200:

                    with open("./zephyr_cmds/zephyrCONN_"+connID+".json","w") as jdata:
                        json.dump(zephyr_body, jdata, indent=4)
                        jdata.close()
                    zephyrCMD_count = zephyrCMD_count+1
                    agentDB["nodes"][p_nodeID]["nodeProperties"]\
                            ["memchunks"][p_chunk_index]["instance_uuid"]= zAssigned_uuid
                    #  add the connection to the producer's node data
                    agentDB["nodes"][p_nodeID]["nodeProperties"]\
                        ["connections"].append(tmpConn)

            # write the DB back to file
            with open(AGENT_DB_FILE, "w") as file_json:
                json.dump(agentDB,file_json, indent=4)
            file_json.close()

            resp = config, 200

        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('FabricsConnectionsAPI POST exit')
        return resp

   
	# HTTP PATCH
    def patch(self, fabric, f_connection):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, f_connection, 'index.json')
        patch_object(path)
        #return self.get(fabric, f_connection)
        return 501

    # HTTP PUT
    def put(self, fabric, f_connection):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, f_connection, 'index.json')
        put_object(path)
        #return self.get(fabric, f_connection)
        return 501

    # HTTP DELETE
    def delete(self, fabric, f_connection):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.fabrics, fabric, self.f_connections, f_connection)
        base_path = create_path(self.root, self.fabrics, fabric, self.f_connections)
        print("running connection DELETE ---------------")
        try:
            global config
            #  config will be the connection request from OFMF
            if request.data: 
                config= json.loads(request.data)
            
            print("connection passed in ", json.dumps(config,indent=4)) 
            fab_uuid = agentDB["fabricIDs"]["fab_uuid"]
            connID = config["Id"] 
            connURI = config["@odata.id"]
            # retrieve the original resource ADD command sent to Zephyr
            with open("./zephyr_cmds/zephyrCONN_"+connID+".json","r") as jdata:
                zephyr_body= json.load(jdata)
            jdata.close()
            print("sending to zephyr:  ",json.dumps(zephyr_body, indent=4))
            # resend the same resource command to Zephyr's DELETE URI
            z_resp=500
            if not "None" in g.ZEPHYR :

                # try to reach Zephyr as defined
                zephyr_response={}
                zephyr_URI = g.ZEPHYR
                postID= g.ZEPHYRDEL
                headers = {'Content-type':'application/json', 'Accept':'text/plain'}
                r = requests.delete(zephyr_URI+postID, data = json.dumps(zephyr_body),\
                            headers=headers)
                zephyr_response = r.json()
                print(r.text)
                # if successful;
                if zephyr_response["callback"]["success"]:
                    z_resp=200
                    print(json.dumps(zephyr_response, indent = 4))
                else:
                    print("Zephyr failed the delete connection call")

            else:
                # no Zephyr, 
                print("could not find zephyr")
                z_resp=200

            #  if the zephry DELETE is successful, update the Agent DB, 
            #  then delete Connection file
            if z_resp==200:
                #   brute force:  compare all nodes' connections to this one
                for nodeID, nodeDetails in agentDB["nodes"].items():
                    # walk through all connections to each node
                    for index, connItem in enumerate(nodeDetails\
                            ["nodeProperties"]["connections"]):
                        if connItem["@odata.id"]==connURI:
                            #  Delete this list entry
                            nodeDetails["nodeProperties"]["connections"].pop(index)
                            print("deleting a connection reference ", nodeID, " ", connItem)


                # write the DB back to file

                with open(AGENT_DB_FILE, "w") as file_json:
                    json.dump(agentDB,file_json, indent=4)
                file_json.close()

                # remove the zephyr command file, as the connection is gone
                # NOTE: the memory chunk's instance_uuid assigned by zephyr is still
                # valid, but it is stored with the memory chunk
                # return the DELETE request from OFMF back to OFMF, it is expecting it
                os.remove("./zephyr_cmds/zephyrCONN_"+connID+".json")
                print("returning DELETE request to OFMF ",json.dumps(config, indent = 4))
                resp = config, 200

        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('FabricsConnectionsAPI POST exit')

        return resp

# Fabrics Connections Collection API
class FabricsConnectionsCollectionAPI(Resource):

    def __init__(self):
        self.root = PATHS['Root']
        self.fabrics = PATHS['Fabrics']['path']
        self.f_connections = PATHS['Fabrics']['f_connection']

    def get(self, fabric):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, 'index.json')
        return get_json_data (path)

    def verify(self, config):
        # TODO: Implement a method to verify that the POST body is valid
        return True,{}

    # HTTP POST Collection
    def post(self, fabric):
        self.root = PATHS['Root']
        self.fabrics = PATHS['Fabrics']['path']
        self.f_connections = PATHS['Fabrics']['f_connection']

        logging.info('FabricsConnectionsCollectionAPI POST called')

        if fabric in members:
            resp = 404
            return resp

        path = create_path(self.root, self.fabrics, fabric, self.f_connections)
        return create_collection (path, 'Connection')

    # HTTP PUT
    def put(self, fabric):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, 'index.json')
        put_object(path)
        return self.get(fabric)

    # HTTP DELETE
    def delete(self, fabric):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.fabrics, fabric, self.f_connections)
        base_path = create_path(self.root, self.fabrics, fabric)
        return delete_collection(path, base_path)
