def walkutil(input_folder,folder_cbk=None,file_cbk=None,\
    exclude_folder_name=None):
    def walk(str1):#nestd function to walk dir
        import os,os.path
        #str1 = os.path.abspath(str1)#get absolute path
        for file in [file for file in \
            os.listdir(str1) if not file in [".",".."]]:
            nfile = os.path.join(str1,file)#combine path
            if os.path.isdir(nfile):#is folder
                if exclude_folder_name is not None and\
                    file.lower() == exclude_folder_name.lower():
                    continue
                if folder_cbk is not None:
                    folder_cbk(nfile)
                walk(nfile)#iter
            else:#or file
                nfile = nfile.replace('\\','/')#replace windows slash
                tmp_input_folder = input_folder.replace('\\','/')
                #get relative path
                file1 = nfile.replace(tmp_input_folder + '/','',1)
                if file_cbk is not None:
                    file_cbk(file1)
    walk(input_folder)


def folder_callback(folder_name):
    print folder_name

def file_callback(file_name):
    print file_name

def main():
    walkutil('.',folder_callback,file_callback,'.svn')
    print('-------------------------------------------')
    walkutil('.',folder_callback,file_callback)

if __name__ == '__main__':
    main()
