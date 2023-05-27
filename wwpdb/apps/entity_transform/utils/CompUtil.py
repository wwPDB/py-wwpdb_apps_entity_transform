##
# File:  CompUtil.py
# Date:  17-Oct-2012
# Updates:
##
"""
Checking Comp/PRD ID and finding chemical component file.

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

from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo


class CompUtil(object):
    """ Class responsible for checking Comp/PRD ID and finding chemical component file.
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        self.__verbose = verbose
        self.__lfh = log

        self.__reqObj = reqObj
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__crpi = ChemRefPathInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        #

    def checkInputId(self, id):  # pylint: disable=redefined-builtin
        filePath = self.__crpi.getFilePath(id, "CC")
        if id[:4] == 'PRD_':
            filePath = self.__crpi.getFilePath(id, "PRD")
        #
        if filePath is None or not os.access(filePath, os.F_OK):
            return id + ' is not a valid Component or PRD ID.\n'
        #
        if id[:4] == 'PRD_':
            cf = mmCIFUtil(filePath=filePath)
            status = cf.GetSingleValue('pdbx_reference_molecule', 'release_status')
            if status.strip().upper() == "WAIT":
                return id + ' has status "WAIT".\n'
            #
        #
        return ''

    def getTemplateFile(self, id):  # pylint: disable=redefined-builtin
        if id[:4] == 'PRD_':
            ccid = id.replace('PRD', 'PRDCC')
            filePath1 = self.__crpi.getFilePath(ccid, "PRDCC")
            if os.access(filePath1, os.F_OK):
                return filePath1
            #
            # check single ligand defined in PRD entry
            #
            fileName = self.__crpi.getFilePath(id, "PRD")
            cf = mmCIFUtil(filePath=fileName)
            dlist = cf.GetValue('pdbx_reference_molecule')
            if not dlist:
                return ''
            #
            if 'chem_comp_id' not in dlist[0]:
                return ''
            #
            ccid = dlist[0]['chem_comp_id'].strip().upper()
            filePath1 = self.__crpi.getFilePath(ccid, "CC")
            if filePath1 and os.access(filePath1, os.F_OK):
                return filePath1
            #
        else:
            filePath = self.__crpi.getFilePath(id, "CC")
            if filePath and os.access(filePath, os.F_OK):
                return filePath
            #
        #
        return ''
