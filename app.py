from flask import Flask, jsonify, request, make_response, g
from flask_restful import Api, Resource

import os, requests

app = Flask(__name__)
api = Api(app)
forwarding = os.environ.get('FORWARDING_ADDRESS') or 0 ## forwarding ip
newdict = {}

class key_value(Resource):
    def get(self, key):
        if 'FORWARDING_ADDRESS' in os.environ:
            #nonempty forwarding address forward to main instance
            try:
                r = requests.get('http://10.10.0.2:8080/key-value-store/' + key)
                return r.json(),r.status_code
            except:
                return make_response(jsonify(error= 'Main instance is down', message = 'Error in GET'), 503)
        else:
            if key in newdict:
                #on key value found return found value
                value = newdict[key]
                return make_response(jsonify(doesExist=True, message="Retrieved successfully", value=value), 200)
            else:
                #on key value not found error
                return make_response(jsonify(doesExist=False, error="Key does not exist", message="Error in GET"), 404)

    def put(self, key):
        if 'FORWARDING_ADDRESS' in os.environ:
            try:
                json = request.get_json()
                r = requests.put('http://10.10.0.2:8080/key-value-store/'+key, json=json)
                return r.json(),r.status_code
            except:
                return make_response(jsonify(error = 'Main instance is down', message="Error in PUT"), 503)
        else:
            if len(key) < 50:
                message = request.get_json()
                v = message.get('value')
                if v:
                    if key in newdict:
                        #edit value @ key, key
                        newdict[key] = v
                        return make_response(jsonify(message='Updated successfully', replaced=True),200)
                    else:
                    #add new value @ key, key
                        newdict[key] = v
                        return make_response(jsonify(message='Added successfully', replaced=False), 201)
                else:
                    return make_response(jsonify(error="Value is missing",message="Error in PUT"), 400)
            else:
                return make_response(jsonify(error="Key is too long", message="Error in PUT"), 400)


    def delete(self, key):
        if 'FORWARDING_ADDRESS' in os.environ:
            try:
                r = requests.delete('http://10.10.0.2:8080/key-value-store/'+key)
                return r.json(),r.status_code
            except:
                return make_response(jsonify(error='Main instance is down', message='Error in DELETE'),503)
        else:
            if newdict.pop(key,None) == None:
                return make_response(jsonify(doesExist=False, error="Key does not exist", message="Error in DELETE"), 404)
            else:
                return make_response(jsonify(doesExist=True, message="Deleted successfully"), 200)


class views(Resource):
    #basic response of replica's views, probably have to check update of views from everyone else beforehand
    #Cases to Test:
    #1. returns correct view list
    def get(self):
        views = os.environ.get('VIEW')
        return make_response(jsonify(doesExist=True, message='View retrieved successfully', view=views))


    #Cases to Test:
    #1.returns appropriate response, i.e if delete was successful or if there is no actual address there
    #2.call get() view after delete to see if its actually deleted
    #3.test if using list.remove() is ok
    def delete(self):
        data = request.get_json()
        delView = data.get('socket-address')
        viewsList = os.environ.get('VIEW').split(',')
        #include code here to check if the request is from a client or from replica, and handle accordingly
        if 'FORWARDING_ADDRESS' not in os.environ:
            #broadcast to all the delete request, 
            socketAddress = os.environ.get('SOCKET_ADDRESS')
            newList = [i for i in viewList]
            newList = newList.remove(socketAddress) 
            broadcast(viewsList)

        if delView in viewsList:
            viewsList.remove(delView)
            newView = ','.join(viewsList)
            os.environ['VIEW'] = newView
            #broadcast this to other replicas, (should every view request check if other replicas are alive before broadcasting?)
            return make_response(jsonify(doesExist=True, message='Replica deleted successfully from the view'), 200)
        else:
            #should also broadcast to other replicas to see if it has that view in the replica
            return make_response(jsonify(doesExist=False, error='Socket address does not exist in the view', message='Error in DELETE') 400)

    def broadcast(self, viewsList):
        for view in viewsList:



api.add_resource(key_value, '/key-value-store/', '/key-value-store/<key>')
api.add_resource(views, 'key-value-store-view')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
