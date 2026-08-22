import time, os

basedir = os.path.abspath(os.path.dirname(__file__))
secretdir = os.path.join(basedir, 'app', 'appdata', 'secrets')

# Read secret key from file
def readKey(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        key = file.read().strip()
    if len(key) < 64:
        raise ValueError('Saved secret key is invalid')
    return key

# Generate new keys
def createKey(filename):
    key = os.urandom(64).hex()
    try:
        filenumber = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    # If another worker is creating the file
    except FileExistsError:
        for attempt in range(50):
            try:
                return readKey(filename)
            except (OSError, ValueError):
                time.sleep(0.02)
        raise RuntimeError('Secret key file could not be read')
    with os.fdopen(filenumber, 'w', encoding='utf-8') as file:
        file.write(key)
        file.flush()
        os.fsync(file.fileno())
    return key

def getSecret(name):
    # Use the environment variable when one has been provided
    envkey = os.environ.get(name)
    if envkey:
        return envkey
    # Otherwise, load or create a persistent random key
    os.makedirs(secretdir, exist_ok=True)
    filename = os.path.join(secretdir, name.lower() + '.txt')
    # Read file if it exists and is valid
    try:
        return readKey(filename)
    # If file not found, create a new key
    except FileNotFoundError:
        return createKey(filename)
    # If invalid file, don't overwrite
    except (OSError, ValueError) as error:
        raise RuntimeError('Secret key file could not be read: ' + filename) from error