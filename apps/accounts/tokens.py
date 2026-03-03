from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator for password reset.
    Works for both Students and AdminsUser models.
    """
    def _make_hash_value(self, user, timestamp):
        # Works for both Students and AdminsUser
        user_id = getattr(user, 'student_id', None) or getattr(user, 'admin_id', None)
        return (
            six.text_type(user_id) + 
            six.text_type(timestamp) +
            six.text_type(user.password)
        )

password_reset_token = AccountActivationTokenGenerator()
