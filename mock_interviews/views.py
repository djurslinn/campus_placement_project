from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q, F, FloatField, ExpressionWrapper
from django.utils import timezone

from accounts.models import StudentProfile, Course
from core.views import coordinator_required, student_required

from .models import MockInterviewSession, MockInterviewPair, MockInterviewEvaluation
from .forms import GenerateSessionForm, EvaluationForm
from .pairing import generate_pairs
from .utils import get_suggestions


# ────────────────────────────────────────────────
# COORDINATOR VIEWS
# ────────────────────────────────────────────────

@login_required
@coordinator_required
def coordinator_dashboard(request):
    """Overview + session generation."""
    departments = Course.objects.all().order_by('name')
    years       = StudentProfile.objects.values_list('year', flat=True).distinct().order_by('year')

    sessions = (
        MockInterviewSession.objects
        .filter(created_by=request.user)
        .prefetch_related('pairs', 'evaluations')
        .order_by('-created_at')
    )

    if request.method == 'POST':
        form = GenerateSessionForm(request.POST, departments=departments, years=years)
        if form.is_valid():
            label        = form.cleaned_data.get('label') or ''
            target_type  = form.cleaned_data.get('target_type')
            dept_id      = form.cleaned_data.get('department')
            year         = form.cleaned_data.get('year')
            target_drive = form.cleaned_data.get('target_drive')

            # Fetch eligible active students
            qs = StudentProfile.objects.filter(is_active=True, is_approved=True).select_related('user')
            
            if target_type == 'department' and dept_id:
                qs = qs.filter(user__department_id=dept_id)
            elif target_type == 'drive' and target_drive:
                # Filter by drive eligibility criteria
                if not target_drive.is_for_all_departments:
                    qs = qs.filter(user__department__in=target_drive.eligible_departments.all())
                
                # Basic batch/year filter
                qs = qs.filter(
                    batch=target_drive.eligible_batch,
                    year=target_drive.eligible_year
                )
                
                # Optional CGPA filter (avoids 'Cannot use None as a query value' error)
                if target_drive.min_cgpa is not None:
                    qs = qs.filter(cgpa__gte=target_drive.min_cgpa)
            # If 'everyone' or other combinations, optionally still apply year/dept filters if provided
            elif target_type == 'everyone':
                if dept_id:
                    qs = qs.filter(user__department_id=dept_id)
            
            if year:
                qs = qs.filter(year=year)

            student_list = list(qs)
            if len(student_list) < 2:
                messages.error(request, 'Need at least 2 eligible students to generate a session.')
                return redirect('mock_interviews:coordinator_dashboard')

            session = MockInterviewSession.objects.create(
                created_by=request.user,
                label=label,
                target_type=target_type,
                department=Course.objects.filter(pk=dept_id).first() if dept_id else None,
                year=year,
                target_drive=target_drive,
            )
            generate_pairs(session, student_list)
            messages.success(request,
                f'Session #{session.pk} created with {session.pairs.count()} pair(s).')
            return redirect('mock_interviews:coordinator_dashboard')
    else:
        form = GenerateSessionForm(departments=departments, years=years)

    # Annotate for summary cards
    total_sessions    = sessions.count()
    active_sessions   = sessions.filter(status='active').count()
    total_pairs       = MockInterviewPair.objects.filter(session__created_by=request.user).count()
    total_evaluations = MockInterviewEvaluation.objects.filter(session__created_by=request.user).count()

    return render(request, 'mock_interviews/coordinator_dashboard.html', {
        'form':              form,
        'sessions':          sessions,
        'courses':           departments,  # renamed to match template
        'years':             years,        # passed for modal if needed
        'total_sessions':    total_sessions,
        'active_sessions':   active_sessions,
        'total_pairs':       total_pairs,
        'total_evaluations': total_evaluations,
    })


@login_required
@coordinator_required
def session_detail(request, session_id):
    """Detailed view of one session: all pairs + completion status + session analysis."""
    session = get_object_or_404(MockInterviewSession, pk=session_id)

    pairs = (
        session.pairs
        .select_related('student1__user', 'student2__user', 'student3__user')
        .prefetch_related('session__evaluations')
        .all()
    )

    # Build rich pair data
    pairs_data = []
    for pair in pairs:
        members = pair.members()
        pair_info = {'pair': pair, 'members': []}

        for student in members:
            partners = pair.partner_of(student)
            for partner in partners:
                latest_eval = (
                    MockInterviewEvaluation.objects
                    .filter(session=session, evaluator=student, evaluatee=partner)
                    .order_by('-submitted_at')
                    .first()
                )
                pair_info['members'].append({
                    'student': student,
                    'partner': partner,
                    'latest_eval': latest_eval,
                    'submitted': latest_eval is not None,
                })
        pairs_data.append(pair_info)

    # Session-wide Analytics
    all_session_evals = list(session.evaluations.all())
    session_analysis = get_suggestions(all_session_evals) if all_session_evals else None

    # Top Performers (based on evaluatee average score in this session)
    top_performers = (
        MockInterviewEvaluation.objects
        .filter(session=session)
        .values('evaluatee', 'evaluatee__user__first_name', 'evaluatee__user__last_name', 'evaluatee__roll_no')
        .annotate(avg_score=Avg(
            ExpressionWrapper(
                (F('communication') + F('confidence') + F('technical') + F('body_language') + F('problem_solving')) / 5.0,
                output_field=FloatField()
            )
        ))
        .order_by('-avg_score')[:5]
    )

    # Student-level filter for reports
    filter_student_id = request.GET.get('student')
    report_evals = []
    filter_student = None
    if filter_student_id:
        filter_student = StudentProfile.objects.filter(pk=filter_student_id).first()
        if filter_student:
            report_evals = list(
                MockInterviewEvaluation.objects
                .filter(session=session, evaluatee=filter_student)
                .select_related('evaluator__user')
                .order_by('-submitted_at')
            )

    all_students = StudentProfile.objects.filter(
        Q(mi_pairs_as_s1__session=session) |
        Q(mi_pairs_as_s2__session=session) |
        Q(mi_pairs_as_s3__session=session)
    ).select_related('user').distinct()

    all_active_sessions = (
        MockInterviewSession.objects
        .filter(status='active', created_by=request.user)
        .exclude(pk=session_id)
        .order_by('-created_at')
    )

    return render(request, 'mock_interviews/session_detail.html', {
        'session':               session,
        'pairs_data':            pairs_data,
        'all_students':          all_students,
        'filter_student':        filter_student,
        'report_evals':          report_evals,
        'pairs_count':           session.total_pairs,
        'completion_percentage': session.completion_pct,
        'session_analysis':      session_analysis,
        'top_performers':        top_performers,
        'all_active_sessions':   all_active_sessions,
    })


