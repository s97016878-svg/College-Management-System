import json
from uuid import uuid4

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import Parent, Student, Teacher


@never_cache
@ensure_csrf_cookie
def home(request):
	login_data = request.POST.copy() if request.method == "POST" else None
	if login_data is not None:
		identifier = login_data.get("username", "").strip()
		if identifier and not User.objects.filter(username=identifier).exists():
			matches = []
			for model, field in (
				(Teacher, "teacher_id"),
				(Student, "student_id"),
				(Parent, "parent_id"),
			):
				matches.extend(model.objects.select_related("user").filter(**{f"{field}__iexact": identifier}))
			matches.extend(Teacher.objects.select_related("user").filter(user__email__iexact=identifier))
			if len(matches) == 1:
				login_data["username"] = matches[0].user.username
	form = AuthenticationForm(request, data=login_data)
	if request.method == "POST":
		if form.is_valid():
			user = form.get_user()
			if user.is_staff:
				login(request, user)
				return redirect("home")
			if Teacher.objects.filter(user=user).exists():
				login(request, user)
				return redirect("teacher-portal")
			if Student.objects.filter(user=user).exists():
				login(request, user)
				return redirect("student-portal")
			if Parent.objects.filter(user=user).exists():
				login(request, user)
				return redirect("parent-portal")
			form.add_error(None, "This account does not have dashboard access.")
	elif request.user.is_authenticated and request.user.is_staff:
		admin_name = request.user.get_full_name() or request.user.username
		return render(request, "index.html", {"admin_name": admin_name})
	elif request.user.is_authenticated and Teacher.objects.filter(user=request.user).exists():
		return redirect("teacher-portal")
	elif request.user.is_authenticated and Student.objects.filter(user=request.user).exists():
		return redirect("student-portal")
	elif request.user.is_authenticated and Parent.objects.filter(user=request.user).exists():
		return redirect("parent-portal")
	elif request.user.is_authenticated:
		form.add_error(None, "This account does not have dashboard access.")
	return render(request, "login.html", {"form": form})


@never_cache
def teacher_portal(request):
	if not request.user.is_authenticated:
		return redirect("home")
	if request.user.is_staff:
		return redirect("home")
	teacher = Teacher.objects.select_related("user").filter(user=request.user).first()
	if teacher is None:
		return HttpResponseForbidden("A teacher account is required.")
	return render(request, "teacher.html", {"teacher": teacher})


@never_cache
def student_portal(request):
	if not request.user.is_authenticated:
		return redirect("home")
	if request.user.is_staff:
		return redirect("home")
	student = Student.objects.select_related("user").filter(user=request.user).first()
	if student is None:
		return HttpResponseForbidden("A student account is required.")
	return render(request, "account.html", {"account_type": "Student", "account": student})


@never_cache
def parent_portal(request):
	if not request.user.is_authenticated:
		return redirect("home")
	if request.user.is_staff:
		return redirect("home")
	parent = Parent.objects.select_related("user", "student__user").filter(user=request.user).first()
	if parent is None:
		return HttpResponseForbidden("A parent account is required.")
	return render(request, "account.html", {"account_type": "Parent", "account": parent})


@require_POST
def frontend_logout(request):
	logout(request)
	return redirect("home")


def _record_data(model, record):
	user = record.user
	name = f"{user.first_name} {user.last_name}".strip()
	if model is Student:
		return {"pk": record.pk, "name": name, "id": record.student_id,
				"course": record.course or record.current_class, "year": record.year,
				"status": record.status}
	if model is Teacher:
		return {"pk": record.pk, "name": name, "id": record.teacher_id,
				"department": record.subject, "email": user.email,
				"status": record.status}
	return {"pk": record.pk, "name": name,
			"id": record.parent_id,
			"student": f"{record.student.user.first_name} {record.student.user.last_name}".strip(),
			"phone": record.contact_number, "relation": record.relation,
			"status": record.status}


def _payload(request):
	try:
		payload = json.loads(request.body)
	except (json.JSONDecodeError, UnicodeDecodeError):
		return None
	return payload if isinstance(payload, dict) else None


