-- Configuration and Provisioning Schema

DROP TABLE tDatapoint;

CREATE TABLE tDatapoint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit INTEGER NOT NULL,
    address INTEGER NOT NULL,
    count INTEGER NOT NULL,
    converter TEXT NOT NULL,
    label TEXT NOT NULL,
    scanRate INTEGER NOT NULL DEFAULT 1000, -- in milliseconds
    lastContact TEXT,
    lastError TEXT,
    lastValue TEXT,
    backoff INTEGER NOT NULL DEFAULT 0, -- in seconds
    CONSTRAINT uniqueDatapoint UNIQUE (unit, address, count, label)
);

