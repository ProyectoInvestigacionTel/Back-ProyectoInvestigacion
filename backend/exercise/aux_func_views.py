from datetime import datetime
import json
import math
import re
from django.core.files.base import ContentFile
from dockerfunctions import run_code_in_container
from teloprogramo import settings
from .models import *
import os
from django.core.files.storage import default_storage


def check_imports(code: str) -> bool:
    direct_imports = re.findall(r"\bimport (\w+)", code)
    from_imports = re.findall(r"\bfrom (\w+)", code)
    return bool(direct_imports or from_imports)


def add_message_to_conversation(detail, sender, message):
    with detail.conversation_file.open("r") as file:
        current_content = json.load(file)

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_message = {"date": date, "sender": sender, "message": message}
    current_content.append(new_message)

    detail.conversation_file.delete(save=False)

    detail.conversation_file.save(
        detail.conversation_file.name, ContentFile(json.dumps(current_content))
    )


def verify_imports(code):
    imports_detected = check_imports(code)
    return imports_detected


def get_excercise_instance(exercise_id):
    try:
        return Exercise.objects.get(pk=exercise_id)
    except Exercise.DoesNotExist:
        return None


def generate_result_json(spected_outputs, clean_result):
    results = []
    max_length = max(len(spected_outputs), len(clean_result))

    for i in range(max_length):
        spected = spected_outputs[i] if i < len(spected_outputs) else None
        real = clean_result[i] if i < len(clean_result) else None

        result = {"output": spected, "obtained": real, "state": spected == real}
        results.append(result)
    return json.dumps(results)


def get_current_attempt(request, user):
    return AttemptExercise.objects.filter(
        exercise_id=request.data["exercise_id"], user_id=user.user_id
    ).first()


def load_use_case(exercise_id):
    use_cases = UseCase.objects.filter(exercise_id=exercise_id)
    return [
        {
            "input": uc.input_code,
            "output": uc.output_code,
            "strength": uc.strength,
            "is_sample": uc.is_sample,
            "explanation": uc.explanation,
        }
        for uc in use_cases
    ]


def execute_code(code: str, head: str, tail: str) -> str:
    print("Llamando a run_code_in_container code: ", code, flush=True)
    if head is None:
        head = ""
    if tail is None:
        tail = ""
    final_code = head + "\n" + code + "\n" + tail
    print("code final: ", final_code, flush=True)
    result = run_code_in_container(final_code)
    print("result:", result, flush=True)
    return result


def compare_outputs_and_calculate_score(spected_outputs, clean_result, binary):
    correct_outputs = sum(
        spected == real for spected, real in zip(spected_outputs, clean_result)
    )
    total_outputs = len(spected_outputs)

    if binary:
        # solo obtiene score si todos los casos son correctos
        result = correct_outputs == total_outputs
        score = 100 if result else 0
    else:
        #  obtiene score por cada caso correcto
        score = (correct_outputs / total_outputs) * 100
        result = correct_outputs == total_outputs

    return score, result


def update_attempt(current_attempt, request, exercise_instance, user, score, result):
    from exercise.serializers import AttemptExerciseSerializer

    if current_attempt:
        current_attempt.attempts += 1
        current_attempt.score = score
        current_attempt.time = request.data["time"]
        current_attempt.result = result
        current_attempt.save()
        return current_attempt
    else:
        attemp_data = {
            "exercise_id": exercise_instance.exercise_id,
            "user_id": user.user_id,
            "attempts": 1,
            "score": score,
            "time": request.data["time"],
            "result": result,
        }
        attempt_serializer = AttemptExerciseSerializer(data=attemp_data)
        if attempt_serializer.is_valid():
            attempt_serializer.save()
            return attempt_serializer.instance
        else:
            print("Error in update attempt:", attempt_serializer.errors, flush=True)
            return None


