# Copyright Notice:
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

#from requests.auth import HTTPDigestAuth
import json
import copy
import requests
from md_chunks import get_MDChunks_instance
from connections import get_Connections_instance

def get_connections(service_URI,f_id, connInventory):
    listConns = []
    maxConnID =0
    rb="/redfish/v1"
    headers = {"Content-type":"application/json" }
    print("get all Connections on this fabric")
    postID=rb + "/Fabrics/"+f_id+"/Connections"
    print(service_URI+postID)
    print("----")
    r = requests.get(service_URI+postID, headers=headers)
    print(r)
    data = json.loads(r.text)
    print(json.dumps(data, indent =4 ))
    connInventory[f_id]={}           # clear out the connection dict for the fabric
    connInventory[f_id]["connections"]={}
    listConns = copy.deepcopy(data["Members"])
    print(listConns)                   # grab list of systems
    for k,v in enumerate(listConns):   # for each connection in list
        print(k,"\n", json.dumps(v, indent=4))
        tmpConnID=v["@odata.id"].split("/")[-1]
        intConnID=int(tmpConnID)
        if intConnID > maxConnID:
            maxConnID=intConnID
        print("searching connection ",tmpConnID)
        connInventory[f_id]["connections"][tmpConnID]={}      #make a dict with Connection ID
        print("---- processing connID ", tmpConnID," of Fabric", f_id)
        print(v)
        # grab the connection object
        postID=v["@odata.id"]
        print(postID)                   # postID is @odata.id of connection
        r = requests.get(service_URI+postID, headers=headers)
        print(r)
        data = json.loads(r.text)
        print(json.dumps(data, indent =4 ))
        tmpList=data["Links"]["InitiatorEndpoints"][0]["@odata.id"]
        connInventory[f_id]["connections"][tmpConnID]["InitiatorEndptURI"]=tmpList
        tmpList=data["Links"]["TargetEndpoints"][0]["@odata.id"]
        connInventory[f_id]["connections"][tmpConnID]["TargetEndptURI"]=tmpList
        tmpList=data["MemoryChunkInfo"][0]["MemoryChunk"]["@odata.id"]
        connInventory[f_id]["connections"][tmpConnID]["MemoryChunkURI"]= tmpList
        tmpList=data["ConnectionType"]
        connInventory[f_id]["connections"][tmpConnID]["ConnectionType"]= tmpList
        tmpList=data["Status"]["State"]
        connInventory[f_id]["connections"][tmpConnID]["State"]= tmpList

    connInventory[f_id]["maxID"]=maxConnID

    return

