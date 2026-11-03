from django.db import models
from django.contrib.auth.models import User

# 1. Teacher Table (टीचर्स का डेटा)
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=100)
    assigned_class = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="Active")

    def __str__(self):
        return f"{self.user.first_name} ({self.subject})"

# 2. Student Table (स्टूडेंट्स का डेटा)
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    roll_number = models.CharField(max_length=20, unique=True)
    current_class = models.CharField(max_length=50)
    course = models.CharField(max_length=100, blank=True, default="")
    year = models.CharField(max_length=30, blank=True, default="")
    status = models.CharField(max_length=20, default="Active")

    def __str__(self):
        return f"{self.user.first_name} ({self.student_id})"

# 3. Parent Table (पैरेंट्स का डेटा जो स्टूडेंट से लिंक होगा)
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent_id = models.CharField(max_length=20, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=15)
    relation = models.CharField(max_length=30, blank=True, default="")
    status = models.CharField(max_length=20, default="Verified")

    def __str__(self):
        return f"Parent of {self.student.user.first_name}"
