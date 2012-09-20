#!/usr/bin/env python
#coding:utf-8

import json
import sys
import util.walk as walk
import util.util as util
import os.path
import os
import subprocess
import tempfile
from threading  import Thread
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x
import logging
try:
    import argparse
except ImportError:
    logging.error('please use use python version >= 2.7')
    exit(-1)
import binascii

import sys
mswindows = (sys.platform == "win32")

len2 = 16
exe_name = 'xdeltatool.exe'
input_folder = ''
src_folders = []
control_json = 'control.json'
ARMORY_META = 'armory_meta.json'


#calucate file's md5,return 32bit md5 string
#if error,return None
def calc_md5(file_name1):
    def str_convert(s2):
        assert(len(s2) == len2)
        rt = ''
        for each in s2:
            c1 = ord(each)
            s3 = '%02X'%(c1)
            rt += s3
        return rt
    import md5,os.path
    f1 = None
    prev = 0
    try:
        if os.path.getsize(file_name1) == 0:#zero size file
            return None,None
        m1 = md5.new()
        f1 = open(file_name1,'rb')#read mode,binary mode(for windows)
        len1 = 1024*32#buffer size
        while 1:
            tmp_buffer = f1.read(len1)
            m1.update(tmp_buffer)
            prev = binascii.crc32(tmp_buffer, prev)
            if len(tmp_buffer) != len1:#file end
                break
        s1 = m1.digest()
        return str_convert(s1),prev & 0xFFFFFFFF#to 16
    except Exception as e:#Exception
        logging.error('calc md5 of %s failed:%s'%(file_name1,str(e)))
        return None,None
    finally:
        if f1 is not None:f1.close()

#use xdeltatool.exe to encode or decode
#code = 1,encode;code not 1 decode
def xdelta_code(input_name,output_name,src_name = None,code = 1):#src could be none
    import subprocess
    import sys
    module_path = os.path.dirname(__file__)
    parent_path = \
        os.path.abspath(os.path.join(module_path, os.path.pardir))
    tmp_name = os.path.join(parent_path,exe_name)
    logging.debug('tmp_name is ' + tmp_name)

    args = []
    args.append(tmp_name)
    if not code == 1:
        args.append('-d')
    else:
        args.append('-e')
    args.append('-v')
    if src_name is not None:
        args.append('-s')
        args.append(src_name)
    args.append(input_name)
    args.append(output_name)
    logging.debug(args)

    try:
        pipe = subprocess.Popen(args,bufsize = 0,\
            stdout = sys.stdout,\
            stderr = subprocess.STDOUT)
    except Exception as e:
        logging.error(str(e))
        return False
    while 1:
        if pipe.returncode is None:
            pipe.poll()
        else:
            break
    if not 0 == pipe.returncode:
        logging.error('xdelta error')
        return False
    return True

#win version
if mswindows:
    def soft_link_file(origin,link):
        def valid_str(str1):
            str1 = str1.replace('"',r'\"')
            return str1
        import subprocess
        origin = valid_str(origin)
        link = valid_str(link)
        origin = '"' + origin + '"'
        link = '"' + link + '"'
        args = 'ln -s' + ' ' + origin + ' ' + link
        #args = ['ln','-s',origin,link]
        args1 = 'rm ' + link
        pipe1 = subprocess.Popen(args1,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)#check out reversion queitly
        pipe1.communicate()
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)#check out reversion queitly
        out,err = pipe.communicate()
        if 0 == pipe.returncode:
            return True
        else:#error
            logging.warning(err)
            logging.debug('origin is ' + origin)
            logging.debug('link is ' + link)
            return False
else:
    def soft_link_file(origin,link):
        import subprocess
        import logging
        args = ["ln","-s",origin,link]
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)#check out reversion queitly
        out,err = pipe.communicate()
        if 0 == pipe.returncode:
            return True
        else:#error
            logging.error(err)
            logging.error('origin is ' + origin)
            logging.error('link is ' + link)
            return False

#url:full svn url(chunk or branch)
#version(not revision):folder name
def check_out_version(url,folder):
    import subprocess
    args = ['svn','co','--force',url,folder]
    try:
        pipe = subprocess.Popen(args,bufsize = 0,\
            stdout = sys.stdout,\
            stderr = subprocess.STDOUT)
    except Exception as e:
        logging.error(str(e))
        return False
    while 1:
        if pipe.returncode is None:
            pipe.poll()
        else:
            break
    if not 0 == pipe.returncode:
        logging.error('check out of %s failed:%s'%(url))
        return False
    return True

