#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# FileName:  crawl_kepp_pathway_level.py
# Author:    Zhihao Xie  \(#^o^)/
# Date:      2018/8/29 13:49
# Version:   v1.0.0
# CopyRight: Copyright ©Zhihao Xie, All rights reserved.

"""
crawl kegg to get pathway level information
"""

import sys
import os
import re
import urllib.request,urllib.error,urllib.parse
from collections import OrderedDict
import time

def crawl_kegg_pathway_level():
    # return a map id dict
    start_url = 'https://www.kegg.jp/kegg/pathway.html'
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
    }

    request = urllib.request.Request(start_url, headers=header)
    try:
        reponse = urllib.request.urlopen(request)
    except urllib.error.HTTPError as e:
        print(e.code, file=sys.stderr)
        print(e.reason, file=sys.stderr)

    level1 = ""
    level2 = ""
    map_id= ""   # also as level3
    pathway_levels = OrderedDict()
    for myline in reponse.readlines():
        myline = myline.decode('utf-8')
        myline = myline.rstrip('\n')
        if re.search('<h4>.+</h4>', myline):
            level1 = re.findall('<h4>(.+)</h4>', myline)[0]
            level1 = re.sub('^\d+[.\d\s]*', '', level1)
        elif re.search('<b>.+</b>', myline) and not re.search('<a href=', myline):
            level2 = re.findall('<b>(.+)</b>', myline)[0]
            level2 = re.sub('^\d+[.\d\s]*', '', level2)
        elif re.search(r'<dt>\d+</dt><dd><a href=.+</a></dd>', myline):
            map_id, link, desc = re.findall(r'<dt>(\d+)</dt><dd><a href=(.+)>(.+)</a></dd>', myline)[0]
            link = link.strip('"').strip("'")
            map_id = 'map' + map_id
            if map_id != '':
                if level1 != "" and level2 != "":
                    pathway_levels.setdefault(map_id, [desc, level1, level2])

    return pathway_levels

def get_ko_map(map_id, temp_dir="."):
    # http://rest.kegg.jp/link/ko/map05010
    url_str = 'http://rest.kegg.jp/link/ko/' + map_id
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'}

    request = urllib.request.Request(url_str, headers=header)
    try:
        reponse = urllib.request.urlopen(request)
    except urllib.error.HTTPError as e:
        print(e.code, file=sys.stderr)
        print(e.reason, file=sys.stderr)
    temp_file = os.path.join(temp_dir, map_id+".html")
    fhandle = open(temp_file, 'wb')
    fhandle.write(reponse.read())
    fhandle.close()
    kos = set()
    if os.path.isfile(temp_file) and os.path.getsize(temp_file)>0:
        with open(temp_file) as fh:
            for line in fh:
                if not re.search('^\s*$', line):
                    mylist = re.split('[:\t]', line.strip())
                    ko = mylist[-1]
                    kos.add(ko)
        os.remove(temp_file)
    else:
        if os.path.isfile(temp_file):
            os.remove(temp_file)
    # return a KOs list
    kos = list(kos)
    kos.sort()
    return kos


def main():
    pathway_levels = crawl_kegg_pathway_level()
    if len(pathway_levels.keys())>0:
        # output header
        print("kegg_pathway\tdescription\thref\tlevel1\tlevel2\tKOs")
        for map_id in pathway_levels:
            KO_list = get_ko_map(map_id)
            href = 'https://www.kegg.jp/kegg-bin/show_pathway?map=' + map_id
            map_info = pathway_levels[map_id]
            map_info.insert(1, href)
            map_info.append(";".join(KO_list))
            print("{}\t{}".format(map_id, "\t".join(map_info)))
            time.sleep(1)
    else:
        print("Error: get kegg pathway level info.", file=sys.stderr)
        sys.exit()


if __name__ == '__main__':
    main()
