from django.contrib import admin


from .models import Person
from .models import Question
from .models import Tiebreaker


# Register your models here.
admin.site.register(Person)
admin.site.register(Question)
admin.site.register(Tiebreaker)
