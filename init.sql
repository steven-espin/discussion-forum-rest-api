drop table if exists forums;
create table forums (
  id integer primary key autoincrement,
  author text not null,
  creator text not null
);

INSERT INTO forums VALUES(1, 'redis', 'alice');
INSERT INTO forums VALUES(2, 'mongodb', 'bob');
