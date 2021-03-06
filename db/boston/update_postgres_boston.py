#!/usr/bin/env python

import sys
import datetime
import psycopg2
import json
import requests

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def load_config_json(filename):
    with open(filename, 'rt') as f:
        config = json.load(f)
        
    return config

def append_log(file_name, message):
    with open(file_name, 'a') as log_file:
        log_file.write('\n') 
	log_file.write(message)
    
def compute_time_range(end_date=None, num_of_days=1):
    """Computing the the start and end date for our Open311 query"""

    days_delta = datetime.timedelta(days=num_of_days)

    if end_date is None:
        end_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    
    end = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    start = end - days_delta

    return (start,end)

def get_requests(city, start, end):
    """
        Retrieving service request data from a 311 endpoint, in this case
        Boston's Open311 API
    """
    
    base_url = config['endpoint']

    query_args = {
                  'start_date' : start.isoformat() +'Z', 
                  'end_date' : end.isoformat() + 'Z'
                 }
    
    # try/except IOError?
        
    return requests.get(base_url, params=query_args)

def update_database(reqs):
    """Inserting and updating Open311 data in our postgres database."""
        
    conn = psycopg2.connect(host=config['DATABASE']['host'], 
        password=config['DATABASE']['password'], dbname=config['DATABASE']['db_name'], 
        user=config['DATABASE']['user'])
    
    cur = conn.cursor()
    
    table_prefix = config['DATABASE']['table_prefix']

    count = 0
    
    try:
        for req in reqs:
            print count
            count = count + 1
            
            attributes = ['service_request_id', 'service_name', 'service_code',
                'description', 'status', 'lat', 'long', 'requested_datetime', 
                'updated_datetime','address', 'media_url']
                
            for attribute in attributes:
                if attribute not in req:
                    req[attribute] = None
                                    
            # Check to see if we have the request and it needs to be updated
            cur.execute("""
                SELECT 
                    service_request_id 
                FROM """ + table_prefix + """requests 
                WHERE service_request_id = %s
                """, (req['service_request_id'],))
            
            res = cur.fetchone()
            
            if res:
                print 'Updating'
                
                # Might need to change this; assumes that the category didn't change.
                cur.execute("""
                    UPDATE """ + table_prefix + """requests 
                    SET service_request_id=%(service_request_id)s, 
                        service_name=%(service_name)s, 
                        service_code=%(service_code)s,
                        description=%(description)s, 
                        status=%(status)s, 
                        lat=%(lat)s, long=%(long)s, 
                        requested_datetime=%(requested_datetime)s,
                        updated_datetime=%(updated_datetime)s, address=%(address)s
                    WHERE service_request_id=%(service_request_id)s
                """, req)
            
            else:
                print 'Inserting'
                
                print 'Getting the neighborhood'
                
                cur.execute("""
                    SELECT name 
                    FROM """ + table_prefix + """geoms 
                    WHERE ST_INTERSECTS(geom, ST_SETSRID(ST_MakePoint((%s),(%s)), 4326))
                """, (req['long'], req['lat']))
                
                neighborhood = cur.fetchone()
                
                print 'neighborhood', neighborhood
                
                if neighborhood:
                    req['neighborhood'] = neighborhood[0]
                else:
                    req['neighborhood'] = None
                
                categories = config['taxonomy']
                
                if req['service_name'] in categories:
                    category = categories[req['service_name']]['category']
                    req['category'] = category
                else:
                    req['category'] = None
                                
                cur.execute("""
                    INSERT 
                    INTO """ + table_prefix + """requests (service_request_id, 
                        service_name, service_code, description, status, 
                        lat, long, requested_datetime, updated_datetime, 
                        address, media_url, neighborhood, category) 
                    VALUES (%(service_request_id)s, %(service_name)s, %(service_code)s,
                        %(description)s, %(status)s, %(lat)s, %(long)s, 
                        %(requested_datetime)s, %(updated_datetime)s, %(address)s, 
                        %(media_url)s, %(neighborhood)s, %(category)s);
                """, req)
                
                                   
    except psycopg2.IntegrityError:
        conn.rollback()
    except Exception as e:
        print e

    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    from optparse import OptionParser
    
    ONE_DAY = datetime.timedelta(1)
    
    parser = OptionParser()

    default_end_date = (datetime.datetime.utcnow()
                        .replace(hour=0, minute=0, second=0, microsecond=0) - ONE_DAY)

    """
        Edit db_config_sample.json to include the specifics about your postgres instance.
        Rename the file to db_config.json.
    """
    
    defaults = {'config': 'update_boston_config.json', 
                'end_date': datetime.datetime.strftime(default_end_date,'%Y-%m-%d'), 
                'num_of_days': 1}

    parser.set_defaults(**defaults)
    
    parser.add_option('-c', '--config', dest='config', 
                      help='Provide your configuration file.')
    parser.add_option('-e', '--end_date', dest='end_date', 
                      help='Provide the end date in the form YYYY-MM-DD')
    parser.add_option('-n', '--num_of_days', dest='num_of_days', type='int', 
                      help='Provide the number of days.')
    options, args = parser.parse_args()

    if (options.config and options.end_date and options.num_of_days):
        print options.end_date
        config = load_config_json(options.config) #global?
        end_date = datetime.datetime.strptime(options.end_date, '%Y-%m-%d')        
        num_of_days = options.num_of_days

        start, end = compute_time_range(end_date, 1) # Just handling one day at a time

        for day in xrange(num_of_days):
            print start.isoformat() + ' ' + end.isoformat()
            
            response = get_requests(config['city'], start, end)
            
            if response:
                update_database(response.json())
            else:
                append_log('err_log.txt', 
                           'Could not get a response for the following\
                            range (start - end): ' 
                            + start.isoformat() + ' - ' + end.isoformat())
                
                continue

            start -= ONE_DAY
            end -= ONE_DAY
