bin/generate_es_mapping.sh $1 indexed_kg_mapping.json index_knowledge_graph.json default_kg_mapping.json
curl -XDELETE $2:$3/$4
curl -XPUT -d @indexed_kg_mapping.json $2:$3/$4
#bin/index_knowledge_graph.sh $5 gtc.out index_knowledge_graph.json
#head -n 100 gtc.out > gtc.out.100
bin/bulk_poster.sh gtc.out.100 $2 $3 $4 ads