##
# File: ImportTests.py
# Date:  06-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for entity transformer"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import os
import unittest
import logging

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from commonsetup import HERE  # noqa:  F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import HERE  # noqa: F401 pylint: disable=relative-beyond-top-level

# from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.apps.entity_transform.webapp.EntityWebApp import EntityWebApp
# from wwpdb.utils.session.WebRequest import InputRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class ImportTests(unittest.TestCase):
    def setUp(self):
        # self.__siteId = getSiteId(defaultSiteId="WWPDB_DEV_TEST")
        # logger.info("\nTesting with site environment for:  %s", self.__siteId)
        # cI = ConfigInfo(self.__siteId)
        # self.__topSessionPath = cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH")
        # self.__reqObj = InputRequest(paramDict={})
        # self.__reqObj.setValue("TopSessionPath", self.__topSessionPath)
        # self.__reqObj.setDefaultReturnFormat(return_format="text")
        pass

    def testInstantiate(self):
        """Tests simple instantiation"""
        _ewa = EntityWebApp()  # noqa: F841


if __name__ == "__main__":
    unittest.main()
