from django.test import TestCase, Client
from .models import Task

class TaskFlowTests(TestCase):
    def test_complete_lifecycle(self):
        created = self.client.post("/tasks", {"title": "实验"}, content_type="application/json")
        self.assertEqual(created.status_code, 201)
        task_id = created.json()["id"]
        self.assertEqual(self.client.get("/tasks").json()["tasks"][0]["title"], "实验")
        result = self.client.patch(f"/tasks/{task_id}", {"done": True}, content_type="application/json")
        self.assertIs(result.json()["done"], True)
        self.assertTrue(Task.objects.get(pk=task_id).done)
        self.assertEqual(self.client.delete(f"/tasks/{task_id}").status_code, 200)
        self.assertEqual(self.client.get("/tasks").json()["tasks"], [])

    def test_bad_inputs_do_not_write(self):
        for body in [{"title": " "}, {"title": 7}, {"title": "x"*121}, []]:
            self.assertEqual(self.client.post("/tasks", body, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/tasks", "{bad", content_type="application/json").status_code, 400)
        self.assertEqual(Task.objects.count(), 0)

    def test_missing_and_boolean_validation(self):
        self.assertEqual(self.client.delete("/tasks/999").status_code, 404)
        task = Task.objects.create(title="阅读")
        for value in [1, "false", None]:
            self.assertEqual(self.client.patch(f"/tasks/{task.id}", {"done": value}, content_type="application/json").status_code, 400)
        task.refresh_from_db()
        self.assertFalse(task.done)

    def test_csrf_and_page(self):
        browser = Client(enforce_csrf_checks=True)
        self.assertEqual(browser.post("/tasks", {"title": "阅读"}, content_type="application/json").status_code, 403)
        page = browser.get("/")
        self.assertContains(page, "TaskFlow")
        token = browser.cookies["csrftoken"].value
        self.assertEqual(browser.post("/tasks", {"title": "阅读"}, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 201)
        self.assertEqual(browser.get("/health").json(), {"status": "ok"})
