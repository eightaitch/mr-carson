drop table if exists server;
create table server (
  id integer primary key autoincrement,
  host string not null,
  port string not null,
  username string not null,
  password string not null
);

drop table if exists tasks;
create table tasks (
  id integer primary key autoincrement,
  name string not null,
  local string not null,
  remote string not null,
  up bool not null
);
create index up_index on tasks (up);
