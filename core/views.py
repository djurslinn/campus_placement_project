from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Q, Avg, F, FloatField, Case, When, Prefetch, ExpressionWrapper, Max
from django.db.models.functions import Cast, NullIf
from django.core.cache import cache
import csv

from accounts.models import User, StudentProfile, Course
from .models import PlacementDrive, JobApplication, Announcement, Notification, Test, Question, TestAttempt, MockInterview
from attendance.models import Attendance
from group_discussion.models import GDGroupMember
from .forms import PlacementDriveForm, AnnouncementForm, CourseForm
from mock_interviews.models import MockInterviewSession, MockInterviewEvaluation


def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('index')
        if request.user.role == 'student' or request.user.role == 'admin' or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Students only.')
        return redirect('index')
    return wrapper

def coordinator_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('index')
        if request.user.role == 'coordinator' or request.user.role == 'admin' or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Coordinators only.')
        return redirect('index')
    return wrapper

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or (request.user.role != 'admin' and not request.user.is_superuser):
            messages.error(request, 'Access denied. Administrators only.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

def index(request):
    if request.user.is_authenticated:
        if request.user.role == 'student':
            return redirect('student_dashboard')
        elif request.user.role == 'coordinator':
            return redirect('coordinator_dashboard')
        elif request.user.role == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')
    
    # Cache landing page stats for 10 minutes
    cache_key = 'landing_page_stats'
    cached_context = cache.get(cache_key)
    
    if cached_context:
        context = cached_context
    else:
        # Fetch real-time metrics for the landing page
        total_students = StudentProfile.objects.count()
        placed_count = StudentProfile.objects.filter(placement_status='placed').count()
        companies_count = PlacementDrive.objects.values('company_name').distinct().count()
        
        success_rate = round((placed_count / total_students * 100), 1) if total_students > 0 else 0
        avg_package = PlacementDrive.objects.aggregate(avg=Avg('package'))['avg'] or 0
        
        # Fetch unique companies and their latest drive details (role, package)
        latest_drive_ids = PlacementDrive.objects.values('company_name').annotate(latest_id=Max('id')).values_list('latest_id', flat=True)
        featured_companies = PlacementDrive.objects.filter(id__in=latest_drive_ids).order_by('-created_at')[:8]
        
        context = {
            'stat_placed': placed_count,
            'stat_companies': companies_count,
            'stat_success': success_rate,
            'stat_avg_package': round(avg_package, 1),
            'featured_companies': featured_companies
        }
        cache.set(cache_key, context, 600)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'coordinator':
                return redirect('coordinator_dashboard')
            elif user.role == 'admin' or user.is_superuser:
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'index.html', context)

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/')

@login_required
@coordinator_required
def coordinator_dashboard(request):
    from django.utils import timezone
    total_students = StudentProfile.objects.count()
    placed_students = StudentProfile.objects.filter(placement_status='placed').count()
    
    now = timezone.now()
    active_drives = PlacementDrive.objects.filter(registration_deadline__gt=now).count()
    expired_drives = PlacementDrive.objects.filter(registration_deadline__lte=now).count()
    
    context = {
        'total_students': total_students,
        'placed_students': placed_students,
        'active_drives': active_drives,
        'expired_drives': expired_drives,
    }
    return render(request, 'coordinator_dashboard.html', context)

@login_required
@admin_required
def admin_dashboard(request):
    """
    Main Admin Dashboard for Superusers
    """
    from django.utils import timezone
    import sys
    import platform
    from django.db import connection
    
    total_users = User.objects.count()
    students_count = User.objects.filter(role='student').count()
    coordinators_count = User.objects.filter(role='coordinator').count()
    admins_count = User.objects.filter(role='admin').count()
    
    total_drives = PlacementDrive.objects.count()
    total_applications = JobApplication.objects.count()
    total_placed = StudentProfile.objects.filter(placement_status='placed').count()
    placement_rate = (total_placed / students_count * 100) if students_count > 0 else 0

    all_courses = Course.objects.all().order_by('name')
    all_drives = PlacementDrive.objects.annotate(
        applications_count=Count('applications', distinct=True),
        placed_count=Count('applications', filter=Q(applications__status='placed'), distinct=True)
    ).order_by('-created_at')

    # Department-wise stats for dashboard
    dept_stats = []
    for dept in all_courses:
        dept_stats.append({
            'name': dept.name,
            'total': User.objects.filter(role='student', department=dept).count(),
            'placed': StudentProfile.objects.filter(user__department=dept, placement_status='placed').count()
        })
    
    import django
    sys_info = {
        'python_version': sys.version.split(' ')[0],
        'django_version': django.get_version(),
        'os': f"{platform.system()} {platform.release()}",
        'db_engine': connection.vendor,
    }
    
    # Recent activity
    recent_users = User.objects.all().order_by('-date_joined')[:6]
    
    context = {
        'total_users': total_users,
        'students_count': students_count,
        'coordinators_count': coordinators_count,
        'admins_count': admins_count,
        'total_drives': total_drives,
        'total_applications': total_applications,
        'total_placed': total_placed,
        'placement_rate': round(placement_rate, 1),
        'sys_info': sys_info,
        'recent_users': recent_users,
        'all_courses': all_courses,
        'all_drives': all_drives,
        'dept_stats': dept_stats,
        'user': request.user
    }
    return render(request, 'admin/admin_dashboard.html', context)

