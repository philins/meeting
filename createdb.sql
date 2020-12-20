create table users(
	id integer primary key,
	name varchar(255),
	age integer,
	gender varchar(255),
	lang varchar(15),
	lat real,
	lng real,
	is_banned boolean,
	created datetime,
	companion_id integer
);
