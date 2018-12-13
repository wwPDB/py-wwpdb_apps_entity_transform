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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os, shutil, string, sys, traceback

from wwpdb.utils.config.ConfigInfo                   import ConfigInfo
from wwpdb.apps.entity_transform.utils.CommandUtil   import CommandUtil
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage
from wwpdb.io.file.mmCIFUtil                         import mmCIFUtil
#

class BuildPrd(object):
    """ Class responsible for building PRD definition based on instance.

    """
    def __init__(self, reqObj=None, summaryFile=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__summaryFile=summaryFile
        self.__sObj=None
        self.__sessionPath=None
        self.__instanceId = str(self.__reqObj.getValue("instanceid"));
        self.__siteId  = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cI=ConfigInfo(self.__siteId)
        #
        self.__getSession()
        self.__instancePath = os.path.join(self.__sessionPath, 'search', self.__instanceId)
        #
        self.__prdID = 'PRD_XXXXXX'
        self.__prdccID = 'PRDCC_XXXXXX'
        self.__prdccFlag = True
        self.__message = ''
        #
        self.__cmdUtil = CommandUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        self.__cmdUtil.setSessionPath(self.__instancePath)

    def build(self):
        """ Build PRD and PRDCC files
        """
        # Build with default fake IDs
        self.__build_prd()
        if self.__message:
            return self.__message
        #
        self.__getNewPrdID()
        #
        # Build with real IDs
        self.__build_prd()
        #
        self.__copyFile(os.path.join(self.__instancePath, self.__prdID + '.cif'), os.path.join(self.__sessionPath, self.__prdID + '.cif'))
        if os.access(os.path.join(self.__instancePath, self.__prdccID + '.cif'), os.F_OK):
            self.__copyFile(os.path.join(self.__instancePath, self.__prdccID + '.cif'), os.path.join(self.__sessionPath, self.__prdccID + '.cif'))
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
        self.__sObj=self.__reqObj.newSessionObj()
        self.__sessionPath=self.__sObj.getPath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")                    
            self.__lfh.write("+BuildPrd.__getSession() - session path %s\n" % self.__sessionPath)            

    def __build_prd(self):
        """ Run PRD & PRDCC build procedure
        """
        for existFile in ( self.__prdID + '.cif', self.__prdID + '.support.cif', self.__prdID + '.comp.cif', self.__prdccID + '.cif'):
            filePath = os.path.join(self.__instancePath, existFile)
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        self.__build_PRD()
        if self.__message:
            return
        #
        self.__prdccFlag = self.__checkPRDCCFlag()
        if not self.__prdccFlag:
            return
        #
        self.__build_PRDCC()
        if self.__message:
            return
        #
        self.__annotate_PRDCC()
        self.__update_PRD_PRDCC()

    def __getNewPrdID(self):
        """ Get new PRDID from unusedPrdId.lst file
        """
        filePath = os.path.join(self.__cI.get('SITE_DEPLOY_PATH'), 'reference', 'id_codes', 'unusedPrdId.lst')
        f = file(filePath, 'r')
        data = f.read()
        f.close()
        #
        idlist = data.split('\n')
        idx = 0
        for id in idlist:
            idx += 1
            prdfile = os.path.join(self.__cI.get('SITE_PRD_CVS_PATH'), id[len(id)-1], id+'.cif')
            if not os.access(prdfile, os.F_OK):
                self.__prdID = id
                self.__prdccID = self.__prdID.replace('PRD', 'PRDCC')
                break
            #
        #
        data = '\n'.join(idlist[idx:])
        f = file(filePath, 'w')
        f.write(data)
        f.close()

    def __build_PRD(self):
        """ Build PRD file
        """
        origFile = os.path.join(self.__instancePath, self.__instanceId + '.orig.cif')
        if not os.access(origFile, os.F_OK):
            return
        #
        rootName = self.__cmdUtil.getRootFileName('build-prd')
        extraOptions = ' -summary ' + self.__summaryFile + ' -instfile ' + self.__instanceId + '.orig.cif -instid ' + self.__instanceId \
                     + ' -prdfile ' + self.__prdID + '.cif -prdid ' + self.__prdID + ' -support ' + self.__prdID + '.support.cif '
        #
        self.__cmdUtil.runAnnotCmd('GenPrdEntry', '', '', rootName + '.log', rootName + '.clog', extraOptions)
        #
        self.__parseLogFile(rootName + '.log')
        self.__parseLogFile(rootName + '.clog')

    def __checkPRDCCFlag(self):
        """ Check if PRDCC is needed
        """
        prdFile = os.path.join(self.__instancePath, self.__prdID + '.cif')
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
        prdFile = os.path.join(self.__instancePath, self.__prdID + '.cif')
        supportFile = os.path.join(self.__instancePath, self.__prdID + '.support.cif')
        if (not os.access(prdFile, os.F_OK)) or (not os.access(supportFile, os.F_OK)):
            return
        #
        rootName = self.__cmdUtil.getRootFileName('build-prdcc')
        extraOptions = ' -instfile ' + self.__instanceId + '.orig.cif -prdfile ' + self.__prdID + '.cif -prdid ' + self.__prdID \
                     + ' -compfile ' + self.__prdID + '.comp.cif -support ' + self.__prdID + '.support.cif '
        #
        self.__cmdUtil.runAnnotCmd('GenPrdCCEntry', '', '', rootName + '.log', rootName + '.clog', extraOptions)
        #
        self.__parseLogFile(rootName + '.log')
        self.__parseLogFile(rootName + '.clog')

    def __annotate_PRDCC(self):
        """ Annotate PRDCC file
        """
        prdccFile = os.path.join(self.__instancePath, self.__prdID + '.comp.cif')
        if not os.access(prdccFile, os.F_OK):
            return
        #
        rootName = self.__cmdUtil.getRootFileName('annotate-prdcc')
        self.__cmdUtil.runAnnotateComp(self.__prdID + '.comp.cif', self.__prdccID + '.cif', rootName + '.clog')
        self.__cmdUtil.removeSelectedFiles('__' + self.__prdID + '__')

    def __update_PRD_PRDCC(self):
        """ Update PRD & PRDCC files
        """
        prdccFile = os.path.join(self.__instancePath, self.__prdccID + '.cif')
        if not os.access(prdccFile, os.F_OK):
            return
        #
        rootName = self.__cmdUtil.getRootFileName('update')
        extraOptions = ' -prd ' + self.__prdID + '.cif -comp ' + self.__prdID + '.comp.cif -annotatecomp ' +  self.__prdccID + '.cif '
        self.__cmdUtil.runAnnotCmd('MergeCompWithPrd', '', '', rootName + '.log', rootName + '.clog', extraOptions)
        #
        self.__parseLogFile(rootName + '.log')
        self.__parseLogFile(rootName + '.clog')

    def __copyFile(self, src, dst):
        """ Copy file
        """
        if os.access(src, os.F_OK):
            shutil.copyfile(src, dst)
        #

    def __parseLogFile(self, fileName):
        """ Read error message from log file
        """
        error = GetLogMessage(os.path.join(self.__instancePath, fileName))
        if not error:
            return
        #
        if self.__message:
            self.__message += '\n'
        #
        self.__message += error
