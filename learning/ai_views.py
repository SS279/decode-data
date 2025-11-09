"""
AI Agent views for dbt learning assistance
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import logging
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)


@login_required
def ai_assistant(request):
    """AI Assistant page"""
    context = {
        'user': request.user,
    }
    return render(request, 'learning/ai_assistant.html', context)


@login_required
@require_http_methods(["POST"])
def ai_chat(request):
    """Handle AI chat requests"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Initialize Groq client
        groq_api_key = settings.GROQ_API_KEY
        if not groq_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Groq API key not configured'
            }, status=500)
        
        client = Groq(api_key=groq_api_key)
        
        # Build conversation messages
        messages = [
            {
                "role": "system",
                "content": """You are an expert dbt (data build tool) instructor and assistant. Your role is to:

1. Help learners understand dbt concepts, best practices, and SQL transformations
2. Explain dbt models, tests, documentation, and project structure
3. Provide clear, beginner-friendly explanations with examples
4. Analyze SQL code and suggest improvements
5. Answer questions about data modeling, transformations, and dbt workflows
6. Guide users through debugging issues with their dbt models

Key topics you cover:
- dbt fundamentals (models, sources, seeds, snapshots)
- SQL transformations and Jinja templating
- Testing and documentation
- Project structure and configuration
- Best practices for data modeling
- Troubleshooting common errors
- MotherDuck/DuckDB specific features

Always be:
- Clear and concise
- Educational and supportive
- Practical with code examples
- Encouraging for beginners

When analyzing SQL code, provide:
- Explanation of what the code does
- Best practice suggestions
- Common pitfalls to avoid
- Optimization tips when relevant"""
            }
        ]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Groq API
        response = client.chat.completions.create(
            model="groq/compound",
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            top_p=0.9,
        )
        
        ai_response = response.choices[0].message.content
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'message': user_message
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your request'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def analyze_model(request):
    """Analyze a dbt model and provide insights"""
    try:
        data = json.loads(request.body)
        model_sql = data.get('sql', '').strip()
        model_name = data.get('model_name', 'model')
        
        if not model_sql:
            return JsonResponse({
                'success': False,
                'error': 'SQL code cannot be empty'
            }, status=400)
        
        # Initialize Groq client
        groq_api_key = settings.GROQ_API_KEY
        if not groq_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Groq API key not configured'
            }, status=500)
        
        client = Groq(api_key=groq_api_key)
        
        # Create analysis prompt
        prompt = f"""Analyze this dbt model and provide insights:

Model Name: {model_name}

SQL Code:
```sql
{model_sql}
```

Please provide:
1. **Summary**: What does this model do?
2. **Best Practices**: Are there any dbt best practices being followed or missed?
3. **Suggestions**: How could this model be improved?
4. **Potential Issues**: Any potential problems or anti-patterns?
5. **Learning Points**: Key concepts demonstrated in this model

Be specific and educational in your feedback."""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert dbt instructor analyzing SQL models. Provide clear, educational feedback."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            top_p=0.9,
        )
        
        analysis = response.choices[0].message.content
        
        return JsonResponse({
            'success': True,
            'analysis': analysis,
            'model_name': model_name
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Model analysis error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while analyzing the model'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def generate_test(request):
    """Generate dbt tests for a model"""
    try:
        data = json.loads(request.body)
        model_sql = data.get('sql', '').strip()
        model_name = data.get('model_name', 'model')
        
        if not model_sql:
            return JsonResponse({
                'success': False,
                'error': 'SQL code cannot be empty'
            }, status=400)
        
        # Initialize Groq client
        groq_api_key = settings.GROQ_API_KEY
        if not groq_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Groq API key not configured'
            }, status=500)
        
        client = Groq(api_key=groq_api_key)
        
        # Create test generation prompt
        prompt = f"""Based on this dbt model, suggest appropriate dbt tests:

Model Name: {model_name}

SQL Code:
```sql
{model_sql}
```

Generate a YAML configuration with appropriate tests. Include:
1. not_null tests for important columns
2. unique tests where appropriate
3. relationships tests if there are foreign keys
4. accepted_values tests if applicable
5. Custom tests if needed

Provide the YAML in proper dbt schema.yml format."""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at writing dbt tests. Generate appropriate test configurations in YAML format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            temperature=0.5,
            max_tokens=1500,
            top_p=0.9,
        )
        
        tests = response.choices[0].message.content
        
        return JsonResponse({
            'success': True,
            'tests': tests,
            'model_name': model_name
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Test generation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while generating tests'
        }, status=500)