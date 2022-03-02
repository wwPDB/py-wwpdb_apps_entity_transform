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
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon


class CompUtil(object):
    """ Class responsible for checking Comp/PRD ID and finding chemical component file.
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        self.__reqObj = reqObj
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        #
        self.__ccPath = self.__cICommon.get_site_cc_cvs_path()
        self.__prdPath = self.__cICommon.get_site_prd_cvs_path()
        self.__prdccPath = self.__cICommon.get_site_prdcc_cvs_path()
        #

    def checkInputId(self, id):  # pylint: disable=redefined-builtin
        filePath = os.path.join(self.__ccPath, id[0], id, id + '.cif')
        if id[:4] == 'PRD_':
            filePath = os.path.join(self.__prdPath, id[len(id) - 1], id + '.cif')
        #
        if not os.access(filePath, os.F_OK):
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
            filePath1 = os.path.join(self.__prdccPath, ccid[len(ccid) - 1], ccid + '.cif')
            if os.access(filePath1, os.F_OK):
                return filePath1
            #
            # check single ligand defined in PRD entry
            #
            fileName = os.path.join(self.__prdPath, id[len(id) - 1], id + '.cif')
            cf = mmCIFUtil(filePath=fileName)
            dlist = cf.GetValue('pdbx_reference_molecule')
            if not dlist:
                return ''
            #
            if 'chem_comp_id' not in dlist[0]:
                return ''
            #
            ccid = dlist[0]['chem_comp_id'].strip().upper()
            filePath1 = os.path.join(self.__ccPath, ccid[0], ccid, ccid + '.cif')
            if os.access(filePath1, os.F_OK):
                return filePath1
            #
        else:
            filePath = os.path.join(self.__ccPath, id[0], id, id + '.cif')
            if os.access(filePath, os.F_OK):
                return filePath
            #
        #
        return ''
