
**General Notes**

An `onlinecourse` app has already been provided in this repo upon which you will be adding a new assesement feature.

- If you want to develop the final project on Theia hosted by [IBM Developer Skills Network](https://labs.cognitiveclass.ai/), you will need to create the same project structure on Theia workspace and save it everytime you close the browser
- Or you could develop the final project locally by setting up your own Python runtime and IDE
- Hints for the final project are left on source code files
- You may choose any cloud platform for deployment (default is IBM Cloud Foundry)
- Depends on your deployment, you may choose any SQL database Django supported such as SQLite3, PostgreSQL, and MySQL (default is SQLite3)

**ER Diagram**
For your reference, we have prepared the ER diagram design for the new assesement feature.

![Onlinecourse ER Diagram](https://github.com/ibm-developer-skills-network/final-cloud-app-with-database/blob/master/static/media/course_images/onlinecourse_app_er.png)

## Exam assessment implementation

The course page lists the lessons and offers an exam to enrolled learners.
An attempt is saved under the learner's enrollment and scored by question
weight. A question earns its points when the selected choices match its
correct answers exactly. A score above 80% passes. The result displays the
learner's selections and the correct choices.

### Run locally

Use Python 3.10 or later.

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

The course list is at http://127.0.0.1:8000/onlinecourse/ and the Django
administration page is at http://127.0.0.1:8000/admin/. Sign in to the
course with the demo learner account, `demo-learner`, and the password
you set when you ran `seed_demo`.

### Assessment files

| Task | Required file |
| --- | --- |
| 1 | `onlinecourse/models.py` |
| 2 | `onlinecourse/admin.py` |
| 3 | `screenshots/03-admin-site.png` |
| 4 | `onlinecourse/templates/onlinecourse/course_details_bootstrap.html` |
| 5 | `onlinecourse/views.py` |
| 6 | `onlinecourse/urls.py` |
| 7 | `screenshots/07-final.png` |
