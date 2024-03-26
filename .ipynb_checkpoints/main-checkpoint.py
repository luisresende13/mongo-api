import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId

# ---
# MongoDB connection

conn_str = os.environ.get('MONGO_CONN_STRING')
client = MongoClient(conn_str) # , serverSelectionTimeoutMS=10*1e3

# ---
# Json encoding

class CustomJSONEncoder(json.JSONEncoder): # This logic might me removed
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


# NOTE: remember to replace `type(...) is ...` to use isinstance instead

# ---
# Flask app

app = Flask(__name__)
CORS(app)

app.json_encoder = CustomJSONEncoder


# ---
# Flask routes

@app.route("/<string:database>/<string:collection>", methods=["GET"])
def get_records(database, collection):
    query = request.args.to_dict()
    # Convert integer fields in the query to integers
    for key, value in query.items():
        try:
            query[key] = int(value)
        except ValueError:
            pass  # Ignore non-integer values
    # Convert "_id" field to ObjectId if present
    if '_id' in query:
        query['_id'] = ObjectId(query['_id'])
    data = list(client[database][collection].find(query))
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

from bson.json_util import dumps

# Endpoint to create a new record in a collection
@app.route("/<string:database>/<string:collection>", methods=["POST"])
def create_record(database, collection):
    record_data = request.get_json()
    
    if type(record_data) is list:
        result = client[database][collection].insert_many(record_data)
        for inserted_id, data in zip(result.inserted_ids, record_data):
            data['_id'] = str(inserted_id)  # Add _id to each dict in the list
    elif type(record_data) is dict:
        result = client[database][collection].insert_one(record_data)
        record_data['_id'] = str(result.inserted_id)  # Add _id to the posted dict
    
    # Return the posted data with the inserted _id(s) in the response
    return jsonify({"message": "Record(s) created successfully", "data": record_data}), 201

# Endpoint to update a record in a collection by ID
@app.route("/<string:database>/<string:collection>/<string:id>", methods=["PUT"])
def update_record(database, collection, id):
    updated_data = request.get_json()
    client[database][collection].update_one({"_id": ObjectId(id)}, {"$set": updated_data})
    
    # Return the updated data in the response
    return jsonify({"message": "Record updated successfully", "data": updated_data}), 200

# Endpoint to delete a record from a collection by ID
@app.route("/<string:database>/<string:collection>/<string:id>", methods=["DELETE"])
def delete_record(database, collection, id):
    # Delete the record from the collection
    deleted_record_id = client[database][collection].delete_one({"_id": ObjectId(id)}).deleted_count
    
    # Return the ID of the deleted record in the response
    return jsonify({"message": "Record deleted successfully", "deleted_record_id": id}), 200
    
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
