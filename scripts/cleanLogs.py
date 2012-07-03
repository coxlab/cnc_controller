#!/bin/bash

rm -f logs/.old_logs.tar
tar cvf logs/.old_logs.tar logs/*
rm -rf logs/*
