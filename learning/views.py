from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
import json
import logging

from .models import User, LearnerProgress, ModelEdit
from .forms import LoginForm, RegisterForm, SQLQueryForm
from .dbt_manager import DBTManager
from .storage import MotherDuckStorage
from .ai_views import ai_assistant, ai_chat, analyze_model, generate_test
from .dbt_lineage_parser import get_project_lineage
from datetime import datetime, date
from decimal import Decimal
import pandas as pd

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, Timestamp, and Decimal objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Lesson configuration
LESSONS = [
    {
        "id": "hello_dbt",
        "title": "🧱 Hello dbt",
        "description": "Learn dbt fundamentals with simple customer and order data",
        "model_dir": "models/hello_dbt",
        "validation": {
            "sql": "SELECT COUNT(*) AS models_built FROM information_schema.tables WHERE table_schema=current_schema()",
            "expected_min": 3
        },
    },
    {
        "id": "fintech",
        "title": "💳 Fintech: Digital Payments",
        "description": "Build payment analytics pipeline - GMV, merchant segments, fraud detection",
        "model_dir": "models/fintech",
        "validation": {
            "sql": "SELECT COUNT(*) AS models_built FROM information_schema.tables WHERE table_schema=current_schema()",
            "expected_min": 5
        },
    },
    {
        "id": "cafe_chain",
        "title": "☕ Café Chain Analytics",
        "description": "Analyze coffee shop sales, product performance, and store metrics",
        "model_dir": "models/cafe_chain",
        "validation": {
            "sql": "SELECT COUNT(*) AS models_built FROM information_schema.tables WHERE table_schema=current_schema()",
            "expected_min": 5
        },
    },
    {
        "id": "energy_smart",
        "title": "⚡ Energy Smart: IoT Data",
        "description": "Process smart meter readings and optimize energy consumption",
        "model_dir": "models/energy_smart",
        "validation": {
            "sql": "SELECT COUNT(*) AS models_built FROM information_schema.tables WHERE table_schema=current_schema()",
            "expected_min": 5
        },
    }
]

# ========== HOME VIEWS ==========

def home(request):
    """Landing page view"""
    # Redirect to dashboard if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'home.html')

# ========== AUTHENTICATION VIEWS ==========

def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ========== DASHBOARD AND LESSON VIEWS ==========

@login_required
def dashboard(request):
    """Main dashboard showing all lessons"""
    user = request.user
    all_progress = LearnerProgress.objects.filter(user=user)
    
    # Build progress dict
    progress_dict = {p.lesson_id: p for p in all_progress}
    
    # Add progress info to lessons
    lessons_with_progress = []
    for lesson in LESSONS:
        lesson_copy = lesson.copy()
        progress = progress_dict.get(lesson['id'])
        lesson_copy['progress'] = progress.lesson_progress if progress else 0
        lessons_with_progress.append(lesson_copy)
    
    # --- Calculate statistics ---
    total_lessons = len(lessons_with_progress)
    completed = sum(1 for l in lessons_with_progress if l['progress'] == 100)
    in_progress = sum(1 for l in lessons_with_progress if 0 < l['progress'] < 100)

    context = {
        'lessons': lessons_with_progress,
        'user': user,
        'total': total_lessons,
        'completed': completed,
        'in_progress': in_progress
    }
    return render(request, 'learning/dashboard.html', context)


@login_required
def lesson_detail(request, lesson_id):
    """Lesson detail view"""
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        messages.error(request, 'Lesson not found')
        return redirect('dashboard')
    
    # Get or create progress
    progress, created = LearnerProgress.objects.get_or_create(
        user=request.user,
        lesson_id=lesson_id,
        defaults={'lesson_progress': 0}
    )
    
    context = {
        'lesson': lesson,
        'progress': progress,
        'user': request.user,
    }
    return render(request, 'learning/lesson_detail.html', context)


# ========== MODEL BUILDER VIEW ==========

