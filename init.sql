drop table if exists users;
create table users (
  username text primary key,
  password text not null
);

INSERT INTO users VALUES('rickybobby', 'aliceInWonderLand');
INSERT INTO users VALUES('yeezus', 'iamagod');

DROP TABLE IF EXISTS forums;
CREATE TABLE forums (
  forum_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  creator TEXT NOT NULL
);

INSERT INTO forums (name, creator) VALUES('Forum 1', 'alice');
INSERT INTO forums (name, creator) VALUES('Forum 2', 'bob');
INSERT INTO forums (name, creator) VALUES('Forum 3', 'scoop');


drop table if exists threads;
create table threads (
  thread_id integer primary key autoincrement,
  title text not null,
  creator text not null,
  timestamp text not null,
  forum_id integer not null
);

INSERT INTO threads VALUES(1, "Thread 1 Under Forum 2", "Bob", "Tue", 2);
INSERT INTO threads VALUES(2, "Thread 2 Under Forum 2", "Charlie", "wed", 2);
INSERT INTO threads VALUES(3, "Thread 1 Under Forum 3", "Charlie", "wed", 3);


drop table if exists posts;
create table posts (
  post_id integer primary key autoincrement,
  author text not null,
  text text not null,
  timestamp text not null,
  thread_id integer not null,
  forum_id integer not null
);

INSERT INTO posts VALUES(1, "Bob", "Post 1 Under thread 1 and Forum 2", "Tue", 1, 2);
INSERT INTO posts VALUES(2, "Alice", "Post 2 Under thread 2 and Forum 2", "wed", 2, 2);
INSERT INTO posts VALUES(3, "Alice", "Post 3 Under thread 3 and Forum 3", "wed", 3, 3);
