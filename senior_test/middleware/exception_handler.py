import uuid
from django.http import JsonResponse
from django.utils.timezone import now
from senior_test.exceptions.domain_exception import DomainException

class CustomExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Asignamos un correlation_id a la petición
        request.correlation_id = str(uuid.uuid4())
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, DomainException):
            payload = {
                "status_code": exception.status_code,
                "error_code": exception.error_code,
                "message": exception.message,
                "timestamp": now().isoformat(),
                "path": request.path,
                "correlation_id": getattr(request, "correlation_id", None)
            }
            return JsonResponse(payload, status=exception.status_code)
        
        # Deja que Django maneje excepciones no controladas (500)
        return None