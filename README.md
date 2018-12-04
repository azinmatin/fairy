# FAIRY: A Framework for Understanding Relationships between Users’ Actions and their Social Feeds

#### Author: [Azin Ghazimatin](http://people.mpi-inf.mpg.de/~aghazima/) (aghazima@mpi-inf.mpg.de)

## Overview
This repository contains the codes required for finding the explanation paths between the users and their social 
feeds in two specific platforms (Quora and Last.fm) and building the feature vectors to learn the ranking of the relevant 
and surprising paths.  

## Usage
In quora_main.py (and lastfm_main.py), the explanation paths of maximum length 4 (or 5 in Lastfm) are found. 
The feature vectors of the paths are computed in quora_feature_extraction.py (or lastfm_feature_extraction.py). 
Note that due to the compliance with the platforms' terms of service, we removed all the details related to the 
interactions graphs.

