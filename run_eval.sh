TIMESTAMP=`date "+%Y-%m-%d-%H-%M-%S"`
QUERY_TYPE=${QUERY_TYPE:-pointfact}
mkdir -p eval/${QUERY_TYPE}/${TIMESTAMP}/
curl -XGET localhost:9200/config > eval/${QUERY_TYPE}/${TIMESTAMP}/config.json
for f in eval/${QUERY_TYPE}/*.json ;
do
	bin/query.sh -q $f > eval/${QUERY_TYPE}/$TIMESTAMP/$(basename ${f}).out
done

./compile_eval.sh $TIMESTAMP $QUERY_TYPE