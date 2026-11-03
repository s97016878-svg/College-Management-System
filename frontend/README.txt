COLLEGE MANAGEMENT SYSTEM

Technology:
- HTML5
- CSS3
- Vanilla JavaScript
- Django 5.2

How to run on Windows (PowerShell):
1. From the backend folder, install dependencies with `py -m pip install -r requirements.txt`.
2. Apply database changes with `py manage.py migrate`.
3. Create an administrator with `py manage.py createsuperuser`.
4. Start Django with `py manage.py runserver`.
5. Open http://127.0.0.1:8000 and sign in with a staff account.

Features:
- Professional responsive dashboard
- Students, Teachers, Parents, Courses, Admissions, Attendance, Examinations, Results, Fees, Notices and Settings sections
- Student, teacher and parent records load from and save to the SQLite database
- Staff can set initial passwords for students, teachers, and parents; they can update a password while editing an account
- Teachers, students, and parents sign in with their account ID and password and see their own role-specific portal; teachers may also use their registered email
- Parent records show their generated Parent ID for sign-in
- Staff-only access to saved records
- Remaining sections use sample records in the browser session
- Download a sample dashboard report as CSV
- Responsive sidebar for mobile screens

The frontend is served by Django so its API requests and session authentication use the same origin. Staff sign in to the dashboard; teachers sign in to their separate profile page. Both roles sign out to the frontend login page. Django's separate administration site remains available directly at http://127.0.0.1:8000/admin/.
