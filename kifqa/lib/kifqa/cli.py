# Copyright (C) 2025 IBM Corp.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import logging
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

from kif_lib import (Filter, Item, KIF_Object, Property, Search, Statement,
                     Store, Value)
from kif_lib.model import FullFingerprint

from kifqa import KIFQA

try:
    from rich.console import Console
    from rich.markdown import Markdown
except ImportError as err:
    raise ImportError(
        f'{__name__} requires https://github.com/Textualize/rich/') from err

console = Console()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Prevent logs from propagating to the root logger
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

TIMETOUT = float(os.getenv('KIF_TIMEOUT', 60.0))


def print_stmts_markdown(stmts):
    for stmt in stmts:
        console.print(Markdown(stmt.to_markdown()))


def _mk_store(store_name) -> Store:
    store = Store(store_name)
    store.timeout = TIMETOUT
    store.snak_mask = Filter.VALUE_SNAK
    store.page_size = 1000
    return store

def _mk_search(search_name) -> Search:
    search = Search(search_name)
    search.timeout = TIMETOUT
    return search

def print_stmts_jsonl(jsonl):
    print(jsonl, flush=True)


def read_dataset(dataset):
    with open(dataset, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                yield entry


def extract_triples(args):
    assert args.config
    assert args.search
    search = _mk_search(args.search)
    store = _mk_store(args.store)
    kifqa = KIFQA(store=store, search=search, config_path=args.config)
    if args.question:
        triples = kifqa.extract_triples(args.question)
        for triple in triples.root:
            console.print((triple.subject, triple.property, triple.object))


def generate_filter(args):
    assert args.store in (x for x, _ in _list_available_stores())
    assert args.search
    assert args.config
    search = _mk_search(args.search)
    store = _mk_store(args.store)
    kifqa = KIFQA(store=store, search=search, config_path=args.config)
    if args.question:
        kifqa.generate_filters(args.question)
        if kifqa.triples:
            for t in kifqa.triples:
                console.print(t)


def _list_available_stores():
    return ((k, v.store_description) for k, v in Store.registry.items())


def _load_jsonl_to_dict(file_path: str) -> dict[str, dict]:
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                entry_id = entry.get('id')
                if entry_id:
                    data[entry_id] = entry
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line in {file_path}")
    return data


def eval_ask(args):
    assert args.store
    assert args.config
    assert args.search
    store = _mk_store(args.store)
    search = _mk_search(args.search)

    kifqa = KIFQA(store=store,
                        search=search,
                        config_path=args.config)
    from_file = args.from_file
    cache_entries = set()
    if from_file:
        if os.path.exists(from_file):
            for entry in read_dataset(from_file):
                cache_entries.add(entry['id'])

    if args.input_dataset:
        if not os.path.exists(args.input_dataset):
            raise FileNotFoundError(f"File '{args.input_dataset}' not found.")

        for entry in read_dataset(args.input_dataset):
            kifqa.reset()
            id = entry['id']
            if id in cache_entries:
                continue

            question = entry['question']
            jsonl = {
                "id": id,
                'source': entry['source'],
                'question': question,
                'error': False
            }

            gold_sub = KIF_Object.from_ast(entry['subject'])
            gold_prop = KIF_Object.from_ast(entry['predicate'])
            gold_obj = KIF_Object.from_ast(entry['object'])

            try:
                our_filter = kifqa.generate_filters(question)

                if our_filter:
                    ask = False
                    for filter in our_filter:
                        f_s = filter.subject
                        f_p = filter.property
                        f_v = filter.value
                        if isinstance(filter.subject, FullFingerprint):
                            f_s = gold_sub
                        if isinstance(filter.property, FullFingerprint):
                            f_p = gold_prop
                        if isinstance(filter.value, FullFingerprint):
                            f_v = gold_obj

                        new_filter = Filter(f_s, f_p, f_v)
                        ask = ask or kifqa._store.ask(filter=new_filter)
                        if ask:
                            break
                    jsonl['ask'] = ask

                    filters = []
                    if kifqa.triples:
                        for triple in kifqa.triples:
                            filters.append([
                                triple[0].iri.content if triple[0] else None,
                                triple[1].iri.content if triple[1] else None,
                                triple[2].iri.content if triple[2] else None,
                            ])
                    jsonl['filter'] = filters

                    labels = []
                    if kifqa.disambiguated_labels:
                        for t_labels in kifqa.disambiguated_labels:
                            labels.append([
                                t_labels[0] if t_labels[0] else '?x',
                                t_labels[1] if t_labels[1] else '?x',
                                t_labels[2] if t_labels[2] else '?x',
                            ])
                    jsonl['triples'] = labels
                else:
                    # tr = kifqa.triples if kifqa.triples else ''
                    la = kifqa.disambiguated_labels if kifqa.disambiguated_labels else ''
                    q2t = kifqa.q2t_labels if kifqa.q2t_labels else ''

                    jsonl['error'] = True
                    jsonl[
                        'error_message'] = f'Error: labels={{{la}}} q2t_labels={{{q2t}}}'
            except Exception as e:
                jsonl['error'] = True
                jsonl['ask'] = False
                # tr = kifqa.triples if kifqa.triples else ''
                la = kifqa.disambiguated_labels if kifqa.disambiguated_labels else ''
                q2t = kifqa.q2t_labels if kifqa.q2t_labels else ''

                jsonl[
                    'error_message'] = f'Error: labels={{{la}}} q2t_labels={{{q2t}}}: {e}'

            jsonl['q2t_labels'] = kifqa.q2t_labels if kifqa.q2t_labels else []
            print_stmts_jsonl(json.dumps(jsonl, ensure_ascii=False))


def generate_simple_question_answer(args):
    assert args.store in (x for x, _ in _list_available_stores())
    assert args.config
    assert args.search

    store = _mk_store(args.store)
    search = _mk_search(args.search)

    kifqa = KIFQA(store=store,
                        search=search,
                        config_path=args.config)
    from_file = args.from_file
    cache_entries = set()
    if from_file:
        if os.path.exists(from_file):
            for entry in read_dataset(from_file):
                cache_entries.add(int(entry['id']))


    if args.input_dataset:
        if not os.path.exists(args.input_dataset):
            raise FileNotFoundError(f"File '{args.input_dataset}' not found.")
        block_set = set()
        if args.block_list:
            with open(args.block_list, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:  # skip empty lines
                        try:
                            number = int(line)
                            block_set.add(number)
                        except ValueError:
                            logging.warning(f"Warning: Skipping non-integer line: {line}")

        for entry in read_dataset(args.input_dataset):
            kifqa.reset()
            id = int(entry['id'])
            if id in block_set:
                continue
            if id in cache_entries:
                logger.info(f'seen ({id})')
                continue

            question = entry['question']
            jsonl = {
                "id": entry['id'],
                'question': question,
                'error': False,
                'select': '',
                'candidates': [],
                'statements': [],
                'count': 0,
            }

            try:
                stmts = list(kifqa.query(question, timeout=TIMETOUT))

                count = 0
                for stmt in stmts:
                    count += 1

                    jsonl['statements'].append(stmt.to_ast())
                jsonl['count'] = count
                filters = []

                candidates = []
                for filter in kifqa.kif_filters:
                    if isinstance(filter.subject, FullFingerprint):
                        jsonl['select'] = 's'
                        candidates.append(filter.value.value.to_ast())
                    else:
                        jsonl['select'] = 'o'
                        candidates.append(filter.subject.value.to_ast())

                    filters.append([
                        filter.subject.to_ast(),
                        filter.property.to_ast(),
                        filter.value.to_ast()
                    ])
                jsonl['filter'] = filters

                jsonl['candidates'] = candidates
            except Exception as e:
                jsonl['error'] = True
                la = kifqa.disambiguated_labels if kifqa.disambiguated_labels else ''
                q2t = kifqa.q2t_labels if kifqa.q2t_labels else ''

                jsonl['error_message'] = f'Error: labels={{{la}}} q2t_labels={{{q2t}}}: {e}'

            jsonl['q2t_labels'] = kifqa.q2t_labels if kifqa.q2t_labels else []
            print_stmts_jsonl(json.dumps(jsonl, ensure_ascii=False))
            cache_entries.add(id)


def query(args):
    assert args.store
    # assert args.store in (x for x, _ in _list_available_stores())
    assert args.search
    assert args.config


    store = _mk_store(args.store)
    search = _mk_search(args.search)
    kifqa = KIFQA(store=store, search=search, config_path=args.config)

    encode = args.encode if args.encode else 'markdown'

    def print_result(stmts: Iterator[Statement]):
        if encode == 'markdown':
            print_stmts_markdown(stmts)
        elif encode == 'jsonl':
            for stmt in stmts:
                print_stmts_jsonl(stmt.to_json())

    if args.question:
        limit = int(args.limit) if args.limit else None
        stmts = kifqa.query(question=args.question, limit=limit)
        print_result(stmts)

    elif args.input_dataset:
        if not os.path.exists(args.input_dataset):
            raise FileNotFoundError(f"File '{args.input_dataset}' not found.")

        for entry in read_dataset(args.input_dataset):
            question = entry['question']
            stmts = kifqa.query(question)

            print_result(stmts)


def list_stores(_):
    stores = _list_available_stores()
    console.print("Available stores:")
    for s in stores:
        console.print(f"{s[0]}:\t{s[1]}")


def list_formats(_):
    console.print("Available formats:")
    for s in [('markdown', '(default) Print statements in Markdown'),
              ('jsonl', 'Print statments in KIF KBQA jsonl format ')]:
        console.print(f"{s[0]}:\t{s[1]}")


def analyze(args):
    assert args.result_dataset
    total_per_source = defaultdict(int)
    ask_true_per_source = defaultdict(int)
    ask_false_entries = defaultdict(list)

    with open(args.result_dataset, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                source = entry.get('source', 'unknown')
                ask = entry.get('ask', False)

                total_per_source[source] += 1
                if ask:
                    ask_true_per_source[source] += 1
                else:
                    ask_false_entries[source].append(entry)
            except json.JSONDecodeError as e:
                console.print(f'Error decoding line: {line}: {e}')
                continue

    console.print('📊 Proportion of "ask=True" per source:\n')
    for source in total_per_source:
        total = total_per_source[source]
        true_count = ask_true_per_source[source]
        proportion = true_count / total if total > 0 else 0
        console.print(f'{source}: {proportion:.2%} ({true_count}/{total})')


def evaluate(args):
    assert args.gold
    assert args.predicted
    from_ast = KIF_Object.from_ast

    from kifqa.metrics import f1_score, precision, recall

    def gold_statement(entry) -> Statement:
        subject: Item = from_ast(entry['subject'])
        property: Property = from_ast(entry['predicate'])
        value: Value = from_ast(entry['object'])
        snak = property(value)
        return Statement(subject=subject, snak=snak)

    def macro_scores(results, size):
        sum_p = 0
        sum_r = 0
        sum_f1 = 0

        for result in results.values():
            sum_p += result["p"]
            sum_r += result["r"]
            sum_f1 += result["f1"]

        return {
            "p": sum_p / size,
            "r": sum_r / size,
            "f1": sum_f1 / size,
            'size': size
        }

    def micro_scores(p_set, g_set, size):
        p_total = precision(preds=p_set, gts=g_set)
        r_total = recall(preds=p_set, gts=g_set)

        return {
            "p": p_total,
            "r": r_total,
            "f1": f1_score(p=p_total, r=r_total),
            'size': size
        }

    gold = {}
    block_set = set()
    if args.block_list:
        with open(args.block_list, 'r') as file:
            for line in file:
                line = line.strip()
                if line:  # skip empty lines
                    try:
                        number = int(line)
                        block_set.add(number)
                    except ValueError:
                         logging.warning(f"Warning: Skipping non-integer line: {line}")

    for entry in read_dataset(args.gold):
        gold[int(entry['id'])] = entry

    results = {}
    results_only_1 = {}
    results_size = 0
    results_size_only_1 = 0
    gold_stmt_set = []
    gold_stmts_set = []
    predicted_set = []
    gold_set_only_1 = []
    predicted_set_only_1 = []

    for entry in read_dataset(args.predicted):
        id = int(entry['id'])
        if id in block_set:
            continue
        if id in gold:
            gold_stmt = gold_statement(gold[id])
            gold_stmt_set.append(gold_stmt.digest)

            error = entry['error']
            if error or len(entry['q2t_labels']) > 1:
                p_stmts = []
            else:
                p_stmts = list(
                    {f.digest
                    for f in map(from_ast, entry.get('statements', []))})
            g_stmts = list({
                f.digest
                for f in map(from_ast, gold[id].get('statements', []))
            })

            predicted_set += p_stmts
            gold_stmts_set += g_stmts

            results[id] = micro_scores(p_stmts, g_stmts, 1)
            if args.output:
                with open(args.output, 'a') as f:
                    evaluation = {
                        'id': id,
                        'question': entry['question'],
                        'evaluation': results[id]
                    }
                    f.write(json.dumps(evaluation, ensure_ascii=False) + '\n')

            if len(g_stmts) == 1:
                results_only_1[id] = results[id]
                gold_set_only_1.append(g_stmts[0])
                results_size_only_1 += 1
                predicted_set_only_1 += p_stmts

            results_size += 1

    macro = macro_scores(results, results_size)
    console.print('Macro gold stms vs predicted  stms:', macro)

    micro = micro_scores(p_set=predicted_set, g_set=gold_stmts_set, size=results_size)
    console.print(f'Micro gold stms ({len(gold_stmts_set)}) vs predicted stms ({len(predicted_set)}):', micro)

    # score_total = micro_scores(predicted_set, gold_stmt_set, results_size)
    # console.print('gold triple (wikidata-only):', score_total)

    macro = macro_scores(results_only_1, results_size_only_1)
    console.print('Macro only one stmt:', macro)

    micro = micro_scores(
        p_set=predicted_set_only_1, g_set=gold_set_only_1, size=results_size_only_1)
    console.print(f'Micro only one stmt | gold ({len(gold_set_only_1)}) vs predicted stms ({len(predicted_set_only_1)})', micro)


def compare_analysis(args):
    assert args.target
    assert args.files

    reference_data = _load_jsonl_to_dict(args.target)
    comparison_files = args.files
    output_dir = args.output_dir if args.output_dir else None

    def compare_and_write(comparison_file: str):
        comparison_data = _load_jsonl_to_dict(comparison_file)
        differences = []

        for entry_id, comp_entry in comparison_data.items():
            ref_entry = reference_data.get(entry_id)
            if not ref_entry:
                continue

            ref_ask = ref_entry.get('ask', False)
            comp_ask = comp_entry.get('ask', False)

            if ref_ask != comp_ask:
                change = 'false_to_true' if not ref_ask and comp_ask else 'true_to_false'
                differences.append({
                    'id': comp_entry['id'],
                    'source': comp_entry.get('source', ''),
                    'question': comp_entry.get('question', ''),
                    'changed': change
                })
        if output_dir:
            output_file = output_dir
        else:
            output_file = os.path.dirname(comparison_file)

        comparison_file_name = os.path.splitext(
            os.path.basename(comparison_file))[0]
        target_file_name = os.path.splitext(os.path.basename(args.target))[0]
        output_file = os.path.join(
            output_file,
            f"comparison_{comparison_file_name}_with_{target_file_name}.jsonl")
        with open(output_file, 'w', encoding='utf-8') as out:
            for diff in differences:
                out.write(json.dumps(diff, ensure_ascii=False) + '\n')

        console.print(
            f"[✔] {output_file} written with {len(differences)} differences")

    with ThreadPoolExecutor() as executor:
        for comparison_file in comparison_files:
            executor.submit(compare_and_write, comparison_file)


def main():
    parser = argparse.ArgumentParser(description='KIF KBQA CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    analize_parser = subparsers.add_parser('analize', help='Analize results')
    analize_parser.add_argument('--result-dataset', '-r')
    analize_parser.set_defaults(func=analyze)

    compare_parser = subparsers.add_parser('compare', help='Analize results')
    compare_parser.add_argument('--target',
                                '-t',
                                help='Target file for analysis.',
                                required=True)
    compare_parser.add_argument(
        '--output_dir', '-o', help='Output directory')
    compare_parser.add_argument(
        '--files',
        '-f',
        nargs='+',
        help='List of JSONL files to compare with the target file.',
        required=True)
    compare_parser.set_defaults(func=compare_analysis)

    query_parser = subparsers.add_parser(
        'query', help='Evaluate questions using a specific store')
    query_parser.add_argument('--input-dataset', '-i', help='Input dataset')
    query_parser.add_argument('--question', '-q')
    query_parser.add_argument('--store', '-s', default='wikidata-extension')
    query_parser.add_argument('--search', '-sh', default='wikidata-wapi')
    query_parser.add_argument('--config', '-c', required=True)
    query_parser.add_argument('--encode', '-e', default='markdown')
    query_parser.add_argument('--limit', '-l')
    query_parser.set_defaults(func=query)

    eval_parser = subparsers.add_parser(
        'evaluate', help='Evaluate SimpleQuestions answers')
    eval_parser.add_argument('--gold', '-g', help='Gold answers dataset', required=True)
    eval_parser.add_argument('--predicted', '-p', help='Predicted answers dataset', required=True)
    eval_parser.add_argument('--output', '-o', help='Output', )
    eval_parser.add_argument('--block-list', '-bl', help='A txt file containing a list of questions to ignore', )
    eval_parser.set_defaults(func=evaluate)

    eval_parser = subparsers.add_parser(
        'simple-question', help='Generate SimpleQuestions answers')
    eval_parser.add_argument('--input-dataset', '-i', help='Input dataset')
    eval_parser.add_argument('--store', '-s', default='wikidata-extension')
    eval_parser.add_argument('--limit', '-l')
    eval_parser.add_argument('--config', '-c', required=True)
    eval_parser.add_argument('--block-list', '-bl', help='A txt file containing a list of questions to ignore', )
    eval_parser.add_argument('--from-file', '-ff')
    eval_parser.set_defaults(func=generate_simple_question_answer)

    eval_parser = subparsers.add_parser(
        'simple-question-ask', help='Generate SimpleQuestions ask answers')
    eval_parser.add_argument('--input-dataset', '-i', help='Input dataset')
    eval_parser.add_argument('--store', '-s', default='wikidata-extension')
    eval_parser.add_argument('--config', '-c', required=True)
    eval_parser.add_argument('--from-file', '-ff')
    eval_parser.set_defaults(func=eval_ask)

    extract_parser = subparsers.add_parser(
        'extract-triples', help='Extract triples from a question')
    extract_parser.add_argument('--question', '-q')
    extract_parser.add_argument('--store', '-s', default='wikidata')
    extract_parser.add_argument('--search', '-sh', default='wikidata-wapi')
    extract_parser.add_argument('--config', '-c', required=True)
    extract_parser.set_defaults(func=extract_triples)

    generate_parser = subparsers.add_parser(
        'generate-filter', help='Generate KIF filter from a question')
    generate_parser.add_argument('--question', '-q')
    generate_parser.add_argument('--store', '-s', default='wikidata-extension')
    generate_parser.add_argument('--config', '-c', required=True)
    generate_parser.set_defaults(func=generate_filter)

    list_parser = subparsers.add_parser('list-stores',
                                        help='List all available stores')
    list_parser.set_defaults(func=list_stores)

    list_parser = subparsers.add_parser(
        'list-formats', help='List available formats to output')
    list_parser.set_defaults(func=list_formats)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
