#!/usr/bin/env python
#coding:utf-8

import getpass
try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)
import util.util as util
import os.path
import tempfile
import json

PANDORA_CONFIG = '.pandora/config.json'
ARMORY_META = 'armory_meta.json'


def get_args():
    parser = argparse.ArgumentParser(description='config generate')
    parser.add_argument('-a', '--address',\
        help='svn server address http://svn.gaia.org/armories',\
        required=True)
    parser.add_argument('-u','--user',help='svn user name',required=True)
    parser.add_argument('-o','--output',help='config.json',required=True)
    args = parser.parse_args()
    password = getpass.getpass("Enter password for %s:" % (args.user))
    if password is None:
        print('MUST enter a password')
        exit(-1)
    args.password = password
    return args

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

def main():
    config_obj = {}
    args = get_args()
    svn_user = args.user
    svn_pwd = args.password
    list1 = util.get_svn_url_list(args.address)
    config_obj['games'] = {}
    config_obj['svn_url'] = args.address
    config_obj['armories_url'] = 'http://armories.pandoramanager.net'
    config_obj['package_mirrors'] = ['http://armories.pandoramanager.net']
    config_obj['patch_mirrors'] = ['http://armories.pandoramanager.net']
    config_obj['base_mirrors'] = []
    for sth in list1:
        #sth is game name
        if sth.endswith('/'):#folder
            game_svn_url = os.path.join(args.address,sth).replace('\\','/')
            if game_svn_url.endswith('/'):
                game_svn_url = game_svn_url[:-1]
            game_trunk_url = util.combine_trunk_url(game_svn_url,'')
            pandora_config = os.path.join(game_trunk_url,PANDORA_CONFIG)
            tmp = tempfile.mktemp()
            if not util.download_svn_file(pandora_config,tmp,svn_user,svn_pwd):
                if not util.download_svn_file(pandora_config,tmp,svn_user,\
                    svn_pwd):
                    continue
            #log = util.get_log(game_svn_url)
            #try:
            #    l1 = util.find_versions(log,sth[:-1],'main')
            #except:
            #    continue

            obj = load_armory_meta(game_svn_url)
            if obj is None:
                exit('could not load '+ ARMORY_META)
            try:
                l1 = util.find_verions_from_armory_meta(obj,'main')
            except:
                continue

            m = {'main':l1}
            f = open(tmp,'rb')
            o1 = json.load(f)
            f.close()
            appid = hex(o1['app_id'])[2:]
            config_obj['games'][appid] = {}
            config_obj['games'][appid]['game_name']= sth[:-1]
            config_obj['games'][appid]['package_name']= sth[:-1]

            game_branch_url =\
                os.path.join(game_svn_url,'branches').replace('\\','/')
            list2 = util.get_svn_url_list(game_branch_url)
            for each2 in list2:
                #each2[:-1] is branch name,such as 3dm
                try:
                    #l2 = util.find_versions(log,sth[:-1],each2[:-1])
                    l2 = util.find_verions_from_armory_meta(obj,each2[:-1])
                except:
                    continue
                m2 = {each2[:-1]:l2}
                m.update(m2)

            config_obj['games'][appid]['versions']= m
                

    f = open(args.output,'w+b')
    json.dump(config_obj,f,indent=4)#dump json
    f.close()

    #get appid
        #download file
    #get version

if __name__ == "__main__":#main entry
    main()

