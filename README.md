# HoneyBadgerBFT
The Honey Badger of BFT Protocols

<img width=200 src="http://i.imgur.com/wqzdYl4.png"/>

[![Travis branch](https://img.shields.io/travis/amiller/HoneyBadgerBFT/dev.svg)](https://travis-ci.org/amiller/HoneyBadgerBFT)
[![Codecov branch](https://img.shields.io/codecov/c/github/amiller/honeybadgerbft/dev.svg)](https://codecov.io/github/amiller/honeybadgerbft?branch=dev)

Most fault tolerant protocols (including RAFT, PBFT, Zyzzyva, Q/U) don't
guarantee good performance when there are Byzantine faults. Even the so-called
"robust" BFT protocols (like UpRight, RBFT, Prime, Spinning, and Stellar) have
various hard-coded timeout parameters, and can only guarantee performance when
the network behaves approximately as expected - hence they are best suited to
well-controlled settings like corporate data centers.

HoneyBadgerBFT is fault tolerance for the wild wild wide-area-network.
HoneyBadger nodes can even stay hidden behind anonymizing relays like Tor, and
the purely-asynchronous protocol will make progress at whatever rate the
network supports.


## Development Activities
Since its initial implementation, the project has gone through a substantial
refactoring, and is currently under active development.

At the moment, the following three milestones are being focused on:

* [Bounded Badger](https://github.com/initc3/HoneyBadgerBFT-Python/milestone/3)
* [Test Network](https://github.com/initc3/HoneyBadgerBFT-Python/milestone/2<Paste>)
* [Release 1.0](https://github.com/initc3/HoneyBadgerBFT-Python/milestone/1)

A roadmap of the project can be found in [ROADMAP.rst](./ROADMAP.rst).


### Contributing
Contributions are welcomed! To quickly get setup for development:

1. Fork the repository and clone your fork. (See the Github Guide
   [Forking Projects](https://guides.github.com/activities/forking/) if
   needed.)

2. Install [`Docker`](https://docs.docker.com/install/). (For Linux, see
   [Manage Docker as a non-root user](https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user)
   to run `docker` without `sudo`.)

3. Install [`docker-compose`](https://docs.docker.com/compose/install/).

4. Run the tests (the first time will take longer as the image will be built):

   ```bash
   $ docker-compose run --rm honeybadger
   ```

   The tests should pass, and you should also see a small code coverage report
   output to the terminal.

If the above went all well, you should be setup for developing
**HoneyBadgerBFT-Python**!

Interested in contributing to HoneyBadgerBFT? Developers wanted. Contact
ic3directors@systems.cs.cornell.edu for more info.


## License
This is released under the CRAPL academic license. See ./CRAPL-LICENSE.txt
Other licenses may be issued at the authors' discretion.
