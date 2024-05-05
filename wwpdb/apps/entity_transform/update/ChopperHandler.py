##
# File:  ChopperHandler.py
# Date:  08-Dec-2012
# Updates:
##
"""
Merge/Split coordinates based on output from chopper tool.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2012 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle
#

import os
import sys

from wwpdb.apps.entity_transform.utils.CommandUtil import CommandUtil
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage


class ChopperHandler(object):
    """ Class responsible for handling chopper tool output.
    """
    def __init__(self, reqObj=None, summaryFile=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__summaryFile = summaryFile
        self.__sObj = None
        self.__sessionPath = None
        self.__option = str(self.__reqObj.getValue('option'))
        #
        self.__getSession()
        #
        self.__instId = str(self.__reqObj.getValue('instanceid'))
        self.__instancePath = os.path.join(self.__sessionPath, self.__instId)
        #
        self.__allInstMappingFiles = []
        self.__successful_message = ''
        self.__message = ''
        #
        self.__cmdUtil = CommandUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

    def process(self):
        """ Update model coordinate file
        """
        alloption = str(self.__reqObj.getValue('alloption'))
        self.__downloadCompCif()
        self.__runMappingScript()
        if alloption == 'true':
            self.__searchOtherInstances()
        #
        self.__runUpdateScript()
        if not self.__message:
            if self.__successful_message:
                self.__message = self.__successful_message
            elif self.__option == 'merge':
                self.__message = 'merged'
            else:
                self.__message = 'split'
            #
        #
        return self.__message

    def __downloadCompCif(self):
        """ Download chopper output file
        """
        cif = str(self.__reqObj.getValue('cif'))
        filePath = os.path.join(self.__instancePath, 'chopper_output.cif')
        f = open(filePath, 'w')
        f.write(cif + '\n')
        f.close()
        #

    def __runMappingScript(self):
        """ Generate mapping file
        """
        option = self.__option
        if option == 'split_residue':
            option = 'split'
        #
        extraOptions = ' -orig_cif ' + self.__instId + '.orig.cif  -merge_cif ' + self.__instId + '.merge.cif -comp_cif ' + self.__instId \
            + '.comp.cif -chopper_cif ' + os.path.join(self.__instancePath, 'chopper_output.cif') + ' -option ' + option + ' '
        self.__cmdUtil.setSessionPath(self.__instancePath)
        self.__cmdUtil.runAnnotCmd('GenMappingFile', '', self.__instId + '.mapping.cif', 'generate-mapping.log', 'generate-mapping.clog', extraOptions)
        #
        logfile = os.path.join(self.__instancePath, 'generate-mapping.log')
        if not os.access(logfile, os.F_OK):
            self.__message += 'Generating atom mapping failed. No log file found.\n'
            return
        #
        self.__getLogMessage(logfile)

    def __searchOtherInstances(self):
        """ Get other instances list
        """
        residue_id = ''
        if self.__option == 'split_residue':
            pickleFilePath = os.path.join(self.__instancePath, self.__instId + ".pkl")
            if os.access(pickleFilePath, os.F_OK):
                fb = open(pickleFilePath, "rb")
                pickleD = pickle.load(fb)
                fb.close()
                #
                if ('residue' in pickleD) and pickleD['residue']:
                    residue_id = pickleD['residue']
                #
            #
        #
        self.__lfh.write("residue_id=%s\n" % residue_id)
        searchPath = os.path.join(self.__sessionPath, 'search')
        extraOptions = ' -summaryfile ' + self.__summaryFile + ' -searchpath ' + searchPath + ' -merge_cif ' + self.__instId \
            + '.merge.cif -chopper_cif ' + os.path.join(self.__instancePath, 'chopper_output.cif') + ' '
        #
        if residue_id != '':
            identifier = str(self.__reqObj.getValue("identifier"))
            ciffile = os.path.join(self.__sessionPath, identifier + '_model_P1.cif')
            extraOptions += ' -residue_id ' + residue_id + ' -model_cif ' + ciffile
        #
        self.__cmdUtil.setSessionPath(self.__instancePath)
        self.__cmdUtil.runAnnotCmd('SearchAllInstances', '', self.__instId + '.all_instance_search.list',
                                   'search-instances.log', 'search-instances.clog', extraOptions)
        #
        filename = os.path.join(self.__instancePath, self.__instId + '.all_instance_search.list')
        if not os.access(filename, os.F_OK):
            return
        #
        f = open(filename, 'r')
        data = f.read()
        f.close()
        dlist = data.split('\n')
        for line in dlist:
            if not line:
                continue
            #
            list1 = line.split(' ')
            if list1[1] == 'successful':
                if self.__option == 'merge':
                    self.__successful_message += list1[0] + ' merged\n'
                else:
                    self.__successful_message += list1[0] + ' split\n'
                #
                if list1[2] == 'self':
                    continue
                #
                self.__allInstMappingFiles.append(list1[2])
            elif list1[1] == 'failed:':
                self.__successful_message += line + '\n'
            #
        #

    def __runUpdateScript(self):
        if self.__message:
            return
        #
        allinst_option = ''
        if self.__option == 'split_residue':
            allinst_option = ' -split_polymer_residue '
        #
        if self.__allInstMappingFiles:
            for file_name in self.__allInstMappingFiles:
                allinst_option += ' -mapping ' + self.__instId + '/' + file_name
            #
        #
        identifier = str(self.__reqObj.getValue("identifier"))
        ciffile = identifier + '_model_P1.cif'
        updateid = 'update-entry-' + self.__instId
        mappingfile = self.__instId + '/' + self.__instId + '.mapping.cif'
        #
        self.__cmdUtil.setSessionPath(self.__sessionPath)
        self.__cmdUtil.runAnnotCmd('UpdateEntry', ciffile, ciffile, updateid + '.log', updateid + '.clog', ' -mapping ' + mappingfile + allinst_option + ' ')
        #
        logfile = os.path.join(self.__sessionPath, updateid + '.log')
        if not os.access(logfile, os.F_OK):
            self.__message += 'Updating coordinate cif file failed. No log file found.\n'
            return
        #
        self.__getLogMessage(logfile)

    def __getLogMessage(self, logfile):
        error = GetLogMessage(logfile)
        if error:
            self.__message += error + '\n'
        #

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        if self.__verbose:
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+ChopperHandler.__getSession() - creating/joining session %s\n" % self.__sObj.getId())
            self.__lfh.write("+ChopperHandler.__getSession() - session path %s\n" % self.__sessionPath)
        #
