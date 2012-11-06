drop table if exists server;
create table server (
  id integer primary key autoincrement,
  host string not null,
  port string not null
  username string not null
  password string not null
);
