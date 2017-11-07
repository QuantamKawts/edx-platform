"""
Signal handlers related to discussions.
"""
import logging

from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey

from django_comment_common import signals
from lms.djangoapps.discussion.config.waffle import waffle, FORUM_RESPONSE_NOTIFICATIONS, SEND_NOTIFICATIONS_FOR_COURSE
from lms.djangoapps.discussion import tasks
from openedx.core.djangoapps.theming.helpers import get_current_site


log = logging.getLogger(__name__)


@receiver(signals.comment_created)
def send_discussion_email_notification(sender, user, post, **kwargs):
    if not waffle().is_enabled(FORUM_RESPONSE_NOTIFICATIONS):
        log.debug('Discussion: Response notifications waffle switch not enabled')
        return

    if not SEND_NOTIFICATIONS_FOR_COURSE.is_enabled(CourseKey.from_string(post.thread.course_id)):
        log.debug('Discussion: Response notifications not enabled for this course')
        return

    current_site = get_current_site()
    if current_site is None:
        log.debug('Discussion: No current site, not sending notification')
        return

    send_message(post, current_site)


def send_message(comment, site):
    thread = comment.thread
    context = {
        'course_id': unicode(thread.course_id),
        'comment_id': comment.id,
        'comment_body': comment.body,
        'comment_author_id': comment.user_id,
        'comment_username': comment.username,
        'comment_created_at': comment.created_at,
        'thread_id': thread.id,
        'thread_title': thread.title,
        'thread_username': thread.username,
        'thread_author_id': thread.user_id,
        'thread_created_at': thread.created_at,
        'thread_commentable_id': thread.commentable_id,
        'site_id': site.id
    }
    tasks.send_ace_message.apply_async(args=[context])
