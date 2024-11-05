#!/usr/bin/env bash


sudo find EMAC/django/static/media/resources \( -type d \) -exec chmod a+rx {} \;

sudo find . -type f \( -iname "*.css" -o -iname "*.js" -o -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.gif" -o -iname "*.svg" \) -exec chmod a+r {} \;