@login_required
@admin_required
def admin_manage_courses(request):
    if request.method == 'POST':
        from .forms import CourseForm
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course/Department added successfully.')
            return redirect('admin_manage_courses')
    else:
        from .forms import CourseForm
        form = CourseForm()
    
    courses = Course.objects.all().order_by('category', 'name')
    return render(request, 'admin/manage_courses.html', {
        'courses': courses,
        'form': form
    })

@login_required
@admin_required
def admin_user_management(request):
    """
    Handle user roles, activation, and basic administration
    """
    role_filter = request.GET.get('role', '')
    q = request.GET.get('q', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    if role_filter:
        users = users.filter(role=role_filter)
    if q:
        users = users.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
        
    context = {
        'users': users,
        'role_filter': role_filter,
        'query': q,
    }
    return render(request, 'admin/user_management.html', context)

@login_required
@admin_required
def admin_toggle_user_status(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        if target_user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        else:
            target_user.is_active = not target_user.is_active
            target_user.save()
            status = "activated" if target_user.is_active else "deactivated"
            messages.success(request, f"User {target_user.email} has been {status}.")
            
    return redirect('admin_user_management')

@login_required
@admin_required
def security_overview(request):
    """
    Overview of system security and access control
    """
    inactive_users = User.objects.filter(is_active=False).count()
    unapproved_students = StudentProfile.objects.filter(is_approved=False).count()
    admins = User.objects.filter(Q(role='admin') | Q(is_superuser=True)).distinct()
    
    context = {
        'inactive_users': inactive_users,
        'unapproved_students': unapproved_students,
        'admins': admins,
    }
    return render(request, 'admin/security_overview.html', context)

@login_required
@coordinator_required
def manage_students(request):
    q = request.GET.get('q', '')
    dept_id = request.GET.get('department', '')
    batch = request.GET.get('batch', '')
    year = request.GET.get('year', '')
    sort = request.GET.get('sort', 'name')

    # Create a unique cache key based on query parameters
    cache_key = f'manage_students_{q}_{dept_id}_{batch}_{year}_{sort}'
    context = cache.get(cache_key)
    if context:
        return render(request, 'core/manage_students.html', context)

    # Base queryset
    applications_prefetch = Prefetch(
        'studentprofile__applications',
        queryset=JobApplication.objects.select_related('drive')
    )
    students = User.objects.filter(role='student').select_related('studentprofile', 'department').prefetch_related(applications_prefetch)

    # Annotations for sorting and display
    # We use distinct=True to avoid multiplication of counts due to multiple joins
    students = students.annotate(
        attendance_count=Count('session_attendances', filter=Q(session_attendances__is_present=True), distinct=True),
        total_sessions_count=Count('session_attendances', distinct=True),
        gd_score=Avg('studentprofile__gdgroupmember__score'),
        aptitude_score=Avg(Cast(F('studentprofile__test_attempts__score'), FloatField()) * 100.0 / NullIf(Cast(F('studentprofile__test_attempts__total_questions'), FloatField()), 0.0)),
        applied_count=Count('studentprofile__applications', distinct=True)
    )

    # Search logic
    if q:
        students = students.filter(
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q) | 
            Q(studentprofile__roll_no__icontains=q) | 
            Q(department__name__icontains=q) |
            Q(email__icontains=q)
        )

    # Filter logic
    if dept_id:
        students = students.filter(department_id=dept_id)
    if batch:
        students = students.filter(studentprofile__batch=batch)
    if year:
        students = students.filter(studentprofile__year=year)

    # Sort logic
    if sort == 'attendance':
        students = students.order_by('-attendance_count', 'first_name')
    elif sort == 'gd':
        students = students.order_by(F('gd_score').desc(nulls_last=True), 'first_name')
    elif sort == 'aptitude':
        students = students.order_by(F('aptitude_score').desc(nulls_last=True), 'first_name')
    elif sort == 'applied':
        students = students.order_by('-applied_count', 'first_name')
    else:
        students = students.order_by('first_name')

    # Get data for filters
    departments = Course.objects.all().order_by('name')
    batches = StudentProfile.objects.values_list('batch', flat=True).distinct().exclude(batch__isnull=True).order_by('-batch')
    drives = PlacementDrive.objects.all().order_by('-created_at')

    context = {
        'students': students,
        'departments': departments,
        'batches': batches,
        'drives': drives,
        'query': q,
        'selected_dept': dept_id,
        'selected_batch': batch,
        'selected_year': year,
        'selected_sort': sort,
    }
    # Cache for 2 minutes
    cache.set(cache_key, context, 120)
    return render(request, 'core/manage_students.html', context)

@login_required
@coordinator_required
def mark_student_placed(request, student_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=student_id, role='student')
        drive_id = request.POST.get('drive_id')
        status = request.POST.get('status', 'placed')
        
        if not hasattr(user, 'studentprofile'):
             messages.error(request, 'Student profile does not exist.')
             return redirect('manage_students')
             
        profile = user.studentprofile
        
        if status == 'placed' and drive_id:
            drive = get_object_or_404(PlacementDrive, id=drive_id)
            # Update or create application
            app, created = JobApplication.objects.get_or_create(
                student=profile,
                drive=drive,
                defaults={'status': 'placed'}
            )
            if not created:
                app.status = 'placed'
                app.save()
            
            profile.placement_status = 'placed'
            profile.save()
            messages.success(request, f'Student {user.get_full_name()} marked as placed in {drive.company_name}.')
        else:
            profile.placement_status = 'not_placed'
            profile.save()
            # Optionally reset application status if needed, but usually we just keep it
            messages.success(request, f'Student {user.get_full_name()} marked as not placed.')
            
    return redirect('manage_students')

@login_required
@coordinator_required
def approve_student(request, student_id):
    # Here student_id refers to User.id
    user = get_object_or_404(User, id=student_id, role='student')
    
    # Try to get or create profile
    profile, created = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'roll_no': f"TEMP_{user.id}",
            'year': 1,
            'phone': '0000000000',
            'is_approved': True
        }
    )
    
    if not created:
        profile.is_approved = True
        profile.save()
        
    messages.success(request, f'Student {user.get_full_name()} approved.')
    return redirect('manage_students')

