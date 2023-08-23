"""
Default maximum lengths for string fields. Please use these, except if you have a very specific
length need (such as, for instance, for an ISSN for which you know the precise length).
"""


SHORT = 64
NORMAL = 256
DESCRIPTION = 1800  # an A4 full of text should be enough?
