# evaluation_bachelor_thesis




# Merge script
Apart from the jupyter notebook (Merge.ipynb), I implemented the merge-file-generator as a command-line tool.

The wd merge script generates a matching file with common Wikidata ID.
```
python wd_merger.py match-wd -f <infile2> -s <infile1> -o <outpath>
```

You can copy an paste it and cd to root dir:
```
python wd_merger.py match-wd -f data/output/everypolitician.json -s data/output/meineabgeordneten_wikidata.json -o data/output/matches.json
```
<hr>

To apply the merge, we can use the `ftm link` command:
```
ftm link -i everypolitician.json -m matches.json -o linked_1.json
```

```
ftm link -i meineabgeordneten_wikidata.json -m matches.json -o linked_2.json
```

Now we have 2 files.

```
cat linked_1.json linked_2.json > matched.json
```

<br>

Aggregate to actually merge them (see [fragmentation](https://followthemoney.readthedocs.io/en/latest/fragments.html))

```
cat matched.json | ftm aggregate -o matched_and_aggregated.json 
```