def get_systems(service_URI,sysInventory):

    listSystems = []
    listEndpts = ""
    listFabricAdapters = ""
    tmpFabricAdapter = {}
    tmpSys={}
    tmpSysID=""
    tmpFA_ID=""
    tmpList=[]
    rb="/redfish/v1"
    headers = {"Content-type":"application/json" }

    print("get all Systems")
    postID=rb + "/Systems"
    print(service_URI+postID)
    print("----")
    r = requests.get(service_URI+postID, headers=headers)
    print(r)
    data = json.loads(r.text)
    print(json.dumps(data, indent =4 ))
    listSystems = copy.deepcopy(data["Members"])
    print(listSystems)                   # grab list of systems
    for k,v in enumerate(listSystems):   # for each system in list
        print(k,"\n", json.dumps(v, indent=4))
        tmpSysID=v["@odata.id"].split("/")[-1]
        print("searching system ",tmpSysID)
        sysInventory[tmpSysID]={}      #make a dict with System ID
        # grab list of FabricAdapters in this system
        postID=rb + "/Systems" +"/" + tmpSysID +"/FabricAdapters"
        print(postID)
        r = requests.get(service_URI+postID, headers=headers)
        print(r)
        data = json.loads(r.text)
        print(json.dumps(data, indent =4 ))
        listFabricAdapters = copy.deepcopy(data["Members"])
        print(json.dumps(listFabricAdapters, indent = 4))                   
        for tmpFA_ID,FA_URI in enumerate(listFabricAdapters):
            print("---- processing FA ", tmpFA_ID," of System", tmpSysID)
            print(FA_URI)
            # grab list of FabricAdapters in this system
            postID=FA_URI["@odata.id"]
            print(postID)
            r = requests.get(service_URI+postID, headers=headers)
            print(r)
            data = json.loads(r.text)
            print(json.dumps(data, indent =4 ))
            tmpFA_ID=postID.split("/")[-1]
            sysInventory[tmpSysID][tmpFA_ID]={}
            tmpList=data["Links"]["Endpoints"][0]["@odata.id"]
            sysInventory[tmpSysID][tmpFA_ID]["EndptURI"]=tmpList
            sysInventory[tmpSysID][tmpFA_ID]["fabricID"]=tmpList.split("/")[4]
            sysInventory[tmpSysID][tmpFA_ID]["size"]=data["GenZ"]["max_data"]
            sysInventory[tmpSysID][tmpFA_ID]["EndptID"]=tmpList.split("/")[-1]
            sysInventory[tmpSysID][tmpFA_ID]["serialNumber"]=data["SerialNumber"]
            sysInventory[tmpSysID][tmpFA_ID]["runState"]=data["Status"]["State"]
            sysInventory[tmpSysID][tmpFA_ID]["connections"]={}


    return

