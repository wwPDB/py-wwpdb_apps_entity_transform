##
# File:  DepictUtil.py
# Date:  28-Apr-2014
# Updates:
##
"""
PRD Depiction Utility Class

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

from wwpdb.apps.entity_transform.prd.HtmlUtil import HtmlUtil


class DepictUtil(object):
    def __init__(self):
        """
        """
        self.__htmlUtil = HtmlUtil()

    def __getValue(self, d, lists):
        """
        """
        vd = {}
        for tlist in lists:
            vd[tlist[0]] = ''
            if tlist[1] in d:
                vd[tlist[0]] = d[tlist[1]]
            #
        #
        return vd

    def __getSourceRow(self, vd, count, entity_list):
        """
        """
        tr = self.__htmlUtil.addTD(self.__htmlUtil.addSelect('entityid_' + str(count), vd['ref_id'], entity_list)) \
            + self.__htmlUtil.addSpanTD('3', self.__htmlUtil.addInput('text', 'orgsci_' + str(count), vd['src_name'], self.__htmlUtil.getSize(50, vd['src_name']), '')) \
            + self.__htmlUtil.addTD(self.__htmlUtil.addInput('text', 'taxid_' + str(count), vd['taxid'], self.__htmlUtil.getSize(15, vd['taxid']), '')) \
            + self.__htmlUtil.addSpanTD('2', self.__htmlUtil.addInput('text', 'source_' + str(count), vd['source'], self.__htmlUtil.getSize(30, vd['source']), '')) \
            + self.__htmlUtil.addSpanTD('2', self.__htmlUtil.addInput('text', 'sourceid_' + str(count), vd['source_id'], self.__htmlUtil.getSize(30, vd['source_id']), '')) \
            + self.__htmlUtil.addTD(self.__htmlUtil.addInput('text', 'natname_' + str(count), vd['db_name'], self.__htmlUtil.getSize(15, vd['db_name']), '')) \
            + self.__htmlUtil.addTD(self.__htmlUtil.addInput('text', 'natcode_' + str(count), vd['db_code'], self.__htmlUtil.getSize(15, vd['db_code']), ''))
        return tr

    def __findMissingResidue(self, d, missing_residue, item_list):
        """
        """
        v_list = []
        for item in item_list:
            v = ''
            if item in d:
                v = d[item]
            #
            v_list.append(v)
        #
        idx = '_'.join(v_list)
        if idx in missing_residue:
            return True
        else:
            return False
        #

    def DepictComponentList(self, dlist):
        """ Depict pdbx_reference_entity_list category
        """
        text = ''
        if not dlist:
            return text
        # fmt:off
        lists = [['comp_id', 'component_id' ],  # noqa: E202,E241
                 ['ref_id',  'ref_entity_id'],  # noqa: E202,E241
                 ['type',    'type'         ],  # noqa: E202,E241
                 ['detail',  'details'      ]]  # noqa: E202,E241
        # fmt:on
        for d in dlist:
            vd = self.__getValue(d, lists)
            tr = self.__htmlUtil.addTD(vd['comp_id']) + self.__htmlUtil.addTD(vd['ref_id']) \
                + self.__htmlUtil.addTD(vd['type']) \
                + self.__htmlUtil.addSpanTD('2',
                                            self.__htmlUtil.addInput('text', 'detailid_' + vd['comp_id'], vd['detail'],
                                                                     self.__htmlUtil.getSize(50, vd['detail']), ''))
            text += self.__htmlUtil.addTR(tr)
        #
        return text

    def DepictSourceInfo(self, slist, row, entity_list):
        """ Depict pdbx_reference_entity_src_nat category
        """
        # fmt: off
        lists = [['ref_id',    'ref_entity_id'       ],  # noqa: E202,E241
                 ['src_name',  'organism_scientific' ],  # noqa: E202,E241
                 ['taxid',     'taxid'               ],  # noqa: E202,E241
                 ['source',    'source'              ],  # noqa: E202,E241
                 ['source_id', 'source_id'           ],  # noqa: E202,E241
                 ['db_name',   'db_name'             ],  # noqa: E202,E241
                 ['db_code',   'db_code'             ]]  # noqa: E202,E241
        # fmt: on
        #
        text = ''
        count = 0
        for d in slist:
            vd = self.__getValue(d, lists)
            if (not vd['ref_id']) and (vd['src_name'] or vd['taxid'] or vd['source'] or vd['source_id']):
                vd['ref_id'] = '.'
            #
            tr = self.__getSourceRow(vd, count, entity_list)
            text += self.__htmlUtil.addTR(tr)
            count += 1
        #
        if count < row:
            vd = {}
            for tlist in lists:
                vd[tlist[0]] = ''
            #
            for i in range(count, row):
                tr = self.__getSourceRow(vd, i, entity_list)
                text += self.__htmlUtil.addTR(tr)
            #
        #
        return text

    def DepictPolymerInfo(self, dlist, aalist):
        """ Depict pdbx_reference_entity_poly_seq category
        """
        text = ''
        if not dlist:
            return text
        #
        # fmt: off
        lists = [['ref_id',        'ref_entity_id'],  # noqa: E202,E241
                 ['num',           'num'          ],  # noqa: E202,E241
                 ['mon_id',        'mon_id'       ],  # noqa: E202,E241
                 ['parent_mon_id', 'parent_mon_id'],  # noqa: E202,E241
                 ['observed',      'observed'     ]]  # noqa: E202,E241
        # fmt: on
        for d in dlist:
            vd = self.__getValue(d, lists)
            if vd['observed'] == 'N':
                tr = self.__htmlUtil.addColorTD(vd['ref_id'], '#FF6699') + self.__htmlUtil.addColorTD(vd['mon_id'], '#FF6699') \
                    + self.__htmlUtil.addColorTD(vd['num'], '#FF6699') + self.__htmlUtil.addColorTD(vd['observed'], '#FF6699') \
                    + self.__htmlUtil.addTD(self.__htmlUtil.addSelect('polymerid_' + vd['ref_id'] + '_' + vd['num'], vd['parent_mon_id'], aalist)) \
                    + self.__htmlUtil.addTD('')
            else:
                tr = self.__htmlUtil.addTD(vd['ref_id']) + self.__htmlUtil.addTD(vd['mon_id']) \
                    + self.__htmlUtil.addTD(vd['num']) + self.__htmlUtil.addTD(vd['observed']) \
                    + self.__htmlUtil.addTD(self.__htmlUtil.addSelect('polymerid_' + vd['ref_id'] + '_' + vd['num'], vd['parent_mon_id'], aalist)) \
                    + self.__htmlUtil.addTD('')
            #
            text += self.__htmlUtil.addTR(tr)
        #
        return text

    def DepictLinkInfo(self, category, dlist, missing_residue):
        """ Depict pdbx_reference_entity_poly_link/pdbx_reference_entity_link category
        """
        bondorder = ['', 'sing', 'doub', 'trip', 'quad', 'arom', 'poly', 'delo', 'pi']
        title = 'Polymer Linkage Information'
        key = 'polylink'
        atomkey1 = 'atom1'
        atomkey2 = 'atom2'
        items = ['ref_entity_id', 'component_id', 'comp_id_1', 'entity_seq_num_1', 'atom_id_1',
                 'ref_entity_id', 'component_id', 'comp_id_2', 'entity_seq_num_2', 'atom_id_2']
        if category == 'pdbx_reference_entity_link':
            title = 'Entity Linkage Information'
            key = 'entitylink'
            items = ['ref_entity_id_1', 'component_1', 'comp_id_1', 'entity_seq_num_1', 'atom_id_1',
                     'ref_entity_id_2', 'component_2', 'comp_id_2', 'entity_seq_num_2', 'atom_id_2']
        #
        text = '<tr><th style="text-align:left" colspan="11"> ' + title + ' </th></tr>\n'
        text += '<tr>\n'
        text += '<th style="text-align:left">Entity ID 1</th>\n'
        text += '<th style="text-align:left">Component ID 1</th>\n'
        text += '<th style="text-align:left">Residue 1</th>\n'
        text += '<th style="text-align:left">Numbering 1</th>\n'
        text += '<th style="text-align:left">Atom 1</th>\n'
        text += '<th style="text-align:left">Entity ID 2</th>\n'
        text += '<th style="text-align:left">Component ID 2</th>\n'
        text += '<th style="text-align:left">Residue 2</th>\n'
        text += '<th style="text-align:left">Numbering 2</th>\n'
        text += '<th style="text-align:left">Atom 2</th>\n'
        text += '<th style="text-align:left">Bond Order</th>\n'
        text += '</tr>\n'
        #
        for d in dlist:
            list = []  # pylint: disable=redefined-builtin
            list.append(items[0])
            list.append(items[3])
            list.append(items[2])
            flag = self.__findMissingResidue(d, missing_residue, list)
            if not flag:
                list = []
                list.append(items[5])
                list.append(items[8])
                list.append(items[7])
                flag = self.__findMissingResidue(d, missing_residue, list)
            text += '<tr>\n'
            #
            for item in items:
                value = ''
                if item in d:
                    value = d[item]
                #
                if flag:
                    if item == 'atom_id_1':
                        text += self.__htmlUtil.addTD(self.__htmlUtil.addText(atomkey1 + '_' + d['link_id'], value, self.__htmlUtil.getSize(15, value)))
                    elif item == 'atom_id_2':
                        text += self.__htmlUtil.addTD(self.__htmlUtil.addText(atomkey2 + '_' + d['link_id'], value, self.__htmlUtil.getSize(15, value)))
                    else:
                        text += self.__htmlUtil.addColorTD(value, '#FF6699')
                else:
                    text += self.__htmlUtil.addTD(value)
                #
            #
            value = ''
            if 'value_order' in d:
                value = d['value_order']
            text += self.__htmlUtil.addTD(self.__htmlUtil.addSelect(key + '_' + d['link_id'], value, bondorder))
            text += '</tr>\n'
        #
        text += '<tr><td style="border-style:none" colspan="11">&nbsp;</td></tr>\n'
        return text

    def DepictDbrefInfo(self, entityList, dbinfo):
        """ Depict DBREF info
        """
        text = ''
        for d in entityList:
            db_name = ''
            db_code = ''
            if d in dbinfo:
                if 'db_name' in dbinfo[d]:
                    db_name = dbinfo[d]['db_name']
                #
                if 'db_code' in dbinfo[d]:
                    db_code = dbinfo[d]['db_code']
                #
            #
            tr = self.__htmlUtil.addTD(d) \
                + self.__htmlUtil.addTD(self.__htmlUtil.addInput('text', 'dbname_' + d, db_name, self.__htmlUtil.getSize(15, db_name), '')) \
                + self.__htmlUtil.addTD(self.__htmlUtil.addInput('text', 'dbcode_' + d, db_code, self.__htmlUtil.getSize(15, db_code), '')) \
                + self.__htmlUtil.addTD('') + self.__htmlUtil.addTD('')
            text += self.__htmlUtil.addTR(tr)
        #
        return text

    def DepictAuditInfo(self, dlist, enumList):
        """ Depict pdbx_prd_audit category
        """
        lists = [['date',        'date'        ],  # noqa: E202,E241
                 ['annotator',   'annotator'   ],  # noqa: E202,E241
                 ['action_type', 'action_type' ],  # noqa: E202,E241
                 ['details',     'details'     ]]  # noqa: E202,E241
        #
        text = ''
        count = 0
        for d in dlist:
            vd = self.__getValue(d, lists)
            #
            tr = self.__htmlUtil.addTD(vd['date']) + self.__htmlUtil.addTD(vd['annotator']) \
                + self.__htmlUtil.addSpanTD('2', self.__htmlUtil.addSelect('actiontype_' + str(count), vd['action_type'], enumList)) \
                + self.__htmlUtil.addSpanTD('7', self.__htmlUtil.addInput('text', 'auditdetails_' + str(count),
                                                                          vd['details'], self.__htmlUtil.getSize(150, vd['details']), ''))
            text += self.__htmlUtil.addTR(tr)
            count += 1
            #
        #
        return text
