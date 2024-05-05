##
# File:  EntityWebApp.py
# Date:  02-Oct-2012
# Updates:
##
"""
Entity fixer web request and response processing modules.

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
import time
import traceback
import ntpath
import shutil

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.wf.dbapi.WfTracking import WfTracking
from wwpdb.apps.editormodule.depict.EditorDepict import EditorDepict
from wwpdb.apps.editormodule.io.PdbxDataIo import PdbxDataIo
from wwpdb.apps.editormodule.config.AccessTemplateFiles import get_template_file_path as get_editor_template_file_path
from wwpdb.apps.entity_transform.depict.LinkDepict import LinkDepict
from wwpdb.apps.entity_transform.depict.PrdSummaryDepict import PrdSummaryDepict
from wwpdb.apps.entity_transform.depict.StrSummaryDepict import StrSummaryDepict
from wwpdb.apps.entity_transform.depict.StrFormDepict import StrFormDepict
from wwpdb.apps.entity_transform.depict.ResultDepict import ResultDepict
from wwpdb.apps.entity_transform.openeye_util.OpenEyeUtil import OpenEyeUtil
from wwpdb.apps.entity_transform.prd.BuildPrd import BuildPrd
from wwpdb.apps.entity_transform.prd.CVSCommit import CVSCommit
from wwpdb.apps.entity_transform.prd.DepictPrd import DepictPrd
from wwpdb.apps.entity_transform.prd.UpdatePrd import UpdatePrd
from wwpdb.apps.entity_transform.update.ChopperHandler import ChopperHandler
from wwpdb.apps.entity_transform.update.MergePolymer import MergePolymer
from wwpdb.apps.entity_transform.update.MergeLigand import MergeLigand
from wwpdb.apps.entity_transform.update.SplitPolymer import SplitPolymer
from wwpdb.apps.entity_transform.update.EditPolymer import EditPolymer
from wwpdb.apps.entity_transform.update.UpdateFile import UpdateFile
from wwpdb.apps.entity_transform.utils.DownloadFile import DownloadFile
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage
from wwpdb.apps.entity_transform.utils.SummaryCifUtil import SummaryCifUtil
from wwpdb.apps.entity_transform.utils.RemoveEmptyCategories import RemoveEmptyCategories
from wwpdb.apps.entity_transform.utils.WFDataIOUtil import WFDataIOUtil
from wwpdb.apps.entity_transform.webapp.FormPreProcess import FormPreProcess
from wwpdb.utils.detach.DetachUtils import DetachUtils
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.session.WebRequest import InputRequest, ResponseContent
#


class EntityWebApp(object):
    """Handle request and response object processing for the entity fixer tool application.

    """
    def __init__(self, parameterDict=None, verbose=False, log=sys.stderr, siteId="WWPDB_DEV"):
        """
        Create an instance of `EntityWebApp` to manage a entity fixer web request.

         :param `parameterDict`: dictionary storing parameter information from the web request.
             Storage model for GET and POST parameter data is a dictionary of lists.
         :param `verbose`:  boolean flag to activate verbose logging.
         :param `log`:      stream for logging.

        """
        if parameterDict is None:
            parameterDict = {}
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        self.__siteId = siteId
        self.__cI = ConfigInfo(self.__siteId)
        self.__topPath = self.__cI.get('SITE_WEB_APPS_TOP_PATH')
        #

        if isinstance(parameterDict, dict):
            self.__myParameterDict = parameterDict
        else:
            self.__myParameterDict = {}

        if (self.__verbose):
            self.__lfh.write("+EntityWebApp.__init() - REQUEST STARTING ------------------------------------\n")
            self.__lfh.write("+EntityWebApp.__init() - dumping input parameter dictionary \n")
            self.__lfh.write("%s" % (''.join(self.__dumpRequest())))

        self.__reqObj = InputRequest(self.__myParameterDict, verbose=self.__verbose, log=self.__lfh)

        # self.__topSessionPath  = os.path.join(self.__topPath)
        self.__topSessionPath = self.__cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH')
        self.__templatePath = os.path.join(self.__topPath, "htdocs", "entity_transform_ui", "templates")
        #
        self.__reqObj.setValue("TopSessionPath", self.__topSessionPath)
        self.__reqObj.setValue("TemplatePath", self.__templatePath)
        self.__reqObj.setValue("TopPath", self.__topPath)
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)
        os.environ["WWPDB_SITE_ID"] = self.__siteId
        #
        self.__reqObj.setReturnFormat(return_format="html")
        #
        if (self.__verbose):
            self.__lfh.write("-----------------------------------------------------\n")
            self.__lfh.write("+EntityWebApp.__init() Leaving _init with request contents\n")
            self.__reqObj.printIt(ofh=self.__lfh)
            self.__lfh.write("---------------EntityWebApp - done -------------------------------\n")
            self.__lfh.flush()

    def doOp(self):
        """ Execute request and package results in response dictionary.

        :Returns:
             A dictionary containing response data for the input request.
             Minimally, the content of this dictionary will include the
             keys: CONTENT_TYPE and REQUEST_STRING.
        """
        stw = EntityWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC = stw.doOp()
        if (self.__debug):
            rqp = self.__reqObj.getRequestPath()
            self.__lfh.write("+EntityWebApp.doOp() operation %s\n" % rqp)
            self.__lfh.write("+EntityWebApp.doOp() return format %s\n" % self.__reqObj.getReturnFormat())
            if rC is not None:
                self.__lfh.write("%s" % (''.join(rC.dump())))
            else:
                self.__lfh.write("+EntityWebApp.doOp() return object is empty\n")

        #
        # Package return according to the request return_format -
        #
        return rC.get()

    def __dumpRequest(self):
        """Utility method to format the contents of the internal parameter dictionary
           containing data from the input web request.

           :Returns:
               ``list`` of formatted text lines
        """
        retL = []
        retL.append("\n-----------------EntityWebApp().__dumpRequest()-----------------------------\n")
        retL.append("Parameter dictionary length = %d\n" % len(self.__myParameterDict))
        for k, vL in self.__myParameterDict.items():
            retL.append("Parameter %30s :" % k)
            for v in vL:
                retL.append(" ->  %s\n" % v)
        retL.append("-------------------------------------------------------------\n")
        return retL


class EntityWebAppWorker(object):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
         Worker methods for the chemical component editor application

         Performs URL - application mapping and application launching
         for chemical component editor tool.

         All operations can be driven from this interface which can
         supplied with control information from web application request
         or from a testing application.
        """
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj = None
        self.__sessionId = None
        self.__sessionPath = None
        self.__rltvSessionPath = None
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cI = ConfigInfo(self.__siteId)
        self.__identifier = ''
        self.__modelfileId = ''
        self.__summaryfileId = ''
        self.__summaryfilePath = ''
        self.__summaryCifObj = None
        self.__pdbId = ''
        self.__title = ''
        #
        self.__message = ''
        #
        # fmt:off
        self.__appPathD = {'/service/environment/dump':                       '_dumpOp',                # noqa: E241
                           '/service/entity/assign':                          '_StandaloneOp',          # noqa: E241
                           '/service/entity/new_session/wf':                  '_WorkflowOp',            # noqa: E241
                           '/service/entity/refresh_struct_summary':          '_reRunPrdSearchOp',      # noqa: E241
                           '/service/entity/check_running_status':            '_checkRunningStatusOp',  # noqa: E241
                           '/service/entity/chopper_output':                  '_chopperHandler',        # noqa: E241
                           '/service/entity/build_prd':                       '_buildPRD',              # noqa: E241
                           '/service/entity/update_prd':                      '_updatePRD',             # noqa: E241
                           '/service/entity/download_file':                   '_downloadFile',          # noqa: E241
                           '/service/entity/commit_prd_to_cvs':               '_commitPRD',             # noqa: E241
                           '/service/entity/gif_view':                        '_gifView',               # noqa: E241
                           '/service/entity/jmol_view':                       '_jmolView',              # noqa: E241
                           '/service/entity/launch_fixer':                    '_LaunchFixer',           # noqa: E241
                           '/service/entity/launch_editor':                   '_LaunchEditor',          # noqa: E241
                           '/service/entity/link_view':                       '_LinkView',              # noqa: E241
                           '/service/entity/mcs_match_view':                  '_OpenEyeMatchView',      # noqa: E241
                           '/service/entity/merge_polymer':                   '_mergePolymer',          # noqa: E241
                           '/service/entity/merge_ligand':                    '_mergeLigand',           # noqa: E241
                           '/service/entity/result_view':                     '_resultView',            # noqa: E241
                           '/service/entity/split_polymer':                   '_splitPolymer',          # noqa: E241
                           '/service/entity/edit_polymer':                    '_editPolymer',           # noqa: E241
                           '/service/entity/summary_view':                    '_StructSummaryView',     # noqa: E241
                           '/service/entity/update_file':                     '_updateFile',            # noqa: E241
                           '/service/entity/exit_finished':                   '_exit_Finished'          # noqa: E241
                           }
        # fmt:on

    def __updateFileId(self):
        self.__identifier = str(self.__reqObj.getValue("identifier"))
        if not self.__identifier:
            return
        #
        self.__modelfileId = self.__identifier + '_model_P1.cif'
        self.__summaryfileId = self.__identifier + '_prd-summary_P1.cif'
        self.__summaryfilePath = os.path.join(self.__sessionPath, self.__summaryfileId)
        self.__updateTitle()

    def __updateTitle(self):
        if os.access(self.__summaryfilePath, os.F_OK):
            self.__summaryCifObj = SummaryCifUtil(summaryFile=self.__summaryfilePath, verbose=self.__verbose, log=self.__lfh)
            self.__pdbId = self.__summaryCifObj.getPdbId()
            self.__title = self.__summaryCifObj.getTitle()
        #

    def doOp(self):
        """Map operation to path and invoke operation.

            :Returns:

            Operation output is packaged in a ResponseContent() object.
        """
        return self.__doOpException()

    def setLogHandle(self, log=sys.stderr):
        """  Reset the stream for logging output.
        """
        try:
            self.__lfh = log
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False
        #

    def __doOpNoException(self):  # pylint: disable=unused-private-member
        """Map operation to path and invoke operation.  No exception handling is performed.

            :Returns:

            Operation output is packaged in a ResponseContent() object.
        """
        #
        reqPath = self.__reqObj.getRequestPath()
        if reqPath not in self.__appPathD:
            # bail out if operation is unknown -
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            rC.setError(errMsg='Unknown operation')
            return rC
        else:
            mth = getattr(self, self.__appPathD[reqPath], None)
            rC = mth()
        return rC

    def __doOpException(self):
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

            :Returns:

            Operation output is packaged in a ResponseContent() object.
        """
        #
        try:
            reqPath = self.__reqObj.getRequestPath()
            if reqPath not in self.__appPathD:
                # bail out if operation is unknown -
                rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                rC.setError(errMsg='Unknown operation')
            else:
                mth = getattr(self, self.__appPathD[reqPath], None)
                rC = mth()
            return rC
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            rC.setError(errMsg='Operation failure')
            return rC

    ################################################################################################################
    # ------------------------------------------------------------------------------------------------------------
    #      Top-level REST methods
    # ------------------------------------------------------------------------------------------------------------
    #
    def _dumpOp(self):
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC.setHtmlList(self.__reqObj.dump(format='html'))
        return rC

    def _StandaloneOp(self):
        """ Launch PRD search module first-level interface (standalone)
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._StandaloneOp() Starting now\n")
        #
        self.__getSession()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        depId = str(self.__reqObj.getValue('identifier')).upper().strip()
        if depId:
            if not self.__copyArchiveFile(depId):
                rC.setError(errMsg='Invalid Deposition ID: ' + depId)
                return rC
            #
        elif self.__isFileUpload():
            if not self.__uploadFile():
                rC.setError(errMsg='Upload file failed')
                return rC
            #
        else:
            rC.setError(errMsg='No Deposition ID input & file uploaded')
            return rC
        #
        #
        dU = DetachUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        dU.set(workerObj=self, workerMethod="_runPrdSearch")
        dU.runDetach()
        #
        return self.__returnPrdSummaryPage()

    def _WorkflowOp(self):
        """ Launch PRD search module first-level interface (workflow)
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._WorkflowOp() Starting now\n")
        #
        self.__getSession()
        #
        annotator = str(self.__reqObj.getValue("annotator"))
        if annotator:
            f = open(os.path.join(self.__sessionPath, "annotator_initial"), "wb")
            if sys.version_info[0] > 2:
                annotator = annotator.encode('ascii')
            f.write(annotator)
            f.close()
        #
        # determine if currently operating in Workflow Managed environment
        bIsWorkflow = self.__isWorkflow()
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._WorkflowOp() workflow flag is %r\n" % bIsWorkflow)
        #
        if not bIsWorkflow:
            self.__reqObj.setReturnFormat(return_format="html")
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            rC.setError(errMsg="Operation is not in Workflow Managed environment\n")
            return rC
        #
        self.__getPrdSearchResult()
        #
        dU = DetachUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        dU.set(workerObj=self, workerMethod="_getSummaryHtml")
        dU.runDetach()
        #
        return self.__returnPrdSummaryPage()

    def _reRunPrdSearchOp(self):
        """ Re-run PRD search
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._reRunPrdSearchOp() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        dU = DetachUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        dU.set(workerObj=self, workerMethod="_runPrdSearch")
        dU.runDetach()
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC.setStatusCode('running')
        return rC

    def _checkRunningStatusOp(self):
        """ Performs a check on the contents of a semaphore file and returns the associated status
        """
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        sph = self.__reqObj.getSemaphore()
        dU = DetachUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        if (dU.semaphoreExists(sph)):
            myD = {}
            myD["statuscode"] = "ok"
            #
            htmlFilePath = os.path.join(self.__sessionPath, sph + '.html')
            ofh = open(htmlFilePath, 'r')
            myD["htmlcontent"] = ofh.read()
            ofh.close()
            #
            rC.addDictionaryItems(myD)
        else:
            time.sleep(2)
            rC.setStatusCode('running')
        #
        return rC

    def _runPrdSearch(self):
        # inputPath = os.path.join(self.__sessionPath, self.__modelfileId)
        WorkingDirPath = os.path.join(self.__sessionPath, 'search')
        firstModelPath = os.path.join(WorkingDirPath, 'firstmodel.cif')
        logFilePath = os.path.join(WorkingDirPath, 'search-prd.log')
        #
        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__cI.get('SITE_PREFIX'), verbose=True)
        dp.setWorkingDir(WorkingDirPath)
        dp.imp(os.path.join(self.__sessionPath, self.__modelfileId))
        dp.addInput(name='firstmodel', value=firstModelPath)
        dp.addInput(name='logfile', value=logFilePath)
        dp.op('prd-search')
        dp.exp(os.path.join(self.__sessionPath, self.__summaryfileId))
        self.__getLogMessage(logFilePath)
        if not self.__message:
            self.__updateTitle()
        #
        return self._getSummaryHtml(iFlag=True)

    def __getPrdSearchResult(self):
        # Update WF status database --
        if not self.__updateWfTrackingDb("open"):
            self.__message = "TRACKING status update to 'open' failed for session %s \n" % self.__sessionId
        else:
            if (self.__verbose):
                self.__lfh.write("+EntityWebAppWorker._WorkflowOp() Tracking status set to open\n")
            #
            ioUtil = WFDataIOUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok = ioUtil.ImportData()
            if not ok:
                self.__message = "Get WorkFlow result(s) failed for session %s \n" % self.__sessionId
            else:
                self.__updateFileId()
            #
        #

    def __returnPrdSummaryPage(self):
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        myD = {}
        myD['sessionid'] = self.__sessionId
        myD['identifier'] = self.__identifier
        myD['pdbid'] = self.__pdbId
        myD['filesource'] = str(self.__reqObj.getValue("filesource"))
        myD['instance'] = str(self.__reqObj.getValue("instance"))
        myD['classID'] = str(self.__reqObj.getValue("classID"))
        myD['title'] = self.__title
        myD['sph'] = self.__reqObj.getSemaphore()
        #
        rC.setHtmlText(self.__processTemplate('summary_view/prd_summary_tmplt.html', myD))
        return rC

    def _getSummaryHtml(self, iFlag=False):
        if not self.__message:
            if not self.__summaryCifObj:
                self.__message = 'Can not find search result file.'
            #
        #
        htmlFilePath = os.path.join(self.__sessionPath, self.__reqObj.getSemaphore() + '.html')
        ofh = open(htmlFilePath, 'w')
        if self.__message:
            ofh.write(self.__message + '\n')
        else:
            summaryObj = PrdSummaryDepict(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
            form_data = summaryObj.DoRenderSummaryPage(imageFlag=iFlag)
            ofh.write(form_data + '\n')
        #
        ofh.close()
        #
        return True

    def _StructSummaryView(self):
        """ Launch structure summary interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._StructSummaryView() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        myD = {}
        myD['sessionid'] = self.__sessionId
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        if not self.__summaryCifObj:
            myD['pdbid'] = 'unknown'
            myD['form_data'] = 'Can not find summary result file.'
        else:
            summaryObj = StrSummaryDepict(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
            myD['pdbid'] = summaryObj.GetPDBID()
            myD['form_data'] = summaryObj.DoRenderSummaryPage()
        #
        rC.setHtmlText(self.__processTemplate('summary_view/str_summary_tmplt.html', myD))
        #
        return rC

    def _LaunchFixer(self):
        """ Launch Entity fixer view interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._LaunchFixer() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        prePro = FormPreProcess(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        error = prePro.getMessage()
        if error:
            myD = {}
            myD['pdbid'] = self.__reqObj.getValue('pdbid')
            myD['identifier'] = self.__identifier
            myD['title'] = self.__title
            myD['error'] = error
            rC.setHtmlText(self.__processTemplate('summary_view/str_summary_error_tmplt.html', myD))
            return rC
        #
        if not self.__summaryCifObj:
            myD = {}
            myD['pdbid'] = self.__reqObj.getValue('pdbid')
            myD['identifier'] = self.__identifier
            myD['title'] = self.__title
            myD['error'] = 'Can not find summary result file.'
            rC.setHtmlText(self.__processTemplate('summary_view/str_summary_error_tmplt.html', myD))
            return rC
        #
        strObj = StrFormDepict(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        rC.setHtmlText(strObj.LaunchFixer())
        return rC

    def _LaunchEditor(self):
        """ Launch Entity fixer view interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._LaunchEditor() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        strObj = StrFormDepict(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        rC.setHtmlText(strObj.LaunchEditor())
        return rC

    def _mergePolymer(self):
        """ Launch Merge Polymer interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._mergePolymer() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        mergeObj = MergePolymer(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        mergeObj.updateFile()
        #
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['data'] = mergeObj.getMessage()
        rC.setHtmlText(self.__processTemplate('update_form/update_result_tmplt.html', myD))
        return rC

    def _mergeLigand(self):
        """ Launch Merge Ligand interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._mergePolymer() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        mergeObj = MergeLigand(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        mergeObj.updateFile()
        #
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['data'] = mergeObj.getMessage()
        rC.setHtmlText(self.__processTemplate('update_form/update_result_tmplt.html', myD))
        return rC

    def _jmolView(self):
        """ Launch Jmol view interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._jmolView() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['instanceid'] = self.__reqObj.getValue('instanceid')
        myD['label'] = self.__reqObj.getValue('label')
        myD['focus'] = self.__reqObj.getValue('focus')
        myD['3dpath'] = os.path.join(self.__rltvSessionPath, 'search', 'firstmodel.cif')
        rC.setHtmlText(self.__processTemplate('summary_view/jmol_environ_view_tmplt.html', myD))
        #
        return rC

    def _gifView(self):
        """ Launch 2D view interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._gifView() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['instanceid'] = self.__reqObj.getValue('instanceid')
        myD['label'] = self.__reqObj.getValue('label')
        imageRelPath = ""
        imageAbsPath = os.path.join(self.__sessionPath, 'search', myD['instanceid'], myD['label'] + '.gif')
        if os.access(imageAbsPath, os.F_OK):
            imageRelPath = os.path.join(self.__rltvSessionPath, 'search', myD['instanceid'], myD['label'] + '.gif')
        else:
            imageAbsPath = os.path.join(self.__sessionPath, 'search', myD['instanceid'], myD['label'] + '.png')
            if os.access(imageAbsPath, os.F_OK):
                imageRelPath = os.path.join(self.__rltvSessionPath, 'search', myD['instanceid'], myD['label'] + '.png')
            #
        #
        myD['2dpath'] = imageRelPath
        rC.setHtmlText(self.__processTemplate('summary_view/inst_2D_view_tmplt.html', myD))
        #
        return rC

    def _buildPRD(self):
        """ Launch Build PRD interface
        """
        if self.__verbose:
            self.__lfh.write("+EntityWebAppWorker._buildPRD() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        prdObj = BuildPrd(reqObj=self.__reqObj, summaryFile=self.__summaryfilePath, verbose=self.__verbose, log=self.__lfh)
        error_msg = prdObj.build()
        if error_msg:
            myD = {}
            myD['pdbid'] = self.__reqObj.getValue('pdbid')
            myD['identifier'] = self.__identifier
            myD['label'] = self.__reqObj.getValue('label')
            myD['message'] = error_msg
            rC.setHtmlText(self.__processTemplate('prd/build_prd_failed_tmplt.html', myD))
            return rC
        #
        # templatePath = os.path.join(str(self.__reqObj.getValue('TopPath')), 'htdocs', 'editormodule')
        # Templates are stored in editor source tree
        templatePath = get_editor_template_file_path()
        self.__reqObj.setValue('TemplatePath', templatePath)
        #
        # subdirectory = str(self.__reqObj.getValue('instanceid'))
        # self.__reqObj.setValue('subdirectory', subdirectory)
        #
        datafile = prdObj.getPRDID() + '.cif'
        self.__reqObj.setValue('datafile', datafile)
        #
        self.__reqObj.setValue('context', 'entityfix')
        # absPath = os.path.join(self.__sessionPath, 'search', subdirectory)
        #
        # instantiate datastore to be used for capturing/persisting edits
        pdbxDataIo = PdbxDataIo(self.__reqObj, self.__verbose, self.__lfh)
        dataBlockName = pdbxDataIo.initializeDataStore()
        pdbxDataIo.initializeDictInfoStore()
        #
        self.__reqObj.setValue('datablockname', dataBlockName)
        edtrDpct = EditorDepict(self.__verbose, self.__lfh)
        # edtrDpct.setAbsolutePath(absPath)
        edtrDpct.setAbsolutePath(self.__sessionPath)
        # oL = edtrDpct.doRender(self.__reqObj,False,dataBlockName,self.__title)
        oL = edtrDpct.doRender(self.__reqObj, False)
        rC.setHtmlText('\n'.join(oL))
        #
        # """
        # prdId = prdObj.getPRDID()
        # prdfile = os.path.join(self.__sessionPath, 'search', str(self.__reqObj.getValue('instanceid')), prdId + '.cif')
        # #
        # initD = {}
        # initD['prd_id'] = ''
        # initD['label_prd_id'] = ''
        # initD['fam_id'] = ''
        # initD['prdfile'] = prdfile
        # initD['family_name'] = ''
        # initD['build_comment_start'] = '<!--'
        # initD['build_comment_end'] = '-->'
        # initD['update_comment_start'] = ''
        # initD['update_comment_end'] = ''
        # #
        # depictObj = DepictPrd(reqObj=self.__reqObj, prdID=prdObj.getPRDID(), prdFile=prdfile, myD=initD, \
        #                       verbose=self.__verbose, log=self.__lfh)
        # myD = depictObj.getDepictContext()
        # rC.setHtmlText(self.__processTemplate('prd/build_prd_tmplt.html', myD))
        # """
        return rC

    def _updatePRD(self):
        """ Update PRD based on interface input
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._updatePRD() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        updObj = UpdatePrd(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        updObj.Update()
        prdId = updObj.getPRDID()
        prdfile = os.path.join(self.__sessionPath, prdId + '.cif')
        #
        initD = {}
        initD['prd_id'] = ''
        initD['label_prd_id'] = ''
        initD['fam_id'] = ''
        initD['prdfile'] = prdfile
        initD['family_name'] = ''
        initD['build_comment_start'] = '<!--'
        initD['build_comment_end'] = '-->'
        initD['update_comment_start'] = ''
        initD['update_comment_end'] = ''
        #
        depictObj = DepictPrd(reqObj=self.__reqObj, prdID=prdId, prdFile=prdfile, myD=initD,
                              verbose=self.__verbose, log=self.__lfh)
        myD = depictObj.getDepictContext()
        rC.setHtmlText(self.__processTemplate('prd/build_prd_tmplt.html', myD))
        return rC

    def _resultView(self):
        """ Launch search result view interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._resultView() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        instId = str(self.__reqObj.getValue("instanceid"))
        viewType = str(self.__reqObj.getValue("type"))  # pylint: disable=redefined-builtin
        resultObj = None
        if self.__summaryCifObj:
            resultObj = ResultDepict(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        #
        myD = {}
        myD['sessionid'] = self.__sessionId
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['label'] = self.__reqObj.getValue('label')
        if viewType == 'match':
            if resultObj:
                myD['form_data'] = resultObj.DoRenderUpdatePage()
            else:
                myD['form_data'] = 'Can not find summary result file.'
            #
            rC.setHtmlText(self.__processTemplate('update_form/update_match_tmplt.html', myD))
        elif viewType == 'input':
            if resultObj:
                myD['form_data'] = resultObj.DoRenderInputPage()
            else:
                myD['form_data'] = 'Can not find summary result file.'
            #
            rC.setHtmlText(self.__processTemplate('update_form/update_user_input_tmplt.html', myD))
        elif viewType == 'split':
            if resultObj:
                myD['form_data'] = resultObj.DoRenderSplitPage()
            else:
                myD['form_data'] = '<tr><td colspan="6">Can not find summary result file.</td></tr>'
            #
            rC.setHtmlText(self.__processTemplate('summary_view/split_polymer_residue_tmplt.html', myD))
        elif viewType == 'split_with_input':
            rC.setHtmlText(self.__processTemplate('summary_view/split_polymer_residue_input_tmplt.html', myD))
        elif viewType == 'merge':
            if resultObj:
                myD['form_data'] = resultObj.DoRenderMergePage()
            else:
                myD['form_data'] = '<tr><td colspan="5">Can not find summary result file.</td></tr>'
            #
            rC.setHtmlText(self.__processTemplate('update_form/update_merge_polymer_residue_tmplt.html', myD))
        else:
            tmplt = 'result_view/all_tmplt.html'
            if resultObj:
                if instId:
                    myD['sequence'] = resultObj.getSeqs(instId)
                    tmplt = 'result_view/individual_tmplt.html'
                myD['form_data'] = resultObj.DoRenderResultPage(instId)
            else:
                myD['form_data'] = 'Can not find summary result file.'
            #
            rC.setHtmlText(self.__processTemplate(tmplt, myD))
        #
        return rC

    def _OpenEyeMatchView(self):
        """ Launch OpenEye MCS view interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._matchView() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        resultObj = OpenEyeUtil(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        rC.setHtmlText(resultObj.MatchHtmlText())
        return rC

    def _updateFile(self):
        """ Launch update coordinate file interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._updateFile() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        updateObj = UpdateFile(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        updateObj.updateFile()
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['form_data'] = updateObj.getMessage()
        #
        rC.setHtmlText(self.__processTemplate('update_form/update_summary_tmplt.html', myD))
        return rC

    def _downloadFile(self):
        """ Launch download file interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._downloadFile() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        fullFilePath = str(self.__reqObj.getValue('filepath'))
        fileId = str(self.__reqObj.getValue('fileid'))
        if fullFilePath:
            self.__reqObj.setReturnFormat(return_format="binary")
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            rC.setBinaryFile(fullFilePath, attachmentFlag=True, serveCompressed=True)
        elif fileId:
            self.__reqObj.setReturnFormat(return_format="binary")
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            filePath = os.path.join(self.__sessionPath, fileId)
            instId = str(self.__reqObj.getValue("instanceid"))
            if instId:
                filePath = os.path.join(self.__sessionPath, 'search', instId, fileId)
            #
            if fileId.startswith('PRD_'):
                RemoveEmptyCategories(filePath)
            #
            rC.setBinaryFile(filePath, attachmentFlag=True, serveCompressed=True)
        else:
            self.__reqObj.setReturnFormat(return_format="html")
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            #
            downloadObj = DownloadFile(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            myD = {}
            myD['pdbid'] = self.__reqObj.getValue('pdbid')
            myD['identifier'] = self.__identifier
            myD['title'] = self.__title
            myD['form_data'] = downloadObj.ListFiles()
            myD['form_data1'] = downloadObj.ListPrds()
            #
            rC.setHtmlText(self.__processTemplate('download/download_tmplt.html', myD))
        #
        return rC

    def _commitPRD(self):
        """ Commit PRD to CVS archive
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._commitPRD() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        cvsObj = CVSCommit(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        returntcontent = cvsObj.checkin()
        rC.setText(text=returntcontent)
        return rC

    def _chopperHandler(self):
        """ Launch chopper handler interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._chopperHandler() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        chopperObj = ChopperHandler(reqObj=self.__reqObj, summaryFile=self.__summaryfilePath, verbose=self.__verbose, log=self.__lfh)
        returnCode = chopperObj.process()
        rC.setStatusCode(returnCode)
        return rC

    def _LinkView(self):
        """ Launch Link view interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._LinkView() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        if not self.__summaryCifObj:
            myD['labelId'] = 'unknown'
            myD['data'] = '<tr><td colspan="12">Can not find summary result file.</td></tr>'
        else:
            linkObj = LinkDepict(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
            myD['labelId'] = linkObj.getLabelId()
            myD['data'] = linkObj.getTableData()
        #
        rC.setHtmlText(self.__processTemplate('result_view/link_tmplt.html', myD))
        return rC

    def _splitPolymer(self):
        """ Launch Split Polymer interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._splitPolymer() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        splitObj = SplitPolymer(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        splitObj.updateFile()
        #
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['data'] = splitObj.getMessage()
        rC.setHtmlText(self.__processTemplate('update_form/update_result_tmplt.html', myD))
        return rC

    def _editPolymer(self):
        """ Launch Edit Polymer interface
        """
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker._editPolymer() Starting now\n")
        #
        self.__getSession()
        self.__updateFileId()
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        editObj = EditPolymer(reqObj=self.__reqObj, summaryCifObj=self.__summaryCifObj, verbose=self.__verbose, log=self.__lfh)
        editObj.updateFile()
        #
        myD = {}
        myD['pdbid'] = self.__reqObj.getValue('pdbid')
        myD['identifier'] = self.__identifier
        myD['title'] = self.__title
        myD['data'] = editObj.getMessage()
        rC.setHtmlText(self.__processTemplate('update_form/update_result_tmplt.html', myD))
        return rC

    def _exit_Finished(self):
        """ Exiting Entity Transform Module when annotator has completed all necessary processing
        """
        if self.__verbose:
            self.__lfh.write("--------------------------------------------\n")
            self.__lfh.write("+EntityWebAppWorker._exit_Finished() - starting\n")
        #
        state = "closed(0)"
        bIsWorkflow = self.__isWorkflow()
        #
        self.__getSession()
        sessionId = self.__sessionId
        self.__reqObj.setReturnFormat('json')
        #
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        if bIsWorkflow:
            try:
                ioUtil = WFDataIOUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                ok = ioUtil.ExportData()
                if ok:
                    bSuccess = self.__updateWfTrackingDb(state)
                    if not bSuccess:
                        rC.setError(errMsg="+EntityWebAppWorker._exit_Finished() - TRACKING status, update to '%s' failed for session %s \n" % (state, sessionId))
                else:
                    rC.setError(errMsg="+EntityWebAppWorker._exit_Finished() - problem saving log module state")

            except:  # noqa: E722 pylint: disable=bare-except
                if self.__verbose:
                    self.__lfh.write("+EntityWebAppWorker._exit_Finished() - problem saving lig module state")
                traceback.print_exc(file=self.__lfh)
                rC.setError(errMsg="+EntityWebAppWorker._exit_Finished() - exception thrown on saving lig module state")
        else:
            if (self.__verbose):
                self.__lfh.write("+EntityWebAppWorker._exit_Finished() - Not in WF environ so skipping save action of pickle file and status update to TRACKING database for session %s \n" % sessionId)  # noqa: E501
            rC.setError(errMsg="+EntityWebAppWorker._exit_Finished() - Not in WF environ")
        #
        return rC

    def __getLogMessage(self, logfile):
        error = GetLogMessage(logfile)
        if error:
            self.__message = '<pre>\n' + error + '\n</pre>\n'
        #

    def __updateWfTrackingDb(self, p_status):
        """ Private function used to udpate the Workflow Status Tracking Database

            :Params:
                ``p_status``: the new status value to which the deposition data set is being set

            :Helpers:
                wwpdb.apps.ccmodule.utils.WfTracking.WfTracking

            :Returns:
                ``bSuccess``: boolean indicating success/failure of the database update
        """
        #
        bSuccess = False
        #
        sessionId = self.__sessionId
        depId = self.__reqObj.getValue("identifier").upper()
        instId = self.__reqObj.getValue("instance")
        classId = str(self.__reqObj.getValue("classID")).lower()
        #
        try:
            wft = WfTracking(verbose=self.__verbose, log=self.__lfh)
            bSuccess = wft.setInstanceStatus(depId=depId,
                                             instId=instId,
                                             classId=classId,
                                             status=p_status)
            if self.__verbose:
                self.__lfh.write("+EntityWebAppWorker.__updateWfTrackingDb() -TRACKING status updated to '%s' for session %s \n" % (p_status, sessionId))
        except:  # noqa: E722 pylint: disable=bare-except
            bSuccess = False
            if self.__verbose:
                self.__lfh.write("+EntityWebAppWorker.__updateWfTrackingDb() - TRACKING status, update to '%s' failed for session %s \n" % (p_status, sessionId))
            traceback.print_exc(file=self.__lfh)
        #
        return bSuccess

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__rltvSessionPath = self.__sObj.getRelativePath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+EntityWebApp.__getSession() - creating/joining session %s\n" % self.__sessionId)
            # self.__lfh.write("+EntityWebApp.__getSession() - workflow storage path    %s\n" % self.__workflowStoragePath)
            self.__lfh.write("+EntityWebApp.__getSession() - session path %s\n" % self.__sessionPath)

    def __isFileUpload(self, fileTag='file'):
        """ Generic check for the existence of request paramenter "file".
        """
        # Gracefully exit if no file is provide in the request object -
        try:
            stringtypes = (unicode, str)
        except NameError:
            stringtypes = (str, bytes)
        fs = self.__reqObj.getRawValue(fileTag)
        if ((fs is None) or isinstance(fs, stringtypes)):
            return False
        return True

    def __copyArchiveFile(self, depId):
        """
        """
        pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        archiveFilePath = pI.getFilePath(dataSetId=depId, wfInstanceId=None, contentType='model', formatType='pdbx', fileSource="archive")
        if archiveFilePath and os.access(archiveFilePath, os.R_OK):
            self.__reqObj.setValue("identifier", depId)
            self.__getInputFileInfo(archiveFilePath)
            shutil.copyfile(archiveFilePath, os.path.join(self.__sessionPath, self.__modelfileId))
            return True
        #
        return False

    def __uploadFile(self, fileTag='file'):
        #
        #
        if (self.__verbose):
            self.__lfh.write("+EntityWebApp.__uploadFile() - file upload starting\n")

        #
        # Copy upload file to session directory -
        try:
            fs = self.__reqObj.getRawValue(fileTag)
            fNameInput = str(fs.filename)
            #
            # Need to deal with some platform issues -
            #
            if (fNameInput.find('\\') != -1) :
                # likely windows path -
                fName = ntpath.basename(fNameInput)
            else:
                fName = os.path.basename(fNameInput)
            #
            if (self.__verbose):
                self.__lfh.write("+EntityWebApp.__uploadFile() - upload file %s\n" % fs.filename)
                self.__lfh.write("+EntityWebApp.__uploadFile() - basename %s\n" % fName)
            #
            # Store upload file in session directory -
            #
            flist = fName.split('.')
            idx = flist[0].find('_model')
            if idx == -1:
                self.__identifier = flist[0]
            else:
                self.__identifier = flist[0][0:idx]
            #
            uploadFilePath = os.path.join(self.__sessionPath, '_upload_' + str(time.strftime("%Y%m%d%H%M%S", time.localtime())))
            ofh = open(uploadFilePath, 'wb')
            ofh.write(fs.file.read())
            ofh.close()
            #
            if os.access(uploadFilePath, os.F_OK):
                self.__getInputFileInfo(uploadFilePath)
                os.rename(uploadFilePath, os.path.join(self.__sessionPath, self.__modelfileId))
                if (self.__verbose):
                    self.__lfh.write("+EntityWebApp.__uploadFile() Uploaded file\n")
                #
                return True
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if (self.__verbose):
                self.__lfh.write("+EntityWebApp.__uploadFile() File upload processing failed for %s\n" % str(fs.filename))
                traceback.print_exc(file=self.__lfh)
            #
        #
        return False

    def __getInputFileInfo(self, inputFileName):
        """
        """
        try:
            cifObj = mmCIFUtil(filePath=inputFileName)
            dList = cifObj.GetValue('database_2')
            for d in dList:
                if ('database_id' not in d) or (not d['database_id']) or ('database_code' not in d) or (not d['database_code']):
                    continue
                #
                dbname = d['database_id'].upper().strip()
                dbcode = d['database_code'].upper().strip()
                if dbname == 'PDB':
                    self.__pdbId = dbcode
                    self.__lfh.write("+EntityWebApp.__getInputFileInfo() pdbId %s\n" % self.__pdbId)
                elif dbname == 'WWPDB':
                    self.__identifier = dbcode
                    self.__lfh.write("+EntityWebApp.__getInputFileInfo() identifier %s\n" % self.__identifier)
                #
            #
            self.__title = cifObj.GetSingleValue('struct', 'title')
            #
            self.__reqObj.setValue('identifier', self.__identifier)
            self.__updateFileId()
        except:  # noqa: E722 pylint: disable=bare-except
            if (self.__verbose):
                traceback.print_exc(file=self.__lfh)
            #
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
        ifh = open(fPath, 'r')
        sIn = ifh.read()
        ifh.close()
        return (sIn % parameterDict)

    def __isWorkflow(self):
        """ Determine if currently operating in Workflow Managed environment

            :Returns:
                boolean indicating whether or not currently operating in Workflow Managed environment
        """
        #
        fileSource = str(self.__reqObj.getValue("filesource")).lower()
        #
        if (self.__verbose):
            self.__lfh.write("+EntityWebAppWorker.__isWorkflow() - filesource is %s\n" % fileSource)
        #
        # add wf_archive to fix PDBe wfm issue -- jdw 2011-06-30
        #
        if fileSource in ['archive', 'wf-archive', 'wf_archive', 'wf-instance', 'wf_instance']:
            # if the file source is any of the above then we are in the workflow manager environment
            return True
        else:
            # else we are in the standalone dev environment
            return False


def main():
    sTool = EntityWebApp()
    d = sTool.doOp()
    for k, v in d.items():
        sys.stdout.write("Key - %s  value - %r\n" % (k, v))


if __name__ == '__main__':
    main()