@login_required
@coordinator_required
def toggle_student_status(request, student_id):
    # Here student_id refers to User.id
    user = get_object_or_404(User, id=student_id, role='student')
    
    # Try to get or create profile
    profile, created = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'roll_no': f"TEMP_{user.id}", # Placeholder if not exists
            'year': 1,
            'phone': '0000000000',
            'is_active': True 
        }
    )
    
    if not created:
        profile.is_active = not profile.is_active
        profile.save()
        status = "activated" if profile.is_active else "deactivated"
    else:
        status = "activated and profile created"
        
    messages.success(request, f'Student {user.get_full_name()} {status}.')
    return redirect('manage_students')

@login_required
@coordinator_required
def manage_drives(request):
    drives = PlacementDrive.objects.all().order_by('-created_at')
    return render(request, 'core/manage_drives.html', {'drives': drives})

@login_required
@coordinator_required
def create_drive(request):
    if request.method == 'POST':
        form = PlacementDriveForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Placement drive created successfully.')
            return redirect('manage_drives')
    else:
        form = PlacementDriveForm()
    return render(request, 'core/drive_form.html', {'form': form, 'title': 'Create Placement Drive'})

@login_required
@coordinator_required
def edit_drive(request, drive_id):
    drive = get_object_or_404(PlacementDrive, id=drive_id)
    if request.method == 'POST':
        form = PlacementDriveForm(request.POST, instance=drive)
        if form.is_valid():
            form.save()
            messages.success(request, 'Placement drive updated successfully.')
            return redirect('manage_drives')
    else:
        form = PlacementDriveForm(instance=drive)
    return render(request, 'core/drive_form.html', {'form': form, 'title': 'Edit Placement Drive'})

@login_required
@coordinator_required
def delete_drive(request, drive_id):
    drive = get_object_or_404(PlacementDrive, id=drive_id)
    drive.delete()
    messages.success(request, 'Placement drive deleted.')
    return redirect('manage_drives')

@login_required
@coordinator_required
def view_drive_students(request, drive_id):
    drive = get_object_or_404(PlacementDrive, id=drive_id)
    
    # 1. Get IDs of students who already applied
    applications = JobApplication.objects.filter(drive=drive).select_related('student', 'student__user', 'student__user__department')
    applicant_ids = set(applications.values_list('student_id', flat=True))
    application_map = {app.student_id: app for app in applications}
    
    # 2. Get students who meet the auto-eligibility criteria
    eligible_qs = StudentProfile.objects.all()
    
    if drive.eligible_batch and drive.eligible_batch != 0:
        eligible_qs = eligible_qs.filter(batch=drive.eligible_batch)
        
    if drive.eligible_year and drive.eligible_year != 0:
        eligible_qs = eligible_qs.filter(year=drive.eligible_year)
    
    if drive.min_cgpa is not None:
        eligible_qs = eligible_qs.filter(cgpa__gte=drive.min_cgpa)
    
    if not drive.is_for_all_departments and drive.eligible_departments.exists():
        eligible_qs = eligible_qs.filter(user__department__in=drive.eligible_departments.all())
    
    eligible_ids = set(eligible_qs.values_list('id', flat=True))
    
    # 3. Combine both sets (Applicants + Eligible candidates)
    all_student_ids = applicant_ids.union(eligible_ids)
    
    # 4. Fetch all relevant profiles in a single query
    relevant_students = StudentProfile.objects.filter(id__in=all_student_ids).select_related('user', 'user__department').order_by('user__first_name', 'roll_no')
    
    # 5. Prepare data for template
    display_students = []
    for student in relevant_students:
        app = application_map.get(student.id)
        student.application = app
        student.has_applied = (app is not None)
        student.is_auto_eligible = (student.id in eligible_ids)
        display_students.append(student)
        
    total_eligible = len(eligible_ids)
    total_applied = len(applicant_ids)
    participation_percentage = (total_applied / total_eligible * 100) if total_eligible > 0 else 0
    
    return render(request, 'core/drive_students.html', {
        'drive': drive,
        'eligible_students': display_students,
        'total_eligible': total_eligible,
        'total_applied': total_applied,
        'participation_percentage': round(participation_percentage, 1),
    })

