TIMESTAMP=$1
QUERY_TYPE=$2
for f in eval/${QUERY_TYPE}/${TIMESTAMP}/* ;
do
	cat $f | jq -c .[] >> eval/${QUERY_TYPE}/${TIMESTAMP}.out
done
jq -c -s . eval/${QUERY_TYPE}/${TIMESTAMP}.out > eval/${QUERY_TYPE}/${TIMESTAMP}.out.compiled

mkdir -p eval/${QUERY_TYPE}/${TIMESTAMP}/config
cp config/etk/* eval/${QUERY_TYPE}/${TIMESTAMP}/config