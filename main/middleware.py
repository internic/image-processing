
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class CleanUpMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.process_response(request, response)
        return response

    def process_response(self, request, response):
        # Check if the session has the uploaded_images key and if the session should be cleared
        if request.session.get('clear_session_files', False):
            uploaded_images = request.session.pop('uploaded_images', [])
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
            for filename in uploaded_images:
                if fs.exists(filename):
                    fs.delete(filename)
            request.session.modified = True
        return response
