create table users(
    id integer primary key,
    age integer,
	sex varchar(15),
	lang varchar(7),
	is_banned boolean,
    created datetime,
	chat_now integer
);
