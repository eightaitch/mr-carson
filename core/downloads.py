import sqlite3
import os
from ftplib import *

# logger
def log(message, severity=0):
    print message

def is_file(ftp, filename):
    try:
        ftp.size(filename) is not None
        return True
    except:
        return False

def download_file(ftp, torrent, remote, local):
    print 'try: ' + os.path.normpath(local+'/'+torrent)
    f = open(os.path.normpath(local+'/'+torrent), 'wb')
    print 'done: ' + os.path.normpath(local+'/'+torrent)
    ftp.retrbinary("RETR " + os.path.join(remote+'/'+torrent), f.write)
    f.close()
    
def download_folder(ftp, torrent, remote, local):
    print 'cwd: ' + remote
    print 'cwd: ' + torrent 
    ftp.cwd(remote)    
    ftp.cwd(torrent)
    os.chdir(local)
    os.mkdir(torrent)
    os.chdir(torrent)
    filelist = ftp.nlst()
    ftppwd = ftp.pwd()
    oscwd = os.getcwd()
    for file in filelist:
        print 'next: ' + file
        if is_file(ftp, file):
            print 'dl file: ' + file + ' ' + ftppwd + ' ' + oscwd
            download_file(ftp, file, ftppwd, oscwd)
        else:
            print 'dl folder: ' + file + ' ' + ftppwd + ' ' + oscwd
            download_folder(ftp, file, ftppwd, oscwd)

def run_downloads(db):
    # server settings
    server_config = db.execute('select * from server').fetchone()
    # get download tasks from db
    downloads = db.execute('select * from tasks where up=0').fetchall()
    db.close()

    try:
        ftp = FTP()
        ftp.connect(server_config[1], server_config[2])
        ftp.login(server_config[3], server_config[4])
    except Exception, e:
        log(e)
        return False
    
    # check download directories 
    for download in downloads:
        remote = download[3]
        local = download[2]
        ftp.cwd(remote)   
        filelist = ftp.nlst()
        for torrent in filelist:
            if is_file(ftp, torrent):
                try:
                    download_file(ftp, torrent, remote, local)
                    log(download[3] + torrent + ' moved to ' + download[2] + torrent) 
                except Exception, e:
                    log(e)
            else:
                try:
                    download_folder(ftp, torrent, remote, local)
                    log(download[3] + torrent + ' moved to ' + download[2] + torrent) 
                except Exception, e:
                    log(e)
    ftp.close()
    return True

""" end downloads """ 


