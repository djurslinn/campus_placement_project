import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import GDTopic, GDSession, GDGroup, GDGroupMember
from .forms import GDSessionForm
from accounts.models import StudentProfile, User
from django.db import transaction

# Decorators from core/views.py (Re-implemented or imported)
def coordinator_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'coordinator':
            messages.error(request, 'Access denied. Coordinators only.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'student':
            messages.error(request, 'Access denied. Students only.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@coordinator_required
def manage_gd_sessions(request):
    sessions = GDSession.objects.all().order_by('-scheduled_at')
    return render(request, 'group_discussion/manage_sessions.html', {'sessions': sessions})

@login_required
@coordinator_required
def delete_gd_session(request, session_id):
    session = get_object_or_404(GDSession, id=session_id)
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Group Discussion session deleted successfully.')
        return redirect('manage_gd_sessions')
    return redirect('manage_gd_sessions')

@login_required
@coordinator_required
def create_gd_session(request):
    if request.method == 'POST':
        form = GDSessionForm(request.POST)
        if form.is_valid():
            num_groups = form.cleaned_data['num_groups']
            dept = form.cleaned_data['department']
            year = form.cleaned_data['year']
            
            # Fetch students based on filters
            students_qs = StudentProfile.objects.filter(is_active=True, is_approved=True)
            if dept:
                students_qs = students_qs.filter(user__department__name=dept)
            if year:
                students_qs = students_qs.filter(year=year)
            
            students_list = list(students_qs)
            
            # Check if enough students exist
            if len(students_list) < num_groups and len(students_list) < 2:
                # If cannot form even 1 valid group (need at least 2 students generally, or 1 student for 1 group)
                # Logic: If user asks for 4 groups but has 3 students -> Algo handles it (makes 1 group of 3 or 2 groups of 2+1)
                # But if user asks for ANY groups and has 0 students:
                pass
            
            if len(students_list) == 0:
                return render(request, 'group_discussion/session_form.html', {
                    'form': form,
                    'error_popup': "No students found matching the selected criteria."
                })
            
            # Additional check: If user wants 4 groups but only has 3 students. 
            # The previous algo handles this by reducing group count.
            # But user asked for specific error "if group cannot be formed".
            # Let's say "group cannot be formed" means 0 students found.
            
            # If the user specifically meant "if I ask for X groups and you can't make X groups", 
            # the previous request asked to "add them with existing groups", which implies flexible group count.
            # So the only fatal error is 0 students.

            try:
                with transaction.atomic():
                    # Create the session
                    session = form.save(commit=False)
                    session.coordinator = request.user
                    session.save()
                    
                    # Randomize students for unique groups
                    random.shuffle(students_list)
                    
                    # Logic to ensure no group has only 1 student (unless total < 2)
                    total_students = len(students_list)
                    if total_students >= 2:
                        # Max groups such that each has at least 2 students
                        max_groups = total_students // 2
                        # Use the requested num_groups unless it causes singleton groups
                        optimal_num_groups = min(num_groups, max_groups)
                        # Ensure at least 1 group
                        optimal_num_groups = max(1, optimal_num_groups)
                    else:
                        optimal_num_groups = 1

                    # Divide students into optimal number of groups
                    groups = [[] for _ in range(optimal_num_groups)]
                    for i, student in enumerate(students_list):
                        groups[i % optimal_num_groups].append(student)
                    
                    # Create GDGroup and Members
                    for i, group_students in enumerate(groups):
                        gd_group = GDGroup.objects.create(
                            session=session,
                            group_name=f"Group {i+1}"
                        )
                        for student in group_students:
                            GDGroupMember.objects.create(
                                group=gd_group,
                                student=student
                            )
                    
                messages.success(request, f"GD Session created with {len(groups)} groups.")
                return redirect('view_gd_session', session_id=session.id)
            except Exception as e:
                messages.error(request, f"Error creating session: {str(e)}")
    else:
        form = GDSessionForm()
    
    return render(request, 'group_discussion/session_form.html', {'form': form})

@login_required
@coordinator_required
def view_gd_session(request, session_id):
    session = get_object_or_404(GDSession, id=session_id)
    groups = session.groups.all().prefetch_related('members__student__user')
    
    if request.method == 'POST':
        # Handle scoring
        for group in groups:
            for member in group.members.all():
                score_key = f"score_{member.id}"
                feedback_key = f"feedback_{member.id}"
                if score_key in request.POST:
                    score_val = request.POST.get(score_key)
                    member.score = score_val if score_val.strip() != "" else None
                    member.feedback = request.POST.get(feedback_key)
                    member.save()
        messages.success(request, "Scores and feedback updated.")
        return redirect('view_gd_session', session_id=session.id)

    return render(request, 'group_discussion/view_session.html', {'session': session, 'groups': groups})

@login_required
@student_required
def student_gd_sessions(request):
    student_profile = request.user.studentprofile
    # Find all groups where this student is a member
    memberships = GDGroupMember.objects.filter(student=student_profile).select_related('group__session', 'group__session__topic')
    
    return render(request, 'group_discussion/student_sessions.html', {'memberships': memberships})
