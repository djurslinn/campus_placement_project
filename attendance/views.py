from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from .models import physicalSession, Attendance
from .forms import SessionForm
from accounts.models import User, StudentProfile
from core.views import coordinator_required, student_required
from core.models import PlacementDrive, JobApplication, TestAttempt as CoreTestAttempt, MockInterview
from aptitude_test.models import PDFTestResult
from group_discussion.models import GDGroupMember
from mock_interviews.models import MockInterviewEvaluation, MockInterviewSession, MockInterviewPair
from mock_interviews.utils import get_suggestions
from .utils import get_performance_insights

@login_required
@coordinator_required
def manage_sessions(request):
    sessions = physicalSession.objects.filter(coordinator=request.user).annotate(
        present_count=Count('attendances', filter=Q(attendances__is_present=True))
    ).order_by('-date', '-time')
    
    for session in sessions:
        session.is_marked = session.attendances.exists()
        
        # Calculate target count per session
        target_students = StudentProfile.objects.all()
        if session.target_type == 'department' and session.department:
            target_students = target_students.filter(user__department=session.department)
        elif session.target_type == 'drive' and session.target_drive:
            drive = session.target_drive
            target_students = target_students.filter(cgpa__gte=drive.min_cgpa or 0)
            if not drive.is_for_all_departments:
                target_students = target_students.filter(user__department__in=drive.eligible_departments.all())
        
        target_count = target_students.count()
        if target_count > 0:
            session.attendance_percentage = (session.present_count / target_count) * 100
        else:
            session.attendance_percentage = 0

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.coordinator = request.user
            session.save()
            messages.success(request, 'Session created successfully.')
            return redirect('attendance:manage_sessions')
    else:
        form = SessionForm()
    
    return render(request, 'attendance/manage_sessions.html', {
        'sessions': sessions,
        'form': form
    })

@login_required
@coordinator_required
def delete_session(request, session_id):
    session = get_object_or_404(physicalSession, id=session_id, coordinator=request.user)
    session.delete()
    messages.success(request, 'Session deleted successfully.')
    return redirect('attendance:manage_sessions')

@login_required
@coordinator_required
def mark_attendance(request, session_id):
    session = get_object_or_404(physicalSession, id=session_id)
    
    # Filter students based on targeting
    students = StudentProfile.objects.select_related('user')
    if session.target_type == 'department' and session.department:
        students = students.filter(user__department=session.department)
    elif session.target_type == 'drive' and session.target_drive:
        drive = session.target_drive
        students = students.filter(cgpa__gte=drive.min_cgpa or 0)
        if not drive.is_for_all_departments:
            students = students.filter(user__department__in=drive.eligible_departments.all())
    
    students = students.all()
    
    # Get existing attendance records for this session
    attendance_records = Attendance.objects.filter(session=session)
    present_student_ids = list(attendance_records.filter(is_present=True).values_list('student_id', flat=True))
    
    if request.method == 'POST':
        selected_student_ids = [int(sid) for sid in request.POST.getlist('students')]
        
        # Reset attendance for this session
        Attendance.objects.filter(session=session).delete()
        
        # Mark all students (create records for everyone to track that attendance was formally taken)
        attendance_objs = []
        for student_profile in students:
            is_p = student_profile.user.id in selected_student_ids
            attendance_objs.append(Attendance(
                session=session, 
                student=student_profile.user, 
                is_present=is_p
            ))
        
        Attendance.objects.bulk_create(attendance_objs)
        messages.success(request, f'Attendance marked for {len(students)} target students.')
        return redirect('attendance:manage_sessions')

    return render(request, 'attendance/mark_attendance.html', {
        'session': session,
        'students': students,
        'present_student_ids': present_student_ids
    })

