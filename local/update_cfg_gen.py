#!/usr/bin/env python
#coding:utf-8

import logging
try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)
import json
import util.util as util
import os
import tempfile

#    "to_backup":[],
#    "to_delta":[],
#    "to_extract":[],
#    "to_delete":[],

#c:\python27\python.exe make_updater.py -a diffs.json -v 1

control_json = 'control.json'
ARMORY_META = 'armory_meta.json'

def get_args():
    parser = argparse.ArgumentParser(description='example: update_cfg_gen.py '
'-a deltas\diffs.json -v 6')
    parser.add_argument('-s','--volsize',help='volume size')
    parser.add_argument('-a','--armoryjson',help='armory json',required=True)
    parser.add_argument('-v','--version',help='target version',required=True)
    parser.add_argument('--outputfolder',help='print extra info')
    args = parser.parse_args()
    if args.outputfolder is None:
        args.outputfolder = '../.portal'#parent folder
    return args

def r1(s1,p1):
    import re
    o1 = re.search(p1,s1)
    if o1 is not None:
        return o1.group(1) 
    return None
    
def main(slave = False,volsize = None,armoryjson = None,version = None,
    outputfolder = '../.portal'):

    def copy_to_tmpdir(o1,delta_dir):
        latest_dir = o1['latest']
        latest_dir = os.path.join(args_outputfolder,latest_dir)
        if not latest_dir.endswith('/') and not latest_dir.endswith('\\'):
            latest_dir = latest_dir + '/'

        update_tmp_folder = tempfile.mkdtemp()
        tmp_dir = update_tmp_folder + '/'

        coding = util.simple_get_encoding()

        #copy lastest files to tmp dir
        for each in o1['template']['to_extract']:
            src = (latest_dir + each).encode(coding).replace('\\','/')
            dst = (tmp_dir + each).encode(coding).replace('\\','/')
            logging.debug('src is ' + src)
            logging.debug('dst is ' + dst)
            folder_name,base_name = os.path.split(dst)
            util.simple_make_dirs(folder_name)
            util.simple_copy(src,dst)
        #copy delta files to tmp dir
        for each in o1['template']['to_delta']:
            src = (delta_dir + '/' + each).encode(coding).replace('\\','/')
            dst = (tmp_dir + each).encode(coding).replace('\\','/')
            folder_name,base_name = os.path.split(dst)
            util.simple_make_dirs(folder_name)
            util.simple_copy(src,dst)
            
        sisium_config = tmp_dir + '.pandora/sisium.json'
        folder_name,base_name = os.path.split(sisium_config)
        util.simple_make_dirs(folder_name)
        sisium_obj = {}
        sisium_obj['version'] = int(o1['latest_num'])
        f1 = open(sisium_config,'w+b')#new json file
        json.dump(sisium_obj,f1,indent=4)#dump json
        f1.close()

        return update_tmp_folder

    if slave:
        args_volsize = volsize
        args_armoryjson = armoryjson
        args_version = version
        args_outputfolder = outputfolder
    else:
        args = get_args()
        args_volsize = args.volsize
        args_armoryjson = args.armoryjson
        args_version = args.version
        args_outputfolder = args.outputfolder

    f1 = None
    try:
        armoryjson_path = os.path.join(args_outputfolder,args_armoryjson)
        f1 = open(armoryjson_path,'rb')
        o1 = json.load(f1)
        f1.close()

        latest = o1['latest']
        target = o1[args_version]
        appid = o1['appid']

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

        package_name = armory_meta_obj['config']['package_name']
        
        if 1 == len(armory_meta_obj['config']['versions']['main']):
            return

        to_modify = target['to_modify']
        to_add = target['to_add']
        to_delete = target['to_delete']
        
        assert(isinstance(to_modify,dict))
        assert(isinstance(to_add,list))
        assert(isinstance(to_delete,list))

        o2 = {}
        o2['to_delete'] = to_delete
        o2['to_extract'] = to_add
        o2['to_delta'] = []
        o2['to_backup'] = []

        for each in to_modify.keys():
            if to_modify[each] is None:
                o2['to_extract'].append(each)
            else:
                o2['to_delta'].append(to_modify[each]['name'])
                
        for each in o2['to_delta']:
            p1 = ur'(.+)-\w+-\w+\.delta'
            o2['to_backup'].append(r1(each,p1))

        out_obj = {}
        out_obj['template'] = o2

        out_obj['latest'] = appid + '/base/' + latest
        out_obj['latest_num'] = latest

        delta_folder = o1['delta_folder']
        delta_folder = os.path.join(args_outputfolder,delta_folder)
        update_tmp_folder = copy_to_tmpdir(out_obj,delta_folder)
        logging.debug(update_tmp_folder)
        f1 = open(update_tmp_folder + '/' + '.install.json','w+b')
        json.dump(out_obj['template'],f1,indent=4)
        f1.close()
        
        old_new = args_version + '_' + latest
        _patch_name = ''.join(['/patch/',package_name,'-','patch','-',\
           args_version,'-',latest,'.ana'])
        patch_name = ''.join([appid,_patch_name])
        patch_name = os.path.join(args_outputfolder,patch_name)
        patch_name = patch_name.replace('\\','/')
        #remove old patches
        util.rm_files(patch_name[:-4] + '*')
        patch_exe_name = patch_name[:-4] + '.exe'
        vol_size = 90*1024*1024 if args_volsize is None else args_volsize


        #make ana file
        logging.debug(patch_name)
        #folder_name,base_name = os.path.split(patch_name)
        #util.simple_make_dirs(folder_name)
        util.make_archive(update_tmp_folder,patch_name,vol_size)
        try:
            util.simple_remove_dir(update_tmp_folder)
        except: pass
        util.simple_move(patch_name,patch_exe_name)

        #update control.json
        control_json_path = \
            os.path.join(args_outputfolder,appid + '/' + control_json)
        f1 = open(control_json_path,'rb')
        control_obj = json.load(f1)
        f1.close()
        if not control_obj.has_key('patch'):
            control_obj['patch'] = {}
        control_obj['patch'][old_new] = []
        patch_unit = {}
        #patch_unit['url'] = ''.join([control_obj['root'],'/patch/',old_new,\
        #    '/','update.exe'])
        folder_name,base_name = os.path.split(patch_exe_name)
        patch_unit['url'] = '/patch/' + base_name
        patch_unit['size'] = util.simple_getsize(patch_exe_name)
        control_obj['patch'][old_new].append(patch_unit)

        #need test
        i = 1
        while 1:
            tmp_name = ''.join([package_name[:-4],'.ana.',str(i)])
            if util.simple_path_exists(tmp_name):
                folder_name,base_name = os.path.split(tmp_name)
                patch_unit = {}
                patch_unit['url'] = '/patch/' + base_name
                patch_unit['size'] = util.simple_getsize(tmp_name) 
                control_obj['patch'][old_new].append(patch_unit)
            else:
                break
            i += 1
            
        f1 = open(control_json_path,'w+b')#new json file
        json.dump(control_obj,f1,indent=4)#dump json
        f1.close()

    finally:
        if f1 is not None:
            f1.close()

    logging.info('updater: ' + patch_exe_name + ' generation successful')


if __name__ == '__main__':
    main()
