#!/usr/local/bin/python
from collections import defaultdict
import random
import sys

markov = defaultdict(list)
STOP_WORD = '\n'
CHAIN_LENGTH = 2


def add_to_brain(phrase, chain_length, write_to_file=False):
    if write_to_file:
        with open('training_text.txt', 'a') as f:
            f.write(phrase + '\n')
    bufr = [STOP_WORD] * chain_length
    for word in phrase.split():
        markov[tuple(bufr)].append(word)
        del bufr[0]
        bufr.append(word)
    markov[tuple(bufr)].append(STOP_WORD)


def generate_sentence(phrase, chain_length, max_words=10000):
    # capitalize the input phrase because that's how we've stored them in the brain
    phrase = phrase.upper()
    parts = phrase.split()
    # get all overlapping n-tuples from the sentence parts, where n is chain_length
    all_tuples = [tuple(values) for values in zip(*[parts[i:] for i in range(chain_length)])]
    # generate a larger list of n-tuples where tuples with larger response pools have more representation
    # (adding, as one element, the initial STOP_WORD tuple for some spice and to ward against an empty list)
    weighted_tuples = [t for tup in all_tuples for t in [tup] * len(markov[tup])] + [(STOP_WORD,) * chain_length]
    # pick from that list to kick off our sentence
    start_path = random.choice(weighted_tuples)

    # create two copies of it, one as the eventual response and one as the working buffer
    bufr = list(start_path)
    response = bufr[:]

    # filter for all non terminal responses in case we run into a dead end
    all_non_terminal_responses = [v for v in markov.values() if set(v) != {'\n'}]
    # loop until we terminate from a stop word (likely) or hit max_words (unlikely)
    for i in xrange(max_words):
        response_path = markov[tuple(bufr)]
        if not response_path:
            # this is a bit of an abstraction leak.  if we miss on the defaultdict key, it creates an entry
            # in the brain with an empty list as its value, which we don't want floating around. delete it!
            del markov[tuple(bufr)]
            # this is the dead end we were worried about, so just pick a random response path
            response_path = random.choice(all_non_terminal_responses)
        next_word = random.choice(response_path)
        if next_word == STOP_WORD:
            # all done!
            break
        # otherwise keep going, append the next word to our eventual response and rotate the working buffer
        response.append(next_word)
        del bufr[0]
        bufr.append(next_word)

    return ' '.join(response)


def user_sentences(name):
    nametag = '<{0}>'.format(name)
    with open("/usr/home/sdmiller/text/irc/DWA-#anim_quad.log") as source:
        return [l.split(nametag)[1].strip() for l in source.readlines() if nametag in l]

if __name__ == '__main__':
    username = sys.argv[1]
    sentences = user_sentences(username)
    print "GENERATING {0}.BOT FROM {1} IRC MESSAGES...".format(username.upper(), len(sentences))

    for s in sentences:
        add_to_brain(s.upper(), CHAIN_LENGTH)

    user_in = True
    while user_in:
        try:
            user_in = raw_input("> ")
        except EOFError:
            sys.exit("\n")

        answer = generate_sentence(user_in, CHAIN_LENGTH).strip()
        print(answer if answer else '...')
