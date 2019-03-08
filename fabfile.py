# -*- coding: utf-8 -*-
from os import path as opath
import os, glob, tarfile, logging

from fabric.api import local, env, run, cd, put, abort
from fabric.contrib.files import os as fos
from fabric.contrib.files import exists as fexists

#env.hosts = ['172.16.0.106', ]
#env.user = ''
#env.password = ''
#env.key_filename = '~/.ssh/id_rsa_work'
# @todo auth method
logger = logging.getLogger('grafana.install')

Download_Path = 'pip-cache'
Requirements_File = 'requirements.txt'
PyPi_URL = 'http://172.16.0.104:3141/threathunter/dev'
Virtual_Path = 'venv'

def init():
    """
    从部署脚本安装的接口
    """
    prepare_env()
    extract_swagger()
    extract_grafana()
    dep_web_front()

def prepare_env():
    """
    upper op:1. git clone from gitlab, 2. download from local pypi and extract 
    
    1. virtualenv 
    2. download packages from local pypi
    3. install packages from local cache
    """
    # 创建虚拟环境
    if not opath.exists(Virtual_Path) and local('virtualenv %s' % Virtual_Path).failed:
        abort('不能创建virtualenv 虚拟环境！')
    
    if not opath.exists(Download_Path) and local('mkdir %s' % Download_Path).failed:
        abort('不能创建pip下载缓存文件夹 pip-cache')
    
    # 从内网pypi下载依赖包们
    if local('%s/bin/pip install -d %s --no-index --find-links=%s -r %s' % (Virtual_Path, Download_Path, PyPi_URL, Requirements_File)).failed:
        abort('不能从内网pypi下载依赖包')
    
    # 安装所有本地的依赖包
    if local('/bin/bash install.sh').failed:
        abort('安装本地python packages失败。')

def install_components(pattern, install_path):
    """
    从Download_Path 查找符合pattern的第一个压缩包, 解压之后移动到install_path
    """
    tarfile_path = find_tarfile(opath.join(Download_Path, pattern)) # ./pip-cache/$pattern-x.x.x.tar.gz ,find ./pip-cache -name pattern-*.tar.gz
    extract_path = find_tarfile_extract_path(tarfile_path) # pattern-x.x.x, tar xzf x.tar.gz | head -n1
    
    if extract_path:
        extract_result = local("tar xzf %s" % (tarfile_path, ))
        
        if extract_result.failed:
            abort('cant not extract %s' % tarfile_path)
        
        if local("mv %s %s" % (extract_path, install_path)).failed:
            abort('can not move %s from %s to %s' % (pattern, extract_path, install_path))

def extract_swagger():
    install_components('swagger-*.tar.gz', 'nebula/middleware/tornado_rest_swagger/assets')

def extract_grafana():
    install_components('grafana-*.tar.gz', 'nebula/grafana_app')

def dep_web_front():
    pattern = 'nebula_web_frontend-*.tar.gz'
    tarfile_path = find_tarfile(opath.join(Download_Path, pattern)) # ./pip-cache/nebula_web_frontend-x.x.x.tar.gz
    extract_path = find_tarfile_extract_path(tarfile_path) # nebula_web_frontend-x.x.x
    
    FrontEnd_Install_Path = 'target/nebula/' # @todo nebula
    move_dirs = ['statics', 'templates']
    if extract_path:
        extract_result = local("tar xzf %s" % (tarfile_path, ))
        
        if extract_result.failed:
            abort('cant not extract %s' % tarfile_path)

        for _ in move_dirs:
            if local("mv %s %s" % ( opath.join(extract_path, _),
                                    opath.join(FrontEnd_Install_Path , _))).failed:
                abort('can not move nebula_web_frontend %s to %s' % (_, FrontEnd_Install_Path))
#        cleanup('nebula_web_frontend', tarfile_path)

def cleanup(compenent_name, filename=None, dirname=None):
    if filename is None and dirname is None:
        # nothing to cleanup
        return
    if local("rm -rf %s" % (filename or dirname)).failed:
        abort('install %s success, but can not move tar.gz file, please remove first before pip install local packages.' % compenent_name)

def find_tarfile_extract_path(tarfile_path):
    if not opath.exists(tarfile_path):
        abort("%s is not exists, can not continue." % tarfile_path)
    with tarfile.open(tarfile_path, mode='r') as f:
        members = f.getmembers()
        if members:
            return members[0].path

def find_tarfile(pattern):
    p = glob.glob(pattern)
    if p:
        return p[0]
    return None
