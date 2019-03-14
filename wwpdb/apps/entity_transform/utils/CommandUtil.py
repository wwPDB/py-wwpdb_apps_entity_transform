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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import datetime, os, signal, subprocess, sys, time, traceback

from wwpdb.utils.config.ConfigInfo import ConfigInfo

class CommandUtil(object):
    """ Class for running back-end commands
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__sObj=None
        self.__sessionPath=None
        self.__siteId  = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cI=ConfigInfo(self.__siteId)
        #

    def setSessionPath(self, sessionPath):
        """ Set session path
        """
        self.__sessionPath = sessionPath

    def runAnnotCmd(self, command, inputFile, outputFile, logFile, clogFile, extraOptions):
        """ Run Annot package back-end commands
        """
        cmd = self.__getCmd(command="${BINPATH}/" + command, setting=self.__getAnnotSetting(), inputFile=inputFile, outputFile=outputFile, \
                            logFile=logFile, clogFile=clogFile, extraOptions=extraOptions)
        self.__runCmd(command=cmd)

    def runCCToolCmd(self, command, inputFile, outputFile, logFile, clogFile, extraOptions):
        """ Run CC_TOOLS package back-end commands
        """
        cmd = self.__getCmd(command="${CC_TOOLS}/" + command, setting=self.__getCCToolSetting(), inputComand=" -i ", inputFile=inputFile, \
                            outputComand=" -o ", outputFile=outputFile, logFile=logFile, clogFile=clogFile, extraOptions=extraOptions)
        self.__runCmd(command=cmd)

    def runCCToolCmdWithTimeOut(self, command, inputFile, outputFile, logFile, clogFile, extraOptions, timeOut=240):
        """ Run CC_TOOLS package back-end commands
        """
        cmd = self.__getCmd(command="${CC_TOOLS}/" + command, setting=self.__getCCToolSetting(), inputComand=" -i ", inputFile=inputFile, \
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
        os.chdir(self.__sessionPath)
        for filename in os.listdir("."):
            if filename.startswith(prefix):
                self.__removeFile(os.path.join(self.__sessionPath, filename))
            #
        #

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj=self.__reqObj.newSessionObj()
        self.__sessionPath=self.__sObj.getPath()

    def __getCmd(self, command="", setting="", inputComand=" -input ", inputFile="", outputComand=" -output ", outputFile="", \
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
            cmd  += " > " + clogFile + " 2>&1"
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
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True, preexec_fn=os.setsid, shell=True)
            while process.poll() == None:
                time.sleep(0.1)
                now = datetime.datetime.now()
                if (now - start).seconds > timeout:
                    os.killpg(process.pid, signal.SIGKILL)
                    os.waitpid(-1, os.WNOHANG)
                    return
                #
            #
        except:
            traceback.print_exc(file=self.__lfh)
        #

    def __getAnnotSetting(self):
        """ Get Annot package bash setting
        """
        setting = " RCSBROOT=" + self.__cI.get("SITE_ANNOT_TOOLS_PATH") + "; export RCSBROOT; " \
                + " COMP_PATH=" + self.__cI.get("SITE_CC_CVS_PATH") + "; export COMP_PATH; " \
                + " PRD_PATH=" + self.__cI.get("SITE_PRD_CVS_PATH") + "; export PRD_PATH; " \
                + " BINPATH=${RCSBROOT}/bin; export BINPATH; "
        #
        return setting

    def __getCCToolSetting(self):
        """ Get CC_TOOLS package bash setting
        """
        setting = " CC_TOOLS=" + self.__cI.get("SITE_CC_APPS_PATH") + "/bin; export CC_TOOLS; " \
                + " OE_DIR=" + self.__cI.get("SITE_CC_OE_DIR") + "; export OE_DIR; " \
                + " OE_LICENSE=" + self.__cI.get("SITE_CC_OE_LICENSE") + "; export OE_LICENSE; " \
                + " ACD_DIR=" + self.__cI.get("SITE_CC_ACD_DIR") + "; export ACD_DIR; " \
                + " CACTVS_DIR=" + self.__cI.get("SITE_CC_CACTVS_DIR") + "; export CACTVS_DIR; " \
                + " CORINA_DIR=" + self.__cI.get("SITE_CC_CORINA_DIR") + "/bin; export CORINA_DIR; " \
                + " BABEL_DIR="  + self.__cI.get("SITE_CC_BABEL_DIR") + "; export BABEL_DIR; " \
                + " BABEL_DATADIR=" + self.__cI.get("SITE_CC_BABEL_DATADIR") + "; export BABEL_DATADIR; " \
                + " LD_LIBRARY_PATH=" + self.__cI.get("SITE_CC_BABEL_LIB") + ":" \
                + os.path.join(self.__cI.get("SITE_LOCAL_APPS_PATH"), "lib") + "; export LD_LIBRARY_PATH; "
        #
        return setting

    def __removeFile(self, filePath):
        """ Remove existing file
        """
        if os.access(filePath, os.F_OK):
            os.remove(filePath)
        #
