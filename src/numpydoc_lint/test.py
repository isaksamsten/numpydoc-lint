"""Test."""

MY_CONST = "hello world"
r"""TEST.{MY_CONST} """


#
# # def __LOL(x):
# #     return print(x)
#
#
class Test:
    """TEST."""

    def __init__(self, test, *args, **kwargs):
        """
        Construct a new Test.

        Lorem ipsum dolor sit amet, officia excepteur ex fugiat reprehenderit
        enim labore culpa sint ad nisi Lorem pariatur mollit ex esse
        exercitation amet. Nisi anim cupidatat excepteur officia. Reprehenderit
        nostrud nostrud ipsum Lorem est aliquip amet voluptate voluptate dolor
        minim nulla est proident. Nostrud officia pariatur ut officia. Sit
        irure elit esse ea nulla sunt ex occaecat reprehenderit commodo officia
        dolor Lorem duis laboris cupidatat officia voluptate. Culpa proident
        adipisicing id nulla nisi laboris ex in Lorem sunt duis officia
        eiusmod. Aliqua reprehenderit commodo ex non excepteur duis sunt velit
        enim. Voluptate laboris sint cupidatat ullamco ut ea consectetur et est
        culpa et culpa duis.

        Lorem ipsum dolor sit amet, qui minim labore adipisicing minim sint
        cillum sint consectetur cupidatat.

        .. deprecated:: 1.0

        Params
        ------
        test.

        .. versionadded 10


        Examples
        --------
        This is an example.

        >>> from test import test
        >>> test.print()

        Parameters
        ----------
        test : int
            The int.
        *args : list
            The args
        **kwargs : dict
            The kwargs

        """
        pass


def no_summary():
    """"""
    pass


class NoSummary:
    """"""

    def no_summary(self):
        """"""


class NotCapitalNoPeriod:
    """a great summary"""

    def no_capital(self):
        """
        not capital no period

        An exteded
        """

class HeadingWhiteSpaces():
    """
       Test
    """

    def __init__(self):
        """ Test."""
