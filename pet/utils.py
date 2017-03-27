import os


def makedirs(exists_ok=False, *args, **kwargs):
    try:
        return os.makedirs(*args, **kwargs)
    except OSError as e:
        if not exists_ok:
            raise e