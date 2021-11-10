Agent_POSTs directory:
Contains tools (*.py) and lots of .json files to test the OFMF_POC and 
the OFMF_Agent emulators in a ‘stacked’ arrangement.  The OFMF_POC emulator 
interfaces to the clients and the admin GUI/CLI.  The OFMF_Agent will 
interface to the Zephyr (Gen-Z / Linux) fabric manager.  
The two emulators talk to each other as necessary.

To work together, both the OFMF-GenZ-POC and OFMF-Agent-POC  must be 
cloned into clean directories, and then targeted to the ‘agent_test’ 
branches of repo’s.
To clone each repo, start at a convenient ‘BASE_DIR’ base directory that 
does not have a current OFMF_Agent or OFMF_POC working directory which 
you do not overwritten.

Starting at BASE_DIR:
1)	mkdir ./<myNewOFMF-GenZ-POC/
2)	cd ./myNewOFMF-GenZ-POC
3)	git clone <OFMFWG/OFMF-GenZ-POC…..>  .      
		#be sure to clone to your current directory!
4)	git branch –a  		   # see if agent_test branch is still unmerged
5)	git checkout agent_test    # if available, use the agent_test branch
6)	Repeat 1-5 for a new OFMF-Agent-POC download


To run the two emulators and test them:
1)	Edit the OFMF-GenZ-POC/emulator-config.json file
	a.	Set the AGENTURI value to the URL of the host server the 
		Agent emulator will run on, so the OFMF POC server 
		can find the Agent
2)	From the OFMF-GenZ-POC directory, run ‘setup.sh’ file.  
		(you may have to change permissions on it to add 
		execution capability )
	a.	Emulator setup script will create the peer working directory 
		OFMF_POC, clone a redfish emulator repo into that directory, 
		clone the mockups directory 
	(CAUTION: if you don’t want to wipe out the 
		mockups you have in that directory, or you don’t have access 
		to the github site, change the setup.sh scripts accordingly!!) 
3)	Wait for the OFMF_POC emulator to finish initializing… 
4)	From the OFMF-Agent-POC directory, run ‘setup.sh’ file 
	a.	This setup script will also create a working directory (OFMF_Agent).
	b.	This setup script will ALSO create a new mockups directory, 
		at the same peer level as OFMF_POC setup script. 
		The two scripts will fight over the mockups directory 
		cloning if the two emulators are in peer directories off 
		the same parent directory!
		However, once an emulator is initialized and running, 
		the mockups directory is no longer used, so things don't get 
		messed up if you start up each emulator in series.

5)	Once the two emulators are running, 
	a.	change directory to newOFMF-Agent-POC/agent_POSTs directory
6)	Invoke a python shell (3.5v or later, I’m using 3.8)
7)	In the python shell:
8)	>>>  import myPoster
9)	>>> from myPoster import *
10)	>>> import myReset
11)	>>> from myReset import *
12)	>>> runReset(HTTP://192.168.11.118:5000)  
	a.	Use whatever IP address the OFMF_POC emulator claims its 
		running with, and the port should be the default 5000.
	b.	This script will reset the OFMF_POC emulator and wipe out 
		the default mockups from the emulator’s database
13)	>>> runPOSTer(“./postFiles.json”, “HTTP://192.168.11.118:5000)
	a.	This script will read a list of json based POST “bodies” 
		from postFiles.json and send them, in order, to the OFMF_POC 
		emulator.
	b.	These POST requests build a redfish fabric tree that describes 
		a default topology configuration which Jim Hull supplied.
	c.	There are NO memory chunks or connections in this list, these 
		come later.  Therefore, the Agent emulator will display no activity.
	d.	After these POSTs finish, the OFMF_POC emulator will have 
		the same default initial configuration as the 
		Agent emulator fires up with.
14)	>>> runPOSTer(“./postFilechunks.json”, “HTTP://192.168.11.118:5000)
	a.	This script will post 4 memory chunks to the OFMF_POC emulator, 
		one for each of the four memory sources in the default topology.
	b.	The OFMF_POC emulator will forward these memory chunk 
		definitions to the Agent emulator, which will in-turn add 
		them to its database.
	c.	These 4 source files are POSTmemChunk*, and 
		make good templates for guiding the creation of 
		additional memory chunks.  
		(see rules of memory chunks later in the document)
15)	>>> runPOSTer("./postFileConnections.json","HTTP://192.168.11.118:5000")
	a.	This script will post a single connection between 
		a single ‘target’ endpoint (a single memory chunk as a ‘producer’) 
		and TWO initiator endpoints (two ‘consumers’)
	b.	The OFMF_POC emulator will pass this to the Agent emulator
	c.	The Agent emulator will update its internal Data Base about 
		resource allocations (producers bound to consumers in 
		Zephyr-speak), and the Agent will 
		i.	Produce a json file with the command body to be 
			sent to the Zephyr fabric manager, and store that file 
			in the OFMF_Agent working directory (I’ll put it 
			in a smarter location in a later version)
	ii.	Eventually the Agent will send the command headers and command 
		body to Zephyr.  That isn’t working yet, but the 
		output file can be inspected for proper data.