def get_memDomains(service_URI,memInventory):
    listFabrics = ""
    listEndpts = ""
    listMemDomains = ""
    listMemChunks = ""
    listChassis = ""
    tmpDomain = {}
    tmpChunk = {}
    tmpFabric=""
    tmpStart=0
    rb="/redfish/v1"
    headers = {"Content-type":"application/json" }

    print("get all memory domains")
    postID=rb + "/Fabrics"
    print(service_URI+postID)
    print("----")
    r = requests.get(service_URI+postID, headers=headers)
    print(r)
    data = json.loads(r.text)
    print(json.dumps(data, indent =4 ))
    listFabrics = copy.deepcopy(data["Members"])
    #print(listFabrics)                   # grab list of fabrics
    for k,v in enumerate(listFabrics):   # for each fabric in list
        tmpFabric=v["@odata.id"].split("/")[-1]
        print("searching fabric ",tmpFabric)
        memInventory[tmpFabric]={}      #make a dict with fabric ID
        # grab list of MemoryDomains
        postID=rb + "/Chassis" +"/" + tmpFabric +"/MemoryDomains"
        print(postID)
        r = requests.get(service_URI+postID, headers=headers)
        print(r)
        data = json.loads(r.text)
        print(json.dumps(data, indent =4 ))
        listMemDomains = copy.deepcopy(data["Members"])
        #print(listMemDomains)                   
        for k,v in enumerate(listMemDomains):   # for each memDomain in list
            tmpDomain={}
            tmpDomNum = v["@odata.id"].split("/")[-1]
            tmpMaxChunkID=0
            tmpMinChunkSize=0
            # grab memory domain details
            postID=rb + "/Chassis" +"/" + tmpFabric +"/MemoryDomains" + "/" +tmpDomNum
            print("searching ",postID)
            r = requests.get(service_URI+postID, headers=headers)
            print(r)
            data = json.loads(r.text)
            print(json.dumps(data, indent =4 )) 

            # extract important details of each domain
            tmpDomain["fabricID"]=tmpFabric
            tmpDomain["memDomain"]=tmpDomNum
            tmpDomain["maxChunkID"]=tmpMaxChunkID
            tmpDomain["memDomURI"]=data["@odata.id"]
            tmpDomain["size"]=data["GenZ"]["max_data"]
            tmpDomain["maxChunks"]=data["GenZ"]["maxChunks"]
            tmpMinChunkSize=data["GenZ"]["minChunkSize"]
            tmpDomain["minChunkSize"]=tmpMinChunkSize
            tmpDomain["block_enabled"]=data["AllowsBlockProvisioning"]
            tmpDomain["chunk_enabled"]=data["AllowsMemoryChunkCreation"]
            tmpDomain["memSource"]=data["Links"]["MediaControllers"]["@odata.id"]
            # trace the memory source to its endpoint via the memory source
            postID=tmpDomain["memSource"]
            print("searching ",postID)
            r = requests.get(service_URI + postID, headers=headers)
            print(r)
            sourceData = json.loads(r.text)
            print(json.dumps(sourceData, indent=4))
            tmpDomain["EndptURI"]=sourceData["Links"]["Endpoints"][0]["@odata.id"] 
            tmpDomain["serialNumber"]=sourceData["SerialNumber"]
            tmpDomain["runState"]=sourceData["Status"]["State"]
            tmpDomain["MemoryChunks"] = {}
            memInventory[tmpFabric][tmpDomNum] = {}
            memInventory[tmpFabric][tmpDomNum]= copy.deepcopy(tmpDomain)

            #  now extract the chunks assigned to this domain
            postID=data["MemoryChunks"]["@odata.id"]
            print("searching ", postID)
            r = requests.get(service_URI+postID, headers=headers)
            print(r)
            if "200" in str(r):                 #found memory chunks collection
                data = json.loads(r.text)
                #print(data)
                print(json.dumps(data, indent =4 ))
                listMemChunks = copy.deepcopy(data["Members"])
                #print(listMemChunks)                   
                for k,v in enumerate(listMemChunks):   # for each memory chunk in list
                    tmpChunk={}
                    tmpStart=0
                    tmpChunkNum = v["@odata.id"].split("/")[-1]
                    print("tmpChunkNum =",tmpChunkNum)
                    print("tmpDom_chunknum =",tmpDomain["maxChunkID"])
                    # track highest chunkID number found
                    if int(tmpChunkNum) > tmpMaxChunkID:
                        tmpMaxChunkID = int(tmpChunkNum)
                    # grab memory chunk details
                    postID="/" + v["@odata.id"]
                    print("searching ",postID)
                    r = requests.get(service_URI+postID, headers=headers)
                    print(r)
                    data = json.loads(r.text)
                    #print(json.dumps(data, indent =4 )) 
                    # extract important details of each chunk
                    tmpStart = data["AddressRangeOffsetMiB"]*(2**20)
                    tmpChunk["fabricID"]=tmpFabric
                    tmpChunk["memDomain"]=tmpDomNum
                    tmpChunk["chunkID"]=data["Id"]
                    tmpChunk["minChunkSize"] = tmpMinChunkSize
                    # following endpoint extraction is PoC specific!!
                    tmpChunk["EndptURI"]=data["Links"]["Endpoints"][0]["@odata.id"] 
                    tmpChunk["size_in_bytes"]=data["MemoryChunkSizeMiB"]*(2**20)
                    tmpChunk["start_in_bytes"]=data["AddressRangeOffsetMiB"]*(2**20)
                    tmpChunk["mediaType"]=data["AddressRangeType"]
                    tmpChunk["use_status"]="busy"   # ["free","busy"] bookkeeping status
                    #print(tmpChunk)
                    # update the max ChunkID found for the memory domain
                    memInventory[tmpFabric][tmpDomNum]["maxChunkID"] = tmpMaxChunkID
                    # put the chunks found into the DB for the memory domain
                    memInventory[tmpFabric][tmpDomNum]["MemoryChunks"][tmpStart] = \
                            copy.deepcopy(tmpChunk)
    return


            
def sort_chunks(memInventory):
    tmpFabricID=""

    for k,v in memInventory.items():  #for every fabric found
        tmpFabricID=k               # grab the fabric name
        for memDomNum, memDomain in v.items():  # for every MD found
            unsorted_chunks={}          # sort the memory chunks in each MD
            sorted_chunks={}
            unsorted_chunks=copy.deepcopy(memInventory[tmpFabricID][memDomNum]["MemoryChunks"])
            sorted_chunks=dict(sorted(unsorted_chunks.items(), key=lambda item: item[0]))
            memInventory[tmpFabricID][memDomNum]["MemoryChunks"] = copy.deepcopy(sorted_chunks)
    return

def make_free_list(memInventory,freeList,busyList):
    tmpFabricID=""
    freeList=[]
    busyList=[]
    tmpChunk={}

    for k,v in memInventory.items():  #for every fabric found
        tmpFabricID=k               # grab the fabric name
        for memDomNum, memDomain in v.items():  # for every MD found
            sorted_chunks={}
            sorted_chunks=copy.deepcopy(memInventory[tmpFabricID][memDomNum]["MemoryChunks"])
            for chunk_start, chunk_body in sorted_chunks.items():  # for every block found
                if chunk_body["use_status"] == 'free':
                    freeList.append(chunk_body)
                if chunk_body["use_status"] == 'busy':
                    busyList.append(chunk_body)
            
        print("busyList ---", json.dumps(busyList,indent=4))
        print("freeList ---", json.dumps(freeList,indent=4))
        print_free_list(freeList)
        print_free_list(busyList)
    return

def print_free_list(freeList):
    f_id="GenZxxx"
    md_id="0"
    stat="none"
    ch_id="0"
    size=0
    start=0
    ep_id="0"
    wildcards={}

    hdr="\nStatus\tMemoryDomain\tChunk\tSize\t\tStart\t\tEndpt\tFabric"
    print("\n-------------------------------------------------------------\n",hdr)
    for index,block in enumerate(freeList):
        stat=block["use_status"]
        md_id=block["memDomain"]
        ch_id=block["chunkID"]
        size=block["size_in_bytes"]
        start=block["start_in_bytes"]
        ep_id=block["EndptURI"].split("/")[-1]
        f_id=block["fabricID"]
        print(stat,"\t",md_id,"\t\t",ch_id,"\t",size,"\t",start,"\t\t",ep_id,"\t",f_id)


    return


def create_connection(service_URI,headers,memInventory,sysInventory,connInventory,\
                fabricID,domainNum,chunkID,sysID,fa_ID):
    print("creating connection" )
    found=False
    wildcards={}
    ofmf_body={}
    tmpList=[]
    tmpStr=""
    tmpDict={}
    rb="/redfish/v1/"
    connID=str(connInventory[fabricID]["maxID"]+1)
    connURI = rb +"Fabrics/" + fabricID + "/Connections/" + connID
    wildcards = {"rb":rb, "f_id":fabricID,"c_id":connID}
    ofmf_body = copy.deepcopy(get_Connections_instance(wildcards)) 

    # grab the initiator endpoint from the system fabric adapter
    tmpStr = sysInventory[sysID][fa_ID]["EndptURI"]
    ofmf_body["Links"]["InitiatorEndpoints"].append({"@odata.id":tmpStr})

    # grab the target endpoint from the memory chunk 
    tmpStr = memInventory[fabricID][domainNum]["EndptURI"]
    ofmf_body["Links"]["TargetEndpoints"].append({"@odata.id":tmpStr})

    # fill in the memory chunk details
    tmpStr = rb + "Chassis/" + fabricID + "/MemoryDomains/" + \
            domainNum + "/MemoryChunks/" +chunkID
    tmpDict["MemoryChunk"]={"@odata.id": tmpStr}
    tmpDict["AccessCapabilities"]=["Read","Write"]
    tmpDict["AccessState"]=["Optimized"]
    ofmf_body["MemoryChunkInfo"].append(tmpDict)

    print(json.dumps(ofmf_body, indent = 4))
    #  just write the new memory chunk POST file for later use
    json_file=""
    json_file=("./iPOSTconn_"+connID+".json")
    print()
    print("posting file ", json_file)
    # hack for testing
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        jdata.close()

    postID=ofmf_body["@odata.id"]
    print ("POST")
    print(service_URI+postID)
    r = requests.post(service_URI+postID, data=json.dumps(ofmf_body),\
                headers=headers)
    print(r)
    data = json.loads(r.text)
    print(json.dumps(data, indent =4 ))

    return

