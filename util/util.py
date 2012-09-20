import logging
import sys
import os.path
import binascii

FOLDER = 0
FILE = 1


#svn_url,svn container root url
def combine_trunk_url(svn_url,path):
    return ''.join([svn_url,'/trunk/',path])

def combine_branch_url(svn_url,branch_name,path):
    return ''.join([svn_url,'/branches/',branch_name,'/',path])

def convert_svnurl_to_httpurl(url,root_url):
    import re
    if not root_url.endswith('/'):
        root_url += '/'
    rel_path = url.replace(root_url,'')
    pattern1 = re.compile(r'(.+)@([0-9]+)') 
    o1 = re.search(pattern1,rel_path)
    file_path = o1.group(1)
    revision = o1.group(2)
    return root_url + '!svn/bc/' + revision + '/' + file_path
#convert_svnurl_to_httpurl('https://192.168.4.3/svn/sisium/trunk/doc/diff_define.md@62',\
#   'https://192.168.4.3/svn/sisium')    

def simple_path_exists(path1):
    import os.path
    return os.path.exists(path1)

def simple_remove_dir(dir1):
    import shutil
    shutil.rmtree(dir1)
    
def simple_make_dirs(path1):
    import os
    if not simple_path_exists(path1):
        os.makedirs(path1)    
    
def simple_get_encoding():#get system encoding
    import sys
    default_encoding = sys.getfilesystemencoding()
    if default_encoding.lower() == 'ascii':
        default_encoding = 'utf-8'
    return default_encoding
    
def simple_copy(src1,dst1):
    import shutil
    shutil.copy(src1,dst1) 

def simple_copy_folder(src1,dst1):
    import shutil
    shutil.copytree(src1,dst1) 
    
def simple_move(src1,dst1):
    import shutil
    shutil.move(src1,dst1) 
    
def simple_getsize(path1):
    import os.path
    return os.path.getsize(path1)    

def simple_remove_file(path1):
    import os
    os.remove(path1)

def download_svn_file(url,out_file,username,password):
    import urllib2
    import base64
    import time
    import os.path
    import datetime

    last_modified = None
    out_file = out_file.replace('\\','/')
    logging.debug('-------- out_file is ' + out_file)
    if simple_path_exists(out_file):
        try:
            last_modified = get_file_modified(out_file)
            logging.debug('------- last_modified is ' + last_modified)
        except:pass
    buff_size = 1024*64
    request = urllib2.Request(url)
    base64string =\
        base64.encodestring('%s:%s' % (username, password)).replace('\n','')
    request.add_header("Authorization", "Basic %s" % base64string)
    if last_modified is not None:
        request.add_header("if-modified-since", last_modified)
        print 'last_modified is ',last_modified
        
    result = None
    f1 = None
    try:
        result = urllib2.urlopen(request)
        size = result.headers.get('content-length',None)
        if size is None:
            size = 0
        remote_last_modified = result.headers.get('last-modified',None)
        if remote_last_modified is not None:
            GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
            last_modified_datetime = datetime.datetime.strptime(remote_last_modified,\
                GMT_FORMAT)
            remote_last_modified = last_modified_datetime.strftime('%Y%m%d%H%M.%S')
        bar = SimpleProgressBar(long(size))
        f1 = open(out_file,'w+b')
        while True:
            s1 = result.read(buff_size)
            if len(s1) == 0:
                bar.done()
                break    
            bar.update_received(long(len(s1)))
            f1.write(s1)
        if f1 is not None:
            f1.close()
        if remote_last_modified is not None:
            set_file_modified_time(out_file,remote_last_modified)
        return True
    except Exception as e:
        logging.warning('download %s failed:%s'%(out_file,str(e)))
        return False
    finally:
        if f1 is not None:
            f1.close()
        if result is not None:
            result.close()

def set_file_modified_time(file_name,modified_time):
    args = ['touch','-m','-t',modified_time,file_name]
    return run_args(args)

def run_args(args):
    import subprocess
    try:
        pipe = subprocess.Popen(args,bufsize = 0)
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

def list_svn_url(url,recursive = False):
    import subprocess
    args = ['svn','ls',url] if not recursive else ['svn','ls','-R',url]
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        logging.error(str(e))
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        return out
    else:#error
        logging.error('list svn url of %s failed:%s'%(url,err))
        return None            

