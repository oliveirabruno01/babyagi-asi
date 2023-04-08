import re, subprocess, platform, openai, prompts, consts, intelligent_tools
from colorama import Fore
from collections import deque
from api import openai_call

print(Fore.RED + "\nOBJECTIVE\n" + Fore.RESET + consts.OBJECTIVE)
openai.api_key = consts.OPENAI_API_KEY


class AutonomousAgent:
    def __init__(self, objective):
        (
            self.objective,
            self.memory,
            self.chore_prompt,
            self.tools,
            self.completed_tasks,
            self.task_id_counter,
            self.create_task_tool,
            self.priorization_tool,
            self.openai_call,
            self.task_list,
        ) = (objective, [], prompts.chore_prompt, prompts.available_tools, [], 1, intelligent_tools.task_creation_agent, intelligent_tools.prioritization_agent, openai_call, deque([]))

    def get_current_state(self):
        return {"self": [nome for nome in dir(self) if not nome.startswith("__")],
                "To-do tasks list": self.task_list}

    def execution_agent(self, current_task):
        prompt = prompts.execution_agent(
                self.objective,
                self.completed_tasks,
                self.get_current_state,
                current_task,
            )
        # print(Fore.LIGHTCYAN_EX + prompt + Fore.RESET)
        changes = openai_call(
            prompt,
            0.4,
            1000,
        )
        print(changes)

        answer = changes[changes.lower().index("answer:")+7:]
        action_func = exec(answer, self.__dict__)
        result = self.action(self)

        self.completed_tasks.append(task)
        return changes + f"; {result}"

    def change_propagation_agent(self, _changes):
        return openai_call(
            prompts.change_propagation_agent(
                self.objective, _changes, self.get_current_state
            ),
            0.7,
            1000,
        )


first_task = {"task_id": 1, "task_name": consts.YOUR_FIRST_TASK}
AI = AutonomousAgent(consts.OBJECTIVE)
AI.task_list.append(first_task)
execution_agent = AI.execution_agent


if __name__ == "__main__":
    while True:
        if AI.task_list:
            print(
                Fore.GREEN
                + "\n*TASK LIST*\n"
                + Fore.RESET
                + "\n".join([f"{t['task_id']}: {t['task_name']}" for t in AI.task_list])
            )
            task = AI.task_list.popleft()
            print(Fore.BLUE + "\n*NEXT TASK*\n" + Fore.RESET)
            print(str(task["task_id"]) + ": " + task["task_name"])

            result = execution_agent(task["task_name"])
            changes = AI.change_propagation_agent(result)

            print(Fore.YELLOW + "\n*TASK RESULT*\n" + Fore.RESET)
        else:
            break