@login_required
@coordinator_required
def mark_students_placed_bulk(request, drive_id):
    if request.method == 'POST':
        student_ids = request.POST.getlist('selected_students')
        drive = get_object_or_404(PlacementDrive, id=drive_id)
        
        if not student_ids:
            messages.warning(request, "No students selected. Please check at least one student.")
            return redirect('view_drive_students', drive_id=drive_id)
        
        from django.utils import timezone
        now = timezone.now()
        
        # Mark selected students as placed
        count = 0
        for student_id in student_ids:
            # Use get_or_create to handle students who hadn't officially applied yet
            application, created = JobApplication.objects.get_or_create(
                drive=drive,
                student_id=student_id,
                defaults={
                    'status': 'placed',
                    'placed_at': now
                }
            )
            
            if not created:
                # Update existing application
                application.status = 'placed'
                application.placed_at = now
                application.save(update_fields=['status', 'placed_at'])
            
            # Ensure student profile is also marked as placed
            StudentProfile.objects.filter(id=student_id).update(placement_status='placed')
            count += 1
        
        messages.success(request, f"Successfully marked {count} student(s) as placed in {drive.company_name} (Placement date: {now.strftime('%d %b %Y')}).")
    
    return redirect('view_drive_students', drive_id=drive_id)

@login_required
@student_required
def select_ready_to_work(request, application_id):
    """Student selects their final 'Ready to Work' placement.
    
    Rules (all enforced at backend):
    1. Application must be in 'placed' status.
    2. Category hierarchy: A(4) > B(3) > C(2) > D(1).
       - Cannot select a lower-category company if already placed in higher on an earlier/same date.
    3. Only one active is_accepted at a time.
    """
    from django.utils import timezone
    
    application = get_object_or_404(
        JobApplication,
        id=application_id,
        student__user=request.user,
        status='placed'
    )
    student = request.user.studentprofile
    new_rank = application.get_category_rank()
    new_placed_at = application.placed_at or timezone.now()
    
    # --- Backend Validation ---
    # Get all OTHER placed applications for this student
    other_placed = JobApplication.objects.filter(
        student=student,
        status='placed'
    ).exclude(id=application.id).select_related('drive')
    
    for pa in other_placed:
        pa_rank = pa.get_category_rank()
        pa_placed_at = pa.placed_at or timezone.now()
        
        # Block: trying to select a LOWER category than a placement that happened earlier or same time
        if pa_rank > new_rank and pa_placed_at <= new_placed_at:
            messages.error(
                request,
                f"Cannot select {application.drive.company_name} (Category {application.drive.category}) "
                f"as Ready to Work. You were already placed in "
                f"{pa.drive.company_name} (Category {pa.drive.category}) "
                f"on {pa_placed_at.strftime('%d %b %Y')}, which is a higher category. "
                f"You may only move to an equal or higher category company."
            )
            return redirect('student_profile')
    
    # All validations passed — clear old selection and set new one
    JobApplication.objects.filter(student=student, is_accepted=True).update(is_accepted=False)
    application.is_accepted = True
    application.save(update_fields=['is_accepted'])
    
    messages.success(
        request,
        f"Ready to Work: {application.drive.company_name} (Category {application.drive.category}) selected as your final placement."
    )
    return redirect('student_profile')

