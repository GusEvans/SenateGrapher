import collections
import csv
import os
import sys
import typing as T

DATA_DIR = os.path.abspath('data')

ELECTION_ID_TO_NAME = {
    # '27966': '2022 Federal Election',
    '24310': '2019 Federal Election',
    # '20499': '2016 Federal Election',
}

STATES = ['ACT']
NEWLINE = '\r\n'


def read_csv_file(csv_path, remove_first_line=True):
    if not os.path.exists(csv_path):
        print(f"File {csv_path} does not exist!")
        sys.exit(1)

    with open(csv_path, newline=NEWLINE) as csv_file:
        all_lines = list(csv_file)
        if remove_first_line:
            all_lines.pop(0)

        csv_reader = csv.DictReader(all_lines)
        return list(csv_reader)


def normalise_name(given_name, surname):
    return f'{surname}, {given_name}'


def read_senate_candidate_id_list(election_id):
    candidate_download_path = os.path.join(DATA_DIR, f'SenateCandidatesDownload-{election_id}.csv')
    csv_data = read_csv_file(candidate_download_path)

    candidate_name_to_data = {}

    for candidate_dict in csv_data:
        full_name = normalise_name(candidate_dict['Surname'], candidate_dict['GivenNm'])
        assert full_name not in candidate_name_to_data

        candidate_name_to_data[full_name] = {
            'party_abbreviation': candidate_dict['PartyAb'],
            'party_name': candidate_dict['PartyNm'],
            'candidate_id': candidate_dict['CandidateID'],
            'state': candidate_dict['StateAb'],
            'given_name': candidate_dict['GivenNm'],
            'surname': candidate_dict['Surname'],
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

    for row in dop_data:
        name = normalise_name(row['GivenNm'], row['Surname'])
        rows_by_count[int(row['Count'])][name] = row

    final_count_num = max(rows_by_count.keys())

    print(f'For {election_name} in {state} there were {final_count_num} counts')

    previous_action = {
        'description': 'First preferences',
        'candidate': None
    }

    final_data = []

    for count in range(1, final_count_num + 1):
        this_count_data = {
            'count': count,
            'action': previous_action
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
        compile_dop_data(election_id, state, dop_data, candidate_info)


def main() -> None:
    for election_number in ELECTION_ID_TO_NAME.keys():
        process_election(election_number)


if __name__ == '__main__':
    main()
