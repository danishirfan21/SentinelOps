FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# The base image's stale Yarn source has no corresponding signing key. Remove it
# so Docker-in-Docker can update APT and install its engine normally.
RUN rm -f /etc/apt/sources.list.d/yarn*.list
