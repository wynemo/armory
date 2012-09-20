#!/usr/bin/env python
#coding:utf-8

import util.util as util
import json
import os
import datetime

import sys
mswindows = (sys.platform == "win32")

VERSION_MAX = 10000


#commit [--name main/branch_name] [-v num] 
#
#list [--name main/branch_name] [--brief]
#
#version 1  r13   [base]
#           r14
#version 2  r15
#version 3  r16

#clean

#def ci(version):
#    dump memory to armory_meta.json
#    get date
#    svn ci test version $version date
#
#para name
#svn info para name
#    if not a svn diroctory or error:
#        exit
#svn st para name 
#    if no diff or error
#        exit('no diff')

#find if exist armory_meta.json
#if error or not exist
    #exit
#load armory_meta.json to memory

#local -> remote
#if memory[name] not exist
#    create
#    memory[name]['1'] = '$Rev$'
#    ci()
#else
#    if not test
#        find max version alreay existed -> max_version
#        if para version is None:
#            memory[name][max_version + 1]  = '$Rev$'
#            ci()
#        else
#            if para version <= max_version
#                exit(error)
#            else:
#                memory[name][para version]  = '$Rev$'
#                ci()
#    else
#        if para version is None:
#            exit('on test,no new version is permit')
#        else:
#            find test version -> test_version
#            memory[name][test_version]  = '$Rev$'
#            ci()

#if local -> remote fail,finally,rm local ARMORY_META,run svn up
#if interupted,also rm local ARMORY_META,run svn up
        

ARMORY_META = 'armory_meta.json'
MAIN_NAME = 'trunk'

import logging
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
        choices=['list', 'commit','ignore','add'],\
        help='action to take')
    parser.add_argument('-d', '--debug', help='print extra info',\
        action='store_true')
    parser.add_argument('-n', '--name', help='main or branch name')
    parser.add_argument('-v', '--version', help='version num')
    parser.add_argument('--customversion', help='custom version for pandora')
    parser.add_argument('--custominfo', help='custom commit info')
    parser.add_argument('--ignorepattern', help='ignore pattern,\
        seperated by commas')

    args = parser.parse_args()
    
    if args.version is not None:
        try:
            tmp_version = int(args.version)
            if tmp_version <= 0:
                logging.error('input postive version num')
        except Exception as e:
            logging.error('not a valid version num ' + str(e))
            exit(-1)
    return args

def is_name_folder(name):
    attr = None
    try:
        attr = util.get_svn_url_attr(name)
        if attr is None:
            return False
    except:
        logging.debug('attr is none')
        return False
    return attr == util.FOLDER

def is_name_file(file1):
    attr = None
    try:
        attr = util.get_svn_url_attr(file1)
        if attr is None:
            return False
    except:
        logging.debug('attr is none')
        return False
    return attr == util.FILE

def name_has_change(name):
    try:
        return util.svn_folder_has_change(name)
    except:
        return False
    


