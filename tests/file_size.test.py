

def get_file_size(file_path):
    """
        This function calculates the size of a file in bytes.

        Args:
        - file_path (str): The file path of the file to be calculated.
        
        Returns:
        - int: The size of the file in bytes.
    """
    try:
        # Open the file in binary mode
        with open('./db.test.py', 'rb') as file:
            # Read the file content
            file_content = file.read()
            # Calculate the size of the file in bytes
            file_size = len(file_content)
            return file_size
    except FileNotFoundError:
        # If the file is not found, return an error message
        return "File not found"

