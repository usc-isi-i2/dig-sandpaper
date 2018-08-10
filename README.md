# dig-sandpaper
![travis ci](https://travis-ci.org/usc-isi-i2/dig-sandpaper.svg?branch=master)

# Docker deployment instructions

`docker run -it -P uscisii2:digsandpaper`

* If you want to provide a custom config file, you can volume mount the config directory

`docker run -it -v config:/etc/sandpaper/config -P uscisii2:digsandpaper`

* By default digsandpaper will use the file at /etc/sandpaper/config/sandpaper.json.  If you need to point to a different config in the mounted volume, create a config directory and put your config in there, and then use the following command

`docker run -it -v config:/etc/sandpaper/config -P uscisii2:digsandpaper bin/start.sh --config config/your-custom-config.json --host 0.0.0.0`

* Docker will expose a port that you should be able to query

`docker run -d -p 9876:9876 uscisii2:digsandpaper`
`curl -XGET localhost:9876`

# Development instructions
It is highly suggested you create a conda environment or virtual environment before installing digsandpaper
```
conda-env create --name sandpaperenv requests
source activate sandpaperenv
```
```
virtualenv sandpaperenv
. sandpaperenv/bin/activate
```

* If you're running outside the repository, you can pip install the latest version of digsandpaper
```
pip install digsandpaper
```

* Then you should copy the following files recursively
```
bin/start.sh
start.py
config/*
```

* Run the sandpaper server script
```
bin/start.sh --config config/basic/config.json
```

* Run Elasticsearch server locally and run unit tests
```
python -W ignore -m unittest discover
```

* Notes
Currently the config files use relative paths that will be resolved relative to the directory you're running the start.sh script from.  You'll want to preserve the directory structure in the meantime.  

* ES notes
To configure the elasticsearch server used by coarse search, edit `$.coarse.execute.components[0]` in config.json and either change the `host` and `port` fields or create an `endpoints` field with an array of endpoints i.e. `["https://username:password@server/proxy"]`.  Update the `type_index_mappings.json` and `type_doc_type_mappings.json` as appropriate to route the queries to the appropriate index and doc type. 

# myDIG integration

The myDIG service provides a convenient web interface for configuring and interacting with sandpaper.  

If myDIG is properly setup with a project, you can configure sandpaper to configure itself using myDIG at runtime. 

```
bin/start.sh --host 0.0.0.0 \
                --config config/sandpaper.json \
                --mydigurl http://USER:PASSWORD@mydig:9879 \
                --project myproject \
                --endpoint https://elasticsearch:9200
```

If you want sandpaper to connect to the sample index specified by the myDIG project add the `--sample` flag

```
bin/start.sh --host 0.0.0.0 \
                --config config/sandpaper.json \
                --mydigurl http://USER:PASSWORD@mydig:9879 \
                --project myproject \
                --endpoint https://elasticsearch:9200 \
                --sample
```

If you want to iterate on a separate or earlier index, add the `--index` flag

```
bin/start.sh --host 0.0.0.0 \
                --config config/sandpaper.json \
                --mydigurl http://USER:PASSWORD@mydig:9879 \
                --project myproject \
                --endpoint https://elasticsearch:9200 \
                --index myoldindex
```

If you need to work with sandpaper from the command line outside of the myDIG interface, you can have it create an index, load some documents, and configure itself using cURL in three easy steps.

First tell dig-sandpaper to create a mapping for a given `project` at the myDIG `url` and use it to create an `index` at an elasticsearch `endpoint`

```
curl -XPUT "http://localhost:9876/mapping?url=http%3A%2F%2FUSER%3APASSWORD%40myDIG%3A9879&project=myproject&index=myindex&endpoint=http%3A//elasticsearch%3A9200"
```

Second, send some jsonlines documents out put by ETK of `type` ads to dig-sandpaper to add at the appropriate `index` and `endpoint`

```
curl  -H "Content-Type: application/json"  -XPOST --data-binary @project_etk_output.jl "localhost:9876/indexing?index=myindex&endpoint=http%3A//elasticsearch%3A9200&type=ads" 
```

Third, tell dig-sandpaper to reconfigure itself using the `project` at the myDIG `url` and use the `index` at the elasticsearch `endpoint`

```
curl -XPOST "localhost:9876/config?url=http%3A%2F%2FUSER%3APASSWORD%40mydig%3A9879&project=myproject&index=myindex&endpoint=http%3A//elasticsearch%3A9200&type=ads" 
```

You should now be able to issue a query using the `bin/query.sh` script.
