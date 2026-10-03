import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from .models import Task

def payload(request):
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("请求必须是合法JSON") from error
    if not isinstance(body, dict):
        raise ValueError("请求必须是JSON对象")
    return body

def as_dict(task):
    return {"id": task.id, "title": task.title, "done": task.done}

@require_http_methods(["GET"])
@ensure_csrf_cookie
def index(request):
    return render(request, "tasks/index.html")

@require_http_methods(["GET"])
def health(request):
    return JsonResponse({"status": "ok"})

@require_http_methods(["GET", "POST"])
def tasks(request):
    if request.method == "GET":
        return JsonResponse({"tasks": [as_dict(t) for t in Task.objects.all()]})
    try:
        title = payload(request).get("title")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            raise ValueError("任务名称须为1到120个字符")
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(as_dict(Task.objects.create(title=title.strip())), status=201)

@require_http_methods(["PATCH", "DELETE"])
def task_detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return JsonResponse({"error": "任务不存在"}, status=404)
    if request.method == "DELETE":
        task.delete()
        return JsonResponse({"deleted": task_id})
    try:
        done = payload(request).get("done")
        if type(done) is not bool:
            raise ValueError("done必须是布尔值")
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    task.done = done
    task.save(update_fields=["done"])
    return JsonResponse(as_dict(task))
