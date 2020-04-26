CREATE TABLE test (
    id int          primary key     NOT NULL,
    subject         TEXT            NOT NULL,
    answer_keys     TEXT            NOT NULL
);
CREATE TABLE scantron
(
    id           integer primary key not null,
    scantron_url text                not null,
    name         text                not null,
    subject      text                not null,
    answers      text                not null,
    test_id      integer             not null,
    foreign key (test_id) references test(id)
);