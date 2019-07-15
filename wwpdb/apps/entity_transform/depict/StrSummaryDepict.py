##
# File:  StrSummaryDepict.py
# Date:  29-Nov-2012
# Updates:
##
"""
Create HTML depiction for structure summary.

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
from wwpdb.apps.entity_transform.utils.LinkUtil    import LinkUtil
#

class StrSummaryDepict(DepictBase):
    """ Class responsible for generating HTML depiction of Structure Summary.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(StrSummaryDepict, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__entities = []
        self.__readEntityData()
        #
        self.__chain_ids = []
        self.__readChainData()
        #
        self.__ligands = []
        self.__readLigandData()
        #
        self.__groups = []
        self.__readGroupData()
        #
        self.__links = {}
        self.__readLinkData()

    def DoRenderSummaryPage(self):
        text = '<ul>\n'
        #
        if self.__entities:
            myD = {}
            myD['id']   = 'polymer'
            myD['text'] = 'Polymers'
            myD['list'] = self.__depictionEntity()
            text += '<li>\n' + self._processTemplate('summary_view/expand_list_tmplt.html', myD) + '</li>\n'
        elif self.__chain_ids:
            myD = {}
            myD['id']   = 'polymer'
            myD['text'] = 'Polymers'
            myD['list'] = self.__depictionChain()
            text += '<li>\n' + self._processTemplate('summary_view/expand_list_tmplt.html', myD) + '</li>\n'
        #
        if self.__ligands:
            myD = {}
            myD['id']   = 'ligand'
            myD['text'] = 'Non-polymers'
            myD['list'] = self.__depictionLigand()
            text += '<li>\n' + self._processTemplate('summary_view/expand_list_tmplt.html', myD) + '</li>\n'
        #
        if self.__groups:
            myD = {}
            myD['id']   = 'group'
            myD['text'] = 'Connected residues(Groups)'
            myD['list'] = self.__depictionGroup()
            text += '<li>\n' + self._processTemplate('summary_view/expand_list_tmplt.html', myD) + '</li>\n'
        #
        if self._pdbId and self._pdbId != 'unknown':
            text += '<li><a class="fltlft" href="/service/entity/download_file?struct=yes&sessionid=' + self._sessionId + '&identifier=' \
                  + self._identifier + '&pdbid=' + self._pdbId + '" target="_blank"> Download Files </a></li>\n'
        #
        text += '</ul>\n'
        return text

    def __readEntityData(self):
        dlist = self._cifObj.getValueList('entity_poly')
        if not dlist:
            return
        #
        for d in dlist:
            if not d.has_key('entity_id'):
                continue
            #
            dic = {}
            for item in ('entity_id', 'pdbx_strand_id', 'name'):
                if d.has_key(item):
                    dic[item] = d[item]
                #
            #
            if not dic:
                continue
            #
            self.__entities.append(dic)
            #
        #

    def __readChainData(self):
        dlist = self._cifObj.getValueList('pdbx_polymer_info')
        if not dlist:
            return
        #
        for d in dlist:
            if d.has_key('pdb_chain_id'):
                self.__chain_ids.append(d['pdb_chain_id'])
            #
        #

    def __readLigandData(self):
        dlist = self._cifObj.getValueList('pdbx_nonpoly_scheme')
        if not dlist:
            return
        #
        for d in dlist:
            #if (not d.has_key('pdbx_strand_id')) or (not d.has_key('mon_id')) or (not d.has_key('pdb_seq_num')):
            if (not d.has_key('mon_id')) or (not d.has_key('pdb_seq_num')):
                continue
            #
            list = []
            list.append(d['mon_id'])
            if d.has_key('pdbx_strand_id'):
                list.append(d['pdbx_strand_id'])
            else:
                list.append('')
            #
            list.append(d['pdb_seq_num'])
            if d.has_key('pdb_ins_code'):
                list.append(d['pdb_ins_code'])
            else:
                list.append('')
            #
            self.__ligands.append(list)
        #

    def __readGroupData(self):
        dlist = self._cifObj.getValueList('pdbx_group_list')
        if not dlist:
            return
        #
        for d in dlist:
            if d.has_key('component_ids'):
                self.__groups.append(d['component_ids'])
            #
        #

    def __readLinkData(self):
        linkutil = LinkUtil(cifObj=self._cifObj, verbose=self._verbose, log=self._lfh)
        self.__links = linkutil.getLinks()

    def __depictionEntity(self):
        text = '<table>\n'
        text += '<tr>\n'
        text += '<th>Entity ID</th>\n'
        text += '<th>Chain ID/<br/>User Defined Group ID</th>\n'
        text += '<th>Links</th>\n'
        text += '<th>Molecule Name</th>\n'
        text += '</tr>\n'
        for d in self.__entities:
            text += '<tr>\n'
            text += '<td><input type="checkbox" name="entity" value="' + d['entity_id'] + '" /> ' + d['entity_id'] + ' </td>\n'
            if d.has_key('pdbx_strand_id'):
                list = d['pdbx_strand_id'].split(',')
                text += '<td>\n'
                for v in list:
                    text += '<input type="checkbox" name="chain" value="' + v + '" /> ' + v + ' &nbsp; &nbsp; <input type="text" name="chain_' + v \
                          + '" size="5" value="" />  <br/>\n'
                text += '</td>\n'
                #
                text += '<td>\n'
                for v in list:
                    if self.__links.has_key(v):
                        text += '<a class="fltlft" href="/service/entity/link_view?sessionid=' + self._sessionId + '&pdbid=' + self._pdbId + '&identifier=' \
                              + self._identifier + '&id=' + v + '" target="_blank"> ' + 'View Chain ' + v + "'s Link </a> <br/>\n"
                    else:
                        text += ' &nbsp; '
                    #
                #
                text += '</td>\n'
            else:
                text += '<td> &nbsp; &nbsp; &nbsp; </td>\n'
                text += '<td> &nbsp; &nbsp; &nbsp; </td>\n'
            #
            if d.has_key('name'):
                text += '<td> ' + d['name'] + ' </td>\n'
            else:
                text += '<td> &nbsp; &nbsp; &nbsp; </td>\n'
            #
            text += '</tr>\n'
        #
        text += '</table>\n'
        return text
        #

    def __depictionChain(self):
        text = '<table>\n'
        text += '<tr>\n'
        text += '<th>Chain ID</th>\n'
        text += '<th>User Defined<br/> Group ID</th>\n'
        text += '<th>Links</th>\n'
        text += '<th style="text-align:left;border-style:none" > &nbsp; &nbsp; &nbsp; </th>\n'
        text += '<th style="text-align:left;border-style:none" > &nbsp; &nbsp; &nbsp; </th>\n'
        text += '</tr>\n'
        for v in self.__chain_ids:
            text += '<tr>\n'
            text += '<td><input type="checkbox" name="chain" value="' + v + '" /> ' + v + ' </td>\n'
            text += '<td><input type="text" name="chain_' + v + '" size="5" value="" /> </td>\n'
            if self.__links.has_key(v):
                text += '<td><a class="fltlft" href="/service/entity/link_view?sessionid=' + self._sessionId + '&pdbid=' + self._pdbId + '&identifier=' \
                      + self._identifier + '&id=' + v + '" target="_blank"> ' + 'View Link' + ' </a></rd>\n'
            else:
                text += '<td> &nbsp; &nbsp; &nbsp; </td>\n'
            #
            text += '<td style="text-align:left;border-style:none" > &nbsp; &nbsp; &nbsp; </td>\n'
            text += '<td style="text-align:left;border-style:none" > &nbsp; &nbsp; &nbsp; </td>\n'
            text += '</tr>\n'
        #
        text += '</table>\n'
        return text

    def __depictionLigand(self):
        text = '<table>\n'
        text += '<tr>\n'
        text += '<th>Selection/<br/>User Defined Group ID</th>\n'
        text += '<th>3 Letter Code</th>\n'
        text += '<th>Chain ID</th>\n'
        text += '<th>ResNum</th>\n'
        text += '<th>InsertCode</th>\n'
        text += '<th>Links</th>\n'
        text += '</tr>\n'
        #
        for list in self.__ligands:
            ligand_id = list[1] + '_' + list[0] + '_' + list[2] + '_' + list[3]
            text += '<tr>\n'
            text += '<td><input type="checkbox" name="ligand" value="' + ligand_id + '" />' + ' &nbsp; &nbsp; <input type="text" name="ligand_' \
                  + ligand_id + '" size="5" value="" /> </td>\n'
            for v in list:
                text += '<td> ' + v + ' </td>\n'
            #
            if self.__links.has_key(ligand_id):
                text += '<td><a class="fltlft" href="/service/entity/link_view?sessionid=' + self._sessionId + '&pdbid=' + self._pdbId \
                      + '&identifier=' + self._identifier + '&id=' + ligand_id + '" target="_blank"> ' + 'View Link' + ' </a></rd>\n'
            else:
                text += '<td> &nbsp; &nbsp; &nbsp; </td>\n'
            #
            text += '</tr>\n'
        #
        text += '</table>\n'
        return text

    def __depictionGroup(self):
        text = '<table>\n'
        text += '<tr>\n'
        text += '<th> &nbsp; &nbsp; &nbsp; </th>\n'
        text += '<th>User Defined<br /> Group ID</th>\n'
        text += '<th colspan="2">Description</th>\n'
        text += '<th>Links</th>\n'
        text += '</tr>\n'
        count = 1
        for v in self.__groups:
            group = str(count) + ',' +  v
            text += '<tr>\n'
            label = 'GROUP_' + str(count)
            text += '<td><input type="checkbox" name="group" value="' + group + '" /> ' + label + ' </td>\n'
            text += '<td><input type="text" name="group_' + v + '" size="5" value="" /> </td>\n'
            #
            label = ''
            list = v.split(',')
            for val in list:
                if label:
                    label += ', '
                list1 = val.split('_')
                if len(list1) == 1:
                    label += 'Chain ' + list1[0]
                else:
                    label += 'Residue ' + ' '.join(list1)
                #
            #
            text += '<td colspan="2">' + label + ' </td>\n'
            if self.__links.has_key(v):
                text += '<td><a class="fltlft" href="/service/entity/link_view?sessionid=' + self._sessionId + '&pdbid=' + self._pdbId \
                      + '&identifier=' + self._identifier + '&id=' + group + '" target="_blank"> ' + 'View Link' + ' </a></rd>\n'
            else:
                text += '<td> &nbsp; &nbsp; &nbsp; </td>\n'
            #
            text += '</tr>\n'
            count += 1
        #
        text += '</table>\n'
        return text
