'use strict';

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
            name => `${name} (${data.candidate_info[name].party_name})`
        ),
        datasets: [{
            label: "Votes",
            data: [],
            backgroundColor: data.names.map(
                name => data.candidate_info[name].colour_data
            )
        },
        {
            data: [0],
            type: "line",
            borderDash: [8, 8],
            pointRadius: 0,
            pointHitRadius: 0
        }]
    };

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
            },
            scales: {
                y: {
                    min: get_scale_min(),
                    type: get_scale_from_dropdown()
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

function load_race(election_name, state) {
    fetch(`./data_out/${election_name}-${state}.json`)
        .then(response => response.json())
        .then(load_race_from_data);
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

window.addEventListener("keydown", e => {
    if (e.key === 'ArrowRight') {
        advance();
    } else if (e.key === 'ArrowLeft') {
        backwards();
    } 
});

load_race('2022-federal-election', 'ACT');