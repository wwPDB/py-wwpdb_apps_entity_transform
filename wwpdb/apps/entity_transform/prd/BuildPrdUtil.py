##
# File:  BuildPrdUtil.py
# Date:  31-Jul-2020
# Updates:
##
"""
Build PRD definition.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2020 wwPDB

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

from wwpdb.apps.entity_transform.utils.CommandUtil import CommandUtil
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
#


class BuildPrdUtil(object):
    """ Class responsible for building PRD definition based on instance.

    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__instanceId = str(self.__reqObj.getValue("instanceid"))
        self.__instancePath = str(self.__reqObj.getValue("instancepath"))
        self.__prdID = str(self.__reqObj.getValue("prdid"))
        self.__prdccID = str(self.__reqObj.getValue("prdccid"))
        self.__summaryFile = str(self.__reqObj.getValue("summaryfile"))
        #
        self.__prdccFlag = True
        self.__message = ""
        #
        self.__cmdUtil = None

    def setInstancePath(self, path):
        """ Set working instance path
        """
        self.__instancePath = path

    def setPrdId(self, prdID):
        """ Set PRD ID
        """
        self.__prdID = prdID

    def setPrdCcId(self, prdccID):
        """ Set PRDCC ID
        """
        self.__prdccID = prdccID

    def setSummaryFile(self, summaryFile):
        """ Set search summary file name
        """
        self.__summaryFile = summaryFile

    def build(self):
        """ Build PRD and PRDCC files
        """
        self.__cmdUtil = CommandUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        self.__cmdUtil.setSessionPath(self.__instancePath)
        #
        for existFile in (self.__prdID + ".cif", self.__prdID + ".support.cif", self.__prdID + ".comp.cif", self.__prdccID + ".cif"):
            filePath = os.path.join(self.__instancePath, existFile)
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        self.__build_PRD()
        if self.__message:
            return self.__message
        #
        self.__prdccFlag = self.__checkPRDCCFlag()
        if not self.__prdccFlag:
            return self.__message
        #
        self.__build_PRDCC()
        if self.__message:
            return self.__message
        #
        self.__annotate_PRDCC()
        self.__update_PRD_PRDCC()
        #
        return self.__message

    def __build_PRD(self):
        """ Build PRD file
        """
        origFile = os.path.join(self.__instancePath, self.__instanceId + ".orig.cif")
        if not os.access(origFile, os.F_OK):
            self.__attachErrorMessage("Missing " + origFile + " file.")
            return
        #
        rootName = self.__cmdUtil.getRootFileName("build-prd")
        extraOptions = " -summary " + self.__summaryFile + " -instfile " + self.__instanceId + ".orig.cif -instid " + self.__instanceId \
            + " -prdfile " + self.__prdID + ".cif -prdid " + self.__prdID + " -support " + self.__prdID + ".support.cif "
        #
        self.__cmdUtil.runAnnotCmd("GenPrdEntry", "", "", rootName + ".log", rootName + ".clog", extraOptions)
        #
        self.__parseLogFile(rootName + ".log")
        self.__parseLogFile(rootName + ".clog")
        #
        prdFile = os.path.join(self.__instancePath, self.__prdID + ".cif")
        if not os.access(prdFile, os.F_OK):
            self.__attachErrorMessage("Missing " + prdFile + " file.")
        #

    def __checkPRDCCFlag(self):
        """ Check if PRDCC is needed
        """
        prdFile = os.path.join(self.__instancePath, self.__prdID + ".cif")
        if not os.access(prdFile, os.F_OK):
            return False
        #
        prdObj = mmCIFUtil(filePath=prdFile)
        representType = prdObj.GetSingleValue("pdbx_reference_molecule", "represent_as")
        chemCompId = prdObj.GetSingleValue("pdbx_reference_molecule", "chem_comp_id")
        if (str(representType).strip().lower() == "single molecule") and (str(chemCompId).strip() != "") and \
           (str(chemCompId).strip() != "?") and (str(chemCompId).strip() != "."):
            return False
        #
        return True

    def __build_PRDCC(self):
        """ Build PRDCC file
        """
        supportFile = os.path.join(self.__instancePath, self.__prdID + ".support.cif")
        if not os.access(supportFile, os.F_OK):
            self.__attachErrorMessage("Missing " + supportFile + " file.")
            return
        #
        prdFile = os.path.join(self.__instancePath, self.__prdID + ".cif")
        if not os.access(prdFile, os.F_OK):
            return
        #
        rootName = self.__cmdUtil.getRootFileName("build-prdcc")
        extraOptions = " -instfile " + self.__instanceId + ".orig.cif -prdfile " + self.__prdID + ".cif -prdid " + self.__prdID \
            + " -compfile " + self.__prdID + ".comp.cif -support " + self.__prdID + ".support.cif "
        #
        self.__cmdUtil.runAnnotCmd("GenPrdCCEntry", "", "", rootName + ".log", rootName + ".clog", extraOptions)
        #
        self.__parseLogFile(rootName + ".log")
        self.__parseLogFile(rootName + ".clog")
        #
        prdccFile = os.path.join(self.__instancePath, self.__prdID + ".comp.cif")
        if not os.access(prdccFile, os.F_OK):
            self.__attachErrorMessage("Missing " + prdccFile + " file.")
        #

    def __annotate_PRDCC(self):
        """ Annotate PRDCC file
        """
        prdccFile = os.path.join(self.__instancePath, self.__prdID + ".comp.cif")
        if not os.access(prdccFile, os.F_OK):
            return
        #
        rootName = self.__cmdUtil.getRootFileName("annotate-prdcc")
        self.__cmdUtil.runAnnotateComp(self.__prdID + ".comp.cif", self.__prdccID + ".cif", rootName + ".clog")
        self.__cmdUtil.removeSelectedFiles("__" + self.__prdID + "__")

    def __update_PRD_PRDCC(self):
        """ Update PRD & PRDCC files
        """
        prdccFile = os.path.join(self.__instancePath, self.__prdccID + ".cif")
        if not os.access(prdccFile, os.F_OK):
            return
        #
        rootName = self.__cmdUtil.getRootFileName("update")
        extraOptions = " -prd " + self.__prdID + ".cif -comp " + self.__prdID + ".comp.cif -annotatecomp " + self.__prdccID + ".cif "
        self.__cmdUtil.runAnnotCmd("MergeCompWithPrd", "", "", rootName + ".log", rootName + ".clog", extraOptions)
        #
        self.__parseLogFile(rootName + ".log")
        self.__parseLogFile(rootName + ".clog")
        #
        os.rename(prdccFile, os.path.join(self.__instancePath, self.__prdccID + ".cif.save"))
        os.rename(os.path.join(self.__instancePath, self.__prdID + ".comp.cif"), prdccFile)

    def __parseLogFile(self, fileName):
        """ Read error message from log file
        """
        error = GetLogMessage(os.path.join(self.__instancePath, fileName))
        if not error:
            return
        #
        self.__attachErrorMessage(error)

    def __attachErrorMessage(self, error):
        """ Attach error message to self.__message
        """
        if self.__message:
            self.__message += "\n"
        #
        self.__message += error
