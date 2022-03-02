##
# File:  OpenEyeUtil.py
# Date:  16-Oct-2012
# Updates:
##
"""
Utility class to utilize OpenEye MCS functionalities

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
import traceback
import inspect

from wwpdb.utils.oe_util.oedepict.OeAlignDepict import OeDepictMCSAlign
from wwpdb.apps.entity_transform.utils.CompUtil import CompUtil
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
#


class OpenEyeUtil(object):
    """ Class responsible for OpenEye MCS functionalities
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__summaryCifObj = summaryCifObj
        self.__sObj = None
        self.__sessionId = None
        self.__sessionPath = None
        self.__rltvSessionPath = None
        #
        self.__getSession()
        #
        self.__pdbId = ''
        self.__title = ''
        self.__labels = {}
        self.__getSummaryCifInfo()
        #
        self.__CoorChemMap = {}
        self.__ChemCoorMap = {}
        self.__atomList = []
        self.__chemAtomList = []
        self.__matchList = []
        self.__missingList = []
        self.__extraList = []

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
            self.__lfh.write("+OpenEyeUtil.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+OpenEyeUtil.__getSession() - session path %s\n" % self.__sessionPath)

    def __getSummaryCifInfo(self):
        if not self.__summaryCifObj:
            return
        #
        self.__pdbId = self.__summaryCifObj.getPdbId()
        self.__title = self.__summaryCifObj.getTitle()
        self.__labels = self.__summaryCifObj.getLabels()
        self.__lfh.write("+OpenEyeUtil.__getSummaryCifInfo() __labels = %d\n" % len(self.__labels))
        for k, v in self.__labels.items():
            self.__lfh.write("+OpenEyeUtil.__getSummaryCifInfo() %s = %s\n" % (k, v))

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
        with open(fPath, 'r') as ifh:
            sIn = ifh.read()
        return (sIn % parameterDict)

    def __MCSAlignPairDepict(self, refFile, fitFile, imageFile):
        """Simple pairwise MCSS alignment  -  Each aligned pair output to a separate image file
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
        #
        try:
            oed = OeDepictMCSAlign(verbose=self.__verbose, log=self.__lfh)
            oed.setSearchType(sType='relaxed')
            oed.setRefPath(refFile)
            oed.setFitPath(fitFile)
            aML = oed.alignPair(imagePath=imageFile, imageX=1000, imageY=1000)
            if len(aML) > 0:
                for (_rCC, rAt, _tCC, tAt) in aML:
                    if rAt and tAt:
                        self.__CoorChemMap[rAt] = tAt
                        self.__ChemCoorMap[tAt] = rAt
                    #
                #
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            # self.fail()
        #
        self.__lfh.write("\nFinished %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
        #

    def __readAtomSite(self, coorPath):
        cifObj = mmCIFUtil(filePath=coorPath)
        elist = cifObj.GetValue('atom_site')
        if not elist:
            return
        #
        for d in elist:
            if d['type_symbol'] == 'H' or d['type_symbol'] == 'D':
                continue
            #
            self.__atomList.append(d)
        #

    def __readChemAtom(self, compPath):
        cifObj = mmCIFUtil(filePath=compPath)
        elist = cifObj.GetValue('chem_comp_atom')
        if not elist:
            return
        #
        for d in elist:
            if d['type_symbol'] == 'H' or d['type_symbol'] == 'D':
                continue
            #
            self.__chemAtomList.append(d)
        #

    def __expendChemAtom(self):
        if not self.__chemAtomList:
            return
        #
        if 'pdbx_residue_numbering' in self.__chemAtomList[0]:
            return
        #
        # get start index for each subcomponent with different subcomponent ids
        #
        count = 0
        i_list = []
        res = ''
        for i in self.__chemAtomList:
            if i['pdbx_component_comp_id'] != res:
                i_list.append(count)
                res = i['pdbx_component_comp_id']
            count += 1
        #
        # get start index for each subcomponent within same subcomponent ids
        #
        length = len(i_list)
        for i in range(0, length - 1):
            res = self.__chemAtomList[i_list[i]]['pdbx_component_comp_id']
            atom = self.__chemAtomList[i_list[i]]['pdbx_component_atom_id']
            for j in range(i_list[i] + 1, i_list[i + 1]):
                if self.__chemAtomList[j]['pdbx_component_comp_id'] == res and \
                   self.__chemAtomList[j]['pdbx_component_atom_id'] == atom:
                    i_list.append(j)
        #
        res = self.__chemAtomList[i_list[length - 1]]['pdbx_component_comp_id']
        atom = self.__chemAtomList[i_list[length - 1]]['pdbx_component_atom_id']
        for j in range(i_list[length - 1] + 1, count):
            if self.__chemAtomList[j]['pdbx_component_comp_id'] == res and \
               self.__chemAtomList[j]['pdbx_component_atom_id'] == atom:
                i_list.append(j)
        #
        # sort start index for each subcomponent
        #
        i_list.sort()
        #
        # add pdbx_residue_numbering
        #
        cnt = 0
        for i in range(0, len(i_list) - 1):
            cnt += 1
            for j in range(i_list[i], i_list[i + 1]):
                self.__chemAtomList[j]['pdbx_residue_numbering'] = str(cnt)
        #
        cnt += 1
        for j in range(i_list[len(i_list) - 1], count):
            self.__chemAtomList[j]['pdbx_residue_numbering'] = str(cnt)
        #

    def __get_Missing_Match_ExtraList(self):
        chemAtomMap = {}
        for d in self.__chemAtomList:
            chemAtomMap[d['atom_id']] = d
            if d['atom_id'] in self.__ChemCoorMap:
                continue
            #
            dic = {}
            dic['td1'] = '&nbsp;'
            dic['td2'] = '&nbsp;'
            dic['td3'] = '&nbsp;'
            dic['td4'] = '&nbsp;'
            dic['td5'] = d['pdbx_component_comp_id']
            dic['td6'] = d['pdbx_residue_numbering']
            dic['td7'] = d['pdbx_component_atom_id']
            self.__missingList.append(dic)
        #

        for d in self.__atomList:
            dic = {}
            dic['td1'] = d['auth_asym_id']
            dic['td2'] = d['auth_comp_id']
            dic['td3'] = d['auth_seq_id']
            dic['td4'] = d['auth_atom_id']
            if d['label_atom_id'] in self.__CoorChemMap:
                d1 = chemAtomMap[self.__CoorChemMap[d['label_atom_id']]]
                dic['td5'] = d1['pdbx_component_comp_id']
                dic['td6'] = d1['pdbx_residue_numbering']
                dic['td7'] = d1['pdbx_component_atom_id']
                self.__matchList.append(dic)
            else:
                dic['td5'] = '&nbsp;'
                dic['td6'] = '&nbsp;'
                dic['td7'] = '&nbsp;'
                self.__extraList.append(dic)
        #

    def __processList(self, title, list_in):
        if not list_in:
            return ''
        #
        myD = {}
        myD['title'] = title
        content = self.__processTemplate('openeye_mcs/title_row_tmplt.html', myD)
        for d in list_in:
            content += self.__processTemplate('openeye_mcs/atom_row_tmplt.html', d)
        return content
        #

    def __getMatchList(self, coorPath, compPath):
        if not self.__CoorChemMap:
            return ''
        #
        self.__readAtomSite(coorPath)
        self.__readChemAtom(compPath)
        self.__expendChemAtom()
        self.__get_Missing_Match_ExtraList()
        if (not self.__matchList) and (not self.__extraList) and \
           (not self.__missingList):
            return ''
        #
        myD = {}
        content = self.__processTemplate('openeye_mcs/table_header_tmplt.html', myD)
        #
        content += self.__processList('Match list:', self.__matchList)
        content += self.__processList('Extra list:', self.__extraList)
        content += self.__processList('Missing list:', self.__missingList)
        return content
        #

    def MatchHtmlText(self):
        instId = str(self.__reqObj.getValue('instanceid'))
        compId = str(self.__reqObj.getValue('compid'))
        #
        compObj = CompUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

        refPath = os.path.join(self.__sessionPath, 'search', instId, instId + '.comp.cif')
        coorPath = os.path.join(self.__sessionPath, 'search', instId, instId + '.merge.cif')
        fitPath = compObj.getTemplateFile(compId)
        imagePath = os.path.join(self.__sessionPath, 'search', instId, instId + '_' + compId + '.png')
        self.__MCSAlignPairDepict(refPath, fitPath, imagePath)
        #
        myD = {}
        myD['pdbid'] = self.__pdbId
        myD['identifier'] = str(self.__reqObj.getValue('identifier'))
        myD['title'] = self.__title
        myD['label'] = self.__labels[instId] + ' vs ' + compId
        myD['2dpath'] = os.path.join(self.__rltvSessionPath, 'search', instId, instId + '_' + compId + '.png')
        myD['match_list'] = self.__getMatchList(coorPath, fitPath)
        return self.__processTemplate('openeye_mcs/mcs_view_tmplt.html', myD)
        #
