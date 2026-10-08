class Transcript:
    def __init__(self, path): 
        self.path = path
        self.file = None
        self.set_tags = set()

    def open_file(self):
        self.file = open(self.path)

    def is_open(self):
        if self.file is None: 
            raise RuntimeError("file not open")

    def write(self, message):
        self.is_open()
        message = str(message)
        self.file.write(message)
        if not message.endswith("\n"):
            self.file.write("\n")
        self.file.flush()

    def write_tag(self, tag, value, quote=False):
        self.is_open()
        if tag in self.set_tags:
            raise RuntimeError("already exists")
        if quote:
            value = f'"{value}"'
        self.write(f"{tag} = {value}")
        self.set_tags.add(tag)
  

