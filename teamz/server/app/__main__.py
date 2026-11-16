import uvicorn

from .config import settings


def main() -> None:
    uvicorn.run("server.app.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
