import re

from django.db import transaction

from comment.models import Comments
from services.audit import create_audit_log
from task.tasks import comment_mention_email_task
from users.admin import Profile
from workspace.models import WorkspaceMember


# text = "jsvayv @hvewgjyqghbd evyjqgdb @cyuwcbnx wjevfygbxi uejygdb"
# listt=text.split()
# a=[]
# for i in listt:
#     if i.startswith('@'):
#         a.append(i[1:])
#
# print(a)
# ['hvewgjyqghbd', 'cyuwcbnx'] result


@transaction.atomic
def mentions(text):
    mentions = set(re.findall(r"@([a-zA-Z0-9_]+)", text))
    return mentions


@transaction.atomic
def create_comment(validated_data, request):
    # request = validated_data.context['request']
    author_profile = Profile.objects.filter(user=request.user).first()
    comment = Comments.objects.create(author=request.user, **validated_data)
    actor = WorkspaceMember.objects.filter(user=request.user).first()
    create_audit_log(actor=actor,
                     action="COMMENT TO TASK",
                     model=comment,
                     )
    task = validated_data["task"]
    text = validated_data["text"]

    listt = mentions(text)

    for username in listt:
        profile = Profile.objects.filter(username=username).first()

        if not profile:
            continue
        comment_mention_email_task(profile, comment, task, author_profile, text)

    return comment