16)	Additional connections can be created and POSTed by using the 
	tools in the agent_POSTs directory.  
17)	Since DELETEs and PATCHes of memory chunks are not yet supported, 
	experimenting with different numbers and sizes of memory chunks requires 
	the experimenter to stop at step 14 and create their own memory chunk 
	and connection POSTs.  


VERY IMPORTANT NOTES:
	A)	The OFMF_POC emulator can be (and MUST be) reset to wipe out 
		its initial configuration (step 12), but the Agent 
		(running agent_test branch) CANNOT. 
	B)	Both emulators must be running agent_test branch 
		(if it has not been merged into master)
		a.	The OFMF_POC emulator will function without the 
			OFMF_Agent emulator being present, as long as no 
			memory chunks or connections are targeted by client 
			requests, but only if the agent_test branch modifications 
			are used.
	b.	OFMF_POC emulator will not function properly for POSTing 
			several objects, without the agent_test branch mods.

Notes about ‘connections’ and memory chunks:
a)	There can only be ONE target endpoint listed in a connection.  
a.	Zephyr and the Agent are currently only accepting one Producer of 
	memory in an ‘add_resource’ command
b)	For PoC demos, we limit all connections to ONE initiator endpoint in a 
	connection request.
	a.	Supposedly, The emulators will both support listing MULTIPLE 
		initiators in a connection
	b.	Supposedly, Zephyr accepts multiple ‘consumers’ in a single request
	c.	We have too little time to test these, so PLEASE let’s just 
		use ONE target, ONE initiator per connection request
c)	For PoC demos, we limit all connections to ONE memory chunk at the 
		ONE target.
	a.	The same target can source multiple chunks to multiple consumers 
		or the same consumer, but we make the ‘connections’ 
		between them ONE at a time.
d)	Memory chunks are subdivisions of a SINGLE memory domain, 
	which is itself associated with a single endpoint.
e)	Memory chunk ranges do not have to start at 0.  
f)	Memory chunk size must be a multiple of the minimum chunk size 
	that is listed in the associated memory domain details.
g)	Memory chunk ranges MUST NOT overlap with another chunk’s 
	range within the same memory domain
h)	Memory chunks do not have to be contiguous in range with any other 
	memory chunk within a memory domain.
i)	The default memory domains do NOT have default memory chunks assigned…  
	so users need to POST memory chunks before they can POST any connections.
j)	There are NO connections to non-memory targets in the POC!
	a.	Zephyr may make them for other reasons, but our PoC GUI stack 
		is not tracking them.
k)	The Agent and the Zephyr fabric manager do not check the math (much) 
	on memory chunk assignments, so the client Memory Manager 
	(person driving the GUI and creating the memory chunks) is 
	responsible for the math.
l)	Zephyr and the Agent pass several details about resources and 
	connections that are not seen by the OFMF_POC emulator or its clients.

