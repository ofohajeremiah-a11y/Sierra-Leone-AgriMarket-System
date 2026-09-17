from pathlib import Path
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path, include

FRONTEND_INDEX = Path(__file__).resolve().parents[2] / 'frontend' / 'dist' / 'index.html'

def frontend(request):
    if not FRONTEND_INDEX.exists():
        raise Http404('Frontend build not found. Run npm run build in the frontend folder.')
    return FileResponse(open(FRONTEND_INDEX, 'rb'), content_type='text/html')

urlpatterns=[
    path('admin/',admin.site.urls),
    path('api/',include('api.urls')),
    path('', frontend),
]
