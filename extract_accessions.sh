#!/bin/sh
exec jq -r '.[].accession'
