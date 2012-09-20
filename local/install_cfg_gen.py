#!/usr/bin/env python
#coding:utf-8

import json
import sys
import os
import os.path
import util.walk as walk
import util.util as util
import logging
try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)
import tempfile

module_path = os.path.dirname(__file__)
parent_path = \
    os.path.abspath(os.path.join(module_path, os.path.pardir))

to_extract = []
control_json = 'control.json'
INSTALLER = '.sisium/installer.exe'
STUB_LUA = '.sisium/stub.lua'
SISIUM_FOLDER = '.sisium'
STUB = 'stub.exe'
args_input = None
ARMORY_META = 'armory_meta.json'
args_outputfolder = ''
newest_objs = []

def append_stub(file1,output_folder):
    tmpfile = tempfile.mktemp(dir=output_folder)
    util.simple_copy(os.path.join(parent_path,STUB),tmpfile)
    util.cat_to_other(file1,tmpfile)
    util.simple_move(tmpfile,file1)

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

def add_extract(filename):
    global to_extract
    coding = util.simple_get_encoding()
    filename = filename.replace('\\','/') 
    crc = None
    for each in newest_objs:
        if each['name'] == filename:
            if each.has_key('crc32'):
                crc = each['crc32']
            break
    _filename = os.path.join(args_input,filename).replace('\\','/')
    if crc is None:
        logging.info('calcing crc32 of ' + filename)
        crc = util.crc32(_filename)
    filename = filename.decode(coding).encode('utf-8')
    obj = {}
    obj['filename'] = filename
    obj['crc32'] = crc
    to_extract.append(obj)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--volsize',help='volume size')
    parser.add_argument('--verbose',help='print debug info',\
        action='store_true')
    parser.add_argument('--outputfolder',help='print extra info')
    parser.add_argument('-a','--armoryjson',help='armory json',required=True)
    
    args = parser.parse_args()
    if args.outputfolder is None:
        args.outputfolder = '../.portal'#parent folder
    return args
    
def main(slave = False,volsize = None,verbose = False,
    outputfolder = '../.portal',armoryjson = None):

    def make_sisium_json():
        sisium_config = args_input + '/' + '.pandora/sisium.json'
        folder_name,base_name = os.path.split(sisium_config)
        util.simple_make_dirs(folder_name)
        sisium_obj = {}
        sisium_obj['version'] = int(version)
        f1 = open(sisium_config,'w+b')#new json file
        json.dump(sisium_obj,f1,indent=4)#dump json
        f1.close()
        
    def remove_install_json():
        try:
            tmp = os.path.join(args_input,'.install.json')
            util.simple_remove_file(tmp)
        except:
            pass

    def make_install_json():
        try:
            #we don't care .svn folder when making installer
            walk.walkutil(args_input,None,add_extract,'.svn')
            o1 = {}
            o1['to_extract'] = to_extract 
            o1['to_backup'] = [] 
            tmp = os.path.join(args_input,'.install.json')
            f = open(tmp,'w+b')
            #print json.dumps(o1)
            json.dump(o1,f)
            f.close()
        except Exception as e:
            logging.error('fail to general a valid json file: ' + str(e))
            exit(-1)
        finally:
            pass

    def remove_sisium():
        try:
            tgt_folder = args_input + '/' + SISIUM_FOLDER
            logging.debug('target folder is ' + tgt_folder)
            util.simple_remove_dir(tgt_folder)
        except Exception as e:
            logging.debug('fail to remove sisium folder' + str(e))

    def copy_sisium():
        tgt_folder =  args_input + '/' + SISIUM_FOLDER + '/'
        logging.debug('target folder is ' + tgt_folder)
        try:
            util.simple_make_dirs(tgt_folder)
        except:pass
        try:
            util.simple_copy(os.path.join(parent_path,INSTALLER),\
                args_input + '/' + SISIUM_FOLDER)
            util.simple_copy(os.path.join(parent_path,STUB_LUA),\
                args_input + '/' + SISIUM_FOLDER)
        except Exception as e:
            logging.error('fail to copy files' + str(e))
            exit(-1)
        

    global args_input
    global args_outputfolder
    global newest_objs
    
    if slave:
        args_volsize = volsize
        args_verbose = verbose
        args_outputfolder = outputfolder
        args_armoryjson = armoryjson
    else:
        args = get_args()
        args_volsize = args.volsize
        args_verbose = args.verbose
        args_armoryjson = args.armoryjson
        args_outputfolder = args.outputfolder

    if args_verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',\
        datefmt='%m/%d/%Y %I:%M:%S %p',\
        level=level)

    changed = False
    old_revision = ''
    new_revision = ''
    package_exe_name = ''


    svn_url = util.get_game_svn_url('.')
    armory_meta_obj = load_armory_meta(svn_url)
    if armory_meta_obj is None:
        logging.error('could not load '+ ARMORY_META)
        return -1

    appid = armory_meta_obj['config']['appid']
    #args_input = appid + '/base/1'
    #args_input = os.path.join(args_outputfolder, args_input)
    args_input = './trunk'
    args_input = args_input.replace('\\','/')
    logging.debug('input folder is ' + args_input)
   
    #try:
    #    old_revision = util.get_revision_by_path(args_input)
    #except:
    #    exit('error get revision of first version')

    #if not old_revision:
    #    exit('error get revision of first version')

    armoryjson_path = os.path.join(args_outputfolder,args_armoryjson)
    f1 = open(armoryjson_path,'rb')
    o1 = json.load(f1)
    f1.close()
    newest_objs = o1[o1['latest']]

    try:
        game_name = armory_meta_obj['config']['game_name']
        versions = armory_meta_obj['config']['versions']['main']
        versions.sort()
        version = str(max(versions))
        new_revision = util.find_revision_from_armory_meta(armory_meta_obj,\
            version,'main')

        #if new_revision is None:
        #    exit('fail to find target revision')
        #if not util.update_path_to_revision(args_input,new_revision):
        #    exit('fail to update to target revision')
        changed = True
        #make archive

        remove_sisium()
        remove_install_json()

        make_sisium_json()
        make_install_json()
        logging.debug('copy sisium folder\'s files')
        copy_sisium()

        _package_name = armory_meta_obj['config']['package_name']
        _package_name = ''.join([_package_name,'-',version,'.ana'])
        output_folder = appid + '/package/' + version
        output_folder = \
            os.path.join(args_outputfolder,output_folder)
        package_name = os.path.join(output_folder,_package_name)
        package_name = package_name.replace('\\','/')
        util.rm_files(package_name[:-4] + '*')
        package_exe_name = package_name[:-4] + '.exe'
        vol_size = 90*1024*1024 if args_volsize is None else args_volsize
        util.make_archive(args_input,package_name,vol_size)
        append_stub(package_name,output_folder)
        util.simple_move(package_name,package_exe_name)

        remove_sisium()
        remove_install_json()

    except Exception as e:
        logging.error(e)
        exit('fail')
    finally:
        pass
        #if changed:
        #    try:
        #        if not util.update_path_to_revision(args_input,old_revision):
        #            logging.error('fail to restore revison')
        #    except:
        #        logging.error('fail to restore revison')

    folder_name,base_name = os.path.split(package_exe_name)

    #update control_json
    logging.info('update control_json')
    f1 = None
    try:
        control_json_path = \
            os.path.join(args_outputfolder,appid + '/' + control_json)
        f1 = open(control_json_path,'rb')
        control_obj = json.load(f1)
        f1.close()
    finally:
        if f1 is not None:
            f1.close()

    if not control_obj.has_key('package'):
        control_obj['package'] = {}
    control_obj['package'][version] = []
    package_unit = {}
    package_unit['url'] = '/package/' + version + '/' + base_name
    package_unit['size'] = util.simple_getsize(package_exe_name) 
    control_obj['package'][version].append(package_unit)
    i = 1
    while 1:
        tmp_name = ''.join([package_name[:-4],'.ana.',str(i)])
        if util.simple_path_exists(tmp_name):
            folder_name,base_name = os.path.split(tmp_name)
            package_unit = {}
            package_unit['url'] = '/package/' + version + '/' + base_name
            package_unit['size'] = util.simple_getsize(tmp_name) 
            control_obj['package'][version].append(package_unit)
        else:
            break
        i += 1

    f1 = None
    try:
        f1 = open(control_json_path,'w+b')#new json file
        json.dump(control_obj,f1,indent=4)#dump json
        f1.close()
    finally:
        if f1 is not None:
            f1.close()

    logging.info('installer:' + package_exe_name + ' generation successful')


