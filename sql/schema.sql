CREATE TABLE IF NOT EXISTS air_quality (
    id          SERIAL PRIMARY KEY,
    city        TEXT NOT NULL,
    measured_at TIMESTAMP NOT NULL,
    pm2_5       REAL,
    pm10        REAL,
    loaded_at   TIMESTAMP DEFAULT now(),
    UNIQUE (city, measured_at)
);
