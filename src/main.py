import consts, json
from colorama import Fore
from babyagi import AutonomousAgent
from collections import deque
from utils.pinecone_utils import pinecone_init


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
    if not consts.LOAD_FROM:
        objective = consts.OBJECTIVE if not consts.USER_IN_THE_LOOP else str(
            input(Fore.LIGHTYELLOW_EX + "Insert the objective: " + Fore.RESET))

        print(Fore.RED + "\nOBJECTIVE\n" + Fore.RESET + objective + "\n\n")

        AI = AutonomousAgent(objective)

        # add tasks manually if .env tasks_list is empty
        if len(consts.TASKS_LIST) == 0:
            ct = 1
            while True:
                mid = ", or insert a blank line to start" if ct > 1 else ""
                task = str(input(f"Add a task"+mid+": "))
                if task.strip() == '':
                    break
                AI.task_list.append({"task_id": ct, "task_name": task})
                ct += 1

        # Append tasks from list in .env
        for i, task_name in enumerate(consts.TASKS_LIST):
            task = {"task_id": i + 1, "task_name": task_name}
            AI.task_list.append(task)
    else:
        AI = load_from_json(consts.LOAD_FROM)

    # Initialize Pinecone if enabled in .env
    if consts.PINECONE_DB:
        pinecone_init(AI)

    running = True

    while True:
        if not running:
            filepath = str(input("\nEnter a file name or path to save the basi agent as a json file, or hit enter to quit without saving: "))
            if filepath:
                save_as_json(AI, filepath+".json")
            break
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

            save_as_json(AI, 'tmp_agent.json')
        else:
            if consts.USER_IN_THE_LOOP:
                AI.task_list = deque(AI.task_list)
                new_task = str(input("\nCreate a new task or hit enter to finish BASI: "))
                if new_task.strip() == "":
                    running = False
                else:
                    AI.task_list.append({'task_id': len(AI.task_list)+1, 'task_name': new_task})
                    while True:
                        task = str(input(f"Add a task, or insert a blank line to start: "))
                        if task.strip() == '':
                            break
                        AI.task_list.append({"task_id": len(AI.task_list) + 1, "task_name": task})

            else:
                if consts.CONTINUOUS_MODE:
                    AI.execution_agent("I must create one or more tasks to keep following my objective.")
                else:
                    if consts.LOAD_FROM and not len(AI.task_list):
                        print("\nPlease, enable any USER_IN_THE_LOOP level to revive a basi agent. Or just edit its json file to include new tasks.")
                    running = False
