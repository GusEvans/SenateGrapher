import collections
import csv
import os
import sys
import typing as T
import pprint
import re
import json


DATA_DIR = os.path.abspath('data_in')
DATA_OUT = os.path.abspath('data_out')

WA_2014_SPECIAL_ELECTION = '2014-special-election'

ELECTION_ID_TO_NAME = {
    '27966': '2022-federal-election',
    '24310': '2019-federal-election',
    '20499': '2016-federal-election',
    '17875': WA_2014_SPECIAL_ELECTION,
    '17496': '2013-federal-election',
    '15508': '2010-federal-election',
    '13745': '2007-federal-election',
    '12246': '2004-federal-election',
}

STATES = ['ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']
NEWLINE = '\r\n'

ELECTED_BLURB_PATH = os.path.join(os.path.abspath(DATA_DIR), 'blurbs.txt')


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


def normalise_name(given_name, surname, state):
    if surname in ('Exhausted', 'Gain/Loss') and given_name == '':
        return f'__{state}_{surname}'

    return f'{surname}, {given_name} ({state})'

def read_blurb_data():
    with open(ELECTED_BLURB_PATH) as blurb_file:
        file_contents = blurb_file.read()
        entries = file_contents.strip().split('\n\n')
        return {
            header_election_id.replace('# ', ''): blurb_text
            for (header_election_id, blurb_text) in [entry.split('\n') for entry in entries]
        }

blurb_data = read_blurb_data()

