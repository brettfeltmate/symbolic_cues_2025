CREATE TABLE participants (
id integer primary key autoincrement not null,
userhash text not null,
sex text not null,
age integer not null,
handedness text not null,
created text not null
) ;

CREATE TABLE trials (
id integer primary autoincrement not null,
participant_id integer not null references participants (id),
practicing text not null,
block_num integer not null,
trial_num integer not null,
cue_reliability text not null,
cue_laterality text not null,
cue_validity text not null,
reaction_time text not null,
movement_time text not null,
touched_target text not null
) ;

CREATE TABLE aborts (
id integer primary key autoincrement not null,
participant_id integer not null references participants (id),
practicing text not null,
block_num integer not null,
trial_num integer not null,
cue_reliability text not null,
cue_laterality text not null,
cue_validity text not null,
reaction_time text not null,
movement_time text not null,
touched_target text not null,
reason text not null,
recycled text not null
) ;
