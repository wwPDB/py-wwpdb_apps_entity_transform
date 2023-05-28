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
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc

from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage


#

class CVSCommit(object):
    """ Class responsible for CVS commit PRD definition.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj = None
        self.__sessionId = None
        self.__sessionPath = None
        # self.__rltvSessionPath = None
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cI = ConfigInfo(self.__siteId)
        self.__cIACc = ConfigInfoAppCc(self.__siteId, verbose=verbose, log=log)
        self.__prdRoot = self.__cIACc.get_site_prd_cvs_path()
        self.__prdccRoot = self.__cIACc.get_site_prdcc_cvs_path()
        #
        self.__PrdIDList = None
        self.__returnError = ""

        self.__getSession()
        #

    def checkin(self):
        """ Check in new PRD/PRDCC to CVS archive
        """
        #
        self.__PrdIDList = self.__reqObj.getValueList("prd_id")
        if not self.__PrdIDList:
            return "No PRD entry selected"
        #
        scriptfile = self.__getFileName(self.__sessionPath, "cvs_commit", "csh")
        logfile = self.__getFileName(self.__sessionPath, "cvs_commit", "log")
        script = os.path.join(self.__sessionPath, scriptfile)
        cvs_username = self.__cI.get("SITE_REFDATA_CVS_USER")
        cvs_password = self.__cI.get("SITE_REFDATA_CVS_PASSWORD")
        cvs_host = self.__cI.get("SITE_REFDATA_CVS_HOST")
        cvs_path = self.__cI.get("SITE_REFDATA_CVS_PATH")
        f = open(script, "w")
        f.write("#!/bin/tcsh -f\n")
        f.write("#\n")
        f.write('setenv CVSROOT ":pserver:{}:{}@{}:{}"\n'.format(cvs_username, cvs_password, cvs_host, cvs_path))
        f.write("#\n")
        #
        self.__returnError = ""
        for prdid in self.__PrdIDList:
            prdfile = os.path.join(self.__sessionPath, prdid + ".cif")
            if not os.access(prdfile, os.F_OK):
                self.__returnError += "No " + prdid + ".cif found!\n"
                continue
            #
            self.__writeCVSScript(f, prdid, self.__prdRoot)
            #
            prdccid = prdid.replace("PRD", "PRDCC")
            prdccfile = os.path.join(self.__sessionPath, prdccid + ".cif")
            if os.access(prdccfile, os.F_OK):
                self.__writeCVSScript(f, prdccid, self.__prdccRoot)
            #
        #
        f.close()
        #
        if self.__returnError:
            return self.__returnError
        #
        self.__RunScript(self.__sessionPath, scriptfile, logfile)
        logPath = os.path.join(self.__sessionPath, logfile)
        return GetLogMessage(logPath)

    def __getFileName(self, path, root, ext):
        """Create unique file name.
        """
        count = 1
        while True:
            filename = root + "_" + str(count) + "." + ext
            fullname = os.path.join(path, filename)
            if not os.access(fullname, os.F_OK):
                return filename
            #
            count += 1
        #
        return root + "_1." + ext

    def __RunScript(self, path, script, log):
        """Run script command
        """
        cmd = "cd " + path + "; chmod 755 " + script \
              + "; ./" + script + " >& " + log
        os.system(cmd)

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        # self.__rltvSessionPath = self.__sObj.getRelativePath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+CVSCommit.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+CVSCommit.__getSession() - session path %s\n" % self.__sessionPath)

    def __writeCVSScript(self, f, Id, cvspath):
        """ Write CVS checkin script
        """
        sourceFile = os.path.join(self.__sessionPath, Id + ".cif")
        hashId = Id[len(Id) - 1]
        hashPath = os.path.join(cvspath, hashId)
        targetFile = os.path.join(hashPath, Id + ".cif")
        is_new = True
        comment = "initial version"
        if os.access(targetFile, os.F_OK):
            is_new = False
            comment = "updated " + Id
        #
        f.write("cd " + hashPath + "\n")
        f.write("cp " + sourceFile + " .\n")
        f.write("chmod 644 " + Id + ".cif\n")
        if is_new:
            f.write("cvs -d${CVSROOT} add " + Id + ".cif\n")
        f.write('cvs -d${CVSROOT} commit -m "' + comment + '" ' + Id + ".cif\n")
        f.write("#\n")
