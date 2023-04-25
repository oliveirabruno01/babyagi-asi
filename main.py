import pinecone
import consts, json
from colorama import Fore
from babyagi import AutonomousAgent
from collections import deque


def pinecone_init(agent):
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
    agent.indexes[table_name] = index


def save_as_json(agent: AutonomousAgent, filepath):
    with open(filepath, 'w') as f:
        f.write(json.dumps({
            "objective": agent.objective,
            "working_memory": agent.working_memory,
            "completed_tasks": agent.completed_tasks,
            "task_id_counter": agent.task_id_counter,
            "task_list": [task for task in list(agent.task_list) if task['task_name']],
            "indexes": [index for index in agent.indexes.keys()],
            "focus": agent.focus,
        }))


def load_from_json(filepath):
    with open(filepath, 'r') as f:
        agent_data = json.loads(f.read())
        agent = AutonomousAgent(agent_data['objective'])
        agent.working_memory = agent_data["working_memory"]
        agent.completed_tasks = agent_data["completed_tasks"]
        agent.task_id_counter = agent_data["task_id_counter"]
        agent.task_list = deque([task for task in agent_data["task_list"] if task['task_name']])
        indexes_names = agent_data["indexes"]
        agent.focus = agent_data["focus"]

    return agent


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
                AI.execution_agent("I must create one or more tasks to keep following my objective.")
            else:
                break