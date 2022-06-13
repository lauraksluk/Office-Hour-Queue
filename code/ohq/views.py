from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
import json
from ohq.models import Profile, Queue, Question, InstructorStatus, Announcement, PinnedQueue
from ohq.forms import LoginForm, RegisterForm, UploadFileForm
from django.utils import timezone
from django.shortcuts import get_object_or_404


def base(request):
    if request.user.username:
        return redirect(reverse('courses'))
    return render(request, 'ohq/base.html', {})


def oauth_page(request):
    return redirect('/oauth/login/google-oauth2/')


def login_page(request):
    context = {}
    if request.method == 'GET':
        if request.user.username:
            return redirect(reverse('courses'))
        context['form'] = LoginForm()
        return render(request, 'ohq/login.html', context)

    form = LoginForm(request.POST)
    context['form'] = form

    if not form.is_valid():
        return render(request, 'ohq/login.html', context)

    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])
    login(request, new_user)
    # return render(request, "ohq/login.html", context)
    return redirect(reverse('courses'))


def register_page(request):
    context = {}
    if request.method == 'GET':
        if request.user.username:
            return redirect(reverse('courses'))
        context['form'] = RegisterForm()
        return render(request, 'ohq/register.html', context)

    form = RegisterForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, 'ohq/register.html', context)

    new_user = User.objects.create_user(username=form.cleaned_data['username'],
                                        password=form.cleaned_data['password'],
                                        email=form.cleaned_data['email'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'])
    new_user.save()
    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])

    new_profile = Profile(linked_user=new_user)
    new_profile.save()

    login(request, new_user)
    return redirect(reverse('courses'))


@login_required
def manage_page(request):
    context = {'form': UploadFileForm()}
    return render(request, 'ohq/manage.html', context)


@login_required
def upload_file_action(request):
    error_message = ""

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            errors = []
            added = set()

            for line in form.cleaned_data['file']:
                line = line.decode("utf-8")
                parts = line.strip().split(',')
                if len(parts) != 2:
                    errors.append(line)
                    continue

                queue_name, email = tuple(parts)
                if len(queue_name) >= 100:
                    errors.append(line)
                    continue
                queues = Queue.objects.filter(name__exact=queue_name)

                if queues.count() == 0:
                    new_queue = Queue(name=queue_name, enabled=True)
                    new_queue.save()

                this_queue_id = Queue.objects.filter(name__exact=queue_name)[0].id

                instructors = User.objects.filter(email__exact=email)
                if instructors.count() == 0:
                    errors.append(line)
                    continue

                for i in range(instructors.count()):
                    this_instructor_id = instructors[i].id

                    # de-duplicate
                    if InstructorStatus.objects.filter(instructor_id=this_instructor_id,
                                                       queue_id=this_queue_id).count() > 0:
                        continue

                    new_instructor_status = InstructorStatus(
                        instructor_id=this_instructor_id,
                        queue_id=this_queue_id,
                        online=True,
                    )
                    new_instructor_status.save()
                    added.add((queue_name, email))

            # print(added)
            error_message = "Error on line(s):\n" + "\n".join(errors) if errors else "Upload successful"

    else:
        form = UploadFileForm()
    return render(request, 'ohq/manage.html', {'form': form, 'error_message': error_message})


@login_required
def courses_page(request):
    pinned_course = PinnedQueue.objects.filter(
        user_id__exact=request.user.id
    )

    pinned_course_list = []
    if pinned_course.count() > 0:
        pinned_course_list = pinned_course[0].pinned_course_list.all()

    unpinned_course_list = []
    for course in Queue.objects.all():
        if course not in pinned_course_list:
            unpinned_course_list.append(course)

    # return render(request, 'ohq/courses.html', {'courses': Queue.objects.all()})
    return render(request, 'ohq/courses.html',
                  {'unpinned_course': unpinned_course_list, 'pinned_course': pinned_course_list})


# redirect to student or instructor page based on role
@login_required
def role_redirect_action(request, queue_id):
    if not check_valid_queue_id(queue_id):
        raise Http404

    if check_instructor(queue_id, request.user.id):
        return redirect(reverse('instructor', args=(queue_id,)))
    else:
        return redirect(reverse('home', args=(queue_id,)))


