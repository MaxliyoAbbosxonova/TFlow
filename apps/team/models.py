from django.db.models import Model, CASCADE, ForeignKey, RESTRICT
from django.db.models.fields import CharField

from users.models import Users


# Create your models here.

class Team(Model):
    name = CharField(max_length=100, unique=True)
    workspace = ForeignKey('workspace.Workspace', related_name='team', on_delete=CASCADE, default=1)
    team_lead = ForeignKey(Users, on_delete=RESTRICT, null=True)

    def __str__(self):
        return self.name
