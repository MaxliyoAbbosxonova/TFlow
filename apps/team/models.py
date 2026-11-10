from django.db.models import CASCADE, RESTRICT, ForeignKey, Model, UniqueConstraint
from django.db.models.fields import CharField

# Create your models here.

class Team(Model):
    name = CharField(max_length=100)
    workspace = ForeignKey('workspace.Workspace', related_name='teams', on_delete=CASCADE)
    team_lead = ForeignKey('users.Users', on_delete=RESTRICT, null=True)

    def __str__(self):
        return self.name

    class Meta:
        constraints=[UniqueConstraint(fields=['name','workspace'],name='Unique_team')]