@login_required
def model_builder(request, lesson_id):
    """Model builder - edit and execute dbt models"""
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        messages.error(request, 'Lesson not found')
        return redirect('dashboard')
    
    # Initialize DBT manager
    try:
        dbt_manager = DBTManager(request.user, lesson)
    except Exception as e:
        logger.error(f"Error initializing DBT manager: {str(e)}")
        messages.error(request, f'Error initializing workspace: {str(e)}')
        return redirect('lesson_detail', lesson_id=lesson_id)
    
    # Variables for logs
    execution_logs = None
    seed_logs = None
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'initialize':
            success, message = dbt_manager.initialize_workspace()
            if success:
                messages.success(request, message)
                # Update progress
                progress, _ = LearnerProgress.objects.get_or_create(
                    user=request.user, lesson_id=lesson_id
                )
                progress.lesson_progress = min(100, progress.lesson_progress + 20)
                progress.completed_steps = progress.completed_steps or []
                if 'sandbox_initialized' not in progress.completed_steps:
                    progress.completed_steps.append('sandbox_initialized')
                progress.save()
            else:
                messages.error(request, message)
        
        elif action == 'save_model':
            model_name = request.POST.get('model_name')
            model_sql = request.POST.get('model_sql')
            success, message = dbt_manager.save_model(model_name, model_sql)
            if success:
                messages.success(request, message)
                # Save to database
                ModelEdit.objects.update_or_create(
                    user=request.user,
                    lesson_id=lesson_id,
                    model_name=model_name,
                    defaults={'model_sql': model_sql}
                )
            else:
                messages.error(request, message)
        
        elif action == 'execute_models':
            selected_models = request.POST.getlist('selected_models')
            include_children = request.POST.get('include_children') == 'on'
            full_refresh = request.POST.get('full_refresh') == 'on'
            use_streaming = request.POST.get('stream') == 'true'

            if not selected_models:
                messages.error(request, 'Please select at least one model to execute')
            else:
                if use_streaming:
                    # Start streaming execution
                    job_id, error = dbt_manager.execute_models_streaming(
                        selected_models, include_children, full_refresh
                    )

                    if job_id:
                        # Return job ID for streaming
                        return JsonResponse({
                            'success': True,
                            'job_id': job_id,
                            'models': selected_models
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': error
                        })
                else:
                    # Non-streaming execution (original code)
                    success, results = dbt_manager.execute_models(
                        selected_models, include_children, full_refresh
                    )

                    if success:
                        # Collect all logs
                        execution_logs = []
                        for result in results:
                            if result['success']:
                                messages.success(request, f"✅ Model '{result['model']}' executed successfully")
                            else:
                                messages.error(request, f"❌ Model '{result['model']}' failed")

                            # Store logs for display
                            execution_logs.append({
                                'model': result['model'],
                                'output': result['output'],
                                'success': result['success']
                            })

                        # Update progress
                        progress, _ = LearnerProgress.objects.get_or_create(
                            user=request.user, lesson_id=lesson_id
                        )
                        progress.models_executed = list(set(progress.models_executed + selected_models))
                        progress.lesson_progress = min(100, progress.lesson_progress + 20)
                        progress.save()
                    else:
                        messages.error(request, f'Error executing models: {results}')
        
        elif action == 'run_seeds':
            use_streaming = request.POST.get('stream') == 'true'

            if use_streaming:
                # Start streaming seed execution
                job_id, error = dbt_manager.run_seeds_streaming()

                if job_id:
                    # Return job ID for streaming
                    return JsonResponse({
                        'success': True,
                        'job_id': job_id
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': error
                    })
            else:
                # Non-streaming execution (original code)
                success, message = dbt_manager.run_seeds()
                if success:
                    messages.success(request, 'Seeds loaded successfully')
                    seed_logs = message  # Store the output
                else:
                    messages.error(request, f'Error loading seeds: {message}')
                    seed_logs = message
        
        # Don't redirect if we have logs to show
        if not execution_logs and not seed_logs:
            return redirect('model_builder', lesson_id=lesson_id)
    
    # GET request - show the builder
    model_files = dbt_manager.get_model_files()
    is_initialized = dbt_manager.is_initialized()
    
    # Get progress
    progress, _ = LearnerProgress.objects.get_or_create(
        user=request.user,
        lesson_id=lesson_id,
        defaults={'lesson_progress': 0}
    )
    
    context = {
        'lesson': lesson,
        'model_files': model_files,
        'is_initialized': is_initialized,
        'progress': progress,
        'execution_logs': execution_logs,
        'seed_logs': seed_logs,
    }
    return render(request, 'learning/model_builder.html', context)


@login_required
def stream_dbt_logs(request, job_id):
    """Stream DBT execution logs using Server-Sent Events"""
    def event_stream():
        """Generator for SSE events"""
        for log_line in DBTManager.get_job_logs(job_id):
            yield log_line

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ========== QUERY VISUALIZER VIEW ==========

