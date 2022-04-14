# Copyright Notice:
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

import json
import copy
import g
import requests

#import agent_utils
#from agent_utils import *
import agent_utils.connections
from agent_utils.connections import get_Connections_instance
import agent_utils.collection
from agent_utils.collection import get_Collection_instance
import agent_utils.fabric
from agent_utils.fabric import get_Fabric_instance
import agent_utils.fabricadapters
from agent_utils.fabricadapters import get_FabricAdapters_instance
import agent_utils.fabric_adapter_port
from agent_utils.fabric_adapter_port import get_FabricAdapterPorts_instance
import agent_utils.mem_chassis
from agent_utils.mem_chassis import get_Chassis_instance
import agent_utils.mediacontrollers
from agent_utils.mediacontrollers import get_MediaControllers_instance
import agent_utils.media_controller_port
from agent_utils.media_controller_port import get_MediaControllerPorts_instance
import agent_utils.memory_domains
from agent_utils.memory_domains import get_ChassisMemoryDomain_instance
import agent_utils.ComputerSystem
from agent_utils.ComputerSystem import get_ComputerSystem_instance
import agent_utils.Zswitches
from agent_utils.Zswitches import get_Switches_instance
import agent_utils.fabric_switch_port
from agent_utils.fabric_switch_port import get_FabricSwitchPorts_instance
import agent_utils.endpoints
from agent_utils.endpoints import get_Endpoints_instance
import agent_utils.md_chunks
from agent_utils.md_chunks import get_MDChunks_instance
import agent_utils.addResource
from agent_utils.addResource import z_add_resource_instance

_cClassLUT = \
        {  "2":{
                "genZtype":"memory",
                "memDom_source":"FabricAdapters",
                "redfishTemplate":"uploadFabricAdapterNode(nodeID,allAgentNodes)",
                "agentTemplate":"./agent_utils/templates/mc_node.json"
            },
            "5":{
                "genZtype":"switch",
                "memDom_source":"",
                "redfishTemplate":"uploadFabricAdapterNode(nodeID,allAgentNodes)",
                "agentTemplate":"./agent_utils/templates/sw_node.json"
                },
            "20":{
                "genZtype":"bridge",
                "memDom_source":"MediaControllers",
                "redfishTemplate":"uploadFabricAdapterNode(nodeID,allAgentNodes)",
                "agentTemplate":"./agent_utils/templates/fa_node.json"
                },
            "21":{
                "genZtype":"bridge",
                "memDom_source":"MediaControllers",
                "redfishTemplate":"uploadFabricAdapterNode(nodeID,allAgentNodes)",
                "agentTemplate":"./agent_utils/templates/fa_node.json"
            }

}

def getZephyrConfig(defaultFile):

    #  see if Zephyr is configured, and available
    if not "None" in g.ZEPHYR :
        # try to reach Zephyr as defined
        zephyr_UIR = g.ZEPHYR
        postID="/fabric/topology"
        print(zephyr_UIR)
        headers = {'Content-type':'application/json', 'Accept':'text/plain'}
        headers = {'Content-type':'text/plain' }
        print("request is ", zephyr_UIR+postID)
        r = requests.get(zephyr_UIR+postID, headers=headers)
        #r = requests.get(zephyr_UIR+postID )
        print(r.json)
        data = r.json()
        print("using Zephyr config")
    else:
        # no Zephyr, use default
        print("using default config")
        with open(defaultFile,"r") as file_json:
            data= json.load(file_json)
        file_json.close()
    

    return data


def updateZephyrNodeIDs(znodeConfig,agentConfig):

    localNodeID = znodeConfig["instance_uuid"]
    print("updating agent node description ", localNodeID)
    # copy all details in Zephyr node description into agent's DB
    for k, v in znodeConfig.items():
        agentConfig["nodes"][localNodeID]["zephyrNodeIDs"][k] = copy.deepcopy(v)
  
    #check if node is the primary fabric manager
    print(" node long id ",agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["id"]) 
    print(" pfm long id ",agentConfig["fabricIDs"]["pfm"]) 
    if (agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["id"]) == \
            (agentConfig["fabricIDs"]["pfm"]):
                agentConfig["fabricIDs"]["pfmID"] = localNodeID
    
    #process the node config details
    tmplist = agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["id"].split(":")
    agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["c_uuid"] = tmplist[0]
    agentConfig["nodes"][localNodeID]["redfishIDs"]["SerialNumber"] = tmplist[1]
    agentConfig["nodes"][localNodeID]["redfishIDs"]["UUID"] = localNodeID

    tmplist = \
            agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["gcids"][0].split(":")
    agentConfig["nodes"][localNodeID]["nodeProperties"]\
            ["functionality"]["GenZ"]["GCID"]["SID"] = tmplist[0]
    agentConfig["nodes"][localNodeID]["nodeProperties"]\
            ["functionality"]["GenZ"]["GCID"]["CID"] = tmplist[1]
   
    tmpstr = agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["gcids"][0]
    agentConfig["GCID_xref"][tmpstr] = localNodeID
    
    if agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["cstate"] == "C-Up":
        agentConfig["nodes"][localNodeID]["redfishIDs"]["Status"]["State"] = "Enabled"
    else:
        agentConfig["nodes"][localNodeID]["redfishIDs"]["Status"]["State"] = "Disabled"

    #process the node memory capabilities
    tmpMemCap = agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["max_data"]
    if tmpMemCap >0:
        tmpChunkSize = 2** agentConfig["nodes"][localNodeID]\
                ["zephyrNodeIDs"]["rsp_page_grid_ps"]
        agentConfig["nodes"][localNodeID]["nodeProperties"]["functionality"]\
                ["minChunkSize"] = tmpChunkSize
        agentConfig["nodes"][localNodeID]["nodeProperties"]["functionality"]\
                ["maxChunks"] = int(tmpMemCap/tmpChunkSize)

    return


