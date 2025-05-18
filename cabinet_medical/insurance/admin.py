from django.contrib import admin
from .models import Insurance, PatientInsurance

@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_info', 'created_at', 'updated_at')
    search_fields = ('name', 'contact_info')
    ordering = ('name',)

@admin.register(PatientInsurance)
class PatientInsuranceAdmin(admin.ModelAdmin):
    list_display = ('patient', 'insurance', 'policy_number', 'is_active', 'start_date', 'end_date', 'requires_authorization')
    list_filter = ('is_active', 'insurance', 'requires_authorization')
    search_fields = ('patient__utilisateur__username', 'insurance__name', 'policy_number')
    raw_id_fields = ('patient', 'insurance')
    date_hierarchy = 'start_date'
