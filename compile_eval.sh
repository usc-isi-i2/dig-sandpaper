TIMESTAMP=$1
QUERY_TYPE=$2
for f in eval/${QUERY_TYPE}/${TIMESTAMP}/*.out ;
do
	cat $f | jq -c .[] >> eval/${QUERY_TYPE}/${TIMESTAMP}.out
done
jq -c -s . eval/${QUERY_TYPE}/${TIMESTAMP}.out > eval/${QUERY_TYPE}/${TIMESTAMP}.out.compiled

for f in eval/${QUERY_TYPE}/${TIMESTAMP}/*.timing ;
do
	cat $f >> eval/${QUERY_TYPE}/${TIMESTAMP}.timing.csv
done

mkdir -p eval/${QUERY_TYPE}/${TIMESTAMP}/config
cp config/etk/* eval/${QUERY_TYPE}/${TIMESTAMP}/config
curl -XGET localhost:9876/config > eval/${QUERY_TYPE}/${TIMESTAMP}/config/config.json