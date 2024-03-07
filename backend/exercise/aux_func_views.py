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
from exercise.use_case.models import UseCase
from subject.models import Subject
from django.db.models import Count, Sum


def calculate_success_rate_for_difficulties(user_id, exercises):
    difficulty_success_rates = {}
    for difficulty in ["Fácil", "Medio", "Dificil"]:
        difficulty_exercises = exercises.filter(difficulty=difficulty)
        difficulty_success_rates[difficulty] = calculate_success_rate(
            difficulty_exercises, user_id
        )
    return difficulty_success_rates


def calculate_success_rate_for_contents(user_id, exercises, subject_name):
    content_success_rates = {}
    subject_instance = Subject.objects.get(name=subject_name)
    contents = subject_instance.contents.split(",")
    for content in contents:
        content_exercises = exercises.filter(contents__icontains=content)
        content_success_rates[content] = calculate_success_rate(
            content_exercises, user_id
        )
    return content_success_rates


def calculate_success_rate(exercises, user_id):
    attempts_details = AttemptExercise.objects.filter(
        exercise_id__in=exercises, user_id=user_id
    )

    correct_attempts = AttemptDetail.objects.filter(
        general_attempt_id__in=attempts_details.values_list(
            "general_attempt_id", flat=True
        ),
        result=True,
    ).count()

    total_attempts = attempts_details.aggregate(total=Sum("attempts"))["total"]

    return (correct_attempts / total_attempts * 100) if total_attempts else 0


def contains_print_statement(code):
    return re.search(r"print\((.*?)\)", code)


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
    return results


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


def execute_code(code, head, tail, input_cases):
    final_code = "\n".join(filter(None, [head, code, tail]))
    full_output = run_code_in_container(final_code, input_cases=input_cases)

    return full_output


def compare_outputs_and_calculate_score(
    spected_outputs, clean_result, binary, max_score
):
    correct_outputs = sum(
        spected == real for spected, real in zip(spected_outputs, clean_result)
    )
    total_outputs = len(spected_outputs)

    if binary:
        # solo obtiene score si todos los casos son correctos
        result = correct_outputs == total_outputs
        # Asegurarse de que el score no exceda el score máximo del ejercicio
        score = max_score if result else 0
    else:
        # obtiene score por cada caso correcto y escala según el score máximo del ejercicio
        score_percentage = correct_outputs / total_outputs
        score = score_percentage * max_score
        result = correct_outputs == total_outputs

    return score, result


def update_attempt(current_attempt, request, exercise_instance, user, score, result):
    from exercise.serializers import AttemptSaveSerializer

    new_time = request.data["time"]
    if current_attempt:
        current_attempt.attempts += 1
        if score > current_attempt.score:
            current_attempt.score = score
        if new_time < current_attempt.time:
            current_attempt.time = new_time
        if current_attempt.result != True:
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
        attempt_serializer = AttemptSaveSerializer(data=attemp_data)
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
    attemp_instance, initial_feedback, code, exercise_id, result_file, gpt
):
    from exercise.serializers import FeedbackDetailSerializer

    if gpt:
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
        result_file_name = f"result_Re{retro_instance.feedback_id}_Ej{exercise_id}.json"

        retro_instance.code_file.save(code_file_name, ContentFile(code))

        if gpt:
            conversation_file_name = (
                f"conversation_Re{retro_instance.feedback_id}_Ej{exercise_id}.json"
            )
            retro_instance.conversation_file.save(
                conversation_file_name, ContentFile(json.dumps(retro_inicial))
            )

        json_result_file = json.dumps(result_file)
        retro_instance.result_file.save(result_file_name, ContentFile(json_result_file))

        retro_instance.save()
        return retro_instance
    else:
        return None


def update_result_state_and_score(attemp_instance, user, score):
    if attemp_instance.result:
        attemp_instance.score = score
        user.save()
        attemp_instance.save()


def get_all_exercises_files(exercise_id, response_data):
    from exercise.serializers import UseCaseSerializer

    if response_data is None:
        response_data = {}

    try:
        exercise = get_excercise_instance(exercise_id)

        if exercise.problem_statement:
            problem_statement_path = os.path.join(
                settings.MEDIA_ROOT, exercise.problem_statement.name
            )
            if os.path.exists(problem_statement_path):
                with open(problem_statement_path, "r") as file:
                    response_data["problem_statement"] = file.read()

        if exercise.example:
            example_path = os.path.join(settings.MEDIA_ROOT, exercise.example.name)
            if os.path.exists(example_path):
                with open(example_path, "r") as file:
                    response_data["examples"] = file.read()

        return response_data
    except Exception as e:
        print(f"Error in get all files: {e}", flush=True)


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


def save_exercise_file(exercise, file_content, category):
    if not exercise.pk:
        raise ValueError("Exercise must have a primary key before saving files.")

    file_extension = ".txt"
    filename = f"{category}_{exercise.pk}{file_extension}"
    directory = os.path.join("exercises", str(exercise.pk))
    full_path = os.path.join(directory, filename)

    full_media_path = os.path.join(settings.MEDIA_ROOT, directory)
    os.makedirs(full_media_path, exist_ok=True)

    existing_file_path = getattr(exercise, category).name

    if existing_file_path and default_storage.exists(existing_file_path):
        print(f'Deleting existing file at "{existing_file_path}"', flush=True)
        default_storage.delete(existing_file_path)

    default_storage.save(full_path, ContentFile(file_content))

    file_field = getattr(exercise, category)
    file_field.name = full_path
    exercise.save(update_fields=[category])

    return full_path


def update_subject_contents(subject_instance, new_contents):
    existing_contents = (
        subject_instance.contents.split(",") if subject_instance.contents else []
    )
    new_contents_list = new_contents.split(",") if new_contents else []

    updated_contents = list(set(existing_contents + new_contents_list))
    subject_instance.contents = ",".join(updated_contents)
    subject_instance.save()
