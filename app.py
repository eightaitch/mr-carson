from __future__ import with_statement
import os
import sys
sys.path.append('libs/')
import sqlite3
import socket
from flask import *
from ftplib import *
from werkzeug import *
from apscheduler.scheduler import *
import uploads
import downloads
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack

# configuration
DATABASE = os.path.normpath('sqlite/mr-carson.db')
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

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    return sqlite3.connect(app.config['DATABASE'])
    #top = _app_ctx_stack.top
    #if not hasattr(top, 'sqlite_db'):
    #    top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
    #return top.sqlite_db

@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

#sched.add_interval_job(uploads.run_uploads, seconds=1)
sched.add_interval_job(downloads.run_downloads, args=[app.config['DATABASE']], seconds=1)

# start
sched.start()
#sched.shutdown()

def flash_error(str):
    flash(u'Error! ' + str, 'text-error')

def flash_success(str):
    flash(u'Success! ' + str, 'text-success')

@app.route('/')
@app.route('/server/')
def server():
    db = get_db()
    server_config = db.execute('select * from server').fetchone()
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
    db = get_db()
    # truncate server table (only one entry for now)
    db.execute('delete from server')
    # save values to db
    db.execute('insert into server (host, port, username, password) values (?, ?, ?, ?)',
                 [request.form['host'],
                  request.form['port'],
                  request.form['username'],
                  request.form['password']])
    db.commit()
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
    db = get_db()
    # populate form if GET sent
    results = db.execute('select * from tasks where up=1 order by name asc')
    uploads = [dict(id=row[0],
                    name=row[1],
                    local=row[2],
                    remote=row[3],
                    up=row[4]) for row in results.fetchall()]
    results = db.execute('select * from tasks where up=0 order by name asc')
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
    db = get_db()
    server_config = db.execute('select * from server').fetchone()
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
    db.execute('insert into tasks (name, local, remote, up) values (?, ?, ?, ?)',
                 [request.form['name'],
                  request.form['local'],
                  request.form['remote'],
                  request.form['up']])
    db.commit()
    flash_success('task tested and saved')
    return redirect(url_for('tasks'))

@app.route('/tasks/delete/<task_id>')
def delete_task(task_id):
    db = get_db()
    db.execute('delete from tasks where id=:id', {'id': task_id})
    db.commit()
    flash_success('task deleted!')
    return redirect(url_for('tasks'))

@app.route('/log/')
def log():
    db = get_db()
    return render_template('log.html')

if __name__ == '__main__':
    app.run()
