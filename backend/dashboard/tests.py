import json

from django.test import Client, TestCase
from django.contrib.auth.models import User

from .models import Parent, Student, Teacher


class RecordsApiTests(TestCase):
	def setUp(self):
		self.staff = User.objects.create_user(username="staff", password="test-pass", is_staff=True)
		self.client.force_login(self.staff)

	def request_json(self, method, url, payload=None):
		return getattr(self.client, method)(
			url,
			data=json.dumps(payload) if payload is not None else None,
			content_type="application/json",
		)

	def test_student_create_update_and_delete(self):
		payload = {"name": "Aarav Sharma", "id": "STU-1", "course": "BCA",
				   "year": "1st Year", "status": "Active",
				   "password": "Copper!Lantern-4827"}
		response = self.request_json("post", "/api/students/", payload)
		self.assertEqual(response.status_code, 201)
		student_id = response.json()["pk"]
		self.assertEqual(Student.objects.get(pk=student_id).user.first_name, "Aarav")

		payload["year"] = "2nd Year"
		response = self.request_json("put", f"/api/students/{student_id}/", payload)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["year"], "2nd Year")

		self.request_json("post", "/api/parents/", {
			"name": "Suresh Sharma", "student": "Aarav Sharma",
			"phone": "9876543210", "relation": "Father", "status": "Verified",
			"password": "Silver!Meadow-7391",
		})

		response = self.client.delete(f"/api/students/{student_id}/")
		self.assertEqual(response.status_code, 204)
		self.assertFalse(Student.objects.filter(pk=student_id).exists())
		self.assertFalse(Parent.objects.exists())
		self.assertFalse(User.objects.filter(username__startswith="parent_").exists())

	def test_teacher_and_parent_are_linked_to_users_and_students(self):
		student = self.request_json("post", "/api/students/", {
			"name": "Aarav Sharma", "id": "STU-2", "course": "BCA",
			"year": "1st Year", "status": "Active",
			"password": "Copper!Lantern-4827",
		}).json()
		teacher_response = self.request_json("post", "/api/teachers/", {
			"name": "Dr. Amit Verma", "id": "TCH-1", "department": "Science",
			"email": "amit@example.com", "status": "Active", "password": "Teacher-Strong-2026!",
		})
		self.assertEqual(teacher_response.status_code, 201)
		self.assertEqual(Teacher.objects.get().user.email, "amit@example.com")
		self.assertTrue(Teacher.objects.get().user.check_password("Teacher-Strong-2026!"))

		parent_response = self.request_json("post", "/api/parents/", {
			"name": "Suresh Sharma", "student": student["name"],
			"phone": "9876543210", "relation": "Father", "status": "Verified",
			"password": "Silver!Meadow-7391",
		})
		self.assertEqual(parent_response.status_code, 201)
		self.assertEqual(Parent.objects.get().student.student_id, "STU-2")
		self.assertIn("id", parent_response.json())
		self.assertTrue(Parent.objects.get().user.check_password("Silver!Meadow-7391"))

	def test_student_and_parent_can_sign_in_to_their_own_portals(self):
		student_response = self.request_json("post", "/api/students/", {
			"name": "Aarav Sharma", "id": "STU-PORTAL", "course": "BCA",
			"year": "1st Year", "status": "Active",
			"password": "Copper!Lantern-4827",
		})
		self.assertEqual(student_response.status_code, 201)
		parent_response = self.request_json("post", "/api/parents/", {
			"name": "Suresh Sharma", "student": student_response.json()["name"],
			"phone": "9876543210", "relation": "Father", "status": "Verified",
			"password": "Silver!Meadow-7391",
		})
		self.assertEqual(parent_response.status_code, 201)

		self.client.logout()
		response = self.client.post("/", {
			"username": "STU-PORTAL", "password": "Copper!Lantern-4827",
		})
		self.assertRedirects(response, "/student/")
		self.assertContains(self.client.get("/student/"), "STU-PORTAL")
		self.assertEqual(self.client.get("/api/students/").status_code, 401)

		self.client.post("/logout/")
		response = self.client.post("/", {
			"username": parent_response.json()["id"], "password": "Silver!Meadow-7391",
		})
		self.assertRedirects(response, "/parent/")
		self.assertContains(self.client.get("/parent/"), "Aarav Sharma")
		self.assertContains(self.client.get("/parent/"), "STU-PORTAL")
		self.assertEqual(self.client.get("/api/parents/").status_code, 401)

	def test_invalid_payload_returns_validation_error(self):
		response = self.request_json("post", "/api/students/", {"name": "Incomplete"})
		self.assertEqual(response.status_code, 400)
		self.assertIn("error", response.json())

	def test_api_requires_staff_login(self):
		self.client.logout()
		response = self.client.get("/api/students/")
		self.assertEqual(response.status_code, 401)

	def test_api_responses_are_not_cached(self):
		response = self.client.get("/api/students/")
		self.assertIn("no-store", response.headers["Cache-Control"])

	def test_homepage_renders_frontend_assets(self):
		response = self.client.get("/")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "/static/style.css")
		self.assertContains(response, "/static/script.js")

	def test_anonymous_homepage_shows_frontend_login(self):
		self.client.logout()
		response = self.client.get("/")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Username, account ID, or teacher email")
		self.assertNotContains(response, "Dashboard Overview")
		self.assertIn("no-store", response.headers["Cache-Control"])

	def test_teacher_registration_password_and_teacher_id_login_work_end_to_end(self):
		payload = {
			"name": "Nisha Teacher", "id": "TCH-LOGIN", "department": "Science",
			"email": "nisha@example.com", "status": "Active",
		}
		response = self.request_json("post", "/api/teachers/", payload)
		self.assertEqual(response.status_code, 400)
		self.assertIn("password", response.json()["error"])

		payload["password"] = "Teacher-Strong-2026!"
		response = self.request_json("post", "/api/teachers/", payload)
		self.assertEqual(response.status_code, 201)
		self.assertNotIn("password", response.json())
		teacher = Teacher.objects.get(teacher_id="TCH-LOGIN")
		self.assertTrue(teacher.user.check_password(payload["password"]))

		self.client.logout()
		response = self.client.post("/", {
			"username": "TCH-LOGIN",
			"password": payload["password"],
		})
		self.assertRedirects(response, "/teacher/")
		portal = self.client.get("/teacher/")
		self.assertContains(portal, "Nisha Teacher")
		self.assertContains(portal, "TCH-LOGIN")
		self.assertEqual(self.client.get("/api/teachers/").status_code, 401)

		self.client.post("/logout/")
		response = self.client.post("/", {
			"username": "NISHA@example.com",
			"password": payload["password"],
		})
		self.assertRedirects(response, "/teacher/")

	def test_frontend_login_and_logout_require_csrf_tokens(self):
		self.staff.set_password("valid-password")
		self.staff.save()
		client = Client(enforce_csrf_checks=True)

		client.get("/")
		csrf_token = client.cookies["csrftoken"].value
		response = client.post("/", {
			"username": self.staff.username,
			"password": "valid-password",
		}, HTTP_X_CSRFTOKEN=csrf_token)
		self.assertRedirects(response, "/")
		self.assertContains(client.get("/"), "Dashboard Overview")

		self.assertEqual(client.post("/logout/").status_code, 403)
		csrf_token = client.cookies["csrftoken"].value
		response = client.post("/logout/", HTTP_X_CSRFTOKEN=csrf_token)
		self.assertRedirects(response, "/")
		self.assertContains(client.get("/"), "Username, account ID, or teacher email")

	def test_frontend_login_rejects_non_staff_users(self):
		self.client.logout()
		regular_user = User.objects.create_user(username="student-user", password="valid-password")
		response = self.client.post("/", {
			"username": regular_user.username,
			"password": "valid-password",
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "does not have dashboard access")
		self.assertFalse(response.wsgi_request.user.is_authenticated)

	def test_frontend_login_and_logout_do_not_use_admin_login(self):
		self.client.logout()
		self.staff.set_password("valid-password")
		self.staff.save()

		response = self.client.post("/", {
			"username": self.staff.username,
			"password": "valid-password",
		})
		self.assertRedirects(response, "/")
		self.assertTrue(self.client.get("/").wsgi_request.user.is_staff)

		response = self.client.post("/logout/")
		self.assertRedirects(response, "/")
		logged_out_home = self.client.get("/")
		self.assertContains(logged_out_home, "Username, account ID, or teacher email")
		self.assertNotContains(logged_out_home, "Dashboard Overview")
		self.assertEqual(self.client.get("/logout/").status_code, 405)
		self.assertEqual(self.client.get("/admin/login/").status_code, 200)
