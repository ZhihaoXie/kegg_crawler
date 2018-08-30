#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# FileName:  link_ko_func_path_infos.py
# Author:    Zhihao Xie  \(#^o^)/
# Date:      2018/4/26 15:29
# Version:   v1.0.0
# CopyRight: Copyright ©Zhihao Xie, All rights reserved.

"""
Note:
    link KEGG KO number and function, pathway, enzyme, module, disease into a big merge table
Output:
    outfile is: kegg_ko_informations.tsv
"""

import sys
import os
import re
from collections import OrderedDict
import time
import shutil


def main():
    if len(sys.argv) <= 1:
        print(__doc__, file=sys.stderr)
        outdir = os.getcwd()
    else:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            print(__doc__)
            print("Usage: python3 {} <outdir>".format(sys.argv[0]))
            sys.exit(1)
        outdir = os.path.abspath(sys.argv[1])

    tmp_dir = os.path.join(outdir, 'temp_'+str(time.time()))
    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)
    os.chdir(tmp_dir)  # change to temp dir

    # get ko enzyme
    # ko:K00001	ec:1.1.1.1
    ko2func = OrderedDict()
    ko2EC = OrderedDict()
    status = os.system('wget -t 30 -c -O ko_ec.tab http://rest.kegg.jp/link/enzyme/ko')
    if status == 0:
        with open("ko_ec.tab") as fh:
            for line in fh:
                if re.search(r'^\s*$', line):
                    continue
                else:
                    fields = line.strip().split("\t")
                    if len(fields) >= 2:
                        ko_number = re.sub(r'^ko:', '', fields[0])
                        ec_number = re.sub('ec:', 'EC:', fields[1])
                        ko2EC.setdefault(ko_number, [])
                        ko2EC[ko_number].extend([ec_number])
    else:
        sys.exit("Error: can't download ko ec.")

    # get ko list
    # ko:K00002	AKR1A1, adh; alcohol dehydrogenase (NADP+) [EC:1.1.1.2]
    status = os.system("wget -t 30 --continue -O ko_list.txt http://rest.kegg.jp/list/ko")
    if status == 0:
        with open("ko_list.txt") as fh:
            for line in fh:
                if not re.search(r'^\s*$', line) and re.match(r'^ko:', line):
                    fields = line.strip().split("\t")
                    ko_number = re.sub(r'^ko:', "", fields[0])
                    ko2func.setdefault(ko_number, "")
                    if re.search(r'\[EC:.*?\]', fields[1]):
                        ec_list = re.findall(r'\[(EC:.*?)\]', fields[1])
                        func_str = re.sub(r'(.*?)\s?\[EC:.*?\]', '\g<1>', fields[1])
                        if len(ec_list) >= 1 and ko_number not in ko2EC:
                            ko2EC.setdefault(ko_number, [])
                            ko2EC[ko_number].extend(ec_list)
                        if func_str != "":
                            ko2func[ko_number] = func_str
                    else:
                        ko2func[ko_number] = fields[1]
    else:
        sys.exit("Error: can't download ko list.\n")

    # get ko pathway
    # ko:K00001	path:map00010
    # path:map00010	Glycolysis / Gluconeogenesis
    ko2path = {}
    os.system("wget -t 30 --continue -O ko_pathway.tab http://rest.kegg.jp/link/pathway/ko")
    os.system("wget -t 30 --continue -O map_name.txt http://rest.kegg.jp/list/pathway")
    if os.path.isfile('ko_pathway.tab') and os.path.getsize('ko_pathway.tab')>0:
        with open("ko_pathway.tab") as fh1, open("map_name.txt") as fh2:
            map_names = {}
            for line in fh2:
                if line.startswith('path:'):
                    fields = line.strip().split("\t")
                    map_id = fields[0].replace('path:', '')
                    map_names[map_id] = fields[1]
            for line in fh1:
                if re.search('path:map', line) and line.startswith('ko:'):
                    fields = line.strip().split("\t")
                    ko_number = re.sub(r'^ko:', '', fields[0])
                    map_id = re.sub(r'path:', '', fields[1])
                    map_str = map_id + "(" + map_names.get(map_id, "") + ")"
                    ko2path.setdefault(ko_number, []).append(map_str)   # maybe one2more
    else:
        sys.exit("Error: can't download ko pathway infors.\n")

    # get ko module
    ko2module = {}
    status = os.system("wget -t 30 --continue -O ko_module.tab http://rest.kegg.jp/link/module/ko")
    if status == 0:
        with open("ko_module.tab") as fh:
            for line in fh:
                if line.startswith("ko:"):
                    fields = line.strip().split("\t")
                    ko_number = re.sub(r'^ko:', '', fields[0])
                    m_name = re.sub(r'md:', '', fields[1])
                    ko2module.setdefault(ko_number, []).append(m_name)
    else:
        sys.exit("Error: can't download ko module.\n")

    output = os.path.join(outdir, 'kegg_ko_informations.tsv')
    with open(output, 'w') as outfh:
        # header
        outfh.write("KO\tFunction\tPathway\tEnzyme\tModules\tHyperlink\n")
        for ko_number in ko2func:
            func_str = ko2func.get(ko_number, "")
            ec_str = " ".join(ko2EC.get(ko_number, []))
            path_str = "; ".join(ko2path.get(ko_number, []))
            mod_str = " ".join(ko2module.get(ko_number, []))
            hyperlink = 'http://rest.kegg.jp/get/' + ko_number
            outfh.write("\t".join([ko_number, func_str, path_str, ec_str, mod_str, hyperlink]) + "\n")

    if os.path.isfile(output) and os.path.getsize(output) > 0:
        shutil.rmtree(tmp_dir)


if __name__ == '__main__':
    main()
