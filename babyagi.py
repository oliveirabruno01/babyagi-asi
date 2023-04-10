import openai, prompts, consts, pinecone
from colorama import Fore
from collections import deque
from api import openai_call

print(Fore.RED + "\nOBJECTIVE\n" + Fore.RESET + consts.OBJECTIVE)
openai.api_key = consts.OPENAI_API_KEY


def split_answer_and_cot(text):
    start_index = text.lower().index("answer:") + 7
    end_index = text.lower().rfind("note:")

    cot = text[:start_index]
    code = text[start_index:end_index if end_index != -1 else len(text)].replace("```", "")
    return [code, cot]


class AutonomousAgent:
    def __init__(self, objective):
        (
            self.objective,
            self.memory,
            self.chore_prompt,
            self.tools,
            self.completed_tasks,
            self.task_id_counter,
            self.openai_call,
            self.task_list,
            self.indexes,
            self.focus,
        ) = (objective, [], prompts.chore_prompt, prompts.available_tools, [], 1, openai_call, deque([]), {}, "")

    def get_current_state(self):
        return {"self": [nome for nome in dir(self) if not nome.startswith("__")],
                "To-do tasks list": self.task_list,
                "Available indexes (pinecone memory)": self.indexes,
                "self.memory": self.memory,
                "self.focus": self.focus}

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

        # try until complete
        result = self.repl_agent(current_task, changes)
        self.completed_tasks.append(task)
        return changes + f"; {result}"

    def repl_agent(self, current_task, changes):
        code, cot = split_answer_and_cot(changes)
        print("\n\nREPL AGENT")

        while True:
            try:
                action_func = exec(code, self.__dict__)
                result = self.action(self)
                return result
            except Exception as e:
                prompt = prompts.fix_agent(current_task, code, cot, e)
                print(prompt)
                new_code = openai_call(
                    prompt,
                    0.4,
                    1000,
                )
                print(new_code)
                code, cot = split_answer_and_cot(new_code)

    def change_propagation_agent(self, _changes):
        return openai_call(
            prompts.change_propagation_agent(
                self.objective, _changes, self.get_current_state
            ),
            0.7,
            1000,
        )

    def memory_agent(self, caller,  content, goal):
        answer = openai_call(
            prompts.memory_agent(self.objective,  caller,  content, goal, self.get_current_state)
        )
        answer = answer[answer.lower().index("answer:")+7:]
        action_func = exec(answer.replace("```", ""), self.__dict__)
        result = self.action(self)

    # Function to query records from the Pinecone index
    def search_in_index(self, index_name, query, top_k=1000):
        results = self.indexes[index_name].query(query, top_k=top_k, include_metadata=True)
        print(results)
        response = [f"{task.metadata['task']}:\n{task.metadata['result']}\n;" for task in results.matches]
        print(response)
        return response

    # Get embedding for the text
    def get_ada_embedding(self, text):
        text = text.replace("\n", " ")
        print(text)
        vector = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
        print(vector)
        return vector

    def append_to_index(self, content, index_name):
        # [(0, (0, 0), {"task": self.task_list[0]["task_name"], "result": "result"})]
        self.indexes[index_name].upsert(content)


first_task = {"task_id": 1, "task_name": consts.YOUR_FIRST_TASK}
AI = AutonomousAgent(consts.OBJECTIVE)
AI.task_list.append(first_task)

pinecone.init(api_key=consts.PINECONE_API_KEY, environment=consts.PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = "agicontext"
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
            AI.task_list = deque(AI.task_list)
            task = AI.task_list.popleft()
            print(Fore.BLUE + "\n*NEXT TASK*\n" + Fore.RESET)
            print(str(task["task_id"]) + ": " + task["task_name"])

            result = execution_agent(task["task_name"])
            changes = AI.change_propagation_agent(result)

            print(Fore.YELLOW + "\n*TASK RESULT*\n" + Fore.RESET)
        else:
            break
