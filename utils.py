import tiktoken, consts

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo" if not consts.USE_GPT4 else "gpt-4")


def count_tokens(text):
    return len(encoding.encode(text))
