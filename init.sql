drop table if exists users;
create table users (
  username text not null,
  password text not null,
  primary key (username)
);

INSERT INTO users VALUES('rickybobby', 'aliceInWonderLand');
INSERT INTO users VALUES('yeezus', 'iamagod');

drop table if exists forums;
create table forums (
  forum_id integer auto_increment,
  author text not null,
  creator text not null,
  primary key (forum_id)
);

INSERT INTO forums VALUES(1, 'Forum 1', 'alice');
INSERT INTO forums VALUES(2, 'Forum 2', 'bob');
INSERT INTO forums VALUES(3, 'Forum 3', 'scoop');


drop table if exists threads;
create table threads (
  thread_id integer auto_increment,
  title text not null,
  creator text not null,
  timestamp text not null,
  forum_id integer not null,
  primary key (thread_id)
);

INSERT INTO threads VALUES(1, "Thread 1 Under Forum 2", "Bob", "Tue", 2);
INSERT INTO threads VALUES(2, "Thread 2 Under Forum 2", "Charlie", "wed", 2);
INSERT INTO threads VALUES(3, "Thread 1 Under Forum 3", "Charlie", "wed", 3);


drop table if exists posts;
create table posts (
  author text not null,
  text text not null,
  timestamp text not null,
  thread_id integer not null,
  forum_id integer,
    FOREIGN KEY (forum_id) REFERENCES threads(forum_id)
);

INSERT INTO posts VALUES( "Bob", "Post 1 Under thread 1 and Forum 2", "Tue", 1, 2);
INSERT INTO posts VALUES( "Alice", "Post 2 Under thread 2 and Forum 2", "wed", 2, 2);
INSERT INTO posts VALUES( "Alice", "Post 3 Under thread 3 and Forum 3", "wed", 3, 3);
