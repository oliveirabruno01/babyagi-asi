import openai, prompts, consts, os, tiktoken, json, re
from tools import serp_api
from colorama import Fore
from collections import deque
from api import openai_call
from utils import count_tokens

openai.api_key = consts.OPENAI_API_KEY

one_shots, p_one_shots = [], []
with open('memories/one-shots.json', 'r') as f:
    one_shots += json.loads(f.read())

with open('memories/private-one-shots.json', 'r') as f:
    p_one_shots += json.loads(f.read())

all_one_shots = one_shots+p_one_shots


def split_answer_and_cot(text):
    start_index = text.lower().index("answer:")+7
    end_index = text.lower().rfind("note:")

    cot = text[:start_index]
    code = text[start_index:end_index if end_index != -1 else len(text)].replace("```", "")
    return [code, cot]


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
            self.current_task
        ) = (objective, [], prompts.chore_prompt, [], 1, openai_call, deque([]), {}, "", serp_api.get_serp_query_result, "")

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

        if not current_task in [o['task'] for o in one_shots]:
            one_shots_names_and_kw = [f"name: '{one_shot['task']}', task_id: '{one_shot['memory_id']}', major objective: {one_shot['objective']}, keywords: '{one_shot['keywords']}';\n\n" for one_shot in all_one_shots]
            code, cot = split_answer_and_cot(openai_call(f"My current task is: {current_task}. My current major objective is {self.objective}."
                                          f"I must choose from 0 to {consts.N_SHOT} most relevant tasks between the following one_shot examples:'\n{one_shots_names_and_kw}'.\n\n"
                                          f"I must write a list({consts.N_SHOT}) cointaining only the memory_ids of the most relevant one_shots, or a empty list. i.e '[\"one_shot example memory_id\"]' or '[]'."
                                          f"I must read the examples' names and choose from 0 to {consts.N_SHOT} by memory_id. I must answer in the format 'CHAIN OF THOUGHTS: here I put a short reasoning;\nANSWER: ['most relevant memory_id']';"
                                          f"My answer:", max_tokens=300).strip("'"))
            print(cot)
            pattern = r'\[([^\]]+)\]'
            matches = re.findall(pattern, code)
            completion = eval("["+matches[0]+"]") if matches else []
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
            changes = openai_call(
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
                    inp = str(input('Do you want to save this action in memory? (Y/N)\n>')).lower()
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
                        "keywords": eval(openai_call("I must analyze the following task name and action and write a list of keywords.\n"
                                    f"Task name: {current_task};\nAction: {code};\n\n"
                                    f"> I must write a python list cointaing only one string, and inside this string 3 or more keywords i.e: ['search, using pyautogui, using execution_agent, how to x, do y']\n"
                                    f"My answer:", max_tokens=2000))[0]
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
        self.working_memory = openai_call(summarizer_prompt)

        return result

    def repl_agent(self, current_task, changes):
        code, cot = split_answer_and_cot(changes)
        ct = 1

        reasoning = changes
        while True:
            try:
                action_func = exec(code, self.__dict__)
                result = self.action(self)
                return result, code, cot
            except Exception as e:
                print(Fore.RED + f"\n\nFIXING AN ERROR: {e}\n" + Fore.RESET)
                print(f"{ct} try")

                prompt = prompts.fix_agent(current_task, code, cot, e)
                new_code = openai_call(
                    prompt,
                    temperature=0.4,
                )
                reasoning += new_code
                reasoning = openai_call(f"I must summarize this past events as a chain of thoughts, in first person: {reasoning}", max_tokens=1000)
                # print(new_code, end="\n")
                try:
                    code, cot = split_answer_and_cot(new_code)
                    action_func = exec(code, self.__dict__)
                    result = self.action(self)
                    return result, code, cot
                except Exception as e:
                    pass
            ct += 1

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
            prompts.memory_agent(self.objective, caller, content, goal, self.get_current_state)
        )
        answer = answer[answer.lower().index("answer:")+7:]
        action_func = exec(answer.replace("```", ""), self.__dict__)
        result = self.action(self)

    # Function to query records from the Pinecone index
    def search_in_index(self, index_name, query, top_k=1000):
        results = self.indexes[index_name].query(query, top_k=top_k, include_metadata=True)
        response = [f"{task.metadata['task']}:\n{task.metadata['result']}\n;" for task in results.matches]
        return response

    # Get embedding for the text
    def get_ada_embedding(self, text):
        text = text.replace("\n", " ")
        vector = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
        return vector

    def append_to_index(self, content, index_name):
        # [(0, (0, 0), {"task": self.task_list[0]["task_name"], "result": "result"})]
        self.indexes[index_name].upsert(content)

    def count_tokens(self, text):
        return count_tokens(text)

    def process_large_text(self, text, instruction, max_output_length=1000, split_text=None):
        text_chunks = split_text(text, max_output_length) if split_text is not None else [text[i:i+max_output_length] for i in range(0, len(text), max_output_length)]
        processed_chunks = []
        for i, chunk in enumerate(text_chunks):
            print(i)
            prompt = f"Chunk {i + 1}/{len(text_chunks)}\n\n" \
                     f"You are an AI processing a text snippet, you must follow the instruction and answer just with the processed output. " \
                     f"If your chunk has any error or an abrupt ending, don't complete/fix it, you must just follow the instruction.\n\n" \
                     f"If generating a large text, or if the chunk is code and your instruction is extract info from the code, answer just with copied code." \
                     f"If there's nothig to extract/return given the current chunk and instruction, write just 'nothing_on_chunk'." \
                     f"Instruction: {instruction}\n\nText chunk: {chunk}. You answer:"
            processed_chunk = openai_call(prompt, role="assistant")
            if '__nothing_on_chunk' not in processed_chunk:
                processed_chunks.append(processed_chunk)

        print('\n'.join(processed_chunks))
        return '\n'.join(processed_chunks)

    def generate_large_text(self, instruction, max_tokens_lenghts=10000):
        text = ""
        heading = "start"
        # hardcoded, for gpt3.5
        # counting chars but the right is to count tokens
        while len(text) + 3500 < max_tokens_lenghts:
            append_text = self.openai_call(f"I am generating a large text. {instruction[round(len(text)/2):]}. Heading: {heading}\n"
                                           f"Current text (last 100 chars, I must continue seamlessly): '{text[:-100]}'.\n\n"
                                           f"The continuation of the given text is:")
            print(append_text)
            text += append_text
            heading = self.openai_call(f"I am generating a large text. My current heading: {heading}\n"
                                       f"Current text. (last 100 chars, I must continue seamlessly): '{text[:-100]}'.\n\n"
                                       f"Given the current text, what am I doing/heading? If the text is finished, I must answer with _end_of_text_. New heading:")
            print(heading)
            if '_end_of_text_' in heading.lower():
                break

        print(text)
        return text
