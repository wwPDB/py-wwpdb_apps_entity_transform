##
# File:  BuildPrd.py
# Date:  09-Oct-2012
# Updates:
##
"""
Build PRD definition.

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
import shutil
import sys

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon, ConfigInfoAppCc
from wwpdb.apps.entity_transform.prd.BuildPrdUtil import BuildPrdUtil
#


class BuildPrd(object):
    """ Class responsible for building PRD definition based on instance.

    """
    def __init__(self, reqObj=None, summaryFile=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__summaryFile = summaryFile
        self.__sObj = None
        self.__sessionPath = None
        self.__instanceId = str(self.__reqObj.getValue("instanceid"))
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__cIAppCc = ConfigInfoAppCc(self.__siteId)
        #
        self.__getSession()
        self.__instancePath = os.path.join(self.__sessionPath, "search", self.__instanceId)
        #
        self.__prdID = "PRD_XXXXXX"
        self.__prdccID = "PRDCC_XXXXXX"
        self.__message = ""
        #

    def build(self):
        """ Build PRD and PRDCC files
        """
        # Build with default fake IDs
        buildUtil = BuildPrdUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        buildUtil.setInstancePath(self.__instancePath)
        buildUtil.setPrdId(self.__prdID)
        buildUtil.setPrdCcId(self.__prdccID)
        buildUtil.setSummaryFile(self.__summaryFile)
        self.__message = buildUtil.build()
        if self.__message:
            return self.__message
        #
        builtPrdPath = os.path.join(self.__instancePath, self.__prdID + ".cif")
        if not os.access(builtPrdPath, os.F_OK):
            self.__attachErrorMessage("Build PRD failed.")
            return self.__message
        #
        builtPrdCcPath = os.path.join(self.__instancePath, self.__prdccID + ".cif")
        #
        # Replace with real IDs
        self.__getNewPrdID()
        self.__replacePrdIDs(builtPrdPath, builtPrdCcPath)
        #
        self.__copyFile(os.path.join(self.__instancePath, self.__prdID + ".cif"), os.path.join(self.__sessionPath, self.__prdID + ".cif"))
        if os.access(os.path.join(self.__instancePath, self.__prdccID + ".cif"), os.F_OK):
            self.__copyFile(os.path.join(self.__instancePath, self.__prdccID + ".cif"), os.path.join(self.__sessionPath, self.__prdccID + ".cif"))
        #
        return self.__message

    def getPRDID(self):
        """ return PRDID
        """
        return self.__prdID

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+BuildPrd.__getSession() - session path %s\n" % self.__sessionPath)

    def __getNewPrdID(self):
        """ Get new PRDID from unusedPrdId.lst file
        """
        filePath = self.__cIAppCc.get_unused_prd_file()
        f = open(filePath, "r")
        data = f.read()
        f.close()
        #
        idlist = data.split("\n")
        idx = 0
        for prdid in idlist:
            idx += 1
            prdfile = os.path.join(self.__cIAppCc.get_site_prd_cvs_path(), prdid[len(prdid) - 1], prdid + ".cif")
            if not os.access(prdfile, os.F_OK):
                self.__prdID = prdid
                self.__prdccID = self.__prdID.replace("PRD", "PRDCC")
                break
            #
        #
        data = "\n".join(idlist[idx:])
        f = open(filePath, "w")
        f.write(data)
        f.close()

    def __replacePrdIDs(self, builtPrdPath, builtPrdCcPath):
        """ Replace fake IDs with real IDs
        """
        if (self.__prdID == "PRD_XXXXXX") or (self.__prdccID == "PRDCC_XXXXXX"):
            return
        #
        realPrdPath = os.path.join(self.__instancePath, self.__prdID + ".cif")
        realPrdCcPath = os.path.join(self.__instancePath, self.__prdccID + ".cif")
        #
        for filePath in (realPrdPath, realPrdCcPath):
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        setting = " RCSBROOT=" + self.__cICommon.get_site_annot_tools_path() + "; export RCSBROOT; "
        #
        cmd = setting + "${RCSBROOT}/bin/UpdatePrdId -input " + builtPrdPath + " -prd_id " + self.__prdID + " -output " + realPrdPath + " -log " \
            + os.path.join(self.__instancePath, "update_prd.log") + " > " + os.path.join(self.__instancePath, "update_prd.clog") + " 2>&1; "
        os.system(cmd)
        if not os.access(realPrdPath, os.F_OK):
            self.__attachErrorMessage("Build " + realPrdPath + " failed.")
            return
        #
        if not os.access(builtPrdCcPath, os.F_OK):
            return
        #
        cmd = setting + "${RCSBROOT}/bin/UpdatePrdId -input " + builtPrdCcPath + " -prd_id " + self.__prdID + " -output " + realPrdCcPath + " -log " \
            + os.path.join(self.__instancePath, "update_prdcc.log") + " > " + os.path.join(self.__instancePath, "update_prdcc.clog") + " 2>&1; "
        os.system(cmd)
        #
        if not os.access(realPrdCcPath, os.F_OK):
            self.__attachErrorMessage("Build " + realPrdCcPath + " failed.")
        #

    def __copyFile(self, src, dst):
        """ Copy file
        """
        if os.access(src, os.F_OK):
            shutil.copyfile(src, dst)
        #

    def __attachErrorMessage(self, error):
        """ Attach error message to self.__message
        """
        if self.__message:
            self.__message += "\n"
        #
        self.__message += error