@login_required
@coordinator_required
def reports(request):
    total_students = StudentProfile.objects.count()
    placed_students = StudentProfile.objects.filter(placement_status='placed').count()
    placement_percentage = (placed_students / total_students * 100) if total_students > 0 else 0
    
    # Company-wise
    company_wise_qs = PlacementDrive.objects.annotate(
        placed_count=Count('applications', filter=Q(applications__status='placed')),
        applied_count=Count('applications'),
    ).order_by('-placed_count')

    # Per-drive: compute eligible count for accurate percentages
    company_wise = []
    for drive in company_wise_qs:
        eligible_qs = StudentProfile.objects.all()
        if drive.eligible_batch and int(drive.eligible_batch) != 0:
            eligible_qs = eligible_qs.filter(batch=drive.eligible_batch)
        if drive.eligible_year and int(drive.eligible_year) != 0:
            eligible_qs = eligible_qs.filter(year=drive.eligible_year)
        if drive.min_cgpa:
            eligible_qs = eligible_qs.filter(cgpa__gte=drive.min_cgpa)
        if not drive.is_for_all_departments and drive.eligible_departments.exists():
            eligible_qs = eligible_qs.filter(user__department__in=drive.eligible_departments.all())
        drive.eligible_count = eligible_qs.count()
        drive.applied_pct  = round((drive.applied_count / drive.eligible_count  * 100), 1) if drive.eligible_count > 0 else 0
        drive.placed_pct   = round((drive.placed_count  / drive.eligible_count  * 100), 1) if drive.eligible_count > 0 else 0
        drive.convert_pct  = round((drive.placed_count  / drive.applied_count   * 100), 1) if drive.applied_count > 0 else 0
        company_wise.append(drive)
    
    # Attendance Analysis
    # Get average attendance percentage across all students who have at least one attendance record
    student_attendance = User.objects.filter(role='student').annotate(
        total_sessions=Count('session_attendances'),
        present_sessions=Count('session_attendances', filter=Q(session_attendances__is_present=True))
    )
    
    overall_attendance_pct = 0
    if student_attendance.exists():
        total_presents = 0
        total_records = 0
        for s in student_attendance:
            total_presents += s.present_sessions
            total_records += s.total_sessions
        if total_records > 0:
            overall_attendance_pct = (total_presents / total_records) * 100

    # Aptitude Analysis
    aptitude_stats = TestAttempt.objects.aggregate(
        avg_score_pct=Avg(Cast(F('score'), FloatField()) * 100.0 / NullIf(Cast(F('total_questions'), FloatField()), 0.0))
    )
    avg_aptitude = aptitude_stats['avg_score_pct'] or 0
    
    # GD Analysis
    gd_stats = GDGroupMember.objects.aggregate(avg_score=Avg('score'))
    avg_gd = gd_stats['avg_score'] or 0

    # Department-wise Results
    dept_results = Course.objects.annotate(
        total_count=Count('user', filter=Q(user__role='student')),
        placed_count=Count('user__studentprofile', filter=Q(user__studentprofile__placement_status='placed')),
        avg_cgpa=Avg('user__studentprofile__cgpa'),
        # Using subqueries or separate processing might be cleaner for complex averages, 
        # but let's try direct annotation first
    )
    
    # For more accurate department averages (Aptitude and GD), we might need manual calculation 
    # as double joins in annotate can cause incorrect counts/sums
    for dept in dept_results:
        dept.placement_pct = (dept.placed_count / dept.total_count * 100) if dept.total_count > 0 else 0
        
        # Aptitude by Dept
        dept_aptitude = TestAttempt.objects.filter(student__user__department=dept).aggregate(
            avg=Avg(Cast(F('score'), FloatField()) * 100.0 / NullIf(Cast(F('total_questions'), FloatField()), 0.0))
        )
        dept.avg_aptitude = dept_aptitude['avg'] or 0
        
        # GD by Dept
        dept_gd = GDGroupMember.objects.filter(student__user__department=dept).aggregate(avg=Avg('score'))
        dept.avg_gd = dept_gd['avg'] or 0
        
        # Attendance by Dept
        dept_att = Attendance.objects.filter(student__department=dept).aggregate(
            total=Count('id'),
            presents=Count('id', filter=Q(is_present=True))
        )
        dept.avg_attendance = (dept_att['presents'] / dept_att['total'] * 100) if dept_att['total'] and dept_att['total'] > 0 else 0

        # Applications for drives eligible to this dept
        dept_applied = JobApplication.objects.filter(
            student__user__department=dept
        ).count()
        dept_eligible_students = dept.total_count
        dept.application_ratio = round((dept_applied / dept_eligible_students * 100), 1) if dept_eligible_students > 0 else 0
        dept.applied_count = dept_applied

        # MI Average by Dept
        dept_mi = MockInterviewEvaluation.objects.filter(
            evaluatee__user__department=dept
        ).aggregate(
            avg=Avg(
                ExpressionWrapper(
                    (F('communication') + F('confidence') + F('technical') + F('body_language') + F('problem_solving')) / 5.0,
                    output_field=FloatField()
                )
            )
        )
        dept.avg_mi = round(float(dept_mi['avg'] or 0), 2)

    # Placement Probability / Trend — includes Mock Interview avg
    # Readiness = (Avg Aptitude * 0.35) + (Avg Attendance * 0.25) + (Avg GD score * 3) + (Avg MI score * 2.5)
    avg_mi_overall = float(avg_gd)  # fallback
    mi_overall_stats = MockInterviewEvaluation.objects.aggregate(
        avg_score=Avg(
            ExpressionWrapper(
                (F('communication') + F('confidence') + F('technical') + F('body_language') + F('problem_solving')) / 5.0,
                output_field=FloatField()
            )
        )
    )
    avg_mi_overall = float(mi_overall_stats['avg_score'] or 0)
    readiness_score = (
        float(avg_aptitude) * 0.35 +
        float(overall_attendance_pct) * 0.25 +
        float(avg_gd) * 3.0 +
        avg_mi_overall * 2.5
    )
    
    # 6. Student Leaderboard (Top 10)
    top_students = User.objects.filter(role='student').select_related('studentprofile', 'department').annotate(
        att_pct=Cast(Count('session_attendances', filter=Q(session_attendances__is_present=True)), FloatField()) * 100.0 / NullIf(Cast(Count('session_attendances'), FloatField()), 0.0),
        apt_pct=Avg(Cast(F('studentprofile__test_attempts__score'), FloatField()) * 100.0 / NullIf(Cast(F('studentprofile__test_attempts__total_questions'), FloatField()), 0.0)),
        gd_val=Avg('studentprofile__gdgroupmember__score'),
        mi_val=Avg(
            ExpressionWrapper(
                (F('studentprofile__evaluations_received__communication') +
                 F('studentprofile__evaluations_received__confidence') +
                 F('studentprofile__evaluations_received__technical') +
                 F('studentprofile__evaluations_received__body_language') +
                 F('studentprofile__evaluations_received__problem_solving')) / 5.0,
                output_field=FloatField()
            )
        )
    )

    # Compute weighted readiness rank for each student
    top_students_list = []
    for s in top_students:
        try:
            s_cgpa = float(s.studentprofile.cgpa)
        except Exception:
            s_cgpa = 0
        s_att  = float(s.att_pct or 0)
        s_apt  = float(s.apt_pct or 0)
        s_gd   = float(s.gd_val  or 0)
        s_mi   = float(s.mi_val  or 0)

        # Weighted readiness: CGPA(10) + Attendance(0.2) + Aptitude(0.3) + GD(5) + MI(3)
        s.readiness_rank = (s_cgpa * 10) + (s_att * 0.2) + (s_apt * 0.3) + (s_gd * 5) + (s_mi * 3)
        top_students_list.append(s)

    top_students_list = sorted(top_students_list, key=lambda x: x.readiness_rank, reverse=True)[:10]

    # 7. Distribution for Charts
    # Aptitude Score Ranges
    aptitude_ranges = {
        '90-100': TestAttempt.objects.filter(score__gte=F('total_questions')*0.9).count(),
        '75-89': TestAttempt.objects.filter(score__gte=F('total_questions')*0.75, score__lt=F('total_questions')*0.9).count(),
        '50-74': TestAttempt.objects.filter(score__gte=F('total_questions')*0.5, score__lt=F('total_questions')*0.75).count(),
        'Below 50': TestAttempt.objects.filter(score__lt=F('total_questions')*0.5).count(),
    }

    # GD Score Ranges
    gd_ranges = {
        'Excellent (9+)': GDGroupMember.objects.filter(score__gte=9).count(),
        'Good (7-8)': GDGroupMember.objects.filter(score__gte=7, score__lt=9).count(),
        'Average (5-6)': GDGroupMember.objects.filter(score__gte=5, score__lt=7).count(),
        'Poor (<5)': GDGroupMember.objects.filter(score__lt=5).count(),
    }

    # Mock Interview Analysis
    mi_sessions_count = MockInterviewSession.objects.count()
    mi_evaluations_count = MockInterviewEvaluation.objects.count()
    
    mi_stats = MockInterviewEvaluation.objects.aggregate(
        avg_comm=Avg('communication'),
        avg_conf=Avg('confidence'),
        avg_tech=Avg('technical'),
        avg_body=Avg('body_language'),
        avg_ps=Avg('problem_solving')
    )
    
    mi_overall_avg = 0
    if mi_evaluations_count > 0:
        total_avgs = [
            float(mi_stats['avg_comm'] or 0),
            float(mi_stats['avg_conf'] or 0),
            float(mi_stats['avg_tech'] or 0),
            float(mi_stats['avg_body'] or 0),
            float(mi_stats['avg_ps'] or 0)
        ]
        mi_overall_avg = sum(total_avgs) / 5.0
        
    # Top Mock Performers
    top_mi_students = MockInterviewEvaluation.objects.values(
        'evaluatee__user__first_name', 'evaluatee__user__last_name', 'evaluatee__roll_no'
    ).annotate(
        avg_score=Avg(
            ExpressionWrapper(
                (F('communication') + F('confidence') + F('technical') + F('body_language') + F('problem_solving')) / 5.0,
                output_field=FloatField()
            )
        )
    ).order_by('-avg_score')[:5]

    # Prepare serializable list for JS
    dept_results_list = []
    for dept in dept_results:
        dept_results_list.append({
            'name': dept.name,
            'count': dept.total_count,
            'placement': round(float(dept.placement_pct), 1),
            'cgpa': round(float(dept.avg_cgpa or 0), 2),
            'attendance': round(float(dept.avg_attendance), 1),
            'aptitude': round(float(dept.avg_aptitude), 1),
            'gd': round(float(dept.avg_gd), 1),
            'mi': dept.avg_mi,
            'applied': dept.applied_count,
            'app_ratio': dept.application_ratio,
        })

    context = {
        'total_students': total_students,
        'placed_students': placed_students,
        'placement_percentage': round(placement_percentage, 2),
        'company_wise': company_wise,
        'overall_attendance_pct': round(overall_attendance_pct, 2),
        'avg_aptitude': round(avg_aptitude, 2),
        'avg_gd': round(float(avg_gd), 2),
        'dept_results': dept_results,
        'dept_results_list': dept_results_list,
        'readiness_score': round(readiness_score, 2),
        'top_students': top_students_list,
        'aptitude_ranges': aptitude_ranges,
        'gd_ranges': gd_ranges,
        # Mock Interview Stats
        'mi_sessions_count': mi_sessions_count,
        'mi_evaluations_count': mi_evaluations_count,
        'mi_overall_avg': round(float(mi_overall_avg), 2),
        'mi_category_avgs': {
            'Communication': round(float(mi_stats['avg_comm'] or 0), 2),
            'Confidence': round(float(mi_stats['avg_conf'] or 0), 2),
            'Technical': round(float(mi_stats['avg_tech'] or 0), 2),
            'Body Language': round(float(mi_stats['avg_body'] or 0), 2),
            'Problem Solving': round(float(mi_stats['avg_ps'] or 0), 2),
        },
        'top_mi_students': top_mi_students,
    }
    return render(request, 'core/reports.html', context)