def main():
    args = get_args()

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',\
        datefmt='%m/%d/%Y %I:%M:%S %p',\
        level=level)
        
    if 'list' == args.action:
        try:
            f = open(ARMORY_META,'rb')
            o = json.load(f)
            f.close()
            l1 = []
            for each in o['info']['main']:
                l1.append(int(each))
            l1.sort()
            l1.reverse()
            for each in l1:
                tmp_r = o['info']['main'][str(each)]
                if tmp_r.startswith(r'$Rev'):
                    tmp_r = util.find_test_version(tmp_r) + ' (test)'
                print 'version',each,': r' + tmp_r
        except Exception as e:
            logging.error(e)
        exit(0)

    elif 'ignore' == args.action:
        carriage = '\r\n' if mswindows else '\n'
        if args.ignorepattern is not None:
            ignore_list = args.ignorepattern.split(',')
        _ignore_list = []
        for each in ignore_list:
            each = each.strip().replace('\r','').replace('\n','')
            _ignore_list.append(each)

        if not _ignore_list:
            exit('invalid or empty pattern')

        def ignore_folder():
            import subprocess
            pattern = carriage.join(_ignore_list)
            args = ['svn','propset','svn:ignore',pattern,'.']
            logging.debug(args)
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

        if not ignore_folder():
            logging.error('fail to ignore pattern')
            exit(-1)

        exit(0)

    elif 'add' == args.action:
        if args.name is None:
            name = MAIN_NAME 
        else:
            if args.name == 'main':
                name = MAIN_NAME 
            else:
                name = 'branches/' + args.name

        def add_folder(folder):
            import subprocess
            args = ['svn','add',folder,'--force']
            logging.debug(args)
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

        if not add_folder(name):
            logging.error('fail to add ' + name)
            exit(-1)

        exit(0)

    if args.name is None:
        name = MAIN_NAME 
        args.name = 'main'
    else:
        if args.name == 'main':
            name = MAIN_NAME 
        else:
            name = 'branches/' + args.name

    if not is_name_folder(name):
        logging.error(args.name + ' is not folder')
        exit(-1)

    if not name_has_change(name):
        logging.info(name + ' has no change')
        exit(-1)

    if not is_name_file(ARMORY_META):
        logging.error('fail to find ' + ARMORY_META)
        exit(-1)

    f = None
    o = None
    first = False
    test_version = None
    commit_info = ''

    try:
        f = open(ARMORY_META,'rb')
        o = json.load(f)
    except Exception as e:
        logging.error('fail to load ' + ARMORY_META + ' ' + str(e))
        exit(-1)
    finally:
        if f is not None:
            f.close()

    if not o.has_key('info'):
        o['info'] = {}
    if not o['info'].has_key(args.name):
        o['info'][args.name] = {}
    if not o['info'][args.name]:
        first = True
        
    def clean():
        #restore
        util.simple_remove_file(ARMORY_META)
        util.update_path_to_revision()

    f = None
    try:
        if first:
            #version = args.version if args.version is not None else "1"
            version = '1'
            o['info'][args.name][version] = '$Rev$'
            commit_info = '#first version:' + version
        else:
            for each in o['info'][args.name]:
                if util.find_test_version(o['info'][args.name][each]) is not None:
                    test_version = each
                    break
            if test_version is not None:
                logging.debug('test version ' + test_version)
                if args.version is not None:
                    if not test_version == args.version:
                        logging.error('on test,can\'t commit other version than ' + test_version)
                        exit(-1)
                #test continue
                o['info'][args.name][test_version] = '$Rev$'
                version = test_version
                commit_info = '#update test version:' + version
            else:
                logging.debug('not test version')
                l1 = o['info'][args.name].keys()
                l2 = []
                for each in l1:
                    l2.append(int(each))
                l2.sort()
                max_version = max(l2)
                if args.version is None:
                    #default new version
                    o['info'][args.name][str(max_version + 1)] = '$Rev$'
                    version = str(max_version + 1)
                    commit_info = '#new test version:' + version
                else:
                    if int(args.version) <= max_version:
                        logging.error('try to commit an older version')
                        exit(-1)
                    else:
                        #new version
                        o['info'][args.name][args.version] = '$Rev$'
                        version = str(args.version)
                        commit_info = '#new test version:' + version 
        f = open(ARMORY_META,'w+b')
        o['date'] = str(datetime.datetime.now())
        

        l_version = str(int(version)%VERSION_MAX)
        h_version = str(int(version)/VERSION_MAX)
        manchine_version = h_version + '.' + l_version
        customversion = '' if args.customversion is None else args.customversion
        o['config']['custom_version'] = customversion + '.' + manchine_version
        
        if not o['config']['versions'].has_key(args.name):
            o['config']['versions'][args.name] = []
        if not int(version) in o['config']['versions'][args.name]:
            o['config']['versions'][args.name].append(int(version))
        
        json.dump(o,f,indent=4)
        if f is not None:
            f.close()
            f = None

        #ci
        if args.custominfo is not None:
            carriage = '\r\n' if mswindows else '\n'
            commit_info += carriage + args.custominfo
        to_commit = [ARMORY_META,name]
        rv = util.commit_folder(commit_info,to_commit)
        if rv:
            logging.info('commit successful')
        else:
            clean()
            logging.error('commit fail')
            

    except Exception as e:
        logging.error(str(e))
        logging.error('commit fail')
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
