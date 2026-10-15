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
| REST add | 1.42 ms | 3.85 ms | 367 ms |
| gRPC add | 0.11 ms | 1.43 ms | 143 ms |
| REST rawimg | 2.95 ms | 8.97 ms | 1482 ms |
| gRPC rawimg | 3.19 ms | 14.37 ms | 375 ms |
| REST dotproduct | 1.84 ms | 4.39 ms | 398 ms |
| gRPC dotproduct | 0.12 ms | 1.50 ms | 161 ms |
| REST jsonimg | 14.12 ms | 43.58 ms | 1644 ms |
| gRPC jsonimg | 8.48 ms | 28.48 ms | 251 ms |
| PING | 0.06 ms | 0.49 ms | 159 ms |

Column setup:

- **Local:** server and client in one Ubuntu 26.04 container, `localhost`, mean
  of two runs, 1000 repetitions for `add` and `dotProduct`, 100 for the image
  calls.
- **Same-Zone:** two `e2-standard-2` VMs in `us-west1-a` (`lab6-server-a`
  10.138.0.23, `lab6-client-a` 10.138.0.22), over internal IPs, 1000 and 100
  repetitions.
- **Different Region:** client in `us-west1-a`, server `lab6-server-eu` in
  `europe-west3-a` (10.156.0.2), over internal IPs, 200 repetitions for `add`
  and `dotProduct`, 30 for the image calls.

`PING` is `ping -c 10` against the server for that column, the floor with no RPC
or Python overhead.

## Observations

The small-payload calls show the per-query overhead. REST opens a new TCP
connection for every query and encodes JSON text, so on localhost `add` costs
1.42 ms and `dotProduct` 1.84 ms. gRPC keeps one HTTP/2 connection for all
queries and sends binary protobuf, so the same calls cost 0.11 ms and 0.12 ms,
roughly 12 to 15 times less. Localhost ping is 0.06 ms, so the gRPC calls are
close to the bare network floor while the REST calls are dominated by connection
setup and text encoding.

The same-zone test isolates the network from the encoding. The round-trip is
0.49 ms, and REST `add` rises to 3.85 ms while gRPC `add` rises to 1.43 ms. The
REST number is about five round trips and the gRPC number about three, so at a
sub-millisecond RTT the fixed per-query overhead still dominates.

The different-region test is where latency takes over. The round-trip to
Frankfurt is 159 ms, and REST `add` costs 367 ms while gRPC `add` costs 143 ms.
Those are the numbers to compare against ping: REST pays about 2.3 round trips
per query, because the new TCP connection costs one round trip before the
request and response, while gRPC pays about 0.9 round trips, because the
connection is opened once and then reused. The README predicted about 270 ms for
REST `add` from Frankfurt, assuming a smaller RTT; the measured 367 ms follows
the same rule of roughly two round trips. This is the clearest evidence that the
connection model, not the payload encoding, is what REST loses on.

The large payloads behave differently. On localhost `rawImage` is a tie (2.95 ms
REST against 3.19 ms gRPC) because the 1.6 MB transfer dominates. Across
regions the connection model matters again: REST `rawImage` is 1482 ms against
375 ms for gRPC, because REST opens a new connection for each 1.6 MB body and
starts from a cold congestion window, while gRPC keeps the connection warm.
`jsonImage` is the slowest call everywhere, since it sends the image as base64
inside JSON, which is about a third larger and needs a JSON parse on both ends.
Its localhost result already favors gRPC (8.48 ms against 14.12 ms), and the gap
widens with distance (251 ms against 1644 ms).

In short: gRPC wins on the small calls at every distance, and the win grows with
latency because it amortizes the connection setup that REST repeats per query.
REST only matches gRPC when the payload is large enough that the transfer time
dwarfs the connection cost, which is the localhost `rawImage` case.

## Resources and collaborators

* Author: Adhitya Mohan (CSCI 4253/5253)
* Collaborators: none
* External resources used:
  * gRPC Python tutorial (https://grpc.io/docs/tutorials/basic/python/)
  * Flask route tutorial (https://hackersandslackers.com/the-art-of-building-flask-routes/)
  * Flatirons image by Jesse Varner, modified by AzaToth, CC BY-SA 2.5
