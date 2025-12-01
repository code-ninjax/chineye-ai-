import os
import sys
from pathlib import Path
import uvicorn

# Ensure repo root is on sys.path so imports work from any CWD
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app


def main() -> None:
    port = int(os.getenv("PORT", 8000))
    # Start Uvicorn with explicit protocol/loop to avoid environment-specific hangs
    uvicorn.run(
        app,
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