import gzip


def extract(file_path: str, copy: bool) -> gzip.GzipFile:
    with gzip.open(file_path, 'rb') as f:
        gz = f.read()

    print(f'{file_path} opened')

    if copy:
        with open(f'{file_path}.xml', 'w+') as f:
            f.write(gz.decode('utf-8'))
        print(f'copy written: {file_path}.xml')

    return gz


def compress(data, file_path: str) -> None:
    with gzip.open(file_path, 'wb+') as f:
        f.write(data)