def delete_connection(service_URI, headers, connInventory ):
    # select connection to delete
    req_fabricID=""
    req_connID=""
    postID=""
    data=""

    rb="/redfish/v1"
    req_fabricID=str(input("use which fabric? >"))
    req_connID=str(input("use which connection? >"))
    postID=rb+"/Fabrics/" + req_fabricID +"/Connections/" + req_connID
    print(service_URI+postID)
    print("----")
    r = requests.get(service_URI+postID, data=json.dumps(data),\
                headers=headers)
    print(r)
    if "200" in str(r):                 #found connection
        data = json.loads(r.text)
        print(json.dumps(data, indent =4 ))
        # just need to check for connection in use
        # get the connections list for this fabric
        # verify this chunk is not part of an existing connection
        #
        # go ahead and delete this connection

        r = requests.delete(service_URI+postID, data=json.dumps(data),\
                    headers=headers)
        print(r)
    else:
        print("Connection not found ")
        print(r.text)


    return


def create_chunk(service_URI,headers,memInventory,fabricID,domainNum,size_in_MiB,memClass):
    print("creating chunk of ",size_in_MiB," MBytes")
    reqSize=size_in_MiB * (2**20)
    found=False
    newChunkID=""
    wildcards={}
    ofmf_body={}
    tmpList=[]

    for chunk_start, chunk_body in memInventory[fabricID][domainNum]["MemoryChunks"].items():
        if chunk_body["size_in_bytes"] >= reqSize:
            if chunk_body["use_status"] == 'free':
                found=True
                newChunkID=str(memInventory[fabricID][domainNum]["maxChunkID"] + 1)
                tmpList=memInventory[fabricID][domainNum]["memDomURI"].split("/")
                print(tmpList)
                rb="/" + tmpList[1]+"/"+tmpList[2] +"/"
                c_id=tmpList[4]
                md_id=tmpList[6]
                mc_id=newChunkID
                # build the new chunk here
                # call the template
                # transfer necessary details to template
                wildcards = {"rb":rb, "c_id":c_id,"md_id":md_id, "mc_id":mc_id }
                ofmf_body = copy.deepcopy(get_MDChunks_instance(wildcards)) 
                #tmpStr = md_path + "/" + md_index + "/MemoryChunks/" + mch_index
                #tmpMemChunk["@odata.id"]=tmpStr
                #  update the associated Endpoint URI 
                #ep_id = allAgentNodes["nodes"][nodeID]["redfishIDs"]["ep_id"]
                #tmpStr = rb+"Fabrics/"+f_id+"/Endpoints/"+ep_id
                tmpStr = memInventory[fabricID][domainNum]["EndptURI"]
                ofmf_body["Links"]["Endpoints"].append({"@odata.id":tmpStr})
                ofmf_body["AddressRangeOffsetMiB"] = int(chunk_start/(2**20))
                ofmf_body["MemoryChunkSizeMiB"] = int(reqSize/(2**20))
                #  add the necessary Oem details from (or for?) zephyr
                #  verify these are defaults that agent overwrites?
                ofmf_body["Oem"]["class"] = memClass    # 2= DAX, 17 = block
                ofmf_body["Oem"]["type"] = 1            # genZ memory space, always 1 for POC
                ofmf_body["Oem"]["flags"] = 0           # Agent calculates this value
                print("new chunk --")
                print(json.dumps(ofmf_body, indent=4))
                #  just write the new memory chunk POST file for later use
                json_file=""
                json_file=("./iPOSTmemChunk_"+md_id+"_"+mc_id+".json")
                print()
                print("posting file ", json_file)
                # hack for testing
                with open(json_file,"w") as jdata:
                    json.dump(ofmf_body,jdata, indent=4)
                    jdata.close()
                break       # no need to search other free space options

    # post the new chunk, if found
    if found:
        print("found space for new chunk ",newChunkID)
        # 
        postID=ofmf_body["@odata.id"]
        print ("POST")
        print(service_URI+postID)
        r = requests.post(service_URI+postID, data=json.dumps(ofmf_body),\
                    headers=headers)
        print(r)
        data = json.loads(r.text)
        print(json.dumps(data, indent =4 ))

        
    else:
        print("no free space chunk large enough in that memory domain")

    return


