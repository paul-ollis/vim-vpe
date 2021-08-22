Module vpe.channels
===================

.. py:module:: vpe.channels

Development of channel support.

JSChannel
---------

.. py:class:: vpe.channels.JSChannel(...)

    .. code::

        JSChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper around a Vim channel in javascript mode.

JsonChannel
-----------

.. py:class:: vpe.channels.JsonChannel(...)

    .. code::

        JsonChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper around a Vim channel in json mode.

NLChannel
---------

.. py:class:: vpe.channels.NLChannel(...)

    .. code::

        NLChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper for a newline based channel.

RawChannel
----------

.. py:class:: vpe.channels.RawChannel(...)

    .. code::

        RawChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper for a raw channel.

VimChannel
----------

.. py:class:: vpe.channels.VimChannel(varname: str)

    Simple proxy for a :vim:`Channel`.

    This manages keeping the underlying Vim channel object alive, by storing
    it in a global Vim variable.

    **Parameters**

    .. container:: parameters itemdetails

        *varname*
            The name of the a vim variable currently referencing the
            :vim:`Channel`.


    **Attributes**

        .. py:attribute:: varname

            The name of a Vim variable holding a reference to the underlying
            Vim channel object. This is provided for debugging purposes.

    **Properties**

        .. py:method:: chid()
            :property:

            The ID for this channel.

        .. py:method:: closed()
            :property:

            True of the channel could not be opened or has been closed.

        .. py:method:: info()
            :property:

            Get the information for a channel.

    **Methods**

        .. py:method:: vpe.channels.VimChannel.close()

            Mark as closed and release the underlying reference variable.