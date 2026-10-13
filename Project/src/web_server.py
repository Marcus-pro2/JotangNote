from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/hello")
def hello():
    return "Hello World From Web Application!"

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="127.0.0.1", port=8080)
