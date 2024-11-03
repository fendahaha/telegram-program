import json


def file_write(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)


def file_read(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def file_write_json(data, filename):
    file_write(json.dumps(data, ensure_ascii=False), filename)


def file_read_json(filename):
    return json.loads(file_read(filename))


def chunk_list(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