def pandora_maker():
    changed = False
    svn_url = util.get_game_svn_url('.')
    armory_meta_obj = load_armory_meta(svn_url)
    if armory_meta_obj is None:
        logging.error('could not load '+ ARMORY_META)
        return -1

    appid = armory_meta_obj['config']['appid']
    args_input = appid + '/base/1'
    args_input = os.path.join('../.portal', args_input)
    args_input = args_input.replace('\\','/')
    logging.debug('input folder is ' + args_input)

    try:
        old_revision = util.get_revision_by_path(args_input)
    except:
        exit('error get revision of first version')

    if not old_revision:
        exit('error get revision of first version')

    try:
        game_name = armory_meta_obj['config']['game_name']
        versions = armory_meta_obj['config']['versions']['main']
        versions.sort()
        version = str(max(versions))
        new_revision = util.find_revision_from_armory_meta(armory_meta_obj,\
            version,'main')

        if new_revision is None:
            exit('fail to find target revision')
        if not util.update_path_to_revision(args_input,new_revision):
            exit('fail to update to target revision')
        changed = True

        custom_version = armory_meta_obj['config']['custom_version']

        def pandora_zip():
            import zipfile
            try:
                outdir = '../.portal/pandora_manager/package/'
                util.simple_make_dirs(outdir)
            except Exception as e:
                logging.error(str(e))
            with zipfile.ZipFile(outdir + 'pandora-' + version + '.zip', 'w',\
                zipfile.ZIP_DEFLATED) as myzip:
                def foo(filename):
                    foo1,bar1 = os.path.split(filename)
                    if bar1 == 'pandora.exe':
                        zip_path = bar1
                    else:
                        zip_path = custom_version + '/' + filename
                    zip_path = zip_path.replace('\\','/')
                    _filename = os.path.join(args_input,filename).replace('\\','/')
                    myzip.write(_filename,zip_path)
                walk.walkutil(args_input,None,foo,'.svn')
                myzip.close()

        pandora_zip()


    except Exception as e:
        logging.error(e)
        exit('fail')
    finally:
        if changed:
            try:
                if not util.update_path_to_revision(args_input,old_revision):
                    logging.error('fail to restore revison')
            except:
                logging.error('fail to restore revison')
    

if __name__ == '__main__':
    main()
