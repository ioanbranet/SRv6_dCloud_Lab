import json
from arango import ArangoClient
from math import ceil
from . import add_route

# Query DB for low latency path parameters and return srv6 SID
def srv6_ll_calc(src_id, dst_id, dst, user, pw, dbname, intf, dataplane):

    client = ArangoClient(hosts='http://198.18.1.101:30852')
    db = client.db(dbname, username=user, password=pw)
    cursor = db.aql.execute("""for v, e in outbound shortest_path """ + '"%s"' % src_id + """ \
        TO """ + '"%s"' % dst_id + """ sr_topology \
            OPTIONS { weightAttribute: 'latency' } \
                return { node: v._key, name: v.name, sid: e.srv6_sid, latency: e.latency } """)
    path = [doc for doc in cursor]
    #print("path: ", path)
    hopcount = len(path)
    #print("hops: ", hopcount)
    pq = ceil((hopcount/2)-1)
    #print(pq)
    pq_node = (path[pq])
    #print("pqnode: ", pq_node)
    sid = 'sid'
    usid_block = 'fc00:0:'

    locators = [a_dict[sid] for a_dict in path]

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
    #print(sidlist)

    srv6_sid = usid_block + sidlist + ipv6_separator
    print("srv6 sid: ", srv6_sid)

    pathdict = {
            'statusCode': 200,
            'source': src_id,
            'destination': dst_id,
            'sid': srv6_sid,
            'path': path
        }

    print("route_add parameters = sid: ", srv6_sid, "dest: ", dst, "intf: ", intf, "dataplane: ", dataplane)
    if dataplane == "linux":
        route_add = add_route.add_linux_route(dst, srv6_sid, intf)
    if dataplane == "vpp":
        route_add = add_route.add_vpp_route(dst, srv6_sid)
    pathobj = json.dumps(pathdict, indent=4)
    return(pathobj)
