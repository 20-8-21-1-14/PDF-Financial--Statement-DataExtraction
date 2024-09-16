from rest_framework import serializers

class FinancialDataSerializer(serializers.Serializer):
    TenCongTy = serializers.CharField(max_length=255, required=False, allow_blank=True)
    NgayBaoCao = serializers.CharField(max_length=255, required=False, allow_blank=True)
    VonDieuLe = serializers.CharField(max_length=255, required=False, allow_blank=True)
    LaiTruocThue = serializers.CharField(max_length=255, required=False, allow_blank=True)
    LoTruocThue = serializers.CharField(max_length=255, required=False, allow_blank=True)
    LaiSauThue = serializers.CharField(max_length=255, required=False, allow_blank=True)
    LoSauThue = serializers.CharField(max_length=255, required=False, allow_blank=True)
