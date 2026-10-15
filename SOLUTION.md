# Lab 6 - REST vs gRPC: Solution

## What this does

The lab asks for the same four services over REST and gRPC, with a client that
times each call:

| Service | Payload | Reply |
|---------|---------|-------|
| `add` | two integers | their sum |
| `rawImage` | JPEG bytes | image width and height |
| `dotProduct` | two float vectors of length 100 | their dot product |
| `jsonImage` | base64 JPEG inside JSON | image width and height |

The REST server and client are extended from the provided starter code
(`rest-server.py`, `rest-client.py`). The gRPC server and client are written
from `lab6.proto`, which mirrors the four services and uses the message layout
from `README-gRPC-details.md`.

The image is `Flatirons_Winter_Sunrise_edit_2.jpg`, 3004 by 1002 pixels, 1.6 MB.
Both implementations return the same dimensions.

## Implementation notes

- The REST server uses `jsonpickle` for replies and Pillow to read the image
  dimensions, matching the two endpoints that were provided.
- `dotProduct` generates two vectors of length 100 with `random.random()` in the
  client, sends them as JSON, and sums the products in the server.
- `jsonImage` base64-encodes the JPEG in the client and decodes it in the server.
- The gRPC client opens one channel and reuses it for every query. The REST
  client uses `requests.post` per query, so it opens a new TCP connection each
  time. That difference is the point of the comparison.
- The protobuf code is generated with
  `python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. lab6.proto`,
  and the generated `lab6_pb2.py` and `lab6_pb2_grpc.py` are committed so the
  code runs without a protoc step.

## How to run

```bash
docker compose up --build -d
docker exec -it lab6-rest-grpc bash
cd /lab

python3 rest-server.py &
python3 grpc-server.py &

python3 rest-client.py localhost add 1000
python3 grpc-client.py localhost add 1000
```

Both clients take `host`, `cmd` (`add`, `rawImage`, `dotProduct`, `jsonImage`),
and `reps`, and print the milliseconds per operation. The REST server uses port
5000 and the gRPC server uses port 50051 by default.

## Results

Measured on localhost, inside one Ubuntu 26.04 container, with the server and
client in the same container. Each value is the mean of two runs, 1000
repetitions for `add` and `dotProduct`, 100 for `rawImage` and `jsonImage`.

| Method | Local | Same-Zone | Different Region |
|--------|-------|-----------|------------------|
| REST add | 1.42 ms | not run | not run |
| gRPC add | 0.11 ms | not run | not run |
| REST rawimg | 2.95 ms | not run | not run |
| gRPC rawimg | 3.19 ms | not run | not run |
| REST dotproduct | 1.84 ms | not run | not run |
| gRPC dotproduct | 0.12 ms | not run | not run |
| REST jsonimg | 14.12 ms | not run | not run |
| gRPC jsonimg | 8.48 ms | not run | not run |
| PING | 0.06 ms | not run | not run |

The same-zone and different-region columns were not run. The Canvas
instructions say the interview runs the code over localhost and does not require
Google Cloud, and the two remote columns need extra VMs in `us-west1-a` and
`europe-west3-a`.

`PING` is the localhost round-trip, `ping -c 10 localhost`, and is the floor
with no RPC or Python overhead.

## Observations

The small-payload calls show the per-query overhead. REST opens a new TCP
connection for every query and encodes JSON text, so `add` costs 1.42 ms and
`dotProduct` 1.84 ms. gRPC keeps one HTTP/2 connection for all queries and sends
binary protobuf, so the same calls cost 0.11 ms and 0.12 ms, roughly 12 to 15
times less. Localhost ping is 0.06 ms, so the gRPC calls are close to the bare
network floor while the REST calls are dominated by connection setup and text
encoding.

For the large payloads the transfer dominates and the gap narrows. `rawImage`
sends 1.6 MB of JPEG, and the two are effectively equal at 2.95 ms (REST) and
3.19 ms (gRPC). `jsonImage` sends the same image as base64 inside JSON, which is
about 2.1 MB of text plus JSON parsing on both ends, and here gRPC is faster:
8.48 ms against 14.12 ms. The base64 step costs the same on both sides, so REST
pays the difference in the larger body and the JSON parse.

Network latency is what decides which effect wins. On localhost the round-trip
is 0.06 ms, so latency is negligible and the difference is all per-query
overhead. Over a network, the connection that REST opens for every query costs
one round trip per query, while gRPC pays it once and then reuses the
connection. That is why the README expects REST `add` to match localhost within
a zone, where the RTT is well under a millisecond, but to reach about 270 ms
across regions, where the RTT to Frankfurt dominates everything else. The
large-payload results would move much less between the zones, because the
transfer time and the encoding cost do not depend on the distance.

## Resources and collaborators

* Author: Adhitya Mohan (CSCI 4253/5253)
* Collaborators: none
* External resources used:
  * gRPC Python tutorial (https://grpc.io/docs/tutorials/basic/python/)
  * Flask route tutorial (https://hackersandslackers.com/the-art-of-building-flask-routes/)
  * Flatirons image by Jesse Varner, modified by AzaToth, CC BY-SA 2.5
