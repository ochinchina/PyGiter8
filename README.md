# Why this project

When I tried to create scala project from giter8 template behind firewall, I can't create project from giter8 template successfully. So I decided to re-implements the giter8 in python to practice scala from giter8 template.

The giter8 template can be regarded as a generic project template also, so if the project is not a java related project or is not a sbt related project, we can still use this python implemented giter8 tool to create project from a template. Such as if a python project is in giter8 template, we can use this tool to create a python project from giter8 template.

# Usage

A project template can be put in github, so this tool can create a project from the github like below:

```shell

$ giter8.py scala/hello-world.g8

```

A project template can be put in a directory and this tool can create project from this local template like:

```shell

$ giter8.py ./my_template_project

```
