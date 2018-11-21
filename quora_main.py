# coding=utf-8
import logging
from pymongo import MongoClient
import time
import argparse
from ConfigParser import ConfigParser
import os
import sys
from user_page_crawler import User_Page_Crawler
from qa_crawler_db import QA_Crawler
from crawl_graph_entities import Crawl_Graph_Entities
from user_crawler_db import UserCrawler
from taxonomy_crawler import TaxonomyCrawler
from crawl_node_influence import User_Node_Influence
from interaction_graph import Interaction_Graph
import db_handler as dbh
import itertools
import networkx as nx
import random
import xlsxwriter
import json
from networkx.readwrite.gml import literal_destringizer
from networkx.readwrite.gml import literal_stringizer


def entity_info(item):
    """
    Todo:
         * should return the entity's name
         * should return entity's type
    """
    return item, None


def get_path_explanation(path, path_pattern, graph):
    path_pattern_updated = []
    index = 0
    for e in path_pattern:
        if index % 2 == 0:
            path_pattern_updated.append(e)
        else:
            source = path[(index - 1)/2]
            source_type = path_pattern[index - 1]
            target = path[(index + 1)/2]
            if e == 'f':
                rel = 'follows'
                if graph[source][target]['direction'] == target or \
                                source_type != 'u':
                    rel = 'followed-by'
                path_pattern_updated.append(rel)
            elif e == 'w':
                rel = 'answers'
                if source_type != 'u':
                    rel = 'answered-by'
                path_pattern_updated.append(rel)
            elif e == 'a':
                rel = 'asks'
                if source_type != 'u':
                    rel = 'asked-by'
                path_pattern_updated.append(rel)
            elif e == 'answer_of':
                rel = 'answer-of'
                if '/answer/' in target:
                    rel = 'question-of'
                path_pattern_updated.append(rel)
            elif e == 'hascategory':
                rel = 'has-category'
                if source_type == 'c':
                    rel = 'is-categoy-of'
                path_pattern_updated.append(rel)
            elif e == 'ancestor':
                rel = 'super-category-of'
                if graph[source][target]['direction'] == source:
                    rel = 'sub-category-of'
                path_pattern_updated.append(rel)
            else:
                path_pattern_updated.append(e)
        index += 1

    path_updated = []
    for e in path:
        tabs = e.split("/")
        if '/answer/' in e or '/answers/' in e:
            item = "answer to question " + tabs[-3].replace('-', ' ')
        else:
            item = tabs[-1].replace('-', ' ')
        path_updated.append(item)

    index = 0
    output = ''
    ouput_with_link = ''
    for e in path_updated:
        output = output + '---' + e
        ouput_with_link = ouput_with_link + '---' + path[index]
        if 2 * index + 1 < len(path_pattern_updated):
            output = output + '---' + path_pattern_updated[2 * index + 1]
            ouput_with_link = ouput_with_link + '---' + path_pattern_updated[2 * index + 1]
        index += 1

    return output[3:], ouput_with_link[3:]


