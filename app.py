import sys
sys.path.append('libs/')
import sqlite3
import socket
from flask import *
from ftplib import *

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

@app.route('/tasks/')
def tasks():
    results = g.db.execute('select * from tasks where up=1 order by name asc')
    uploads = [dict(name=row[1],
                    local=row[2],
                    remote=row[3],
                    up=row[4]) for row in results.fetchall()]
    results = g.db.execute('select * from tasks where up=0 order by name asc')
    downloads = [dict(name=row[1],
                    local=row[2],
                    remote=row[3],
                    up=row[4]) for row in results.fetchall()]
    return render_template('tasks.html', uploads=uploads, downloads=downloads)

@app.route('/tasks/', methods=['POST'])
def add_task():
    # save values to db
    g.db.execute('insert into tasks (name, local, remote, up) values (?, ?, ?, ?)',
                 [request.form['name'],
                  request.form['local'],
                  request.form['remote'],
                  request.form['up']])
    g.db.commit()
    return redirect(url_for('tasks'))
 
@app.route('/log/')
def log():
    return 'log'

if __name__ == '__main__':
    app.run()
