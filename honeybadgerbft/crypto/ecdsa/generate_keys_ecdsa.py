import argparse
import pickle

from coincurve import PrivateKey


def generate_key_list(players):
    return [PrivateKey().secret for _ in range(players)]


def main():
    """ """
    parser = argparse.ArgumentParser()
    parser.add_argument('players', help='The number of players')
    args = parser.parse_args()
    players = int(args.players)
    keylist = generate_key_list(players)
    print(pickle.dumps(keylist))


if __name__ == '__main__':
    main()
