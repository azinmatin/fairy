# coding=utf-8
import logging
from pymongo import MongoClient
import time
import argparse
from ConfigParser import ConfigParser
import os
import sys
from crawl_graph_entities import Crawl_Graph_Entities
from user_page_crawler import User_Page_Crawler
from interaction_graph import Interaction_Graph
import networkx as nx
import xlsxwriter
import random
import itertools
from networkx.readwrite.gml import literal_destringizer
from networkx.readwrite.gml import literal_stringizer


def path_has_feed(path, d):
    for elem in path:
        if elem not in d:
            return True
    return False


def entity_info(link):
    """
    Todo:
         * should return the entity's name
    """
    return link


def get_path_explanation(path, pattern, graph):
    """""
    Returns:
         str: human readable explanation
         str: explanation with links
    """""
    path_updated = []
    index = 0
    for elem in path:
        name = entity_info(elem)
        index += 1
        path_updated.append(name)

    pattern_updated = list(pattern)
    rel_dir = {'listened-to': 'listened-by', 'follows': 'followed-by',
               'sang': 'sung-by', 'has-track': 'is-a-track-of',
               'has-tag': 'is-a-tag-of', 'loves-track': 'loved-by',
               'super-category-of': 'sub-category-of',
               'listened-and-loves': 'listened-and-loved-by'}

    index = 0
    while index + 2 < len(pattern):
        source = pattern[index]
        target = pattern[index + 2]
        source_link = path[index/2]
        target_link = path[(index + 2) / 2]
        rel = pattern[index + 1]
        edge_id = -1
        for id_ in graph[source_link][target_link]:
            if graph[source_link][target_link][id_]['label'] == rel:
                edge_id = id_
                break
        if graph[source_link][target_link][edge_id]['direction'] == target_link:
            rel = rel_dir[rel]
        pattern_updated[index] = source
        pattern_updated[index+1] = rel
        pattern_updated[index+2] = target
        index += 2

    index = 0
    output = ''
    output_with_link = ''
    for elem in path_updated:
        output = output + '---' + elem
        output_with_link = output_with_link + '---' + path[index]
        if 2 * index + 1 < len(pattern_updated):
            output = output + '---' + pattern_updated[2 * index + 1]
            output_with_link = output_with_link + '---' + pattern_updated[2 * index + 1]
        index += 1
    return output[3:], output_with_link[3:]


def write_explanations_to_file(user_rec_paths, path_prefix, current_time, file_name):
    """ generates excel sheets of explanation pairs for evaluation """
    # open excel file
    if not os.path.exists(path_prefix + 'explanations/' + current_time):
        os.makedirs(path_prefix + 'explanations/' + current_time)
    filename = path_prefix + 'explanations/' + current_time + '/' + file_name
    # Create a new workbook and add a worksheet
    workbook = xlsxwriter.Workbook(filename)
    red_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    blue_format = workbook.add_format({'font_color': 'blue'})
    user_count = 0
    for user_n, recs_dict in user_rec_paths.items():
        user_count += 1
        print 'pairs of user started', user_count, user_n
        worksheet = workbook.add_worksheet(user_n)
        row = 0
        worksheet.write_string(row, 2, 'Comments')
        row += 1

        # sorting recs based on number of paths
        recs_sorted = []
        for rec_item, con_paths in recs_dict.items():
            recs_sorted.append((rec_item, len(con_paths)))
        recs_sorted = sorted(recs_sorted, key=lambda x: x[1])

        # residual for efficient number of elements
        residual = 0
        rec_share = 25
        trans_share = 100

        for rec_item, paths_num in recs_sorted:
            con_paths = recs_dict[rec_item]
            type_ = con_paths[0][2].split(' ')[-1]
            rec_name = entity_info(rec_item)
            path_list_size = len(con_paths)
            m = (path_list_size * (path_list_size - 1)) / 2
            con_paths_new = list(con_paths)

            # --------------------generating transitive pairs -----------------
            all_indices = [i for i in range(path_list_size)]
            if path_list_size == 2:
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
                # random.shuffle(pairs)

            # --------------------------- perturbed paths ---------------------
            for pair in pairs[:(min(m, rec_share + residual))]:
                i = pair[0]
                j = pair[1]
                if con_paths_new[i][2] == con_paths_new[j][2] and \
                                con_paths_new[i][3] == con_paths_new[j][3]:
                    continue
                worksheet.write_string(row, 0, 'Recommended item of type '
                                       + type_, blue_format)
                worksheet.write_string(row, 1, rec_name)
                row += 1

                worksheet.write_string(row, 0,
                                       'Link to recommended item', blue_format)
                worksheet.write_url(row, 1, rec_item)
                row += 1

                worksheet.write_string(row, 0,
                                       'First explanation', blue_format)
                worksheet.write_string(row, 1, con_paths_new[i][0])
                row += 1

                worksheet.write_string(row, 0,
                                       'Second explanation', blue_format)
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

                worksheet.write_string(row, 0,
                                       'First explanation links', blue_format)
                worksheet.write_string(row, 1, con_paths_new[i][1])
                row += 1

                worksheet.write_string(row, 0,
                                       'Second explanation links', blue_format)
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
                    paths = nx.all_simple_paths(g, source=user, target=f, cutoff=5)
                    for path in paths:
                        path_pattern = ''   # should be the pattern of the path
                        path_exp, path_str = get_path_explanation(path, path_pattern, g)
                        path_info = (path_exp, path_str, ' '.join(path_pattern), path_id)
                        user_feed_paths[user][f].append(path_info)
                file_name = 'explanations.xlsx'
                write_explanations_to_file(user_rec_paths, prefix_path, date, file_name)

    except:
        logging.info('', exc_info=1)
