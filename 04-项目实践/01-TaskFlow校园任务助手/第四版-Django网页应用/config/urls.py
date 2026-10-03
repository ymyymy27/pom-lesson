from django.urls import path
from tasks import views
urlpatterns = [path("", views.index), path("health", views.health),
               path("tasks", views.tasks), path("tasks/<int:task_id>", views.task_detail)]
