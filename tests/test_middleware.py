import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import Response

from src.api.middleware import ProxyMiddleware, SSEMiddleware

def test_proxy_middleware_conflicting_headers():
    app = FastAPI()
    app.add_middleware(ProxyMiddleware)
    
    @app.get("/")
    def read_root():
        return {"status": "ok"}
        
    client = TestClient(app)
    
    # Normal request
    response = client.get("/")
    assert response.status_code == 200
    
    # Request with forwarded
    response = client.get("/", headers={"Forwarded": "for=192.0.2.60"})
    assert response.status_code == 200
    
    # Request with x-forwarded-for
    response = client.get("/", headers={"X-Forwarded-For": "192.0.2.60"})
    assert response.status_code == 200
    
    # Conflicting headers
    response = client.get("/", headers={
        "Forwarded": "for=192.0.2.60",
        "X-Forwarded-For": "192.0.2.60"
    })
    assert response.status_code == 400
    assert response.text == "Conflicting forwarded headers"

def test_sse_middleware_compression():
    app = FastAPI()
    app.add_middleware(SSEMiddleware)
    
    @app.get("/sse")
    def sse_endpoint():
        return Response(content="data: ok\n\n", media_type="text/event-stream")
        
    @app.get("/normal")
    def normal_endpoint():
        return {"status": "ok"}
        
    client = TestClient(app)
    
    # Normal request
    response = client.get("/normal", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert "no-transform" not in response.headers.get("Cache-Control", "")
    
    # SSE request without accept-encoding
    response = client.get("/sse", headers={"Accept": "text/event-stream"})
    assert response.status_code == 200
    assert "no-transform" in response.headers.get("Cache-Control", "")
    
    # SSE request with accept-encoding
    response = client.get("/sse", headers={
        "Accept": "text/event-stream",
        "Accept-Encoding": "gzip"
    })
    assert response.status_code == 200
    assert "no-transform" in response.headers.get("Cache-Control", "")
