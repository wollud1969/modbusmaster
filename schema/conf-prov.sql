-- Configuration and Provisioning Schema


DROP TABLE tReadDatapoint;

CREATE TABLE tReadDatapoint (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    unit INTEGER NOT NULL,
    address INTEGER NOT NULL,
    count INTEGER NOT NULL,
    converter VARCHAR(10) NOT NULL,
    label VARCHAR(128) NOT NULL,
    scanRate TIME(3) DEFAULT '00:00:01.000',
    topic VARCHAR(256) NOT NULL,
    lastContact TIMESTAMP(3) NOT NULL DEFAULT '2000-01-01 00:00:01.000',
    lastError VARCHAR(512),
    lastValue VARCHAR(512),
    backoff TIME(3) DEFAULT '00:00:00.000',
    available BOOLEAN DEFAULT TRUE,
    retries INTEGER NOT NULL DEFAULT 0,
    giveUpCount INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uniqueReadDatapoint UNIQUE (unit, address, count, label)
);

INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(4, 0x2000, 2, 'F', '(ERR) Unavailable device', 'IoT/ModbusMaster1/UnavailableDevice', '00:00:01.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2000, 4, 'F', '(ERR) Wrong register size', 'IoT/ModbusMaster1/WrongRegisterSize', '00:05:00.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2000, 2, 'F', 'Voltage', 'IoT/ModbusMaster1/Voltage', '00:05:00.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2020, 2, 'F', 'Frequency', 'IoT/ModbusMaster1/Frequency', '00:05:00.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2060, 2, 'F', 'Current', 'IoT/ModbusMaster1/Current', '00:05:00.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x0004, 2, 'RF', 'Resistance Channel 1', 'IoT/ModbusMaster1/Channel1/Resistance', '00:00:01.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x000C, 2, 'RF', 'Temperature Channel 1', 'IoT/ModbusMaster1/Channel1/Temperature', '00:00:01.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x0014, 2, 'RF', 'Resistance Channel 2', 'IoT/ModbusMaster1/Channel2/Resistance', '00:00:01.000');
INSERT INTO tReadDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x001C, 2, 'RF', 'Temperature Channel 2', 'IoT/ModbusMaster1/Channel2/Temperature', '00:00:01.000');


DROP TABLE tWriteDatapoint;

CREATE TABLE tWriteDatapoint (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    unit INTEGER NOT NULL,
    address INTEGER NOT NULL,
    count INTEGER NOT NULL,
    converter VARCHAR(10) NOT NULL,
    label VARCHAR(128) NOT NULL,
    topic VARCHAR(256) NOT NULL,
    lastContact TIMESTAMP(3) NOT NULL DEFAULT '2000-01-01 00:00:01.000',
    lastError VARCHAR(512),
    value VARCHAR(512),
    retries INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uniqueWriteDatapoint UNIQUE (unit, address, count, label)
);



INSERT INTO tWriteDatapoint (unit, address, count, converter, label, topic, active)
    VALUES(5, 0x0000, 1, 'B', 'Relay 1', 'IoT/ModbusMaster1/Relay1', FALSE);


CREATE OR REPLACE VIEW vReadDatapointsToBeHandled AS 
    SELECT id, unit, address, count, converter
        FROM tReadDatapoint 
        WHERE available AND
              active AND
              ADDTIME(lastContact, ADDTIME(scanRate, backoff)) < NOW(3)
        ORDER BY scanRate;

CREATE OR REPLACE VIEW vWriteDatapintsToBeHandled AS
    SELECT id, unit, address, count, converter, value
        FROM tWriteDatapoint
        WHERE active;



DROP TABLE tReadNotification;

CREATE TABLE tReadNotification (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    readDatapointId INTEGER NOT NULL REFERENCES tReadDatapoint(id),
    notificationType VARCHAR(1),
    CONSTRAINT checkNotificationType CHECK (notificationtype IN ('V', 'F', 'R')) -- value, failure, return
);


