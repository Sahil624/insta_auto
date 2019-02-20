import random


def add_time(time):
    """ Make some random for next iteration"""
    return time * 0.9 + time * 0.2 * random.random()


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance
