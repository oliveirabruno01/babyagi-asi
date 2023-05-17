import openai, prompts, consts, os, json, re
from tools import serp_api
from colorama import Fore
from collections import deque
from common_utils import count_tokens, split_answer_and_cot, get_oneshots, openai_call, bard_api_call
from utils import pinecone_utils, text_processing

openai.api_key = consts.OPENAI_API_KEY

one_shots, p_one_shots = get_oneshots()
all_one_shots = one_shots+p_one_shots


class AutonomousAgent:
    def __init__(self, objective):
        (
            self.objective,
            self.working_memory,
            self.chore_prompt,
            self.completed_tasks,
            self.task_id_counter,
            self.openai_call,
            self.task_list,
            self.indexes,
            self.focus,
            self.get_serp_query_result,
            self.current_task,
            self.bard_api_call
        ) = (objective, [], prompts.chore_prompt, [], 1, bard_api_call, deque([]), {}, "", serp_api.get_serp_query_result, "", bard_api_call)

    def get_current_state(self):
        # filter properties to avoid adiction
        hash = {"self": [nome for nome in dir(self) if not nome.startswith("__") and nome not in "search_in_index get_ada_embedding append_to_index memory_agent repl_agent task_list memory focus indexes"],
                "To-do tasks list": self.task_list,
                "Available indexes": [ind for ind in self.indexes.keys()],
                "self.working_memory": self.working_memory,
                "self.focus": self.focus,
                "current dir": os.listdir(os.getcwd())}
        return hash

    def execution_agent(self, current_task, root=False):
        self.current_task = current_task

        if not root:
            print(Fore.LIGHTRED_EX + "\nExecution Agent call with task:" + Fore.RESET + f"{current_task}")

        if current_task not in [o['task'] for o in one_shots]:
            one_shots_names_and_kw = [f"name: '{one_shot['task']}', task_id: '{one_shot['memory_id']}', keywords: '{one_shot['keywords']}';\n\n" for one_shot in all_one_shots]
            code = bard_api_call(
                f"My current task is: {current_task}."
                f"I must choose from 0 to {consts.N_SHOT} most relevant tasks between the following one_shot examples:'\n{one_shots_names_and_kw}'.\n\n"
                f"These oneshots will be injected in execution_agent as instant memories, task memory. I will try to choose {consts.N_SHOT} tasks memories that may help ExA. I will tell the relevant tasks by looking the names and keywords, and imagining what abilities ExA used to produce this memory."
                f"I must write a list({consts.N_SHOT}) cointaining only the memory_ids of the most relevant one_shots, or a empty list. i.e '[\"one_shot example memory_id\"]' or '[]'."
                f"I must read the examples' names and choose from 0 to {consts.N_SHOT} by memory_id. "
                f"I must answer in the format 'CHAIN OF THOUGHTS: here I put a short reasoning;\nANSWER: ['most relevant memory_id']';"
                f"My answer:", max_tokens=900).strip("'")
            print(code)
            pattern = r'\[([^\]]+)\]'
            matches = re.findall(pattern, code)
            completion = ""
            print(f"\nChosen one-shot example: {completion}\n")
            one_shot_example_names = completion[:consts.N_SHOT] if len(completion) > 0 else None
            prompt = prompts.execution_agent(
                    self.objective,
                    self.completed_tasks,
                    self.get_current_state,
                    current_task,
                    [one_shot for one_shot in all_one_shots if one_shot["memory_id"] in one_shot_example_names] if one_shot_example_names is not None else '',
                    self.task_list
                )
            # print(Fore.LIGHTCYAN_EX + prompt + Fore.RESET)
            changes = bard_api_call(
                prompt,
                .5,
                4000-self.count_tokens(prompt),
            )

            print(Fore.LIGHTMAGENTA_EX+f"\n\ncodename ExecutionAgent:"+Fore.RESET+f"\n\n{changes}")

            # try until complete
            result, code, cot = self.repl_agent(current_task, changes)

            save_task = True
            if consts.USER_IN_THE_LOOP:
                while True:
                    inp = str(input('\nDo you want to save this action in memory? (Y/N)\n>')).lower()
                    if inp in 'y yes n no':
                        if inp[0] == 'n':
                            save_task = False
                        break

            if save_task:
                one_shots.append(
                    {
                        "memory_id": "os-{0:09d}".format(len(one_shots)+1),
                        "objective": self.objective,
                        "task": current_task,
                        "thoughts": cot[cot.lower().index('chain of thoughts:')+18:cot.lower().index('answer:')].strip(),
                        "code": code.strip().strip('\n\n'),
                        "keywords": ', '.join(eval(bard_api_call("I must analyze the following task name and action and write a list of keywords.\n"
                                    f"Task name: {current_task};\nAction: {code};\n\n"
                                    f"> I must write a python list cointaing strings, each string one relevant keyword that will be used by ExecutionAgent to retrieve this memories when needed."
                                                     f" i.e: ['search', 'using pyautogui', 'using execution_agent', 'how to x', 'do y']\n"
                                    f"My answer:", max_tokens=2000)))
                    }
                )
                with open("memories/one-shots.json", 'w') as f:
                    f.write(json.dumps(one_shots, indent=True, ensure_ascii=False))

        else:
            cot, code = [[o['thoughts'], o['code']] for o in one_shots if o['task'] == current_task][0]
            print(Fore.LIGHTMAGENTA_EX + f"\n\ncodename ExecutionAgent:" + Fore.RESET + f"\nChain of thoughts: {cot}\n\nAnswer:\n{code}")
            action_func = exec(code, self.__dict__)
            result = self.action(self)

        self.completed_tasks.append(current_task)
        summarizer_prompt = f"I must summarize the 'working memory' and the last events, I must answer as a chain of thoughts, in first person, in the same verb tense of the 'event'. Working memory: {self.working_memory}, event: {cot} result: {result}. " \
                            f"My answer must include the past workig memory and the new events and thoughts. If there's some error or fix in the event I must summarize it as a learning:"
        self.working_memory = bard_api_call(summarizer_prompt)

        return result

    def repl_agent(self, current_task, changes):
        code = changes
        ct = 1

        reasoning = changes
        while True:
            try:
                action_func = exec(code, self.__dict__)
                result = self.action(self)
                return result, code
            except Exception as e:
                print(Fore.RED + f"\n\nFIXING AN ERROR: {e}\n" + Fore.RESET)
                print(f"{ct} try")

                prompt = prompts.fix_agent(current_task, code, "", e)
                new_code = bard_api_call(prompt)
                reasoning += new_code
                reasoning = openai_call(f"I must summarize this past events as a chain of thoughts, in first person: {reasoning}", max_tokens=1000)
            
                try:
                    code = new_code
                    action_func = exec(code, self.__dict__)
                    result = self.action(self)
                    return result, code
                except Exception as e:
                    pass
            ct += 1

    def change_propagation_agent(self, _changes):
        return bard_api_call(
            prompts.change_propagation_agent(
                self.objective, _changes, self.get_current_state
            ),
            0.7,
            1000,
        )

    def memory_agent(self, caller,  content, goal):
        answer = bard_api_call(
            prompts.memory_agent(self.objective, caller, content, goal, self.get_current_state)
        )
        answer = answer[answer.lower().index("answer:")+7:]
        action_func = exec(answer.replace("```", ""), self.__dict__)
        result = self.action(self)

    def search_in_index(self, index_name, query, top_k=1000):
        pinecone_utils.search_in_index(self, index_name, query, top_k=1000)

    def get_ada_embedding(self, text):
        pinecone_utils.get_ada_embedding(text)

    def append_to_index(self, content, index_name):
        pinecone_utils.append_to_index(self, content, index_name)

    def count_tokens(self, text):
        return count_tokens(text)

    def process_large_text(self, text, instruction, max_output_length=1000, split_text=None):
        return text_processing.process_large_text(text, instruction, max_output_length=1000, split_text=None)

    def generate_large_text(self, instruction, max_tokens_lenghts=10000):
        return text_processing.generate_large_text(instruction, max_tokens_lenghts=10000)
