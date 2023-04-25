import tiktoken, json
from src import consts


encoding = tiktoken.encoding_for_model("gpt-3.5-turbo" if not consts.USE_GPT4 else "gpt-4")


def count_tokens(text):
    return len(encoding.encode(text))


def split_answer_and_cot(text):
    start_index = text.lower().index("answer:")+7
    end_index = text.lower().rfind("note:")

    cot = text[:start_index]
    code = text[start_index:end_index if end_index != -1 else len(text)].replace("```", "")
    return [code, cot]


def get_oneshots():
    one_shots, p_one_shots = [], []
    with open('memories/one-shots.json', 'r') as f:
        one_shots += json.loads(f.read())

    with open('memories/private-one-shots.json', 'r') as f:
        p_one_shots += json.loads(f.read())

    return one_shots, p_one_shots