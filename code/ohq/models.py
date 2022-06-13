from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    linked_user = models.OneToOneField(User, on_delete=models.PROTECT)
    bio = models.CharField(blank=True, max_length=200)

    def __str__(self):
        return "profile is linked to user id=" + str(self.linked_user.id) \
               + " with bio=" + self.bio


class Queue(models.Model):
    name = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField()

    def __str__(self):
        return "queue has name=" + self.name \
               + " enabled=" + str(self.enabled)


class PinnedQueue(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, unique=True)
    pinned_course_list = models.ManyToManyField(Queue, related_name="pinned_courses")

    def __str__(self):
        return "pinnedQueue: user=" + str(self.user) 
            #    + " pinned_course_list=" + str(self.pinned_course_list)


class Question(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.PROTECT)
    student = models.ForeignKey(User, on_delete=models.PROTECT, related_name="related_student")
    assigned_instructor = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT,
                                            related_name="related_instructor")
    creation_time = models.DateTimeField()
    processed_time = models.DateTimeField(blank=True, null=True)
    resolution_time = models.DateTimeField(blank=True, null=True)
    content = models.CharField(max_length=2000)
    location = models.CharField(max_length=2000)
    question_type = models.CharField(max_length=2000)
    # - waiting: still waiting in the queue
    # - processing: being helped by an instructor
    # - done: done being helped by an instructor
    # - unresolved: not resolved until the end of OH session
    status = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return "question is for course=" + self.queue.name \
               + " by student=" + str(self.student.id) \
               + " content=" + self.content \
               + " status=" + self.status


class InstructorStatus(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.PROTECT)
    queue = models.ForeignKey(Queue, on_delete=models.PROTECT)
    online = models.BooleanField()

    def __str__(self):
        return "instructor has user id=" + str(self.linked_user.id) \
               + " for queue=" + str(self.queue.id) \
               + " online=" + str(self.online)


class Announcement(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.PROTECT)
    poster = models.ForeignKey(User, on_delete=models.PROTECT, related_name="poster")
    content = models.CharField(max_length=2000)
    creation_time = models.DateTimeField()
    status = models.CharField(max_length=200, default="ongoing") # ongoing, outdated
    type = models.CharField(max_length=200, default="public") # public, private
    receiver = models.ForeignKey(User, on_delete=models.PROTECT, related_name="receiver", null=True) # only valid if type is private

    def __str__(self):
        return "annoucement posted by user id=" + str(self.poster.id) \
               + " for queue=" + str(self.queue.id) \
               + " status=" + str(self.status)
