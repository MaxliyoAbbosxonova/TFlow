# Create your views here.
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.views import APIView

from comment.models import Comments
from comment.serializers import CommentsModelSerializer, CommentCreateModelSerializer, ReplyCommentSerializer
from services.comment import create_comment, reply_comment
from shared.permissions import IsMemberForComment
from task.models import Task


@extend_schema(tags=["Comments"])
class CommentsListApiView(APIView):
    serializer_class = CommentsModelSerializer
    pagination_class=LimitOffsetPagination

    def get(self, request, task_id):
        task = Task.objects.filter(id=task_id).first()
        if task is None:
            return NotFound("Task topilmadi ")
        comments = Comments.objects.filter(task=task)
        serializer = self.serializer_class(comments, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


@extend_schema(tags=["Comments"])
class CommentsCreateApiView(CreateAPIView):
    serializer_class = CommentCreateModelSerializer

    # def get_queryset(self):
    #     return Comments.objects.filter(author=self.request.user).all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
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
    permission_classes = (IsMemberForComment,)

    def get_queryset(self):
        return Comments.objects.filter(author=self.request.user).all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = reply_comment(serializer.validated_data, request)
        return Response(data={'id': comment.id, 'comment': comment.text, 'author': comment.author},
                        status=HTTP_201_CREATED)
