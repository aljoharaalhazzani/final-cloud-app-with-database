import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.decorators.http import require_POST

from .models import Choice, Course, Enrollment, Submission

logger = logging.getLogger(__name__)
LOGIN_URL = "onlinecourse:login"


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except User.DoesNotExist:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lessons"] = self.object.lesson_set.order_by("order", "pk")
        context["questions"] = self.object.question_set.prefetch_related("choice_set").order_by("pk")
        context["is_enrolled"] = check_if_enrolled(self.request.user, self.object)
        return context


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))



@login_required(login_url=LOGIN_URL)
@require_POST
@transaction.atomic
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if enrollment is None:
        return HttpResponseForbidden("Enroll in the course before taking the exam.")
    try:
        selected_ids = {int(choice_id) for choice_id in request.POST.getlist("choices")}
    except ValueError:
        return HttpResponseBadRequest("Invalid answer selection.")

    choices = list(Choice.objects.filter(question__course=course, pk__in=selected_ids))
    if len(choices) != len(selected_ids):
        return HttpResponseBadRequest("An answer does not belong to this course.")

    submission = Submission.objects.create(enrollment=enrollment)
    submission.choices.set(choices)
    return redirect("onlinecourse:show_exam_result", course_id=course.pk, submission_id=submission.pk)


@login_required(login_url=LOGIN_URL)
def show_exam_result(request, course_id, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related("enrollment__course"),
        pk=submission_id,
        enrollment__course_id=course_id,
        enrollment__user=request.user,
    )
    course = submission.enrollment.course
    selected_ids = set(submission.choices.values_list("pk", flat=True))
    questions = course.question_set.prefetch_related("choice_set").order_by("pk")

    results = []
    total_points = earned_points = 0
    for question in questions:
        total_points += question.grade
        is_correct = question.is_get_score(selected_ids)
        if is_correct:
            earned_points += question.grade
        results.append({
            "question": question,
            "is_correct": is_correct,
            "choices": [
                {"choice": choice, "selected": choice.pk in selected_ids}
                for choice in question.choice_set.all()
            ],
        })

    grade = round(100 * earned_points / total_points) if total_points else 0
    return render(request, "onlinecourse/exam_result_bootstrap.html", {
        "course": course,
        "grade": grade,
        "passed": total_points > 0 and earned_points * 100 > total_points * 80,
        "results": results,
    })
