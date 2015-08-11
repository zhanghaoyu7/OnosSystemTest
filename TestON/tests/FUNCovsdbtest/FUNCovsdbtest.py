"""
Description: This test is to check onos set configuration and flows with ovsdb connection.

List of test cases:
CASE1: Compile ONOS and push it to the test machines
CASE2: Test ovsdb connection and tearDown
CASE3: Test default br-int configuration and vxlan port
CASE4: Test default openflow configuration
CASE5: Test default flows
CASE6: Configure Network Subnet Port And Check On ONOS
CASE7: Test host go online and ping each other
zhanghaoyu7@huawei.com
"""
import os

class FUNCovsdbtest:
    
    def __init__( self ):
        self.default = ''

    def CASE1( self, main ):
        """
        CASE1 is to compile ONOS and push it to the test machines
        
        Startup sequence:
        cell <name>
        onos-verify-cell
        NOTE: temporary - onos-remove-raft-logs
        onos-uninstall
        start mininet
        git pull
        mvn clean install
        onos-package
        onos-install -f
        onos-wait-for-start
        start cli sessions
        start ovsdb
        start onos-core-netvirt
        """
        import os
        main.log.info( "ONOS Single node start " +
                         "ovsdb test - initialization" )
        main.case( "Setting up test environment" )
        main.caseExplanation = "Setup the test environment including " +\
                                "installing ONOS, start ONOS."
 
        # load some variables from the params file
        PULLCODE = False
        if main.params[ 'GIT' ][ 'pull' ] == 'True':
            PULLCODE = True
        gitBranch = main.params[ 'GIT'][ 'branch' ]
        cellName = main.params[ 'ENV'][ 'cellName' ]
        ipList = os.getenv( main.params[ 'CTRL'][ 'ip1' ] )
        OVSDB1Ip = os.getenv( main.params[ 'OVSDB'][ 'ip1' ] )
        OVSDB2Ip = os.getenv( main.params[ 'OVSDB'][ 'ip2' ] )

        main.step( "Create cell file" )
        cellAppString = main.params[ 'ENV' ][ 'cellApps' ]
        main.ONOSbench.createCellFile( main.ONOSbench.ip_address, cellName,
                                       main.Ovsdb1.ip_address,
                                       cellAppString, ipList )

        main.step( "Applying cell variable to environment" )
        cellResult = main.ONOSbench.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()

        # FIXME:this is short term fix
        main.log.info( "Removing raft logs" )
        main.ONOSbench.onosRemoveRaftLogs()

        main.CLIs = []
        main.nodes = []
        main.numCtrls= 1

        for i in range( 1, main.numCtrls + 1 ):
            try:
                main.CLIs.append( getattr( main, 'ONOScli' + str( i ) ) )
                main.nodes.append( getattr( main, 'ONOS' + str( i ) ) )
                ipList.append( main.nodes[ -1 ].ip_address )
            except AttributeError:
                break

        main.log.info( "Uninstalling ONOS" )
        for node in main.nodes:
            main.ONOSbench.onosUninstall( node.ip_address )

        # Make sure ONOS is DEAD
        main.log.info( "Killing any ONOS processes" )
        killResults = main.TRUE
        for node in main.nodes:
            killed = main.ONOSbench.onosKill( node.ip_address )
            killResults = killResults and killed

        cleanInstallResult = main.TRUE
        gitPullResult = main.TRUE
        main.step( "Git checkout and pull" +gitBranch )
        if PULLCODE:
            main.ONOSbench.gitCheckout( gitBranch )
            gitPullResult = main.ONOSbench.gitPull()
            # values of 1 or 3 are good
            utilities.assert_lesser( expect=0, actual=gitPullResult,
                                      onpass="Git pull successful",
                                      onfail="Git pull failed" )

        main.ONOSbench.getVersion( report=True )
        main.step( "Using mvn clean install" )
        cleanInstallResult = main.TRUE
        if PULLCODE and gitPullResult == main.TRUE:
            cleanInstallResult = main.ONOSbench.cleanInstall()
        else:
            main.log.warn( "Did not pull new code so skipping mvn" +
                           "clean install" )

        utilities.assert_equals( expect=main.TRUE,
                                 actual=cleanInstallResult,
                                 onpass="MCI successful",
                                 onfail="MCI failed" )        
        main.step( "Creating ONOS package" )
        packageResult = main.ONOSbench.onosPackage()
        utilities.assert_equals( expect=main.TRUE,
                                     actual=packageResult,
                                     onpass="Successfully created ONOS package",
                                     onfail="Failed to create ONOS package" )

        main.step( "Installing ONOS package" )
        onosInstallResult = main.ONOSbench.onosInstall(
                options="-f", node=main.nodes[0].ip_address )
        utilities.assert_equals( expect=main.TRUE, actual=onosInstallResult,
                                 onpass="ONOS install successful",
                                 onfail="ONOS install failed" )

        main.step( "Checking if ONOS is up yet" )
        print main.nodes[0].ip_address
        for i in range( 2 ):
            onos1Isup = main.ONOSbench.isup( main.nodes[0].ip_address )
            if onos1Isup:
                break
        utilities.assert_equals( expect=main.TRUE, actual=onos1Isup,
                                 onpass="ONOS startup successful",
                                 onfail="ONOS startup failed" )
        main.log.step( "Starting ONOS CLI sessions" )
        print main.nodes[0].ip_address
        cliResults = main.ONOScli1.startOnosCli( main.nodes[0].ip_address )
        utilities.assert_equals( expect=main.TRUE, actual=cliResults,
                                 onpass="ONOS cli startup successful",
                                 onfail="ONOS cli startup failed" )
        main.step( "App Ids check" )
        appCheck = main.ONOScli1.appToIDCheck()

        if appCheck !=main.TRUE:
            main.log.warn( main.CLIs[0].apps() )
            main.log.warn( main.CLIs[0].appIDs() )
            utilities.assert_equals( expect=main.TRUE, actual=appCheck,
                                 onpass="App Ids seem to be correct",
                                 onfail="Something is wrong with app Ids" )
        if cliResults == main.FALSE:
            main.log.error( "Failed to start ONOS,stopping test" )
            main.cleanup()
            main.exit()

        main.step( "Install onos-ovsdb-lib" )
        installResults = main.ONOScli1.featureInstall( "onos-ovsdb-lib" )
        utilities.assert_equals( expect=main.TRUE, actual=installResults,
                                 onpass="Install onos-ovsdb-lib successful",
                                 onfail="Install onos-ovsdb-lib failed" )

        main.step( "Install onos-ovsdb-providers" )
        installResults = main.ONOScli1.featureInstall( "onos-ovsdb-providers" )
        utilities.assert_equals( expect=main.TRUE, actual=installResults,
                                 onpass="Install onos-ovsdb-provider successful",
                                 onfail="Install onos-ovsdb-provider failed" )

        main.step( "Install onos-core-netvirt" )
        installResults = main.ONOScli1.featureInstall( "onos-core-netvirt" )
        utilities.assert_equals( expect=main.TRUE, actual=installResults,
                                 onpass="Install onos-core-netvirt successful",
                                 onfail="Install onos-core-netvirt failed" )

    def CASE2( self, main ):

        import re
        import time
        """
        Test ovsdb connection and teardown
        """
        import os,sys
        ctrlip = os.getenv( main.params['CTRL']['ip1'] )
        ovsdbport = main.params['CTRL']['ovsdbport']
        main.step( "Set ovsdb node manager" )
        assignResult = main.Ovsdb1.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()

        main.step( "Check ovsdb node manager is " + str(ctrlip))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
            main.log.info("ovsdb node manager is " + str(response))
        else:
            assignResult = main.FALSE
            main.log.info("set ovsdb node manager " + str(response) + " failed!")

        main.step( "Check onoscli ovsdb-node have node " + str(OVSDB1Ip))
        response = main.ONOScli1.getOvsdbNode()
        if re.search(OVSDB1Ip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE

        main.step( "Delete ovsdb node manager" )
        assignResult = main.Ovsdb1.delManager()
        if not assignResult:
            main.cleanup()
            main.exit()

        main.step( "Check ovsdb node delete manager " + str(ctrlip))
        response = main.Ovsdb1.getManager()
        if not re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
            main.log.info("delete ovsdb node manager sucess")
        else:
            assignResult = main.FALSE
            main.log.info("delete ovsdb node manager failed")

        main.step( "Check onoscli ovsdb-node delete node " + str(OVSDB1Ip))
        response = main.ONOScli1.getOvsdbNode()
        if not re.search(OVSDB1Ip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        stepResult=assignResult
        utilities.assert_equals( expect=main.TRUE,
                                 actual=stepResult,
                                 onpass="Successfully test ovsdb connection and teardown ",
                                 onfail="Failed to test ovsdb connection and teardown " )

    def CASE3( self, main ):

        import re
        import time
        import os,sys
        """
        Test default br-int configuration and vxlan port
        """
        ctrlip = os.getenv( main.params['CTRL']['ip1'] )
        ovsdbport = main.params['CTRL']['ovsdbport']
        main.step( "ovsdb node 1 set ovs manager to " + str(ctrlip))
        assignResult = main.Ovsdb1.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()

        main.step( "ovsdb node 2 set ovs manager to " + str(ctrlip))
        assignResult = main.Ovsdb2.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()

        main.step( "Check ovsdb node 1 manager is " + str(ctrlip))
        response = main.Ovsdb1.getManager()
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
            main.log.info("ovsdb node 1 manager is " + str(response))
        else:
            assignResult = main.FALSE
            main.log.info("ovsdb node 1 manager check failed ")

        main.step( "Check ovsdb node 2 manager is " + str(ctrlip))
        response = main.Ovsdb2.getManager()
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
            main.log.info("ovsdb node 2 manager is " + str(response))
        else:
            assignResult = main.FALSE
            main.log.info("ovsdb node 1 manager check failed ")

        main.step( "Check default br-int bridge on ovsdb node " + str(OVSDB1Ip))
        response = main.Ovsdb1.listBr()
        if re.search("br-int", response):
            assignResult = assignResult and main.TRUE
            main.log.info("onos add default bridge on the node 1")
        else:
            assignResult = main.FALSE
            main.log.info("onos add default bridge on the node 1 failed ")

        main.step( "Check default br-int bridge on ovsdb node " + str(OVSDB2Ip))
        response = main.Ovsdb2.listBr()
        if re.search("br-int", response):
            assignResult = assignResult and main.TRUE
            main.log.info("onos add default bridge on the node 2")
        else:
            assignResult = main.FALSE
            main.log.info("onos add default bridge on the node 2 failed ")

        main.step( "Check default vxlan port on ovsdb node " + str(OVSDB1Ip))
        response = main.Ovsdb1.listPorts("br-int")
        if re.search("vxlan", response) and re.search(str(OVSDB2Ip), response):
            assignResult = assignResult and main.TRUE
            main.log.info("onos add default vxlan port in the br-int on the node 1")
        else:
            assignResult = main.FALSE
            main.log.info("onos add default vxlan port in the br-int on the node 1 failed")

        main.step( "Check default vxlan port on ovsdb node " + str(OVSDB2Ip))
        response = main.Ovsdb2.listPorts("br-int")
        if re.search("vxlan", response) and re.search(str(OVSDB1Ip), response):
            assignResult = assignResult and main.TRUE
            main.log.info("onos add default vxlan port in the br-int on the node 2")
        else:
            assignResult = main.FALSE
            main.log.info("onos add default vxlan port in the br-int on the node 2 failed")
        stepResult=assignResult
        utilities.assert_equals( expect=main.TRUE,
                                 actual=stepResult,
                                 onpass="Successfully set default br-int configuration and vxlan port " +\
                                 str(ctrlip),
                                 onfail="Failed to set default br-int configuration and vxlan port " +\
                                 str(ctrlip))        

    def CASE4( self, main ):
        import re
        import time
        import os,sys
        """
        Test default openflow configuration
        """
        ctrlip = main.params['CTRL']['ip1']
        ovsdbport = main.params['CTRL']['ovsdbport']
        main.step( "ovsdb node 1 set ovs manager to " + str(ctrlip))
        assignResult = main.Ovsdb1.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        main.step( "ovsdb node 2 set ovs manager to " + str(ctrlip))
        assignResult = main.Ovsdb2.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        main.step( "Check ovsdb node 1 manager is " + str(ctrlip))
        response = main.Ovsdb1.getManager()
        main.log.info("ovsdb node 1 manager is " + str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check ovsdb node 2 manager is " + str(ctrlip))
        response = main.Ovsdb2.getManager()
        main.log.info("ovsdb node 2 manager is " + str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check ovsdb node 1 bridge br-int controller set to " + str(ctrlip))
        response = main.Ovsdb1.getController("br-int")
        print("Response is "+ str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check ovsdb node 2 bridge br-int controller set to  " + str(ctrlip))
        response = main.Ovsdb2.getController("br-int")
        print("Response is "+ str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
            
        main.step( "Check onoscli devices have ovs " + str(OVSDB1Ip))
        response = main.ONOScli1.devices()
        print("Response is "+ str(response))
        if re.search(OVSDB1Ip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check onoscli devices have ovs " + str(OVSDB2Ip))
        response = main.ONOScli1.devices()
        print("Response is "+ str(response))
        if re.search(OVSDB2Ip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        stepResult=assignResult
        utilities.assert_equals( expect=main.TRUE,
                                 actual=stepResult,
                                 onpass="Successfully set default openflow configuration " +
                                        str(ctrlip),
                                 onfail="Failed to set default openflow configuration " +
                                        str(ctrlip))  
    def CASE5( self, main ):
        import re
        import time
        import os,sys
        """
        Test default flows
        """
        ctrlip = main.params['CTRL']['ip1']
        ovsdbport = main.params['CTRL']['ovsdbport']
        main.step( "ovsdb node 1 set ovs manager to onos" )
        assignResult = main.Ovsdb1.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        main.step( "Check ovsdb node 1 manager is " + str(ctrlip))
        response = main.Ovsdb1.getManager()
        print("Response is "+ str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check ovsdb node 1 bridge br-int default flows on " + str(OVSDB1Ip))
        response = main.Ovsdb1.dumpFlows(sw="br-int",protocols="OpenFlow13")
        print("Response is "+ str(response))    
        if re.search("cookie", response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        stepResult=assignResult
        utilities.assert_equals( expect=main.TRUE,
                                 actual=stepResult,
                                 onpass="Successfully set default flows " +
                                        str(ctrlip),
                                 onfail="Failed to set default flows " +
                                        str(ctrlip))
    def CASE6( self, main ):
        """
        Configure Network Subnet Port And Check On ONOS
        """
        import os,sys
        sys.path.append("..")
        from tests.FUNCovsdbtest.dependencies.Nbdata import NetworkData
        from tests.FUNCovsdbtest.dependencies.Nbdata import SubnetkData
        from tests.FUNCovsdbtest.dependencies.Nbdata import VirtualPortData
        
        ctrlip = main.params['CTRL']['ip1']
        port = main.params['HTTP']['port']
        path = main.params['HTTP']['path']
        
        main.step( "Generate Post Data" )
        network = NetworkData
        network.id = '030d6d3d-fa36-45bf-ae2b-4f4bc43a54dc'
        network.tenant_id = '26cd996094344a0598b0a1af1d525cdc'
        subnet = SubnetkData()
        subnet.id = 'e44bd655-e22c-4aeb-b1e9-ea1606875178'
        subnet.tenant_id = network.tenant_id
        subnet.network_id = network_id
        virtualport = VirtualPortData()
        virtualport.id = '9352e05c-58b8-4f2c-b3df-c20624e22d44'
        virtualport.subnetId =subnet.id
        virtualport.tenant_id = network.tenant_id
        virtualport.network_id = network_id
        
        networkpostdata = network.DictoJson()
        subnetkpostdata = subnet.DictoJson()
        virtualportpostdata = virtualport.DictoJson()
        
        main.step( "Post Network Data via HTTP(post port need post network)" )
        Poststatus, result = main.ONOSrest.send(ctrlip,port,'',path+'networks/','POST',None,networkpostdata)
        utilities.assert_equals(
                expect='200',
                actual=Poststatus,
                onpass="Post Network Success ",
                onfail="Post Network Failed " + str(Poststatus)+str(result))
        
        main.step( "Post Subnet Data via HTTP(post port need post network)" )
        Poststatus, result = main.ONOSrest.send(ctrlip,port,'',path+'subnets/','POST',None,subnetpostdata)
        utilities.assert_equals(
                expect='202',
                actual=Poststatus,
                onpass="Post Subnet Success ",
                onfail="Post Subnet Failed " + str(Poststatus)+str(result))
        
        main.step( "Post VirtualPort Data via HTTP" )
        Poststatus, result = main.ONOSrest.send(ctrlip,port,'',path+'virtualports/','POST',None,virtualportpostdata)
        utilities.assert_equals(
                expect='200',
                actual=Poststatus,
                onpass="Post VirtualPort Success ",
                onfail="Post VirtualPort Failed " + str(Poststatus)+str(result))
    def CASE7( self, main ):
        import re
        import time
        import os,sys
        """
        Test host go online and ping each other
        """
        ctrlip = main.params['CTRL']['ip1']
        ovsdbport = main.params['CTRL']['ovsdbport']
        OVSDB1Ip = main.params['MN']['ip1']
        OVSDB2Ip = main.params['MN']['ip2']
        main.step( "ovsdb node 1 set ovs manager to " + str(ctrlip))
        assignResult = main.Ovsdb1.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        main.step( "ovsdb node 2 set ovs manager to " + str(ctrlip))
        assignResult = main.Ovsdb2.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        
        main.step( "Create host1 on node 1 " + str (OVSDB1Ip))
        assignResult = main.Ovsdb1.createHost(hostname="host1")
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
       
        main.step( "Create host2 on node 2 " + str (OVSDB2Ip))
        assignResult = main.Ovsdb2.createHost(hostname="host2")
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        
        main.step( "Create port on host1 on the node " + str (OVSDB1Ip))
        assignResult = main.Ovsdb1.createHostport(hostname="host1",hostport="host1-eth0",hostportmac="000000000001")
        if not assignResult:
            main.cleanup()
            main.exit()
        main.step( "Create port on host2 on the node " + str (OVSDB2Ip))
        assignResult = main.Ovsdb2.createHostport(hostname="host2",hostport="host2-eth0",hostportmac="000000000002")
        if not assignResult:
            main.cleanup()
            main.exit()    
            
        main.step( "add port to ovs br-int and host go-online on the node " + str (OVSDB1Ip))
        assignResult = main.Ovsdb1. addPortToOvs(ovsname="br-int",ifaceId="host1-eth0",attachedMac="000000000001")
        if not assignResult:
            main.cleanup()
            main.exit() 
        main.step( "add port to ovs br-int and host go-online on the node " + str (OVSDB2Ip))
        assignResult = main.Ovsdb1. addPortToOvs(ovsname="br-int",ifaceId="host2-eth0",attachedMac="000000000002")
        if not assignResult:
            main.cleanup()
            main.exit()
        main.step( "Check onos set host flows on the node " + str(OVSDB1Ip))
        response = main.Ovsdb1.dumpFlows(sw="br-int",protocols="OpenFlow13")
        print("Response is " + str(response))    
        if re.search("cookie", response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check onos set host flows on the node " + str(OVSDB2Ip))
        response = main.Ovsdb2.dumpFlows(sw="br-int",protocols="OpenFlow13")
        print("Response is " + str(response))    
        if re.search("cookie", response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
            
        main.step( "Check hosts can ping each other" )
        main.Ovsdb1.setHostportIp(hostname="host1" , hostport1="host1-eth0" , ip="10.0.0.1")
        main.Ovsdb1.setHostportIp(hostname="host2" , hostport1="host2-eth0" ,ip="10.0.0.2")
        pingResult1 = main.Ovsdb1.hostPing(src="10.0.0.1" ,hostname="host1" ,target="10.0.0.2" )
        pingResult2 = main.Ovsdb2.hostPing(src="10.0.0.2" ,hostname="host2" ,target="10.0.0.1" )
        stepResult = assignResult and pingResult1 and pingResult2
        utilities.assert_equals( expect=main.TRUE,
                                 actual=stepResult,
                                 onpass="Successfully host go online and ping each other,controller is " +
                                        str(ctrlip),
                                 onfail="Failed to host go online and ping each other,controller is " +
                                        str(ctrlip))
