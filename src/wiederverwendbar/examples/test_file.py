from pathlib import Path

from wiederverwendbar.functions.test_file import test_file

if __name__ == '__main__':
    generated_file = test_file(1, 'MB')

    # move the file to the current directory
    generated_file = generated_file.replace(Path(generated_file.name))

    input("Press any key to remove the generated file.")

    # remove the file
    generated_file.unlink()