def cat_to_other(src,dst):
    import subprocess
    src = src.replace('\\','/')
    dst = dst.replace('\\','/')
    cmd = ''.join(['cat ',src,' ','>> ',dst])
    args = ['sh',"-c",cmd]
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        logging.error(str(e))
        return False            
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        return True
    else:#error
        print err
        return False            

def get_file_modified(file_name):
    import subprocess
    import datetime
    cmd = ''.join(['stat ',file_name,' ',r"|grep Modify|sed 's/Modify:\s*\(.*\)\..*/\1/'"])
    args = ['sh',"-c",cmd]
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        logging.error(str(e))
        return None            
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        out =  out.replace('\r','').replace('\n','')
        if out:
            fmt = '%Y-%m-%d %H:%M:%S'
            return datetime.datetime.strptime(out,fmt).strftime('%a, %d %b %Y %H:%M:%S GMT')
        return None
    else:#error
        print err
        return None            

def get_svn_url_list(url,recursive = False):
    l1 = []
    buffer1 = list_svn_url(url,recursive)
    if buffer1 is not None:
        list1 = buffer1.splitlines()
        for sth in list1:
            sth = sth.strip().replace('\r','').replace('\n','')
            if 0 == len(sth):
                continue
            l1.append(sth)
    return l1

def find_revision(log,game_name,name,version):#from commit log,find revision
    import re
    pattern = ''.join([r'r([0-9]+).*\r*\n\r*\n#',game_name,' ','.*',\
        name,':',version,'[^0-9]'])
    flag = re.I
    o1 = re.search(pattern,log,flag)
    logging.debug('pattern is ' + pattern)
    logging.debug('log is ' + log)
    if o1 is not None:
        return o1.group(1)
    return None

def find_versions(log,game_name,name):
    #find sorted versions
    import re
    pattern = ''.join([r'r[0-9]+.*\r*\n\r*\n#',game_name,' ','.*',\
        name,':','([0-9]+)'])
    flag = re.I
    o1 = re.finditer(pattern,log,flag)
    l1 = []
    if o1 is not None:
        for each in o1:
            l1.append(int(each.group(1)))
        if l1:#elements >= 1
            l1.sort()
        return l1
    else:
        return None

#url,root url,https://192.168.4.3/svn/sisium1
def get_log(url):
    import subprocess
    args = ['svn','log',url]
    logging.debug('svn log url is ' + url)
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        print e
        return None
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        return out
    else:#error
        logging.error('get log of %s failed:%s'%(url,err))
        return None

def commit_folder(info='',folder=None):
    import subprocess
    args = ['svn','ci']
    if folder is not None:
        if not isinstance(folder,list):
            logging.error('error paras in commit_folder,should be list')
            assert(0)
        args.extend(folder)
    args.append('-m"' + info + '"')
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
    

def get_revision_by_path(path):
    import subprocess
    fmtstr = "svn info %s|grep Revision|sed 's/Revision:\s\s*//'"
    cmd = fmtstr % path
    args = ['sh',"-c",cmd]
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        print e
        return None
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        return out.replace('\n','')
    else:#error
        print err
        return None
#get_revision_by_path('base/1')

def get_game_svn_url(path):
    import subprocess
    fmtstr = ''.join(["svn info %s|","grep URL|",\
        "sed 's/^URL:\s\s*//'|","sed 's/\(.*\)\/trunk$/\\1/'"])
    cmd = fmtstr % path
    args = ['sh',"-c",cmd]
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        print e
        return None
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        return out.replace('\n','')
    else:#error
        print err
        return None
#get_game_svn_url('base/1')      

def rm_files(str1):
    import subprocess
    args = ['rm',str1]
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        logging.error(e)
    out,err = pipe.communicate()
    if not 0 == pipe.returncode:
        logging.debug(err)

def get_svn_url_attr(url):
    import subprocess
    import re
    flag = re.I|re.M
    args = ['svn','info']
    pattern = r'^Node\s*Kind:\s*(\w+)'#begin of line
    args.append(url)
    #print args
    logging.debug(args)
    pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
        stderr = subprocess.PIPE)
    if 0 == pipe.wait():
        s1 = pipe.stdout.read()
        o1 = re.search(pattern,s1,flag)
        if o1 is not None:
            if o1.group(1).lower() == 'file':
                return FILE
            if o1.group(1).lower() == 'directory':
                return FOLDER
    else:
        logging.error('get attirbute of %s failed:%s'%(url,pipe.stderr.read()))
    return None

