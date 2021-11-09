def parse_connection_for_zephyr(agentDB_file,rdf_conn_file):
    print("---- build add_resource----")
    zephyr_body = {}
    wildcards = {}
    producers=[]
    consumers=[]
    tmpStr=""

    with open(rdf_conn_file,"r") as file_json:
        conn_data = json.load(file_json)
    file_json.close()

    with open(agentDB_file,"r") as file_json:
        agentDB = json.load(file_json)
    file_json.close()

    connType = conn_data["ConnectionType"]
    if connType != "Memory":
        print("ooops, not a memory resource connection -- exit")
        return

    fab_uuid = agentDB["fabricIDs"]["fab_uuid"]
    connID = conn_data["Id"]            
    zephyrCMD_count = 0
    producers= copy.deepcopy(conn_data["Links"]["TargetEndpoints"])
    consumers= copy.deepcopy(conn_data["Links"]["InitiatorEndpoints"])
    print("consumers ",consumers)
    chunks= copy.deepcopy(conn_data["MemoryChunkInfo"])
    print(chunks)

    # each producer(memory target) must have its own add_resource() call
    for p_index, p_item in enumerate(producers):
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
        p_Chunks=[]
        p_Chunks=copy.deepcopy(agentDB["nodes"][p_nodeID]["nodeProperties"]["memchunks"])
        print("p_Chunks ",json.dumps(p_Chunks,indent=4))
        # search all chunks mentioned in connection, for link to this producer
        for con_ch_index, con_ch_item in enumerate(chunks):
            print("connector chunk ", json.dumps(con_ch_item, indent=4))
            conn_chunkURI=con_ch_item["MemoryChunk"]["@odata.id"]
            print("connector chunk uri ", conn_chunkURI)
            for index, item in enumerate(p_Chunks):
                p_chunkURI=p_Chunks[index]["@odata.id"]
                print("producer chunk URI ",p_chunkURI)
                if p_chunkURI == conn_chunkURI :
                    PchunkDetails.append(copy.deepcopy(p_Chunks[index]))
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

        # ready to stuff the add_resource() template
        # right now, all producer memory uses the same flags, class, and class_uuid
        class_uuid=PchunkDetails[0]["class_uuid"]
        flags_int=PchunkDetails[0]["flags"]
        class_int=PchunkDetails[0]["class"]
        wildcards = { "fab_uuid":fab_uuid, "prod_cuuid":p_cuuid, "class_uuid":class_uuid,\
                    "flags_int":flags_int, "class_int":class_int}
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
        
        print(json.dumps(zephyr_body, indent=4))
        with open("./zephyr_add_"+connID+"_"+str(zephyrCMD_count)+ ".json","w") as jdata:
            json.dump(zephyr_body, jdata, indent=4)
            jdata.close()
        zephyrCMD_count = zephyrCMD_count+1


    return