@login_required
@student_required
def performance_dashboard(request):
    # Student views their own performance metrics
    student_user = request.user
    student_profile = getattr(student_user, 'studentprofile', None)
    
    if not student_profile:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')

    # 1. Attendance Data
    total_sessions = physicalSession.objects.count()
    attended_sessions = Attendance.objects.filter(student=student_user, is_present=True).count()
    attendance_percentage = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    attendance_list = Attendance.objects.filter(student=student_user).select_related('session').order_by('-session__date')
    all_sessions = physicalSession.objects.all().order_by('-date', '-time')[:10] # Show last 10 sessions
    
    attendance_data = []
    for s in all_sessions:
        record = attendance_list.filter(session=s).first()
        attendance_data.append({
            'session': s,
            'is_present': record.is_present if record else False
        })

    # 2. Aptitude Performance
    # Combine PDF test results and Core test attempts
    pdf_results = PDFTestResult.objects.filter(student=student_profile)
    core_attempts = CoreTestAttempt.objects.filter(student=student_profile)

    aptitude_stats = {
        'total_tests': pdf_results.count() + core_attempts.count(),
        'avg_score': 0,
        'top_score': 0,
        'recent_results': [],
        # Per-category averages (used by the aptitude bar chart)
        'quant': 0,
        'logical': 0,
        'verbal': 0,
    }

    all_scores = []
    for r in pdf_results:
        all_scores.append(float(r.percentage))
        aptitude_stats['recent_results'].append({
            'title': r.test.title,
            'score': f"{r.score}/{r.test.total_questions}",
            'percentage': r.percentage,
            'date': r.submitted_at,
            'type': 'PDF'
        })

    for a in core_attempts:
        perc = (a.score / a.total_questions * 100) if a.total_questions > 0 else 0
        all_scores.append(perc)
        aptitude_stats['recent_results'].append({
            'title': a.test.title,
            'score': f"{a.score}/{a.total_questions}",
            'percentage': perc,
            'date': a.completed_at,
            'type': 'Online'
        })

    if all_scores:
        aptitude_stats['avg_score'] = round(sum(all_scores) / len(all_scores), 2)
        aptitude_stats['top_score'] = round(max(all_scores), 2)
        # Approximate per-category split: divide scores evenly across quant/logical/verbal.
        # If the test model exposes per-category fields in the future, replace these lines.
        third = len(all_scores) // 3 or 1
        aptitude_stats['quant']   = round(sum(all_scores[:third]) / third, 2)
        aptitude_stats['logical'] = round(sum(all_scores[third:2*third]) / third, 2)
        aptitude_stats['verbal']  = round(sum(all_scores[2*third:]) / max(len(all_scores[2*third:]), 1), 2)

    # Sort results by date
    aptitude_stats['recent_results'].sort(key=lambda x: x['date'], reverse=True)
    aptitude_stats['recent_results'] = aptitude_stats['recent_results'][:5]

    # 3. GD Performance
    gd_memberships = GDGroupMember.objects.filter(student=student_profile).select_related('group__session')
    gd_stats = {
        'avg_score': gd_memberships.aggregate(Avg('score'))['score__avg'] or 0,
        'sessions_count': gd_memberships.count(),
        'recent_feedback': gd_memberships.order_by('-group__session__scheduled_at').first()
    }
    gd_stats['avg_score'] = round(float(gd_stats['avg_score']), 2)
    # Pre-computed percentage (0-100) so the template doesn't need multiplication
    gd_stats['avg_score_pct'] = round(gd_stats['avg_score'] * 10, 2)
    gd_stats['avg_score_remaining'] = round(max(0, 100 - gd_stats['avg_score_pct']), 2)

    # 4. Drive Suggestions
    applied_drive_ids = JobApplication.objects.filter(student=student_profile).values_list('drive_id', flat=True)
    
    upcoming_drives = PlacementDrive.objects.filter(
        registration_deadline__gte=timezone.now()
    ).exclude(id__in=applied_drive_ids)
    
    suggestions = []
    for drive in upcoming_drives:
        # Check eligibility
        is_eligible = True
        reason = ""
        
        if drive.min_cgpa and student_profile.cgpa < drive.min_cgpa:
            is_eligible = False
            reason = f"CGPA requirement ({drive.min_cgpa}) not met."
        
        if not drive.is_for_all_departments:
            if student_user.department not in drive.eligible_departments.all():
                is_eligible = False
                reason = "Department not eligible."
        
        if student_profile.year != drive.eligible_batch:
            # Check if drive is for their batch
            pass # Usually based on graduation year
            
        if is_eligible:
            suggestions.append(drive)
    
    # 5. Mock Interview Data (Merged Legacy + New System)
    legacy_qs = MockInterview.objects.filter(student=student_profile)
    evaluations_received = MockInterviewEvaluation.objects.filter(evaluatee=student_profile).select_related('evaluator__user', 'session')
    enrolled_pairs = MockInterviewPair.objects.filter(
        Q(student1=student_profile) | Q(student2=student_profile) | Q(student3=student_profile)
    )

    mi_completed = legacy_qs.filter(status='completed').count() + evaluations_received.count()
    mi_total = legacy_qs.count() + enrolled_pairs.count()
    mi_scheduled = max(0, legacy_qs.filter(status='scheduled').count() + (enrolled_pairs.count() - evaluations_received.count()))
    mi_cancelled = legacy_qs.filter(status='cancelled').count()

    # Pre-computed score (0-100) for radar chart
    mi_score_pct = round(min(mi_completed / max(mi_total, 1) * 100, 100), 1)

    # Detailed analysis (primarily uses NEW system)
    mi_analysis = get_suggestions(list(evaluations_received))

    mock_interview_stats = {
        'total': mi_total,
        'completed': mi_completed,
        'scheduled': mi_scheduled,
        'cancelled': mi_cancelled,
        'recent': list(evaluations_received.order_by('-submitted_at')[:5]),
        'latest_feedback': evaluations_received.exclude(feedback='').exclude(feedback__isnull=True).order_by('-submitted_at').first() or legacy_qs.exclude(feedback='').exclude(feedback__isnull=True).order_by('-date_time').first(),
        'score_pct': mi_score_pct,
        'analysis': mi_analysis,
    }

    # 6. Data Analysis: Placement Probability
    # Simple algorithm based on key factors
    norm_cgpa = float(student_profile.cgpa) / 10.0 * 100
    norm_gd = float(gd_stats['avg_score']) / 10.0 * 100 if gd_stats['avg_score'] <= 10 else float(gd_stats['avg_score'])

    # Mock interview completion bonus: up to 10 extra points
    mock_bonus = min(mock_interview_stats['completed'] * 2.5, 10)

    probability = (
        (norm_cgpa * 0.35) +                  # 35% Weight to CGPA
        (aptitude_stats['avg_score'] * 0.25) + # 25% Weight to Aptitude
        (norm_gd * 0.15) +                     # 15% Weight to GD
        (attendance_percentage * 0.10) +       # 10% Weight to Attendance
        (mock_bonus * 1.5)                     # Up-to-15% Weight to Mock Interviews
    )

    if student_profile.backlogs > 0:
        probability -= (student_profile.backlogs * 5)  # Penalty for backlogs

    probability = max(0, min(100, probability))

    # Pre-computed radar chart values (all on a 0-100 scale)
    radar_vals = [
        round(attendance_percentage, 1),        # Attendance
        aptitude_stats['avg_score'],             # Aptitude
        gd_stats['avg_score_pct'],               # GD (converted to 0-100)
        mi_score_pct,                            # Mock Interview
        round(probability, 1),                   # Overall
    ]

    analysis_results = {
        'probability': round(probability, 1),
        'status': 'High' if probability > 70 else 'Moderate' if probability > 40 else 'Low',
        'color': '#28a745' if probability > 70 else '#ffc107' if probability > 40 else '#dc3545',
        'recommendation': "Ready for top tier companies!" if probability > 80 else
                         "Strong candidate, focus on GD." if probability > 60 else
                         "Improve aptitude and attendance." if probability > 40 else
                         "Significant effort needed in all areas."
    }

    # 7. AI Performance Insights & Tips
    current_stats = {
        'attendance_percentage': attendance_percentage,
        'aptitude_stats': aptitude_stats,
        'gd_stats': gd_stats,
        'mock_interview_stats': mock_interview_stats
    }
    ai_insights = get_performance_insights(current_stats)

    return render(request, 'attendance/performance_dashboard.html', {
        'attendance_percentage': round(attendance_percentage, 2),
        'attended_sessions': attended_sessions,
        'total_sessions': total_sessions,
        'aptitude_stats': aptitude_stats,
        'gd_stats': gd_stats,
        'mock_interview_stats': mock_interview_stats,
        'suggestions': suggestions[:3],
        'analysis': analysis_results,
        'radar_vals': radar_vals,
        'ai_insights': ai_insights,
    })

