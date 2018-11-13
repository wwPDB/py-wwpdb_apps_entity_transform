##
# File:  UpdateBase.py
# Date:  04-Dec-2012
# Updates:
##
"""
Merge polymer(s) in coordinate cif file.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2012 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os, sys, string, traceback

from wwpdb.apps.entity_transform.utils.CommandUtil    import CommandUtil
from wwpdb.apps.entity_transform.utils.GetLogMessage  import GetLogMessage

class UpdateBase(object):
    """ Class responsible for merging polymer(s) in coordinate cif file.

    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        self._verbose=verbose
        self._lfh=log
        self._reqObj=reqObj
        self._cifObj = summaryCifObj
        self._sObj=None
        self._sessionPath=None
        self._cmdUtil=None
        #
        self._identifier = str(self._reqObj.getValue("identifier"))
        self._modelCIFile = self._identifier + '_model_P1.cif'
        #
        self._message = ''
        #
        self.__getSession()

    def getMessage(self):
        """ Return result message
        """
        return self._message

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self._sObj=self._reqObj.newSessionObj()
        self._sessionPath=self._sObj.getPath()
        if (self._verbose):
            self._lfh.write("------------------------------------------------------\n")                    
            self._lfh.write("+%s.%s() - creating/joining session %s\n" % ( self.__class__.__name__, sys._getframe().f_code.co_name, self._sObj.getId() ))
            self._lfh.write("+%s.%s() - session path %s\n" % ( self.__class__.__name__, sys._getframe().f_code.co_name, self._sessionPath ))
        #

    def _runUpdateScript(self, progName, taskName, logRootName, options):
        """ Run update program
        """
        if not os.access(os.path.join(self._sessionPath, self._modelCIFile), os.F_OK):
            self._message = 'Model coordinate file ' + self._modelCIFile + ' does not exist.'
            return
        #
        if not self._cmdUtil:
            self._cmdUtil = CommandUtil(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        self._cmdUtil.setSessionPath(self._sessionPath)
        self._cmdUtil.runAnnotCmd(progName, self._modelCIFile, self._modelCIFile, logRootName + '.log', logRootName + '.clog', options)
        #
        logfile = os.path.join(self._sessionPath, logRootName + '.log')
        if not os.access(logfile, os.F_OK):
            self._message = 'Option "' + taskName + '" failed. No log file found.'
            return
        #
        error = GetLogMessage(logfile)
        if error:
            self._message = '<pre>\n' + error + '</pre>\n'
        elif self._cifObj:
            self._message = 'Entry ' + self._cifObj.getEntryIds() + ' updated.'
        else:
            self._message = 'Entry updated.'
        #