@login_required
@coordinator_required
def export_reports_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="placement_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Company Name', 'Job Role', 'Placed Count'])
    
    drives = PlacementDrive.objects.annotate(
        placed_count=Count('applications', filter=Q(applications__status='placed'))
    )
    
    for drive in drives:
        writer.writerow([drive.company_name, drive.job_role, drive.placed_count])
    
    return response

@login_required
@coordinator_required
def notifications(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            
            # Create individual notifications
            students = User.objects.filter(role='student')
            if announcement.target_type == 'drive' and announcement.drive:
                applied_student_ids = JobApplication.objects.filter(drive=announcement.drive).values_list('student__user_id', flat=True)
                students = students.filter(id__in=applied_student_ids)
            
            for student_user in students:
                Notification.objects.create(user=student_user, announcement=announcement)
                
            messages.success(request, 'Notification sent to students.')
            return redirect('notifications')
    else:
        form = AnnouncementForm()
    
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'core/notifications.html', {'form': form, 'announcements': announcements})
    

@login_required
@coordinator_required
def manage_courses(request):
    courses = Course.objects.all().order_by('category', 'type', 'name')
    return render(request, 'core/manage_courses.html', {'courses': courses})


@login_required
@coordinator_required
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course created successfully.')
            return redirect('manage_courses')
    else:
        form = CourseForm()
    return render(request, 'core/course_form.html', {'form': form, 'title': 'Create Course'})


