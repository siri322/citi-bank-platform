from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
import random
import time
from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Prometheus Metrics
PAYMENT_REQUESTS = Counter(
    "payment_requests_total", 
    "Total number of payment requests", 
    ["status"]
)
PAYMENT_LATENCY = Histogram(
    "payment_latency_seconds", 
    "Latency of payment processing"
)

app = FastAPI(title="Payment Service")

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# OpenTelemetry Setup
JAEGER_HOST = os.getenv("JAEGER_HOST", "jaeger-all-in-one")
JAEGER_PORT = int(os.getenv("JAEGER_PORT", "6831"))
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account-service:8000")

resource = Resource.create({"service.name": "payment-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))

jaeger_exporter = JaegerExporter(
    agent_host_name=JAEGER_HOST,
    agent_port=JAEGER_PORT,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()

class PaymentRequest(BaseModel):
    account_id: str
    amount: float

@app.post("/pay")
async def process_payment(request: PaymentRequest):
    start_time = time.time()
    try:
        # Simulate processing delay
        time.sleep(random.uniform(0.05, 0.2))
        
        # Verify account
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ACCOUNT_SERVICE_URL}/account/{request.account_id}")
            response.raise_for_status()
            
        # Randomly fail some payments to simulate issues
        if random.random() < 0.05: # 5% failure rate
            PAYMENT_REQUESTS.labels(status="failed").inc()
            raise HTTPException(status_code=500, detail="Internal payment processing error")

        PAYMENT_REQUESTS.labels(status="success").inc()
        return {"status": "success", "transaction_id": "txn_" + str(random.randint(1000, 9999))}
    except httpx.HTTPStatusError as e:
        PAYMENT_REQUESTS.labels(status="failed").inc()
        raise HTTPException(status_code=400, detail="Account verification failed")
    except Exception as e:
        PAYMENT_REQUESTS.labels(status="failed").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        PAYMENT_LATENCY.observe(time.time() - start_time)

@app.get("/health")
def health_check():
    return {"status": "up"}