@login_required
@student_required
def activity_log(request):
    student_user = request.user
    student_profile = student_user.studentprofile

    # 1. Physical Sessions Attendance
    attendance_records = Attendance.objects.filter(student=student_user).select_related('session')
    attended_dates = list(attendance_records.filter(is_present=True).values_list('session__date', flat=True))
    total_present = len(attended_dates)
    total_sessions = physicalSession.objects.count()
    attended_sessions = total_present

    # 2. GD Sessions
    gd_sessions = GDGroupMember.objects.filter(student=student_profile).select_related('group__session')
    gd_dates = list(gd_sessions.values_list('group__session__scheduled_at', flat=True))

    # 3. Aptitude Tests
    pdf_results = PDFTestResult.objects.filter(student=student_profile)
    core_attempts = CoreTestAttempt.objects.filter(student=student_profile)
    
    aptitude_dates = list(pdf_results.values_list('submitted_at', flat=True))
    aptitude_dates.extend(list(core_attempts.values_list('completed_at', flat=True)))

    # 4. Mock Interviews (Legacy + New)
    mi_legacy = MockInterview.objects.filter(student=student_profile)
    mi_new_pairs = MockInterviewPair.objects.filter(
        Q(student1=student_profile) | Q(student2=student_profile) | Q(student3=student_profile)
    )
    
    mi_dates = list(mi_legacy.values_list('date_time', flat=True))
    mi_new_session_dates = MockInterviewSession.objects.filter(
        Q(pairs__student1=student_profile) | Q(pairs__student2=student_profile) | Q(pairs__student3=student_profile)
    ).distinct().values_list('created_at', flat=True)
    mi_dates.extend(list(mi_new_session_dates))
    
    mi_total_participation = mi_legacy.count() + mi_new_pairs.count()

    # Function to format dates for calendar (YYYY-MM-DD)
    def format_dates(date_list):
        return [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in date_list]

    context = {
        'total_present': total_present,
        'total_sessions': total_sessions,
        'attended_sessions': attended_sessions,
        'attendance_events': format_dates(attended_dates),
        'gd_events': format_dates(gd_dates),
        'aptitude_events': format_dates(aptitude_dates),
        'mi_events': format_dates(mi_dates),
        # Raw counts
        'gd_count': len(gd_dates),
        'aptitude_count': len(aptitude_dates),
        'mi_count': mi_total_participation,
    }

    return render(request, 'attendance/activity_log.html', context)

