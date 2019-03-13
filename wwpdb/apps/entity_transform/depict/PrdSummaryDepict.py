##
# File:  PrdSummaryDepict.py
# Date:  09-Oct-2012
# Updates:
##
"""
Create HTML depiction for PRD search summary.

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

from wwpdb.apps.entity_transform.depict.DepictBase import DepictBase
from wwpdb.apps.entity_transform.depict.ProcessPrdSummary import ProcessPrdSummary

class PrdSummaryDepict(DepictBase):
    """ Class responsible for generating HTML depiction of PRD search results.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(PrdSummaryDepict, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__data = []
        self.__matchResultFlag = {}
        self.__graphmatchResultFlag = False
        self.__combResidueFlag = False
        self.__splitPolymerResidueFlag = False

    def DoRenderSummaryPage(self, imageFlag=True):
        """
        """
        prdUtil = ProcessPrdSummary(reqObj=self._reqObj, summaryCifObj=self._cifObj, verbose=self._verbose, log=self._lfh)
        prdUtil.run(imageFlag)
        self.__data = prdUtil.getPrdData()
        self.__matchResultFlag = prdUtil.getMatchResultFlag()
        self.__graphmatchResultFlag = prdUtil.getGraphmatchResultFlag()
        self.__combResidueFlag = prdUtil.getCombResidueFlag()
        self.__splitPolymerResidueFlag = prdUtil.getSplitPolymerResidueFlag()
        #
        input_data = 'sessionid=' + self._sessionId + '&identifier=' + self._identifier + '&pdbid=' + self._pdbId
        #
        text = '<ul>\n'
        #
        text += self.__depiction(self.__data) + '\n'
        #
        text += '<li><a class="fltlft" href="/service/entity/summary_view?' + input_data + '" target="_blank"> Access to split or merge </a></li>\n'
        #
        if self.__splitPolymerResidueFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
                  + '&type=split" target="_blank"> Split modified amino acid residue to standard amino acid residue + modification in polymer </a></li>\n'
        #
        if self.__combResidueFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
                  + '&type=merge" target="_blank"> Merge standard amino acid residue + modification to modified amino acid residue in polymer </a></li>\n' 
        #
        if self.__matchResultFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data + '" target="_blank"> View All Search Result(s) </a></li>\n'
        # 
        if self.__graphmatchResultFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
                  + '&type=match" target="_blank"> Update Coordinate File with Match Result(s) </a></li>\n' 
        #
        text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
              + '&type=input" target="_blank"> Update Coordinate File with Input IDs </a></li>\n'
        #
        text += '<li><a class="fltlft" href="/service/entity/download_file?' + input_data + '" target="_blank"> Download Files </a></li>\n'
        #
        text += '</ul>\n'
        #
        return text

    def __depiction(self, datalist):
        """
        """
        text = ''
        if not datalist:
            return text
        #
        for d in datalist:
            myD = {}
            myD['id'] = d['id']
            myD['text'] = d['text']
            if d.has_key('list_text'):
                list_text = '<li>\n' + d['list_text'] + '</li>\n'
                if d.has_key('list'):
                    list_text += self.__depictInstanceTable(d['list'])
                myD['list'] = list_text
            elif d.has_key('list'):
                myD['list'] = self.__depiction(d['list'])
            else:
                myD['list'] = ''
            text += '<li>\n' + self._processTemplate('summary_view/expand_list_tmplt.html', myD) + '</li>\n'
        #
        return text

    def __depictInstanceTable(self, datalist):
        """
        """
        if not datalist:
            return ''
        #
        text = '<table>\n'
        #
        for d in datalist:
            myD = {}
            myD['sessionid'] = self._sessionId
            myD['identifier'] =  self._identifier
            myD['pdbid' ] = self._pdbId
            myD['instanceid'] = d['id']
            myD['label'] = d['label']
            myD['focus'] = d['focus']
            myD['3d_view'] = self._processTemplate('summary_view/3d_view_tmplt.html', myD)
            if self.__has2D_Image(d['id'], d['label']):
                myD['2d_view'] = self._processTemplate('summary_view/2d_view_tmplt.html', myD)
            else:
                myD['2d_view'] = '&nbsp;'
            #
            myD['build_prd'] = self._processTemplate('summary_view/build_prd_tmplt.html', myD)
            if self.__matchResultFlag.has_key(d['id']):
                text += self._processTemplate('summary_view/row_with_result_tmplt.html', myD) + '\n'
            elif d['linkage_info'] == 'linked':
                text += self._processTemplate('summary_view/row_tmplt.html', myD) + '\n'
            else:
                if d.has_key('message'):
                    message = d['message'].replace('\n', '<br/>')
                    myD['text'] = '<span class="warninfo">\n<a href="#" title="' + message + '" onclick="return false">\nNot connected</a>\n</span>'
                else:
                    myD['text'] = 'Not connected'
                text += self._processTemplate('summary_view/row_without_2D_view_tmplt.html', myD) + '\n'
        #
        text += '</table>\n'
        return text

    def __has2D_Image(self, instanceid, label):
        """
        """
        imagePath = os.path.join(self._sessionPath, 'search', instanceid, label + '.gif')
        if not os.access(imagePath, os.F_OK):
            return False
        #
        statinfo = os.stat(imagePath)
        if statinfo.st_size == 0:
            return False
        #
        return True
