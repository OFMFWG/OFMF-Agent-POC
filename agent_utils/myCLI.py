# Copyright Notice:
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

#from requests.auth import HTTPDigestAuth
import json
import copy
import requests
from md_chunks import get_MDChunks_instance

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
            tmpDomain["minChunkSize"]=data["GenZ"]["minChunkSize"]
            tmpDomain["block_enabled"]=data["AllowsBlockProvisioning"]
            tmpDomain["chunk_enabled"]=data["AllowsMemoryChunkCreation"]
            tmpDomain["memSource"]=data["Links"]["MediaControllers"]["@odata.id"]
            # trace the memory source to its endpoint
            postID=tmpDomain["memSource"]
            print("searching ",postID)
            r = requests.get(service_URI + postID, headers=headers)
            print(r)
            sourceData = json.loads(r.text)
            print(json.dumps(sourceData, indent=4))
            tmpDomain["EndptURI"]=sourceData["Links"]["Endpoints"][0]["@odata.id"] 
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
def create_chunk(service_URI,headers,memInventory,fabricID,domainNum,size_in_MiB):
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
                ofmf_body["Oem"]["class"] = 2
                ofmf_body["Oem"]["type"] = 1
                ofmf_body["Oem"]["flags"] = 0
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
        elif myCMD == "list_free":
            print("retrieve free mem and busy mem lists")
            make_free_list(memInventory,freeList,busyList)
        elif myCMD == "create_chunk":
            req_fabricID=str(input("use which fabric? >"))
            req_domNum=str(input("use which memory domain? >"))
            req_sizeInMB=int(input("size of chunk in MiB? >"))
            print(type(req_sizeInMB))
            create_chunk(service_URI,headers,memInventory,req_fabricID,req_domNum,req_sizeInMB)
            # call get_mem
            # call sort_mem

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
