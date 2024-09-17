from rest_framework import serializers

class FinancialDataSerializer(serializers.Serializer):
    TenCongTy = serializers.CharField(max_length=255, required=False)
    NgayBaoCao = serializers.CharField(max_length=255, required=False)
    VonDieuLe = serializers.CharField(max_length=255, required=False)
    LaiTruocThue = serializers.CharField(max_length=255, required=False)
    LoTruocThue = serializers.CharField(max_length=255, required=False)
    LaiSauThue = serializers.CharField(max_length=255, required=False)
    LoSauThue = serializers.CharField(max_length=255, required=False)
