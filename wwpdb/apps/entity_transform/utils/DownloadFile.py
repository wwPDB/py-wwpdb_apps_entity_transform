##
# File:  DownloadFile.py
# Date:  16-Oct-2012
# Updates:
##
"""
Download files.

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

import os, sys, string, traceback

class DownloadFile(object):
    """ Class responsible for download files.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__cifObj = summaryCifObj
        self.__sObj=None
        self.__sessionId=None
        self.__sessionPath=None
        self.__rltvSessionPath=None
        self.__siteId  = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        #
        self.__getSession()
        #
        self.__allInstIds = []
        #self.__getAllInstIds()
        #
        self.__fileId = str(self.__reqObj.getValue('identifier')) + '_model_P1.cif'
        #
        self.__PrdIds = []

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj=self.__reqObj.newSessionObj()
        self.__sessionId=self.__sObj.getId()
        self.__sessionPath=self.__sObj.getPath()
        self.__rltvSessionPath=self.__sObj.getRelativePath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")                    
            self.__lfh.write("+DownloadFile.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+DownloadFile.__getSession() - session path %s\n" % self.__sessionPath)            

    def __processTemplate(self,fn,parameterDict={}):
        """ Read the input HTML template data file and perform the key/value substitutions in the
            input parameter dictionary.
            
            :Params:
                ``parameterDict``: dictionary where
                key = name of subsitution placeholder in the template and
                value = data to be used to substitute information for the placeholder
                
            :Returns:
                string representing entirety of content with subsitution placeholders now replaced with data
        """
        tPath =self.__reqObj.getValue("TemplatePath")
        fPath=os.path.join(tPath,fn)
        ifh=open(fPath,'r')
        sIn=ifh.read()
        ifh.close()
        return (  sIn % parameterDict )

    def __getAllInstIds(self):
        if not self.__cifObj:
            return
        #
        category_item = [ [ 'pdbx_polymer_info',     'polymer_id'  ], \
                          [ 'pdbx_non_polymer_info', 'instance_id' ], \
                          [ 'pdbx_group_info',       'group_id'    ] ]
        for d in category_item:
            elist = self.__cifObj.getValueList(d[0])
            if not elist:
                continue
            #
            for e in elist:
                if d[1] not in e:
                    continue
                #
                self.__allInstIds.append(e[d[1]])
            #
        #

    def __findFiles(self, instId):
        list = []
        path = os.path.join(self.__sessionPath, 'search', instId)
        if not os.access(path, os.F_OK):
            return list
        #
        os.chdir(path)
        #
        for files in os.listdir('.'):
            if files.endswith('.cif') and \
               (files[:4] == 'PRD_' or files[:6] == 'PRDCC_'):
                list1 = files.split('.')
                if len(list1) > 2:
                    continue
                list.append(files)
            #
        #
        return list

    def __findPRDFiles(self):
        list = []
        os.chdir(self.__sessionPath)
        #
        for files in os.listdir('.'):
            if files.endswith('.cif') and (files.startswith('PRD_') or files.startswith('PRDCC_')):
                list1 = files.split('.')
                if len(list1) > 2:
                    continue
                list.append(files)
                if list1[0].startswith('PRD_'):
                    self.__PrdIds.append(list1[0])
            #
        #
        return list

    def ListFiles(self):
        myD = {}
        myD['sessionid'] = self.__sessionId
        myD['instanceid'] = ''
        myD['fileid'] = self.__fileId
        content = self.__processTemplate('download/one_file_tmplt.html', myD) + '\n'
        #
        #for instId in self.__allInstIds:
        #    filelist = self.__findFiles(instId)
        #    if not filelist:
        #        continue
        #    #
        #    for f in filelist:
        #        myD['instanceid'] = instId
        #        myD['fileid'] = f
        #        content += self.__processTemplate('download/one_file_tmplt.html', myD) + '\n'
        #    #
        #
        filelist = self.__findPRDFiles()
        if filelist:
            for f in filelist:
                myD['instanceid'] = ''
                myD['fileid'] = f
                content += self.__processTemplate('download/one_file_tmplt.html', myD) + '\n'
            #
        #
        return content

    def ListPrds(self):
        if not self.__PrdIds:
            return ''
        #
        content = ''
        for prd_id in self.__PrdIds:
            myd = {}
            myd['prd_id'] = prd_id
            content += self.__processTemplate('download/one_prd_tmplt.html', myd) + '\n'
        #
        myD = {}
        myD['sessionid'] = self.__sessionId
        myD['form_data'] = content
        return self.__processTemplate('download/prd_cvs_tmplt.html', myD)
