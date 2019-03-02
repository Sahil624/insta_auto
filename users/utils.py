import random
import string

# Length of random tokens
N = 32


def generate_random_token():
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_lowercase + string.hexdigits)
        for _ in
        range(N))
