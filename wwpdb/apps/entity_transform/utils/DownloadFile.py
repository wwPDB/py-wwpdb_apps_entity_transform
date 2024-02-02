##
# File:  DownloadFile.py
# Date:  16-Oct-2012
# Updates:
##
"""
Download files.

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
import traceback

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class DownloadFile(object):
    """ Class responsible for download files.
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
        #
        self.__getSession()
        #
        self.__fileId = str(self.__reqObj.getValue("identifier")) + "_model_P1.cif"
        self.__PrdIds = []

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
            self.__lfh.write("+DownloadFile.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+DownloadFile.__getSession() - session path %s\n" % self.__sessionPath)
        #

    def __processTemplate(self, fn, parameterDict=None):
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
        tPath = self.__reqObj.getValue("TemplatePath")
        fPath = os.path.join(tPath, fn)
        ifh = open(fPath, "r")
        sIn = ifh.read()
        ifh.close()
        return (sIn % parameterDict)

    def __findPRDFiles(self):
        fileList = []
        #
        for files in os.listdir(self.__sessionPath):
            if files.endswith(".cif") and (files.startswith("PRD_") or files.startswith("PRDCC_")):
                list1 = files.split(".")
                if len(list1) > 2:
                    continue
                fileList.append(files)
                if list1[0].startswith("PRD_"):
                    self.__PrdIds.append(list1[0])
            #
        #
        return fileList

    def __updatePrdCcChemName(self):
        setting = " RCSBROOT=" + self.__cI.get("SITE_ANNOT_TOOLS_PATH") + "; export RCSBROOT; "
        #
        dictCheckMsg = ""
        for prdid in self.__PrdIds:
            prdfile = os.path.join(self.__sessionPath, prdid + ".cif")
            if not os.access(prdfile, os.F_OK):
                continue
            #
            prdccid = prdid.replace("PRD", "PRDCC")
            prdccfile = os.path.join(self.__sessionPath, prdccid + ".cif")
            if not os.access(prdccfile, os.F_OK):
                cmd = setting + "${RCSBROOT}/bin/UpdatePrdCcName -prd " + prdfile + " -log " \
                    + os.path.join(self.__sessionPath, prdid + "-name-update.log") + "  > " \
                    + os.path.join(self.__sessionPath, prdid + "-name-update.clog") + " 2>&1; "
            else:
                cmd = setting + "${RCSBROOT}/bin/UpdatePrdCcName -prd " + prdfile + " -prdcc " + prdccfile + " -log " \
                    + os.path.join(self.__sessionPath, prdid + "-name-update.log") + "  > " \
                    + os.path.join(self.__sessionPath, prdid + "-name-update.clog") + " 2>&1; "
            #
            os.system(cmd)
            #
            logfile = os.path.join(self.__sessionPath, "checking-" + prdid + ".log")
            if os.access(logfile, os.F_OK):
                os.remove(logfile)
            #
            try:
                dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
                dp.imp(prdfile)
                dp.op("check-cif")
                dp.exp(logfile)
                if os.access(logfile, os.F_OK):
                    ifh = open(logfile, "r")
                    sIn = ifh.read()
                    ifh.close()
                    if not sIn:
                        dictCheckMsg += "\n" + prdid + ": OK\n"
                    else:
                        dictCheckMsg += "\n" + prdid + ":\n" + sIn + "\n"
                    #
                #
                dp.cleanup()
            except:  # noqa: E722 pylint: disable=bare-except
                traceback.print_exc(file=self.__lfh)
            #
        #
        if not dictCheckMsg:
            return dictCheckMsg
        else:
            return "<pre>\nCIF Dictionary Check:\n" + dictCheckMsg + "</pre>\n"
        #

    def ListFiles(self):
        myD = {}
        myD["sessionid"] = self.__sessionId
        myD["instanceid"] = ""
        myD["fileid"] = self.__fileId
        content = self.__processTemplate("download/one_file_tmplt.html", myD) + "\n"
        #
        filelist = self.__findPRDFiles()
        if filelist:
            for f in filelist:
                myD["instanceid"] = ""
                myD["fileid"] = f
                content += self.__processTemplate("download/one_file_tmplt.html", myD) + "\n"
            #
        #
        return content

    def ListPrds(self):
        if not self.__PrdIds:
            return ""
        #
        dictCheckMsg = self.__updatePrdCcChemName()
        #
        content = ""
        for prd_id in self.__PrdIds:
            myd = {}
            myd["prd_id"] = prd_id
            content += self.__processTemplate("download/one_prd_tmplt.html", myd) + "\n"
        #
        myD = {}
        myD["sessionid"] = self.__sessionId
        myD["form_data"] = content
        return dictCheckMsg + self.__processTemplate("download/prd_cvs_tmplt.html", myD)
