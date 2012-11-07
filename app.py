import os
import sys
sys.path.append('libs/')
import sqlite3
import socket
from flask import *
from ftplib import *
from apscheduler.scheduler import *

# configuration
DATABASE = 'sqlite/mr-carson.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# scheduler
sched = Scheduler()

# logger
def log(message, severity=0):
    print message

""" uploads """
@sched.interval_schedule(seconds=5)
def run_uploads():
    # connect to db
    db = sqlite3.connect(app.config['DATABASE'])

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

""" downloads """
def is_file(ftp, filename):
    try:
        ftp.size(filename) is not None
        return True
    except:
        return False

def download_file(torrent, remote, local):
    
def run_downloads():
    # connect to db
    db = sqlite3.connect(app.config['DATABASE'])
    # server settings
    server_config = db.execute('select * from server').fetchone()
    # get download tasks from db
    downloads = db.execute('select * from tasks where up=0').fetchall()

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
            if is_file(torrent):
                download_file(torrent, remote, local)
            else:
                download_folder(torrent, remote, local)


""" end downloads """ 

# start
#sched.start()
sched.shutdown()

def flash_error(str):
    flash(u'Error! ' + str, 'text-error')

def flash_success(str):
    flash(u'Success! ' + str, 'text-success')

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/')
@app.route('/server/')
def server():
    server_config = g.db.execute('select * from server').fetchone()
    if server_config != None:
        # server entry exists
        #values = dict('host'=server_config[0])
        server = dict(host=server_config[1],
                 port=server_config[2],
                 username=server_config[3],
                 password=server_config[4])
        return render_template('server.html', server=server)
    else:
        #server needs configuration    
        return render_template('server.html', server=None)

@app.route('/server/', methods=['POST'])
def edit_server():
    # truncate server table (only one entry for now)
    g.db.execute('delete from server')
    # save values to db
    g.db.execute('insert into server (host, port, username, password) values (?, ?, ?, ?)',
                 [request.form['host'],
                  request.form['port'],
                  request.form['username'],
                  request.form['password']])
    g.db.commit()
    # attempt to connect to server
    ftp = FTP()
    try:
        port = int(request.form['port'])
        ftp.connect(request.form['host'], port, 5)
        ftp.login(request.form['username'], request.form['password'])
    except ValueError:
        flash_error('make sure \'Port\' is a valid integer')
    except socket.timeout:
        flash_error('unable to connect to server: timeout')
    except socket.gaierror:
        flash_error('make sure \'host\' is formatted correctly')
    else:
        flash_success('connection established')
    return redirect(url_for('server'))

@app.route('/tasks/', methods=['GET'])
def tasks():
    # populate form if GET sent
    results = g.db.execute('select * from tasks where up=1 order by name asc')
    uploads = [dict(id=row[0],
                    name=row[1],
                    local=row[2],
                    remote=row[3],
                    up=row[4]) for row in results.fetchall()]
    results = g.db.execute('select * from tasks where up=0 order by name asc')
    downloads = [dict(id=row[0],
                    name=row[1],
                    local=row[2],
                    remote=row[3],
                    up=row[4]) for row in results.fetchall()]
    return render_template('tasks.html', uploads=uploads, downloads=downloads, edit=request.args)

@app.route('/tasks/', methods=['POST'])
def add_task():
    # descriptive name?
    if request.form['name'].strip() == '':
        flash_error('choose a descriptive name!') 
        return redirect(url_for('tasks', name=request.form['name'],
                                         local=request.form['local'],
                                         remote=request.form['remote'],
                                         up=request.form['up']))
    # require local trailing slash 
    if all(c != request.form['local'][-1:] for c in ['/', '\\']):
        flash_error('make sure your local path ends with a trailing slash!') 
        return redirect(url_for('tasks', name=request.form['name'],
                                         local=request.form['local'],
                                         remote=request.form['remote'],
                                         up=request.form['up']))
    # require remote trailing slash
    if all(c != request.form['remote'][-1:] for c in ['/', '\\']):
        flash_error('make sure your remote path ends with a trailing slash!') 
        return redirect(url_for('tasks', name=request.form['name'],
                                         local=request.form['local'],
                                         remote=request.form['remote'],
                                         up=request.form['up']))
    # valid local path?
    try:
        file = open(request.form['local'] + '.mr-carson.tmp', 'w+')
        file.close()
        os.remove(request.form['local'] + '.mr-carson.tmp')
    except:
        flash_error('trouble accessing \'' + request.form['local'] + '\'') 
        return redirect(url_for('tasks', name=request.form['name'],
                                         local=request.form['local'],
                                         remote=request.form['remote'],
                                         up=request.form['up']))
    # valid remote path?
    server_config = g.db.execute('select * from server').fetchone()
    if server_config != None:
        # server entry exists
        server = dict(host=server_config[1],
                 port=server_config[2],
                 username=server_config[3],
                 password=server_config[4])
    else:
        # no server entry
        flash_error('let\'s configure your ftp server!') 
        return redirect(url_for('server'))
    # try ftp to supplied directory
    try:
        ftp = FTP()
        port = int(server['port'])
        ftp.connect(server['host'], port, 5)
        ftp.login(server['username'], server['password'])
        ftp.cwd(request.form['remote'])
    except:
        flash_error('unable to access \'' + request.form['remote'] + '\'') 
        return redirect(url_for('tasks', name=request.form['name'],
                                         local=request.form['local'],
                                         remote=request.form['remote'],
                                         up=request.form['up']))
    # save values to db
    g.db.execute('insert into tasks (name, local, remote, up) values (?, ?, ?, ?)',
                 [request.form['name'],
                  request.form['local'],
                  request.form['remote'],
                  request.form['up']])
    g.db.commit()
    flash_success('task tested and saved')
    return redirect(url_for('tasks'))

@app.route('/tasks/delete/<task_id>')
def delete_task(task_id):
    g.db.execute('delete from tasks where id=:id', {'id': task_id})
    g.db.commit()
    flash_success('task deleted!')
    return redirect(url_for('tasks'))

@app.route('/log/')
def log():
    return render_template('log.html')

if __name__ == '__main__':
    app.run()
