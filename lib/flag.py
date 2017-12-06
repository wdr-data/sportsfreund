OFFSET = 127462 - ord('A')


def flag(code):
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)