def create_or_update_attempt_detal(current_attemp, score, result):
    from exercise.serializers import AttemptDetailSerializer

    detail_data = {
        "general_attempt_id": current_attemp.general_attempt_id,
        "date": datetime.now(),
        "score": math.floor(score),
        "result": result,
        "feedback": 1 if not result else 0,
    }
    detail_serializer = AttemptDetailSerializer(data=detail_data)
    if detail_serializer.is_valid():
        return detail_serializer.save()
    else:
        print(
            "Error in create or update attempt detail:",
            detail_serializer.errors,
            flush=True,
        )
        return None


def create_or_update_feedback(
    attemp_instance, initial_feedback, code, exercise_id, result_file
):
    from exercise.serializers import FeedbackDetailSerializer

    retro_inicial = [
        {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender": "CHATGPT",
            "message": initial_feedback,
        }
    ]
    retro_serializer = FeedbackDetailSerializer(
        data={"attempt_id": attemp_instance.attempt_id}
    )
    if retro_serializer.is_valid():
        retro_instance = retro_serializer.save()
        code_file_name = f"code_Re{retro_instance.feedback_id}_Ej{exercise_id}.txt"
        conversation_file_name = (
            f"conversation_Re{retro_instance.feedback_id}_Ej{exercise_id}.json"
        )
        result_file_name = f"result_Re{retro_instance.feedback_id}_Ej{exercise_id}.json"

        retro_instance.code_file.save(code_file_name, ContentFile(code))
        retro_instance.conversation_file.save(
            conversation_file_name, ContentFile(json.dumps(retro_inicial))
        )
        retro_instance.result_file.save(result_file_name, ContentFile(result_file))

        retro_instance.save()
        return retro_instance
    else:
        return None


def update_result_state_and_score(attemp_instance, user, score):
    if attemp_instance.result:
        attemp_instance.score = score
        user.coins += 10
        user.save()
        attemp_instance.save()


def get_all_exercises_files(exercise_id, response_data):
    from exercise.serializers import UseCaseSerializer

    if response_data is None:
        response_data = {}

    try:
        exercise = get_excercise_instance(exercise_id)

        # Handle problem statement file
        if exercise.problem_statement and hasattr(exercise.problem_statement, "file"):
            with exercise.problem_statement.open("r") as file:
                response_data["problem_statement"] = file.read()

        # Handle example file
        if exercise.example and hasattr(exercise.example, "file"):
            with exercise.example.open("r") as file:
                response_data["examples"] = file.read()

        use_cases = UseCase.objects.filter(exercise_id=exercise_id)
        use_cases_data = UseCaseSerializer(use_cases, many=True).data
        response_data["use_cases"] = use_cases_data

        return response_data
    except Exception as e:
        print("Error in get all files:", e, flush=True)
        raise e


def format_response_data(data):
    path = os.path.join("global", "format_response_data.json")
    with open(path, "r", encoding="utf-8") as file:
        fields = json.load(file)

    def format_item(item):
        return {fields.get(key, key): value for key, value in item.items()}

    if isinstance(data, list):
        return [format_item(item) for item in data]
    else:
        return format_item(data)


def format_entry_data(data):
    path = os.path.join("global", "format_entry_data.json")
    with open(path, "r", encoding="utf-8") as archivo:
        fields = json.load(archivo)

    def format_item(item):
        return {fields.get(key, key): value for key, value in item.items()}

    if isinstance(data, list):
        return [format_item(item) for item in data]
    else:
        return format_item(data)


def save_exercise_file(exercise: Exercise, file_content: str, category: str):
    if not exercise.pk:
        raise ValueError("Exercise must have a primary key before saving files.")

    file_extension = ".txt"
    filename = f"{category}_{exercise.pk}{file_extension}"
    directory = os.path.join("exercises", str(exercise.pk))
    full_path = os.path.join(directory, filename)

    full_media_path = os.path.join(settings.MEDIA_ROOT, directory)
    os.makedirs(full_media_path, exist_ok=True)

    default_storage.save(full_path, ContentFile(file_content))

    file_field = getattr(exercise, category)
    file_field.name = full_path
    exercise.save(update_fields=[category])

    print(f'File saved to "{full_path}"', flush=True)
    return full_path
