
CREATE DATABASE IF NOT EXISTS jcr DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
USE jcr;

DROP TABLE IF EXISTS journal_info;
CREATE TABLE journal_info (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `name` varchar(200) NOT NULL UNIQUE ,
    `isoAbbr` varchar(100) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO journal_info (name, isoAbbr)
VALUES ('CA-A CANCER JOURNAL FOR CLINICIANS', 'CA-Cancer J. Clin.');

SELECT count(id) FROM journal_info;
