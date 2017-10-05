import json
import numpy as np

if __name__ == "__main__":
    from google.cloud import datastore
    client = datastore.Client()
    print(vars(client))

    # key = client.key('EntityKind', 1235)

    # entity = datastore.Entity(key)

    # entity['person'] = ['abc', 123456789]

    # print('Putting')
    # with client.batch() as batch:
    #     batch.put(entity)

    query = client.query(kind='Interaction')
    query.add_filter('people', '=', 'Alex')

    print('\nFetching')
    for item in query.fetch():
        print(item.key.id)
        print(item['people'])