def read_senate_candidate_id_list(election_id):
    election_name = ELECTION_ID_TO_NAME[election_id]
    candidate_download_path = os.path.join(DATA_DIR, f'SenateCandidatesDownload-{election_id}.csv')
    csv_data = read_csv_file(candidate_download_path)

    colour_csv = read_csv_file(os.path.join(DATA_DIR, 'party color codes.csv'))
    colour_data = {
        row['party_code']: row['colour']
        for row in colour_csv
    }

    candidate_name_to_data = {}

    for candidate_dict in csv_data:
        full_name = normalise_name(
            candidate_dict['GivenNm'], candidate_dict['Surname'],
            candidate_dict['StateAb']
        )
        assert full_name not in candidate_name_to_data

        party_abbreviation = candidate_dict['PartyAb']
        if party_abbreviation == '':
            party_abbreviation = 'IND'

        display_name = f"{candidate_dict['GivenNm']} {titlecase_surname(candidate_dict['Surname'])}"
        tooltip_name = display_name

        if candidate_dict['PartyNm']:
            tooltip_name += f" ({candidate_dict['PartyNm']})"

        if party_abbreviation not in colour_data:
            colour_data[party_abbreviation] = '888888'
            print('Party', party_abbreviation, f'({candidate_dict["PartyNm"]})', 'not found for', election_name)

        candidate_name_to_data[full_name] = {
            'party_abbreviation': party_abbreviation,
            'party_name': candidate_dict['PartyNm'],
            'candidate_id': candidate_dict['CandidateID'],
            'state': candidate_dict['StateAb'],
            'given_name': candidate_dict['GivenNm'],
            'surname': candidate_dict['Surname'],
            'display_name': display_name,
            'tooltip_name': tooltip_name,
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

def titlecase_surname(surname):
    surname = surname.title()

    for prefix in ['Mc', 'Mac']:
        surname = re.sub(
            r'\b' + prefix + r'(\w)',
            lambda match: prefix + match.group(1).title(),
            surname
        )
    return surname

def compile_dop_data(election_id, state, dop_data, candidate_info):
    rows_by_count = collections.defaultdict(dict)
    election_name = ELECTION_ID_TO_NAME[election_id]

    all_normalised_names = []

    first_row = dop_data[0]

    for row in dop_data:
        name = normalise_name(row['GivenNm'], row['Surname'], state)
        rows_by_count[int(row['Count'])][name] = row

        if name not in all_normalised_names:
            all_normalised_names.append(name)

    final_count_num = max(rows_by_count.keys())

    print(f'For {election_name} in {state} there were {final_count_num} counts and {len(all_normalised_names)} candidates')

    previous_action = {
        'comment': 'First preferences.'
    }

    # last_elecection_exclusion = {
    #     'candidate': '',
    #     'type': ''
    # }

    all_count_data = []

    changed_names = None

    for count in range(1, final_count_num + 1):
        if 'Changed' in rows_by_count[count][all_normalised_names[0]]:
            changed_key = 'Changed'
        else:
            changed_key = 'ChangedFl'

        changed_rows = [
            (name, row)
            for name, row in rows_by_count[count].items()
            if row[changed_key].strip()
        ]
        if changed_rows:
            changed_names = [(row[0], row[1]) for row in changed_rows]
        # assert len(changed_rows) <= 1, f'{count} {election_name}'

        # if changed_rows:
        #     last_elecection_exclusion = {
        #         'candidate': changed_rows[0][0],
        #         'type': changed_rows[0][1]['Status']
        #     }

        # print(count, changed_rows)

        this_comment = previous_action['comment']
        if count == final_count_num:
            this_comment = this_comment + ' All vacancies filled.'
            this_comment = this_comment.strip()
        this_count_data = {
            'count': count,
            'progressive_vote_total': [
                int(rows_by_count[count][name]['ProgressiveVoteTotal'])
                for name in all_normalised_names
            ],
            'action': {
                'comment': this_comment
            },
            # 'last_change': last_elecection_exclusion
            'status': [
                ['', 'Excluded', 'Elected'].index(rows_by_count[count][name]['Status'])
                for name in all_normalised_names
            ],
            'has_change': int(len(changed_rows) >= 1)
        }
        all_count_data.append(this_count_data)

        comment = None
        comment_row = 0
        while not comment and comment_row < len(all_normalised_names):
            comment = rows_by_count[count][all_normalised_names[comment_row]]['Comment']
            comment_row += 1
        if not comment:
            print(f'No comment on {count=} {election_name=} {state=}')
            comment = ''

        if match := re.search(r'Preferences with a transfer value of ([0-9]+[.]?[0-9]*) will be distributed in count', comment):
            assert changed_names
            all_names = [
                candidate_info[changed_name[0]]['display_name']
                for changed_name in changed_names
            ]
            if len(all_names) == 2:
                excluded_names = f'{all_names[0]} and {all_names[1]}'
            elif len(all_names) > 2:
                excluded_names = ', '.join(all_names[:-1]) + ', and ' + all_names[-1]
            else:
                excluded_names = all_names[0]
            transfer_value = float(match.group(1))
            was_were = 'were' if len(changed_names) > 1 else 'was'
            if transfer_value == 1:
                comment = f'{excluded_names} {was_were} excluded and preferences were distributed at full value.'
            else:
                comment = f'{excluded_names} {was_were} excluded and preferences were distributed at a transfer value of {transfer_value:.4f}.'
            if len(changed_names) > 1: comment = 'Bulk exclusion: ' + comment
        elif match := re.search(r'has [0-9]* surplus vote\(s\) to be distributed in count # [0-9]+ at a transfer value of ([0-9]+[.]?[0-9]*).', comment):
            for future_name, future_row in rows_by_count[count + 1].items():
                if int(future_row['Papers']) < 0:
                    elected_name = future_name
                    break
            else:
                raise Exception('no negative papers???')
            elected_display_name = candidate_info[elected_name]['display_name']
            transfer_value = float(match.group(1))
            comment = f'{elected_display_name} was elected and surplus votes were distributed at transfer value {transfer_value:.3f}'

        previous_action = {
            'comment': comment
        }


    special_candidate_info = {
        normalise_name('', 'Exhausted', state): {
            'party_abbreviation': '',
            'party_name': '',
            'candidate_id': -1,
            'state': state,
            'given_name': "",
            'surname': "Exhausted",
            'display_name': 'Exhausted',
            'colour_data': '#DDDDDD'
        },
        normalise_name('', 'Gain/Loss', state): {
            'party_abbreviation': '',
            'party_name': '',
            'candidate_id': -2,
            'state': state,
            'given_name': "",
            'surname': "Gain/Loss",
            'display_name': 'Gain/Loss',
            'colour_data': '#DDDDDD'
        }
    }

    # generate list of elected candidates in order
    elected_rows = sorted([
        (int(row['Order Elected']), row['GivenNm'], row['Surname'], normalised)
        for normalised, row in rows_by_count[final_count_num].items()
        if row['Order Elected'] and int(row['Order Elected'])
    ])

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
        } | special_candidate_info,
        'election_name': election_name,
        'blurb_text': blurb_data[election_name + '-' + first_row['State'].strip()]
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
        if election_name == WA_2014_SPECIAL_ELECTION and state != 'WA':
            continue

        dop_data = read_senate_race(election_id, state)
        compiled_info = compile_dop_data(election_id, state, dop_data, candidate_info)
        json_filename = os.path.join(DATA_OUT, f'{election_name}-{state}.json')
        with open(json_filename, 'w') as json_file:
            json.dump(compiled_info, json_file)

        # CORS :(
        js_filename = os.path.join(DATA_OUT, f'{election_name}-{state}.js')
        js_contents = 'got_js_payload_data('
        js_contents += json.dumps(compiled_info)
        js_contents += ')'

        with open(js_filename, 'w') as js_file:
            js_file.write(js_contents)


def main() -> None:
    for election_number in ELECTION_ID_TO_NAME.keys():
        process_election(election_number)


def clear_data_out():
    for filename in os.listdir(DATA_OUT):
        if filename.endswith('.json') or filename.endswith('js'):
            os.remove(os.path.join(DATA_OUT, filename))

if __name__ == '__main__':
    clear_data_out()
    main()