def updateAgentNodePorts(localPortConfig,peerPortConfig,agentConfig,extras):
    print(json.dumps(localPortConfig, indent = 4))
    localNodeID=next(iter(localPortConfig))
    peerNodeID=next(iter(peerPortConfig))
    delPortNum=""
    tmpPortID=""
    print("updating ports for instance_uuid = ", localNodeID)
    localNodePortNums = (agentConfig["nodes"][localNodeID]\
            ["topology"]["node_ports"].keys())
    localPortDesc = localPortConfig[localNodeID]
    localPortNum = localPortDesc["num"]
    
    if localPortNum in localNodePortNums:
        print("found ", localPortNum, " in agentDB")
        print("need to update existing port details")
        #update the existing port details
    else:
        print("need to create new local ports")
        #make sure we have enough physical ports
        maxPorts = agentConfig["nodes"][localNodeID]["zephyrNodeIDs"]["max_iface"]
        tmpPortID = len(localNodePortNums)
        print("max ports ", maxPorts)
        print("ports in use ", tmpPortID)
        if (tmpPortID<maxPorts):
            print("room for another port")
        else:
            print("ooops, no spare ports")

    # create a new port or update an existing one
    tmpLocalPort={}
    tmpLocalPort["num"] = copy.deepcopy(localPortDesc["num"])
    tmpLocalPort["state"] = copy.deepcopy(localPortDesc["state"])
    tmpLocalPort["phy"] = copy.deepcopy(localPortDesc["phy"])
    tmpLocalPort["peer_port"]={"num":"","state":""}
    tmpLocalPort["peer_port"]["num"] = copy.deepcopy(peerPortConfig[peerNodeID]["num"])
    tmpLocalPort["peer_port"]["state"] = copy.deepcopy(peerPortConfig[peerNodeID]["state"])
    tmpLocalPort["redfish_portID"] = tmpPortID # give it a redfish portID 
    # copy the whole port structure into the agent's DB entry for the node
    agentConfig["nodes"][localNodeID]["topology"]\
            ["node_ports"][localPortNum] = copy.deepcopy(tmpLocalPort)

    return

def parseZephyrLink(znodeLink,agentConfig):

    print("parsing Zephyr Link")
    # 'znodeLink' is a zephyr link object
    # contains Port descriptions for two nodes, A & B
    print()
    nodeList = []
    extras = {}
    for k, v in znodeLink.items():
        if isinstance(v, dict):
            #  k = instance_uuid, v = port details for node K
            nodeList.append({k:v})
        else:
            extras[k] = copy.deepcopy(v)
    if len(nodeList) != 2:
        print("error in znodelink decode, expected exactly 2 dictionaries")
        return
    else:
        print("2 ports found")
    
    #update agentDB topology description for both nodes on the link 
    updateAgentNodePorts(nodeList[0],nodeList[1],agentConfig,extras)
    updateAgentNodePorts(nodeList[1],nodeList[0],agentConfig,extras)
    return

