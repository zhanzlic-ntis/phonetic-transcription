#!/usr/bin/env python3
# coding: utf-8

import re
import sys
from phon_polish import ipa_polish

punct_symbols = [".", ",", ";", ":", "!", "?", "-", "…", ")", "&"]

# ----------

def fix_text(text: str) -> str:

    text = text.replace("—", "-").replace("–", "-")  # unify hyphen symbols
    text = text.replace('...', '…').replace('..', '…').replace('--', '-')

    text = text.replace("!.", "!").replace(".!", "!")  # simplify punctuation combinations
    text = text.replace("?.", "?").replace(".?", "?")

    text = text.replace("\"", "").replace("„", "").replace("'", "")  # discard quotation marks
    text = text.replace("<unk>", "")  # remove unknown symbols
    
    # remove improper initial punctuation and whitespaces
    while len(text) > 0 and (text[0] in punct_symbols or text[0].isspace()):
        text = text[1:]

    return text

# ----------

def split_text(text: str) -> list:

    tokens_txt = list()
    for token_txt in text.split():

        if all(c in punct_symbols for c in token_txt): # standalone punctuation symbol(s)
            tokens_txt.append(token_txt)

        else:
            chars = ""
            for phn in token_txt:
                if phn in punct_symbols:
                    if len(chars) > 0:
                        tokens_txt.append(chars)
                        chars = ""
                    tokens_txt[-1] += phn
                else:
                    chars += phn

            if len(chars) > 0:
                tokens_txt.append(chars)

    return tokens_txt

# ----------

def parse_text(text: str) -> list:
    # returns list of tokens (text, phones, punctuation)

    tokens_txt = list()
    for token_txt in text.split():
        
        text = ""
        phones = ""
        punct = ""

        while len(token_txt) > 0 and token_txt[-1] in punct_symbols:  # cut terminal punctuation symbol(s)
            punct = token_txt[-1] + punct
            token_txt = token_txt[:-1]

        phon_flag = False
        for char in token_txt:
            
            if char == "[":
                phon_flag = True
            elif char == "]":
                phon_flag = False
            
            else:
                if phon_flag:
                    phones += char
                else:
                    text += char
        
        tokens_txt.append((text, phones, punct))

    return tokens_txt

# ----------

def get_text(tokens: list, include_phones: bool = True) -> str:
    
    text_items = list()
    for token in tokens:
        if include_phones and token[1]:
            text_items.append(f"{token[0]}[{token[1]}]{token[2]}")
        else:
            text_items.append(f"{token[0]}{token[2]}")
    
    return " ".join(text_items)

# ----------

def merge_tokens(tokens_orig: list, tokens_phn: list, phn_brackets=("[", "]")) -> str:
    
    items_merged = list()
    
    idx_phn = 0
    for token_orig in tokens_orig:
        
        if len(token_orig[0]) == 0 and len(token_orig[2]) > 0: # standalone punctuation symbol(s)
            items_merged.append(token_orig[2])
            continue

        if idx_phn >= len(tokens_phn):
            print("Cannot merge:", file=sys.stderr)
            print(tokens_orig, file=sys.stderr)
            print(tokens_phn, file=sys.stderr)
            return None
        
        for separator in [ "-", "." ]:
            if separator in token_orig[0]:
                token_phn = ""
                for segment in token_orig[0].split(separator):
                    if len(segment) > 0:
                        if token_phn != "":
                            token_phn += "+"
                        token_phn += tokens_phn[idx_phn]
                        idx_phn += 1
                break
        else:
            token_phn = tokens_phn[idx_phn]
            if token_phn[-1] == ":" and token_txt[-1] == ":":  # remove forgotten ":"
                token_phn = token_phn[:-1]
            idx_phn += 1
            
        if (len(token_orig[1]) > 0) and (token_orig[1] != token_phn): # add default and new transcription (when differ)
            token_phn = token_phn + " " + token_orig[1]

        items_merged.append(token_orig[0] + phn_brackets[0] + token_phn + phn_brackets[1] + token_orig[2])
        
    if idx_phn < len(tokens_phn):  # check if all phonetic tokens were merged
        print("Cannot merge:", file=sys.stderr)
        print(tokens_orig, file=sys.stderr)
        print(tokens_phn, file=sys.stderr)
    
    return " ".join(items_merged)

# ----------

def trans_utt(line: str, phn_brackets: tuple = ("[", "]"), phn_separator: str = "", id_separator: str = " ") -> str:

    if "|" in line:
        items = line.split("|")
        if len(items) <= 3:
            utt_name = items[0]
            text = items[1]
        else:
            print("Cannot parse line - too many separators \"|\":", file=sys.stderr)
            print(line, file=sys.stderr)
    else:
        utt_name, text = line.split(maxsplit=1)
    
    if re.search("\d", text):  # skip utterances with numbers
        return None

    utt_name = utt_name.strip()
    if utt_name.endswith(".wav"):
        utt_name = utt_name[:-4]

    idx = utt_name.rfind("/")
    if idx >= 0:
        utt_name = utt_name[idx+1:]

    text = fix_text(text)
    tokens = parse_text(text)
    #tokens_txt = split_text(text)

    phn_trans = ipa_polish(get_text(tokens, include_phones=False))
    if phn_trans is None:
        print("Cannot transcribe:", text, file=sys.stderr)
        return None

    tokens_phn = phn_trans.strip().split("   ")
    tokens_phn = [ token.strip().replace(" ", phn_separator) for token in tokens_phn ]
    tokens_phn = [ token for token in tokens_phn if token not in ("|", "||", "") ]

    idx_phn = 0
    merged_str = merge_tokens(tokens, tokens_phn, phn_brackets)

    if len(merged_str) > 0:
        return f"{utt_name}{id_separator}{merged_str}"
    else:
        return None

# ----------

# running script if it is used in shell (with stdin or path to file)
if __name__ == '__main__':

    if not sys.stdin.isatty():  # read from stdin
        for line in sys.stdin:
            trans = trans_utt(line)
            if trans:
                print(trans)

    else:  # read from file
        if len(sys.argv) == 2:
            with open(sys.argv[1], mode='r', encoding='utf-8') as f:
                for line in f:
                    trans = trans_utt(line)
                    if trans:
                        print(trans)
        else:
            print('Error: Use script in pipeline or give the path '
                  'to the relevant file in the first argument.')
