"""
Security middleware for adding headers and rate limiting
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .security import SecurityHeaders, RateLimiter, AuditLogger, get_client_ip

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger('audit')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    Excludes documentation endpoints to allow Swagger/ReDoc to load
    """
    
    def process_response(self, request, response):
        """Add security headers (but skip CSP for docs)"""
        
        # Skip CSP for documentation endpoints - let Django's CSP settings handle it
        if self._is_docs_endpoint(request.path):
            logger.debug(f"Skipping CSP for docs endpoint: {request.path}")
            return response
        
        # Add security headers for all other endpoints
        return SecurityHeaders.add_security_headers(response)
    
    @staticmethod
    def _is_docs_endpoint(path):
        """Check if this is a documentation endpoint"""
        docs_paths = [
            '/api/docs/',
            '/api/schema/',
            '/admin/',
        ]
        return any(path.startswith(p) for p in docs_paths)


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Log all API requests for audit trail
    """
    
    # Paths to skip logging
    SKIP_PATHS = [
        '/static/',
        '/media/',
        '/.well-known/',  # Skip chrome devtools and other well-known paths
    ]
    
    def process_request(self, request):
        """Check rate limits"""
        
        print(f"\n{'='*60}")
        print(f"🔍 RateLimitMiddleware CHECK")
        print(f"Path: {request.path}")
        print(f"Method: {request.method}")
        
        # Skip rate limiting for docs
        if request.path.startswith('/api/docs/') or request.path.startswith('/api/schema/'):
            print("⏭️ Skipping (docs endpoint)")
            return None
        
        client_ip = get_client_ip(request)
        print(f"Client IP: {client_ip}")
        
        # Apply rate limiting
        try:
            is_allowed = RateLimiter.is_request_allowed(
                client_ip=client_ip,
                path=request.path
            )
            
            print(f"Rate limit check result: {is_allowed}")
            
            if not is_allowed:
                print(f"❌ BLOCKING REQUEST - Rate limit exceeded")
                logger.warning(
                    f"⛔ Rate limit exceeded | path={request.path} | ip={client_ip}"
                )
                from django.http import JsonResponse
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded. Please try again later.',
                        'retry_after': 60
                    },
                    status=429
                )
            else:
                print(f"✓ ALLOWING REQUEST")
        
        except Exception as e:
            print(f"❌ Error in rate limiting: {str(e)}")
            logger.error(f"Rate limiting error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
        print(f"{'='*60}\n")
        return None
    
    def process_response(self, request, response):
        """Log API response"""
        
        # Skip logging for certain paths
        if self._should_skip(request.path):
            return response
        
        # Calculate request duration
        duration = 0
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Log API request
        log_message = (
            f"API Request | "
            f"method={request.method} | "
            f"path={request.path} | "
            f"status={response.status_code} | "
            f"duration={duration:.3f}s | "
            f"ip={client_ip}"
        )
        
        logger.info(log_message)
        
        # Log audit trail for sensitive operations
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


class RateLimitMiddleware(MiddlewareMixin):
    """
    Apply rate limiting to sensitive endpoints
    """
    
    def process_request(self, request):
        """Check rate limits"""
        
        # Skip rate limiting for docs
        if request.path.startswith('/api/docs/') or request.path.startswith('/api/schema/'):
            return None
        
        # Apply rate limiting
        try:
            is_allowed = RateLimiter.is_request_allowed(
                client_ip=get_client_ip(request),
                path=request.path
            )
            
            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded | "
                    f"path={request.path} | "
                    f"ip={get_client_ip(request)}"
                )
                from django.http import JsonResponse
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded. Please try again later.',
                        'retry_after': 60
                    },
                    status=429
                )
        
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # Don't block requests if rate limiting fails
            return None
        
        return None