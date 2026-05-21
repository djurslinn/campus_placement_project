from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from core.models import PlacementDrive
from accounts.models import StudentProfile
from .models import PDFTest, PDFTestResult
from .forms import PDFTestForm

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

# --- Coordinator Views ---

@login_required
@coordinator_required
def manage_pdf_tests(request):
    tests = PDFTest.objects.all().order_by('-created_at')
    return render(request, 'aptitude_test/manage_tests.html', {'tests': tests})

@login_required
@coordinator_required
def create_pdf_test(request):
    if request.method == 'POST':
        form = PDFTestForm(request.POST, request.FILES)
        if form.is_valid():
            test = form.save(commit=False)
            test.created_by = request.user
            test.save()
            messages.success(request, 'Aptitude Test created successfully.')
            return redirect('manage_pdf_tests')
    else:
        form = PDFTestForm()
    return render(request, 'aptitude_test/create_test.html', {
        'form': form,
        'is_edit': False
    })

@login_required
@coordinator_required
def edit_pdf_test(request, test_id):
    test = get_object_or_404(PDFTest, id=test_id)
    if request.method == 'POST':
        form = PDFTestForm(request.POST, request.FILES, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aptitude Test updated successfully.')
            return redirect('manage_pdf_tests')
    else:
        # Initialize form with answer_key_input
        form = PDFTestForm(instance=test, initial={'answer_key_input': test.answer_key})
    
    return render(request, 'aptitude_test/create_test.html', {
        'form': form,
        'test': test,
        'is_edit': True
    })

@login_required
@coordinator_required
def delete_pdf_test(request, test_id):
    test = get_object_or_404(PDFTest, id=test_id)
    if request.method == 'POST':
        test.delete()
        messages.success(request, 'Test deleted successfully.')
    return redirect('manage_pdf_tests')

@login_required
@coordinator_required
def toggle_test_visibility(request, test_id):
    test = get_object_or_404(PDFTest, id=test_id)
    test.is_published = not test.is_published
    test.save()
    status = "visible to" if test.is_published else "hidden from"
    messages.success(request, f"Test is now {status} students.")
    return redirect('manage_pdf_tests')

@login_required
@coordinator_required
def reset_test_results(request, test_id):
    test = get_object_or_404(PDFTest, id=test_id)
    if request.method == 'POST':
        PDFTestResult.objects.filter(test=test).delete()
        messages.success(request, f"All results for '{test.title}' have been cleared. Students can now retest.")
    return redirect('manage_pdf_tests')

@login_required
@coordinator_required
def view_test_results(request, test_id):
    test = get_object_or_404(PDFTest, id=test_id)
    results = PDFTestResult.objects.filter(test=test).order_by('-score')
    return render(request, 'aptitude_test/view_results.html', {'test': test, 'results': results})

@login_required
@coordinator_required
def view_eligible_students(request, test_id):
    test = get_object_or_404(PDFTest, id=test_id)
    
    # Base queryset for approved active students
    students = StudentProfile.objects.filter(is_active=True, is_approved=True).select_related('user', 'user__department')
    
    # Filter based on test target
    if test.target_type == 'everyone':
        # No additional filtering needed
        pass
    elif test.target_type == 'department':
        students = students.filter(user__department=test.target_department)
    elif test.target_type == 'drive':
        drive = test.target_drive
        if drive:
            if not drive.is_for_all_departments:
                students = students.filter(user__department__in=drive.eligible_departments.all())
            
            students = students.filter(
                batch=drive.eligible_batch,
                year=drive.eligible_year,
                cgpa__gte=drive.min_cgpa or 0
            )
        else:
            # If drive was deleted or not set correctly for 'drive' type
            students = students.none()
    
    # Mark students who have already completed the test
    completed_student_ids = PDFTestResult.objects.filter(test=test).values_list('student_id', flat=True)
    
    eligible_students = []
    attempted_count = 0
    for student in students:
        is_completed = student.id in completed_student_ids
        if is_completed:
            attempted_count += 1
        eligible_students.append({
            'profile': student,
            'completed': is_completed
        })
        
    total_eligible = len(eligible_students)
    remaining_count = total_eligible - attempted_count

    return render(request, 'aptitude_test/eligible_students.html', {
        'test': test,
        'eligible_students': eligible_students,
        'stats': {
            'total': total_eligible,
            'attempted': attempted_count,
            'remaining': remaining_count
        }
    })


# --- Student Views ---

@login_required
@student_required
def student_pdf_tests(request):
    student = request.user.studentprofile
    
    # Get IDs of drives student is eligible for
    eligible_drive_ids = PlacementDrive.objects.filter(
        Q(is_for_all_departments=True) | Q(eligible_departments=student.user.department),
        eligible_batch=student.batch,
        eligible_year=student.year,
        min_cgpa__lte=student.cgpa
    ).values_list('id', flat=True)

    # Filter tests based on target_type and eligibility
    tests = PDFTest.objects.filter(
        Q(target_type='everyone') |
        Q(target_type='department', target_department=student.user.department) |
        Q(target_type='drive', target_drive_id__in=eligible_drive_ids),
        is_published=True
    ).order_by('-created_at')
    # Use a dictionary to check attempt status efficiently
    results = PDFTestResult.objects.filter(student=request.user.studentprofile).select_related('test')
    attempted_ids = {r.test.id: r for r in results}
    
    test_list = []
    for t in tests:
        result = attempted_ids.get(t.id)
        test_list.append({
            'test': t,
            'attempted': result is not None,
            'message': f"Score: {result.score}/{t.total_questions}" if result else "Start Test"
        })
        
    return render(request, 'aptitude_test/student_tests.html', {'test_list': test_list})

@login_required
@student_required
def take_pdf_test(request, test_id):
    test = get_object_or_404(PDFTest, id=test_id)
    student = request.user.studentprofile
    
    # Preventing multiple attempts
    if PDFTestResult.objects.filter(student=student, test=test).exists():
        messages.warning(request, "You have already attempted this test.")
        return redirect('student_pdf_tests')

    total_questions = test.total_questions
    
    if request.method == 'POST':
        user_answers = {}
        correct_count = 0
        answer_key = {}
        
        # Parse answer key string "1:A,2:B..." into dict {'1': 'A', '2': 'B'}
        if test.answer_key:
            items = [x.strip() for x in test.answer_key.split(',') if x.strip()]
            for item in items:
                parts = item.split(':')
                if len(parts) == 2:
                    answer_key[parts[0].strip()] = parts[1].strip().upper()
        
        # Process POST data "q_1", "q_2", etc.
        for i in range(1, total_questions + 1):
            q_key = str(i)
            selected = request.POST.get(f'q_{i}')
            
            if selected:
                user_answers[q_key] = selected
                correct_ans = answer_key.get(q_key)
                if correct_ans and selected == correct_ans:
                    correct_count += 1
            else:
                user_answers[q_key] = None # Or 'Skipped'
        
        # Calculate score
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Save Result
        PDFTestResult.objects.create(
            student=student,
            test=test,
            score=correct_count,
            percentage=round(percentage, 2),
            submitted_answers=str(user_answers) # Just for record
        )
        
        messages.success(request, f"Test submitted! Your score: {correct_count}/{total_questions}")
        return redirect('student_pdf_tests')

    return render(request, 'aptitude_test/take_test.html', {
        'test': test,
        'range': range(1, total_questions + 1)
    })
