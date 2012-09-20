###appdata制作
1. 到此网站<http://www.sliksvn.com/en/download/>下载silksvn,svn的命令行工具
2. 安装silksvn,并在windows环境变量path中加入svn的bin目录
3. 签出<http://svn.gaia.org/elements/trunk>,编译工程
4. 将编译出的archivemaker.exe 放入sisium\armory\目录下
5. 在命令行中进入sisium\armory\目录,输入如下命令

        python appdata.py -o appdata.ana -u svn_user_name -a http://svn.gaia.org/armories
