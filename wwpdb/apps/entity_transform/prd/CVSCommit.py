##
# File:  CVSCommit.py
# Date:  09-May-2014
# Updates:
##
"""
CVS commit utility.

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

from wwpdb.utils.config.ConfigInfo                     import ConfigInfo
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage
from wwpdb.apps.releasemodule.utils.Utility          import *
#

class CVSCommit(object):
    """ Class responsible for CVS commit PRD definition.

    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__sObj=None
        self.__sessionId=None
        self.__sessionPath=None
        self.__rltvSessionPath=None
        self.__siteId  = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cI=ConfigInfo(self.__siteId)
        self.__prdRoot = self.__cI.get('SITE_PRD_CVS_PATH')
        self.__prdccRoot = self.__cI.get('SITE_PRDCC_CVS_PATH')
        #
        self.__getSession()
        #

    def checkin(self):
        """ Check in new PRD/PRDCC to CVS archive
        """
        self.__PrdIDList = self.__reqObj.getValueList('prd_id')
        if not self.__PrdIDList:
            return 'No PRD entry selected'
        #
        scriptfile = getFileName(self.__sessionPath, 'cvs_commit', 'csh')
        logfile    = getFileName(self.__sessionPath, 'cvs_commit', 'log')
        script = os.path.join(self.__sessionPath, scriptfile)
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv CVSROOT ":pserver:liganon3:lig1234@rcsb-cvs-1.rutgers.edu:/cvs-ligands"\n')
        f.write('#\n')
        #
        self.__returnError = ''
        for prdid in self.__PrdIDList:
            prdfile =  os.path.join(self.__sessionPath, prdid + '.cif')
            if not os.access(prdfile, os.F_OK):
                self.__returnError += 'No ' + prdid + '.cif found!\n'
                continue
            #
            self.__writeCVSScript(f, prdid, self.__prdRoot)
            #
            prdccid = prdid.replace('PRD', 'PRDCC')
            prdccfile = os.path.join(self.__sessionPath, prdccid + '.cif')
            if os.access(prdccfile, os.F_OK):
                self.__writeCVSScript(f, prdccid, self.__prdccRoot)
            #
        #
        f.close()
        #
        if self.__returnError:
            return self.__returnError
        #
        RunScript(self.__sessionPath, scriptfile, logfile)
        logPath = os.path.join(self.__sessionPath, logfile)
        return GetLogMessage(logPath)

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj=self.__reqObj.newSessionObj()
        self.__sessionId=self.__sObj.getId()
        self.__sessionPath=self.__sObj.getPath()
        self.__rltvSessionPath=self.__sObj.getRelativePath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")                    
            self.__lfh.write("+CVSCommit.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+CVSCommit.__getSession() - session path %s\n" % self.__sessionPath)            

    def __writeCVSScript(self, f, id, cvspath):
        """ Write CVS checkin script
        """
        sourceFile = os.path.join(self.__sessionPath, id + '.cif')
        hash = id[len(id) - 1]
        hashPath = os.path.join(cvspath, hash)
        targetFile = os.path.join(hashPath, id + '.cif')
        is_new = True
        comment = 'initial version'
        if os.access(targetFile, os.F_OK):
            is_new = False
            comment = 'updated ' + id
        #
        f.write('cd ' + hashPath + '\n')
        f.write('cp ' + sourceFile + ' .\n')
        f.write('chmod 644 ' + id + '.cif\n')
        if is_new:
            f.write('cvs -d${CVSROOT} add ' + id + '.cif\n')
        f.write('cvs -d${CVSROOT} commit -m "' + comment + '" ' + id + '.cif\n')
        f.write('#\n')
