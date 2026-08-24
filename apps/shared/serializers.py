from rest_framework.fields import ListField, FileField
from rest_framework.serializers import Serializer


class MultipleFileUploadSerializer(Serializer):
    # List of files (each file is validated by FileField)
    files = ListField(
        child=FileField(
            max_length=1024 * 1024 * 5,
            allow_empty_file=False,  # Reject empty files
            use_url=False  # Return file path instead of URL (adjust as needed)
        ),
        min_length=1  # Require at least one file
    )

    def create(self, validated_data):
        """Save multiple files to the database."""
        files = validated_data.pop('files')  # Extract files from validated data
        file_uploads = []

        for file in files:
            # Create a FileUpload instance for each file
            file_upload = FileUpload.objects.create(file=file, **validated_data)
            file_uploads.append(file_upload)

        return file_uploads


from rest_framework import serializers
from .models import FileUpload


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['id', 'file', 'uploaded_at']  # Fields to expose in the API
        read_only_fields = ['uploaded_at']
