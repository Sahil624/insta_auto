import random


def add_time(time):
    """ Make some random for next iteration"""
    return time * 0.9 + time * 0.2 * random.random()


# def print_dict(dict):
#     # for x in dict:
#     #     print(x)
#     #     for y in dict[x]:
#     #         print(y, ':', dict[x][y])
#     print(str(dict['likes_per_day']))
