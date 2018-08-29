*******
Roadmap
*******
The project is currently focusing on three milestones:

* `Bounded Badger`_: A more secure HoneyBadgerBFT that no longer requires
  unbounded buffers for protocol messages.
* `Test Network`_: HoneyBadgerBFT in action with a long-running test network.
* `Release 1.0`_: Towards a better and more stable HoneyBadgerBFT Python
  implementation.

An overview of each milestone is given below.


`Bounded Badger`_
=================
The main goal of this milestone is to implement a CHECKPOINT mechanism that
will allow the HoneyBadgerBFT protocol to only require bounded storage. Please
see `amiller/honeybadgerbft#57`_ for a detailed description of the issue, its
motivation, and benefits.

Overall, this should make HoneyBadgerBFT more secure, (e.g.: resilient to DoS
attacks), and provide a way for nodes to catch up when they fall out of sync.

The completion of this milestone will involve the following implementations:

* Tests that reproduce problems stemming from the unbounded-buffers approach
  (`#17`_).
* Threshold signature upon the finalization of a block of transactions (
  `#15`_).
* Broadcasting and reception of CHECKPOINT messages along with a "message
  bounding" behavior (`#16`_).
* Message bounding of ABA (`#22`_).
* Recovery mechanism aka "speedybadger" (`#18`_, `#21`_, `#33`_).
* Garbage collection of "outdated" outgoing protocol messages (`#19`_, `#7`_).

To stay up-to-date with the issues the milestone comprises, see the milestone
on Github at https://github.com/initc3/HoneyBadgerBFT-Python/milestone/3.


`Test Network`_
===============
At a minimum this milestone wishes to have a long running test network
deployed of approximately 10+ nodes.

The network will be administered by a trusted party to start with, and
will consist of nodes running the Python implementation. In the near future,
we would like to have an heteregenous network such that some nodes also run
implementations written in other languages (e.g.: Go, Rust, Erlang, Haskell).

In order to support the delpoyment and operation of the test network, the
following tasks are planned:

* Persistence layer for transactions, blocks, and "system state" (`#20`_,
  `#21`_).
* Update and fix the relevant legacy experiments, including benchmark tests
  (`#23`_).
* Provide authenticated communications, with persistent connections (`#25`_,
  `#26`_).
* Setup minimal logging infrastructure to help monitoring and troubleshooting
  (`#24`_).
* Provide a basic dashboard to view the network's state and activity (`#27`_,
  `#35`_).

To stay up-to-date with the issues the milestone comprises, see the milestone
on Github at https://github.com/initc3/HoneyBadgerBFT-Python/milestone/2.


`Release 1.0`_
==============
Release planned to appear after the completion of the bounded badger and
test network milestones. 

This milestone aims to make the implementation of better quality by addressing
most of the opened issues, meaning:

* Resolving opened bugs (`#31`_, `#46`_).
* Making sure the subprotocols are well tested (`#34`_).
* Implementing the proposed batch size to be floor(B/N) (`#28`_).
* Implementing a coin schedule for ABA (`#38`_).
* Properly handling redundant messages in ABA (`#10`_).
* Providing an overall good documentation of the project (`#30`_, `#43`_).
* Implementing general best software engineering practices (`#13`_, `#14`_,
  `#29`_, `#32`_, `#40`_, `#41`_, `#42`_, `#44`_).

To stay up-to-date with the issues the milestone comprises, see the milestone
on Github at https://github.com/initc3/HoneyBadgerBFT-Python/milestone/1.


For Future Milestones
=====================

Message Formats
---------------
Serialization/deserialization of messages using protocol buffers.

Distributed Key Generation
--------------------------
Dynamic addition and removal of nodes.


.. _Bounded Badger: https://github.com/initc3/HoneyBadgerBFT-Python/milestone/3
.. _Test Network: https://github.com/initc3/HoneyBadgerBFT-Python/milestone/2
.. _Release 1.0: https://github.com/initc3/HoneyBadgerBFT-Python/milestone/1
.. _amiller/honeybadgerbft#57: https://github.com/amiller/HoneyBadgerBFT/issues/57
.. _#7: https://github.com/initc3/HoneyBadgerBFT-Python/issues/7
.. _#10: https://github.com/initc3/HoneyBadgerBFT-Python/issues/10
.. _#13: https://github.com/initc3/HoneyBadgerBFT-Python/issues/13
.. _#14: https://github.com/initc3/HoneyBadgerBFT-Python/issues/14
.. _#15: https://github.com/initc3/HoneyBadgerBFT-Python/issues/15
.. _#16: https://github.com/initc3/HoneyBadgerBFT-Python/issues/16
.. _#17: https://github.com/initc3/HoneyBadgerBFT-Python/issues/17
.. _#18: https://github.com/initc3/HoneyBadgerBFT-Python/issues/18
.. _#19: https://github.com/initc3/HoneyBadgerBFT-Python/issues/19
.. _#20: https://github.com/initc3/HoneyBadgerBFT-Python/issues/20
.. _#21: https://github.com/initc3/HoneyBadgerBFT-Python/issues/21
.. _#22: https://github.com/initc3/HoneyBadgerBFT-Python/issues/22
.. _#23: https://github.com/initc3/HoneyBadgerBFT-Python/issues/23
.. _#24: https://github.com/initc3/HoneyBadgerBFT-Python/issues/24
.. _#25: https://github.com/initc3/HoneyBadgerBFT-Python/issues/25
.. _#26: https://github.com/initc3/HoneyBadgerBFT-Python/issues/26
.. _#27: https://github.com/initc3/HoneyBadgerBFT-Python/issues/27
.. _#28: https://github.com/initc3/HoneyBadgerBFT-Python/issues/28
.. _#29: https://github.com/initc3/HoneyBadgerBFT-Python/issues/29
.. _#30: https://github.com/initc3/HoneyBadgerBFT-Python/issues/30
.. _#31: https://github.com/initc3/HoneyBadgerBFT-Python/issues/31
.. _#32: https://github.com/initc3/HoneyBadgerBFT-Python/issues/32
.. _#33: https://github.com/initc3/HoneyBadgerBFT-Python/issues/33
.. _#34: https://github.com/initc3/HoneyBadgerBFT-Python/issues/34
.. _#35: https://github.com/initc3/HoneyBadgerBFT-Python/issues/35
.. _#38: https://github.com/initc3/HoneyBadgerBFT-Python/issues/38
.. _#40: https://github.com/initc3/HoneyBadgerBFT-Python/issues/40
.. _#41: https://github.com/initc3/HoneyBadgerBFT-Python/issues/41
.. _#42: https://github.com/initc3/HoneyBadgerBFT-Python/issues/42
.. _#43: https://github.com/initc3/HoneyBadgerBFT-Python/issues/43
.. _#44: https://github.com/initc3/HoneyBadgerBFT-Python/issues/44
.. _#46: https://github.com/initc3/HoneyBadgerBFT-Python/issues/46
