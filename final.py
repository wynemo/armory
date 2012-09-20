#!/usr/bin/env python
#coding:utf-8


import util.util as util
import logging
import json
import datetime


ARMORY_META = 'armory_meta.json'
MAIN_NAME = 'trunk'

def main():

    def clean():
        #restore
        util.simple_remove_file(ARMORY_META)
        util.update_path_to_revision()

    level = logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',\
        datefmt='%m/%d/%Y %I:%M:%S %p',\
        level=level)

    try:
        f = None
        f = open(ARMORY_META,'r+b')
        o = json.load(f)
        changed = False

        versions = []

        for each in o['info']:
            for foo in o['info'][each]:
                tmp_r = o['info'][each][foo]
                if tmp_r.startswith(r'$Rev'):
                    tmp_r = util.find_test_version(tmp_r)
                    o['info'][each][foo] = tmp_r
                    versions.append(foo.encode('utf-8'))
                    changed =True

        if not changed:
            logging.info('not find test version')
            exit(0)

        f.truncate(0)
        f.seek(0)
        o['date'] = str(datetime.datetime.now())
        json.dump(o,f,indent = 4)
        f.close()
        f = None

        commit_info = 'test version ' + str(versions) + ' -> final'

        to_commit = [ARMORY_META]
        rv = util.commit_folder(commit_info,to_commit)
        if rv:
            logging.info(str(versions) + ' test -> final successful')
        else:
            clean()
            logging.error('final fail')

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
