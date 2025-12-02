"""
Security utilities for DoS, XSS, CSRF, and SQL Injection prevention
"""

import logging
import re
from django.core.cache import cache
from django.http import HttpResponse
from functools import wraps
from django.utils.html import escape

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate Limiting to prevent DoS attacks
    Tracks API calls per user/IP and blocks if exceeded
    """
    
    def __init__(self, max_requests=100, window_seconds=3600):
        """
        Args:
            max_requests: Maximum requests allowed in time window
            window_seconds: Time window in seconds (default 1 hour)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    @staticmethod
    def is_request_allowed(client_ip, path):
        """
        Static method to check if request is allowed based on rate limits
        Used by RateLimitMiddleware
        
        Args:
            client_ip: Client IP address
            path: Request path (e.g., '/api/auth/login/')
        
        Returns:
            bool: True if allowed, False if rate limit exceeded
        """
        from django.conf import settings
        
        rate_config = settings.RATE_LIMIT_CONFIG
        
        # Find config for this path
        config = rate_config.get('default', {})
        
        # Check specific endpoint configs
        for limit_type, limit_config in rate_config.items():
            if limit_type != 'default':
                endpoints = limit_config.get('endpoints', [])
                
                # Check if current path matches any endpoint in config
                if any(path == ep or path.startswith(ep) for ep in endpoints):
                    config = limit_config
                    logger.debug(
                        f"Rate limit config for {path}: "
                        f"max={config.get('max_requests')} "
                        f"window={config.get('window_seconds')}s"
                    )
                    break
        
        # Generate cache key
        cache_key = f"rate_limit:{client_ip}:{path}"
        
        # Get current count from cache
        current_count = cache.get(cache_key, 0)
        
        # Get limits from config
        max_requests = config.get('max_requests', 100)
        window_seconds = config.get('window_seconds', 3600)
        
        logger.debug(
            f"Rate limit check | IP={client_ip} | Path={path} | "
            f"Current={current_count} | Max={max_requests}"
        )
        
        # Check if limit exceeded
        if current_count >= max_requests:
            logger.warning(
                f"⛔ RATE LIMIT EXCEEDED | IP={client_ip} | Path={path} | "
                f"Count={current_count} >= Max={max_requests}"
            )
            return False
        
        # Increment counter and set TTL
        cache.set(cache_key, current_count + 1, window_seconds)
        logger.debug(f"✓ Request allowed | Count incremented to {current_count + 1}")
        
        return True
    
    def get_client_identifier(self, request):
        """
        Get unique identifier for the client
        Priority: user_id > authenticated user > IP address
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'student_id'):
                return f"student_{request.user.student_id}"
            elif hasattr(request.user, 'admin_id'):
                return f"admin_{request.user.admin_id}"
        
        # Fallback to IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        return f"ip_{ip}"
    
    def is_rate_limited(self, request):
        """
        Check if client has exceeded rate limit
        
        Returns:
            tuple: (is_limited: bool, remaining_requests: int, reset_time: int)
        """
        client_id = self.get_client_identifier(request)
        cache_key = f"rate_limit_{client_id}"
        
        # Get current request count from cache
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.max_requests:
            # Get TTL (time to live)
            ttl = cache.ttl(cache_key) if hasattr(cache, 'ttl') else None
            return True, 0, ttl if ttl else self.window_seconds
        
        # Increment counter
        request_count += 1
        cache.set(cache_key, request_count, self.window_seconds)
        
        remaining = self.max_requests - request_count
        return False, remaining, self.window_seconds
    
    def get_rate_limit_headers(self, request):
        """Generate rate limit headers for response"""
        client_id = self.get_client_identifier(request)
        cache_key = f"rate_limit_{client_id}"
        request_count = cache.get(cache_key, 0)
        remaining = max(0, self.max_requests - request_count)
        
        ttl = cache.ttl(cache_key) if hasattr(cache, 'ttl') else self.window_seconds
        
        return {
            'X-RateLimit-Limit': str(self.max_requests),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(int(ttl) if ttl else self.window_seconds),
        }


def rate_limit(max_requests=100, window_seconds=3600):
    """
    Decorator for rate limiting API endpoints
    """
    limiter = RateLimiter(max_requests, window_seconds)
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            is_limited, remaining, reset_time = limiter.is_rate_limited(request)
            
            if is_limited:
                logger.warning(
                    f"Rate limit exceeded for {limiter.get_client_identifier(request)}"
                )
                response = HttpResponse(
                    f"Rate limit exceeded. Try again in {reset_time} seconds.",
                    status=429
                )
                response['Retry-After'] = str(reset_time)
                response['X-RateLimit-Remaining'] = '0'
                return response
            
            # Call the actual view
            response = view_func(self, request, *args, **kwargs)
            
            # Add rate limit headers
            for key, value in limiter.get_rate_limit_headers(request).items():
                response[key] = value
            
            return response
        
        return wrapper
    return decorator


class InputValidator:
    """Validate user input to prevent XSS, SQL Injection, etc."""
    
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?1?\d{9,15}$'
    NID_PATTERN = r'^\d{14}$'
    UID_PATTERN = r'^[a-zA-Z0-9]{5,20}$'
    NAME_PATTERN = r'^[a-zA-Z\s\u0600-\u06FF]{2,100}$'
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email or not isinstance(email, str):
            raise ValueError("Invalid email format")
        
        email = email.strip().lower()
        
        if not re.match(InputValidator.EMAIL_PATTERN, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:
            raise ValueError("Email too long")
        
        return email
    
    @staticmethod
    def validate_nid(nid):
        """Validate National ID (14 digits)"""
        if not nid or not isinstance(nid, str):
            raise ValueError("Invalid NID format")
        
        nid = nid.strip()
        
        if not re.match(InputValidator.NID_PATTERN, nid):
            raise ValueError("NID must be 14 digits")
        
        return nid
    
    @staticmethod
    def validate_uid(uid):
        """Validate University ID"""
        if not uid or not isinstance(uid, str):
            raise ValueError("Invalid UID format")
        
        uid = uid.strip()
        
        if not re.match(InputValidator.UID_PATTERN, uid):
            raise ValueError("UID must be 5-20 alphanumeric characters")
        
        return uid
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number"""
        if not phone or not isinstance(phone, str):
            raise ValueError("Invalid phone format")
        
        phone = phone.strip()
        
        if not re.match(InputValidator.PHONE_PATTERN, phone):
            raise ValueError("Invalid phone number format")
        
        return phone
    
    @staticmethod
    def validate_name(name):
        """Validate name (prevents XSS)"""
        if not name or not isinstance(name, str):
            raise ValueError("Invalid name format")
        
        name = name.strip()
        
        if not re.match(InputValidator.NAME_PATTERN, name):
            raise ValueError("Invalid name format")
        
        if len(name) > 100:
            raise ValueError("Name too long")
        
        return name
    
    @staticmethod
    def sanitize_string(value):
        """Sanitize string to prevent XSS"""
        if not isinstance(value, str):
            return value
        
        return escape(value)
    
    @staticmethod
    def validate_sql_injection(query_string):
        """Detect common SQL injection patterns"""
        suspicious_patterns = [
            r"('\s*OR\s*')",
            r"('\s*AND\s*')",
            r"(;\s*DROP\s+)",
            r"(;\s*DELETE\s+)",
            r"(UNION\s+SELECT)",
            r"(--\s*$)",
            r"(/\*.*\*/)",
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                logger.warning(f"Potential SQL injection: {query_string[:50]}")
                raise ValueError("Invalid input detected")
        
        return True


class SecurityHeaders:
    """Add security headers to responses"""
    
    @staticmethod
    def add_security_headers(response):
        """Add standard security headers to HTTP response"""
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class AuditLogger:
    """Log security-relevant events for audit trail"""
    
    AUDIT_LOGGER = logging.getLogger('audit')
    
    @staticmethod
    def log_login(user_id, user_type, auth_method, ip_address, success=True):
        """Log login attempts"""
        status = "SUCCESS" if success else "FAILED"
        AuditLogger.AUDIT_LOGGER.info(
            f"Login {status} | user_id={user_id} | type={user_type} | "
            f"method={auth_method} | ip={ip_address}"
        )
    
    @staticmethod
    def log_data_access(user_id, user_type, resource, action, ip_address):
        """Log data access"""
        AuditLogger.AUDIT_LOGGER.info(
            f"Data Access | user_id={user_id} | type={user_type} | "
            f"resource={resource} | action={action} | ip={ip_address}"
        )
    
    @staticmethod
    def log_data_modification(user_id, user_type, resource, action, changes, ip_address):
        """Log data modification"""
        AuditLogger.AUDIT_LOGGER.warning(
            f"Data Modification | user_id={user_id} | type={user_type} | "
            f"resource={resource} | action={action} | changes={changes} | ip={ip_address}"
        )
    
    @staticmethod
    def log_failed_auth(email, reason, ip_address):
        """Log failed authentication"""
        AuditLogger.AUDIT_LOGGER.warning(
            f"Failed Auth | email={email} | reason={reason} | ip={ip_address}"
        )
    
    @staticmethod
    def log_rate_limit_exceeded(client_id, ip_address, endpoint):
        """Log rate limit violations"""
        AuditLogger.AUDIT_LOGGER.warning(
            f"Rate Limit Exceeded | client_id={client_id} | "
            f"ip={ip_address} | endpoint={endpoint}"
        )


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    return ip



@staticmethod
def is_request_allowed(client_ip, path):
    """Check if request is allowed based on rate limits"""
    from django.conf import settings
    
    print(f"\n🔐 RateLimiter.is_request_allowed()")
    print(f"  Client IP: {client_ip}")
    print(f"  Path: {path}")
    
    rate_config = settings.RATE_LIMIT_CONFIG
    
    # Find config for this path
    config = rate_config.get('default', {})
    print(f"  Starting with default config: {config}")
    
    # Check specific endpoint configs
    for limit_type, limit_config in rate_config.items():
        if limit_type != 'default':
            endpoints = limit_config.get('endpoints', [])
            print(f"  Checking {limit_type}: endpoints={endpoints}")
            
            # Check if current path matches any endpoint in config
            for endpoint in endpoints:
                if path == endpoint or path.startswith(endpoint):
                    config = limit_config
                    print(f"  ✓ MATCH FOUND! Using {limit_type} config")
                    print(f"    max_requests={config.get('max_requests')}")
                    print(f"    window_seconds={config.get('window_seconds')}")
                    break
    
    # Generate cache key
    cache_key = f"rate_limit:{client_ip}:{path}"
    print(f"  Cache key: {cache_key}")
    
    # Get current count from cache
    current_count = cache.get(cache_key, 0)
    print(f"  Current count: {current_count}")
    
    # Get limits from config
    max_requests = config.get('max_requests', 100)
    window_seconds = config.get('window_seconds', 3600)
    print(f"  Limits: max={max_requests}, window={window_seconds}s")
    
    # Check if limit exceeded
    if current_count >= max_requests:
        print(f"  ❌ LIMIT EXCEEDED: {current_count} >= {max_requests}")
        logger.warning(
            f"⛔ Rate limit exceeded | IP={client_ip} | Path={path} | "
            f"Count={current_count} >= Max={max_requests}"
        )
        return False
    
    # Increment counter and set TTL
    new_count = current_count + 1
    cache.set(cache_key, new_count, window_seconds)
    print(f"  ✓ ALLOWED - Counter incremented: {current_count} → {new_count}")
    
    return True