import re

import tiktoken


def sentence_split(text: str) -> list[str]:
    single_sentence_list = re.split('(?<=[.!?。！？])\\s+', text)
    return single_sentence_list


def merge_sentences(single_sentence_list: list[str], max_tokens: int = 32768, encoding_name: str = 'o200k_base') -> list[str]:
    merged_sentence_list = []

    encoding = tiktoken.get_encoding(encoding_name)

    current_merged_sentence = None
    for sentence in single_sentence_list:
        chunk = current_merged_sentence + sentence if current_merged_sentence else sentence
        tokens = encoding.encode(chunk)
        if len(tokens) < max_tokens:
            current_merged_sentence = chunk
        else:
            merged_sentence_list.append(current_merged_sentence)
            current_merged_sentence = None

    if current_merged_sentence:
        merged_sentence_list.append(current_merged_sentence)

    return merged_sentence_list
