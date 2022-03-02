##
# File:  ProcessSummary_main.py
# Date:  27-Mar-2019
# Updates:
##
"""
Process PRD search results and generate images.

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

import getopt
import sys
import traceback

from wwpdb.apps.entity_transform.depict.ProcessPrdSummary import ProcessPrdSummary
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.session.WebRequest import InputRequest

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "i:p:", ["input=", "path="])

    resultFilePath = None
    dirPath = None
    for opt, arg in opts:
        if opt in ("-i", "--input"):
            resultFilePath = arg
        elif opt in ("-p", "--path"):
            dirPath = arg
        #
    #

    if resultFilePath and dirPath:
        try:
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
            myReqObj.setValue("TopSessionPath", cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH"))
            myReqObj.setValue("TopPath", cI.get("SITE_WEB_APPS_TOP_PATH"))
            myReqObj.setValue("WWPDB_SITE_ID", siteId)
            prdUtil = ProcessPrdSummary(reqObj=myReqObj, verbose=True, log=sys.stderr)
            prdUtil.setTopDirPath(dirPath)
            prdUtil.setPrdSummaryFile(resultFilePath)
            prdUtil.run()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=sys.stderr)
        #
    #
