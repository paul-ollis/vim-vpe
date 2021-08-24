=======================
Handling buffer changes
=======================

.. |Buffer| replace:: `vpe.Buffer`
.. |add_listener| replace:: `vpe.Buffer.add_listener`
.. |listener_add| replace:: :vim:`listener_add()`

Vim version 8.2 introduced the |listener_add| and supporting functions, which
allow you to immediately respond to changes to a buffer. VPE provides the
|add_listener| method to the |Buffer| class as its way of supporting this.

Currently this should be considered *very* experimental. Feel free to use it and
provide feedback, but be prepared for big changes in the next release of VPE.
