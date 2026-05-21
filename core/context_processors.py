from django.core.cache import cache
from accounts.models import StudentProfile, Course
from core.models import PlacementDrive
from mock_interviews.models import MockInterviewSession

def coordinator_stats(request):
    if request.user.is_authenticated and request.user.role == 'coordinator':
        # Cache for 5 minutes
        stats = cache.get('coordinator_dashboard_stats')
        if not stats:
            stats = {
                'coord_total_students': StudentProfile.objects.count(),
                'coord_total_departments': Course.objects.count(),
                'coord_total_drives': PlacementDrive.objects.count(),
                'coord_total_mock_interviews': MockInterviewSession.objects.count(),
            }
            cache.set('coordinator_dashboard_stats', stats, 300)
        return stats
    return {}
