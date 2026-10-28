from django.utils import timezone


def test_str_returns_file_name(file_upload):
    assert str(file_upload) == file_upload.file.name


def test_file_saved_in_dated_folder(file_upload):
    today = timezone.now()
    expected_prefix = f"uploads/{today:%Y/%m/%d}/"
    assert file_upload.file.name.startswith(expected_prefix)


def test_uploaded_at_is_set_automatically(file_upload):
    assert file_upload.uploaded_at is not None
