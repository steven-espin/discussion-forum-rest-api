drop table if exists users;
create table users (
  username text primary key,
  password text not null
);

INSERT INTO users VALUES('rickybobby', 'aliceInWonderLand');
INSERT INTO users VALUES('yeezus', 'iamagod');
INSERT INTO users VALUES('user', '123');

DROP TABLE IF EXISTS forums;
CREATE TABLE forums (
  forum_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  creator TEXT NOT NULL
);

INSERT INTO forums (name, creator) VALUES('Forum 1 Redis', 'rickybobby');
INSERT INTO forums (name, creator) VALUES('Forum 2 MongoDB', 'user');


drop table if exists threads;
create table threads (
  thread_id integer primary key autoincrement,
  title text not null,
  creator text not null,
  timestamp text not null,
  forum_id integer not null
);

INSERT INTO threads VALUES(1, "Does anyone know how to start Redis?", "Bob", "Wed, 26 Sep 2018 23:02:59 GMT", 1);
INSERT INTO threads VALUES(2, "Has anyone heard of Edis?", "Charlie", "Wed, 26 Sep 2018 23:03:59 GMT", 1);


drop table if exists posts;
create table posts (
  post_id integer primary key autoincrement,
  author text not null,
  text text not null,
  timestamp text not null,
  thread_id integer not null,
  forum_id integer not null
);

INSERT INTO posts VALUES(1, "Bob", "Does anyone know how to start Redis?", "Wed, 26 Sep 2018 23:02:59 GMT", 1, 1);
INSERT INTO posts VALUES(2, "Bob", "tried restarting your router?", "Wed, 26 Sep 2018 23:02:59 GMT", 1, 1);
INSERT INTO posts VALUES(3, "Bob", "Red is beautiful.", "Wed, 26 Sep 2018 23:02:59 GMT", 1, 1);
INSERT INTO posts VALUES(4, "Charlie", "Has anyone heard of Edis?", "Wed, 26 Sep 2018 23:03:59 GMT", 2, 1);
INSERT INTO posts VALUES(5, "Charlie", "Nope I have never heard of edis, but i have heard of Redis", "Wed, 26 Sep 2018 23:07:59 GMT", 2, 1);
