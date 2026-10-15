#!/usr/bin/env python3
"""gRPC server for the lab6 comparison.

Implements the same four services as the REST server: add, rawImage,
dotProduct, and jsonImage.
"""

import argparse
import base64
import io
from concurrent import futures

import grpc
from PIL import Image

import lab6_pb2
import lab6_pb2_grpc


class Lab6Servicer(lab6_pb2_grpc.Lab6Servicer):

    def Add(self, request, context):
        return lab6_pb2.addReply(sum=request.a + request.b)

    def RawImage(self, request, context):
        try:
            img = Image.open(io.BytesIO(request.img))
            return lab6_pb2.imageReply(width=img.size[0], height=img.size[1])
        except Exception:
            return lab6_pb2.imageReply(width=0, height=0)

    def DotProduct(self, request, context):
        total = float(sum(x * y for x, y in zip(request.a, request.b)))
        return lab6_pb2.dotProductReply(dotproduct=total)

    def JsonImage(self, request, context):
        try:
            raw = base64.b64decode(request.img)
            img = Image.open(io.BytesIO(raw))
            return lab6_pb2.imageReply(width=img.size[0], height=img.size[1])
        except Exception:
            return lab6_pb2.imageReply(width=0, height=0)


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lab6_pb2_grpc.add_Lab6Servicer_to_server(Lab6Servicer(), server)
    server.add_insecure_port('[::]:%d' % port)
    server.start()
    print("gRPC server listening on port %d" % port)
    server.wait_for_termination()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='gRPC server')
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=50051,
        help='Port on which to run the server (default: 50051)'
    )
    args = parser.parse_args()
    serve(args.port)