@login_required
@coordinator_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('manage_courses')
    else:
        form = CourseForm(instance=course)
    return render(request, 'core/course_form.html', {'form': form, 'title': 'Edit Course'})


@login_required
@coordinator_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, 'Course deleted.')
    return redirect('manage_courses')


# --- Student Module Views ---

@login_required
@student_required
def student_aptitude_tests(request):
    tests = Test.objects.all().order_by('-created_at')
    attempts = TestAttempt.objects.filter(student__user=request.user).select_related('test').order_by('-completed_at')
    return render(request, 'core/student_aptitude_tests.html', {
        'tests': tests,
        'attempts': attempts
    })


@login_required
@student_required
def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all()

    if request.method == 'POST':
        score = 0
        total = questions.count()
        for question in questions:
            selected_option = request.POST.get(f'question_{question.id}')
            if selected_option and int(selected_option) == question.correct_option:
                score += 1

        student_profile = request.user.studentprofile
        TestAttempt.objects.create(
            student=student_profile,
            test=test,
            score=score,
            total_questions=total
        )
        messages.success(request, f'Test "{test.title}" completed! Your score: {score}/{total}')
        return redirect('student_aptitude_tests')

    return render(request, 'core/take_test.html', {
        'test': test,
        'questions': questions
    })


@login_required
@student_required
def student_mock_interviews(request):
    interviews = MockInterview.objects.filter(student__user=request.user).order_by('-date_time')
    return render(request, 'core/student_mock_interviews.html', {
        'interviews': interviews
    })

@login_required
@coordinator_required
def view_student_detail(request, student_id):
    # Base query for the specific student
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Calculate stats exactly like in manage_students
    # We need to wrap it in a queryset to use annotate properly or just calculate manually since it's one user
    # Using aggregation on related objects is cleaner for a single instance
    
    # Attendance
    attendance_qs = student.session_attendances.all()
    total_sessions = attendance_qs.count() # This might be wrong if session_attendances only exists for marked attendance? 
    # Let's check model. Attendance model links session and student. 
    # If we want total sessions occurred, we need all physicalSession objects? 
    # In manage_students we used: total_sessions_count=Count('session_attendances', distinct=True)
    # This implies we are counting Attendance records. 
    
    present_count = attendance_qs.filter(is_present=True).count()
    total_attendance_records = attendance_qs.count() 
    
    # GD Score
    # GDSession -> GDGroup -> GDGroupMember(student, score)
    gd_members = student.studentprofile.gdgroupmember_set.all()
    gd_avg = gd_members.aggregate(Avg('score'))['score__avg']
    
    # Aptitude Score
    # TestAttempt(score, total_questions)
    attempts = student.studentprofile.test_attempts.all()
    # Calculate average percentage
    aptitude_avg = 0
    if attempts.exists():
        total_percentage = 0
        for attempt in attempts:
            if attempt.total_questions > 0:
                total_percentage += (attempt.score / attempt.total_questions) * 100
        aptitude_avg = total_percentage / attempts.count()
        
    # Applied Drives
    applied_count = student.studentprofile.applications.count()
    
    drives = PlacementDrive.objects.all().order_by('-created_at')

    context = {
        'student': student,
        'attendance_present': present_count,
        'attendance_total': total_attendance_records,
        'gd_avg': gd_avg,
        'aptitude_avg': aptitude_avg,
        'applied_count': applied_count,
        'drives': drives, # For the placement modal if we move it here
    }
    return render(request, 'core/student_detail.html', context)

