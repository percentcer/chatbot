#!/usr/local/bin/python
from collections import defaultdict
import random
import sys
import tweepy
import argparse


markov = defaultdict(list)
STOP_WORD = '\n'
CHAIN_LENGTH = 2
MAX_TWEETS_PER_CALL = 200
MAX_TWEETS = 3200


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
    for i in range(max_words):
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

    response = response or ['...']
    return ' '.join(response).strip()


def user_tweets(name, api):

    user = api.get_user(name)
    total = user.statuses_count if user.statuses_count < MAX_TWEETS else MAX_TWEETS

    print("grabbing all tweets from {0} ({1})".format(user.screen_name, total))

    ret = []

    public_tweets = api.user_timeline(id=name, count=MAX_TWEETS_PER_CALL)
    count = len(public_tweets)
    while public_tweets:
        ret.extend([t.text for t in public_tweets])
        min_id = min(public_tweets, key=lambda t: t.id).id
        print("{0:.2f}% complete".format(count / total * 100))
        public_tweets = api.user_timeline(id=name, count=MAX_TWEETS_PER_CALL, max_id=min_id - 1)
        count += len(public_tweets)

    return ret


def authenticate_twitter(consumer_key, consumer_secret, access_token, access_token_secret):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)


def authenticate_facebook():
    pass


def main(clargs):
    api = authenticate_twitter(clargs.ck, clargs.cs, clargs.at, clargs.ats)
    tweets = user_tweets(clargs.username, api)

    print("GENERATING {0}.BOT...".format(clargs.username.upper(), len(tweets)))

    for s in tweets:
        add_to_brain(s.upper(), CHAIN_LENGTH)

    user_in = True
    while user_in:
        try:
            user_in = input("> ")
        except EOFError:
            break

        if user_in:
            print(generate_sentence(user_in, CHAIN_LENGTH))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a bot based on a twitter user.')
    parser.add_argument('username', metavar='username', type=str, help='twitter username')
    parser.add_argument('ck', metavar='consumer_key', help='OAuth consumer key')
    parser.add_argument('cs', metavar='consumer_key_secret', help='OAuth consumer key secret')
    parser.add_argument('at', metavar='access_token', help='OAuth access token')
    parser.add_argument('ats', metavar='access_token_secret', help='OAuth access token secret')
    args = parser.parse_args()
    main(args)