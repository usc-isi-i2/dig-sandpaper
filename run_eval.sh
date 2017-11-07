TIMESTAMP=`date "+%Y-%m-%d-%H-%M-%S"`
QUERY_TYPE=${QUERY_TYPE:-pointfact}
mkdir -p eval/${QUERY_TYPE}/${TIMESTAMP}/
for f in eval/${QUERY_TYPE}/*.json ;
do
	bin/query.sh -q $f > eval/${QUERY_TYPE}/$TIMESTAMP/$(basename ${f}).out 2> eval/${QUERY_TYPE}/$TIMESTAMP/$(basename ${f}).timing
done

./compile_eval.sh $TIMESTAMP $QUERY_TYPE