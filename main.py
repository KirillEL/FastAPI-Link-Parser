import uvicorn


def main():
    uvicorn.run(
        app="app.api.server:app",
        workers=1,
        host="0.0.0.0",
        port=2222
    )


if __name__ == "__main__":
    main()
