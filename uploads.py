import sqlite3
import os
from ftplib import *

# logger
def log(message, severity=0):
    print message

def run_uploads():
    # get upload tasks from db
    uploads = db.execute('select * from tasks where up=1').fetchall()

    # see if anything requires upload
    do_upload = False
    for upload in uploads:
        if len(os.listdir(upload[2])) != 0:
            do_upload = True
            break 
        
    # do upload            
    if do_upload:

        # connect to ftp server
        server_config = db.execute('select * from server').fetchone()
        db.close()
        try:
            ftp = FTP()
            ftp.connect(server_config[1], server_config[2])
            ftp.login(server_config[3], server_config[4])
        except Exception, e:
            log(e)
            return False

        # store .torrent files 
        for upload in uploads:
            try:
                ftp.cwd(upload[3])
                filelist = os.listdir(upload[2])
                for torrent in filelist:
                    try:
                        f = open(upload[2] + torrent, 'rb')
                        ftp.storbinary("STOR " + torrent, f)
                        f.close()
                        os.remove(upload[2] + torrent)      
                        log(upload[2] + torrent + ' moved to ' + upload[3] + torrent) 
                    except Exception, e:
                        log(e) 
                        log('could not move '+upload[2]+torrent+' to '+upload[3]+torrent, 2) 
            except Exception, e:
                log(e) 

        # close connection
        ftp.quit()

    else:
        db.close()

    return True
""" end uploads"""

