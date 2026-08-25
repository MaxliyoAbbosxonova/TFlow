from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FileUpload
from .serializers import MultipleFileUploadSerializer, FileUploadSerializer


class MultipleFileUploadView(APIView):
    # Allow file uploads (DRF uses MultiPartParser by default for form-data)
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # Initialize serializer with request data (files)
        serializer = MultipleFileUploadSerializer(data=request.data)

        if serializer.is_valid():
            # Save files using the serializer's create() method
            file_uploads = serializer.save()
            # Return serialized data for the uploaded files
            return Response(
                FileUploadSerializer(file_uploads, many=True).data,
                status=status.HTTP_201_CREATED
            )

            # Return errors if validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = FileUpload.objects.all()  # List all uploaded files
    serializer_class = FileUploadSerializer

    @action(
        detail=True,
        methods=["POST"],
        parser_classes=[MultiPartParser],
        url_path=r"upload/(?P<filename>[a-zA-Z0-9_]+\.mp3)",
    )
    def upload(self, request, **kwargs):
        track = self.get_object()

        if "file" not in request.data:
            raise ValidationError("There is no file in the HTTP body.")

        file = request.data["file"]
        track.file.save(file.name, file)
        return Response(FileUploadSerializer(track).data)
