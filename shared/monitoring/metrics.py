"""
Comprehensive metrics collection middleware for FastAPI services
Provides Prometheus metrics, structured logging, and distributed tracing
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
import structlog
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'service'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint', 'service']
)

# AI/ML specific metrics
ai_inference_duration_seconds = Histogram(
    'ai_inference_duration_seconds',
    'AI model inference duration in seconds',
    ['model_name', 'service'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

ai_model_errors_total = Counter(
    'ai_model_errors_total',
    'Total AI model errors',
    ['model_name', 'error_type', 'service']
)

ai_model_requests_total = Counter(
    'ai_model_requests_total',
    'Total AI model requests',
    ['model_name', 'service']
)

# Memory and resource metrics
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['service']
)

gpu_memory_usage_bytes = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage in bytes',
    ['gpu_id', 'service']
)

# Queue metrics
queue_length = Gauge(
    'queue_length',
    'Current queue length',
    ['queue_name', 'service']
)

queue_jobs_processed_total = Counter(
    'queue_jobs_processed_total',
    'Total jobs processed from queue',
    ['queue_name', 'status', 'service']
)

queue_job_duration_seconds = Histogram(
    'queue_job_duration_seconds',
    'Queue job processing duration',
    ['queue_name', 'service'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0]
)

# Business metrics
generation_requests_total = Counter(
    'generation_requests_total',
    'Total generation requests',
    ['model_type', 'status', 'service']
)

quality_assessment_score = Histogram(
    'quality_assessment_score',
    'Quality assessment scores',
    ['assessment_type', 'service'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

recommendation_requests_total = Counter(
    'recommendation_requests_total',
    'Total recommendation requests',
    ['recommendation_type', 'service']
)

recommendation_clicks_total = Counter(
    'recommendation_clicks_total',
    'Total recommendation clicks',
    ['recommendation_type', 'service']
)

# Service info
service_info = Info(
    'service_info',
    'Service information'
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for collecting metrics and structured logging."""
    
    def __init__(self, app: FastAPI, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        
        # Set service info
        service_info.info({
            'service': service_name,
            'version': getattr(app, 'version', '1.0.0'),
            'description': getattr(app, 'description', ''),
            'started_at': datetime.utcnow().isoformat()
        })
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with metrics collection and logging."""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Extract request info
        method = request.method
        path = request.url.path
        endpoint = self._get_endpoint_name(path)
        
        # Add request ID to headers for tracing
        request.state.request_id = request_id
        
        # Track in-progress requests
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).inc()
        
        # Structured logging - request start
        logger.info(
            "Request started",
            request_id=request_id,
            method=method,
            path=path,
            endpoint=endpoint,
            service=self.service_name,
            user_agent=request.headers.get("user-agent"),
            client_ip=self._get_client_ip(request)
        )
        
        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            # Handle exceptions
            duration = time.time() - start_time
            
            logger.error(
                "Request failed with exception",
                request_id=request_id,
                method=method,
                path=path,
                endpoint=endpoint,
                service=self.service_name,
                duration=duration,
                error=str(e),
                exc_info=True
            )
            
            # Record metrics for failed requests
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500,
                service=self.service_name
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                service=self.service_name
            ).observe(duration)
            
            raise
        
        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint,
                service=self.service_name
            ).dec()
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            service=self.service_name
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).observe(duration)
        
        # Structured logging - request complete
        log_level = "warning" if status_code >= 400 else "info"
        getattr(logger, log_level)(
            "Request completed",
            request_id=request_id,
            method=method,
            path=path,
            endpoint=endpoint,
            service=self.service_name,
            status_code=status_code,
            duration=duration,
            response_size=response.headers.get("content-length", 0)
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _get_endpoint_name(self, path: str) -> str:
        """Extract endpoint name from path for metrics labeling."""
        # Remove query parameters and normalize path
        path = path.split('?')[0]
        
        # Replace dynamic segments with placeholders
        path_parts = path.split('/')
        normalized_parts = []
        
        for part in path_parts:
            if not part:
                continue
            
            # Check if part looks like an ID or UUID
            if (part.isdigit() or 
                len(part) == 36 and part.count('-') == 4 or  # UUID
                len(part) > 10 and part.replace('-', '').replace('_', '').isalnum()):
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)
        
        return '/' + '/'.join(normalized_parts) if normalized_parts else '/'
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"


class AIMetricsCollector:
    """Collector for AI/ML specific metrics."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    @asynccontextmanager
    async def track_inference(self, model_name: str):
        """Context manager to track AI inference metrics."""
        start_time = time.time()
        
        ai_model_requests_total.labels(
            model_name=model_name,
            service=self.service_name
        ).inc()
        
        try:
            yield
        except Exception as e:
            # Record error
            ai_model_errors_total.labels(
                model_name=model_name,
                error_type=type(e).__name__,
                service=self.service_name
            ).inc()
            
            logger.error(
                "AI model inference failed",
                model_name=model_name,
                service=self.service_name,
                error=str(e),
                exc_info=True
            )
            raise
        finally:
            # Record duration
            duration = time.time() - start_time
            ai_inference_duration_seconds.labels(
                model_name=model_name,
                service=self.service_name
            ).observe(duration)
            
            logger.info(
                "AI inference completed",
                model_name=model_name,
                service=self.service_name,
                duration=duration
            )
    
    def record_quality_score(self, assessment_type: str, score: float):
        """Record quality assessment score."""
        quality_assessment_score.labels(
            assessment_type=assessment_type,
            service=self.service_name
        ).observe(score)
    
    def record_generation_request(self, model_type: str, status: str):
        """Record generation request."""
        generation_requests_total.labels(
            model_type=model_type,
            status=status,
            service=self.service_name
        ).inc()
    
    def record_recommendation_request(self, recommendation_type: str):
        """Record recommendation request."""
        recommendation_requests_total.labels(
            recommendation_type=recommendation_type,
            service=self.service_name
        ).inc()
    
    def record_recommendation_click(self, recommendation_type: str):
        """Record recommendation click."""
        recommendation_clicks_total.labels(
            recommendation_type=recommendation_type,
            service=self.service_name
        ).inc()


class QueueMetricsCollector:
    """Collector for queue-related metrics."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def update_queue_length(self, queue_name: str, length: int):
        """Update queue length metric."""
        queue_length.labels(
            queue_name=queue_name,
            service=self.service_name
        ).set(length)
    
    @asynccontextmanager
    async def track_job_processing(self, queue_name: str):
        """Context manager to track job processing metrics."""
        start_time = time.time()
        
        try:
            yield
            status = "success"
        except Exception as e:
            status = "failed"
            logger.error(
                "Queue job processing failed",
                queue_name=queue_name,
                service=self.service_name,
                error=str(e),
                exc_info=True
            )
            raise
        finally:
            # Record processing time and status
            duration = time.time() - start_time
            
            queue_job_duration_seconds.labels(
                queue_name=queue_name,
                service=self.service_name
            ).observe(duration)
            
            queue_jobs_processed_total.labels(
                queue_name=queue_name,
                status=status,
                service=self.service_name
            ).inc()


def setup_monitoring(app: FastAPI, service_name: str, jaeger_endpoint: Optional[str] = None):
    """Setup comprehensive monitoring for a FastAPI application."""
    
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware, service_name=service_name)
    
    # Setup distributed tracing if Jaeger endpoint provided
    if jaeger_endpoint:
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_endpoint.split(':')[0],
            agent_port=int(jaeger_endpoint.split(':')[1]) if ':' in jaeger_endpoint else 14268,
        )
        
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint."""
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Add health check with detailed status
    @app.get("/health/detailed")
    async def detailed_health():
        """Detailed health check with metrics."""
        return {
            "status": "healthy",
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "version": getattr(app, 'version', '1.0.0'),
            "metrics": {
                "requests_total": sum([
                    metric.samples[0].value 
                    for metric in http_requests_total.collect() 
                    for sample in metric.samples
                ]),
                "requests_in_progress": sum([
                    metric.samples[0].value 
                    for metric in http_requests_in_progress.collect() 
                    for sample in metric.samples
                ])
            }
        }
    
    return AIMetricsCollector(service_name), QueueMetricsCollector(service_name)


def get_resource_metrics(service_name: str):
    """Collect and update resource usage metrics."""
    import psutil
    import os
    
    try:
        # Memory usage
        process = psutil.Process(os.getpid())
        memory_usage_bytes.labels(service=service_name).set(process.memory_info().rss)
        
        # GPU memory if available
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    gpu_memory_usage_bytes.labels(
                        gpu_id=str(i),
                        service=service_name
                    ).set(torch.cuda.memory_allocated(i))
        except ImportError:
            pass
            
    except Exception as e:
        logger.warning(f"Failed to collect resource metrics: {e}")


async def start_metrics_collection_task(service_name: str):
    """Start background task for periodic metrics collection."""
    async def collect_metrics():
        while True:
            try:
                get_resource_metrics(service_name)
                await asyncio.sleep(15)  # Collect every 15 seconds
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)  # Back off on error
    
    asyncio.create_task(collect_metrics())