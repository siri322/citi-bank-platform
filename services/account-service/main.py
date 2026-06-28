from fastapi import FastAPI, HTTPException
import os
import time
import random
from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Prometheus Metrics
ACCOUNT_REQUESTS = Counter(
    "account_requests_total", 
    "Total number of account verification requests", 
    ["status"]
)
ACCOUNT_LATENCY = Histogram(
    "account_latency_seconds", 
    "Latency of account verification"
)

app = FastAPI(title="Account Service")

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# OpenTelemetry Setup
JAEGER_HOST = os.getenv("JAEGER_HOST", "jaeger-all-in-one")
JAEGER_PORT = int(os.getenv("JAEGER_PORT", "6831"))

resource = Resource.create({"service.name": "account-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))

jaeger_exporter = JaegerExporter(
    agent_host_name=JAEGER_HOST,
    agent_port=JAEGER_PORT,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

FastAPIInstrumentor.instrument_app(app)

# Mock DB
VALID_ACCOUNTS = {"acc_123", "acc_456", "acc_789"}

@app.get("/account/{account_id}")
def verify_account(account_id: str):
    start_time = time.time()
    try:
        # Simulate DB lookup latency
        time.sleep(random.uniform(0.01, 0.05))
        
        if account_id not in VALID_ACCOUNTS:
            ACCOUNT_REQUESTS.labels(status="failed").inc()
            raise HTTPException(status_code=404, detail="Account not found")
            
        ACCOUNT_REQUESTS.labels(status="success").inc()
        return {"account_id": account_id, "status": "active"}
    finally:
        ACCOUNT_LATENCY.observe(time.time() - start_time)

@app.get("/health")
def health_check():
    return {"status": "up"}
