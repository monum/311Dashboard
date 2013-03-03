CREATE TABLE sf_requests (
        id                      SERIAL PRIMARY KEY NOT NULL,
        status                  VARCHAR(10) DEFAULT NULL,
        description             text DEFAULT NULL,
        service_code            text DEFAULT NULL,
        service_name            text DEFAULT NULL,
        service_request_id      bigint DEFAULT NULL,
        requested_datetime      timestamp DEFAULT NULL,
        expected_datetime       timestamp DEFAULT NULL,
        updated_datetime        timestamp DEFAULT NULL,
        address                 text DEFAULT NULL,
        zipcode                 integer DEFAULT NULL,
        lon                     double precision DEFAULT NULL,
        lat                     double precision DEFAULT NULL
);

ALTER TABLE sf_requests ADD COLUMN neighborhood text DEFAULT NULL;
ALTER TABLE sf_requests ADD COLUMN category text DEFAULT NULL;

CREATE INDEX requested_day_idx ON sf_requests ( DATE(requested_datetime) );
CREATE INDEX updated_day_idx ON sf_requests ( DATE(updated_datetime) );
CREATE INDEX neighborhood_idx ON sf_requests ( neighborhood );
CREATE INDEX request_status_idx ON sf_requests ( status );

CREATE TABLE boston_requests (
        id                      SERIAL PRIMARY KEY NOT NULL,
        status                  VARCHAR(10) DEFAULT NULL,
        status_notes            text DEFAULT NULL,
        description             text DEFAULT NULL,
        service_code            text DEFAULT NULL,
        service_name            text DEFAULT NULL,
        service_request_id      bigint DEFAULT NULL,
        requested_datetime      timestamp DEFAULT NULL,
        updated_datetime        timestamp DEFAULT NULL,
        address                 text DEFAULT NULL,
        long                    double precision DEFAULT NULL,
        lat                     double precision DEFAULT NULL,
        media_url               text DEFAULT NULL
);

ALTER TABLE boston_requests ADD COLUMN neighborhood text DEFAULT NULL;
ALTER TABLE boston_requests ADD COLUMN category text DEFAULT NULL;

CREATE INDEX boston_requested_day_idx ON boston_requests ( DATE(requested_datetime) );
CREATE INDEX boston_updated_day_idx ON boston_requests ( DATE(updated_datetime) );
CREATE INDEX boston_neighborhood_idx ON boston_requests ( neighborhood );
CREATE INDEX boston_request_status_idx ON boston_requests ( status );