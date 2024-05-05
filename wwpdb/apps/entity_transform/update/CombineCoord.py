##
# File:  CombineCoord.py
# Date:  06-Dec-2012
# Updates:
##
"""
Combine selected instances into single residue.

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
import shutil
import sys

from wwpdb.apps.entity_transform.utils.CommandUtil import CommandUtil
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage
#


class CombineCoord(object):
    """ Class responsible for combining selected instances into single residue.
    """
    def __init__(self, reqObj=None, instList=None, cifFile=None, verbose=False, log=sys.stderr):
        if instList is None:
            instList = []
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__instList = instList
        self.__cifFile = cifFile
        self.__sObj = None
        self.__sessionPath = None
        self.__instId = ''
        self.__message = ''
        self.__submitValue = ''
        #
        self.__getSession()
        self.__getInstId()
        #
        self.__instancePath = os.path.join(self.__sessionPath, self.__instId)
        #
        self.__cmdUtil = CommandUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

    def processWithCombine(self):
        #
        self.__runCombineScript()
        #
        if self.__message:
            return
        #
        self.__runUpdateScript()

    def processWithCopy(self, submitValue=''):
        #
        self.__submitValue = submitValue
        #
        if self.__submitValue and (len(self.__instList) == 1) and self.__instList[0]:
            pickleFilePath = os.path.join(self.__instancePath, self.__instId + ".pkl")
            if os.access(pickleFilePath, os.F_OK):
                os.remove(pickleFilePath)
            #
            pickleD = {}
            pickleD['residue'] = self.__instList[0]
            pickleD['submit'] = self.__submitValue
            #
            fb = open(pickleFilePath, "wb")
            pickle.dump(pickleD, fb)
            fb.close()
        #
        if not self.__runCopyScript():
            self.__runCombineScript()
        #
        if self.__message:
            return
        #
        self.__runUpdateScript()

    def getInstId(self):
        return self.__instId

    def getMessage(self):
        return self.__message

    def __getInstId(self):
        count = 1
        while True:
            self.__instId = 'chopper_inst_' + str(count)
            pth = os.path.join(self.__sessionPath, self.__instId)
            if not os.access(pth, os.F_OK):
                os.makedirs(pth)
                break
            #
            count += 1
        #

    def __runCombineScript(self):
        if not self.__instList or not self.__instList[0]:
            self.__message = 'No instance found.'
            return
        #
        ciffile = os.path.join(self.__sessionPath, self.__cifFile)
        #
        options = ' -output_orig ' + self.__instId + '.orig.cif -output_merge ' + self.__instId + '.merge.cif -output_comp ' \
            + self.__instId + '.comp.cif -group ' + ','.join(self.__instList) + ' '
        #
        self.__cmdUtil.setSessionPath(self.__instancePath)
        self.__cmdUtil.runAnnotCmd('GetCombineCoord', ciffile, '', 'run-comb.log', 'run-comb.clog', options)
        #
        logfile = os.path.join(self.__instancePath, 'run-comb.log')
        if not os.access(logfile, os.F_OK):
            self.__message = 'Option "Merge to polymer" failed. No log file found.'
            return
        #
        error = GetLogMessage(logfile)
        if error:
            self.__message = '<pre>\n' + error + '</pre>\n'
        #

    def __runCopyScript(self):
        if not self.__instList or not self.__instList[0]:
            return False
        #
        for ext in ('.orig.cif', '.merge.cif', '.comp.cif'):
            source = os.path.join(self.__sessionPath, 'search', self.__instList[0], self.__instList[0] + ext)
            if not os.access(source, os.F_OK):
                return False
            #
            shutil.copyfile(source, os.path.join(self.__instancePath, self.__instId + ext))
        #
        return True

    def __runUpdateScript(self):
        """
        """
        target = os.path.join(self.__instancePath, self.__instId + '.comp.cif')
        if not os.access(target, os.F_OK):
            return
        #
        self.__cmdUtil.setSessionPath(self.__instancePath)
        self.__cmdUtil.runCCToolCmd('updateComponent', '', '', '', 'update-comp.clog', ' -f ' + self.__instId + '.comp.cif ')
        self.__cmdUtil.runAnnotateComp(self.__instId + '.comp.cif', self.__instId + '.comp.cif.new', 'update-comp.clog')
        #
        source = os.path.join(self.__instancePath, self.__instId + '.comp.cif.new')
        if os.access(source, os.F_OK):
            os.rename(source, target)
        #

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+CombineCoord.__getSession() - creating/joining session %s\n" % self.__sObj.getId())
            self.__lfh.write("+CombineCoord.__getSession() - session path %s\n" % self.__sessionPath)
        #