#def export_version(url,folder):
#    import subprocess
#    args = ['svn','export','-q','--force',url,folder]
#    pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
#        stderr = subprocess.PIPE)#check out reversion queitly
#    out,err = pipe.communicate()
#    if 0 == pipe.returncode:
#        return True
#    else:#error
#        logging.error('export of %s failed:%s'%(url,err))
#        return False

def diff_between_urls(url1,url2): # r1 -> r2
    import subprocess
    args = ['svn','di','--summarize']
    old = ''.join(['--old=',url1])
    new = ''.join(['--new=',url2])
    args.append(old)
    args.append(new)
    rv = ''
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        logging.error(str(e))
        return None
    while 1:
        s = pipe.stdout.read()
        if s:
            rv += s
        if pipe.returncode is None:
            pipe.poll()
        else:
            break
    if not 0 == pipe.returncode:
        return None
    return rv

def combine_url_at_rev(url,revision):
    return ''.join([url,'@',revision])


#def get_svn_file_size(url,username,password):
#    import urllib2, base64
#    class HeadRequest(urllib2.Request):
#        def get_method(self):
#            return "HEAD"
#
#    request = HeadRequest(url)
#    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n','')
#    request.add_header("Authorization", "Basic %s" % base64string)
#    try:
#        result = urllib2.urlopen(request)
#        size = result.headers.get('content-length',None)
#        #seems svn apache don't give content length header when file's size is 0
#        if size is None:
#            return 0
#        return size
#    except:
#        return None
#    finally:
#        result.close()

def get_modified_from_svn_diff_line(s1):
    pattern = r"\s*M\s+(.+)$"
    return get_url_from_svn_line(s1,pattern)

def get_deleted_from_svn_diff_line(s1):
    pattern = r"\s*D\s+(.+)$"
    return get_url_from_svn_line(s1,pattern)

def get_added_from_svn_diff_line(s1):
    pattern = r"\s*A\s+(.+)$"
    return get_url_from_svn_line(s1,pattern)

def get_url_from_svn_line(s1,pattern):
    import re
    if 0 == len(s1):
        return None
    o1 = re.search(pattern,s1)
    if o1 is not None:
        rv = o1.group(1)
        if rv.endswith('\r'):
            rv = rv[:-1]
        return rv
    return None

def unicode_to_utf8(o1):
    if isinstance(o1,unicode):
        return o1.encode('utf-8')
    return o1

def my_quote_plus(url):
    import urllib
    return urllib.quote_plus(url).replace('+','%20')

def quote_path(path):
    l1 = path.split('/')
    l2 = []
    for each in l1:
        l2.append(my_quote_plus(each))
    return '/'.join(l2)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logname',help='set log file name')
    parser.add_argument('-j','--diffjson',help='diffs.json file name',\
        required=True)
    parser.add_argument('--verbose',help='print extra info',\
        action='store_true')
    parser.add_argument('--outputfolder',help='print extra info')
    args = parser.parse_args()
    if args.outputfolder is None:
        args.outputfolder = '../.portal'#parent folder
    return args

