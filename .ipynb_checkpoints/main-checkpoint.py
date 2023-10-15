import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import json

class CustomJSONEncoder(json.JSONEncoder): # This logic might me removed
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)
        
app = Flask(__name__)
CORS(app)

app.json_encoder = CustomJSONEncoder

# ---
# MongoDB connection

conn_str = os.environ['MONGO_CONN_STRING']
client = MongoClient(conn_str) # , serverSelectionTimeoutMS=10*1e3

# Endpoint to get all records from a collection
@app.route("/<string:database>/<string:collection>", methods=["GET"])
def get_all_records(database, collection):
    data = list(client[database][collection].find({}))
    for doc in data:
        doc['_id'] = str(doc['_id'])
    return jsonify(data), 200

# Endpoint to get a specific record from a collection by ID
@app.route("/<string:database>/<string:collection>/<string:id>", methods=["GET"])
def get_record_by_id(database, collection, id):
    doc = client[database][collection].find_one({"_id": ObjectId(id)})
    if doc:
        doc['_id'] = str(doc['_id'])
        return jsonify(doc), 200
    return "Record not found", 404

# Endpoint to create a new record in a collection
@app.route("/<string:database>/<string:collection>", methods=["POST"])
def create_record(database, collection):
    record_data = request.get_json()
    if type(record_data) is list:
        client[database][collection].insert_many(record_data)
    elif type(record_data) is dict:
        client[database][collection].insert_one(record_data)
    return "Record created successfully", 201

# Endpoint to update a record in a collection by ID
@app.route("/<string:database>/<string:collection>/<string:id>", methods=["PUT"])
def update_record(database, collection, id):
    updated_data = request.get_json()
    client[database][collection].update_one({"_id": ObjectId(id)}, {"$set": updated_data})
    return "Record updated successfully", 200

# Endpoint to delete a record from a collection by ID
@app.route("/<string:database>/<string:collection>/<string:id>", methods=["DELETE"])
def delete_record(database, collection, id):
    client[database][collection].delete_one({"_id": ObjectId(id)})
    return "Record deleted successfully", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
