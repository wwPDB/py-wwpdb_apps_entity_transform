##
# File:  UpdatePrd.py
# Date:  29-Apr-2014
# Updates:
##
"""
Update PRD definition based on input form.

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

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc
from wwpdb.apps.entity_transform.prd.ReadFormUtil import ReadFormUtil
#


class UpdatePrd(object):
    """ Class responsible for updating PRD definition.

    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj = None
        self.__sessionId = None
        self.__sessionPath = None
        self.__updateStatus = True

        # self.__rltvSessionPath = None
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cIAppCc = ConfigInfoAppCc(self.__siteId)
        #
        self.__getSession()
        #
        self.__getInputData()

    def getPRDID(self):
        """ return PRD ID
        """
        return self.__inputData['prd_id']

    def Update(self):
        """
        """
        self.__updateStatus = True
        submit = self.__reqObj.getValue('submit')
        if submit == 'Get New PRD ID':
            self.__processNewPrdID()
        # elif submit == 'Get Existing PRD Info':
        # elif submit == 'Add Rows':
        # elif submit == 'Commit to CVS':
        # elif submit == 'Continue CVS Commit':
        else:
            self.__updateStatus = False
        #
        return self.__updateStatus

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
            self.__lfh.write("+UpdatePrd.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+UpdatePrd.__getSession() - session path %s\n" % self.__sessionPath)

    def __getInputData(self):
        """
        """
        self.__inputData = {}
        for key in ('prd_id', 'mol_name_flag', 'class_flag', 'type_flag', 'status_flag',
                    'comp_detail_flag', 'description_flag'):
            self.__inputData[key] = str(self.__reqObj.getValue(key))
        #
        if not self.__inputData['prd_id'] or self.__inputData['prd_id'] == '':
            self.__inputData['prd_id'] = 'PRD_XXXXXX'
        #
        self.__inputData['prd_id'] = self.__inputData['prd_id'].upper()

    def __getNewPrdID(self):
        """
        """
        filePath = self.__cIAppCc.get_unused_prd_file()
        with open(filePath, 'r') as f:
            data = f.read()
        #
        newId = ''
        idlist = data.split('\n')
        idx = 0
        for cid in idlist:
            idx += 1
            prdfile = os.path.join(self.__cIAppCc.get_site_prd_cvs_path(), cid[len(cid) - 1], cid + '.cif')
            if not os.access(prdfile, os.F_OK):
                newId = cid
                break
            #
        #
        data = '\n'.join(idlist[idx:])
        with open(filePath, 'w') as f:
            f.write(data)
        #
        return newId

    def __processNewPrdID(self):
        """
        """
        self.__inputData['prd_id'] = self.__getNewPrdID()
        self.__writePrdFile()

    def __writePrdFile(self):
        """
        """
        filePath = os.path.join(self.__sessionPath, self.__inputData['prd_id'] + '.cif')
        formUtil = ReadFormUtil(reqObj=self.__reqObj, prdID=self.__inputData['prd_id'], outputFile=filePath,
                                verbose=self.__verbose, log=self.__lfh)
        status = formUtil.processForm()
        if not status:
            self.__updateStatus = False
        #