@login_required
@coordinator_required
def delete_session(request, session_id):
    session = get_object_or_404(MockInterviewSession, pk=session_id, created_by=request.user)
    session.delete()
    messages.success(request, 'Session deleted.')
    return redirect('mock_interviews:coordinator_dashboard')


# ────────────────────────────────────────────────
# STUDENT VIEWS
# ────────────────────────────────────────────────

@login_required
@student_required
def student_dashboard(request):
    """Student's mock interview overview: all sessions they're part of."""
    try:
        profile = request.user.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')

    # All pairs this student is part of
    pairs = (
        MockInterviewPair.objects
        .filter(
            Q(student1=profile) | Q(student2=profile) | Q(student3=profile)
        )
        .select_related(
            'session',
            'student1__user', 'student2__user', 'student3__user',
        )
        .order_by('-session__created_at')
    )

    pairings = []
    for pair in pairs:
        session = pair.session
        partners = pair.partner_of(profile)

        for partner in partners:
            latest_eval = (
                MockInterviewEvaluation.objects
                .filter(session=session, evaluator=profile, evaluatee=partner)
                .order_by('-submitted_at')
                .first()
            )
            pairings.append({
                'session':    session,
                'pair':       pair,
                'partner':    partner,
                'evaluation': latest_eval,
                'status':     'Submitted' if latest_eval else 'Pending',
            })

    return render(request, 'mock_interviews/student_tasks.html', {
        'pairings':    pairings,
        'profile':     profile,
        'score_range': range(1, 11),
    })


@login_required
@student_required
def submit_evaluation(request, session_id, evaluatee_id):
    """Create or update evaluation (always inserts new row = full history)."""
    try:
        profile = request.user.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('student_dashboard')

    session  = get_object_or_404(MockInterviewSession, pk=session_id)
    evaluatee = get_object_or_404(StudentProfile, pk=evaluatee_id)

    # Guard: student cannot evaluate themselves
    if profile == evaluatee:
        messages.error(request, 'You cannot evaluate yourself.')
        return redirect('mock_interviews:student_dashboard')

    # Guard: must be in same pair
    in_pair = (
        MockInterviewPair.objects
        .filter(session=session)
        .filter(
            Q(student1=profile) | Q(student2=profile) | Q(student3=profile)
        )
        .filter(
            Q(student1=evaluatee) | Q(student2=evaluatee) | Q(student3=evaluatee)
        )
        .exists()
    )
    if not in_pair:
        messages.error(request, 'You are not paired with this student in this session.')
        return redirect('mock_interviews:student_dashboard')

    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            # Use update_or_create for "unlimited submissions, update in db each time"
            ev, created = MockInterviewEvaluation.objects.update_or_create(
                session=session,
                evaluator=profile,
                evaluatee=evaluatee,
                defaults={
                    'communication':   form.cleaned_data['communication'],
                    'confidence':      form.cleaned_data['confidence'],
                    'technical':       form.cleaned_data['technical'],
                    'body_language':   form.cleaned_data['body_language'],
                    'problem_solving': form.cleaned_data['problem_solving'],
                    'feedback':        form.cleaned_data['feedback'],
                    'submitted_at':    timezone.now(),
                }
            )
            msg = f'Evaluation for {evaluatee.user.get_full_name()} updated!' if not created else f'Evaluation for {evaluatee.user.get_full_name()} submitted!'
            messages.success(request, msg)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        messages.error(request, 'Invalid request method.')

    return redirect('mock_interviews:student_dashboard')


@login_required
@student_required
def student_report(request):
    """Full report: all evaluations received, averages, suggestions."""
    try:
        profile = request.user.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('student_dashboard')

    evaluations = list(
        MockInterviewEvaluation.objects
        .filter(evaluatee=profile)
        .select_related('evaluator__user', 'session')
        .order_by('-submitted_at')
    )

    # Group latest eval per (session, evaluator) for "per-session" view
    seen_keys = set()
    latest_evals = []
    for ev in evaluations:
        key = (ev.session_id, ev.evaluator_id)
        if key not in seen_keys:
            seen_keys.add(key)
            latest_evals.append(ev)

    analysis = get_suggestions(latest_evals)

    return render(request, 'mock_interviews/student_report.html', {
        'profile':             profile,
        'evaluations':         latest_evals,
        'latest_eval':         latest_evals[0] if latest_evals else None,
        'analysis':            analysis,
        'strengths':           analysis['strengths'],
        'weaknesses':          analysis['weaknesses'],
        'suggestions':         analysis['suggestions'],
        'overall_avg':         analysis['overall_avg'],
        'performance_level':   analysis['performance_level'],
        'improvement_summary': analysis['improvement_summary'],
    })
