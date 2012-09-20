#!/usr/bin/env python
#coding:utf-8


import os.path
import logging
import getpass
try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)
import json
import util.util as util

INFO_NAME = 'appinfo.json'
ANA_NAME = 'test.ana'
SEARCH_FILE_NAME = 'search.lua'

def get_args():
    parser = argparse.ArgumentParser(description='appdata.ana maker')
    parser.add_argument('-o', '--ouput', help='output file', required=True)
    parser.add_argument('-u', '--user', help='svn user name', required=True)
    parser.add_argument('-a', '--address',\
        help='svn server address http://svn.gaia.org/armories',\
        required=True)
    parser.add_argument('-d', '--debug', help='print extra info',\
        action='store_true')
    args = parser.parse_args()
    password = getpass.getpass("Enter password for %s:" % (args.user))
    if password is None:
        print('MUST enter a password')
        exit(-1)
    args.password = password
    if not args.address.endswith('/'):
        args.address = args.address + '/'
    return args

def make_appdata_ana(ar_name):
    import subprocess
    tmp_dir = 'appdata'
    module_path = os.path.dirname(__file__)
    tmp_name = os.path.join(module_path,'archivemaker.exe')
    args = [tmp_name,'/makear',tmp_dir,'/output',ar_name]
    pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
        stderr = subprocess.PIPE)
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        pass
    else:#error
        logging.error('make appdata ana failed:%s'%(err))
        exit(-1)

def download_appdata(args):
    tmp_dir = 'appdata'
    try:
        util.simple_remove_dir(tmp_dir)
    except:
        pass
    util.simple_make_dirs(tmp_dir)
    info_url = args.address + INFO_NAME
    search_file_url = args.address + SEARCH_FILE_NAME
    info_file = None
    try:
        if not util.download_svn_file(info_url,tmp_dir + '/' + INFO_NAME,
            args.user,args.password):
            exit(-1)
        info_file = open(tmp_dir + '/' + INFO_NAME,'r')
        info_object = json.load(info_file)
        info_file.close()
        info_file = None
        for each in info_object.keys():
            id1 = int(info_object[each]['id'])
            appid_dir = tmp_dir + '/' + hex(id1)[2:]
            util.simple_make_dirs(appid_dir)
            folder_url = args.address + info_object[each]['folder']
            misc_url = folder_url + '/misc'
            misc_buffer = util.list_svn_url(misc_url)
            if misc_buffer is None:
                exit('error')
            misc_list = misc_buffer.splitlines()
            for sth in misc_list:
                sth = sth.strip().replace('\r','').replace('\n','')
                if 0 == len(sth):
                    continue
                sth_url = misc_url + '/' + sth
                sth_parent,sth_base = os.path.split(sth)
                if len(sth_parent) > 0:
                    util.simple_make_dirs(appid_dir + '/' + sth_parent)
                util.download_svn_file(sth_url,appid_dir + '/' + sth,
                    args.user,args.password)
                logging.info('download file %s'%(sth_url))

        if not util.download_svn_file(search_file_url,\
            tmp_dir + '/' + SEARCH_FILE_NAME,\
            args.user,args.password):
            exit(-1)

        return True
    except Exception as e:
        logging.error('%s'%(str(e)))
        return False;
    finally:
        if info_file is not None:
            info_file.close()

def main():
    args = get_args()
    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',\
        datefmt='%m/%d/%Y %I:%M:%S %p',\
        level=level)
    if not download_appdata(args):
        exit(-1)
    make_appdata_ana(args.ouput)
    logging.info('generate %s successful'%(args.ouput))

if __name__ == "__main__":#main entry
    main()
