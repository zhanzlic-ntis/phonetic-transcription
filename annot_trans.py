#!/usr/bin/env python3
# coding: utf-8

import re
import sys
from phon_polish import ipa_polish

punct_symbols = [".", ",", ";", ":", "!", "?", "-", "…"]

def trans_utt(line: str, phn_brackets: tuple = ("[", "]"), phn_separator: str = "", id_separator: str = " ") -> str:

    if "|" in line:
        utt_name, text = line.split("|", maxsplit=1)
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

    text = text.strip().lstrip(".,;-—!? ").replace("—", "-").replace('...', '…').replace('--', '-')

    phn_trans = ipa_polish(text)
    if phn_trans is None:
        return None

    tokens_txt = text.split()
    tokens_phn = phn_trans.strip().split("   ")
    tokens_phn = [ token.strip().replace(" ", phn_separator) for token in tokens_phn ]
    tokens_phn = [ token for token in tokens_phn if token not in ("|", "||", "") ]

    idx_phn = 0
    merged = list()

    for token_txt in tokens_txt:
        if token_txt in punct_symbols: # standalone punctuation or symbol
            merged.append(token_txt)
        else:
            if idx_phn >= len(tokens_phn):
                print("Cannot merge:", file=sys.stderr)
                print(tokens_txt, file=sys.stderr)
                print(tokens_phn, file=sys.stderr)
                return None

            punct = ""

            token_phn = tokens_phn[idx_phn]
            if token_phn[-1] == ":" and token_txt[-1] == ":":  # remove forgotten ":"
                token_phn = token_phn[:-1]

            while token_txt[-1] in punct_symbols:
                punct = token_txt[-1]
                token_txt = token_txt[:-1]
                if token_txt == "":
                    print("Cannot merge:", file=sys.stderr)
                    print(tokens_txt, file=sys.stderr)
                    print(tokens_phn, file=sys.stderr)
                    return None

            merged.append(token_txt + phn_brackets[0] + token_phn + phn_brackets[1] + punct)
            idx_phn += 1

    if len(merged) > 0:
        merged_str = " ".join(merged)
        return f"{utt_name}{id_separator}{merged_str}"
    else:
        return None


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