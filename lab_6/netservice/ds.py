import json
import sys
import subprocess
from arango import ArangoClient
from . import add_route

# Query DB for a path that avoids a given country and return srv6 SID
def ds_calc(src, dst, user, pw, dbname, ctr, intf, route):

    client = ArangoClient(hosts='http://198.18.1.101:30852')
    db = client.db(dbname, username=user, password=pw)

    aql = db.aql
    cursor = db.aql.execute("""for p in outbound k_shortest_paths \
        """ + '"%s"' % src + """ TO """ + '"%s"' % dst + """ sr_topology \
            options {uniqueVertices: "path", bfs: true} \
            filter p.edges[*].country_codes !like "%"""+'%s' % ctr +"""%" limit 1 \
                return { path: p.edges[*].remote_node_name, sid: p.edges[*].srv6_sid, \
                    countries_traversed: p.edges[*].country_codes[*], latency: sum(p.edges[*].latency), \
                        percent_util_out: avg(p.edges[*].percent_util_out)} """)

    path = [doc for doc in cursor]
    print("path: ", path)

    pdict = path[0]
    locators = pdict['sid']
    usid_block = 'fc00:0:'

    for sid in list(locators):
        if sid == None:
            locators.remove(sid)
    print("locators: ", locators)

    usid = []
    for s in locators:
        if s != None and usid_block in s:
            usid_list = s.split(usid_block)
            sid = usid_list[1]
            usid_int = sid.split(':')
            u = int(usid_int[0])
            usid.append(u)

    ipv6_separator = ":"

    sidlist = ""
    for word in usid:
        sidlist += str(word) + ":"

    srv6_sid = usid_block + sidlist + ipv6_separator
    print("srv6 sid: ", srv6_sid)
    #print("path: ", path)

    siddict = {}
    siddict['srv6_sid'] = srv6_sid
    path.append(siddict)

    pathdict = {
            'statusCode': 200,
            'source': src,
            'destination': dst,
            'sid': srv6_sid,
            'path': path
        }

    pathobj = json.dumps(pathdict, indent=4)
    with open('netservice/log/srv6_data_sovereignty.json', 'w') as f:
        sys.stdout = f 
        print(pathobj)

    route_add = add_route.add_linux_route(dst, srv6_sid, intf, route)
    #print("adding route: ", route_add, "type: ", route)