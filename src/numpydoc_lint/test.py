# noqa: W0101
"""Test."""

# noqa: I0010
MY_CONST = "hello world"
r"""TEST.{MY_CONST} """
#
#
# #
# # # def __LOL(x):
# # #     return print(x)
# #
# #
# class Test:
#     """TEST this is a long wi
#     winding thing im writing.
#     please read me not.
#     """
#
#     def __init__(self, test, *args, **kwargs):
#         """
#         Construct a new Test.
#
#         .. deprecated:: 1.0
#         Lorem ipsum dolor sit amet, officia excepteur ex fugiat reprehenderit
#         enim labore culpa sint ad nisi Lorem pariatur mollit ex esse
#         exercitation amet. Nisi anim cupidatat excepteur officia. Reprehenderit
#         nostrud nostrud ipsum Lorem est aliquip amet voluptate voluptate dolor
#         minim nulla est proident. Nostrud officia pariatur ut officia. Sit
#         irure elit esse ea nulla sunt ex occaecat reprehenderit commodo officia
#         dolor Lorem duis laboris cupidatat officia voluptate. Culpa proident
#         adipisicing id nulla nisi laboris ex in Lorem sunt duis officia
#         eiusmod. Aliqua reprehenderit commodo ex non excepteur duis sunt velit
#         enim. Voluptate laboris sint cupidatat ullamco ut ea consectetur et est
#         culpa et culpa duis.
#
#         .. deprecated:: 1.0
#         Lorem ipsum dolor sit amet, qui minim labore adipisicing minim sint
#         cillum sint consectetur cupidatat.
#
#         .. deprecated:: 1.0
#
#         Params
#         ------
#         test.
#
#         .. versionadded 10
#
#
#         Examples
#         --------
#         This is an example.
#
#         >>> from test import test
#         >>> test.print()
#
#         Parameters
#         ----------
#         test : int
#             The int.
#         *args : list
#             The args
#         **kwargs : dict
#             The kwargs
#
#         """
#         pass
#
#
# def no_summary():
#     """"""
#     pass
#
#
# class NoSummary:
#     """"""
#
#     def no_summary(self):
#         """"""
#
#
# class NotCapitalNoPeriod:
#     """a great summary."""
#
#     def no_capital(self):
#         """
#         not capital no period.
#
#         An exteded
#         """
#
#
# class HeadingWhiteSpaces:
#     """Test."""
#
#     def __init__(self):
#         """Test."""
#
#
# def genitive_s():
#     """Returns the longest string."""
#
#
# class GenitiveS:
#     """Represents a class."""
#
#     def genitive_s(self):
#         """Represents a method."""
#         pass


import numpy as np


# noqa: H0003
class Test:
    # noqa: SS11
    def test(self):
        pass


def _array_or_scalar(x, squeeze=True):
    if not isinstance(x, np.ndarray):
        return x

    if x.size == 1:
        return x.item()
    else:
        return np.squeeze(x) if squeeze else x


def test(*, a: int, b, c, d: int = 20):
    """
    Summary.

    Extended summary.

    Examples
    --------
    >>> from test import test

    Parameters
    ----------
    a : {test, test}
    q : integer
    b : object or integer
        Test b.
    c : object, optional
        Test c.
    x : object
        A parameter.

    **kwargs :OrderedDict or dict.
        Other arguments.
    unkown : object
        Unkown test.

    See Also
    --------
    test : a test function,
    :obj:`test` : test func

    """
    pass


# noqa: W0101
def test_wrong_order(a, b, c):
    """
    Summary.

    Extended.

    Parameters
    ----------
    a : int
        Test.
    c : int
        Test.
    b : int
        Test.

    Returns
    -------
    wrongs : int
        test
        .. deprecated:: 1.0
    rights : int
        The numver in right order::
            Test
            Test
    """
    return None
