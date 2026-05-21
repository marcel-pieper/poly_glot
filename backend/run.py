import os

import uvicorn

if __name__ == "__main__":
    is_prod = os.getenv("ENV") == "production" or os.getenv("APP_ENV") == "production"
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1" if is_prod else "0.0.0.0",
        port=8001,
        reload=not is_prod,
    )
