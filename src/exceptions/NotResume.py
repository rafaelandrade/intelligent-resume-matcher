class NotResume(Exception):
    def __init__(self, language: str, message=None):
        if message is None:
            if language.lower() in ['pt-br', 'pt', 'portuguese']:
                self.message = "O PDF não é um currículo válido"
            else:
                self.message = "The PDF is not a valid resume"
        else:
            self.message = message
            
        self.language = language
        super().__init__(self.message)
