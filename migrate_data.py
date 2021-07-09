#!/usr/bin/env python3
import elasticsearch
from elasticsearch.helpers import scan
import argparse
import json
import requests

class MigrateData:
    def __init__(self, args):
        self.oldes = args.oldes
        self.newes = args.newes

    def get_olddocs(self):
        self.data_dict = {}
        es = elasticsearch.Elasticsearch(self.oldes)
        es_response = scan(es, index='insights_perf_index*', query={"query":{"match_all":{}}}, raise_on_error=False)
        for item in es_response:
            try:
                self.data_dict[item['_index']].append(item['_source'])
            except KeyError:
                self.data_dict[item['_index']] = []
                self.data_dict[item['_index']].append(item['_source'])

        return

    def upload_olddocs(self):
        self.responses = []
        for index, es_data in self.data_dict.items():
            for data in es_data:
                url = self.newes + index + '/_doc/'
                headers = {"Content-Type": "application/json"}
                self.responses.append(requests.post(url=url, headers=headers, data=json.dumps(data)))
    
    def verify_allposts(self):
        def get_response(resp_obj):
            if resp_obj.status_code == 201:
                return True
            else:
                return False
        
        responses = map(self.responses, get_response)
        return all(responses)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate the data from old to new elasticsearch',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--oldes', default='http://elasticsearch.perf.lab.eng.bos.redhat.com:9286',
                        help='old elastic search url link')
    parser.add_argument('--newes', default='http://elasticsearch.intlab.perf-infra.lab.eng.rdu2.redhat.com/',
                        help='new elastic search url link')
    
    args = parser.parse_args()

    migrate_data = MigrateData(args)
    migrate_data.get_olddocs()
    migrate_data.upload_olddocs()
    response = migrate_data.verify_allposts()
    print("The final response for the requests is: ", response)


if __name__ == "__main__":
    main()
