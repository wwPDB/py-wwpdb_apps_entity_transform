##
# File:  ResultDepict.py
# Date:  15-Oct-2012
# Updates:
##
"""
Create HTML depiction for PRD search result summary.

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

from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo
from wwpdb.apps.entity_transform.depict.DepictBase import DepictBase
#


class ResultDepict(DepictBase):
    """ Class responsible for generating HTML depiction of PRD search results.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(ResultDepict, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__siteId = str(self._reqObj.getValue("WWPDB_SITE_ID"))
        self.__crpi = ChemRefPathInfo(siteId=self.__siteId, verbose=verbose, log=log)
        #
        self.__instIds = self._cifObj.getMatchInstIds()
        self.__matchResults = self._cifObj.getMatchResults()

    def getSeqs(self, instId):
        return self._cifObj.getSeq(instId)

    def DoRenderResultPage(self, instId):
        if instId:
            return self.__processMatch(instId)
        #
        content = ''
        for instId in self.__instIds:
            if instId.startswith('merge'):
                continue
            #
            myD = {}
            myD['label'] = self._cifObj.getLabel(instId)
            myD['sequence'] = self.getSeqs(instId)
            content += self._processTemplate('result_view/all_individual_header_tmplt.html', myD)
            content += self.__processMatch(instId)
        return content

    def DoRenderUpdatePage(self):
        content = ''
        count = 0
        for instId in self.__instIds:
            if instId.startswith('merge') or ('graph' not in self.__matchResults[instId]):
                continue
            #
            myD = {}
            myD['label'] = self._cifObj.getLabel(instId)
            myD['id'] = 'id_' + str(count)
            myD['value'] = instId
            myD['sequence'] = self.getSeqs(instId)
            content += self._processTemplate('update_form/update_header_tmplt.html', myD)
            content += self.__processUpdate(instId, self.__matchResults[instId]['graph'], count)
            count += 1
        #
        content += '<input type="hidden" name="count" value="' + str(count) + '" />\n'
        return content

    def DoRenderInputPage(self):
        content = ''
        count = 0
        allInstIds = self._cifObj.getAllInstIds()
        for instId in allInstIds:
            if instId.startswith('merge') or self._cifObj.getLinkageInfo(instId) == 'big_polymer':
                continue
            #
            myD = {}
            myD['label'] = self._cifObj.getLabel(instId)
            myD['sequence'] = self.getSeqs(instId)
            myD['id'] = 'id_' + str(count)
            myD['value'] = instId
            myD['user_defined_id'] = 'user_defined_id_' + str(count)
            content += self._processTemplate('update_form/row_input_tmplt.html', myD)
            count += 1
        #
        content += '<input type="hidden" name="count" value="' + str(count) + '" />\n'
        return content

    def DoRenderSplitPage(self):
        form_data = ''
        split_polymer_residue_list = self._cifObj.getValueList('pdbx_split_polymer_residue_info')
        for d in split_polymer_residue_list:
            if 'instance_id' not in d:
                continue
            #
            form_data += '<tr>'
            form_data += '<td><input type="radio" name="split_polymer_residue" value="' + d['instance_id'] + '" /></td>'
            for val in d['instance_id'].split('_'):
                form_data += '<td>' + val + '</td>'
            #
            myD = {}
            myD['sessionid'] = self._sessionId
            myD['identifier'] = self._identifier
            myD['pdbid'] = self._pdbId
            myD['instanceid'] = d['instance_id']
            myD['label'] = d['instance_id']
            myD['focus'] = d['focus']
            form_data += '<td>' + self._processTemplate('summary_view/3d_view_tmplt.html', myD) + '</td>'
            form_data += '</tr>\n'
        #
        return form_data

    def DoRenderMergePage(self):
        form_data = ''
        count = 0
        allInstIds = self._cifObj.getAllInstIds()
        for instId in allInstIds:
            if not instId.startswith('merge'):
                continue
            #
            myD = {}
            myD['sessionid'] = self._sessionId
            myD['identifier'] = self._identifier
            myD['pdbid'] = self._pdbId
            myD['instanceid'] = instId
            myD['label'] = self._cifObj.getLabel(instId)
            myD['focus'] = self._cifObj.getFocus(instId)
            myD['residues'] = self.getSeqs(instId)
            myD['id'] = 'id_' + str(count)
            myD['value'] = instId
            myD['user_defined_id'] = 'user_defined_id_' + str(count)
            myD['3d_view'] = self._processTemplate('summary_view/3d_view_tmplt.html', myD)
            myD['launch_ligand_editor'] = ''
            if self._cifObj.getLinkageInfo(instId) == 'linked':
                myD['launch_ligand_editor'] = self._processTemplate('summary_view/editor_link_tmplt.html', myD)
            elif self._cifObj.getLinkageInfo(instId) == 'not linked':
                myD['launch_ligand_editor'] = 'not linked'
            #
            form_data += self._processTemplate('update_form/update_merge_polymer_residue_instance_header_tmplt.html', myD)
            #
            if instId in self.__matchResults and 'graph' in self.__matchResults[instId]:
                form_data += self._processTemplate('update_form/update_merge_polymer_residue_match_header_tmplt.html', {})
                for d in self.__matchResults[instId]['graph']:
                    myD['match_id'] = 'match_id_' + str(count)
                    myD['selection'] = instId + ',' + d['ccid']
                    myD['ccid'] = d['ccid']
                    myD['cstatus'] = self.__getStatus(d['ccid'])
                    myD['value'] = d['value']
                    form_data += self._processTemplate('update_form/update_merge_polymer_residue_match_row_tmplt.html', myD)
                #
            #
            count += 1
        #
        form_data += '<input type="hidden" name="count" value="' + str(count) + '" />\n'
        return form_data

    def __processMatch(self, instId):
        if instId not in self.__matchResults:
            return ''
        #
        content = ''
        dic = self.__matchResults[instId]
        if 'graph' in dic:
            content += self._processTemplate('result_view/graph_match_header.html', {})
            content += self.__processHit(instId, dic['graph'])
        if 'sequence' in dic:
            content += self._processTemplate('result_view/sequence_similarity_header.html', {})
            content += self.__processHit(instId, dic['sequence'])
        return content

    def __processHit(self, instId, hlist):
        content = ''
        for d in hlist:
            myD = {}
            myD['value'] = d['value']
            myD['instanceid'] = instId
            myD['sessionid'] = self._sessionId
            myD['identifier'] = self._identifier
            #
            if 'sequence' in d:
                myD['sequence'] = d['sequence']
            else:
                myD['sequence'] = ''
            #
            if 'prdid' in d and 'ccid' in d:
                myD['prdid'] = d['prdid']
                myD['pstatus'] = self.__getStatus(d['prdid'])
                myD['ccid'] = d['ccid']
                myD['cstatus'] = self.__getStatus(d['ccid'])
                myD['compid'] = d['ccid']
                content += self._processTemplate('result_view/row_with_prdid_ccid_tmplt.html', myD)
            elif 'prdid' in d:
                myD['prdid'] = d['prdid']
                myD['pstatus'] = self.__getStatus(d['prdid'])
                myD['compid'] = d['prdid']
                content += self._processTemplate('result_view/row_with_prdid_tmplt.html', myD)
            elif 'ccid' in d:
                myD['ccid'] = d['ccid']
                myD['cstatus'] = self.__getStatus(d['ccid'])
                myD['compid'] = d['ccid']
                content += self._processTemplate('result_view/row_with_ccid_tmplt.html', myD)
                #
            #
        #
        return content

    def __processUpdate(self, instId, mlist, count):
        content = self._processTemplate('update_form/graph_match_selection_header.html', {})
        #
        for d in mlist:
            myD = {}
            myD['value'] = d['value']
            myD['id'] = 'match_id_' + str(count)
            #
            if 'sequence' in d:
                myD['sequence'] = d['sequence']
            else:
                myD['sequence'] = ''
            #
            if 'prdid' in d and 'ccid' in d:
                myD['prdid'] = d['prdid']
                myD['pstatus'] = self.__getStatus(d['prdid'])
                myD['ccid'] = d['ccid']
                myD['cstatus'] = self.__getStatus(d['ccid'])
                myD['selection'] = instId + ',' + d['ccid']
                content += self._processTemplate('update_form/row_prdid_ccid_tmplt.html', myD)
            elif 'prdid' in d:
                myD['prdid'] = d['prdid']
                myD['pstatus'] = self.__getStatus(d['prdid'])
                myD['selection'] = instId + ',' + d['prdid']
                content += self._processTemplate('update_form/row_prdid_tmplt.html', myD)
            elif 'ccid' in d:
                myD['ccid'] = d['ccid']
                myD['cstatus'] = self.__getStatus(d['ccid'])
                myD['selection'] = instId + ',' + d['ccid']
                content += self._processTemplate('update_form/row_ccid_tmplt.html', myD)
                #
            #
        #
        return content

    def __getStatus(self, cid):
        sourcefile = ''
        category = ''
        item = ''

        if cid[:4] == 'PRD_':
            sourcefile = self.__crpi.getFilePath(cid, "PRD")
            category = 'pdbx_reference_molecule'
            item = 'release_status'
        else:
            sourcefile = self.__crpi.getFilePath(cid, "CC")
            category = 'chem_comp'
            item = 'pdbx_release_status'
        #
        if not sourcefile:
            return ''
        if not os.access(sourcefile, os.F_OK):
            return ''
        #
        cf = mmCIFUtil(filePath=sourcefile)
        status = cf.GetSingleValue(category, item)
        return status
