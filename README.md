# evaluation_bachelor_thesis




# Merge script
Apart from the jupyter notebook (Merge.ipynb), I implemented the merge-file-generator as a command-line tool. The wd merge script generates a matching file that links FtM Ids that have a common Wikidata ID and calls `ftm link`, which applies the merges and `ftm aggregate` to actually merge them (see [fragmentation](https://followthemoney.readthedocs.io/en/latest/fragments.html))
```
python wd_merger.py match-wd -f <infile2> -s <infile1> -o <outfile>
```

You can copy an paste it and cd to root dir:
```
python wd_merger.py match-wd -f data/output/everypolitician.json -s data/output/meineabgeordneten_wikidata.json -o data/output/matches.json
```
This generates a `matches.json`, which can be used to stream to an Aleph instance or ingest into a Neo4j db.

Aleph:
```cat matches.json | alephclient --host https://aleph.occrp.org --api-key asdf123 write-entities -f collection_id ```

 Neo4j:
 ```
 cat matches.json | ftm export-cypher | cypher-shell -u user -p password
 ```