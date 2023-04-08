from api import openai_call
import prompts
from collections import deque


def task_creation_agent(objective, task_list, task_id_counter):
    completion = openai_call(
        prompts.task_creation_agent(
            objective, task_list
        )
    )
    completion = eval(completion[completion.lower().index("answer:")+7:])
    print(completion)
    new_tasks = [
        {"task_name": task_name}
        for task_name in completion
    ]
    print(new_tasks)

    for new_task in new_tasks:
        task_id_counter += 1
        new_task.update({"task_id": task_id_counter})
        task_list.append(new_task)

    return new_tasks


def prioritization_agent(objective, this_task_id, task_list):
    task_names = [t["task_name"] for t in task_list]
    task_list = deque()
    for task_string in openai_call(
            prompts.priorization_agent(
                objective, task_names, int(this_task_id) + 1
            )
    ).split("\n"):
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})