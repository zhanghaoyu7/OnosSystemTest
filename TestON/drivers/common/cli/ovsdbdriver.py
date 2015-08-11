#!/usr/bin/env python

"""
drivers for ovsdb commands.

zhanghaoyu7@huawei.com
AUG 10 2015
"""
import pexpect
import re
import json
import types
import time
import os
from drivers.common.clidriver import CLI


class OvsdbDriver( CLI ):

    def __init__( self ):
        """
        Initialize client
        """
        self.name = None
        self.home = None
        self.handle = None
        super( CLI, self ).__init__()
    def setManager( self,ip ,port ):
        command= "sudo ovs-vsctl set-manager tcp:" + str(ip) + ":" + str(port)
        try:
            response = self.execute(
                cmd=command,
                timeout=10 )
            return response
        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception found" )
            main.log.error( self.name + ":     " + self.handle.before )
            main.cleanup()
            main.exit()

    def delManager( self):
        command= "sudo ovs-vsctl del-manager"
        try:
            response = self.execute(
                cmd=command,
                timeout=10 )
            return response
        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception found" )
            main.log.error( self.name + ":     " + self.handle.before )
            main.cleanup()
            main.exit()

    def getManager(self):
        command= "sudo ovs-vsctl get-manager"
        try:
            response = self.execute(
                cmd=command,
                timeout=10 )
            return response
        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception found" )
            main.log.error( self.name + ":     " + self.handle.before )
            main.cleanup()
            main.exit()

    def listBr(self):
        """
        Parameters:
            none
        Return:
            The output of the command from the linux
            or main.FALSE on timeout
        """
        command= "sudo ovs-vsctl list-br"
        try:
            response = self.execute(
                cmd=command,
                timeout=10 )
            if response:
                return response
            else:
                return main.FALSE
        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception found" )
            main.log.error( self.name + ":     " + self.handle.before )
            main.cleanup()
            main.exit()

    def listPorts(self ,sw):
        """
        Parameters:
            sw: The name of an OVS switch. Example "s1"
        Return:
            The output of the command from the linux
            or main.FALSE on timeout
        """
        command= "sudo ovs-vsctl list-ports " + str(sw)
        try:
            response = self.execute(
                cmd=command,
                timeout=10 )
            if response:
                return response
            else:
                return main.FALSE
        except pexpect.EOF:
            main.log.error( self.name + ": EOF exception found" )
            main.log.error( self.name + ":     " + self.handle.before )
            main.cleanup()
            main.exit()

    def getController(self, sw):
        """
        Parameters:
            sw: The name of an OVS switch. Example "s1"
        Return:
            The output of the command from the mininet cli
            or main.FALSE on timeout"""
        command = "sudo ovs-vsctl get-controller " + str(sw)
        try:
            response = self.execute(
                cmd=command,
                timeout=10)
            if response:
                return response
            else:
                return main.FALSE
        except pexpect.EOF:
            main.log.error(self.name + ": EOF exception found")
            main.log.error(self.name + ":     " + self.handle.before)
            main.cleanup()
            main.exit()
    def ovsShow(self):
        """
        Parameters:
            none
        Return:
            The output of the command from the linux
            or main.FALSE on timeout"""
        command = "sudo ovs-vsctl show "
        try:
            response = self.execute(
                cmd=command,
                timeout=10)
            if response:
                return response
            else:
                return main.FALSE
        except pexpect.EOF:
            main.log.error(self.name + ": EOF exception found" )
            main.log.error(self.name + ":     " + self.handle.before)
            main.cleanup()
            main.exit()