@login_required
@coordinator_required
def send_personal_notification(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(User, id=student_id, role='student')
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        if title and message:
            announcement = Announcement.objects.create(
                title=title,
                message=message,
                target_type='personal',
                recipient=student,
                created_by=request.user
            )
            # Create the notification record so it shows up in student's alerts
            Notification.objects.create(user=student, announcement=announcement)
            messages.success(request, f'Personal notification sent to {student.get_full_name()}.')
        else:
            messages.error(request, 'Both title and message are required.')
            
    return redirect('view_student_detail', student_id=student_id)

@login_required
@student_required
def student_placement_drives(request):
    from django.utils import timezone
    student = request.user.studentprofile
    now = timezone.now()

    # Filter drives based on eligibility (Batch, Year, Departments, CGPA)
    from django.db.models import Q
    drives = PlacementDrive.objects.filter(
        Q(eligible_batch=student.batch) | Q(eligible_batch__in=[0, None]),
        Q(eligible_year=student.year) | Q(eligible_year__in=[0, None])
    ).order_by('registration_deadline')

    active_eligible_drives = []
    expired_eligible_drives = []
    
    student_course = student.user.department
    
    for drive in drives:
        # Check CGPA eligibility (if min_cgpa is set)
        cgpa_eligible = True
        if drive.min_cgpa is not None:
            if student.cgpa < drive.min_cgpa:
                cgpa_eligible = False
        
        # Check Department eligibility
        dept_eligible = False
        if drive.is_for_all_departments:
            dept_eligible = True
        elif student_course and drive.eligible_departments.filter(id=student_course.id).exists():
            dept_eligible = True
        elif not drive.eligible_departments.exists():
            dept_eligible = True
            
        if cgpa_eligible and dept_eligible:
            if drive.registration_deadline > now:
                active_eligible_drives.append(drive)
            else:
                expired_eligible_drives.append(drive)

    # Get application status — store full app objects keyed by drive_id
    applications = JobApplication.objects.filter(student=student).select_related('drive')
    applied_drive_ids = list(applications.values_list('drive_id', flat=True))
    application_map = {app.drive_id: app for app in applications}  # full object, not just status

    # Placed applications (for "Ready to Work" section)
    placed_applications = [app for app in applications if app.status == 'placed']
    accepted_application = next((app for app in applications if app.is_accepted), None)

    return render(request, 'core/student_placement_drives.html', {
        'active_drives': active_eligible_drives,
        'expired_drives': expired_eligible_drives,
        'applied_drive_ids': applied_drive_ids,
        'application_map': application_map,
        'placed_applications': placed_applications,
        'accepted_application': accepted_application,
    })


@login_required
@student_required
def apply_drive(request, drive_id):
    drive = get_object_or_404(PlacementDrive, id=drive_id)
    student = request.user.studentprofile

    # Double check eligibility
    student_course = student.user.department
    
    cgpa_eligible = True
    if drive.min_cgpa is not None:
        if student.cgpa < drive.min_cgpa:
            cgpa_eligible = False
            
    dept_eligible = False
    if drive.is_for_all_departments:
        dept_eligible = True
    elif student_course and drive.eligible_departments.filter(id=student_course.id).exists():
        dept_eligible = True
    elif not drive.eligible_departments.exists():
        dept_eligible = True
        
    is_eligible = (
        cgpa_eligible and 
        dept_eligible and
        student.batch == drive.eligible_batch and
        student.year == drive.eligible_year and
        not drive.is_expired
    )

    if is_eligible:
        JobApplication.objects.get_or_create(drive=drive, student=student)
        messages.success(request, f'Successfully applied for {drive.company_name}.')
    elif drive.is_expired:
        messages.error(request, 'The registration deadline for this drive has passed.')
    else:
        messages.error(request, 'You are not eligible for this drive.')

    return redirect('student_placement_drives')


@login_required
@student_required
def withdraw_application(request, drive_id):
    drive = get_object_or_404(PlacementDrive, id=drive_id)
    student = request.user.studentprofile
    
    application = JobApplication.objects.filter(drive=drive, student=student).first()
    if application:
        application.delete()
        messages.success(request, f'Withdrawn from {drive.company_name}.')
    
    return redirect('student_placement_drives')

@login_required
@student_required
def student_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at').select_related('announcement')
    
    personal_notifications = []
    announcements = []
    
    for notif in notifications:
        if notif.announcement.target_type == 'personal':
            personal_notifications.append(notif)
        else:
            announcements.append(notif)
    
    # Mark as read functionality 
    unread_notifications = notifications.filter(is_read=False)
    if unread_notifications.exists():
        unread_notifications.update(is_read=True)
        
    return render(request, 'core/student_notifications.html', {
        'personal_notifications': personal_notifications,
        'announcements': announcements
    })
