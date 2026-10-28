from comment.models import Comments

"""Comment modeli uchun testlar """


def test_top_level_comment_has_no_parent(comment):
    assert comment.parent is None


def reply_is_linked_to_parent(comment, reply):
    assert reply.parent == comment


def test_parent_children_contains_reply(comment, reply):
    assert reply in comment.get_children()


def test_tree_levels(comment, reply):
    comment.refresh_from_db()
    reply.refresh_from_db()
    assert comment.level == 0
    assert reply.level == 1


def test_replies_deleted_when_parent_deleted(comment, reply):
    comment.delete()
    assert not Comments.objects.filter(id=reply.id).exists()
