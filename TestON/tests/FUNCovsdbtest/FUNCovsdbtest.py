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
        onos-verity-cell
        NOTE: temporary - onos-remove-raft-logs
        onos-uninstall
        start mininet
        git pull
        mvn clean install
        onos-package
        onos-install -f
        onos-wait-for-start
        start cli sessions
        start tcpdump
        """
        main.log.info( "ONOS Single node start " +
                         "openstack fwd test - initialization" )
        main.case( "Setting up test environment" )
        main.caseExplanation = "Setup the test environment including " +\
                                "installing ONOS, start ONOS."
                                
        # load some variables from the params file
        PULLCODE = False
        if main.params[ 'GIT' ][ 'pull' ] == 'True':
            PULLCODE = True
        gitBranch = main.params[ 'GIT'][ 'branch' ]
        cellName = main.params[ 'ENV'][ 'cellName' ]
        ipList = main.params[ 'CTRL'][ 'ip1' ]
        MN1Ip = main.params[ 'MN'][ 'ip1' ]
        MN2Ip = main.params[ 'MN'][ 'ip2' ]
        
        main.step( "Create cell file" )
        cellAppString = main.params[ 'ENV' ][ 'cellApps' ]
        main.ONOSbench.createCellFile( main.ONOSbench.ip_address, cellName,
                                       main.Mininet1.ip_address,
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
            main.log.warm( "Did not pull new code so skipping mvn" +
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
        import time
        time.sleep(20)
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
        ctrlip = main.params['CTRL']['ip1']
        ovsdbport = main.params['CTRL']['ovsdbport']
        main.step( "Set ovsdb node manager" )
        assignResult = main.Mininet1.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        main.step( "Check ovsdb node manager is " + str(ctrlip))
        response = main.Mininet1.getManager()
        print("Response is "+ str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check onoscli ovsdb-node have node " + str(MN1IP))
        response = main.ONOScli1.getOvsdbNode()
        print("Response is " + str(response))
        if re.search(MN1IP, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Delete ovsdb node manager" )
        assignResult = main.Mininet1.delManager()
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        main.step( "Check ovsdb node delete manager " + str(ctrlip))
        response = main.Mininet1.getManager()
        print("Response is "+ str(response))
        if not re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check onoscli ovsdb-node delete node " + str(MN1IP))
        response = main.ONOScli1.getOvsdbNode()
        print("Response is " + str(response))
        if not re.search(MN1IP, response):
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
        ctrlip = main.params['CTRL']['ip1']
        ovsdbport = main.params['CTRL']['ovsdbport']
        main.step( "ovsdb node 1 set ovs manager to " + str(ctrlip))
        assignResult = main.Mininet1.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        main.step( "ovsdb node 2 set ovs manager to " + str(ctrlip))
        assignResult = main.Mininet2.setManager(ip=ctrlip,port=ovsdbport)
        if not assignResult:
            main.cleanup()
            main.exit()
        time.sleep(2)
        main.step( "Check ovsdb node 1 manager is " + str(ctrlip))
        response = main.Mininet1.getManager()
        print("Response is "+ str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check ovsdb node 2 manager is " + str(ctrlip))
        response = main.Mininet2.getManager()
        print("Response is "+ str(response))
        if re.search(ctrlip, response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check default br-int bridge on ovsdb node " + str(MN1Ip))
        response = main.Mininet1.listBr()
        print("Response is "+ str(response))
        if re.search("br-int", response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check default br-int bridge on ovsdb node " + str(MN2Ip))
        response = main.Mininet2.listBr()
        print("Response is "+ str(response))
        if re.search("br-int", response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check default vxlan port on ovsdb node " + str(MN1Ip))
        response = main.Mininet1.listPorts("br-int")
        print("Response is "+ str(response))
        if re.search("vxlan", response) and re.search(str(MN2Ip), response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        main.step( "Check default vxlan port on ovsdb node " + str(MN2Ip))
        response = main.Mininet2.listPorts("br-int")
        print("Response is "+ str(response))
        if re.search("vxlan", response) and re.search(str(MN1Ip), response):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE
        stepResult=assignResult
        utilities.assert_equals( expect=main.TRUE,
                                 actual=stepResult,
                                 onpass="Successfully set default br-int configuration and vxlan port " + str(ctrlip),
                                 onfail="Failed to set default br-int configuration and vxlan port " + str(ctrlip))        
