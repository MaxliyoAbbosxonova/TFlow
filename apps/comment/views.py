# Create your views here.
from comment.models import Comments
from comment.serializers import (
    CommentCreateModelSerializer,
    CommentsModelSerializer,
    ReplyCommentSerializer,
)
from django.core.cache import cache
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.views import APIView
from services.comment import create_comment, reply_comment
from shared.permissions import IsMemberForComment
from task.models import Task


def comments_key(task_id):
    return f"comments:task:{task_id}"


def invalidate_comments(task_id):
    transaction.on_commit(lambda: cache.delete(comments_key(task_id)))


@extend_schema(tags=["Comments"])
class CommentsListApiView(APIView):
    serializer_class = CommentsModelSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthenticated,)

    def get(self, request, task_id):
        task = Task.objects.filter(id=task_id).first()
        if task is None:
            raise NotFound("Task topilmadi ")
        comments = Comments.objects.filter(task=task)
        serializer = self.serializer_class(comments, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


@extend_schema(tags=["Comments"])
class CommentsCreateApiView(CreateAPIView):
    serializer_class = CommentCreateModelSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        comment = create_comment(serializer.validated_data, request)
        return Response(data={'id': comment.id, 'comment': comment.text, 'author': comment.author.id},
                        status=HTTP_201_CREATED)


@extend_schema(tags=["Comments"])
class CommentsRetrieveUpdateDestroyApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = CommentsModelSerializer
    permission_classes = (IsMemberForComment,)

    def get_queryset(self):
        return Comments.objects.filter(author=self.request.user).all()


@extend_schema(tags=['Comments'])
class ReplyToComment(APIView):
    serializer_class = ReplyCommentSerializer

    def get_queryset(self):
        return Comments.objects.filter(author=self.request.user).all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        comment = reply_comment(serializer.validated_data, request)
        return Response(data={'id': comment.id, 'comment': comment.text, 'author': comment.author.id},
                        status=HTTP_201_CREATED)
