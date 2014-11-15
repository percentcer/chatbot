#!/usr/local/bin/python
from collections import defaultdict
import random
import sys

markov = defaultdict(list)
STOP_WORD = "\n"

def add_to_brain(message, chain_length, write_to_file=False):
    if write_to_file:
        with open('training_text.txt', 'a') as f:
            f.write(message + '\n')
    buffer = [STOP_WORD] * chain_length
    for word in message.split():
        markov[tuple(buffer)].append(word)
        del buffer[0]
        buffer.append(word)
    markov[tuple(buffer)].append(STOP_WORD)

def generate_sentence(message, chain_length, max_words=10000):
    message = message.upper()
    buffer = message.split()[:chain_length]

    if len(message.split()) > chain_length:
        message = buffer[:]
    else:
        message = [random.choice(random.choice(markov.values())) for i in range(chain_length)]
        
    all_non_terminal_responses = [v for v in markov.values() if v and v != ['\n']]
    for i in xrange(max_words):
        try:
            next_word = random.choice(markov[tuple(buffer)])
        except IndexError:            
            random_bin = random.choice(all_non_terminal_responses)
            next_word = random.choice(random_bin)
            message = []
        if next_word == STOP_WORD:
            break
        message.append(next_word)
        del buffer[0]
        buffer.append(next_word)

    return ' '.join(message)

def user_sentences(username):
    nametag = '<{0}>'.format(username)
    with open("/usr/home/sdmiller/text/irc/DWA-#anim_quad.log") as source:
        return [l.split(nametag)[1].strip() for l in source.readlines() if nametag in l]

if __name__ == '__main__':
    username = sys.argv[1]
    sentences = user_sentences(username)
    print "GENERATING {0}.BOT FROM {1} IRC MESSAGES...".format(username.upper(), len(sentences))

    for s in sentences:
        add_to_brain(s.upper(), 2)

    message = True
    while message:
        try:
            message = raw_input("? ")
        except EOFError:
            print
            break

        answer = generate_sentence(message, 2).strip()

        if answer:
            print(answer)
        else:
            print("...")
