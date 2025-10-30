# apps/accounts/schema.py
from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CustomJWTAuthScheme(OpenApiAuthenticationExtension):
    # dotted path to your class
    target_class = 'apps.accounts.authentication.CustomJWTAuthentication'

    # the name that will appear in components.securitySchemes
    name = 'Bearer'                         # <- keep it identical to
                                            #    SPECTACULAR_SETTINGS

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }