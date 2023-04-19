from typing import Union

from fastapi import FastAPI, status

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "Worlddddddd"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get('/healthcheck', status_code=status.HTTP_200_OK)
def perform_healthcheck():
    return {'healthcheck': 'Everything OK!'}