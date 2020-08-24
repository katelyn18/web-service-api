DROP TABLE IF EXISTS Post;
DROP TABLE IF EXISTS Thread;
DROP TABLE IF EXISTS Forum;
DROP TABLE IF EXISTS User;

CREATE TABLE User(
    username varchar( 50 ) NOT NULL,
    pssword tinytext NOT NULL,
    CONSTRAINT user_pk PRIMARY KEY( username )
);

CREATE TABLE Forum(
    forumId INTEGER PRIMARY KEY AUTOINCREMENT,
    fname varchar( 50 ) NOT NULL,
    creator varchar( 50 ) NOT NULL,
    CONSTRAINT forum_user_fk FOREIGN KEY( creator ) REFERENCES User( username )
);

CREATE TABLE Thread(
    threadId INTEGER PRIMARY KEY AUTOINCREMENT,
    title varchar( 50 ) NOT NULL,
    creator varchar( 50 ) NOT NULL,
    time_stamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    forumId int NOT NULL,
    CONSTRAINT thread_user_fk FOREIGN KEY( creator ) REFERENCES User( username ),
    CONSTRAINT thread_forum_fk FOREIGN KEY( forumId ) REFERENCES Forum( forumId )
);

CREATE TABLE Post(
    postId INTEGER PRIMARY KEY AUTOINCREMENT,
    author varchar( 50 ) NOT NULL,
    ptext text NOT NULL,
    time_stamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    threadId int NOT NULL,
    CONSTRAINT post_user_fk FOREIGN KEY( author ) REFERENCES User( username ),
    CONSTRAINT post_thread_fk FOREIGN KEY( threadId ) REFERENCES Thread( threadId )
);

INSERT INTO User VALUES( "alice", "alice123" );
INSERT INTO User VALUES( "bob", "bob123" );
INSERT INTO User VALUES( "charlie", "charlie123" );
INSERT INTO User VALUES( "eve", "eve123" );

INSERT INTO Forum VALUES( 1, "redis", "alice" );
INSERT INTO Forum VALUES( 2, "mongodb", "bob" );

INSERT INTO Thread( threadId, title, creator, forumId ) VALUES( 1, "Does anyone know how to start Redis?", "bob", 1 );
INSERT INTO Thread( threadId, title, creator, forumId ) VALUES( 2, "Has anyone heard of Edis?", "charlie", 1 );
INSERT INTO Thread( threadId, title, creator, forumId ) VALUES( 3, "Has anyone heard of Ongodb?", "eve", 2 );

INSERT INTO Post( postId, author, ptext, threadId ) VALUES( 1, "bob", "Trying to start Redis", 1 );
INSERT INTO Post( postId, author, ptext, threadId ) VALUES( 2, "alice", "Did you do this?", 1 );

