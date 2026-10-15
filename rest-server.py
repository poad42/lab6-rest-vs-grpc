#!/usr/bin/env python3

from flask import Flask, request, Response
import jsonpickle
from PIL import Image
import base64
import io
import argparse

# Initialize the Flask application
app = Flask(__name__)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)


@app.route('/api/add/<int:a>/<int:b>', methods=['GET', 'POST'])
def add(a, b):
    response = {'sum': str(a + b)}
    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )


@app.route('/api/rawimage', methods=['POST'])
def rawimage():
    r = request

    # Convert the data to a PIL image type so we can extract dimensions
    try:
        ioBuffer = io.BytesIO(r.data)
        img = Image.open(ioBuffer)

        response = {
            'width': img.size[0],
            'height': img.size[1]
        }
    except:
        response = {'width': 0, 'height': 0}

    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )


@app.route('/api/dotproduct', methods=['POST'])
def dotproduct():
    data = request.get_json()
    a = data['a']
    b = data['b']
    total = float(sum(x * y for x, y in zip(a, b)))
    response = {'dotproduct': total}
    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )


@app.route('/api/jsonimage', methods=['POST'])
def jsonimage():
    data = request.get_json()
    try:
        raw = base64.b64decode(data['image'])
        img = Image.open(io.BytesIO(raw))
        response = {'width': img.size[0], 'height': img.size[1]}
    except Exception:
        response = {'width': 0, 'height': 0}
    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )


if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Flask REST server'
    )

    parser.add_argument(
        '-p', '--port',
        type=int,
        default=5000,
        help='Port on which to run the server (default: 5000)'
    )

    args = parser.parse_args()

    # Start Flask app
    app.run(host='0.0.0.0', port=args.port)
