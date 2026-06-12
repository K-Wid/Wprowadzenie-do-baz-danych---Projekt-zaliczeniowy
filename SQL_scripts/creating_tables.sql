
-- Creating tables

CREATE TABLE date_table (
	date_id			SERIAL	PRIMARY KEY,
	date_value		DATE	NOT NULL UNIQUE
);

CREATE TABLE time_table (
	time_id			SERIAL PRIMARY KEY,
	time_value		TIME	NOT NULL UNIQUE
);

CREATE TABLE error_table (
	error_id		INTEGER PRIMARY KEY,
	reason			TEXT	NOT NULL
);

CREATE TABLE log_import (
	import_id		SERIAL	PRIMARY KEY,
	date_id			INTEGER	NOT NULL,
	time_id			INTEGER	NOT NULL,
	error_id		INTEGER NULL		DEFAULT NULL,
	import_time_ms	FLOAT,
	CONSTRAINT log_import_date
		FOREIGN KEY (date_id)
			REFERENCES date_table(date_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT,
	CONSTRAINT log_import_time
		FOREIGN KEY (time_id)
			REFERENCES time_table(time_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT,
	CONSTRAINT log_import_error
		FOREIGN KEY (error_id)
			REFERENCES error_table(error_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT
);

CREATE TABLE timezone (
	timezone_id 	SERIAL	PRIMARY KEY,
	full_name		TEXT	NOT NULL,
	short_name		TEXT	NOT NULL,
	time_offset		TIME	NOT NULL
);

CREATE TABLE location_table (
	location_id		SERIAL	PRIMARY KEY,
	latitude		FLOAT	NOT NULL,
	longitude		FLOAT	NOT NULL,
	elevation		FLOAT	NOT NULL,
	timezone_id		INTEGER,
	name			TEXT,
	CONSTRAINT location_timezone
		FOREIGN KEY (timezone_id)
			REFERENCES timezone(timezone_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT
);

CREATE TABLE measurement (
	measurement_id	SERIAL	PRIMARY KEY,
	location_id		INTEGER	NOT NULL,
	date_id			INTEGER NOT NULL,
	time_id			INTEGER NOT NULL,
	import_id		INTEGER NOT NULL,
	CONSTRAINT measurement_location
		FOREIGN KEY (location_id)
			REFERENCES location_table(location_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT,
	CONSTRAINT measurement_date
		FOREIGN KEY (date_id)
			REFERENCES date_table(date_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT,
	CONSTRAINT measurement_time
		FOREIGN KEY (time_id)
			REFERENCES time_table(time_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT,
	CONSTRAINT measurement_import
		FOREIGN KEY (import_id)
			REFERENCES log_import(import_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT
);

CREATE TABLE temperature (
	measurement_id			INTEGER NOT NULL UNIQUE,
	temperature				FLOAT	NOT NULL,
	apparent_temperature	INTEGER NOT NULL,
	CONSTRAINT temperature_measurement
		FOREIGN KEY (measurement_id)
			REFERENCES measurement(measurement_id)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);

CREATE TABLE precipitation (
	measurement_id		INTEGER NOT NULL UNIQUE,
	relative_humidity	FLOAT	NOT NULL,
	precipitation		FLOAT	NOT NULL,
	rain				FLOAT	NOT NULL,
	snowfall			FLOAT	NOT NULL,
	CONSTRAINT precipitation_measurement
		FOREIGN KEY (measurement_id)
			REFERENCES measurement(measurement_id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT precipitation_humidity
		CHECK (relative_humidity BETWEEN 0 AND 100)
);

CREATE TABLE wind (
	measurement_id		INTEGER	NOT NULL UNIQUE,
	wind_speed			FLOAT	NOT NULL,
	wind_direction		FLOAT	NOT NULL,
	wind_gusts			FLOAT	NOT NULL,
	CONSTRAINT wind_measurement
		FOREIGN KEY (measurement_id)
			REFERENCES measurement(measurement_id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT wind_wind_direction
		CHECK (wind_direction BETWEEN 0 AND 360)
);

CREATE TABLE weather_code (
	weather_code_id		INTEGER NOT NULL UNIQUE,
	description			TEXT	NOT NULL
);

CREATE TABLE weather (
	measurement_id		INTEGER NOT NULL UNIQUE,
	surface_pressure	FLOAT	NOT NULL,
	cloud_cover			FLOAT	NOT NULL,
	weather_code_id		INTEGER	NOT NULL,
	CONSTRAINT weather_measurement
		FOREIGN KEY (measurement_id)
			REFERENCES measurement(measurement_id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT weather_weather_code
		FOREIGN KEY (weather_code_id)
			REFERENCES weather_code(weather_code_id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT
);

-- Indexes

CREATE INDEX idx_import_id
	ON log_import (import_id);

CREATE INDEX idx_measurement_id
	ON measurement (measurement_id);

CREATE INDEX idx_location_id
	ON location_table (location_id);

CREATE INDEX idx_date_id
	ON date_table (date_id);

CREATE INDEX idx_time_id
	ON time_table (time_id);


-- Weather codes

INSERT INTO weather_code (weather_code_id, description)
	VALUES 	(0, 'Clear sky'),
			(1, 'Mainly clear'),
			(2, 'Partly cloudy'),
			(3, 'Overcast'),
			(45, 'Fog'),
			(48, 'Depositing rime fog'),
			(51, 'Light drizzle'),
			(53, 'Moderate drizzle'),
			(55, 'Dense drizzle'),
			(56, 'Light freezing drizzle'),
			(57, 'Dense freezing drizzle'),
			(61, 'Slight rain'),
			(63, 'Moderate rain'),
			(65, 'Intense rain'),
			(66, 'Light freezing rain'),
			(67, 'Heavy freezing rain'),
			(71, 'Slight snow fall'),
			(73, 'Moderate snow fall'),
			(75, 'Heavy snow fall'),
			(77, 'Snow grains'),
			(80, 'Slight rain shower'),
			(81, 'Moderate rain shower'),
			(82, 'Heavy rain shower'),
			(85, 'Slight snow shower'),
			(86, 'Heavy snow shower'),
			(95, 'Thunderstorm'),
			(96, 'Thunderstorm with slight hail'),
			(99, 'Thunderstorm with heavy hail');

INSERT INTO error_table (error_id, reason)
	VALUES 	(0, 'SUCCESS'),
			(1, 'MEASUREMENT_ALREADY_EXISTS'),
			(2, 'ALL_MEASUREMENTS_EXISTED'),
			(3, 'SOME_MEASUREMENTS_EXISTED');
