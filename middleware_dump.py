import logging

logger = logging.getLogger(__name__)

class DumpRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request path and body
        try:
            body = request.body.decode('utf-8')
        except:
            body = '<binary>'
            
        with open('/home/ubuntu/project/temp_insight_deploy/backend/request_dump.log', 'a') as f:
            f.write(f"[{request.method}] {request.path}\nBody: {body}\nHeaders: {request.headers}\n\n")

        response = self.get_response(request)
        return response
