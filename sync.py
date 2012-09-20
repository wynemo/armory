#!/usr/bin/env python
#coding:utf-8

import logging
import tempfile
import util.util as util
import json
import os.path
import sys
import subprocess
try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)

ARMORY_META = 'armory_meta.json'
gargs = None

def get_args():
    global gargs
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-a','--sshalias', help='ssh alias',required=True)
    parser.add_argument('-d','--dir', help='root dir')
    parser.add_argument('-i','--inputdir', help='input dir,default current')

    gargs = parser.parse_args()

def sync_folder(local,remote,clean = True):
    args = ['rsync','-rltDvzPe','ssh','--exclude=.svn','--delete-excluded']
    if clean:
        args.append('--delete')
    args.append(local)
    args.append(remote)
    logging.debug(args)
    return run_args(args)

def run_args(args):
    try:
        pipe = subprocess.Popen(args,bufsize = 0,\
            stdout = sys.stdout,\
            stderr=subprocess.STDOUT)
    except Exception as e:
        logging.error(str(e))
        return False
    while 1:
        if pipe.returncode is None:
            pipe.poll()
        else:
            break
    if not 0 == pipe.returncode:
        return False
    return True

def my_chown():
    args = ['ssh',gargs.sshalias,'chown','www:www',gargs.dir,'-R']
    return run_args(args)

def my_chmod():
    args = ['ssh',gargs.sshalias,'chmod','u+rx',gargs.dir,'-R']
    return run_args(args)

def my_mkdir(dir1):
    args = ['ssh',gargs.sshalias,'mkdir',dir1]
    return run_args(args)

def main():
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

    get_args()

    if gargs.dir is None:
        gargs.dir = '/var/wwwroot/armories/' 

    if not gargs.dir.endswith('/'):
        gargs.dir = gargs.dir + '/'

    inputdir = '.' if gargs.inputdir is None else gargs.inputdir

    svn_url = util.get_game_svn_url(inputdir)
    armory_meta_obj = load_armory_meta(svn_url)
    if armory_meta_obj is None:
        logging.error('could not load '+ ARMORY_META)
        return -1
    config_obj = armory_meta_obj['config']
    appid = config_obj['appid']

    args_outputfolder = '../.portal'
    local_folder = os.path.join(args_outputfolder,appid) + '/'
    remote_folder = gargs.sshalias + ':' + gargs.dir
    remote_folder = os.path.join(remote_folder,appid + '/')
    
    local_folder = local_folder.replace('\\','/')
    remote_folder = remote_folder.replace('\\','/')

    local_base_folder = local_folder + 'base/'
    local_package_folder = local_folder + 'package/'
    local_patch_folder = local_folder + 'patch/'
    local_control_json = local_folder + 'control.json'

    remote_base_folder = remote_folder + 'base/'
    remote_package_folder = remote_folder + 'package/'
    remote_patch_folder = remote_folder + 'patch/'
    remote_control_json = remote_folder + 'control.json'

    my_mkdir(gargs.dir + appid)
    if util.simple_path_exists(local_base_folder):
        sync_folder(local_base_folder,remote_base_folder)
    if util.simple_path_exists(local_package_folder):
        sync_folder(local_package_folder,remote_package_folder)
    if util.simple_path_exists(local_patch_folder):
        sync_folder(local_patch_folder,remote_patch_folder)
    if util.simple_path_exists(local_control_json):
        sync_folder(local_control_json,remote_control_json)

    my_chown()
    my_chmod()

    


if __name__ == "__main__":#main entry
    main()
