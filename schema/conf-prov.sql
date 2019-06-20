-- Configuration and Provisioning Schema


DROP TABLE tDatapoint;

CREATE TABLE tDatapoint (
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
    CONSTRAINT uniqueDatapoint UNIQUE (unit, address, count, label)
);

-- ALTER TABLE tDatapoint MODIFY available BOOLEAN DEFAULT TRUE;
-- ALTER TABLE tDatapoint MODIFY lastContact TIMESTAMP(3);
-- ALTER TABLE tDatapoint MODIFY scanRate TIME(3) DEFAULT '00:00:01.000';
-- ALTER TABLE tDatapoint ADD giveUpCount INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE tDatapoint MODIFY lastContact TIMESTAMP(3) NOT NULL DEFAULT '1970-01-01 00:00:01.000';

--  ModbusRequestDefinition(4, 0x2000, 2, 'F', '(ERR) Unavailable device'),
--  ModbusRequestDefinition(1, 0x2000, 4, 'F', '(ERR) Wrong register size'),
--  ModbusRequestDefinition(1, 0x2000, 2, 'F', 'Voltage'),
--  ModbusRequestDefinition(1, 0x2020, 2, 'F', 'Frequency'),
--  ModbusRequestDefinition(1, 0x2060, 2, 'F', 'Current'),
--  ModbusRequestDefinition(3, 0x0004, 2, 'RF', 'Resistance Channel 1'),
--  ModbusRequestDefinition(3, 0x000C, 2, 'RF', 'Temperature Channel 1'),
--  ModbusRequestDefinition(3, 0x0014, 2, 'RF', 'Resistance Channel 2'),
--  ModbusRequestDefinition(3, 0x001C, 2, 'RF', 'Temperature Channel 2'),

INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(4, 0x2000, 2, 'F', '(ERR) Unavailable device', 'IoT/ModbusMaster1/UnavailableDevice', '00:00:01.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2000, 4, 'F', '(ERR) Wrong register size', 'IoT/ModbusMaster1/WrongRegisterSize', '00:05:00.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2000, 2, 'F', 'Voltage', 'IoT/ModbusMaster1/Voltage', '00:05:00.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2020, 2, 'F', 'Frequency', 'IoT/ModbusMaster1/Frequency', '00:05:00.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(1, 0x2060, 2, 'F', 'Current', 'IoT/ModbusMaster1/Current', '00:05:00.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x0004, 2, 'RF', 'Resistance Channel 1', 'IoT/ModbusMaster1/Channel1/Resistance', '00:00:01.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x000C, 2, 'RF', 'Temperature Channel 1', 'IoT/ModbusMaster1/Channel1/Temperature', '00:00:01.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x0014, 2, 'RF', 'Resistance Channel 2', 'IoT/ModbusMaster1/Channel2/Resistance', '00:00:01.000');
INSERT INTO tDatapoint (unit, address, count, converter, label, topic, scanRate)
    VALUES(3, 0x001C, 2, 'RF', 'Temperature Channel 2', 'IoT/ModbusMaster1/Channel2/Temperature', '00:00:01.000');


CREATE OR REPLACE VIEW vDatapointsToBeQueried AS 
    SELECT id, unit, address, count, converter
        FROM tDatapoint 
        WHERE ADDTIME(lastContact, ADDTIME(scanRate, backoff)) < NOW(3) AND
              available;


DROP TABLE tNotification;

CREATE TABLE tNotification (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    datapointId INTEGER NOT NULL REFERENCES tDatapoint(id),
    notificationType VARCHAR(1),
    CONSTRAINT checkNotificationType CHECK (notificationtype IN ('V', 'F', 'R'))
);


DELIMITER $$
CREATE OR REPLACE TRIGGER trCheckAvailability
    BEFORE UPDATE ON tDatapoint FOR EACH ROW
    BEGIN
        IF NEW.retries >= 5 THEN
            IF NEW.backoff = '00:00:00.000' THEN
                SET NEW.backoff = OLD.scanRate;
            ELSE
                SET NEW.backoff = ADDTIME(OLD.backoff, OLD.backoff);
            END IF;
            SET NEW.retries := 0;
            SET NEW.giveUpCount := OLD.giveUpCount + 1;
        END IF;
        IF NEW.giveUpCount = 10 THEN
            SET NEW.available := FALSE;
            SET NEW.giveUpCount := 0;
            SET NEW.backoff := '00:00:00.000';
        END IF;
    END; $$
DELIMITER ;

DELIMITER $$
CREATE OR REPLACE TRIGGER trNotification
    AFTER UPDATE ON tDatapoint FOR EACH ROW
    BEGIN
        DECLARE v_notificationType VARCHAR(1);
        IF (NEW.lastError IS NULL OR NEW.lastError = '') AND (NEW.lastValue IS NOT NULL) THEN
            SET v_notificationType := 'V';
        ELSEIF NEW.available AND NOT OLD.available THEN
            SET v_notificationType := 'R';
        ELSEIF NOT NEW.available AND OLD.available THEN 
            SET v_notificationType := 'F';
        END IF;
        IF v_notificationType IS NOT NULL THEN
            INSERT INTO tNotification (datapointId, notificationType) VALUES(NEW.id, v_notificationType);
        END IF;
    END; $$
DELIMITER ;

