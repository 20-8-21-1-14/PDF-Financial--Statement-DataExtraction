from rest_framework import serializers


class FinancialStatementSerializer(serializers.Serializer):
    year = serializers.IntegerField(required=True)
    accounting_loss_before_tax = serializers.DecimalField(max_digits=15, decimal_places=2)
    accounting_loss_after_tax = serializers.DecimalField(max_digits=15, decimal_places=2)

class FinancialDataSerializer(serializers.Serializer):
    tax_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    start_years_of_business = serializers.CharField(max_length=50, required=False, allow_blank=True) # serializers.DateField(required=False, format="%Y-%m-%d", input_formats=["%Y-%m-%d"], allow_null=True)
    is_business = serializers.BooleanField(default=True)
    dl = serializers.DecimalField(max_digits=20, decimal_places=0, required=False, allow_null=True)  # This maps to VonDieuLe
    financial_statement = FinancialStatementSerializer(many=True, required=False)