def delete_chunk(service_URI, headers, memInventory, busyList):
    # select chunk to delete
    req_fabricID=""
    req_domNum=""
    req_chunkID=0
    postID=""
    data=""

    rb="/redfish/v1"
    print_free_list(busyList)
    req_fabricID=str(input("use which fabric? >"))
    req_domNum=str(input("use which memory domain? >"))
    req_chunkID=str(input("delete which memory chunk? >"))
    postID=rb+"/Chassis/" + req_fabricID +"/MemoryDomains/" +\
            req_domNum +"/MemoryChunks/" + req_chunkID
    print(service_URI+postID)
    print("----")
    r = requests.get(service_URI+postID, data=json.dumps(data),\
                headers=headers)
    print(r)
    if "200" in str(r):                 #found memory chunks collection
        data = json.loads(r.text)
        print(json.dumps(data, indent =4 ))
        # just need to check for connections
        # get the connections list for this fabric
        # verify this chunk is not part of an existing connection
        #
        # go ahead and delete this chunk

        r = requests.delete(service_URI+postID, data=json.dumps(data),\
                    headers=headers)
        print(r)
    else:
        print("memory chunk not found ")
        print(r.text)


    return

def find_free_mem(memInventory):
    # routine finds free memory ranges in a domain, fills them with
    # 'free' chunks, and consolidates all free chunks into as few contiguous
    # free chunks as possible

    tmpFabricID=""
    print("find and consolidate free space")


    for fabricID,fabric_inventory in memInventory.items():  #for every fabric found
        for memDomNum, memDomain in fabric_inventory.items():  # for every MD found
            print("collecting mem domain ",memDomNum)
            sorted_chunks={}
            tmp_chunks={}
            new_chunk={}
            domSize=memInventory[fabricID][memDomNum]["size"]
            sorted_chunks=copy.deepcopy(memInventory[fabricID][memDomNum]["MemoryChunks"])
            print("sorted_chunks = ")
            print(sorted_chunks)

            if not bool(sorted_chunks):
                print("domain ",memDomNum," is empty")
                # simply create a free chunk the size of the domain
                new_start=0
                new_chunk["fabricID"]=memDomain["fabricID"]
                new_chunk["chunkID"]="none"
                new_chunk["memDomain"]=memDomNum
                new_chunk["EndptURI"]=memDomain["EndptURI"]
                new_chunk["size_in_bytes"]=memDomain["size"]
                new_chunk["minChunkSize"]=memDomain["minChunkSize"]
                new_chunk["start_in_bytes"]=0
                new_chunk["mediaType"]="Volatile"
                new_chunk["use_status"]="free"
                print("domain ", memDomNum, "has free space of",\
                        new_chunk["size_in_bytes"], " Bytes")
                # add this free chunk to the memory domain DB
                tmp_chunks[new_start]=copy.deepcopy(new_chunk)
                print(json.dumps(tmp_chunks, indent = 4))
                # done with this memory domain, so update its chunk list
                memInventory[fabricID][memDomNum]["MemoryChunks"]=copy.deepcopy(tmp_chunks)


            else:
                print("domain ",memDomNum," chunks")
                last_start=0
                last_end= (-1)
                last_status="none"
                last_chunkID=0
                for chunkID, chunkBody in sorted_chunks.items(): # for every chunk found
                    print(json.dumps(chunkBody, indent = 4))
                    current_status=chunkBody["use_status"]
                    current_start=chunkBody["start_in_bytes"]
                    current_size=chunkBody["size_in_bytes"]
                    current_end=current_start + current_size -1
                    if current_start > (last_end+1): # there's a gap
                        print("found a gap")
                        memGap = current_start - (last_end +1)
                        if last_status =="free":
                            print("expand previous free block")
                            last_size = tmp_chunks[last_chunkID]["size_in_bytes"]
                            tmp_chunks[last_chunkID]["size_in_bytes"] = \
                                    last_size + memGap
                        else:
                            print("add new free block")
                            new_start=(last_end+1)
                            new_chunk={}
                            new_chunk["fabricID"]=memDomain["fabricID"]
                            new_chunk["chunkID"]="none"
                            new_chunk["memDomain"]=memDomNum
                            new_chunk["EndptURI"]=memDomain["EndptURI"]
                            new_chunk["size_in_bytes"]=memGap
                            new_chunk["start_in_bytes"]=last_end+1
                            new_chunk["mediaType"]="Volatile"
                            new_chunk["use_status"]="free"
                            # add this free chunk to the memory domain DB
                            tmp_chunks[new_start]=copy.deepcopy(new_chunk)
                            # copy the current chunk to the memory domain DB
                            tmp_chunks[current_start]=copy.deepcopy(chunkBody)

                    else:
                        print("no gap")
                        # copy this chunk over to the tmp_chunks
                        tmp_chunks[chunkID]=copy.deepcopy(chunkBody)

                    # save this chunk's details for next chunk iteration
                    last_end=current_end 
                    last_start=current_start
                    last_status=chunkBody["use_status"]
                    last_chunkID=chunkID

                # check if there is free space after the last used or free chunk
                if last_end < (domSize-1):  # need to pad to end of domain
                    print("need end free block")
                    print("add new free block")
                    memGap = domSize-(last_end+1)
                    new_start=(last_end+1)
                    new_chunk={}
                    new_chunk["fabricID"]=memDomain["fabricID"]
                    new_chunk["chunkID"]="none"
                    new_chunk["memDomain"]=memDomNum
                    new_chunk["EndptURI"]=memDomain["EndptURI"]
                    new_chunk["size_in_bytes"]=memGap
                    new_chunk["start_in_bytes"]=last_end+1
                    new_chunk["mediaType"]="Volatile"
                    new_chunk["use_status"]="free"
                    # add this free chunk to the memory domain DB
                    tmp_chunks[new_start]=copy.deepcopy(new_chunk)

                print("done with memdomain ",memDomNum)

            memInventory[fabricID][memDomNum]["MemoryChunks"] = copy.deepcopy(tmp_chunks)
    return


