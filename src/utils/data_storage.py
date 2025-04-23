def save_data(data, filename):
    with open(filename, 'w') as file:
        file.write(data)

def load_data(filename):
    with open(filename, 'r') as file:
        return file.read()