def write_explanations_to_file(user_rec_paths, path_prefix, current_time, file_name):
    """ generates excel sheets of explanation pairs for evaluation """
    # open excel file
    if not os.path.exists(path_prefix + 'explanations/' + current_time):
        os.makedirs(path_prefix + 'explanations/' + current_time)
    filename = path_prefix + 'explanations/'+ current_time + '/' + file_name
    # Create a new workbook and add a worksheet
    workbook = xlsxwriter.Workbook(filename)
    red_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    blue_format = workbook.add_format({'font_color': 'blue'})
    for user_n in user_rec_paths.keys():
        workbook.add_worksheet(user_n)
    index = 0
    for worksheet in workbook.worksheets():
        user_n = user_rec_paths.keys()[index]
        print 'pairs of users started', user_n
        recs_dict = user_rec_paths[user_n]
        row = 0
        worksheet.write_string(row, 2, 'Comments')
        row += 1

        # resedual > 0 when there are less than rec_share paths
        residual = 0
        rec_share = 23
        trans_share = 100

        # sorting recs based on number of paths
        recs_sorted = []
        for rec_item, con_paths in recs_dict.items():
            recs_sorted.append((rec_item, len(con_paths)))
        recs_sorted = sorted(recs_sorted, key=lambda x: x[1])

        for rec_item, paths_num in recs_sorted:
            con_paths = recs_dict[rec_item]
            rec_name, type_ = entity_info(rec_item)
            l = len(con_paths)
            m = (l * (l-1)) / 2
            con_paths_new = list(con_paths)

            # ------------------- transitive pairs -------------------------
            all_indices = [i for i in range(l)]
            if l == 2:
                pairs = [(0, 1)]
            else:
                random.shuffle(all_indices)
                triplets = itertools.combinations(all_indices, 3)
                pairs = []
                num_trans = 0
                for triplet in triplets:
                    if num_trans >= trans_share:
                        break
                    a = triplet[0]
                    b = triplet[1]
                    c = triplet[2]
                    if not (a, b) in pairs and not (b, a) in pairs:
                        pairs.append((a, b))
                    if not (a, c) in pairs and not (c, a) in pairs:
                        pairs.append((a, c))
                    if not (b, c) in pairs and not (c, b) in pairs:
                        pairs.append((c, b))
                    num_trans += 1

            for pair in pairs[:(min(m, rec_share + residual))]:
                i = pair[0]
                j = pair[1]
                if con_paths_new[i][2] == con_paths_new[j][2] and \
                                con_paths_new[i][3] == con_paths_new[j][3]:
                    continue
                worksheet.write_string(row, 0, 'Recommended item of type ' +
                                       type_, blue_format)
                worksheet.write_string(row, 1, rec_name)
                row += 1

                worksheet.write_string(row, 0, 'Link to recommended item',
                                       blue_format)
                worksheet.write_url(row, 1, rec_item)
                row += 1

                worksheet.write_string(row, 0, 'First explanation',
                                       blue_format)
                worksheet.write_string(row, 1, con_paths_new[i][0])
                row += 1

                worksheet.write_string(row, 0, 'Second explanation',
                                       blue_format)
                worksheet.write_string(row, 1, con_paths_new[j][0])
                row += 1

                if random.randint(0, 9) < 7:
                    worksheet.write_string(row, 0, 'More surprising to you',
                                           red_format)
                    row += 1

                    worksheet.write_string(row, 0, 'More relevant/useful to '
                                                   'you', red_format)
                    row += 1
                else:
                    worksheet.write_string(row, 0, 'More relevant/useful to '
                                                   'you', red_format)
                    row += 1

                    worksheet.write_string(row, 0, 'More surprising to you',
                                           red_format)
                    row += 1

                worksheet.write_string(row, 0, 'First explanation links',
                                       blue_format)
                worksheet.write_string(row, 1, con_paths_new[i][1])
                row += 1

                worksheet.write_string(row, 0, 'Second explanation links',
                                       blue_format)
                worksheet.write_string(row, 1, con_paths_new[j][1])
                row += 1

                worksheet.write_string(row, 0, 'First explanation pattern')
                worksheet.write_string(row, 1, con_paths_new[i][2])
                row += 1

                worksheet.write_string(row, 0, 'Second explanation pattern')
                worksheet.write_string(row, 1, con_paths_new[j][2])
                row += 1

                worksheet.write_string(row, 0, 'First explanation ID')
                worksheet.write_string(row, 1, con_paths_new[i][3])
                row += 1

                worksheet.write_string(row, 0, 'Second explanation ID')
                worksheet.write_string(row, 1, con_paths_new[j][3])
                row += 3
            if rec_share + residual > m:
                residual = rec_share + residual - m
            else:
                residual = 0

        index += 1
    workbook.close()


if __name__ == '__main__':
    try:
        users = ['u1', 'u2', 'u3']  # evaluators
        dates = ['d1', 'd2']
        selected_feeds = {'u1': {'d1': ['f1'], 'd2': ['f2']},
                          'u2': {'d1': ['f3'], 'd2': ['f4']},
                          'u3': {'d1': ['f5'], 'd2': ['f6']}}

        # -----------------------------generate explanations-------------------
        user_feed_paths = {'u1': {'f1': [], 'f2': []},
                           'u2': {'f3': [], 'f4': []},
                           'u3': {'f5': [], 'f6': []}}
        for user in users:
            for date in dates:
                file_path = ''  # path to user's interaction graph
                g = nx.read_gml(file_path, destringizer=literal_destringizer)
                for f in selected_feeds[user][date]:
                    paths = nx.nx.shortest_simple_paths(g, source=user, target=f)
                    for path in paths:
                        path_pattern = ''   # should be the pattern of the path
                        path_exp, path_str = get_path_explanation(path, path_pattern, g)
                        path_info = (path_exp, path_str, ' '.join(path_pattern), path_id)
                        user_feed_paths[user][f].append(path_info)
                file_name = 'explanations.xlsx'
                write_explanations_to_file(user_rec_paths, prefix_path, date, file_name)

    except:
        logging.info('', exc_info=1)
