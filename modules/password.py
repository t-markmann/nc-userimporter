import random
import string

class PasswordGenerator:
    """
    A class to generate random passwords with a specified length.
    
    The generated password will always include at least one uppercase letter, 
    one lowercase letter, one digit, and one special character to ensure complexity.
    """

    def __init__(self, length=8):
        """
        Initializes the PasswordGenerator with the desired password length.
        
        Args:
            length (int): The length of the password to be generated. Defaults to 8.
                          Must be at least 4 to ensure inclusion of all character types.

        Raises:
            ValueError: If the provided password length is less than 4.
        """
        if length < 4:
            raise ValueError("Password length should be at least 4 to include all character types.")
        self.length = length

    def generate(self):
        """
        Generates a random password with the specified length.
        
        The password will always contain at least one character from each of the following:
        - Uppercase letters
        - Lowercase letters
        - Digits
        - Special characters
        
        Returns:
            str: A randomly generated password.
        """
        # Ensure the password contains at least one character from each category
        password = [
            random.choice(string.ascii_uppercase),   # At least one uppercase letter
            random.choice(string.ascii_lowercase),   # At least one lowercase letter
            random.choice(string.digits),            # At least one digit
            random.choice(string.punctuation)        # At least one special character
        ]

        # Pool of all possible characters
        all_characters = string.ascii_letters + string.digits + string.punctuation

        # Generate the remaining characters to match the desired password length
        password += [random.choice(all_characters) for _ in range(self.length - 4)]

        # Shuffle the list to ensure randomness of the character order
        random.shuffle(password)

        # Return the final password as a string
        return ''.join(password)
