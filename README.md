# Static-Analyser

![master_ci](https://img.shields.io/jenkins/build/https/ci.elliothargreaves.com/job/Static%20Analyser.svg?label=master)
![python_versions](https://img.shields.io/badge/python-3.6%7C3.7-informational.svg)

##### dev

![dev_ci](https://img.shields.io/jenkins/build/https/ci.elliothargreaves.com/job/sa_test/PYTHON=python3.6.7,label_exp=python3.6.7.svg?label=python3.6)
![dev_ci](https://img.shields.io/jenkins/build/https/ci.elliothargreaves.com/job/sa_test/PYTHON=python3.7.2,label_exp=python3.7.2.svg?label=python3.7)

My final year project for my Computer Science degree at Newcastle University.

My intention for this software is to investigate the viability of generating
a model from source files and performing analysis on the model to try to
find issues with the source files. I rely heavily on using RegEx for matching 
code from the source files so it can be loaded into objects that can be 
serialised to and from JSON.

As a proof of concept this is ***far*** from being even remotely production
ready, and would benefit greatly from a rewrite in a faster language such
as Rust, however I chose python for its flexibility and my familiarity with
it.

It's been fun though! 😁 

I think with a rewrite, I would support languages with specific libraries
rather than trying to add support through TOML/JSON/text files. Would make
it much easier, and once a language is supported it's not like there needs
to be more people implementing it... a bit of a poor design choice by me
imo but live and learn.