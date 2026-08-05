from django.db import models

class ResourceCategory(models.TextChoices):
    FOOD = "food", "Food Assistance"