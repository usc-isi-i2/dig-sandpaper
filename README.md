# dig-sandpaper
![travis ci](https://travis-ci.org/usc-isi-i2/dig-sandpaper.svg?branch=master)

# Docker deployment instructions

`docker run -it -P digsandpaper:digsandpaper`

* If you want to provide a custom config file, you can volume mount the config directory

`docker run -it -v config:/etc/sandpaper/config -P digsandpaper:digsandpaper`

* By default digsandpaper will use the file at /etc/sandpaper/config/sandpaper.json.  If you need to point to a different config in the mounted volume, create a config directory and put your config in there, and then use the following command

`docker run -it -v config:/etc/sandpaper/config -P digsandpaper:digsandpaper bin/start.sh --config config/your-custom-config.json --host 0.0.0.0`

* Docker will expose a port that you should be able to query

`docker run -d -p 9876:9876 digsandpaper:digsandpaper`
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

* Notes
Currently the config files use relative paths that will be resolved relative to the directory you're running the start.sh script from.  You'll want to preserve the directory structure in the meantime.  

* ES notes
To configure the elasticsearch server used by coarse search, edit `$.coarse.execute.components[0]` in config.json and either change the `host` and `port` fields or create an `endpoints` field with an array of endpoints i.e. `["https://username:password@server/proxy"]`.  Update the `type_index_mappings.json` and `type_doc_type_mappings.json` as appropriate to route the queries to the appropriate index and doc type. 

