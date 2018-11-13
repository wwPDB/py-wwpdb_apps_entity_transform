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

import platform
import os
import unittest

# #####################  setup DepUi test environment here from emdb translator############
# HERE = os.path.abspath(os.path.dirname(__file__))
# TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
# TESTOUTPUT = os.path.join(HERE, 'test-output', platform.python_version())
# if not os.path.exists(TESTOUTPUT):
#     os.makedirs(TESTOUTPUT)
# mockTopPath = os.path.join(TOPDIR, 'wwpdb', 'mock-data')
# rwMockTopPath = os.path.join(TESTOUTPUT)

# # Must create config file before importing ConfigInfo
# from wwpdb.utils.testing.SiteConfigSetup  import SiteConfigSetup
# from wwpdb.utils.testing.CreateRWTree import CreateRWTree
# # Copy site-config and selected items
# crw = CreateRWTree(mockTopPath, TESTOUTPUT)
# crw.createtree(['site-config', 'depuiresources', 'emdresources'])
# # Use populate r/w site-config using top mock site-config
# SiteConfigSetup().setupEnvironment(rwMockTopPath, rwMockTopPath)

# # Setup DepUI specific directories
# from wwpdb.utils.config.ConfigInfo import ConfigInfo
# import os
# import os.path
# cI = ConfigInfo()
# FILE_UPLOAD_TEMP_DIR = os.path.join(
#     cI.get("SITE_DEPOSIT_STORAGE_PATH"),
#     "deposit",
#     "temp_files")
# if not os.path.exists(FILE_UPLOAD_TEMP_DIR):
#     os.makedirs(FILE_UPLOAD_TEMP_DIR)

# # Django envivonment setup
# #os.environ['DJANGO_SETTINGS_MODULE'] = "wwpdb.apps.deposit.settings"
# os.environ['IN_ANNOTATION'] = "no"
# ##################################################

try:
    from wwpdb.apps.entity_transform.webapp.EntityWebApp import EntityWebApp
except ImportError:
    # Handle openeye dependency
    from wwpdb.utils.config.ConfigInfo                        import ConfigInfo
    from wwpdb.utils.wf.dbapi.WfTracking                      import WfTracking
    from wwpdb.apps.editormodule.depict.EditorDepict          import EditorDepict
    from wwpdb.apps.editormodule.io.PdbxDataIo                import PdbxDataIo
    from wwpdb.apps.entity_transform.depict.LinkDepict        import LinkDepict
    from wwpdb.apps.entity_transform.depict.PrdSummaryDepict  import PrdSummaryDepict
    from wwpdb.apps.entity_transform.depict.StrSummaryDepict  import StrSummaryDepict
    from wwpdb.apps.entity_transform.depict.StrFormDepict     import StrFormDepict
    from wwpdb.apps.entity_transform.depict.ResultDepict      import ResultDepict
#    from wwpdb.apps.entity_transform.openeye_util.OpenEyeUtil import OpenEyeUtil
    from wwpdb.apps.entity_transform.prd.BuildPrd             import BuildPrd
    # RELEASE MODULE XXX
    from wwpdb.apps.entity_transform.prd.CVSCommit            import CVSCommit
    from wwpdb.apps.entity_transform.prd.DepictPrd            import DepictPrd
    from wwpdb.apps.entity_transform.prd.UpdatePrd            import UpdatePrd
    from wwpdb.apps.entity_transform.update.ChopperHandler    import ChopperHandler
    from wwpdb.apps.entity_transform.update.MergePolymer      import MergePolymer
    from wwpdb.apps.entity_transform.update.SplitPolymer      import SplitPolymer
    from wwpdb.apps.entity_transform.update.UpdateFile        import UpdateFile
    from wwpdb.apps.entity_transform.utils.CommandUtil        import CommandUtil
    from wwpdb.apps.entity_transform.utils.DownloadFile       import DownloadFile
    from wwpdb.apps.entity_transform.utils.GetLogMessage      import GetLogMessage
    from wwpdb.apps.entity_transform.utils.SummaryCifUtil     import SummaryCifUtil
    from wwpdb.apps.entity_transform.utils.RemoveEmptyCategories import RemoveEmptyCategories
    from wwpdb.apps.entity_transform.utils.WFDataIOUtil       import WFDataIOUtil
    from wwpdb.apps.entity_transform.webapp.FormPreProcess    import FormPreProcess
    from wwpdb.utils.detach.DetachUtils                       import DetachUtils
    from wwpdb.io.file.mmCIFUtil                           import mmCIFUtil
    from wwpdb.utils.dp.RcsbDpUtility                       import RcsbDpUtility
    from wwpdb.utils.session.WebRequest                          import InputRequest,ResponseContent
    
class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        """Tests simple instantiation"""
        pass
