'use strict';

let js_loaded_data = {};

let state = {
    current_data: null,
    current_count: null,
    char: null
};

function load_data_for_count() {
    state.data.datasets[0].data = state.current_data.counts[
        state.current_count
    ].progressive_vote_total;
    state.config.options.plugins.title.text = `Count ${state.current_count + 1}`;

    state.chart.update();
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

function get_scale_from_dropdown() {
    return document.getElementById('scale-linear').checked ? 'linear' : 'logarithmic';
}

function get_scale_min() {
    return get_scale_from_dropdown() == 'logarithmic' ? 1 : 0;
}

function load_race_from_data(data) {
    console.log(data);

    if (state.chart) {
        state.chart.destroy();
    }


    state.current_data = data;
    state.current_count = 0;

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
                )
            },
            {
                data: new Array(data.names.length).fill(data.quota),
                type: "line",
                borderDash: [8, 8],
                pointRadius: 0,
                pointHitRadius: 0
            }
        ]
    };

    const font_size = data.names.length > 50 ? 10 : 14;

    state.config = {
        type: "bar",
        data: state.data,
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
                            console.log(data.candidate_info[name].tooltip_name);
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
                        autoSkip: false
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

['scale-linear', 'scale-logarithmic'].forEach(id_name => {
    document.getElementById(id_name).addEventListener('change', e => {
        console.log(e);
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
    const ELECTION_YEARS = [2022, 2019, 2016, 2013, 2010, 2007, 2004];
    const all_races = [];

    ELECTION_YEARS.forEach(election_year => {
        ALL_STATES.forEach(state => {
            all_races.push({
                id: `${election_year}-federal-election-${state}`,
                state: state,
                year: election_year
            });
        });
    });

    return all_races;
}

const race_choose_el = document.getElementById('race-chooser');
get_race_list().forEach(race => {
    const option = document.createElement('option');
    option.innerText = `${race.year} ${race.state}`;
    option.dataset['race'] = race.id;
    race_choose_el.appendChild(option);
});

race_choose_el.addEventListener('input', e => {
    const option = race_choose_el.selectedOptions[0];
    if (!option) return;

    load_race(option.dataset['race']);
});

load_race(get_race_list()[0].id);