DROP TABLE tWrittenNotification;

CREATE TABLE tWrittenNotification (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    writeDatapointId INTEGER NOT NULL REFERENCES tWriteDatapoint(id),
    notificationType VARCHAR(1),
    CONSTRAINT checkNotificationType CHECK (notificationtype IN ('S', 'F')) -- success, failure
);




DELIMITER $$
CREATE OR REPLACE PROCEDURE prWriteFeedback (IN p_id INTEGER, IN p_lastError VARCHAR(512))
    MODIFIES SQL DATA
    BEGIN
        DECLARE v_retries INTEGER;
        DECLARE v_active BOOLEAN;

        IF p_lastError = '' OR p_lastError IS NULL THEN
            UPDATE tWriteDatapoint
                SET lastError = NULL,
                    lastContact = NOW(3),
                    retries = 0,
                    active = FALSE
                WHERE id = p_id;
            INSERT INTO tWrittenNotification (writeDatapointId, notificationType) VALUES (p_id, 'S');
        ELSE
            SELECT retries
                INTO v_retries
                FROM tWriteDatapoint
                WHERE id = p_id;

            SET v_retries := v_retries + 1;

            IF v_retries >= 5 THEN
                SET v_retries := 0;
                SET v_active := FALSE;
            ELSE
                SET v_active := TRUE;
            END IF;

            UPDATE tWriteDatapoint
                SET lastError = p_lastError,
                    retries = v_retries,
                    active = v_active
                WHERE id = p_id;

            IF NOT v_active THEN
                INSERT INTO tWrittenNotification (writeDatapointId, notificationType) VALUES(p_id, 'F');
            END IF;
        END IF;
    END; $$
DELIMITER ;




DELIMITER $$
CREATE OR REPLACE PROCEDURE prReadFeedback (IN p_id INTEGER, IN p_lastValue VARCHAR(512), IN p_lastError VARCHAR(512))
    MODIFIES SQL DATA
    BEGIN
        DECLARE v_retries INTEGER;
        DECLARE v_backoff TIME(3);
        DECLARE v_scanRate TIME(3);
        DECLARE v_giveUpCount INTEGER;
        DECLARE v_available BOOLEAN;

        IF p_lastError = '' OR p_lastError IS NULL THEN
            UPDATE tReadDatapoint
                SET lastError = NULL,
                    lastContact = NOW(3),
                    lastValue = p_lastValue,
                    retries = 0,
                    backoff = '00:00:00.000',
                    giveUpCount = 0
                WHERE id = p_id;
            INSERT INTO tReadNotification (readDatapointId, notificationType) VALUES(p_id, 'V');
        ELSE
            SELECT retries, backoff, scanRate, giveUpCount
                INTO v_retries, v_backoff, v_scanRate, v_giveUpCount
                FROM tReadDatapoint
                WHERE id = p_id;

            SET v_retries := v_retries + 1;

            IF v_retries >= 5 THEN
                IF v_backoff = '00:00:00.000' THEN
                    SET v_backoff = v_scanRate;
                ELSE
                    SET v_backoff = ADDTIME(v_backoff, v_backoff);
                END IF;
                SET v_retries := 0;
                SET v_giveUpCount := v_giveUpCount + 1;
                SET v_available := TRUE;
            END IF;
            IF v_giveUpCount = 10 THEN
                SET v_available := FALSE;
                SET v_giveUpCount := 0;
                SET v_backoff := '00:00:00.000';
            END IF;

            UPDATE tReadDatapoint
                SET lastError = p_lastError,
                    retries = v_retries,
                    backoff = v_backoff,
                    giveUpCount = v_giveUpCount,
                    available = v_available
                WHERE id = p_id;

            IF NOT v_available THEN
                INSERT INTO tReadNotification (readDatapointId, notificationType) VALUES(p_id, 'F');
            END IF;
        END IF;
    END; $$
DELIMITER ;


