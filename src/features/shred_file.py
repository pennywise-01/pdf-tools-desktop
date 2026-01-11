import os
import random
import string

def shred_file(file_path, passes=3):
    """
    Securely deletes a file using multiple overwrite passes.
    DoD 5220.22-M style (simplified to 3 passes).
    
    Args:
        file_path (str): Path to file to shred.
        passes (int): Number of overwrite passes.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    length = os.path.getsize(file_path)

    with open(file_path, "wb") as f:
        # Pass 1: Zeros
        f.write(b'\x00' * length)
        f.flush()
        os.fsync(f.fileno())
        f.seek(0)
        
        # Pass 2: Ones
        f.write(b'\xFF' * length)
        f.flush()
        os.fsync(f.fileno())
        f.seek(0)
        
        # Pass 3: Random
        f.write(os.urandom(length))
        f.flush()
        os.fsync(f.fileno())
    
    # Rename to obscure filename before deletion
    dir_name = os.path.dirname(file_path)
    new_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    new_path = os.path.join(dir_name, new_name)
    os.rename(file_path, new_path)
    
    os.remove(new_path)
