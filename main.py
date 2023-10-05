import os
from bot import Bot

if __name__ == '__main__':
    os.mkdir('downloads') if not os.path.isdir('downloads') else None
    Bot().run()
