from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

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


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import FileUpload
from .serializers import FileUploadSerializer


class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = FileUpload.objects.all()  # List all uploaded files
    serializer_class = FileUploadSerializer

    def create(self, request, *args, **kwargs):
        # Get list of files from request.FILES (client sends files under key "files")
        files = request.FILES.getlist('files')

        if not files:
            return Response(
                {'error': 'No files submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

            # Save each file
        uploaded_files = []
        for file in files:
            serializer = self.get_serializer(data={'file': file})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            uploaded_files.append(serializer.data)

        return Response(uploaded_files, status=status.HTTP_201_CREATED)  