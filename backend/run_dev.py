import os
import uvicorn


def main() -> None:
    port = int(os.getenv("PORT", 8000))
    # Start Uvicorn with explicit protocol/loop to avoid environment-specific hangs
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        loop="asyncio",
        http="h11",
        workers=1,
        log_level="debug",
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    main()