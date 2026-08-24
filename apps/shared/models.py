from django.db.models import Model, FileField, DateTimeField


class FileUpload(Model):
    file = FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_at = DateTimeField(auto_now_add=True)  

    def __str__(self):
        return self.file.name


