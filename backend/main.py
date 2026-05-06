from fastapi import FastAPI

app = FastAPI(title="Ai Assistant Showcase API")


@app.get("/")
async def root():
    return {"message": "Welcome to the Ai Assistant Showcase API"}
