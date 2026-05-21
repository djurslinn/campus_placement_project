from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('accounts.urls')),
    path('resumes/', include(('resumes.urls', 'resumes'), namespace='resumes')),
    path('attendance/', include('attendance.urls')),
    path('gd/', include('group_discussion.urls')),
    path('aptitude-test/', include('aptitude_test.urls')),
    path('mock-interviews/', include('mock_interviews.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
