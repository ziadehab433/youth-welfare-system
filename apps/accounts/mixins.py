"""
Reusable mixins for admin actions with consistent logging and transaction handling.
"""

from django.db import transaction
from apps.accounts.utils import get_current_admin, get_client_ip, log_data_access


class AdminActionMixin:
    """
    Mixin that provides a reusable mechanism for admin actions with:
    - Automatic admin retrieval
    - Client IP extraction
    - Transaction wrapping
    - Consistent logging after successful operations
    """
    
    def execute_admin_action(
        self,
        request,
        action_name,
        target_type,
        business_operation,
        solidarity_id=None,
        family_id=None,
        event_id=None,
        student_id=None
    ):
        """
        Execute an admin action with automatic transaction handling and logging.
        
        Args:
            request: The HTTP request object
            action_name: Description of the action being performed (e.g., 'موافقة مبدئية')
            target_type: Type of target entity (e.g., 'اسر', 'نشاط', 'تكافل')
            business_operation: Callable that performs the business logic.
                               Should accept (admin, ip_address) as parameters.
                               Should return the result data.
            solidarity_id: Optional solidarity ID for logging
            family_id: Optional family ID for logging
            event_id: Optional event ID for logging (can be None for create operations)
            student_id: Optional student ID for logging
        
        Returns:
            The result returned by business_operation
        """
        admin = get_current_admin(request)
        ip_address = get_client_ip(request)
        
        with transaction.atomic():
            # Execute the business operation
            result = business_operation(admin, ip_address)
            
            # For create operations, extract event_id from result if it's an object
            final_event_id = event_id
            if event_id is None and hasattr(result, 'event_id'):
                final_event_id = result.event_id
            
            # Log the action after successful execution
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action=action_name,
                target_type=target_type,
                solidarity_id=solidarity_id,
                family_id=family_id,
                event_id=final_event_id,
                ip_address=ip_address,
                student_id=student_id
            )
        
        return result
