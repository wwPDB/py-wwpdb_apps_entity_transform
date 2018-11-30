##
# File:  ImageGenerator.py
# Date:  09-Jan-2018
# Updates:
##
"""
Generate instance's image

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2018 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import multiprocessing, os, sys, string, traceback

from wwpdb.apps.entity_transform.utils.CommandUtil import CommandUtil
from rcsb.utils.multiproc.MultiProcUtil                import MultiProcUtil

class ImageGenerator(object):
    """ Class responsible generating instance's image
    """
    def __init__(self, reqObj=None, subPath='search', fileExt='comp.cif', verbose=False, log=sys.stderr):
        self.__reqObj = reqObj
        self.__subPath = subPath
        self.__fileExt = fileExt 
        self.__verbose = verbose
        self.__lfh = log
        self.__sessionPath = None
        self.__cmdUtil = None

    def run(self, instList):
        """
        """
        if not instList:
            return
        #
        self.__getSession()
        self.__cmdUtil = CommandUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        numProc = multiprocessing.cpu_count() / 2
        mpu = MultiProcUtil(verbose = True)
        mpu.set(workerObj = self, workerMethod = "runMultiProcess")
        mpu.setWorkingDir(self.__sessionPath)
        ok,failList,retLists,diagList = mpu.runMulti(dataList=instList, numProc=numProc, numResults=1)

    def runMultiProcess(self, dataList, procName, optionsD, workingDir):
        """
        """
        rList = []
        for instData in dataList:
            self.__generate2DImage(instData[0], instData[1])
            rList.append(instData[0])
        #
        return rList,rList,[]

    def __getSession(self):
        """
        """
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def __generate2DImage(self, inst_id, label):
        """
        """
        instancePath = os.path.join(self.__sessionPath, self.__subPath, inst_id)
        target = os.path.join(instancePath, inst_id + '.' + self.__fileExt)
        if not os.access(target, os.F_OK):
            return
        #
        het_id = label
        list = inst_id.split('_')
        if len(list) == 4:
            het_id = list[1]
        #
        self.__cmdUtil.setSessionPath(instancePath)
        rootName = self.__cmdUtil.getRootFileName('update-comp')
        self.__cmdUtil.runCCToolCmd('updateComponent', '', '', '', rootName + '.clog', ' -f ' + inst_id + '.' + self.__fileExt + ' ')
        rootName = self.__cmdUtil.getRootFileName('annotate-comp')
        self.__cmdUtil.runAnnotateComp(inst_id + '.' + self.__fileExt, inst_id + '.' + self.__fileExt + '.new', rootName + '.clog')
        #
        source = os.path.join(instancePath, inst_id + '.' + self.__fileExt + '.new')
        if os.access(source, os.F_OK):
            os.rename(source, target)
        #
        rootName = self.__cmdUtil.getRootFileName('comp-report')
        self.__cmdUtil.runCCToolCmd('makeCompReport', '', '', '', rootName + '.clog', ' -v -i ' + inst_id + '.' + self.__fileExt + \
                                    ' -type html-cctools -path "./" -of report.html -noaromatic ')
        #
        source = os.path.join(instancePath, het_id + '-500.gif')
        if os.access(source, os.F_OK):
            os.rename(source, os.path.join(instancePath, label + '.gif'))
        #
        self.__cmdUtil.removeSelectedFiles('__' + het_id + '__')

