#!/usr/bin/env python
#coding:utf-8

import logging
import json
try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)
import server.diffs as diffs
import local.install_cfg_gen as install_cfg_gen
import local.update_cfg_gen as update_cfg_gen
import util.util as util
import tempfile
ARMORY_META = 'armory_meta.json'

def get_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s','--volsize',help='volume size 94371840')
    parser.add_argument('--verbose',help='print debug info',\
        action='store_true')
    parser.add_argument('--installer',help='installer only',\
        action='store_true')
    parser.add_argument('--updater',help='updater only',\
        action='store_true')
    args = parser.parse_args()
    return args

def main():
    args = get_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',\
        datefmt='%m/%d/%Y %I:%M:%S %p',\
        level=level)

    svn_url = util.get_game_svn_url('.')
    def load_armory_meta(svn_url):
        tmpfile = tempfile.mktemp()
        if not util.export_svn_file_to_local(svn_url + '/' + ARMORY_META,tmpfile):
            return None
        armory_meta_obj = None
        f = None
        try:
            f = open(tmpfile,'rb')
            armory_meta_obj = json.load(f)
        except Exception as e:
            logging.debug(str(e))
        finally:
            if f is not None:f.close()
        return armory_meta_obj
    armory_meta_obj = load_armory_meta(svn_url)
    if armory_meta_obj is None:
        logging.error('could not load '+ ARMORY_META)
        return -1


    config_obj = armory_meta_obj['config']
    package_name = config_obj['package_name']
    main_versions = config_obj['versions']['main']

    armory_json = config_obj['appid'] + '/' + package_name + '.json'
    
    if args.installer:
        if config_obj['appid'] == 'pandora_manager':
            install_cfg_gen.pandora_maker()
        else:
            install_cfg_gen.main(True,args.volsize,args.verbose,armoryjson = armory_json)
    elif args.updater:
        if not config_obj['appid'] == 'pandora_manager':
            if len(main_versions) > 1:
                main_versions.sort()
                for each1 in main_versions[:-1]:
                    update_cfg_gen.main(True,args.volsize,armory_json,str(each1))
    else:  
        diffs.main(True,None,armory_json,args.verbose)

        if config_obj['appid'] == 'pandora_manager':
            install_cfg_gen.pandora_maker()
        else:
            install_cfg_gen.main(True,args.volsize,args.verbose,armoryjson = armory_json)
            
            if len(main_versions) > 1:
                main_versions.sort()
                for each1 in main_versions[:-1]:
                    update_cfg_gen.main(True,args.volsize,armory_json,str(each1))

        

if __name__ == "__main__":#main entry
    main()