def main(slave = False,logname = None,diffjson = '',verbose = False,\
    outputfolder = '../.portal'):

    if slave:
        args_logname = logname
        args_diffjson = diffjson
        args_verbose = verbose
        args_outputfolder = outputfolder
    else:
        args = get_args()
        args_logname = args.logname
        args_diffjson = args.diffjson
        args_verbose = args.verbose
        args_outputfolder = args.outputfolder

    svn_user = 'db.zhang'
    svn_pwd = 'zkf123456'

    latest_diffs = {}

    if args_verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',\
        datefmt='%m/%d/%Y %I:%M:%S %p',\
        level=level,
        filename=args_logname)

    all_versions = {}

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
    versions = config_obj['versions']
    version1 = 1
    no_delta = False
    if len(versions['main']) == 1:
        no_delta = True 
    if not version1 in versions['main']:
        versions['main'].append(version1)
    newest_num = str(max(versions['main']))
    game_name = unicode_to_utf8(config_obj['game_name'])
    root_url = unicode_to_utf8(config_obj['svn_url'])
    armories_url = unicode_to_utf8(config_obj['armories_url'])
    package_mirrors = unicode_to_utf8(config_obj['package_mirrors'])
    base_mirrors = unicode_to_utf8(config_obj['base_mirrors'])
    patch_mirrors = unicode_to_utf8(config_obj['patch_mirrors'])
    appid = config_obj['appid']

    delta_folder = ''.join([appid,'/','base','/',newest_num])
    first_folder = ''.join([appid,'/','base','/','1'])
    tmp_folder = ''.join([appid,'/','.',appid])

    delta_folder = os.path.join(args_outputfolder,delta_folder)
    first_folder = os.path.join(args_outputfolder,first_folder)
    tmp_folder = os.path.join(args_outputfolder,tmp_folder)
        
    if not versions.has_key('main'):
        logging.error('must have a main version')
        return -1
    newest_version = 'main',newest_num
    for each in versions.keys():
        if versions[each] is None:
            continue
        for num in versions[each]:
            str_num = str(num)
            each = str(each)
            if (each,str_num) in all_versions:
                continue
            #r_num = util.find_revision(log,game_name,each,str_num)
            r_num = util.find_revision_from_armory_meta(armory_meta_obj,\
                str_num,each)
            if r_num is None:
                logging.error('failed to find revision %s of',str_num)
                return -1
            all_versions[each,str_num] = r_num

    #main 1st version num
    #first_num = util.find_revision(log,game_name,'main','1')
    first_num = util.find_revision_from_armory_meta(armory_meta_obj,'1','main')
    if first_num is None:
        logging.error('failed to find revision %s of',1)
        return -1

    #try:
    #    util.simple_remove_dir(tmp_folder)
    #except:
    #    pass
    #util.simple_make_dirs(tmp_folder)

    nv_url = combine_url_at_rev(util.combine_trunk_url(svn_url,''),\
        all_versions[newest_version])
    input_folder = delta_folder

    #try:
    #    util.simple_remove_dir(input_folder)
    #except:
    #    pass

    #input_folder = tmp_folder + '/' + 'main' + all_versions[newest_version]
    #if not check_out_version(nv_url,input_folder):
    #    return -1
    first_url = combine_url_at_rev(util.combine_trunk_url(svn_url,''),first_num)

    #always check out 1st version
    if not util.simple_path_exists(first_folder):
        logging.info('copy first version from local')
        util.simple_copy_folder('./trunk',first_folder)
    if not check_out_version(first_url,first_folder):
        return -1

    d_to_xdelta = {}

    def download_lastest_file(path):
        rel_name = os.path.join(input_folder,path)
        if util.simple_path_exists(rel_name):
            return
        folder_name,base_name = os.path.split(rel_name)
        util.simple_make_dirs(folder_name)
        tmp_http_url = util.convert_svnurl_to_httpurl(nv_url,root_url)#svn_url is root path
        if not tmp_http_url.endswith('/'):
            tmp_http_url += '/'
        download_url = tmp_http_url + quote_path(path)
        logging.info('latest: ' + download_url)
        logging.debug(nv_url)
        nv_svn_url = combine_url_at_rev(util.combine_trunk_url(svn_url,'') + \
            quote_path(path),\
            all_versions[newest_version])
        #logging.info(nv_svn_url)
        #logging.info(rel_name)
        #logging.info(util.simple_path_exists(rel_name))
        #util.export_svn_file_to_local(nv_svn_url,rel_name)
        
        rv = util.download_svn_file(download_url,rel_name,svn_user,svn_pwd)#download old file to folder
        if not rv:#retry
            rv = util.download_svn_file(download_url,rel_name,svn_user,svn_pwd)#download old file to folder

    lastest_changed = []

    for each in all_versions.keys():
        if each == newest_version:
            continue
        tmp_revision = all_versions[each]
        if each[0] == 'main':
            base_url = util.combine_trunk_url(svn_url,'')
        else:
            base_url = util.combine_branch_url(svn_url,each[0],'')
        tmp_url = combine_url_at_rev(base_url,tmp_revision)
        s1 = diff_between_urls(tmp_url,nv_url)
        logging.debug(s1)
        if s1 is not None:
            diff_to_newest_key = each[1] if each[0] == 'main' else None
            if diff_to_newest_key is not None:
                latest_diffs[diff_to_newest_key] = {}
                latest_diffs[diff_to_newest_key]['to_modify'] = {}
                latest_diffs[diff_to_newest_key]['to_delete'] = []
                latest_diffs[diff_to_newest_key]['to_add'] = []
            logging.info(''.join([each[0],each[1],'->',\
                newest_version[0],newest_version[1]]))
            l1 = s1.split('\n')
            for diff in l1:
                m1 = get_modified_from_svn_diff_line(diff)
                logging.debug('m1 is ' + str(m1))
                if m1 is not None:
                    attr = util.get_svn_url_attr(combine_url_at_rev(m1,all_versions[newest_version]))
                    assert(attr is not None)
                    #print 'attr is ',attr
                    if util.FOLDER == attr:
                        continue #on windows,blind to directory,just pass
                    if not m1.startswith(base_url):
                        assert(0)
                    m1 = m1.replace(base_url,'')
                    if not d_to_xdelta.has_key(each):
                        d_to_xdelta[each] = []
                    tmp_http_url = util.convert_svnurl_to_httpurl(tmp_url,root_url)#svn_url is root path
                    if not tmp_http_url.endswith('/'):
                        tmp_http_url += '/'
                    #d_to_xdelta[each].append((m1,tmp_http_url + m1))
                    rel_name = os.path.join(tmp_folder + '/' + each[0] + each[1]+'/',m1)
                    folder_name,base_name = os.path.split(rel_name)
                    util.simple_make_dirs(folder_name)
                    m1 = m1.decode(util.simple_get_encoding()).encode('utf-8')
                    if diff_to_newest_key is not None:
                        latest_diffs[diff_to_newest_key]['to_modify'][m1] = None
                    download_url = tmp_http_url + quote_path(m1)
                    tmp_svn_url = combine_url_at_rev(base_url + quote_path(m1),\
                        tmp_revision)
                    #logging.info(tmp_svn_url)
                    #logging.info(rel_name)
                    #util.export_svn_file_to_local(tmp_svn_url,rel_name)

                    logging.info(download_url)
                    rv = util.download_svn_file(download_url,rel_name,svn_user,svn_pwd)#download old file to folder
                    if not rv:#retry
                        rv = util.download_svn_file(download_url,rel_name,svn_user,svn_pwd)#download old file to folder

                    #also download the related latest version file
                    download_lastest_file(m1)

                    m1 = m1.replace('\\','/')
                    if m1 not in lastest_changed:
                        lastest_changed.append(m1)

                m2 = get_added_from_svn_diff_line(diff)
                if m2 is not None:
                    attr = util.get_svn_url_attr(combine_url_at_rev(m2,all_versions[newest_version]))
                    assert(attr is not None)
                    if util.FOLDER == attr:
                        continue
                    if diff_to_newest_key is not None:
                        m2 = m2.replace(base_url,'')
                        m2 = m2.decode(util.simple_get_encoding())
                        latest_diffs[diff_to_newest_key]['to_add'].append(m2)
                    download_lastest_file(m2)

                    m2 = m2.replace('\\','/')
                    if m2 not in lastest_changed:
                        lastest_changed.append(m2)

                m3 = get_deleted_from_svn_diff_line(diff)
                if m3 is not None:
                    if diff_to_newest_key is not None:
                        m3 = m3.replace(base_url,'')
                        m3 = m3.decode(util.simple_get_encoding())
                        latest_diffs[diff_to_newest_key]['to_delete'].append(m3)

    src_folders = []
    for each in d_to_xdelta.keys():
        version_name = each[1] if each[0] == 'main' else each[0] + '_' + each[1]
        t1 = each[0] + each[1],version_name
        src_folders.append(t1)

    logging.info(d_to_xdelta.keys())
    latest_diffs[newest_version[1]] = []
    latest_diffs['latest'] = newest_version[1]


    def make_diffs(file_name):
        if not file_name.find('.svn/') == -1:#ignore svn folder
            return
        coding = util.simple_get_encoding()
        entry1 = {}
        file_name = file_name.replace('\\','/')
        if file_name not in lastest_changed:
            return
        abs_input_name = input_folder + '/' + file_name
        entry1['size'] = util.simple_getsize(abs_input_name)#zero size input file
        entry1['name'] = file_name.decode(coding)
        if entry1['size'] != 0:
            entry1['hash'],entry1['crc32']= calc_md5(abs_input_name)
            srcs = []
            for each,version_name in src_folders:#each source folder,try to get delta
                src_file1 = tmp_folder + '/' + each + '/' + file_name
                if util.simple_path_exists(src_file1):#src exists
                    if util.simple_getsize(src_file1) != 0:#zero size file not having md5,skip it
                        src_md5 = calc_md5(src_file1)[0]
                        #if md5 already exist 
                        #or the same with input file,continue
                        output_name = ''.join([file_name,'-',version_name,'-',\
                            newest_version[1],'.delta'])
                        if src_md5 not in srcs and entry1['hash'] != src_md5:
                            if no_delta:
                                continue
                            logging.info('encoding...')
                            logging.info('input:' + abs_input_name)
                            logging.info('src:' + src_file1)
                            logging.info('output:' + output_name)
                            xdelta_code(abs_input_name,\
                                delta_folder + '/' + output_name,\
                                src_file1,1)#encode,generate a xdelta file
                            xdelta_size = util.simple_getsize(delta_folder +\
                                '/' + output_name)
                            #print each,type(each)
                            xdelta_dict = {}
                            #name should be a unicode object
                            xdelta_dict['name'] = output_name.decode(coding)
                            xdelta_dict['size'] = xdelta_size
                            xdelta_dict['hash'] = src_md5
                            srcs.append(xdelta_dict)
                            if each.startswith('main'):
                                latest_diffs[each[4:]]['to_modify'][file_name.decode(coding).encode('utf-8')] = xdelta_dict
            if len(srcs):
                entry1['deltas'] = srcs
        latest_diffs[newest_version[1]].append(entry1)
    
    latest_diffs['delta_folder'] = delta_folder
    latest_diffs['appid'] = appid

    walk.walkutil(input_folder,None,make_diffs)

    def replace_with_doubledot(path):
        import re
        return re.sub(r'[^/]+','..',path)
    
    base_folder = ''.join([appid,'/','base'])
    base_folder = os.path.join(args_outputfolder,base_folder).replace('\\','/')
    nv_list = util.get_svn_url_list(nv_url,True)
    for sth in nv_list:
        input_path = os.path.join(input_folder,sth).replace('\\','/')
        if util.simple_path_exists(input_path) and \
            sth.replace('\\','/') in lastest_changed:
            continue
        else:
            first_path = os.path.join(first_folder,sth).replace('\\','/')
            #files not change,make a soft link to 1st version file
            if util.simple_path_exists(first_path):
                if os.path.isfile(first_path):
                    tmp_path = first_path.replace(base_folder + '/1/','',1)
                    folder_name,base_name = os.path.split(tmp_path)
                    parent_folder_name = os.path.join(replace_with_doubledot(folder_name),'../1')
                    folder_name = os.path.join(parent_folder_name,folder_name)
                    tmp_path = os.path.join(folder_name,base_name).replace('\\','/')
                    soft_link_file(tmp_path,input_path)

                    #update diffs.json
                    coding = util.simple_get_encoding()
                    entry1 = {}
                    entry1['size'] = util.simple_getsize(first_path)#zero size input file
                    entry1['name'] = sth.decode(coding)
                    if entry1['size'] != 0:
                        entry1['hash'],entry1['crc32'] = calc_md5(first_path)
                    latest_diffs[newest_version[1]].append(entry1)

                else:
                    util.simple_make_dirs(input_path)
            else:
                pass
                #assert(0)
                tmp = sth
                tmp = tmp.decode(util.simple_get_encoding())
                download_lastest_file(tmp)
    
    
    diffjson_path = os.path.join(args_outputfolder,args_diffjson)
    f1 = open(diffjson_path,'w+b')#new json file
    json.dump(latest_diffs,f1,indent=4)#dump json
    f1.close()

    control_obj = {}
    control_obj['root'] = util.simle_join_path(armories_url,appid)
    control_obj['package_mirrors'] = []
    control_obj['patch_mirrors'] = []
    control_obj['base_mirrors'] = []
    for each in package_mirrors:
        control_obj['package_mirrors'].append(util.simle_join_path(each,appid))
    for each in patch_mirrors:
        control_obj['patch_mirrors'].append(util.simle_join_path(each,appid))
    for each in base_mirrors:
        control_obj['base_mirrors'].append(util.simle_join_path(each,appid))
    control_obj['latest'] = latest_diffs['latest']
    control_obj['base'] = {}
    control_obj['base'][newest_version[1]] = latest_diffs[newest_version[1]]
    for each in control_obj['base'][newest_version[1]]:
        if each.has_key('crc32'):
            each.pop('crc32')
        

    control_json_path = \
        os.path.join(args_outputfolder,appid + '/' + control_json)
    f1 = open(control_json_path,'w+b')#new json file
    json.dump(control_obj,f1,indent=4)#dump json
    f1.close()

    logging.info('armory generation successful')

if __name__ == "__main__":#main entry
    main()