def _name_parts(name):
	parts = name.strip().split(maxsplit=1)
	return parts[0], parts[1] if len(parts) > 1 else ""


def _save_record(model, payload, record=None):
	required = {
		Student: ("name", "id", "course", "year", "status"),
		Teacher: ("name", "id", "department", "email", "status"),
		Parent: ("name", "student", "phone", "relation", "status"),
	}[model]
	missing = [key for key in required if not str(payload.get(key, "")).strip()]
	if model in (Student, Teacher, Parent) and record is None and not payload.get("password"):
		missing.append("password")
	if missing:
		raise ValueError(f"Required fields: {', '.join(missing)}")

	first_name, last_name = _name_parts(payload["name"])
	identifier = payload.get("id", "")

	if model is Parent:
		student = Student.objects.filter(user__first_name=payload["student"].strip().split(maxsplit=1)[0])
		student = next((item for item in student if _record_data(Student, item)["name"] == payload["student"].strip()), None)
		if student is None:
			raise ValueError("Select a student that exists in the student directory.")
		record = record or Parent(user=User(), parent_id=f"PAR-{uuid4().hex[:12].upper()}")
		record.student = student
		record.contact_number = payload["phone"].strip()
		record.relation = payload["relation"].strip()
		record.status = payload["status"].strip()
		username = f"parent_{record.parent_id}"
	elif model is Student:
		record = record or Student(user=User(), student_id=identifier, roll_number=identifier)
		record.student_id = identifier.strip()
		record.roll_number = record.student_id
		record.current_class = payload["course"].strip()
		record.course = payload["course"].strip()
		record.year = payload["year"].strip()
		record.status = payload["status"].strip()
		username = f"student_{record.student_id}"
	else:
		record = record or Teacher(user=User(), teacher_id=identifier)
		record.teacher_id = identifier.strip()
		record.subject = payload["department"].strip()
		record.assigned_class = record.assigned_class or ""
		record.status = payload["status"].strip()
		username = f"teacher_{record.teacher_id}"

	record.user.username = username
	record.user.first_name = first_name
	record.user.last_name = last_name
	record.user.email = payload.get("email", "").strip() if model is Teacher else ""
	password = payload.get("password", "")
	if password:
		try:
			validate_password(password, record.user)
		except ValidationError as error:
			raise ValueError(" ".join(error.messages)) from error
		record.user.set_password(password)
	elif record.user.pk is None:
		record.user.set_unusable_password()
	record.user.save()
	record.save()
	return record


@never_cache
def records(request, resource, pk=None):
	if not request.user.is_authenticated or not request.user.is_staff:
		return JsonResponse({"error": "A staff login is required."}, status=401)

	models = {"students": Student, "teachers": Teacher, "parents": Parent}
	model = models.get(resource)
	if model is None:
		return JsonResponse({"error": "Unknown resource."}, status=404)

	if pk is not None:
		record = get_object_or_404(model, pk=pk)
		if request.method == "GET":
			return JsonResponse(_record_data(model, record))
		if request.method == "DELETE":
			with transaction.atomic():
				user = record.user
				if model is Student:
					for parent in Parent.objects.filter(student=record).select_related("user"):
						parent.user.delete()
				record.delete()
				user.delete()
			return JsonResponse({}, status=204)
		if request.method != "PUT":
			return JsonResponse({"error": "Method not allowed."}, status=405)
	elif request.method == "GET":
		return JsonResponse([_record_data(model, record) for record in model.objects.select_related("user").all()], safe=False)
	elif request.method != "POST":
		return JsonResponse({"error": "Method not allowed."}, status=405)

	payload = _payload(request)
	if payload is None:
		return JsonResponse({"error": "Expected a JSON object."}, status=400)
	try:
		with transaction.atomic():
			saved = _save_record(model, payload, record if pk is not None else None)
	except ValueError as error:
		return JsonResponse({"error": str(error)}, status=400)
	except IntegrityError:
		return JsonResponse({"error": "That ID is already in use."}, status=400)
	return JsonResponse(_record_data(model, saved), status=201 if pk is None else 200)
