create table users(
  id integer primary key,
  name varchar(255),
  age integer,
	gender varchar(15),
	lang varchar(7),
	is_banned boolean,
  created datetime,
	chat_now integer
);
