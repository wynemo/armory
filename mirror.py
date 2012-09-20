#!/usr/bin/env python
#coding:utf-8


import util.util as util
import logging
import json
import datetime

ARMORY_META = 'armory_meta.json'

try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)

def get_args():
    parser = argparse.ArgumentParser(description='ATTENTION:befor using this'\
'scrpit,MAKE USE you svn work space UP TO DATE and CLEAN,'\
'no merge,conflict stuff or something is considered')
    parser.add_argument('action',\
        choices=['package', 'base','patch'],\
        help='which')
    parser.add_argument('-d','--debug', help='print extra info',\
        action='store_true')
    parser.add_argument('-u','--urls', help='seperated by comma')

    args = parser.parse_args()
    
    return args

def main():

    def clean():
        #restore
        util.simple_remove_file(ARMORY_META)
        util.update_path_to_revision()

    level = logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',\
        datefmt='%m/%d/%Y %I:%M:%S %p',\
        level=level)

    args = get_args()

    if args.urls is None:
        args.urls = ''
    mirror_list = args.urls.split(',')
    _mirror_list = []
    for each in mirror_list:
        each = each.strip().replace('\r','').replace('\n','')
        if each:
            _mirror_list.append(each)
    _mirror_list.sort()

    action = args.action

    if action == 'patch' or action == 'package':
        if not _mirror_list:
            logging.error('patch,package should set at least one mirror')
            exit(-1)

    try:
        f = None
        f = open(ARMORY_META,'r+b')
        o = json.load(f)

        if action == 'patch':
            tmp_l = []
            tmp_l.extend(o['config']['patch_mirrors'])
            tmp_l.sort()
            if tmp_l == _mirror_list:
                logging.error('mirror not change')
                exit(0)
            o['config']['patch_mirrors'] = _mirror_list
        elif action == 'package':
            tmp_l = []
            tmp_l.extend(o['config']['package_mirrors'])
            tmp_l.sort()
            if tmp_l == _mirror_list:
                logging.error('mirror not change')
                exit(0)
            o['config']['package_mirrors'] = _mirror_list
        elif action == 'base':
            tmp_l = []
            tmp_l.extend(o['config']['base_mirrors'])
            tmp_l.sort()
            if tmp_l == _mirror_list:
                logging.error('mirror not change')
                exit(0)
            o['config']['base_mirrors'] = _mirror_list

        f.truncate(0)
        f.seek(0)
        o['date'] = str(datetime.datetime.now())
        json.dump(o,f,indent = 4)
        f.close()
        f = None

        commit_info = 'set mirror for ' + action

        to_commit = [ARMORY_META]
        rv = util.commit_folder(commit_info,to_commit)
        if rv:
            pass
        else:
            clean()
            logging.error('change mirror fail')

    except Exception as e:
        logging.error(str(e))
        if f is not None:
            f.close()
            f = None
        clean()
    finally:
        if f is not None:
            f.close()
            f = None

if __name__ == "__main__":#main entry
    main()
