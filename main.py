import consts, pinecone
from colorama import Fore
from babyagi import AutonomousAgent
from collections import deque

print(Fore.RED + "\nOBJECTIVE\n" + Fore.RESET + consts.OBJECTIVE)

AI = AutonomousAgent(consts.OBJECTIVE)

# Append tasks from list in .env
for i, task_name in enumerate(consts.TASKS_LIST):
    task = {"task_id": i+1, "task_name": task_name}
    AI.task_list.append(task)

pinecone.init(api_key=consts.PINECONE_API_KEY, environment=consts.PINECONE_ENVIRONMENT)

# Initialize Pinecone if enabled in .env
if consts.PINECONE_DB:
    pinecone.init(api_key=consts.PINECONE_API_KEY, environment=consts.PINECONE_ENVIRONMENT)

    # Create Pinecone index
    table_name = consts.PINECONE_TABLE_NAME
    dimension = 1536
    metric = "cosine"
    pod_type = "p1"
    if table_name not in pinecone.list_indexes():
        pinecone.create_index(
            table_name, dimension=dimension, metric=metric, pod_type=pod_type
        )

    # Connect to the index
    index = pinecone.Index(table_name)
    AI.indexes[table_name] = index


if __name__ == "__main__":
    while True:
        if AI.task_list:
            print(
                Fore.GREEN
                + "\n*TASK LIST*\n"
                + Fore.RESET
                + "\n".join([f"{t['task_id']}: {t['task_name']}" for t in AI.task_list])
            )
            AI.task_list = deque(AI.task_list)
            task = AI.task_list.popleft()
            print(Fore.BLUE + "\n*NEXT TASK*\n" + Fore.RESET)
            print(str(task["task_id"]) + ": " + task["task_name"])

            result = AI.execution_agent(task["task_name"], root=True)
            changes = AI.change_propagation_agent(result)

            print(Fore.YELLOW + "\n*TASK RESULT*\n" + Fore.RESET)
            print(Fore.MAGENTA+"\n\ncodename ChangePropagationAgent:"+Fore.RESET+f"\n{changes}")
        else:
            if consts.CONTINUOUS_MODE:
                AI.execution_agent("I must create one or more tasks to keep following my objective (I can also change my objective)")
            else:
                break