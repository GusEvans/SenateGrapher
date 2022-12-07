'use strict';

let js_loaded_data = {};

let state = {
    current_data: null,
    current_count: null,
    count_change: null,
    old_count: null,
    chart: null
};

function load_data_for_count() {
    const data_for_count = state.current_data.counts[state.current_count];

    if (state.old_count === null) {
        state.old_count = Array(state.current_data.names.length).fill(0);
    }

    state.count_change = state.old_count.map((old_count, i) => {
        return data_for_count.progressive_vote_total[i] - old_count;
    });
    console.log(state.count_change);

    state.data.datasets[0].data = data_for_count.progressive_vote_total;
    state.config.options.plugins.title.text = `Count ${state.current_count + 1}: ${data_for_count.action.comment}`;

    state.old_count = data_for_count.progressive_vote_total;

    state.chart.update();

    let at_end = state.current_count === state.current_data.counts.length - 1;
    let at_beginning = state.current_count === 0;
    document.getElementById("advance").disabled = at_end;
    document.getElementById("advance_major").disabled = at_end;
    document.getElementById("backwards").disabled = at_beginning;
    document.getElementById("backwards_major").disabled = at_beginning;
}

function advance() {
    if (state.current_count + 1 < state.current_data.counts.length) {
        state.current_count++;
        load_data_for_count();
    }
}

function backwards() {
    if (state.current_count - 1 >= 0) {
        state.current_count--;
        load_data_for_count();
    }
}

function advance_major() {
    state.current_count += 1;

    while (state.current_count + 1 < state.current_data.counts.length && !state.current_data.counts[state.current_count].has_change) {
        state.current_count += 1;
    }
    state.current_count = Math.min(state.current_count, state.current_data.counts.length - 1);
    load_data_for_count();
}

function backwards_major() {
    state.current_count -= 1;

    while (state.current_count > 0 && !state.current_data.counts[state.current_count].has_change) {
        state.current_count -= 1;
    }
    state.current_count = Math.max(state.current_count, 0);
    load_data_for_count();
}

function jump_to_count() {
    const input_value = parseInt(document.getElementById('count_to_jump_to').value);
    if (isNaN(input_value)) return;

    state.current_count = Math.max(0, Math.min(input_value - 1, state.current_data.counts.length - 1))

    load_data_for_count();
}

function get_scale_from_dropdown() {
    return document.getElementById('scale-linear').checked ? 'linear' : 'logarithmic';
}

function get_scale_min() {
    return get_scale_from_dropdown() == 'logarithmic' ? 1 : 0;
}

function load_race_from_data(data) {
    if (state.chart) {
        state.chart.destroy();
    }

    if (location.href.indexOf('git') == -1) {
        console.log(data);
    }

    document.getElementById('election-blurb').innerText = data.blurb_text;

    state.current_data = data;
    state.current_count = 0;
    state.old_count = null;

    state.data = {
        labels: data.names.map(
            name => data.candidate_info[name].display_name
        ),
        datasets: [
            {
                label: "Votes",
                data: [],
                backgroundColor: data.names.map(
                    name => data.candidate_info[name].colour_data
                ),
                datalabels: {
                    color: data.names.map(
                        name => data.candidate_info[name].colour_data
                    ),
                    anchor: 'end',
                    align: 'end',
                    offset: -5,
                    formatter: function(value, context) {
                        let change = `${state.count_change[context.dataIndex]}`;
                        if (change === '0') {
                            change = ''
                        } else if (change[0] !== '-') {
                            change = `+${change}`;
                        }
                        return change;
                    }
                },
            },
            {
                data: new Array(data.names.length).fill(data.quota),
                type: "line",
                borderDash: [8, 8],
                pointRadius: 0,
                pointHitRadius: 0,
                datalabels: {
                    display: false
                }
            }
        ]
    };

    const font_size = data.names.length > 50 ? 10 : 14;

    state.config = {
        type: "bar",
        data: state.data,
        plugins: [ChartDataLabels],
        options: {
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: ""
                },
                tooltip: {
                    callbacks: {
                        title: tooltips => tooltips.map(tooltip => {
                            const name = data.names[tooltip.dataIndex];
                            return data.candidate_info[name].tooltip_name || data.candidate_info[name].display_name;
                        })
                    }
                }
            },
            scales: {
                y: {
                    min: get_scale_min(),
                    type: get_scale_from_dropdown()
                },
                x: {
                    ticks: {
                        font: {
                            size: font_size
                        },
                        padding: 1,
                        major: {
                            enabled: true
                        },
                        autoSkip: false,
                        color: (c) => {
                            let status = data.counts[state.current_count].status[c.index];

                            if (status == 1) {
                                // excluded
                                return '#aaa';
                            }
                        }
                    }
                }
            }
        }
    };

    state.chart = new Chart(
        document.getElementById("vote-chart"),
        state.config
    );

    load_data_for_count();

    state.chart.update();
}

function got_js_payload_data(data) {
    let race_id = `${data.election_name}-${data.state}`;
    js_loaded_data[race_id] = data;
    load_race_from_js(race_id);
}

function load_race_from_js(race_id) {
    if (js_loaded_data[race_id]) {
        load_race_from_data(js_loaded_data[race_id]);
    } else {
        const loader = document.createElement('script');
        loader.src = `./data_out/${race_id}.js`;
        document.body.appendChild(loader);
    }
}

function load_race(race_id) {
    fetch(`./data_out/${race_id}.json`)
        .then(response => response.json())
        .then(load_race_from_data)
        .catch(
            err => load_race_from_js(race_id)
        );
}


document.getElementById("advance").addEventListener("click", advance);
document.getElementById("backwards").addEventListener("click", backwards);
document.getElementById("advance_major").addEventListener("click", advance_major);
document.getElementById("backwards_major").addEventListener("click", backwards_major);
document.getElementById("jump_to_count").addEventListener("click", jump_to_count);

['scale-linear', 'scale-logarithmic'].forEach(id_name => {
    document.getElementById(id_name).addEventListener('change', e => {
        state.config.options.scales.y.type = get_scale_from_dropdown();
        state.config.options.scales.y.min = get_scale_min();
        load_data_for_count();
    });
});

document.body.addEventListener("keydown", e => {
    if (e.key === 'ArrowRight') {
        advance();
    } else if (e.key === 'ArrowLeft') {
        backwards();
    }
});

function get_race_list() {
    // TODO: move this data into a JSON in data_out
    const ALL_STATES = ['ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'].sort();
    const ELECTION_YEARS = [2022, 2019, 2016, '2014-special', 2013, 2010, 2007, 2004];
    const all_races = [];

    ELECTION_YEARS.forEach(election_year => {
        if (election_year == '2014-special') {
            all_races.push({
                id: `2014-special-election-WA`,
                state: 'WA',
                year: 2014,
                display_name: '2014 WA (special)'
            });
            return;
        }

        ALL_STATES.forEach(state => {
            all_races.push({
                id: `${election_year}-federal-election-${state}`,
                state: state,
                year: election_year,
                display_name: `${election_year} ${state}`
            });
        });
    });

    return all_races;
}

const race_choose_el = document.getElementById('race-chooser');
get_race_list().forEach(race => {
    const option = document.createElement('option');
    option.innerText = race.display_name;
    option.dataset['race'] = race.id;
    race_choose_el.appendChild(option);
});

race_choose_el.addEventListener('input', e => {
    const option = race_choose_el.selectedOptions[0];
    if (!option) return;

    load_race(option.dataset['race']);
});

load_race(get_race_list()[0].id);
