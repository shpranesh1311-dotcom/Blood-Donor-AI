"""
run.py
======
Convenience entrypoint. From the project root, run:

    python run.py

This starts the Uvicorn server with the FastAPI app defined in app/main.py.
Then open http://127.0.0.1:8000 in your browser.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
