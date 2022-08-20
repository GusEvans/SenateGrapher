import collections
import csv
import os
import sys
import typing as T
import pprint
import json

DATA_DIR = os.path.abspath('data_in')
DATA_OUT = os.path.abspath('data_out')

ELECTION_ID_TO_NAME = {
    '27966': '2022-federal-election',
    '24310': '2019-federal-election',
    # '20499': '2016 Federal Election',
}

STATES = ['ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']
NEWLINE = '\r\n'


def read_csv_file(csv_path, remove_first_line=True):
    if not os.path.exists(csv_path):
        print(f"File {csv_path} does not exist!")
        sys.exit(1)

    with open(csv_path, newline='\n') as csv_file:
        all_lines = [line.replace('\r', '') for line in csv_file]
        if remove_first_line:
            all_lines.pop(0)

        csv_reader = csv.DictReader(all_lines)
        return list(csv_reader)


def normalise_name(given_name, surname):
    if surname in ('Exhausted', 'Gain/Loss') and given_name == '':
        return '__' + surname

    return f'{surname}, {given_name}'


def read_senate_candidate_id_list(election_id):
    candidate_download_path = os.path.join(DATA_DIR, f'SenateCandidatesDownload-{election_id}.csv')
    csv_data = read_csv_file(candidate_download_path)

    colour_csv = read_csv_file(os.path.join(DATA_DIR, 'party color codes.csv'))
    colour_data = {
        row['party_code']: row['colour']
        for row in colour_csv
    }

    print(colour_csv)

    candidate_name_to_data = {}

    for candidate_dict in csv_data:
        full_name = normalise_name(candidate_dict['GivenNm'], candidate_dict['Surname'])
        assert full_name not in candidate_name_to_data

        party_abbreviation = candidate_dict['PartyAb']
        if party_abbreviation == '':
            party_abbreviation = 'IND'

        candidate_name_to_data[full_name] = {
            'party_abbreviation': party_abbreviation,
            'party_name': candidate_dict['PartyNm'],
            'candidate_id': candidate_dict['CandidateID'],
            'state': candidate_dict['StateAb'],
            'given_name': candidate_dict['GivenNm'],
            'surname': candidate_dict['Surname'],
            'colour_data': '#' + colour_data[party_abbreviation]
        }

    return candidate_name_to_data


def get_senate_dop_download_path(election_id, state):
    return os.path.join(
        DATA_DIR, f'SenateDopDownload-{election_id}',
        f'SenateStateDOPDownload-{election_id}-{state}.csv'
    )


def read_senate_race(election_id: str, state: str) -> T.List[T.Dict[str, str]]:
    election_name = ELECTION_ID_TO_NAME[election_id]
    csv_path = get_senate_dop_download_path(election_id, state)

    if not os.path.exists(csv_path):
        print(f"Cannot find Senate DOP data for {state} {election_name}")
        sys.exit(1)

    with open(csv_path, newline='') as csv_file:
        senate_reader = csv.DictReader(csv_file)
        return list(senate_reader)


def compile_dop_data(election_id, state, dop_data, candidate_info):
    rows_by_count = collections.defaultdict(dict)
    election_name = ELECTION_ID_TO_NAME[election_id]

    all_normalised_names = []

    first_row = dop_data[0]

    for row in dop_data:
        name = normalise_name(row['GivenNm'], row['Surname'])
        rows_by_count[int(row['Count'])][name] = row

        if name not in all_normalised_names:
            all_normalised_names.append(name)

    final_count_num = max(rows_by_count.keys())

    print(f'For {election_name} in {state} there were {final_count_num} counts')

    previous_action = {
        # 'description': 'First preferences',
        # 'candidate': None,
    }

    # print(all_normalised_names)

    all_count_data = []

    for count in range(1, final_count_num + 1):
        # changed_rows = [
        #     row
        #     for row in rows_by_count[count].values()
        #     if row['Changed']
        # ]

        # print(count, changed_rows)
        # assert len(changed_rows) == 1

        this_count_data = {
            'count': count,
            'progressive_vote_total': [
                int(rows_by_count[count][name]['ProgressiveVoteTotal'])
                for name in all_normalised_names
            ]
        }
        all_count_data.append(this_count_data)

    return {
        'counts': all_count_data,
        'state': first_row['State'],
        'num_vacancies': int(first_row['No Of Vacancies']),
        'total_formal': int(first_row['Total Formal Papers']),
        'quota': int(first_row['Quota']),
        'names': all_normalised_names,
        'candidate_info': {
            candidate_name: candidate_data
            for candidate_name, candidate_data in candidate_info.items()
            if candidate_data['state'] == state
        } | {
            '__Exhausted': {
                'party_abbreviation': 'META',
                'party_name': 'Internal',
                'candidate_id': -1,
                'state': state,
                'given_name': "I'm",
                'surname': "exhausted",
                'colour_data': '#DDDDDD'
            },
            '__Gain/Loss': {
                'party_abbreviation': 'META',
                'party_name': 'Internal',
                'candidate_id': -2,
                'state': state,
                'given_name': "Gain",
                'surname': "Loss",
                'colour_data': '#DDDDDD'
            },
        }
    }


def process_election(election_id: str) -> None:
    election_name = ELECTION_ID_TO_NAME[election_id]

    senate_dop_download_path = os.path.join(DATA_DIR, f'SenateDopDownload-{election_id}')

    if not os.path.isdir(senate_dop_download_path):
        print(f"Cannot find Senate DOP data for {election_name} (id {election_id})")
        sys.exit(1)

    candidate_info = read_senate_candidate_id_list(election_id)
    print(f'For {election_name}, found {len(candidate_info)} candidates.')

    for state in STATES:
        dop_data = read_senate_race(election_id, state)
        compiled_info = compile_dop_data(election_id, state, dop_data, candidate_info)
        json_filename = os.path.join(DATA_OUT, f'{election_name}-{state}.json')
        json.dump(compiled_info, open(json_filename, 'w'))


def main() -> None:
    for election_number in ELECTION_ID_TO_NAME.keys():
        process_election(election_number)


def clear_data_out():
    for filename in os.listdir(DATA_OUT):
        if filename.endswith('.json'):
            os.remove(os.path.join(DATA_OUT, filename))

if __name__ == '__main__':
    clear_data_out()
    main()