def uploadFabricInstance(allAgentNodes):

    rb = "/redfish/v1/"
    full_f_id=""
    # create a fabric instance to POST to OFMF

    ofmf_body = {}
    full_f_id = allAgentNodes["fabricIDs"]["fab_uuid"]
    trim_f_id = "GenZ" + full_f_id.split("-")[2]
    allAgentNodes["fabricIDs"]["f_id"] = trim_f_id
    allAgentNodes["fabricIDs"]["rb"] = rb
    # update agentDB with fabric instance URI
    allAgentNodes["fabricIDs"]["@odata.id"] = rb+"Fabrics/"+trim_f_id
    wildcards = {"rb":rb, "f_id":trim_f_id}
    ofmf_body = copy.deepcopy(get_Fabric_instance(wildcards)) 
    ofmf_body["Oem"].append({"fab_uuid":full_f_id})
    print("POSTing fabric ",trim_f_id)


    # hack for testing
    with open("./agent_POSTs/POSTfabric_" + trim_f_id +".json","w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()


    return

def uploadChassis(allAgentNodes,memDomainCount):

    # also need a memory domain collection
    # need a memory domain for each node with memory
    # need a chunk collection under each memory domain
    
    #  first create and POST the Chassis instance 

    print("create Chassis instance and its memory subordinates")
    rb = allAgentNodes["fabricIDs"]["rb"]
    ch_id = allAgentNodes["fabricIDs"]["f_id"]
    allAgentNodes["fabricIDs"]["ch_id"] = ch_id
    wildcards = {"rb":rb, "id":ch_id }
    ofmf_body = copy.deepcopy(get_Chassis_instance(wildcards)) 
    domainCounter = memDomainCount

    json_file=""
    json_file=("./agent_POSTs/POSTchassis_"+ch_id+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()



    #  now create and POST the Chassis' memory domains collection

    cType = "MemoryDomains"
    mdPath = rb+"Chassis/"+ch_id+"/MemoryDomains"
    allAgentNodes["fabricIDs"]["md_path"] = mdPath
    wildcards = {"cType":cType, "path":mdPath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 

    #print("Domains Collection  ",json.dumps(ofmf_body, indent=4))
    json_file=""
    json_file=("./agent_POSTs/POSTdomains_"+ch_id+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()

    #  now create and POST the Chassis' media controller collection

    cType = "MediaControllers"
    mcPath = rb+"Chassis/"+ch_id+"/MediaControllers"
    wildcards = {"cType":cType, "path":mcPath }
    allAgentNodes["fabricIDs"]["mc_path"] = mcPath
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 

    json_file=""
    json_file=("./agent_POSTs/POSTmemctrl_"+ch_id+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()


    
    return
    
def createRedfishIDs(allAgentNodes,cClassDecoder):

    # run through the nodes in the agentDB
    # look up the proper template
    # call the proper redfish building routines
    print()
    for k,v in (allAgentNodes["nodes"].items()):
        print("node ID build ",k)
        nodeID=k
        z_class = str(allAgentNodes["nodes"][k]["zephyrNodeIDs"]["cclass"])
        nodeType =cClassDecoder[z_class]["genZtype"]
        if nodeType == "memory":
            createMC_IDs(nodeID,allAgentNodes)
        elif nodeType =="bridge":
                createFA_IDs(nodeID,allAgentNodes)
        else:
                createSW_IDs(nodeID,allAgentNodes)


    return

def postRedfishNodes(allAgentNodes,cClassDecoder):
    # now post the nodes
    for k,v in (allAgentNodes["nodes"].items()):
        print("node POST  ",k)
        nodeID=k
        z_class = str(allAgentNodes["nodes"][k]["zephyrNodeIDs"]["cclass"])
        nodeType =cClassDecoder[z_class]["genZtype"]
        if nodeType == "memory":
            postMC_nodes(nodeID,allAgentNodes)
        elif nodeType =="bridge":
            postFA_nodes(nodeID,allAgentNodes)
        else:
            postSW_nodes(nodeID,allAgentNodes)

    return

def createFA_IDs(nodeID,allAgentNodes):

    # walk through agent's fabric adapter data to generate anticipated redfish IDs
    
    tmpList=[]
    tmpStr=""
    md_path=""
    md_index=""
    maxMem=0
    rb = allAgentNodes["fabricIDs"]["rb"]
    f_id = allAgentNodes["fabricIDs"]["f_id"]
    node_index=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["node_index"]
    maxMem=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["max_data"]
    
    tmpList = nodeID.split("-")
    #s_id = 'SY_'+ tmpList[2]    #use field 2 of instance_uuid for System id
    #fa_id= 'FA_' +tmpList[2]    #use same field for FabricAdapter id
    s_id = 'SY_'+ node_index
    fa_id= 'FA_'+ node_index


    allAgentNodes["nodes"][nodeID]["redfishIDs"]["s_id"] = s_id

    allAgentNodes["nodes"][nodeID]["redfishIDs"]["fa_id"] = fa_id
    
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["@odata.id"]= \
            rb+"Systems/"+s_id+"/FabricAdapters/"+fa_id
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["Id"]= fa_id
    allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]=\
            "Bridge "+fa_id
   
    ep_id = allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Id"]
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["ep_id"] = ep_id
    allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["@odata.id"] =\
            str(rb+"Fabrics/"+f_id+"/Endpoints/"+ep_id)
    #record the memory domain URI into agentDB if appropriate
    if maxMem>0:

        md_path=allAgentNodes["fabricIDs"]["md_path"]
        md_index=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["md_index"]
        tmpStr = md_path + "/" + md_index
        allAgentNodes["nodes"][nodeID]["nodeProperties"]\
                ["memdomains"].append({"@odata.id":tmpStr})
    return

def createMC_IDs(nodeID,allAgentNodes):

    # walk through agent's media controller data to generate anticipated redfish IDs
    
    tmpList=[]
    tmpStr=""
    md_path=""
    md_index=""
    rb = allAgentNodes["fabricIDs"]["rb"]
    ch_id=allAgentNodes["fabricIDs"]["ch_id"]
    f_id = allAgentNodes["fabricIDs"]["f_id"]
    node_index=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["node_index"]
    
    tmpList = nodeID.split("-") #nodeID is the instance_uuid
    #s_id = 'SY_'+ tmpList[2]    #use field 2 of instance_uuid for System id
    #mc_id= 'MC_' +tmpList[2]    #use field 2 for MediaController id
    mc_id= 'MC_' +node_index



    allAgentNodes["nodes"][nodeID]["redfishIDs"]["mc_id"] = mc_id
    
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["@odata.id"]= \
            rb+"Chassis/"+ch_id+"/MediaControllers/"+mc_id
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["Id"]= mc_id
    allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]=\
            "MediaController "+mc_id
   
    ep_id = allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Id"]
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["ep_id"] = ep_id
    allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["@odata.id"] =\
            str(rb+"Fabrics/"+f_id+"/Endpoints/"+ep_id)
    
    #record the memory domain URI into agentDB
    md_path=allAgentNodes["fabricIDs"]["md_path"]
    md_index=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["md_index"]
    tmpStr = md_path + "/" + md_index
    allAgentNodes["nodes"][nodeID]["nodeProperties"]\
            ["memdomains"].append({"@odata.id":tmpStr})
    return

def createSW_IDs(nodeID,allAgentNodes):

    # walk through agent's Switch data to generate anticipated redfish IDs
    
    tmpList=[]
    tmpStr=""
    rb = allAgentNodes["fabricIDs"]["rb"]
    f_id = allAgentNodes["fabricIDs"]["f_id"]
    node_index=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["node_index"]
    
    tmpList = nodeID.split("-")
    #sw_id = 'SW_'+ tmpList[2]    #use field 2 of instance_uuid for System id
    sw_id = 'SW_'+ node_index


    allAgentNodes["nodes"][nodeID]["redfishIDs"]["sw_id"] = sw_id

    allAgentNodes["nodes"][nodeID]["redfishIDs"]["@odata.id"]= \
            rb+"Fabrics/"+f_id+"/Switches/"+sw_id
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["Id"]= sw_id
    allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]=\
            "Switch "+sw_id
   
    ep_id = allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Id"]
    allAgentNodes["nodes"][nodeID]["redfishIDs"]["ep_id"] = ep_id
    allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["@odata.id"] =\
            str(rb+"Fabrics/"+f_id+"/Endpoints/"+ep_id)
    
    return

def createMemChunkIDs(allAgentNodes):
    ofmf_body = {}
    wildcards = {}
    tmpList=[]
    tmpStr=""
    # need a template for the mem chunk structure
    chunkFile="./agent_utils/templates/agent_mem_chunk.json"  
    rb = allAgentNodes["fabricIDs"]["rb"]
    ch_id=allAgentNodes["fabricIDs"]["ch_id"]
    f_id = allAgentNodes["fabricIDs"]["f_id"] 
    md_path=allAgentNodes["fabricIDs"]["md_path"]
    for k,v in (allAgentNodes["nodes"].items()):
        print("node ID for memChunk install ",k)
        nodeID=k
        # first post a memory domain instance for the node if one is needed
        max_data=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["max_data"]
        if max_data>0 :
            md_index=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["md_index"]
            mch_index="1"  #  no memory chunk at initial configuration
            #  build a memory domain instance 
            wildcards = {"rb":rb, "c_id":ch_id, "md_id":md_index }
            ofmf_body = copy.deepcopy(get_ChassisMemoryDomain_instance(wildcards)) 
            #  update the source entity for the memory domain
            ofmf_body["Links"]["MediaControllers"]["@odata.id"]=\
                    allAgentNodes["nodes"][nodeID]["redfishIDs"]["@odata.id"]
            
            #ofmf_body["GenZ"]["gcid"]=\
                    #allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["gcids"][0]
            #ofmf_body["GenZ"]["c_uuid"]=c_uuid
            ofmf_body["GenZ"]["max_data"]=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["max_data"]
            ofmf_body["GenZ"]["minChunkSize"]=\
                    allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["minChunkSize"]
            ofmf_body["GenZ"]["maxChunks"]=\
                    allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["maxChunks"]
            ofmf_body["AddressRangeType"] = "????"


            json_file=""
            json_file=("./agent_POSTs/POSTmemDomInstance_"+md_index+".json")
            print()
            print("posting file ", json_file)
            # hack for testing
            with open(json_file,"w") as jdata:
                 json.dump(ofmf_body,jdata, indent=4)
                 allPostFiles.append(jdata.name)
                 jdata.close()
    

            #  build a sample memory chunk instance (the first one in this case)
            #  but we won't POST it to the OFMF, as the Memory Manager does this
            with open(chunkFile,"r") as file_json:
                tmpMemChunk = json.load(file_json)
            file_json.close()

            wildcards = {"rb":rb, "c_id":ch_id,"md_id":md_index, "mc_id":mch_index }
            ofmf_body = copy.deepcopy(get_MDChunks_instance(wildcards)) 
            tmpStr = md_path + "/" + md_index + "/MemoryChunks/" + mch_index
            tmpMemChunk["@odata.id"]=tmpStr
            #  update the associated Endpoint URI 
            ep_id = allAgentNodes["nodes"][nodeID]["redfishIDs"]["ep_id"]
            tmpStr = rb+"Fabrics/"+f_id+"/Endpoints/"+ep_id
            ofmf_body["Links"]["Endpoints"].append({"@odata.id":tmpStr})
            ofmf_body["AddressRangeOffsetMiB"] = 0
            ofmf_body["MemoryChunkSizeMiB"] = \
                    int(allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["max_data"] / (2**20))
            #  add the necessary Oem details from zephyr
            ofmf_body["Oem"]["class"] = tmpMemChunk["class"]
            ofmf_body["Oem"]["type"] = tmpMemChunk["type"]
            ofmf_body["Oem"]["flags"] = tmpMemChunk["flags"]
            tmpMemChunk["start"] = copy.deepcopy(ofmf_body["AddressRangeOffsetMiB"])
            tmpMemChunk["length"] = copy.deepcopy(ofmf_body["MemoryChunkSizeMiB"])
            #  don't place the new memory chunk into the agentDB
            #allAgentNodes["nodes"][nodeID]["nodeProperties"]\
            #    ["memchunks"].append(tmpMemChunk)
            #  just write the new memory chunk POST file for later use
            json_file=""
            json_file=("./agent_POSTs/POSTmemChunk_"+md_index+"_"+mch_index+".json")
            print()
            print("posting file ", json_file)
            # hack for testing
            with open(json_file,"w") as jdata:
                 json.dump(ofmf_body,jdata, indent=4)
                 #allPostFiles.append(jdata.name)
                 jdata.close()
    return

def postFA_nodes(nodeID,allAgentNodes):

    # fabric adapter template fill and POST function
    
    ofmf_body = {}
    wildcards = {}
    tmpList=[]
    tmpStr=""
    rb = allAgentNodes["fabricIDs"]["rb"]
    
    tmpList = allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["id"].split(":")
    s_num = tmpList[1]      #put SerialNumber in proper place
    c_uuid = tmpList[0]      #put c_uuid in proper place

    s_id = allAgentNodes["nodes"][nodeID]["redfishIDs"]["s_id"] 
    z_id = nodeID               #put instance_uuid in 'UUID' of FA

    #  create and post a unique system instance for this fabric adapter
    wildcards = {"rb":rb, "s_id":s_id }
    ofmf_body = copy.deepcopy(get_ComputerSystem_instance(wildcards)) 
    
    json_file=""
    json_file=("./agent_POSTs/POSTsystem"+s_id+".json")
    print()
    print("posting file ", json_file)
    # hack for testing
    with open(json_file,"w") as jdata:
       json.dump(ofmf_body,jdata, indent=4)
       allPostFiles.append(jdata.name)
       jdata.close()

    #  create a FabricAdapters collection for this system

    cType = "FabricAdapters"
    cPath = rb+"Systems/"+s_id+"/"+cType
    wildcards = {"cType":cType, "path":cPath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 

    # do the POST
    json_file=""
    json_file=("./agent_POSTs/POSTadapters_"+s_id+".json")
    print()
    print("posting file ", json_file)
    # hack for testing
    with open(json_file,"w") as jdata:
       json.dump(ofmf_body,jdata, indent=4)
       allPostFiles.append(jdata.name)
       jdata.close()

    #  create a fabric adapter object to POST
    fa_id = allAgentNodes["nodes"][nodeID]["redfishIDs"]["fa_id"]
    wildcards = {"rb":rb, "s_num":s_num, "s_id":s_id, "fa_id":fa_id,"z_id":z_id }
    ofmf_body = copy.deepcopy(get_FabricAdapters_instance(wildcards)) 

    # add additional details from agentDB into fabric adapater POST
    ofmf_body["Status"]["State"]=\
            allAgentNodes["nodes"][nodeID]["redfishIDs"]["Status"]["State"]
    ofmf_body["GenZ"]["gcid"]=\
            allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["gcids"][0]
    ofmf_body["GenZ"]["c_uuid"]=c_uuid
    ofmf_body["GenZ"]["max_data"]=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["max_data"]
    ofmf_body["GenZ"]["minChunkSize"]=\
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["minChunkSize"]
    ofmf_body["GenZ"]["maxChunks"]=\
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["maxChunks"]

    tmpStr=allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["@odata.id"]
    ofmf_body["Links"]["Endpoints"].append(\
            {"@odata.id":tmpStr})
    ofmf_body["Links"]["MemoryDomains"] = copy.deepcopy(allAgentNodes["nodes"][nodeID]\
            ["nodeProperties"]["memdomains"])

    
    # do the POST
    json_file=""
    json_file=("./agent_POSTs/POSTnode"+fa_id+".json")
    print()
    print("posting file ", json_file)
    # hack for testing
    with open(json_file,"w") as jdata:
       json.dump(ofmf_body,jdata, indent=4)
       allPostFiles.append(jdata.name)
       jdata.close()
   
   # create the fabric endpoint associated with the fabric adapter
    ep_id = allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Id"]
    f_id = allAgentNodes["fabricIDs"]["f_id"]
    wildcards = {"rb":rb, "f_id":f_id , "ep_id":ep_id}
    ofmf_body = copy.deepcopy(get_Endpoints_instance(wildcards)) 

    # update the template with additional details from agentDB
    ofmf_body["ConnectedEntities"][0]["EntityLink"]["@odata.id"]= \
            allAgentNodes["nodes"][nodeID]["redfishIDs"]["@odata.id"]
    ofmf_body["ConnectedEntities"][0]["EntityType"]= \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["EntityType"]
    ofmf_body["ConnectedEntities"][0]["GenZ"]=copy.deepcopy( \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["GenZ"])
    ofmf_body["Name"] = \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]
    ofmf_body["Description"] = "endpoint for "+\
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]
    # update the agentDB with endpoint details
    #allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["@odata.id"] =\
    #        rb+f_id+"Fabrics/"+f_id+"/Endpoints/"+ep_id
    
    # do the POST
    json_file=""
    json_file=("./agent_POSTs/POSTendpt_"+fa_id+"_"+str(ep_id)+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()


    #  create and post the FA's ports
    #
    #  first create the Ports collection
    cType = "Ports"
    cPath = rb+"Systems/"+s_id+"/FabricAdapters/"+fa_id+"/"+cType
    wildcards = {"cType":cType, "path":cPath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 
    #  now POST the Ports collection
    json_file=""
    json_file=("./agent_POSTs/POSTport_collection_"+fa_id+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()

    #  now POST the actual ports of the fabric adapter    
    #  find out how many FA ports are connected
    numPortsUsed = len(allAgentNodes["nodes"][nodeID]["topology"]["node_ports"])
    portDict = (allAgentNodes["nodes"][nodeID]["topology"]["node_ports"])
    print("number of ports in use ", numPortsUsed)
    if numPortsUsed >0 :
        for portName,portDesc in portDict.items():
            fap_id=str(portDesc["redfish_portID"])
            print("fap_id = ", fap_id)
            print(portName)
            fap_num = (portName.split(".")[1])

            wildcards = {"rb":rb,"s_id":s_id,"fa_id":fa_id,"fap_id":fap_id,"fap_num":fap_num }
            ofmf_body = copy.deepcopy(get_FabricAdapterPorts_instance(wildcards)) 
            # update port POST body with additional details from agentDB
            # fill in peer port link
            peer_port_num=portDesc["peer_port"]["num"]
            peer_gcid = peer_port_num.split(".")[0]
            peer_nodeID = allAgentNodes["GCID_xref"][peer_gcid]
            peer_entityID = allAgentNodes["nodes"][peer_nodeID]["redfishIDs"]["@odata.id"]
            peer_port = peer_entityID +"/Ports/"+ \
                    str(allAgentNodes["nodes"][peer_nodeID]["topology"]\
                    ["node_ports"][peer_port_num]["redfish_portID"])
            #portDesc["peer_port"]["ConnectedEntity"]=peer_entityID
            portDesc["peer_port"]["ConnectedPorts"]=peer_port
            #ofmf_body["Links"]["ConnectedEntities"].append(\
            #        {"@odata.id": str(portDesc["peer_port"]["ConnectedEntity"])})
            ofmf_body["Links"]["ConnectedPorts"].append(\
                    {"@odata.id": str(portDesc["peer_port"]["ConnectedPorts"])})
            #   
            json_file=""
            json_file=("./agent_POSTs/POSTport"+fa_id+"_"+fap_id+".json")
            print()
            print("posting file ", json_file)
            
            with open(json_file,"w") as jdata:
                 json.dump(ofmf_body,jdata, indent=4)
                 allPostFiles.append(jdata.name)
                 jdata.close()

    return

def postMC_nodes(nodeID,allAgentNodes):

    # media controller template fill and POST function
    
    ofmf_body = {}
    wildcards = {}
    tmpList=[]
    tmpStr=""
    rb = allAgentNodes["fabricIDs"]["rb"]
    
    tmpList = allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["id"].split(":")
    s_num = tmpList[1]      #put SerialNumber in proper place
    c_uuid = tmpList[0]      #put c_uuid in proper place

    ch_id = allAgentNodes["fabricIDs"]["ch_id"] 
    mc_id = allAgentNodes["nodes"][nodeID]["redfishIDs"]["mc_id"] 
    ep_id = allAgentNodes["nodes"][nodeID]["redfishIDs"]["ep_id"] 
    z_id = nodeID               #put instance_uuid in 'UUID' of FA

    #  create a media controller object to POST
    wildcards = {"rb":rb, "s_num":s_num, "c_id":ch_id, "mc_id":mc_id,"z_id":z_id }
    ofmf_body = copy.deepcopy(get_MediaControllers_instance(wildcards)) 


    # add additional details from agentDB into media controller POST
    ofmf_body["Status"]["State"]=\
            allAgentNodes["nodes"][nodeID]["redfishIDs"]["Status"]["State"]
    ofmf_body["GenZ"]["gcid"]=\
            allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["gcids"][0]
    ofmf_body["GenZ"]["c_uuid"]=c_uuid
    ofmf_body["GenZ"]["max_data"]=allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["max_data"]
    ofmf_body["GenZ"]["minChunkSize"]=\
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["minChunkSize"]
    ofmf_body["GenZ"]["maxChunks"]=\
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["maxChunks"]
    tmpStr=allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["@odata.id"]
    ofmf_body["Links"]["Endpoints"].append(\
            {"@odata.id":tmpStr})

    ofmf_body["Links"]["MemoryDomains"] = copy.deepcopy(allAgentNodes["nodes"][nodeID]\
            ["nodeProperties"]["memdomains"])
    
    # do the POST
    json_file=""
    json_file=("./agent_POSTs/POSTnode"+mc_id+".json")
    print()
    print("posting file ", json_file)
    # hack for testing
    with open(json_file,"w") as jdata:
       json.dump(ofmf_body,jdata, indent=4)
       allPostFiles.append(jdata.name)
       jdata.close()
   
   # create the fabric endpoint associated with the media controller
    f_id = allAgentNodes["fabricIDs"]["f_id"]
    wildcards = {"rb":rb, "f_id":f_id , "ep_id":ep_id}
    ofmf_body = copy.deepcopy(get_Endpoints_instance(wildcards)) 

    # update the template with additional details from agentDB
    ofmf_body["ConnectedEntities"][0]["EntityLink"]["@odata.id"]= \
            allAgentNodes["nodes"][nodeID]["redfishIDs"]["@odata.id"]
    ofmf_body["ConnectedEntities"][0]["EntityType"]= \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["EntityType"]
    ofmf_body["ConnectedEntities"][0]["GenZ"]=copy.deepcopy( \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["GenZ"])
    ofmf_body["Name"] = \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]
    ofmf_body["Description"] = "endpoint for "+\
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]
    
    # do the POST
    json_file=""
    json_file=("./agent_POSTs/POSTendpt_"+mc_id+"_"+str(ep_id)+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()


    #  create and post the MediaController's ports
    #
    #  first create the Ports collection
    cType = "Ports"
    cPath = rb+"Chassis/"+ch_id+"/MediaControllers/"+mc_id+"/"+cType
    wildcards = {"cType":cType, "path":cPath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 
    #  now POST the Ports collection
    json_file=""
    json_file=("./agent_POSTs/POSTport_collection_"+mc_id+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()

    #  now POST the actual ports of the fabric adapter    
    #  find out how many FA ports are connected
    numPortsUsed = len(allAgentNodes["nodes"][nodeID]["topology"]["node_ports"])
    portDict = (allAgentNodes["nodes"][nodeID]["topology"]["node_ports"])
    print("number of ports in use ", numPortsUsed)
    if numPortsUsed >0 :
        for portName,portDesc in portDict.items():
            mcp_id=str(portDesc["redfish_portID"])
            print("mcp_id = ", mcp_id)
            print(portName)
            mcp_num = (portName.split(".")[1])

            wildcards = {"rb":rb,"ch_id":ch_id,"mc_id":mc_id,\
                    "mcp_id":mcp_id,"mcp_num":mcp_num }
            ofmf_body = copy.deepcopy(get_MediaControllerPorts_instance(wildcards)) 
            # update port POST body with additional details from agentDB
            # fill in peer port link
            peer_port_num=portDesc["peer_port"]["num"]
            peer_gcid = peer_port_num.split(".")[0]
            peer_nodeID = allAgentNodes["GCID_xref"][peer_gcid]
            peer_entityID = allAgentNodes["nodes"][peer_nodeID]["redfishIDs"]["@odata.id"]
            peer_port = peer_entityID +"/Ports/"+ \
                    str(allAgentNodes["nodes"][peer_nodeID]["topology"]\
                    ["node_ports"][peer_port_num]["redfish_portID"])
            #portDesc["peer_port"]["ConnectedEntity"]=peer_entityID
            portDesc["peer_port"]["ConnectedPorts"]=peer_port
            #ofmf_body["Links"]["ConnectedEntities"].append(\
            #        {"@odata.id": str(portDesc["peer_port"]["ConnectedEntity"])})
            ofmf_body["Links"]["ConnectedPorts"].append(\
                    {"@odata.id": str(portDesc["peer_port"]["ConnectedPorts"])})
            #   
            json_file=""
            json_file=("./agent_POSTs/POSTport"+mc_id+"_"+mcp_id+".json")
            print()
            print("posting file ", json_file)
            
            with open(json_file,"w") as jdata:
                 json.dump(ofmf_body,jdata, indent=4)
                 allPostFiles.append(jdata.name)
                 jdata.close()

    return

def postSW_nodes(nodeID,allAgentNodes):

    # switch template fill and POST function
    
    ofmf_body = {}
    wildcards = {}
    tmpList=[]
    tmpStr=""
    rb = allAgentNodes["fabricIDs"]["rb"]
    f_id = allAgentNodes["fabricIDs"]["f_id"]
    
    tmpList = allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["id"].split(":")
    s_num = tmpList[1]      #put SerialNumber in proper place
    c_uuid = tmpList[0]      #put c_uuid in proper place

    sw_id = allAgentNodes["nodes"][nodeID]["redfishIDs"]["sw_id"] 
    z_id = nodeID               #put instance_uuid in 'UUID' of FA

    
    #  create a switch object to POST
    wildcards = {"rb":rb, "s_num":s_num, "s_id":sw_id, "f_id":f_id,"z_id":z_id }
    ofmf_body = copy.deepcopy(get_Switches_instance(wildcards)) 

   

    # add additional details from agentDB into Switch POST
    ofmf_body["Status"]["State"]=\
            allAgentNodes["nodes"][nodeID]["redfishIDs"]["Status"]["State"]
    ofmf_body["GenZ"]["gcid"]=\
            allAgentNodes["nodes"][nodeID]["zephyrNodeIDs"]["gcids"][0]
    tmpStr=allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["@odata.id"]
    ofmf_body["Links"]["Endpoints"].append(\
            {"@odata.id":tmpStr})
    ofmf_body["GenZ"]["c_uuid"]=c_uuid

    
    # do the POST
    json_file=""
    json_file=("./agent_POSTs/POSTswitch"+sw_id+".json")
    print()
    print("posting file ", json_file)
    # hack for testing
    with open(json_file,"w") as jdata:
       json.dump(ofmf_body,jdata, indent=4)
       allPostFiles.append(jdata.name)
       jdata.close()
   
   # create the endpoint associated with the switch
    ep_id = allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Id"]
    f_id = allAgentNodes["fabricIDs"]["f_id"]
    wildcards = {"rb":rb, "f_id":f_id , "ep_id":ep_id}
    ofmf_body = copy.deepcopy(get_Endpoints_instance(wildcards)) 

    # update the template with additional details from agentDB
    ofmf_body["ConnectedEntities"][0]["EntityLink"]["@odata.id"]= \
            allAgentNodes["nodes"][nodeID]["redfishIDs"]["@odata.id"]
    ofmf_body["ConnectedEntities"][0]["EntityType"]= \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["EntityType"]
    ofmf_body["ConnectedEntities"][0]["GenZ"]=copy.deepcopy( \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["functionality"]["GenZ"])
    ofmf_body["Name"] = \
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]
    ofmf_body["Description"] = "endpoint for "+\
            allAgentNodes["nodes"][nodeID]["nodeProperties"]["endpoints"]["Name"]
    
    # do the POST
    json_file=""
    json_file=("./agent_POSTs/POSTendpt_"+sw_id+"_"+str(ep_id)+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()


    #  create and post the Switch's ports
    #
    #  first create the Ports collection if needed
    cType = "Ports"
    cPath = rb+"Fabrics/"+f_id+"/Switches"+sw_id+"/"+cType
    wildcards = {"cType":cType, "path":cPath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 
    #  now POST the Ports collection
    #  just build a sample collection file, POSTing the switch caused
    #  the OFMF emulator to create and post the associated Ports collection
    json_file=""
    json_file=("./agent_POSTs/POSTport_collection_"+sw_id+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        #allPostFiles.append(jdata.name)
        jdata.close()

    #  now POST the actual ports of the switch 
    #  find out how many switch ports are connected
    numPortsUsed = len(allAgentNodes["nodes"][nodeID]["topology"]["node_ports"])
    portDict = (allAgentNodes["nodes"][nodeID]["topology"]["node_ports"])
    print("number of ports in use ", numPortsUsed)
    if numPortsUsed >0 :
        for portName,portDesc in portDict.items():
            fsp_id=str(portDesc["redfish_portID"])
            print("fsp_id = ", fsp_id)
            print(portName)
            fsp_num = (portName.split(".")[1])

            wildcards = {"rb":rb,"f_id":f_id,"s_id":sw_id,"fsp_id":fsp_id,"fsp_num":fsp_num }
            ofmf_body = copy.deepcopy(get_FabricSwitchPorts_instance(wildcards)) 
            # update port POST body with additional details from agentDB
            # fill in peer port link
            peer_port_num=portDesc["peer_port"]["num"]
            peer_gcid = peer_port_num.split(".")[0]
            peer_nodeID = allAgentNodes["GCID_xref"][peer_gcid]
            peer_entityID = allAgentNodes["nodes"][peer_nodeID]["redfishIDs"]["@odata.id"]
            peer_port = peer_entityID +"/Ports/"+ \
                    str(allAgentNodes["nodes"][peer_nodeID]["topology"]\
                    ["node_ports"][peer_port_num]["redfish_portID"])
            peer_endpt = str(allAgentNodes["nodes"][peer_nodeID]["nodeProperties"]\
                    ["endpoints"]["@odata.id"])
            portDesc["peer_port"]["AssociatedEndpoints"]=peer_endpt
            portDesc["peer_port"]["ConnectedPorts"]=peer_port
            ofmf_body["Links"]["AssociatedEndpoints"].append(\
                    {"@odata.id": str(portDesc["peer_port"]["AssociatedEndpoints"])})
            ofmf_body["Links"]["ConnectedPorts"].append(\
                    {"@odata.id": str(portDesc["peer_port"]["ConnectedPorts"])})
            #   
            json_file=""
            json_file=("./agent_POSTs/POSTport"+sw_id+"_"+fsp_id+".json")
            print()
            print("posting file ", json_file)
            
            with open(json_file,"w") as jdata:
                 json.dump(ofmf_body,jdata, indent=4)
                 allPostFiles.append(jdata.name)
                 jdata.close()

    return

def createRootCollections():

    rb = "/redfish/v1/"
    ofmf_body = {}

    #  create and post the root Systems collection
    cType = "Systems"
    rootpath = rb+cType
    wildcards = {"cType":cType, "path":rootpath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 

    json_file=""
    json_file=("./agent_POSTs/POSTroot_"+cType+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()

    #  create and post the root Fabrics collection
    cType = "Fabrics"
    rootpath = rb+cType
    wildcards = {"cType":cType, "path":rootpath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 

    json_file=""
    json_file=("./agent_POSTs/POSTroot_"+cType+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()

    #  create and post the root Chassis collection
    cType = "Chassis"
    rootpath = rb+cType
    wildcards = {"cType":cType, "path":rootpath }
    ofmf_body = copy.deepcopy(get_Collection_instance(wildcards)) 

    json_file=""
    json_file=("./agent_POSTs/POSTroot_"+cType+".json")
    print()
    print("posting file ", json_file)
    with open(json_file,"w") as jdata:
        json.dump(ofmf_body,jdata, indent=4)
        allPostFiles.append(jdata.name)
        jdata.close()


    return


def post_to_OFMF(allPostFiles):
    headers = {'Content-type':'application/json', 'Accept':'text/plain'}

    OFMF_URI = g.OFMF
    if g.OFMFCONFIG == 'Enable':
        print("POSTing configuration to ", OFMF_URI)
        # first reset the OFMF Resources
        postID="/redfish/v1/resetclear"
        print(OFMF_URI+postID)
        r = requests.delete(OFMF_URI+postID, headers=headers)
        print(r)
        print(r.text)

        # now POST all the initial configuration files
        for index, postName in enumerate(allPostFiles):
            print("POST file is ",postName)
            postFile = postName
            with open(postFile,"r") as file_json:
                data = json.load(file_json)
            file_json.close()
            postID=data["@odata.id"]
            print(postID)
            print(data)
            r = requests.post(OFMF_URI+postID, data=json.dumps(data), headers=headers)
            print(r)
            print(r.text)



    return

def zConfigParser(myfile):
    print()
    print("---------------- runParser ------------")
    allAgentNodes={"fabricIDs":{}, "nodes":{}, "endpt_xref":{},\
            "mDomain_xref":{}, "GCID_xref":{}  }
    tmpTopology={}
    cClassDecoder = copy.deepcopy(_cClassLUT)

    global allPostFiles 
    allPostFiles =[]
    data= {}

    # see if Zephyr has a config file for us
    data = getZephyrConfig(myfile)
    print("returned config file is ",json.dumps(data, indent=4))
    nodeCount=0
    memDomainCount=0
    daxCount=0

    print("processing Graph -------------------")
    
    allAgentNodes["fabricIDs"] = copy.deepcopy(data["graph"])
    allAgentNodes["fabricIDs"]["@odata.id"] = "INVALID"
    allAgentNodes["fabricIDs"]["nodeCount"] = nodeCount
    allAgentNodes["fabricIDs"]["daxCount"] = daxCount

    print("processing Nodes -------------------")
    tmpNodes = copy.deepcopy(data["nodes"])
    for index, item in enumerate(tmpNodes):

        #use instance_uuid as the nodeID for agentDB
        tmpNodeID=item["instance_uuid"]  
        tmpNodeCclass = str(item["cclass"])
        print(tmpNodeCclass)
        print(tmpNodeID)
        print("class ",cClassDecoder[tmpNodeCclass]["genZtype"])
        agentTMPL = cClassDecoder[tmpNodeCclass]["agentTemplate"]
        with open(agentTMPL) as file_json:
            agentNodeTemplate = json.load(file_json)
        file_json.close()
        # if new node, add it to agent DB, if exists, update it
        if tmpNodeID in allAgentNodes["nodes"]:
            print("duplicate instance_uuid?", tmpNodeID)
            #update existing entry with actual values from zephry 
            #not really working and tested, just a placeholder
            #updateZephyrNodeIDs(item,allAgentNodes)
        else:

            print("adding new node")
            nodeCount = nodeCount+1  # adjust node count, which equals endpoint count
            allAgentNodes["fabricIDs"]["nodeCount"] = nodeCount
            allAgentNodes["endpt_xref"][str(nodeCount)] = tmpNodeID
            allAgentNodes["nodes"][tmpNodeID] = copy.deepcopy(agentNodeTemplate)
            allAgentNodes["nodes"][tmpNodeID]["nodeProperties"]["endpoints"]["Id"] \
                            = str(nodeCount)
            allAgentNodes["nodes"][tmpNodeID]["zephyrNodeIDs"]\
                                ["node_index"] = str(nodeCount)
            maxMem=item["max_data"]  # extract memory capacity of node
            if maxMem>0:

                memDomainCount = memDomainCount + 1  # need another mem domain
                allAgentNodes["fabricIDs"]["memDomainCount"] = memDomainCount
                allAgentNodes["nodes"][tmpNodeID]["zephyrNodeIDs"]\
                                ["md_index"] = str(memDomainCount)
                allAgentNodes["mDomain_xref"][str(memDomainCount)] = tmpNodeID
                    
            updateZephyrNodeIDs(item,allAgentNodes)

    #  now for Links
    tmpLinks = copy.deepcopy(data["links"])
    print()
    print("now for links")
    for index, item in enumerate(tmpLinks):
        print("link ", index)  #links is a list of link objects
        parseZephyrLink(item,allAgentNodes)  #'item' is a zephyr link object
    print()
    
    #done with parsing networkX configuration and building initial agent database
    # now need to create Redfish model of the configuration
    # create the root Chassis, Fabrics, Systems collections
    createRootCollections()
    # create a fabric instance to POST to OFMF
    uploadFabricInstance(allAgentNodes)
    # emulator will POST the following subordinate collections of 
    # the new fabric:  Connections, Endpoints, Switches, and Zones

    # if any nodes had memory, need a chassis collection and the
    # associated memory domain collections and memory controller collections
    if memDomainCount > 0:
        uploadChassis(allAgentNodes,memDomainCount)
    # create all the Redfish ID's we need 
    createRedfishIDs(allAgentNodes,cClassDecoder)
    # create the node instances for POSTing
    postRedfishNodes(allAgentNodes,cClassDecoder) 
    # create the associated memory structures but don't POST the memory chunks
    createMemChunkIDs(allAgentNodes)
    # in POC, don't create the default connections
    #createDefaultConnections(allAgentNodes)

    # do the actual posts to OFMF, if it is running
    #  allPostFiles[] contains only the files to be posted, in the correct order!
    post_to_OFMF(allPostFiles)

    # put the agent data base in a file
    with open("./agentDB.json","w") as jdata:
        json.dump(allAgentNodes,jdata, indent=4)
        jdata.close()

    with open("./agent_POSTs/postFiles.json","w") as jdata:
        json.dump(allPostFiles,jdata, indent=4)
        jdata.close()

    #print(json.dumps(allPostFiles, indent = 4))
    #print(json.dumps(allAgentNodes,indent = 4))
    return 200
