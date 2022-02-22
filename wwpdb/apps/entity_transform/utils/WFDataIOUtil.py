##
# File:    WFDataIOUtil.py
# Date:    03-Apr-2013
#
# Update:
#
##

"""
Class to encapsulate data import/export for prd search result files from the workflow directory hierarchy.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"


import sys
import os
import os.path

from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.io.locator.PathInfo import PathInfo


class WFDataIOUtil(object):
    """ Controlling class for data import operations

        Supported file sources:
        + archive         -  WF archive storage
        + wf-instance     -  WF instance storage

    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__reqObj = reqObj
        self.__lfh = log
        #
        self.__statusOK = True
        self.__sessionObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sessionObj.getPath()
        self.__fileSource = str(self.__reqObj.getValue("filesource")).strip()
        self.__identifier = str(self.__reqObj.getValue("identifier")).strip()
        self.__instance = str(self.__reqObj.getValue("instance")).strip()
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")

    def ImportData(self):
        de = DataExchange(reqObj=self.__reqObj, depDataSetId=self.__identifier, wfInstanceId=self.__instance,
                          fileSource=self.__fileSource, verbose=self.__verbose, log=self.__lfh)
        de.copyToSession(contentType="model", formatType="pdbx", version="latest", partitionNumber=1)
        de.copyToSession(contentType="prd-search", formatType="pdbx", version="latest", partitionNumber=1)

        pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        wfdirPath = pI.getDirPath(dataSetId=self.__identifier, wfInstanceId=self.__instance,
                                  contentType="model", formatType="pdbx", fileSource=self.__fileSource,
                                  versionId="latest", partNumber=1)
        os.symlink(os.path.join(wfdirPath, 'search'), os.path.join(self.__sessionPath, 'search'))

        return self.__statusOK

    def ExportData(self):
        de = DataExchange(reqObj=self.__reqObj, depDataSetId=self.__identifier, wfInstanceId=self.__instance,
                          fileSource=self.__fileSource, verbose=self.__verbose, log=self.__lfh)
        entryFile = os.path.join(self.__sessionPath, self.__identifier + "_model_P1.cif")
        self.__statusOK = de.export(entryFile, contentType="model", formatType="pdbx", version="next")

        return self.__statusOK
