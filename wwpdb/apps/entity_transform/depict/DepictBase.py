##
# File:  DepictBase.py
# Date:  22-Jan-2018
# Updates:
##
"""
Base depiction class

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2018 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys
import inspect


class DepictBase(object):
    """ Base depiction class
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        self._verbose = verbose
        self._lfh = log
        self._reqObj = reqObj
        self._cifObj = summaryCifObj
        self._sObj = None
        self._sessionId = None
        self._sessionPath = None
        self._rltvSessionPath = None
        self._identifier = str(self._reqObj.getValue('identifier'))
        #
        self._pdbId = str(self._reqObj.getValue('pdbid'))
        if (not self._pdbId) and self._cifObj:
            self._pdbId = self._cifObj.getPdbId()
        #
        if not self._pdbId:
            self._pdbId = 'unknown'
        #
        self.__getSession()
        #

    def GetPDBID(self):
        return self._pdbId

    def _processTemplate(self, fn, parameterDict=None):
        """ Read the input HTML template data file and perform the key/value substitutions in the
            input parameter dictionary.

            :Params:
                ``parameterDict``: dictionary where
                key = name of subsitution placeholder in the template and
                value = data to be used to substitute information for the placeholder

            :Returns:
                string representing entirety of content with subsitution placeholders now replaced with data
        """
        if parameterDict is None:
            parameterDict = {}
        tPath = self._reqObj.getValue("TemplatePath")
        fPath = os.path.join(tPath, fn)
        ifh = open(fPath, 'r')
        sIn = ifh.read()
        ifh.close()
        return (sIn % parameterDict)

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self._sObj = self._reqObj.newSessionObj()
        self._sessionId = self._sObj.getId()
        self._sessionPath = self._sObj.getPath()
        self._rltvSessionPath = self._sObj.getRelativePath()
        if (self._verbose):
            self._lfh.write("------------------------------------------------------\n")
            self._lfh.write("+%s.%s() - creating/joining session %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self._sessionId))
            self._lfh.write("+%s.%s() - session path %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self._sessionPath))
        #
