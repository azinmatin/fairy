# coding=utf-8
import db_handler as dbh
from user_page_crawler import User_Page_Crawler
from user_crawler_db import UserCrawler
import graph_embedding.pme.data_preparation as pmedp
from crawl_graph_entities import Crawl_Graph_Entities
from interaction_graph import Interaction_Graph
from environment import Environment
import Utils as util
import logging
from pymongo import MongoClient
import time
import argparse
from ConfigParser import ConfigParser
import os
import sys
from datetime import datetime
import json
import random
import networkx as nx
from networkx.readwrite.gml import literal_destringizer
import numpy as np
import urllib
import pandas as pd


class Feature_Extractor:
    def __init__(self):
        self.pattern_frequency_dict = util.read('lastfm_pattern_frequency.txt')
        self.pattern_confidence_dict = util.read(
            'lastfm_pattern_confidence.txt')
        # pairwise similarity of the tags based on SIF similarity
        # described in paper
        # "A Simple but Tough-to-Beat Baseline for Sentence Embedding"
        # https://openreview.net/pdf?id=SyK00v5xx
        self.tags_sif_similarity = pd.read_csv(
            '../sif/examples/tags_sif_similarity', sep='\t', encoding='utf-8')

    def extract_features(self, path, pattern):
        # users features
        f1, f11, f12, f13 = self.aggregate_user_influence(path)
        features = [f1, f11, f12, f13]

        # category features
        f2, f21 = self.aggregate_category_specificity(path)
        features.append(f2)
        features.append(f21)

        # item features
        f3 = self.aggregate_item_specificity(path, pattern)
        features.append(f3)
        f4 = self.aggregate_item_engagement(path, pattern)
        features.append(f4)

        # path frequency
        if pattern in self.pattern_frequency_dict:
            f5 = self.pattern_frequency_dict[pattern]
        else:
            f5 = None
        features.append(f5)

        # path confidence
        if pattern in self.pattern_confidence_dict:
            f6 = self.pattern_confidence_dict[pattern]
        else:
            f6 = None
        features.append(f6)

        # path relevance score to start user
        f7 = self.path_relevance_user(path)
        features.append(f7)

        # path relevance score to rec
        f8 = self.extract_tags_sif_similarity(path, pattern)
        features.append(f8)

        # path length
        f9 = len(path)
        features.append(f9)

        # path recency
        f10 = self.path_recency(path, pattern)
        features.append(f10)

        # path edge weights (edge multiplicity)
        f11 = self.aggregate_edge_weight(path, pattern)
        features.append(f11)

        # path edge counts
        cc = self.intermediate_components_count(pattern)
        for elem in cc:
            features.append(elem)

        self.num_features = len(features)

        return features

    def aggregate_user_influence(self, path):
        """
        Todo:
            compute:
            * avg. users influence (np.followers/no.followees)
            * avg. no. scrobbles
            * avg. no. artists the user has listened to
            * avg. no. tracks the user loves
        """
        return agg_influnece, agg_scrobble_num, agg_artist_num, agg_love_num

    def aggregate_category_specificity(self, path):
        """
        Todo:
            compute:
            * avg. taxonomical path of tags on path
            * 1/avg. number of tags' children
        """
        return agg_level_num, 1/agg_children_num

    def extract_tags_sif_similarity(self, path, pattern_list):
        """
        Todo:
            * This function should compute similarity
            of recommendation's tags to those of items on
            path using cosine similarity in
            sif embedding space. The pairwise
            tags similarities s stored in
            self.tags_sif_similarity
        """
        return sim

    def path_relevance_user(self, path):
        user = path[0]
        index = 1
        rel = []
        while index < len(path) - 1:
            current_node = path[index]
            relevance = 0
            con_paths = nx.all_simple_paths(
                self.graph, user, current_node, cutoff=2)
            for con_path in con_paths:
                if len(con_path) >= 5:
                    break
                relevance += len(self.ig.find_path_type(con_path))
            rel.append(relevance)
            index += 1
        return self.aggregate_func(rel)

    def path_recency(self, path, pattern_list):
        """
        Todo:
            * timestamp = timestamp of the most recent edge
        """
        path_date = datetime.strptime(timestamp, '%Y-%m-%d')
        feed_date = datetime.strptime(self.date, '%Y-%m-%d')
        return (feed_date - path_date).days

    def aggregate_edge_weight(self, path, pattern):
        """
        Todo:
            * should return the avg. multiplicity of the edges
        """
        return avg_multiplicity

    def aggregate_item_engagement(self, path, pattern_list):
        """
        Todo:
            * should compute the avg. no. scrobbles of items
            * should compute the avg. no. listeners of items
        """
        return (avg_scrobble_num + avg_listen_num) / 2.0

    def aggregate_item_specificity(self, path, pattern):
        """
        Todo:
            compute:
            * avg. 1/no. of item's tags

        """
        return avg_spec

    def intermediate_components_count(self, pattern_list):
        # edge counts
        sang_count = pattern_list.count('sang')
        has_track_count = pattern_list.count('has-track')
        has_tag_count = pattern_list.count('has-tag')
        follows_count = pattern_list.count('follows')
        listened_to_count = pattern_list.count('listened-to')
        loves_track_count = pattern_list.count('loves-track')
        res = [sang_count, has_track_count, has_tag_count,
               follows_count, listened_to_count, loves_track_count]
        return res


if __name__ == '__main__':
    fe = Feature_Extractor()

    # loading pairs of explanation
    # with the following format
    # pair_id, path1, pattern1, path2, pattern2, user, date
    # separated by tabs
    pair_segments = {}
    with open('pairs.txt') as f_in:
        for line in f_in:
            t = line.strip().split('\t')
            pair_id, path1, pattern1, path2, pattern2, user, date = t
            d = {
                'pair_id': pair_id, 'path1': path1, 'pattern1': pattern1,
                'path2': path2, 'pattern2': pattern2, 'user': user,
                'date': date
                }
            if user not in pair_segments:
                pair_segments[user] = {}
            if date not in pair_segments[user]:
                pair_segments[user][date] = []
            pair_segments[user][date].append(dict(d))

    for user in pair_segments.keys():
        for date in pair_segments[user].keys():
            file_path = ''  # interaction graph of user on date 'date'
            g = nx.read_gml(file_path, destringizer=literal_destringizer)
            fe.set_graph(g)
            fe.set_date(date)
            for d in pair_segments[user][date]:
                path1 = d['path1']
                path2 = d['path2']
                pattern1 = d['pattern1']
                pattern2 = d['pattern2']
                # features can be stored in a file or in the database
                fs1 = fe.extract_features(path1, pattern1)
                fs2 = fe.extract_features(path2, pattern2)
