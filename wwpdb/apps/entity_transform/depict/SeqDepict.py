##
# File:  SeqDepict.py
# Date:  11-Dec-2012
# Updates:
##
"""
Create HTML depiction for spliting polymer(s)

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
import string


class SeqDepict(object):
    """ Class responsible for generating HTML depiction of spliting polymer(s).
    """
    _monDict3 = {
        'ALA': 'A',
        'ARG': 'R',
        'ASN': 'N',
        'ASP': 'D',
        'ASX': 'B',
        'CYS': 'C',
        'GLN': 'Q',
        'GLU': 'E',
        'GLX': 'Z',
        'GLY': 'G',
        'HIS': 'H',
        'ILE': 'I',
        'LEU': 'L',
        'LYS': 'K',
        'MET': 'M',
        'PHE': 'F',
        'PRO': 'P',
        'SER': 'S',
        'THR': 'T',
        'TRP': 'W',
        'TYR': 'Y',
        'VAL': 'V',
        'DAL': 'A',
        'DAR': 'R',
        'DSG': 'N',
        'DAS': 'D',
        'DCY': 'C',
        'DGN': 'Q',
        'DGL': 'E',
        'DHI': 'H',
        'DIL': 'I',
        'DLE': 'L',
        'DLY': 'K',
        'MED': 'M',
        'DPN': 'F',
        'DPR': 'P',
        'DSN': 'S',
        'DTH': 'T',
        'DTR': 'W',
        'DTY': 'Y',
        'DVA': 'V',
        'DA': 'A',
        'DC': 'C',
        'DG': 'G',
        'DT': 'T',
        'DU': 'U',
        'DI': 'I',
        'A': 'A',
        'C': 'C',
        'G': 'G',
        'I': 'I',
        'T': 'T',
        'U': 'U',
        'UNK': 'X',
        '.': '.'
    }

    _monDictDNA = {
        '.': '.',
        'A': 'DA',
        'C': 'DC',
        'G': 'DG',
        'I': 'DI',
        'T': 'DT',
        'U': 'DU',
        'X': 'UNK'
    }

    _monDictRNA = {
        '.': '.',
        'A': 'A',
        'C': 'C',
        'G': 'G',
        'I': 'I',
        'T': 'T',
        'U': 'U',
        'X': 'UNK'
    }

    _monDictL = {
        '.': '.',
        'A': 'ALA',
        'R': 'ARG',
        'N': 'ASN',
        'D': 'ASP',
        'B': 'ASX',
        'C': 'CYS',
        'Q': 'GLN',
        'E': 'GLU',
        'Z': 'GLX',
        'G': 'GLY',
        'H': 'HIS',
        'I': 'ILE',
        'L': 'LEU',
        'K': 'LYS',
        'M': 'MET',
        'F': 'PHE',
        'P': 'PRO',
        'S': 'SER',
        'T': 'THR',
        'W': 'TRP',
        'Y': 'TYR',
        'V': 'VAL'
    }

    _monDictD = {
        '.': '.',
        'A': 'DAL',
        'R': 'DAR',
        'N': 'DSG',
        'D': 'DAS',
        'C': 'DCY',
        'Q': 'DGN',
        'E': 'DGL',
        'H': 'DHI',
        'I': 'DIL',
        'L': 'DLE',
        'K': 'DLY',
        'M': 'MED',
        'F': 'DPN',
        'P': 'DPR',
        'S': 'DSN',
        'T': 'DTH',
        'W': 'DTR',
        'Y': 'DTY',
        'V': 'DVA'
    }

    def __init__(self, entityInfo=None, option="split", verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        self.__entityInfo = entityInfo
        self.__option = option
        # self.__verbose = verbose
        # self.__lfh = log
        self.__entityLength = {}
        self.__entityIndices = {}

    def getHtmlText(self):
        html_text = ''
        count = 0
        for infolist in self.__entityInfo:
            polytype = 'polypeptide(L)'
            if infolist[4]:
                polytype = infolist[4]
            #
            seqlist = self.__getSeqList(polytype, infolist[3])
            length = len(seqlist)
            self.__entityLength[str(count) + '_' + infolist[0]] = length
            #
            html_text += self.__depictSummaryTable(count, infolist[0], infolist[1], infolist[2], length, seqlist[0][1], seqlist[length - 1][1])
            if infolist[5]:
                labelList = list(infolist[5])
                if len(labelList) != length:
                    labelList = ["1"] * length
                #
            else:
                labelList = ["1"] * length
            #
            html_text += self.__depictSequence(count, infolist[0], seqlist, labelList)
            if self.__option == "edit":
                html_text += self.__depictEditTable(count, infolist[0])
            else:
                html_text += self.__depictSplitTable(count, infolist[0])
            #
            html_text += '<div class="emptyspace"></div>\n'
            html_text += '<div class="emptyspace"></div>\n'
            count += 1
        #
        return html_text

    def getScriptText(self):
        #

        scriptText = 'var lengthMap = ' + self.__writeToString(obj=self.__entityLength) + ';\n' \
            + 'var indexMap = ' + self.__writeToString(obj=self.__entityIndices) + ';'
        return scriptText

    def __getSeqList(self, polytype, one_letter_seq):
        seqlist = []
        r3 = ''
        inP = False
        for s in one_letter_seq:
            if s in string.whitespace:
                continue
            elif s == '(':
                inP = True
                r3 = ''
            elif s == ')':
                inP = False
                r1 = 'X'
                if r3 in SeqDepict._monDict3:
                    r1 = SeqDepict._monDict3[r3]
                #
                tmplist = []
                tmplist.append(r1)
                tmplist.append(r3)
                seqlist.append(tmplist)
            elif inP:
                r3 += s
            else:
                r3L = self.__getThreeLetterCode(s, polytype)
                tmplist = []
                tmplist.append(s)
                tmplist.append(r3L)
                seqlist.append(tmplist)
            #
        #
        return seqlist

    def __getThreeLetterCode(self, one_letter_code, polytype):
        if polytype == 'polypeptide(L)':
            if one_letter_code in SeqDepict._monDictL:
                return SeqDepict._monDictL[one_letter_code]
        elif polytype == 'polypeptide(D)':
            if one_letter_code in SeqDepict._monDictD:
                return SeqDepict._monDictD[one_letter_code]
        elif polytype == 'polydeoxyribonucleotide':
            if one_letter_code in SeqDepict._monDictDNA:
                return SeqDepict._monDictDNA[one_letter_code]
        elif polytype == 'polyribonucleotide' or polytype == 'polydeoxyribonucleotide/polyribonucleotide hybrid':
            if one_letter_code in SeqDepict._monDictRNA:
                return SeqDepict._monDictRNA[one_letter_code]

        return one_letter_code

    def __depictSummaryTable(self, count, entity_id, chain_ids, mol_name, seq_length, n_res, c_res):
        text = '<div id="summery_table_div_' + str(count) + '">\n'
        text += '<table>\n'
        text += '<tr>\n'
        text += '<th>Entity ID</th>\n'
        text += '<th>Chain ID/Group ID</th>\n'
        text += '<th>Molecule Name</th>\n'
        text += '<th>Terminal Residues</th>\n'
        text += '</tr>\n'
        text += '<tr>\n'
        text += '<td> ' + entity_id + ' </td>\n'
        text += '<td> ' + chain_ids + ' </td>\n'
        text += '<td> ' + mol_name + ' </td>\n'
        text += '<td> N: ' + n_res + ' 1 <br /> C: ' + c_res + ' ' + str(seq_length) + ' </td>\n'
        text += '</tr>\n'
        text += '</table>\n'
        text += '</div>\n'
        text += '<div class="emptyspace"></div>\n'
        #
        text += '<input type="hidden" name="entity" value="' + entity_id + '" />\n'
        text += '<input type="hidden" name="chain_' + entity_id + '" value="' + chain_ids + '" />\n'
        return text

    def __depictSequence(self, count, entity_id, seqList, labelList):
        resNumber = len(seqList)
        resPerLine = 100
        integerLine = int(resNumber / resPerLine)
        remainderLine = resNumber % resPerLine
        lineNumber = integerLine
        if remainderLine != 0:
            lineNumber += 1
        #
        entity_key = str(count) + '_' + entity_id
        #
        # start result div
        text = '<div id="result_' + entity_key + '" class="result">\n'
        #
        resPerBlock = 10
        blockNumber = int(resPerLine / resPerBlock)
        #
        # start empty ul
        text += '<ul class="legend whitebg">\n'
        for j in range(0, blockNumber):
            for k in range(0, resPerBlock):
                text += '<li> </li>\n'
            #
            # add space between block
            text += '<li> </li>\n'
            #
        #
        # end empty ul
        text += '</ul>\n'
        #
        for i in range(0, lineNumber):
            cssClassBg = 'whitebg'
            if i % 2:
                cssClassBg = 'greybg'
            line_key = entity_key + '_' + str(i)
            #
            # start line div
            text += '<div id="line_' + line_key + '" class="' + cssClassBg + '">\n'
            resNumberinLine = resPerLine
            if i == integerLine:
                resNumberinLine = remainderLine
            #
            integerBlock = int(resNumberinLine / resPerBlock)
            remainderBlock = resNumberinLine % resPerBlock
            blockNumber = integerBlock
            if remainderBlock != 0:
                blockNumber += 1
            #
            # start number ul
            text += '<ul class="legend ' + cssClassBg + '">\n'
            for j in range(0, blockNumber):
                if j == integerBlock:
                    continue
                #
                number = i * resPerLine + j * resPerBlock + resPerBlock
                snumber = str(number)
                text_tmp = ''
                for k in range(0, (resPerBlock - len(str(snumber)))):
                    text_tmp += ' '
                text_tmp += str(number)
                for k in text_tmp:
                    text += '<li>' + k + '</li>\n'
                #
                # add space between block
                text += '<li> </li>\n'
                #
            #
            # end empty ul
            text += '</ul>\n'
            #
            # start seq ul
            text += '<ul id="seq_' + line_key + '" class="pickable ' + cssClassBg + '">\n'
            for j in range(0, blockNumber):
                resNumberinBlock = resPerBlock
                if j == integerBlock:
                    resNumberinBlock = remainderBlock
                #
                for k in range(0, resNumberinBlock):
                    idx = i * resPerLine + j * resPerBlock + k
                    currRes = seqList[idx][1] + '_' + str(idx + 1)
                    nextRes = ''
                    if (idx + 1) < resNumber:
                        nextRes = seqList[idx + 1][1] + '_' + str(idx + 2)
                    #
                    if nextRes and (self.__option == "split"):
                        currRes += '_' + nextRes
                    #
                    currCss = "viewres dblclick"
                    if labelList and (labelList[idx] == "1"):
                        currCss += " greenbg"
                    #
                    if entity_key in self.__entityIndices:
                        self.__entityIndices[entity_key][idx + 1] = currRes
                    else:
                        self.__entityIndices[entity_key] = {idx + 1 : currRes}
                    #
                    # text += '<li id="' + entity_key + '_' + currRes + '" class="dblclick viewres">' + seqList[idx][0] + '</li>\n'
                    text += '<li id="' + entity_key + '_' + currRes + '" class="' + currCss + '">' + seqList[idx][0] + '</li>\n'
                #
                # add space between block
                text += '<li> </li>\n'
                #
            #
            # end seq ul
            text += '</ul>\n'
            #
            # start empty ul
            text += '<ul class="legend ' + cssClassBg + '">\n'
            for j in range(0, blockNumber):
                resNumberinBlock = resPerBlock
                if j == integerBlock:
                    resNumberinBlock = remainderBlock
                #
                for k in range(0, resNumberinBlock):
                    text += '<li> </li>\n'
                #
                # add space between block
                text += '<li> </li>\n'
                #
            #
            # end empty ul
            text += '</ul>\n'
            #
            # end line div
            text += '</div>\n'
        #
        # end result div
        text += '</div>\n'
        text += '<div class="emptyspace"></div>\n'
        #
        return text

    def __depictSplitTable(self, count, entity_id):
        entity_key = str(count) + '_' + entity_id
        text = '<div id="split_table_div_' + str(count) + '">\n'
        text += '<table id="split_table_' + entity_key + '">\n'
        text += '<tr>\n'
        text += '<th colspan="5">Split Position between Residues</th>\n'
        text += '</tr>\n'
        text += '<tr>\n'
        text += '<th id="delete_all_' + entity_key + '" colspan="5" class="displaynone"><input type="button" id="delete_all_button_' \
            + entity_key + '" value="Remove All" class="deleteallrows action_button" /></th>\n'
        text += '</tr>\n'
        text += '<tr>\n'
        text += '<th>1st Residue Name</th>\n'
        text += '<th>1st Residue Position</th>\n'
        text += '<th>2nd Residue Name</th>\n'
        text += '<th>2nd Residue Position</th>\n'
        text += '<th>Action</th>\n'
        text += '</tr>\n'
        text += '</table>\n'
        text += '</div>\n'
        text += '<div class="emptyspace"></div>\n'
        return text

    def __depictEditTable(self, count, entity_id):
        entity_key = str(count) + '_' + entity_id
        text = '<div id="edit_table_div_' + str(count) + '">\n'
        text += '<table id="edit_table_' + entity_key + '">\n'
        text += '<tr>\n'
        text += '<th colspan="3">Remove Residue(s)</th>\n'
        text += '</tr>\n'
        text += '<tr>\n'
        text += '<th id="delete_all_' + entity_key + '"colspan="3" class="displaynone"><input type="button" id="delete_all_button_' \
            + entity_key + '" value="Delete All" class="deleteallrows action_button" /></th>\n'
        text += '</tr>\n'
        text += '<tr>\n'
        text += '<th>Residue Name</th>\n'
        text += '<th>Residue Position</th>\n'
        text += '<th>Action</th>\n'
        text += '</tr>\n'
        text += '</table>\n'
        text += '</div>\n'
        text += '<div class="emptyspace"></div>\n'
        return text

    def __writeToString(self, obj=None, delimiter=','):
        text = ''

        if sys.version_info[0] < 3:
            numtypes = (int, long, float)  # noqa: F821  pylint: disable=undefined-variable
            stringtypes = (str, unicode)  # noqa: F821  pylint: disable=undefined-variable
        else:
            numtypes = (int, float)
            stringtypes = (str, bytes)

        if isinstance(obj, bool):
            if obj:
                text += 'true'
            else:
                text += 'false'
            #
        elif isinstance(obj, numtypes):
            text += str(obj)
        elif isinstance(obj, stringtypes):
            text += "'" + str(obj) + "'"
        elif isinstance(obj, (list, tuple)):
            text1 = ''
            for v in obj:
                if text1:
                    text1 += delimiter
                #
                text1 += self.__writeToString(obj=v)
            #
            text += '[' + text1 + ']'
        elif isinstance(obj, dict):
            text1 = ''
            for k, v in obj.items():
                if text1:
                    text1 += delimiter
                #
                text1 += self.__writeToString(obj=k) + ':' + self.__writeToString(obj=v)
            #
            text += '{' + text1 + '}'
        #
        return text
