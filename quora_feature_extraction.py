# coding=utf-8
import time
from datetime import datetime
import networkx as nx
import pandas as pd
from networkx.readwrite.gml import literal_destringizer
import Utils as util


class Feature_Extractor:
    def __init__(self):
        self.pattern_frequency_dict = util.read('quora_pattern_frequency.txt')
        self.pattern_confidence_dict = util.read('quora_pattern_confidence.txt')
        self.topics_lsa_similariy = \
            pd.read_csv('../topics_lsa_similarity', sep='\t', encoding='utf-8')
        # pairwise similarity of the topics based on SIF similarity
        # described in paper
        # "A Simple but Tough-to-Beat Baseline for Sentence Embedding"
        # https://openreview.net/pdf?id=SyK00v5xx
        self.topics_sif_similarity = \
            pd.read_csv('../sif/examples/topics_sif_similarity_sl',
                        sep='\t', encoding='utf-8')

    def set_graph(self, g):
        self.graph = g

    def set_date(self, date):
        self.date = date

    def extract_features(self, path, pattern):
        # users influence aggregate
        f1, f11, f12, f13, f14, f15 = self.aggregate_user_influence(path)
        features = [f1, f11, f12, f13, f14, f15]

        # category specificity
        f2, f21, f22, f23 = self.aggregate_category_specificity(path)
        features.append(f2)
        features.append(f21)
        features.append(f22)
        features.append(f23)

        # post engagement
        f3 = self.aggregate_post_engagement(path)
        features.append(f3)

        # post specificity: no. of tags
        f4 = self.aggregate_post_specificity(path)
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
        f8 = fe.extract_topic_sif_similarity(path)
        features.append(f8)

        # path length
        f9 = len(path)
        features.append(f9)

        # path recency
        # print 'path recency'
        f10 = self.path_recency(path)
        features.append(f10)

        # path edge counts
        cc = self.count_path_components(pattern)
        for elem in cc:
            features.append(elem)

        self.num_features = len(features)

        return features

    def aggregate_user_influence(self, path):
        """
        Todo:
            compute:
            * avg. users influence (no.followers/no.followees)
            * avg. no. edits
            * avg. no. questions answered
            * avg. no. questions asked
            * avg. no. posts
            * avg. no. editsblogs
        """
        return agg_influnece, agg_edits_num, agg_answers_num, \
               agg_questions_num, agg_posts_num, agg_blogs_num

    def aggregate_category_specificity(self, path):
        """
        Todo:
            compute:
            * avg. taxonomical path of categories on path
            * avg. 1/no. of categories' children
            * avg. no. followers of the category
            * avg. no. questions asked in each category

        """
        return agg_depth, agg_inv_child, agg_followers, agg_questions

    def extract_topic_sif_similarity(self, path):
        """
        Todo:
            * This function should compute similarity
            of recommendation topics to topics on
            path using cosine similarity in
            sif embedding space. The pairwise
            topics/categories similarities
            is stored in self.topics_sif_similarity
        """
        return sim

    def path_relevance_user(self, path):
        user = path[0]
        index = 1
        rel = []
        while index < len(path) - 1:
            current_node = path[index]
            relevance = 0
            con_paths = nx.shortest_simple_paths(self.graph, user, current_node)
            for con_path in con_paths:
                if len(con_path) >= 4:
                    break
                relevance += 1
            rel.append(relevance)
            index += 1
        return self.aggregate_func(rel)

    def path_recency(self, path):
        """
        Todo:
            * timestamp = timestamp of the most recent edge
        """
        path_date = datetime.strptime(timestamp, '%Y-%m-%d')
        feed_date = datetime.strptime(self.date, '%Y-%m-%d')
        return (feed_date - path_date).days

    def aggregate_post_engagement(self, path):
        """

        Todo:
            * compute the average upvotes/follows (or answers)
            of answers/questions
        """
        return eng

    def aggregate_post_specificity(self, path):
        """

        Todo:
            * compute spec = avg. 1/no. of post's categories
        """
        return spec

    def count_path_components(self, pattern_list):
        ask_count = pattern_list.count('a')
        answer_count = pattern_list.count('w')
        upvote_count = pattern_list.count('upvotes')
        know_count = pattern_list.count('knows_about')
        follow_question_count = pattern_str.count('u f c') + pattern_str.count('c f u')
        follow_category_count = pattern_str.count('u f p') + pattern_str.count('p f u')

        answer_question_count = pattern_list.count('answer_of')
        belong_count = pattern_list.count('hascategory')
        ancestor_count = pattern_list.count('ancestor')

        follow_user_count = pattern_str.count('u f u')

        res = [ask_count, answer_count + answer_question_count,
               follow_question_count + follow_category_count + follow_user_count, belong_count + ancestor_count,
               upvote_count,
               know_count]

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
            d = {'pair_id': pair_id, 'path1': path1, 'pattern1': pattern1,
                 'path2': path2, 'pattern2': pattern2, 'user': user,
                 'date': date}
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
