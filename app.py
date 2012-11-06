import sys
sys.path.append('libs/')
import sqlite3
from flask import *

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

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

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
        return render_template('server.html')

@app.route('/server/', methods=['POST'])
def edit_server():
    g.db.execute('delete from server')
    g.db.execute('insert into server (host, port, username, password) values (?, ?, ?, ?)',
                 [request.form['host'],
                  request.form['port'],
                  request.form['username'],
                  request.form['password']])
    g.db.commit()
    flash('Server settings saved!')
    return redirect(url_for('server'))

if __name__ == '__main__':
    app.run()
