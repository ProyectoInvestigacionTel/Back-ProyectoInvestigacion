from rest_framework import serializers
from exercise.use_case.models import UseCase


class UseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UseCase
        fields = (
            "id",
            "input_code",
            "output_code",
            "strength",
            "is_sample",
            "explanation",
        )


class UseCaseBulkCreateSerializer(serializers.Serializer):
    use_cases = UseCaseSerializer(many=True)

    def create(self, validated_data):
        use_cases_data = validated_data.pop("use_cases")
        use_cases = [
            UseCase.objects.create(**use_case_data) for use_case_data in use_cases_data
        ]
        return use_cases