def get_svn_folder_status(dir1):
    import subprocess
    args = ['svn','st',dir1]
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        print e
        return None
    out,err = pipe.communicate()
    if not 0 == pipe.returncode:
        print err
        return None
    return out

#find M A D
def svn_folder_has_change(dir1):
    import re
    out = get_svn_folder_status(dir1)
    if out is None:
        return False
    list1 = out.splitlines()
    pattern = r'^\s?[MAD].+'
    for sth in list1:
        o = re.search(pattern,out,re.M)
        if o is not None:
            return True
    return False
#svn_folder_has_change('.')

def update_path_to_revision(path=None,revision=None):
    import subprocess
    import sys
    args = ['svn','up']
    if path is not None:
        args.append(path)
    if revision is not None:
        args.append('-r')
        args.append(revision)
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
#update_path_to_revision('base/1','81')

def export_svn_file_to_local(url,filename):
    import subprocess
    args = ['svn','export',url,filename]
    logging.debug(args)
    try:
        pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
            stderr = subprocess.PIPE)
    except Exception as e:
        print e
        return False
    out,err = pipe.communicate()
    if not 0 == pipe.returncode:
        print err
        return False
    return True

def find_test_version(str1):
    import re
    pattern = r'[$]Rev:\s*([0-9]+)\s*[$]'
    o = re.search(pattern,str1)
    if o is not None:
        return o.group(1)
    return None

def find_verions_from_armory_meta(obj,name='main'):
    l1 = []
    if obj.has_key('info') and obj['info'].has_key(name):
        for each in obj['info'][name]:
            l1.append(each)
        return l1 if l1 else None
    return None

def find_revision_from_armory_meta(obj,version,name='main'):
    if obj.has_key('info') and obj['info'].has_key(name):
        if obj['info'][name].has_key(version):
            rnumstr = obj['info'][name][version]
            if rnumstr.startswith(r'$Rev'):
                return find_test_version(rnumstr)
            else:
                return rnumstr
    return None

def simle_join_path(path1,path2):
    if path2.startswith('/') or path2.startswith('\\'):
        path2 = path2[1:]
    return os.path.join(path1,path2).replace('\\','/')

def make_archive(folder,output = None,vol_size = 90*1024*1024):
    import subprocess
    exe_name = 'archivemaker.exe'
    module_path = os.path.dirname(__file__)
    parent_path = \
        os.path.abspath(os.path.join(module_path, os.path.pardir))
    tmp_name = os.path.join(parent_path,exe_name)
    logging.debug('tmp_name is ' + tmp_name)
    args = [tmp_name,'/makear',folder]
    if output is not None:
        args.append('/output')
        args.append(output)
        args.append('/volsize')
        args.append(str(vol_size))
    pipe = subprocess.Popen(args,bufsize = 4096,stdout = subprocess.PIPE,\
        stderr = subprocess.PIPE)#check out reversion queitly
    out,err = pipe.communicate()
    if 0 == pipe.returncode:
        return True
    else:#error
        logging.error('make archive of %s failed'%(folder))
        return False

def crc32(file_name):
    prev = 0
    f = None
    try:
        f = open(file_name,"rb")
        for eachLine in f:
            prev = binascii.crc32(eachLine, prev)
        #return "%X"%(prev & 0xFFFFFFFF)
        return prev & 0xFFFFFFFF#return an integar
    except Exception as e:
        print e
        return None
    finally:
        if f is not None:f.close()        

class SimpleProgressBar:
    def __init__(self, total_size, total_pieces=1):
        self.displayed = False
        self.total_size = total_size
        self.total_pieces = total_pieces
        self.current_piece = 1
        self.received = 0
    def update(self):
        self.displayed = True
        bar_size = 40
        percent = self.received*100/self.total_size
        if percent > 100:
            percent = 100
        dots = bar_size * percent / 100
        plus = percent - dots / bar_size * 100
        if plus > 0.8:
            plus = '='
        elif plus > 0.4:
            plu = '>'
        else:
            plus = ''
        bar = '=' * dots + plus
        bar = '{0:>3}%[{1:<40}] {2}/{3}'.format(percent, bar, self.current_piece, self.total_pieces)
        sys.stdout.write('\r'+bar)
        sys.stdout.flush()
    def update_received(self, n):
        self.received += n
        self.update()
    def update_piece(self, n):
        self.current_piece = n
    def done(self):
        if self.displayed:
            print
            self.displayed = False