def myCLI(agent_URI,service_URI):
    postFile=""
    myCMD=""
    memInventory={}
    sysInventory={}
    tmpMemInventory={}
    freeList=[]
    busyList=[]
    
    print(agent_URI)
    print(service_URI)
    #with open(infile,"r") as file_json:
        #fileList = json.load(file_json)
    #file_json.close()

    

    #headers = {"Content-type":"application/json", "Accept":"text/plain"}
    headers = {"Content-type":"application/json" }

    while myCMD != "q":
        myCMD = input("OFMF_cli> ")
        print ()
        print ()
        print ()
        print ("-----------------------------------------")
        print (myCMD)
        if myCMD == "get":
            postFile= input("file to receive response of GET?> ")
            print ("GET")
            with open(postFile,"r") as file_json:
                data = json.load(file_json)
            file_json.close()
            postID=data["@odata.id"]
            print(postID)
            print(service_URI+postID)
            print(data)
            print("----")
            r = requests.get(service_URI+postID, data=json.dumps(data),\
                    headers=headers)
            print(r)
            data = json.loads(r.text)
            print(json.dumps(data, indent =4 ))
        elif myCMD == "get_sys":
            tmpSysInventory={}
            get_systems(service_URI,tmpSysInventory)
            print(json.dumps(tmpSysInventory, indent = 4))
            sysInventory=copy.deepcopy(tmpSysInventory)
        elif myCMD == "get_conns":
            tmpConnInventory={}
            f_id="GenZ4b0a"
            get_connections(service_URI,f_id, tmpConnInventory)
            print(json.dumps(tmpConnInventory, indent = 4))
            connInventory=copy.deepcopy(tmpConnInventory)
        elif myCMD == "get_mem":
            tmpMemInventory={}
            get_memDomains(service_URI,tmpMemInventory)
            sort_chunks(tmpMemInventory)
            print(json.dumps(tmpMemInventory, indent = 4))
            memInventory=copy.deepcopy(tmpMemInventory)
            print("---------------------")
            print()
            print(json.dumps(memInventory, indent=4))
            print("done get_mem")
        elif myCMD == "sort_mem":
            print("sorting memory chunks and inserting free blocks")
            tmpMemInventory=copy.deepcopy(memInventory)
            sort_chunks(tmpMemInventory)
            print(json.dumps(tmpMemInventory, indent = 4))
            find_free_mem(tmpMemInventory)
            print(json.dumps(tmpMemInventory, indent = 4))
            memInventory=copy.deepcopy(tmpMemInventory)
            print("---------------------")
            print()
            print(json.dumps(memInventory, indent=4))
            print("done sort_mem")
        elif myCMD == "list_mem":
            print("retrieve free mem and busy mem lists")
            make_free_list(memInventory,freeList,busyList)
        elif myCMD == "create_chunk":
            req_fabricID=str(input("use which fabric? >"))
            req_domNum=str(input("use which memory domain? >"))
            req_sizeInMB=int(input("size of chunk in MiB? >"))
            req_class=int(input("class (dax=2, block=17) of chunk (2 or 17)> "))
            create_chunk(service_URI,headers,memInventory,req_fabricID,req_domNum,req_sizeInMB,req_class)
        elif myCMD =="delete_chunk":
            delete_chunk(service_URI,headers,memInventory,busyList)

        elif myCMD == "create_conn":
            req_fabricID=str(input("use which fabric? >"))
            req_domNum=str(input("use which memory domain? >"))
            req_chunkID=str(input("use which memory chunk? >"))
            req_sysID=(input("use which systemID? >"))
            req_faID=(input("use which Fabric Adapter ? >"))
            create_connection(service_URI,headers,memInventory,sysInventory,connInventory,
                    req_fabricID,req_domNum,req_chunkID,req_sysID,req_faID)

        elif myCMD =="delete_conn":
            delete_connection(service_URI,headers,connInventory)

        elif myCMD == "post":
            postFile= input("file for body of POST?> ")
            with open(postFile,"r") as file_json:
                data = json.load(file_json)
            file_json.close()
            postID=data["@odata.id"]
            print ("POST")
            print(service_URI+postID)
            print(data)
            r = requests.post(service_URI+postID, data=json.dumps(data),\
                   headers=headers)
            print(r)
            data = json.loads(r.text)
            print(json.dumps(data, indent =4 ))
        elif myCMD == "delete":
            postFile= input("file for body of DELETE?> ")
            with open(postFile,"r") as file_json:
                data = json.load(file_json)
            file_json.close()
            postID=data["@odata.id"]
            print ("DELETE")
            print(service_URI+postID)
            print(data)
            r = requests.delete(service_URI+postID, data=json.dumps(data),\
                   headers=headers)
            print(r)
            data = json.loads(r.text)
            print(json.dumps(data, indent =4 ))
        elif myCMD == "reset_OFMF":
            print ("reset OFMF inventory")
            postID="/redfish/v1/resettopology/"
            print("URI ",agent_URI+postID )
            r = requests.delete(agent_URI+postID,headers=headers)
            print(r)
        elif myCMD == "q":
            print ("quit")
        else:
            print ("unrecognized cmd")

    return
