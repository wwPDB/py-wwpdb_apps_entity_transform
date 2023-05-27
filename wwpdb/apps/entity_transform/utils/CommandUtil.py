##
# File:  CommandUtil.py
# Date:  21-Jan-2018
# Updates:
##
"""
Class for running back-end commands

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

import datetime
import os
import signal
import subprocess
import sys
import time
import traceback

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon, ConfigInfoAppCc


class CommandUtil(object):
    """ Class for running back-end commands
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        # self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj = None
        self.__sessionPath = None
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__cIcc = ConfigInfoAppCc(self.__siteId, verbose=verbose, log=log)
        #

    def setSessionPath(self, sessionPath):
        """ Set session path
        """
        self.__sessionPath = sessionPath

    def runAnnotCmd(self, command, inputFile, outputFile, logFile, clogFile, extraOptions):
        """ Run Annot package back-end commands
        """
        cmd = self.__getCmd(command="${BINPATH}/" + command, setting=self.__getAnnotSetting(), inputFile=inputFile, outputFile=outputFile,
                            logFile=logFile, clogFile=clogFile, extraOptions=extraOptions)
        self.__runCmd(command=cmd)

    def runCCToolCmd(self, command, inputFile, outputFile, logFile, clogFile, extraOptions):
        """ Run CC_TOOLS package back-end commands
        """
        cmd = self.__getCmd(command="${CC_TOOLS}/" + command, setting=self.__getCCToolSetting(), inputComand=" -i ", inputFile=inputFile,
                            outputComand=" -o ", outputFile=outputFile, logFile=logFile, clogFile=clogFile, extraOptions=extraOptions)
        self.__runCmd(command=cmd)

    def runCCToolCmdWithTimeOut(self, command, inputFile, outputFile, logFile, clogFile, extraOptions, timeOut=240):
        """ Run CC_TOOLS package back-end commands
        """
        cmd = self.__getCmd(command="${CC_TOOLS}/" + command, setting=self.__getCCToolSetting(), inputComand=" -i ", inputFile=inputFile,
                            outputComand=" -o ", outputFile=outputFile, logFile=logFile, clogFile=clogFile, extraOptions=extraOptions)
        #
        self.__runCmd_with_Timeout(cmd, timeout=timeOut)

    def runAnnotateComp(self, inputFile, outputFile, clogFile):
        """ Run ${CC_TOOLS}/annotateComp command
        """
        extraOptions = " -vv -op 'stereo-cactvs|aro-cactvs|descriptor-oe|descriptor-cactvs|descriptor-inchi|" \
            + "name-oe|name-acd|xyz-ideal-corina|xyz-model-h-oe|rename|fix' "
        #
        self.runCCToolCmd("annotateComp", inputFile, outputFile, "", clogFile, extraOptions)

    def getRootFileName(self, prefix):
        """ Generate unique root file name
        """
        fileName = prefix + "_" + str(time.strftime("%Y%m%d%H%M%S", time.localtime()))
        return fileName

    def removeSelectedFiles(self, prefix):
        """ Remove selected files from session directory
        """
        if not self.__sessionPath:
            return
        #
        for filename in os.listdir(self.__sessionPath):
            if filename.startswith(prefix):
                self.__removeFile(os.path.join(self.__sessionPath, filename))
            #
        #

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def __getCmd(self, command="", setting="", inputComand=" -input ", inputFile="", outputComand=" -output ", outputFile="",
                 logFile="", clogFile="", extraOptions=""):
        """ Get general back-end commands
        """
        if not self.__sessionPath:
            self.__getSession()
        #
        cmd = "cd " + self.__sessionPath + " ; " + setting + " " + command
        if inputFile:
            cmd += inputComand + inputFile
        #
        if outputFile:
            if outputFile != inputFile:
                self.__removeFile(os.path.join(self.__sessionPath, outputFile))
            #
            cmd += outputComand + outputFile
        #
        if extraOptions:
            cmd += " " + extraOptions
        #
        if logFile:
            self.__removeFile(os.path.join(self.__sessionPath, logFile))
            cmd += " -log " + logFile
        #
        if clogFile:
            self.__removeFile(os.path.join(self.__sessionPath, clogFile))
            cmd += " > " + clogFile + " 2>&1"
        #
        cmd += " ; "
        self.__lfh.write("cmd=%s\n" % cmd)
        return cmd

    def __runCmd(self, command=""):
        """ Run back-end command with os.system
        """
        if command:
            os.system(command)
        #

    def __runCmd_with_Timeout(self, cmd, timeout=240):
        """ Run back-end command using subprocess with timeout limitation
        """
        start = datetime.datetime.now()
        try:
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE,  # pylint: disable=subprocess-popen-preexec-fn
                                       stdout=subprocess.PIPE, close_fds=True,
                                       preexec_fn=os.setsid, shell=True)
            while process.poll() is None:
                time.sleep(0.1)
                now = datetime.datetime.now()
                if (now - start).seconds > timeout:
                    os.killpg(process.pid, signal.SIGKILL)
                    os.waitpid(-1, os.WNOHANG)
                    return
                #
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def __getAnnotSetting(self):
        """ Get Annot package bash setting
        """
        setting = " RCSBROOT=" + self.__cICommon.get_site_annot_tools_path() + "; export RCSBROOT; PDB2GLYCAN=" \
            + os.path.join(os.path.abspath(self.__cICommon.get_site_packages_path()), "pdb2glycan", "bin", "PDB2Glycan") + "; export PDB2GLYCAN; " \
            + " COMP_PATH=" + self.__cIcc.get_site_cc_cvs_path() + "; export COMP_PATH; " \
            + " PRD_PATH=" + self.__cIcc.get_site_prd_cvs_path() + "; export PRD_PATH; " \
            + " BINPATH=${RCSBROOT}/bin; export BINPATH; "
        #
        return setting

    def __getCCToolSetting(self):
        """ Get CC_TOOLS package bash setting
        """
        setting = " CC_TOOLS=" + self.__cICommon.get_site_cc_apps_path() + "/bin; export CC_TOOLS; " \
            + " OE_DIR=" + self.__cICommon.get_site_cc_oe_dir() + "; export OE_DIR; " \
            + " OE_LICENSE=" + self.__cICommon.get_site_cc_oe_licence() + "; export OE_LICENSE; " \
            + " ACD_DIR=" + self.__cICommon.get_site_cc_acd_dir() + "; export ACD_DIR; " \
            + " CACTVS_DIR=" + self.__cICommon.get_site_cc_cactvs_dir() + "; export CACTVS_DIR; " \
            + " CORINA_DIR=" + self.__cICommon.get_site_cc_corina_dir() + "/bin; export CORINA_DIR; " \
            + " BABEL_DIR=" + self.__cICommon.get_site_cc_babel_dir() + "; export BABEL_DIR; " \
            + " BABEL_DATADIR=" + self.__cICommon.get_site_cc_babel_datadir() + "; export BABEL_DATADIR; " \
            + " LD_LIBRARY_PATH=" + self.__cICommon.get_site_cc_babel_lib() + ":" \
            + os.path.join(self.__cICommon.get_site_local_apps_path(), "lib") + "; export LD_LIBRARY_PATH; "
        #
        return setting

    def __removeFile(self, filePath):
        """ Remove existing file
        """
        if os.access(filePath, os.F_OK):
            os.remove(filePath)
        #
