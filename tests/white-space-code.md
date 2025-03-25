
```python

"""
AuthData is a dataclass that represents Authentication data sent from Autoscaler to client requesting a route.
When a user requests a route from autoscaler, see Vast's Serverless documentation for how routing and AuthData
work.
When a user receives a route for this PyWorker, they'll call PyWorkers API with the following JSON:
{
    auth_data: AuthData,
    payload : InputData # defined above
}
"""
from aiohttp import web

from lib.data_types import EndpointHandler, JsonDataException
from lib.server import start_server
from .data_types import InputData
```
