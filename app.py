import sys
sys.path.append('libs/')
from sqlalchemy import *
from sqlalchemy.sql import *

engine = create_engine('sqlite:///sqlite/mr-carson.db', echo=True)

metadata = MetaData()
server = Table('server',
               metadata,
               Column('id', Integer, primary_key=True),
               Column('host', String),
               Column('port', String),
               Column('username', String),
               Column('password', String))

ins = server.insert()
#print str(ins)

conn = engine.connect()
#print conn

import web
web.app.run()
