# /usr/local/bin/python3
# https://docs.aws.amazon.com/Route53/latest/APIReference/API_CreateHostedZone.html


import boto3, datetime, csv, json


class Route53(object):
    """Connects to aws route53 to create/ modify/ delete Zones and DNS records"""

    def __init__(self):
        # boto3 respects the aws creds in ~./aws/config and pulls from there
        self.conn = self.connect()
        self.c_time = self.current_time()
        self.zone_ids = []

    def current_time(self):
        c_time = datetime.datetime.now()
        return c_time

    def connect(self):
        # boto3 respects the aws creds in ~./aws/config and pulls from there
        conn = boto3.client('route53')
        return conn

    def list_zones(self):
        # get's list of domain names/ ids currently in route53
        zone_list = self.conn.list_hosted_zones_by_name(MaxItems='100')  # pulls domains 100 at a time (max amount)
        print(zone_list)
        if str(zone_list.get('IsTruncated', None)) == 'True':  # - may have to join the 2 zone_list dicts together etc
            #  do something with truncated zone_list
            print(zone_list.get('IsTruncated', None))
        else:
            existing_zoneids = []
            for zone in zone_list.get('HostedZones'):
                existing_zoneids.append(zone.get('Id'))
            self.existing_zones(existing_zoneids)

    def existing_zones(self, existing_zoneids):
        # uses zone ids to get NS list
        ns_records = []
        for zone_id in existing_zoneids:
            domain_records = {}
            existing_zones = self.conn.get_hosted_zone(Id=zone_id)  # 'Z1R6SUTMNC612U'
            domain = existing_zones['HostedZone']['Name']  # gets domain name
            ns_value = existing_zones['DelegationSet']['NameServers']  # gets NS records
            domain_records[domain] = ns_value
            ns_records.append(domain_records)
        print(ns_records)

    def create_record(self, domain):
        # creates a new DNS zone
        response = self.conn.create_hosted_zone(
            # must be strings
            Name=domain,  # 'alex-testingsdi8743rsdf98u8.com'
            CallerReference=str(self.current_time())
        )
        # get the NS list <NameServers>
        #          <NameServer>string</NameServer>
        #       </NameServers>
        # https://docs.aws.amazon.com/Route53/latest/APIReference/API_CreateHostedZone.html
        print(response)
        for k, v in response.items():
            if k == 'HostedZone':
                print(v)
                for record in v:
                    if record == 'Id':
                        zone_id = (v[record])
                        print(zone_id)
        return zone_id

    def edit_record(self, record, r_type, target, zone_id):
        # edits the records of DNS zone created in create_record
        # set variables: zone_id, action, record, r_type, target as necessary - see below
        response = self.conn.change_resource_record_sets(
            HostedZoneId=zone_id,  # e.g. 'Z1XWWDQ5R7AY0L'
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'UPSERT',  # action DELETE vs CREATE vs UPSERT: If a resource record set does not already exist, AWS creates it. If a resource set does exist, Route 53 updates it with the values in the request.
                        'ResourceRecordSet': {
                            'Name': record,  # e.g 'autodiscover.alex-testingsdi8743rsdf98u8.com.'
                            'Type': r_type,  # e.g. 'CNAME'
                            'TTL': 300,
                            'ResourceRecords': [
                                {
                                    'Value': target  # e.g. 'ar.exch690.serverdata.net'
                                }
                            ]
                        }
                    }
                ]
            }
        )
        return response

    def process_domain_keys(self, domain_list):
        for k, v in domain_list.items():
            if v:
                self.process_records(k, v)
            else:
                continue

    def process_records(self, domain, records):
        print("FQDN is " + domain)
        zone_id = self.create_record(domain)  # zone_id = '/hostedzone/Z3HKZFSVVLYKNO'
        desired_records = ['CNAME', 'TXT', 'MX', 'SOA', 'NS', 'A', 'AAAA', 'PTR', 'SRV', 'SPF', 'NAPTR', 'CAA']
        for k, v in records.items():
            if not v:
                continue
            for record in desired_records:
                if v.split(" ", 1)[0] == record:
                    if record == 'SOA':
                        continue
                    else:
                        record = k  # returns record e.g. firsttestalex.com, autodiscover.firsttestalex.com. etc
                        print(record)
                        r_type = v.split(" ", 1)[0]  # returns record type - SOA, CNAME etc
                        print(r_type)
                        if 'v=spf1' not in v.split(" ")[1]:
                            value = v.split(" ")[1]
                            print(value)
                        else:
                                value = '"%s"' % v.split('"')[1]
                                print(value)
                    self.edit_record(record, r_type, value, zone_id)


def main():
    current_time = datetime.datetime.now()
    json_data = open('exampledomains.json', 'r').read()  # 'exportedzones.json'
    domain_list = json.loads(json_data)
    print(current_time)
    r53 = Route53()
    # r53.existing_zones()
    # r53.create_record()
    # r53.edit_record()
    r53.list_zones()
    # r53.process_domain_keys(domain_list)



if __name__ == '__main__':
    main()