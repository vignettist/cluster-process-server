#!flask/bin/python
from flask import Flask, jsonify
import pymongo
from shapely.geometry import MultiPoint
from bson import ObjectId
from flask import make_response

app = Flask(__name__)
client = pymongo.MongoClient("localhost", 3001)
db = client.meteor

@app.route('/update/<string:cluster_id>', methods=['PUT'])
def update_cluster(cluster_id):
    print(cluster_id)
    clusters = list(db.clusters.find({'_id': ObjectId(cluster_id)}));

    if (len(clusters) > 1):
        return jsonify({'error': 'too many clusters'})

    if (len(clusters) == 0):
        return jsonify({'error': 'no cluster with id'})

    cluster = clusters[0]

    points = MultiPoint(cluster['locations']['coordinates'])
    geom = {}
    geom['type'] = 'Polygon'
    
    try:
        p = points.convex_hull
        p = p.buffer(np.sqrt(p.area) * 0.33)
        geom['coordinates'] = list(p.simplify(0.0005).exterior.coords)
    except:
        p = points.buffer(0.005)
        p = p.convex_hull
        geom['coordinates'] = list(p.simplify(0.0005).exterior.coords)
    
    centroid = {'type': 'Point'}
    centroid['coordinates'] = list(p.centroid.coords)[0]
    
    print(centroid)

    db.clusters.update_one({'_id': cluster['_id']}, {'$set': {'boundary': geom, 'centroid': centroid}})

    return jsonify({'response': 'okay'})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(500)
def not_found(error):
    return make_response(jsonify({'error': 'Internal server error'}), 404)

if __name__ == '__main__':
    app.run(debug=True, port=3122)