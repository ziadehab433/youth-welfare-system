"""
Security middleware for adding headers and rate limiting
"""

import time
import logging
import sys
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import JsonResponse
from .security import SecurityHeaders, RateLimiter, AuditLogger, get_client_ip

# ✅ Get all loggers
logger = logging.getLogger(__name__)
audit_logger = logging.getLogger('audit')
sec_logger = logging.getLogger('security')

# ✅ Force print to console to verify it's being called
print(f"\n🔧 MIDDLEWARE LOADED - Logger Config:")
print(f"   sec_logger name: {sec_logger.name}")
print(f"   sec_logger level: {sec_logger.level} (WARNING=30)")
print(f"   sec_logger handlers: {sec_logger.handlers}")
print(f"   sec_logger effective level: {sec_logger.getEffectiveLevel()}\n")


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def process_response(self, request, response):
        """Add security headers"""
        if self._is_docs_endpoint(request.path):
            logger.debug(f"Skipping CSP for docs endpoint: {request.path}")
            return response
        return SecurityHeaders.add_security_headers(response)
    
    @staticmethod
    def _is_docs_endpoint(path):
        """Check if this is a documentation endpoint"""
        docs_paths = ['/api/docs/', '/api/schema/', '/admin/']
        return any(path.startswith(p) for p in docs_paths)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Apply rate limiting to all requests (except docs)
    """
    
    SKIP_PATHS = [
        '/static/',
        '/media/',
        '/.well-known/',
        '/api/docs/',
        '/api/schema/',
        '/admin/',
    ]
    
    def process_request(self, request):
        """Check rate limits on incoming request"""
        
        # Skip rate limiting for certain paths
        if self._should_skip(request.path):
            return None
        
        client_ip = get_client_ip(request)
        
        try:
            # Check if request is allowed
            is_allowed = RateLimiter.is_request_allowed(
                client_ip=client_ip,
                path=request.path
            )
            
            if not is_allowed:
                # 🔴 MULTIPLE LOGGING ATTEMPTS
                
                # Method 1: Direct print (should always work)
                print(f"\n{'='*60}")
                print(f"🚨 RATE LIMIT EXCEEDED")
                print(f"   Method: {request.method}")
                print(f"   Path: {request.path}")
                print(f"   IP: {client_ip}")
                print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}\n")
                sys.stdout.flush()  # Force flush
                
                # Method 2: Using sec_logger
                message = (
                    f"⛔ RATE LIMIT EXCEEDED | "
                    f"method={request.method} | "
                    f"path={request.path} | "
                    f"ip={client_ip}"
                )
                
                print(f"📝 Attempting to log: {message}")
                print(f"   Logger: {sec_logger.name}")
                print(f"   Level: WARNING (30)")
                
                # ✅ Multiple ways to log
                sec_logger.warning(message)
                sec_logger.warn(message)  # Alias
                
                # Method 3: Also try error level
                sec_logger.error(message)
                
                # Force flush handlers
                for handler in sec_logger.handlers:
                    print(f"   Flushing handler: {handler}")
                    handler.flush()
                
                print(f"✓ Logging complete\n")
                
                return JsonResponse(
                    {
                        'detail': 'Too many requests. Please try again later.',
                        'retry_after': 60
                    },
                    status=429
                )
        
        except Exception as e:
            print(f"❌ Rate limiting error: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Rate limiting error: {str(e)}")
            return None
        
        return None
    
    @staticmethod
    def _should_skip(path):
        """Check if path should be skipped from rate limiting"""
        skip_paths = [
            '/static/',
            '/media/',
            '/.well-known/',
            '/api/docs/',
            '/api/schema/',
            '/admin/',
        ]
        return any(path.startswith(p) for p in skip_paths)


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Log all API requests for audit trail
    """
    
    SKIP_PATHS = [
        '/static/',
        '/media/',
        '/.well-known/',
    ]
    
    def process_request(self, request):
        """Track request start time"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log API response"""
        
        if self._should_skip(request.path):
            return response
        
        duration = 0
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        
        client_ip = get_client_ip(request)
        
        log_message = (
            f"method={request.method} | "
            f"path={request.path} | "
            f"status={response.status_code} | "
            f"duration={duration:.3f}s | "
            f"ip={client_ip}"
        )
        
        logger.info(log_message)
        
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            audit_logger.info(
                f"{request.method} {request.path} | "
                f"User: {request.user} | "
                f"Status: {response.status_code} | "
                f"IP: {client_ip}"
            )
        
        return response
    
    @staticmethod
    def _should_skip(path):
        """Check if path should be skipped from logging"""
        skip_paths = [
            '/static/',
            '/media/',
            '/.well-known/',
        ]
        return any(path.startswith(p) for p in skip_paths)