@login_required
def query_visualize(request, lesson_id):
    """Query builder and visualizer"""
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        messages.error(request, 'Lesson not found')
        return redirect('dashboard')
    
    result_data = None
    result_data_json = None
    query = None
    
    if request.method == 'POST':
        form = SQLQueryForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            storage = MotherDuckStorage()
            
            try:
                result_data = storage.execute_query(
                    request.user.schema_name, 
                    query
                )
                
                # Convert to JSON for JavaScript with custom encoder
                result_data_json = json.dumps({
                    'columns': result_data['columns'],
                    'data': result_data['data']
                }, cls=CustomJSONEncoder)
                
                messages.success(request, 'Query executed successfully')
                
                # Update progress
                progress, _ = LearnerProgress.objects.get_or_create(
                    user=request.user, lesson_id=lesson_id
                )
                progress.queries_run += 1
                progress.lesson_progress = min(100, progress.lesson_progress + 10)
                progress.save()
                
            except Exception as e:
                messages.error(request, f'Query error: {str(e)}')
    else:
        form = SQLQueryForm()
    
    context = {
        'lesson': lesson,
        'form': form,
        'result_data': result_data,
        'result_data_json': result_data_json,
        'query': query,
    }
    return render(request, 'learning/query_visualize.html', context)


@login_required
def progress_dashboard(request, lesson_id):
    """Progress tracking dashboard"""
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        messages.error(request, 'Lesson not found')
        return redirect('dashboard')
    
    progress = get_object_or_404(LearnerProgress, user=request.user, lesson_id=lesson_id)
    all_progress = LearnerProgress.objects.filter(user=request.user)
    
    # Serialize progress data for JavaScript
    all_progress_data = [
        {
            'lesson_id': p.lesson_id,
            'lesson_progress': p.lesson_progress
        }
        for p in all_progress
    ]
    
    context = {
        'lesson': lesson,
        'progress': progress,
        'all_progress': json.dumps(all_progress_data),
        'lessons': json.dumps(LESSONS),
    }
    return render(request, 'learning/progress.html', context)


# ========== API ENDPOINTS ==========

@login_required
@require_http_methods(["POST"])
def api_get_model_content(request):
    """API: Get model SQL content"""
    model_name = request.POST.get('model_name')
    lesson_id = request.POST.get('lesson_id')
    
    try:
        model_edit = ModelEdit.objects.get(
            user=request.user,
            lesson_id=lesson_id,
            model_name=model_name
        )
        return JsonResponse({'success': True, 'sql': model_edit.model_sql})
    except ModelEdit.DoesNotExist:
        # Return original from file
        lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
        if lesson:
            dbt_manager = DBTManager(request.user, lesson)
            sql = dbt_manager.load_original_model(model_name)
            return JsonResponse({'success': True, 'sql': sql})
        return JsonResponse({'success': False, 'message': 'Model not found'})


@login_required
@require_http_methods(["POST"])
def api_validate_lesson(request):
    """API: Validate lesson completion"""
    lesson_id = request.POST.get('lesson_id')
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)

    if not lesson:
        return JsonResponse({'success': False, 'message': 'Lesson not found'})

    storage = MotherDuckStorage()
    try:
        result = storage.validate_output(
            request.user.schema_name,
            lesson['validation']
        )

        if result['success']:
            progress, _ = LearnerProgress.objects.get_or_create(
                user=request.user, lesson_id=lesson_id
            )
            progress.lesson_progress = 100
            progress.completed_steps = progress.completed_steps or []
            if 'lesson_completed' not in progress.completed_steps:
                progress.completed_steps.append('lesson_completed')
            progress.save()

        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_http_methods(["GET"])
def api_get_project_lineage(request, project_id):
    """API: Get data model lineage for a project"""
    try:
        lineage_data = get_project_lineage(project_id)
        return JsonResponse({
            'success': True,
            'data': lineage_data
        })
    except Exception as e:
        logger.error(f"Error getting project lineage: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ========== PROJECT VIEWS ==========

def projects_view(request):
    return render(request, 'additional/projects.html')

# ========== BLOG VIEWS ==========

def blogs_view(request):
    """Landing page view"""
    # Redirect to dashboard if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'additional/blogs.html')