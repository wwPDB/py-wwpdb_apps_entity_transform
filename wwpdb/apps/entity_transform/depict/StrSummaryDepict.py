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
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys

from wwpdb.apps.entity_transform.depict.DepictBase import DepictBase
from wwpdb.apps.entity_transform.utils.LinkUtil import LinkUtil
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
        text = "<ul>\n"
        #
        if self.__entities:
            text += self.__depictionList("polymer", "Polymers", self.__depictionEntity())
        elif self.__chain_ids:
            text += self.__depictionList("polymer", "Polymers", self.__depictionChain())
        #
        if self.__ligands:
            text += self.__depictionList("ligand", "Non-polymers", self.__depictionLigand())
        #
        if self.__groups:
            text += self.__depictionList("group", "Connected residues(Groups)", self.__depictionGroup())
        #
        if self._pdbId and self._pdbId != "unknown":
            text += '<li><a class="fltlft" href="/service/entity/download_file?struct=yes&sessionid=' + self._sessionId + "&identifier=" \
                + self._identifier + "&pdbid=" + self._pdbId + '" target="_blank"> Download Files </a></li>\n'
        #
        text += '<li><a class="fltlft" href="https://rcsbpdb.atlassian.net/wiki/spaces/WT/pages/2375385215/Protein+Modifications+Annotation+Documentation" target="_blank"> View PCM/PTM Documentation </a></li>\n'  # noqa: E501
        #
        text += "</ul>\n"
        return text

    def __readEntityData(self):
        dlist = self._cifObj.getValueList('entity_poly')
        if not dlist:
            return
        #
        for d in dlist:
            if 'entity_id' not in d:
                continue
            #
            dic = {}
            for item in ('entity_id', 'pdbx_strand_id', 'name'):
                if item in d:
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
            if 'pdb_chain_id' in d:
                self.__chain_ids.append(d['pdb_chain_id'])
            #
        #

    def __readLigandData(self):
        dlist = self._cifObj.getValueList('pdbx_nonpoly_scheme')
        if not dlist:
            return
        #
        for d in dlist:
            # if (not d.has_key('pdbx_strand_id')) or (not d.has_key('mon_id')) or (not d.has_key('pdb_seq_num')):
            if ('mon_id' not in d) or ('pdb_seq_num' not in d):
                continue
            #
            llist = []
            llist.append(d['mon_id'])
            if 'pdbx_strand_id' in d:
                llist.append(d['pdbx_strand_id'])
            else:
                llist.append('')
            #
            llist.append(d['pdb_seq_num'])
            if 'pdb_ins_code' in d:
                llist.append(d['pdb_ins_code'])
            else:
                llist.append('')
            #
            self.__ligands.append(llist)
        #

    def __readGroupData(self):
        dlist = self._cifObj.getValueList('pdbx_group_list')
        if not dlist:
            return
        #
        for d in dlist:
            if 'component_ids' in d:
                self.__groups.append(d['component_ids'])
            #
        #

    def __readLinkData(self):
        linkutil = LinkUtil(cifObj=self._cifObj, verbose=self._verbose, log=self._lfh)
        self.__links = linkutil.getLinks()

    def __depictionList(self, listId, listText, listContent):
        myD = {}
        myD["id"] = listId
        myD["arrow"] = "ui-icon-circle-arrow-e"
        myD["text"] = listText
        myD["display"] = "none"
        myD["image2d"] = ""
        myD["list"] = listContent
        return "<li>\n" + self._processTemplate("summary_view/expand_list_tmplt.html", myD) + "</li>\n"

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
            if 'pdbx_strand_id' in d:
                list = d['pdbx_strand_id'].split(',')  # pylint: disable=redefined-builtin
                text += '<td>\n'
                for v in list:  # pylint: disable=redefined-builtin
                    text += '<input type="checkbox" name="chain" value="' + v + '" /> ' + v + ' &nbsp; &nbsp; <input type="text" name="chain_' + v \
                        + '" size="5" value="" />  <br/>\n'
                text += '</td>\n'
                #
                text += '<td>\n'
                for v in list:
                    if v in self.__links:
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
            if 'name' in d:
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
            if v in self.__links:
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
        text += '<th>Selection/<br/>User Defined Group ID<br/><input id="ligand_select_all" value="Select All" type="button" onClick="select_ligand(' \
            + "'ligand_select_all'" + ');" /></th>\n'
        text += '<th>3 Letter Code</th>\n'
        text += '<th>Chain ID</th>\n'
        text += '<th>ResNum</th>\n'
        text += '<th>InsertCode</th>\n'
        text += '<th>Links</th>\n'
        text += '</tr>\n'
        #
        for liglist in self.__ligands:
            ligand_id = liglist[1] + '_' + liglist[0] + '_' + liglist[2] + '_' + liglist[3]
            text += '<tr>\n'
            text += '<td><input type="checkbox" name="ligand" value="' + ligand_id + '" />' + ' &nbsp; &nbsp; <input type="text" name="ligand_' \
                + ligand_id + '" size="5" value="" /> </td>\n'
            for v in liglist:
                text += '<td> ' + v + ' </td>\n'
            #
            if ligand_id in self.__links:
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
            group = str(count) + ',' + v
            text += '<tr>\n'
            label = 'GROUP_' + str(count)
            text += '<td><input type="checkbox" name="group" value="' + group + '" /> ' + label + ' </td>\n'
            text += '<td><input type="text" name="group_' + v + '" size="5" value="" /> </td>\n'
            #
            label = ''
            glist = v.split(',')
            for val in glist:
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
            if v in self.__links:
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
