#!/bin/sh
exec docker run --rm -it -v `pwd`:/work prideglyco "$@"
