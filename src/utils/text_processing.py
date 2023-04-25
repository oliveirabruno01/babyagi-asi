from src.api import openai_call


def process_large_text(text, instruction, max_output_length=1000, split_text=None):
    text_chunks = split_text(text, max_output_length) if split_text is not None else [text[i:i + max_output_length] for
                                                                                      i in range(0, len(text),
                                                                                                 max_output_length)]
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


def generate_large_text(instruction, max_tokens_lenghts=10000):
    text = ""
    heading = "start"
    # hardcoded, for gpt3.5
    # counting chars but the right is to count tokens
    while len(text) + 3500 < max_tokens_lenghts:
        append_text = openai_call(
            f"I am generating a large text. {instruction[round(len(text) / 2):]}. Heading: {heading}\n"
            f"Current text (last 100 chars, I must continue seamlessly): '{text[:-100]}'.\n\n"
            f"The continuation of the given text is:")
        print(append_text)
        text += append_text
        heading = openai_call(f"I am generating a large text. My current heading: {heading}\n"
                                   f"Current text. (last 100 chars, I must continue seamlessly): '{text[:-100]}'.\n\n"
                                   f"Given the current text, what am I doing/heading? If the text is finished, I must answer with _end_of_text_. New heading:")
        print(heading)
        if '_end_of_text_' in heading.lower():
            break

    print(text)
    return text
