from django.db import models

class ResourceCategory(models.TextChoices):
    FOOD = "food", "Food Assistance"
    FOOD_DELIVERY = "food_delivery", "Food Delivery"
    HOUSING = "housing", "Housing"
    TRANSPORTATION = "transportation", "Transportation"
    
class Language(models.TextChoices):
    ENGLISH = "english", "English"
    SPANISH = "spanish", "Spanish"
    OTHER = "other", "Other"
    
    
class ReferralRequest(models.model):
    
    age = models.PositiveSmallIntegerField(null = True, blank= True)
    county = models.CharField(max_length = 100) 
    city = models.CharField(max_length = 100, blank= True)
    preferred_language = models.CharField(max_length = 30, choices = Language.choices, blank = True,)
    insurance_type = models.CharField(max_length = 100, blank= True)
    wheelchair = models.BooleanField(default=False)
    needs = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add = True)
    
class CommunityResources(models.model):
    name = models.CharField(max_length = 255)
    city = models.CharField(max_length = 100)
    state = models.CharField(max_length = 100)
    description = models.TextField(max_length = 100)
    
    counties_served = models_CharField(default = list)
    cities_served = models_CharField(default = list)
    needs_addressed = models.JSONField(default=list)
    
    minimum_age = models.PositiveSmallIntegerField(null= True, blank = True)
    maximum_age = models.PositiveSmallIntegerField(null = True, blank = True)
    
    accepted_insurance = models.JSONField(default = list)
    supported_languages = models.JSONField(default = list)
    
    wheelchair_accessible = models.BooleanField(default = False)
    active = models.BooleanField(default = True)
    
    source_url = models.URLField(blank = True)
    source_excerpt = models.TextField(blank = True)
    last_verified_at = models.DateTimeField(null = True, blank = True)
    
     def __str__(self) -> str:
        return self.name
    