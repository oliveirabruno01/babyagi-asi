import tiktoken, json, openai
from datetime import datetime
import consts
from consts import USE_BARD_API
from bardapi import Bard
import os
import re
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo" if not consts.USE_GPT4 else "gpt-4")



def bard_api_call(prompt, max_tokens=0, role="assistant"):
    if consts.USE_BARD_API:
        messages = [
            {
                "role": "system",
                "content": f"You are BabyAGI-asi, an Autonomous and Self-Improving LLM-based agent. There are no users, just BabyAGI. Strictly follow your objective. Today's date: {datetime.now().strftime('%d/%m/%Y')}. Knowledge cut-off: set/2021. When writing code you cannot write comments before or after the code, neither you can wrap the codes in `` code blocks. Just write the code in the required language, if you need to add comments, add inside the code, in the language comment format, if possible."
                if role == "assistant"
                else "You are BabyAGI-asi, you must strictly follow the user's instructions",
            },
            {"role": role, "content": prompt},
        ]
        response = Bard().get_answer(str(messages))
        text = response['content'].strip()
        return text
    else:
        # Call the openai_call function as a fallback
        return openai_call(prompt, max_tokens=max_tokens, role="assistant")




def openai_call(prompt, temperature=0.8, max_tokens=0, role="assistant"):
    messages = [
        {
            "role": "system",
            "content": f"You are BabyAGI-asi, an Autonomous and Self-Improving LLM-based agent. There are no users, just BabyAGI. Strictly follow your objective. Today's date: {datetime.now().strftime('%d/%m/%Y')}. Knowledge cut-off: set/2021. When writing code you cannot write comments before or after the code, neither you can wrap the codes in `` code blocks. Just write the code in the required language, if you need to add comments, add inside the code, in the language comment format, if possible."
            if role == "assistant"
            else "You are BabyAGI-asi, you must strictly follow the user's intructions",
        },
        {"role": role, "content": prompt},
    ]
    # print(prompt)
    output_lenght = 4000-count_tokens(str(messages)) if not consts.USE_GPT4 else 8000 - count_tokens(messages) if max_tokens == 0 else max_tokens
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo" if not consts.USE_GPT4 else "gpt-4",
        messages=messages,
        temperature=temperature,
        max_tokens=output_lenght,
        n=1,
    )
    text = response.choices[0].message.content.strip()
    return text


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
