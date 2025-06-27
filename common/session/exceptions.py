"""

A module for custom exceptions used in the session package.

"""


class DocumentNotFound(Exception):
    """
    Exception raised when a document is not found.

    Methods:
        - __init__(): Initializes the exception with an optional message.

    """

    def __init__(self, message: str = "Document not found") -> None:
        """
        Initializes the exception with an optional message.

        Args:
            message (str): The error message to be displayed. Defaults to "Document not found".

        Returns:
            None

        """
        self.message = message
        super().__init__(self.message)


class UnauthorizedAccess(Exception):
    def __init__(self, message="Only members of _admin_ group can access admin interface !"):
        self.message = message
        super().__init__(self.message)


class UnknownFileType(Exception):
    def __init__(self, message="Failed to recognize file type ! File formatting may be broken."):
        self.message = message
        super().__init__(self.message)


class UnsupportedFile(Exception):
    def __init__(self, message="Unsupported file type !"):
        self.message = message
        super().__init__(self.message)