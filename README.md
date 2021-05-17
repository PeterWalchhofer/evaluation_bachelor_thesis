# README 

## Evaluation
In this repository, the notebook `Analysis.ipynb` computes the numbers for the evaluation section of my bachelor thesis.
Also, the `Merge.ipynb` explains the merging and enrichment logic that is incorporated into the CLI `merger` tool, which can be found in the `./merger` directory. 
The code was written with replicability in mind. Therefore, it is not necessary to run an instance of Aleph along with the scripts.
The `TestWorkflow.ipynb` can be used for going through the reconciliation -> download -> (enrich) -> match -> merge process.
The `ontology mapping.xlsx` documents the mapping decisions between FtM and Wikidata.

## Scraper
The [scraper](https://github.com/PeterWalchhofer/opensanctions/blob/master/opensanctions/crawlers/at_poi.py) for [meineabgeordneten.at](https://www.meineabgeordneten.at/Abgeordnete) can be found [here](https://github.com/PeterWalchhofer/opensanctions). It is called `at_poi`.The repository of OpenSanction was forked to preserve functionality on future changes. The extracted data however, is found in this repository (in the `/data` directory) in case the scraper breaks due changes of the site's structure.

## Reconciliation UI
The reconciliation tool was implemented by forking the Aleph repository and can be found [here](https://github.com/PeterWalchhofer/aleph). A detailed description on how to run the service is also found there.