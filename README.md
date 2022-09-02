# SenateGrapher

## About

This program allows for the visualisation of the distribution of preferences in Australian Senate elections. Not all planned features have been implemented, but the core functionality is all there.

## `process_data.py`

`process_data.py` is responsible for turning the AEC input data and outputting JSON which can be fetched by the webpage. The following additional input files should be downloaded from the AEC tally room website and put in the `data_in` folder for `process_data.py` to work:
 * `SenateCandidatesDownload-{election}.csv`, which contains the candidate information (for mapping candidate name to candidate party).
 * `SenateDopDownload-{election}`, which should be another folder which is unzipped from the original AEC download. Each folder then contains files of the form `SenateStateDOPDownload-{election}-{state}.csv`, which is where the actual distribution of preferences data comes from.

The `ELECTION_ID_TO_NAME` dict at the top of `process_data.py` has to be manually modified to include the election event ID's which should be processed. The output data is placed in `data_out`.

## Credits

- **Code**: Written by Gus Evans and Xavier Cooney, and licensed under the [MIT License](LICENSE).
- **Graphing library**: [Chart.js](https://www.chartjs.org), licensed under the [MIT License](https://github.com/chartjs/Chart.js/blob/master/LICENSE.md).
- **Election data**: From the [Australian Electoral Commission](https://www.aec.gov.au)'s online [Tally Room](https://results.aec.gov.au), licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Party colours**: From the [English Wikipedia](https://en.wikipedia.org/wiki/Template:Australian_politics/party_colours), licensed under [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