@login_required
def instructor_action(request, queue_id):
    if not check_valid_queue_id(queue_id):
        raise Http404
    if not check_instructor(queue_id, request.user.id):
        return HttpResponse('Unauthorized', status=401)

    context = {
        "this_queue_id": queue_id, "this_queue_name": Queue.objects.filter(id=queue_id)[0].name
    }

    return render(request, "ohq/instructor.html", context)


@login_required
def student_action(request, queue_id):
    if not check_valid_queue_id(queue_id):
        raise Http404

    context = {
        "this_queue_id": queue_id, "this_queue_name": Queue.objects.filter(id=queue_id)[0].name
    }

    questions = Question.objects.filter(
        queue_id__exact=queue_id,
        student=request.user,
        status__in=["waiting", "processing"],
    ).order_by("-creation_time")

    if questions.count() == 0:
        return render(request, "ohq/student.html", context)  # html provides empty default value
    else:
        context["current_question"] = questions[0]
        return render(request, "ohq/student.html", context)


def waiting_questions_json(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.GET["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    # for the instructor view, we expose the details of each question
    waiting_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="waiting",
    ).order_by("creation_time")

    result = []
    for q in waiting_questions:
        result.append({
            "id": str(q.id),
            "student_id": str(q.student.id),
            "student_name": f"{q.student.first_name} {q.student.last_name}",
            "student_email": q.student.email,
            "content": q.content,
            "location": q.location,
            "question_type": q.question_type
        })

    response = json.dumps(result)
    return HttpResponse(response, content_type='application/json')


def waiting_questions_count_json(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.GET["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    # for the student view, we only expose the number of waiting questions in queue,
    # instead of the details of each question
    waiting_questions_count = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="waiting",
    ).count()

    result = {
        "waiting_questions_count": waiting_questions_count,
    }

    response = json.dumps(result)
    return HttpResponse(response, content_type='application/json')


def remove_question(request, queue_id):
    context = {
        "this_queue_id": queue_id,
    }
    if request.method == 'GET':
        return render(request, 'ohq/student.html', context)

    question_to_remove = Question.objects.filter(
        queue_id__exact=queue_id,
        status="waiting",
        student=request.user,
    )

    if question_to_remove.count() > 0:
        question_to_remove[0].delete()

    return redirect(reverse('home', args=(queue_id,)))


def add_question(request, queue_id):
    # print("enter add question in the view.py")
    context = {
        "this_queue_id": queue_id,
    }

    if request.method == 'GET':
        # print("enter get method")
        return render(request, 'ohq/student.html', context)

    # Adds the new item to the database if the request parameter is present
    if 'location' not in request.POST or not request.POST['location']:
        context['error'] = 'You must enter an location to add.'
        return render(request, 'ohq/student.html', context)
    if 'content' not in request.POST or not request.POST['content']:
        context['error'] = 'You must enter a content to add.'
        return render(request, 'ohq/student.html', context)
    if 'question_type' not in request.POST or not request.POST['question_type']:
        context['error'] = 'You must enter a question type to add.'
        return render(request, 'ohq/student.html', context)

    existing_questions_for_student = Question.objects.filter(
        queue_id__exact=queue_id,
        student=request.user,
        status__in=["waiting", "processing"],
    ).order_by('-creation_time')

    queues = Queue.objects.filter(id=queue_id)
    if queues.count() == 0:
        # swallow failure
        return redirect(reverse('home', args=(queue_id,)))

    if existing_questions_for_student.count() == 0:
        # user is only allowed to add a new question if the queue is open
        if queues[0].enabled:
            new_question = Question(queue_id=queue_id, content=request.POST['content'],
                                    location=request.POST['location'],
                                    question_type=request.POST['question_type'],
                                    student=request.user, status="waiting",
                                    creation_time=timezone.now())
            new_question.save()
    else:
        # user can update an existing question regardless of whether the queue is open
        existing_question = existing_questions_for_student[0]
        existing_question.content = request.POST['content']
        existing_question.location = request.POST['location']
        existing_question.question_type = request.POST['question_type']
        existing_question.save()

    return redirect(reverse('home', args=(queue_id,)))


def student_current_position_json(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.GET["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    student_curr_position = -2
    all_waiting_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="waiting",
    ).order_by("creation_time")

    all_processed_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="processing",
    ).order_by("-processed_time")

    result = {}

    if len(all_processed_questions) > 0 and request.user.id == all_processed_questions[0].student.id:
        student_curr_position = 0
        result["assigned_instructor"] = all_processed_questions[0].assigned_instructor.first_name + " " + \
                                        all_processed_questions[0].assigned_instructor.last_name
    elif len(all_waiting_questions) == 0:
        student_curr_position = -1
    else:
        index = 0
        while index < len(all_waiting_questions):
            question = all_waiting_questions[index]
            if question.student.id == request.user.id:
                break
            index += 1

        if index < len(all_waiting_questions):
            student_curr_position = index + 1  # 1-based index
        else:
            student_curr_position = -1

    result["student_curr_position"] = student_curr_position

    response = json.dumps(result)
    return HttpResponse(response, content_type='application/json')

def check_if_assigned(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.GET["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)
    
    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    processing_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="processing",
        assigned_instructor=request.user,
    )

    result = {}
    if len(processing_questions) != 0:
        result["assigned"] = "true"
    else:
        result["assigned"] = "false"
    
    return HttpResponse(json.dumps(result), content_type='application/json')

def assign_question_from_top_of_queue_json(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    waiting_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="waiting",
    ).order_by("creation_time")

    processing_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="processing",
        assigned_instructor=request.user,
    )

    if len(processing_questions) != 0:
        return _my_json_error_response("An instructor cannot be assigned a new question when they are helping a student.", status=401)

    if len(waiting_questions) == 0:
        result = {
            "status": "false",
        }
    else:
        top_question = waiting_questions[0]
        Question.objects.filter(id=top_question.id).update(status='processing')
        Question.objects.filter(id=top_question.id).update(processed_time=timezone.now())
        Question.objects.filter(id=top_question.id).update(assigned_instructor=request.user)

        result = {
            "status": "true",
            "id": str(top_question.id),
            "student_id": str(top_question.student.id),
            "student_name": f"{top_question.student.first_name} {top_question.student.last_name}",
            "student_email": top_question.student.email,
            "content": top_question.content,
            "location": top_question.location,
            "question_type": top_question.question_type,
        }
    response = json.dumps(result)
    return HttpResponse(response, content_type='application/json')


def assign_question_from_list(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    if 'question_id' not in request.POST or not request.POST["question_id"] or \
            not request.POST["question_id"].isdigit():
        return _my_json_error_response("request must include a valid question_id parameter", status=400)

    request_question_id = request.POST['question_id']
    waiting_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="waiting",
    ).order_by("creation_time")

    processing_questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="processing",
        assigned_instructor=request.user,
    )

    if len(processing_questions) != 0:
        return _my_json_error_response("An instructor cannot be assigned a new question when they are helping a student.", status=401)

    if (len(waiting_questions) == 0):
        result = {
            "status": "false",
        }
    else:
        requested_question = get_object_or_404(Question, id=request_question_id)
        Question.objects.filter(id=request_question_id).update(status='processing')
        Question.objects.filter(id=request_question_id).update(processed_time=timezone.now())
        Question.objects.filter(id=request_question_id).update(assigned_instructor=request.user)

        result = {
            "status": "true",
            "id": str(requested_question.id),
            "student_id": str(requested_question.student.id),
            "student_name": f"{requested_question.student.first_name} {requested_question.student.last_name}",
            "student_email": requested_question.student.email,
            "content": requested_question.content,
            "location": requested_question.location,
            "question_type": requested_question.question_type,
        }
    response = json.dumps(result)
    return HttpResponse(response, content_type='application/json')


def get_assigned_question_json(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.GET["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    questions = Question.objects.filter(
        queue_id__exact=queue_id,
        assigned_instructor=request.user,
        status__exact="processing",
    )

    result = {}
    # print("num q tht r processing is" + str(questions.count()))

    if questions.count() == 0:
        # note: this needs to be different from "false" (cannot find a new student to assign)
        result["status"] = "no_question"
    else:
        question = questions[0]
        result = {
            "status": "true",
            "id": str(question.id),
            "student_id": str(question.student.id),
            "student_name": f"{question.student.first_name} {question.student.last_name}",
            "student_email": question.student.email,
            "content": question.content,
            "location": question.location,
            "question_type": question.question_type,
        }

    response = json.dumps(result)
    return HttpResponse(response, content_type='application/json')


def set_queue_status(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    if 'end_state' not in request.POST or not request.POST["end_state"] or \
            request.POST["end_state"] not in ["true", "false"]:
        return _my_json_error_response("request must include a valid resulting_queue_state parameter", status=400)

    result_state = (request.POST["end_state"] == "true")

    queues = Queue.objects.filter(id=queue_id)
    if queues.count() == 0:
        return _my_json_error_response(f"no queue found with id={queue_id}, expected 1", status=400)

    queue = queues[0]
    queue.enabled = result_state
    queue.save()
    return HttpResponse(json.dumps({}), content_type='application/json')


def queue_status_json(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.GET["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    queues = Queue.objects.filter(id=queue_id)
    if queues.count() == 0:
        return _my_json_error_response(f"no queue found with id={queue_id}, expected 1", status=400)

    result = {
        "queue_id": queue_id,
        "queue_status": queues[0].enabled,
    }

    return HttpResponse(json.dumps(result), content_type='application/json')


def add_announcement(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    if "announcement_content" not in request.POST or not request.POST["announcement_content"]:
        return _my_json_error_response("request must include a valid announcement_content parameter", status=400)

    new_announcement = Announcement(
        poster=request.user,
        content=request.POST["announcement_content"],
        creation_time=timezone.now(),
        queue_id=queue_id,
        status="ongoing",
        type="public",
    )

    new_announcement.save()
    return HttpResponse(json.dumps({}), content_type='application/json')


def get_announcements_json(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.GET["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    announcements = Announcement.objects.filter(
        queue_id__exact=queue_id,
        status__exact="ongoing",
    ).order_by("creation_time")

    announcements_list = []
    for announcement in announcements:
        if announcement.type == "public":
            announcements_list.append({
                "announcement_id": str(announcement.id),
                "announcement_content": announcement.content,
                "announcement_creation_time": timezone.localtime(announcement.creation_time).strftime(
                    "%Y-%m-%d %H:%M:%S"),
                "announcement_poster": f"{announcement.poster.first_name} {announcement.poster.last_name}",
                "type": "announcement",
            })
        elif announcement.type == "private":
            announcements_list.append({
                "private_message_id": str(announcement.id),
                "private_message_content": announcement.content,
                "private_message_creation_time": timezone.localtime(announcement.creation_time).strftime(
                    "%Y-%m-%d %H:%M:%S"),
                "private_message_poster": f"{announcement.poster.first_name} {announcement.poster.last_name}",
                "private_message_receiver_id": announcement.receiver.id,
                "private_message_receiver_name": f"{announcement.receiver.first_name} {announcement.receiver.last_name}",
                "type": "private_message",
            })

    result = {"announcements": announcements_list, "request_user_id": request.user.id}
    response = json.dumps(result)
    return HttpResponse(response, content_type='application/json')

def instruct_remove_question(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)
    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    question_to_remove = Question.objects.filter(
        queue_id__exact=queue_id,
        assigned_instructor=request.user,
        status__exact="processing",
    )
    # print("num remove q is")
    # print(question_to_remove.count())
    if question_to_remove.count() == 0:
        return _my_json_error_response(f"this instructor is not helping any student", status=400)

    if question_to_remove.count() > 0:
        question_to_remove[0].delete()

    return HttpResponse(json.dumps({}), content_type='application/json')


def finish_current_question(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    currently_helping = Question.objects.filter(
        queue_id__exact=queue_id,
        assigned_instructor=request.user,
        status__exact="processing",
    )

    if currently_helping.count() == 0:
        return _my_json_error_response(f"this instructor is not helping any student", status=400)

    question = currently_helping[0]
    question.resolution_time = timezone.now()
    question.status = "done"
    question.save()
    return HttpResponse(json.dumps({}), content_type='application/json')


def end_office_hour_session(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    annoucements_in_session = Announcement.objects.filter(
        status__exact="ongoing",
    )
    annoucements_in_session.update(status="outdated")

    questions_in_queue = Question.objects.filter(
        status__in=["processing", "waiting"],
    )
    questions_in_queue.update(status="unresolved")
    Queue.objects.filter(id=queue_id).update(enabled=False)

    return HttpResponse(json.dumps({}), content_type='application/json')

def send_remove_reason_message(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)
    
    if "remove_reason_message_content" not in request.POST or not request.POST["remove_reason_message_content"]:
        return _my_json_error_response("request must include a valid remove_reason_message_content parameter", status=400)
    
    if "receive_student_user_id" not in request.POST or not request.POST["receive_student_user_id"] or \
        not request.POST["receive_student_user_id"].isdigit():
        return _my_json_error_response("request must include a valid receive_student_user_id parameter", status=400)
    
    new_removal_announcement = Announcement(
        poster=request.user,
        content="You have been removed from the queue. Message from instructor: " + request.POST["remove_reason_message_content"],
        creation_time=timezone.now(),
        queue_id=queue_id,
        status="ongoing",
        type="private",
        receiver_id=request.POST["receive_student_user_id"],
    )
    new_removal_announcement.save()
    return HttpResponse(json.dumps({}), content_type='application/json')


def send_private_message(request):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    try:
        queue_id = int(request.POST["queue_id"])
    except:
        return _my_json_error_response("You must include a valid queue_id parameter", status=400)

    if not check_instructor(queue_id, request.user.id):
        return _my_json_error_response("You must be an instructor", status=401)

    if "private_message_content" not in request.POST or not request.POST["private_message_content"]:
        return _my_json_error_response("request must include a valid private_message_content parameter", status=400)

    if "receive_user_id" not in request.POST or not request.POST["receive_user_id"] or \
            not request.POST["receive_user_id"].isdigit():
        return _my_json_error_response("request must include a valid receive_user_id parameter", status=400)

    new_announcement = Announcement(
        poster=request.user,
        content=request.POST["private_message_content"],
        creation_time=timezone.now(),
        queue_id=queue_id,
        status="ongoing",
        type="private",
        receiver_id=request.POST["receive_user_id"],
    )

    new_announcement.save()
    return HttpResponse(json.dumps({}), content_type='application/json')


def check_valid_queue_id(queue_id):
    return Queue.objects.filter(id=queue_id).count() > 0


def check_instructor(queue_id, user_id):
    return InstructorStatus.objects.filter(
        queue_id__exact=queue_id,
        instructor_id__exact=user_id,
    ).count() > 0


def _my_json_error_response(message, status=200):
    response_json = '{ "error": "' + message + '" }'
    return HttpResponse(response_json, content_type='application/json', status=status)


def pin_course(request, queue_id):
    user = request.user.id
    context = {
        "this_queue_id": queue_id,
    }
    if request.method == 'GET':
        return render(request, 'ohq/courses.html', context)

    user_queue = PinnedQueue.objects.filter(
        user_id__exact=request.user.id
    )

    if user_queue.count() == 0:
        pinned_queue = PinnedQueue(user=request.user)
        pinned_queue.save()
        pinned_queue.pinned_course_list.add(queue_id)
        pinned_queue.save()

    else:
        # get a set of all pinned queue ids for this user
        pinned_queue_ids = set()
        for item in user_queue[0].pinned_course_list.all():
            pinned_queue_ids.add(item.id)

        if queue_id in pinned_queue_ids:
            user_queue[0].pinned_course_list.remove(queue_id)
            user_queue[0].save()
        else:
            user_queue[0].pinned_course_list.add(queue_id)
            user_queue[0].save()

    return redirect(reverse('courses'))


@login_required
def statistics_action(request, queue_id):
    if not check_valid_queue_id(queue_id):
        raise Http404
    if not check_instructor(queue_id, request.user.id):
        return HttpResponse('Unauthorized', status=401)

    queue_name = Queue.objects.get(id=queue_id).name

    stats = {}  # date string --> [# of questions, sum time to resolution]

    questions = Question.objects.filter(
        queue_id__exact=queue_id,
        status__exact="done",
        creation_time__isnull=False,
        resolution_time__isnull=False,
    )

    for question in questions:
        question_date = str(question.creation_time.date())
        # this is in *seconds*
        time_to_resolve_seconds = (question.resolution_time - question.creation_time).seconds

        if question_date not in stats:
            stats[question_date] = [1, time_to_resolve_seconds]
        else:
            prev_question_count, prev_time_to_resolution = stats[question_date]
            # aggregate number of questions and total time to resolve
            stats[question_date] = [prev_question_count + 1, prev_time_to_resolution + time_to_resolve_seconds]

    result = []
    for question_date in stats:
        question_count, time_to_resolve_seconds = stats[question_date]
        result.append({
            "date": question_date,
            "question_count": question_count,
            # calculate avg time to resolve, and convert to minutes
            "time_to_resolve": f"{time_to_resolve_seconds / question_count / 60:.2f}"
        })

    return render(request, "ohq/statistics.html", {"result": result, "queue_name": queue_name})
